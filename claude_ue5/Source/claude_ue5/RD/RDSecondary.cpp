// The heroes' secondary abilities (the user's list of 2026-11-08b, docs/improvements9.txt, its sixth phase: "earned in the
// wilderness by gathering materials and making Angel Tokens"; SourceArt/balance/secondary.json, 911). Each hero has five or six
// (the Rogue none: the list names none for her), six ranks each; an Angel Token used from the inventory raises one a rank (the
// first learns it). Active ones go on the quick bar ("@<Name>") with a cooldown, toggles go on and off there, passives always
// hold. The tokens are made at the anvil from the wilderness's Seraph Feathers (its monsters') and Hallowed Stones (its old
// places'). What each one does:
//   Warrior   ShieldBash (stuns all in front), Grapple (holds one: it still strikes), Trip (one prone: no move, no blow),
//             BlindingStrike (a blow that blinds), SweepingPush (all around pushed away), PullingAttack (one pulled to her)
//   Mage      ManaSwarm (seeking lights by her mana left), RechargeShield (blows become mana), AblationShield (layers peeled,
//             each striking back), MistyStep (a step away from her foes), SpellBoost1 / 2 (a chosen spell's damage, for good)
//   Warlock   ManaShield (her mana takes the blows), Curse / Blinding / BleedingShield (all within 2 m), MistyTransfer (one sent
//             far off), ManaBlade (a toggle: blows take mana for damage)
//   Summoner  MinionHealth, MinionDamage, Frenzy (passives on her summons), SummonHealing (heals them), SoulHarvest (deaths
//             near her heal and boost them)
//   Martial   WallRun (a leap up and across), FlashStep (a dash through foes), WaterWalk (over water), Parry (blows in front
//             turned aside, their makers staggered), IronSkin (blows weaker)
#include "RD/RDCombat.h"
#include "RD/RDDungeonGenerator.h"
#include "RD/RDMonster.h"
#include "RD/RDMistward.h"
#include "RD/RDWild.h"
#include "RD/RDGameInstance.h"
#include "GameFramework/Character.h"
#include "GameFramework/CharacterMovementComponent.h"
#include "GameFramework/RootMotionSource.h"
#include "Components/CapsuleComponent.h"
#include "Engine/World.h"
#include "CollisionQueryParams.h"

DEFINE_LOG_CATEGORY_STATIC(LogRDSecondary, Log, All);

namespace
{
	const FName RDSecShieldBash(TEXT("ShieldBash")), RDSecGrapple(TEXT("Grapple")), RDSecTrip(TEXT("Trip")), RDSecBlinding(TEXT("BlindingStrike")),
		RDSecPush(TEXT("SweepingPush")), RDSecPull(TEXT("PullingAttack")), RDSecSwarm(TEXT("ManaSwarm")), RDSecRecharge(TEXT("RechargeShield")),
		RDSecAblation(TEXT("AblationShield")), RDSecMistyStep(TEXT("MistyStep")), RDSecManaShield(TEXT("ManaShield")), RDSecCurseShield(TEXT("CurseShield")),
		RDSecBlindShield(TEXT("BlindingShield")), RDSecTransfer(TEXT("MistyTransfer")), RDSecBleedShield(TEXT("BleedingShield")), RDSecManaBlade(TEXT("ManaBlade")),
		RDSecMinionHealth(TEXT("MinionHealth")), RDSecMinionDamage(TEXT("MinionDamage")), RDSecHealing(TEXT("SummonHealing")), RDSecFrenzy(TEXT("Frenzy")),
		RDSecSoul(TEXT("SoulHarvest")), RDSecWallRun(TEXT("WallRun")), RDSecFlash(TEXT("FlashStep")), RDSecWater(TEXT("WaterWalk")), RDSecParry(TEXT("Parry")),
		RDSecIronSkin(TEXT("IronSkin"));
	const int32 RDSecMaxRank = 6;
	/** "{v}", "{v2}", "{s}" in a text by a rank's numbers */
	FString RDSecText(const FRDSecondaryDef& D, int32 Rank)
	{
		const int32 I = FMath::Clamp(Rank, 1, RDSecMaxRank) - 1;
		auto Num = [](const TArray<float>& A, int32 K) -> FString
		{
			if (!A.IsValidIndex(K)) return TEXT("?");
			const float V = A[K];
			return FMath::IsNearlyEqual(V, FMath::RoundToFloat(V)) ? FString::Printf(TEXT("%.0f"), V) : FString::Printf(TEXT("%.1f"), V);
		};
		FString T = D.Text;
		T.ReplaceInline(TEXT("{v2}"), *Num(D.Values2, I)); T.ReplaceInline(TEXT("{v}"), *Num(D.Values, I)); T.ReplaceInline(TEXT("{s}"), *Num(D.Seconds, I));
		if (D.Cooldowns.IsValidIndex(I) && D.Kind == ERDSecondaryKind::Active) T += FString::Printf(TEXT("  (every %s s)"), *Num(D.Cooldowns, I));
		return T;
	}
}

// ------------------------------------------------------------------------------------------------ ranks
const FRDSecondaryDef* URDCombatComponent::SecDef(FName Ability) const
{
	return Generator ? Generator->FindSecondary(Ability) : nullptr;
}

int32 URDCombatComponent::GetSecondaryRank(FName Ability) const
{
	const int32* R = SecondaryRanks.Find(Ability);
	return R ? *R : 0;
}

float URDCombatComponent::SecondaryValue(FName Ability, int32 Which) const
{
	const FRDSecondaryDef* D = SecDef(Ability);
	const int32 R = GetSecondaryRank(Ability);
	if (!D || R <= 0 || !Generator || D->Hero != Generator->CurrentHero) return 0.f;
	const TArray<float>& A = Which == 0 ? D->Values : Which == 1 ? D->Values2 : Which == 2 ? D->Seconds : D->Cooldowns;
	return A.Num() > 0 ? A[FMath::Clamp(R, 1, A.Num()) - 1] : 0.f;
}

