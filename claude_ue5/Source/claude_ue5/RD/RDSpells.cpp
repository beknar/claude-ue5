// random_dungeonmagic_level5: the spell table's spells (the generator's Spells), her rings, the monsters' abilities on her.
// Part of URDCombatComponent (RDCombat.h): a spell of her weapons (FRDWeaponDef::Spell) is cast with her cast clips; at
// the clip's hit time a Bolt flies (LaunchBolt, with the spell's pierce, slow, burn, jumps and explosion: SpellBurst), any
// other kind does here what ERDSpellKind says (ReleaseSpell). What lasts (shields on her, zones, clouds, rifts, meteor
// storms, a drain) is worked by TickSpells. Effects come from the spell's data (CastFx, BoltFx, ImpactFx, AreaFx,
// ShieldFx: MagicProjectilesVol4 / 5, ToonExplosionVol1 / ToonExplosionsVol2, StylizedShieldsVol1), spawned with the
// packs' own parameters (User.Scale, User.Color01-03, User.Duration).
#include "RD/RDCombat.h"
#include "RD/RDDungeonGenerator.h"
#include "RD/RDMonster.h"
#include "RD/RDBlood.h"
#include "Components/CapsuleComponent.h"
#include "Components/PointLightComponent.h"
#include "Components/SkeletalMeshComponent.h"
#include "GameFramework/Character.h"
#include "Engine/World.h"
#include "NiagaraComponent.h"
#include "NiagaraFunctionLibrary.h"
#include "NiagaraSystem.h"
#include "Particles/ParticleSystem.h"
#include "Kismet/GameplayStatics.h"

static FString RDSpLower(FName N) { return N.ToString().ToLower(); }

const FRDSpellDef* URDCombatComponent::SpellOf(int32 Wi) const
{
	if (!Generator || !Generator->Weapons.IsValidIndex(Wi)) return nullptr;
	const int32 S = Generator->Weapons[Wi].SpellIndex;
	return Generator->Spells.IsValidIndex(S) ? &Generator->Spells[S] : nullptr;
}

float URDCombatComponent::GetCooldownLeft(int32 Index) const
{
	if (!Generator || !Generator->Weapons.IsValidIndex(Index) || Generator->Weapons[Index].Cooldown <= 0.f) return 0.f;
	const float* R = ReadyAt.Find(Generator->Weapons[Index].Name);
	return R ? FMath::Max(0.f, *R - GetWorld()->GetTimeSeconds()) : 0.f;
}

bool URDCombatComponent::KnowsSpell(FName Spell) const
{
	if (!Generator) return false;
	const int32 Si = Generator->FindSpell(Spell);
	for (const FRDWeaponDef& W : Generator->Weapons) if (!W.bScroll && ((Si >= 0 && W.SpellIndex == Si) || W.Name == Spell)) return true;
	return false;
}

bool URDCombatComponent::LearnSpell(FName Spell)
{
	const int32 Si = Generator ? Generator->FindSpell(Spell) : -1;
	if (Si < 0 || KnowsSpell(Spell)) return false;
	const FRDSpellDef& S = Generator->Spells[Si];
	if (!Generator->HeroLearns(S.Type))
	{
		SetMessage(FString::Printf(TEXT("The %s cannot learn %s (%s)"), *Generator->PlayerTitle.ToLower(), *S.Name.ToString(), RDSpellTypeName(S.Type)));
		return false;
	}
	FRDWeaponDef W;
	if (!Generator->MakeSpellWeapon(Si, W)) return false;
	Generator->Weapons.Add(W);
	SyncWear();
	++SpellsLearned;
	int32 Key = 0;
	for (const FRDWeaponDef& Wk : Generator->Weapons) if (!Wk.bScroll) ++Key;          // (a scroll being read is no weapon of hers)
	FString Msg = Key <= 10 ? FString::Printf(TEXT("You learn %s:  key %d"), *S.Name.ToString(), Key % 10) : FString::Printf(TEXT("You learn %s:  the wheel"), *S.Name.ToString());
	// (the user's of 2026-10-28: a spell that costs more than any ring gives raises her pool by being learned)
	const float OldMax = MaxMana;
	UpdateMaxima();
	if (MaxMana > OldMax + 0.5f)
	{
		Msg += FString::Printf(TEXT(".  Your mana pool grows to %.0f"), MaxMana);
		UE_LOG(LogTemp, Log, TEXT("RDSPELL %s raises her mana pool %.0f -> %.0f"), *S.Name.ToString(), OldMax, MaxMana);
	}
	SetMessage(Msg);
	PlayUiSound(TEXT("Player.Learn"), TEXT("Player.Loot"));
	UE_LOG(LogTemp, Log, TEXT("RDSPELL learned %s (%d weapons and spells)"), *S.Name.ToString(), Generator->Weapons.Num());
	return true;
}

float URDCombatComponent::GetTomeMana() const
{
	const FRDHeroDef* H = Generator ? Generator->FindHero(Generator->CurrentHero) : nullptr;
	float Best = 0.f;
	if (H) for (const TPair<FName, float>& P : H->TomeMana) if (P.Value > Best && KnowsSpell(P.Key)) Best = P.Value;
	return Best;
}

void URDCombatComponent::HealBy(float Amount)
{
	if (bDead || Amount <= 0.f) return;
	Health = FMath::Min(MaxHealth, Health + Amount);
}

void URDCombatComponent::CountSpellDamage(float Amount)
{
	DamageDealt += Amount; ++HitsLanded;
	LastHitTime = GetWorld()->GetTimeSeconds();
}

bool URDCombatComponent::IsVeiled() const { return GetWorld() && GetWorld()->GetTimeSeconds() < VeilUntil; }
bool URDCombatComponent::IsPoisoned() const { return GetWorld() && GetWorld()->GetTimeSeconds() < PoisonUntil && PoisonDps > 0.f; }
float URDCombatComponent::GetWeakness() const { return GetWorld() && GetWorld()->GetTimeSeconds() < WeakUntil ? WeakShare : 0.f; }
float URDCombatComponent::GetSlowness() const { return GetWorld() && GetWorld()->GetTimeSeconds() < SlowMeUntil ? SlowMeShare : 0.f; }
float URDCombatComponent::WeakMul() const { return 1.f - GetWeakness(); }
int32 URDCombatComponent::GetWardHits() const { return GetWorld() && GetWorld()->GetTimeSeconds() < WardUntil ? WardHits : 0; }
float URDCombatComponent::GetWardPool() const { return GetWorld() && GetWorld()->GetTimeSeconds() < WardUntil ? WardPool : 0.f; }
float URDCombatComponent::GetSkinBonus() const { return GetWorld() && GetWorld()->GetTimeSeconds() < SkinUntil ? SkinShare : 0.f; }

