// The user's list of 2026-11-20 (docs/improvements15.txt; the plan docs/improvements15_plan.md), its sixteenth phase: getting about
// (docs/wilderness_ideas.md's idea 9, in part).
//   - Waystones: one beside a major road in each region's cell (the world's, FRDWildWorld::WaystoneOf: its own ids, WaystoneIdBase + the
//     cell), a carved rune stone; found as she comes within 40 m (a place on the map like every other), lit with F (it glows, for the game);
//     a lit waystone is a place to travel to from the map, an unlit one is not.
//   - Crossroads posts: at each of the world's crossroads a post with an arm for each road out of it, naming the town (a major road) or the
//     place (a minor road) down it and how far along it, in the road signs' lettering (one builder for both, RDList14k.cpp).
#include "RD/RDDungeonGenerator.h"
#include "RD/RDWild.h"
#include "RD/RDGameInstance.h"
#include "RD/RDCombat.h"
#include "Components/StaticMeshComponent.h"
#include "Components/PointLightComponent.h"
#include "Kismet/GameplayStatics.h"
#include "Engine/World.h"
DEFINE_LOG_CATEGORY_STATIC(LogRDList15o, Log, All);

// ================================================================================================ the waystones (the world's)
static const TCHAR* RDO15Names[] = { TEXT("Ashen"), TEXT("Pilgrim's"), TEXT("Old Road"), TEXT("Moss"), TEXT("Grey"), TEXT("Wayfarer's"), TEXT("Elder"), TEXT("Raven"),
	TEXT("Hollow"), TEXT("Thorn"), TEXT("Dawn"), TEXT("Dusk"), TEXT("Lantern"), TEXT("King's"), TEXT("Crossing"), TEXT("Watcher's") };