bool URDCombatComponent::SetSecondaryRank(FName Ability, int32 Rank, FName Spell)
{
	const FRDSecondaryDef* D = SecDef(Ability);
	if (!D) return false;
	const int32 R = FMath::Clamp(Rank, 0, RDSecMaxRank);
	if (R == 0) { SecondaryRanks.Remove(Ability); BoostSpells.Remove(Ability); }
	else SecondaryRanks.Add(Ability, R);
	if (D->bChoosesSpell && !Spell.IsNone()) BoostSpells.Add(Ability, Spell);
	if (Generator) Generator->RefreshSummonsSecondary();
	return true;
}

FName URDCombatComponent::GetBoostSpell(FName Ability) const
{
	const FName* S = BoostSpells.Find(Ability);
	return S ? *S : NAME_None;
}

bool URDCombatComponent::RankUpSecondary(FName Ability, FName Spell)
{
	const FRDSecondaryDef* D = SecDef(Ability);
	if (!D || !Generator || bDead) return false;
	if (D->Hero != Generator->CurrentHero) { SetMessage(FString::Printf(TEXT("%s is not your hero's"), *D->Title)); return false; }
	if (D->Slot > 0) { SetMessage(FString::Printf(TEXT("%s is learned from its manual"), *D->Title)); return false; }
	const int32 R = GetSecondaryRank(Ability);
	if (R >= RDSecMaxRank) { SetMessage(FString::Printf(TEXT("%s is at its last rank"), *D->Title)); return false; }
	if (Generator->AngelTokenItem.IsNone() || GetItemCount(Generator->AngelTokenItem) <= 0) { SetMessage(TEXT("You have no Angel Token")); return false; }
	// (a spell boost's first rank takes a spell she knows, not the other boost's)
	if (D->bChoosesSpell && R == 0)
	{
		if (Spell.IsNone()) { SetMessage(TEXT("Choose the spell first")); return false; }
		for (const TPair<FName, FName>& B : BoostSpells) if (B.Key != Ability && B.Value == Spell) { SetMessage(FString::Printf(TEXT("%s is boosted already"), *Spell.ToString())); return false; }
		BoostSpells.Add(Ability, Spell);
	}
	RemoveItem(Generator->AngelTokenItem, 1);
	SecondaryRanks.Add(Ability, R + 1);
	Generator->RefreshSummonsSecondary();
	// (an active one learned goes on the quick bar's first free slot)
	if (R == 0 && D->Kind != ERDSecondaryKind::Passive) AddAbilityToQuickBar(Ability);
	SetMessage(FString::Printf(TEXT("%s rank %d:  %s"), *D->Title, R + 1, *RDSecText(*D, R + 1)));
	PlayUiSound(TEXT("Player.Inventory"), TEXT("Player.Inventory"));
	UE_LOG(LogRDSecondary, Log, TEXT("RDSECONDARY %s rank %d%s"), *Ability.ToString(), R + 1, D->bChoosesSpell ? *FString::Printf(TEXT(" (%s)"), *GetBoostSpell(Ability).ToString()) : TEXT(""));
	return true;
}

void URDCombatComponent::AddAbilityToQuickBar(FName Ability)
{
	if (!Generator || !Generator->bQuickSlots) return;
	const FName Entry(*(TEXT("@") + Ability.ToString()));
	if (QuickSlots.Contains(Entry)) return;
	const int32 Free = QuickSlots.IndexOfByPredicate([](const FName& N) { return N.IsNone(); });
	AssignQuickEntry(Free >= 0 ? Free : QuickSlots.Num(), Entry);
}

TArray<FString> URDCombatComponent::GetSecondaryLines() const
{
	TArray<FString> Out;
	if (!Generator) return Out;
	for (const FRDSecondaryDef& D : Generator->Secondaries)
	{
		if (D.Hero != Generator->CurrentHero) continue;
		const int32 R = GetSecondaryRank(D.Name);
		const int32 Max = D.Slot > 0 ? 1 : RDSecMaxRank;          // (the Rogue's arts: one rank, from their manuals (PR #60's review))
		Out.Add(FString::Printf(TEXT("%s|%s|%s|%d|%d|%s|%s|%s"), *D.Name.ToString(), *D.Title, D.Kind == ERDSecondaryKind::Active ? TEXT("active") : D.Kind == ERDSecondaryKind::Toggle ? TEXT("toggle") : TEXT("passive"),
			R, Max, R > 0 ? *RDSecText(D, R) : TEXT(""), R < Max ? *RDSecText(D, R + 1) : TEXT(""), *GetBoostSpell(D.Name).ToString()));
	}
	return Out;
}

// ------------------------------------------------------------------------------------------------ the token's list
bool URDCombatComponent::BeginRankUp(FName Item)
{
	const int32 Ix = Generator ? Generator->FindItem(Item) : -1;
	if (Ix < 0 || Generator->Items[Ix].Kind != ERDItemKind::Token || GetItemCount(Item) <= 0 || bDead) return false;
	if (!Generator->Secondaries.ContainsByPredicate([this](const FRDSecondaryDef& D) { return D.Hero == Generator->CurrentHero && D.Slot == 0; }))
	{ SetMessage(FString::Printf(TEXT("The %s has no ability to raise for your hero"), *Item.ToString())); return false; }
	RankWith = Item; RankSpellFor = NAME_None; RankCursor = 0;
	ResetListView();
	SetMessage(TEXT("Choose the ability the Angel Token raises"));
	PlayUiSound(TEXT("Player.Inventory"), TEXT("Player.Inventory"));
	return true;
}

void URDCombatComponent::CancelRankUp()
{
	// (choosing a boost's spell: back to the abilities; else out of the list)
	if (!RankSpellFor.IsNone()) { RankSpellFor = NAME_None; RankCursor = 0; ResetListView(); return; }
	if (!RankWith.IsNone()) ResetListView();
	RankWith = NAME_None; RankCursor = 0;
}

