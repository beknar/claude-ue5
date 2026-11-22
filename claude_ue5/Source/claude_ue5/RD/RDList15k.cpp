// The user's list of 2026-11-20 (docs/improvements15.txt; the plan docs/improvements15_plan.md), its twelfth phase: rewards that last
// (docs/wilderness_ideas.md's idea 4).
//   - Collectibles: a kind of find to each kind of region (CollectibleKinds15: an amber shard in the forests, an obsidian flake on the
//     volcanoes...), one in CollectibleChance15 of a 500 m grid's cells, a small glowing thing laid within 150 m of her; F takes it (once
//     for the game). At a town's temple CollectibleTradeN15 of a kind buy 10 hit points or 10 mana for good, or an Angel Token (a rank of a
//     secondary ability, the tokens' own way).
//   - Treasure maps: in TreasureMapChance15 of the ruins a loose map lies by the ruin's middle; taken, it is a picture of a spot by the
//     nearest landmark (a region's landmark or a broken tower within 20 km), taken in play from that spot toward the landmark's top, shown
//     beside her big map; at the spot a chest lies buried, dug up with F (the land's tier's things and gold), once.
//   - Named items tied to places: each kind of structure a ring of its own (PlaceItems15), in the first of its chests she opens, once.
// Every one on a stream and ids of its own: nothing else moves.
#include "RD/RDDungeonGenerator.h"
#include "RD/RDWild.h"
#include "RD/RDGameInstance.h"
#include "RD/RDCombat.h"
#include "RD/RDTown.h"
#include "RD/RDMistward.h"
#include "Components/StaticMeshComponent.h"
#include "Components/PointLightComponent.h"
#include "Components/SceneCaptureComponent2D.h"
#include "Engine/TextureRenderTarget2D.h"
#include "Kismet/GameplayStatics.h"
#include "Kismet/KismetRenderingLibrary.h"
#include "Materials/MaterialInstanceDynamic.h"
#include "Engine/World.h"
DEFINE_LOG_CATEGORY_STATIC(LogRDList15k, Log, All);

static constexpr double RDK15CollectCellM = 500.0;
static void RDK15Drop(ARDDungeonGenerator::FRewardLaid15& R)
{
	if (R.Mesh.IsValid()) R.Mesh->DestroyComponent();
	if (R.Lid.IsValid()) R.Lid->DestroyComponent();
	if (R.Light.IsValid()) R.Light->DestroyComponent();
}

// ================================================================================================ the collectibles
bool ARDDungeonGenerator::CollectibleOf15(FIntPoint Cell, FCollectible15& Out) const
{
	if (const FCollectible15* Got = CollectibleCache15.Find(Cell)) { Out = *Got; return Got->Kind >= 0; }
	FCollectible15 C;
	const FRDWildWorld& W = *Wild;
	const FVector2D S(W.Xs + (Cell.X + 0.1 + 0.8 * FRDWildWorld::Rand01(Cell.X, Cell.Y, W.Seed + 1801u)) * RDK15CollectCellM,
		W.Yw + (Cell.Y + 0.1 + 0.8 * FRDWildWorld::Rand01(Cell.Y, Cell.X, W.Seed + 1802u)) * RDK15CollectCellM);
	if (Cell.X >= 0 && Cell.Y >= 0 && S.X < W.Xn && S.Y < W.Ye && FRDWildWorld::Rand01(Cell.X, Cell.Y, W.Seed + 1803u) < CollectibleChance15)
	{
		FRDWSample Q; W.Sample(S.X, S.Y, Q, false);
		const FString Bn = W.BiomeName(Q.Biome);
		const int32 K = CollectibleKinds15.IndexOfByPredicate([&](const FString& L) { TArray<FString> F, Bs; L.ParseIntoArray(F, TEXT("|"), false); if (F.Num() > 1) F[1].ParseIntoArray(Bs, TEXT(";")); return Bs.Contains(Bn); });          // (whole names: one biome's name can be inside another's)
		double Dt = 1e12; W.NearestTown(S.X, S.Y, Dt);
		if (K >= 0 && Q.WaterKind == 0 && Q.Road < 0.05f && Q.Lava < 0.05f && Dt > 800.0)
		{
			C.Kind = K; C.At = S; C.Id = Cell.X * 1000 + Cell.Y;
			TArray<FString> F; CollectibleKinds15[K].ParseIntoArray(F, TEXT("|"), false);
			C.Item = FName(*F[0]);
			TArray<FString> Rgb; if (F.Num() > 2) F[2].ParseIntoArray(Rgb, TEXT(","));
			C.Color = Rgb.Num() == 3 ? FLinearColor(FCString::Atof(*Rgb[0]), FCString::Atof(*Rgb[1]), FCString::Atof(*Rgb[2])) : FLinearColor(1.f, 0.8f, 0.4f);
		}
	}
	CollectibleCache15.Add(Cell, C);
	Out = C;
	return C.Kind >= 0;
}

