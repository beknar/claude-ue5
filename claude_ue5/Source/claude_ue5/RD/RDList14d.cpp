// The user's list of 2026-11-16 (docs/improvements14.txt; the plan docs/improvements14_plan.md), its fifth phase's second part:
// the alchemist's and librarian's tables in the wilderness (items 2 and 3: "in various places in the wilderness") and the farmsteads'
// ovens (item 15: "ovens to craft food should be available at farms in the wilderness"). Behind the generator's bTables14.
#include "RD/RDDungeonGenerator.h"
#include "RD/RDWild.h"
#include "RD/RDCombat.h"
#include "Components/StaticMeshComponent.h"
#include "ProceduralMeshComponent.h"
#include "Engine/StaticMesh.h"
#include "Engine/World.h"
#include "GameFramework/Character.h"
#include "Kismet/GameplayStatics.h"
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

bool ARDDungeonGenerator::WildBoxFree14(const FVector& Center, float Yaw, const FVector& Half) const
{
	// (nothing solid in the box: the pieces, the farm's instances, the trees (world static and dynamic); her pawn left out)
	FCollisionObjectQueryParams Ob; Ob.AddObjectTypesToQuery(ECC_WorldStatic); Ob.AddObjectTypesToQuery(ECC_WorldDynamic);
	FCollisionQueryParams Qp(SCENE_QUERY_STAT(RDWildBoxFree14), false);
	if (APawn* Her = UGameplayStatics::GetPlayerPawn(this, 0)) Qp.AddIgnoredActor(Her);
	return !GetWorld()->OverlapAnyTestByObjectType(Center, FRotator(0.f, Yaw, 0.f).Quaternion(), Ob, FCollisionShape::MakeBox(Half), Qp);
}

void ARDDungeonGenerator::LayWildTables14(ARDWildChunk* C, const FRDWildPlace& P)
{
	if (!C || !C->Ground || !Wild) return;
	const TArray<FName> Want = WildTablesOf14(P);
	if (Want.Num() == 0) return;
	// (each on level, dry ground round the place's middle, clear of everything laid there (a box overlap), its front to the middle,
	// the first of rings of tries from a stream of its own)
	FRandomStream R((int32)FRDWildWorld::Hash(P.Id, 1415, Wild->Seed));
	const bool bRuin = P.Kind == TEXT("ruins") || P.Site >= 0;
	const float R0 = bRuin ? 3.f : 4.2f, R1 = bRuin ? 16.f : 8.f;          // (metres)
	const FVector O = C->GetActorLocation();
	for (const FName& K : Want)
	{
		const FRDPiece* Pc = Piece(K == TEXT("Alchemist") ? AlchemistPiece : LibrarianPiece);
		if (!Pc || !Pc->Mesh) { UE_LOG(LogRDWildTables14, Warning, TEXT("RDWILDTABLES14 no piece for the %s's table"), *K.ToString()); continue; }
		const float A0 = R.FRandRange(0.f, 360.f);
		bool bLaid = false;
		for (int32 Ring = 0; Ring < 4 && !bLaid; ++Ring)
			for (int32 I = 0; I < 12 && !bLaid; ++I)
			{
				const float Rr = FMath::Lerp(R0, R1, Ring / 3.f), A = FMath::DegreesToRadians(A0 + I * 30.f + Ring * 15.f);
				const FVector2D Pm = P.At + FVector2D(FMath::Cos(A), FMath::Sin(A)) * Rr;
				FRDWSample S; Wild->Sample(Pm.X, Pm.Y, S, false);
				if (S.Water > -1e8f || S.Road > 0.3f || S.Lava > 0.1f) continue;
				const float Yaw = FMath::RadiansToDegrees(FMath::Atan2(P.At.Y - Pm.Y, P.At.X - Pm.X));
				const FQuat Q = FRotator(0.f, Yaw, 0.f).Quaternion();
				const float Hx = (float)Pc->Size.X * 0.5f, Hy = (float)Pc->Size.Y * 0.5f;
				const FVector Mid(Pm.X * 100.0, Pm.Y * 100.0, 0.0);
				float Zmin = 1e9f, Zmax = -1e9f;
				for (const FVector2D& Cn : { FVector2D(0, 0), FVector2D(Hx, Hy), FVector2D(-Hx, Hy), FVector2D(Hx, -Hy), FVector2D(-Hx, -Hy) })
				{
					const float Z = WildGroundZ(Mid + Q.RotateVector(FVector(Cn.X, Cn.Y, 0.f)));
					Zmin = FMath::Min(Zmin, Z); Zmax = FMath::Max(Zmax, Z);
				}
				if (Zmax - Zmin > 25.f) continue;
				const float Hz = (float)Pc->Size.Z * 0.5f;
				if (!WildBoxFree14(FVector(Mid.X, Mid.Y, Zmax + 15.f + Hz), Yaw, FVector(Hx + 25.f, Hy + 25.f, Hz - 5.f))) continue;
				// (the table's foot on the ground's middle height; its legs take the rest)
				const FVector Loc(Mid.X, Mid.Y, (Zmin + Zmax) * 0.5f);
				UStaticMeshComponent* Sm = NewObject<UStaticMeshComponent>(C);
				Sm->SetStaticMesh(Pc->Mesh);
				Sm->SetupAttachment(C->Ground);
				Sm->SetRelativeTransform(Pc->Adjust * FTransform(FRotator(0.f, Yaw, 0.f), Loc - O));
				if (Pc->Material) Sm->SetMaterial(0, Pc->Material);
				Sm->RegisterComponent();
				C->PlaceProps.Add(Sm);
				ARDWildChunk::FStation14 St; St.At = Loc; St.Yaw = Yaw; St.Kind = K; St.Owner = P.Id;
				C->Stations14.Add(St);
				bLaid = true;
			}
		if (!bLaid) UE_LOG(LogRDWildTables14, Log, TEXT("RDWILDTABLES14 no room for the %s's table at %s (%s)"), *K.ToString(), *P.Name, *P.Kind);
	}
}