bool FRDWildWorld::WaystoneOf(FIntPoint Cell, FRDWildPlace& Out) const
{
	{
		FScopeLock Lk(&WaystoneCache->Lock);
		if (const FRDWildPlace* Got = WaystoneCache->Cells.Find(Cell)) { Out = *Got; return Got->Id != 0; }
	}
	FRDWildPlace L; L.Id = 0;
	const double X0 = Xs + Cell.X * CellM, Y0 = Yw + Cell.Y * CellM;
	if (Cell.X >= 0 && Cell.Y >= 0 && Cell.X < 1024 && Cell.Y < 1024 && X0 + CellM <= Xn && Y0 + CellM <= Ye)
	{
		// (beside the major road that passes nearest the cell's middle: its nearest point, then along it in steps of 150 m each way, 12 m off its
		// middle on the side of the cell's hash, dry, gentle, 1.5 km from a town and 80 m from every other place)
		const FVector2D Mid(X0 + CellM * 0.5, Y0 + CellM * 0.5);
		TArray<int32> Rs; RoadsIn(FBox2D(FVector2D(X0, Y0), FVector2D(X0 + CellM, Y0 + CellM)), false, Rs);
		int32 Best = -1, BestSeg = 0; double BestD = 1e12;
		for (const int32 Ri : Rs)
			for (int32 I = 0; I + 1 < Roads[Ri].P.Num(); ++I)
			{
				const FVector2D C = FMath::ClosestPointOnSegment2D(Mid, Roads[Ri].P[I], Roads[Ri].P[I + 1]);
				if (C.X < X0 || C.X >= X0 + CellM || C.Y < Y0 || C.Y >= Y0 + CellM) continue;
				const double D = FVector2D::Distance(C, Mid);
				if (D < BestD) { BestD = D; Best = Ri; BestSeg = I; }
			}
		// (off the road's eased bed: 12, 18 or 26 m from its middle, the first that is clear (the road's own weight reaches past 12 m on a
		// major road: at 12 m alone no cell within 25 km had one); the segments nearest the middle first, then on either way)
		const double Sg0 = (Hash(Cell.X, Cell.Y, Seed + 1951u) & 1) ? 1.0 : -1.0;
		int32 Why[5] = { 0, 0, 0, 0, 0 };          // (out of the cell, wet or on the road, a town near, steep, other places near)
		for (int32 Try = 0; Best >= 0 && Try < 24 && L.Id == 0; ++Try)
		{
			const TArray<FVector2D>& P = Roads[Best].P;
			const int32 Sg = FMath::Clamp(BestSeg + (Try % 2 ? 1 : -1) * ((Try + 1) / 2), 0, P.Num() - 2);
			const FVector2D A = P[Sg], B = P[Sg + 1], D = (B - A).GetSafeNormal();
			for (const double Off : { 12.0, 18.0, 26.0 })
			{
				for (const double Sd : { Sg0, -Sg0 })
				{
					const FVector2D S = (A + B) * 0.5 + FVector2D(-D.Y, D.X) * (Off * Sd);
					if (S.X < X0 || S.X >= X0 + CellM || S.Y < Y0 || S.Y >= Y0 + CellM) { ++Why[0]; continue; }
					FRDWSample Q; Sample(S.X, S.Y, Q, false);
					if (Q.WaterKind != 0 || Q.Road > 0.05f || Q.Lava > 0.02f || Q.Chan > 0.f || Q.Terrace > 0.f) { ++Why[1]; continue; }
					double Dt = 1e12; NearestTown(S.X, S.Y, Dt);
					if (Dt < 1500.0) { ++Why[2]; continue; }
					const double H0 = Height(S.X, S.Y);
					bool bSteep = false;
					for (int32 K = 0; K < 8 && !bSteep; ++K) bSteep = FMath::Abs(Height(S.X + 4.0 * FMath::Cos(K * PI / 4.0), S.Y + 4.0 * FMath::Sin(K * PI / 4.0)) - H0) > 1.5;
					if (bSteep) { ++Why[3]; continue; }
					// (80 m from every other place, 15 m from a road sign, and clear of the generator's own layers (its region landmarks: the veto
					// it gives, PR #108's review))
					TArray<int32> Sn; SignsNear(S, 15.0, Sn);
					if (!ClearOfPlaces15(S, 80.0, true) || Sn.Num() > 0 || (WaystoneVeto && WaystoneVeto(S))) { ++Why[4]; continue; }
					L.Id = WaystoneIdBase + ((Cell.X & 0x3FF) << 10 | (Cell.Y & 0x3FF));
					L.Kind = TEXT("waystone");
					L.Name = FString::Printf(TEXT("%s Waystone"), RDO15Names[Hash(Cell.X, Cell.Y, Seed + 1952u) % UE_ARRAY_COUNT(RDO15Names)]);
					L.At = S; L.H = (float)H0; L.Tier = TierAt(S.X, S.Y); L.Biome = Q.Biome;
					L.Yaw = (float)FMath::RadiansToDegrees(FMath::Atan2(-D.X * Sd, D.Y * Sd));          // (its +X toward the road, its +Y along it)
					break;
				}
				if (L.Id != 0) break;
			}
		}
		static bool bSaid = false;
		if (Best >= 0 && L.Id == 0 && !bSaid) { bSaid = true; UE_LOG(LogRDList15o, Log, TEXT("RDWAYSTONE15 cell (%d, %d) has none: out %d, wet or road %d, town %d, steep %d, places %d"), Cell.X, Cell.Y, Why[0], Why[1], Why[2], Why[3], Why[4]); }
	}
	FScopeLock Lk(&WaystoneCache->Lock);
	WaystoneCache->Cells.Add(Cell, L);
	Out = L;
	return L.Id != 0;
}

// ================================================================================================ the waystones in play
bool ARDDungeonGenerator::IsWaystoneLit15(int32 Id) const
{
	const URDGameInstance* GI = URDGameInstance::Of(this);
	return GI && GI->WaystonesLit15.Contains(Id);
}