void ARDDungeonGenerator::TickRewards15(float Dt, const FVector& Her)
{
	RewardLook15 -= Dt;
	if (RewardLook15 > 0.f || !IsWildReady()) return;
	RewardLook15 = 0.5f;
	if (WildReadySince15 < 0.f && GetWorld()) WildReadySince15 = GetWorld()->GetTimeSeconds();
	URDGameInstance* GI = URDGameInstance::Of(this);
	const FVector2D H2(Her.X / 100.0, Her.Y / 100.0);
	auto Glow = [this](const FVector& At, const FLinearColor& Col, float Scale) -> TPair<UStaticMeshComponent*, UPointLightComponent*>
	{
		UStaticMeshComponent* M = nullptr; UPointLightComponent* L = nullptr;
		if (RewardGlowMesh15)
		{
			M = NewObject<UStaticMeshComponent>(this);
			M->SetStaticMesh(RewardGlowMesh15);
			if (RewardGlowMat15) { UMaterialInstanceDynamic* Md = UMaterialInstanceDynamic::Create(RewardGlowMat15, M); Md->SetVectorParameterValue(TEXT("Color"), Col); M->SetMaterial(0, Md); }
			M->SetCollisionEnabled(ECollisionEnabled::NoCollision); M->SetCastShadow(false);
			M->RegisterComponent();
			M->SetWorldTransform(FTransform(FRotator::ZeroRotator, At, FVector(Scale)));
		}
		L = NewObject<UPointLightComponent>(this);
		L->SetIntensityUnits(ELightUnits::Candelas); L->SetIntensity(8.f); L->SetLightColor(Col); L->SetAttenuationRadius(400.f); L->SetCastShadows(false);
		L->RegisterComponent();
		L->SetWorldLocation(At + FVector(0, 0, 40.f));
		return TPair<UStaticMeshComponent*, UPointLightComponent*>(M, L);
	};
	// (the collectibles within 150 m, laid; gone past 250 m)
	if (CollectibleKinds15.Num() > 0)
	{
		const FIntPoint Cc(FMath::FloorToInt((H2.X - Wild->Xs) / RDK15CollectCellM), FMath::FloorToInt((H2.Y - Wild->Yw) / RDK15CollectCellM));
		for (int32 I = -1; I <= 1; ++I) for (int32 J = -1; J <= 1; ++J)
		{
			FCollectible15 C;
			if (!CollectibleOf15(Cc + FIntPoint(I, J), C) || FVector2D::Distance(C.At, H2) > 150.0 || (GI && GI->CollectiblesTaken15.Contains(C.Id)) || CollectiblesLaid15.Contains(C.Id)) continue;
			const FVector At(C.At.X * 100.0, C.At.Y * 100.0, WildGroundZ(FVector(C.At.X * 100.0, C.At.Y * 100.0, 0.0)) + 30.f);
			const auto G = Glow(At, C.Color, 0.28f);
			FRewardLaid15 R; R.At = At; R.Mesh = G.Key; R.Light = G.Value; R.Item = C.Item; R.Id = C.Id;
			CollectiblesLaid15.Add(C.Id, R);
		}
		for (auto It = CollectiblesLaid15.CreateIterator(); It; ++It)
			if (FVector::Dist2D(It.Value().At, Her) > 25000.f) { RDK15Drop(It.Value()); It.RemoveCurrent(); }
	}
	// (the quests' places (ids from QuestIdBase: the captain's den and watchtower, whose places move with each game's roads) are no ruins of chance)
	// (the ruins within 150 m: a loose treasure map by the middle of some; the maps she holds: their buried chests within 300 m)
	if (TreasureMapChance15 > 0.f)
	{
		TArray<FRDWildPlace> Ps;
		const FIntPoint P0 = Wild->PlaceCellOf(H2.X - 200.0, H2.Y - 200.0), P1 = Wild->PlaceCellOf(H2.X + 200.0, H2.Y + 200.0);
		for (int32 I = P0.X; I <= P1.X; ++I) for (int32 J = P0.Y; J <= P1.Y; ++J) Wild->PlacesIn(FIntPoint(I, J), Ps);
		for (const FRDWildPlace& P : Ps)
		{
			if (FVector2D::Distance(P.At, H2) > 150.0 || MapsLaid15.Contains(P.Id) || (GI && GI->TreasureMapsTaken15.Contains(P.Id)) || !RuinHasMap15(P)) continue;
			const FVector2D Mp = P.At + FVector2D(4.0, 0.0).GetRotated(FRDWildWorld::Rand01(P.Id, 1811, Wild->Seed) * 360.f);
			const FVector At(Mp.X * 100.0, Mp.Y * 100.0, WildGroundZ(FVector(Mp.X * 100.0, Mp.Y * 100.0, 0.0)) + 25.f);
			const auto G = Glow(At, FLinearColor(0.95f, 0.85f, 0.55f), 0.22f);
			FRewardLaid15 R; R.At = At; R.Mesh = G.Key; R.Light = G.Value; R.Id = P.Id;
			MapsLaid15.Add(P.Id, R);
		}
		for (auto It = MapsLaid15.CreateIterator(); It; ++It)
			if (FVector::Dist2D(It.Value().At, Her) > 25000.f) { RDK15Drop(It.Value()); It.RemoveCurrent(); }
		if (GI)
			for (const int32 Mid : GI->TreasureMaps15)
			{
				if (ChestsLaid15.Contains(Mid) || GI->TreasuresDug15.Contains(Mid)) continue;
				FRDWildPlace Rp; FVector2D T; FString Lk;
				if (!Wild->FindPlace(Mid, Rp) || !TreasureSpotOf15(Mid, Rp.At, T, Lk) || FVector2D::Distance(T, H2) > 300.0) continue;
				FRewardLaid15 R; R.Id = Mid;
				R.At = FVector(T.X * 100.0, T.Y * 100.0, WildGroundZ(FVector(T.X * 100.0, T.Y * 100.0, 0.0)));
				// (the dungeon's chest piece, its body and its shut lid on the hinge as the sections lay a container; buried to its lid:
				// the whole chest's top 35 cm over the ground. The body alone read as an empty frame in the grass)
				const FRDPiece* Pc = Piece(TEXT("Chest"));
				UStaticMesh* BodyMesh = Pc ? Pc->Mesh.Get() : TreasureChestMesh15.Get();
				if (BodyMesh)
				{
					const FTransform W(FRotator(0.f, (float)(FRDWildWorld::Hash(Mid, 1812, Wild->Seed) % 360u), 0.f), R.At);
					auto Part = [this](UStaticMesh* Sm, const FTransform& T) {
						UStaticMeshComponent* M = NewObject<UStaticMeshComponent>(this);
						M->SetStaticMesh(Sm);
						M->SetCollisionEnabled(ECollisionEnabled::QueryAndPhysics); M->SetCollisionResponseToAllChannels(ECR_Block);
						M->RegisterComponent(); M->SetWorldTransform(T); return M; };
					UStaticMeshComponent* Body = Part(BodyMesh, Pc ? Pc->Adjust * W : W);
					UStaticMeshComponent* Lid = nullptr;
					if (Pc && Pc->Moving)
						Lid = Part(Pc->Moving, FTransform(W.GetRotation() * Pc->Adjust.GetRotation(), W.TransformPosition(Pc->Hinge), Pc->Adjust.GetScale3D()));          // (the piece's turn first, then the world's, as Adjust * W (PR #104's review))
					float Top = Body->Bounds.GetBox().Max.Z;
					if (Lid) Top = FMath::Max(Top, (float)Lid->Bounds.GetBox().Max.Z);
					const FVector Down(0, 0, R.At.Z + 35.f - Top);
					Body->AddWorldOffset(Down); if (Lid) Lid->AddWorldOffset(Down);
					R.Mesh = Body; R.Lid = Lid;
				}
				ChestsLaid15.Add(Mid, R);
			}
		if (GI)
		{
			for (int32 I = TreasurePictures15.Num() - 1; I >= 0; --I)
				if (!GI->TreasureMaps15.Contains(TreasurePictures15[I].Id)) { TreasureTargets15.Remove(TreasurePictures15[I].Rt); TreasurePictures15.RemoveAt(I); }
			if (GetWorld() && GetWorld()->GetTimeSeconds() - WildReadySince15 > 8.f)          // (the far land made round her first)
				for (const int32 Mid : GI->TreasureMaps15)
					if (!TreasurePictures15.ContainsByPredicate([Mid](const FTreasurePicture15& Tp) { return Tp.Id == Mid; }))
					{
						FRDWildPlace Rp; FVector2D T; FString Lk;
						if (Wild->FindPlace(Mid, Rp) && TreasureSpotOf15(Mid, Rp.At, T, Lk)) DrawTreasureMap15(Mid, T, Lk);
						break;          // (one a look)
					}
		}
		for (auto It = ChestsLaid15.CreateIterator(); It; ++It)
			if (FVector::Dist2D(It.Value().At, Her) > 40000.f || (GI && GI->TreasuresDug15.Contains(It.Key()))) { RDK15Drop(It.Value()); It.RemoveCurrent(); }
	}
}

