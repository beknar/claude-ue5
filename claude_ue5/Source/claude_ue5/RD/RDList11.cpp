// The user's list of 2026-11-11 (docs/improvements11.txt), its second phase:
//   guards         "when an ambush from outside town appears in the wilderness and makes it into town, the guards should fight
//                  it": a guard, a militiaman, a soldier or the captain who sees a monster on its town's ground runs at it with
//                  its sword drawn and strikes (918 guards: the Dwarf pack's warrior attacks on the NPC packs' Manny skeleton);
//                  the monster may take it for its foe (ARDMonster::PickFoe), and a guard beaten down falls back to its post a
//                  while, its health back. A guard's blow is a share of the monster's whole health, so a few of them bring
//                  down a monster of any tier; one guard alone holds one off for a while.
#include "RD/RDDungeonGenerator.h"
#include "RD/RDTown.h"
#include "RD/RDMonster.h"
#include "RD/RDSection.h"
#include "RD/RDCombat.h"
#include "RD/RDGameInstance.h"
#include "Kismet/GameplayStatics.h"
#include "Components/CapsuleComponent.h"
#include "Components/SkeletalMeshComponent.h"
#include "Components/StaticMeshComponent.h"
#include "Animation/AnimSequenceBase.h"
#include "Engine/World.h"

DEFINE_LOG_CATEGORY_STATIC(LogRDList11, Log, All);

namespace
{
	/** the monster's middle at the guard's height: the guard runs at it on its own floor */
	FVector RDL11Flat(const FVector& P, float Z) { return FVector(P.X, P.Y, Z); }
}

bool ARDTownsfolk::IsGuardFighter() const
{
	return TownRole == ERDTownRole::Guard || TownRole == ERDTownRole::Militia || TownRole == ERDTownRole::Soldier || TownRole == ERDTownRole::Captain
	    || TownRole == ERDTownRole::Templar;
}

AActor* ARDTownsfolk::GetGuardFoe() const { return GuardFoe.Get(); }

bool ARDTownsfolk::IsSwordDrawn() const { return GuardSword && GuardSword->IsVisible(); }

ARDMonster* ARDTownsfolk::FindGuardFoe() const
{
	// (a monster on its town's ground: alive, not hers, not caged, not the Mistward Hall's own guards (HomeRoom), within its
	// sight and not far from its post)
	if (!Gen || !Section) return nullptr;
	const FVector L = GetActorLocation();
	ARDMonster* Best = nullptr; float BestD = Gen->TownGuardSight;
	for (ARDMonster* Mo : Gen->GetMonsters())
	{
		if (!IsValid(Mo) || Mo->IsDead() || Mo->IsAlly() || Mo->bCaged || Mo->HomeRoom >= 0) continue;
		const FVector M = Mo->GetActorLocation();
		if (FMath::Abs(M.Z - L.Z) > 400.f) continue;
		const float D = FVector::Dist2D(M, L);
		if (D >= BestD || FVector::Dist2D(M, Post) > Gen->TownGuardLeash) continue;
		// (inside the town: on a tile of its section's ground or rooms)
		if (!Section->IsWalkable(Section->WorldToLocal(M))) continue;
		Best = Mo; BestD = D;
	}
	// (the call to arms: a guard fighting within TownGuardCall brings it, whatever it sees itself (the first test's militiawoman
	// fought a rat alone for 40 s, the other guards out of sight round the corner)
	if (!Best)
		for (const TWeakObjectPtr<ARDTownsfolk>& W : Gen->FightingGuards)
		{
			const ARDTownsfolk* O = W.Get();
			ARDMonster* F = O && O != this && O->IsFighting() ? O->GuardFoe.Get() : nullptr;
			if (!F || F->IsDead() || FVector::Dist2D(O->GetActorLocation(), L) > Gen->TownGuardCall) continue;
			if (FVector::Dist2D(F->GetActorLocation(), Post) > Gen->TownGuardLeash || !Section->IsWalkable(Section->WorldToLocal(F->GetActorLocation()))) continue;
			return F;
		}
	return Best;
}

