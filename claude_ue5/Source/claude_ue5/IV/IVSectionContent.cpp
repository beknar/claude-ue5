// AIVSection: furniture by building purpose, yards and gardens, the market square, the churchyard, trees and verges.
#include "IV/IVSection.h"
#include "IV/IVVillageGenerator.h"
#include "Components/PointLightComponent.h"

// ------------------------------------------------------------------------------------------------ indoor placement
FVector2D AIVSection::InnerHalf(const FBld& B) const
{
	const float M = Generator->Module, In = B.Style == EIVStyle::Stone ? 36.f : 26.f;
	return FVector2D(B.Nx * M * 0.5f - In, B.Ny * M * 0.5f - In);
}

static FString ContainerKind(FName Name)
{
	FString S = Name.ToString().ToLower();
	while (S.Len() > 0 && FChar::IsDigit(S[S.Len() - 1])) S.LeftChopInline(1);
	return S;
}

bool AIVSection::Place(FBld& B, FName Name, const FVector2D& Local, float LocalYaw, bool bContainer, float Clear, bool bBlocks, float Z, int32 WallGroup)
{
	const FIVPiece* P = Generator->Piece(Name);
	if (!P) return false;
	const float Yr = FMath::DegreesToRadians(LocalYaw);
	const float Cs = FMath::Abs(FMath::Cos(Yr)), Sn = FMath::Abs(FMath::Sin(Yr));
	const FVector2D H(0.5f * (P->Size.X * Cs + P->Size.Y * Sn), 0.5f * (P->Size.X * Sn + P->Size.Y * Cs));
	const FVector2D In = InnerHalf(B);
	if (FMath::Abs(Local.X) + H.X > In.X + 1.f || FMath::Abs(Local.Y) + H.Y > In.Y + 1.f) return false;
	const FBox2D Bx(Local - H, Local + H);
	if (bBlocks) for (const FBox2D& U : B.Used) if (U.ExpandBy(Clear).Intersect(Bx)) return false;
	const FVector W = BldPoint(B, Local.X, Local.Y, B.FloorZ + Z);
	const float Yaw = B.Yaw + LocalYaw;
	const bool bOpens = bContainer && P->Moving;
	FVector Stand = W;
	if (bBlocks && (P->bCollision || bOpens))
	{
		// it takes floor away from her: mark it, and keep it only if the door still leads to every container of the
		// house (and to the front of this one)
		const float Wy = FMath::DegreesToRadians(Yaw);
		const FVector2D Fx(FMath::Cos(Wy), FMath::Sin(Wy)), Fy(-Fx.Y, Fx.X), C(W.X, W.Y), Hs = FVector2D(P->Size.X, P->Size.Y) * 0.5f;
		const float Ext = Hs.Size() + 90.f;
		const FIntPoint I0 = NavIndex(C - FVector2D(Ext)), I1 = NavIndex(C + FVector2D(Ext));
		TArray<uint8> Saved;
		for (int32 Y = I0.Y; Y <= I1.Y; ++Y) for (int32 X = I0.X; X <= I1.X; ++X) Saved.Add((X >= 0 && Y >= 0 && X < NavN && Y < NavN) ? Nav[Y * NavN + X] : 0);
		NavBox(C, Fx, Fy, Hs, 1, 30.f);
		Stand = W + FVector(Fx, 0.f) * (P->Size.X * 0.5f + 62.f);
		if (!InteriorOk(B, bOpens ? &Stand : nullptr))
		{
			int32 K = 0;
			for (int32 Y = I0.Y; Y <= I1.Y; ++Y) for (int32 X = I0.X; X <= I1.X; ++X, ++K) if (X >= 0 && Y >= 0 && X < NavN && Y < NavN) Nav[Y * NavN + X] = Saved[K];
			return false;
		}
	}
	if (bOpens)
	{
		// she stands on the floor cell InteriorOk found in front of it
		const int32 CI = AddContainer(Name, W, Yaw, ContainerKind(Name));
		if (Containers.IsValidIndex(CI))
		{
			Containers[CI].Stand = Stand; Containers[CI].Group = WallGroup;
			if (Containers.IsValidIndex(Containers[CI].Partner)) { Containers[Containers[CI].Partner].Stand = Stand; Containers[Containers[CI].Partner].Group = WallGroup; }
		}
	}
	// (a tall piece against a wall comes off with that wall: seen from behind it would hide the room)
	else if (WallGroup >= 0 && CurBld >= 0 && P->Mesh && !P->ActorClass && !P->bHidden) AddToGroup(B, CurBld, WallGroup, Name, FTransform(FRotator(0, Yaw, 0), W));
	else AddPieceAt(Name, W, Yaw);
	if (bBlocks) B.Used.Add(Bx);
	LastLocal = Local; LastYaw = LocalYaw;
	return true;
}

bool AIVSection::InteriorOk(const FBld& B, FVector* ExtraStand) const
{
	// flood the house floor (nav value 2) from just inside the front door
	const float M = Generator->Module;
	const float Hx = B.Nx * M * 0.5f, Hy = B.Ny * M * 0.5f, Ext = FMath::Sqrt(Hx * Hx + Hy * Hy) + 60.f;
	const FIntPoint I0 = NavIndex(B.C - FVector2D(Ext)), I1 = NavIndex(B.C + FVector2D(Ext));
	const int32 Wd = I1.X - I0.X + 1, Ht = I1.Y - I0.Y + 1;
	if (Wd <= 0 || Ht <= 0) return true;
	TArray<uint8> Seen; Seen.Init(0, Wd * Ht);
	auto Floor = [&](const FIntPoint& I) { return I.X >= I0.X && I.Y >= I0.Y && I.X <= I1.X && I.Y <= I1.Y && I.X >= 0 && I.Y >= 0 && I.X < NavN && I.Y < NavN && Nav[I.Y * NavN + I.X] == 2; };
	auto Mark = [&](const FIntPoint& I) -> uint8& { return Seen[(I.Y - I0.Y) * Wd + (I.X - I0.X)]; };
	const FVector In = BldPoint(B, Hx - 95.f, (B.DoorCell + 0.5f) * M - Hy);
	const FIntPoint S = NavIndex(FVector2D(In.X, In.Y));
	if (!Floor(S)) return false;
	TArray<FIntPoint> Q; Q.Reserve(Wd * Ht);
	Q.Add(S); Mark(S) = 1;
	static const FIntPoint D4[4] = { FIntPoint(1, 0), FIntPoint(-1, 0), FIntPoint(0, 1), FIntPoint(0, -1) };
	for (int32 H = 0; H < Q.Num(); ++H)
		for (int32 K = 0; K < 4; ++K)
		{
			const FIntPoint N = Q[H] + D4[K];
			if (Floor(N) && !Mark(N)) { Mark(N) = 1; Q.Add(N); }
		}
	auto Reached = [&](const FVector& P) { const FIntPoint C = NavIndex(FVector2D(P.X, P.Y)); return Floor(C) && Mark(C) != 0; };
	if (ExtraStand)
	{
		// the new container: the reached floor cell nearest the spot in front of it becomes where she stands
		const FVector2D Mn = GetSectionMin() - FVector2D(NavMargin);
		const FIntPoint C = NavIndex(FVector2D(ExtraStand->X, ExtraStand->Y));
		float BestD = 1e9f; FVector2D BestP = FVector2D::ZeroVector;
		for (int32 Dx = -1; Dx <= 1; ++Dx)
			for (int32 Dy = -1; Dy <= 1; ++Dy)
			{
				const FIntPoint N = C + FIntPoint(Dx, Dy);
				if (!Floor(N) || !Mark(N)) continue;
				const FVector2D P = Mn + FVector2D((N.X + 0.5f) * NavCell, (N.Y + 0.5f) * NavCell);
				const float D = FVector2D::DistSquared(P, FVector2D(ExtraStand->X, ExtraStand->Y));
				if (D < BestD) { BestD = D; BestP = P; }
			}
		if (BestD > 1e8f) return false;
		ExtraStand->X = BestP.X; ExtraStand->Y = BestP.Y;
	}
	for (const FMover& Mv : Containers) if (Mv.Building == CurBld && CurBld >= 0 && !Reached(Mv.Stand)) return false;
	// the back door too
	if (B.BackDoorCell >= 0 && !Reached(BldPoint(B, -Hx + 95.f, (B.BackDoorCell + 0.5f) * M - Hy))) return false;
	return true;
}

