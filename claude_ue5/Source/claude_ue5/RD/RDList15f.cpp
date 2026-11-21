// The user's list of 2026-11-20 (docs/improvements15.txt; the plan docs/improvements15_plan.md), its seventh phase: the villages'
// ground. Item 26, "the small villages on the hillsides should have cut flat ledges into the hillsides and support them with retaining
// walls and buttresses to create ground for homes, plazas and fortifications. the procedural terrain generation should account for this
// when placing villages onto angled terrain": a village's houses and its square stand on level pads (FRDWPad), each held at the land's
// height at its middle in the world's own height (Feature: what she walks on, what is drawn and the far land agree), eased to the land
// over a short band (longer where a road comes in); a retaining wall with buttresses along every edge the land stands away from. The
// village is 8 to 15 houses on two rings round its square (item 28's size: phase 8 fills them). A village is placed on the land
// without terraces and refused where a pad would stand more than TerraceMaxStepM off it. Item 29 (steps that reach the ground) is
// RDWild10.cpp's and RDWildFarm11.cpp's.
#include "RD/RDDungeonGenerator.h"
#include "RD/RDWild.h"
#include "Components/InstancedStaticMeshComponent.h"
#include "Engine/StaticMesh.h"
#include "ProceduralMeshComponent.h"
DEFINE_LOG_CATEGORY_STATIC(LogRDList15f, Log, All);

// ================================================================================================ the world's side
namespace { thread_local int32 GRDW15NoTerrace = 0; }
FRDWNoTerrace::FRDWNoTerrace() { ++GRDW15NoTerrace; }
FRDWNoTerrace::~FRDWNoTerrace() { --GRDW15NoTerrace; }
bool FRDWNoTerrace::On() { return GRDW15NoTerrace > 0; }

/** the gap between two rectangles on the ground (the most any of their four axes keeps them apart; negative: they overlap) */
static float RDW15PadGap(const FRDWPad& A, const FRDWPad& B)
{
	const FVector2D Ua(FMath::Cos(FMath::DegreesToRadians(A.Yaw)), FMath::Sin(FMath::DegreesToRadians(A.Yaw))), Va(-Ua.Y, Ua.X);
	const FVector2D Ub(FMath::Cos(FMath::DegreesToRadians(B.Yaw)), FMath::Sin(FMath::DegreesToRadians(B.Yaw))), Vb(-Ub.Y, Ub.X);
	const FVector2D D = B.C - A.C;
	float Best = -1e9f;
	for (const FVector2D& N : { Ua, Va, Ub, Vb })
	{
		const float Ra = A.Half.X * FMath::Abs(FVector2D::DotProduct(Ua, N)) + A.Half.Y * FMath::Abs(FVector2D::DotProduct(Va, N));
		const float Rb = B.Half.X * FMath::Abs(FVector2D::DotProduct(Ub, N)) + B.Half.Y * FMath::Abs(FVector2D::DotProduct(Vb, N));
		Best = FMath::Max(Best, FMath::Abs(FVector2D::DotProduct(D, N)) - Ra - Rb);
	}
	return Best;
}