TArray<FString> URDCombatComponent::GetRankLines() const
{
	TArray<FString> Out;
	if (!Generator || RankWith.IsNone()) return Out;
	if (!RankSpellFor.IsNone())
	{
		// (the spells she knows, by their spells' names; one the other boost has is dim)
		TSet<FName> Seen;
		for (const FRDWeaponDef& W : Generator->Weapons)
		{
			if (!W.bSpell || W.bScroll || W.BoltMesh || !Generator->Spells.IsValidIndex(W.SpellIndex)) continue;
			const FName Sp = Generator->Spells[W.SpellIndex].Name;
			if (Seen.Contains(Sp)) continue;
			Seen.Add(Sp);
			FName By = NAME_None;
			for (const TPair<FName, FName>& B : BoostSpells) if (B.Value == Sp) By = B.Key;
			Out.Add(FString::Printf(TEXT("spell|%s|%s"), *Sp.ToString(), *By.ToString()));
		}
		return Out;
	}
	for (const FRDSecondaryDef& D : Generator->Secondaries)
	{
		if (D.Hero != Generator->CurrentHero || D.Slot > 0) continue;          // (the Rogue's arts: from their manuals, never a token)
		const int32 R = GetSecondaryRank(D.Name);
		Out.Add(FString::Printf(TEXT("rank|%s|%s|%d|%d|%s"), *D.Name.ToString(), *D.Title, R, RDSecMaxRank, R < RDSecMaxRank ? *RDSecText(D, R + 1) : TEXT("at its last rank")));
	}
	return Out;
}

void URDCombatComponent::MoveRankCursor(int32 Step)
{
	const int32 N = GetRankLines().Num();
	if (N > 0) RankCursor = ((RankCursor + Step) % N + N) % N;
}

bool URDCombatComponent::RankEntry(int32 Line)
{
	const TArray<FString> L = GetRankLines();
	const int32 I = Line >= 0 ? Line : RankCursor;
	if (!L.IsValidIndex(I) || !Generator) return false;
	TArray<FString> P; L[I].ParseIntoArray(P, TEXT("|"), false);
	if (P.Num() < 2) return false;
	if (P[0] == TEXT("spell"))
	{
		const FName Ab = RankSpellFor;
		RankSpellFor = NAME_None;
		const bool bOk = RankUpSecondary(Ab, FName(*P[1]));
		if (GetItemCount(RankWith) <= 0) { RankWith = NAME_None; }
		RankCursor = 0; ResetListView();
		return bOk;
	}
	const FName Ab(*P[1]);
	const FRDSecondaryDef* D = SecDef(Ab);
	if (!D) return false;
	// (a spell boost's first rank: its spell chosen next)
	if (D->bChoosesSpell && GetSecondaryRank(Ab) == 0)
	{
		RankSpellFor = Ab; RankCursor = 0; ResetListView();
		if (GetRankLines().Num() == 0) { RankSpellFor = NAME_None; SetMessage(TEXT("You know no spell to boost")); return false; }
		SetMessage(FString::Printf(TEXT("Choose the spell %s boosts"), *D->Title));
		return true;
	}
	const bool bOk = RankUpSecondary(Ab, NAME_None);
	if (bOk && GetItemCount(RankWith) <= 0) { RankWith = NAME_None; RankCursor = 0; ResetListView(); }
	return bOk;
}

// ------------------------------------------------------------------------------------------------ using one
ARDMonster* URDCombatComponent::SecTargetAhead(float Reach, float CosMin) const
{
	AActor* O = GetOwner();
	if (!O || !Generator) return nullptr;
	const FVector L = O->GetActorLocation(), Fw = O->GetActorForwardVector() * FVector(1, 1, 0);
	ARDMonster* Best = nullptr; float BestD = Reach;
	FCollisionQueryParams Q(SCENE_QUERY_STAT(RDSecSight), false, O);
	for (ARDMonster* Mo : Generator->GetMonsters())
	{
		if (!IsValid(Mo) || Mo->IsDead() || Mo->IsAlly()) continue;
		const FVector D = (Mo->GetActorLocation() - L) * FVector(1, 1, 0);
		const float Dist = D.Size() - Mo->GetCapsuleComponent()->GetScaledCapsuleRadius();
		if (Dist > BestD || FMath::Abs(Mo->GetActorLocation().Z - L.Z) > 400.f) continue;
		if (Dist > 40.f && FVector::DotProduct(D.GetSafeNormal(), Fw.GetSafeNormal()) < CosMin) continue;
		// (seen from her chest: not through a wall)
		FHitResult H; Q.ClearIgnoredSourceObjects(); Q.AddIgnoredActor(O); Q.AddIgnoredActor(Mo);
		if (GetWorld()->LineTraceSingleByChannel(H, L + FVector(0, 0, 50.f), Mo->GetActorLocation() + FVector(0, 0, 30.f), ECC_Visibility, Q) && !Cast<ARDMonster>(H.GetActor())) continue;
		BestD = Dist; Best = Mo;
	}
	return Best;
}

TArray<ARDMonster*> URDCombatComponent::SecTargetsAround(float Reach, float CosMin) const
{
	TArray<ARDMonster*> Out;
	AActor* O = GetOwner();
	if (!O || !Generator) return Out;
	const FVector L = O->GetActorLocation(), Fw = O->GetActorForwardVector() * FVector(1, 1, 0);
	FCollisionQueryParams Q(SCENE_QUERY_STAT(RDSecAround), false, O);
	for (ARDMonster* Mo : Generator->GetMonsters())
	{
		if (!IsValid(Mo) || Mo->IsDead() || Mo->IsAlly()) continue;
		const FVector D = (Mo->GetActorLocation() - L) * FVector(1, 1, 0);
		const float Dist = D.Size() - Mo->GetCapsuleComponent()->GetScaledCapsuleRadius();
		if (Dist > Reach || FMath::Abs(Mo->GetActorLocation().Z - L.Z) > 300.f) continue;
		if (CosMin > -1.f && Dist > 40.f && FVector::DotProduct(D.GetSafeNormal(), Fw.GetSafeNormal()) < CosMin) continue;
		// (PR #35's review: not through a wall)
		FHitResult H; Q.ClearIgnoredSourceObjects(); Q.AddIgnoredActor(O); Q.AddIgnoredActor(Mo);
		if (GetWorld()->LineTraceSingleByChannel(H, L + FVector(0, 0, 50.f), Mo->GetActorLocation() + FVector(0, 0, 30.f), ECC_Visibility, Q) && !Cast<ARDMonster>(H.GetActor())) continue;
		Out.Add(Mo);
	}
	return Out;
}

