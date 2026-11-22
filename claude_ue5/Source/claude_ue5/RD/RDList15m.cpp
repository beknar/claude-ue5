// The user's list of 2026-11-20 (docs/improvements15.txt; the plan docs/improvements15_plan.md), its fourteenth phase: camps cleared that
// change the world (docs/wilderness_ideas.md's idea 6).
//   - A camp to clear is a plain lair ("<beast> Lair") or hollow ("<name> Hollow": the spawn points): no quest's, structure's or town's.
//     Once every one of its monsters is dead (their keys in WildKilled), it is cleared for the game: a waypoint is laid there as she comes
//     (a fire, a tent to rest in until morning, a trader by his cart who opens the store); found, it is a place to travel to on the map.
//   - ReclaimDays15 days after a camp is cleared, a household moves into the nearest ordinary ruin within ReclaimRuinKm15: its guardians
//     are gone for good and its people stand round a fire at its middle, with their own lines.
//   - The big map shows each region with a cleared camp its share reclaimed ("2 of 7 camps reclaimed").
// Every one on a stream and ids of its own: nothing else moves.
#include "RD/RDDungeonGenerator.h"
#include "RD/RDWild.h"
#include "RD/RDGameInstance.h"
#include "RD/RDCombat.h"
#include "RD/RDTown.h"
#include "Components/StaticMeshComponent.h"
#include "Components/PointLightComponent.h"
#include "NiagaraFunctionLibrary.h"
#include "NiagaraComponent.h"
#include "Kismet/GameplayStatics.h"
#include "Engine/World.h"
DEFINE_LOG_CATEGORY_STATIC(LogRDList15m, Log, All);

bool ARDDungeonGenerator::IsClearableCamp15(const FRDWildPlace& P) const
{
	return (P.Kind == TEXT("lair") || P.Kind == TEXT("spawn")) && P.Quest.IsEmpty() && P.Site < 0 && P.Town < 0 && P.Id < FRDWildWorld::QuestIdBase;
}

int32 ARDDungeonGenerator::WildPlaceMonsterCount15(const FRDWildPlace& P) const
{
	// (SpawnWildMonsters' own draws on the place's stream: the kind first (one draw whatever the range), then the number; a lair 3 to 5,
	// a hollow 2 or 3)
	FRandomStream R((int32)FRDWildWorld::Hash(P.Id, 91, Wild->Seed));
	R.RandRange(0, 0);
	return P.Kind == TEXT("lair") ? R.RandRange(3, 5) : R.RandRange(2, 3);
}

bool ARDDungeonGenerator::CampCleared15(const FRDWildPlace& P) const
{
	const URDGameInstance* GI = URDGameInstance::Of(this);
	if (!GI || !IsClearableCamp15(P)) return false;
	TArray<int32> Kinds; WildKindsForTier(P.Tier, Kinds);
	if (Kinds.Num() == 0 || !bCombat) return false;          // (no monsters were ever laid there: nothing to clear)
	const int32 N = WildPlaceMonsterCount15(P);
	for (int32 I = 0; I < N; ++I) if (!GI->WildKilled.Contains((int64)P.Id * 16 + I)) return false;
	return true;
}

int32 ARDDungeonGenerator::CampClearedDay15(int32 Id) const
{
	const URDGameInstance* GI = URDGameInstance::Of(this);
	const int32 I = GI ? GI->CampsCleared15.IndexOfByKey(Id) : INDEX_NONE;
	return I != INDEX_NONE && GI->CampsClearedDay15.IsValidIndex(I) ? GI->CampsClearedDay15[I] : -1;
}