bool ARDDungeonGenerator::RuinHasMap15(const FRDWildPlace& P) const
{
	// (an ordinary ruin, by its own hash, with a spot found: the quests' places (ids from QuestIdBase: the captain's den and watchtower, whose
	// places move with each game's roads) are no ruins of chance)
	if (P.Kind != TEXT("ruins") || P.Id >= FRDWildWorld::QuestIdBase || FRDWildWorld::Rand01(P.Id, 1810, Wild->Seed) >= TreasureMapChance15) return false;
	return TreasureSpot15(P.Id, P.At) != nullptr;
}

bool ARDDungeonGenerator::TreasureSpotOf15(int32 RuinId, const FVector2D& RuinAt, FVector2D& Spot, FString& Landmark) const
{
	const FTreasureSpot15* T = TreasureSpot15(RuinId, RuinAt);
	if (!T) return false;
	Spot = T->Spot; Landmark = T->Landmark;
	return true;
}

const ARDDungeonGenerator::FTreasureSpot15* ARDDungeonGenerator::TreasureSpot15(int32 RuinId, const FVector2D& RuinAt) const
{
	// (the nearest landmark within 20 km of the ruin: a region's landmark (two to a region's cell) or a broken tower; the spot 60 to 120 m
	// from its foot, on dry gentle ground, a way of the ruin's own hash. Kept with the landmark itself, for the picture)
	if (const FTreasureSpot15* Got = TreasureSpots15.Find(RuinId)) return Got->Landmark.IsEmpty() ? nullptr : Got;
	double Best = 20000.0; FTreasureSpot15 T;
	const FIntPoint Lc = Wild->LookoutCellOf(RuinAt.X, RuinAt.Y);
	ParseRegionLandmarks15();
	for (int32 I = -3; I <= 3; ++I) for (int32 J = -3; J <= 3; ++J) for (int32 Sl = 0; Sl < 2; ++Sl)
	{
		FRegionLandmark15 Lm;
		if (RegionLandmarkOf15(Lc + FIntPoint(I, J), Sl, Lm) && FVector2D::Distance(Lm.At, RuinAt) < Best)
		{
			Best = FVector2D::Distance(Lm.At, RuinAt);
			T.LmAt = Lm.At; T.bTower = false; T.Cell = Lc + FIntPoint(I, J); T.Slot = Sl;
			T.Landmark = RegionLandmarkParsed15.IsValidIndex(Lm.Line) ? RegionLandmarkParsed15[Lm.Line].Name : FString(TEXT("landmark"));
		}
	}
	if (WildLandmarkMesh && WildLandmarkBiomes.Num() > 0)
	{
		const int32 Ci = FMath::FloorToInt(RuinAt.X / WildLandmarkCellM), Cj = FMath::FloorToInt(RuinAt.Y / WildLandmarkCellM);
		for (int32 I = Ci - 4; I <= Ci + 4; ++I) for (int32 J = Cj - 4; J <= Cj + 4; ++J)
		{
			FVector2D S;
			if (WildTowerSite13(I, J, S) && FVector2D::Distance(S, RuinAt) < Best) { Best = FVector2D::Distance(S, RuinAt); T.LmAt = S; T.bTower = true; T.Landmark = TEXT("broken tower"); }
		}
	}
	bool bOk = false;
	if (!T.Landmark.IsEmpty())
		for (int32 Try = 0; Try < 12 && !bOk; ++Try)
		{
			const float A = FRDWildWorld::Rand01(RuinId, 1813 + Try, Wild->Seed) * 2.f * PI;
			const float D = 60.f + 60.f * FRDWildWorld::Rand01(RuinId, 1830 + Try, Wild->Seed);
			const FVector2D Q = T.LmAt + FVector2D(FMath::Cos(A), FMath::Sin(A)) * D;
			FRDWSample S; Wild->Sample(Q.X, Q.Y, S, false);
			if (S.WaterKind != 0 || S.Road > 0.05f || S.Lava > 0.05f) continue;
			const double H0 = Wild->Height(Q.X, Q.Y);
			bool bSteep = false;
			for (int32 K = 0; K < 4 && !bSteep; ++K) bSteep = FMath::Abs(Wild->Height(Q.X + 4.0 * FMath::Cos(K * PI / 2.0), Q.Y + 4.0 * FMath::Sin(K * PI / 2.0)) - H0) > 1.5;
			if (!bSteep) { T.Spot = Q; bOk = true; }
		}
	if (!bOk) T.Landmark.Reset();
	const FTreasureSpot15& Kept = TreasureSpots15.Add(RuinId, T);
	return bOk ? &Kept : nullptr;
}

