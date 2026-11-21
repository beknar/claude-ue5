// The user's list of 2026-11-16 (docs/improvements14.txt; the plan docs/improvements14_plan.md), its eighth phase: the wilds'
// people hurt and killed (items 9 and 11): "if a random monster encounter comes across a wandering NPC before it reaches the
// player, it should attack the NPC instead, damaging and killing it" and "kill NPCs and loot them". A person of the wilds (a
// farmstead's family, a traveller, one the director met her with, a freed captive, a scenery's people: no section) takes her blows
// and bolts and a wild monster's (one that has it nearer than her takes it for its foe), runs from what struck it, and dies: its
// body lies where it fell (the Dwarf pack's death retargeted onto the townsfolk, 930 clips), with a pile of what it carried and a
// few gold by it (930 data: SourceArt/wilderness/folk14.json). The people laid again with their chunk (the farms', the captives',
// the scenery's) lie dead by their key in the game's WildKilled (11 << 40). A child and a quest's people are struck but never die;
// a caged captive is behind its bars.
#include "RD/RDDungeonGenerator.h"
#include "RD/RDTown.h"
#include "RD/RDGameInstance.h"
#include "RD/RDMistward.h"
#include "RD/RDCombat.h"
#include "RD/RDWild.h"
#include "Components/CapsuleComponent.h"
#include "Components/SkeletalMeshComponent.h"
#include "Components/StaticMeshComponent.h"
#include "Animation/AnimSequenceBase.h"
#include "Engine/World.h"
DEFINE_LOG_CATEGORY_STATIC(LogRDFolk14, Log, All);

// (WildKilled's range of the people's deaths: (11 << 40) + its kind (0 a farm's family, 1 a structure's captive, 2 a scenery's) << 37
// + its place's id x 16 + its slot there; the ranges below are the farms' containers (1) ... the farm animals' (10))
static constexpr int64 RDFolkKeys14 = 11LL << 40;

int64 ARDDungeonGenerator::WildFolkKey14(int32 Kind, int64 Id, int32 N)
{
	return RDFolkKeys14 + ((int64)(Kind & 7) << 37) + (Id & ((1LL << 33) - 1)) * 16 + (N & 15);
}

bool ARDDungeonGenerator::IsWildFolkDead14(int64 Key) const
{
	// (the game's kept keys as a set (IsWildKeyKept14, the ninth phase's: read again only when the list changes))
	return Key >= RDFolkKeys14 && IsWildKeyKept14(Key);
}

void ARDDungeonGenerator::KeepWildFolk14(ARDTownsfolk* T, int64 Key)
{
	if (!T) return;
	T->WildDeadKey14 = Key;
	if (bWildFolkHurt14 && IsWildFolkDead14(Key)) T->LayWildDead14();
}

const TArray<ARDTownsfolk*>& ARDDungeonGenerator::WildPeople14() const
{
	// (gathered once a frame (PR #86's review: every monster's foe, every bolt and shot gathered it again); the four lists hold
	// nobody twice; a caller checks IsValid, as one destroyed in the frame stays listed until the next)
	if (WildPeopleFrame14 != GFrameCounter)
	{
		WildPeopleFrame14 = GFrameCounter;
		WildPeopleCache14.Reset();
		auto Add = [&](const TWeakObjectPtr<ARDTownsfolk>& W) { if (ARDTownsfolk* T = W.Get(); IsValid(T)) WildPeopleCache14.Add(T); };
		for (const FRDWildFarmRec& F : WildFarms) for (const TWeakObjectPtr<ARDTownsfolk>& W : F.Folk) Add(W);
		for (const TWeakObjectPtr<ARDTownsfolk>& W : WildSiteFolk) Add(W);
		for (const TWeakObjectPtr<ARDTownsfolk>& W : WildRoamFolk) Add(W);
		for (const FTraveller& G : WildTravellers) for (const TWeakObjectPtr<ARDTownsfolk>& W : G.Folk) Add(W);
		for (const TWeakObjectPtr<ARDTownsfolk>& W : WildVillageFolk15) Add(W);          // (the list of 2026-11-20: the villages' households)
	}
	return WildPeopleCache14;
}

