// Heaven (the user's list of 2026-11-08b, docs/improvements9.txt: "a modern city that is surrounded by a shimmering shield. it is
// characterized by modern skyscrapers, office buildings, modern shops, modern streets, modern vehicles navigating the streets
// ... the outside and entrance of the dungeon is a foreboding research facility called 'Kratos Aurorim Research, LLC'"). The
// city is the wilderness's last town (the generator's TownPlan 5, RDTownPlan.cpp's bModern: the facility at the town's middle,
// a grid of straight streets, towers, office blocks, shops and apartments of concrete, glass and steel). Its town section's
// theme is "Heaven": every piece the town asks for is Heaven's own where 908 made one ("Heaven.<name>": the wall and its towers
// in glass and steel, the furniture). This file builds:
//   - the research facility: its lobby and laboratory hall in Heaven's laboratory pieces ("Lab.*"), a dark glass block over
//     the hall, its name over the door, the security door at the hall's far wall (walked into with the Kratos Keycard it opens
//     the fortress: RDTownGame.cpp, as the other cities' ways down; RDKeys.cpp refuses it without its key);
//   - a building's flat roof and parapet ("Modern.*"); a tower's floors over its lobby ("Heaven.TowerMid", "Heaven.TowerTop");
//   - the streets' asphalt, the pavements and the paving of the open ground ("Heaven.Road", "Heaven.Paving");
//   - a street light or a street's furniture (a bench, a bus stop, a hydrant, a bin);
//   - the shimmering shield over the whole town ("Heaven.Dome") and the cars driving its streets (play's own meshes).
#include "RD/RDSection.h"
#include "RD/RDDungeonGenerator.h"
#include "RD/RDTown.h"
#include "Engine/World.h"
#include "Engine/StaticMesh.h"
#include "Components/StaticMeshComponent.h"
#include "Components/PointLightComponent.h"
#include "Components/TextRenderComponent.h"

DEFINE_LOG_CATEGORY_STATIC(LogRDHeaven, Log, All);

static const FIntPoint RDHeavenDir4[4] = { FIntPoint(-1, 0), FIntPoint(1, 0), FIntPoint(0, -1), FIntPoint(0, 1) };
static const FName RDHeavenCarTag(TEXT("HeavenCar"));
static const FName RDHeavenDomeTag(TEXT("HeavenDome"));

