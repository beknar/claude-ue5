// The user's list of 2026-11-22 (docs/improvements16.txt, "the city of heaven"; the plan docs/improvements16_plan.md), its twenty-second
// phase, Heaven's goods and life:
// - "food, items and other things bought in the city of heaven should be modern in looks": every everyday item has a modern twin
//   (946 goods: its kind, numbers, tiers and buff copied, its own name, words and picture); Heaven's stores sell the twins in their
//   likes' place and its tables lay modern food that gives them; a twin is in no draw and no other store (CaveItemAllowed16);
// - "typical city ambience": people walking the pavements (each from one pavement's tile to another, over the pavements and the
//   zebras only; the cars wait for them on the street as for her), the city's sound (its bed by day and by night, the crowd near the
//   square, horns and cars passing), billboards on the roofs by the streets (lit at night), and neon over the shops' doors lit at night.
#include "RD/RDDungeonGenerator.h"
#include "RD/RDSection.h"
#include "RD/RDTown.h"
#include "RD/RDCombat.h"
#include "Components/AudioComponent.h"
#include "Components/InstancedStaticMeshComponent.h"
#include "Materials/MaterialInstanceDynamic.h"
#include "Sound/SoundWave.h"
#include "Kismet/GameplayStatics.h"
DEFINE_LOG_CATEGORY_STATIC(LogRDHeaven22, Log, All);

static TAutoConsoleVariable<int32> CVarRDNeon22(TEXT("rd.Neon22"), 1, TEXT("Heaven's neon and billboards: 1 by the hour (lit at night), 0 never lit (tests: the street without them)"));
static TAutoConsoleVariable<int32> CVarRDPeds22(TEXT("rd.Peds22"), 1, TEXT("Heaven's pedestrians on the pavements: 1 walking, 0 none (tests: the frame rate with and without them)"));
static TAutoConsoleVariable<int32> CVarRDCity22(TEXT("rd.CitySound22"), 1, TEXT("Heaven's city sound: 1 on, 0 off (tests: a recording with and without it)"));

static const FIntPoint RDH22Dir4[4] = { FIntPoint(-1, 0), FIntPoint(1, 0), FIntPoint(0, -1), FIntPoint(0, 1) };

// ------------------------------------------------------------------------------------------------ the goods
FName ARDDungeonGenerator::HeavenGood22(FName Like, bool bHeaven) const
{
	if (HeavenGoods22.Num() == 0 || !(bHeaven || InHeaven21())) return Like;
	const FName* T = HeavenGoods22.Find(Like);
	return T && FindItem(*T) >= 0 ? *T : Like;
}

bool ARDDungeonGenerator::IsHeavenTwin22(FName Item) const
{
	if (HeavenTwinsN22 != HeavenGoods22.Num())
	{
		HeavenTwins22.Reset();
		for (const TPair<FName, FName>& KV : HeavenGoods22) HeavenTwins22.Add(KV.Value);
		HeavenTwinsN22 = HeavenGoods22.Num();
	}
	return HeavenTwins22.Contains(Item);
}

TArray<FString> ARDDungeonGenerator::GetTownStock22() const
{
	TArray<FString> Out;
	for (const FName& N_ : TownStock()) Out.Add(N_.ToString());
	return Out;
}

// ------------------------------------------------------------------------------------------------ the pavements
void ARDSection::MakePave22() const
{
	if (Pave22.Num() == N * N) return;
	Pave22.Init(0, N * N); PaveTiles22.Reset();
	auto Asph = [&](const FIntPoint& T) { return In(T) && ((TownRoadMask.IsValidIndex(Idx(T)) && TownRoadMask[Idx(T)] == 1 && !TownSquare.Contains(T)) || ParkTiles19.Contains(Idx(T))); };
	auto Open = [&](const FIntPoint& T) { return In(T) && Type[Idx(T)] == 2 && Owner[Idx(T)] == 1000; };
	// (the zebras: a run's end tile across its street, where a run of four tiles or more meets a crossing (HeavenStreets19Build's rule))
	for (const FRun19& Ru : Runs19)
	{
		if (Ru.E - Ru.S < 4) continue;
		for (int32 End = 0; End < 2; ++End)
		{
			if (!(End == 0 ? Ru.bStartJ : Ru.bEndJ)) continue;
			const int32 Zc = End == 0 ? Ru.S : Ru.E - 1;
			for (int32 C = Ru.C0; C < Ru.C1; ++C)
			{
				const FIntPoint T = Ru.bX ? FIntPoint(Zc, C) : FIntPoint(C, Zc);
				if (Open(T) && !ParkTiles19.Contains(Idx(T))) Pave22[Idx(T)] = 2;
			}
		}
	}
	// (the pavement: open ground beside the asphalt, a tile or two from it; the square walked too)
	for (int32 Y = 0; Y < N; ++Y)
		for (int32 X = 0; X < N; ++X)
		{
			const FIntPoint T(X, Y);
			if (!Open(T) || Asph(T) || Pave22[Idx(T)] == 2) continue;
			int32 Near = 99;
			for (int32 Dx = -2; Dx <= 2; ++Dx)
				for (int32 Dy = -2; Dy <= 2; ++Dy)
					if (Asph(T + FIntPoint(Dx, Dy))) Near = FMath::Min(Near, FMath::Max(FMath::Abs(Dx), FMath::Abs(Dy)));
			if (Near <= 1) { Pave22[Idx(T)] = 1; if (!Blocked[Idx(T)]) PaveTiles22.Add(T); }
			else if (Near <= 2 || TownSquare.Contains(T)) Pave22[Idx(T)] = 3;
		}
}

