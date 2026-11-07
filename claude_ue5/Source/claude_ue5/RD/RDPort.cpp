// Graymourne (the user's spec of 2026-11-07, docs/graymourne.txt): "a fog bound port where the tide brings in more bodies than
// ships. this is a sea port on the northern coast. there are lots of docks and ships parked on them. the dungeon is located in
// the sewers. take a sewer entrance to get there". The city is one of the wilderness's towns (the generator's TownPlan 3,
// RDTownPlan.cpp's bPort): the sluice house over the sewers at its middle, an inner harbour along its sea wall (every town's
// ground is at one height, 12 m or more over the sea, and the wilds' land round a town is levelled and dried: the harbour's
// water is the town's own, 1.1 m under the quay), its quay, five piers, the ships and boats moored at them, two wrecks, the
// drowned dead on the quay, gibbets, the fishers' racks; the town's fog thickened round it. This file builds:
//   - the harbour's water and the blockers along the quay's edge and the piers' sides (she walks the piers, not the water);
//   - each harbour spot's things ("Port.*" pieces: 896 sets them);
//   - the sewer gate in the sluice house's far wall (walked into, it opens the sewers: RDTownGame.cpp, as the holy city's stair).
#include "RD/RDSection.h"
#include "RD/RDDungeonGenerator.h"
#include "RD/RDTown.h"
#include "ProceduralMeshComponent.h"
#include "Engine/World.h"

DEFINE_LOG_CATEGORY_STATIC(LogRDPort, Log, All);

namespace
{
	/** the harbour's water under the quay (cm), the walked bottom under it, the drawn bed */
	constexpr float RDPortWaterZ = -110.f, RDPortWalkZ = -170.f, RDPortBedZ = -260.f;
}

bool ARDSection::InHarbourWater(const FIntPoint& T) const
{
	if (TownHarbour.Area() <= 0 || !TownHarbour.Contains(T)) return false;
	for (const FIntRect& Pr : TownPiers) if (Pr.Contains(T)) return false;
	return true;
}