TArray<FString> URDCombatComponent::GetBuffLines() const
{
	TArray<FString> Out;
	const UWorld* W = GetWorld();
	const AActor* O = GetOwner();
	if (!W || !O) return Out;
	const float Now = W->GetTimeSeconds();
	const FVector L = O->GetActorLocation();
	auto Add = [&](const FString& T, float Until, bool bGood) { if (Now < Until) Out.Add(FString::Printf(TEXT("%s|%.1f|%d"), *T, Until - Now, bGood ? 1 : 0)); };
	if (WardPool > 0.f) Add(FString::Printf(TEXT("WARD %.0f HP"), WardPool), WardUntil, true);
	else Add(FString::Printf(TEXT("WARD %d"), WardHits), WardUntil, true);
	Add(FString::Printf(TEXT("IRON SKIN +%.0f%%"), SkinShare * 100.f), SkinUntil, true);
	Add(TEXT("VEILED"), VeilUntil, true);
	Add(TEXT("MIRROR"), MirrorUntil, true);
	Add(TEXT("UNDYING PACT"), PactUntil, true);
	if (FVector::Dist2D(L, RuneAt) <= RuneRadius) Add(FString::Printf(TEXT("RUNE -%.0f%%"), RuneShare * 100.f), RuneUntil, true);
	if (FVector::Dist2D(L, SanctumAt) <= SanctumRadius) Add(TEXT("SANCTUM"), SanctumUntil, true);
	Add(TEXT("HEX-WARDED"), DispelUntil, true);
	if (DrainTarget.IsValid()) Add(TEXT("DRAINING"), DrainUntil, true);
	if (PoisonDps > 0.f) Add(FString::Printf(TEXT("POISON %.1f/s"), PoisonDps), PoisonUntil, false);
	Add(FString::Printf(TEXT("WEAKENED -%.0f%%"), WeakShare * 100.f), WeakUntil, false);
	Add(FString::Printf(TEXT("SLOWED -%.0f%%"), SlowMeShare * 100.f), SlowMeUntil, false);
	// (the third list: the block, a shrine's blessing, the slashes' holds on her)
	if (bBlocking && Generator) Out.Add(FString::Printf(TEXT("BLOCKING +%.0f%%|0.0|1"), Generator->BlockShare * 100.f));
	if (!BlessName.IsEmpty()) Add(BlessName.ToUpper(), BlessUntil, true);
	Add(FString::Printf(TEXT("HASTE +%.0f%%"), HasteShare * 100.f), HasteUntil, true);
	Add(FString::Printf(TEXT("EVASION %.0f%%"), SlashEvadeShare * 100.f), SlashEvadeUntil, true);
	Add(FString::Printf(TEXT("DEFLECT %.0f%%"), DeflectShare * 100.f), DeflectUntil, true);
	if (bSlashShieldUp) Out.Add(TEXT("CRYSTAL SHIELD|0.0|1"));
	return Out;
}

void URDCombatComponent::ApplyMonsterAbility(ERDMonsterAbility Ability, float Power, float Blow)
{
	if (bDead || Ability == ERDMonsterAbility::None || Power <= 0.f || !GetWorld()) return;
	const float Now = GetWorld()->GetTimeSeconds();
	if (Now < DispelUntil) return;                // (Dispel Hex: none takes hold)
	switch (Ability)
	{
	case ERDMonsterAbility::Poison:
		if (Now >= PoisonUntil) SetMessage(TEXT("You are poisoned"));
		PoisonDps = FMath::Max(Now < PoisonUntil ? PoisonDps : 0.f, Blow * 0.10f * Power);
		PoisonUntil = FMath::Max(PoisonUntil, Now + 3.f + Power);
		break;
	case ERDMonsterAbility::Weaken:
		if (Now >= WeakUntil) SetMessage(TEXT("You are weakened: your blows and spells do less"));
		WeakShare = FMath::Clamp(0.15f * Power, 0.f, 0.5f);
		WeakUntil = FMath::Max(WeakUntil, Now + 4.f + Power);
		break;
	case ERDMonsterAbility::Slow:
		if (Now >= SlowMeUntil) SetMessage(TEXT("You are slowed"));
		SlowMeShare = FMath::Clamp(0.2f * Power, 0.f, 0.6f);
		SlowMeUntil = FMath::Max(SlowMeUntil, Now + 2.5f + 0.5f * Power);
		UpdateWalkSpeed();
		break;
	default: break;
	}
}

void URDCombatComponent::ClearAfflictions()
{
	PoisonDps = 0.f; PoisonUntil = WeakUntil = SlowMeUntil = -100.f; PoisonAcc = 0.f; WeakShare = SlowMeShare = 0.f;
	if (bSlowMeOn) { bSlowMeOn = false; UpdateWalkSpeed(); }
}

// ------------------------------------------------------------------------------------------------ rings
float URDCombatComponent::GetRingBonus(ERDRingKind Kind) const
{
	const FName* N = WornRings.Find((uint8)Kind);
	const int32 Ix = N && Generator ? Generator->FindItem(*N) : -1;
	return Ix >= 0 ? Generator->Items[Ix].Amount : 0.f;
}

void URDCombatComponent::UpdateMaxima()
{
	if (!Generator) return;
	const float OldH = MaxHealth, OldM = MaxMana;
	MaxHealth = FMath::Max(1.f, Generator->PlayerMaxHealth * (1.f + GetRingBonus(ERDRingKind::Health)));
	MaxMana = FMath::Max(Generator->PlayerMaxMana * (1.f + GetRingBonus(ERDRingKind::Magic)), GetTomeMana());
	// (a ring put on adds its part to what she has; one taken off takes no more than it gave)
	if (MaxHealth > OldH) Health += MaxHealth - OldH;
	if (MaxMana > OldM) Mana += MaxMana - OldM;
	Health = FMath::Min(Health, MaxHealth); Mana = FMath::Min(Mana, MaxMana);
	UpdateManaShares();
}

