// AIVSection: what stands where (plan), the house shells and their doors.
#include "IV/IVSection.h"
#include "IV/IVVillageGenerator.h"
#include "Components/InstancedStaticMeshComponent.h"
#include "Components/PointLightComponent.h"
#include "Components/StaticMeshComponent.h"
#include "Engine/StaticMesh.h"

FName AIVSection::StyleName(EIVStyle S)
{
	switch (S)
	{
	case EIVStyle::Thatch: return TEXT("Thatch");
	case EIVStyle::Stone: return TEXT("Stone");
	default: return TEXT("Timber");
	}
}

FName AIVSection::KitPiece(const FBld& B, const TCHAR* Part) const
{
	return FName(*FString::Printf(TEXT("%s_%s"), *StyleName(B.Style).ToString(), Part));
}

// ------------------------------------------------------------------------------------------------ plan
void AIVSection::Plan()
{
	Blds.Reset(); Vacant.Reset(); Foreign.Reset(); Patches.Reset(); MapTrees.Reset(); MapProps.Reset(); KeepClear.Reset();
	const float SS = Generator->SectionSize;
	const FVector2D Mn = GetSectionMin(), Mx = Mn + FVector2D(SS);
	const FVector2D Cl(FMath::Clamp(0.f, (float)Mn.X, (float)Mx.X), FMath::Clamp(0.f, (float)Mn.Y, (float)Mx.Y));
	const float Rmin = Cl.Size();
	float Rmax = 0.f;
	for (const FVector2D& Cn : { Mn, FVector2D(Mx.X, Mn.Y), FVector2D(Mn.X, Mx.Y), Mx }) Rmax = FMath::Max(Rmax, (float)Cn.Size());
	// per-section limits on the trades (the square already has one of each)
	TMap<EIVBuildingKind, int32> Used;
	auto Cap = [](EIVBuildingKind K) { return (K == EIVBuildingKind::Tavern || K == EIVBuildingKind::Smithy || K == EIVBuildingKind::Bakery || K == EIVBuildingKind::Manor) ? 1 : K == EIVBuildingKind::Store ? 2 : 1000; };
	for (int32 B = 0; ; ++B)
	{
		if (Generator->RingBase(B) - 800.f > Rmax + 1600.f) break;
		if (Generator->RingBase(B + 1) + 800.f < Rmin - 1600.f) continue;
		for (const FIVLot& L : Generator->GetLots(B))
		{
			const bool bIn = L.Center.X >= Mn.X && L.Center.Y >= Mn.Y && L.Center.X < Mx.X && L.Center.Y < Mx.Y;
			if (!bIn)
			{
				if (L.Center.X > Mn.X - 1500.f && L.Center.Y > Mn.Y - 1500.f && L.Center.X < Mx.X + 1500.f && L.Center.Y < Mx.Y + 1500.f) Foreign.Add(L);
				continue;
			}
			FRandomStream R((int32)(L.Id ^ ((uint32)Seed * 2654435761u)));
			if (L.FixedKind < 0 && R.FRand() > Generator->Density(L.Radius)) { Vacant.Add(L); continue; }
			FBld Bd; Bd.Lot = L; Bd.Seed = (uint32)R.RandHelper(0x7fffffff);
			if (L.FixedKind >= 0) Bd.Kind = (EIVBuildingKind)L.FixedKind;
			else
			{
				struct FW { EIVBuildingKind K; float W; };
				TArray<FW> Ws;
				const int32 Area = L.CellsX * L.CellsY;
				if (Area <= 4) Ws = { { EIVBuildingKind::Cottage, 62 }, { EIVBuildingKind::Storehouse, 20 }, { EIVBuildingKind::Workshop, 18 } };
				else if (Area <= 6) Ws = { { EIVBuildingKind::Cottage, 46 }, { EIVBuildingKind::Farmhouse, 16 }, { EIVBuildingKind::Bakery, 5 }, { EIVBuildingKind::Store, 7 }, { EIVBuildingKind::Workshop, 8 },
					{ EIVBuildingKind::Smithy, 5 }, { EIVBuildingKind::Storehouse, 6 }, { EIVBuildingKind::Barn, 7 } };
				else if (Area <= 8) Ws = { { EIVBuildingKind::Farmhouse, 32 }, { EIVBuildingKind::Barn, 22 }, { EIVBuildingKind::Tavern, 8 }, { EIVBuildingKind::Cottage, 20 }, { EIVBuildingKind::Store, 7 },
					{ EIVBuildingKind::Manor, 4 }, { EIVBuildingKind::Workshop, 7 } };
				else Ws = { { EIVBuildingKind::Farmhouse, 30 }, { EIVBuildingKind::Barn, 32 }, { EIVBuildingKind::Tavern, 12 }, { EIVBuildingKind::Manor, 8 }, { EIVBuildingKind::Storehouse, 18 } };
				// farther out: more farms and barns
				const float Far = FMath::Clamp((L.Radius - 9000.f) / 14000.f, 0.f, 1.f);
				float Sum = 0.f;
				for (FW& W : Ws)
				{
					if (W.K == EIVBuildingKind::Farmhouse || W.K == EIVBuildingKind::Barn) W.W *= 1.f + 1.6f * Far;
					if (Used.FindRef(W.K) >= Cap(W.K)) W.W = 0.f;
					Sum += W.W;
				}
				float U = R.FRand() * Sum; Bd.Kind = EIVBuildingKind::Cottage;
				for (const FW& W : Ws) { U -= W.W; if (U <= 0.f && W.W > 0.f) { Bd.Kind = W.K; break; } }
			}
			Used.FindOrAdd(Bd.Kind)++;
			PlanBuilding(Bd, R);
			Blds.Add(Bd);
		}
	}
}