bool AIVSection::PlaceWall(FBld& B, FName Name, int32 Side, float U, bool bContainer, float Gap)
{
	const FIVPiece* P = Generator->Piece(Name);
	if (!P) return false;
	const FVector2D In = InnerHalf(B);
	const float Dp = P->Size.X * 0.5f + Gap, Wd = P->Size.Y * 0.5f + 4.f;
	FVector2D L; float Yaw;
	switch (Side)
	{
	case 0: L = FVector2D(-In.X + Dp, FMath::Lerp(-In.Y + Wd, In.Y - Wd, U)); Yaw = 0.f; break;
	case 1: L = FVector2D(In.X - Dp, FMath::Lerp(-In.Y + Wd, In.Y - Wd, U)); Yaw = 180.f; break;
	case 2: L = FVector2D(FMath::Lerp(-In.X + Wd, In.X - Wd, U), -In.Y + Dp); Yaw = 90.f; break;
	default: L = FVector2D(FMath::Lerp(-In.X + Wd, In.X - Wd, U), In.Y - Dp); Yaw = -90.f; break;
	}
	// side -> wall group (+X, -X, +Y, -Y)
	static const int32 Wall[4] = { GWall + 1, GWall + 0, GWall + 3, GWall + 2 };
	return Place(B, Name, L, Yaw, bContainer, 8.f, true, 0.f, (bWallHide && P->Size.Z > 140.f) ? Wall[FMath::Clamp(Side, 0, 3)] : -1);
}

int32 AIVSection::PlaceAnyWall(FBld& B, FRandomStream& R, FName Name, bool bContainer, int32 PreferSide)
{
	const FIVPiece* P = Generator->Piece(Name);
	if (!P) return -1;
	int32 Order[4] = { 0, 2, 3, 1 };
	for (int32 I = 3; I > 0; --I) Swap(Order[I], Order[R.RandRange(0, I)]);
	if (PreferSide >= 0) for (int32 I = 0; I < 4; ++I) if (Order[I] == PreferSide) { Swap(Order[0], Order[I]); break; }
	// tall pieces stand against the walls away from the camera of the view the level starts with: against a cut-away
	// wall they would show their backs and hide the room behind them (turned to another view, they come off with
	// their wall)
	const bool bTall = P->Size.Z > 140.f;
	const FVector2D ToCam = FVector2D(Generator->ToCameraDefault().X, Generator->ToCameraDefault().Y).GetSafeNormal();
	auto Near = [&](int32 Side)
	{
		const FVector2D N = Side == 0 ? -B.Fx : Side == 1 ? B.Fx : Side == 2 ? -B.Fy : B.Fy;
		return FVector2D::DotProduct(N, ToCam) > 0.08f;
	};
	static const float Us[9] = { 0.f, 1.f, 0.5f, 0.25f, 0.75f, 0.12f, 0.88f, 0.37f, 0.63f };
	const int32 Off = R.RandRange(0, 8);
	for (int32 Pass = 0; Pass < 2; ++Pass)
		for (int32 S = 0; S < 4; ++S)
		{
			// first the walls away from the camera, then (low pieces only) the others
			if (Near(Order[S]) != (Pass == 1) || (Pass == 1 && bTall)) continue;
			for (int32 K = 0; K < 9; ++K)
				if (PlaceWall(B, Name, Order[S], Us[(K + Off) % 9], bContainer)) return Order[S];
		}
	return -1;
}

bool AIVSection::PlaceFree(FBld& B, FRandomStream& R, FName Name, bool bContainer, int32 Tries)
{
	const FIVPiece* P = Generator->Piece(Name);
	if (!P) return false;
	const FVector2D In = InnerHalf(B);
	for (int32 T = 0; T < Tries; ++T)
	{
		const float Yaw = 90.f * R.RandRange(0, 3);
		const bool bTurn = FMath::Abs(FMath::Sin(FMath::DegreesToRadians(Yaw))) > 0.5f;
		const FVector2D H = (bTurn ? FVector2D(P->Size.Y, P->Size.X) : FVector2D(P->Size.X, P->Size.Y)) * 0.5f;
		const float Rx = In.X - H.X - 60.f, Ry = In.Y - H.Y - 60.f;
		if (Rx < 0.f || Ry < 0.f) continue;
		if (Place(B, Name, FVector2D(R.FRandRange(-Rx, Rx), R.FRandRange(-Ry, Ry)), Yaw, bContainer, 52.f, true)) return true;
	}
	return false;
}

void AIVSection::PlaceOn(FBld& B, FName Name, const FVector2D& Local, float Z, float LocalYaw, float Scale)
{
	AddPieceAt(Name, BldPoint(B, Local.X, Local.Y, B.FloorZ + Z), B.Yaw + LocalYaw, Scale, true);
}