void ARDTownsfolk::EndGuardFight(float Now, bool bBeaten)
{
	GuardFoe = nullptr; GuardSwingT = -1.f; GuardPath.Reset(); GuardStuck = 0.f; bGuardEngaged = false;
	if (Gen) Gen->FightingGuards.RemoveAll([this](const TWeakObjectPtr<ARDTownsfolk>& W) { return !W.IsValid() || W.Get() == this; });
	if (GuardSword) GuardSword->SetVisibility(false);
	CurAnim = nullptr;
	if (bBeaten) GuardRestUntil = Now + (Gen ? Gen->TownGuardRest : 20.f);
	// (back to its post by the town's tiles; its round takes up again from there)
	if (Section)
	{
		TArray<FVector> P = Section->FindPathWorld(GetActorLocation(), Post);
		if (P.Num() >= 2 && P.Num() < 150) { P.RemoveAt(0); Path = P; SetClip(true); }
		else SetClip(false);
	}
	NextTrip = Now + R.FRandRange(4.f, 10.f);
}

void ARDTownsfolk::TakeGuardBlow(float Dmg, AActor* From)
{
	if (!IsFighting()) return;
	++GuardBlowsTaken;
	GuardHealth -= Dmg;
	if (GuardHealth <= 0.f)
	{
		UE_LOG(LogRDList11, Log, TEXT("RDGUARD %s beaten back by %s"), *Title, From ? *From->GetName() : TEXT("?"));
		EndGuardFight(GetWorld()->GetTimeSeconds(), true);
	}
}