void ARDSection::ResearchShell(int32 BI)
{
	FTownBld& B = TownBlds[BI];
	const float M = Generator->TileSize;
	const FName Wall(TEXT("Lab.Wall")), Floor(TEXT("Lab.Floor")), Ceil(TEXT("Lab.Ceil")), Roof(TEXT("Lab.Roof")), Doorway(TEXT("Lab.Doorway"));
	const FRDPiece* Wp = Generator->Piece(Wall);
	const FRDPiece* Dp = Generator->Piece(Doorway);
	const float T = Wp ? FMath::Clamp((float)Wp->Size.X, 10.f, 80.f) : 30.f;
	const float WZ = Wp ? FMath::Max((float)Wp->Size.Z - 1.f, 50.f) : 300.f;
	auto HeightOf = [&](int32 K) { return K == 0 ? 600.f : 900.f; };
	auto Stack = [&](FName Nm, const FVector& At, float Yaw, float Z0, float Z1)
	{
		for (float Z = Z0; Z < Z1 - 5.f; Z += WZ)
			AddPiece(Nm, FTransform(FRotator(0, Yaw, 0), At + FVector(0, 0, Z), FVector(1.f, 1.f, FMath::Min(1.f, (Z1 + 1.f - Z) / (WZ + 1.f)))));
	};
	// ---- the rooms: concrete and glass walls, a polished floor, a ceiling of light panels, a flat roof; the doorways glass doors
	for (int32 K = 0; K < B.Rooms.Num(); ++K)
	{
		const int32 RI = B.Rooms[K];
		const FRoom& Rm = Rooms[RI];
		const float H = HeightOf(K);
		for (int32 X = Rm.Min.X; X < Rm.Max.X; ++X)
			for (int32 Y = Rm.Min.Y; Y < Rm.Max.Y; ++Y)
			{
				const FIntPoint Tl(X, Y);
				const FVector C = TileWorld(Tl);
				AddPieceAt(Floor, C, 0.f);
				AddPieceAt(Ceil, C + FVector(0, 0, H), 0.f, 1.f, true);
				AddPieceAt(Roof, C + FVector(0, 0, H + 2.f), 0.f, 1.f, true);
				for (int32 Side = 0; Side < 4; ++Side)
				{
					const FIntPoint Nb = Tl + RDHeavenDir4[Side];
					const int32 On = In(Nb) ? Owner[Idx(Nb)] : -1;
					if (On == RI) continue;
					const bool bOut = B.Rooms.IndexOfByKey(On) == INDEX_NONE;
					const bool bDoor = DoorEdges.Contains(EdgeKey(Tl, Nb));
					const FVector Edge = C + FVector(RDHeavenDir4[Side].X, RDHeavenDir4[Side].Y, 0) * (M * 0.5f);
					const float Yaw = InwardYaw(Side);
					const FVector OutW = FRotator(0, Yaw, 0).RotateVector(FVector(-1, 0, 0));
					// (between two rooms each its own wall half a thickness into its room, as the castle's)
					const FVector At = bOut ? Edge : Edge - OutW * (T * 0.5f);
					if (bDoor)
					{
						AddPieceAt(Doorway, At, Yaw);
						Stack(Wall, At, Yaw, Dp ? Dp->Size.Z - 1.f : 300.f, H);
						continue;
					}
					Stack(Wall, At, Yaw, 0.f, H);
				}
			}
	}
	// ---- the hall's light: cold white panels; a dark glass block over the hall, the facility's name over its door
	if (B.Rooms.Num() >= 2)
	{
		const FRoom& Hl = Rooms[B.Rooms[1]];
		for (int32 X = Hl.Min.X + 2; X < Hl.Max.X - 1; X += 4)
			for (int32 Y = Hl.Min.Y + 2; Y < Hl.Max.Y - 1; Y += 4)
				AddLight(TileWorld(FIntPoint(X, Y)) + FVector(0, 0, 820.f), FLinearColor(0.85f, 0.93f, 1.f), 300.f, 1800.f, false, 0.f);
		const FVector Hc = (TileWorld(Hl.Min) + TileWorld(Hl.Max - FIntPoint(1, 1))) * 0.5f;
		if (const FRDPiece* Bx = Generator->Piece(TEXT("Lab.Block")))
		{
			const FVector2D Sz((Hl.Max.X - Hl.Min.X) * M, (Hl.Max.Y - Hl.Min.Y) * M);
			const float Hb = 2400.f;
			AddPiece(TEXT("Lab.Block"), FTransform(FRotator::ZeroRotator, Hc + FVector(0, 0, HeightOf(1) + 30.f), FVector(Sz.X * 0.86f / FMath::Max((float)Bx->Size.X, 1.f), Sz.Y * 0.86f / FMath::Max((float)Bx->Size.Y, 1.f), Hb / FMath::Max((float)Bx->Size.Z, 1.f))), true);
			HeavenTallestZ = FMath::Max(HeavenTallestZ, HeightOf(1) + 30.f + Hb);
			// (a red warning light at each top corner of the block)
			for (int32 Cx = -1; Cx <= 1; Cx += 2)
				for (int32 Cy = -1; Cy <= 1; Cy += 2)
					AddLight(Hc + FVector(Cx * Sz.X * 0.43f, Cy * Sz.Y * 0.43f, HeightOf(1) + 60.f + Hb), FLinearColor(1.f, 0.08f, 0.05f), 400.f, 1500.f, false, 0.f);
		}
	}
	{
		// (its name over the front door outside, the company's own white letters; read from the forecourt)
		const FVector Front = FVector(RDHeavenDir4[B.DoorSide].X, RDHeavenDir4[B.DoorSide].Y, 0.f);
		const FVector At = TileWorld(B.DoorTile) + Front * (M * 0.5f + 8.f) + FVector(0, 0, 470.f);
		if (bBuildStatic)
		{
			UTextRenderComponent* Tx = NewObject<UTextRenderComponent>(this, NAME_None, RF_Transactional);
			Tx->SetupAttachment(RootComponent);
			Tx->SetMobility(EComponentMobility::Static);
			Tx->SetText(FText::FromString(TEXT("KRATOS AURORIM RESEARCH, LLC")));
			Tx->SetHorizontalAlignment(EHTA_Center);
			Tx->SetVerticalAlignment(EVRTA_TextCenter);
			Tx->SetWorldSize(64.f);
			Tx->SetTextRenderColor(FColor(225, 238, 255));
			Tx->SetCollisionEnabled(ECollisionEnabled::NoCollision);
			Tx->ComponentTags.Add(TEXT("HeavenSign"));
			Tx->SetWorldLocationAndRotation(At, Front.Rotation());
			Tx->RegisterComponent();
			AddInstanceComponent(Tx);
		}
		AddLight(At + Front * 120.f, FLinearColor(0.8f, 0.9f, 1.f), 260.f, 1400.f, false, 0.f);
	}
	// ---- the security door down into the fortress: its frame at the hall's far wall, a red light over it
	AddPieceAt(TEXT("Lab.Gate"), MistgateAt + MistgateNormal * 30.f, MistgateNormal.Rotation().Yaw, 1.f, true);
	AddLight(MistgateAt + MistgateNormal * 220.f + FVector(0, 0, 320.f), FLinearColor(1.f, 0.1f, 0.06f), 300.f, 1200.f, false, 0.f);
	B.Style = 7;          // (its doors Heaven's: glass)
	UE_LOG(LogRDHeaven, Log, TEXT("RDHEAVEN the research facility built: %d rooms, the security door at (%.0f, %.0f)"), B.Rooms.Num(), MistgateAt.X, MistgateAt.Y);
}