void ARDSection::HarbourBuild()
{
	if (TownHarbour.Area() <= 0) return;
	const float M = Generator->TileSize;
	// ---- the water: one flat sheet over the harbour (the wilds' sea material), a little under the quay's edge
	if (bBuildStatic)
	{
		const FVector A(TownHarbour.Min.X * M, TownHarbour.Min.Y * M, RDPortWaterZ), B(TownHarbour.Max.X * M, TownHarbour.Max.Y * M, RDPortWaterZ);
		const int32 Nx = FMath::Max(2, (TownHarbour.Max.X - TownHarbour.Min.X) + 1), Ny = FMath::Max(2, (TownHarbour.Max.Y - TownHarbour.Min.Y) + 1);
		TArray<FVector> V; TArray<int32> Tr; TArray<FVector> Nm; TArray<FVector2D> Uv;
		for (int32 I = 0; I < Nx; ++I)
			for (int32 J = 0; J < Ny; ++J)
			{
				const FVector P(FMath::Lerp(A.X, B.X, I / float(Nx - 1)), FMath::Lerp(A.Y, B.Y, J / float(Ny - 1)), RDPortWaterZ);
				V.Add(P); Nm.Add(FVector::UpVector); Uv.Add(FVector2D(P.X / 800.f, P.Y / 800.f));
			}
		for (int32 I = 0; I < Nx - 1; ++I)
			for (int32 J = 0; J < Ny - 1; ++J)
			{
				const int32 Aa = I * Ny + J, Bb = (I + 1) * Ny + J, Cc = (I + 1) * Ny + J + 1, Dd = I * Ny + J + 1;
				Tr.Append({ Aa, Cc, Bb, Aa, Dd, Cc });
			}
		UProceduralMeshComponent* W = NewObject<UProceduralMeshComponent>(this, TEXT("HarbourWater"), RF_Transactional);
		W->SetupAttachment(RootComponent);
		W->SetMobility(EComponentMobility::Static);
		W->RegisterComponent();
		AddInstanceComponent(W);
		W->CreateMeshSection(0, V, Tr, Nm, Uv, TArray<FColor>(), TArray<FProcMeshTangent>(), false);
		W->SetCollisionEnabled(ECollisionEnabled::NoCollision);
		W->SetCastShadow(false);
		if (UMaterialInterface* Mt = Generator->WildSeaMaterial ? Generator->WildSeaMaterial.Get() : Generator->WildWaterMaterial.Get()) W->SetMaterial(0, Mt);
	}
	// ---- the blockers: an invisible wall 1.5 m high along every edge where walked ground meets the water (the quay, the
	// harbour's sides, each pier's sides and end)
	int32 Walls = 0;
	auto Blocker = [&](const FVector& P0, const FVector& P1)
	{
		const FVector D = P1 - P0;
		const float Len = D.Size2D();
		if (Len < 10.f) return;
		const FRDPiece* Cp = Generator->Piece(TEXT("Town.Collider"));
		const float Px = Cp ? FMath::Max((float)Cp->Size.X, 1.f) : 100.f, Py = Cp ? FMath::Max((float)Cp->Size.Y, 1.f) : 100.f, Pz = Cp ? FMath::Max((float)Cp->Size.Z, 1.f) : 100.f;
		AddPiece(TEXT("Town.Collider"), FTransform(FRotator(0, D.Rotation().Yaw, 0), (P0 + P1) * 0.5f + FVector(0, 0, -60.f), FVector(Len / Px, 30.f / Py, 210.f / Pz)));
		++Walls;
	};
	for (int32 X = TownHarbour.Min.X; X < TownHarbour.Max.X; ++X)
		for (int32 Y = TownHarbour.Min.Y; Y < TownHarbour.Max.Y; ++Y)
		{
			const FIntPoint T(X, Y);
			if (!InHarbourWater(T)) continue;
			static const FIntPoint Dir[4] = { FIntPoint(-1, 0), FIntPoint(1, 0), FIntPoint(0, -1), FIntPoint(0, 1) };
			for (int32 S_ = 0; S_ < 4; ++S_)
			{
				const FIntPoint Nb = T + Dir[S_];
				if (In(Nb) && InHarbourWater(Nb)) continue;
				if (!In(Nb) || Type[Idx(Nb)] == 0) continue;            // (outside the town or the wall: nothing to keep in)
				const FVector C = TileWorld(T), E = FVector(Dir[S_].X, Dir[S_].Y, 0) * (M * 0.5f), Al(Dir[S_].Y, -Dir[S_].X, 0);
				Blocker(C + E - Al * (M * 0.5f), C + E + Al * (M * 0.5f));
				// (the quay's stone face down to the bed where the land meets the water; the piers stand on their pilings)
				bool bPier = false;
				for (const FIntRect& Pr : TownPiers) if (Pr.Contains(Nb)) bPier = true;
				if (!bPier) AddPiece(TEXT("Port.Quay"), FTransform(FRotator(0, (-FVector(Dir[S_].X, Dir[S_].Y, 0)).Rotation().Yaw, 0), C + E + FVector(0, 0, RDPortBedZ)), true);
			}
		}
	UE_LOG(LogRDPort, Log, TEXT("RDPORT the harbour: %d x %d tiles, %d piers, %d blocker lengths"), TownHarbour.Max.X - TownHarbour.Min.X, TownHarbour.Max.Y - TownHarbour.Min.Y, TownPiers.Num(), Walls);
}