bool ARDTownsfolk::TickGuardFight(float Dt, float Now)
{
	if (!Gen || !Gen->bTownGuardsFight || !Section || !IsGuardFighter() || bRoadWalker) return false;
	ARDMonster* Foe = GuardFoe.Get();
	// (PR #47's review: a foe destroyed in the fight (a roamer dropped once she is 250 m off, a place's with its chunk) ends it too:
	// the sword put away, the swing let go, back to its post)
	if (!Foe && bGuardEngaged) EndGuardFight(Now, false);
	if (Foe && (Foe->IsDead() || FVector::Dist2D(Foe->GetActorLocation(), Post) > Gen->TownGuardLeash * 1.2f || !Section->IsWalkable(Section->WorldToLocal(Foe->GetActorLocation()))))
	{
		EndGuardFight(Now, false);
		Foe = nullptr;
	}
	if (!Foe)
	{
		if (Now < GuardScanAt || Now < GuardRestUntil) return false;
		GuardScanAt = Now + 0.4f;
		Foe = FindGuardFoe();
		if (!Foe) return false;
		// (to arms: out of bed, off its work, its sword drawn)
		GuardFoe = Foe; ++GuardFights; bGuardEngaged = true;
		Gen->FightingGuards.AddUnique(this);
		if (bInBed) { bInBed = false; SetActorLocationAndRotation(PreBed, FRotator(0.f, HomeYaw, 0.f)); }
		if (Act != 0) EndWork();
		Path.Reset(); FaceUntil = -100.f; GuardPath.Reset(); GuardRepathAt = 0.f;
		GuardHealth = FMath::Max(Foe->GetDamage(), 1.f) * Gen->TownGuardBlowsToBeat;
		const FRDTownsfolkDef* D = Gen->Townsfolk.IsValidIndex(Def) ? &Gen->Townsfolk[Def] : nullptr;
		if (D && D->GuardWeapon)
		{
			if (!GuardSword)
			{
				GuardSword = NewObject<UStaticMeshComponent>(this, TEXT("RDGuardSword"));
				GuardSword->SetCollisionEnabled(ECollisionEnabled::NoCollision);
				GuardSword->SetupAttachment(Body, TEXT("hand_r"));
				GuardSword->RegisterComponent();
			}
			GuardSword->SetStaticMesh(D->GuardWeapon);
			GuardSword->AttachToComponent(Body, FAttachmentTransformRules::SnapToTargetNotIncludingScale, TEXT("hand_r"));
			GuardSword->SetRelativeTransform(D->GuardGrip);
			GuardSword->SetVisibility(true);
		}
		UE_LOG(LogRDList11, Log, TEXT("RDGUARD %s (%s) takes on %s %.0f m off"), *Title, *GetRoleName(), *Foe->GetName(), FVector::Dist2D(Foe->GetActorLocation(), GetActorLocation()) / 100.f);
	}
	const FVector L = GetActorLocation(), Fl = Foe->GetActorLocation();
	FVector Dv = Fl - L; Dv.Z = 0.f;
	const float Dist = Dv.Size();
	const float Gap = Dist - Capsule->GetScaledCapsuleRadius() - Foe->GetCapsuleComponent()->GetScaledCapsuleRadius();
	auto Face = [&](const FVector& Dir, float Rate)
	{
		if (Dir.IsNearlyZero(1.f)) return;
		SetActorRotation(FRotator(0.f, FMath::RInterpConstantTo(GetActorRotation(), Dir.Rotation(), Dt, Rate).Yaw, 0.f));
	};
	// (a blow under way: it plays out, the hit at its time if the monster is still before it)
	if (GuardSwingT >= 0.f)
	{
		GuardSwingT += Dt;
		Face(Dv, 360.f);
		if (!bGuardHitDone && GuardSwingT >= GuardSwingHit)
		{
			bGuardHitDone = true;
			if (Gap < 160.f && FVector::DotProduct(Dv.GetSafeNormal(), GetActorForwardVector()) > 0.3f)
			{
				const float Dmg = FMath::Max(Foe->GetMaxHealth() * Gen->TownGuardBlowShare, 1.f);
				++GuardHits; GuardDamageDone += Dmg;
				Foe->ApplyDamage(Dmg, this);
				Gen->AddHitText(Fl + FVector(0, 0, Foe->GetCapsuleComponent()->GetScaledCapsuleHalfHeight()), Dmg, false);
			}
		}
		if (GuardSwingT >= GuardSwingLen) { GuardSwingT = -1.f; GuardReadyAt = Now + 0.25f; CurAnim = nullptr; }
		return true;
	}
	// (in reach: strike, a blow of its own at a time)
	if (Gap < 110.f)
	{
		Face(Dv, 420.f);
		const int32 Nk = Gen->TownGuardStrikes.Num();
		if (Now >= GuardReadyAt && Nk > 0 && FVector::DotProduct(Dv.GetSafeNormal(), GetActorForwardVector()) > 0.7f)
		{
			const int32 K = (GuardSwingK++) % Nk;
			UAnimSequenceBase* A = Gen->TownGuardStrikes[K];
			if (A)
			{
				const float Rate = FMath::Max(Gen->TownGuardStrikeRate, 0.2f);
				CurAnim = A; CurRate = Rate;
				Body->PlayAnimation(A, false);
				Body->SetPlayRate(Rate);
				GuardSwingLen = A->GetPlayLength() / Rate;
				const float Ht = Gen->TownGuardHitTimes.IsValidIndex(K) ? Gen->TownGuardHitTimes[K] : A->GetPlayLength() * 0.45f;
				GuardSwingHit = FMath::Clamp(Ht / Rate, 0.05f, GuardSwingLen);
				GuardSwingT = 0.f; bGuardHitDone = false; ++GuardStrikes;
				return true;
			}
		}
		SetClip(false);
		return true;
	}
	// (on its way: straight at it while nothing stands between, else by the town's tiles)
	const float Speed_ = Gen->TownGuardRunSpeed;
	FVector To = Fl;
	if (GuardPath.Num() > 0)
	{
		if (FVector::Dist2D(GuardPath[0], L) < 60.f) GuardPath.RemoveAt(0);
		if (GuardPath.Num() > 0) To = GuardPath[0];
	}
	if (Now >= GuardRepathAt && (GuardStuck > 0.3f || GuardPath.Num() > 0))
	{
		GuardRepathAt = Now + 0.8f;
		TArray<FVector> P = Section->FindPathWorld(L, Fl);
		GuardPath.Reset();
		if (P.Num() >= 2 && P.Num() < 150) { P.RemoveAt(0); GuardPath = P; To = GuardPath[0]; }
	}
	FVector Mv = To - L; Mv.Z = 0.f;
	const FVector Step = Mv.GetSafeNormal() * FMath::Min(Speed_ * Dt, FMath::Max(Mv.Size(), 0.f));
	FHitResult Hit;
	SetActorLocation(RDL11Flat(L + Step, L.Z), true, &Hit);
	if (Hit.bBlockingHit && Hit.GetActor() != Foe) GuardStuck += Dt; else GuardStuck = FMath::Max(0.f, GuardStuck - Dt);
	// (a door on the way is opened, as its walks do)
	Section->OpenDoorAhead(L, Mv, 160.f, true);
	Face(Mv, 480.f);
	// (its walk played faster to its run)
	if (WalkAnim) PlayAnim(WalkAnim, FMath::Clamp(Speed_ / FMath::Max(ClipSpeed, 10.f), 0.8f, 2.4f));
	return true;
}

