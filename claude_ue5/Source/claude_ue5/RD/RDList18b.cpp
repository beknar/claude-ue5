// The user's list of 2026-11-27 (docs/improvements18.txt; the plan docs/improvements18_plan.md), its third phase: Closed Structures' windows.
//   "For the Closed Structures game mode, windows will be either opaque and reflective for buildings that have glass like in Heaven, or
//   barricaded entirely both outside and inside."
//   - Glass (Heaven's styles, or a window piece whose own material is glass): nothing covers it. Its glass (MI_HV_Glass: dark, metallic, an
//     8 cm box) is already opaque and reflective, from the street and from the building's level; no room picture outside, no street's cube in.
//   - Every other window of a closed building is boarded over its whole opening, outside and inside: the openings measured once on the window
//     pieces' and village houses' own faces (951 windows: WindowHoles18), planks laid in rows across each (BoardMesh18, a plank of the packs,
//     BoardAdjust18 turning it to the board's frame: thickness X, length Y, width Z), the rows overlapping, and one board across. Outside with
//     the town (one instanced component), or the wild house; inside in the building's own level. The boards stop nothing but sight
//     (Visibility only): the window's own collider holds her, and the inside boards stand in no furniture (left out where a laid piece is).
//   - rd.Windows18 0: list 17's room pictures and street cubes (RDList17e.cpp, RDBuilding17.cpp).
#include "RD/RDDungeonGenerator.h"
#include "RD/RDSection.h"
#include "RD/RDTown.h"
#include "RD/RDWild.h"
#include "Components/InstancedStaticMeshComponent.h"
#include "Engine/StaticMesh.h"
#include "HAL/IConsoleManager.h"
#include "Kismet/GameplayStatics.h"
#include "ProceduralMeshComponent.h"
DEFINE_LOG_CATEGORY_STATIC(LogRDList18b, Log, All);

namespace
{
	TAutoConsoleVariable<int32> CVarRDWindows18(TEXT("rd.Windows18"), 1, TEXT("Closed Structures' windows: glass left as it is and every other window boarded outside and in (1), or list 17's room pictures and street views (0); a town or house laid after the change"));

	TAutoConsoleVariable<int32> CVarRDBoards18Trace(TEXT("rd.Boards18Trace"), 0, TEXT("Tests: Closed Structures' boards take sight traces (1; they have no collision in play: the windows' own colliders stop her and sight); boards laid after the change"));

	UInstancedStaticMeshComponent* RDL18bIsm(UObject* Outer, USceneComponent* Parent, UStaticMesh* M, const TArray<FTransform>& Xs)
	{
		// (PR #148's review: no collision (each window piece's hidden box already stops her and sight; 24,000 bodies made in one frame for
		// nothing), no shadow, the instances added before the component is registered)
		UInstancedStaticMeshComponent* H = NewObject<UInstancedStaticMeshComponent>(Outer);
		H->SetStaticMesh(M);
		H->SetMobility(EComponentMobility::Static);
		if (CVarRDBoards18Trace.GetValueOnGameThread() != 0)
		{
			H->SetCollisionEnabled(ECollisionEnabled::QueryOnly);
			H->SetCollisionResponseToAllChannels(ECR_Ignore);
			H->SetCollisionResponseToChannel(ECC_Visibility, ECR_Block);
		}
		else H->SetCollisionEnabled(ECollisionEnabled::NoCollision);
		H->SetCastShadow(false);
		H->SetCullDistances(7000, 9000);
		H->ComponentTags.Add(TEXT("RDBoard18"));
		H->SetupAttachment(Parent);
		// (the world's places made the parent's own before the component is registered: an unregistered component does not know where it is,
		// and taken as world places the boards stood off by the section's own place (w18f))
		const FTransform Pw = Parent ? Parent->GetComponentTransform() : FTransform::Identity;
		TArray<FTransform> Local; Local.Reserve(Xs.Num());
		for (const FTransform& X : Xs) Local.Add(X.GetRelativeTransform(Pw));
		H->AddInstances(Local, false, false);
		H->RegisterComponent();
		return H;
	}
	/** a piece's box in its own frame and where it stands, for a board's overlap */
	struct FRDL18bSolid { FBox Local; FTransform T; };
	/** a board standing in a piece: three or more of its middle line's five points inside one piece's own turned box (drawn in 2 cm). A board
	 *  that only touches a piece's box is kept: left out for any point, a corner in a shelf's box left the window behind it open (w18f) */
	bool RDL18bInSolid(const FBox& Board, const FTransform& T, const TArray<FRDL18bSolid>& Solids)
	{
		const FVector C = Board.GetCenter(), E = Board.GetExtent();
		TArray<FVector, TInlineAllocator<5>> Pts;
		for (int32 K = -2; K <= 2; ++K) Pts.Add(T.TransformPosition(C + FVector(0.f, E.Y * K * 0.45f, 0.f)));
		for (const FRDL18bSolid& S : Solids)
		{
			const FBox In = S.Local.ExpandBy(-2.f);
			int32 N = 0;
			for (const FVector& P : Pts) if (In.IsInside(S.T.InverseTransformPosition(P))) ++N;
			if (N >= 3) return true;
		}
		return false;
	}
}