bool URDCombatComponent::SecFloorAt(const FVector& To, float HalfHeight, float Radius, FVector& Out) const
{
	AActor* O = GetOwner();
	UWorld* W = GetWorld();
	if (!W) return false;
	FCollisionQueryParams Q(SCENE_QUERY_STAT(RDSecFloor), false, O);
	FHitResult H;
	if (!W->LineTraceSingleByChannel(H, To + FVector(0, 0, 300.f), To - FVector(0, 0, 900.f), ECC_Visibility, Q)) return false;
	if (Cast<ARDMonster>(H.GetActor()) || H.ImpactNormal.Z < 0.7f) return false;
	const FVector At = H.ImpactPoint + FVector(0, 0, HalfHeight + 5.f);
	if (W->OverlapAnyTestByChannel(At, FQuat::Identity, ECC_Pawn, FCollisionShape::MakeCapsule(Radius, HalfHeight), Q)) return false;
	Out = At;
	return true;
}

bool URDCombatComponent::IsSecondaryOn(FName Ability) const
{
	const float Now = GetWorld() ? GetWorld()->GetTimeSeconds() : 0.f;
	if (Ability == RDSecManaBlade) return bManaBlade;
	if (Ability == RDSecRecharge) return Now < RechargeUntil;
	if (Ability == RDSecAblation) return Now < AblationUntil && AblationLayers > 0;
	if (Ability == RDSecManaShield) return Now < ManaShieldUntil;
	if (Ability == RDSecCurseShield) return Now < CurseShieldUntil;
	if (Ability == RDSecBlindShield) return Now < BlindShieldUntil;
	if (Ability == RDSecBleedShield) return Now < BleedShieldUntil;
	if (Ability == RDSecParry) return Now < ParryUntil;
	if (Ability == RDSecIronSkin) return Now < IronSkinUntil;
	if (Ability == RDSecWater) return bWaterWalking;
	return false;
}

float URDCombatComponent::GetSecondaryCooldownLeft(FName Ability) const
{
	const float* R = ReadyAt.Find(FName(*(TEXT("@") + Ability.ToString())));
	return R && GetWorld() ? FMath::Max(0.f, *R - GetWorld()->GetTimeSeconds()) : 0.f;
}