void ARDDungeonGenerator::TickWaystones15(float Dt, const FVector& Her)
{
	WaystoneLook15 -= Dt;
	if (!bWaystones15 && WaystonesLaid15.Num() > 0) { for (auto& Kv : WaystonesLaid15) DropReward15(Kv.Value); WaystonesLaid15.Reset(); }
	if (WaystoneLook15 > 0.f || !IsWildReady() || !bWaystones15) return;
	WaystoneLook15 = 0.5f;
	EnsureWaystoneVeto15();
	const FVector2D H2(Her.X / 100.0, Her.Y / 100.0);
	const FIntPoint C0 = Wild->LookoutCellOf(H2.X, H2.Y);
	TSet<int32> Want;
	for (int32 I = -1; I <= 1; ++I) for (int32 J = -1; J <= 1; ++J)
	{
		FRDWildPlace P;
		if (!Wild->WaystoneOf(C0 + FIntPoint(I, J), P)) continue;
		const double D = FVector2D::Distance(P.At, H2);
		// (found as she comes within 40 m: a place on the map, told)
		if (D < 40.0 && !WildFound.Contains(P.Id))
		{
			WildFound.Add(P.Id);
			if (PlayerCombat) PlayerCombat->ShowMessage(FString::Printf(TEXT("Discovered: %s. Light it (F) to travel here from the map"), *P.Name));
			WildAutosave(TEXT("found"));
		}
		if (D < 250.0 || (WaystonesLaid15.Contains(P.Id) && D < 330.0)) Want.Add(P.Id);
		if (D < 250.0 && !WaystonesLaid15.Contains(P.Id)) LayWaystone15(P);
	}
	for (auto It = WaystonesLaid15.CreateIterator(); It; ++It)
		if (!Want.Contains(It.Key())) { DropReward15(It.Value()); It.RemoveCurrent(); }
}

void ARDDungeonGenerator::LayWaystone15(const FRDWildPlace& P)
{
	// (a rune stone of the places' table, WaystoneHeight15 tall by its box, its foot 30 cm into the ground; lit, a glow on its face and a light)
	FRewardLaid15 R; R.Id = P.Id;
	R.At = FVector(P.At.X * 100.0, P.At.Y * 100.0, WildGroundZ(FVector(P.At.X * 100.0, P.At.Y * 100.0, 0.0)));
	TArray<UStaticMesh*> Ms; WildPiecesOf(TEXT("stone"), Ms);
	if (Ms.Num() > 0)
	{
		UStaticMesh* Sm = Ms[FRDWildWorld::Hash(P.Id, 1953, Wild->Seed) % (uint32)Ms.Num()];
		const FBox B = Sm->GetBoundingBox();
		const float Sc = WaystoneHeight15 * 100.f / FMath::Max((float)B.GetSize().Z, 1.f);
		UStaticMeshComponent* C = NewObject<UStaticMeshComponent>(this);
		C->SetStaticMesh(Sm);
		C->SetCollisionEnabled(ECollisionEnabled::QueryAndPhysics); C->SetCollisionResponseToAllChannels(ECR_Block);
		C->RegisterComponent();
		C->SetWorldTransform(FTransform(FRotator(0.f, P.Yaw, 0.f), R.At, FVector(Sc)));
		const FBox Wb = C->Bounds.GetBox();
		C->AddWorldOffset(FVector(R.At.X - Wb.GetCenter().X, R.At.Y - Wb.GetCenter().Y, R.At.Z - 30.f - Wb.Min.Z));
		R.Mesh = C;
		R.TopZ = C->Bounds.GetBox().Max.Z;
	}
	WaystonesLaid15.Add(P.Id, R);
	if (IsWaystoneLit15(P.Id)) GlowWaystone15(P.Id);
}