bool ARDDungeonGenerator::Windows18On() const { return CVarRDWindows18.GetValueOnGameThread() != 0 && BoardMesh18 != nullptr; }

bool ARDDungeonGenerator::IsGlassWindow18(const ARDSection* S, int32 Bld, FName PieceName) const
{
	if (S && S->TownBlds.IsValidIndex(Bld) && S->TownBlds[Bld].Style >= 7) return true;
	// (the window piece by its name as laid: a theme's own window is laid under its themed name)
	const FRDPiece* P = Piece(PieceName);
	if (P && P->Mesh)
		for (const FStaticMaterial& Sm : P->Mesh->GetStaticMaterials())
			if (Sm.MaterialInterface && Sm.MaterialInterface->GetName().Contains(TEXT("Glass"))) return true;
	return false;
}

void ARDDungeonGenerator::HolesOf18(FName Key, TArray<FBox>& Out, TArray<int32>* Sides) const
{
	for (const FRDWindowHole18& H : WindowHoles18) if (H.Key == Key) { Out.Add(H.Box); if (Sides) Sides->Add(H.Side); }
}

void ARDDungeonGenerator::BoardsFor18(const FTransform& Frame, const FBox& Hole, bool bOutside, uint32 Seed, TArray<FTransform>& Out, float MarginL, float MarginR) const
{
	// (the hole in the frame's axes: X out of the wall (Hole.Min.X its inner face, Max.X its outer), Y along it, Z up; rows of planks over it
	// from just under its sill to just over its head, each the opening's width and a little more, a board across them on the outside face)
	if (!BoardMesh18) return;
	const float T = FMath::Max(1.f, (float)BoardSize18.X), L = FMath::Max(10.f, (float)BoardSize18.Y), W = FMath::Max(5.f, (float)BoardSize18.Z);
	// (past the opening by 8 cm on each side, or by less toward a neighbouring opening of the same piece: half the mullion (PR #148's review:
	// two-light windows' rows met in their 8 cm mullion))
	const float Y0 = Hole.Min.Y - MarginL, Y1 = Hole.Max.Y + MarginR, Z0 = Hole.Min.Z - 8.f, Z1 = Hole.Max.Z + 8.f;
	const float Jit = FMath::Min(3.f, FMath::Min(MarginL, MarginR) * 0.4f);
	const float Wd = Y1 - Y0, Ht = Z1 - Z0;
	if (Wd <= 0.f || Ht <= 0.f) return;
	const float Xf = bOutside ? Hole.Max.X + T * 0.5f + 0.5f : Hole.Min.X - T * 0.5f - 0.5f;
	const float Sg = bOutside ? 1.f : -1.f;
	FRandomStream R((int32)Seed);
	const int32 N = FMath::Max(1, FMath::CeilToInt(Ht / (W * 0.9f)));
	const float Step = Ht / N;
	const FMatrix Fm = Frame.ToMatrixWithScale(), Am = BoardAdjust18.ToMatrixWithScale();
	auto Add = [&](float X, float Y, float Z, float Roll, float Len, float Wid)
	{
		const FTransform Loc(FRotator(0.f, 0.f, Roll), FVector(X, Y, Z), FVector(1.f, Len / L, Wid / W));
		Out.Add(FTransform(Am * Loc.ToMatrixWithScale() * Fm));
	};
	for (int32 K = 0; K < N; ++K)
		// (overlapping by a third: a row tilted 1.5 degrees over a metre and more of opening lifts its ends 2 to 3 cm, and at 12 % (w18a) 1 % of
		// the rays through the openings passed between two rows)
		Add(Xf + Sg * (K % 2) * 0.4f, (Y0 + Y1) * 0.5f + R.FRandRange(-Jit, Jit), Z0 + Step * (K + 0.5f), R.FRandRange(-1.5f, 1.5f), Wd + 2.f * Jit, Step * 1.35f);
	// (the brace across, over the rows on this face)
	const float Ang = FMath::RadiansToDegrees(FMath::Atan2(Ht, Wd)) * (R.FRand() < 0.5f ? 1.f : -1.f);
	Add(Xf + Sg * (T + 0.4f), (Y0 + Y1) * 0.5f, (Z0 + Z1) * 0.5f, Ang, FMath::Sqrt(Wd * Wd + Ht * Ht) * 0.92f, W);
}

