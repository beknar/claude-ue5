// The user's list of 2026-11-20 (docs/improvements15.txt; the plan docs/improvements15_plan.md), its ninth phase: the caves. Item 23,
// "a cave complex ... of the same Tier that the region is coded for", the user's choice: every landmark tower (the broken towers, one in
// each 6 km square of the open lands, RDWildScenery13.cpp's TickWildLandmark13) holds a cave's mouth at its foot. One cave level (935,
// a Save As copy of the castle in the Cave theme) serves them all: the tower's cell is the cave's key (its tiers opened, its first set's
// chests, its bosses under "cave:<i>_<j>"), the region's tier (FRDWildWorld::TierAt at the tower) is every one of its tiers. The castle's
// own systems are off there: the key chain, the final boss, the arena, the cells and the bosses' unique rewards (slashes, chi attacks,
// the later dungeons' abilities); its beasts are the wilds' kinds of its tier.
#include "RD/RDDungeonGenerator.h"
#include "RD/RDWild.h"
#include "RD/RDGameInstance.h"
#include "RD/RDCombat.h"
#include "RD/RDTown.h"
#include "Components/StaticMeshComponent.h"
#include "Engine/World.h"
DEFINE_LOG_CATEGORY_STATIC(LogRDList15h, Log, All);


void ARDDungeonGenerator::LayCaveMouth15(UStaticMeshComponent* Tower, const FVector2D& SiteM)
{
	if (!Tower || !CaveMouthMesh15 || CaveLevel15.IsEmpty() || !IsWildReady())
	{
		if (UStaticMeshComponent* M = CaveMouth15.Get()) M->DestroyComponent();
		if (UStaticMeshComponent* M = CaveMouthB15.Get()) M->DestroyComponent();
		if (UStaticMeshComponent* D = CaveDark15.Get()) D->DestroyComponent();
		CaveMouth15.Reset(); CaveMouthB15.Reset(); CaveDark15.Reset(); CaveCell15 = FIntPoint(INT32_MAX, INT32_MAX);
		return;
	}
	// (the foot between two buttresses (the tower's five stand at 0, 72, ... degrees of its own frame), on the ground there)
	const float A = FMath::DegreesToRadians(CaveGapDeg15);
	const FVector Out = Tower->GetComponentTransform().TransformVectorNoScale(FVector(FMath::Cos(A), -FMath::Sin(A), 0.f)).GetSafeNormal2D();
	const FVector2D F2 = SiteM * 100.0 + FVector2D(Out) * CaveFootRadius15;
	const FVector Foot(F2.X, F2.Y, Wild->ToZ(Wild->Height(F2.X / 100.0, F2.Y / 100.0)));
	const FRotator Face = Out.Rotation();
	const FTransform Fr(FRotator(0.f, Face.Yaw, 0.f), Foot);
	auto Make = [this](TWeakObjectPtr<UStaticMeshComponent>& W, UStaticMesh* Mesh, UMaterialInterface* Mat, bool bCollide) -> UStaticMeshComponent*
	{
		UStaticMeshComponent* C = W.Get();
		if (!C)
		{
			C = NewObject<UStaticMeshComponent>(this);
			C->SetMobility(EComponentMobility::Movable);
			C->SetCollisionEnabled(bCollide ? ECollisionEnabled::QueryAndPhysics : ECollisionEnabled::NoCollision);
			if (bCollide) C->SetCollisionResponseToAllChannels(ECR_Block);
			C->SetCastShadow(bCollide);
			C->RegisterComponent();
			W = C;
		}
		C->SetStaticMesh(Mesh);
		if (Mat) C->SetMaterial(0, Mat);
		return C;
	};
	if (UStaticMeshComponent* M = Make(CaveMouth15, CaveMouthMesh15, nullptr, true))
		M->SetWorldTransform(FTransform(FRotator(0.f, Face.Yaw + CaveMouthYaw15, 0.f), Fr.TransformPosition(CaveMouthOffset15), CaveMouthScale15));
	// (its mirror across the mouth's middle: the arch's own X mirrored, its place across the frame's Y)
	if (bCaveMouthMirror15)
	{
		if (UStaticMeshComponent* M = Make(CaveMouthB15, CaveMouthMesh15, nullptr, true))
			M->SetWorldTransform(FTransform(FRotator(0.f, Face.Yaw + CaveMouthYaw15, 0.f), Fr.TransformPosition(FVector(CaveMouthOffset15.X, -CaveMouthOffset15.Y, CaveMouthOffset15.Z)),
				FVector(-CaveMouthScale15.X, CaveMouthScale15.Y, CaveMouthScale15.Z)));
	}
	if (CaveDarkMesh15)
		if (UStaticMeshComponent* D = Make(CaveDark15, CaveDarkMesh15, CaveDarkMaterial15, false))
			D->SetWorldTransform(FTransform(FRotator(Fr.GetRotation()) + CaveDarkTurn15, Fr.TransformPosition(CaveDarkOffset15), CaveDarkScale15));
	CaveMouthAt15 = Foot; CaveMouthOut15 = Out;
	CaveCell15 = FIntPoint(FMath::FloorToInt(SiteM.X / WildLandmarkCellM), FMath::FloorToInt(SiteM.Y / WildLandmarkCellM));
	UE_LOG(LogRDList15h, Log, TEXT("RDCAVE15 mouth of the tower (%.0f, %.0f) m: cell %d_%d, tier %d"), SiteM.X, SiteM.Y, CaveCell15.X, CaveCell15.Y, Wild->TierAt(SiteM.X, SiteM.Y));
}

