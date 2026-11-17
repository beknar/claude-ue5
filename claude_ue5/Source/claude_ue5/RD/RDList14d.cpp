// The user's list of 2026-11-16 (docs/improvements14.txt; the plan docs/improvements14_plan.md), its fifth phase's second part:
// the alchemist's and librarian's tables in the wilderness (items 2 and 3: "in various places in the wilderness") and the farmsteads'
// ovens (item 15: "ovens to craft food should be available at farms in the wilderness"). Behind the generator's bTables14.
#include "RD/RDDungeonGenerator.h"
#include "RD/RDWild.h"
#include "RD/RDCombat.h"
#include "Components/StaticMeshComponent.h"
#include "Components/HierarchicalInstancedStaticMeshComponent.h"
#include "ProceduralMeshComponent.h"
#include "Engine/StaticMesh.h"
#include "Engine/World.h"
#include "Engine/OverlapResult.h"
#include "GameFramework/Character.h"
#include "Kismet/GameplayStatics.h"
#include "RD/RDTown.h"
DEFINE_LOG_CATEGORY_STATIC(LogRDWildTables14, Log, All);

TArray<FName> ARDDungeonGenerator::WildTablesOf14(const FRDWildPlace& P) const
{
	// (which tables a place has, from a hash of its own id (no draw of the place's streams: every layout stays): a village one in two
	// both; a camp one in three the alchemist's; a witch's hut, a shrine and a structure's village the alchemist's (and the village the
	// librarian's); the abbey's and the temple's ruins the librarian's)
	TArray<FName> T;
	if (!bTables14 || !Wild || P.Poi >= 0 || P.Scenery >= 0) return T;
	const uint32 H = FRDWildWorld::Hash(P.Id, 1414, Wild->Seed);
	const FName A(TEXT("Alchemist")), L(TEXT("Librarian"));
	if (P.Site >= 0)
	{
		if (!WildSiteKinds.IsValidIndex(P.Site)) return T;
		const FName N = WildSiteKinds[P.Site].Name;
		if (N == TEXT("witchhut") || N == TEXT("shrine")) T.Add(A);
		else if (N == TEXT("village") && H % 2 == 0) { T.Add(A); T.Add(L); }
		return T;
	}
	if (P.Kind == TEXT("village") && H % 2 == 0) { T.Add(A); T.Add(L); }
	else if (P.Kind == TEXT("camp") && H % 3 == 0) T.Add(A);
	else if (P.Kind == TEXT("ruins"))
	{
		const int32 K = WildRuinKindOf(P);
		if (WildRuinKinds.IsValidIndex(K) && (WildRuinKinds[K].Name == TEXT("abbey") || WildRuinKinds[K].Name == TEXT("temple"))) T.Add(L);
	}
	return T;
}

bool ARDDungeonGenerator::WildFootLevel14(const FVector& Mid, float Yaw, float Hx, float Hy, float MaxStep, float& Zmin, float& Zmax) const
{
	// (the ground under a footprint's middle and corners: level enough when the highest is within MaxStep of the lowest (cm))
	const FQuat Q = FRotator(0.f, Yaw, 0.f).Quaternion();
	Zmin = 1e9f; Zmax = -1e9f;
	for (const FVector2D& Cn : { FVector2D(0, 0), FVector2D(Hx, Hy), FVector2D(-Hx, Hy), FVector2D(Hx, -Hy), FVector2D(-Hx, -Hy), FVector2D(Hx, 0), FVector2D(-Hx, 0), FVector2D(0, Hy), FVector2D(0, -Hy) })
	{
		const float Z = WildGroundZ(FVector(Mid.X, Mid.Y, 0.0) + Q.RotateVector(FVector(Cn.X, Cn.Y, 0.f)));
		Zmin = FMath::Min(Zmin, Z); Zmax = FMath::Max(Zmax, Z);
	}
	return Zmax - Zmin <= MaxStep;
}