// ------------------------------------------------------------------------------------------------ furnishing
void AIVSection::Furnish(int32 BI)
{
	FBld& B = Blds[BI];
	FRandomStream R((int32)(B.Seed ^ 0x2468ace1u));
	const float M = Generator->Module;
	const float Hx = B.Nx * M * 0.5f, Hy = B.Ny * M * 0.5f;
	const FVector2D In = InnerHalf(B);
	B.Used.Reset();
	// the doorways stay clear
	{ const float Y = (B.DoorCell + 0.5f) * M - Hy; B.Used.Add(FBox2D(FVector2D(Hx - 215.f, Y - 85.f), FVector2D(Hx, Y + 85.f))); }
	if (B.BackDoorCell >= 0) { const float Y = (B.BackDoorCell + 0.5f) * M - Hy; B.Used.Add(FBox2D(FVector2D(-Hx, Y - 85.f), FVector2D(-Hx + 215.f, Y + 85.f))); }
	const FName LightTag(*FString::Printf(TEXT("IVF_%d"), BI));
	auto Dir = [](float Yaw) { const float A = FMath::DegreesToRadians(Yaw); return FVector2D(FMath::Cos(A), FMath::Sin(A)); };
	auto Wall = [&](const TCHAR* N, bool bCont = false, int32 Prefer = -1) { return PlaceAnyWall(B, R, FName(N), bCont, Prefer) >= 0; };
	auto Free = [&](const TCHAR* N, bool bCont = false) { return PlaceFree(B, R, FName(N), bCont); };
	// a fire against a wall: flames, a warm flickering light (lit while she is inside), firewood beside it
	auto Fire = [&](const TCHAR* N, int32 Prefer, float FireZ)
	{
		// (the hearth stays when its wall is cut away: the fire and its light belong to it)
		{ TGuardValue<bool> Keep(bWallHide, false); if (PlaceAnyWall(B, R, FName(N), false, Prefer) < 0) return false; }
		const FVector2D F = Dir(LastYaw), L = LastLocal;
		const FIVPiece* P = Generator->Piece(FName(N));
		AddEffect(TEXT("HearthFire"), BldPoint(B, L.X, L.Y, B.FloorZ + FireZ), 0.8f);
		if (UPointLightComponent* Lt = AddLight(BldPoint(B, L.X + F.X * (P->Size.X * 0.5f + 55.f), L.Y + F.Y * (P->Size.X * 0.5f + 55.f), B.FloorZ + 95.f), FLinearColor(1.f, 0.56f, 0.24f), 260.f, 620.f, 0.2f, LightTag))
		{
			Lt->SetVisibility(false);
			B.FillLights.Add(Lt);
		}
		return true;
	};
	// a table somewhere in the room with seats along its two long sides and a few things on it
	auto TableSet = [&](const TCHAR* T, const TCHAR* Seat, int32 Seats, const TArray<FName>& Tops)
	{
		if (!PlaceFree(B, R, FName(T))) return false;
		const FVector2D C = LastLocal; const float Yaw = LastYaw;
		const FIVPiece* P = Generator->Piece(FName(T));
		const FIVPiece* S = Generator->Piece(FName(Seat));
		const FVector2D Fx = Dir(Yaw), Fy(-Fx.Y, Fx.X);
		if (S)
		{
			// the long side of the table takes the seats
			const bool bLongY = P->Size.Y >= P->Size.X;
			const float Across = (bLongY ? P->Size.X : P->Size.Y) * 0.5f + S->Size.X * 0.5f + 12.f;
			const float Len = (bLongY ? P->Size.Y : P->Size.X) - 30.f;
			const int32 PerSide = FMath::Max(1, (Seats + 1) / 2);
			for (int32 I = 0; I < Seats; ++I)
			{
				const float Sd = (I % 2) ? 1.f : -1.f;
				const float Along = PerSide > 1 ? FMath::Lerp(-Len * 0.5f + S->Size.Y * 0.5f, Len * 0.5f - S->Size.Y * 0.5f, (I / 2) / (float)(PerSide - 1)) : 0.f;
				const FVector2D Off = bLongY ? Fx * (Sd * Across) + Fy * Along : Fy * (Sd * Across) + Fx * Along;
				// seats face the table
				const float SeatYaw = Yaw + (bLongY ? (Sd > 0.f ? 180.f : 0.f) : (Sd > 0.f ? -90.f : 90.f));
				Place(B, FName(Seat), C + Off, SeatYaw, false, 1.f, true);
			}
		}
		for (int32 I = 0; I < Tops.Num(); ++I)
		{
			const FVector2D Off = Fx * R.FRandRange(-P->Size.X * 0.28f, P->Size.X * 0.28f) + Fy * R.FRandRange(-P->Size.Y * 0.32f, P->Size.Y * 0.32f);
			PlaceOn(B, Tops[I], C + Off, P->Size.Z, Yaw + R.FRandRange(0.f, 360.f));
		}
		return true;
	};
	auto Rug = [&](const TCHAR* N) { if (const FIVPiece* P = Generator->Piece(FName(N))) Place(B, FName(N), FVector2D(R.FRandRange(-In.X * 0.3f, In.X * 0.3f), R.FRandRange(-In.Y * 0.3f, In.Y * 0.3f)), 90.f * R.RandRange(0, 3), false, 0.f, false, 0.5f); };
	auto Barrels = [&](int32 N) { for (int32 I = 0; I < N; ++I) { const int32 K = R.RandRange(0, 3); Wall(K == 0 ? TEXT("Barrel") : K == 1 ? TEXT("Barrel2") : K == 2 ? TEXT("Crate") : TEXT("Crate2"), true); } };
	const TArray<FName> Meal = { TEXT("Bread"), TEXT("Tankard"), TEXT("Bowl"), TEXT("Candle") };

	switch (B.Kind)
	{
	case EIVBuildingKind::Cottage:
		Fire(TEXT("Fireplace"), 0, 35.f);
		Wall(TEXT("Bed")); Wall(TEXT("Chest"), true);
		TableSet(TEXT("TableSmall"), TEXT("Stool"), 2, { TEXT("Bowl"), TEXT("Candle") });
		if (B.Nx * B.Ny >= 6 && R.FRand() < 0.7f) Wall(TEXT("Wardrobe"), true);
		Barrels(1);
		if (B.Nx * B.Ny >= 6 && R.FRand() < 0.5f) Wall(TEXT("Shelf"));
		if (R.FRand() < 0.5f) Wall(TEXT("Bucket"));
		Rug(R.RandBool() ? TEXT("Rug") : TEXT("Rug2"));
		break;
	case EIVBuildingKind::Farmhouse:
		Fire(TEXT("Fireplace"), 0, 35.f);
		Wall(TEXT("Bed")); Wall(TEXT("Bed")); Wall(TEXT("Chest"), true); Wall(TEXT("Trunk"), true);
		TableSet(TEXT("TableLong"), TEXT("Bench"), 2, Meal);
		Wall(TEXT("Wardrobe"), true); Barrels(2);
		Wall(TEXT("Shelf")); Wall(TEXT("Sack")); Wall(TEXT("Sack2"));
		if (R.FRand() < 0.4f) Wall(TEXT("Crib"));
		Rug(TEXT("Rug"));
		break;
	case EIVBuildingKind::Tavern:
	{
		Fire(TEXT("Fireplace"), 0, 35.f);
		// the bar: a counter a step out from a side wall, kegs and a shelf behind it
		const int32 Side = R.RandBool() ? 2 : 3;
		Wall(TEXT("Keg"), false, Side); Wall(TEXT("Keg"), false, Side); Wall(TEXT("Shelf"), false, Side);
		if (const FIVPiece* P = Generator->Piece(TEXT("Counter")))
			for (float U : { 0.3f, 0.6f }) if (PlaceWall(B, TEXT("Counter"), Side, U, false, 135.f)) PlaceOn(B, TEXT("Tankard"), LastLocal, P->Size.Z, R.FRandRange(0, 360));
		const int32 Sets = FMath::Clamp(B.Nx * B.Ny / 3, 2, 5);
		for (int32 I = 0; I < Sets; ++I)
			if (I % 2 == 0) TableSet(TEXT("TableLong"), TEXT("Bench"), 2, Meal); else TableSet(TEXT("TableRound"), TEXT("Stool"), 4, { TEXT("Tankard"), TEXT("Tankard"), TEXT("Candle") });
		Barrels(3); Wall(TEXT("Chest"), true);
		if (B.Nx * B.Ny >= 8) { Wall(TEXT("Bed")); Wall(TEXT("Trunk"), true); }
		break;
	}
	case EIVBuildingKind::Smithy:
		if (Fire(TEXT("Forge"), 0, 95.f))
		{
			const FVector2D F = Dir(LastYaw), L = LastLocal;
			Place(B, TEXT("Anvil"), L + F * 150.f, LastYaw + 90.f, false, 6.f, true);
		}
		Free(TEXT("QuenchTub")); Wall(TEXT("ToolBoard")); Wall(TEXT("WeaponStand"));
		if (Wall(TEXT("PrepTable"))) { if (const FIVPiece* P = Generator->Piece(TEXT("PrepTable"))) PlaceOn(B, TEXT("Hammer"), LastLocal, P->Size.Z, R.FRandRange(0, 360)); }
		Wall(TEXT("Coal")); Wall(TEXT("Chest"), true); Barrels(2); Wall(TEXT("Stool"));
		break;
	case EIVBuildingKind::Bakery:
		Fire(TEXT("BreadOven"), 0, 60.f);
		for (int32 I = 0; I < 2; ++I)
			if (Wall(TEXT("PrepTable"))) if (const FIVPiece* P = Generator->Piece(TEXT("PrepTable")))
			{
				const FVector2D C = LastLocal, Fy = FVector2D(-Dir(LastYaw).Y, Dir(LastYaw).X);
				PlaceOn(B, TEXT("Bread"), C + Fy * 35.f, P->Size.Z, R.FRandRange(0, 360)); PlaceOn(B, TEXT("Bread2"), C - Fy * 35.f, P->Size.Z, R.FRandRange(0, 360));
			}
		Wall(TEXT("Shelf")); Wall(TEXT("Shelf")); Wall(TEXT("Sack")); Wall(TEXT("Sack2")); Wall(TEXT("Sack"));
		Barrels(2); Wall(TEXT("Firewood"));
		TableSet(TEXT("TableSmall"), TEXT("Stool"), 1, { TEXT("Bread"), TEXT("Cheese") });
		break;
	case EIVBuildingKind::Store:
	{
		Wall(TEXT("Shelf")); Wall(TEXT("Shelf")); Wall(TEXT("Shelf"));
		Wall(TEXT("FoodStand")); Wall(TEXT("FoodStand2")); Wall(TEXT("FoodStand3"));
		if (const FIVPiece* P = Generator->Piece(TEXT("Counter")))
			if (PlaceFree(B, R, TEXT("Counter"))) { PlaceOn(B, TEXT("Balance"), LastLocal, P->Size.Z, LastYaw); }
		Wall(TEXT("Sack")); Wall(TEXT("Sack2")); Barrels(3); Wall(TEXT("Chest"), true);
		break;
	}
	case EIVBuildingKind::Workshop:
		if (Wall(TEXT("PrepTable"))) { if (const FIVPiece* P = Generator->Piece(TEXT("PrepTable"))) PlaceOn(B, TEXT("Hammer"), LastLocal, P->Size.Z, R.FRandRange(0, 360)); }
		Wall(TEXT("ToolBoard")); Wall(TEXT("Planks")); Wall(TEXT("Ladder"));
		Free(TEXT("Logs")); Free(TEXT("TableSmall")); Wall(TEXT("Stool")); Wall(TEXT("Chest"), true); Barrels(2);
		break;
	case EIVBuildingKind::Barn:
		Wall(TEXT("HayPile")); Wall(TEXT("HayPile")); Wall(TEXT("HayPile"));
		Wall(TEXT("HayBale")); Wall(TEXT("HayBale")); Free(TEXT("HayBale"));
		Wall(TEXT("Trough")); Wall(TEXT("StallPartition")); Wall(TEXT("StallPartition"));
		Wall(TEXT("Pitchfork")); Wall(TEXT("Sack")); Wall(TEXT("Sack2")); Barrels(2);
		if (B.Nx * B.Ny >= 8) Free(TEXT("Cart"));
		break;
	case EIVBuildingKind::Storehouse:
		Barrels(4 + B.Nx * B.Ny / 2);
		Wall(TEXT("Shelf")); Wall(TEXT("Sack")); Wall(TEXT("Sack2")); Wall(TEXT("Sack")); Wall(TEXT("Ladder"));
		Wall(TEXT("Chest"), true);
		break;
	case EIVBuildingKind::Church:
	{
		// altar on the back wall, candelabra beside it, pews either side of the aisle; the tower base stays open
		if (PlaceWall(B, TEXT("Altar"), 0, 0.5f, false, 40.f)) { if (const FIVPiece* P = Generator->Piece(TEXT("Altar"))) PlaceOn(B, TEXT("Candle"), LastLocal, P->Size.Z, 0.f); }
		PlaceWall(B, TEXT("Candelabrum"), 0, 0.08f); PlaceWall(B, TEXT("Candelabrum"), 0, 0.92f);
		if (UPointLightComponent* Lt = AddLight(BldPoint(B, -In.X + 150.f, 0, B.FloorZ + 180.f), FLinearColor(1.f, 0.72f, 0.42f), 220.f, 800.f, 0.12f, LightTag)) { Lt->SetVisibility(false); B.FillLights.Add(Lt); }
		if (const FIVPiece* P = Generator->Piece(TEXT("Pew")))
		{
			const float Aisle = 120.f;
			const bool bTwo = 2.f * P->Size.Y + Aisle <= 2.f * In.Y;
			const float X1 = Hx - B.TowerCells * M - 60.f;
			for (float X = -In.X + 330.f; X + P->Size.X * 0.5f < X1; X += P->Size.X + 75.f)
			{
				if (bTwo) { Place(B, TEXT("Pew"), FVector2D(X, -(Aisle + P->Size.Y) * 0.5f), 180.f, false, 2.f); Place(B, TEXT("Pew"), FVector2D(X, (Aisle + P->Size.Y) * 0.5f), 180.f, false, 2.f); }
				else Place(B, TEXT("Pew"), FVector2D(X, -In.Y + P->Size.Y * 0.5f + 8.f), 180.f, false, 2.f);
			}
		}
		Wall(TEXT("Statue")); Wall(TEXT("Chest"), true, 1); Wall(TEXT("Candelabrum"), false, 1); Wall(TEXT("Bench"));
		break;
	}
	case EIVBuildingKind::Manor:
		Fire(TEXT("Fireplace"), 0, 35.f);
		if (TableSet(TEXT("TableLong"), TEXT("Chair"), 6, { TEXT("Bread"), TEXT("Cheese"), TEXT("Tankard"), TEXT("Candle"), TEXT("Bowl") })) {}
		Wall(TEXT("Throne")); Wall(TEXT("Bookshelf")); Wall(TEXT("Bookshelf")); Wall(TEXT("Dresser"));
		Wall(TEXT("Bed2")); Wall(TEXT("Wardrobe"), true); Wall(TEXT("Chest"), true); Wall(TEXT("Trunk"), true);
		Wall(TEXT("Candelabrum")); Wall(TEXT("ArmorStand")); Barrels(1);
		Rug(TEXT("Rug")); Rug(TEXT("Rug2"));
		break;
	}
}

