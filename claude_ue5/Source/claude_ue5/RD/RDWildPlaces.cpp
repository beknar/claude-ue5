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
		// (the farms' farmsteads: RDWildFarm.cpp)
		// (one a frame, after the chunk's own steps: a farmstead is some 30 pieces, 10 animals and 4 people (PR #30's review))
		if (P.Kind == TEXT("farmstead")) { WildFarmQueue.Add({ C, P }); continue; }
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
		if (P.Quest == TEXT("wolves"))
		{
			// (the captain's "Wolves on the Mill Road": a den beside the road, the sheep's bones round it, a broken fence)
			Put(TEXT("skeleton"), P.At, P.Yaw, 0.8f, 5.f, false);
			Ring(R.RandRange(5, 7), 6.f, 25.f, [&](const FVector2D& At, float Yaw) { Put(TEXT("bones"), At, Yaw + R.FRandRange(0.f, 360.f), 1.f, 2.f, false); });
			Ring(10, 3.f, 10.f, [&](const FVector2D& At, float Yaw) { Put(TEXT("branch"), At, Yaw + 90.f + R.FRandRange(-20.f, 20.f), 1.f, 3.f, false); });
			const FVector2D Fw(FMath::Cos(FMath::DegreesToRadians(P.Yaw)), FMath::Sin(FMath::DegreesToRadians(P.Yaw))), Sd(-Fw.Y, Fw.X);
			Put(TEXT("fence"), P.At + Fw * 14.f + Sd * 3.f, P.Yaw + 90.f + R.FRandRange(-10.f, 10.f), 1.f, 5.f);
			Put(TEXT("fence"), P.At + Fw * 13.f - Sd * 4.f, P.Yaw + 70.f + R.FRandRange(-10.f, 10.f), 1.f, 25.f);
			Put(TEXT("hay"), P.At + Fw * 10.f + Sd * 8.f, P.Yaw, 1.f, 5.f);
		}
		else if (P.Quest == TEXT("patrol"))
		{
			// (the captain's "The Lost Patrol": a ruined watchtower, Brokenspire's round tower's quarters (Castle Forge, 882's
			// Town.TowerRing*: their origin the ring's middle) two storeys whole and a third broken, its fallen stones; the five
			// of the watch lie before its doorway, which faces the road)
			const float Z0 = WildGroundZ(FVector(P.At.X * 100.0, P.At.Y * 100.0, 0.0)) - 40.f;
			const FRDPiece* Rp = Piece(TEXT("Town.TowerRingE"));
			const float Hs = Rp ? FMath::Max((float)Rp->Size.Z - 14.f, 100.f) : 300.f;
			auto Quarter = [&](TCHAR V, float Yaw, float Z)
			{
				const FRDPiece* Q = Piece(FName(*FString::Printf(TEXT("Town.TowerRing%c"), V)));
				if (!Q) Q = Rp;
				if (!Q || !Q->Mesh) return;
				const FTransform T = Q->Adjust * FTransform(FRotator(0.f, Yaw, 0.f), FVector(P.At.X * 100.0, P.At.Y * 100.0, Z) - O);
				UStaticMeshComponent* Sm = NewObject<UStaticMeshComponent>(C);
				Sm->SetStaticMesh(Q->Mesh);
				Sm->SetupAttachment(C->Ground);
				Sm->SetRelativeTransform(T);
				Sm->RegisterComponent();
				C->PlaceProps.Add(Sm);
				++Laid;
			};
			// (the doorway quarter's middle on the way to the road: a quarter spans its yaw to its yaw + 90)
			const float Y0 = P.Yaw - 45.f;
			static const TCHAR Low[4] = { TEXT('D'), TEXT('A'), TEXT('E'), TEXT('A') };
			static const TCHAR Mid[4] = { TEXT('B'), TEXT('A'), TEXT('C'), TEXT('A') };
			for (int32 K = 0; K < 4; ++K) Quarter(Low[K], Y0 + 90.f * K, Z0);
			for (int32 K = 0; K < 4; ++K) Quarter(Mid[K], Y0 + 90.f * K, Z0 + Hs);
			const int32 Kept = R.RandRange(0, 3);
			Quarter(TEXT('E'), Y0 + 90.f * Kept, Z0 + 2.f * Hs);
			Quarter(TEXT('A'), Y0 + 90.f * ((Kept + 1) % 4), Z0 + 2.f * Hs);
			for (int32 I = 0; I < 3; ++I)
			{
				const float A = FMath::DegreesToRadians(P.Yaw + 120.f + 60.f * I + R.FRandRange(-15.f, 15.f)), D = R.FRandRange(8.f, 12.f);
				Put(TEXT("ruin"), P.At + FVector2D(FMath::Cos(A), FMath::Sin(A)) * D, R.FRandRange(0.f, 360.f), 0.45f, 20.f);
			}
			const FVector2D Rm = WildQuestRemainsAt(P), Fw(FMath::Cos(FMath::DegreesToRadians(P.Yaw)), FMath::Sin(FMath::DegreesToRadians(P.Yaw))), Sd(-Fw.Y, Fw.X);
			for (int32 I = 0; I < 5; ++I)
				Put(TEXT("bones"), Rm + Sd * ((I - 2) * 1.6f + R.FRandRange(-0.3f, 0.3f)) + Fw * R.FRandRange(-1.2f, 1.2f), P.Yaw + R.FRandRange(-60.f, 60.f) + (I % 2 ? 180.f : 0.f), 1.f, 2.f, false);
		}
		else if (P.Kind == TEXT("village"))
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
		if (P.Kind == TEXT("spawn") || P.Kind == TEXT("lair") || !P.Quest.IsEmpty()) SpawnWildMonsters(C, P);
		if (HallowedKinds.Num() > 0) LayHallowedStone(C, P);          // (the sixth phase: the Angel Tokens' stone)
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
	// (the rebalance to tier 25: a kind with wild tiers meets her in them (the dungeons' kinds spread along the roads), another in
	// its own tier)
	for (int32 T = P.Tier; T >= 1 && Kinds.Num() == 0; --T)
		for (int32 K = 0; K < Monsters.Num(); ++K)
		{
			const FRDMonsterDef& D = Monsters[K];
			if (D.Mesh && (D.WildTierMax > 0 ? (T >= D.WildTierMin && T <= D.WildTierMax) : D.Tier == T)) Kinds.Add(K);
		}
	if (Kinds.Num() == 0) for (int32 K = 0; K < Monsters.Num(); ++K) if (Monsters[K].Mesh) Kinds.Add(K);
	if (Kinds.Num() == 0) return;
	// (destroyed ones out of the list: the chunks' monsters go with their chunks, and GetMonsters walks it)
	Ws->SpawnedMonsters.RemoveAll([](const TObjectPtr<ARDMonster>& M) { return !IsValid(M); });
	URDGameInstance* GI = URDGameInstance::Of(this);
	FRandomStream R((int32)FRDWildWorld::Hash(P.Id, 91, Wild->Seed));
	const bool bLair = P.Kind == TEXT("lair") && P.Quest.IsEmpty();
	int32 Kind = Kinds[R.RandRange(0, Kinds.Num() - 1)];
	int32 N = bLair ? R.RandRange(3, 5) : R.RandRange(2, 3);
	// (the captain's quests: the den's pack of ripper dogs, the nearest the castle's monsters come to wolves, at tier 1's
	// strength; the watchtower's three of what killed the patrol)
	if (!P.Quest.IsEmpty())
	{
		N = WildQuestMonsters(P);
		if (P.Quest == TEXT("wolves"))
		{
			// (by name: the ripper dogs, else any wolf, hound or dog; with none the place's own kind, said in the log (PR #25's
			// review: a level without them would have sent another kind silently). Case kept: "Werewolf" or "Hellhound" is not
			// a pack (PR #26's review); the warning once a play (the generator's, not a static: one outlives play sessions), not at
			// every making of the den's chunk)
			int32 Found = -1;
			for (const TCHAR* Want : { TEXT("Ripper"), TEXT("Wolf"), TEXT("Hound"), TEXT("Dog") })
			{
				for (int32 K = 0; K < Monsters.Num() && Found < 0; ++K)
					if (Monsters[K].Mesh && Monsters[K].Name.ToString().Contains(Want, ESearchCase::CaseSensitive)) Found = K;
				if (Found >= 0) break;
			}
			if (Found >= 0) Kind = Found;
			else if (!bWildWolvesWarned) { bWildWolvesWarned = true; UE_LOG(LogRDWildPlace, Warning, TEXT("RDWILD %s: no ripper dog, wolf, hound or dog among the monsters: its pack is %s"), *P.Name, *Monsters[Kind].Name.ToString()); }
		}
	}
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
		M->Empower(P.Tier, bLair ? 1.35f : 1.f, bLair ? 1.2f : 1.f, 1.f, bLair ? FString::Printf(TEXT("%s"), *P.Name) : P.Quest == TEXT("wolves") ? FString(TEXT("Mill Road Wolf")) : FString());
		Ws->SpawnedMonsters.Add(M);
		C->Props.Add(M);
		++WildMonstersSpawned;
	}
}