void ARDSection::ModernRoof(int32 BI, float Top)
{
	const FTownBld& B = TownBlds[BI];
	const float M = Generator->TileSize;
	const int32 Nx = B.DoorSide < 2 ? B.Max.X - B.Min.X : B.Max.Y - B.Min.Y;
	const int32 Ny = B.DoorSide < 2 ? B.Max.Y - B.Min.Y : B.Max.X - B.Min.X;
	const float Hx = Nx * M * 0.5f, Hy = Ny * M * 0.5f;
	const float Yaw0 = TownBldYaw(B);
	auto WallT = [&](const FVector2D& P, const FVector2D& Out, float Z)
	{
		const FVector Ow = FRotator(0, Yaw0, 0).RotateVector(FVector(Out.X, Out.Y, 0));
		return FTransform(FRotator(0, Ow.Rotation().Yaw, 0), TownBldPoint(B, P.X, P.Y, Z));
	};
	// ---- the roof: a slab a tile, a parapet round its edge
	for (int32 I = 0; I < Nx; ++I)
		for (int32 J = 0; J < Ny; ++J)
			AddPiece(TEXT("Modern.Roof"), FTransform(FRotator(0, Yaw0, 0), TownBldPoint(B, (I + 0.5f) * M - Hx, (J + 0.5f) * M - Hy, Top)), true);
	const struct { FVector2D Out; int32 N; } Sides[4] = { { FVector2D(1, 0), Ny }, { FVector2D(-1, 0), Ny }, { FVector2D(0, 1), Nx }, { FVector2D(0, -1), Nx } };
	for (int32 Si = 0; Si < 4; ++Si)
		for (int32 K = 0; K < Sides[Si].N; ++K)
		{
			const FVector2D P = Si < 2 ? FVector2D(Sides[Si].Out.X * Hx, (K + 0.5f) * M - Hy) : FVector2D((K + 0.5f) * M - Hx, Sides[Si].Out.Y * Hy);
			AddPiece(TEXT("Modern.Parapet"), WallT(P, Sides[Si].Out, Top), true);
		}
	HeavenTallestZ = FMath::Max(HeavenTallestZ, Top);
	// ---- a tower: its floors stacked over the lobby, fitted to the lobby's footprint, its rooftop; how many floors by its seed
	if (B.Kind == TK_SkyTower)
	{
		const FRDPiece* Mid = Generator->Piece(TEXT("Heaven.TowerMid"));
		const FRDPiece* TopP = Generator->Piece(TEXT("Heaven.TowerTop"));
		if (!Mid) return;
		const float Fx = Nx * M / FMath::Max((float)Mid->Size.X, 1.f), Fy = Ny * M / FMath::Max((float)Mid->Size.Y, 1.f);
		const int32 Floors = 4 + (int32)(B.Seed % 7u);
		float Z = Top + 30.f;
		const float Step = FMath::Max((float)Mid->Size.Z - 22.f, 100.f);
		for (int32 K = 0; K < Floors; ++K, Z += Step)
			AddPiece(TEXT("Heaven.TowerMid"), FTransform(FRotator(0, Yaw0, 0), TownBldPoint(B, 0.f, 0.f, Z), FVector(Fx, Fy, 1.f)), true);
		if (TopP) AddPiece(TEXT("Heaven.TowerTop"), FTransform(FRotator(0, Yaw0, 0), TownBldPoint(B, 0.f, 0.f, Z), FVector(Fx, Fy, 1.f)), true);
		HeavenTallestZ = FMath::Max(HeavenTallestZ, Z + (TopP ? (float)TopP->Size.Z : 0.f));
	}
	// ---- an office block's roof plant: a unit or two by its seed
	else if (B.Kind == TK_Office)
	{
		FRandomStream R((int32)(B.Seed ^ 0x0FF1CEu));
		for (int32 K = 0; K < 1 + R.RandRange(0, 1); ++K)
			AddPiece(TEXT("Modern.RoofUnit"), FTransform(FRotator(0, Yaw0 + 90.f * R.RandRange(0, 3), 0), TownBldPoint(B, R.FRandRange(-Hx * 0.5f, Hx * 0.5f), R.FRandRange(-Hy * 0.5f, Hy * 0.5f), Top + 25.f)));
	}
}