// ------------------------------------------------------------------------------------------------ outdoors
bool AIVSection::IsFreeOutdoor(const FVector2D& P, float Radius) const
{
	const float SS = Generator->SectionSize, M = Generator->Module;
	const FVector2D Mn = GetSectionMin();
	if (P.X < Mn.X + Radius + 20.f || P.Y < Mn.Y + Radius + 20.f || P.X > Mn.X + SS - Radius - 20.f || P.Y > Mn.Y + SS - Radius - 20.f) return false;
	int32 Type;
	if (Generator->RoadDistance(P, Type) < Radius + 45.f) return false;
	for (int32 I = 0; I < Blds.Num(); ++I)
	{
		const FBld& B = Blds[I];
		const FVector2D L = BldLocal(B, P);
		if (FMath::Abs(L.X) < B.Nx * M * 0.5f + Radius + 60.f && FMath::Abs(L.Y) < B.Ny * M * 0.5f + Radius + 60.f) return false;
		// the way to the doors stays open
		const float Yd = (B.DoorCell + 0.5f - B.Ny * 0.5f) * M;
		if (FVector2D::Distance(L, FVector2D(B.Nx * M * 0.5f + 150.f, Yd)) < Radius + 190.f) return false;
		if (B.BackDoorCell >= 0 && FVector2D::Distance(L, FVector2D(-B.Nx * M * 0.5f - 150.f, (B.BackDoorCell + 0.5f - B.Ny * 0.5f) * M)) < Radius + 190.f) return false;
	}
	for (const FIVLot& F : Foreign)
	{
		const float Yr = FMath::DegreesToRadians(F.Yaw);
		const FVector2D Fx(FMath::Cos(Yr), FMath::Sin(Yr)), D = P - F.Center;
		const float Lx = FVector2D::DotProduct(D, Fx), Ly = FVector2D::DotProduct(D, FVector2D(-Fx.Y, Fx.X));
		if (FMath::Abs(Lx) < F.CellsX * M * 0.5f + Radius + 260.f && FMath::Abs(Ly) < F.CellsY * M * 0.5f + Radius + 80.f) return false;
	}
	if (NavAt(P) == 1) return false;
	for (const FVector2D& K : KeepClear) if (FVector2D::DistSquared(K, P) < FMath::Square(Radius + 75.f)) return false;
	const float Q = Radius * 0.75f;
	for (const FVector2D& O : { FVector2D(Q, 0), FVector2D(-Q, 0), FVector2D(0, Q), FVector2D(0, -Q) }) if (NavAt(P + O) == 1) return false;
	return true;
}