bool ARDDungeonGenerator::RewardFirst15(const FVector& From, int32& Kind, int32& Id) const
{
	// (the nearest of the collectibles, the loose maps and the buried chests within 2.2 m, nearer than every other wild thing F reaches)
	float Best = 220.f; Kind = -1; Id = -1;
	for (const auto& Kv : CollectiblesLaid15) { const float D = FVector::Dist2D(Kv.Value.At, From); if (D < Best && FMath::Abs(Kv.Value.At.Z - From.Z) < 250.f) { Best = D; Kind = 0; Id = Kv.Key; } }
	for (const auto& Kv : MapsLaid15) { const float D = FVector::Dist2D(Kv.Value.At, From); if (D < Best && FMath::Abs(Kv.Value.At.Z - From.Z) < 250.f) { Best = D; Kind = 1; Id = Kv.Key; } }
	// (a buried chest is reached from 2.8 m (it is wider), but only when nothing nearer was found (PR #104's review: its slack over a nearer find))
	for (const auto& Kv : ChestsLaid15) { const float D = FVector::Dist2D(Kv.Value.At, From); if (D < (Kind < 0 ? 280.f : Best) && FMath::Abs(Kv.Value.At.Z - From.Z) < 300.f) { Best = D; Kind = 2; Id = Kv.Key; } }
	for (const auto& Kv : ContractSignsLaid15) { const float D = FVector::Dist2D(Kv.Value.At, From); if (D < Best && FMath::Abs(Kv.Value.At.Z - From.Z) < 250.f) { Best = D; Kind = 3; Id = Kv.Key; } }          // (the thirteenth phase: a contract's sign)
	if (Kind < 0) return false;
	FVector Sa; FName Sk;
	if (WildStationNear14(From, Sa, Sk) && FVector::Dist2D(Sa, From) < Best) return false;
	if (const FSceneryUse* U = WildSceneryUseNear(From); U && FVector::Dist2D(U->At, From) < Best) return false;
	if (const FRDWildPoiLive* P = WildPoiNear(From, 320.f); P && FVector::Dist2D(P->At, From) < Best) return false;
	int32 Di = -1;
	if (const ARDWildChunk* C = bWildHouseInsides ? WildDoorNear(From, 190.f, Di) : nullptr; C && C->Doors.IsValidIndex(Di) && FVector::Dist2D(C->Doors[Di].At, From) < Best) return false;
	if (const ARDTownsfolk* T = WildFolkForF(From); T && FVector::Dist2D(T->GetActorLocation(), From) < Best) return false;
	return true;
}