bool ARDDungeonGenerator::CaveMouthNear15(const FVector& From, float Reach) const
{
	if (!CaveMouth15.IsValid()) return false;
	return FVector::Dist2D(From, CaveMouthAt15) < FMath::Min(Reach, 450.f) && FMath::Abs(From.Z - CaveMouthAt15.Z) < 400.f;
}

bool ARDDungeonGenerator::CaveMouthFirst15(const FVector& From, float Reach) const
{
	// (PR #101's review: the nearest of everything F reaches out there takes it, the mouth too: a station, a scenery's use, a point of
	// interest, a wild door or container, a person nearer than the mouth keeps F)
	if (!CaveMouthNear15(From, Reach)) return false;
	const float Dm = FVector::Dist2D(CaveMouthAt15, From);
	FVector Sa; FName Sk;
	if (WildStationNear14(From, Sa, Sk) && FVector::Dist2D(Sa, From) < Dm) return false;
	if (const FSceneryUse* U = WildSceneryUseNear(From); U && FVector::Dist2D(U->At, From) < Dm) return false;
	if (const FRDWildPoiLive* P = WildPoiNear(From, 320.f); P && FVector::Dist2D(P->At, From) < Dm) return false;
	int32 Di = -1;
	if (const ARDWildChunk* C = bWildHouseInsides ? WildDoorNear(From, 190.f, Di) : nullptr; C && C->Doors.IsValidIndex(Di) && FVector::Dist2D(C->Doors[Di].At, From) < Dm) return false;
	if (const ARDTownsfolk* T = WildFolkForF(From); T && FVector::Dist2D(T->GetActorLocation(), From) < Dm) return false;
	return true;
}