bool URDCombatComponent::UseSecondary(FName Ability)
{
	const FRDSecondaryDef* D = SecDef(Ability);
	ACharacter* C = Cast<ACharacter>(GetOwner());
	if (!D || !C || !Generator || bDead || GetSecondaryRank(Ability) <= 0 || D->Hero != Generator->CurrentHero) return false;
	if (Generator->IsMounted()) { SetMessage(FString::Printf(TEXT("%s: not from the saddle"), *D->Title)); return false; }
	if (Generator->IsSwimming()) { SetMessage(FString::Printf(TEXT("%s: not while swimming"), *D->Title)); return false; }
	UWorld* W = GetWorld();
	const float Now = W->GetTimeSeconds();
	if (D->Slot > 0) return UseRogueArt(*D);          // (the list of 2026-11-12: the Rogue's arts, RDRogue12.cpp)
	const float V = SecondaryValue(Ability, 0), V2 = SecondaryValue(Ability, 1), S = SecondaryValue(Ability, 2), Cd = SecondaryValue(Ability, 3);
	if (D->Kind == ERDSecondaryKind::Passive) { SetMessage(FString::Printf(TEXT("%s always holds"), *D->Title)); return false; }
	if (D->Kind == ERDSecondaryKind::Toggle)
	{
		bManaBlade = Ability == RDSecManaBlade ? !bManaBlade : bManaBlade;
		SetMessage(FString::Printf(TEXT("%s %s"), *D->Title, bManaBlade ? TEXT("on") : TEXT("off")));
		LastSecondary = FString::Printf(TEXT("%s|%d|%.1f"), *Ability.ToString(), bManaBlade ? 1 : 0, V);
		++SecondaryUses;
		return true;
	}
	const FName Key(*(TEXT("@") + Ability.ToString()));
	if (const float* R = ReadyAt.Find(Key); R && *R > Now) { SetMessage(FString::Printf(TEXT("%s is not ready: %.0f s"), *D->Title, FMath::CeilToFloat(*R - Now))); return false; }
	const FVector L = C->GetActorLocation();
	FVector Fw = C->GetActorForwardVector() * FVector(1, 1, 0); Fw = Fw.GetSafeNormal();
	UCharacterMovementComponent* CM = C->GetCharacterMovement();
	const float Hh = C->GetCapsuleComponent()->GetScaledCapsuleHalfHeight(), Rad = C->GetCapsuleComponent()->GetScaledCapsuleRadius();
	const float Reach = D->Reach > 0.f ? D->Reach : 250.f;
	FString Refused; int32 Reached = 0; float Number = 0.f;
	auto NoTarget = [&](const TCHAR* What) { Refused = FString::Printf(TEXT("%s: %s"), *D->Title, What); };
	if (Ability == RDSecShieldBash)
	{
		for (ARDMonster* Mo : SecTargetsAround(Reach, FMath::Cos(FMath::DegreesToRadians(60.f)))) { Mo->StunFor(V); ++Reached; }
		if (Reached == 0) NoTarget(TEXT("no enemy within reach in front of you"));
		Number = V;
	}
	else if (Ability == RDSecGrapple || Ability == RDSecTrip || Ability == RDSecBlinding)
	{
		ARDMonster* Mo = SecTargetAhead(Reach, 0.5f);
		if (!Mo) NoTarget(TEXT("no enemy within reach before you"));
		else
		{
			// (grapple: held where it stands, its blows still come; trip: prone, no move and no blow; the strike: her weapon's blow
			// and blindness)
			if (Ability == RDSecGrapple) Mo->SlowFor(1.f, V);
			else if (Ability == RDSecTrip) Mo->StunFor(V);
			else
			{
				const int32 Wi = GetWeaponIndex();
				const float Dmg = Generator->Weapons.IsValidIndex(Wi) && !Generator->Weapons[Wi].bSpell ? GetDamageOf(Wi) : 0.f;
				if (Dmg > 0.f) { if (Mo->ApplyDamage(Dmg, C)) ++Kills; DamageDealt += Dmg; Generator->AddHitText(Mo->GetActorLocation() + FVector(0, 0, 90.f), Dmg, false); }
				Mo->BlindFor(1.f, V);
			}
			Reached = 1; Number = V;
		}
	}
	else if (Ability == RDSecPush)
	{
		for (ARDMonster* Mo : SecTargetsAround(Reach, -2.f))
		{
			const FVector Dir = ((Mo->GetActorLocation() - L) * FVector(1, 1, 0)).GetSafeNormal();
			const float Sp = 2600.f;
			ForcedMoves.Add({ Mo, Mo->GetActorLocation() + (Dir.IsNearlyZero() ? Fw : Dir) * V * 100.f, Sp, Now + V * 100.f / Sp + 0.3f });
			Mo->StunFor(V * 100.f / Sp + 0.5f);
			++Reached;
		}
		if (Reached == 0) NoTarget(TEXT("no enemy within reach"));
		Number = V;
	}
	else if (Ability == RDSecPull)
	{
		ARDMonster* Mo = SecTargetAhead(V * 100.f, FMath::Cos(FMath::DegreesToRadians(25.f)));
		if (!Mo) NoTarget(TEXT("no enemy before you within reach"));
		else
		{
			const float Sp = 3200.f, Dist = FVector::Dist2D(Mo->GetActorLocation(), L);
			ForcedMoves.Add({ Mo, L + Fw * (Rad + Mo->GetCapsuleComponent()->GetScaledCapsuleRadius() + 60.f), Sp, Now + Dist / Sp + 0.5f });
			Mo->StunFor(Dist / Sp + 0.4f);
			Reached = 1; Number = Dist / 100.f;
		}
	}
	else if (Ability == RDSecSwarm)
	{
		ARDMonster* Mo = SecTargetAhead(Reach, FMath::Cos(FMath::DegreesToRadians(45.f)));
		const int32 N = V > 0.f ? FMath::FloorToInt(Mana / V) : 0;
		// (each light a share of her first spell's blow (her fire bolt's), as her growth makes it)
		int32 First = Generator->Weapons.IndexOfByPredicate([](const FRDWeaponDef& Wd) { return Wd.bSpell && !Wd.BoltMesh && !Wd.bScroll; });
		const float Dmg = First >= 0 ? GetDamageOf(First) * FMath::Max(D->Share, 0.05f) : 0.f;
		if (!Mo) NoTarget(TEXT("no enemy before you"));
		else if (N <= 0) { Refused = FString::Printf(TEXT("%s: too little mana (one light for every %.0f)"), *D->Title, V); NoManaTime = Now; }
		else
		{
			SwarmTarget = Mo; SwarmLeft = N; SwarmDmg = Dmg; SwarmNextAt = Now; SwarmSpell = Generator->FindSpell(D->LookSpell);
			Mana -= N * V;          // (PR #35's review: its lights are her mana's, spent)
			Reached = N; Number = Dmg;
		}
	}
	else if (Ability == RDSecRecharge) { RechargeUntil = Now + S; Reached = 1; Number = S; }
	else if (Ability == RDSecAblation) { AblationUntil = Now + S; AblationLayers = FMath::RoundToInt(V); Reached = AblationLayers; Number = S; }
	else if (Ability == RDSecManaShield) { ManaShieldUntil = Now + S; Reached = 1; Number = S; }
	else if (Ability == RDSecCurseShield) { CurseShieldUntil = Now + S; ShieldAuraTick = 0.f; Reached = 1; Number = S; }
	else if (Ability == RDSecBlindShield) { BlindShieldUntil = Now + S; ShieldAuraTick = 0.f; Reached = 1; Number = S; }
	else if (Ability == RDSecBleedShield) { BleedShieldUntil = Now + S; ShieldAuraTick = 0.f; Reached = 1; Number = S; }
	else if (Ability == RDSecParry) { ParryUntil = Now + S; Reached = 1; Number = S; }
	else if (Ability == RDSecIronSkin) { IronSkinUntil = Now + S; Reached = 1; Number = V; }
	else if (Ability == RDSecHealing)
	{
		for (ARDMonster* A : Generator->Allies)
			if (IsValid(A) && !A->IsDead() && !A->SummonSpell.IsNone()) { A->HealBy(A->GetMaxHealth() * V / 100.f); ++Reached; }
		if (Reached == 0) NoTarget(TEXT("no summon of yours stands"));
		Number = V;
	}
	else if (Ability == RDSecMistyStep || Ability == RDSecTransfer)
	{
		// (her, or the enemy before her, to a floor that far off (or nearer, by fifths), the way farthest from her foes for her, from
		// her for it)
		ARDMonster* Mo = Ability == RDSecTransfer ? SecTargetAhead(Reach, 0.5f) : nullptr;
		if (Ability == RDSecTransfer && !Mo) NoTarget(TEXT("no enemy before you"));
		else
		{
			AActor* Who = Mo ? (AActor*)Mo : (AActor*)C;
			const FVector From = Who->GetActorLocation();
			const float H2 = Mo ? Mo->GetCapsuleComponent()->GetScaledCapsuleHalfHeight() : Hh, R2 = Mo ? Mo->GetCapsuleComponent()->GetScaledCapsuleRadius() : Rad;
			TArray<ARDMonster*> Foes = SecTargetsAround(4000.f, -2.f);
			FVector Best = FVector::ZeroVector; float BestScore = -1.f, BestLen = 0.f;
			for (float F = 1.f; F >= 0.19f && BestScore < 0.f; F -= 0.2f)
				for (int32 K = 0; K < 16; ++K)
				{
					const float A = K * PI / 8.f;
					FVector Spot;
					if (!SecFloorAt(From + FVector(FMath::Cos(A), FMath::Sin(A), 0.f) * V * 100.f * F, H2, R2, Spot)) continue;
					// (PR #35's review: in sight of where it starts: never through a wall into a vault, a cell or past the arena's bars)
					FHitResult Sh; FCollisionQueryParams Sq(SCENE_QUERY_STAT(RDSecMisty), false, C); Sq.AddIgnoredActor(Who);
					if (W->LineTraceSingleByChannel(Sh, From + FVector(0, 0, 40.f), Spot + FVector(0, 0, 40.f), ECC_Visibility, Sq) && !Cast<ARDMonster>(Sh.GetActor())) continue;
					float Score = 0.f;
					if (Mo) Score = FVector::Dist2D(Spot, L);
					else { Score = 1e9f; for (ARDMonster* Fo : Foes) Score = FMath::Min(Score, (float)FVector::Dist2D(Spot, Fo->GetActorLocation())); }
					if (Score > BestScore) { BestScore = Score; Best = Spot; BestLen = FVector::Dist2D(Spot, From); }
				}
			if (BestScore < 0.f) NoTarget(TEXT("no safe place that far"));
			else
			{
				if (Generator->TeleportFx) SpawnFx(Generator->TeleportFx, From - FVector(0, 0, H2), FRotator::ZeroRotator, 1.f);
				Who->SetActorLocation(Best, false, nullptr, ETeleportType::TeleportPhysics);
				if (Mo) Mo->StunFor(0.6f); else CM->StopMovementImmediately();
				if (Generator->TeleportFx) SpawnFx(Generator->TeleportFx, Best - FVector(0, 0, H2), FRotator::ZeroRotator, 1.f);
				LastMoveLength = BestLen; Reached = 1; Number = BestLen / 100.f;
			}
		}
	}
	else if (Ability == RDSecWallRun)
	{
		// (a leap: the farthest landing on a floor along her way within its length, up to half its length higher, the arc clear)
		FCollisionQueryParams Q(SCENE_QUERY_STAT(RDSecLeap), false, C);
		const FCollisionShape Cap = FCollisionShape::MakeCapsule(Rad, Hh);
		FVector Land = FVector::ZeroVector; float Len = 0.f;
		for (float Dd = V * 100.f; Dd >= 200.f && Len <= 0.f; Dd -= 50.f)
		{
			const FVector P = L + Fw * Dd;
			FHitResult Fh;
			if (!W->LineTraceSingleByChannel(Fh, FVector(P.X, P.Y, L.Z + Dd * 0.5f + 200.f), FVector(P.X, P.Y, L.Z - 2000.f), ECC_Visibility, Q)) continue;
			if (Fh.ImpactNormal.Z < 0.7f || Cast<ARDMonster>(Fh.GetActor())) continue;
			const FVector At = Fh.ImpactPoint + FVector(0, 0, Hh + 5.f);
			if (W->OverlapAnyTestByChannel(At, FQuat::Identity, ECC_Pawn, Cap, Q)) continue;
			const float Top = FMath::Max(L.Z, At.Z) + 150.f + Dd * 0.08f;
			FHitResult Sh;
			if (W->SweepSingleByChannel(Sh, L, FVector(L.X, L.Y, Top), FQuat::Identity, ECC_Pawn, Cap, Q)) continue;
			if (W->SweepSingleByChannel(Sh, FVector(L.X, L.Y, Top), FVector(At.X, At.Y, Top), FQuat::Identity, ECC_Pawn, Cap, Q)) continue;
			if (W->SweepSingleByChannel(Sh, FVector(At.X, At.Y, Top), At, FQuat::Identity, ECC_Pawn, Cap, Q)) continue;
			Land = At; Len = Dd;
		}
		if (Len <= 0.f) NoTarget(TEXT("nowhere to land along your way"));
		else
		{
			const float T = FMath::Clamp(Len / 1500.f, 0.55f, 1.6f), G = CM->GetGravityZ();
			const FVector Dv = Land - L;
			C->LaunchCharacter(FVector(Dv.X / T, Dv.Y / T, Dv.Z / T - 0.5f * G * T), true, true);
			LastMoveLength = Len; Reached = 1; Number = Len / 100.f;
		}
	}
	else if (Ability == RDSecFlash)
	{
		// (along her way through every enemy: only the walls stop it)
		FCollisionObjectQueryParams Ob; Ob.AddObjectTypesToQuery(ECC_WorldStatic); Ob.AddObjectTypesToQuery(ECC_WorldDynamic);
		FCollisionQueryParams Q(SCENE_QUERY_STAT(RDSecFlash), false, C);
		FHitResult Sh;
		float Len = V * 100.f;
		if (W->SweepSingleByObjectType(Sh, L, L + Fw * Len, FQuat::Identity, Ob, FCollisionShape::MakeCapsule(Rad, Hh - 5.f), Q)) Len = FMath::Max(0.f, Sh.Distance - 20.f);
		if (Len < 150.f) NoTarget(TEXT("a wall is in the way"));
		else
		{
			FlashPawnWas = C->GetCapsuleComponent()->GetCollisionResponseToChannel(ECC_Pawn);
			C->GetCapsuleComponent()->SetCollisionResponseToChannel(ECC_Pawn, ECR_Ignore);
			const float Dur = FMath::Clamp(Len / 4000.f, 0.15f, 0.6f);
			TSharedPtr<FRootMotionSource_ConstantForce> F = MakeShared<FRootMotionSource_ConstantForce>();
			F->InstanceName = TEXT("RDFlashStep");
			F->AccumulateMode = ERootMotionAccumulateMode::Override;
			F->Settings.SetFlag(ERootMotionSourceSettingsFlags::IgnoreZAccumulate);
			F->Priority = 6; F->Duration = Dur; F->Force = Fw * (Len / Dur);
			F->FinishVelocityParams.Mode = ERootMotionFinishVelocityMode::ClampVelocity; F->FinishVelocityParams.ClampVelocity = 60.f;
			CM->ApplyRootMotionSource(F);
			FlashUntil = Now + Dur + 0.1f;
			LastMoveLength = Len; Reached = 1; Number = Len / 100.f;
		}
	}
	else if (Ability == RDSecWater)
	{
		// (water under her or within 8 m before her: from the shore she runs onto it)
		float Wz = 0.f; bool bWater = false;
		for (int32 K = 0; K <= 8 && Generator->bWild && !bWater; ++K) bWater = Generator->WildWaterZAt(L + Fw * (K * 100.f), Wz);
		if (!bWater) NoTarget(TEXT("no water before you"));
		else
		{
			bWaterWalking = true; bWaterReached = false; WaterLeft = V * 100.f; WaterLast = L; LastMoveLength = 0.f;
			WaterUntil = Now + V * 100.f / FMath::Max(CM->MaxWalkSpeed, 200.f) + 4.f;
			Reached = 1; Number = V;
		}
	}
	if (!Refused.IsEmpty()) { SetMessage(Refused); return false; }
	ReadyAt.Add(Key, Now + Cd);
	++SecondaryUses;
	LastSecondary = FString::Printf(TEXT("%s|%d|%.2f"), *Ability.ToString(), Reached, Number);
	SetMessage(FString::Printf(TEXT("%s"), *D->Title));
	UE_LOG(LogRDSecondary, Log, TEXT("RDSECONDARY %s used: %d reached, %.2f"), *Ability.ToString(), Reached, Number);
	return true;
}

