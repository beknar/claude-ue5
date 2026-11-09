// Brokenspire and Mistward Castle (the user's of 2026-11-06: "when the heroes go into the dungeon, they should bring with them
// their current state. when the heroes leave to go to Brokenspire, they should also bring with them their current state. this
// includes statistics and all inventory items"). The generator's SaveCarry / RestoreCarry (RDTownGame.cpp) keep her things,
// what she wears, her spells, hit points, mana and blessing; this keeps the rest of her as it was:
//   statistics       the combat component's counters (kills, blows, damage dealt and taken, potions used, ...), each spell's
//                    casts, each slash's procs
//   on her           potions' and food's effects, her spells on her (ward, iron skin, veil, mirror, pact, hex ward) with their
//                    looks, stealth, a slash's haste, evasion and deflection, the crystal shield, poison, weakness,
//                    slowness, a snare: each with the seconds it had left
//   ready            her weapons' and spells' cooldowns, her roll's and dash's (the seconds left), the Rogue's dexterity energy
//   at hand          the slash on each found weapon, the quick bar as she set it, the torch lit
//   her summons      each standing summon, called to her side again in the next level as hurt as it was
// A level's clock starts again from 0: every time on her is kept as the seconds left, not as a moment.
#include "RD/RDCombat.h"
#include "RD/RDDungeonGenerator.h"
#include "RD/RDGameInstance.h"
#include "RD/RDMonster.h"
#include "Engine/World.h"
#include "GameFramework/Pawn.h"

DEFINE_LOG_CATEGORY_STATIC(LogRDCarry, Log, All);

// (her statistics: whole counts and amounts)
#define RDCARRY_COUNTS(X) X(Kills) X(AttacksMade) X(HitsLanded) X(HitsTaken) X(Deaths) X(StepsTaken) X(BoltsCast) X(BoltsOnMonsters) \
	X(BoltsElsewhere) X(Rolls) X(DodgedHits) X(Dashes) X(AbilitiesUsed) X(CastsRefused) X(ItemsUsed) X(ArmourChanges) X(ArmourWornOut) \
	X(ItemsRepaired) X(ItemsCrafted) X(WeaponsBroken) X(WeaponsTaken) X(SpellsLearned) X(WardBlocks) X(Reflected) X(PactSaves) X(Evaded) \
	X(ZoneBlocks) X(CooldownRefusals) X(StealthUses) X(StealthRefusals) X(Ambushes) X(StealthTrapsPassed) X(WeaponsBrokenDown) \
	X(ShieldBlocks) X(ShieldsBroken) X(GearBrokenDown) X(HarvestsTaken) X(ScrollsRead) X(SummonsRefused) X(Summoned) X(BlockedHits) X(FallsHurt) \
	X(MouseUses) X(LimbFxMade)
#define RDCARRY_AMOUNTS(X) X(DamageDealt) X(DamageTaken) X(AmbushDamage) X(SlashBonusDealt)