bool ARDDungeonGenerator::WildStationNear14(const FVector& From, FVector& At, FName& Kind) const
{
	// (the nearest station of the chunks round her within F's reach, seen from her: a table or oven behind a wall is not used (the
	// line from her chest to over it meets nothing but the station itself))
	if (!bTables14) return false;
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
			if (GetWorld()->LineTraceSingleByChannel(Hit, Eye, Over, ECC_Visibility, Qp) && FVector::Dist2D(Hit.Location, S.At) > 120.f) continue;
			Bd = D; At = S.At; Kind = S.Kind; bFound = true;
		}
	}
	return bFound;
}

FString ARDDungeonGenerator::WildStationDescribe14(const FName& Kind) const
{
	return Kind == TEXT("Oven") ? FString(TEXT("bake at the oven")) : Kind == TEXT("Alchemist") ? FString(TEXT("use the alchemist's table")) : FString(TEXT("use the librarian's table"));
}

FString ARDDungeonGenerator::WildStationUse14(const FName& Kind)
{
	if (!PlayerCombat) return FString();
	PlayerCombat->SetCraftStation(Kind);
	PlayerCombat->SetCraftingOpen(true);
	return Kind == TEXT("Oven") ? TEXT("oven") : Kind == TEXT("Alchemist") ? TEXT("alchemist") : TEXT("librarian");
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
	// "<id>|<kind>|<name>|<x m>|<y m>|<tables>" for the places within RadiusM whose rule gives them tables (structures included)
	TArray<FString> Out;
	if (!IsWildReady()) return Out;
	const double X = Near.X / 100.0, Y = Near.Y / 100.0;
	const FIntPoint C0 = Wild->PlaceCellOf(X - RadiusM, Y - RadiusM), C1 = Wild->PlaceCellOf(X + RadiusM, Y + RadiusM);
	TArray<FRDWildPlace> Ps;
	for (int32 I = C0.X; I <= C1.X; ++I) for (int32 J = C0.Y; J <= C1.Y; ++J) Wild->PlacesIn(FIntPoint(I, J), Ps);
	for (const FRDWildPlace& P : Ps)
	{
		if (FVector2D::Distance(P.At, FVector2D(X, Y)) > RadiusM) continue;
		const TArray<FName> T = WildTablesOf14(P);
		if (T.Num() == 0) continue;
		TArray<FString> Ts; for (const FName& N : T) Ts.Add(N.ToString());
		Out.Add(FString::Printf(TEXT("%d|%s|%s|%.0f|%.0f|%s"), P.Id, *P.Kind, *P.Name, P.At.X, P.At.Y, *FString::Join(Ts, TEXT(","))));
	}
	return Out;
}
