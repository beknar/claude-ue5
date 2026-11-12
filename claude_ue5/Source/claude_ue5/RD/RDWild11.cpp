// The user's list of 2026-11-11 (docs/improvements11.txt), its fifth phase, the wilderness:
//   - "there should be more different types of events that the player can encounter in the wilderness -- most of the types
//     encountered are the satchels found and ambushers - what else can the player find within a 40s amount of time?": the
//     director (RDWildPoi.cpp) meets her besides with a point of interest laid ahead of her (a camp, a cache, a herb patch, a
//     shrine, a wagon... of her region), a herd of the wild animals, or a person on the way who talks and gives
//     (MakeWildEncounter11; the kinds from SourceArt/wilderness/events11.json, 920 events);
//   - "in meadows, there should be some scattering of debris ... leaves blowing in the wind": the leaves blown round her in the
//     meadows and woods (TickWild11: a Niagara system before the camera, WildLeavesBiomes);
//   - Graymourne: "when the player goes in the water, there should be displacement, a splash and a wake" (TickWild11: a splash
//     where she comes into water, the harbour's or the wilds', rings on its face round her and behind her; WaterFaceAt in
//     RDPort.cpp, with the harbour open to the sea and its ramps).
#include "RD/RDDungeonGenerator.h"
#include "RD/RDWild.h"
#include "RD/RDTown.h"
#include "RD/RDCombat.h"
#include "RD/RDSection.h"
#include "RD/RDGameInstance.h"
#include "Kismet/GameplayStatics.h"
#include "Camera/PlayerCameraManager.h"
#include "NiagaraFunctionLibrary.h"
#include "NiagaraComponent.h"
#include "NiagaraSystem.h"
#include "Engine/World.h"
#include "GameFramework/Character.h"
#include "Components/CapsuleComponent.h"
#include "Components/StaticMeshComponent.h"
#include "Materials/MaterialInstanceDynamic.h"

DEFINE_LOG_CATEGORY_STATIC(LogRDWild11, Log, All);

ARDWildChunk* ARDDungeonGenerator::WildChunkAtCm(const FVector2D& At) const
{
	for (const auto& Kv : WildChunks)
	{
		ARDWildChunk* K = Kv.Value;
		if (!IsValid(K) || K->bMaking) continue;
		const FVector L = K->GetActorLocation();
		if (At.X >= L.X && At.X < L.X + WildChunkM * 100.f && At.Y >= L.Y && At.Y < L.Y + WildChunkM * 100.f) return K;
	}
	return nullptr;
}