void ARDDungeonGenerator::TickReclaim15(float Dt, const FVector& Her)
{
	ReclaimLook15 -= Dt;
	if (ReclaimLook15 > 0.f || !IsWildReady() || ReclaimDays15 <= 0.f) return;
	ReclaimLook15 = 1.f;
	URDGameInstance* GI = URDGameInstance::Of(this);
	if (!GI) return;
	const FVector2D H2(Her.X / 100.0, Her.Y / 100.0);
	// (the camps within 300 m: cleared ones recorded for the game, told and autosaved)
	TArray<FRDWildPlace> Ps;
	const FIntPoint P0 = Wild->PlaceCellOf(H2.X - 300.0, H2.Y - 300.0), P1 = Wild->PlaceCellOf(H2.X + 300.0, H2.Y + 300.0);
	for (int32 I = P0.X; I <= P1.X; ++I) for (int32 J = P0.Y; J <= P1.Y; ++J) Wild->PlacesIn(FIntPoint(I, J), Ps);
	TSet<int32> WantCamps, WantRuins;
	for (const FRDWildPlace& P : Ps)
	{
		const double D = FVector2D::Distance(P.At, H2);
		if (D > 300.0) continue;
		if (IsClearableCamp15(P))
		{
			if (!GI->CampsCleared15.Contains(P.Id) && CampCleared15(P))
			{
				GI->CampsCleared15.Add(P.Id); GI->CampsClearedDay15.Add(TownDay);
				ReclaimShareCache15.Reset();
				if (PlayerCombat) PlayerCombat->ShowMessage(FString::Printf(TEXT("%s is cleared: travellers will camp here, and in a few days people may settle the ruins nearby"), *P.Name));
				UE_LOG(LogRDList15m, Log, TEXT("RDRECLAIM15 %s cleared on day %d"), *P.Name, TownDay);
				WildAutosave(TEXT("found"));
			}
			if (GI->CampsCleared15.Contains(P.Id) && D < 200.0) WantCamps.Add(P.Id);
		}
		if (P.Kind == TEXT("ruins") && GI->RuinsResettled15.Contains(P.Id) && D < 200.0) WantRuins.Add(P.Id);
	}
	for (const int32 Id : WantCamps) if (!CampsLaid15.Contains(Id)) { FRDWildPlace P; if (Wild->FindPlace(Id, P)) LayCampWaypoint15(P); }
	for (const int32 Id : WantRuins) if (!RuinsLaid15.Contains(Id)) { FRDWildPlace P; if (Wild->FindPlace(Id, P)) LayRuinFolk15(P); }
	auto Drop = [](FReclaimLaid15& L) { for (TWeakObjectPtr<USceneComponent>& C : L.Comps) if (C.IsValid()) C->DestroyComponent(); for (TWeakObjectPtr<AActor>& A : L.Folk) if (A.IsValid()) A->Destroy(); };
	for (auto It = CampsLaid15.CreateIterator(); It; ++It) if (!WantCamps.Contains(It.Key()) && FVector2D::Distance(It.Value().At2, H2) > 350.0) { Drop(It.Value()); It.RemoveCurrent(); }
	for (auto It = RuinsLaid15.CreateIterator(); It; ++It) if (!WantRuins.Contains(It.Key()) && FVector2D::Distance(It.Value().At2, H2) > 350.0) { Drop(It.Value()); It.RemoveCurrent(); }
	// (the days since each camp was cleared: its nearest ordinary ruin resettled once ReclaimDays15 have passed)
	for (int32 I = 0; I < GI->CampsCleared15.Num(); ++I)
	{
		const int32 Id = GI->CampsCleared15[I];
		if (GI->CampsResettledFrom15.Contains(Id) || !GI->CampsClearedDay15.IsValidIndex(I) || TownDay - GI->CampsClearedDay15[I] < FMath::RoundToInt(ReclaimDays15)) continue;
		GI->CampsResettledFrom15.Add(Id);          // (looked for once: a camp with no ruin near is passed by for good)
		FRDWildPlace C; FRDWildPlace Got; FVector2D At;
		if (!Wild->FindPlace(Id, C)) continue;
		if (!FindNearestWildPlace(C.At.X, C.At.Y, ReclaimRuinKm15, [&](const FRDWildPlace& P, FVector2D& A)
			{ if (P.Kind != TEXT("ruins") || !P.Quest.IsEmpty() || P.Site >= 0 || P.Id >= FRDWildWorld::QuestIdBase || GI->RuinsResettled15.Contains(P.Id)) return false; A = P.At; return true; }, Got, At))
		{
			UE_LOG(LogRDList15m, Log, TEXT("RDRECLAIM15 %s: no ordinary ruin within %.1f km to resettle"), *C.Name, ReclaimRuinKm15);
			continue;
		}
		GI->RuinsResettled15.Add(Got.Id);
		// (its guardians gone for good: every key of its place's monsters taken, as kills kept)
		for (int32 K = 0; K < 16; ++K) GI->WildKilled.Add((int64)Got.Id * 16 + K);
		ReclaimShareCache15.Reset();
		if (PlayerCombat) PlayerCombat->ShowMessage(FString::Printf(TEXT("Word on the road: with %s cleared, a family has settled the %s"), *C.Name, *Got.Name));
		UE_LOG(LogRDList15m, Log, TEXT("RDRECLAIM15 %s resettled on day %d (%s cleared on day %d)"), *Got.Name, TownDay, *C.Name, GI->CampsClearedDay15[I]);
	}
}