uint8 ARDSection::PaveAt22(const FVector& W) const
{
	MakePave22();
	const FIntPoint T = WorldToLocal(W);
	return In(T) ? Pave22[Idx(T)] : 0;
}

bool ARDSection::FindPavePath22(const FVector& From, const FVector& To, TArray<FVector>& Out) const
{
	Out.Reset();
	MakePave22();
	auto Ok = [&](const FIntPoint& T) { return In(T) && Pave22[Idx(T)] != 0 && IsWalkable(T); };
	auto Snap = [&](FIntPoint& T)
	{
		if (Ok(T)) return true;
		for (int32 D = 1; D <= 2; ++D)
			for (int32 Dx = -D; Dx <= D; ++Dx)
				for (int32 Dy = -D; Dy <= D; ++Dy)
					if (Ok(T + FIntPoint(Dx, Dy))) { T = T + FIntPoint(Dx, Dy); return true; }
		return false;
	};
	FIntPoint A = WorldToLocal(From), B = WorldToLocal(To);
	if (!Snap(A) || !Snap(B)) return false;
	TArray<int32> Prev; Prev.Init(-1, N * N);
	TArray<FIntPoint> Q; Q.Reserve(512); Q.Add(A); Prev[Idx(A)] = Idx(A);
	for (int32 H = 0; H < Q.Num() && Q.Num() < 6000; ++H)
	{
		const FIntPoint T = Q[H];
		if (T == B) break;
		for (const FIntPoint& D : RDH22Dir4)
		{
			const FIntPoint U = T + D;
			if (!Ok(U) || Prev[Idx(U)] != -1) continue;
			// (onto a zebra only along it, across the street: never along the street from one zebra tile's side)
			Prev[Idx(U)] = Idx(T); Q.Add(U);
		}
	}
	if (Prev[Idx(B)] == -1) return false;
	TArray<FIntPoint> P;
	for (int32 C = Idx(B); ; C = Prev[C]) { P.Insert(FIntPoint(C % N, C / N), 0); if (C == Idx(A) || P.Num() > 220) break; }
	if (P.Num() > 200) return false;
	for (const FIntPoint& T : P) Out.Add(TileWorld(T));
	return true;
}

TArray<FString> ARDSection::GetPave22Lines() const
{
	MakePave22();
	int32 Cnt[4] = { 0, 0, 0, 0 };
	for (const uint8 V : Pave22) ++Cnt[FMath::Min<int32>(V, 3)];
	TArray<FString> Out;
	Out.Add(FString::Printf(TEXT("pave|%d|%d|%d|%d"), Cnt[1], Cnt[2], Cnt[3], PaveTiles22.Num()));
	return Out;
}