bool ARDDungeonGenerator::IsWildPrey14(const ARDTownsfolk* T, const FVector& From) const
{
	// (a monster's prey: one that can die (a child or a quest's people is none: a structure's guards would chase its quest's giver
	// for ever), out in the open (not indoors or in bed), in the monster's sight, and near her: what happens far from her is not
	// played out (PR #86's review: a lair's monsters would have killed a farm's family 2 km before she came, and kept it dead)
	if (!IsValid(T) || !T->CanBeHurt14() || T->IsWildProtected14() || T->IsWildIndoors() || T->IsInBed()) return false;
	const AActor* Her = PlayerCombat ? PlayerCombat->GetOwner() : nullptr;
	if (!Her || FVector::Dist2D(Her->GetActorLocation(), T->GetActorLocation()) > WildFolkNearHerCm14) return false;
	return !WildWayBlocked14(From + FVector(0, 0, 40.f), T->GetActorLocation() + FVector(0, 0, 40.f), 0.f, nullptr);
}

FString ARDDungeonGenerator::WildFolkLootOf14(const ARDTownsfolk* T, float& Health, int32& GoldLo, int32& GoldHi) const
{
	// (its line by a whole word of its title ("farmhand of Oakfield", "a weary pilgrim", "Freed captive"), then its role, the table's
	// order first; else "default")
	Health = 50.f; GoldLo = 0; GoldHi = 0;
	if (!T) return FString();
	TArray<FString> Words; T->Title.ToLower().ParseIntoArrayWS(Words);
	const FString RoleW = T->GetRoleName().ToLower();
	const FString* Use = nullptr; const FString* Def = nullptr;
	TArray<FString> P;
	for (const FString& L : WildFolkLoot14)
	{
		FString Who; if (!L.Split(TEXT("|"), &Who, nullptr)) continue;
		Who = Who.ToLower();
		if (Who == TEXT("default")) { if (!Def) Def = &L; continue; }
		if (Words.Contains(Who) || RoleW == Who) { Use = &L; break; }
	}
	if (!Use) Use = Def;
	if (!Use) return FString();
	Use->ParseIntoArray(P, TEXT("|"), false);
	if (P.Num() < 5) return FString();
	// (its hit points and gold grown with the wilds' tier where it stands, as the monsters' blows grow (WildGoldAt's factor))
	const float Grow = (float)WildGoldAt(1000, T->GetActorLocation()) / 1000.f;
	Health = FMath::Max(FCString::Atof(*P[1]) * FMath::Max(Grow, 1.f), 1.f);
	GoldLo = FCString::Atoi(*P[2]); GoldHi = FCString::Atoi(*P[3]);
	// (the things: the rest of the line, "Item|min|max|chance;...")
	FString Drops;
	for (int32 I = 4; I < P.Num(); ++I) { if (I > 4) Drops += TEXT("|"); Drops += P[I]; }
	return Drops;
}

int32 ARDDungeonGenerator::HitWildFolkInArc14(const FVector& L, const FVector& Fw, float Reach, float MinCos, float Dmg, FName Sound, AActor* Her)
{
	if (!bWildFolkHurt14) return 0;
	// (as the farms' animals (HitFarmAnimalsInArc14): within her weapon's reach and its arc, or close)
	int32 N = 0;
	for (ARDTownsfolk* T : WildPeople14())
	{
		if (!IsValid(T) || !T->CanBeHurt14()) continue;
		const FVector C = T->GetActorLocation();
		const FVector D = (C - L) * FVector(1, 1, 0);
		const float Dist = D.Size() - 34.f;
		if (Dist > Reach || FMath::Abs(C.Z - L.Z) > 220.f) continue;
		if (Dist > 40.f && FVector::DotProduct(D.GetSafeNormal(), Fw) < MinCos) continue;
		if (!Sound.IsNone()) PlaySoundAt(Sound, C);
		AddHitText(C + FVector(0, 0, 80.f), Dmg, false);
		T->TakeWildHit14(Dmg, Her);
		++N;
	}
	return N;
}