void AIVSection::PlanBuilding(FBld& B, FRandomStream& R)
{
	const FIVLot& L = B.Lot;
	B.C = L.Center; B.Yaw = L.Yaw;
	const float Yr = FMath::DegreesToRadians(B.Yaw);
	B.Fx = FVector2D(FMath::Cos(Yr), FMath::Sin(Yr)); B.Fy = FVector2D(-FMath::Sin(Yr), FMath::Cos(Yr));
	B.Nx = L.CellsX; B.Ny = L.CellsY;
	B.FloorZ = Generator->FloorHeight;
	B.Storeys = 1; B.TowerCells = 0; B.TowerStoreys = 0; B.BackDoorCell = -1;
	// style: stone for the church, the elder's hall and the fire trades; thatch gets commoner away from the square
	const float Far = FMath::Clamp((L.Radius - 5000.f) / 14000.f, 0.f, 1.f);
	const float U = R.FRand();
	switch (B.Kind)
	{
	case EIVBuildingKind::Church: case EIVBuildingKind::Manor: case EIVBuildingKind::Smithy: B.Style = EIVStyle::Stone; break;
	case EIVBuildingKind::Tavern: case EIVBuildingKind::Bakery: B.Style = U < 0.5f ? EIVStyle::Stone : EIVStyle::Timber; break;
	case EIVBuildingKind::Store: case EIVBuildingKind::Workshop: B.Style = U < 0.75f ? EIVStyle::Timber : EIVStyle::Thatch; break;
	case EIVBuildingKind::Barn: case EIVBuildingKind::Storehouse: B.Style = U < 0.6f ? EIVStyle::Timber : EIVStyle::Thatch; break;
	default: B.Style = U < 0.34f + 0.3f * Far ? EIVStyle::Thatch : U < 0.88f ? EIVStyle::Timber : EIVStyle::Stone; break;
	}
	if (B.Kind == EIVBuildingKind::Church)
	{
		// nave two cells wide and two storeys high, the tower over its front two rows
		B.Ny = 2; B.Storeys = 2; B.bRidgeY = false; B.Span = 2;
		B.TowerCells = 2; B.TowerStoreys = 4;
		B.DoorCell = R.RandRange(0, 1);
		return;
	}
	if (B.Nx % 2 == 0 && B.Ny % 2 == 0) B.bRidgeY = B.Nx <= B.Ny; else B.bRidgeY = (B.Nx % 2 == 0);
	B.Span = B.bRidgeY ? B.Nx : B.Ny;
	B.DoorCell = B.Ny <= 2 ? R.RandRange(0, B.Ny - 1) : R.RandRange(1, B.Ny - 2);
	if ((B.Kind == EIVBuildingKind::Tavern || B.Kind == EIVBuildingKind::Barn || B.Kind == EIVBuildingKind::Manor) && B.Ny >= 3) B.BackDoorCell = R.RandRange(0, B.Ny - 1);
}

