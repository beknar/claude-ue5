// The user's list of 2026-11-20 (docs/improvements15.txt; the plan docs/improvements15_plan.md), its eighth phase: the villages lived
// in. Item 27, "the small villages are not inhabited. example: Hawkby", and item 28, "8-15 small buildings, with a 2-5 person household
// per building": each village house (phase 7 lays 8 to 15 on their terraces) a household of 2 to 5. Beds where the room has room (the
// farmhouses' way: along its walls, clear of everything in it), a work place each (the square, before their door, by the well), their
// day the farm folk's (RDList14f.cpp: out at six, home at half past eight, asleep from nine in their own bed), the villagers' lines,
// counted by the wild people's rules (hurt, killed and kept dead, looted, seeing a lock picked), and still beyond 250 m.
#include "RD/RDDungeonGenerator.h"
#include "RD/RDWild.h"
#include "RD/RDTown.h"
#include "Components/StaticMeshComponent.h"
#include "Components/SkeletalMeshComponent.h"
#include "ProceduralMeshComponent.h"
#include "Kismet/GameplayStatics.h"
#include "Engine/World.h"
DEFINE_LOG_CATEGORY_STATIC(LogRDList15g, Log, All);

static constexpr float RDV15DormantCm = 25000.f;

void ARDDungeonGenerator::LayVillageHousehold15(ARDWildChunk* C, const FRDWildPlace& P, int32 HouseK, int32 HouseIdx)
{
	if (!C || !Wild.IsValid() || !C->Houses.IsValidIndex(HouseIdx)) return;
	ARDWildChunk::FHouse& Hs = C->Houses[HouseIdx];
	if (!Hs.bDoor15) return;
	const uint32 Hh = FRDWildWorld::Hash(P.Id, 640 + HouseK, Wild->Seed);
	const int32 N = 2 + (int32)(Hh % 4u);
	// ---- its beds: the house's own and as many more as the household needs, along the room's walls (30 cm apart, the head to the wall),
	// clear of the door's way and of everything in the room (an overlap test from 30 cm over the floor, the farmhouses' way)
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
			const FVector L = Hs.C + Rr.RotateVector(FVector(T.X, T.Y, 0.f));
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
	for (int32 I = 0; I < Townsfolk.Num(); ++I)
	{
		const FRDTownsfolkDef& Df = Townsfolk[I];
		if (!Df.Mesh || !Df.Town.IsEmpty()) continue;
		if (Df.Role == ERDTownRole::Child) Kids.Add(I);
		else if (Df.Role == ERDTownRole::Townsfolk) (Df.Name.ToString().Contains(TEXT("woman")) ? Women : Men).Add(I);
	}
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
		// (where it works by day: the first at the square, the second before the door, a child by the well, another grown-up at the square)
		FVector2D At; float Yaw; const TCHAR* Work = nullptr; const TCHAR* Prop = nullptr;
		const float A = FMath::DegreesToRadians((float)(Hk % 360u));
		// (spread out: a third of the grown-ups at the square, the rest before their own door (each its own side of it); half the children
		// round the well, half before their house (all of a village's men in the square and its children round the well were a crowd))
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
		const FVector W(At.X * 100.0, At.Y * 100.0, WildGroundZ(FVector(At.X * 100.0, At.Y * 100.0, 0.0)) + 92.f);
		ARDTownsfolk* T = GetWorld()->SpawnActor<ARDTownsfolk>(ARDTownsfolk::StaticClass(), FTransform(FRotator(0, Yaw, 0), W), Sp);
		if (!T) continue;
		T->Init(this, nullptr, D, W, Yaw, 0.f, HashCombine((uint32)P.Id, (uint32)(HouseK * 8 + K) * 7919u + 17u));
		const TCHAR* LineRole = Body == 2 ? TEXT("child") : Body == 1 ? TEXT("villagewoman") : TEXT("villager");
		T->SetTitle(FString::Printf(TEXT("%s of %s"), Body == 2 ? TEXT("a child") : Body == 1 ? TEXT("a villager") : TEXT("a villager"), *P.Name));
		// (home in the house at night: each its own place inside, side by side across the door's way (two at one spot stood in each other)),
		// its own bed (the K-th) if the house has one for it)
		const FVector Side(-Ow.Y, Ow.X, 0.f);
		const FVector In = Hs.DoorIn15 + Side * ((K % 4) - 1.5f) * 55.f;
		T->SetWildFarmHome(FVector(DoorOut.X, DoorOut.Y, DoorOut.Z + 94.f), FVector(In.X, In.Y, In.Z + 92.f));
		if (Hs.Beds15.IsValidIndex(K))
		{
			const FTransform& B = Hs.Beds15[K];
			const FVector Lie = B.GetLocation() + B.GetRotation().GetForwardVector() * 15.f;
			float Top = B.GetLocation().Z + 55.f;
			FHitResult Hit; FCollisionQueryParams Qp(SCENE_QUERY_STAT(RDVillageBed15), false); Qp.AddIgnoredActor(T);
			if (GetWorld()->LineTraceSingleByChannel(Hit, Lie + FVector(0, 0, 200.f), Lie - FVector(0, 0, 20.f), ECC_Visibility, Qp)) Top = Hit.Location.Z;
			T->SetBed(FVector(Lie.X, Lie.Y, Top), B.Rotator().Yaw);
		}
		if (Work) T->SetStandWork(Work, Prop ? FName(Prop) : NAME_None);
		for (const FString& L : WildVillageLines15)
		{
			FString Who, Line;
			if (!L.Split(TEXT("|"), &Who, &Line)) continue;
			if (Who == LineRole || Who == TEXT("any") || (Body != 2 && Who == TEXT("grown"))) T->OwnLines.Add(Line.Replace(TEXT("{village}"), *P.Name));
		}
		T->Tags.Add(FName(*FString::Printf(TEXT("RDVillage15|%s|%d"), *P.Name, HouseK)));
		C->Props.Add(T);
		WildVillageFolk15.Add(T);
		// (killed in this game, it lies dead: its key from the village's id and its house (kind 3: a village's household))
		KeepWildFolk14(T, WildFolkKey14(3, ((int64)P.Id << 4) | (HouseK & 15), K));
	}
	WildVillageFolk15.RemoveAll([](const TWeakObjectPtr<ARDTownsfolk>& W) { return !W.IsValid(); });
}