void URDCombatComponent::GatherState(FRDCarry& C) const
{
	C.Stats.Reset(); C.SpellCasts.Reset(); C.SlashProcs.Reset(); C.Timed.Reset(); C.Cooldowns.Reset();
	C.EffectItems.Reset(); C.EffectKinds.Reset(); C.EffectAmounts.Reset(); C.EffectLeft.Reset();
	C.QuickSlots.Reset(); C.QuickOff.Reset(); C.Summons.Reset(); C.SummonShares.Reset(); C.SlashWeapons.Reset(); C.SlashNames.Reset();
	C.DexEnergy = -1.f; C.TorchHeld = NAME_None; C.QuickFirst = 0;
	C.SecondaryRanks = SecondaryRanks; C.BoostSpells = BoostSpells;          // (the sixth phase)
	const UWorld* W = GetWorld();
	if (!W || !Generator) return;
	const float Now = W->GetTimeSeconds();
	// ---- statistics
#define RDCARRY_PUT(N) C.Stats.Add(FName(TEXT(#N)), (float)N);
	RDCARRY_COUNTS(RDCARRY_PUT)
	RDCARRY_AMOUNTS(RDCARRY_PUT)
#undef RDCARRY_PUT
	C.SpellCasts = SpellsReleased;
	C.SlashProcs = SlashProcs;
	// ---- what is on her: the seconds left and its strength
	auto Put = [&](const TCHAR* N, float Until, float Amount)
	{
		if (Until <= Now) return;
		C.Timed.Add(FName(*(FString(N) + TEXT("Left"))), Until - Now);
		C.Timed.Add(FName(N), Amount);
	};
	Put(TEXT("Ward"), WardUntil, WardPool);
	if (WardUntil > Now) C.Timed.Add(TEXT("WardHits"), (float)WardHits);
	Put(TEXT("Skin"), SkinUntil, SkinShare);
	Put(TEXT("Veil"), VeilUntil, VeilEvade);
	Put(TEXT("Mirror"), MirrorUntil, MirrorShare);
	Put(TEXT("Pact"), PactUntil, PactShare);
	Put(TEXT("Dispel"), DispelUntil, 0.f);
	Put(TEXT("Stealth"), StealthUntil, bAmbushArmed ? 1.f : 0.f);
	Put(TEXT("Poison"), PoisonUntil, PoisonDps);
	Put(TEXT("Weak"), WeakUntil, WeakShare);
	Put(TEXT("Slow"), SlowMeUntil, SlowMeShare);
	Put(TEXT("Haste"), HasteUntil, HasteShare);
	Put(TEXT("Evasion"), SlashEvadeUntil, SlashEvadeShare);
	Put(TEXT("Deflect"), DeflectUntil, DeflectShare);
	Put(TEXT("CrystalReady"), SlashShieldReadyAt, 0.f);
	Put(TEXT("Roll"), RollReadyAt, 0.f);                 // (her roll's and dash's cooldown)
	if (bSlashShieldUp) C.Timed.Add(TEXT("CrystalUp"), 1.f);
	if (bHeldOn) Put(TEXT("Held"), HeldUntil, 0.f);
	// ---- potions and food working on her
	for (const FEffect& E : Effects)
	{
		C.EffectItems.Add(E.Item); C.EffectKinds.Add((uint8)E.Kind); C.EffectAmounts.Add(E.Amount); C.EffectLeft.Add(E.Left);
	}
	// ---- ready: cooldowns, the Rogue's energy
	for (const TPair<FName, float>& R : ReadyAt) if (R.Value > Now) C.Cooldowns.Add(R.Key, R.Value - Now);
	if (MaxDexEnergy > 0.f) C.DexEnergy = DexEnergy;
	// ---- at hand: the slashes on her found weapons (with the weapon's item), the quick bar, the torch
	for (const FRDWeaponDef& Wd : Generator->Weapons)
		if (!Wd.Item.IsNone() && !Wd.Slash.IsNone()) { C.SlashWeapons.Add(Wd.Item); C.SlashNames.Add(Wd.Slash); }
	C.QuickSlots = QuickSlots; C.QuickOff = QuickOff.Array(); C.QuickFirst = QuickFirst;
	if (bTorchHeld && !TorchItem.IsNone()) C.TorchHeld = TorchItem;
	// ---- her summons standing
	for (const ARDMonster* A : Generator->Allies)
		if (IsValid(A) && !A->IsDead() && !A->SummonSpell.IsNone())
		{
			C.Summons.Add(A->SummonSpell); C.SummonShares.Add(A->GetMaxHealth() > 0.f ? A->GetHealth() / A->GetMaxHealth() : 1.f);
		}
	// (and those she brought that are not at her side yet: the town's autosave as she comes in is taken before they are)
	for (int32 I = 0; I < Generator->CarrySummons.Num(); ++I)
	{
		C.Summons.Add(Generator->CarrySummons[I]); C.SummonShares.Add(Generator->CarrySummonShares.IsValidIndex(I) ? Generator->CarrySummonShares[I] : 1.f);
	}
}

