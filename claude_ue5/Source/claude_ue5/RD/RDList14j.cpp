// The user's list of 2026-11-16 (docs/improvements14.txt; the plan docs/improvements14_plan.md), its tenth phase: storms by their
// strength, and lightning (item 19): "the medium and stronger storms should have varying degrees of lightning and thunder, and if
// lightning hits someone, that someone should get damaged". Each weather the sky picks has a strength (light, moderate, strong,
// violent) drawn with it from the same hash, by region (dry land draws the strong ones less); rain, wind and cloud go by it. A storm of
// moderate strength or more has lightning, the stronger the more often: a jagged bolt of our own (the engine's cylinder in segments,
// an unlit additive material of 932's), a light where it lands, the sky light flashing, and thunder after it by its distance (343 m/s;
// the Quest Game pack's strike and rumbles, 932 sounds). Some strikes are aimed at someone in the open near her; a strike hurts
// whoever stands within StrikeRadiusCm14 of where it lands and is not under a roof: her (a share of her hit points, as a trap's), the
// monsters, the animals and the wilds' people (a blow grown with the wilds' tier).
#include "RD/RDDungeonGenerator.h"
#include "RD/RDTown.h"
#include "RD/RDCombat.h"
#include "RD/RDMonster.h"
#include "RD/RDSection.h"
#include "RD/RDWild.h"
#include "Components/StaticMeshComponent.h"
#include "Components/PointLightComponent.h"
#include "Components/AudioComponent.h"
#include "Materials/MaterialInstanceDynamic.h"
#include "Engine/StaticMesh.h"
#include "Engine/World.h"
DEFINE_LOG_CATEGORY_STATIC(LogRDStorm14, Log, All);

namespace
{
	/** the weathers that carry rain, snow or dust: the ones a strength changes */
	bool RDStormHasStrength(int32 W) { return W == 4 || W == 5 || W == 6 || W == ARDDungeonGenerator::WeatherWhiteout || W == ARDDungeonGenerator::WeatherDust; }
	float RDStormAt(const TArray<float>& A, int32 I, float Def) { return A.IsValidIndex(I) ? A[I] : Def; }
	const TCHAR* RDStrengthNames[4] = { TEXT("light"), TEXT("moderate"), TEXT("strong"), TEXT("violent") };
}

FString ARDDungeonGenerator::StrengthName14(int32 S) { return RDStrengthNames[FMath::Clamp(S, 0, 3)]; }

int32 ARDDungeonGenerator::PickStrength14(int32 W, uint32 H, bool bDry) const
{
	// (a storm's weights, or a rain's (rain, snow, whiteout, dust); in dry land the strong and violent weigh DryStrongShare14 of theirs)
	if (!RDStormHasStrength(W)) return 0;
	const TArray<float>& Src = W == 5 ? StormStrengthWeights14 : RainStrengthWeights14;
	float Wt[4]; float Sum = 0.f;
	for (int32 K = 0; K < 4; ++K) { Wt[K] = FMath::Max(RDStormAt(Src, K, 0.f), 0.f) * (bDry && K >= 2 ? DryStrongShare14 : 1.f); Sum += Wt[K]; }
	if (Sum <= 0.f) return W == 5 ? 1 : 0;
	float Pick = ((H >> 5) % 10000u) / 10000.f * Sum;
	int32 K = 0;
	for (; K < 3; ++K) { if (Pick < Wt[K]) break; Pick -= Wt[K]; }
	// (a storm is moderate or stronger, whatever the weights say: the one place a strength is picked (PR #88's review))
	return W == 5 ? FMath::Max(K, 1) : K;
}

void ARDDungeonGenerator::ApplyStrength14()
{
	// (rain, wind and cloud by the strength: the look's own times StrengthScale14's)
	if (!RDStormHasStrength(Weather)) return;
	// (a share of the look's own, 1 at most (PR #88's review: a violent storm's 1.15 was cut back to 1 by the drops, the clouds and the
	// rain's loop, and looked and sounded as a strong one))
	const float F = FMath::Clamp(RDStormAt(StrengthScale14, WeatherStrength14, 1.f), 0.f, 1.f);
	SkyRainWant *= F; SkyWindWant *= F;
	SkyCoverWant *= FMath::Sqrt(F);
}

void ARDDungeonGenerator::SetWeatherStrength14(int32 S)
{
	// (the strength alone: the look again with it on, at once; no new weather (PR #88's review: through SetWeather it counted a change,
	// moved the weather's hashes and the lightning's stream, and stretched the weather to its longest))
	WeatherStrength14 = FMath::Clamp(S, 0, 3);
	if (Weather == 5) WeatherStrength14 = FMath::Max(WeatherStrength14, 1);          // (a storm is moderate or stronger)
	SetWeatherWants14(true);
	NextStrikeAt14 = -1.f;
}