bool ARDDungeonGenerator::EnterCave15()
{
	if (!bWild || !CaveMouth15.IsValid() || CaveLevel15.IsEmpty() || !IsWildReady()) return false;
	if (PlayerCombat && PlayerCombat->IsDead()) return false;
	const FVector2D SiteM = WildLandmarkAt;
	const int32 Tier = FMath::Clamp(Wild->TierAt(SiteM.X, SiteM.Y), 1, GameTierMax);
	// (she comes back 6 m out before the mouth, facing away from the tower)
	const FVector2D B2 = FVector2D(CaveMouthAt15) + FVector2D(CaveMouthOut15) * 600.0;
	const FVector Back(B2.X, B2.Y, Wild->ToZ(Wild->Height(B2.X / 100.0, B2.Y / 100.0)) + 100.f);
	URDGameInstance* GI = URDGameInstance::Of(this);
	const FString Key = FString::Printf(TEXT("cave:%d_%d"), CaveCell15.X, CaveCell15.Y);
	if (GI && !bTravelDryRun) { GI->CaveKey15 = Key; GI->CaveTier15 = Tier; }
	if (!DescendToCatacombs(Back, CaveMouthOut15.Rotation().Yaw, CaveLevel15)) return false;
	if (GI && !bTravelDryRun) GI->ReturnTown = TEXT("the Broken Tower");          // (the way back's label)
	LastTravel = TEXT("cave");
	UE_LOG(LogRDList15h, Log, TEXT("RDCAVE15 into %s (tier %d)%s"), *Key, Tier, bTravelDryRun ? TEXT(" (dry run)") : TEXT(""));
	return true;
}

void ARDDungeonGenerator::ApplyCave15()
{
	const URDGameInstance* GI = URDGameInstance::Of(this);
	const FString Key = GI && !GI->CaveKey15.IsEmpty() ? GI->CaveKey15 : FString(TEXT("cave:test"));
	const int32 Tier = FMath::Clamp(GI && GI->CaveTier15 > 0 ? GI->CaveTier15 : CaveDefaultTier15, 1, GameTierMax);
	DungeonKey = Key;
	DungeonTierBase = Tier - 1; DungeonTierCap = Tier;          // (every tier of the level is the game's Tier: MapTier's cap)
	bFinalBossOn = false;          // (the title is the level's own, 935's from cave15.json (PR #101's review))
	CaveKindsTier15 = -1; TArray<int32> K; CaveKinds15(Tier, K);          // (worked out once: every tier is the one game tier)
	UE_LOG(LogRDList15h, Log, TEXT("RDCAVE15 the cave %s: tier %d (base %d, cap %d)"), *DungeonKey, Tier, DungeonTierBase, DungeonTierCap);
}

void ARDDungeonGenerator::CaveKinds15(int32 GameTier, TArray<int32>& Out) const
{
	Out.Reset();
	// (PR #101's review: worked out once for the level's tier, not at every spawn and every mean of the factors)
	if (CaveKindsTier15 == GameTier) { Out = CaveKindsCache15; return; }
	ON_SCOPE_EXIT { CaveKindsTier15 = GameTier; CaveKindsCache15 = Out; };
	auto Excluded = [this](const FString& Name)
	{
		for (const FString& X : CaveExclude15) if (!X.IsEmpty() && Name.Contains(X, ESearchCase::CaseSensitive)) return true;
		return false;
	};
	for (int32 T = FMath::Clamp(GameTier, 1, GameTierMax); T >= 1 && Out.Num() == 0; --T)
		for (int32 K = 0; K < Monsters.Num(); ++K)
		{
			const FRDMonsterDef& D = Monsters[K];
			if (D.Mesh && D.Weight > 0.f && D.WildTierMax > 0 && T >= D.WildTierMin && T <= D.WildTierMax && !Excluded(D.Name.ToString())) Out.Add(K);
		}
}

FString ARDDungeonGenerator::GetCaveMouth15() const
{
	if (!CaveMouth15.IsValid() || !IsWildReady()) return TEXT("off");
	// (the tier as the way in clamps it: the cave's own)
	return FString::Printf(TEXT("on|%.0f|%.0f|%.0f|%.3f|%.3f|cave:%d_%d|%d"), CaveMouthAt15.X, CaveMouthAt15.Y, CaveMouthAt15.Z, CaveMouthOut15.X, CaveMouthOut15.Y,
		CaveCell15.X, CaveCell15.Y, FMath::Clamp(Wild->TierAt(WildLandmarkAt.X, WildLandmarkAt.Y), 1, GameTierMax));
}

FString ARDDungeonGenerator::GetCave15() const
{
	return FString::Printf(TEXT("%s|%d|%d|%d|%s"), *DungeonKey, DungeonTierCap, DungeonTierBase, DungeonTierCap, *DungeonTitle);
}
