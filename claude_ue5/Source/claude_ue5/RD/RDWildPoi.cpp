// The wilderness's small points of interest and its encounter director (the user's list of 2026-11-08b, docs/improvements9.txt,
// its seventh phase: "in order to retain engagement, the player should be able to interact or encounter something every 40
// seconds when roaming the wilderness. the terrain generation algorithm should take this into account"; SourceArt/wilderness/
// poi.json, 912). FRDWildWorld::PoisIn puts one in most cells of a 160 m grid, of the kinds of the region (a kind's biomes),
// beside the roads or off them, landmarks in one cell in nine; here each is laid with its chunk (its pieces, what it holds, its
// guards) and F uses it (a pile taken, a blessing, a rest, a story, a milestone's ways to the towns). The director meets her on
// her way with an encounter (an ambush, a lost satchel) whenever 25 s go by with nothing near her: no fight, no point of
// interest, pile or animal within reach of her eye.
#include "RD/RDDungeonGenerator.h"
#include "RD/RDWild.h"
#include "RD/RDMonster.h"
#include "RD/RDMistward.h"
#include "RD/RDCombat.h"
#include "RD/RDSection.h"
#include "Kismet/GameplayStatics.h"
#include "ProceduralMeshComponent.h"
#include "RD/RDGameInstance.h"
#include "Components/StaticMeshComponent.h"
#include "Engine/StaticMesh.h"
#include "Engine/World.h"

DEFINE_LOG_CATEGORY_STATIC(LogRDWildPoi, Log, All);

namespace
{
	/** a point of interest used for good: its key in the game instance's WildKilled (out of the places' kill range and the
	 *  stones' -(id + 2), as the ids are) */
	int64 RDPoiUsedKey(int32 Id) { return -((int64)Id + 2); }
	const TCHAR* RDPoiCompass(const FVector2D& D)
	{
		static const TCHAR* N[8] = { TEXT("north"), TEXT("north-east"), TEXT("east"), TEXT("south-east"), TEXT("south"), TEXT("south-west"), TEXT("west"), TEXT("north-west") };
		// (the world's +X is north, +Y east: as the map draws it)
		const float A = FMath::RadiansToDegrees(FMath::Atan2(D.Y, D.X));
		return N[((int32)FMath::RoundToInt((A < 0.f ? A + 360.f : A) / 45.f)) % 8];
	}
}

bool ARDDungeonGenerator::IsWildPoiUsed(int32 Id) const
{
	const URDGameInstance* GI = URDGameInstance::Of(this);
	if (GI && GI->WildKilled.Contains(RDPoiUsedKey(Id))) return true;
	const float* R = WildPoiReadyAt.Find(Id);
	return R && GetWorld() && GetWorld()->GetTimeSeconds() < *R;
}