// ------------------------------------------------------------------------------------------------ on her and on her blows
float URDCombatComponent::AbsorbBySecondary(float Amount, AActor* From)
{
	UWorld* W = GetWorld();
	if (!W || !Generator || Amount <= 0.f) return Amount;
	const float Now = W->GetTimeSeconds();
	ARDMonster* Mo = Cast<ARDMonster>(From);
	AActor* O = GetOwner();
	// (parry: a blow from in front of her turned aside, its maker staggered)
	if (Now < ParryUntil && Mo && O && FVector::DotProduct((Mo->GetActorLocation() - O->GetActorLocation()).GetSafeNormal2D(), O->GetActorForwardVector().GetSafeNormal2D()) > 0.2f)
	{
		const FRDSecondaryDef* D = SecDef(RDSecParry);
		Mo->StunFor(D && D->Share > 0.f ? D->Share : 1.5f); ++ParriedBlows;
		return 0.f;
	}
	// (ablation: a layer peeled, the blow struck back at its maker)
	if (Now < AblationUntil && AblationLayers > 0)
	{
		--AblationLayers; ++PeeledLayers;
		const FRDSecondaryDef* D = SecDef(RDSecAblation);
		if (Mo && !Mo->IsDead()) CurrentSpellElement = NAME_None;          // (PR #48's review: no earlier spell's element)
		if (Mo && !Mo->IsDead()) SpellHurt(Mo, Amount * (D && D->Share > 0.f ? D->Share : 1.f), Mo->GetActorLocation() + FVector(0, 0, 40.f), true);
		return 0.f;
	}
	// (recharge: the blow becomes mana)
	if (Now < RechargeUntil) { const float Got = FMath::Min(Amount, MaxMana - Mana); Mana += Got; RechargedMana += Got; return 0.f; }
	// (her mana takes what it can)
	if (Now < ManaShieldUntil && Mana > 0.f) { const float T = FMath::Min(Mana, Amount); Mana -= T; ShieldManaSpent += T; Amount -= T; }
	if (Now < IronSkinUntil) Amount *= 1.f - FMath::Clamp(SecondaryValue(RDSecIronSkin, 0) / 100.f, 0.f, 0.9f);
	return Amount;
}