FString ARDDungeonGenerator::RewardDescribe15(const FVector& From) const
{
	int32 K, Id;
	if (!RewardFirst15(From, K, Id)) return FString();
	if (K == 0) { const FRewardLaid15* R = CollectiblesLaid15.Find(Id); return R ? FString::Printf(TEXT("take the %s"), *R->Item.ToString().ToLower()) : FString(); }
	return K == 1 ? FString(TEXT("take the old map")) : K == 3 ? FString(TEXT("read the signs")) : FString(TEXT("dig up the buried chest"));
}

FString ARDDungeonGenerator::RewardInteract15(const FVector& From)
{
	int32 K, Id;
	if (!RewardFirst15(From, K, Id) || !PlayerCombat) return FString();
	URDGameInstance* GI = URDGameInstance::Of(this);
	if (K == 3) return ReadContractSign15(Id);
	if (K == 0)
	{
		FRewardLaid15 R = CollectiblesLaid15.FindAndRemoveChecked(Id); RDK15Drop(R);
		if (GI) GI->CollectiblesTaken15.AddUnique(Id);
		PlayerCombat->AddItem(R.Item, 1);
		PlayerCombat->ShowMessage(FString::Printf(TEXT("You find %s (%d carried): a temple takes %d of a kind for something that lasts"), *R.Item.ToString(), PlayerCombat->GetItemCount(R.Item), CollectibleTradeN15));
		PlaySoundAt(TEXT("Player.Loot"), R.At);
		WildAutosave(TEXT("found"));
		return TEXT("collectible");
	}
	if (K == 1)
	{
		FRewardLaid15 R = MapsLaid15.FindAndRemoveChecked(Id); RDK15Drop(R);
		if (GI) { GI->TreasureMapsTaken15.AddUnique(Id); GI->TreasureMaps15.AddUnique(Id); }
		FRDWildPlace P; FVector2D T; FString Lk;
		if (Wild->FindPlace(Id, P) && TreasureSpotOf15(Id, P.At, T, Lk)) DrawTreasureMap15(Id, T, Lk);
		PlayerCombat->ShowMessage(FString::Printf(TEXT("An old map: a picture of a spot by a %s, an X scratched where to dig. It is beside your map (M)"), *Lk));
		PlaySoundAt(TEXT("Player.Loot"), R.At);
		WildAutosave(TEXT("found"));
		return TEXT("map");
	}
	// (the buried chest: the land's tier's things (CollectibleChestN15 of them, drawn by their weight among the items of that tier, on a
	// stream of the map's own) and gold)
	FRewardLaid15 R = ChestsLaid15.FindAndRemoveChecked(Id); RDK15Drop(R);
	if (GI) { GI->TreasuresDug15.AddUnique(Id); GI->TreasureMaps15.Remove(Id); }
	const int32 Tier = FMath::Clamp(Wild->TierAt(R.At.X / 100.0, R.At.Y / 100.0), 1, GameTierMax);
	TArray<int32> Pool; float Sum = 0.f;
	for (int32 I = 0; I < Items.Num(); ++I)
		if (Items[I].Weight > 0.f && Items[I].Tiers.Contains(Tier) && Items[I].Kind != ERDItemKind::Recipe && Items[I].Kind != ERDItemKind::Key) { Pool.Add(I); Sum += Items[I].Weight; }
	FRandomStream Rs((int32)FRDWildWorld::Hash(Id, 1814, Wild->Seed));
	TArray<FName> Things;
	for (int32 N = 0; N < TreasureChestItems15 && Pool.Num() > 0; ++N)
	{
		float U = Rs.FRand() * Sum; int32 Pick = Pool.Last();          // (a float sum's rounding can leave U over 0 after the last: it is the last)
		for (const int32 I : Pool) { U -= Items[I].Weight; if (U <= 0.f) { Pick = I; break; } }
		Things.Add(Items[Pick].Name);
	}
	const int32 Gold = FMath::RoundToInt(TreasureChestGold15 * (1.f + 0.35f * (Tier - 1)));
	AddGold(Gold, TEXT("a buried chest"));
	TArray<float> Wear; Wear.Init(0.f, Things.Num());
	if (ARDLootPile* Pile = DropLoot(R.At + FVector(80.f, 0.f, 60.f), Things, Wear)) Pile->bHers = false;
	PlayerCombat->ShowMessage(FString::Printf(TEXT("You dig up the buried chest: %d gold and %d things (tier %d)"), Gold, Things.Num(), Tier));
	PlaySoundAt(TEXT("Player.Loot"), R.At);
	LastChestDug15 = FString::Printf(TEXT("%d|%d|%d|%s"), Id, Tier, Gold, *FString::JoinBy(Things, TEXT(","), [](const FName& N) { return N.ToString(); }));
	WildAutosave(TEXT("found"));
	return TEXT("treasure");
}