void ARDSection::HeavenStreets()
{
	// (every tile of the open ground: the streets asphalt, the rest (the square, the pavements, the lane by the wall) paving; no
	// grass in Heaven. Under the buildings nothing: they have floors)
	int32 Roads = 0, Paved = 0;
	for (int32 X = 0; X < N; ++X)
		for (int32 Y = 0; Y < N; ++Y)
		{
			const FIntPoint T(X, Y);
			if (Type[Idx(T)] != 2 || Owner[Idx(T)] != 1000) continue;
			const FVector C = TileWorld(T);
			const bool bRoad = TownRoadMask[Idx(T)] == 1 && !TownSquare.Contains(T);
			if (AddPieceAt(bRoad ? FName(TEXT("Heaven.Road")) : FName(TEXT("Heaven.Paving")), C, 0.f, 1.f, true)) { if (bRoad) ++Roads; else ++Paved; }
		}
	UE_LOG(LogRDHeaven, Log, TEXT("RDHEAVEN streets: %d tiles of asphalt, %d paved"), Roads, Paved);
}

void ARDSection::HeavenSpotBuild(const FTownSpot& Sp)
{
	if (Sp.Kind == TS_StreetLight)
	{
		// (its arm out over the street; one in three lit (the town's lights are many already))
		AddPieceAt(TEXT("Heaven.StreetLight"), Sp.At, Sp.Yaw);
		if (HashCombine(GetTypeHash(FIntPoint(FMath::RoundToInt(Sp.At.X), FMath::RoundToInt(Sp.At.Y))), 0x11u) % 3u == 0u)
			AddLight(Sp.At + FRotator(0, Sp.Yaw, 0).RotateVector(FVector(260.f, 0, 0)) + FVector(0, 0, 740.f), FLinearColor(1.f, 0.9f, 0.75f), 220.f, 1700.f, false, 0.f);
		MarkBlocked(Sp.At, 0.f, FVector2D(90.f, 90.f), true);
		return;
	}
	if (Sp.Kind == TS_TrafficLight) { AddPieceAt(TEXT("Heaven.TrafficLight"), Sp.At, Sp.Yaw); MarkBlocked(Sp.At, 0.f, FVector2D(60.f, 60.f), true); return; }
	// (the street's bench is its own piece: "Heaven.Bench" is the rooms' (the town's furnishing asks for "Bench"))
	static const TCHAR* Props[4] = { TEXT("Heaven.StreetBench"), TEXT("Heaven.BusStop"), TEXT("Heaven.Hydrant"), TEXT("Heaven.Bin") };
	const FName Nm(Props[FMath::Clamp(Sp.Bld, 0, 3)]);
	// (a bench and a bus stop face the street: along it)
	AddPieceAt(Nm, Sp.At, Sp.Yaw + (Sp.Bld <= 1 ? 90.f : 0.f));
	const FRDPiece* P = Generator->Piece(Nm);
	MarkBlocked(Sp.At, Sp.Yaw + (Sp.Bld <= 1 ? 90.f : 0.f), P ? FVector2D(P->Size.X + 20.f, P->Size.Y + 20.f) : FVector2D(100.f, 100.f), true);
}