// ------------------------------------------------------------------------------------------------ the pedestrians
bool ARDDungeonGenerator::NextPavePath22(ARDTownsfolk* F, TArray<FVector>& Out) const
{
	const ARDSection* S = GetSection(FIntPoint::ZeroValue);
	if (!S || !F || !InHeaven21()) return false;
	S->MakePave22();
	if (S->PaveTiles22.Num() == 0) return false;
	const FVector L = F->GetActorLocation();
	const FVector Fw = F->GetActorForwardVector();
	FRandomStream R((int32)HashCombine(GetTypeHash(F->GetName()), (uint32)(F->Walks * 2654435761u)));
	// (a pavement's tile 15 to 60 m off, ahead of it more often than not: on along the street, or round a corner, or across at a zebra)
	for (int32 Try = 0; Try < 40; ++Try)
	{
		const int32 K = R.RandRange(0, S->PaveTiles22.Num() - 1);
		const FVector W = S->PaveTileWorld22(K);
		const float D = FVector::Dist2D(W, L);
		if (D < 1500.f || D > 6000.f) continue;
		if (Try < 25 && FVector::DotProduct((W - L).GetSafeNormal2D(), Fw) < -0.2f) continue;
		if (S->FindPavePath22(L, W, Out) && Out.Num() >= 2) return true;
	}
	return false;
}

void ARDTownsfolk::TickPave22(float Dt, float Now)
{
	const FVector L = GetActorLocation();
	if (Path.Num() == 0)
	{
		if (Now < NextTrip) { SetClip(false); return; }
		TArray<FVector> P;
		if (Gen && Gen->NextPavePath22(this, P) && P.Num() >= 2) { P.RemoveAt(0); for (FVector& Q : P) Q.Z = L.Z; Path = P; ++Walks; }
		else NextTrip = Now + R.FRandRange(1.f, 3.f);
		return;
	}
	FVector D = Path[0] - L; D.Z = 0.f;
	if (D.Size() < 40.f)
	{
		Path.RemoveAt(0);
		if (Path.Num() == 0) { SetClip(false); NextTrip = Now + R.FRandRange(0.5f, 5.f); }
		return;
	}
	const FVector Step = D.GetSafeNormal() * FMath::Min(Speed * Dt, D.Size());
	FHitResult Hit;
	SetActorLocation(L + Step, true, &Hit);
	if (Hit.bBlockingHit)
	{
		// (someone or something in the way: it waits a moment, then takes another way)
		SetClip(false);
		if (++PaveBlocked22 > 45) { Path.Reset(); PaveBlocked22 = 0; NextTrip = Now + R.FRandRange(0.5f, 2.f); }
		return;
	}
	PaveBlocked22 = 0;
	SetActorRotation(FRotator(0.f, FMath::RInterpConstantTo(GetActorRotation(), D.Rotation(), Dt, 300.f).Yaw, 0.f));
	SetClip(true);
}

int32 ARDDungeonGenerator::ClearPeds22()
{
	int32 N_ = 0;
	for (const TWeakObjectPtr<ARDTownsfolk>& P : Peds22) if (ARDTownsfolk* F = P.Get()) { TownPeople.Remove(F); F->Destroy(); ++N_; }
	Peds22.Reset();
	return N_;
}

void ARDDungeonGenerator::TickPeds22(const FVector& Her, ARDSection* S, bool bNight)
{
	// (gone: those beyond her reach, and at night those over the night's few out of her sight's 40 m)
	const int32 Want = CVarRDPeds22.GetValueOnGameThread() == 0 ? 0 : (bNight ? Peds22Night : Peds22Day);
	for (int32 I = Peds22.Num() - 1; I >= 0; --I)
	{
		ARDTownsfolk* F = Peds22[I].Get();
		const bool bFar = !F || FVector::Dist2D(F->GetActorLocation(), Her) > Peds22Reach * 1.35f;
		const bool bOver = F && Peds22.Num() > Want && (Want == 0 || FVector::Dist2D(F->GetActorLocation(), Her) > 4000.f);
		if (bFar || bOver)
		{
			if (F) { TownPeople.Remove(F); F->Destroy(); }
			Peds22.RemoveAt(I);
		}
	}
	if (Peds22.Num() >= Want || !GetWorld()) return;
	S->MakePave22();
	if (S->PaveTiles22.Num() == 0) return;
	// (their people: the town's own townsfolk, else the shared ones)
	const FString Here = bTownHome ? FString() : TownName;
	TArray<int32> Pool, Shared;
	for (int32 D = 0; D < Townsfolk.Num(); ++D)
	{
		const FRDTownsfolkDef& Df = Townsfolk[D];
		if (!Df.Mesh || Df.Role != ERDTownRole::Townsfolk) continue;
		if (Df.Town == Here && !Here.IsEmpty()) Pool.Add(D); else if (Df.Town.IsEmpty()) Shared.Add(D);
	}
	if (Pool.Num() == 0) Pool = Shared;
	if (Pool.Num() == 0) return;
	FRandomStream R((int32)HashCombine((uint32)StartSeed ^ 0x9EDu, (uint32)PedsMade22 * 2654435761u));
	FActorSpawnParameters Sp; Sp.SpawnCollisionHandlingOverride = ESpawnActorCollisionHandlingMethod::AlwaysSpawn;
	// (a few a look, on a pavement's tile 25 m and more from her (out of her face) and within her reach)
	for (int32 K = 0, Tries = 0; K < 4 && Peds22.Num() < Want && Tries < 60; ++Tries)
	{
		const int32 Ti = R.RandRange(0, S->PaveTiles22.Num() - 1);
		const FVector W = S->PaveTileWorld22(Ti);
		const float D = FVector::Dist2D(W, Her);
		if (D < 2500.f || D > Peds22Reach) continue;
		bool bTaken = false;
		for (const TWeakObjectPtr<ARDTownsfolk>& O : Peds22) if (O.IsValid() && FVector::Dist2D(O->GetActorLocation(), W) < 300.f) bTaken = true;
		if (bTaken) continue;
		const FVector At = W + FVector(0, 0, 92.f);
		ARDTownsfolk* F = GetWorld()->SpawnActor<ARDTownsfolk>(ARDTownsfolk::StaticClass(), FTransform(FRotator(0, R.FRandRange(0.f, 360.f), 0), At), Sp);
		if (!F) continue;
		F->Init(this, S, Pool[R.RandRange(0, Pool.Num() - 1)], At, 0.f, 0.f, HashCombine((uint32)StartSeed, (uint32)(++PedsMade22) * 7919u));
		F->bPave22 = true;
		F->SetTitle(FString::Printf(TEXT("%s out walking"), *F->Title));
		Peds22.Add(F); TownPeople.Add(F);
		++K;
	}
}