bool URDCombatComponent::WearRing(FName Item)
{
	const int32 Ix = Generator && !bDead ? Generator->FindItem(Item) : -1;
	if (Ix < 0 || Generator->Items[Ix].Kind != ERDItemKind::Ring || GetItemCount(Item) <= 0) return false;
	const FRDItemDef& It = Generator->Items[Ix];
	static const TCHAR* What[3] = { TEXT("mana"), TEXT("hit points"), TEXT("ranged damage") };
	const int32 K = (int32)It.RingKind;
	if (GetWornRing(It.RingKind) == Item)
	{
		WornRings.Remove((uint8)It.RingKind); UpdateMaxima();
		SetMessage(FString::Printf(TEXT("You take off the %s"), *RDSpLower(Item)));
		PlayUiSound(TEXT("Player.Inventory"), TEXT("Player.Inventory"));
		return true;
	}
	if (!Generator->HeroWearsRing(It.RingKind))
	{
		SetMessage(FString::Printf(TEXT("The %s cannot wear the %s: it gives %s"), *Generator->PlayerTitle.ToLower(), *RDSpLower(Item), What[K]));
		return false;
	}
	WornRings.Add((uint8)It.RingKind, Item); UpdateMaxima();
	SetMessage(FString::Printf(TEXT("You put on the %s:  +%.0f%% %s"), *RDSpLower(Item), It.Amount * 100.f, What[K]));
	PlayUiSound(TEXT("Player.Inventory"), TEXT("Player.Inventory"));
	return true;
}

// ------------------------------------------------------------------------------------------------ the spells' pieces
UFXSystemComponent* URDCombatComponent::SpawnSpellFx(UFXSystemAsset* Asset, const FVector& At, const FRotator& Rot, float Scale, const FRDSpellDef* S, USceneComponent* AttachTo, FName Socket)
{
	if (!Asset) return nullptr;
	UNiagaraSystem* Ns = Cast<UNiagaraSystem>(Asset);
	if (!Ns) return SpawnFx(Asset, At, Rot, Scale, AttachTo, Socket);
	// (the packs size their effects with User.Scale and colour them with User.Color01-03: set before it starts)
	UNiagaraComponent* C = AttachTo
		? UNiagaraFunctionLibrary::SpawnSystemAttached(Ns, AttachTo, Socket, At, Rot, FVector(1.f), EAttachLocation::KeepRelativeOffset, true, ENCPoolMethod::None, false)
		: UNiagaraFunctionLibrary::SpawnSystemAtLocation(this, Ns, At, Rot, FVector(1.f), true, false, ENCPoolMethod::None, false);
	if (!C) return nullptr;
	C->SetVariableFloat(TEXT("User.Scale"), Scale);
	if (S && S->bUseColors)
		for (int32 K = 0; K < S->Colors.Num() && K < 3; ++K) C->SetVariableLinearColor(FName(*FString::Printf(TEXT("User.Color%02d"), K + 1)), S->Colors[K]);
	if (S && S->Duration > 0.f) C->SetVariableFloat(TEXT("User.Duration"), S->Duration);
	C->Activate(true);
	SpellComps.Add(C);
	return C;
}

void URDCombatComponent::SetAura(ERDSpellKind Kind, const FRDSpellDef* S, bool bOn, float Seconds)
{
	if (TWeakObjectPtr<UFXSystemComponent>* Have = Auras.Find((uint8)Kind))
	{
		// (gone at once: a shield's particles live as long as its User.Duration says, and a plain Deactivate left the
		// mirror's hexagons on her seconds after it ended)
		if (UFXSystemComponent* F = Have->Get()) { F->DeactivateImmediate(); F->DestroyComponent(); }
		Auras.Remove((uint8)Kind);
	}
	if (!bOn || !S || !S->ShieldFx || !GetOwner()) return;
	// (on her: round her middle, it goes where she goes)
	if (UFXSystemComponent* C = SpawnSpellFx(S->ShieldFx, FVector::ZeroVector, FRotator::ZeroRotator, S->ShieldFxScale, S, GetOwner()->GetRootComponent()))
		Auras.Add((uint8)Kind, C);
}

FVector URDCombatComponent::SpellTargetPoint(float Reach) const
{
	const AActor* O = GetOwner();
	if (!O) return FVector::ZeroVector;
	const float Feet = O->GetSimpleCollisionHalfHeight();
	if (const ARDMonster* T = LastTarget.Get())
		if (!T->IsDead()) return T->GetActorLocation() - FVector(0, 0, T->GetCapsuleComponent()->GetScaledCapsuleHalfHeight() - 5.f);
	// (no one in front of her: a point ahead, short of the first wall)
	const FVector From = O->GetActorLocation(), To = From + O->GetActorForwardVector() * FMath::Min(Reach, 700.f);
	FHitResult H;
	FCollisionQueryParams Q(SCENE_QUERY_STAT(RDSpellPoint), false, O);
	const FVector End = GetWorld()->LineTraceSingleByChannel(H, From, To, ECC_Visibility, Q) ? H.ImpactPoint - O->GetActorForwardVector() * 60.f : To;
	return End - FVector(0, 0, Feet - 5.f);
}

void URDCombatComponent::SpellHurt(ARDMonster* Mo, float Dmg, const FVector& Where, bool bWound)
{
	if (!Mo || Mo->IsDead() || Dmg <= 0.f || !Generator) return;
	const bool bKilled = Mo->ApplyDamageEx(Dmg, GetOwner(), &Where, bWound, bWound);
	Generator->AddHitText(Mo->GetActorLocation() + FVector(0, 0, Mo->GetCapsuleComponent()->GetScaledCapsuleHalfHeight()), Dmg, false);
	CountSpellDamage(Dmg);
	if (bKilled) ++Kills;
}

void URDCombatComponent::LoseHealth(float Amount)
{
	if (bDead || Amount <= 0.f) return;
	Health -= Amount; DamageTaken += Amount;
	if (Health > 0.f) return;
	const float Now = GetWorld()->GetTimeSeconds();
	if (Now < PactUntil) { Health = FMath::Max(1.f, MaxHealth * PactShare); PactUntil = Now; ++PactSaves; SetAura(ERDSpellKind::Pact, nullptr, false); SetMessage(TEXT("Your pact holds: you rise again")); return; }
	Fall();
}