bool AIVSection::PlaceOutdoor(FName Name, const FVector2D& P, float Yaw, float Scale, bool bSolid, float Radius, bool bCheck)
{
	const FIVPiece* Pc = Generator->Piece(Name);
	if (!Pc) return false;
	const float Rad = Radius >= 0.f ? Radius : FMath::Max(Pc->Size.X, Pc->Size.Y) * 0.5f * Scale;
	if (bCheck && !IsFreeOutdoor(P, Rad)) return false;
	if (bSolid && Pc->Moving)
	{
		// a lid needs her standing in front of it: turn the container until that spot is free ground
		int32 Turn = -1;
		for (int32 K = 0; K < 4 && Turn < 0; ++K)
		{
			const float A = FMath::DegreesToRadians(Yaw + 90.f * K);
			if (NavAt(P + FVector2D(FMath::Cos(A), FMath::Sin(A)) * (Pc->Size.X * 0.5f + 62.f)) == 0) Turn = K;
		}
		if (Turn < 0) return false;
		const float A = FMath::DegreesToRadians(Yaw + 90.f * Turn);
		const int32 CI = AddContainer(Name, FVector(P, 0.f), Yaw + 90.f * Turn, ContainerKind(Name));
		KeepClear.Add(P + FVector2D(FMath::Cos(A), FMath::Sin(A)) * (Pc->Size.X * 0.5f + 62.f));
		if (Containers.IsValidIndex(CI)) Containers[CI].Building = -1;
	}
	else AddPieceAt(Name, FVector(P, 0.f), Yaw, Scale, !bSolid);
	if (bSolid) NavDisc(P, Rad + 30.f, 1);
	return true;
}

bool AIVSection::TreeAllowed(const FVector2D& P, float Height, float Radius) const
{
	// a tree hides whatever stands behind it from the camera (of the view the level starts with): none may throw that
	// "shadow" over a house
	const FVector U = Generator->ToCameraDefault();
	const FVector2D Away = -FVector2D(U.X, U.Y).GetSafeNormal();
	const float Len = Height * FVector2D(U.X, U.Y).Size() / FMath::Max((float)U.Z, 0.1f);
	const float M = Generator->Module;
	auto Hits = [&](const FVector2D& C, float Yaw, int32 Nx, int32 Ny)
	{
		const float Yr = FMath::DegreesToRadians(Yaw);
		const FVector2D Fx(FMath::Cos(Yr), FMath::Sin(Yr)), Fy(-Fx.Y, Fx.X);
		for (int32 K = 0; K <= 8; ++K)
		{
			const FVector2D D = P + Away * (Len * K / 8.f) - C;
			if (FMath::Abs(FVector2D::DotProduct(D, Fx)) < Nx * M * 0.5f + Radius && FMath::Abs(FVector2D::DotProduct(D, Fy)) < Ny * M * 0.5f + Radius) return true;
		}
		return false;
	};
	for (const FBld& B : Blds) if (FVector2D::DistSquared(B.C, P) < FMath::Square(Len + 2500.f) && Hits(B.C, B.Yaw, B.Nx, B.Ny)) return false;
	for (const FIVLot& F : Foreign) if (FVector2D::DistSquared(F.Center, P) < FMath::Square(Len + 2500.f) && Hits(F.Center, F.Yaw, F.CellsX, F.CellsY)) return false;
	return true;
}

void AIVSection::AddFence(const FVector2D& A, const FVector2D& Bp, FRandomStream& R, float GapChance)
{
	const FIVPiece* P = Generator->Piece(TEXT("Fence"));
	if (!P) return;
	const float Len = P->Size.Y, Total = FVector2D::Distance(A, Bp);
	const int32 N = FMath::FloorToInt(Total / Len);
	if (N < 1) return;
	const FVector2D D = (Bp - A).GetSafeNormal();
	const float Yaw = FMath::RadiansToDegrees(FMath::Atan2(D.Y, D.X)) - 90.f;        // the piece runs along its Y
	for (int32 I = 0; I < N; ++I)
	{
		const FVector2D C = A + D * ((I + 0.5f) * Len);
		const bool bGap = R.FRand() < GapChance;
		if (bGap || !IsFreeOutdoor(C, 45.f)) continue;
		AddPieceAt(TEXT("Fence"), FVector(C, 0.f), Yaw + (R.RandBool() ? 0.f : 180.f));
		NavBox(C, D, FVector2D(-D.Y, D.X), FVector2D(Len * 0.5f, P->Size.X * 0.5f), 1, 30.f);
	}
}