void ARDSection::HeavenWorks()
{
	const float M = Generator->TileSize;
	HeavenCars.Reset();
	// ---- the shield: a dome over the whole town, its middle the town's, reaching past the outline's farthest corner
	if (const FRDPiece* Dm = Generator->Piece(TEXT("Heaven.Dome")); Dm && Dm->Mesh)
	{
		FVector2D Mid(0, 0);
		for (const FVector2D& P : TownBorder) Mid += P;
		Mid /= FMath::Max(1, TownBorder.Num());
		float Rad = 0.f;
		for (const FVector2D& P : TownBorder) Rad = FMath::Max(Rad, (float)FVector2D::Distance(P, Mid));
		Rad += 1500.f;
		const float Sc = 2.f * Rad / FMath::Max((float)Dm->Size.X, 1.f);
		const FVector At(Mid.X, Mid.Y, GetActorLocation().Z);
		UStaticMeshComponent* C = AddMesh(RootComponent, Dm->Mesh, Dm->Adjust * FTransform(FRotator::ZeroRotator, At - GetActorLocation(), FVector(Sc)), false);
		if (C)
		{
			if (Dm->Material) for (int32 K = 0; K < C->GetNumMaterials(); ++K) C->SetMaterial(K, Dm->Material);
			C->SetCastShadow(false);
			C->SetCollisionEnabled(ECollisionEnabled::NoCollision);
			C->LDMaxDrawDistance = 0.f; C->SetCachedMaxDrawDistance(0.f);
			C->ComponentTags.Add(RDHeavenDomeTag);
			HeavenDomeRadius = Rad;
		}
	}
	// ---- the traffic: on every street 14 tiles long or more, a car every 70 m or so in each lane, of the kinds 908 made (at 45 m
	// 160 cars drove the streets)
	TArray<const FRDPiece*> Kinds;
	for (int32 K = 1; K <= 6; ++K) if (const FRDPiece* P = Generator->Piece(FName(*FString::Printf(TEXT("Heaven.Car_%d"), K)))) if (P->Mesh) Kinds.Add(P);
	if (Kinds.Num() == 0) return;
	int32 Made = 0;
	// (not on the main road or the cross road through the square: PR #33's review: cars drove across the paved square and turned
	// back among the director and the guards at the facility's door)
	FIntRect Keep = TownSquare;
	if (TownBlds.IsValidIndex(CastleBld)) Keep.Union(FIntRect(TownBlds[CastleBld].Min, TownBlds[CastleBld].Max));
	Keep.InflateRect(3);
	for (int32 Ri = 0; Ri < TownRoads.Num(); ++Ri)
	{
		const FIntRect& Rr = TownRoads[Ri];
		const bool bAlongX = Rr.Width() >= Rr.Height();
		const int32 Len = bAlongX ? Rr.Width() : Rr.Height(), Wd = bAlongX ? Rr.Height() : Rr.Width();
		if (Len < 14 || Wd < 3) continue;
		if (Rr.Intersect(Keep)) continue;
		// (the street's middle line, from end to end, a tile in from each end)
		const FVector A = bAlongX ? (TileWorld(FIntPoint(Rr.Min.X + 1, Rr.Min.Y)) + TileWorld(FIntPoint(Rr.Min.X + 1, Rr.Max.Y - 1))) * 0.5f
		                          : (TileWorld(FIntPoint(Rr.Min.X, Rr.Min.Y + 1)) + TileWorld(FIntPoint(Rr.Max.X - 1, Rr.Min.Y + 1))) * 0.5f;
		const FVector Bv = bAlongX ? (TileWorld(FIntPoint(Rr.Max.X - 2, Rr.Min.Y)) + TileWorld(FIntPoint(Rr.Max.X - 2, Rr.Max.Y - 1))) * 0.5f
		                           : (TileWorld(FIntPoint(Rr.Min.X, Rr.Max.Y - 2)) + TileWorld(FIntPoint(Rr.Max.X - 1, Rr.Max.Y - 2))) * 0.5f;
		const float L = FVector::Dist2D(A, Bv);
		const int32 Per = FMath::Max(1, FMath::FloorToInt(L / 7000.f));
		for (int32 Lane = 0; Lane < 2; ++Lane)
			for (int32 K = 0; K < Per; ++K)
			{
				const uint32 Hh = HashCombine(GetTypeHash(Rr.Min), GetTypeHash(FIntPoint(Lane, K)));
				const FRDPiece* P = Kinds[Hh % (uint32)Kinds.Num()];
				USceneComponent* Pv = AddPivot(RootComponent, FTransform::Identity);
				if (!Pv) continue;
				UStaticMeshComponent* C = AddMesh(Pv, P->Mesh, P->Adjust, true);
				if (C)
				{
					if (P->Material) C->SetMaterial(0, P->Material);
					C->ComponentTags.Add(RDHeavenCarTag);
				}
				Pv->ComponentTags.Add(RDHeavenCarTag);
				FRDHeavenCar Cr;
				Cr.C = Pv; Cr.L0 = A; Cr.L1 = Bv; Cr.bFwd = Lane == 0; Cr.Street = Ri;
				Cr.S = (K + 0.5f + ((Hh >> 8) % 100u) / 400.f) / Per * L;
				Cr.Speed = 800.f + (float)((Hh >> 12) % 400u);
				HeavenCars.Add(Cr);
				++Made;
			}
	}
	TickHeavenCars(0.f, FVector(1e9));
	UE_LOG(LogRDHeaven, Log, TEXT("RDHEAVEN the shield %.0f m across, %d cars on the streets"), HeavenDomeRadius * 0.02f, Made);
}