void URDCombatComponent::LaunchSpellBolt(int32 Spell, const FVector& From, ARDMonster* Target, float Dmg, int32 ChainLeft, const TArray<TWeakObjectPtr<ARDMonster>>& Done)
{
	if (!Generator || !Generator->Spells.IsValidIndex(Spell) || !Target) return;
	const FRDSpellDef& S = Generator->Spells[Spell];
	FBolt B;
	B.At = From; B.Weapon = -1; B.Spell = Spell; B.Dmg = Dmg; B.ChainLeft = ChainLeft; B.Done = Done; B.Target = Target;
	B.Vel = (Target->GetActorLocation() - From).GetSafeNormal() * S.BoltSpeed * 1.8f;
	B.Fx = SpawnSpellFx(S.BoltFx, B.At, B.Vel.Rotation(), S.BoltFxScale, &S);
	B.Light = MakeLight(B.At, S.LightColor, S.LightIntensity, 700.f);
	Bolts.Add(B);
}

void URDCombatComponent::LaunchGoalBolt(int32 Spell, const FVector& From, const FVector& To, float Speed, bool bWisp)
{
	if (!Generator || !Generator->Spells.IsValidIndex(Spell)) return;
	const FRDSpellDef& S = Generator->Spells[Spell];
	FBolt B;
	B.At = From; B.Weapon = -1; B.Spell = Spell; B.bGoal = true; B.bWisp = bWisp; B.Goal = To;
	B.Vel = (To - From).GetSafeNormal() * Speed;
	B.Fx = SpawnSpellFx(S.BoltFx, B.At, B.Vel.Rotation(), S.BoltFxScale * (bWisp ? 0.6f : 1.f), &S);
	if (!bWisp) B.Light = MakeLight(B.At, S.LightColor, S.LightIntensity, 900.f);
	Bolts.Add(B);
}

void URDCombatComponent::SpellPierce(FBolt& B, ARDMonster* Mo, const FVector& At)
{
	const FRDSpellDef* S = Generator && Generator->Spells.IsValidIndex(B.Spell) ? &Generator->Spells[B.Spell] : nullptr;
	if (!S || !Mo) return;
	const float Dmg = B.Dmg >= 0.f ? B.Dmg : (Generator->Weapons.IsValidIndex(B.Weapon) ? GetDamageOf(B.Weapon) : S->Damage);
	SpellHurt(Mo, Dmg, At, true);
	if (S->Slow > 0.f) Mo->SlowFor(S->Slow, S->Duration > 0.f ? S->Duration : 2.f);
	SpawnSpellFx(S->ImpactFx, At, B.Vel.Rotation(), S->ImpactFxScale * 0.7f, S);
	Generator->PlaySoundAt(FName(*FString::Printf(TEXT("Player.Hit.%s"), *S->SoundKey.ToString())), At);
	++BoltsOnMonsters;
}

void URDCombatComponent::SpellBurst(FBolt& B, const FVector& At, ARDMonster* Direct)
{
	const FRDSpellDef* S = Generator && Generator->Spells.IsValidIndex(B.Spell) ? &Generator->Spells[B.Spell] : nullptr;
	EndBoltFx(B);
	if (!S) { if (UPointLightComponent* L = B.Light.Get()) L->DestroyComponent(); return; }
	const float Dmg = B.Dmg >= 0.f ? B.Dmg : (Generator->Weapons.IsValidIndex(B.Weapon) ? GetDamageOf(B.Weapon) : S->Damage);
	UFXSystemComponent* HitFx = SpawnSpellFx(S->ImpactFx, At, B.Vel.IsNearlyZero() ? FRotator::ZeroRotator : B.Vel.Rotation(), S->ImpactFxScale, S);
	// (a chi bolt's hit (the Martial Artist's: a range of its own) gone for good after its BurstLife (2 s when none); the Mage's
	// are left as they were)
	if (HitFx && Generator->Weapons.IsValidIndex(B.Weapon) && Generator->Weapons[B.Weapon].BoltRange > 0.f)
		TimedFx.Add({ HitFx, Generator->Weapons[B.Weapon].BurstLife > 0.f ? Generator->Weapons[B.Weapon].BurstLife : 2.f, true });
	Generator->PlaySoundAt(FName(*FString::Printf(TEXT("Player.Hit.%s"), *S->SoundKey.ToString())), At);
	if (UPointLightComponent* L = B.Light.Get()) { L->SetWorldLocation(At); Flashes.Add({ L, 0.f, S->LightIntensity * 3.f }); }
	// (what stays on a monster it struck: a slow, a burn that gives some back to her)
	auto Hold = [&](ARDMonster* Mo)
	{
		if (S->Slow > 0.f) Mo->SlowFor(S->Slow, S->Duration > 0.f ? S->Duration : 2.f);
		if (S->Burn > 0.f) { const float Sec = FMath::Max(S->Duration, 0.5f); Mo->AddBurn(Dmg * S->Burn / Sec, Sec, S->Drain); }
	};
	auto Near = [&](const FVector& C, float R, TFunctionRef<void(ARDMonster*)> Do)
	{
		for (ARDMonster* Mo : Generator->GetMonsters())
		{
			if (!Mo || Mo->IsDead() || Mo == Direct) continue;
			const FVector P = Mo->GetActorLocation();
			if (FVector::Dist2D(P, C) - Mo->GetCapsuleComponent()->GetScaledCapsuleRadius() > R) continue;
			if (FMath::Abs(P.Z - C.Z) > Mo->GetCapsuleComponent()->GetScaledCapsuleHalfHeight() + 120.f) continue;
			Do(Mo);
		}
	};
	if (B.bGoal)
	{
		// (a meteor lands: everyone within its splash)
		Near(At, S->Splash, [&](ARDMonster* Mo) { SpellHurt(Mo, Dmg, Mo->GetActorLocation(), true); Hold(Mo); });
	}
	else
	{
		if (Direct && !Direct->IsDead()) { SpellHurt(Direct, Dmg, At, true); Hold(Direct); }
		if (S->Radius > 0.f && S->Count <= 0)
			Near(At, S->Radius, [&](ARDMonster* Mo) { SpellHurt(Mo, Dmg, Mo->GetActorLocation(), true); Hold(Mo); });     // (a fireball: all of it)
		else if (S->Splash > 0.f && S->Count <= 0)
			Near(At, S->Splash, [&](ARDMonster* Mo) { SpellHurt(Mo, Dmg * 0.5f, Mo->GetActorLocation(), true); });
		// (chain lightning: on to the nearest one it has not struck yet, if she could see it)
		if (B.ChainLeft > 0 && Direct)
		{
			TArray<TWeakObjectPtr<ARDMonster>> Done = B.Done; Done.Add(Direct);
			ARDMonster* Next = nullptr; float Best = S->Radius;
			for (ARDMonster* Mo : Generator->GetMonsters())
			{
				if (!Mo || Mo->IsDead() || Done.Contains(Mo)) continue;
				const float D = FVector::Dist(Mo->GetActorLocation(), Direct->GetActorLocation());
				if (D < Best && CanSee(At, Mo)) { Best = D; Next = Mo; }
			}
			if (Next) LaunchSpellBolt(B.Spell, At, Next, Dmg * 0.85f, B.ChainLeft - 1, Done);
		}
	}
	(Direct ? BoltsOnMonsters : BoltsElsewhere)++;
	LastBurstAt = At; LastBoltFlown = B.Flown;
}