void ARDDungeonGenerator::GlowWaystone15(int32 Id)
{
	FRewardLaid15* R = WaystonesLaid15.Find(Id);
	if (!R || R->Light.IsValid()) return;
	FRewardLaid15 G;
	MakeGlow15(G, FVector(R->At.X, R->At.Y, (R->TopZ > 0.f ? R->TopZ : R->At.Z + 200.f) + 25.f), FLinearColor(0.45f, 0.75f, 1.f), 0.22f);
	R->Light = G.Light; R->Lid = G.Mesh;          // (the glow's sphere kept in the lid's slot: DropReward15 takes both)
	if (UPointLightComponent* L = R->Light.Get()) { L->SetIntensity(60.f); L->SetAttenuationRadius(1500.f); }
}

bool ARDDungeonGenerator::WaystoneFirst15(const FVector& From, float& Best, int32& Kind, int32& Id) const
{
	// (the rewards' nearest, its ninth kind: a waystone (2.2 m of its middle))
	bool bAny = false;
	for (const auto& Kv : WaystonesLaid15)
	{
		const float D = FVector::Dist2D(Kv.Value.At, From);          // (from its middle: 80 cm thick, she stands a metre off it; no slack over a nearer thing (PR #108's review))
		if (D < Best && FMath::Abs(Kv.Value.At.Z - From.Z) < 300.f) { Best = D; Kind = 9; Id = Kv.Key; bAny = true; }
	}
	return bAny;
}

FString ARDDungeonGenerator::LightWaystone15(int32 Id)
{
	URDGameInstance* GI = URDGameInstance::Of(this);
	FRDWildPlace P;
	if (!GI || !Wild->FindPlace(Id, P)) return FString();
	if (GI->WaystonesLit15.Contains(Id))
	{
		if (PlayerCombat) PlayerCombat->ShowMessage(FString::Printf(TEXT("%s glows: travel here from the map"), *P.Name));
		return TEXT("waystone");
	}
	GI->WaystonesLit15.Add(Id);
	WildFound.Add(Id);
	GlowWaystone15(Id);
	if (PlayerCombat) PlayerCombat->ShowMessage(FString::Printf(TEXT("You light %s: travel here from the map"), *P.Name));
	if (const FRewardLaid15* Rl = WaystonesLaid15.Find(Id)) PlaySoundAt(TEXT("Player.Loot"), Rl->At);          // (at the stone, its ground's height (PR #108's review: at z 0))
	UE_LOG(LogRDList15o, Log, TEXT("RDWAYSTONE15 %s lit (%d)"), *P.Name, Id);
	WildAutosave(TEXT("found"));
	return TEXT("light");
}

FString ARDDungeonGenerator::WaystoneDescribe15(int32 Id) const
{
	return IsWaystoneLit15(Id) ? FString(TEXT("the waystone glows")) : FString(TEXT("light the waystone"));
}

TArray<FString> ARDDungeonGenerator::GetWaystones15(float Km) const
{
	// (tests: "id|name|x|y|found|lit|laid" for the waystones within Km)
	TArray<FString> Out;
	const APawn* Her = UGameplayStatics::GetPlayerPawn(this, 0);
	if (!Her || !IsWildReady()) return Out;
	const FVector2D H2(Her->GetActorLocation().X / 100.0, Her->GetActorLocation().Y / 100.0);
	EnsureWaystoneVeto15();
	const int32 R = FMath::CeilToInt(Km * 1000.0 / Wild->CellM);
	const FIntPoint C0 = Wild->LookoutCellOf(H2.X, H2.Y);
	for (int32 I = -R; I <= R; ++I) for (int32 J = -R; J <= R; ++J)
	{
		FRDWildPlace P;
		if (!Wild->WaystoneOf(C0 + FIntPoint(I, J), P) || FVector2D::Distance(P.At, H2) > Km * 1000.0) continue;
		Out.Add(FString::Printf(TEXT("%d|%s|%.1f|%.1f|%d|%d|%d"), P.Id, *P.Name, P.At.X, P.At.Y, WildFound.Contains(P.Id) ? 1 : 0, IsWaystoneLit15(P.Id) ? 1 : 0, WaystonesLaid15.Contains(P.Id) ? 1 : 0));
	}
	return Out;
}