void AIVSection::BuildYard(int32 BI, FRandomStream& R)
{
	const FBld& B = Blds[BI];
	if (B.Kind == EIVBuildingKind::Church) return;
	const float M = Generator->Module;
	const float Hx = B.Nx * M * 0.5f, Hy = B.Ny * M * 0.5f;
	auto W2 = [&](float X, float Y) { const FVector V = BldPoint(B, X, Y); return FVector2D(V.X, V.Y); };
	const float Yd = (B.DoorCell + 0.5f) * M - Hy;
	// ---- by the front door: a bench, a sign for the trades, a torch post (hugging the wall, off the road)
	auto Front = [&](FName N, float X, float Y, float Yaw, bool bSolid)
	{
		const FVector2D P = W2(X, Y);
		int32 T;
		if (Generator->RoadDistance(P, T) < 70.f || NavAt(P) == 1) return false;
		return PlaceOutdoor(N, P, B.Yaw + Yaw, 1.f, bSolid, -1.f, false);
	};
	const float Side = (Yd > 0.f ? -1.f : 1.f) * (R.RandBool() || B.Ny > 2 ? 1.f : -1.f);
	if (B.Kind == EIVBuildingKind::Tavern || B.Kind == EIVBuildingKind::Smithy || B.Kind == EIVBuildingKind::Bakery || B.Kind == EIVBuildingKind::Store || B.Kind == EIVBuildingKind::Workshop)
		Front(TEXT("Sign"), Hx + 55.f, Yd + (Yd > 0.f ? -1.f : 1.f) * 115.f, 0.f, true);
	if (R.FRand() < (B.Kind == EIVBuildingKind::Cottage || B.Kind == EIVBuildingKind::Farmhouse || B.Kind == EIVBuildingKind::Tavern ? 0.45f : 0.15f))
		if (const FIVPiece* Pb = Generator->Piece(TEXT("Bench")))
		{
			const float Y = FMath::Clamp(Yd + Side * (150.f + Pb->Size.Y * 0.5f), -Hy + Pb->Size.Y * 0.5f, Hy - Pb->Size.Y * 0.5f);
			if (FMath::Abs(Y - Yd) > 110.f + Pb->Size.Y * 0.5f) Front(TEXT("Bench"), Hx + 30.f + Pb->Size.X * 0.5f, Y, 0.f, true);
		}
	if (R.FRand() < 0.3f) Front(TEXT("TorchPost"), Hx + 45.f, Yd - Side * 105.f, 0.f, true);
	// ---- the plot behind the house: as deep as the block allows
	float Depth = 0.f;
	for (float D = 100.f; D <= 1500.f; D += 100.f)
	{
		bool bOk = true;
		for (float Y : { -Hy + 60.f, 0.f, Hy - 60.f }) bOk &= IsFreeOutdoor(W2(-Hx - D, Y), 40.f) || D < 180.f;
		int32 T;
		if (Generator->RoadDistance(W2(-Hx - D, 0), T) < 330.f) bOk = false;
		if (!bOk) break;
		Depth = D;
	}
	if (Depth < 350.f) return;
	Depth = FMath::Min(Depth, 500.f + R.FRand() * 900.f);
	const float X0 = -Hx - 90.f, X1 = -Hx - Depth, Wy = Hy - 15.f;
	int32 Kind = R.RandRange(0, 4);
	if (B.Kind == EIVBuildingKind::Tavern) Kind = 5;
	else if (B.Kind == EIVBuildingKind::Barn) Kind = 2;
	else if (B.Kind == EIVBuildingKind::Smithy || B.Kind == EIVBuildingKind::Workshop) Kind = 3;
	else if (B.Kind == EIVBuildingKind::Manor) Kind = 6;
	else if (B.Kind == EIVBuildingKind::Storehouse || B.Kind == EIVBuildingKind::Store) Kind = 7;
	auto Rnd = [&](float PadX, float PadY) { return W2(R.FRandRange(X1 + PadX, X0 - PadX), R.FRandRange(-Wy + PadY, Wy - PadY)); };
	auto Soil = [&](uint8 Type) { Patches.Add({ { W2(X0, -Wy), W2(X1, -Wy), W2(X1, Wy), W2(X0, Wy) }, Type }); };
	switch (Kind)
	{
	case 0:      // kitchen garden: tilled soil, rows of plants
		Soil(2);
		for (float X = X0 - 70.f; X > X1 + 50.f; X -= 115.f)
			for (float Y = -Wy + 60.f; Y < Wy - 40.f; Y += 95.f)
				if (R.FRand() < 0.8f) PlaceOutdoor(R.FRand() < 0.25f ? TEXT("Pumpkins") : R.RandBool() ? TEXT("Plant") : TEXT("Plant2"), W2(X + R.FRandRange(-12, 12), Y + R.FRandRange(-12, 12)), R.FRandRange(0, 360), R.FRandRange(0.8f, 1.15f), false);
		break;
	case 1:      // orchard
		Soil(3);
		for (int32 I = 0; I < 4; ++I)
		{
			const FVector2D P = Rnd(150.f, 120.f);
			const FName N = R.RandBool() ? TEXT("Fruit") : TEXT("Fruit2");
			const FIVPiece* Pc = Generator->Piece(N);
			if (!Pc) continue;
			const float Sc = R.FRandRange(0.85f, 1.15f);
			if (TreeAllowed(P, Pc->Size.Z * Sc, Pc->Size.X * 0.3f * Sc) && PlaceOutdoor(N, P, R.FRandRange(0, 360), Sc, true, 45.f))
				MapTree(P, Pc->Size.X * 0.42f * Sc, Pc->Size.Z * Sc, 2);
		}
		break;
	case 2:      // hay yard
		for (int32 I = 0; I < 3; ++I) { const FVector2D P = Rnd(140.f, 140.f); if (PlaceOutdoor(TEXT("HayStack"), P, R.FRandRange(0, 360))) MapProp(P, 0.f, 3); }
		{ const FVector2D P = Rnd(180.f, 160.f); const float Yw = R.FRandRange(0, 360); if (PlaceOutdoor(TEXT("Cart"), P, Yw)) MapProp(P, Yw, 2); }
		PlaceOutdoor(TEXT("Trough"), Rnd(120.f, 120.f), B.Yaw + 90.f * R.RandRange(0, 3));
		break;
	case 3:      // wood yard
		for (int32 I = 0; I < 3; ++I) PlaceOutdoor(R.RandBool() ? TEXT("WoodPile") : TEXT("Logs"), Rnd(120.f, 120.f), B.Yaw + 90.f * R.RandRange(0, 3));
		PlaceOutdoor(TEXT("ChopBlock"), Rnd(100.f, 100.f), R.FRandRange(0, 360));
		break;
	case 4:      // washing line and a patch of flowers
		for (int32 I = 0; I < 2; ++I) PlaceOutdoor(TEXT("Laundry"), Rnd(120.f, 120.f), B.Yaw + (R.RandBool() ? 0.f : 90.f));
		for (int32 I = 0; I < 6; ++I) PlaceOutdoor(R.RandBool() ? TEXT("Flower") : TEXT("Flower2"), Rnd(60.f, 60.f), R.FRandRange(0, 360), R.FRandRange(0.8f, 1.2f), false);
		PlaceOutdoor(TEXT("Bucket"), Rnd(80.f, 80.f), R.FRandRange(0, 360));
		break;
	case 5:      // tavern yard: tables, barrels to open
		for (int32 I = 0; I < 2; ++I)
		{
			const FVector2D P = Rnd(170.f, 170.f);
			if (!PlaceOutdoor(TEXT("TableSmall"), P, B.Yaw + 90.f * R.RandRange(0, 3), 1.f, true, 95.f)) continue;
			for (int32 K = 0; K < 2; ++K) PlaceOutdoor(TEXT("Stool"), P + B.Fy * (K ? 95.f : -95.f), R.FRandRange(0, 360), 1.f, true, 28.f, false);
		}
		for (int32 I = 0; I < 3; ++I) PlaceOutdoor(R.RandBool() ? TEXT("Barrel") : TEXT("Barrel2"), Rnd(90.f, 90.f), B.Yaw + 90.f * R.RandRange(0, 3));
		break;
	case 6:      // the elder's garden: flowers, a statue, benches
		Soil(3);
		{ const FVector2D P = W2((X0 + X1) * 0.5f, 0.f); if (PlaceOutdoor(TEXT("Statue"), P, B.Yaw)) MapProp(P, B.Yaw, 4); }
		for (int32 I = 0; I < 12; ++I) PlaceOutdoor(R.RandBool() ? TEXT("Flower") : TEXT("Flower2"), Rnd(50.f, 50.f), R.FRandRange(0, 360), R.FRandRange(0.9f, 1.3f), false);
		PlaceOutdoor(TEXT("Bench"), W2(X0 - 80.f, Wy - 130.f), B.Yaw + 180.f);
		break;
	default:     // goods yard: a cart, crates and barrels to open
	{
		const FVector2D P = Rnd(180.f, 160.f); const float Yw = R.FRandRange(0, 360);
		if (PlaceOutdoor(TEXT("Cart"), P, Yw)) MapProp(P, Yw, 2);
		for (int32 I = 0; I < 3; ++I) PlaceOutdoor(R.RandBool() ? TEXT("Crate") : TEXT("Barrel"), Rnd(90.f, 90.f), B.Yaw + 90.f * R.RandRange(0, 3));
		for (int32 I = 0; I < 2; ++I) PlaceOutdoor(R.RandBool() ? TEXT("Sack") : TEXT("Sack2"), Rnd(80.f, 80.f), R.FRandRange(0, 360));
		break;
	}
	}
	// ---- fences along the sides of the plot (never closed: gaps keep every yard reachable)
	if (R.FRand() < 0.7f) AddFence(W2(X0 + 60.f, -Hy - 35.f), W2(X1, -Hy - 35.f), R, 0.22f);
	if (R.FRand() < 0.7f) AddFence(W2(X0 + 60.f, Hy + 35.f), W2(X1, Hy + 35.f), R, 0.22f);
	if (R.FRand() < 0.35f) AddFence(W2(X1 - 20.f, -Hy - 35.f), W2(X1 - 20.f, Hy + 35.f), R, 0.4f);
}