// ================================================================================================ the towns
namespace
{
	// (how far a piece's opening's boards reach past its sides: 8 cm, or less toward a neighbouring opening of the same piece (half the mullion))
	void RDL18bMargins(const TArray<FBox>& Hs, int32 K, float& L, float& R)
	{
		L = R = 8.f;
		for (int32 J = 0; J < Hs.Num(); ++J)
		{
			if (J == K || Hs[J].Max.Z < Hs[K].Min.Z || Hs[J].Min.Z > Hs[K].Max.Z) continue;
			if (Hs[J].Max.Y <= Hs[K].Min.Y) L = FMath::Min(L, FMath::Max(0.5f, (float)(Hs[K].Min.Y - Hs[J].Max.Y) * 0.5f - 0.5f));
			if (Hs[J].Min.Y >= Hs[K].Max.Y) R = FMath::Min(R, FMath::Max(0.5f, (float)(Hs[J].Min.Y - Hs[K].Max.Y) * 0.5f - 0.5f));
		}
	}
}

void ARDDungeonGenerator::BoardsOfHoles18(const FTransform& Frame, const TArray<FBox>& Hs, bool bOutside, uint32 Seed, TArray<FTransform>& Out) const
{
	for (int32 K = 0; K < Hs.Num(); ++K)
	{
		float L, R; RDL18bMargins(Hs, K, L, R);
		BoardsFor18(Frame, Hs[K], bOutside, HashCombine(Seed, (uint32)K), Out, L, R);
	}
}

int32 ARDDungeonGenerator::FilterBoards18(TArray<FTransform>& Boards, const TArray<TPair<UStaticMesh*, FTransform>>& Laid) const
{
	// (a board left out where it would stand in a piece of the room's furniture (that piece's own turned box), the boards' own pieces passed by)
	if (!BoardMesh18 || Boards.Num() == 0) return 0;
	TArray<FRDL18bSolid> Solids;
	for (const TPair<UStaticMesh*, FTransform>& P : Laid) if (P.Key && P.Key != BoardMesh18) Solids.Add({ P.Key->GetBoundingBox(), P.Value });
	const FBox Bb = BoardMesh18->GetBoundingBox();
	const int32 N0 = Boards.Num();
	Boards.RemoveAll([&](const FTransform& T) { return RDL18bInSolid(Bb, T, Solids); });
	return N0 - Boards.Num();
}

void ARDDungeonGenerator::SyncWindowModes18()
{
	// (rd.Windows18 changed in play (PR #148's review): the other way's pieces hidden, not left standing under the new way's; the counters of a
	// town no longer closed let go)
	const bool bOn = Windows18On();
	if (bOn && bPanes17Shown && Panes17.Num() > 0)
	{
		for (const TWeakObjectPtr<UInstancedStaticMeshComponent>& W : Panes17) if (UInstancedStaticMeshComponent* C = W.Get()) C->SetVisibility(false);
		bPanes17Shown = false; Panes17For = nullptr;
	}
	if (!bOn && Boards18Out.IsValid()) { Boards18Out->SetVisibility(false); Boards18Out = nullptr; Boards18For = nullptr; }
	ARDSection* S = GetSection(FIntPoint::ZeroValue);
	if (Boards18For.IsValid() && (Boards18For.Get() != S || !S->BldClosed17))
	{
		Boards18For = nullptr; Boards18Out = nullptr; Boards18Windows = 0; Boards18Glass = 0; Boards18Unmeasured = 0; Boards18Placed = 0;
	}
}