int32 FRDWildWorld::VillageSlots(const FRDWildPlace& V, TArray<FRDWPad>* Out) const
{
	// (the houses are up to 10.7 x 20.9 m with their doors on their +X and -X walls (measured on the five meshes at their scale): a
	// pad 16 x 24 m leaves 2.6 m before each door; seven slots at 36 m round the square (24 m across) and eight at 60 m. PR #99's
	// review: at 33 m the inner pads' inner corners cleared each other by 4 cm at their nominal 51.4 degrees and met under the jitter;
	// at 36 m they need 46.4, and a slot whose pad would meet one kept already (by their rectangles, 1 m apart at least) is not built.
	// The count and the jitters are drawn first, whatever the land, so a slot's place never moves with another's refusal. Each pad kept
	// carries its height, the land at its PadRef as tested)
	FRandomStream R((int32)Hash(V.Id, 501, Seed));
	const int32 N = R.RandRange(VillageHousesMin, VillageHousesMax);
	TArray<FRDWPad> Slots;
	auto Ring = [&](int32 Count, float Rr, float Off)
	{
		for (int32 I = 0; I < Count; ++I)
		{
			const float A = V.Yaw + (I + Off) * 360.f / Count + R.FRandRange(-2.f, 2.f);
			FRDWPad P; P.C = V.At + FVector2D(FMath::Cos(FMath::DegreesToRadians(A)), FMath::Sin(FMath::DegreesToRadians(A))) * Rr;
			P.Yaw = A + 180.f; P.Half = FVector2D(8.f, 12.f); P.Kind = 1;
			Slots.Add(P);
		}
	};
	Ring(7, VillageInnerRingM, 0.f);
	Ring(8, VillageOuterRingM, 0.5f);
	FRDWPad Sq; Sq.C = V.At; Sq.Yaw = V.Yaw; Sq.Half = FVector2D(12.f, 12.f); Sq.Kind = 0;
	auto Buildable = [this](FRDWPad& Pd)
	{
		const FVector2D Ax(FMath::Cos(FMath::DegreesToRadians(Pd.Yaw)), FMath::Sin(FMath::DegreesToRadians(Pd.Yaw))), Ay(-Ax.Y, Ax.X);
		const FVector2D Hr = PadRef(Pd);
		const float Hc = NaturalHeight(Hr.X, Hr.Y);
		for (int32 Ix = -1; Ix <= 1; ++Ix)
			for (int32 Iy = -1; Iy <= 1; ++Iy)
			{
				const FVector2D Q = Pd.C + Ax * (Pd.Half.X * Ix) + Ay * (Pd.Half.Y * Iy);
				const FRDWNoTerrace G;
				FRDWSample Sq2; Sample(Q.X, Q.Y, Sq2, false);
				// (the land's own height there (with its detail): the coarse sample without it stood up to 10 m off it in the hills)
				if (Sq2.WaterKind != 0 || FMath::Abs(NaturalHeight(Q.X, Q.Y) - Hc) > TerraceMaxStepM) return false;
			}
		Pd.H = Hc;
		return true;
	};
	extern int32 GRDW15Refused[3];
	if (!Buildable(Sq)) { if (FRDWNoTerrace::On()) FPlatformAtomics::InterlockedIncrement(&GRDW15Refused[1]); return 0; }
	TArray<FRDWPad> Kept; Kept.Add(Sq);
	int32 Can = 0;
	for (FRDWPad& S : Slots)
	{
		bool bClear = true;
		for (const FRDWPad& K : Kept) if (RDW15PadGap(S, K) < 1.f) { bClear = false; break; }
		if (bClear && Buildable(S)) { if (Can < N) Kept.Add(S); ++Can; }
	}
	if (Out) *Out = MoveTemp(Kept);
	{ extern int32 GRDW15SlotHist[16]; FPlatformAtomics::InterlockedIncrement(&GRDW15SlotHist[FMath::Clamp(Can, 0, 15)]); }
	return Can;
}

FVector2D FRDWildWorld::PadRef(const FRDWPad& Pd)
{
	// (a house's pad at the land's height at its front door (its +X edge's middle, toward the square): the door opens on the land,
	// the cut or fill behind it where its walls stand. Held at its middle's, a pad 5 m under the land before its door and 18 m under
	// the square left that door out of reach on foot (Mistwell). The square at its middle's)
	if (Pd.Kind != 1) return Pd.C;
	return Pd.C + FVector2D(FMath::Cos(FMath::DegreesToRadians(Pd.Yaw)), FMath::Sin(FMath::DegreesToRadians(Pd.Yaw))) * Pd.Half.X;
}

float FRDWildWorld::NaturalHeight(double X, double Y) const
{
	const FRDWNoTerrace G;
	return Feature(X, Y, LandHeight(X, Y, true), nullptr);
}