void ARDDungeonGenerator::SetWeatherWants14(bool bAtOnce)
{
	// (the weather's look, its strength on it; at once or eased to)
	const int32 Wk = FMath::Clamp(Weather, 0, NumWeathers - 1);
	float Cover = 0.f, Rain = 0.f, Wind = 0.f, Fog = 0.f; FLinearColor Tint;
	WeatherLookOf(Wk, Cover, Rain, Wind, Fog, Tint);
	SkyCoverWant = Cover; SkyRainWant = Rain; SkyWindWant = Wind; SkyFogWant = Fog; SkyFogTintWant = Tint;
	ApplyStrength14();
	if (bAtOnce) { SkyCover = SkyCoverWant; SkyRain = SkyRainWant; SkyWind = SkyWindWant; SkyFog = SkyFogWant; SkyFogTint = SkyFogTintWant; }
	ApplySky7();
}

FString ARDDungeonGenerator::CountWeatherStrengths14(int32 W, int32 N, bool bDry) const
{
	// (the game's own pick of a strength, N times from the session's hashes as the turn draws them: how often each comes)
	int32 C[4] = { 0, 0, 0, 0 };
	for (int32 I = 0; I < N; ++I)
	{
		const uint32 H = HashCombine((uint32)SessionSeed ^ 0x5EA7u, (uint32)(I + 1000003) * 2654435761u);
		++C[PickStrength14(W, HashCombine(H, 0x57A0u), bDry)];
	}
	return FString::Printf(TEXT("light:%d|moderate:%d|strong:%d|violent:%d"), C[0], C[1], C[2], C[3]);
}

// ================================================================================================ lightning

bool ARDDungeonGenerator::IsSheltered14(const FVector& At, const AActor* Skip) const
{
	// (under a roof: a wild house's or farm building's box (their roofs have no collision), a town's building, or anything over it)
	for (const auto& Kv : WildChunks)
	{
		const ARDWildChunk* C = Kv.Value;
		if (!IsValid(C) || FVector::Dist2D(C->GetActorLocation(), At) > WildChunkM * 100.f * 1.5f) continue;
		for (const ARDWildChunk::FHouse& Hs : C->Houses)
		{
			const FVector Lp = FRotator(0.f, -Hs.Yaw, 0.f).RotateVector(At - Hs.C);
			if (FMath::Abs(Lp.X) <= Hs.H.X && FMath::Abs(Lp.Y) <= Hs.H.Y && At.Z > Hs.FloorZ - 150.f && At.Z < Hs.FloorZ + 600.f) return true;
		}
	}
	if (const ARDSection* S0 = GetSection(FIntPoint::ZeroValue); S0 && S0->TownBuildingAt(At) >= 0) return true;
	return WildWayBlocked14(At + FVector(0, 0, 120.f), At + FVector(0, 0, 4000.f), 0.f, Skip);
}

int32 ARDDungeonGenerator::ForceLightning14(FVector At)
{
	if (!GetWorld()) return 0;
	return Strike14(At);
}