// ================================================================================================ the director's new kinds
int32 ARDDungeonGenerator::MakeWildEncounter11(const FRDWildPoiKind& K, const FVector2D& At, FRandomStream& Rs)
{
	if (!IsWildReady()) return 0;
	int32 Made = 0;
	FRDWSample S; Wild->Sample(At.X / 100.0, At.Y / 100.0, S, false);
	const FString Bn = Wild->BiomeName(S.Biome);
	// ---- a point of interest laid ahead of her: one of the kinds named that grows in her region, with its pieces, what it holds,
	// its guards; it goes with its chunk
	if (!K.Place.IsEmpty())
	{
		TArray<FString> Names; K.Place.ParseIntoArray(Names, TEXT(","), true);
		TArray<int32> Ks;
		for (FString N : Names)
		{
			N.TrimStartAndEndInline();
			const int32 I = WildPoiKinds.IndexOfByPredicate([&](const FRDWildPoiKind& X) { return X.Name.ToString() == N && !X.bRoaming; });
			if (I < 0) continue;
			for (const FString& B : WildPoiKinds[I].Biomes) if (B == TEXT("*") || B == Bn) { Ks.Add(I); break; }
		}
		if (ARDWildChunk* C = Ks.Num() > 0 ? WildChunkAtCm(At) : nullptr)
		{
			FRDWildPlace P;
			P.Id = (1 << 29) + (1 << 25) + (++WildDirectorPlaces & 0xFFFFF);
			P.Kind = TEXT("poi"); P.Poi = Ks[Rs.RandRange(0, Ks.Num() - 1)]; P.Name = WildPoiKinds[P.Poi].Title;
			P.At = At / 100.0; P.Yaw = Rs.FRandRange(0.f, 360.f); P.Tier = Wild->TierAt(P.At.X, P.At.Y); P.Biome = S.Biome;
			SpawnWildPoi(C, P);
			++Made;
			WildEngagements.Add(FString::Printf(TEXT("%.1f|placed|%s|%.0f|%.0f"), GetWorld()->GetTimeSeconds(), *WildPoiKinds[P.Poi].Name.ToString(), P.At.X, P.At.Y));
			UE_LOG(LogRDWild11, Log, TEXT("RDENCOUNTER11 %s laid %s at (%.0f, %.0f) m"), *K.Name.ToString(), *WildPoiKinds[P.Poi].Name.ToString(), P.At.X, P.At.Y);
		}
	}
	// ---- a herd of the wild animals
	if (!K.Animals.IsEmpty())
	{
		TArray<FString> Parts; K.Animals.ParseIntoArray(Parts, TEXT(","), true);
		for (const FString& Pa : Parts)
		{
			FString Kn, Cn;
			if (!Pa.Split(TEXT(":"), &Kn, &Cn)) { Kn = Pa; Cn = TEXT("3"); }
			Kn.TrimStartAndEndInline();
			for (int32 I = 0, N = FMath::Clamp(FCString::Atoi(*Cn), 1, 8); I < N; ++I)
			{
				const float A = Rs.FRandRange(0.f, 2.f * PI), D = Rs.FRandRange(100.f, 900.f);
				FVector Q(At.X + FMath::Cos(A) * D, At.Y + FMath::Sin(A) * D, 0.f);
				Q.Z = WildGroundZ(Q);
				if (ARDWildAnimal* An = SpawnWildAnimalAt(FName(*Kn), Q)) { WildRoamHerd.Add(An); ++Made; }
			}
		}
	}
	// ---- a person on the way, with their line and their gift
	if (!K.Folk.IsEmpty())
	{
		const int32 D = Townsfolk.IndexOfByPredicate([&](const FRDTownsfolkDef& X) { return X.Mesh && X.Name.ToString() == K.Folk; });
		if (D >= 0)
		{
			const float Yaw = Rs.FRandRange(0.f, 360.f);
			const FVector Q(At.X, At.Y, WildGroundZ(FVector(At.X, At.Y, 0.f)) + 92.f);
			FActorSpawnParameters Sp; Sp.SpawnCollisionHandlingOverride = ESpawnActorCollisionHandlingMethod::AlwaysSpawn;
			if (ARDTownsfolk* T = GetWorld()->SpawnActor<ARDTownsfolk>(ARDTownsfolk::StaticClass(), FTransform(FRotator(0, Yaw, 0), Q), Sp))
			{
				T->Init(this, nullptr, D, Q, Yaw, 0.f, Rs.GetUnsignedInt());
				T->SetTitle(K.Title);
				TArray<FString> Lines; K.Text.ParseIntoArray(Lines, TEXT("|"), true);
				T->OwnLines = Lines;
				T->WildGift = K.Gift; T->WildGiftGold = K.GiftGold;
				WildRoamFolk.Add(T);
				++Made;
			}
		}
	}
	return Made;
}

void ARDDungeonGenerator::GiveWildGift(ARDTownsfolk* T)
{
	if (!T || !PlayerCombat || T->bWildGiven) return;
	TArray<FString> Lines; T->WildGift.ParseIntoArray(Lines, TEXT(";"), true);
	FRandomStream R((int32)HashCombine(T->GetUniqueID(), 0x61F7u));
	TArray<FName> Got = RollWildThings(Lines, R);
	if (Got.Num() == 0)
		for (const FString& L : Lines)
		{
			FString Nm, Rest;
			if (!L.Split(TEXT("|"), &Nm, &Rest)) Nm = L;
			if (FindItem(FName(*Nm)) >= 0) { Got.Add(FName(*Nm)); break; }
		}
	TArray<FName> Order; TMap<FName, int32> N;
	for (const FName& G : Got) { if (!N.Contains(G)) Order.Add(G); N.FindOrAdd(G)++; }
	for (const FName& G : Order) PlayerCombat->AddItem(G, N[G]);
	if (Order.Num() > 0) { LastFound = Order[0]; LastFoundList = Order; LastFoundTime = GetWorld()->GetTimeSeconds(); ItemsFound += Order.Num(); }
	const int32 Gold = WildGoldAt(T->WildGiftGold, T->GetActorLocation());
	if (Gold > 0) AddGold(Gold, FString::Printf(TEXT("from %s"), *T->Title.ToLower()));
	T->WildGift.Empty(); T->WildGiftGold = 0; T->bWildGiven = true;
	WildEngagements.Add(FString::Printf(TEXT("%.1f|given|%s|%d things, %d gold"), GetWorld()->GetTimeSeconds(), *T->Title, Got.Num(), Gold));
	PlaySoundAt(TEXT("Player.Loot"), T->GetActorLocation());
}