void FRDWildWorld::StoreTerraces(FIntPoint Cell, const FRDWildPlace* V, const TArray<FRDWPad>* Pads) const
{
	// (the slots its placing tested, at the heights it tested them (PR #99's review: passed from that test, not worked out twice): the
	// land as the places are made. Read after the minor roads, whose beds ran through the pads, a pad's land spanned 30 m in the
	// mountains; the ways now start past the pads (VillageWayInsetM))
	TSharedPtr<FRDWTerraces> Tr;
	if (V && Pads)
	{
		Tr = MakeShared<FRDWTerraces>();
		Tr->Mid = V->At; Tr->VillageId = V->Id; Tr->Pads = *Pads;
		double Rm = 0.0;
		for (const FRDWPad& Pd : Tr->Pads) Rm = FMath::Max(Rm, FVector2D::Distance(Pd.C, V->At) + Pd.Half.Size());
		Tr->R = Rm + 25.0;          // (the longest ramp, 24 m)
	}
	FScopeLock Lk(&TerraceCache->Lock);
	if (!TerraceCache->Cells.Contains(Cell)) TerraceCache->Cells.Add(Cell, Tr);
}

namespace
{
	// (a thread's last cell asked for: every ground sample of a chunk asks for its cell, and nearly all ask for the same one (PR #99's
	// review: a lock and a map lookup for every sample on every worker). Keyed by the world and its Init, which empties the cache)
	struct FRDW15LastTerrace { const FRDWildWorld* W = nullptr; uint32 Gen = 0; FIntPoint Cell = FIntPoint(MIN_int32, MIN_int32); TSharedPtr<const FRDWTerraces> T; };
	thread_local FRDW15LastTerrace GRDW15Last;
}

TSharedPtr<const FRDWTerraces> FRDWildWorld::TerracesAt(double X, double Y) const
{
	const FIntPoint Cell = PlaceCellOf(X, Y);
	if (GRDW15Last.W == this && GRDW15Last.Gen == TerraceGen && GRDW15Last.Cell == Cell) return GRDW15Last.T;
	TSharedPtr<const FRDWTerraces> Got;
	bool bHave = false;
	for (int32 Pass = 0; Pass < 2 && !bHave; ++Pass)
	{
		{
			FScopeLock Lk(&TerraceCache->Lock);
			if (const TSharedPtr<const FRDWTerraces>* G = TerraceCache->Cells.Find(Cell)) { Got = *G; bHave = true; }
		}
		// (the cell's places made (they record its village's slots); a cell outside the continent's places has none)
		if (!bHave && Pass == 0) { const FRDWNoTerrace G; TArray<FRDWildPlace> Ps; PlacesIn(Cell, Ps); }
	}
	if (!bHave) { FScopeLock Lk(&TerraceCache->Lock); if (!TerraceCache->Cells.Contains(Cell)) TerraceCache->Cells.Add(Cell, nullptr); }
	GRDW15Last.W = this; GRDW15Last.Gen = TerraceGen; GRDW15Last.Cell = Cell; GRDW15Last.T = Got;
	return Got;
}

float FRDWildWorld::ApplyTerrace(double X, double Y, float H, float& Terrace) const
{
	// (a house's pad: level; on its two door sides (its +X front, toward the square, and its back) an earth ramp to the land, 1 in 3
	// (walkable: with walls on every side the land stood off, no door was reached on foot); on its long sides a retaining wall's
	// band (LayTerraceWalls15). The square ramps on every side. Where two ramps meet, each pad's eased height weighted so that a
	// pad's own height holds at its edge (PR #99's review: weighted by nearness alone, a neighbour's ramp lifted the ground just
	// outside a pad 2 m over its edge), and how far the pads reach by the nearest's)
	Terrace = 0.f;
	const TSharedPtr<const FRDWTerraces> T = TerracesAt(X, Y);
	if (!T.IsValid()) return H;
	const FVector2D P(X, Y);
	if (FVector2D::DistSquared(P, T->Mid) > T->R * T->R) return H;
	float Ws = 0.f, Hs = 0.f;
	for (const FRDWPad& Pd : T->Pads)
	{
		const float A = FMath::DegreesToRadians(Pd.Yaw), Ca = FMath::Cos(A), Sa = FMath::Sin(A);
		const FVector2D D = P - Pd.C;
		const float Lx = D.X * Ca + D.Y * Sa, Ly = -D.X * Sa + D.Y * Ca;
		const float Ex = FMath::Abs(Lx) - Pd.Half.X, Ey = FMath::Abs(Ly) - Pd.Half.Y;
		if (Ex <= 0.f && Ey <= 0.f) { Terrace = 1.f; return Pd.H; }
		// (the distance outside the rectangle, and how much of the way out is a door side's: 1 before a door side, 0 beside a long
		// side, between them round a corner (a switch along the corner's diagonal stood as steps of 2.6 to 7.8 m on a mountain))
		const float Px = FMath::Max(Ex, 0.f), Py = FMath::Max(Ey, 0.f), E = FMath::Sqrt(Px * Px + Py * Py);
		const float Wr = Pd.Kind == 0 ? 1.f : Py <= 0.f ? 1.f : Px <= 0.f ? 0.f : Px / (Px + Py);
		const float Band = FMath::Lerp(0.6f, FMath::Clamp(FMath::Abs(Pd.H - H) * TerraceRampRun, 0.6f, 24.f), Wr);
		if (E >= Band) continue;
		const float Af = E / Band;
		const float W = FMath::Square(1.f - Af) / FMath::Max(Af, 1e-3f);
		Hs += W * FMath::Lerp(Pd.H, H, Af); Ws += W;          // (straight: a smoothstep's middle is 1.5 times its slope)
		Terrace = FMath::Max(Terrace, 1.f - Af);
	}
	if (Ws <= 0.f) return H;
	return FMath::Lerp(H, Hs / Ws, Terrace);
}