void ARDDungeonGenerator::TickBoards18(ARDSection* S)
{
	// (outside, once a town: every window of every closed building but glass, boarded; Windows18 counted for the tests)
	SyncWindowModes18();
	if (!S || S->IsBuilding() || !S->BldClosed17 || !Windows18On()) return;
	if (Boards18For.Get() == S) return;
	Boards18For = S; Boards18Out = nullptr; Boards18Windows = 0; Boards18Glass = 0; Boards18Unmeasured = 0; Boards18Placed = 0;
	TArray<FTransform> All;
	for (const ARDSection::FTownWin16& Wn : S->TownWindows16)
	{
		if (!S->HasRecord17(Wn.Bld)) continue;
		if (IsGlassWindow18(S, Wn.Bld, Wn.Piece)) { ++Boards18Glass; continue; }
		++Boards18Windows;
		TArray<FBox> Hs; HolesOf18(Wn.Piece, Hs);
		if (Hs.Num() == 0) { ++Boards18Unmeasured; continue; }
		BoardsOfHoles18(Wn.Xf, Hs, true, GetTypeHash(Wn.At), All);
	}
	if (All.Num() == 0) return;
	UInstancedStaticMeshComponent* H = RDL18bIsm(S, S->GetRootComponent(), BoardMesh18, All);
	S->AddInstanceComponent(H);
	Boards18Out = H; Boards18Placed = All.Num();
	UE_LOG(LogRDList18b, Log, TEXT("RDBOARDS18 %d windows boarded with %d boards, %d glass, %d unmeasured"), Boards18Windows, All.Num(), Boards18Glass, Boards18Unmeasured);
}

int32 ARDDungeonGenerator::LayInnerBoards18(ARDSection* S, int32 BI, AActor* A)
{
	// (inside the building's level: its windows but glass, boarded on their inner faces, a board left out where it would stand in a laid
	// piece of its furniture)
	Boards18InnerLeft = 0;
	if (!S || !A || !Windows18On()) return 0;
	TArray<TPair<UStaticMesh*, FTransform>> Furn;
	if (const ARDSection::FBldRec17* Rc = S->BldRec17.Find(BI))
		for (const TPair<FString, ARDSection::FBldRecPiece17>& Kv : Rc->Pieces)
			for (const FTransform& T : Kv.Value.T) Furn.Add(TPair<UStaticMesh*, FTransform>(const_cast<UStaticMesh*>(ToRawPtr(Kv.Value.Mesh)), T));
	TArray<FTransform> All;
	for (const ARDSection::FTownWin16& Wn : S->TownWindows16)
	{
		if (Wn.Bld != BI || IsGlassWindow18(S, Wn.Bld, Wn.Piece)) continue;
		TArray<FBox> Hs; HolesOf18(Wn.Piece, Hs);
		BoardsOfHoles18(Wn.Xf, Hs, false, HashCombine(GetTypeHash(Wn.At), 1000u), All);
	}
	Boards18InnerLeft = FilterBoards18(All, Furn);
	if (All.Num() == 0) return 0;
	UInstancedStaticMeshComponent* H = RDL18bIsm(A, A->GetRootComponent(), BoardMesh18, All);
	A->AddInstanceComponent(H);
	return All.Num();
}