bool ARDDungeonGenerator::WildSpotFree14(const ARDWildChunk* C, const FVector& Center, float Yaw, const FVector& Half) const
{
	// (nothing of its own chunk in the box: the pieces laid and a farm's instances (by an overlap test, the ground, the water and the
	// ground's collision left out), and its plants by their instances' bounds: the chunk's trees and rocks have no collision until she
	// is near (SetWildNear), so an overlap test never saw them (PR #82's review). Only its own chunk's: what a neighbouring chunk holds
	// counted only when that chunk happened to be made, and the table's place would have changed with the order the chunks came in.
	// Small plants (under 80 cm) do not refuse a spot: they are cleared under it (WildClearRect))
	if (!C) return false;
	const FQuat Q = FRotator(0.f, Yaw, 0.f).Quaternion();
	FCollisionObjectQueryParams Ob; Ob.AddObjectTypesToQuery(ECC_WorldStatic); Ob.AddObjectTypesToQuery(ECC_WorldDynamic);
	FCollisionQueryParams Qp(SCENE_QUERY_STAT(RDWildSpotFree14), false);
	if (APawn* Her = UGameplayStatics::GetPlayerPawn(this, 0)) Qp.AddIgnoredActor(Her);
	TArray<FOverlapResult> Hits;
	GetWorld()->OverlapMultiByObjectType(Hits, Center, Q, Ob, FCollisionShape::MakeBox(Half), Qp);
	for (const FOverlapResult& H : Hits)
	{
		const UPrimitiveComponent* Pc = H.GetComponent();
		if (!Pc || Pc->GetOwner() != C || Pc == C->Ground || Pc == C->GroundCollision || Pc == C->WaterMesh) continue;
		return false;
	}
	const FVector Ext(FMath::Abs(Q.RotateVector(FVector(Half.X, 0, 0)).X) + FMath::Abs(Q.RotateVector(FVector(0, Half.Y, 0)).X),
	                  FMath::Abs(Q.RotateVector(FVector(Half.X, 0, 0)).Y) + FMath::Abs(Q.RotateVector(FVector(0, Half.Y, 0)).Y), Half.Z);
	const FBox B(Center - Ext, Center + Ext);
	for (const UHierarchicalInstancedStaticMeshComponent* Hm : C->Foliage)
	{
		if (!Hm || !Hm->GetStaticMesh()) continue;
		const float Mz = (float)Hm->GetStaticMesh()->GetBoundingBox().GetSize().Z;
		for (const int32 I : Hm->GetInstancesOverlappingBox(B, true))
		{
			FTransform It; if (!Hm->GetInstanceTransform(I, It, true)) continue;
			if (Mz * (float)It.GetScale3D().Z >= 80.f) return false;
		}
	}
	return true;
}

void ARDDungeonGenerator::LayWildTables14(ARDWildChunk* C, const FRDWildPlace& P)
{
	if (!C || !C->Ground || !Wild) return;
	const TArray<FName> Want = WildTablesOf14(P);
	if (Want.Num() == 0) return;
	// (each on level, dry ground round the place's middle, clear of what its chunk holds there, its front to the middle, the first
	// of rings of tries from a stream of its own)
	FRandomStream R((int32)FRDWildWorld::Hash(P.Id, 1415, Wild->Seed));
	// (a camp's ring reaches 12 m: in the fens its first 8 m were pools and reeds (888 tables14's Fen Camp had no room))
	const bool bRuin = P.Kind == TEXT("ruins") || P.Site >= 0;
	const float R0 = bRuin ? 3.f : 4.2f, R1 = bRuin ? 16.f : P.Kind == TEXT("camp") ? 12.f : 8.f;          // (metres)
	const FVector O = C->GetActorLocation();
	for (const FName& K : Want)
	{
		const FRDPiece* Pc = Piece(K == TEXT("Alchemist") ? AlchemistPiece : LibrarianPiece);
		if (!Pc || !Pc->Mesh) { UE_LOG(LogRDWildTables14, Warning, TEXT("RDWILDTABLES14 no piece for the %s's table"), *K.ToString()); continue; }
		const float A0 = R.FRandRange(0.f, 360.f);
		bool bLaid = false;
		for (int32 Ring = 0; Ring < 5 && !bLaid; ++Ring)
			for (int32 I = 0; I < 16 && !bLaid; ++I)
			{
				const float Rr = FMath::Lerp(R0, R1, Ring / 4.f), A = FMath::DegreesToRadians(A0 + I * 22.5f + Ring * 11.25f);
				const FVector2D Pm = P.At + FVector2D(FMath::Cos(A), FMath::Sin(A)) * Rr;
				FRDWSample S; Wild->Sample(Pm.X, Pm.Y, S, false);
				if (S.Water > -1e8f || S.Road > 0.3f || S.Lava > 0.1f) continue;
				const float Yaw = FMath::RadiansToDegrees(FMath::Atan2(P.At.Y - Pm.Y, P.At.X - Pm.X));
				const float Hx = (float)Pc->Size.X * 0.5f, Hy = (float)Pc->Size.Y * 0.5f, Hz = (float)Pc->Size.Z * 0.5f;
				const FVector Mid(Pm.X * 100.0, Pm.Y * 100.0, 0.0);
				float Zmin, Zmax;
				if (!WildFootLevel14(Mid, Yaw, Hx, Hy, 25.f, Zmin, Zmax)) continue;
				// (the box from just over the lowest ground up: a fallen stone or a floor slab lower than the highest ground is seen
				// (PR #82's review: from over the highest it was not); the ground itself is left out of the test)
				if (!WildSpotFree14(C, FVector(Mid.X, Mid.Y, Zmin + 4.f + Hz), Yaw, FVector(Hx + 25.f, Hy + 25.f, Hz))) continue;
				// (the table's foot on the ground's middle height; its legs take the rest)
				const FVector Loc(Mid.X, Mid.Y, (Zmin + Zmax) * 0.5f);
				UStaticMeshComponent* Sm = NewObject<UStaticMeshComponent>(C);
				Sm->SetStaticMesh(Pc->Mesh);
				Sm->SetupAttachment(C->Ground);
				Sm->SetRelativeTransform(Pc->Adjust * FTransform(FRotator(0.f, Yaw, 0.f), Loc - O));
				if (Pc->Material) Sm->SetMaterial(0, Pc->Material);
				Sm->RegisterComponent();
				C->PlaceProps.Add(Sm);
				// (no grass through it, nor where she stands to use it (PR #82's review))
				WildClearRect(C, Loc, Yaw, FVector2D(Hx + 120.f, Hy + 30.f), nullptr);
				ARDWildChunk::FStation14 St; St.At = Loc; St.Yaw = Yaw; St.Kind = K; St.Owner = P.Id; St.Comp = Sm;
				C->Stations14.Add(St);
				bLaid = true;
			}
		if (!bLaid) UE_LOG(LogRDWildTables14, Log, TEXT("RDWILDTABLES14 no room for the %s's table at %s (%s)"), *K.ToString(), *P.Name, *P.Kind);
	}
}

