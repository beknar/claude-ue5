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

	UInstancedStaticMeshComponent* RDL18bIsm(UObject* Outer, USceneComponent* Parent, UStaticMesh* M)
	{
		UInstancedStaticMeshComponent* H = NewObject<UInstancedStaticMeshComponent>(Outer);
		H->SetStaticMesh(M);
		H->SetMobility(EComponentMobility::Static);
		// (seen and traced by sight, walked through: the window's own collider holds her)
		H->SetCollisionEnabled(ECollisionEnabled::QueryOnly);
		H->SetCollisionResponseToAllChannels(ECR_Ignore);
		H->SetCollisionResponseToChannel(ECC_Visibility, ECR_Block);
		H->SetCullDistances(7000, 9000);
		H->ComponentTags.Add(TEXT("RDBoard18"));
		H->SetupAttachment(Parent);
		H->RegisterComponent();
		return H;
	}
}

bool ARDDungeonGenerator::Windows18On() const { return CVarRDWindows18.GetValueOnGameThread() != 0 && BoardMesh18 != nullptr; }

bool ARDDungeonGenerator::IsGlassWindow18(const ARDSection* S, int32 Bld, FName PieceName) const
{
	if (S && S->TownBlds.IsValidIndex(Bld) && S->TownBlds[Bld].Style >= 7) return true;
	// (a themed name's piece first, as the section's own lookup takes it)
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

void ARDDungeonGenerator::BoardsFor18(const FTransform& Frame, const FBox& Hole, bool bOutside, uint32 Seed, TArray<FTransform>& Out) const
{
	// (the hole in the frame's axes: X out of the wall (Hole.Min.X its inner face, Max.X its outer), Y along it, Z up; rows of planks over it
	// from just under its sill to just over its head, each the opening's width and a little more, a board across them on the outside face)
	if (!BoardMesh18) return;
	const float T = FMath::Max(1.f, (float)BoardSize18.X), L = FMath::Max(10.f, (float)BoardSize18.Y), W = FMath::Max(5.f, (float)BoardSize18.Z);
	const float Y0 = Hole.Min.Y - 8.f, Y1 = Hole.Max.Y + 8.f, Z0 = Hole.Min.Z - 8.f, Z1 = Hole.Max.Z + 8.f;
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
		Add(Xf + Sg * (K % 2) * 0.4f, (Y0 + Y1) * 0.5f + R.FRandRange(-3.f, 3.f), Z0 + Step * (K + 0.5f), R.FRandRange(-1.5f, 1.5f), Wd + 8.f + R.FRandRange(0.f, 8.f), Step * 1.35f);
	// (the brace across, over the rows on this face)
	const float Ang = FMath::RadiansToDegrees(FMath::Atan2(Ht, Wd)) * (R.FRand() < 0.5f ? 1.f : -1.f);
	Add(Xf + Sg * (T + 0.4f), (Y0 + Y1) * 0.5f, (Z0 + Z1) * 0.5f, Ang, FMath::Sqrt(Wd * Wd + Ht * Ht) * 0.92f, W);
}

// ================================================================================================ the towns
void ARDDungeonGenerator::TickBoards18(ARDSection* S)
{
	// (outside, once a town: every window of every closed building but glass, boarded; Windows18 counted for the tests)
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
		for (int32 K = 0; K < Hs.Num(); ++K) BoardsFor18(Wn.Xf, Hs[K], true, HashCombine(GetTypeHash(Wn.At), K), All);
	}
	if (All.Num() == 0) return;
	UInstancedStaticMeshComponent* H = RDL18bIsm(S, S->GetRootComponent(), BoardMesh18);
	for (const FTransform& T : All) H->AddInstance(T, true);
	S->AddInstanceComponent(H);
	Boards18Out = H; Boards18Placed = All.Num();
	UE_LOG(LogRDList18b, Log, TEXT("RDBOARDS18 %d windows boarded with %d boards, %d glass, %d unmeasured"), Boards18Windows, All.Num(), Boards18Glass, Boards18Unmeasured);
}