void AIVSection::BuildVacant(int32 VI, FRandomStream& R)
{
	const FIVLot& L = Vacant[VI];
	const float M = Generator->Module;
	const float Yr = FMath::DegreesToRadians(L.Yaw);
	const FVector2D Fx(FMath::Cos(Yr), FMath::Sin(Yr)), Fy(-Fx.Y, Fx.X);
	const float Hx = L.CellsX * M * 0.5f + 150.f, Hy = L.CellsY * M * 0.5f + 60.f;
	auto W2 = [&](float X, float Y) { return L.Center + Fx * X + Fy * Y; };
	auto Soil = [&](uint8 Type) { Patches.Add({ { W2(Hx, -Hy), W2(-Hx, -Hy), W2(-Hx, Hy), W2(Hx, Hy) }, Type }); };
	const float U = R.FRand();
	if (U < 0.3f)
	{
		Soil(3);     // orchard
		for (float X = -Hx + 170.f; X < Hx - 100.f; X += 380.f)
			for (float Y = -Hy + 150.f; Y < Hy - 100.f; Y += 360.f)
			{
				const FVector2D P = W2(X + R.FRandRange(-40, 40), Y + R.FRandRange(-40, 40));
				const FName N = R.RandBool() ? TEXT("Fruit") : TEXT("Fruit2");
				const FIVPiece* Pc = Generator->Piece(N);
				if (!Pc) continue;
				const float Sc = R.FRandRange(0.9f, 1.2f);
				if (TreeAllowed(P, Pc->Size.Z * Sc, Pc->Size.X * 0.3f * Sc) && PlaceOutdoor(N, P, R.FRandRange(0, 360), Sc, true, 45.f)) MapTree(P, Pc->Size.X * 0.42f * Sc, Pc->Size.Z * Sc, 2);
			}
	}
	else if (U < 0.58f)
	{
		Soil(1);     // a strip of field: stooks of hay, a scarecrow
		for (int32 I = 0; I < 5; ++I) { const FVector2D P = W2(R.FRandRange(-Hx + 120, Hx - 120), R.FRandRange(-Hy + 120, Hy - 120)); if (PlaceOutdoor(TEXT("HayBale"), P, R.FRandRange(0, 360))) MapProp(P, 0.f, 3); }
		PlaceOutdoor(TEXT("Scarecrow"), W2(0, 0), L.Yaw);
		for (int32 I = 0; I < 14; ++I) PlaceOutdoor(R.RandBool() ? TEXT("Plant") : TEXT("Plant2"), W2(R.FRandRange(-Hx + 60, Hx - 60), R.FRandRange(-Hy + 60, Hy - 60)), R.FRandRange(0, 360), 1.f, false);
	}
	else if (U < 0.8f)
	{
		Soil(3);     // a green: a well or a tree with a bench under it
		if (R.FRand() < 0.5f) { const FVector2D P = W2(0, 0); if (PlaceOutdoor(TEXT("Well"), P, L.Yaw)) { AddPieceAt(TEXT("WellRoof"), FVector(P, 0.f), L.Yaw, 1.f, true); MapProp(P, L.Yaw, 0); } }
		PlaceOutdoor(TEXT("Bench"), W2(Hx - 260.f, Hy - 150.f), L.Yaw);
		for (int32 I = 0; I < 8; ++I) PlaceOutdoor(R.RandBool() ? TEXT("Flower") : TEXT("Flower2"), W2(R.FRandRange(-Hx + 60, Hx - 60), R.FRandRange(-Hy + 60, Hy - 60)), R.FRandRange(0, 360), 1.f, false);
	}
	else
	{
		for (int32 I = 0; I < 3; ++I) { const FVector2D P = W2(R.FRandRange(-Hx + 150, Hx - 150), R.FRandRange(-Hy + 150, Hy - 150)); if (PlaceOutdoor(TEXT("HayStack"), P, R.FRandRange(0, 360))) MapProp(P, 0.f, 3); }
		const FVector2D P = W2(R.FRandRange(-Hx + 180, Hx - 180), R.FRandRange(-Hy + 150, Hy - 150)); const float Yw = R.FRandRange(0, 360);
		if (PlaceOutdoor(TEXT("Cart2"), P, Yw)) MapProp(P, Yw, 2);
	}
}

void AIVSection::BuildHub(FRandomStream& R)
{
	// the square (start section only): the market cross a few steps from the centre (the centre itself stays open:
	// she starts there), the well, a ring of stalls facing in, goods around them
	if (!Generator->IsStartSection(Coord)) return;
	auto Polar = [](float Rr, float Th) { return FVector2D(Rr * FMath::Cos(Th), Rr * FMath::Sin(Th)); };
	auto Clear = [&](const FVector2D& P, float Rad) { for (const FVector2D& O : { FVector2D(0, 0), FVector2D(Rad, 0), FVector2D(-Rad, 0), FVector2D(0, Rad), FVector2D(0, -Rad) }) if (NavAt(P + O) == 1) return false; return true; };
	auto Put = [&](FName N, const FVector2D& P, float Yaw, bool bSolid = true, float Rad = -1.f)
	{
		const FIVPiece* Pc = Generator->Piece(N);
		if (!Pc) return false;
		const float Rr = Rad >= 0.f ? Rad : FMath::Max(Pc->Size.X, Pc->Size.Y) * 0.5f;
		if (P.Size() < 330.f + Rr || !Clear(P, Rr)) return false;
		return PlaceOutdoor(N, P, Yaw, 1.f, bSolid, Rr, false);
	};
	const float A0 = 2.f * PI * R.FRand();
	{ const FVector2D P = Polar(620.f, A0); if (Put(TEXT("MarketCross"), P, FMath::RadiansToDegrees(A0) + 180.f)) MapProp(P, 0.f, 4); }
	{ const FVector2D P = Polar(980.f, A0 + PI); const float Yw = R.FRandRange(0, 360); if (Put(TEXT("Well"), P, Yw)) { AddPieceAt(TEXT("WellRoof"), FVector(P, 0.f), Yw, 1.f, true); MapProp(P, 0.f, 0); } }
	// stalls on a ring, leaving the mouths of the five streets open
	const int32 Ns = Generator->SpokeCount(0);
	const int32 Slots = 14;
	int32 Placed = 0;
	for (int32 I = 0; I < Slots; ++I)
	{
		const float Th = A0 + 2.f * PI * (I + 0.5f) / Slots;
		const float Rr = Generator->RingRadius(0, Th) - 620.f;
		bool bMouth = false;
		for (int32 S = 0; S < Ns; ++S)
		{
			float D = FMath::Fmod(FMath::Abs(Th - Generator->SpokeAngle(0, S, 0.f)), 2.f * PI); if (D > PI) D = 2.f * PI - D;
			if (D * Rr < 520.f) bMouth = true;
		}
		if (bMouth || R.FRand() < 0.25f) continue;
		const FVector2D P = Polar(Rr, Th);
		const float Yaw = FMath::RadiansToDegrees(Th) + 180.f;       // facing the middle of the square
		const FName N = FName(*FString::Printf(TEXT("Stall%d"), 1 + (Placed % 3)));
		if (!Put(N, P, Yaw, true, 190.f)) continue;
		++Placed;
		MapProp(P, Yaw, 1);
		// goods beside the stall: some to open
		const FVector2D T(-FMath::Sin(Th), FMath::Cos(Th));
		Put(R.RandBool() ? TEXT("Barrel") : TEXT("Crate"), P + T * 270.f + Polar(60.f, Th), R.FRandRange(0, 360));
		Put(R.RandBool() ? TEXT("Sack") : TEXT("Sack2"), P - T * 250.f + Polar(80.f, Th), R.FRandRange(0, 360));
		if (R.FRand() < 0.5f) Put(TEXT("FoodStand"), P - T * 265.f - Polar(40.f, Th), Yaw);
	}
	{ const float Th = A0 + 1.3f; const FVector2D P = Polar(1250.f, Th); if (Put(TEXT("Cart"), P, R.FRandRange(0, 360))) MapProp(P, 0.f, 2); }
	{ const float Th = A0 - 1.1f; Put(TEXT("NoticeBoard"), Polar(Generator->RingRadius(0, Th) - 260.f, Th), FMath::RadiansToDegrees(Th) + 180.f); }
	for (int32 I = 0; I < 3; ++I) { const float Th = A0 + 2.1f * I + 0.4f; Put(TEXT("Bench"), Polar(820.f + 200.f * R.FRand(), Th), FMath::RadiansToDegrees(Th) + 180.f); }
	for (int32 I = 0; I < 6; ++I)
	{
		const float Th = A0 + 2.f * PI * I / 6.f + 0.2f;
		const FVector2D P = Polar(Generator->RingRadius(0, Th) - 170.f, Th);
		if (Put(TEXT("TorchPost"), P, FMath::RadiansToDegrees(Th) + 180.f, true, 30.f)) AddLight(FVector(P, 250.f), FLinearColor(1.f, 0.6f, 0.3f), 60.f, 700.f, 0.2f);
	}
}