void ARDDungeonGenerator::DrawTreasureMap15(int32 Id, const FVector2D& Spot, const FString& Landmark)
{
	// (the picture: from the spot 1.7 m up toward the landmark, taken now into a target of its own. The landmark is laid for the moment of
	// the picture when it is not standing (PR #104's review: 20 km off nothing of it stood, and the picture was the far land alone); the
	// ground there is the far land's (the chunks reach 2 km))
	if (!GetWorld()) return;
	FRDWildPlace P;
	const FTreasureSpot15* T = Wild->FindPlace(Id, P) ? TreasureSpot15(Id, P.At) : nullptr;
	if (!T) return;
	UTextureRenderTarget2D* Rt = UKismetRenderingLibrary::CreateRenderTarget2D(this, 512, 288, RTF_RGBA8_SRGB);
	if (!Rt) return;
	TArray<UStaticMeshComponent*> Temp;
	float TopZ = 0.f;
	if (T->bTower)
	{
		if (WildLandmark.IsValid() && FVector2D::Distance(WildLandmarkAt, T->LmAt) < 1.0) TopZ = WildLandmark->Bounds.GetBox().Max.Z;
		else if (WildLandmarkMesh)
		{
			UStaticMeshComponent* C = NewObject<UStaticMeshComponent>(this);
			C->SetStaticMesh(WildLandmarkMesh); C->SetMobility(EComponentMobility::Movable); C->SetCollisionEnabled(ECollisionEnabled::NoCollision);
			C->RegisterComponent();
			C->SetWorldTransform(FTransform(FRotator(0.f, (float)(FRDWildWorld::Hash((int32)T->LmAt.X, (int32)T->LmAt.Y, Wild->Seed) % 360u), 0.f),
				FVector(T->LmAt.X * 100.0, T->LmAt.Y * 100.0, Wild->ToZ(Wild->Height(T->LmAt.X, T->LmAt.Y)) - 200.f)));          // (as the nearest tower is laid)
			TopZ = C->Bounds.GetBox().Max.Z; Temp.Add(C);
		}
	}
	else
	{
		FRegionLandmark15 Lm;
		if (const FRegionLandmark15* Laid = RegionLandmarks15.Find(FIntVector(T->Cell.X, T->Cell.Y, T->Slot)); Laid && Laid->TopZ > 0.f) TopZ = Laid->TopZ;
		else if (RegionLandmarkOf15(T->Cell, T->Slot, Lm))
		{
			LayRegionLandmark15(Lm);
			TopZ = Lm.TopZ;
			if (UStaticMeshComponent* C = Lm.Main.Get()) Temp.Add(C);
			if (UStaticMeshComponent* C = Lm.Extra.Get()) Temp.Add(C);
		}
	}
	const FVector Eye(Spot.X * 100.0, Spot.Y * 100.0, Wild->ToZ(Wild->Height(Spot.X, Spot.Y)) + 170.f);
	const FVector Look(T->LmAt.X * 100.0, T->LmAt.Y * 100.0, TopZ > 0.f ? TopZ * 0.5f + Eye.Z * 0.5f : Eye.Z);
	USceneCaptureComponent2D* Cap = NewObject<USceneCaptureComponent2D>(this);
	Cap->RegisterComponent();
	FRotator Aim = (Look - Eye).Rotation(); Aim.Pitch = FMath::Clamp(Aim.Pitch, -5.f, 12.f);          // (aimed half way up a 182 m tower from 60 m the picture was the sky)
	Cap->SetWorldLocationAndRotation(Eye, Aim);
	Cap->FOVAngle = 80.f;
	Cap->TextureTarget = Rt;
	Cap->CaptureSource = ESceneCaptureSource::SCS_FinalColorLDR;
	Cap->bCaptureEveryFrame = false; Cap->bCaptureOnMovement = false;
	Cap->CaptureScene();
	Cap->DestroyComponent();
	for (UStaticMeshComponent* C : Temp) C->DestroyComponent();
	TreasurePictures15.RemoveAll([Id](const FTreasurePicture15& Tp) { return Tp.Id == Id; });
	TreasurePictures15.Add(FTreasurePicture15{ Id, Rt, Landmark });
	TreasureTargets15.Add(Rt);          // (held for the garbage collector: the struct's pointer is not seen by it)
	UE_LOG(LogRDList15k, Log, TEXT("RDTREASURE15 map %d: the spot (%.0f, %.0f) m by a %s, its picture taken (%s)"), Id, Spot.X, Spot.Y, *Landmark, Temp.Num() ? TEXT("its landmark laid for it") : TEXT("its landmark standing"));
}