// ------------------------------------------------------------------------------------------------ the city's sound
void ARDDungeonGenerator::TickCitySound22(float Dt, const FVector& Her, ARDSection* S, bool bIn, bool bNight)
{
	const bool bOn = bIn && CVarRDCity22.GetValueOnGameThread() != 0;
	auto Loop = [&](TObjectPtr<UAudioComponent>& A, FName Key, float Vol, FName& Was) -> float
	{
		const FRDSoundSet* Set = Sounds.Find(Key);
		if (!Set || Set->Sounds.Num() == 0) return 0.f;
		if (!A)
		{
			A = NewObject<UAudioComponent>(this);
			A->bAutoActivate = false; A->bAutoDestroy = false; A->bAllowSpatialization = false;
			A->SetupAttachment(RootComponent); A->RegisterComponent();
		}
		const float Target = Vol * Set->Volume * UserVolumeOf(TEXT("Atmos.Explore"));
		if (Vol <= 0.001f) { if (A->IsPlaying()) A->FadeOut(2.f, 0.f); Was = NAME_None; return 0.f; }
		if (Was != Key || !A->IsPlaying())
		{
			// (one of its loops by the session's seed; a new one when the day turns to night)
			USoundBase* Snd = Set->Sounds[FMath::Abs(SessionSeed + (int32)GetTypeHash(Key)) % Set->Sounds.Num()];
			if (USoundWave* Wv = Cast<USoundWave>(Snd)) Wv->bLooping = true;
			A->SetSound(Snd); A->FadeIn(2.5f, Target); Was = Key;
		}
		else A->AdjustVolume(0.5f, Target);
		return Target;
	};
	FName Key = bNight && HasSound(TEXT("Heaven.CityNight")) ? FName(TEXT("Heaven.CityNight")) : FName(TEXT("Heaven.City"));
	CityVol22 = Loop(CityAudio22, Key, bOn ? 1.f : 0.f, CityKey22);
	// (the crowd: near the square and the market, by day)
	float CrowdShare = 0.f;
	if (bOn && !bNight && S)
	{
		const FVector Sq = S->LocalToWorld(FIntPoint((S->TownSquare.Min.X + S->TownSquare.Max.X) / 2, (S->TownSquare.Min.Y + S->TownSquare.Max.Y) / 2));
		const float D = FVector::Dist2D(Sq, Her);
		CrowdShare = 1.f - FMath::Clamp((D - CrowdReach22.X) / FMath::Max(CrowdReach22.Y - CrowdReach22.X, 1.f), 0.f, 1.f);
	}
	CrowdVol22 = Loop(CrowdAudio22, TEXT("Heaven.Crowd"), CrowdShare, CrowdKey22);
	if (!bOn || !S) return;
	const float Now = GetWorld()->GetTimeSeconds();
	// (a horn now and then from a car in the streets 15 to 80 m off; a car passing close by heard once a pass)
	// (a wait longer than the range now allows is drawn again: the range was shortened)
	if (HornAt22 < 0.f || HornAt22 > Now + HornEvery22.Y) HornAt22 = Now + FMath::FRandRange(HornEvery22.X, HornEvery22.Y);
	TArray<FVector> Cars; TArray<int32> CarIx;
	for (int32 I = 0; I < S->HeavenCars.Num(); ++I) if (const USceneComponent* C = S->HeavenCars[I].C.Get()) { Cars.Add(C->GetComponentLocation()); CarIx.Add(I); }
	if (Now >= HornAt22 && !bNight)
	{
		HornAt22 = Now + FMath::FRandRange(HornEvery22.X, HornEvery22.Y);
		TArray<int32> Pick;
		for (int32 I = 0; I < Cars.Num(); ++I) { const float D = FVector::Dist2D(Cars[I], Her); if (D > 1500.f && D < 8000.f) Pick.Add(I); }
		if (Pick.Num() > 0 && PlaySoundAt(TEXT("Heaven.Horn"), Cars[Pick[FMath::RandRange(0, Pick.Num() - 1)]] + FVector(0, 0, 100.f))) ++Horns22;
	}
	if (Now >= PassByAt22)
		for (int32 I = 0; I < Cars.Num(); ++I)
		{
			if (FVector::Dist2D(Cars[I], Her) > 1000.f) continue;
			if (const float* T = CarPassed22.Find(CarIx[I]); T && Now - *T < 20.f) continue;
			CarPassed22.Add(CarIx[I], Now);
			if (PlaySoundAt(TEXT("Heaven.PassBy"), Cars[I] + FVector(0, 0, 80.f))) { ++PassBys22; PassByAt22 = Now + 5.f; }
			break;
		}
}

