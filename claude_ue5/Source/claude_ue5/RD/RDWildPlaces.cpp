// The wilderness's places of interest (the user's spec of 2026-11-03: "villages, towns, major cities, camps, lone houses in the
// wilderness, spawn points, ruins, ancient ritual sites, caves, monster lairs"): FRDWildWorld::PlacesIn says where each is and
// what; a chunk lays its places' props when it is made (components of the chunk: they go with it) from the generator's
// WildPieces, taken by prefix ("house1", "house2", ...), each laid out after its kind; spawn points and lairs have monsters of
// their tier (RDMonster's open-ground mode: no tile grid out here).
#include "RD/RDDungeonGenerator.h"
#include "RD/RDWild.h"
#include "RD/RDMonster.h"
#include "RD/RDSection.h"
#include "RD/RDGameInstance.h"
#include "Components/StaticMeshComponent.h"
#include "ProceduralMeshComponent.h"
#include "Engine/StaticMesh.h"
#include "NiagaraComponent.h"
#include "NiagaraFunctionLibrary.h"
#include "NiagaraSystem.h"

DEFINE_LOG_CATEGORY_STATIC(LogRDWildPlace, Log, All);

void ARDDungeonGenerator::WildPiecesOf(const FString& Prefix, TArray<UStaticMesh*>& Out) const
{
	Out.Reset();
	for (const auto& Kv : WildPieces)
		if (Kv.Value && Kv.Key.ToString().StartsWith(Prefix)) Out.Add(Kv.Value);
	Out.Sort([](const UStaticMesh& A, const UStaticMesh& B) { return A.GetName() < B.GetName(); });
}