// ------------------------------------------------------------------------------------------------ shell
void AIVSection::BuildShell(int32 BI)
{
	FBld& B = Blds[BI];
	FRandomStream R((int32)(B.Seed ^ 0x13579bdfu));
	const float M = Generator->Module, WH = Generator->WallHeight;
	const FVector2D ToCam = FVector2D(Generator->ToCamera().X, Generator->ToCamera().Y).GetSafeNormal();
	const float Hx = B.Nx * M * 0.5f, Hy = B.Ny * M * 0.5f;
	// a wall piece: P = middle of the wall segment (building frame), Out = its outward direction there
	auto WallT = [&](const FVector2D& P, const FVector2D& Out, float Z)
	{
		const FVector2D Ow = B.Fx * Out.X + B.Fy * Out.Y;
		return FTransform(FRotator(0, FMath::RadiansToDegrees(FMath::Atan2(Ow.Y, Ow.X)), 0), BldPoint(B, P.X, P.Y, Z));
	};
	auto GroupOf = [&](const FVector2D& Out)
	{
		const FVector2D Ow = B.Fx * Out.X + B.Fy * Out.Y;
		return FVector2D::DotProduct(Ow, ToCam) > 0.08f ? GNear : GFar;
	};
	// ---- floor
	for (int32 I = 0; I < B.Nx; ++I)
		for (int32 J = 0; J < B.Ny; ++J)
			AddPieceAt(KitPiece(B, TEXT("Floor")), BldPoint(B, (I + 0.5f) * M - Hx, (J + 0.5f) * M - Hy, B.FloorZ), B.Yaw + 90.f * R.RandRange(0, 3));
	// ---- walls: the four sides, storey by storey
	const bool bPlain = B.Kind == EIVBuildingKind::Barn || B.Kind == EIVBuildingKind::Storehouse;
	const FName Win2 = Generator->Piece(KitPiece(B, TEXT("WallWindow2"))) ? KitPiece(B, TEXT("WallWindow2")) : KitPiece(B, TEXT("WallWindow"));
	struct FSide { FVector2D Out; int32 N; };
	const FSide Sides[4] = { { FVector2D(1, 0), B.Ny }, { FVector2D(-1, 0), B.Ny }, { FVector2D(0, 1), B.Nx }, { FVector2D(0, -1), B.Nx } };
	for (int32 S = 0; S < 4; ++S)
	{
		const FSide& Sd = Sides[S];
		const int32 G = GroupOf(Sd.Out);
		for (int32 K = 0; K < Sd.N; ++K)
		{
			const FVector2D P = S < 2 ? FVector2D(Sd.Out.X * Hx, (K + 0.5f) * M - Hy) : FVector2D((K + 0.5f) * M - Hx, Sd.Out.Y * Hy);
			for (int32 St = 0; St < B.Storeys; ++St)
			{
				const float Z = B.FloorZ + St * WH;
				const bool bDoor = St == 0 && ((S == 0 && K == B.DoorCell) || (S == 1 && K == B.BackDoorCell));
				FName Nm = KitPiece(B, TEXT("Wall"));
				if (bDoor) Nm = KitPiece(B, TEXT("Doorway"));
				else
				{
					const float Chance = B.Kind == EIVBuildingKind::Church ? (St == 1 ? 0.9f : 0.25f) : bPlain ? 0.15f : S == 0 ? 0.6f : 0.4f;
					if (R.FRand() < Chance) Nm = (B.Kind == EIVBuildingKind::Church || R.FRand() < 0.35f) ? Win2 : KitPiece(B, TEXT("WallWindow"));
				}
				// upper storeys come off with the roof (the church nave is open to it)
				AddToGroup(B, BI, St == 0 ? G : GRoof, Nm, WallT(P, Sd.Out, Z));
			}
		}
	}
	// corner posts hide the wall joints
	for (int32 Cx = -1; Cx <= 1; Cx += 2)
		for (int32 Cy = -1; Cy <= 1; Cy += 2)
			for (int32 St = 0; St < B.Storeys; ++St)
				AddToGroup(B, BI, St > 0 ? GRoof : GroupOf(FVector2D(Cx, Cy).GetSafeNormal()), KitPiece(B, TEXT("Pillar")),
					FTransform(FRotator(0, B.Yaw, 0), BldPoint(B, Cx * Hx, Cy * Hy, B.FloorZ + St * WH)));
	// ---- roof: gable roof over the cells not under the tower; ridge along A, slopes across C
	const float Top = B.FloorZ + B.Storeys * WH;
	const FVector2D A = B.bRidgeY ? FVector2D(0, 1) : FVector2D(1, 0), C = B.bRidgeY ? FVector2D(1, 0) : FVector2D(0, 1);
	const int32 NAlong = B.bRidgeY ? B.Ny : B.Nx;
	const float HAlong = NAlong * M * 0.5f, HAcross = B.Span * M * 0.5f;
	const int32 R0 = 0, R1 = NAlong - B.TowerCells;        // (the tower stands on the +X end; the church ridge runs along X)
	for (int32 Al = R0; Al < R1; ++Al)
		for (int32 Ac = 0; Ac < B.Span; ++Ac)
		{
			const bool bLow = Ac < B.Span / 2;
			const int32 Level = bLow ? Ac : B.Span - 1 - Ac;
			const FVector2D Out = C * (bLow ? -1.f : 1.f);                // toward the eave
			const FVector2D P = A * ((Al + 0.5f) * M - HAlong) + C * ((Ac + 0.5f) * M - HAcross);
			const FTransform T = WallT(P, Out, Top + Level * M);
			AddToGroup(B, BI, GRoof, KitPiece(B, TEXT("Roof")), T);
			if (Level == 0) AddToGroup(B, BI, GRoof, KitPiece(B, TEXT("RoofTrim")), T);
			// barge boards on the gable ends: the piece frame's +Y is Out turned by +90 degrees
			const FVector2D Yp(-Out.Y, Out.X);
			const float Dy = FVector2D::DotProduct(Yp, A);
			if (Al == R1 - 1 && B.TowerCells == 0) AddToGroup(B, BI, GRoof, KitPiece(B, Dy > 0.f ? TEXT("RoofEndL") : TEXT("RoofEndR")), T);
			if (Al == R0) AddToGroup(B, BI, GRoof, KitPiece(B, Dy > 0.f ? TEXT("RoofEndR") : TEXT("RoofEndL")), T);
		}
	// gable walls under the roof ends
	for (int32 End = 0; End < 2; ++End)
	{
		if (End == 1 && B.TowerCells > 0) continue;
		const FVector2D Out = A * (End == 0 ? -1.f : 1.f);
		const FVector2D Yp(-Out.Y, Out.X);                                // the gable frame's +Y in the building frame
		const FVector2D P0 = A * ((End == 0 ? R0 : R1) * M - HAlong);
		auto At = [&](float Y, float Z) { return WallT(P0 + Yp * Y, Out, Top + Z); };
		if (B.Span == 2)
		{
			AddToGroup(B, BI, GRoof, KitPiece(B, TEXT("GableNeg")), At(0, 0));
			AddToGroup(B, BI, GRoof, KitPiece(B, TEXT("GablePos")), At(0, 0));
		}
		else
		{
			for (int32 Sg = -1; Sg <= 1; Sg += 2)
			{
				AddToGroup(B, BI, GRoof, KitPiece(B, Sg > 0 ? TEXT("GablePos") : TEXT("GableNeg")), At(Sg * M, 0));
				AddToGroup(B, BI, GRoof, KitPiece(B, TEXT("Wall")), At(Sg * M * 0.5f, 0));
			}
			AddToGroup(B, BI, GRoof, KitPiece(B, TEXT("GableNeg")), At(0, M));
			AddToGroup(B, BI, GRoof, KitPiece(B, TEXT("GablePos")), At(0, M));
		}
	}
	// ---- church tower: walls above the nave on all four sides, a pyramid roof
	if (B.TowerCells > 0)
	{
		const float X0 = Hx - B.TowerCells * M, X1 = Hx;
		for (int32 St = B.Storeys; St < B.TowerStoreys; ++St)
		{
			const float Z = B.FloorZ + St * WH;
			const FName Nm = St == B.TowerStoreys - 1 ? Win2 : KitPiece(B, TEXT("Wall"));
			for (int32 K = 0; K < B.Ny; ++K)
			{
				AddToGroup(B, BI, GRoof, Nm, WallT(FVector2D(X1, (K + 0.5f) * M - Hy), FVector2D(1, 0), Z));
				AddToGroup(B, BI, GRoof, Nm, WallT(FVector2D(X0, (K + 0.5f) * M - Hy), FVector2D(-1, 0), Z));
			}
			for (int32 K = 0; K < B.TowerCells; ++K)
			{
				AddToGroup(B, BI, GRoof, Nm, WallT(FVector2D(X0 + (K + 0.5f) * M, Hy), FVector2D(0, 1), Z));
				AddToGroup(B, BI, GRoof, Nm, WallT(FVector2D(X0 + (K + 0.5f) * M, -Hy), FVector2D(0, -1), Z));
			}
			for (int32 Cx = 0; Cx <= 1; ++Cx)
				for (int32 Cy = -1; Cy <= 1; Cy += 2)
					AddToGroup(B, BI, GRoof, KitPiece(B, TEXT("Pillar")), FTransform(FRotator(0, B.Yaw, 0), BldPoint(B, Cx ? X1 : X0, Cy * Hy, Z)));
		}
		// four corner pieces make the spire (piece frame: the corner of the eaves at +X +Y)
		const float Zt = B.FloorZ + B.TowerStoreys * WH;
		const FVector2D Tc((X0 + X1) * 0.5f, 0.f);
		for (int32 Q = 0; Q < 4; ++Q)
		{
			const FVector2D D = Q == 0 ? FVector2D(1, 1) : Q == 1 ? FVector2D(-1, 1) : Q == 2 ? FVector2D(-1, -1) : FVector2D(1, -1);
			AddToGroup(B, BI, GRoof, KitPiece(B, TEXT("CornerOut")),
				FTransform(FRotator(0, B.Yaw + 90.f * Q, 0), BldPoint(B, Tc.X + D.X * M * 0.5f, Tc.Y + D.Y * M * 0.5f, Zt)));
		}
	}
	// ---- a light for the cut-away view (off until she is inside), lifted above head height
	if (UPointLightComponent* Lt = AddLight(BldPoint(B, 0, 0, B.FloorZ + 270.f), FLinearColor(1.f, 0.90f, 0.76f), 55.f + 5.f * B.Nx * B.Ny, FMath::Max(Hx, Hy) * 2.f + 500.f, 0.f,
		FName(*FString::Printf(TEXT("IVF_%d"), BI))))
	{
		Lt->SetVisibility(false);
		B.FillLights.Add(Lt);
	}
}