void ARDDungeonGenerator::EnsureWaystoneVeto15() const
{
	// (the generator's own layers a waystone keeps clear of: its region landmarks (two a region's cell), 80 m; set before any waystone is
	// worked out and kept)
	if (!Wild || Wild->WaystoneVeto) return;
	Wild->WaystoneVeto = [this](const FVector2D& S)
	{
		ParseRegionLandmarks15();
		const FIntPoint Lc = Wild->LookoutCellOf(S.X, S.Y);
		for (int32 I = -1; I <= 1; ++I) for (int32 J = -1; J <= 1; ++J) for (int32 Sl = 0; Sl < 2; ++Sl)
		{
			FRegionLandmark15 Lm;
			if (RegionLandmarkOf15(Lc + FIntPoint(I, J), Sl, Lm) && FVector2D::Distance(Lm.At, S) < 80.0) return true;
		}
		return false;
	};
}

void ARDDungeonGenerator::ForgetWaystones15(const TArray<int32>& Ids)
{
	// (tests: the waystones named forgotten (unlit, not found), their glows out: only those the test touched (PR #108's review: every one of
	// a played save's went))
	URDGameInstance* GI = URDGameInstance::Of(this);
	for (const int32 Id : Ids)
	{
		if (GI) GI->WaystonesLit15.Remove(Id);
		WildFound.Remove(Id);
		if (FRewardLaid15* R = WaystonesLaid15.Find(Id)) { DropReward15(*R); WaystonesLaid15.Remove(Id); }
	}
}

void ARDDungeonGenerator::DropWaystonesAndPosts15()
{
	// (everything the two layers laid: with the wilds dropped (WildDropAll), or a switch turned off (PR #108's review))
	for (auto& Kv : WaystonesLaid15) DropReward15(Kv.Value);
	WaystonesLaid15.Reset();
	for (auto& Kv : CrossPostActors15) if (Kv.Value.IsValid()) Kv.Value->Destroy();
	CrossPostActors15.Reset();
}