bool ARDDungeonGenerator::WildStationNear14(const FVector& From, FVector& At, FName& Kind) const
{
	// (the nearest station of the chunks round her within F's reach, seen from her: the line from her chest to over it meets nothing
	// or the station's own mesh (PR #82's review: any hit within 1.2 m passed, and an oven against a wall answered through it))
	if (!bTables14 || Recipes.Num() == 0) return false;
	float Bd = 230.f; bool bFound = false;
	for (const auto& Kv : WildChunks)
	{
		const ARDWildChunk* C = Kv.Value;
		if (!IsValid(C) || !C->bNear) continue;
		for (const ARDWildChunk::FStation14& S : C->Stations14)
		{
			const float D = FVector::Dist2D(S.At, From);
			if (D >= Bd || FMath::Abs(S.At.Z - From.Z) > 220.f) continue;
			FHitResult Hit;
			FCollisionQueryParams Qp(SCENE_QUERY_STAT(RDWildStation14), false);
			if (APawn* Her = UGameplayStatics::GetPlayerPawn(this, 0)) Qp.AddIgnoredActor(Her);
			const FVector Eye = From + FVector(0, 0, 40.f), Over = S.At + FVector(0, 0, 80.f);
			if (GetWorld()->LineTraceSingleByChannel(Hit, Eye, Over, ECC_Visibility, Qp) && Hit.GetComponent() != S.Comp.Get()) continue;
			Bd = D; At = S.At; Kind = S.Kind; bFound = true;
		}
	}
	return bFound;
}

bool ARDDungeonGenerator::WildStationFirst14(const FVector& From, FName& Kind) const
{
	FVector At;
	if (!WildStationNear14(From, At, Kind)) return false;
	const float Ds = FVector::Dist2D(At, From);
	if (const FSceneryUse* U = WildSceneryUseNear(From); U && FVector::Dist2D(U->At, From) < Ds) return false;
	if (const FRDWildPoiLive* P = WildPoiNear(From, 320.f); P && FVector::Dist2D(P->At, From) < Ds) return false;
	int32 Di = -1;
	if (const ARDWildChunk* C = bWildHouseInsides ? WildDoorNear(From, 190.f, Di) : nullptr; C && C->Doors.IsValidIndex(Di) && FVector::Dist2D(C->Doors[Di].At, From) < Ds) return false;
	if (const ARDTownsfolk* T = WildFolkForF(From); T && FVector::Dist2D(T->GetActorLocation(), From) < Ds) return false;
	return true;
}

