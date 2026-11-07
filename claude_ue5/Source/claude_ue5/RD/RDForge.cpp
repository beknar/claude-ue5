// Ashenreach (the user's spec of 2026-11-07, docs/ashenreach.txt): "a forge city on the edge of a burned plain, ruled by a
// forge-guild ... a city whose job is to build weapons, armor and gear. lots of industrial theming. the dungeon is located in a
// besieged factory". The city is one of the wilderness's towns (the generator's TownPlan 2, RDTownPlan.cpp's bForge: the
// foundry at the town's middle, the square before it with the guild's great anvil and open forges, the workshops, houses of
// soot-dark stone, the guild's workers and soldiers). This file builds the foundry and the square's things:
//   - its rooms (the plan's): the gatehouse between the two chimney stacks' bases, the casting hall, the furnace hall whose far
//     wall holds the iron gate down into The War Engine, a workshop wing down each side;
//   - each room's walls inward to its height (the halls 14 m, the wings 9 m, the stacks 24 m), the outer brick outward a
//     wall's thickness out with tall windows, gabled roofs of the city's stone over the halls and the wings; on each stack its
//     chimney and the smoke over it;
//   - the furnaces either side of the gate, their fire and glow; the gate itself (walked into, it opens The War Engine:
//     RDTownGame.cpp, as the holy city's stair);
//   - the siege: the barricade across the forecourt facing the foundry's door (the plan's spots, built here).
// The pieces are "Foundry.*" and "Forge.*" in the generator's table (pipeline/unreal/894 sets them); the effects
// "ChimneySmoke" and "ForgeSparks" too (with the dungeon's "BrazierFire").
#include "RD/RDSection.h"
#include "RD/RDDungeonGenerator.h"
#include "RD/RDTown.h"
#include "Engine/World.h"

DEFINE_LOG_CATEGORY_STATIC(LogRDForge, Log, All);

static const FIntPoint RDForgeDir4[4] = { FIntPoint(-1, 0), FIntPoint(1, 0), FIntPoint(0, -1), FIntPoint(0, 1) };