// ================================================================================================ the wilds
void ARDDungeonGenerator::AddWildBoards18(int32 Ri, const TArray<TPair<FName, FTransform>>& Wins, UStaticMeshComponent* House, TArray<TWeakObjectPtr<UActorComponent>>* Keep)
{
	// (a closed wild building: its windows' boards outside on its chunk, and inside recorded apart from its furniture (the building level lays
	// them, leaving out any that would stand in its furniture): a kit building's by its window pieces, a village house's by its own mesh's
	// measured openings)
	if (!WildBlds17.IsValidIndex(Ri) || !Windows18On()) return;
	FWildBld17& B = WildBlds17[Ri];
	ARDWildChunk* C = B.C.Get();
	if (!B.bClosed || !C || !C->Ground) return;
	TArray<FTransform> OutB, InB;
	for (const TPair<FName, FTransform>& Wn : Wins)
	{
		TArray<FBox> Hs; HolesOf18(Wn.Key, Hs);
		if (Hs.Num() == 0) continue;
		const uint32 Sd = GetTypeHash(Wn.Value.GetLocation());
		BoardsOfHoles18(Wn.Value, Hs, true, Sd, OutB);
		BoardsOfHoles18(Wn.Value, Hs, false, Sd + 77u, InB);
		++B.Boarded18;
	}
	if (House && House->GetStaticMesh())
	{
		// (a house mesh's openings are in its own frame on a side: turned so that side's way out is X (+X, -X, +Y, -Y as 1 to 4), the face
		// at the opening's X)
		TArray<FBox> Hs; TArray<int32> Sides;
		HolesOf18(FName(*House->GetStaticMesh()->GetPathName()), Hs, &Sides);
		const FTransform Hx = House->GetComponentTransform();
		for (int32 K = 0; K < Hs.Num(); ++K)
		{
			const float Yaw = Sides[K] == 1 ? 0.f : Sides[K] == 2 ? 180.f : Sides[K] == 3 ? 90.f : -90.f;
			// (the side's frame: its face's plane through the mesh's origin turned to the side; the hole's U along the frame's Y)
			const FBox& Hb = Hs[K];
			const bool bNeg = Sides[K] == 2 || Sides[K] == 4;
			// (Box's X: the reveal's two faces along the side's axis in the mesh's frame; in the side's frame the outer is the larger)
			const float Xa = (float)Hb.Min.X * (bNeg ? -1.f : 1.f), Xb = (float)Hb.Max.X * (bNeg ? -1.f : 1.f);
			// (on the -X and +Y sides the frame's Y runs against the mesh's U: the hole's U range mirrored)
			const bool bFlip = Sides[K] == 2 || Sides[K] == 3;
			const float U0 = bFlip ? -(float)Hb.Max.Y : (float)Hb.Min.Y, U1 = bFlip ? -(float)Hb.Min.Y : (float)Hb.Max.Y;
			const FBox Local(FVector(FMath::Min(Xa, Xb), U0, Hb.Min.Z), FVector(FMath::Max(Xa, Xb), U1, Hb.Max.Z));
			const FTransform Fr = FTransform(FRotator(0.f, Yaw, 0.f)) * Hx;
			const uint32 Sd = HashCombine(GetTypeHash(Hx.GetLocation()), (uint32)K);
			BoardsFor18(Fr, Local, true, Sd, OutB);
			BoardsFor18(Fr, Local, false, Sd + 77u, InB);
			++B.Boarded18;
		}
	}
	if (OutB.Num() > 0)
	{
		UInstancedStaticMeshComponent* H = RDL18bIsm(C, C->Ground.Get(), BoardMesh18, OutB);
		if (Keep) Keep->Add(H); else C->PlaceProps.Add(H);
	}
	// (the inside boards apart from the furniture (the record's N is the same in both modes), laid in the building level with it)
	B.Boards18InT = MoveTemp(InB);
	B.Boards18 = OutB.Num() + B.Boards18InT.Num(); B.Boards18In = B.Boards18InT.Num();
}
// ================================================================================================ the tests
TArray<FString> ARDDungeonGenerator::GetWindows18() const
{
	// (tests: "<building>|<style>|<glass>|<piece>|<holes>|<x>|<y>|<z>|<out x>|<out y>" a window of a closed building of the town)
	TArray<FString> Out;
	const ARDSection* S = const_cast<ARDDungeonGenerator*>(this)->GetSection(FIntPoint::ZeroValue);
	if (!S) return Out;
	for (const ARDSection::FTownWin16& Wn : S->TownWindows16)
	{
		if (!S->HasRecord17(Wn.Bld)) continue;
		TArray<FBox> Hs; HolesOf18(Wn.Piece, Hs);
		Out.Add(FString::Printf(TEXT("%d|%d|%d|%s|%d|%.0f|%.0f|%.0f|%.3f|%.3f"), Wn.Bld, S->TownBlds.IsValidIndex(Wn.Bld) ? S->TownBlds[Wn.Bld].Style : -1,
			IsGlassWindow18(S, Wn.Bld, Wn.Piece) ? 1 : 0, *Wn.Piece.ToString(), Hs.Num(), Wn.At.X, Wn.At.Y, Wn.At.Z, Wn.Out.X, Wn.Out.Y));
	}
	return Out;
}