float URDCombatComponent::SpellBoostMul(const FRDWeaponDef& W) const
{
	if (!Generator || !W.bSpell || W.BoltMesh || !Generator->Spells.IsValidIndex(W.SpellIndex) || BoostSpells.Num() == 0) return 1.f;
	const FName Sp = Generator->Spells[W.SpellIndex].Name;
	float M = 1.f;
	for (const TPair<FName, FName>& B : BoostSpells) if (B.Value == Sp) M *= FMath::Max(SecondaryValue(B.Key, 0), 1.f);
	return M;
}

float URDCombatComponent::ManaBladeBonus(bool bSpend)
{
	if (!bManaBlade) return 0.f;
	const float Ratio = SecondaryValue(RDSecManaBlade, 0), Cost = SecondaryValue(RDSecManaBlade, 1);
	if (Ratio <= 0.f || Cost <= 0.f || Mana < Cost) return 0.f;
	if (bSpend) { Mana -= Cost; ++ManaBladeBlows; }
	return Cost * Ratio;
}

void URDCombatComponent::TickSecondary(float Dt)
{
	UWorld* W = GetWorld();
	ACharacter* C = Cast<ACharacter>(GetOwner());
	if (!W || !C || !Generator) return;
	const float Now = W->GetTimeSeconds();
	TickRogueArts(Dt);
	// (pulled and pushed: swept tick by tick, walls stop them)
	for (int32 I = ForcedMoves.Num() - 1; I >= 0; --I)
	{
		FForcedMove& F = ForcedMoves[I];
		ARDMonster* Mo = F.M.Get();
		if (!Mo || Mo->IsDead() || Now > F.Until || FVector::Dist2D(Mo->GetActorLocation(), F.To) < 70.f) { ForcedMoves.RemoveAt(I); continue; }
		Mo->PullToward(F.To, F.Speed, Dt);
	}
	// (the swarm's lights, one after another)
	if (SwarmLeft > 0 && Now >= SwarmNextAt)
	{
		ARDMonster* T = SwarmTarget.Get();
		if (!T || T->IsDead()) SwarmLeft = 0;
		else
		{
			const USkeletalMeshComponent* M = Body();
			const FVector From = (M ? M->GetSocketLocation(TEXT("hand_r")) : C->GetActorLocation()) + FVector(FMath::FRandRange(-20.f, 20.f), FMath::FRandRange(-20.f, 20.f), FMath::FRandRange(0.f, 30.f));
			if (Generator->Spells.IsValidIndex(SwarmSpell)) LaunchSpellBolt(SwarmSpell, From, T, SwarmDmg, 0, {});
			else { if (T->ApplyDamage(SwarmDmg, C)) ++Kills; DamageDealt += SwarmDmg; }
			--SwarmLeft; SwarmNextAt = Now + 0.07f;
		}
	}
	// (the Warlock's shields on everyone within their reach, twice a second)
	if (Now < CurseShieldUntil || Now < BlindShieldUntil || Now < BleedShieldUntil)
	{
		ShieldAuraTick -= Dt;
		if (ShieldAuraTick <= 0.f)
		{
			ShieldAuraTick = 0.5f;
			auto Each = [&](FName Ab, TFunctionRef<void(ARDMonster*)> Do)
			{
				const FRDSecondaryDef* D = SecDef(Ab);
				for (ARDMonster* Mo : SecTargetsAround(D && D->Reach > 0.f ? D->Reach : 200.f, -2.f)) Do(Mo);
			};
			if (Now < CurseShieldUntil) Each(RDSecCurseShield, [&](ARDMonster* Mo) { Mo->CurseFor(SecondaryValue(RDSecCurseShield, 0) / 100.f, 1.f); });
			if (Now < BlindShieldUntil) Each(RDSecBlindShield, [&](ARDMonster* Mo) { Mo->BlindFor(1.f, 1.f); });
			if (Now < BleedShieldUntil) Each(RDSecBleedShield, [&](ARDMonster* Mo) { Mo->AddBurn(SecondaryValue(RDSecBleedShield, 0) * Generator->TierSpellMul(), 0.5f, 0.f); });
		}
	}
	// (the flash step over: her capsule stops pawns again)
	if (FlashUntil > 0.f && Now > FlashUntil) { C->GetCapsuleComponent()->SetCollisionResponseToChannel(ECC_Pawn, FlashPawnWas); FlashUntil = -100.f; }
	// (the water walk: held on the water's face as she goes, its length counted over water; off it, or its length gone, she walks
	// (or falls in))
	if (bWaterWalking)
	{
		UCharacterMovementComponent* CM = C->GetCharacterMovement();
		const FVector L = C->GetActorLocation();
		float Wz = 0.f;
		const bool bOver = Generator->WildWaterZAt(L, Wz);
		// (on the shore still: she walks; on the water: held on its face)
		if (bOver && !bWaterReached) { bWaterReached = true; FlySpeedWas = CM->MaxFlySpeed; CM->SetMovementMode(MOVE_Flying); }
		if (bOver)
		{
			const float Hh = C->GetCapsuleComponent()->GetScaledCapsuleHalfHeight();
			C->SetActorLocation(FVector(L.X, L.Y, Wz + Hh + 2.f), false);
			CM->Velocity.Z = 0.f; CM->MaxFlySpeed = CM->MaxWalkSpeed;
			const float Step = FVector::Dist2D(L, WaterLast);
			WaterLeft -= Step; LastMoveLength += Step;
		}
		WaterLast = L;
		if ((!bOver && bWaterReached) || WaterLeft <= 0.f || Now > WaterUntil)
		{
			bWaterWalking = false;
			if (CM->MovementMode == MOVE_Flying) CM->SetMovementMode(MOVE_Falling);
			if (FlySpeedWas >= 0.f) { CM->MaxFlySpeed = FlySpeedWas; FlySpeedWas = -1.f; }
		}
	}
}