void ARDDungeonGenerator::SpawnWildPoi(ARDWildChunk* C, const FRDWildPlace& P)
{
	if (!C || !WildPoiKinds.IsValidIndex(P.Poi)) return;
	const FRDWildPoiKind& K = WildPoiKinds[P.Poi];
	FRandomStream R((int32)FRDWildWorld::Hash(P.Id, 78, Wild->Seed));
	const FVector O = C->GetActorLocation();
	auto Put = [&](const FString& Prefix, const FVector2D& At, float Yaw, float Scale, float Sink, bool bCollide)
	{
		TArray<UStaticMesh*> Ms; WildPiecesOf(Prefix, Ms);
		if (Ms.Num() == 0) return;
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
		// (a landmark is seen from the chunks' whole reach)
		if (K.Layer >= 2) { Sm->SetCachedMaxDrawDistance(0.f); Sm->bNeverDistanceCull = true; }
		Sm->RegisterComponent();
		C->PlaceProps.Add(Sm);
	};
	// ("prefix|count|ring radius m|scale|sink|collide"; radius 0: at its point, a little apart)
	for (const FString& Ln : K.Props)
	{
		TArray<FString> F; Ln.ParseIntoArray(F, TEXT("|"), false);
		if (F.Num() < 2) continue;
		const int32 N = FMath::Max(1, FCString::Atoi(*F[1]));
		const float Rr = F.Num() > 2 ? FCString::Atof(*F[2]) : 0.f, Sc = F.Num() > 3 ? FCString::Atof(*F[3]) : 1.f;
		const float Sink = F.Num() > 4 ? FCString::Atof(*F[4]) : 10.f;
		const bool bCollide = F.Num() > 5 ? F[5] != TEXT("0") : true;
		const float A0 = R.FRandRange(0.f, 360.f);
		for (int32 I = 0; I < N; ++I)
		{
			const float A = FMath::DegreesToRadians(A0 + I * 360.f / N + R.FRandRange(-12.f, 12.f));
			const float D = Rr > 0.f ? Rr + R.FRandRange(-1.f, 1.f) : (N > 1 ? R.FRandRange(0.8f, 2.5f) : 0.f);
			const FVector2D At = P.At + FVector2D(FMath::Cos(A), FMath::Sin(A)) * D;
			Put(F[0], At, Rr > 0.f ? FMath::RadiansToDegrees(A) + 180.f : P.Yaw + R.FRandRange(-25.f, 25.f), Sc > 0.f ? Sc : 1.f, Sink, bCollide);
		}
	}
	// ---- what it holds, who guards it
	const bool bUsed = IsWildPoiUsed(P.Id);
	if (!bUsed && (K.Use == TEXT("loot") || K.Use == TEXT("resource") || K.Use == TEXT("guarded")))
	{
		TArray<FName> Got;
		for (const FString& T : K.Things)
		{
			TArray<FString> F; T.ParseIntoArray(F, TEXT("|"), false);
			if (F.Num() < 1 || FindItem(FName(*F[0])) < 0) continue;
			const int32 Lo = F.Num() > 1 ? FCString::Atoi(*F[1]) : 1, Hi = F.Num() > 2 ? FCString::Atoi(*F[2]) : Lo;
			const float Ch = F.Num() > 3 ? FCString::Atof(*F[3]) : 1.f;
			if (R.FRand() > Ch) continue;
			for (int32 I = 0, N = R.RandRange(Lo, FMath::Max(Lo, Hi)); I < N; ++I) Got.Add(FName(*F[0]));
		}
		if (Got.Num() > 0)
		{
			FVector At(P.At.X * 100.0 + 120.0, P.At.Y * 100.0, 0.0);
			At.Z = WildGroundZ(At) + 40.f;
			TArray<float> Wr; Wr.Init(-1.f, Got.Num());
			LootPiles.RemoveAll([](const TObjectPtr<ARDLootPile>& Lp) { return !IsValid(Lp); });
			if (ARDLootPile* Lp = DropLoot(At, Got, Wr))
			{
				Lp->bHers = false; Lp->bHarvest = true; Lp->Tier = 1; Lp->WildKey = RDPoiUsedKey(P.Id);
				if (HarvestTints.Num() > 0) Lp->SetTint(HarvestTints[0]);
				C->Props.Add(Lp);
			}
		}
	}
	// (its guards: a nest's or a guarded cache's, of its tier; killed ones stay dead (WildKilled, its id x 16 + n))
	if (K.Use == TEXT("guarded") || K.Use == TEXT("nest")) SpawnWildMonsters(C, P);
	// (the rest are used with F where it stands; every one is something near her for the director)
	WildPoiLive.RemoveAll([](const FRDWildPoiLive& L) { return !L.Chunk.IsValid(); });
	WildPoiLive.Add({ P.Id, P.Poi, FVector(P.At.X * 100.0, P.At.Y * 100.0, WildGroundZ(FVector(P.At.X * 100.0, P.At.Y * 100.0, 0.0))), C });
	++WildPoisLaid;
}

// ------------------------------------------------------------------------------------------------ F at one
static bool RDPoiUsable(const FName& Use) { return Use == TEXT("buff") || Use == TEXT("heal") || Use == TEXT("lore") || Use == TEXT("milestone"); }

const ARDDungeonGenerator::FRDWildPoiLive* ARDDungeonGenerator::WildPoiNear(const FVector& From, float Reach) const
{
	const FRDWildPoiLive* Best = nullptr; float BestD = Reach;
	for (const FRDWildPoiLive& L : WildPoiLive)
	{
		if (!L.Chunk.IsValid() || !WildPoiKinds.IsValidIndex(L.Kind) || !RDPoiUsable(WildPoiKinds[L.Kind].Use) || IsWildPoiUsed(L.Id)) continue;
		const float D = FVector::Dist2D(L.At, From);
		if (D < BestD) { BestD = D; Best = &L; }
	}
	return Best;
}