int32 ARDDungeonGenerator::LayInnerBoards18(ARDSection* S, int32 BI, AActor* A)
{
	// (inside the building's level: its windows but glass, boarded on their inner faces, a board left out where a laid piece of its furniture
	// stands (its box))
	if (!S || !A || !Windows18On()) return 0;
	TArray<FBox> Furn;
	if (const ARDSection::FBldRec17* Rc = S->BldRec17.Find(BI))
		for (const TPair<FString, ARDSection::FBldRecPiece17>& Kv : Rc->Pieces)
			if (Kv.Value.Mesh)
				for (const FTransform& T : Kv.Value.T) Furn.Add(Kv.Value.Mesh->GetBoundingBox().TransformBy(T).ExpandBy(-2.f));
	TArray<FTransform> All; int32 Left = 0;
	for (const ARDSection::FTownWin16& Wn : S->TownWindows16)
	{
		if (Wn.Bld != BI || IsGlassWindow18(S, Wn.Bld, Wn.Piece)) continue;
		TArray<FBox> Hs; HolesOf18(Wn.Piece, Hs);
		for (int32 K = 0; K < Hs.Num(); ++K)
		{
			TArray<FTransform> Bs; BoardsFor18(Wn.Xf, Hs[K], false, HashCombine(GetTypeHash(Wn.At), 1000 + K), Bs);
			for (const FTransform& T : Bs)
			{
				const FBox Bb = BoardMesh18->GetBoundingBox().TransformBy(T);
				if (Furn.ContainsByPredicate([&](const FBox& F) { return F.Intersect(Bb); })) { ++Left; continue; }
				All.Add(T);
			}
		}
	}
	Boards18InnerLeft = Left;
	if (All.Num() == 0) return 0;
	UInstancedStaticMeshComponent* H = RDL18bIsm(A, A->GetRootComponent(), BoardMesh18);
	for (const FTransform& T : All) H->AddInstance(T, true);
	A->AddInstanceComponent(H);
	return All.Num();
}

// ================================================================================================ the wilds
void ARDDungeonGenerator::AddWildBoards18(int32 Ri, const TArray<TPair<FName, FTransform>>& Wins, UStaticMeshComponent* House, TArray<TWeakObjectPtr<UActorComponent>>* Keep)
{
	// (a closed wild building: its windows' boards outside on its chunk, and inside recorded with its furniture (the building level lays them):
	// a kit building's by its window pieces, a village house's by its own mesh's measured openings)
	if (!WildBlds17.IsValidIndex(Ri) || !Windows18On()) return;
	FWildBld17& B = WildBlds17[Ri];
	ARDWildChunk* C = B.C.Get();
	if (!B.bClosed || !C || !C->Ground) return;
	TArray<FTransform> OutB, InB;
	auto Board = [&](const FTransform& Frame, const FBox& Hole, uint32 Seed)
	{
		BoardsFor18(Frame, Hole, true, Seed, OutB);
		BoardsFor18(Frame, Hole, false, Seed + 77u, InB);
		++B.Boarded18;
	};
	for (const TPair<FName, FTransform>& Wn : Wins)
	{
		TArray<FBox> Hs; HolesOf18(Wn.Key, Hs);
		for (int32 K = 0; K < Hs.Num(); ++K) Board(Wn.Value, Hs[K], HashCombine(GetTypeHash(Wn.Value.GetLocation()), K));
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
			Board(FTransform(FRotator(0.f, Yaw, 0.f)) * Hx, Local, HashCombine(GetTypeHash(Hx.GetLocation()), K));
		}
	}
	if (OutB.Num() > 0)
	{
		UInstancedStaticMeshComponent* H = RDL18bIsm(C, C->Ground.Get(), BoardMesh18);
		for (const FTransform& T : OutB) H->AddInstance(T, true);
		if (Keep) Keep->Add(H); else C->PlaceProps.Add(H);
	}
	// (the inside boards laid in the building level with its furniture, not counted as furniture (the record's N is the same in both modes))
	if (InB.Num() > 0)
	{
		FWildPiece17& P = B.Pieces.FindOrAdd(FString::Printf(TEXT("%s|-|0|board18"), *BoardMesh18->GetPathName()));
		P.Mesh = BoardMesh18; P.bCol = false; P.T.Append(InB);
	}
	B.Boards18 = OutB.Num() + InB.Num(); B.Boards18In = InB.Num();
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
	// back): how many rays meet a board, how many meet glass (any other piece), how many meet nothing: "<rays>|<boards>|<other>|<none>")
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