// ------------------------------------------------------------------------------------------------ the Summoner's (the generator's)
float ARDDungeonGenerator::SecondaryMul(FName Ability, int32 Which) const
{
	const float V = PlayerCombat ? PlayerCombat->SecondaryValue(Ability, Which) : 0.f;
	return V > 0.f ? V : 1.f;
}

void ARDDungeonGenerator::RefreshSummonsSecondary()
{
	for (ARDMonster* A : Allies)
	{
		if (!IsValid(A) || A->IsDead() || A->SummonSpell.IsNone()) continue;
		A->AllyPace = SecondaryMul(RDSecFrenzy);
		if (SummonsGrow()) { float Hp = 0.f, Dm = 0.f; int32 St = 0; SummonStrength(A->SummonSpell, Hp, Dm, St); A->SetStrength(St, Hp, Dm); }
	}
}

void ARDDungeonGenerator::SecondaryOnKill(ARDMonster* Monster)
{
	if (!Monster || !PlayerCombat || Monster->IsAlly()) return;
	const float Now = GetWorld()->GetTimeSeconds();
	// (the wilds' monsters drop Seraph Feathers (a hash of the monster: no stream of the play's))
	if (Monster->bOpenGround && !SeraphFeatherItem.IsNone() && FindItem(SeraphFeatherItem) >= 0)
	{
		const uint32 H = HashCombine(GetTypeHash(Monster->WildKey), GetTypeHash(Monster->GetUniqueID()) ^ 0x5E4Au);
		if ((H % 1000u) / 1000.f < SeraphFeatherChance) DropHarvest(Monster->GetActorLocation() + FVector(60.f, 0.f, 0.f), { SeraphFeatherItem }, FMath::Clamp(Monster->Tier, 1, 5));
	}
	// (the soul harvest: a death near her heals her summons and makes their blows harder a while)
	const float Boost = PlayerCombat->SecondaryValue(RDSecSoul, 0);
	if (Boost <= 0.f) return;
	const FRDSecondaryDef* D = FindSecondary(RDSecSoul);
	const APawn* Her = PlayerCombat->GetOwner() ? Cast<APawn>(PlayerCombat->GetOwner()) : nullptr;
	if (!Her || FVector::Dist(Her->GetActorLocation(), Monster->GetActorLocation()) > (D && D->Reach > 0.f ? D->Reach : 2500.f)) return;
	const float Heal = PlayerCombat->SecondaryValue(RDSecSoul, 1) / 100.f, Secs = FMath::Max(PlayerCombat->SecondaryValue(RDSecSoul, 2), 1.f);
	int32 N = 0;
	for (ARDMonster* A : Allies)
		if (IsValid(A) && !A->IsDead() && !A->SummonSpell.IsNone()) { A->HealBy(A->GetMaxHealth() * Heal); A->AllyBoost = Boost; A->AllyBoostUntil = Now + Secs; ++N; }
	if (N > 0) ++PlayerCombat->SoulHarvests;
}

void ARDDungeonGenerator::LayHallowedStone(ARDWildChunk* C, const FRDWildPlace& P)
{
	if (!C || HallowedStoneItem.IsNone() || FindItem(HallowedStoneItem) < 0 || !HallowedKinds.Contains(P.Kind)) return;
	// (PR #35's review: a range of its own: a place's kills are its id x 16 + 0..15, and a quest counts them all)
	const int64 Key = -((int64)P.Id + 2);          // (-1 is a pile's "none")
	if (const URDGameInstance* GI = URDGameInstance::Of(this); GI && GI->WildKilled.Contains(Key)) return;
	// (a chunk made again lays it again: the piles of the chunks gone are out of the list first, and it is no harvest)
	LootPiles.RemoveAll([](const TObjectPtr<ARDLootPile>& Lp) { return !IsValid(Lp); });
	FVector At(P.At.X * 100.0 + 250.0, P.At.Y * 100.0, 0.0);
	At.Z = WildGroundZ(At) + 40.f;
	TArray<float> Wr; Wr.Init(-1.f, 1);
	if (ARDLootPile* Lp = DropLoot(At, { HallowedStoneItem }, Wr))
	{
		Lp->bHers = false; Lp->bHarvest = false; Lp->WildKey = Key;          // ("take the hallowed stone")
		C->Props.Add(Lp);
	}
}