void ARDDungeonGenerator::TickVillageFolk15()
{
	// (once a second: a villager beyond 250 m of her stands still, its body unposed (a village is 30 to 75 people, and the chunks hold the
	// villages 2 km round her); within it, it lives its day again, the hour read afresh)
	const UWorld* W = GetWorld();
	if (!W || W->GetTimeSeconds() < VillageFolkCheckAt15) return;
	VillageFolkCheckAt15 = W->GetTimeSeconds() + 1.f;
	const APawn* Her = UGameplayStatics::GetPlayerPawn(this, 0);
	if (!Her) return;
	const FVector L = Her->GetActorLocation();
	WildVillageFolk15.RemoveAll([](const TWeakObjectPtr<ARDTownsfolk>& Wk) { return !Wk.IsValid(); });
	for (const TWeakObjectPtr<ARDTownsfolk>& Wk : WildVillageFolk15)
	{
		ARDTownsfolk* T = Wk.Get();
		if (!T) continue;
		const bool bFar = FVector::Dist2D(T->GetActorLocation(), L) > RDV15DormantCm;
		if (T->IsActorTickEnabled() == !bFar) continue;
		T->SetActorTickEnabled(!bFar);
		TInlineComponentArray<USkeletalMeshComponent*> Sk(T);
		for (USkeletalMeshComponent* S : Sk) S->SetComponentTickEnabled(!bFar);
	}
}

TArray<FString> ARDDungeonGenerator::GetVillageFolk15(const FString& Village) const
{
	TArray<FString> Out;
	for (const TWeakObjectPtr<ARDTownsfolk>& Wk : WildVillageFolk15)
	{
		const ARDTownsfolk* T = Wk.Get();
		if (!T) continue;
		FString Tag;
		for (const FName& G : T->Tags) if (G.ToString().StartsWith(TEXT("RDVillage15|"))) { Tag = G.ToString(); break; }
		TArray<FString> Pt; Tag.ParseIntoArray(Pt, TEXT("|"));
		if (Pt.Num() < 3 || Pt[1] != Village) continue;
		const FVector L = T->GetActorLocation();
		Out.Add(FString::Printf(TEXT("%s|%s|%.0f|%.0f|%.0f|%d|%d|%d|%d|%d"), *T->Title, *Pt[2], L.X, L.Y, L.Z, T->IsSleeping() ? 1 : 0, T->IsInBed() ? 1 : 0,
			T->IsWildIndoors() ? 1 : 0, T->IsActorTickEnabled() ? 0 : 1, T->HasBed15() ? 1 : 0));
	}
	return Out;
}