UTextureRenderTarget2D* ARDDungeonGenerator::TreasurePictureToShow15(FString& Caption) const
{
	// (the latest picture of a map she still holds, shown beside her big map)
	const URDGameInstance* GI = URDGameInstance::Of(this);
	for (int32 I = TreasurePictures15.Num() - 1; I >= 0; --I)
		if (GI && GI->TreasureMaps15.Contains(TreasurePictures15[I].Id) && TreasurePictures15[I].Rt)
		{
			Caption = FString::Printf(TEXT("An old map: dig where this was drawn, by a %s"), *TreasurePictures15[I].Landmark);
			return TreasurePictures15[I].Rt;
		}
	return nullptr;
}

// ================================================================================================ the temple's trade
void ARDDungeonGenerator::AddCollectibleTrades15(TFunctionRef<void(const FString& Act, const FString& Label, const FString& Tag, const FString& Detail, bool bOn, const FString& Arg)> Add) const
{
	if (!PlayerCombat) return;
	for (const FString& L : CollectibleKinds15)
	{
		TArray<FString> F; L.ParseIntoArray(F, TEXT("|"), false);
		if (F.Num() < 1) continue;
		const FName It(*F[0]);
		const int32 Have = PlayerCombat->GetItemCount(It);
		if (Have <= 0) continue;
		const bool bOn = Have >= CollectibleTradeN15;
		const FString Tag = FString::Printf(TEXT("%d of %d"), FMath::Min(Have, CollectibleTradeN15), CollectibleTradeN15);
		Add(TEXT("collect"), FString::Printf(TEXT("Offer %d %s: 10 hit points for good"), CollectibleTradeN15, *F[0]), Tag, TEXT("Your hit points' top raised by 10, in every land, for the rest of the game"), bOn, F[0] + TEXT("|hp"));
		if (PlayerMaxMana > 0.f)          // (a hero with no mana gains nothing by it (PR #104's review))
			Add(TEXT("collect"), FString::Printf(TEXT("Offer %d %s: 10 mana for good"), CollectibleTradeN15, *F[0]), Tag, TEXT("Your mana's top raised by 10, in every land, for the rest of the game"), bOn, F[0] + TEXT("|mana"));
		if (!AngelTokenItem.IsNone())
			Add(TEXT("collect"), FString::Printf(TEXT("Offer %d %s: an %s"), CollectibleTradeN15, *F[0], *AngelTokenItem.ToString()), Tag, TEXT("A token for a rank of one of your secondary abilities"), bOn, F[0] + TEXT("|token"));
	}
}

bool ARDDungeonGenerator::TownCollectTrade15(const FString& Arg)
{
	FString Item, What;
	if (!PlayerCombat || !Arg.Split(TEXT("|"), &Item, &What)) return false;
	const FName It(*Item);
	if (PlayerCombat->GetItemCount(It) < CollectibleTradeN15) { SetTownNote(FString::Printf(TEXT("You need %d of them"), CollectibleTradeN15)); return false; }
	if (What == TEXT("mana") && PlayerMaxMana <= 0.f) { SetTownNote(TEXT("You have no mana to raise")); return false; }
	if (What != TEXT("hp") && What != TEXT("mana") && What != TEXT("token")) return false;
	URDGameInstance* GI = URDGameInstance::Of(this);
	PlayerCombat->RemoveItem(It, CollectibleTradeN15);
	if (What == TEXT("hp") && GI) { GI->LastingHealth15 += 10; PlayerCombat->RefreshMaxima(); SetTownNote(TEXT("The priest lays a hand on your brow: your hit points' top rises by 10")); }
	else if (What == TEXT("mana") && GI) { GI->LastingMana15 += 10; PlayerCombat->RefreshMaxima(); SetTownNote(TEXT("The priest murmurs a prayer: your mana's top rises by 10")); }
	else if (What == TEXT("token")) { PlayerCombat->AddItem(AngelTokenItem, 1); SetTownNote(FString::Printf(TEXT("The priest gives you an %s"), *AngelTokenItem.ToString())); }
	TownCount(TEXT("collect_trades"));
	return true;
}

float ARDDungeonGenerator::LastingHealth15() const { const URDGameInstance* GI = URDGameInstance::Of(this); return GI ? (float)GI->LastingHealth15 : 0.f; }
float ARDDungeonGenerator::LastingMana15() const { const URDGameInstance* GI = URDGameInstance::Of(this); return GI ? (float)GI->LastingMana15 : 0.f; }

