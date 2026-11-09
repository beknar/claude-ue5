// Kethrys Spire (the user's list of 2026-11-08b, docs/improvements9.txt: "a mage-city clustered around a black tower that hasn't
// opened its gates in a century. the lights in the upper windows still move. ... magical effects, laboratories, libraries, study
// rooms, meditation chambers, stone houses ... this is not a poor village"). The
// city is one of the wilderness's towns (the generator's TownPlan 4, RDTownPlan.cpp's bMage: the black tower at the town's
// middle, the square before it with its rune circle and crystal pylons, the libraries and laboratories, houses of well-kept
// grey-blue stone, the archmage, scribes, alchemists, apprentices and the Spire's wardens). This file builds:
//   - the black tower: its gatehouse and its hall (dark stone inside and out, a flat roof), the round tower over the hall rising
//     to TowerTop with its crown and spire, its windows' glow, a beam of light from its top, mist round its foot; the gate sealed
//     for a century at the hall's far wall (walked into with the Spire Key it opens the tower's dungeon: RDTownGame.cpp, as the
//     other cities' ways down; RDKeys.cpp refuses it without its key);
//   - a rune circle glowing on the ground, a crystal pylon on its plinth with its glow;
//   - a laboratory's cauldron (bubbling, its smoke) and its table of potions, before the furniture (a stream of their own);
//   - the upper storeys' lights that move (the spec: "the lights in the upper windows still move"): lights and glowing orbs on
//     pivots turned by rotating movements. (The meditation chambers' rune circles and candles are in ARDSection::Furnish.)
// The pieces are "Spire.*" and "Mage.*" in the generator's table (pipeline/unreal/906 sets them), the effects "MageWard",
// "MageRune", "MageCrystal", "MageMist", "MageBeam", "CauldronFx" too.
#include "RD/RDSection.h"
#include "RD/RDDungeonGenerator.h"
#include "RD/RDTown.h"
#include "Engine/World.h"
#include "Misc/ScopeExit.h"
#include "Components/PointLightComponent.h"
#include "GameFramework/RotatingMovementComponent.h"
#include "NiagaraComponent.h"
#include "NiagaraSystem.h"

DEFINE_LOG_CATEGORY_STATIC(LogRDMage, Log, All);

// (the upper storeys' moving lights and their pivots: found by a test with GetComponentsByTag)
static const FName RDSpireWindowTag(TEXT("SpireWindow"));

static const FIntPoint RDMageDir4[4] = { FIntPoint(-1, 0), FIntPoint(1, 0), FIntPoint(0, -1), FIntPoint(0, 1) };