// ================================================================================================ the leaves in the wind
void ARDDungeonGenerator::TickWild11(float Dt, const FVector& Her)
{
	if (!bWild || !IsWildReady()) return;
	// (the director's people and herds far behind her gone)
	for (int32 I = WildRoamFolk.Num() - 1; I >= 0; --I)
		if (ARDTownsfolk* T = WildRoamFolk[I].Get(); !T || FVector::Dist2D(T->GetActorLocation(), Her) > 25000.f) { if (T) T->Destroy(); WildRoamFolk.RemoveAt(I); }
	for (int32 I = WildRoamHerd.Num() - 1; I >= 0; --I)
		if (ARDWildAnimal* A = WildRoamHerd[I].Get(); !A || FVector::Dist2D(A->GetActorLocation(), Her) > 25000.f) { if (A) A->Destroy(); WildRoamHerd.RemoveAt(I); }
	// ---- the water round her ("when the player goes in the water, there should be displacement, a splash and a wake"): a splash
	// where she comes into it (falling in throws it higher), then rings on its face: behind her as she wades (her wake), now and
	// then round her as she stands in it
	if (const ACharacter* Ch = Cast<ACharacter>(UGameplayStatics::GetPlayerPawn(this, 0)))
	{
		float Fz = 0.f;
		const float Feet = Her.Z - (Ch->GetCapsuleComponent() ? Ch->GetCapsuleComponent()->GetScaledCapsuleHalfHeight() : 90.f);
		const bool bIn = WaterFaceAt(Her, Fz) && Feet < Fz - 5.f && Feet > Fz - 400.f;
		const FVector V = Ch->GetVelocity();
		if (bIn && !bInWater)
		{
			const float Hard = FMath::Clamp(-V.Z / 600.f, 0.f, 1.f);
			LastSplashAt = FVector(Her.X, Her.Y, Fz);
			if (WaterSplashFx)
				if (UNiagaraComponent* C = UNiagaraFunctionLibrary::SpawnSystemAtLocation(this, WaterSplashFx, LastSplashAt, FRotator::ZeroRotator, FVector(WaterSplashScale * (0.7f + 0.8f * Hard)), true, true, ENCPoolMethod::None))
					WaterFxMade.Add({ C, WaterFxLife });
			PlaySoundAt(TEXT("Player.Splash"), LastSplashAt);
			MakeWaterRing(LastSplashAt, WaterRingRadius.X * 1.5f, WaterRingRadius.Y * (1.6f + Hard), WaterRingLife * 1.4f, 1.f);
			++WaterSplashes; WaterWakeClock = 0.f;
			UE_LOG(LogRDWild11, Log, TEXT("RDWATER splash at (%.0f, %.0f, %.0f), falling %.0f cm/s"), Her.X, Her.Y, Fz, -V.Z);
		}
		bInWater = bIn;
		if (bIn)
		{
			const float Sp = V.Size2D();
			WaterWakeClock -= Dt;
			if (Sp > 80.f) WaterWakeClock = FMath::Min(WaterWakeClock, 0.22f);       // (a wake from her first steps, not after a standing ring's wait)
			if (WaterWakeClock <= 0.f)
			{
				WaterWakeClock = Sp > 80.f ? 0.22f : 1.1f;
				const FVector Back = Sp > 80.f ? -V.GetSafeNormal2D() * 60.f : FVector::ZeroVector;
				// (our own ring where the material is set; else the pack's ripple)
				if (WaterRingMaterial && WaterRingMesh)
					MakeWaterRing(FVector(Her.X, Her.Y, Fz) + Back, WaterRingRadius.X, WaterRingRadius.Y * (Sp > 80.f ? 1.f : 0.75f), WaterRingLife, Sp > 80.f ? 0.8f : 0.55f);
				else if (WaterRingFx)
					if (UNiagaraComponent* C = UNiagaraFunctionLibrary::SpawnSystemAtLocation(this, WaterRingFx, FVector(Her.X, Her.Y, Fz + 1.f) + Back, FRotator(0, V.Rotation().Yaw, 0), FVector(WaterRingScale * (Sp > 80.f ? 1.f : 0.7f)), true, true, ENCPoolMethod::None))
						WaterFxMade.Add({ C, WaterFxLife });
				++WaterRings;
			}
		}
	}
	TickWaterRings(Dt);
	for (int32 I = WaterFxMade.Num() - 1; I >= 0; --I)
	{
		WaterFxMade[I].Value -= Dt;
		UNiagaraComponent* C = WaterFxMade[I].Key.Get();
		if (!C) { WaterFxMade.RemoveAtSwap(I); continue; }
		if (WaterFxMade[I].Value <= 0.f) { C->DeactivateImmediate(); C->DestroyComponent(); WaterFxMade.RemoveAtSwap(I); }
	}
	if (!WildLeavesFx) return;
	const APlayerCameraManager* Cam = UGameplayStatics::GetPlayerCameraManager(this, 0);
	if (!Cam) return;
	WildLeavesClock -= Dt;
	if (WildLeavesClock <= 0.f)
	{
		WildLeavesClock = 0.5f;
		FRDWSample S; Wild->Sample(Her.X / 100.0, Her.Y / 100.0, S, false);
		WildLeavesBiome = Wild->BiomeName(S.Biome);
		const bool bWant = !IsInTownWalls(Her) && S.WaterKind == 0 && WildLeavesBiomes.Contains(WildLeavesBiome);
		if (bWant && !WildLeavesComp)
		{
			WildLeavesComp = UNiagaraFunctionLibrary::SpawnSystemAtLocation(this, WildLeavesFx, Her, FRotator::ZeroRotator, FVector(WildLeavesScale), false, true, ENCPoolMethod::None);
			UE_LOG(LogRDWild11, Log, TEXT("RDLEAVES on in %s"), *WildLeavesBiome);
		}
		else if (WildLeavesComp && bWant != WildLeavesComp->IsActive()) { if (bWant) WildLeavesComp->Activate(true); else WildLeavesComp->Deactivate(); }
	}
	// (before the camera, at her height, the way it looks)
	if (WildLeavesComp)
	{
		const FVector Fw = (Cam->GetCameraRotation().Vector() * FVector(1, 1, 0)).GetSafeNormal();
		WildLeavesComp->SetWorldLocation(FVector(Cam->GetCameraLocation().X, Cam->GetCameraLocation().Y, Her.Z + 120.f) + Fw * WildLeavesAhead);
	}
}

