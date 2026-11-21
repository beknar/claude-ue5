// The user's list of 2026-11-20 (docs/improvements15.txt; the plan docs/improvements15_plan.md), its eighth phase: the villages lived
// in. Item 27, "the small villages are not inhabited. example: Hawkby", and item 28, "8-15 small buildings, with a 2-5 person household
// per building": each village house (phase 7 lays 8 to 15 on their terraces) a household of 2 to 5. Beds where the room has room (the
// farmhouses' way: along its walls, clear of everything in it), a work place each (the square, before their door, by the well), their
// day the farm folk's (RDList14f.cpp: out at six, home at half past eight, asleep from nine in their own bed), the villagers' lines,
// counted by the wild people's rules (hurt, killed and kept dead, looted, seeing a lock picked). The households are laid one a frame
// after the village's pieces (VillageHouseQueue15), and every wild person beyond 250 m of her stops its day.
#include "RD/RDDungeonGenerator.h"
#include "RD/RDWild.h"
#include "RD/RDTown.h"
#include "Components/StaticMeshComponent.h"
#include "ProceduralMeshComponent.h"
#include "Kismet/GameplayStatics.h"
#include "Engine/World.h"
DEFINE_LOG_CATEGORY_STATIC(LogRDList15g, Log, All);

static constexpr float RDV15DormantCm = 25000.f;

void ARDDungeonGenerator::WildBodyPools15(TArray<int32>& Men, TArray<int32>& Women, TArray<int32>& Kids) const
{
	for (int32 I = 0; I < Townsfolk.Num(); ++I)
	{
		const FRDTownsfolkDef& Df = Townsfolk[I];
		if (!Df.Mesh || !Df.Town.IsEmpty()) continue;
		if (Df.Role == ERDTownRole::Child) Kids.Add(I);
		else if (Df.Role == ERDTownRole::Townsfolk) (Df.Name.ToString().Contains(TEXT("woman")) ? Women : Men).Add(I);
	}
}