void ARDDungeonGenerator::LayCampWaypoint15(const FRDWildPlace& P)
{
	// (by the camp's middle: a fire with its light, a tent to rest in, a trader by his cart; laid in its own frame by the camp's yaw)
	FReclaimLaid15 L; L.At2 = P.At;
	const float Yaw = P.Yaw;
	const FVector2D Fw(FMath::Cos(FMath::DegreesToRadians(Yaw)), FMath::Sin(FMath::DegreesToRadians(Yaw))), Rt(-Fw.Y, Fw.X);
	auto Ground = [this](const FVector2D& M) { return FVector(M.X * 100.0, M.Y * 100.0, WildGroundZ(FVector(M.X * 100.0, M.Y * 100.0, 0.0))); };
	auto Put = [&](const TCHAR* Prefix, const FVector2D& M, float Y, int32 Pick, float Sink) -> UStaticMeshComponent*
	{
		TArray<UStaticMesh*> Ms; WildPiecesOf(Prefix, Ms);
		if (Ms.Num() == 0) return nullptr;
		UStaticMesh* Sm = Ms[FMath::Abs(Pick) % Ms.Num()];
		const float* Ks = WildPieceScale.Find(FName(*Sm->GetName()));
		const float Sc = Ks ? *Ks : 1.f;
		UStaticMeshComponent* C = NewObject<UStaticMeshComponent>(this);
		C->SetStaticMesh(Sm);
		C->SetCollisionEnabled(ECollisionEnabled::QueryAndPhysics); C->SetCollisionResponseToAllChannels(ECR_Block);
		C->RegisterComponent();
		C->SetWorldTransform(FTransform(FRotator(0.f, Y, 0.f), Ground(M) - FVector(0, 0, Sink * Sc), FVector(Sc)));
		L.Comps.Add(C);
		return C;
	};
	const FVector2D Fire = P.At + Fw * 6.0;
	if (UStaticMeshComponent* F = Put(TEXT("campfire"), Fire, 0.f, 0, 2.f))
	{
		F->SetCollisionEnabled(ECollisionEnabled::NoCollision);
		if (WildFireFx) if (UNiagaraComponent* Fx = UNiagaraFunctionLibrary::SpawnSystemAttached(WildFireFx, F, NAME_None, FVector(0, 0, 25.f), FRotator::ZeroRotator, EAttachLocation::KeepRelativeOffset, true)) L.Comps.Add(Fx);
		UPointLightComponent* Lt = NewObject<UPointLightComponent>(this);
		Lt->SetIntensityUnits(ELightUnits::Candelas); Lt->SetIntensity(40.f); Lt->SetAttenuationRadius(1400.f); Lt->SetLightColor(FLinearColor(1.f, 0.55f, 0.22f)); Lt->SetCastShadows(false);
		Lt->RegisterComponent(); Lt->SetWorldLocation(F->GetComponentLocation() + FVector(0, 0, 60.f));
		L.Comps.Add(Lt);
	}
	const FVector2D Tent = Fire + Rt * 6.0 + Fw * 2.0, Cart = Fire - Rt * 6.0;
	Put(TEXT("tent"), Tent, Yaw + 180.f, P.Id, 2.f);
	Put(TEXT("cart"), Cart, Yaw + 90.f, 0, 2.f);
	for (int32 K = 0; K < 2; ++K) if (UStaticMeshComponent* Lg = Put(TEXT("log"), Fire + (K ? Rt : -Rt) * 2.2 - Fw * 1.5, Yaw + 90.f, K, 0.f)) Lg->SetCollisionEnabled(ECollisionEnabled::NoCollision);
	L.TentAt = Ground(Tent - Rt * 2.2);          // (its door's side, toward the fire)
	// (the trader by his cart, facing the fire)
	const FVector2D TraderAt = Cart + Rt * 2.0;
	if (ARDTownsfolk* T = SpawnReclaimFolk15(TraderAt, Yaw - 90.f, (uint32)P.Id * 7u + 1u, ReclaimTraderDef15, TEXT("a travelling trader"), ReclaimTraderLines15))
	{
		L.Folk.Add(T); L.TraderAt = T->GetActorLocation();
	}
	CampsLaid15.Add(P.Id, L);
	UE_LOG(LogRDList15m, Log, TEXT("RDRECLAIM15 the waypoint at %s laid (%d pieces, %s)"), *P.Name, L.Comps.Num(), L.Folk.Num() ? TEXT("a trader") : TEXT("no trader"));
}