// ------------------------------------------------------------------------------------------------ the generator's look at Heaven
void ARDDungeonGenerator::TickHeaven22(float Dt)
{
	if (TownPlan != 5) return;
	ARDSection* S = GetSection(FIntPoint::ZeroValue);
	const APawn* P = UGameplayStatics::GetPlayerPawn(this, 0);
	const bool bHeaven = S && !S->IsBuilding() && InHeaven21();
	const FVector Her = P ? P->GetActorLocation() : FVector::ZeroVector;
	const bool bIn = bHeaven && P && IsInTownWalls(Her);
	const bool bNight = IsStreetNight16();
	// (the pedestrians on the street: the cars wait for them, every frame)
	if (S)
	{
		S->CarYield22.Reset();
		for (const TWeakObjectPtr<ARDTownsfolk>& F : Peds22)
			if (const ARDTownsfolk* Fk = F.Get()) { const uint8 K = S->PaveAt22(Fk->GetActorLocation()); if (K == 2 || K == 0) S->CarYield22.Add(Fk->GetActorLocation()); }
	}
	Heaven22Clock -= Dt;
	if (Heaven22Clock > 0.f) return;
	Heaven22Clock = 0.5f;
	if (!bHeaven)
	{
		if (Peds22.Num() > 0) ClearPeds22();
		TickCitySound22(0.5f, Her, nullptr, false, bNight);
		return;
	}
	// ---- the neon and the billboards: gathered once a town (by their tags), lit at night
	// (again every 5 s: a restart's replan makes the faces anew (RestartPlay clears the interactive pieces))
	bool bStale = S != Heaven22Of.Get();
	for (const TWeakObjectPtr<UStaticMeshComponent>& B : Boards22) if (!B.IsValid()) bStale = true;
	if (bStale || (BoardsN22 -= 1) <= 0)
	{
		if (S != Heaven22Of.Get()) CarPassed22.Reset();
		Heaven22Of = S; Boards22.Reset(); Neon22Lit = -1; BoardsN22 = 10; BoardGlowNow22 = NeonLitNow22 = -1.f;
		if (!S->Neon22.IsValid())
			for (UActorComponent* C : S->GetComponentsByTag(UInstancedStaticMeshComponent::StaticClass(), TEXT("HeavenNeon22"))) { S->Neon22 = Cast<UInstancedStaticMeshComponent>(C); break; }
		for (UActorComponent* C : S->GetComponentsByTag(UStaticMeshComponent::StaticClass(), TEXT("HeavenBoard22")))
			if (UStaticMeshComponent* M = Cast<UStaticMeshComponent>(C)) { if (!Cast<UMaterialInstanceDynamic>(M->GetMaterial(0))) M->CreateAndSetMaterialInstanceDynamic(0); Boards22.Add(M); }
	}
	const bool bLit = bNight && CVarRDNeon22.GetValueOnGameThread() != 0;
	if ((bLit ? 1 : 0) != Neon22Lit)
	{
		Neon22Lit = bLit ? 1 : 0;
		NeonLitNow22 = CVarRDNeon22.GetValueOnGameThread() == 0 ? 0.f : (bLit ? 1.f : NeonDay22);
		if (UInstancedStaticMeshComponent* I = S->Neon22.Get())
		{
			for (int32 K = 0; K < I->GetInstanceCount(); ++K) I->SetCustomDataValue(K, 3, NeonLitNow22, false);
			I->MarkRenderStateDirty();
		}
		BoardGlowNow22 = CVarRDNeon22.GetValueOnGameThread() == 0 ? 0.f : (bLit ? BoardGlow22.Y : BoardGlow22.X);
		for (const TWeakObjectPtr<UStaticMeshComponent>& B : Boards22)
			if (UStaticMeshComponent* M = B.Get()) if (UMaterialInstanceDynamic* Md = Cast<UMaterialInstanceDynamic>(M->GetMaterial(0))) Md->SetScalarParameterValue(TEXT("Glow"), BoardGlowNow22);
		UE_LOG(LogRDHeaven22, Log, TEXT("RDHEAVEN22 neon %s: %d tubes, %d billboards (%.1f h)"), bLit ? TEXT("lit") : TEXT("dim"), S->Neon22.IsValid() ? S->Neon22->GetInstanceCount() : 0, Boards22.Num(), TownHour);
	}
	// ---- the neon's hum near her at night: the nearest tube within 12 m
	bNeonHum22 = false;
	if (bLit && bIn && CVarRDCity22.GetValueOnGameThread() != 0)
		if (const UInstancedStaticMeshComponent* I = S->Neon22.Get())
		{
			float Best = 1200.f; FVector At = FVector::ZeroVector;
			for (int32 K = 0; K < I->GetInstanceCount(); K += 4)
			{
				FTransform T; I->GetInstanceTransform(K, T, true);
				const float D = FVector::Dist(T.GetLocation(), Her);
				if (D < Best) { Best = D; At = T.GetLocation(); }
			}
			if (Best < 1200.f)
				if (const FRDSoundSet* Set = Sounds.Find(TEXT("Heaven.Neon")); Set && Set->Sounds.Num() > 0)
				{
					if (!NeonAudio22) { NeonAudio22 = NewObject<UAudioComponent>(this); NeonAudio22->bAutoActivate = false; NeonAudio22->SetupAttachment(RootComponent); NeonAudio22->RegisterComponent(); }
					if (!NeonAudio22->IsPlaying())
					{
						if (USoundWave* Wv = Cast<USoundWave>(Set->Sounds[0])) Wv->bLooping = true;
						NeonAudio22->SetSound(Set->Sounds[0]);
						FSoundAttenuationSettings At_; At_.bAttenuate = true; At_.bSpatialize = AreSoundsSpatialized();
						At_.AttenuationShapeExtents = FVector(Set->InnerRadius); At_.FalloffDistance = Set->FalloffDistance;
						NeonAudio22->bOverrideAttenuation = true; NeonAudio22->AttenuationOverrides = At_;
						NeonAudio22->FadeIn(1.f, Set->Volume * UserVolumeOf(TEXT("Heaven.Neon")));
					}
					NeonAudio22->SetWorldLocation(At);
					bNeonHum22 = true;
				}
		}
	if (!bNeonHum22 && NeonAudio22 && NeonAudio22->IsPlaying()) NeonAudio22->FadeOut(1.f, 0.f);
	// ---- the pedestrians, once a second
	PedsClock22 -= 0.5f;
	if (PedsClock22 <= 0.f) { PedsClock22 = 1.f; if (bIn) TickPeds22(Her, S, bNight); else if (Peds22.Num() > 0 && !bIn) TickPeds22(Her, S, bNight); }
	TickCitySound22(0.5f, Her, S, bIn, bNight);
}