void ARDSection::FoundryShell(int32 BI)
{
	FTownBld& B = TownBlds[BI];
	FRandomStream R((int32)(B.Seed ^ 0x5A17F0Du));
	const float M = Generator->TileSize;
	const FName Wall(TEXT("Foundry.Wall")), WallOut(TEXT("Foundry.WallOut")), WinOut(TEXT("Foundry.WindowOut")), Floor(TEXT("Foundry.Floor")), Ceil(TEXT("Foundry.Ceil"));
	const FRDPiece* Wp = Generator->Piece(Wall);
	const FRDPiece* Op = Generator->Piece(WallOut);
	const FRDPiece* Dp = Generator->Piece(TEXT("Doorway"));
	const float T = Wp ? FMath::Clamp((float)Wp->Size.X, 20.f, 120.f) : 60.f;
	const float WZ = Wp ? FMath::Max((float)Wp->Size.Z - 2.f, 50.f) : 300.f;
	const float OZ = Op ? FMath::Max((float)Op->Size.Z - 2.f, 50.f) : WZ;
	// (the plan's rooms in order: the gatehouse, the casting hall, the furnace hall, the left and right wings, the two stacks)
	auto HeightOf = [&](int32 K) { return K <= 2 ? 1400.f : K <= 4 ? 900.f : 2400.f; };
	auto Stack = [&](FName Nm, float Step, const FVector& At, float Yaw, float Z0, float Z1)
	{
		for (float Z = Z0; Z < Z1 - 5.f; Z += Step)
			AddPiece(Nm, FTransform(FRotator(0, Yaw, 0), At + FVector(0, 0, Z), FVector(1.f, 1.f, FMath::Min(1.f, (Z1 + 2.f - Z) / (Step + 2.f)))));
	};
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
				AddPieceAt(Floor, C, 90.f * R.RandRange(0, 3));
				AddPieceAt(Ceil, C + FVector(0, 0, H), 90.f * R.RandRange(0, 1));
				for (int32 Side = 0; Side < 4; ++Side)
				{
					const FIntPoint Nb = Tl + RDForgeDir4[Side];
					const int32 On = In(Nb) ? Owner[Idx(Nb)] : -1;
					if (On == RI) continue;
					const int32 Kn = B.Rooms.IndexOfByKey(On);
					const bool bOut = Kn == INDEX_NONE;
					const bool bDoor = DoorEdges.Contains(EdgeKey(Tl, Nb));
					const FVector Edge = C + FVector(RDForgeDir4[Side].X, RDForgeDir4[Side].Y, 0) * (M * 0.5f);
					const float Yaw = InwardYaw(Side);
					const FVector OutW = FRotator(0, Yaw, 0).RotateVector(FVector(-1, 0, 0));
					const FVector At = bOut ? Edge : Edge - OutW * (T * 0.5f);
					const float Hn = bOut ? 0.f : HeightOf(Kn);
					const FVector AtOut = Edge + OutW * (bOut ? T : T * 0.5f);
					const bool bWindowCol = ((X + Y) % 3) == 0;
					auto OuterFace = [&](float Z0)
					{
						// (the outer brick: tall windows every third bay above the ground storey, plain brick below and at the top)
						for (float Z = Z0; Z < H - 5.f; Z += OZ)
						{
							const bool bWin = bWindowCol && Z >= 290.f && Z + OZ <= H - 150.f && Generator->Piece(WinOut);
							AddPiece(bWin ? WinOut : WallOut, FTransform(FRotator(0, Yaw + 180.f, 0), AtOut + FVector(0, 0, Z), FVector(1.f, 1.f, FMath::Min(1.f, (H + 2.f - Z) / (OZ + 2.f)))));
						}
					};
					if (bDoor)
					{
						AddPieceAt(TEXT("Doorway"), At, Yaw);
						Stack(Wall, WZ, At, Yaw, Dp ? Dp->Size.Z - 2.f : 300.f, H);
						if (bOut) { AddPieceAt(TEXT("Doorway"), Edge + OutW * T, Yaw + 180.f); OuterFace(Dp ? Dp->Size.Z - 2.f : 300.f); }
						else if (Hn < H) OuterFace(Hn);
						continue;
					}
					Stack(Wall, WZ, At, Yaw, 0.f, H);
					if (bOut) OuterFace(0.f);
					else if (Hn < H) OuterFace(Hn);
				}
			}
	}
	// ---- the roofs: a gable of the city's stone over the three halls together, one over each wing
	auto Bounds = [&](int32 K0, int32 K1)
	{
		FIntRect U(FIntPoint(MAX_int32, MAX_int32), FIntPoint(MIN_int32, MIN_int32));
		for (int32 K = K0; K <= K1 && K < B.Rooms.Num(); ++K) { const FRoom& Rm = Rooms[B.Rooms[K]]; U.Min = U.Min.ComponentMin(Rm.Min); U.Max = U.Max.ComponentMax(Rm.Max); }
		return U;
	};
	int32 Stacks = 0;
	if (B.Rooms.Num() >= 7)
	{
		HolyGable(Bounds(0, 2), HeightOf(0), TEXT("Forge"));
		HolyGable(Bounds(3, 3), HeightOf(3), TEXT("Forge"));
		HolyGable(Bounds(4, 4), HeightOf(4), TEXT("Forge"));
		// ---- the chimney stacks: a flat top, the chimney on it, its smoke and the furnaces' glow under it
		const FRDPiece* Cp = Generator->Piece(TEXT("Foundry.Chimney"));
		const float Ch = Cp ? (float)Cp->Size.Z : 600.f;
		for (int32 K = 5; K <= 6; ++K)
		{
			const FRoom& Rm = Rooms[B.Rooms[K]];
			const FVector Tc = (TileWorld(Rm.Min) + TileWorld(Rm.Max - FIntPoint(1, 1))) * 0.5f;
			for (int32 X = Rm.Min.X; X < Rm.Max.X; ++X) for (int32 Y = Rm.Min.Y; Y < Rm.Max.Y; ++Y) AddPieceAt(TEXT("Town.CastleRoof"), TileWorld(FIntPoint(X, Y)) + FVector(0, 0, HeightOf(K) + 40.f), 0.f, 1.f, true);
			if (AddPieceAt(TEXT("Foundry.Chimney"), Tc + FVector(0, 0, HeightOf(K) + 40.f), TownBldYaw(B), 1.f, true)) ++Stacks;
			AddEffect(TEXT("ChimneySmoke"), Tc + FVector(0, 0, HeightOf(K) + 40.f + Ch), 2.5f);
			AddLight(Tc + FVector(0, 0, HeightOf(K) + 40.f + Ch + 60.f), FLinearColor(1.f, 0.45f, 0.18f), 120.f, 1500.f, false, 0.25f);
		}
	}
	// ---- the gate down into The War Engine: its iron arch against the furnace hall's far wall (in front of the brick's face:
	// 30 cm behind it, as the cathedral's arch stands, the wall hid it: ar1's picture), a furnace either side, their fire
	AddPieceAt(TEXT("Foundry.Gate"), MistgateAt + MistgateNormal * 45.f, MistgateNormal.Rotation().Yaw, 1.f, true);
	AddLight(MistgateAt + MistgateNormal * 220.f + FVector(0, 0, 260.f), FLinearColor(1.f, 0.5f, 0.22f), 200.f, 1100.f, false, 0.15f);
	{
		const FVector Across(MistgateNormal.Y, -MistgateNormal.X, 0.f);
		const FRDPiece* Fp = Generator->Piece(TEXT("Foundry.Furnace"));
		const float Fz = Fp ? (float)Fp->Size.Z : 300.f;
		for (const float Sd : { -1.f, 1.f })
		{
			const FVector P = MistgateAt + MistgateNormal * 260.f + Across * (Sd * 650.f);
			FurnRoom = CastleHallRoom;
			if (AddPieceAt(TEXT("Foundry.Furnace"), P, MistgateNormal.Rotation().Yaw))
			{
				MarkBlocked(P, MistgateNormal.Rotation().Yaw, FVector2D(320.f, 320.f), true);
				// (the fire in the kiln's mouth, low: at a third of its height it stood over the mouth, unseen (ar1))
				AddEffect(TEXT("BrazierFire"), P + MistgateNormal * 95.f + FVector(0, 0, Fz * 0.15f), 2.5f);
				AddEffect(TEXT("ForgeSparks"), P + MistgateNormal * 110.f + FVector(0, 0, Fz * 0.25f), 1.f);
				AddLight(P + MistgateNormal * 180.f + FVector(0, 0, 160.f), FLinearColor(1.f, 0.38f, 0.1f), 420.f, 1600.f, true, 0.3f);
			}
			FurnRoom = -1;
		}
	}
	// ---- the halls' hanging lamps down their middle
	for (int32 K = 1; K <= 2 && K < B.Rooms.Num(); ++K)
	{
		const FRoom& Hl = Rooms[B.Rooms[K]];
		const bool bAlongX = (Hl.Max.X - Hl.Min.X) >= (Hl.Max.Y - Hl.Min.Y);
		const int32 L0 = bAlongX ? Hl.Min.X : Hl.Min.Y, L1 = bAlongX ? Hl.Max.X : Hl.Max.Y;
		const int32 Mid = bAlongX ? (Hl.Min.Y + Hl.Max.Y) / 2 : (Hl.Min.X + Hl.Max.X) / 2;
		for (int32 L = L0 + 2; L < L1 - 1; L += 4)
		{
			const FVector P = TileWorld(bAlongX ? FIntPoint(L, Mid) : FIntPoint(Mid, L));
			AddPieceAt(TEXT("Foundry.Lamp"), P + FVector(0, 0, 900.f), 0.f, 1.f, true);
			AddLight(P + FVector(0, 0, 820.f), FLinearColor(1.f, 0.62f, 0.32f), 480.f, 2200.f, false, 0.06f);
		}
	}
	// ---- the casting hall's working lines (ar1's picture: a bare brick hall): a forge and its anvil every third tile down each
	// long wall, facing the hall's middle (no work for the guild there: the foundry is lost to them); an ore cart's rail along
	// one side; the lane down the middle and the rows of the side doors kept free
	int32 Lines = 0;
	if (B.Rooms.Num() > 1)
	{
		const FRoom& Hl = Rooms[B.Rooms[1]];
		const bool bAlongX = (Hl.Max.X - Hl.Min.X) >= (Hl.Max.Y - Hl.Min.Y);
		const int32 L0 = bAlongX ? Hl.Min.X : Hl.Min.Y, L1 = bAlongX ? Hl.Max.X : Hl.Max.Y;
		const int32 W0 = bAlongX ? Hl.Min.Y : Hl.Min.X, W1 = bAlongX ? Hl.Max.Y : Hl.Max.X;
		auto At = [&](int32 L, int32 W) { return TileWorld(bAlongX ? FIntPoint(L, W) : FIntPoint(W, L)); };
		// (the tiles of a side door: a door edge out of the hall on that row; every other row a forge (ar2: every third row with
		// the rows either side of a door kept left four forges, the hall still bare))
		auto DoorRow = [&](int32 L)
		{
			for (int32 Dl = 0; Dl <= 0; ++Dl)
				for (const int32 W : { W0, W1 - 1 })
				{
					const FIntPoint T = bAlongX ? FIntPoint(L + Dl, W) : FIntPoint(W, L + Dl);
					for (int32 Side = 0; Side < 4; ++Side) if (DoorEdges.Contains(EdgeKey(T, T + RDForgeDir4[Side]))) return true;
				}
			return false;
		};
		FurnRoom = B.Rooms[1];
		for (int32 L = L0 + 1; L < L1 - 1; L += 2)
		{
			if (DoorRow(L)) continue;
			for (const int32 Sd : { 0, 1 })
			{
				const int32 W = Sd ? W1 - 1 : W0;
				const FVector P = At(L, W), In_ = (At(L, (W0 + W1) / 2) - P).GetSafeNormal2D();
				FTownSpot Fs; Fs.Kind = TS_Forge; Fs.At = P + In_ * 40.f; Fs.Yaw = In_.Rotation().Yaw;
				OpenForgeBuild(Fs, false);
				MarkBlocked(Fs.At, Fs.Yaw, FVector2D(200.f, 200.f), true);
				++Lines;
			}
		}
		// (the rail and its carts two rows in from the first side, off the lane)
		const int32 Wr = W0 + 2;
		for (int32 L = L0; L < L1; ++L) AddPieceAt(TEXT("Forge.Rail"), At(L, Wr), bAlongX ? 0.f : 90.f, 1.f, true);
		for (const int32 L : { L0 + 2, L1 - 3 })
		{
			const FRDPiece* Rl = Generator->Piece(TEXT("Forge.Rail"));
			const FVector P = At(L, Wr) + FVector(0, 0, Rl ? (float)Rl->Size.Z : 10.f);
			if (AddPieceAt(TEXT("Forge.Cart"), P, bAlongX ? 0.f : 90.f)) MarkBlocked(P, bAlongX ? 0.f : 90.f, FVector2D(220.f, 120.f), true);
		}
		FurnRoom = -1;
	}
	B.Style = 5;
	UE_LOG(LogRDForge, Log, TEXT("RDFORGE the foundry built: %d rooms, %d chimneys, %d forges down the casting hall, the gate down at (%.0f, %.0f)"), B.Rooms.Num(), Stacks, Lines, MistgateAt.X, MistgateAt.Y);
}