ARDTownsfolk* ARDDungeonGenerator::WildFolkOnSegment14(const FVector& A, const FVector& B, float Pad, float& OutT, FVector& OutAt) const
{
	// (the bolt against each body's upright axis, as the monsters' capsules)
	ARDTownsfolk* Best = nullptr; OutT = 2.f;
	if (!bWildFolkHurt14) return nullptr;
	const FVector Ab = B - A;
	for (ARDTownsfolk* T : WildPeople14())
	{
		if (!IsValid(T) || !T->CanBeHurt14()) continue;
		const FVector C = T->GetActorLocation(), A0 = C - FVector(0, 0, 56.f), A1 = C + FVector(0, 0, 56.f);
		FVector P, Q;
		FMath::SegmentDistToSegmentSafe(A, B, A0, A1, P, Q);
		if (FVector::Dist(P, Q) > 34.f + Pad) continue;
		const float Tt = Ab.IsNearlyZero() ? 0.f : FVector::DotProduct(P - A, Ab) / Ab.SizeSquared();
		if (Tt < OutT) { OutT = Tt; Best = T; OutAt = Q + (P - Q).GetSafeNormal() * 30.f; }
	}
	return Best;
}

void ARDDungeonGenerator::OnWildFolkKilled14(ARDTownsfolk* T, AActor* By)
{
	if (!T) return;
	++WildFolkKilled14;
	URDGameInstance* GI = URDGameInstance::Of(this);
	if (GI && T->WildDeadKey14 >= 0)
	{
		GI->WildKilled.AddUnique(T->WildDeadKey14);
	}
	// (what it carried, drawn from a hash (no stream of the play's): its key, or the actor's name for one never laid again)
	float Hp = 0.f; int32 Lo = 0, Hi = 0;
	const FString Drops = WildFolkLootOf14(T, Hp, Lo, Hi);
	TArray<FString> Lines; Drops.ParseIntoArray(Lines, TEXT(";"), true);
	const uint32 H0 = HashCombine(T->WildDeadKey14 >= 0 ? GetTypeHash(T->WildDeadKey14) : GetTypeHash(T->GetFName()), 0xF014u ^ (uint32)(IsWildReady() ? Wild->Seed : 0));
	const TArray<FName> Got = RollDropLines(Lines, H0);
	int32 Gold = Hi > 0 ? Lo + (int32)(HashCombine(H0, 77u) % (uint32)FMath::Max(Hi - Lo + 1, 1)) : 0;
	if (Gold > 0) Gold = FMath::Max(WildGoldAt(Gold, T->GetActorLocation()), 1);
	LastWildFolkDrops14 = Got; LastWildFolkGold14 = Gold;
	// (by the body, on its right (the death clip lays it on its back), traced down from the body's own height (a farmhouse's floor
	// stands over the ground: PR #86's review); where a wall or fence stands within that, at the body)
	const FVector Bc = T->GetActorLocation();
	FVector At = Bc + T->GetActorRightVector() * 80.f;
	if (WildWayBlocked14(Bc, At, 20.f, T)) At = Bc;
	if (Got.Num() > 0)
	{
		TArray<float> Wr; Wr.Init(-1.f, Got.Num());
		if (ARDLootPile* Lp = DropLoot(At, Got, Wr))
		{
			Lp->bHers = false; Lp->bHarvest = false; Lp->Gold = Gold; Lp->Owner14 = T->Title;
			WildRoamPiles.Add(Lp);
		}
	}
	const bool bHers = By && PlayerCombat && By == PlayerCombat->GetOwner();
	UE_LOG(LogRDFolk14, Log, TEXT("RDWILDFOLK %s killed by %s (%lld): %s, %d gold"), *T->Title, bHers ? TEXT("her") : By ? *By->GetName() : TEXT("nothing"),
		T->WildDeadKey14, Got.Num() ? *FString::JoinBy(Got, TEXT(", "), [](const FName& N) { return N.ToString(); }) : TEXT("nothing"), Gold);
	// (killed by a monster near her: she is told)
	if (!bHers && PlayerCombat && PlayerCombat->GetOwner() && FVector::Dist2D(PlayerCombat->GetOwner()->GetActorLocation(), T->GetActorLocation()) < 6000.f)
		PlayerCombat->ShowMessage(FString::Printf(TEXT("%s is killed"), *T->Title));
}