TArray<FString> ARDDungeonGenerator::GetHeaven22Lines() const
{
	TArray<FString> Out;
	const ARDSection* S = GetSection(FIntPoint::ZeroValue);
	int32 Zebra = 0, Road = 0, Alive = 0;
	for (const TWeakObjectPtr<ARDTownsfolk>& F : Peds22)
		if (const ARDTownsfolk* Fk = F.Get())
		{
			++Alive;
			const uint8 K = S ? S->PaveAt22(Fk->GetActorLocation()) : 0;
			if (K == 2) ++Zebra; else if (K == 0) ++Road;
		}
	const int32 Tubes = S && S->Neon22.IsValid() ? S->Neon22->GetInstanceCount() : 0;
	const APawn* P = UGameplayStatics::GetPlayerPawn(this, 0);
	Out.Add(FString::Printf(TEXT("life22|%d|%d|%d|%d|%.2f|%d|%.2f|%s|%.3f|%.3f|%d|%d|%d|%d|%d"), Alive, Zebra, Road, Tubes, NeonLitNow22, Boards22.Num(), BoardGlowNow22,
		*CityKey22.ToString(), CityVol22, CrowdVol22, Horns22, PassBys22, IsStreetNight16() ? 1 : 0, InHeaven21() ? 1 : 0, bNeonHum22 ? 1 : 0));
	for (const TWeakObjectPtr<ARDTownsfolk>& F : Peds22)
		if (const ARDTownsfolk* Fk = F.Get())
		{
			const FVector L = Fk->GetActorLocation();
			Out.Add(FString::Printf(TEXT("ped|%.0f|%.0f|%.0f|%d|%d|%d|%s"), L.X, L.Y, L.Z, S ? S->PaveAt22(L) : 0, Fk->IsWalking() ? 1 : 0, Fk->Walks, *Fk->GetName()));
		}
	return Out;
}