void ARDSection::PortSpotBuild(const FTownSpot& Sp)
{
	FRandomStream R((int32)HashCombine(GetTypeHash(FIntPoint(FMath::RoundToInt(Sp.At.X), FMath::RoundToInt(Sp.At.Y))), 0x9077u));
	const FRotator Ro(0, Sp.Yaw, 0);
	const float M = Generator->TileSize;
	(void)M;
	switch (Sp.Kind)
	{
	case TS_Pier:
	{
		// (the deck from the quay's edge out 16 tiles, 2 wide, its pilings at the corners every other tile, a bollard at the end)
		if (!TownPiers.IsValidIndex(Sp.Bld)) break;
		const FIntRect& Pr = TownPiers[Sp.Bld];
		const FRDPiece* Dk = Generator->Piece(TEXT("Port.Deck"));
		const float Dz = Dk ? (float)Dk->Size.Z : 20.f;
		for (int32 X = Pr.Min.X; X < Pr.Max.X; ++X)
		{
			const FVector C = (TileWorld(FIntPoint(X, Pr.Min.Y)) + TileWorld(FIntPoint(X, Pr.Max.Y - 1))) * 0.5f;
			AddPieceAt(TEXT("Port.Deck"), C - FVector(0, 0, Dz - 6.f), Sp.Yaw + 90.f * R.RandRange(0, 1) * 2.f);
			if ((X - Pr.Min.X) % 2 == 1)
				for (const int32 Yy : { Pr.Min.Y, Pr.Max.Y })
					AddPieceAt(TEXT("Port.Piling"), FVector(C.X, GetActorLocation().Y + Yy * M, GetActorLocation().Z + RDPortBedZ), Sp.Yaw, 1.f, true);
		}
		const FVector End = (TileWorld(FIntPoint(Pr.Max.X - 1, Pr.Min.Y)) + TileWorld(FIntPoint(Pr.Max.X - 1, Pr.Max.Y - 1))) * 0.5f;
		for (const float Sd : { -1.f, 1.f }) AddPieceAt(TEXT("Port.Bollard"), End + FVector(0, Sd * M * 0.8f, 0), Sp.Yaw);
		break;
	}
	case TS_Ship: AddPieceAt(TEXT("Port.Ship"), FVector(Sp.At.X, Sp.At.Y, Sp.At.Z + RDPortWaterZ - 45.f), Sp.Yaw, 1.f, true); break;
	case TS_Boat: AddPieceAt(TEXT("Port.Boat"), FVector(Sp.At.X, Sp.At.Y, Sp.At.Z + RDPortWaterZ - 15.f), Sp.Yaw, 1.f, true); break;
	case TS_Wreck: AddPiece(TEXT("Port.Wreck"), FTransform(FRotator(R.FRandRange(-8.f, 8.f), Sp.Yaw, R.FRandRange(10.f, 22.f)), FVector(Sp.At.X, Sp.At.Y, Sp.At.Z + RDPortWaterZ - 120.f)), true); break;
	case TS_Body: AddPieceAt(R.RandBool() ? FName(TEXT("Port.Body")) : FName(TEXT("Port.Body2")), Sp.At, Sp.Yaw, 1.f, true); break;
	case TS_Gibbet: AddPieceAt(TEXT("Port.Gibbet"), Sp.At, Sp.Yaw); break;
	case TS_DockProps:
	{
		// (a fish rack, nets over a crate, crab cages, a barrel: in a row along the quay)
		const FVector Al = Ro.RotateVector(FVector(0, 1, 0));
		AddPieceAt(TEXT("Port.FishRack"), Sp.At, Sp.Yaw);
		// (its fish and its rope: meshes of their own on the frame's origin)
		AddPieceAt(TEXT("Port.FishRack2"), Sp.At, Sp.Yaw, 1.f, true);
		AddPieceAt(TEXT("Port.FishRack3"), Sp.At, Sp.Yaw, 1.f, true);
		AddPieceAt(TEXT("Port.Net"), Sp.At + Al * 260.f, Sp.Yaw + R.FRandRange(-20.f, 20.f), 1.f, true);
		AddPieceAt(TEXT("Port.Cages"), Sp.At - Al * 250.f, Sp.Yaw + R.FRandRange(-30.f, 30.f));
		AddPieceAt(TEXT("Port.Barrel"), Sp.At + Al * 420.f, R.FRandRange(0.f, 360.f));
		break;
	}
	default: break;
	}
}

void ARDSection::SewerGateBuild(int32 BI)
{
	// (the sluice house's far wall: the sewer's round iron gate standing 45 cm out of it, a dim green-grey light, the drip of
	// water. The Sewer pack's mud before it read as a pale disc on the floor (884 gm1, gm2): left out)
	if (MistgateAt.IsZero()) return;
	FurnRoom = CastleHallRoom;
	AddPieceAt(TEXT("Port.SewerArch"), MistgateAt + MistgateNormal * 45.f, MistgateNormal.Rotation().Yaw, 1.f, true);
	// (at 160 cd 2.2 m before it the outfall's pale concrete glowed white (884 gm1's picture): dim, higher, further out)
	AddLight(MistgateAt + MistgateNormal * 380.f + FVector(0, 0, 330.f), FLinearColor(0.45f, 0.62f, 0.52f), 35.f, 900.f, false, 0.05f);
	AddEffect(TEXT("SewerDrip"), MistgateAt + MistgateNormal * 120.f + FVector(0, 0, 320.f), 1.f);
	FurnRoom = -1;
	UE_LOG(LogRDPort, Log, TEXT("RDPORT the sewer gate at (%.0f, %.0f)"), MistgateAt.X, MistgateAt.Y);
}