void ARDSection::TickHeavenCars(float Dt, const FVector& Her)
{
	// each car drives its lane (the right of its way); at the street's end it turns back into the other lane. It waits while she
	// or another car stands within 9 m ahead of it in its lane, so it never drives into her
	// (PR #33's review: still while she is far beyond the shield (they stand where they were); each car checks only its own
	// street's cars)
	if (HeavenDomeRadius > 0.f && Dt > 0.f)
	{
		FVector2D Mid(0, 0);
		for (const FVector2D& P : TownBorder) Mid += P;
		Mid /= FMath::Max(1, TownBorder.Num());
		if (FVector2D::Distance(Mid, FVector2D(Her.X, Her.Y)) > HeavenDomeRadius + 30000.f) return;
	}
	for (int32 I = 0; I < HeavenCars.Num(); ++I)
	{
		FRDHeavenCar& Cr = HeavenCars[I];
		USceneComponent* C = Cr.C.Get();
		if (!C) continue;
		const FVector Way = (Cr.L1 - Cr.L0).GetSafeNormal2D() * (Cr.bFwd ? 1.f : -1.f);
		const FVector Right(-Way.Y, Way.X, 0.f);
		const float L = FVector::Dist2D(Cr.L0, Cr.L1);
		const FVector Here = (Cr.bFwd ? Cr.L0 : Cr.L1) + Way * Cr.S + Right * Cr.Lane;
		bool bWait = false;
		{
			const FVector D = Her - Here;
			const float Ahead = FVector::DotProduct(D, Way), Side = FMath::Abs(FVector::DotProduct(D, Right));
			if (Ahead > -150.f && Ahead < 900.f && Side < 260.f && FMath::Abs(D.Z) < 400.f) bWait = true;
		}
		for (int32 J = 0; J < HeavenCars.Num() && !bWait; ++J)
		{
			if (J == I) continue;
			const FRDHeavenCar& O = HeavenCars[J];
			if (O.Street != Cr.Street || O.bFwd != Cr.bFwd) continue;
			const float Gap = O.S - Cr.S;
			if (Gap > 0.f && Gap < 900.f) bWait = true;
		}
		if (!bWait) Cr.S = FMath::Min(Cr.S + Cr.Speed * Dt, L);
		// (at the street's end it turns into the other lane, only once that lane's start is clear of her and of its cars (PR #33's
		// review: it jumped 4.4 m across onto whatever stood there))
		if (Cr.S >= L)
		{
			const FVector To = (Cr.bFwd ? Cr.L1 : Cr.L0) - Right * Cr.Lane;
			bool bClear = FVector::Dist2D(To, Her) > 600.f || FMath::Abs(To.Z - Her.Z) > 400.f;
			for (int32 J = 0; J < HeavenCars.Num() && bClear; ++J)
				if (J != I && HeavenCars[J].Street == Cr.Street && HeavenCars[J].bFwd != Cr.bFwd && HeavenCars[J].S < 900.f) bClear = false;
			if (bClear) { Cr.S = 0.f; Cr.bFwd = !Cr.bFwd; }
		}
		const FVector W2 = (Cr.bFwd ? Cr.L1 - Cr.L0 : Cr.L0 - Cr.L1).GetSafeNormal2D();
		const FVector R2(-W2.Y, W2.X, 0.f);
		const FVector P = (Cr.bFwd ? Cr.L0 : Cr.L1) + W2 * Cr.S + R2 * Cr.Lane;          // (UE's +Y is the right of +X: right-hand traffic)
		C->SetWorldLocationAndRotation(FVector(P.X, P.Y, GetActorLocation().Z + 2.f), W2.Rotation());
	}
}