// ------------------------------------------------------------------------------------------------ the fronts: neon over the door
void ARDSection::HeavenFront22(int32 BI, float Hx, float Hy, int32 DoorK, float Yaw0)
{
	if (!TownBlds.IsValidIndex(BI)) return;
	const FTownBld& B = TownBlds[BI];
	const float M = Generator->TileSize;
	// (the trades' fronts: a shop by its kind, the market, the hotel, the clinic, the gear shop; each its colour)
	FLinearColor Col;
	switch (B.Kind)
	{
	case TK_Shop: { const int32 K = ShopKind21(BI); Col = K == 0 ? FLinearColor(0.1f, 1.f, 0.25f) : K == 1 ? FLinearColor(0.1f, 0.85f, 1.f) : FLinearColor(1.f, 0.45f, 0.05f); break; }
	case TK_Store: Col = FLinearColor(1.f, 0.1f, 0.75f); break;
	case TK_Tavern: Col = FLinearColor(1.f, 0.12f, 0.2f); break;
	case TK_Healer: Col = FLinearColor(0.2f, 0.6f, 1.f); break;
	case TK_Smithy: Col = FLinearColor(1.f, 0.75f, 0.1f); break;
	default: return;
	}
	const FRDPiece* Tp = Generator->Piece(TEXT("Heaven.Neon22"));
	if (!Tp || !Tp->Mesh) return;
	// (a frame of tubes on the wall's face over the door: two along the front 2.6 m long, two upright 50 cm at their ends; the tube's
	// mesh is a 100 cm bar along its X; the front is the building's +X, the door at its DoorK tile)
	// (on the wall's outer face as its piece measures (Heaven's modern walls stand thicker than the 13 cm the first frame stood out by:
	// it was inside them, unseen), 6 cm out from it)
	float Face = 13.f;
	if (const FRDPiece* Wp = Pc(TownPiece(B, TEXT("Wall"))); Wp && Wp->Mesh)
		Face = FMath::Max(0.f, (float)Wp->Mesh->GetBoundingBox().TransformBy(Wp->Adjust).Max.X) + 6.f;
	const float Dy = (DoorK + 0.5f) * M - Hy, Fx = Hx + Face;
	const float Z0 = 268.f, Z1 = 318.f, W = 130.f;
	const FVector Mid = TownBldPoint(B, Fx, Dy, (Z0 + Z1) * 0.5f);
	Fronts22.Add(FString::Printf(TEXT("front|%d|%d|4|%.2f|%.2f|%.2f|%.0f|%.0f|%.0f|%.1f|%.1f"), BI, (int32)B.Kind, Col.R, Col.G, Col.B, Mid.X, Mid.Y, Mid.Z, Yaw0, Face));
	// (the tubes are the static build's: a replan with static building off (RestartPlay) keeps them, found again by their tag)
	if (!bBuildStatic) return;
	UInstancedStaticMeshComponent* I = Neon22.Get();
	if (!I)
	{
		I = NewObject<UInstancedStaticMeshComponent>(this, NAME_None, RF_Transactional);
		I->SetStaticMesh(Tp->Mesh);
		if (Tp->Material) I->SetMaterial(0, Tp->Material);
		I->SetNumCustomDataFloats(4);
		I->SetCollisionEnabled(ECollisionEnabled::NoCollision);
		I->SetCastShadow(false);
		I->SetupAttachment(RootComponent);
		I->ComponentTags.Add(TEXT("HeavenNeon22"));
		I->RegisterComponent();
		AddInstanceComponent(I);
		Neon22 = I;
	}
	const FRotator Ry(0, Yaw0 + 90.f, 0), Rz(90.f, Yaw0, 0);
	const FTransform Ts[4] = {
		// (8 cm thick: at 4 cm a front's neon was a few pixels from across the street, its light lost in the picture)
		FTransform(Ry, TownBldPoint(B, Fx, Dy, Z0), FVector(2.f * W / 100.f, 2.f, 2.f)),
		FTransform(Ry, TownBldPoint(B, Fx, Dy, Z1), FVector(2.f * W / 100.f, 2.f, 2.f)),
		FTransform(Rz, TownBldPoint(B, Fx, Dy - W, (Z0 + Z1) * 0.5f), FVector((Z1 - Z0) / 100.f, 2.f, 2.f)),
		FTransform(Rz, TownBldPoint(B, Fx, Dy + W, (Z0 + Z1) * 0.5f), FVector((Z1 - Z0) / 100.f, 2.f, 2.f)) };
	const float Lit = Generator->NeonDay22;
	for (const FTransform& T : Ts)
	{
		const int32 K = I->AddInstance(T, true);
		const float Data[4] = { Col.R, Col.G, Col.B, Lit };
		I->SetCustomData(K, TArrayView<const float>(Data, 4), false);
	}
	I->MarkRenderStateDirty();
}