void AIVSection::AddDoorsFor(int32 BI)
{
	FBld& B = Blds[BI];
	const float M = Generator->Module;
	const float Hx = B.Nx * M * 0.5f, Hy = B.Ny * M * 0.5f;
	const FVector2D ToCam = FVector2D(Generator->ToCamera().X, Generator->ToCamera().Y).GetSafeNormal();
	for (int32 Which = 0; Which < 2; ++Which)
	{
		const int32 Cell = Which == 0 ? B.DoorCell : B.BackDoorCell;
		if (Cell < 0) continue;
		const float Sx = Which == 0 ? 1.f : -1.f;
		const FVector2D Out = B.Fx * Sx;
		const FVector Mid = BldPoint(B, Sx * Hx, (Cell + 0.5f) * M - Hy, B.FloorZ);
		// nav: the doorway joins the cell outside to the cell inside
		const FVector2D Mid2(Mid.X, Mid.Y);
		Portals.Add(TPair<FIntPoint, FIntPoint>(GlobalCell(Mid2 + Out * 125.f), GlobalCell(Mid2 - Out * 95.f)));
		NavDisc(Mid2 + Out * 125.f, 55.f, 0);
		if (!bBuildInteractive) continue;
		const FIVPiece* P = Generator->Piece(KitPiece(B, TEXT("Door")));
		if (!P) continue;
		// doorway frame: +X outward, the hinge at P->Hinge, the closed leaf running toward -Y from it.
		// The leaf piece spans +Y from its origin: its pivot is turned half round, so pivot +X points into the house.
		const float Yaw = FMath::RadiansToDegrees(FMath::Atan2(Out.Y, Out.X));
		const FRotator Rot(0, Yaw, 0);
		const FVector HingeW = Mid + Rot.RotateVector(FVector(P->Hinge.X, P->Hinge.Y, 0)) + FVector(0, 0, P->Hinge.Z);
		USceneComponent* Pv = AddPivot(RootComponent, FTransform(FRotator(0, Yaw + 180.f, 0), HingeW - GetActorLocation()));
		UStaticMeshComponent* Leaf = AddMesh(Pv, P->Mesh, P->Adjust, true);
		FMover Mv; Mv.Pivot = Pv; Mv.Parts = { Leaf }; Mv.Closed = Pv->GetRelativeRotation().Quaternion(); Mv.bDoor = true;
		Mv.Kind = B.Kind == EIVBuildingKind::Church ? TEXT("church door") : TEXT("door");
		Mv.LeafSign = 1.f;
		Mv.Center = Mid + FVector(0, 0, 100);
		Mv.Normal = FVector(-Out.X, -Out.Y, 0.f);
		Mv.Building = BI;
		Mv.Group = FVector2D::DotProduct(Out, ToCam) > 0.08f ? GNear : GFar;
		const int32 DI = Doors.Add(Mv);
		if (Which == 0) B.DoorIndex = DI; else B.BackDoorIndex = DI;
	}
}