void ARDSection::ForgeAnvilBuild(const FTownSpot& Sp)
{
	// (the guild's great anvil: on its plinth, standing on the plinth's top, a brazier's glow on it at night)
	const FRDPiece* Pl = Generator->Piece(TEXT("Forge.Plinth"));
	AddPieceAt(TEXT("Forge.Plinth"), Sp.At, Sp.Yaw);
	AddPieceAt(TEXT("Forge.GreatAnvil"), Sp.At + FVector(0, 0, Pl ? (float)Pl->Size.Z - 2.f : 100.f), Sp.Yaw);
	AddLight(Sp.At + FVector(0, 0, 520.f), FLinearColor(1.f, 0.6f, 0.3f), 140.f, 1200.f, false, 0.1f);
}

void ARDSection::OpenForgeBuild(const FTownSpot& Sp, bool bWork)
{
	// (an open forge on the square: the forge, its anvil before it toward the square's middle (Sp.Yaw points there), its fire,
	// sparks and smoke, its glow; the work there for the guild's workers: hammering at the anvil, tending the fire)
	const FRotator Ro(0, Sp.Yaw, 0);
	const FRDPiece* Fg = Generator->Piece(TEXT("Forge.OpenForge"));
	const float Fz = Fg ? (float)Fg->Size.Z : 150.f;
	AddPieceAt(TEXT("Forge.OpenForge"), Sp.At, Sp.Yaw);
	const FVector Av = Sp.At + Ro.RotateVector(FVector(200.f, 0, 0));
	AddPieceAt(TEXT("Forge.Anvil"), Av, Sp.Yaw + 90.f);
	AddEffect(TEXT("BrazierFire"), Sp.At + FVector(0, 0, Fz * 0.55f), 1.3f);
	AddEffect(TEXT("ForgeSparks"), Sp.At + FVector(0, 0, Fz * 0.6f), 0.8f);
	AddEffect(TEXT("ChimneySmoke"), Sp.At + FVector(0, 0, Fz + 120.f), 0.7f);
	AddLight(Sp.At + Ro.RotateVector(FVector(90.f, 0, 0)) + FVector(0, 0, 140.f), FLinearColor(1.f, 0.42f, 0.12f), 320.f, 1800.f, true, 0.25f);
	MarkBlocked(Av, Sp.Yaw, FVector2D(120.f, 120.f), true);
	if (!bWork) return;
	const float* RHam = Generator->TownWorkReach.Find(TEXT("Hammer"));
	FTownWork Hm; Hm.Kind = TEXT("Hammer"); Hm.At = Av + Ro.RotateVector(FVector(RHam ? *RHam : 85.f, 0, 0)); Hm.Yaw = Sp.Yaw + 180.f; Hm.Group = TW_Smithy; Hm.Bld = -1; Hm.Prop = TEXT("Hammer");
	TownWorks.Add(Hm);
	FTownWork Fw; Fw.Kind = TEXT("Forge"); Fw.At = Sp.At + Ro.RotateVector(FVector(130.f, 110.f, 0)); Fw.Yaw = Sp.Yaw + 180.f; Fw.Group = TW_Smithy; Fw.Bld = -1;
	TownWorks.Add(Fw);
}

void ARDSection::OreCartBuild(const FTownSpot& Sp)
{
	// (an ore cart on a stretch of rail along the way to the foundry: three lengths of rail, the cart on the middle one)
	const FRotator Ro(0, Sp.Yaw, 0);
	const FRDPiece* Rl = Generator->Piece(TEXT("Forge.Rail"));
	const float L = Rl ? FMath::Max((float)Rl->Size.X, 100.f) : 300.f;
	for (int32 K = -1; K <= 1; ++K) AddPieceAt(TEXT("Forge.Rail"), Sp.At + Ro.RotateVector(FVector(K * L, 0, 0)), Sp.Yaw, 1.f, true);
	AddPieceAt(TEXT("Forge.Cart"), Sp.At + FVector(0, 0, Rl ? (float)Rl->Size.Z : 10.f), Sp.Yaw);
}

void ARDSection::BarricadeBuild(const FTownSpot& Sp)
{
	// (a stretch of the barricade before the foundry, its spikes toward the foundry's door (Sp.Yaw points there))
	AddPieceAt(TEXT("Forge.Barricade"), Sp.At, Sp.Yaw);
}