int32 ARDDungeonGenerator::CountFightingGuards() const
{
	int32 N = 0;
	for (const TWeakObjectPtr<ARDTownsfolk>& W : FightingGuards) if (W.IsValid() && W->IsFighting()) ++N;
	return N;
}

TArray<FString> ARDDungeonGenerator::GetGuardLines() const
{
	TArray<FString> Out;
	for (const auto& Tw : TownPeople)
	{
		const ARDTownsfolk* T = Tw.Get();
		if (!IsValid(T) || !T->IsGuardFighter()) continue;
		const FVector L = T->GetActorLocation();
		Out.Add(FString::Printf(TEXT("%s|%s|%d|%d|%d|%d|%.1f|%d|%.1f|%d|%.0f|%.0f|%.0f"), *T->Title, *T->GetRoleName(), T->IsFighting() ? 1 : 0, T->GuardFights, T->GuardStrikes,
			T->GuardHits, T->GuardDamageDone, T->GuardBlowsTaken, T->GetGuardHealth(), T->IsSwordDrawn() ? 1 : 0, L.X, L.Y, L.Z));
	}
	return Out;
}

// ================================================================================================ the console (rd.Tier, rd.Pois, rd.GoToPoi, rd.RevealMap)
int32 ARDDungeonGenerator::ConsoleTierNow() const
{
	const URDGameInstance* GI = URDGameInstance::Of(this);
	return GI ? GI->ConsoleTier : 0;
}

bool URDCombatComponent::ForgetWeapon(FName Name)
{
	if (!Generator) return false;
	const int32 I = Generator->Weapons.IndexOfByPredicate([Name](const FRDWeaponDef& W) { return W.Name == Name; });
	if (I < 0) return false;
	const bool bDrawn = I == WeaponIndex;
	DropWeaponAt(I);
	// (PR #47's review: the one in her hands forgotten, she draws the first she has, as when one breaks (WeaponIndex left on it
	// pointed at the next weapon, or past the list)
	if (bDrawn)
	{
		WeaponIndex = -1;
		for (int32 K = 0; K < Generator->Weapons.Num(); ++K) if (!Generator->Weapons[K].bAlongside && !Generator->Weapons[K].bScroll) { SelectWeapon(K); break; }
	}
	return true;
}

bool URDCombatComponent::PayFreeBolt(FBolt& B, const FVector& At, ARDMonster* Direct, float Reach)
{
	// (PR #47's review: a chi made at no mana with no monster in range could still hurt one that came into its way or its burst:
	// it takes its mana when it does, or, without enough, does no harm)
	if (!B.bFree || !Generator) return true;
	bool bMeets = Direct && !Direct->IsDead();
	if (!bMeets && Reach > 0.f)
		for (const ARDMonster* Mo : Generator->GetMonsters())
		{
			if (!Mo || Mo->IsDead()) continue;
			const FVector P = Mo->GetActorLocation();
			if (FVector::Dist2D(P, At) - Mo->GetCapsuleComponent()->GetScaledCapsuleRadius() <= Reach && FMath::Abs(P.Z - At.Z) < Mo->GetCapsuleComponent()->GetScaledCapsuleHalfHeight() + 120.f) { bMeets = true; break; }
		}
	if (!bMeets) return true;
	const float Cost = Generator->Weapons.IsValidIndex(B.Weapon) ? Generator->Weapons[B.Weapon].ManaCost : 0.f;
	if (Generator->bInfiniteMana || Mana >= Cost)
	{
		if (!Generator->bInfiniteMana) Mana = FMath::Max(0.f, Mana - Cost);
		B.bFree = false; ++ChiFreePaid;
		return true;
	}
	++ChiFreeHarmless;
	return false;
}