void ARDDungeonGenerator::LayVillageHousehold15(ARDWildChunk* C, const FRDWildPlace& P, int32 HouseK, int32 HouseIdx)
{
	if (!C || !Wild.IsValid() || !C->Houses.IsValidIndex(HouseIdx)) return;
	ARDWildChunk::FHouse& Hs = C->Houses[HouseIdx];
	if (!Hs.bDoor15) return;
	const uint32 Hh = FRDWildWorld::Hash(P.Id, 640 + HouseK, Wild->Seed);
	const int32 N = 2 + (int32)(Hh % 4u);
	// ---- its beds: the house's own and as many more as the household needs, along the room's walls (30 cm apart, the head to the wall),
	// clear of the door's way and of everything in the room (an overlap test from 30 cm over the floor, the farmhouses' way). The room
	// round its own middle (PR #100's review: its mesh's origin is not the room's middle, and tries on one side stood in the wall)
	if (const FRDPiece* Bp = Piece(TEXT("Bed")); Bp && Bp->Mesh)
	{
		const float Bx = (float)Bp->Size.X, By = (float)Bp->Size.Y, Bz = (float)Bp->Size.Z;
		const FRotator Rr(0.f, Hs.Yaw, 0.f);
		const float X0 = -Hs.H.X + 8.f, X1 = Hs.H.X - 8.f, Y0 = -Hs.H.Y + 8.f, Y1 = Hs.H.Y - 8.f;
		struct FBd { float X, Y, YawL; };
		TArray<FBd> Tries;
		for (float Y = Y1 - By * 0.5f - 4.f; Y >= Y0 + By * 0.5f + 4.f; Y -= 30.f) { Tries.Add({ X0 + Bx * 0.5f, Y, 0.f }); Tries.Add({ X1 - Bx * 0.5f, Y, 180.f }); }
		for (float X = X0 + By * 0.5f + 4.f; X <= X1 - By * 0.5f - 4.f; X += 30.f) { Tries.Add({ X, Y1 - Bx * 0.5f, -90.f }); Tries.Add({ X, Y0 + Bx * 0.5f, 90.f }); }
		for (const FBd& T : Tries)
		{
			if (Hs.Beds15.Num() >= N) break;
			const FVector L = Hs.RoomC15 + Rr.RotateVector(FVector(T.X, T.Y, 0.f));
			const FVector Lf(L.X, L.Y, Hs.FloorZ + 1.f);
			if (FVector::Dist2D(Lf, Hs.DoorIn15) < FMath::Max(Bx, By) * 0.5f + 190.f) continue;          // (not in the door's way or its leaf's swing)
			const float Y2 = Hs.Yaw + T.YawL;
			if (!WildSpotFree14(C, Lf + FVector(0, 0, 30.f + (Bz - 40.f) * 0.5f), Y2, FVector(Bx * 0.5f - 3.f, By * 0.5f - 3.f, (Bz - 40.f) * 0.5f))) continue;
			UStaticMeshComponent* Sm = NewObject<UStaticMeshComponent>(C);
			Sm->SetStaticMesh(Bp->Mesh);
			if (Bp->Material) Sm->SetMaterial(0, Bp->Material);
			Sm->SetupAttachment(C->Ground.Get());
			if (!Bp->bCollision) Sm->SetCollisionEnabled(ECollisionEnabled::NoCollision);
			Sm->RegisterComponent();
			Sm->SetWorldTransform(Bp->Adjust * FTransform(FRotator(0.f, Y2, 0.f), Lf));
			C->PlaceProps.Add(Sm);
			Hs.Beds15.Add(FTransform(FRotator(0.f, Y2, 0.f), Lf));
			++Hs.Furniture;
		}
	}
	// ---- its people: two grown-ups (a man and a woman), then children and grown-ups by the house's own hash
	TArray<int32> Men, Women, Kids;
	WildBodyPools15(Men, Women, Kids);
	const FVector2D Sq = P.At;
	const FVector DoorOut = Hs.DoorOut15, Ow = (Hs.DoorOut15 - Hs.DoorIn15).GetSafeNormal2D();
	FActorSpawnParameters Sp; Sp.SpawnCollisionHandlingOverride = ESpawnActorCollisionHandlingMethod::AlwaysSpawn;
	for (int32 K = 0; K < N; ++K)
	{
		const uint32 Hk = FRDWildWorld::Hash(P.Id, 700 + HouseK * 8 + K, Wild->Seed);
		const int32 Body = K == 0 ? 0 : K == 1 ? 1 : (Hk % 3u == 0u ? (Hk & 8u ? 1 : 0) : 2);
		const TArray<int32>& Pool = Body == 2 ? Kids : Body == 1 ? Women : Men;
		if (Pool.Num() == 0) continue;
		const int32 D = Pool[(int32)((Hk >> 4) % (uint32)Pool.Num())];
		// (spread out: a third of the grown-ups at the square, the rest before their own door (each its own side of it); half the children
		// round the well, half before their house (all of a village's men in the square and its children round the well were a crowd))
		FVector2D At; float Yaw; const TCHAR* Work = nullptr; const TCHAR* Prop = nullptr;
		const float A = FMath::DegreesToRadians((float)(Hk % 360u));
		const FVector2D Door2 = FVector2D(DoorOut.X, DoorOut.Y) / 100.f, Ow2(Ow.X, Ow.Y), Sd2(-Ow.Y, Ow.X);
		const bool bSquare = Body == 2 ? (Hk & 16u) != 0u : (K != 1 && (Hk >> 5) % 3u == 0u);
		if (bSquare)
		{
			const float Rr = Body == 2 ? 3.f + (Hk >> 9) % 4 : 6.5f + (Hk >> 9) % 4;
			At = Sq + FVector2D(FMath::Cos(A), FMath::Sin(A)) * Rr; Yaw = FMath::RadiansToDegrees(A) + 180.f;
			if (Body != 2) Work = TEXT("Talk");
		}
		else
		{
			At = Door2 + Ow2 * (1.8f + 0.5f * (K % 3)) + Sd2 * ((K % 2 ? 1.f : -1.f) * (1.2f + 0.9f * (K / 2)));
			Yaw = FMath::RadiansToDegrees(FMath::Atan2(Sq.Y - At.Y, Sq.X - At.X));
			if (K == 1) { Work = TEXT("Scatter"); Prop = TEXT("Bowl"); } else if (Body != 2) Work = TEXT("Talk");
		}
		// (a spot clear of the square's well, hay and cart and the walls, laid before the households (PR #100's review: spawned before them,
		// a villager could stand in the hay all day): its own spot, else a few round it)
		for (int32 Tr = 0; Tr < 8; ++Tr)
		{
			const FVector2D Q = At + (Tr == 0 ? FVector2D::ZeroVector : FVector2D(FMath::Cos(Tr * PI / 3.5f), FMath::Sin(Tr * PI / 3.5f)) * (0.8f + 0.3f * Tr));
			const float Gz = WildGroundZ(FVector(Q.X * 100.0, Q.Y * 100.0, 0.0));
			if (WildSpotFree14(C, FVector(Q.X * 100.0, Q.Y * 100.0, Gz + 100.f), 0.f, FVector(35.f, 35.f, 70.f))) { At = Q; break; }
		}
		const FVector W(At.X * 100.0, At.Y * 100.0, WildGroundZ(FVector(At.X * 100.0, At.Y * 100.0, 0.0)) + 92.f);
		ARDTownsfolk* T = GetWorld()->SpawnActor<ARDTownsfolk>(ARDTownsfolk::StaticClass(), FTransform(FRotator(0, Yaw, 0), W), Sp);
		if (!T) continue;
		T->Init(this, nullptr, D, W, Yaw, 0.f, HashCombine((uint32)P.Id, (uint32)(HouseK * 8 + K) * 7919u + 17u));
		const TCHAR* LineRole = Body == 2 ? TEXT("child") : Body == 1 ? TEXT("villagewoman") : TEXT("villager");
		T->SetTitle(FString::Printf(TEXT("%s of %s"), Body == 2 ? TEXT("a child") : TEXT("a villager"), *P.Name));
		SetWildFolkHome15(T, Hs.Beds15, DoorOut, Hs.DoorIn15, K);
		if (Work) T->SetStandWork(Work, Prop ? FName(Prop) : NAME_None);
		for (const FString& L : WildVillageLines15)
		{
			FString Who, Line;
			if (!L.Split(TEXT("|"), &Who, &Line)) continue;
			if (Who == LineRole || Who == TEXT("any")) T->OwnLines.Add(Line.Replace(TEXT("{village}"), *P.Name));
		}
		T->Tags.Add(FName(*FString::Printf(TEXT("RDVillage15|%s|%d|%.0f|%.0f"), *P.Name, HouseK, Hs.RoomC15.X, Hs.RoomC15.Y)));
		C->Props.Add(T);
		WildVillageFolk15.Add(T);
		// (killed in this game, it lies dead: its key from the village's id and its house (kind 3: a village's household))
		KeepWildFolk14(T, WildFolkKey14(3, ((int64)P.Id << 4) | (HouseK & 15), K));
	}
}