FString ARDDungeonGenerator::WildPoiDescribe(const FVector& From) const
{
	const FRDWildPoiLive* L = WildPoiNear(From, 320.f);
	if (!L) return FString();
	const FRDWildPoiKind& K = WildPoiKinds[L->Kind];
	const TCHAR* Verb = K.Use == TEXT("buff") ? TEXT("pray at") : K.Use == TEXT("heal") ? TEXT("rest at") : K.Use == TEXT("milestone") ? TEXT("read") : TEXT("look at");
	return FString::Printf(TEXT("%s the %s"), Verb, *K.Title.ToLower());
}

FString ARDDungeonGenerator::WildPoiInteract(const FVector& From)
{
	const FRDWildPoiLive* L = WildPoiNear(From, 320.f);
	if (!L || !PlayerCombat) return FString();
	const FRDWildPoiKind& K = WildPoiKinds[L->Kind];
	const int32 Id = L->Id;
	FString Said;
	if (K.Use == TEXT("buff"))
	{
		PlayerCombat->Bless(K.Text, K.BuffDamage, K.BuffArmour, 0.f, K.BuffSeconds);
		Said = FString::Printf(TEXT("%s:  your blows %.0f%% stronger, %.0f%% less of each blow reaches you, for %.0f minutes"), *K.Text, K.BuffDamage * 100.f, K.BuffArmour * 100.f, K.BuffSeconds / 60.f);
	}
	else if (K.Use == TEXT("heal"))
	{
		PlayerCombat->SetHealth(PlayerCombat->GetMaxHealth()); PlayerCombat->SetMana(PlayerCombat->GetMaxMana());
		Said = K.Text.IsEmpty() ? FString(TEXT("You rest: your wounds close, your mana comes back")) : K.Text;
	}
	else if (K.Use == TEXT("milestone") && IsWildReady())
	{
		// (the two nearest towns, how far and which way)
		TArray<TPair<double, int32>> Ds;
		for (int32 T = 0; T < Wild->Towns.Num(); ++T) Ds.Add({ FVector2D::Distance(Wild->Towns[T].Site, FVector2D(From.X / 100.0, From.Y / 100.0)), T });
		Ds.Sort([](const TPair<double, int32>& A, const TPair<double, int32>& B) { return A.Key < B.Key; });
		TArray<FString> Parts;
		for (int32 I = 0; I < FMath::Min(2, Ds.Num()); ++I)
		{
			const FRDWildTown& T = Wild->Towns[Ds[I].Value];
			Parts.Add(FString::Printf(TEXT("%s %.1f km %s"), *T.Name, Ds[I].Key / 1000.0, RDPoiCompass(T.Site - FVector2D(From.X / 100.0, From.Y / 100.0))));
		}
		Said = FString::Printf(TEXT("The milestone reads:  %s"), *FString::Join(Parts, TEXT(";  ")));
	}
	else Said = K.Text;
	PlayerCombat->ShowMessage(Said);
	if (K.bReusable) WildPoiReadyAt.Add(Id, GetWorld()->GetTimeSeconds() + 180.f);
	else if (URDGameInstance* GI = URDGameInstance::Of(this)) GI->WildKilled.AddUnique(RDPoiUsedKey(Id));
	++WildPoisUsed; WildLastEngaged = GetWorld()->GetTimeSeconds();
	WildEngagements.Add(FString::Printf(TEXT("%.1f|used|%s|%s"), WildLastEngaged, *K.Name.ToString(), *Said.Left(120)));
	UE_LOG(LogRDWildPoi, Log, TEXT("RDPOI used %s (%d): %s"), *K.Name.ToString(), Id, *Said);
	return TEXT("poi");
}