ARDTownsfolk* ARDDungeonGenerator::SpawnReclaimFolk15(const FVector2D& At, float Yaw, uint32 Seed, const FString& Def, const FString& Title, const TArray<FString>& Lines)
{
	if (Townsfolk.Num() == 0 || !GetWorld()) return nullptr;
	int32 D = Townsfolk.IndexOfByPredicate([&](const FRDTownsfolkDef& X) { return X.Mesh && !Def.IsEmpty() && X.Name.ToString().StartsWith(Def); });
	if (D < 0) D = Townsfolk.IndexOfByPredicate([&](const FRDTownsfolkDef& X) { return X.Mesh && X.Name.ToString().StartsWith(TEXT("Townsman")); });
	if (D < 0) return nullptr;
	const FVector Q(At.X * 100.0, At.Y * 100.0, WildGroundZ(FVector(At.X * 100.0, At.Y * 100.0, 0.0)) + 92.f);
	FActorSpawnParameters Sp; Sp.SpawnCollisionHandlingOverride = ESpawnActorCollisionHandlingMethod::AlwaysSpawn;
	ARDTownsfolk* T = GetWorld()->SpawnActor<ARDTownsfolk>(ARDTownsfolk::StaticClass(), FTransform(FRotator(0, Yaw, 0), Q), Sp);
	if (!T) return nullptr;
	T->Init(this, nullptr, D, Q, Yaw, 0.f, Seed);
	T->SetTitle(Title);
	T->OwnLines = Lines;
	T->bWildGiven = true;
	return T;
}