FString ARDDungeonGenerator::ConsoleSetTier(int32 N)
{
	// ("in console: a way to set the tier of a character, giving them the max abilities/spells/etc of that tier or taking those
	// abilities away if a lower tier is set": her growth (hit points, mana, power: GrowthTier), her locked weapons (the Martial
	// Artist's chi attacks: UnlockPerBoss a tier's boss), her later abilities (a dungeon's, once its last tier is reached), the
	// spells of the tomes' places up to it (FRDSpellDef::Slot, one a tier of the chain), and the Warrior's slashes (one a tier).
	// 0: the game's own again (what was given stays))
	URDGameInstance* GI = URDGameInstance::Of(this);
	if (!GI) return TEXT("no game instance");
	N = FMath::Clamp(N, 0, 30);
	GI->ConsoleTier = N;
	const FRDHeroDef* H = FindHero(CurrentHero);
	URDCombatComponent* Cb = PlayerCombat;
	if (!H || !Cb) return FString::Printf(TEXT("tier %d (no hero in play)"), N);
	if (N == 0) { Cb->RefreshMaxima(); return FString::Printf(TEXT("the game's own tier again (%d)"), GrowthTier()); }
	int32 Gave = 0, Took = 0;
	auto Owns = [this](FName Nm) { return Weapons.ContainsByPredicate([Nm](const FRDWeaponDef& W) { return W.Name == Nm; }); };
	// (her locked and later weapons as StartWeaponsOf gives them at this tier)
	if (!bUnlockAll && H->LockedWeapons.Num() > 0) WeaponsUnlocked = FMath::Min(H->LockedWeapons.Num(), FMath::Max(H->UnlockPerBoss, 1) * N);
	TArray<FRDWeaponDef> Base; StartWeaponsOf(*H, Base);
	auto Want = [&Base](FName Nm) { return Base.ContainsByPredicate([Nm](const FRDWeaponDef& W) { return W.Name == Nm; }); };
	for (const TArray<FRDWeaponDef>* L : { &H->LockedWeapons, &H->LaterWeapons })
		for (const FRDWeaponDef& W : *L)
		{
			const bool bW = Want(W.Name), bO = Owns(W.Name);
			if (bW && !bO) { Weapons.Add(W); ++Gave; }
			else if (!bW && bO && Cb->ForgetWeapon(W.Name)) ++Took;
		}
	// (the tomes' spells of the tiers up to it, those her hero learns; those past it forgotten (not her card's))
	int32 Learned = 0, Forgot = 0;
	for (const FRDSpellDef& S : Spells)
	{
		if (S.Slot <= 0 || !HeroCanLearnSpell(S)) continue;
		const bool bCard = H->Weapons.ContainsByPredicate([&S](const FRDWeaponDef& W) { return W.Name == S.Name; });
		if (S.Slot <= N) { if (!Cb->KnowsSpell(S.Name) && Cb->LearnSpell(S.Name)) ++Learned; }
		else if (!bCard && Cb->KnowsSpell(S.Name))
		{
			const int32 Si = FindSpell(S.Name);
			const int32 Wi = Weapons.IndexOfByPredicate([&](const FRDWeaponDef& W) { return !W.bScroll && W.Item.IsNone() && (W.SpellIndex == Si || W.Name == S.Name); });
			if (Wi >= 0 && Cb->ForgetWeapon(Weapons[Wi].Name)) ++Forgot;
		}
	}
	// (the Warrior's slashes: one a tier, the table's in its tiers' order; those past it taken off her weapons and out of her pack)
	int32 SlashGave = 0, SlashTook = 0;
	if (HeroSlashes())
	{
		TArray<int32> Order; for (int32 I = 0; I < Slashes.Num(); ++I) Order.Add(I);
		Order.StableSort([this](int32 A, int32 B) { return Slashes[A].Tier < Slashes[B].Tier; });
		for (int32 K = 0; K < Order.Num(); ++K)
		{
			const FName Sn = Slashes[Order[K]].Name;
			const int32 OnW = Weapons.IndexOfByPredicate([Sn](const FRDWeaponDef& W) { return W.Slash == Sn; });
			const bool bHas = OnW >= 0 || Cb->GetItemCount(Sn) > 0;
			if (K < N && !bHas) { Cb->AddItem(Sn, 1); SlashesGiven.AddUnique(Sn); ++SlashGave; }
			else if (K >= N && bHas)
			{
				if (OnW >= 0) Cb->RemoveSlash(OnW);
				const int32 C = Cb->GetItemCount(Sn);
				if (C > 0) Cb->RemoveItem(Sn, C);
				SlashesGiven.Remove(Sn); ++SlashTook;
			}
		}
	}
	Cb->SyncWear(); Cb->UpdateManaShares(); Cb->RefreshMaxima();
	const FString R = FString::Printf(TEXT("tier %d: %d abilities given, %d taken; %d spells learned, %d forgotten; %d slashes given, %d taken; %.0f hit points, %.0f mana"),
		N, Gave, Took, Learned, Forgot, SlashGave, SlashTook, Cb->GetMaxHealth(), Cb->GetMaxMana());
	UE_LOG(LogRDList11, Log, TEXT("RDTIER %s"), *R);
	return R;
}