// ================================================================================================ named items tied to places
void ARDDungeonGenerator::AddPlaceItem15(const FVector& BoxAt, int64 BoxKey, TArray<FName>& Got)
{
	// (a structure's chest (the structure nearest the box within 120 m): the kind's named ring, in the first of its chests she opens)
	// (a structure's own chests only: their keys are (5 << 40) on; a farm's, a house's or a ruin's box beside a structure is not its chest
	// (PR #104's review))
	if (!IsWildReady() || PlaceItems15.Num() == 0 || BoxKey < (int64(5) << 40) || BoxKey >= (int64(6) << 40)) return;
	URDGameInstance* GI = URDGameInstance::Of(this);
	if (!GI) return;
	const FVector2D B2(BoxAt.X / 100.0, BoxAt.Y / 100.0);
	TArray<FRDWildPlace> Ss;
	const FIntPoint S0 = Wild->SiteCellOf(B2.X, B2.Y);
	for (int32 I = -1; I <= 1; ++I) for (int32 J = -1; J <= 1; ++J) Wild->SitesIn(S0 + FIntPoint(I, J), Ss);
	const FRDWildPlace* Near = nullptr; double Best = 120.0;
	for (const FRDWildPlace& P : Ss) { const double D = FVector2D::Distance(P.At, B2); if (P.Site >= 0 && D < Best) { Best = D; Near = &P; } }
	if (!Near || !WildSiteKinds.IsValidIndex(Near->Site)) return;
	const FString Kind = WildSiteKinds[Near->Site].Name.ToString();
	for (const FString& L : PlaceItems15)
	{
		FString K, It;
		if (!L.Split(TEXT("|"), &K, &It) || K != Kind || GI->PlaceItemsGiven15.Contains(Kind) || FindItem(FName(*It)) < 0) continue;
		GI->PlaceItemsGiven15.AddUnique(Kind);
		Got.Add(FName(*It));
		if (PlayerCombat) PlayerCombat->ShowMessage(FString::Printf(TEXT("Among the things: %s, a thing of this place"), *It));
		UE_LOG(LogRDList15k, Log, TEXT("RDPLACEITEM15 %s's %s given"), *Kind, *It);
		return;
	}
}

TArray<FString> ARDDungeonGenerator::GetRewards15(float Km) const
{
	// (tests: "c|id|item|x|y|taken|laid" for the collectibles, "m|ruin id|x|y|taken|laid|spot x|spot y|landmark" for the ruins' maps within
	// Km, "x|id|laid|dug" for the buried chests of the maps she holds)
	TArray<FString> Out;
	const APawn* Her = UGameplayStatics::GetPlayerPawn(this, 0);
	if (!Her || !IsWildReady()) return Out;
	const URDGameInstance* GI = URDGameInstance::Of(this);
	const FVector2D H2(Her->GetActorLocation().X / 100.0, Her->GetActorLocation().Y / 100.0);
	const int32 R = FMath::CeilToInt(Km * 1000.0 / RDK15CollectCellM);
	const FIntPoint Cc(FMath::FloorToInt((H2.X - Wild->Xs) / RDK15CollectCellM), FMath::FloorToInt((H2.Y - Wild->Yw) / RDK15CollectCellM));
	for (int32 I = -R; I <= R; ++I) for (int32 J = -R; J <= R; ++J)
	{
		FCollectible15 C;
		if (!CollectibleOf15(Cc + FIntPoint(I, J), C) || FVector2D::Distance(C.At, H2) > Km * 1000.0) continue;
		Out.Add(FString::Printf(TEXT("c|%d|%s|%.1f|%.1f|%d|%d"), C.Id, *C.Item.ToString(), C.At.X, C.At.Y, GI && GI->CollectiblesTaken15.Contains(C.Id) ? 1 : 0, CollectiblesLaid15.Contains(C.Id) ? 1 : 0));
	}
	TArray<FRDWildPlace> Ps;
	const FIntPoint P0 = Wild->PlaceCellOf(H2.X - Km * 1000.0, H2.Y - Km * 1000.0), P1 = Wild->PlaceCellOf(H2.X + Km * 1000.0, H2.Y + Km * 1000.0);
	for (int32 I = P0.X; I <= P1.X; ++I) for (int32 J = P0.Y; J <= P1.Y; ++J) Wild->PlacesIn(FIntPoint(I, J), Ps);
	for (const FRDWildPlace& P : Ps)
	{
		if (FVector2D::Distance(P.At, H2) > Km * 1000.0 || !RuinHasMap15(P)) continue;
		const FTreasureSpot15* T = TreasureSpot15(P.Id, P.At);
		Out.Add(FString::Printf(TEXT("m|%d|%.1f|%.1f|%d|%d|%.1f|%.1f|%s"), P.Id, P.At.X, P.At.Y, GI && GI->TreasureMapsTaken15.Contains(P.Id) ? 1 : 0, MapsLaid15.Contains(P.Id) ? 1 : 0, T->Spot.X, T->Spot.Y, *T->Landmark));
	}
	if (GI) for (const int32 Mid : GI->TreasureMaps15) Out.Add(FString::Printf(TEXT("x|%d|%d|%d"), Mid, ChestsLaid15.Contains(Mid) ? 1 : 0, GI->TreasuresDug15.Contains(Mid) ? 1 : 0));
	return Out;
}