int32 ARDDungeonGenerator::Strike14(const FVector& Aim)
{
	UWorld* W = GetWorld();
	const AActor* Her = PlayerCombat ? PlayerCombat->GetOwner() : nullptr;
	if (!W) return 0;
	const float Now = W->GetTimeSeconds();
	const int32 S = FMath::Clamp(WeatherStrength14, 1, 3);
	// (where it lands: the first thing over the ground at the aim (a roof with collision, a tree near her, the ground))
	FVector At(Aim.X, Aim.Y, IsWildReady() ? WildGroundZ(Aim) : Aim.Z);
	{
		FCollisionQueryParams Q(SCENE_QUERY_STAT(RDStrike14), false);
		FCollisionObjectQueryParams O; O.AddObjectTypesToQuery(ECC_WorldStatic); O.AddObjectTypesToQuery(ECC_WorldDynamic);
		FHitResult H;
		if (W->LineTraceSingleByObjectType(H, FVector(Aim.X, Aim.Y, At.Z + 4000.f), FVector(Aim.X, Aim.Y, At.Z - 100.f), O, Q) && !Cast<ARDTownsfolk>(H.GetActor())) At = H.ImpactPoint;
	}
	++LightningStrikes14; LastStrikeAt14 = At; LastStrikeTime14 = Now;
	const float Dist = Her ? FVector::Dist(Her->GetActorLocation(), At) : 0.f;
	// ---- the bolt: a jagged line of segments from the clouds (1.6 km) down to it, and a branch; it flickers and is gone in 0.35 s
	FBolt14 B; B.Born = Now;
	if (LightningMesh14 && LightningMaterial14)
	{
		FRandomStream R((int32)HashCombine((uint32)LightningStrikes14 * 7919u, (uint32)SessionSeed ^ 0xB017u));
		const float Wd = FMath::Clamp(Dist * 0.0025f, 40.f, 900.f);
		auto Seg = [&](const FVector& A, const FVector& Bp, float Width)
		{
			UStaticMeshComponent* M = NewObject<UStaticMeshComponent>(this);
			M->SetStaticMesh(LightningMesh14); M->SetMaterial(0, LightningMaterial14);
			M->SetCollisionEnabled(ECollisionEnabled::NoCollision); M->SetCastShadow(false); M->bNeverDistanceCull = true;
			M->SetMobility(EComponentMobility::Movable);
			M->RegisterComponent();
			const FVector D = Bp - A;
			M->SetWorldTransform(FTransform(FRotationMatrix::MakeFromZ(D.GetSafeNormal()).Rotator(), (A + Bp) * 0.5f, FVector(Width / 100.f, Width / 100.f, D.Size() / 100.f)));
			B.Segs.Add(M);
		};
		const int32 N = 12;
		FVector P = At + FVector(R.FRandRange(-300.f, 300.f), R.FRandRange(-300.f, 300.f), 160000.f), Prev = P;
		for (int32 K = 1; K <= N; ++K)
		{
			const float T = (float)K / N;
			const FVector Q = K == N ? At : FMath::Lerp(P, At, T) + FVector(R.FRandRange(-1.f, 1.f), R.FRandRange(-1.f, 1.f), 0.f) * 160000.f / N * 0.35f;
			Seg(Prev, Q, Wd * (0.6f + 0.4f * T));
			if (K == N / 3) { const FVector Br = Q + FVector(R.FRandRange(-1.f, 1.f), R.FRandRange(-1.f, 1.f), -0.6f).GetSafeNormal() * 40000.f; Seg(Q, Br, Wd * 0.5f); }
			Prev = Q;
		}
	}
	UPointLightComponent* Lt = NewObject<UPointLightComponent>(this);
	Lt->SetIntensityUnits(ELightUnits::Candelas); Lt->SetIntensity(400000.f); Lt->SetAttenuationRadius(60000.f);
	Lt->SetLightColor(FLinearColor(0.75f, 0.85f, 1.f)); Lt->SetCastShadows(false);
	Lt->RegisterComponent(); Lt->SetWorldLocation(At + FVector(0, 0, 800.f));
	B.Light = Lt;
	Bolts14.Add(MoveTemp(B));
	// ---- the sky lit by it (nearer, brighter), the thunder after it by its distance
	LightningFlash14 = FMath::Max(LightningFlash14, FMath::Lerp(1.f, 0.25f, FMath::Clamp(Dist / FMath::Max(StrikeFarCm14, 1.f), 0.f, 1.f)));
	Thunders14.Add({ Now + Dist / 34300.f, Dist });
	// ---- whoever stands where it lands, in the open
	int32 Hit = 0;
	const float Grow = IsWildReady() ? FMath::Max((float)WildGoldAt(1000, At) / 1000.f, 1.f) : 1.f;
	const float Dmg = RDStormAt(LightningDamage14, S, 60.f) * Grow;
	auto Near = [&](const FVector& L) { return FVector::Dist2D(L, At) <= StrikeRadiusCm14 && FMath::Abs(L.Z - At.Z) < 400.f; };
	if (PlayerCombat && Her && !PlayerCombat->IsDead() && Near(Her->GetActorLocation()) && !IsSheltered14(Her->GetActorLocation(), Her))
	{
		PlayerCombat->HurtByTrap(RDStormAt(StrikeHurtShare14, S, 0.2f), 0.f, 0.f, TEXT("Struck by lightning"));
		++LightningOnHer14; ++Hit;
	}
	for (ARDMonster* Mo : GetMonsters())
		if (IsValid(Mo) && !Mo->IsDead() && Mo->bOpenGround && Near(Mo->GetActorLocation()) && !IsSheltered14(Mo->GetActorLocation(), Mo))
		{
			// (no kill of hers, nor a blow that wakes it (PR #88's review: it was sent after her and its death paid her))
			bNotHerKill14 = true; Mo->ApplyDamageEx(Dmg, nullptr, &At, true, false); bNotHerKill14 = false;
			AddHitText(Mo->GetActorLocation() + FVector(0, 0, 100.f), Dmg, false); ++LightningOnOthers14; ++Hit;
		}
	for (ARDTownsfolk* T : WildPeople14())
		if (IsValid(T) && T->CanBeHurt14() && Near(T->GetActorLocation()) && !T->IsWildIndoors() && !IsSheltered14(T->GetActorLocation(), T))
		{ T->TakeWildHit14(Dmg, nullptr); ++LightningOnOthers14; ++Hit; }
	auto HitAnimal = [&](ARDWildAnimal* An)
	{
		if (!IsValid(An) || An->IsDead() || !Near(An->GetActorLocation()) || IsSheltered14(An->GetActorLocation(), An)) return;
		// (not her kill: no things, not kept (bWildPredatorKill, as a predator's))
		bWildPredatorKill = true; An->TakeHit(Dmg, At); bWildPredatorKill = false;
		++LightningOnOthers14; ++Hit;
	};
	// (every wild animal is in WildAnimals, the herds' too: struck once (PR #88's review: the herds' lists struck them again))
	for (const TObjectPtr<ARDWildAnimal>& An : WildAnimals) HitAnimal(An.Get());
	for (const FRDWildFarmRec& F : WildFarms)
		for (const TWeakObjectPtr<ARDTownAnimal>& An : F.Animals)
			if (ARDTownAnimal* A = An.Get(); IsValid(A) && A->CanBeHurt14() && Near(A->GetActorLocation()) && !IsSheltered14(A->GetActorLocation(), A))
			{
				// (a farm animal killed so is no kill of hers either: not kept, no things (as the wild animals'))
				bWildPredatorKill = true; A->TakeHit14(Dmg, At); bWildPredatorKill = false;
				++LightningOnOthers14; ++Hit;
			}
	UE_LOG(LogRDStorm14, Log, TEXT("RDLIGHTNING %s storm: a strike at (%.0f, %.0f, %.0f), %.0f m from her, %d struck"), *StrengthName14(S), At.X, At.Y, At.Z, Dist / 100.f, Hit);
	return Hit;
}