// ------------------------------------------------------------------------------------------------ the encounter director
void ARDDungeonGenerator::TickWildEncounters(float Dt, const FVector& Her)
{
	if (!IsWildReady() || !PlayerCombat || WildPoiKinds.Num() == 0) return;
	const float Now = GetWorld()->GetTimeSeconds();
	// (her roamers far behind her gone)
	for (int32 I = WildRoamers.Num() - 1; I >= 0; --I)
	{
		ARDMonster* M = WildRoamers[I].Get();
		if (!M) { WildRoamers.RemoveAt(I); continue; }
		if (FVector::Dist2D(M->GetActorLocation(), Her) > 25000.f) { M->Destroy(); WildRoamers.RemoveAt(I); }
	}
	WildEncounterTick -= Dt;
	if (WildEncounterTick > 0.f) return;
	WildEncounterTick = 1.f;
	if (WildLastEngaged < 0.f || IsInTownWalls(Her) || PlayerCombat->IsDead()) { WildLastEngaged = Now; return; }
	// (something near her: a fight, a point of interest not used, a pile, an animal within 45 m)
	FString Near;
	if (IsWildCombat()) Near = TEXT("fight");
	if (Near.IsEmpty())
		for (const FRDWildPoiLive& L : WildPoiLive)
			if (L.Chunk.IsValid() && FVector::Dist2D(L.At, Her) < WildEngageM && !IsWildPoiUsed(L.Id)) { Near = WildPoiKinds.IsValidIndex(L.Kind) ? WildPoiKinds[L.Kind].Name.ToString() : TEXT("poi"); break; }
	if (Near.IsEmpty()) for (const ARDLootPile* Lp : LootPiles) if (IsValid(Lp) && FVector::Dist2D(Lp->GetActorLocation(), Her) < WildEngageM) { Near = TEXT("pile"); break; }
	if (Near.IsEmpty()) for (const ARDWildAnimal* An : WildAnimals) if (IsValid(An) && !An->IsDead() && FVector::Dist2D(An->GetActorLocation(), Her) < WildEngageM) { Near = TEXT("animal"); break; }
	if (Near.IsEmpty()) for (const TWeakObjectPtr<ARDMonster>& M : WildRoamers) if (M.IsValid() && !M->IsDead() && FVector::Dist2D(M->GetActorLocation(), Her) < WildEngageM) { Near = TEXT("roamer"); break; }
	if (!Near.IsEmpty())
	{
		// (said again every 3 s while it lasts: the tests read the gaps between what met her)
		if (Now - WildLastNearSaid >= 3.f || Near != WildLastNear) { WildEngagements.Add(FString::Printf(TEXT("%.1f|near|%s|"), Now, *Near)); WildLastNearSaid = Now; }
		if (WildEngagements.Num() > 400) WildEngagements.RemoveAt(0, WildEngagements.Num() - 400);
		WildLastEngaged = Now; WildLastNear = Near;
		return;
	}
	WildLastNear.Reset();
	if (Now - WildLastEngaged < WildEncounterGap) return;
	// ---- an encounter ahead of her (the way she goes, else the way she faces), 45-70 m on, on dry, flat ground
	const APawn* P = UGameplayStatics::GetPlayerPawn(this, 0);
	FVector Dir = P ? P->GetVelocity() * FVector(1, 1, 0) : FVector::ZeroVector;
	if (Dir.Size() < 50.f && P) Dir = P->GetActorForwardVector() * FVector(1, 1, 0);
	Dir = Dir.GetSafeNormal();
	FRandomStream Rs((int32)HashCombine((uint32)SessionSeed ^ 0xE7C0u, (uint32)(++WildEncountersMade)));
	FVector2D At = FVector2D::ZeroVector; bool bOk = false;
	for (int32 T = 0; T < 8 && !bOk; ++T)
	{
		const float A = FMath::DegreesToRadians(Rs.FRandRange(-35.f, 35.f)), D = Rs.FRandRange(4500.f, 7000.f);
		const FVector W = Dir.RotateAngleAxis(FMath::RadiansToDegrees(A), FVector::UpVector);
		const FVector Q = Her + W * D;
		FRDWSample S; Wild->Sample(Q.X / 100.0, Q.Y / 100.0, S, false);
		if (S.WaterKind != 0 || S.Lava > 0.3f || IsInTownWalls(Q)) continue;
		At = FVector2D(Q.X, Q.Y); bOk = true;
	}
	if (!bOk) return;
	// (a roaming kind of the region)
	FRDWSample S; Wild->Sample(At.X / 100.0, At.Y / 100.0, S, false);
	const FString Bn = Wild->BiomeName(S.Biome);
	TArray<int32> Ks; TArray<float> Ws; float Sum = 0.f;
	for (int32 I = 0; I < WildPoiKinds.Num(); ++I)
	{
		const FRDWildPoiKind& K = WildPoiKinds[I];
		if (!K.bRoaming) continue;
		for (const FString& B : K.Biomes) if (B == TEXT("*") || B == Bn) { Ks.Add(I); Ws.Add(K.Weight); Sum += K.Weight; break; }
	}
	if (Ks.Num() == 0) return;
	float U = Rs.FRand() * Sum; int32 Pick = Ks.Last();
	for (int32 I = 0; I < Ks.Num(); ++I) { if (U < Ws[I]) { Pick = Ks[I]; break; } U -= Ws[I]; }
	const FRDWildPoiKind& K = WildPoiKinds[Pick];
	const int32 Tier = Wild->TierAt(At.X / 100.0, At.Y / 100.0);
	int32 Made = 0;
	if (K.Monsters > 0 && Monsters.Num() > 0)
	{
		ARDSection* Ws_ = EnsureWildSection();
		TArray<int32> Kinds;
		for (int32 T = Tier; T >= 1 && Kinds.Num() == 0; --T)
			for (int32 Ki = 0; Ki < Monsters.Num(); ++Ki)
			{
				const FRDMonsterDef& D = Monsters[Ki];
				if (D.Mesh && (D.WildTierMax > 0 ? (T >= D.WildTierMin && T <= D.WildTierMax) : D.Tier == T)) Kinds.Add(Ki);
			}
		if (Ws_ && Kinds.Num() > 0)
		{
			const FRDMonsterDef& Def = Monsters[Kinds[Rs.RandRange(0, Kinds.Num() - 1)]];
			for (int32 I = 0; I < K.Monsters; ++I)
			{
				const float A = Rs.FRandRange(0.f, 2.f * PI), D = Rs.FRandRange(200.f, 600.f);
				FVector Q(At.X + FMath::Cos(A) * D, At.Y + FMath::Sin(A) * D, 0.f);
				Q.Z = WildGroundZ(Q) + Def.CapsuleHalfHeight + 10.f;
				FActorSpawnParameters Sp; Sp.SpawnCollisionHandlingOverride = ESpawnActorCollisionHandlingMethod::AdjustIfPossibleButAlwaysSpawn;
				ARDMonster* M = GetWorld()->SpawnActor<ARDMonster>(ARDMonster::StaticClass(), FTransform(FRotator(0, Rs.FRandRange(0.f, 360.f), 0), Q), Sp);
				if (!M) continue;
				M->SpawnIndex = -1; M->bOpenGround = true; M->HomeAt = Q; M->WildKey = -1;
				M->Setup(Ws_, Def, (int32)Rs.GetUnsignedInt());
				M->Empower(Tier, K.MonsterHealth > 0.f ? K.MonsterHealth : 1.f, 1.f, 1.f, K.Title);
				Ws_->SpawnedMonsters.Add(M);
				WildRoamers.Add(M); ++Made;
			}
		}
	}
	else
	{
		TArray<FName> Got;
		for (const FString& T : K.Things)
		{
			TArray<FString> F; T.ParseIntoArray(F, TEXT("|"), false);
			if (F.Num() < 1 || FindItem(FName(*F[0])) < 0) continue;
			const int32 Lo = F.Num() > 1 ? FCString::Atoi(*F[1]) : 1, Hi = F.Num() > 2 ? FCString::Atoi(*F[2]) : Lo;
			if (Rs.FRand() > (F.Num() > 3 ? FCString::Atof(*F[3]) : 1.f)) continue;
			for (int32 I = 0, N = Rs.RandRange(Lo, FMath::Max(Lo, Hi)); I < N; ++I) Got.Add(FName(*F[0]));
		}
		if (Got.Num() > 0)
		{
			TArray<float> Wr; Wr.Init(-1.f, Got.Num());
			LootPiles.RemoveAll([](const TObjectPtr<ARDLootPile>& Lp) { return !IsValid(Lp); });
			if (ARDLootPile* Lp = DropLoot(FVector(At.X, At.Y, WildGroundZ(FVector(At.X, At.Y, 0.f)) + 40.f), Got, Wr)) { Lp->bHers = false; Lp->bHarvest = true; Lp->Tier = 1; ++Made; }
		}
	}
	if (Made == 0) return;
	WildLastEngaged = Now;
	if (WildEngagements.Num() > 400) WildEngagements.RemoveAt(0, WildEngagements.Num() - 400);
	WildEngagements.Add(FString::Printf(TEXT("%.1f|met|%s|%.0f|%.0f"), Now, *K.Name.ToString(), At.X / 100.f, At.Y / 100.f));
	if (!K.Text.IsEmpty()) PlayerCombat->ShowMessage(K.Text);
	UE_LOG(LogRDWildPoi, Log, TEXT("RDENCOUNTER %s at (%.0f, %.0f) m, tier %d, %d made"), *K.Name.ToString(), At.X / 100.f, At.Y / 100.f, Tier, Made);
}

TArray<FString> ARDDungeonGenerator::GetWildEncounterLines() const
{
	TArray<FString> Out = WildEngagements;
	Out.Add(FString::Printf(TEXT("state|%d|%d|%d|%d|%.1f"), WildPoisLaid, WildPoisUsed, WildEncountersMade, WildRoamers.Num(), WildLastEngaged));
	return Out;
}