void ARDDungeonGenerator::LayRuinFolk15(const FRDWildPlace& P)
{
	// (the household round a fire at the ruin's middle: two to four of them, by the ruin's hash)
	FReclaimLaid15 L; L.At2 = P.At;
	// (off the ruin's pieces, as its guards are (PR #56's rule): its middle can be inside its keep, and the first fire and settlers stood
	// inside the tower)
	const FRuinLaid* Rl = WildRuinsLaid.FindByPredicate([&](const FRuinLaid& X) { return X.Id == P.Id; });
	auto Clear = [&](const FVector2D& Want, float RadCm) -> FVector2D
	{
		if (!Rl) return Want;
		for (int32 K = 0; K < 48; ++K)
		{
			const FVector2D Q = K == 0 ? Want : Rl->At + FVector2D(FMath::Cos(K * 2.f * PI / 12.f), FMath::Sin(K * 2.f * PI / 12.f)) * (4.0 + 4.0 * (K / 12));
			const FVector Q3(Q.X * 100.0, Q.Y * 100.0, WildGroundZ(FVector(Q.X * 100.0, Q.Y * 100.0, 0.0)) + 100.f);
			if (!WildRuinInPiece(*Rl, Q3, RadCm, 100.f)) return Q;
		}
		return Want;
	};
	const FVector2D C = Clear(WildRuinCentre(P), 450.f);          // (room for the fire and the ring of them round it)
	TArray<UStaticMesh*> Ms; WildPiecesOf(TEXT("campfire"), Ms);
	if (Ms.Num() > 0)
	{
		UStaticMeshComponent* F = NewObject<UStaticMeshComponent>(this);
		F->SetStaticMesh(Ms[0]); F->SetCollisionEnabled(ECollisionEnabled::NoCollision); F->RegisterComponent();
		const float* Ks = WildPieceScale.Find(FName(*Ms[0]->GetName()));
		F->SetWorldTransform(FTransform(FRotator::ZeroRotator, FVector(C.X * 100.0, C.Y * 100.0, WildGroundZ(FVector(C.X * 100.0, C.Y * 100.0, 0.0)) - 2.f), FVector(Ks ? *Ks : 1.f)));
		L.Comps.Add(F);
		if (WildFireFx) if (UNiagaraComponent* Fx = UNiagaraFunctionLibrary::SpawnSystemAttached(WildFireFx, F, NAME_None, FVector(0, 0, 25.f), FRotator::ZeroRotator, EAttachLocation::KeepRelativeOffset, true)) L.Comps.Add(Fx);
	}
	L.FireAt = C;
	const int32 N = 2 + (int32)(FRDWildWorld::Hash(P.Id, 1901, Wild->Seed) % 3u);
	static const TCHAR* Defs[] = { TEXT("Townsman"), TEXT("Townswoman"), TEXT("Child"), TEXT("Townswoman") };
	for (int32 K = 0; K < N; ++K)
	{
		const float A = 2.f * PI * K / N + 0.4f;
		const FVector2D At = Clear(C + FVector2D(FMath::Cos(A), FMath::Sin(A)) * 3.2, 60.f);
		if (ARDTownsfolk* T = SpawnReclaimFolk15(At, FMath::RadiansToDegrees(A) + 180.f, (uint32)P.Id * 13u + K, Defs[K % 4], TEXT("a settler"), ReclaimSettlerLines15)) L.Folk.Add(T);
	}
	RuinsLaid15.Add(P.Id, L);
	UE_LOG(LogRDList15m, Log, TEXT("RDRECLAIM15 the settlers of %s laid (%d)"), *P.Name, L.Folk.Num());
}

bool ARDDungeonGenerator::ReclaimFirst15(const FVector& From, float& Best, int32& Kind, int32& Id) const
{
	// (the rewards' nearest, its fifth and sixth kinds: a waypoint's trader (2 m) and its tent (2.5 m))
	bool bAny = false;
	for (const auto& Kv : CampsLaid15)
	{
		const FReclaimLaid15& L = Kv.Value;
		if (!L.TraderAt.IsZero()) { const float D = FVector::Dist2D(L.TraderAt, From); if (D < FMath::Min(Best, 200.f) && FMath::Abs(L.TraderAt.Z - From.Z) < 250.f) { Best = D; Kind = 4; Id = Kv.Key; bAny = true; } }
		const float Dt = FVector::Dist2D(L.TentAt, From);
		if (Dt < FMath::Min(Best, 250.f) && FMath::Abs(L.TentAt.Z - From.Z) < 300.f) { Best = Dt; Kind = 5; Id = Kv.Key; bAny = true; }
	}
	// (and the settlers of a resettled ruin (2 m): a word each; the key is the ruin's id x 8 + the settler)
	for (const auto& Kv : RuinsLaid15)
		for (int32 K = 0; K < Kv.Value.Folk.Num(); ++K)
			if (const AActor* A = Kv.Value.Folk[K].Get())
			{
				const float D = FVector::Dist2D(A->GetActorLocation(), From);
				if (D < FMath::Min(Best, 200.f) && FMath::Abs(A->GetActorLocation().Z - From.Z) < 250.f) { Best = D; Kind = 6; Id = Kv.Key * 8 + K; bAny = true; }
			}
	return bAny;
}