void ARDDungeonGenerator::SetWildLeavesFx(UNiagaraSystem* Fx)
{
	if (WildLeavesComp) { WildLeavesComp->DeactivateImmediate(); WildLeavesComp->DestroyComponent(); WildLeavesComp = nullptr; }
	WildLeavesFx = Fx; WildLeavesClock = 0.f;
}

TArray<FString> ARDDungeonGenerator::GetWild11Lines() const
{
	TArray<FString> Out;
	const FVector L = WildLeavesComp ? WildLeavesComp->GetComponentLocation() : FVector::ZeroVector;
	Out.Add(FString::Printf(TEXT("leaves|%d|%s|%d|%.0f|%.0f|%.0f"), WildLeavesComp && WildLeavesComp->IsActive() ? 1 : 0, *WildLeavesBiome, WildLeavesFx ? 1 : 0, L.X, L.Y, L.Z));
	for (const TWeakObjectPtr<ARDTownsfolk>& W : WildRoamFolk)
		if (const ARDTownsfolk* T = W.Get()) Out.Add(FString::Printf(TEXT("folk|%s|%.0f|%.0f|%d"), *T->Title, T->GetActorLocation().X, T->GetActorLocation().Y, T->bWildGiven ? 1 : 0));
	Out.Add(FString::Printf(TEXT("herd|%d"), WildRoamHerd.Num()));
	Out.Add(FString::Printf(TEXT("water|%d|%d|%d|%.0f|%.0f|%.0f|%d|%d"), bInWater ? 1 : 0, WaterSplashes, WaterRings, LastSplashAt.X, LastSplashAt.Y, LastSplashAt.Z, WaterSplashFx ? 1 : 0, WaterRingFx ? 1 : 0));
	if (const ARDSection* S = GetSection(FIntPoint::ZeroValue))
		for (int32 I = 0; I < S->GetRampFeet().Num() && I < S->GetRampTops().Num(); ++I)
		{
			const FVector& A = S->GetRampFeet()[I]; const FVector& B = S->GetRampTops()[I];
			Out.Add(FString::Printf(TEXT("ramp|%.0f|%.0f|%.0f|%.0f|%.0f|%.0f"), A.X, A.Y, A.Z, B.X, B.Y, B.Z));
		}
	return Out;
}