void URDCombatComponent::RestoreState(const FRDCarry& C)
{
	UWorld* W = GetWorld();
	if (!W || !Generator) return;
	const float Now = W->GetTimeSeconds();
	// ---- statistics
#define RDCARRY_GETCOUNT(N) if (const float* V = C.Stats.Find(FName(TEXT(#N)))) N = FMath::RoundToInt(*V);
#define RDCARRY_GETAMOUNT(N) if (const float* V = C.Stats.Find(FName(TEXT(#N)))) N = *V;
	RDCARRY_COUNTS(RDCARRY_GETCOUNT)
	RDCARRY_AMOUNTS(RDCARRY_GETAMOUNT)
#undef RDCARRY_GETCOUNT
#undef RDCARRY_GETAMOUNT
	SpellsReleased = C.SpellCasts;
	SlashProcs = C.SlashProcs;
	SecondaryRanks = C.SecondaryRanks; BoostSpells = C.BoostSpells;          // (the sixth phase's abilities, before the quick bar)
	// ---- what is on her, with the seconds it had left (and the look of a spell on her)
	auto Get = [&](const TCHAR* N, float& Until, float& Amount) -> bool
	{
		const float* L = C.Timed.Find(FName(*(FString(N) + TEXT("Left"))));
		if (!L || *L <= 0.f) return false;
		Until = Now + *L;
		if (const float* A = C.Timed.Find(FName(N))) Amount = *A;
		return true;
	};
	// (a spell on her looks as the spell she knows of that kind casts it, or the table's first of the kind)
	auto SpellOfKind = [&](ERDSpellKind K) -> const FRDSpellDef*
	{
		for (const FRDWeaponDef& Wd : Generator->Weapons)
			if (Wd.bSpell && Generator->Spells.IsValidIndex(Wd.SpellIndex) && Generator->Spells[Wd.SpellIndex].Kind == K) return &Generator->Spells[Wd.SpellIndex];
		return Generator->Spells.FindByPredicate([K](const FRDSpellDef& S) { return S.Kind == K; });
	};
	float Dummy = 0.f;
	if (Get(TEXT("Ward"), WardUntil, WardPool))
	{
		if (const float* H = C.Timed.Find(TEXT("WardHits"))) WardHits = FMath::RoundToInt(*H);
		SetAura(ERDSpellKind::Ward, SpellOfKind(ERDSpellKind::Ward), true);
	}
	if (Get(TEXT("Skin"), SkinUntil, SkinShare)) SetAura(ERDSpellKind::Skin, SpellOfKind(ERDSpellKind::Skin), true);
	if (Get(TEXT("Veil"), VeilUntil, VeilEvade)) SetAura(ERDSpellKind::Veil, SpellOfKind(ERDSpellKind::Veil), true);
	if (Get(TEXT("Mirror"), MirrorUntil, MirrorShare)) SetAura(ERDSpellKind::Mirror, SpellOfKind(ERDSpellKind::Mirror), true);
	if (Get(TEXT("Pact"), PactUntil, PactShare)) SetAura(ERDSpellKind::Pact, SpellOfKind(ERDSpellKind::Pact), true);
	if (Get(TEXT("Dispel"), DispelUntil, Dummy)) SetAura(ERDSpellKind::Dispel, SpellOfKind(ERDSpellKind::Dispel), true);
	float Armed = 0.f;
	if (MaxDexEnergy > 0.f && Get(TEXT("Stealth"), StealthUntil, Armed))
	{
		bAmbushArmed = Armed > 0.5f; StealthEndReason.Reset();
		// (its look as StartStealth gives it: the table's first Shadow Veil, under the stealth's own key)
		const int32 Vi = Generator->Spells.IndexOfByPredicate([](const FRDSpellDef& S) { return S.Kind == ERDSpellKind::Veil; });
		if (Vi >= 0) SetAura(RDStealthAuraKind, &Generator->Spells[Vi], true);
	}
	Get(TEXT("Poison"), PoisonUntil, PoisonDps);
	Get(TEXT("Weak"), WeakUntil, WeakShare);
	Get(TEXT("Slow"), SlowMeUntil, SlowMeShare);          // (her walk slows on the next tick, as when a monster slows her)
	Get(TEXT("Haste"), HasteUntil, HasteShare);
	Get(TEXT("Evasion"), SlashEvadeUntil, SlashEvadeShare);
	Get(TEXT("Deflect"), DeflectUntil, DeflectShare);
	Get(TEXT("CrystalReady"), SlashShieldReadyAt, Dummy);
	Get(TEXT("Roll"), RollReadyAt, Dummy);
	bSlashShieldUp = C.Timed.Contains(TEXT("CrystalUp"));
	if (Get(TEXT("Held"), HeldUntil, Dummy)) bHeldOn = true;
	// ---- potions and food working on her
	Effects.Reset();
	for (int32 I = 0; I < C.EffectItems.Num() && I < C.EffectKinds.Num() && I < C.EffectAmounts.Num() && I < C.EffectLeft.Num(); ++I)
		if (C.EffectLeft[I] > 0.f) Effects.Add({ (ERDItemKind)C.EffectKinds[I], C.EffectAmounts[I], C.EffectLeft[I], C.EffectItems[I] });
	// ---- ready: cooldowns, the Rogue's energy
	for (const TPair<FName, float>& R : C.Cooldowns) ReadyAt.Add(R.Key, Now + R.Value);
	if (C.DexEnergy >= 0.f && MaxDexEnergy > 0.f) DexEnergy = FMath::Clamp(C.DexEnergy, 0.f, MaxDexEnergy);
	// ---- at hand: each slash back on a found weapon of the item it was on (TakeBack laid it in her pack beside it; a weapon
	// this level could not give back leaves its slash in her pack and moves no other), then the quick bar as she set it
	// (FillQuickSlots keeps what is set and fills only what is empty)
	for (int32 I = 0; I < C.SlashWeapons.Num() && I < C.SlashNames.Num(); ++I)
	{
		const FName Sl = C.SlashNames[I];
		if (Sl.IsNone() || GetItemCount(Sl) <= 0) continue;
		for (FRDWeaponDef& Wd : Generator->Weapons)
			if (Wd.Item == C.SlashWeapons[I] && Wd.Slash.IsNone()) { Wd.Slash = Sl; RemoveCarried(Sl, 1); break; }
	}
	if (C.QuickSlots.Num() > 0)
	{
		QuickSlots = C.QuickSlots; QuickOff.Reset(); for (const FName& Q : C.QuickOff) QuickOff.Add(Q);
		if (Generator->bQuickSlots) FillQuickSlots();
		QuickFirst = FMath::Clamp(C.QuickFirst, 0, FMath::Max(0, QuickSlots.Num() - 1));
	}
	if (!C.TorchHeld.IsNone() && GetItemCount(C.TorchHeld) > 0) { TorchItem = C.TorchHeld; HoldTorch(true); }
	UpdateWalkSpeed();
	// ---- her summons: called to her side once she stands in this level (the generator's TickCarrySummons)
	Generator->CarrySummons = C.Summons; Generator->CarrySummonShares = C.SummonShares;
	Generator->CarrySummonFrom = Now + 0.5f; Generator->CarrySummonUntil = Now + 20.f;
	UE_LOG(LogRDCarry, Log, TEXT("RDCARRY state back: %d statistics (%d kills), %d timed, %d effects, %d cooldowns, %d quick slots, torch %s, %d slashes, %d summons to call"),
		C.Stats.Num(), Kills, C.Timed.Num() / 2, Effects.Num(), C.Cooldowns.Num(), C.QuickSlots.Num(), *C.TorchHeld.ToString(), C.SlashNames.Num(), C.Summons.Num());
}