FString ARDDungeonGenerator::TalkSettler15(int32 Key)
{
	if (!PlayerCombat || ReclaimSettlerLines15.Num() == 0) return FString();
	const int32 N = ReclaimSettlerLines15.Num();
	const FString& L = ReclaimSettlerLines15[(int32)(FRDWildWorld::Hash(Key, TownDay * 7 + SettlerTalks15++, Wild->Seed) % (uint32)N)];
	PlayerCombat->ShowMessage(FString::Printf(TEXT("A settler: \"%s\""), *L));
	return TEXT("talk");
}

FString ARDDungeonGenerator::RestAtCamp15(int32 Id)
{
	// (rest in the tent: whole again, the night slept through to the next morning (7:00), autosaved)
	if (!PlayerCombat) return FString();
	PlayerCombat->SetHealth(PlayerCombat->GetMaxHealth());
	PlayerCombat->SetMana(PlayerCombat->GetMaxMana());
	const int32 Day0 = TownDay;
	if (TownHour >= 7.f) ++TownDay;
	SetTownHour(7.f);
	PlayerCombat->ShowMessage(FString::Printf(TEXT("You rest in the tent until morning: day %d, 07:00, whole again"), TownDay));
	UE_LOG(LogRDList15m, Log, TEXT("RDRECLAIM15 rested at camp %d: day %d -> %d"), Id, Day0, TownDay);
	WildAutosave(TEXT("found"));
	return TEXT("rest");
}

void ARDDungeonGenerator::ForgetReclaim15()
{
	// (tests: the camps cleared and the ruins resettled forgotten (the resettled ruins' guardians back), the laid waypoints and settlers gone)
	URDGameInstance* GI = URDGameInstance::Of(this);
	if (GI)
	{
		for (const int32 Id : GI->RuinsResettled15) for (int32 K = 0; K < 16; ++K) GI->WildKilled.Remove((int64)Id * 16 + K);
		for (const int32 Id : GI->CampsCleared15) for (int32 K = 0; K < 16; ++K) GI->WildKilled.Remove((int64)Id * 16 + K);          // (its monsters back: else it is cleared again at the next look)
		GI->CampsCleared15.Reset(); GI->CampsClearedDay15.Reset(); GI->CampsResettledFrom15.Reset(); GI->RuinsResettled15.Reset();
	}
	for (TMap<int32, FReclaimLaid15>* Mp : { &CampsLaid15, &RuinsLaid15 })
	{
		for (auto& Kv : *Mp) { for (TWeakObjectPtr<USceneComponent>& C : Kv.Value.Comps) if (C.IsValid()) C->DestroyComponent(); for (TWeakObjectPtr<AActor>& A : Kv.Value.Folk) if (A.IsValid()) A->Destroy(); }
		Mp->Reset();
	}
	ReclaimShareCache15.Reset();
}

void ARDDungeonGenerator::SkipDays15(int32 Days)
{
	// (tests: the days passed at once (the game's own day counter), the clock kept)
	TownDay += FMath::Max(Days, 0);
	if (URDGameInstance* GI = URDGameInstance::Of(this)) GI->TownDay = TownDay;
	ReclaimLook15 = 0.f;
}

void ARDDungeonGenerator::DrawReclaimShares15(TFunctionRef<void(const FVector2D& AtM, const FString& Text)> Each) const
{
	// (each region's cell with a camp cleared: its share of the camps there, at the cell's middle)
	const URDGameInstance* GI = URDGameInstance::Of(this);
	if (!GI || !IsWildReady() || GI->CampsCleared15.Num() == 0) return;
	TMap<FIntPoint, int32> Cleared;
	TMap<FIntPoint, FVector2D> Where;
	for (const int32 Id : GI->CampsCleared15) { FRDWildPlace P; if (Wild->FindPlace(Id, P)) { const FIntPoint Cl = Wild->LookoutCellOf(P.At.X, P.At.Y); Cleared.FindOrAdd(Cl)++; Where.FindOrAdd(Cl, P.At); } }
	for (const auto& Kv : Cleared)
	{
		// (at the region's first cleared camp, under its mark: a region's cell is wider than the map's view at its first zoom, and its middle
		// was out of it in the first test)
		const int32 All = ReclaimCampsInCell15(Kv.Key);
		Each(Where[Kv.Key] + FVector2D(0.0, 0.0), FString::Printf(TEXT("this region: %d of %d camps reclaimed"), Kv.Value, FMath::Max(All, Kv.Value)));
	}
}