void ARDSection::SpireShell(int32 BI)
{
	FTownBld& B = TownBlds[BI];
	FRandomStream R((int32)(B.Seed ^ 0x3A9E51u));
	const float M = Generator->TileSize;
	const FName Wall(TEXT("Spire.Wall")), WallOut(TEXT("Spire.WallOut")), Floor(TEXT("Spire.Floor")), Ceil(TEXT("Spire.Ceil"));
	const FRDPiece* Wp = Generator->Piece(Wall);
	const FRDPiece* Op = Generator->Piece(WallOut);
	const FRDPiece* Dp = Generator->Piece(TEXT("Doorway"));
	const float T = Wp ? FMath::Clamp((float)Wp->Size.X, 20.f, 120.f) : 60.f;
	const float WZ = Wp ? FMath::Max((float)Wp->Size.Z - 2.f, 50.f) : 300.f;
	const float OZ = Op ? FMath::Max((float)Op->Size.Z - 2.f, 50.f) : WZ;
	// (the plan's rooms: the gatehouse, the hall under the round tower)
	auto HeightOf = [&](int32 K) { return K == 0 ? 750.f : 1200.f; };
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
				AddPieceAt(TEXT("Town.CastleRoof"), C + FVector(0, 0, H + 40.f), 0.f, 1.f, true);
				for (int32 Side = 0; Side < 4; ++Side)
				{
					const FIntPoint Nb = Tl + RDMageDir4[Side];
					const int32 On = In(Nb) ? Owner[Idx(Nb)] : -1;
					if (On == RI) continue;
					const int32 Kn = B.Rooms.IndexOfByKey(On);
					const bool bOut = Kn == INDEX_NONE;
					const bool bDoor = DoorEdges.Contains(EdgeKey(Tl, Nb));
					const FVector Edge = C + FVector(RDMageDir4[Side].X, RDMageDir4[Side].Y, 0) * (M * 0.5f);
					const float Yaw = InwardYaw(Side);
					const FVector OutW = FRotator(0, Yaw, 0).RotateVector(FVector(-1, 0, 0));
					const FVector At = bOut ? Edge : Edge - OutW * (T * 0.5f);
					const float Hn = bOut ? 0.f : HeightOf(Kn);
					const FVector AtOut = Edge + OutW * (bOut ? T : T * 0.5f);
					auto OuterFace = [&](float Z0) { Stack(WallOut, OZ, AtOut, Yaw + 180.f, Z0, H + 40.f); };
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
	// ---- the round tower over the hall: its rings stacked from the hall's roof to TowerTop, its crown and its spire; its windows'
	// glow every other ring; a beam of light from its top; mist round the tower's foot
	int32 Rings = 0;
	if (B.Rooms.Num() >= 2)
	{
		const FRoom& Hl = Rooms[B.Rooms[1]];
		const FVector Tc = (TileWorld(Hl.Min) + TileWorld(Hl.Max - FIntPoint(1, 1))) * 0.5f;
		const FRDPiece* Rp = Generator->Piece(TEXT("Spire.Ring"));
		const float Rh = Rp ? FMath::Max((float)Rp->Size.Z - 10.f, 100.f) : 800.f;
		const float Z0 = HeightOf(1) + 40.f;
		const float Top = FMath::Max(Generator->SpireTowerTop, Z0 + Rh);
		const float Yaw0 = TownBldYaw(B);
		const float Rr = Rp ? (float)FMath::Max(Rp->Size.X, Rp->Size.Y) * 0.5f : 1000.f;
		const int32 NRings = FMath::Max(1, FMath::CeilToInt((Top - 5.f - Z0) / Rh));
		float Z = Z0;
		for (; Z < Top - 5.f; Z += Rh)
		{
			const int32 Ri = Rings;
			if (AddPieceAt(TEXT("Spire.Ring"), Tc + FVector(0, 0, Z), Yaw0 + 90.f * (Rings % 4))) ++Rings;
			if (Ri * 3 >= NRings && bBuildStatic)
			{
				// (the spec: "the lights in the upper windows still move": in each upper storey two lights and their glowing orbs on
				// a pivot that a rotating movement turns, each storey its own pace and way, so the glow passes from window to window.
				// At the windows' line just outside the wall: the ring's windows are recesses, and a light inside lit nothing that
				// shows (884 spire's night picture, test_ks6), as the lower storeys' lights at the wall show)
				USceneComponent* Pv = AddPivot(RootComponent, FTransform(FRotator(0, R.FRandRange(0.f, 360.f), 0), Tc + FVector(0, 0, Z + Rh * 0.5f) - GetActorLocation()));
				if (!Pv) continue;
				Pv->ComponentTags.Add(RDSpireWindowTag);
				for (int32 K = 0; K < 2; ++K)
				{
					const FVector Rel((Rr + 45.f) * (K ? -1.f : 1.f), 0.f, R.FRandRange(-0.15f, 0.15f) * Rh);
					if (UPointLightComponent* L = AddLight(Pv->GetComponentTransform().TransformPosition(Rel), FLinearColor(0.6f, 0.4f, 1.f), 260.f, 1100.f, false, 0.f))
					{
						L->AttachToComponent(Pv, FAttachmentTransformRules::KeepWorldTransform);
						L->ComponentTags.Add(RDSpireWindowTag);
						L->MaxDrawDistance = 0.f;                       // (seen from beyond the wall)
					}
					if (const TObjectPtr<UNiagaraSystem>* S = Generator->Effects.Find(TEXT("MageCrystal")); S && *S)
					{
						UNiagaraComponent* C = NewObject<UNiagaraComponent>(this, NAME_None, RF_Transactional);
						C->SetAsset(*S);
						C->SetupAttachment(Pv);
						C->SetRelativeLocation(Rel);
						C->SetRelativeScale3D(FVector(2.f));
						C->SetAutoActivate(true);
						C->RegisterComponent();
						AddInstanceComponent(C);
					}
				}
				URotatingMovementComponent* Rot = NewObject<URotatingMovementComponent>(this, NAME_None, RF_Transactional);
				Rot->SetUpdatedComponent(Pv);
				Rot->RotationRate = FRotator(0.f, (R.RandBool() ? 1.f : -1.f) * R.FRandRange(14.f, 32.f), 0.f);
				Rot->bRotationInLocalSpace = true;
				Rot->RegisterComponent();
				AddInstanceComponent(Rot);
			}
			else if (Ri % 2 == 0)
				for (int32 K = 0; K < 3; ++K)
				{
					const FVector Dir = FRotator(0, Yaw0 + 60.f + 120.f * K + 30.f * (Ri % 3), 0).RotateVector(FVector(1, 0, 0));
					AddLight(Tc + Dir * (Rr + 60.f) + FVector(0, 0, Z + Rh * 0.55f), FLinearColor(0.55f, 0.35f, 1.f), 160.f, 1400.f, false, 0.15f);
				}
		}
		AddPieceAt(TEXT("Spire.RingTop"), Tc + FVector(0, 0, Z), Yaw0, 1.f, true);
		const FRDPiece* Tp = Generator->Piece(TEXT("Spire.RingTop"));
		const float Zc = Z + (Tp ? (float)Tp->Size.Z : 0.f);
		AddPieceAt(TEXT("Spire.Cap"), Tc + FVector(0, 0, Zc - 20.f), Yaw0, 1.f, true);
		const FRDPiece* Cp = Generator->Piece(TEXT("Spire.Cap"));
		AddEffect(TEXT("MageBeam"), Tc + FVector(0, 0, Zc + (Cp ? (float)Cp->Size.Z : 1500.f) - 200.f), 3.f);
		AddLight(Tc + FVector(0, 0, Zc + 400.f), FLinearColor(0.5f, 0.3f, 1.f), 600.f, 6000.f, false, 0.f);
		TowerTopZ = Zc;
		// (mist round its foot, before the gatehouse and along the hall's sides)
		const FVector Front = FVector(RDMageDir4[B.DoorSide].X, RDMageDir4[B.DoorSide].Y, 0.f), Across(Front.Y, -Front.X, 0.f);
		const FVector Door = TileWorld(B.DoorTile) + Front * 600.f;
		for (const float Sd : { -1.f, 1.f }) AddEffect(TEXT("MageMist"), Door + Across * Sd * 900.f, 1.5f);
	}
	// ---- the hall's light: cold and violet, a lamp of crystals down its middle
	if (B.Rooms.Num() >= 2)
	{
		const FRoom& Hl = Rooms[B.Rooms[1]];
		for (int32 X = Hl.Min.X + 2; X < Hl.Max.X - 1; X += 4)
			for (int32 Y = Hl.Min.Y + 2; Y < Hl.Max.Y - 1; Y += 4)
				AddLight(TileWorld(FIntPoint(X, Y)) + FVector(0, 0, 800.f), FLinearColor(0.6f, 0.5f, 1.f), 260.f, 1600.f, false, 0.1f);
	}
	// ---- the gate sealed for a century: its arch against the hall's far wall, its ward's glow (walked into with the key, it
	// opens the tower's dungeon)
	AddPieceAt(TEXT("Spire.Gate"), MistgateAt + MistgateNormal * 45.f, MistgateNormal.Rotation().Yaw, 1.f, true);
	AddEffect(TEXT("MageWard"), MistgateAt + MistgateNormal * 80.f + FVector(0, 0, 150.f), 1.2f);
	AddLight(MistgateAt + MistgateNormal * 220.f + FVector(0, 0, 260.f), FLinearColor(0.55f, 0.3f, 1.f), 260.f, 1200.f, false, 0.2f);
	B.Style = 6;
	UE_LOG(LogRDMage, Log, TEXT("RDMAGE the black tower built: %d rooms, %d rings to %.0f cm, the gate at (%.0f, %.0f)"), B.Rooms.Num(), Rings, TowerTopZ, MistgateAt.X, MistgateAt.Y);
}

void ARDSection::MageSpotBuild(const FTownSpot& Sp)
{
	if (Sp.Kind == TS_Rune)
	{
		// (a rune circle on the ground: its ring of light turning, small stones round it, a cold glow)
		AddEffect(TEXT("MageRune"), Sp.At + FVector(0, 0, 8.f), 2.f);
		for (int32 K = 0; K < 6; ++K)
		{
			const FVector D = FRotator(0, Sp.Yaw + 60.f * K, 0).RotateVector(FVector(1, 0, 0));
			AddPieceAt(TEXT("Mage.RuneStone"), Sp.At + D * 330.f, Sp.Yaw + 60.f * K + 180.f, 0.5f);
			MarkBlocked(Sp.At + D * 330.f, 0.f, FVector2D(90.f, 90.f), true);     // (PR #32's review: the townsfolk walked into them)
		}
		AddLight(Sp.At + FVector(0, 0, 120.f), FLinearColor(0.4f, 0.55f, 1.f), 200.f, 900.f, false, 0.2f);
		return;
	}
	// (a crystal pylon: its plinth, the crystal on it, its glow)
	const FRDPiece* Pl = Generator->Piece(TEXT("Mage.Plinth"));
	const float Pz = Pl ? (float)Pl->Size.Z - 2.f : 100.f;
	AddPieceAt(TEXT("Mage.Plinth"), Sp.At, Sp.Yaw);
	AddPieceAt(TEXT("Mage.Crystal"), Sp.At + FVector(0, 0, Pz), Sp.Yaw, 1.f, true);
	AddEffect(TEXT("MageCrystal"), Sp.At + FVector(0, 0, Pz + 80.f), 1.f);
	AddLight(Sp.At + FVector(0, 0, Pz + 120.f), FLinearColor(0.45f, 0.6f, 1.f), 160.f, 800.f, false, 0.1f);
}

void ARDSection::MageLabBuild(int32 BI)
{
	// (a laboratory: a cauldron bubbling on the far side from the door, a table of potions beside it, both off the door's lane;
	// a stream of their own, so the plan's draws and the furniture's stay where they were)
	const FTownBld& B = TownBlds[BI];
	if (B.State != 0 || B.Rooms.Num() == 0) return;
	FRandomStream R((int32)(B.Seed ^ 0xA1C4E3u));
	// (after the room's own furnishing, among its footprints: a piece that would stand in another is refused (FurnRoom), so each
	// is tried at a few places; PR #32's review: built before it, the kitchen's barrels and crates were set into them)
	FurnRoom = B.Rooms[0];
	ON_SCOPE_EXIT { FurnRoom = -1; };
	const float M = Generator->TileSize;
	const int32 Nx = B.DoorSide < 2 ? B.Max.X - B.Min.X : B.Max.Y - B.Min.Y;
	const int32 Ny = B.DoorSide < 2 ? B.Max.Y - B.Min.Y : B.Max.X - B.Min.X;
	const float Hx = Nx * M * 0.5f, Hy = Ny * M * 0.5f;
	const float Yaw0 = TownBldYaw(B);
	const float Sd = R.RandBool() ? 1.f : -1.f;
	const float CYaw = Yaw0 + R.FRandRange(0.f, 360.f);
	FVector Cauldron = FVector::ZeroVector; bool bCauldron = false;
	for (const FVector2D& Q : { FVector2D(-Hx + 220.f, Sd * (Hy - 230.f)), FVector2D(-Hx + 220.f, -Sd * (Hy - 230.f)), FVector2D(-Hx * 0.2f, Sd * (Hy - 230.f)),
	                            FVector2D(-Hx * 0.2f, -Sd * (Hy - 230.f)), FVector2D(Hx * 0.3f, Sd * (Hy - 230.f)), FVector2D(Hx * 0.3f, -Sd * (Hy - 230.f)) })
	{
		Cauldron = TownBldPoint(B, Q.X, Q.Y, 0.f);
		if (AddPieceAt(TEXT("Mage.Cauldron"), Cauldron, CYaw)) { bCauldron = true; break; }
	}
	if (bCauldron)
	{
		const FRDPiece* Cp = Generator->Piece(TEXT("Mage.Cauldron"));
		AddEffect(TEXT("CauldronFx"), Cauldron + FVector(0, 0, Cp ? (float)Cp->Size.Z * 0.85f : 80.f), 1.f);
		AddLight(Cauldron + FVector(0, 0, 150.f), FLinearColor(0.35f, 1.f, 0.55f), 140.f, 700.f, false, 0.3f);
		MarkBlocked(Cauldron, Yaw0, FVector2D(260.f, 260.f), true);
	}
	const FRDPiece* Tp = Generator->Piece(TEXT("Mage.LabTable"));
	const float Tz = Tp ? (float)Tp->Size.Z : 90.f;
	for (const FVector2D& Q : { FVector2D(-Hx * 0.2f, -Sd * (Hy - 160.f)), FVector2D(-Hx * 0.2f, Sd * (Hy - 160.f)), FVector2D(Hx * 0.3f, -Sd * (Hy - 160.f)),
	                            FVector2D(Hx * 0.3f, Sd * (Hy - 160.f)), FVector2D(-Hx + 200.f, -Sd * (Hy - 160.f)), FVector2D(-Hx + 200.f, Sd * (Hy - 160.f)) })
	{
		const FVector Table = TownBldPoint(B, Q.X, Q.Y, 0.f);
		if (!AddPieceAt(TEXT("Mage.LabTable"), Table, Yaw0 + 90.f)) continue;
		for (int32 K = 0; K < 4; ++K)
			AddPieceAt(TEXT("Mage.Potion"), Table + FRotator(0, Yaw0 + 90.f, 0).RotateVector(FVector(R.FRandRange(-60.f, 60.f), R.FRandRange(-20.f, 20.f), Tz)), R.FRandRange(0.f, 360.f), 1.f, true);
		MarkBlocked(Table, Yaw0 + 90.f, FVector2D(Tp ? (float)Tp->Size.X + 40.f : 220.f, Tp ? (float)Tp->Size.Y + 40.f : 120.f), true);
		break;
	}
	if (!bCauldron) UE_LOG(LogRDMage, Warning, TEXT("RDMAGE no room for a laboratory's cauldron (building %d)"), BI);
}