int32 ARDDungeonGenerator::ConsoleShowPlaces(bool bShow)
{
	// ("in console: need way to list all points of interest in map, then make them go away again if they haven't already been
	// discovered by hand": every place of the map's (the towns, the quests' places, the 4 km cells' villages, camps, ruins,
	// caves, lairs...) and the small points of interest near her, drawn on the maps while it is on; off, the maps show again
	// only what she found (WildFound is never touched, so nothing is saved found))
	if (!bShow) { bWildShowAllPlaces = false; return 0; }
	ConsolePlaces.Reset();
	if (!bWild || !IsWildReady() || !Wild) return 0;
	TSet<int32> Seen;
	auto Add = [&](const FRDWildPlace& P) { if (!Seen.Contains(P.Id)) { Seen.Add(P.Id); ConsolePlaces.Add(P); } };
	for (int32 Ti = 0; Ti < Wild->Towns.Num(); ++Ti)
	{
		const FRDWildTown& T = Wild->Towns[Ti];
		FRDWildPlace P; P.Id = FRDWildWorld::TownIdBase + Ti; P.Kind = T.Kind == TEXT("city") ? TEXT("city") : TEXT("town"); P.Name = T.Name; P.At = T.Site; P.H = T.H; P.Town = Ti;
		Add(P);
	}
	for (const FRDWildPlace& Q : Wild->QuestPlaces) Add(Q);
	const FIntPoint C0 = Wild->PlaceCellOf(Wild->Xs, Wild->Yw), C1 = Wild->PlaceCellOf(Wild->Xn - 1.0, Wild->Ye - 1.0);
	TArray<FRDWildPlace> Tmp;
	for (int32 X = C0.X; X <= C1.X; ++X)
		for (int32 Y = C0.Y; Y <= C1.Y; ++Y) { Tmp.Reset(); Wild->PlacesIn(FIntPoint(X, Y), Tmp); for (const FRDWildPlace& P : Tmp) Add(P); }
	// (the small points of interest: within ConsolePoiKm of her (the whole continent is six million cells of them))
	const APawn* Her = UGameplayStatics::GetPlayerPawn(this, 0);
	const FVector2D Hm = Her ? FVector2D(Her->GetActorLocation().X / 100.0, Her->GetActorLocation().Y / 100.0) : FVector2D::ZeroVector;
	if (Her)
	{
		const int32 Rc = FMath::CeilToInt(ConsolePoiKm * 1000.0 / FRDWildWorld::PoiCellM);
		const FIntPoint Pc = Wild->PoiCellOf(Hm.X, Hm.Y);
		for (int32 Dx = -Rc; Dx <= Rc; ++Dx)
			for (int32 Dy = -Rc; Dy <= Rc; ++Dy)
			{
				Tmp.Reset(); Wild->PoisIn(Pc + FIntPoint(Dx, Dy), Tmp);
				for (const FRDWildPlace& P : Tmp) if (FVector2D::Distance(P.At, Hm) <= ConsolePoiKm * 1000.0) Add(P);
			}
	}
	ConsolePlaces.StableSort([&Hm](const FRDWildPlace& A, const FRDWildPlace& B) { return FVector2D::DistSquared(A.At, Hm) < FVector2D::DistSquared(B.At, Hm); });
	bWildShowAllPlaces = true;
	UE_LOG(LogRDList11, Log, TEXT("RDPOIS %d places listed"), ConsolePlaces.Num());
	return ConsolePlaces.Num();
}