// ================================================================================================ the crossroads posts
void ARDDungeonGenerator::CrossroadsNear15(const FVector2D& P, double R, TArray<int32>& Out) const
{
	// (the world's crossroads hashed into 500 m cells once, then those within R of P)
	if (CrossHashFor15 != Wild->Crossroads.Num())
	{
		CrossHash15.Reset();
		for (int32 Ci = 0; Ci < Wild->Crossroads.Num(); ++Ci) CrossHash15.Add(FIntPoint(FMath::FloorToInt(Wild->Crossroads[Ci].X / 500.0), FMath::FloorToInt(Wild->Crossroads[Ci].Y / 500.0)), Ci);
		CrossHashFor15 = Wild->Crossroads.Num();
	}
	const int32 N = FMath::CeilToInt(R / 500.0);
	const FIntPoint C0(FMath::FloorToInt(P.X / 500.0), FMath::FloorToInt(P.Y / 500.0));
	for (int32 I = -N; I <= N; ++I) for (int32 J = -N; J <= N; ++J)
		for (auto It = CrossHash15.CreateConstKeyIterator(C0 + FIntPoint(I, J)); It; ++It)
			if (FVector2D::Distance(Wild->Crossroads[It.Value()], P) <= R) Out.Add(It.Value());
}
bool ARDDungeonGenerator::CrossPostOf15(int32 Ci, FCrossPost15& Out) const
{
	if (const FCrossPost15* Got = CrossPosts15.Find(Ci)) { Out = *Got; return Got->Arms.Num() > 0; }
	FCrossPost15 C;
	if (Wild && Wild->Crossroads.IsValidIndex(Ci))
	{
		const FVector2D X = Wild->Crossroads[Ci];
		TArray<int32> Rs;
		const FBox2D Bx(X - FVector2D(30.0), X + FVector2D(30.0));
		Wild->RoadsIn(Bx, false, Rs); Wild->RoadsIn(Bx, true, Rs);
		TSet<int32> Seen;
		for (const int32 Ri : Rs)
		{
			if (Seen.Contains(Ri)) continue;
			Seen.Add(Ri);
			const FRDWildWorld::FRoad& R = Wild->Roads[Ri];
			if (R.bTrack && !R.bMinor) continue;          // (a plain track leads to no named place)
			// (its nearest point to the crossroads and how far along the road that is)
			double Acc = 0.0, BestD = 1e12, BestS = 0.0; FVector2D BestDir(1, 0);
			for (int32 I = 0; I + 1 < R.P.Num(); ++I)
			{
				const double L = FVector2D::Distance(R.P[I], R.P[I + 1]);
				const FVector2D Q = FMath::ClosestPointOnSegment2D(X, R.P[I], R.P[I + 1]);
				const double D = FVector2D::Distance(Q, X);
				if (D < BestD) { BestD = D; BestS = Acc + FVector2D::Distance(R.P[I], Q); BestDir = (R.P[I + 1] - R.P[I]).GetSafeNormal(); }
				Acc += L;
			}
			if (BestD > 15.0) continue;
			const double L = Acc;
			auto AddArm = [&](const FString& Name, double M, const FVector2D& Dir)
			{
				if (Name.IsEmpty() || M < 40.0) return;
				// (one arm a place: two roads on one line (merged) or a minor road's join name the same place: the nearer kept)
				for (FCrossArm15& A : C.Arms) if (A.Name == Name) { if (M < A.M) { A.M = (float)M; A.Dir = Dir; } return; }
				C.Arms.Add(FCrossArm15{ Name, (float)M, Dir });
			};
			if (!R.bTrack && Wild->Towns.IsValidIndex(R.To) && Wild->Towns.IsValidIndex(R.From))
			{
				AddArm(Wild->Towns[R.To].Name, L - BestS, BestDir);
				AddArm(Wild->Towns[R.From].Name, BestS, -BestDir);
			}
			else if (R.bMinor)
			{
				// (back along it to its place, as its own signs say, unless its join's own sign stands right there naming it (PR #108's review:
				// two posts naming one village 10 m apart); on toward what it joins only where it goes on past the crossroads: at its join
				// its last segment points across the major road, whose own arms name the towns)
				TArray<int32> Sn; Wild->SignsNear(X, 30.0, Sn);
				const bool bJoinSign = Sn.ContainsByPredicate([&](int32 K) { return Wild->Signs[K].Kind == 2 && Wild->Signs[K].A == R.Dest; });
				if (!bJoinSign) AddArm(R.Dest, BestS, -BestDir);
				if (L - BestS > 40.0) AddArm(R.Up, (L - BestS) + R.UpM, BestDir);
			}
		}
		// (the post 7 m from the crossroads, off every road: the first of eight ways that is dry and off the roads)
		for (int32 K = 0; K < 8 && C.Arms.Num() > 0; ++K)
		{
			const FVector2D P = X + FVector2D(FMath::Cos(K * PI / 4.0 + 0.4), FMath::Sin(K * PI / 4.0 + 0.4)) * 7.0;
			FRDWSample S; Wild->Sample(P.X, P.Y, S, false);
			TArray<int32> Sn; Wild->SignsNear(P, 5.0, Sn);
			if (S.WaterKind == 0 && S.Road < 0.05f && Sn.Num() == 0 && Wild->ClearOfPlaces15(P, 12.0, false)) { C.At = P; C.bPlaced = true; break; }          // (off the signs and the crossroads' scenery's pieces (PR #108's review))
		}
		if (!C.bPlaced) C.Arms.Reset();
		C.Arms.Sort([](const FCrossArm15& A, const FCrossArm15& B) { return A.M < B.M; });
		if (C.Arms.Num() > 4) C.Arms.SetNum(4);          // (four arms at most on one post: the nearest places)
	}
	CrossPosts15.Add(Ci, C);
	Out = C;
	return C.Arms.Num() > 0;
}