bool URDCombatComponent::CastSpellNow(int32 Index, ARDMonster* Target)
{
	const FRDSpellDef* S = SpellOf(Index);
	if (!S || bDead) return false;
	LastTarget = Target ? Target : PickTarget(S->Reach, true);
	const float SavedT = AttackTime; const int32 SavedI = AttackIndex;
	AttackIndex = Index; AttackTime = 0.f;
	if (S->Kind == ERDSpellKind::Bolt) LaunchBolt(); else ReleaseSpell(Index);
	AttackTime = SavedT; AttackIndex = SavedI;
	if (S->Kind == ERDSpellKind::Bolt) SpellsReleased.FindOrAdd(S->Name)++;
	return true;
}

// ------------------------------------------------------------------------------------------------ the release
void URDCombatComponent::ReleaseSpell(int32 Wi)
{
	const FRDSpellDef* S = SpellOf(Wi);
	AActor* O = GetOwner();
	USkeletalMeshComponent* M = Body();
	if (!S || !O || !Generator) return;
	StopCharge();
	const float Now = GetWorld()->GetTimeSeconds();
	const FVector L = O->GetActorLocation(), Fw = O->GetActorForwardVector();
	const FVector Feet = L - FVector(0, 0, O->GetSimpleCollisionHalfHeight() - 5.f);
	const float Dmg = GetDamageOf(Wi);
	const int32 Si = Generator->Weapons[Wi].SpellIndex;
	const FVector Hand = M ? M->GetSocketLocation(Generator->Weapons[Wi].SpellBone) : L;
	SpellsReleased.FindOrAdd(S->Name)++;
	Generator->PlaySoundAt(FName(*FString::Printf(TEXT("Player.Cast.%s"), *S->SoundKey.ToString())), Hand);
	auto Around = [&](const FVector& C, float R, TFunctionRef<void(ARDMonster*)> Do)
	{
		for (ARDMonster* Mo : Generator->GetMonsters())
		{
			if (!Mo || Mo->IsDead()) continue;
			const FVector P = Mo->GetActorLocation();
			if (FVector::Dist2D(P, C) - Mo->GetCapsuleComponent()->GetScaledCapsuleRadius() > R || FMath::Abs(P.Z - C.Z) > 320.f) continue;
			Do(Mo);
		}
	};
	auto AddArea = [&](ERDSpellKind Kind, const FVector& At, float Seconds, float Dps, float Slow, int32 Strikes, bool bLoopFx)
	{
		FArea Ar;
		Ar.Kind = Kind; Ar.At = At; Ar.Radius = S->Radius; Ar.Left = Seconds; Ar.Dps = Dps; Ar.Slow = Slow; Ar.Every = S->AreaEvery; Ar.Spell = Si; Ar.Strikes = Strikes;
		// (a looping effect stays the whole time; a one-shot one is fired again every AreaEvery seconds)
		if (bLoopFx || S->AreaEvery <= 0.f) Ar.Fx = SpawnSpellFx(S->AreaFx, At, FRotator::ZeroRotator, S->AreaFxScale, S);
		Areas.Add(Ar);
	};
	switch (S->Kind)
	{
	case ERDSpellKind::Lash:
	{
		// (an arc in front of her: hurt and pushed away)
		SpawnSpellFx(S->ImpactFx, L + Fw * 90.f + FVector(0, 0, 20.f), Fw.Rotation(), S->ImpactFxScale, S);
		const float MinCos = FMath::Cos(FMath::DegreesToRadians(FMath::Max(S->Radius, 30.f) * 0.5f));
		Around(L, S->Reach, [&](ARDMonster* Mo)
		{
			const FVector D = (Mo->GetActorLocation() - L) * FVector(1, 1, 0);
			if (D.Size() > 60.f && FVector::DotProduct(D.GetSafeNormal(), Fw) < MinCos) return;
			SpellHurt(Mo, Dmg, Mo->GetActorLocation(), true);
			if (!Mo->IsDead()) Mo->Knock(D.GetSafeNormal() * S->Amount);
		});
		break;
	}
	case ERDSpellKind::Ward:
		WardUntil = Now + S->Duration; WardHits = S->Amount > 0.f ? 0 : FMath::Max(S->Count, 1); WardPool = S->Amount > 0.f ? S->Amount * MaxHealth : 0.f;
		SetAura(ERDSpellKind::Ward, S, true);
		break;
	case ERDSpellKind::Skin:
		SkinUntil = Now + S->Duration; SkinShare = S->Amount;
		SetAura(ERDSpellKind::Skin, S, true);
		break;
	case ERDSpellKind::Dispel:
		ClearAfflictions(); DispelUntil = Now + FMath::Max(S->Duration, 2.f);
		SpawnSpellFx(S->ImpactFx, L, FRotator::ZeroRotator, S->ImpactFxScale, S);
		SetAura(ERDSpellKind::Dispel, S, true);
		break;
	case ERDSpellKind::Drain:
	{
		ARDMonster* T = LastTarget.Get();
		if (!T || T->IsDead()) T = PickTarget(S->Reach, true);
		if (!T) { SetMessage(TEXT("Nothing in front of you to drain")); break; }
		DrainTarget = T; DrainUntil = Now + S->Duration; DrainDps = Dmg; DrainShare = S->Drain; DrainSpell = Si; DrainTick = DrainWisp = 0.f;
		SpawnSpellFx(S->ImpactFx, T->GetActorLocation(), FRotator::ZeroRotator, S->ImpactFxScale, S);
		break;
	}
	case ERDSpellKind::Cloud:
	{
		const FVector At = SpellTargetPoint(S->Reach);
		SpawnSpellFx(S->ImpactFx, At, FRotator::ZeroRotator, S->ImpactFxScale, S);
		AddArea(ERDSpellKind::Cloud, At, S->Duration, Dmg, S->Slow, 0, false);
		break;
	}
	case ERDSpellKind::Veil:
		VeilUntil = Now + S->Duration; VeilEvade = S->Amount;
		SetAura(ERDSpellKind::Veil, S, true);
		SpawnSpellFx(S->ImpactFx, L, FRotator::ZeroRotator, S->ImpactFxScale, S);
		break;
	case ERDSpellKind::Curse:
	{
		const FVector At = SpellTargetPoint(S->Reach);
		SpawnSpellFx(S->ImpactFx, At, FRotator::ZeroRotator, S->ImpactFxScale, S);
		Around(At, S->Radius, [&](ARDMonster* Mo)
		{
			Mo->CurseFor(S->Amount, S->Duration);
			// (the curse shows on it while it lasts)
			if (UFXSystemComponent* C = SpawnSpellFx(S->AreaFx, FVector::ZeroVector, FRotator::ZeroRotator, S->AreaFxScale, S, Mo->GetRootComponent())) TimedFx.Add({ C, S->Duration, true });
		});
		break;
	}
	case ERDSpellKind::Raise:
	{
		const TArray<ARDMonster*> Dead = Generator->GetCorpsesNear(L, S->Reach);
		int32 N = 0;
		for (ARDMonster* C : Dead)
		{
			if (N >= FMath::Max(S->Count, 1)) break;
			const FVector At = C->GetActorLocation();
			if (Generator->RaiseAlly(C, S->Duration, S->Amount > 0.f ? S->Amount : 0.6f))
			{
				++N;
				SpawnSpellFx(S->ImpactFx, At, FRotator::ZeroRotator, S->ImpactFxScale, S);
				SpawnSpellFx(S->AreaFx, At, FRotator::ZeroRotator, S->AreaFxScale, S);
			}
		}
		SetMessage(N > 0 ? FString::Printf(TEXT("%d of the dead rise to fight for you"), N) : FString(TEXT("No dead near you to raise")));
		break;
	}
	case ERDSpellKind::Rune:
		RuneAt = Feet; RuneRadius = S->Radius; RuneUntil = Now + S->Duration; RuneShare = S->Amount;
		SpawnSpellFx(S->ImpactFx, Feet, FRotator::ZeroRotator, S->ImpactFxScale, S);
		AddArea(ERDSpellKind::Rune, Feet, S->Duration, 0.f, 0.f, 0, true);
		break;
	case ERDSpellKind::Nova:
	{
		// (it costs her: a share of her hit points, never the last of them)
		const float Price = FMath::Min(Health * S->Amount, Health - 1.f);
		if (Price > 0.f) { Health -= Price; DamageTaken += Price; Generator->AddHitText(L + FVector(0, 0, 90.f), Price, true); }
		SpawnSpellFx(S->ImpactFx, L, FRotator::ZeroRotator, S->ImpactFxScale, S);
		if (S->ShieldFx) SpawnSpellFx(S->ShieldFx, L, FRotator::ZeroRotator, S->ShieldFxScale, S);
		Around(L, S->Radius, [&](ARDMonster* Mo) { SpellHurt(Mo, Dmg, Mo->GetActorLocation(), true); });
		break;
	}
	case ERDSpellKind::Mirror:
		MirrorUntil = Now + S->Duration; MirrorShare = S->Amount > 0.f ? S->Amount : 1.f;
		SetAura(ERDSpellKind::Mirror, S, true);
		break;
	case ERDSpellKind::Rend:
	{
		ARDMonster* T = LastTarget.Get();
		if (!T || T->IsDead()) T = PickTarget(S->Reach, true);
		if (T) { SpawnSpellFx(S->ImpactFx, T->GetActorLocation(), FRotator::ZeroRotator, S->ImpactFxScale, S); SpellHurt(T, Dmg, T->GetActorLocation(), true); }
		break;
	}
	case ERDSpellKind::Corpse:
	{
		const FVector At = SpellTargetPoint(S->Reach);
		// (the corpses by the monster she faces; none there: the ones round her)
		TArray<ARDMonster*> Dead = Generator->GetCorpsesNear(At, FMath::Max(S->Splash, 600.f));
		if (Dead.Num() == 0) Dead = Generator->GetCorpsesNear(L, S->Reach);
		int32 N = 0;
		for (ARDMonster* C : Dead)
		{
			if (N >= FMath::Max(S->Count, 1)) break;
			const FVector P = C->GetActorLocation();
			SpawnSpellFx(S->ImpactFx, P, FRotator::ZeroRotator, S->ImpactFxScale, S);
			if (URDBloodComponent* Bl = Generator->GetBlood()) Bl->Burst(P + FVector(0, 0, 30.f), FVector(0, 0, 1.f), 1.f);
			Around(P, S->Radius, [&](ARDMonster* Mo) { SpellHurt(Mo, Dmg, Mo->GetActorLocation(), true); });
			Generator->ConsumeCorpse(C);
			++N;
		}
		if (N == 0) SetMessage(TEXT("No corpses there to burst"));
		break;
	}
	case ERDSpellKind::Pillar:
	{
		const FVector At = SpellTargetPoint(S->Reach);
		SpawnSpellFx(S->ImpactFx, At, FRotator::ZeroRotator, S->ImpactFxScale, S);
		Around(At, S->Radius * 0.6f, [&](ARDMonster* Mo) { SpellHurt(Mo, Dmg, Mo->GetActorLocation(), true); });
		AddArea(ERDSpellKind::Pillar, At, S->Duration, Dmg * FMath::Max(S->Burn, 0.1f), 0.f, 0, false);
		break;
	}
	case ERDSpellKind::Rift:
	{
		const FVector At = SpellTargetPoint(S->Reach);
		SpawnSpellFx(S->ImpactFx, At + FVector(0, 0, 80.f), FRotator::ZeroRotator, S->ImpactFxScale, S);
		AddArea(ERDSpellKind::Rift, At, S->Duration, Dmg, 0.f, 0, false);
		break;
	}
	case ERDSpellKind::Pact:
		PactUntil = Now + S->Duration; PactShare = S->Amount > 0.f ? S->Amount : 0.4f;
		SetAura(ERDSpellKind::Pact, S, true);
		break;
	case ERDSpellKind::Knight:
	{
		FVector At = L + Fw * 220.f;
		FHitResult H; FCollisionQueryParams Q(SCENE_QUERY_STAT(RDKnight), false, O);
		if (GetWorld()->LineTraceSingleByChannel(H, L, At, ECC_Visibility, Q)) At = L + Fw * FMath::Max(H.Distance - 80.f, 0.f);
		ARDMonster* K = Generator->SummonAlly(Generator->KnightMonster, At - FVector(0, 0, O->GetSimpleCollisionHalfHeight()), Generator->KnightStrength);
		if (K)
		{
			SpawnSpellFx(S->ImpactFx, K->GetActorLocation(), FRotator::ZeroRotator, S->ImpactFxScale, S);
			SpawnSpellFx(S->AreaFx, At - FVector(0, 0, O->GetSimpleCollisionHalfHeight() - 5.f), FRotator::ZeroRotator, S->AreaFxScale, S);
			SetMessage(FString::Printf(TEXT("%s comes to your side"), *(K->Title.IsEmpty() ? K->MonsterName.ToString() : K->Title)));
		}
		break;
	}
	case ERDSpellKind::Summon:
	{
		// (mistward, the Summoner: one of its kind in front of her, beside the ones she leads already)
		const int32 Have = Generator->CountSummoned(S->Name);
		const FVector Rt = O->GetActorRightVector();
		const float Side = (Have % 2 == 0 ? 1.f : -1.f) * 70.f * ((Have + 1) / 2);
		// (in front of her, else to a side, else behind: the first way with room for it; facing a wall from 60 cm the
		// point came back to her own place, inside her capsule (the PR review's find))
		FCollisionQueryParams Q(SCENE_QUERY_STAT(RDSummon), false, O);
		const FVector Ways[4] = { Fw * 230.f + Rt * Side, Rt * 230.f, Rt * -230.f, Fw * -230.f };
		FVector At = L + Ways[0]; float Room = -1.f;
		for (const FVector& Wy : Ways)
		{
			FHitResult H;
			const float D = GetWorld()->LineTraceSingleByChannel(H, L, L + Wy, ECC_Visibility, Q) ? H.Distance - 80.f : Wy.Size();
			if (D > Room) { Room = D; At = L + Wy.GetSafeNormal() * FMath::Max(D, 0.f); }
			if (D >= 120.f) break;
		}
		// (mistward4: a spot nobody stands on: the first of each spell came to the same place in front of her, the second of
		// each to the same place beside it)
		if (Generator->bAllySpacing)
		{
			const FRDMonsterDef* Kd = Generator->Monsters.FindByPredicate([S](const FRDMonsterDef& D) { return D.Name == S->SummonKind; });
			Generator->FindAllySpot(L, Fw, Kd ? Kd->CapsuleRadius : 45.f, O, At);
		}
		ARDMonster* K = Generator->SummonKindAlly(S->SummonKind, At - FVector(0, 0, O->GetSimpleCollisionHalfHeight()), S->Name);
		if (K)
		{
			++Summoned;
			SpawnSpellFx(S->ImpactFx, K->GetActorLocation(), FRotator::ZeroRotator, S->ImpactFxScale, S);
			SpawnSpellFx(S->AreaFx, At - FVector(0, 0, O->GetSimpleCollisionHalfHeight() - 5.f), FRotator::ZeroRotator, S->AreaFxScale, S);
			SetMessage(FString::Printf(TEXT("%s answers your call  (%d of %d)"), *(K->Title.IsEmpty() ? K->MonsterName.ToString() : K->Title), Generator->CountSummoned(S->Name), FMath::Max(S->Count, 1)));
		}
		else
		{
			// (nothing came (no set under the spot, no such kind): what the cast took is given back (the PR review's find): its
			// mana, its cooldown, the scroll it was read from)
			const FRDWeaponDef& Wd = Generator->Weapons[Wi];
			if (!Generator->bInfiniteMana) Mana = FMath::Min(MaxMana, Mana + Wd.ManaCost);
			ReadyAt.Remove(Wd.Name);
			// (the scroll that was read, by its own name (not one rebuilt from the spell's): the PR review's find)
			if (Wd.bScroll && !ScrollItemRead.IsNone()) { AddItem(ScrollItemRead, 1); --ScrollsRead; ScrollItemRead = NAME_None; }
			SetMessage(FString::Printf(TEXT("Nothing answers %s here: what it took is given back"), *S->Name.ToString()));
		}
		break;
	}
	case ERDSpellKind::Meteors:
	{
		const FVector At = SpellTargetPoint(S->Reach);
		AddArea(ERDSpellKind::Meteors, At, S->Duration + 2.5f, 0.f, 0.f, FMath::Max(S->Count, 1), false);
		break;
	}
	case ERDSpellKind::Sanctum:
		SanctumAt = Feet; SanctumRadius = S->Radius; SanctumUntil = Now + S->Duration;
		SpawnSpellFx(S->ImpactFx, Feet, FRotator::ZeroRotator, S->ImpactFxScale, S);
		if (S->ShieldFx) { FArea Ar; Ar.Kind = ERDSpellKind::Sanctum; Ar.At = Feet; Ar.Radius = S->Radius; Ar.Left = S->Duration; Ar.Spell = Si; Ar.Fx = SpawnSpellFx(S->ShieldFx, Feet + FVector(0, 0, 90.f), FRotator::ZeroRotator, S->ShieldFxScale, S); Areas.Add(Ar); }
		break;
	case ERDSpellKind::Apocalypse:
	{
		SpawnSpellFx(S->CastFx, L, FRotator::ZeroRotator, S->CastFxScale, S);
		SpawnSpellFx(S->ImpactFx, Feet, FRotator::ZeroRotator, S->ImpactFxScale, S);
		const FVector Eye = L + FVector(0, 0, 50.f);
		Around(L, S->Reach, [&](ARDMonster* Mo)
		{
			if (!CanSee(Eye, Mo)) return;
			SpawnSpellFx(S->AreaFx, Mo->GetActorLocation(), FRotator::ZeroRotator, S->AreaFxScale, S);
			SpellHurt(Mo, Dmg, Mo->GetActorLocation(), true);
		});
		break;
	}
	default:
		break;
	}
	UE_LOG(LogTemp, Log, TEXT("RDSPELL %s released (%d)"), *S->Name.ToString(), SpellsReleased.FindRef(S->Name));
}