TArray<FString> ARDDungeonGenerator::GetConsolePlaceLines() const
{
	TArray<FString> Out;
	const APawn* Her = UGameplayStatics::GetPlayerPawn(this, 0);
	const FVector2D Hm = Her ? FVector2D(Her->GetActorLocation().X / 100.0, Her->GetActorLocation().Y / 100.0) : FVector2D::ZeroVector;
	for (int32 I = 0; I < ConsolePlaces.Num(); ++I)
	{
		const FRDWildPlace& P = ConsolePlaces[I];
		Out.Add(FString::Printf(TEXT("%d|%s|%s|%.0f|%.0f|%d|%.2f"), I + 1, *P.Name, *P.Kind, P.At.X, P.At.Y, WildFound.Contains(P.Id) ? 1 : 0, FVector2D::Distance(P.At, Hm) / 1000.0));
	}
	return Out;
}

bool ARDDungeonGenerator::ConsoleGoToPlace(const FString& What)
{
	if (!bWild || !IsWildReady()) return false;
	if (ConsolePlaces.Num() == 0) { const bool bWas = bWildShowAllPlaces; ConsoleShowPlaces(true); bWildShowAllPlaces = bWas; }
	const FString W = What.TrimStartAndEnd();
	int32 K = -1;
	if (W.IsNumeric()) K = FCString::Atoi(*W) - 1;
	else for (int32 I = 0; I < ConsolePlaces.Num() && K < 0; ++I) if (ConsolePlaces[I].Name.Contains(W, ESearchCase::IgnoreCase)) K = I;
	if (!ConsolePlaces.IsValidIndex(K)) return false;
	const FRDWildPlace P = ConsolePlaces[K];
	// (a town by fast travel, to its gate; anywhere else put down 6 m short of it, the chunks there made at once)
	if (P.Town >= 0)
	{
		bTravelForced = true;
		const bool bOk = WildTravelToTown(Wild->Towns[P.Town].Name);
		bTravelForced = false;
		return bOk;
	}
	const bool bOk = WildPutHer((float)(P.At.X - 6.0), (float)P.At.Y);
	UE_LOG(LogRDList11, Log, TEXT("RDPOIS to %s (%s) at %.0f, %.0f: %s"), *P.Name, *P.Kind, P.At.X, P.At.Y, bOk ? TEXT("there") : TEXT("refused"));
	return bOk;
}

void ARDDungeonGenerator::SetMapRevealAll(bool bAll)
{
	// ("in console: a way to reveal the entire map and then to make it return to normal": a drawing switch; what she has seen is
	// not changed, so a save keeps her own)
	bMapRevealAll = bAll;
	WildFogVersion = -1; WildMiniTime = -100.0;
	UE_LOG(LogRDList11, Log, TEXT("RDMAP the whole map %s"), bAll ? TEXT("shown") : TEXT("as she has seen it"));
}

ARDMonster* ARDDungeonGenerator::SpawnTestAmbusher(FVector At, int32 Tier)
{
	// (as the wilds' ambush makes its monsters: one of the tier's kinds, on the wild section, hunting her a minute)
	ARDSection* Ws_ = bWild ? EnsureWildSection() : nullptr;
	if (!Ws_ || Monsters.Num() == 0) { UE_LOG(LogRDList11, Warning, TEXT("RDGUARD no wild section or monster kinds")); return nullptr; }
	TArray<int32> Kinds; WildKindsForTier(FMath::Max(Tier, 1), Kinds);
	if (Kinds.Num() == 0) return nullptr;
	const FRDMonsterDef& Def = Monsters[Kinds[0]];
	FHitResult H;
	FCollisionQueryParams Q(TEXT("RDTestAmbusher"), false);
	if (APawn* P = GetWorld()->GetFirstPlayerController() ? GetWorld()->GetFirstPlayerController()->GetPawn() : nullptr) Q.AddIgnoredActor(P);
	const float Gz = GetWorld()->LineTraceSingleByChannel(H, At + FVector(0, 0, 3000.f), At - FVector(0, 0, 6000.f), ECC_Visibility, Q) ? H.ImpactPoint.Z : WildGroundZ(At);
	ARDMonster* M = SpawnWildMonsterAt(Def, FVector(At.X, At.Y, Gz), 0.f, 4242 + WildRoamers.Num(), FMath::Max(Tier, 1), 1.f, TEXT("Ambusher"));
	if (!M) return nullptr;
	M->bHunting = true; M->HuntUntil = GetWorld()->GetTimeSeconds() + 60.f;
	WildRoamers.Add(M);
	return M;
}