FString ARDDungeonGenerator::TraceWindow18(int32 Index, bool bFromOutside, int32 Grid) const
{
	// (tests: the closed building's Index-th window's openings, each on a Grid x Grid of points, traced from 40 cm outside to 40 cm inside (or
	// back): how many rays meet a board of that side's layer, how many meet anything else, how many meet nothing: "<rays>|<boards>|<other>|<none>".
	// Only the side's own layer is traced (PR #148's review: from inside, the outside boards behind made every ray "a board"); the boards take
	// traces only with rd.Boards18Trace 1)
	const ARDSection* S = const_cast<ARDDungeonGenerator*>(this)->GetSection(FIntPoint::ZeroValue);
	UWorld* Wd = GetWorld();
	if (!S || !Wd) return FString();
	int32 I = -1;
	for (const ARDSection::FTownWin16& Wn : S->TownWindows16)
	{
		if (!S->HasRecord17(Wn.Bld)) continue;
		if (++I != Index) continue;
		TArray<FBox> Hs; HolesOf18(Wn.Piece, Hs);
		int32 Rays = 0, Board = 0, Other = 0, None = 0;
		FCollisionQueryParams Q(SCENE_QUERY_STAT(RDTraceWindow18), true);
		if (APawn* P = UGameplayStatics::GetPlayerPawn(Wd, 0)) Q.AddIgnoredActor(P);
		// (the windows' hidden colliders (a box over each window piece's bounds) stand in every ray: left out, the boards and the pieces are met)
		if (const FRDPiece* Cp = Piece(TEXT("Town.Collider")); Cp && Cp->Mesh)
		{
			TInlineComponentArray<UInstancedStaticMeshComponent*> Is(S);
			for (UInstancedStaticMeshComponent* C : Is) if (C && C->GetStaticMesh() == Cp->Mesh) Q.AddIgnoredComponent(C);
		}
		if (bFromOutside) { if (AActor* Ba = BuildingActor17.Get()) Q.AddIgnoredActor(Ba); }
		else if (UInstancedStaticMeshComponent* Ob = Boards18Out.Get()) Q.AddIgnoredComponent(Ob);
		for (const FBox& H : Hs)
			for (int32 A = 0; A < Grid; ++A)
				for (int32 B = 0; B < Grid; ++B)
				{
					const float Y = FMath::Lerp((float)H.Min.Y + 3.f, (float)H.Max.Y - 3.f, (A + 0.5f) / Grid), Z = FMath::Lerp((float)H.Min.Z + 3.f, (float)H.Max.Z - 3.f, (B + 0.5f) / Grid);
					const FVector Po = Wn.Xf.TransformPosition(FVector(H.Max.X + 40.f, Y, Z)), Pi = Wn.Xf.TransformPosition(FVector(H.Min.X - 40.f, Y, Z));
					FHitResult Hit; ++Rays;
					if (!Wd->LineTraceSingleByChannel(Hit, bFromOutside ? Po : Pi, bFromOutside ? Pi : Po, ECC_Visibility, Q)) { ++None; continue; }
					const UPrimitiveComponent* Hc = Hit.GetComponent();
					if (Hc && Hc->ComponentHasTag(TEXT("RDBoard18"))) ++Board; else ++Other;
				}
		return FString::Printf(TEXT("%d|%d|%d|%d"), Rays, Board, Other, None);
	}
	return FString();
}

FString ARDDungeonGenerator::GetBoards18State() const
{
	// (tests: "<windows boarded>|<glass>|<unmeasured>|<outside boards>|<inside boards in her building>|<inside boards left out>|<on>")
	return FString::Printf(TEXT("%d|%d|%d|%d|%d|%d|%d"), Boards18Windows, Boards18Glass, Boards18Unmeasured, Boards18Placed, Building17Boards18, Boards18InnerLeft, Windows18On() ? 1 : 0);
}