void ARDDungeonGenerator::TickVillageFolk15()
{
	// (one household a frame from the queue: its house found again in its chunk by the room's middle)
	while (VillageHouseQueue15.Num() > 0)
	{
		const FVillageHouseQ15 Q = VillageHouseQueue15[0];
		VillageHouseQueue15.RemoveAt(0);
		ARDWildChunk* C = Q.Chunk.Get();
		if (!IsValid(C)) continue;
		const int32 Hi = C->Houses.IndexOfByPredicate([&Q](const ARDWildChunk::FHouse& H) { return FVector::Dist2D(H.RoomC15, Q.RoomC) < 10.f; });
		if (Hi >= 0) { LayVillageHousehold15(C, Q.P, Q.HouseK, Hi); AddHouseLight15(C, C->Houses[Hi].RoomC15, C->Houses[Hi].DoorOut15, C->Houses[Hi].bDoor15); break; }          // (the tenth phase: its light by night)
	}
	// (once a second: a wild person beyond 250 m of her stops its day (no tick); its body is left to pose as the engine poses what is seen
	// (PR #100's review: its skeletal tick switched off too, a village laid off screen and looked at from 300 m stood in its reference
	// pose); the dead are left alone (their death pose is set on their first tick). Every kind of the wilds' people, not the villagers
	// alone (the review: the farms' families and the travellers kept ticking at any distance))
	const UWorld* W = GetWorld();
	if (!W || W->GetTimeSeconds() < VillageFolkCheckAt15) return;
	VillageFolkCheckAt15 = W->GetTimeSeconds() + 1.f;
	const APawn* Her = UGameplayStatics::GetPlayerPawn(this, 0);
	if (!Her) return;
	const FVector L = Her->GetActorLocation();
	WildVillageFolk15.RemoveAll([](const TWeakObjectPtr<ARDTownsfolk>& Wk) { return !Wk.IsValid(); });
	for (ARDTownsfolk* T : WildPeople14())
	{
		if (!IsValid(T) || T->IsWildDead14()) continue;
		const bool bFar = FVector::Dist2D(T->GetActorLocation(), L) > RDV15DormantCm;
		if (T->IsActorTickEnabled() == !bFar) continue;
		T->SetActorTickEnabled(!bFar);
	}
}

TArray<FString> ARDDungeonGenerator::GetVillageFolk15(const FString& Village) const
{
	// ("title|house|x|y|z|asleep|in bed|indoors|dormant|has a bed|its house's room middle x|y")
	TArray<FString> Out;
	for (const TWeakObjectPtr<ARDTownsfolk>& Wk : WildVillageFolk15)
	{
		const ARDTownsfolk* T = Wk.Get();
		if (!T) continue;
		FString Tag;
		for (const FName& G : T->Tags) if (G.ToString().StartsWith(TEXT("RDVillage15|"))) { Tag = G.ToString(); break; }
		TArray<FString> Pt; Tag.ParseIntoArray(Pt, TEXT("|"));
		if (Pt.Num() < 5 || Pt[1] != Village) continue;
		const FVector L = T->GetActorLocation();
		Out.Add(FString::Printf(TEXT("%s|%s|%.0f|%.0f|%.0f|%d|%d|%d|%d|%d|%s|%s"), *T->Title, *Pt[2], L.X, L.Y, L.Z, T->IsSleeping() ? 1 : 0, T->IsInBed() ? 1 : 0,
			T->IsWildIndoors() ? 1 : 0, T->IsActorTickEnabled() ? 0 : 1, T->HasBed() ? 1 : 0, *Pt[3], *Pt[4]));
	}
	return Out;
}