// ------------------------------------------------------------------------------------------------ what lasts
void URDCombatComponent::TickSpells(float Dt, float Now)
{
	if (!Generator) return;
	const AActor* O = GetOwner();
	// poison, and her slowness coming and going
	if (PoisonDps > 0.f && Now < PoisonUntil && !bDead)
	{
		PoisonAcc += PoisonDps * Dt;
		if (PoisonAcc >= 2.f) { if (O) Generator->AddHitText(O->GetActorLocation() + FVector(0, 0, 90.f), PoisonAcc, true); LoseHealth(PoisonAcc); PoisonAcc = 0.f; }
	}
	else if (Now >= PoisonUntil) { PoisonDps = 0.f; PoisonAcc = 0.f; }
	const bool bSlowNow = GetSlowness() > 0.f;
	if (bSlowNow != bSlowMeOn) { bSlowMeOn = bSlowNow; UpdateWalkSpeed(); }
	// the shields on her end
	auto Expire = [&](ERDSpellKind K, float Until) { if (Now >= Until && Auras.Contains((uint8)K)) SetAura(K, nullptr, false); };
	Expire(ERDSpellKind::Ward, WardUntil); Expire(ERDSpellKind::Skin, SkinUntil); Expire(ERDSpellKind::Veil, VeilUntil);
	Expire(ERDSpellKind::Mirror, MirrorUntil); Expire(ERDSpellKind::Pact, PactUntil); Expire(ERDSpellKind::Dispel, DispelUntil);
	// the drain: hurt a few times a second, part of it back to her, a wisp flying back to her hand
	if (ARDMonster* T = DrainTarget.Get())
	{
		const FRDSpellDef* S = Generator->Spells.IsValidIndex(DrainSpell) ? &Generator->Spells[DrainSpell] : nullptr;
		if (!O || bDead || Now >= DrainUntil || T->IsDead() || !S || FVector::Dist(T->GetActorLocation(), O->GetActorLocation()) > S->Reach + 400.f) DrainTarget = nullptr;
		else
		{
			if ((DrainTick -= Dt) <= 0.f)
			{
				DrainTick = 0.25f;
				const float D = DrainDps * 0.25f;
				SpellHurt(T, D, T->GetActorLocation(), false);
				HealBy(D * DrainShare);
			}
			if ((DrainWisp -= Dt) <= 0.f)
			{
				DrainWisp = 0.3f;
				LaunchGoalBolt(DrainSpell, T->GetActorLocation() + FVector(0, 0, 40.f), O->GetActorLocation() + FVector(0, 0, 40.f), 1100.f, true);
			}
		}
	}
	// the areas: clouds, burning ground, rifts, meteor storms, zones
	for (int32 I = Areas.Num() - 1; I >= 0; --I)
	{
		FArea& Ar = Areas[I];
		const FRDSpellDef* S = Generator->Spells.IsValidIndex(Ar.Spell) ? &Generator->Spells[Ar.Spell] : nullptr;
		Ar.Left -= Dt;
		if (!S || (Ar.Left <= 0.f && Ar.Strikes <= 0))
		{
			if (UFXSystemComponent* F = Ar.Fx.Get()) { F->DeactivateImmediate(); F->DestroyComponent(); }
			Areas.RemoveAt(I); continue;
		}
		if (Ar.Every > 0.f && S->AreaFx && Ar.Kind != ERDSpellKind::Meteors && (Ar.FxTimer -= Dt) <= 0.f)
		{
			Ar.FxTimer = Ar.Every;
			const FVector P = Ar.At + FVector(SpellR.FRandRange(-0.6f, 0.6f) * Ar.Radius, SpellR.FRandRange(-0.6f, 0.6f) * Ar.Radius, 0.f);
			SpawnSpellFx(S->AreaFx, P, FRotator::ZeroRotator, S->AreaFxScale, S);
		}
		if (Ar.Kind == ERDSpellKind::Rift)
			for (ARDMonster* Mo : Generator->GetMonsters())
				if (Mo && !Mo->IsDead() && FVector::Dist2D(Mo->GetActorLocation(), Ar.At) < Ar.Radius) Mo->PullToward(Ar.At, 300.f, Dt);
		if (Ar.Dps > 0.f && (Ar.HurtTimer -= Dt) <= 0.f)
		{
			Ar.HurtTimer = 0.5f;
			for (ARDMonster* Mo : Generator->GetMonsters())
			{
				if (!Mo || Mo->IsDead()) continue;
				if (FVector::Dist2D(Mo->GetActorLocation(), Ar.At) - Mo->GetCapsuleComponent()->GetScaledCapsuleRadius() > Ar.Radius) continue;
				if (FMath::Abs(Mo->GetActorLocation().Z - Ar.At.Z) > 350.f) continue;
				SpellHurt(Mo, Ar.Dps * 0.5f, Mo->GetActorLocation(), false);
				if (Ar.Slow > 0.f) Mo->SlowFor(Ar.Slow, 1.f);
			}
		}
		if (Ar.Kind == ERDSpellKind::Meteors && Ar.Strikes > 0 && (Ar.StrikeTimer -= Dt) <= 0.f)
		{
			// (a meteor: from high up and a little aside, to a point of the area)
			Ar.StrikeTimer = FMath::Max(S->Duration, 0.5f) / FMath::Max(S->Count, 1);
			--Ar.Strikes;
			// (most fall on a monster in the area, the rest anywhere in it)
			TArray<ARDMonster*> In;
			for (ARDMonster* Mo : Generator->GetMonsters())
				if (Mo && !Mo->IsDead() && FVector::Dist2D(Mo->GetActorLocation(), Ar.At) < Ar.Radius) In.Add(Mo);
			FVector P = Ar.At + FVector(SpellR.FRandRange(-1.f, 1.f) * Ar.Radius, SpellR.FRandRange(-1.f, 1.f) * Ar.Radius, 0.f);
			if (In.Num() > 0 && SpellR.FRand() < 0.6f)
			{
				const ARDMonster* T = In[SpellR.RandRange(0, In.Num() - 1)];
				P = T->GetActorLocation() - FVector(0, 0, T->GetCapsuleComponent()->GetScaledCapsuleHalfHeight()) + FVector(SpellR.FRandRange(-90.f, 90.f), SpellR.FRandRange(-90.f, 90.f), 0.f);
			}
			LaunchGoalBolt(Ar.Spell, P + FVector(SpellR.FRandRange(-250.f, 250.f), SpellR.FRandRange(-250.f, 250.f), 950.f), P, 1900.f, false);
		}
	}
}