void ARDDungeonGenerator::TickLightning14(float Dt)
{
	UWorld* W = GetWorld();
	if (!W) return;
	const float Now = W->GetTimeSeconds();
	// (the bolts flicker: seen 0-0.08 s and 0.13-0.22 s, gone at 0.35 s; its light the same)
	for (int32 I = Bolts14.Num() - 1; I >= 0; --I)
	{
		FBolt14& B = Bolts14[I];
		const float A = Now - B.Born;
		const bool bOn = A < 0.08f || (A > 0.13f && A < 0.22f) || A < LightningHoldSeconds14;
		for (const TWeakObjectPtr<UStaticMeshComponent>& M : B.Segs) if (M.IsValid()) M->SetVisibility(bOn);
		if (UPointLightComponent* L = B.Light.Get()) L->SetIntensity(bOn ? 400000.f : 0.f);
		if (A > FMath::Max(0.35f, LightningHoldSeconds14 + 0.05f))
		{
			for (const TWeakObjectPtr<UStaticMeshComponent>& M : B.Segs) if (M.IsValid()) M->DestroyComponent();
			if (UPointLightComponent* L = B.Light.Get()) L->DestroyComponent();
			Bolts14.RemoveAt(I);
		}
	}
	// (the sky's flash fades in a quarter of a second: the sky light is set by ApplyDayNight, so it is applied every frame while it lasts)
	if (LightningFlash14 > 0.f)
	{
		LightningFlash14 = FMath::Max(0.f, LightningFlash14 - Dt * 4.f);
		ApplyDayNight();
	}
	// (thunder when its sound arrives: near, the strike's crack and roll; far, a rumble; quieter and lower the farther)
	for (int32 I = Thunders14.Num() - 1; I >= 0; --I)
	{
		if (Now < Thunders14[I].When) continue;
		const float D = Thunders14[I].Dist;
		const float Far = FMath::Clamp(D / FMath::Max(StrikeFarCm14, 1.f), 0.f, 1.f);
		const AActor* Her = PlayerCombat ? PlayerCombat->GetOwner() : nullptr;
		LastThunderSet14 = D < ThunderNearCm14 ? FName(TEXT("Weather.Thunder")) : FName(TEXT("Weather.ThunderFar"));
		PlaySoundAt(LastThunderSet14, Her ? Her->GetActorLocation() : FVector::ZeroVector, FMath::Lerp(1.f, 0.35f, Far), FMath::Lerp(1.f, 0.85f, Far));
		++LightningThunders14; LastThunderTime14 = Now;
		Thunders14.RemoveAt(I);
	}
	// (strikes: only in a storm of moderate strength or more, once its rain has come in)
	if (!bLightning14 || Weather != 5 || WeatherStrength14 < 1 || SkyRain < 0.5f || !PlayerCombat || !PlayerCombat->GetOwner()) { NextStrikeAt14 = -1.f; return; }
	const float Rate = FMath::Max(RDStormAt(StrikesPerMinute14, WeatherStrength14, 0.f), 0.f);
	if (Rate <= 0.f) return;
	auto Wait = [&]() { return FMath::Clamp(-FMath::Loge(FMath::Max(LightningR14.FRand(), 0.0001f)) * 60.f / Rate, 1.5f, 240.f); };
	if (NextStrikeAt14 < 0.f) { LightningR14.Initialize((int32)HashCombine((uint32)SessionSeed, 0x11647u + (uint32)WeatherChanges)); NextStrikeAt14 = Now + Wait(); return; }
	if (Now < NextStrikeAt14) return;
	NextStrikeAt14 = Now + Wait();
	const FVector Her = PlayerCombat->GetOwner()->GetActorLocation();
	// (some aimed at someone in the open near her (her too); the rest anywhere round her out to StrikeFarCm14)
	FVector Aim = FVector::ZeroVector; bool bAimed = false;
	if (LightningR14.FRand() < StrikeNearShare14)
	{
		TArray<FVector> Who;
		if (!PlayerCombat->IsDead() && !IsSheltered14(Her, PlayerCombat->GetOwner())) Who.Add(Her);
		for (ARDMonster* Mo : GetMonsters()) if (IsValid(Mo) && !Mo->IsDead() && Mo->bOpenGround && FVector::Dist2D(Mo->GetActorLocation(), Her) < StrikeNearCm14) Who.Add(Mo->GetActorLocation());
		for (ARDTownsfolk* T : WildPeople14()) if (IsValid(T) && T->CanBeHurt14() && !T->IsWildIndoors() && FVector::Dist2D(T->GetActorLocation(), Her) < StrikeNearCm14) Who.Add(T->GetActorLocation());
		for (const TObjectPtr<ARDWildAnimal>& An : WildAnimals) if (IsValid(An) && !An->IsDead() && FVector::Dist2D(An->GetActorLocation(), Her) < StrikeNearCm14) Who.Add(An->GetActorLocation());
		if (Who.Num() > 0) { Aim = Who[LightningR14.RandRange(0, Who.Num() - 1)]; bAimed = !IsSheltered14(Aim, nullptr); }
	}
	if (!bAimed)
	{
		const float A = LightningR14.FRandRange(0.f, 2.f * PI), R = FMath::Lerp(StrikeNearCm14 * 0.5f, StrikeFarCm14, FMath::Sqrt(LightningR14.FRand()));
		Aim = Her + FVector(FMath::Cos(A) * R, FMath::Sin(A) * R, 0.f);
	}
	Strike14(Aim);
}