void ARDDungeonGenerator::MakeWaterRing(const FVector& At, float From, float To, float Life, float Strength)
{
	if (!WaterRingMaterial || !WaterRingMesh || WaterRingsLive.Num() >= 24) return;
	UStaticMeshComponent* C = NewObject<UStaticMeshComponent>(this, NAME_None, RF_Transient);
	C->SetStaticMesh(WaterRingMesh);
	C->SetCollisionEnabled(ECollisionEnabled::NoCollision);
	C->SetCastShadow(false);
	C->SetMobility(EComponentMobility::Movable);
	C->SetUsingAbsoluteLocation(true); C->SetUsingAbsoluteRotation(true); C->SetUsingAbsoluteScale(true);
	C->RegisterComponent();
	UMaterialInstanceDynamic* M = UMaterialInstanceDynamic::Create(WaterRingMaterial, C);
	M->SetScalarParameterValue(TEXT("Fade"), 0.f);
	C->SetMaterial(0, M);
	// (the plane is 100 cm across, its face up: 2 cm over the water, out of its waves' way)
	// (its turn from where it is: no draw from any stream the play uses)
	const float Yaw = (float)(HashCombine(GetTypeHash(FMath::RoundToInt(At.X)), GetTypeHash(FMath::RoundToInt(At.Y))) % 360u);
	C->SetWorldLocationAndRotation(At + FVector(0, 0, 2.f), FRotator(0, Yaw, 0));
	C->SetWorldScale3D(FVector(From * 2.f / 100.f, From * 2.f / 100.f, 1.f));
	FWaterRing R; R.C = C; R.M = M; R.Life = FMath::Max(Life, 0.1f); R.From = From; R.To = To; R.Strength = Strength;
	WaterRingsLive.Add(R);
}

void ARDDungeonGenerator::TickWaterRings(float Dt)
{
	for (int32 I = WaterRingsLive.Num() - 1; I >= 0; --I)
	{
		FWaterRing& R = WaterRingsLive[I];
		R.Age += Dt;
		UStaticMeshComponent* C = R.C.Get();
		if (!C || R.Age >= R.Life) { if (C) C->DestroyComponent(); WaterRingsLive.RemoveAtSwap(I); continue; }
		// (out fast at first, slowing as a ring on water does; bright at once, fading out)
		const float T = R.Age / R.Life, Ease = 1.f - FMath::Square(1.f - T);
		const float Rad = FMath::Lerp(R.From, R.To, Ease);
		C->SetWorldScale3D(FVector(Rad * 2.f / 100.f, Rad * 2.f / 100.f, 1.f));
		if (UMaterialInstanceDynamic* M = R.M.Get()) M->SetScalarParameterValue(TEXT("Fade"), R.Strength * FMath::Min(1.f, T * 8.f) * FMath::Square(1.f - T));
	}
}

float ARDDungeonGenerator::GetWaterFaceUnderHer() const
{
	const APawn* P = UGameplayStatics::GetPlayerPawn(this, 0);
	float Z = 0.f;
	return P && WaterFaceAt(P->GetActorLocation(), Z) ? Z : -1e9f;
}