TArray<FString> ARDDungeonGenerator::GetWildFolkLines14() const
{
	// "i|title|role|x|y|z|health|dead|protected|fleeing|key|hits|flees|killed by|hurt"
	TArray<FString> Out;
	const TArray<ARDTownsfolk*>& All = WildPeople14();
	for (int32 I = 0; I < All.Num(); ++I)
	{
		const ARDTownsfolk* T = All[I]; const FVector L = T->GetActorLocation();
		Out.Add(FString::Printf(TEXT("%d|%s|%s|%.0f|%.0f|%.0f|%.1f|%d|%d|%d|%lld|%d|%d|%s|%d"), I, *T->Title, *T->GetRoleName(), L.X, L.Y, L.Z, T->GetWildHealth14(),
			T->IsWildDead14() ? 1 : 0, T->IsWildProtected14() ? 1 : 0, T->IsWildFleeing14() ? 1 : 0, T->WildDeadKey14, T->WildHitsTaken14, T->WildFlees14, *T->WildKilledBy14,
			T->CanBeHurt14() ? 1 : 0));
	}
	return Out;
}

ARDTownsfolk* ARDDungeonGenerator::GetWildPerson14(int32 I) const
{
	const TArray<ARDTownsfolk*>& All = WildPeople14();
	return All.IsValidIndex(I) ? All[I] : nullptr;
}

// ================================================================================================ the person

bool ARDTownsfolk::CanBeHurt14() const
{
	if (bWildDead14 || !Gen || !Gen->bWild || !Gen->bWildFolkHurt14 || Section) return false;
	// (a captive in its cage: the bars between)
	if (WildSiteCage.IsValid() && !bWildGiven) return false;
	return true;
}

bool ARDTownsfolk::IsWildProtected14() const
{
	// (a child; a quest's giver and its people (the giver is laid again whenever its structure is: kept alive, the quest is kept))
	return TownRole == ERDTownRole::Child || WildQuestSite != 0;
}

float ARDTownsfolk::GetWildHealth14() const
{
	if (bWildDead14) return 0.f;
	if (WildHealth14 >= 0.f) return WildHealth14;
	float Hp = 50.f; int32 Lo = 0, Hi = 0;
	if (Gen) Gen->WildFolkLootOf14(this, Hp, Lo, Hi);
	return Hp;
}

bool ARDTownsfolk::IsWildFleeing14() const
{
	return GetWorld() && GetWorld()->GetTimeSeconds() < WildFleeUntil14 && !bWildDead14;
}

void ARDTownsfolk::InterruptLife14()
{
	// (out of its bed, its talk, its work and its way)
	if (bInBed) { bInBed = false; SetActorLocationAndRotation(PreBed, FRotator(0.f, HomeYaw, 0.f)); }
	bSleeping = false; FaceUntil = -100.f;
	if (Act != 0) EndWork();
	Path.Reset();
}

void ARDTownsfolk::RunFrom14(AActor* From, float Now, float Seconds)
{
	WildFleeFrom14 = From;
	WildFleeAt14 = From ? From->GetActorLocation() : GetActorLocation() - GetActorForwardVector() * 100.f;
	if (Now >= WildFleeUntil14) ++WildFlees14;
	WildFleeUntil14 = FMath::Max(WildFleeUntil14, Now + Seconds);
	InterruptLife14();
}