TArray<FString> ARDDungeonGenerator::GetStormLines14() const
{
	// "storm|weather|strength|strikes|on her|on others|thunders|last strike x|y|z|its time|last thunder's time|next strike in|flash|the
	// drops' amount as drawn|the rain loop's volume|the last thunder's set"
	const float Now = GetWorld() ? GetWorld()->GetTimeSeconds() : 0.f;
	const float Drops = RainDropMID ? RainDropMID->K2_GetScalarParameterValue(TEXT("Amount")) : -1.f;
	const float Loop = WeatherRainSound ? WeatherRainSound->VolumeMultiplier : -1.f;
	return { FString::Printf(TEXT("storm|%s|%s|%d|%d|%d|%d|%.0f|%.0f|%.0f|%.3f|%.3f|%.1f|%.2f|%.3f|%.3f|%s"), *WeatherName(Weather), *StrengthName14(WeatherStrength14), LightningStrikes14,
		LightningOnHer14, LightningOnOthers14, LightningThunders14, LastStrikeAt14.X, LastStrikeAt14.Y, LastStrikeAt14.Z, LastStrikeTime14, LastThunderTime14,
		NextStrikeAt14 < 0.f ? -1.f : NextStrikeAt14 - Now, LightningFlash14, Drops, Loop, *LastThunderSet14.ToString()) };
}