TArray<FString> URDCombatComponent::GetStateLines() const
{
	TArray<FString> Out;
	if (!Generator) return Out;
	FRDCarry C; GatherState(C);
	Out.Add(FString::Printf(TEXT("hp|%.2f|%.2f"), Health, MaxHealth));
	Out.Add(FString::Printf(TEXT("mana|%.2f|%.2f"), Mana, MaxMana));
	if (C.DexEnergy >= 0.f) Out.Add(FString::Printf(TEXT("dex|%.2f|%.2f"), C.DexEnergy, MaxDexEnergy));
	for (const TPair<FName, float>& S : C.Stats) Out.Add(FString::Printf(TEXT("stat|%s|%.2f"), *S.Key.ToString(), S.Value));
	for (const TPair<FName, int32>& S : C.SpellCasts) Out.Add(FString::Printf(TEXT("spell|%s|%d"), *S.Key.ToString(), S.Value));
	for (const TPair<FString, int32>& S : C.SlashProcs) Out.Add(FString::Printf(TEXT("proc|%s|%d"), *S.Key, S.Value));
	for (const TPair<FName, float>& T : C.Timed)
	{
		const FString K = T.Key.ToString();
		if (!K.EndsWith(TEXT("Left"))) continue;
		const FString N = K.LeftChop(4);
		const float* A = C.Timed.Find(FName(*N));
		Out.Add(FString::Printf(TEXT("timed|%s|%.2f|%.3f"), *N, T.Value, A ? *A : 0.f));
	}
	if (C.Timed.Contains(TEXT("CrystalUp"))) Out.Add(TEXT("timed|CrystalUp|0|1"));
	if (const float* H = C.Timed.Find(TEXT("WardHits"))) Out.Add(FString::Printf(TEXT("timed|WardHits|0|%.0f"), *H));
	for (int32 I = 0; I < C.EffectItems.Num(); ++I)
		Out.Add(FString::Printf(TEXT("effect|%s|%d|%.3f|%.2f"), *C.EffectItems[I].ToString(), (int32)C.EffectKinds[I], C.EffectAmounts[I], C.EffectLeft[I]));
	for (const TPair<FName, float>& R : C.Cooldowns) Out.Add(FString::Printf(TEXT("cooldown|%s|%.2f"), *R.Key.ToString(), R.Value));
	for (int32 I = 0; I < C.QuickSlots.Num(); ++I) if (!C.QuickSlots[I].IsNone()) Out.Add(FString::Printf(TEXT("quick|%d|%s"), I, *C.QuickSlots[I].ToString()));
	for (const FName& Q : C.QuickOff) Out.Add(FString::Printf(TEXT("quickoff|%s"), *Q.ToString()));
	if (!C.TorchHeld.IsNone()) Out.Add(FString::Printf(TEXT("torch|%s"), *C.TorchHeld.ToString()));
	for (int32 I = 0; I < C.SlashNames.Num(); ++I) Out.Add(FString::Printf(TEXT("slash|%s|%s"), *C.SlashWeapons[I].ToString(), *C.SlashNames[I].ToString()));
	for (int32 I = 0; I < C.Summons.Num(); ++I) Out.Add(FString::Printf(TEXT("summon|%s|%.3f"), *C.Summons[I].ToString(), C.SummonShares[I]));
	Out.Sort();
	return Out;
}