void ARDDungeonGenerator::SpawnWildPlaces(ARDWildChunk* C, const TArray<FRDWildPlace>& Places)
{
	if (!C || !IsWildReady()) return;
	for (const FRDWildPlace& P : Places)
	{
		FRandomStream R((int32)FRDWildWorld::Hash(P.Id, 77, Wild->Seed));
		const FVector O = C->GetActorLocation();
		int32 Laid = 0;
		// one prop: a piece of the kind (by prefix), at a point (world metres), turned, sunk, scaled
		auto Put = [&](const FString& Prefix, const FVector2D& At, float Yaw, float Scale = 1.f, float Sink = 10.f, bool bCollide = true) -> UStaticMeshComponent*
		{
			TArray<UStaticMesh*> Ms; WildPiecesOf(Prefix, Ms);
			if (Ms.Num() == 0) return nullptr;
			UStaticMesh* M = Ms[R.RandRange(0, Ms.Num() - 1)];
			const float* Ks = WildPieceScale.Find(FName(*M->GetName()));
			const float Sc = Scale * (Ks ? *Ks : 1.f);
			const float Z = WildGroundZ(FVector(At.X * 100.0, At.Y * 100.0, 0.0));
			UStaticMeshComponent* Sm = NewObject<UStaticMeshComponent>(C);
			Sm->SetStaticMesh(M);
			Sm->SetupAttachment(C->Ground);
			Sm->SetRelativeLocation(FVector(At.X * 100.0, At.Y * 100.0, Z - Sink * Sc) - O);
			Sm->SetRelativeRotation(FRotator(0.f, Yaw, 0.f));
			Sm->SetRelativeScale3D(FVector(Sc));
			if (!bCollide) Sm->SetCollisionEnabled(ECollisionEnabled::NoCollision);
			Sm->RegisterComponent();
			C->PlaceProps.Add(Sm);
			++Laid;
			return Sm;
		};
		auto Ring = [&](int32 N, float Rr, float Jit, TFunctionRef<void(const FVector2D&, float)> Each)
		{
			const float A0 = R.FRandRange(0.f, 360.f);
			for (int32 I = 0; I < N; ++I)
			{
				const float A = FMath::DegreesToRadians(A0 + I * 360.f / N + R.FRandRange(-Jit, Jit));
				const FVector2D At = P.At + FVector2D(FMath::Cos(A), FMath::Sin(A)) * (Rr + R.FRandRange(-1.5f, 1.5f));
				Each(At, FMath::RadiansToDegrees(A) + 180.f);      // (facing the middle)
			}
		};
		if (P.Kind == TEXT("village"))
		{
			Ring(R.RandRange(4, 7), R.FRandRange(18.f, 26.f), 14.f, [&](const FVector2D& At, float Yaw) { Put(TEXT("house"), At, Yaw, 1.f, 25.f); });
			Put(TEXT("well"), P.At, R.FRandRange(0.f, 360.f));
			Ring(3, 9.f, 25.f, [&](const FVector2D& At, float Yaw) { Put(TEXT("hay"), At, Yaw + R.FRandRange(-40.f, 40.f), 1.f, 5.f); });
			Put(TEXT("cart"), P.At + FVector2D(6.f, -5.f), R.FRandRange(0.f, 360.f));
		}
		else if (P.Kind == TEXT("camp"))
		{
			Ring(R.RandRange(2, 4), 7.f, 20.f, [&](const FVector2D& At, float Yaw) { Put(TEXT("tent"), At, Yaw, 1.f, 5.f); });
			if (UStaticMeshComponent* F = Put(TEXT("campfire"), P.At, 0.f, 1.f, 2.f, false))
				if (WildFireFx) UNiagaraFunctionLibrary::SpawnSystemAttached(WildFireFx, F, NAME_None, FVector(0, 0, 25.f), FRotator::ZeroRotator, EAttachLocation::KeepRelativeOffset, true);
			Ring(3, 3.2f, 15.f, [&](const FVector2D& At, float Yaw) { Put(TEXT("log"), At, Yaw + 90.f, 1.f, 3.f); });
		}
		else if (P.Kind == TEXT("house"))
		{
			Put(TEXT("house"), P.At, P.Yaw, 1.f, 25.f);
			Put(TEXT("fence"), P.At + FVector2D(9.f, 0.f), P.Yaw + 90.f, 1.f, 5.f);
			Put(TEXT("fence"), P.At + FVector2D(-9.f, 3.f), P.Yaw + 90.f, 1.f, 5.f);
			Put(TEXT("hay"), P.At + FVector2D(4.f, 9.f), P.Yaw, 1.f, 5.f);
		}
		else if (P.Kind == TEXT("spawn"))
		{
			Put(TEXT("totem"), P.At, P.Yaw, 1.f, 10.f);
			Ring(6, 5.f, 20.f, [&](const FVector2D& At, float Yaw) { Put(TEXT("bones"), At, Yaw + R.FRandRange(0.f, 360.f), 1.f, 2.f, false); });
		}
		else if (P.Kind == TEXT("ruins"))
		{
			for (int32 I = 0, N = R.RandRange(4, 7); I < N; ++I)
			{
				const float A = R.FRandRange(0.f, 2.f * PI), D = R.FRandRange(2.f, 13.f);
				Put(TEXT("ruin"), P.At + FVector2D(FMath::Cos(A), FMath::Sin(A)) * D, P.Yaw + 90.f * R.RandRange(0, 3) + R.FRandRange(-8.f, 8.f), 1.f, 30.f);
			}
		}
		else if (P.Kind == TEXT("ritual"))
		{
			Ring(R.RandRange(7, 9), 7.5f, 4.f, [&](const FVector2D& At, float Yaw) { Put(TEXT("stone"), At, Yaw, R.FRandRange(0.9f, 1.15f), 20.f); });
			Put(TEXT("altar"), P.At, P.Yaw, 1.f, 8.f);
		}
		else if (P.Kind == TEXT("cave"))
		{
			Put(TEXT("cave"), P.At, P.Yaw, 1.f, 60.f);
			Ring(4, 9.f, 30.f, [&](const FVector2D& At, float Yaw) { Put(TEXT("rock"), At, Yaw + R.FRandRange(0.f, 360.f), R.FRandRange(0.7f, 1.3f), 40.f); });
		}
		else if (P.Kind == TEXT("lair"))
		{
			Put(TEXT("skeleton"), P.At, P.Yaw, 1.f, 5.f, false);
			Ring(R.RandRange(6, 9), 6.f, 25.f, [&](const FVector2D& At, float Yaw) { Put(TEXT("bones"), At, Yaw + R.FRandRange(0.f, 360.f), 1.f, 2.f, false); });
			Ring(10, 3.f, 10.f, [&](const FVector2D& At, float Yaw) { Put(TEXT("branch"), At, Yaw + 90.f + R.FRandRange(-20.f, 20.f), 1.f, 3.f, false); });
		}
		// (the caldera's hot springs steam: their places are the world's ponds of kind 6, laid by the chunk's water)
		if (P.Kind == TEXT("spawn") || P.Kind == TEXT("lair")) SpawnWildMonsters(C, P);
		UE_LOG(LogRDWildPlace, Verbose, TEXT("RDWILD %s (%s): %d props"), *P.Name, *P.Kind, Laid);
	}
}