int32 ARDDungeonGenerator::ReclaimCampsInCell15(FIntPoint Cell) const
{
	if (const int32* Got = ReclaimShareCache15.Find(Cell)) return *Got;
	const double X0 = Wild->Xs + Cell.X * Wild->CellM, Y0 = Wild->Yw + Cell.Y * Wild->CellM;
	TArray<FRDWildPlace> Ps;
	const FIntPoint P0 = Wild->PlaceCellOf(X0, Y0), P1 = Wild->PlaceCellOf(X0 + Wild->CellM, Y0 + Wild->CellM);
	for (int32 I = P0.X; I <= P1.X; ++I) for (int32 J = P0.Y; J <= P1.Y; ++J) Wild->PlacesIn(FIntPoint(I, J), Ps);
	int32 N = 0;
	for (const FRDWildPlace& P : Ps) if (IsClearableCamp15(P) && Wild->LookoutCellOf(P.At.X, P.At.Y) == Cell) ++N;
	ReclaimShareCache15.Add(Cell, N);
	return N;
}

TArray<FString> ARDDungeonGenerator::GetReclaim15(float Km) const
{
	// (tests: "camp|id|name|kind|x|y|monsters|cleared day (-1)|laid|trader|tent x|y|z|trader x|y|z (cm)" for the camps within Km, "ruin|id|name|x|y|resettled|
	// laid|settlers" for the resettled ruins, "day|n")
	TArray<FString> Out;
	const APawn* Her = UGameplayStatics::GetPlayerPawn(this, 0);
	const URDGameInstance* GI = URDGameInstance::Of(this);
	if (!Her || !IsWildReady() || !GI) return Out;
	const FVector2D H2(Her->GetActorLocation().X / 100.0, Her->GetActorLocation().Y / 100.0);
	TArray<FRDWildPlace> Ps;
	const FIntPoint P0 = Wild->PlaceCellOf(H2.X - Km * 1000.0, H2.Y - Km * 1000.0), P1 = Wild->PlaceCellOf(H2.X + Km * 1000.0, H2.Y + Km * 1000.0);
	for (int32 I = P0.X; I <= P1.X; ++I) for (int32 J = P0.Y; J <= P1.Y; ++J) Wild->PlacesIn(FIntPoint(I, J), Ps);
	for (const FRDWildPlace& P : Ps)
	{
		if (!IsClearableCamp15(P) || FVector2D::Distance(P.At, H2) > Km * 1000.0) continue;
		const FReclaimLaid15* L = CampsLaid15.Find(P.Id);
		Out.Add(FString::Printf(TEXT("camp|%d|%s|%s|%.1f|%.1f|%d|%d|%d|%d|%.0f|%.0f|%.0f|%.0f|%.0f|%.0f"), P.Id, *P.Name, *P.Kind, P.At.X, P.At.Y, WildPlaceMonsterCount15(P), CampClearedDay15(P.Id),
			L ? 1 : 0, L ? L->Folk.Num() : 0, L ? L->TentAt.X : 0.0, L ? L->TentAt.Y : 0.0, L ? L->TentAt.Z : 0.0, L ? L->TraderAt.X : 0.0, L ? L->TraderAt.Y : 0.0, L ? L->TraderAt.Z : 0.0));
	}
	for (const int32 Id : GI->RuinsResettled15)
	{
		FRDWildPlace P;
		if (!Wild->FindPlace(Id, P)) continue;
		const FReclaimLaid15* L = RuinsLaid15.Find(Id);
		const FVector2D C = L ? L->FireAt : WildRuinCentre(P);
		Out.Add(FString::Printf(TEXT("ruin|%d|%s|%.1f|%.1f|1|%d|%d"), Id, *P.Name, C.X, C.Y, L ? 1 : 0, L ? L->Folk.Num() : 0));
	}
	Out.Add(FString::Printf(TEXT("day|%d"), TownDay));
	return Out;
}