void ARDDungeonGenerator::TickCrossPosts15(float Dt, const FVector& Her)
{
	CrossLook15 -= Dt;
	if (CrossLook15 > 0.f || !IsWildReady() || !bCrossPosts15) return;
	CrossLook15 = 0.5f;
	if (!bCrossPosts15 && CrossPostActors15.Num() > 0) { for (auto& Kv : CrossPostActors15) if (Kv.Value.IsValid()) Kv.Value->Destroy(); CrossPostActors15.Reset(); }
	const FVector2D H2(Her.X / 100.0, Her.Y / 100.0);
	TSet<int32> Want;
	int32 Made = 0;
	TArray<int32> Near; CrossroadsNear15(H2, 330.0, Near);          // (by a hash of 500 m cells (PR #108's review: every crossroads of the continent twice a second))
	for (const int32 Ci : Near)
	{
		const double D = FVector2D::Distance(Wild->Crossroads[Ci], H2);
		if (CrossPostActors15.Contains(Ci)) { Want.Add(Ci); continue; }
		if (D > 250.0 || Made >= 2) continue;
		FCrossPost15 C;
		if (!CrossPostOf15(Ci, C)) continue;
		TArray<FSignArm14> Arms;
		for (const FCrossArm15& A : C.Arms) Arms.Add(FSignArm14{ A.Name, A.M, (float)FMath::RadiansToDegrees(FMath::Atan2(-A.Dir.X, A.Dir.Y)) });
		if (AActor* Ac = SpawnSignPost14(C.At, 0.f, Arms, FString::Printf(TEXT("cross15:%d"), Ci))) { CrossPostActors15.Add(Ci, Ac); Want.Add(Ci); ++Made; }
	}
	for (auto It = CrossPostActors15.CreateIterator(); It; ++It)
		if (!Want.Contains(It.Key()) || !It.Value().IsValid()) { if (It.Value().IsValid()) It.Value()->Destroy(); It.RemoveCurrent(); }
}

TArray<FString> ARDDungeonGenerator::GetCrossPosts15(float Km) const
{
	// (tests: "post|crossroads|x|y|laid|arms" then "arm|crossroads|name|metres|dir x|dir y|text components on the post" for each within Km)
	TArray<FString> Out;
	const APawn* Her = UGameplayStatics::GetPlayerPawn(this, 0);
	if (!Her || !IsWildReady()) return Out;
	const FVector2D H2(Her->GetActorLocation().X / 100.0, Her->GetActorLocation().Y / 100.0);
	TArray<int32> Near; CrossroadsNear15(H2, Km * 1000.0, Near);
	for (const int32 Ci : Near)
	{
		FCrossPost15 C;
		if (!CrossPostOf15(Ci, C)) continue;
		const TWeakObjectPtr<AActor>* A = CrossPostActors15.Find(Ci);
		int32 Texts = 0;
		if (A && A->IsValid()) { TArray<UActorComponent*> Tc = (*A)->GetComponentsByTag(UActorComponent::StaticClass(), TEXT("SignText14")); Texts = Tc.Num(); }
		Out.Add(FString::Printf(TEXT("post|%d|%.1f|%.1f|%d|%d|%d"), Ci, C.At.X, C.At.Y, A && A->IsValid() ? 1 : 0, C.Arms.Num(), Texts));
		for (const FCrossArm15& Ar : C.Arms) Out.Add(FString::Printf(TEXT("arm|%d|%s|%.0f|%.3f|%.3f"), Ci, *Ar.Name, Ar.M, Ar.Dir.X, Ar.Dir.Y));
	}
	return Out;
}