ARDSection* ARDDungeonGenerator::EnsureWildSection()
{
	if (WildSection) return WildSection;
	FActorSpawnParameters Sp; Sp.SpawnCollisionHandlingOverride = ESpawnActorCollisionHandlingMethod::AlwaysSpawn;
	WildSection = GetWorld()->SpawnActor<ARDSection>(ARDSection::StaticClass(), FTransform(FVector(0, 0, -100000.f)), Sp);
	if (WildSection) { WildSection->Generator = this; WildSection->Coord = FIntPoint(1 << 16, 1 << 16); }
	return WildSection;
}

void ARDDungeonGenerator::SpawnWildMonsters(ARDWildChunk* C, const FRDWildPlace& P)
{
	if (!bCombat || Monsters.Num() == 0) return;
	ARDSection* Ws = EnsureWildSection();
	if (!Ws) return;
	// kinds of its tier (or the nearest tier below that has any)
	TArray<int32> Kinds;
	for (int32 T = P.Tier; T >= 1 && Kinds.Num() == 0; --T)
		for (int32 K = 0; K < Monsters.Num(); ++K) if (Monsters[K].Mesh && Monsters[K].Tier == T) Kinds.Add(K);
	if (Kinds.Num() == 0) for (int32 K = 0; K < Monsters.Num(); ++K) if (Monsters[K].Mesh) Kinds.Add(K);
	if (Kinds.Num() == 0) return;
	// (destroyed ones out of the list: the chunks' monsters go with their chunks, and GetMonsters walks it)
	Ws->SpawnedMonsters.RemoveAll([](const TObjectPtr<ARDMonster>& M) { return !IsValid(M); });
	URDGameInstance* GI = URDGameInstance::Of(this);
	FRandomStream R((int32)FRDWildWorld::Hash(P.Id, 91, Wild->Seed));
	const bool bLair = P.Kind == TEXT("lair");
	const int32 Kind = Kinds[R.RandRange(0, Kinds.Num() - 1)];
	const int32 N = bLair ? R.RandRange(3, 5) : R.RandRange(2, 3);
	const FRDMonsterDef& Def = Monsters[Kind];
	for (int32 I = 0; I < N; ++I)
	{
		const float A = R.FRandRange(0.f, 2.f * PI), D = R.FRandRange(300.f, 900.f), Yaw = R.FRandRange(0.f, 360.f);
		// (one killed stays dead: its draws are made first, so the others keep their places)
		const int64 Key = (int64)P.Id * 16 + I;
		if (GI && GI->WildKilled.Contains(Key)) continue;
		FVector At(P.At.X * 100.0 + FMath::Cos(A) * D, P.At.Y * 100.0 + FMath::Sin(A) * D, 0.0);
		At.Z = WildGroundZ(At) + Def.CapsuleHalfHeight + 10.f;
		FActorSpawnParameters Sp; Sp.SpawnCollisionHandlingOverride = ESpawnActorCollisionHandlingMethod::AdjustIfPossibleButAlwaysSpawn;
		ARDMonster* M = GetWorld()->SpawnActor<ARDMonster>(ARDMonster::StaticClass(), FTransform(FRotator(0, Yaw, 0), At), Sp);
		if (!M) continue;
		M->SpawnIndex = -1;
		M->bOpenGround = true; M->HomeAt = At; M->WildKey = Key;
		M->Setup(Ws, Def, (int32)FRDWildWorld::Hash(P.Id, 100 + I, Wild->Seed));
		M->Empower(P.Tier, bLair ? 1.35f : 1.f, bLair ? 1.2f : 1.f, 1.f, bLair ? FString::Printf(TEXT("%s"), *P.Name) : FString());
		Ws->SpawnedMonsters.Add(M);
		C->Props.Add(M);
		++WildMonstersSpawned;
	}
}