// ------------------------------------------------------------------------------------------------ the billboards on the roofs
void ARDSection::HeavenBillboard22(int32 BI, float Top, float Hx, float Hy, float Yaw0)
{
	if (!TownBlds.IsValidIndex(BI) || Generator->BillboardFaces22 <= 0) return;
	const FTownBld& B = TownBlds[BI];
	// (one roof in three of the low buildings wide enough for its 6.4 m face, by the building's seed; not the towers, not the facility)
	if (B.Kind == TK_SkyTower || BI == CastleBld || B.Storeys > 3 || B.bBoarded) return;
	if (Hy * 2.f < 760.f || Hx * 2.f < 600.f) return;
	const uint32 H = HashCombine(B.Seed, 0xB111B0A2u);
	if (H % 3u != 0u) return;
	const FRDPiece* Fr = Generator->Piece(TEXT("Heaven.Billboard22"));
	const int32 Fi = (int32)((H >> 4) % (uint32)Generator->BillboardFaces22);
	const FName FaceN(*FString::Printf(TEXT("Heaven.BillboardFace22_%d"), Fi));
	const FRDPiece* Fc = Generator->Piece(FaceN);
	if (!Fr || !Fr->Mesh || !Fc || !Fc->Mesh) return;
	// (its legs on the roof 1.2 m in from the front's parapet, facing out over the street; never over a core's way up)
	const FVector At = TownBldPoint(B, Hx - 120.f, 0.f, Top);
	for (const float Ly : { -280.f, 0.f, 280.f }) if (InCore20(TownBldPoint(B, Hx - 120.f, Ly, Top))) return;
	const FTransform T(FRotator(0, Yaw0, 0), At);
	Fronts22.Add(FString::Printf(TEXT("board|%d|%.0f|%.0f|%.0f|%.0f|%d"), BI, At.X, At.Y, At.Z, Yaw0, Fi));
	// (the frame is the static build's; the face an interactive piece (its own material instance, lit at night): made again by a replan
	// with static building off, as RestartPlay clears the interactive pieces)
	AddPiece(TEXT("Heaven.Billboard22"), T, false);
	if (!bBuildInteractive) return;
	UStaticMeshComponent* C = AddMesh(RootComponent, Fc->Mesh, Fc->Adjust * T * GetActorTransform().Inverse(), false);
	if (!C) return;
	if (Fc->Material) C->SetMaterial(0, Fc->Material);
	C->SetCastShadow(false);
	C->ComponentTags.Add(TEXT("HeavenBoard22"));
}