void ARDTownsfolk::ScareWild14(AActor* From)
{
	// (a monster after it, close: it stops where it is and cowers, facing it, while the monster is near (renewed each tick the monster
	// is after it); struck, it runs a short way. Running at every sight of one, travellers walking on and running again were never
	// caught (the first test: a monster chased three of them for a minute and landed nothing))
	if (!CanBeHurt14() || !GetWorld()) return;
	const float Now = GetWorld()->GetTimeSeconds();
	if (Now >= WildCowerUntil14) InterruptLife14();
	WildCowerUntil14 = Now + 1.5f;
	WildFleeFrom14 = From;
	if (From) WildFleeAt14 = From->GetActorLocation();
}

bool ARDTownsfolk::TakeWildHit14(float Dmg, AActor* From)
{
	if (!CanBeHurt14() || !GetWorld()) return false;
	const float Now = GetWorld()->GetTimeSeconds();
	if (WildHealth14 < 0.f) WildHealth14 = GetWildHealth14();
	WildHealth14 -= FMath::Max(Dmg, 0.f);
	++WildHitsTaken14;
	if (IsWildProtected14()) WildHealth14 = FMath::Max(WildHealth14, 1.f);
	if (WildHealth14 > 0.f)
	{
		WildHitUntil14 = Now + 0.45f;
		// (turned on her, it fights on (the ninth phase); else it runs a short way)
		if (!(bWildHostile14 && !IsWildProtected14())) RunFrom14(From, Now, 2.f);
		return false;
	}
	// (killed: its body lies where it fell; nothing of it stops her or takes F (no flight counted: PR #86's review))
	InterruptLife14();
	bWildDead14 = true; WildDeadAt14 = Now; WildHealth14 = 0.f; WildFleeUntil14 = -100.f;
	RoadPath.Reset(); SetProp(NAME_None); SetLantern(false);
	WildKilledBy14 = !From ? FString() : (Gen && Gen->GetPlayerCombat() && From == Gen->GetPlayerCombat()->GetOwner()) ? TEXT("her") : From->GetName();
	if (Capsule) Capsule->SetCollisionEnabled(ECollisionEnabled::NoCollision);
	PlayDie14(false);
	if (Gen) Gen->OnWildFolkKilled14(this, From);
	return true;
}

void ARDTownsfolk::LayWildDead14()
{
	// (laid again with its chunk: dead where it stands, the death clip's last pose)
	bWildDead14 = true; WildHealth14 = 0.f; WildDeadAt14 = -100.f;
	RoadPath.Reset(); Path.Reset(); SetProp(NAME_None); SetLantern(false);
	if (Capsule) Capsule->SetCollisionEnabled(ECollisionEnabled::NoCollision);
	PlayDie14(true); bWildLaidDead14 = true;
}

void ARDTownsfolk::PlayDie14(bool bAtEnd)
{
	UAnimationAsset* A = WorkClip(TEXT("Die"));
	bWildDieClip14 = A != nullptr;
	if (!A) return;
	CurAnim = A; CurRate = 1.f;
	Body->PlayAnimation(A, false);
	Body->SetPlayRate(1.f);
	if (bAtEnd)
	{
		if (const UAnimSequenceBase* S = Cast<UAnimSequenceBase>(A)) Body->SetPosition(FMath::Max(S->GetPlayLength() - 0.02f, 0.f), false);
		// (its pose made now, seen or not: a body out of view keeps the pose it had)
		Body->TickAnimation(0.f, false); Body->RefreshBoneTransforms();
	}
}