// ================================================================================================ her summons, called again
void ARDDungeonGenerator::TickCarrySummons()
{
	if (CarrySummons.Num() == 0 || !GetWorld()) return;
	const float Now = GetWorld()->GetTimeSeconds();
	if (Now < CarrySummonFrom) return;
	// (in the town: once she stands where she comes in (before the castle's door), not where the level's start put her; a game
	// loaded in the wilds: once TickWildLoad has put her where the save was made (the PR review's find: bTownPlaced is set at
	// once there, and they came in Brokenspire's square, kilometres from her))
	const URDGameInstance* GI = URDGameInstance::Of(this);
	if ((bTown && !bTownPlaced) || (GI && GI->bLoadPending)) { CarrySummonUntil = FMath::Max(CarrySummonUntil, Now + 20.f); return; }
	APawn* P = PlayerCombat ? Cast<APawn>(PlayerCombat->GetOwner()) : nullptr;
	if (!P || PlayerCombat->IsDead()) return;
	const FVector L = P->GetActorLocation(), Fw = P->GetActorForwardVector();
	const float Half = P->GetSimpleCollisionHalfHeight();
	TArray<FName> Left; TArray<float> LeftShares;
	for (int32 I = 0; I < CarrySummons.Num(); ++I)
	{
		const FName Sp = CarrySummons[I];
		const FRDSpellDef* S = Spells.FindByPredicate([Sp](const FRDSpellDef& D) { return D.Name == Sp; });
		if (!S || S->SummonKind.IsNone()) { UE_LOG(LogRDCarry, Warning, TEXT("RDCARRY no summoning %s here: left behind"), *Sp.ToString()); continue; }
		const FRDMonsterDef* Kd = Monsters.FindByPredicate([S](const FRDMonsterDef& D) { return D.Name == S->SummonKind; });
		FVector At = L + Fw * 230.f;
		FindAllySpot(L, Fw, Kd ? Kd->CapsuleRadius : 45.f, P, At, Fw);
		ARDMonster* M = SummonKindAlly(S->SummonKind, At - FVector(0, 0, Half), Sp);
		if (!M) { Left.Add(Sp); LeftShares.Add(CarrySummonShares.IsValidIndex(I) ? CarrySummonShares[I] : 1.f); continue; }
		M->SetHealthShare(CarrySummonShares.IsValidIndex(I) ? CarrySummonShares[I] : 1.f);
		UE_LOG(LogRDCarry, Log, TEXT("RDCARRY summon %s back at her side: %.0f of %.0f hit points"), *Sp.ToString(), M->GetHealth(), M->GetMaxHealth());
	}
	// (one with no set of rooms under its spot yet waits a little; at the end it is left behind, and said so)
	CarrySummons = Left; CarrySummonShares = LeftShares;
	if (CarrySummons.Num() > 0 && Now >= CarrySummonUntil)
	{
		UE_LOG(LogRDCarry, Warning, TEXT("RDCARRY %d summons found no room at her side: left behind"), CarrySummons.Num());
		CarrySummons.Reset(); CarrySummonShares.Reset();
	}
	else if (CarrySummons.Num() > 0) CarrySummonFrom = Now + 0.5f;
}