void AIVSection::BuildChurchyard(const FBld& B, FRandomStream& R)
{
	const float M = Generator->Module;
	const float Hx = B.Nx * M * 0.5f, Hy = B.Ny * M * 0.5f;
	auto W2 = [&](float X, float Y) { const FVector V = BldPoint(B, X, Y); return FVector2D(V.X, V.Y); };
	Patches.Add({ { W2(Hx + 60.f, -Hy - 950.f), W2(-Hx - 200.f, -Hy - 950.f), W2(-Hx - 200.f, Hy + 950.f), W2(Hx + 60.f, Hy + 950.f) }, 5 });
	// rows of graves either side of the nave
	for (int32 Sd = -1; Sd <= 1; Sd += 2)
		for (int32 Row = 0; Row < 3; ++Row)
			for (float X = -Hx + 120.f; X < Hx - 380.f; X += 230.f)
			{
				if (R.FRand() < 0.3f) continue;
				const FVector2D P = W2(X + R.FRandRange(-25, 25), Sd * (Hy + 250.f + Row * 220.f));
				const FName N = FName(*FString::Printf(TEXT("Grave%d"), R.RandRange(1, 5)));
				if (PlaceOutdoor(N, P, B.Yaw + R.FRandRange(-8, 8), 1.f, true, 45.f)) MapProp(P, B.Yaw, 6);
			}
	for (int32 Sd = -1; Sd <= 1; Sd += 2)
	{
		const FVector2D P = W2(-Hx - 60.f, Sd * (Hy + 520.f));
		const FIVPiece* Pc = Generator->Piece(TEXT("Conifer"));
		if (Pc && TreeAllowed(P, Pc->Size.Z, Pc->Size.X * 0.3f) && PlaceOutdoor(TEXT("Conifer"), P, R.FRandRange(0, 360), 1.f, true, 55.f)) MapTree(P, Pc->Size.X * 0.4f, Pc->Size.Z, 1);
	}
	{ const FVector2D P = W2(Hx + 150.f, -(Hy + 330.f)); if (PlaceOutdoor(TEXT("Statue"), P, B.Yaw)) MapProp(P, B.Yaw, 4); }
}

void AIVSection::ScatterNature(FRandomStream& R)
{
	const float SS = Generator->SectionSize;
	const FVector2D Mn = GetSectionMin();
	auto RandP = [&]() { return Mn + FVector2D(R.FRandRange(0.f, SS), R.FRandRange(0.f, SS)); };
	// ---- trees: in the middle of the blocks, thicker away from the square
	int32 Trees = 0;
	for (int32 T = 0; T < 520 && Trees < 110; ++T)
	{
		const FVector2D P = RandP();
		int32 Ty; const float Rd = Generator->RoadDistance(P, Ty);
		if (Rd < 520.f) continue;
		const float Open = 1.f - Generator->Density(P.Size());
		if (R.FRand() > 0.28f + 1.2f * Open) continue;
		const float U = R.FRand();
		const int32 Type = U < 0.5f ? 0 : U < 0.66f + 0.2f * Open ? 1 : 2;
		const FName N = Type == 0 ? FName(*FString::Printf(TEXT("Tree%d"), R.RandRange(1, 4))) : Type == 1 ? FName(R.RandBool() ? TEXT("Conifer") : TEXT("Conifer2")) : FName(R.RandBool() ? TEXT("Fruit") : TEXT("Fruit2"));
		const FIVPiece* Pc = Generator->Piece(N);
		if (!Pc) continue;
		const float Sc = R.FRandRange(0.8f, 1.15f);
		const float H = Pc->Size.Z * Sc, Canopy = Pc->Size.X * 0.42f * Sc;
		if (!TreeAllowed(P, H, Canopy * 0.7f)) continue;
		if (!PlaceOutdoor(N, P, R.FRandRange(0, 360), Sc, true, 55.f)) continue;
		MapTree(P, Canopy, H, (uint8)Type);
		++Trees;
	}
	// ---- bushes behind the houses and along the fences
	for (int32 T = 0; T < 260; ++T)
	{
		const FVector2D P = RandP();
		int32 Ty; if (Generator->RoadDistance(P, Ty) < 260.f) continue;
		const FName N = FName(*FString::Printf(TEXT("Bush%d"), R.RandRange(1, 3)));
		const FIVPiece* Pc = Generator->Piece(N);
		if (!Pc) continue;
		const float Sc = R.FRandRange(0.7f, 1.2f);
		if (PlaceOutdoor(N, P, R.FRandRange(0, 360), Sc, false, 60.f) && R.FRand() < 0.5f) MapTree(P, Pc->Size.X * 0.4f * Sc, Pc->Size.Z * Sc, 3);
	}
	// ---- verges: tufts of grass, flowers and stones along the roads and in the grass
	for (int32 T = 0; T < 1500; ++T)
	{
		const FVector2D P = RandP();
		int32 Ty; const float Rd = Generator->RoadDistance(P, Ty);
		if (Rd < 25.f || (Rd > 320.f && R.FRand() < 0.6f)) continue;
		const float U = R.FRand();
		const FName N = U < 0.62f ? FName(*FString::Printf(TEXT("Grass%d"), R.RandRange(1, 4))) : U < 0.88f ? FName(*FString::Printf(TEXT("Flower%d"), R.RandRange(1, 3))) : FName(*FString::Printf(TEXT("Rock%d"), R.RandRange(1, 3)));
		if (NavAt(P) == 2) continue;
		PlaceOutdoor(N, P, R.FRandRange(0, 360), R.FRandRange(0.75f, 1.25f), false, 25.f);
	}
}