bool ARDTownsfolk::TickWild14(float Dt, float Now)
{
	if (bWildDead14)
	{
		// (laid dead with its chunk: the death clip's last pose set on its first tick (set as it was spawned, before its body's
		// animation was made, it stood: the first test's farmhand laid again had its head 1.6 m up))
		if (bWildLaidDead14) { bWildLaidDead14 = false; PlayDie14(true); }
		// (no death clip on its body: it tips over backwards over 0.6 s (the farms' animals' way))
		if (!bWildDieClip14 && Gen && Gen->Townsfolk.IsValidIndex(Def))
		{
			const float T = WildDeadAt14 < 0.f ? 1.f : FMath::Clamp((Now - WildDeadAt14) / 0.6f, 0.f, 1.f);
			const float E = T * T * (3.f - 2.f * T);
			const FRDTownsfolkDef& D = Gen->Townsfolk[Def];
			Body->SetRelativeRotation(FQuat(FVector(0, 1, 0), FMath::DegreesToRadians(-85.f * E)) * FRotator(0.f, D.MeshYaw, 0.f).Quaternion());
			Body->SetRelativeLocation(FVector(0, 0, -HalfHeight + D.MeshZ + 20.f * E));
		}
		return true;
	}
	if (!Gen) return false;
	// (the ninth phase (RDList14i.cpp): turned on her by a lock picked or broken: it runs at her and strikes, its flinch first; a child
	// or a quest's people run from her instead)
	if (bWildHostile14)
	{
		if (IsWildProtected14())
		{
			const AActor* Her = WildFoe14.Get();
			if (!Her || FVector::Dist2D(Her->GetActorLocation(), GetActorLocation()) > Gen->WildCalmCm14) CalmWild14();
			else { WildFleeFrom14 = WildFoe14; WildFleeUntil14 = FMath::Max(WildFleeUntil14, Now + 0.5f); }
		}
		else if (Now < WildHitUntil14 && WildSwingT14 < 0.f)
		{
			if (UAnimationAsset* H = WorkClip(TEXT("Hit")); H && CurAnim != H) { CurAnim = H; CurRate = 1.f; Body->PlayAnimation(H, false); Body->SetPlayRate(1.f); }
			return true;
		}
		else if (TickHostile14(Dt, Now)) return true;
	}
	// (a monster after it, not struck just now: it stands and cowers, facing it)
	if (Now >= WildFleeUntil14 && Now < WildCowerUntil14)
	{
		const FVector Fl = WildFleeFrom14.IsValid() ? WildFleeFrom14->GetActorLocation() : WildFleeAt14;
		FVector Df = Fl - GetActorLocation(); Df.Z = 0.f;
		if (!Df.IsNearlyZero(1.f)) SetActorRotation(FRotator(0.f, FMath::RInterpConstantTo(GetActorRotation(), Df.Rotation(), Dt, 360.f).Yaw, 0.f));
		SetClip(false);
		return true;
	}
	if (Now >= WildFleeUntil14) return false;
	// (struck: its flinch first)
	if (Now < WildHitUntil14)
	{
		if (UAnimationAsset* H = WorkClip(TEXT("Hit")); H && CurAnim != H) { CurAnim = H; CurRate = 1.f; Body->PlayAnimation(H, false); Body->SetPlayRate(1.f); }
		return true;
	}
	// (inside its house it cowers where it is: the way out is its door)
	if (bWildIndoors) { SetClip(false); return true; }
	const FVector L = GetActorLocation();
	const FVector From = WildFleeFrom14.IsValid() ? WildFleeFrom14->GetActorLocation() : WildFleeAt14;
	FVector Aw = L - From; Aw.Z = 0.f;
	const FVector Dir = Aw.IsNearlyZero(1.f) ? -GetActorForwardVector() : Aw.GetSafeNormal();
	const float Sp = FMath::Max(Gen->WildFolkRunSpeed14, 50.f);
	// (away from it, or as near that as a wall lets it)
	StepOnGround14(Dir, Sp, Dt);
	UAnimationAsset* Run = WorkClip(TEXT("Run"));
	if (Run) PlayAnim(Run, 1.f); else { bWalkClip = true; PlayAnim(WalkAnim, Sp / FMath::Max(ClipSpeed, 1.f)); }
	return true;
}