FString ARDDungeonGenerator::StationWords14(const FName& Kind)
{
	return Kind == TEXT("Oven") ? FString(TEXT("bake at the oven")) : Kind == TEXT("Alchemist") ? FString(TEXT("use the alchemist's table"))
	     : Kind == TEXT("Librarian") ? FString(TEXT("use the librarian's table")) : FString(TEXT("use the forge"));
}

FString ARDDungeonGenerator::OpenStation14(const FName& Kind)
{
	// (one way to open a station's panel, the towns', dungeons' and wilds' alike: none on a map with no recipes)
	if (!PlayerCombat || Recipes.Num() == 0) return FString();
	PlayerCombat->SetCraftStation(Kind);
	PlayerCombat->SetCraftingOpen(true);
	return Kind == TEXT("Oven") ? TEXT("oven") : Kind == TEXT("Alchemist") ? TEXT("alchemist") : Kind == TEXT("Librarian") ? TEXT("librarian") : Kind.ToString().ToLower();
}

TArray<FString> ARDDungeonGenerator::GetWildStations14() const
{
	TArray<FString> Out;
	for (const auto& Kv : WildChunks)
		if (const ARDWildChunk* C = Kv.Value; IsValid(C))
			for (const ARDWildChunk::FStation14& S : C->Stations14)
				Out.Add(FString::Printf(TEXT("%s|%.0f|%.0f|%.0f|%.0f|%d"), *S.Kind.ToString(), S.At.X, S.At.Y, S.At.Z, S.Yaw, S.Owner));
	return Out;
}

TArray<FString> ARDDungeonGenerator::GetWildTablePlaces14(FVector Near, float RadiusM) const
{
	// "<id>|<kind>|<name>|<x m>|<y m>|<tables>" for the places within RadiusM whose rule gives them tables, and the structures within
	// 15 km of them (SitesIn: PR #82's review, PlacesIn holds none; a structure's cell is worked out with a water search, so the reach
	// is kept short)
	TArray<FString> Out;
	if (!IsWildReady()) return Out;
	const double X = Near.X / 100.0, Y = Near.Y / 100.0;
	const FIntPoint C0 = Wild->PlaceCellOf(X - RadiusM, Y - RadiusM), C1 = Wild->PlaceCellOf(X + RadiusM, Y + RadiusM);
	TArray<FRDWildPlace> Ps;
	for (int32 I = C0.X; I <= C1.X; ++I) for (int32 J = C0.Y; J <= C1.Y; ++J) Wild->PlacesIn(FIntPoint(I, J), Ps);
	const double Rs = FMath::Min((double)RadiusM, 15000.0);
	const FIntPoint S0 = Wild->SiteCellOf(X - Rs, Y - Rs), S1 = Wild->SiteCellOf(X + Rs, Y + Rs);
	TArray<FRDWildPlace> Ss;
	for (int32 I = S0.X; I <= S1.X; ++I) for (int32 J = S0.Y; J <= S1.Y; ++J) Wild->SitesIn(FIntPoint(I, J), Ss);
	for (const FRDWildPlace& Sp : Ss) if (FVector2D::Distance(Sp.At, FVector2D(X, Y)) <= Rs && !Ps.ContainsByPredicate([&Sp](const FRDWildPlace& Q) { return Q.Id == Sp.Id; })) Ps.Add(Sp);
	for (const FRDWildPlace& P : Ps)
	{
		if (FVector2D::Distance(P.At, FVector2D(X, Y)) > RadiusM) continue;
		const TArray<FName> T = WildTablesOf14(P);
		if (T.Num() == 0) continue;
		TArray<FString> Ts; for (const FName& N : T) Ts.Add(N.ToString());
		const FString Kd = P.Site >= 0 && WildSiteKinds.IsValidIndex(P.Site) ? FString::Printf(TEXT("site:%s"), *WildSiteKinds[P.Site].Name.ToString())
		                 : P.Kind == TEXT("ruins") && WildRuinKinds.IsValidIndex(WildRuinKindOf(P)) ? FString::Printf(TEXT("ruins:%s"), *WildRuinKinds[WildRuinKindOf(P)].Name.ToString()) : P.Kind;
		Out.Add(FString::Printf(TEXT("%d|%s|%s|%.0f|%.0f|%s"), P.Id, *Kd, *P.Name, P.At.X, P.At.Y, *FString::Join(Ts, TEXT(","))));
	}
	return Out;
}