// ================================================================================================ the village laid on its pads
void ARDDungeonGenerator::LayTerraceWalls15(ARDWildChunk* C, const FRDWTerraces& T)
{
	// (a retaining wall along a house pad's long sides where the land stands 40 cm or more off it: on its line, from under the lower
	// ground to over the higher (a low parapet where the pad is the higher); a buttress every 4 m on its low side where it is over 1.2 m
	// tall (shallow on the pad's side, so it does not stand in a house). One instanced mesh for the village; each wall recorded
	// (TerraceWallLines15) for the test)
	if (!C || !Wild.IsValid()) return;
	if (!TerraceCube15) TerraceCube15 = LoadObject<UStaticMesh>(nullptr, TEXT("/Engine/BasicShapes/Cube.Cube"));
	if (!TerraceCube15) return;
	UInstancedStaticMeshComponent* Is = NewObject<UInstancedStaticMeshComponent>(C);
	Is->SetStaticMesh(TerraceCube15);
	Is->SetupAttachment(C->Ground.Get());
	if (WildPlinthMaterial) Is->SetMaterial(0, WildPlinthMaterial);
	Is->SetMobility(EComponentMobility::Movable);
	Is->RegisterComponent();
	Is->SetWorldTransform(FTransform::Identity);
	C->PlaceProps.Add(Is);
	int32 Walls = 0, Buttresses = 0;
	for (const FRDWPad& Pd : T.Pads)
	{
		const FVector2D Ax(FMath::Cos(FMath::DegreesToRadians(Pd.Yaw)), FMath::Sin(FMath::DegreesToRadians(Pd.Yaw))), Ay(-Ax.Y, Ax.X);
		for (int32 Side = 0; Side < 4; ++Side)
		{
			// (the walls on a house's long sides; its door sides and the square's are earth ramps (ApplyTerrace))
			if (Pd.Kind == 0 || Side < 2) continue;
			const FVector2D Nrm = Side == 0 ? Ax : Side == 1 ? -Ax : Side == 2 ? Ay : -Ay;
			const FVector2D Tng = Side < 2 ? Ay : Ax;
			const float Hn = Side < 2 ? Pd.Half.X : Pd.Half.Y, Lh = (Side < 2 ? Pd.Half.Y : Pd.Half.X) + 0.3f;
			const float Yaw = FMath::RadiansToDegrees(FMath::Atan2(Tng.Y, Tng.X));
			const int32 Ns = FMath::CeilToInt(2.f * Lh / 2.f);
			const float Seg = 2.f * Lh / Ns;
			for (int32 K = 0; K < Ns; ++K)
			{
				const float U = -Lh + Seg * (K + 0.5f);
				const FVector2D Pe = Pd.C + Nrm * Hn + Tng * U, Po = Pe + Nrm * 1.2f;
				// (the ground as drawn there, past the pad's band: the land with whatever else shapes it (a way's bank by the village))
				const float Nat = Wild->Height(Po.X, Po.Y) - Wild->PortLift(Po.X, Po.Y), D = Pd.H - Nat;
				if (FMath::Abs(D) < 0.4f) continue;
				FRDWSample Sr; Wild->Sample(Po.X, Po.Y, Sr, false);
				if (Sr.Road > 0.1f || Sr.WaterKind != 0) continue;
				const float Lo = FMath::Min(Pd.H, Nat) - 0.6f, Hi = FMath::Max(Pd.H, Nat) + (D > 0.f ? 0.35f : 0.1f);
				const FVector2D Pw = Pe + Nrm * 0.3f;
				// (the drawn ground is the terraces' heights plus the port's lift (PR #99's review: without it the walls stood the lift under it
				// within 40 km of Graymourne))
				const float Lift = Wild->PortLift(Pw.X, Pw.Y);
				const float Zl = Wild->ToZ(Lo + Lift), Zh = Wild->ToZ(Hi + Lift);
				TerraceWallLines15.Add(FString::Printf(TEXT("%d|%.0f|%.0f|%.0f|%.0f|%.0f|%.0f|%.0f|%.0f"), T.VillageId, Pw.X * 100.0, Pw.Y * 100.0, Zl, Zh, Wild->ToZ(Pd.H + Lift), Wild->ToZ(Nat + Lift), Po.X * 100.0, Po.Y * 100.0));
				if (TerraceWallLines15.Num() > 6000) TerraceWallLines15.RemoveAt(0, 1000);
				Is->AddInstance(FTransform(FRotator(0.f, Yaw, 0.f), FVector(Pw.X * 100.0, Pw.Y * 100.0, (Zl + Zh) * 0.5f), FVector(Seg + 0.05f, 0.6f, (Zh - Zl) / 100.f)), true);
				++Walls;
				if (K % 2 == 0 && FMath::Abs(D) > 1.2f)
				{
					const float Depth = D > 0.f ? 0.9f : 0.35f;
					const FVector2D Pb = D > 0.f ? Pe + Nrm * (0.6f + Depth * 0.5f) : Pe - Nrm * (Depth * 0.5f);
					const float Zb = Wild->ToZ(FMath::Min(Pd.H, Nat) + FMath::Abs(D) * 0.85f + Lift);
					Is->AddInstance(FTransform(FRotator(0.f, Yaw, 0.f), FVector(Pb.X * 100.0, Pb.Y * 100.0, (Zl + Zb) * 0.5f), FVector(0.7f, Depth, (Zb - Zl) / 100.f)), true);
					++Buttresses;
				}
			}
		}
	}
	TerraceWalls15 += Walls; TerraceButtresses15 += Buttresses;
	UE_LOG(LogRDList15f, Verbose, TEXT("RDTERRACE15 village %d: %d wall segments, %d buttresses"), T.VillageId, Walls, Buttresses);
}

TArray<FString> ARDDungeonGenerator::GetVillageTerraces15(FVector2D AtM) const
{
	// ("pad|kind|x|y|yaw|halfx|halfy|h" for the village of the place cell at AtM (metres), heights in the game's z (cm))
	TArray<FString> Out;
	if (!Wild.IsValid()) return Out;
	const TSharedPtr<const FRDWTerraces> T = Wild->TerracesAt(AtM.X, AtM.Y);
	if (!T.IsValid()) return Out;
	Out.Add(FString::Printf(TEXT("village|%d|%.1f|%.1f|%.1f"), T->VillageId, T->Mid.X, T->Mid.Y, T->R));
	for (const FRDWPad& Pd : T->Pads)
		Out.Add(FString::Printf(TEXT("pad|%d|%.2f|%.2f|%.1f|%.1f|%.1f|%.1f"), Pd.Kind, Pd.C.X, Pd.C.Y, Pd.Yaw, Pd.Half.X, Pd.Half.Y, Wild->ToZ(Pd.H + Wild->PortLift(Pd.C.X, Pd.C.Y))));
	return Out;
}
