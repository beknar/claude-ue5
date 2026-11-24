// The user's list of 2026-11-22 (docs/improvements16.txt; the plan docs/improvements16_plan.md), its twelfth phase: the caves'
// weapons. Their items are found weapons copied by 945 from weapons of the table (each hero's fit kept, their meshes and grips the
// originals' or, for the miner's pick, another mesh set on the original's grip by the two meshes' measured frames): a miner's pick that
// breaks cave rubble, a shard blade of crystal mended only with geode shards, a lost adventurer's named blade on a skeleton deep in a
// cave, bone weapons dark and brittle, a lightless bow whose shot leaves her hidden. Here: the rubble across a set's side tunnel (a
// tunnel the set's rooms stay joined without) and the cache between its two piles, broken by the pick's blow or three of the Warrior's;
// the lost blade's place; a weapon's own look; the shard blade's mending.
#include "RD/RDDungeonGenerator.h"
#include "RD/RDSection.h"
#include "RD/RDCombat.h"
#include "RD/RDGameInstance.h"
#include "RD/RDMistward.h"
#include "Components/BoxComponent.h"
#include "Components/StaticMeshComponent.h"
#include "Engine/CollisionProfile.h"
#include "Engine/StaticMesh.h"
#include "Engine/World.h"
DEFINE_LOG_CATEGORY_STATIC(LogRDCave16d, Log, All);

// ================================================================================================ the rubble and its cache
void ARDSection::CaveRubbleSet16()
{
	CaveRubble16.Reset();
	if (!Generator || Generator->RubbleMeshes16.Num() == 0 || CaveRuns16.Num() == 0) return;
	FRandomStream R(Seed ^ 0x2BB1E16);          // (its own stream: the plan's draws stay where they were)
	// (the share is rolled once: by the plan for its side tunnel to nowhere; here only when there is none and a loop's tunnel may take it
	// (PR #119's review: rolled twice on two streams, a capped spur could stand with no rubble))
	const bool bHasSpur = CaveRuns16.ContainsByPredicate([](const FCaveRun16& Rn) { return Rn.To == CaveSpurTo16; });
	if (!bHasSpur && R.FRand() >= Generator->RubbleShare16) return;
	// (a side tunnel: one between two kit rooms that stay joined by the others; never a portal's)
	auto Joined = [&](int32 Skip, int32 A, int32 B)
	{
		TArray<int32> Up; Up.Init(-1, CavePlaced16.Num());
		auto Find = [&](int32 X) { while (Up.IsValidIndex(X) && Up[X] >= 0) X = Up[X]; return X; };
		for (int32 K = 0; K < CaveRuns16.Num(); ++K)
		{
			const FCaveRun16& Rn = CaveRuns16[K];
			if (K == Skip || !Up.IsValidIndex(Rn.From) || !Up.IsValidIndex(Rn.To)) continue;
			const int32 Fa = Find(Rn.From), Fb = Find(Rn.To);
			if (Fa != Fb) Up[Fa] = Fb;
		}
		return Find(A) == Find(B);
	};
	// (a spur (the plan's side tunnel to nowhere) first: one pile across it, the cache at its end; else a loop's tunnel: a pile at
	// each end, the cache between)
	TArray<int32> Cand, Spurs;
	for (int32 K = 0; K < CaveRuns16.Num(); ++K)
	{
		const FCaveRun16& Rn = CaveRuns16[K];
		if (Rn.Points.Num() < 2 || !CavePlaced16.IsValidIndex(Rn.From)) continue;
		if (Rn.To == CaveSpurTo16 && Rn.Length >= 900.f) { Spurs.Add(K); continue; }
		if (Rn.Length < 1800.f || !CavePlaced16.IsValidIndex(Rn.To)) continue;
		if (Joined(K, Rn.From, Rn.To)) Cand.Add(K);
	}
	const bool bSpur = Spurs.Num() > 0;
	if (!bSpur && Cand.Num() == 0) return;
	const FCaveRun16& Run = CaveRuns16[bSpur ? Spurs[R.RandRange(0, Spurs.Num() - 1)] : Cand[R.RandRange(0, Cand.Num() - 1)]];
	const FVector O = GetActorLocation();
	auto PointAt = [&](float F, FVector& P, FVector& D)
	{
		const float Want = F * Run.Length; float Acc = 0.f;
		for (int32 I = 1; I < Run.Points.Num(); ++I)
		{
			const float Seg = FVector::Dist(Run.Points[I], Run.Points[I - 1]);
			if (Acc + Seg >= Want || I == Run.Points.Num() - 1)
			{
				const float A = Seg > 1.f ? FMath::Clamp((Want - Acc) / Seg, 0.f, 1.f) : 0.f;
				P = O + FMath::Lerp(Run.Points[I - 1], Run.Points[I], A); D = (Run.Points[I] - Run.Points[I - 1]).GetSafeNormal2D();
				return;
			}
			Acc += Seg;
		}
	};
	const float Half = Generator->CaveTunnels16.IsValidIndex(Run.Kit) && Generator->CaveTunnels16[Run.Kit].Mesh
		? (float)Generator->CaveTunnels16[Run.Kit].Mesh->GetBoundingBox().GetExtent().Y : 450.f;
	const float S = Generator->TileSize;
	FVector Cache, CacheDir; PointAt(bSpur ? 0.8f : 0.5f, Cache, CacheDir);
	// (phase 13: a side tunnel to nowhere may be flooded instead: its middle under water, its dry end the cache and a piece of the
	// drowned knight's set)
	// (by a hash of the set's seed, not the stream's next draw: a stream seeded by its seed with a constant XORed in gives nearly the
	// same first draws to neighbouring seeds, and a whole session's side tunnels came out all rubble (0 floods in 25 sets))
	// (a loop's tunnel may flood too (a session with no side tunnel to nowhere had no water at all): 14 m about its middle, the cache and the
	// drowned piece under it)
	const float Lf = Run.Length > 1.f ? FMath::Min(0.2f, 700.f / Run.Length) : 0.2f;
	const float FloodRoll = (float)(HashCombine((uint32)Seed, 0xF100D16u) % 10000u) / 10000.f;
	const bool bFloodRolled = FloodRoll < Generator->FloodShare16;
	const bool bFlood = bFloodRolled && CaveFloodSet16(Run, Half, bSpur ? 0.25f : 0.5f - Lf, bSpur ? 0.7f : 0.5f + Lf);
	UE_LOG(LogRDCave16d, Log, TEXT("RDCAVE16 (%d,%d): the water's roll %.3f against %.2f, %s"), Coord.X, Coord.Y, FloodRoll, Generator->FloodShare16,
		bFlood ? TEXT("flooded") : bFloodRolled ? TEXT("rolled, but the water was not laid") : TEXT("rubble"));
	for (int32 Pile = 0; Pile < (bFlood ? 0 : bSpur ? 1 : 2); ++Pile)
	{
		FCaveRubble16 Rb; Rb.Index = Pile; Rb.Cache = Cache;
		PointAt(bSpur ? 0.4f : Pile == 0 ? 0.3f : 0.7f, Rb.At, Rb.Dir);
		if (Generator->RubbleCleared16.Contains(FIntVector(Coord.X, Coord.Y, Pile))) { Rb.Hits = -1; CaveRubble16.Add(Rb); continue; }
		// (its run's tiles within a tile and a half of it blocked: the paths go round by the other tunnels)
		for (int32 T = 0; T < Owner.Num(); ++T)
		{
			if (Owner[T] != Run.Room) continue;
			const FIntPoint Tl(T % N, T / N);
			const FVector W = TileWorld(Tl, CaveFloorAt16(Tl));
			if (FVector::Dist2D(W, Rb.At) <= 1.25f * S) { Blocked[T] = true; Rb.Tiles.Add(Tl); }
		}
		if (bBuildInteractive && GetWorld() && GetWorld()->IsGameWorld())
		{
			const FRotator Yaw(0.f, Rb.Dir.Rotation().Yaw, 0.f);
			UBoxComponent* B = NewObject<UBoxComponent>(this);
			B->SetupAttachment(RootComponent);
			B->SetRelativeTransform(FTransform(Yaw, Rb.At + FVector(0, 0, 160.f) - O));
			B->SetBoxExtent(FVector(70.f, Half * 0.85f, 160.f));
			B->SetCollisionProfileName(UCollisionProfile::BlockAll_ProfileName);
			B->SetHiddenInGame(true);
			B->RegisterComponent();
			Rb.Comps.Add(B); CaveComps16.Add(B);
			const FVector Side = FVector(-Rb.Dir.Y, Rb.Dir.X, 0.f);
			// (a pile to the roof's height: three rocks across the floor, two on them (three loose on the floor read as a way past while an
			// unseen box stood in it: the first picture))
			for (int32 K = 0; K < 5; ++K)
			{
				UStaticMesh* Ms = Generator->RubbleMeshes16[R.RandRange(0, Generator->RubbleMeshes16.Num() - 1)];
				if (!Ms) continue;
				UStaticMeshComponent* C = NewObject<UStaticMeshComponent>(this);
				C->SetMobility(EComponentMobility::Movable);
				C->SetStaticMesh(Ms);
				C->SetupAttachment(RootComponent);
				const bool bTop = K >= 3;
				const float Lat = bTop ? (K == 3 ? -0.3f : 0.3f) : (K - 1) * 0.6f;
				const FVector At = Rb.At + Side * (Lat * Half) + Rb.Dir * R.FRandRange(-40.f, 40.f) + FVector(0, 0, bTop ? 110.f : -20.f);
				const float Sc = R.FRandRange(Generator->RubbleScale16.X, Generator->RubbleScale16.Y) * (bTop ? 0.8f : 1.f);
				C->SetRelativeTransform(FTransform(FRotator(R.FRandRange(-12.f, 12.f), R.FRandRange(0.f, 360.f), R.FRandRange(-12.f, 12.f)), At - O, FVector(Sc)));
				C->SetCollisionProfileName(UCollisionProfile::NoCollision_ProfileName);
				C->RegisterComponent();
				Rb.Comps.Add(C); CaveComps16.Add(C);
			}
		}
		CaveRubble16.Add(Rb);
	}
	// (the cache between the piles: a chest of kind "cache", out of the set's chests to loot (a hero without a pick may never reach it))
	FurnRoom = -1;
	AddContainer(TEXT("Chest"), Cache, CacheDir.Rotation().Yaw + 90.f, TEXT("cache"));
	if (bFlood && bBuildInteractive && GetWorld() && GetWorld()->IsGameWorld())
	{
		// (the drowned knight's piece of this cave beside the cache, once a run)
		const FName Pc = Generator->DrownedPieceOf16();
		if (!Pc.IsNone() && !Generator->DrownedLaid16.Contains(Coord))
		{
			Generator->DrownedLaid16.Add(Coord); Generator->bDrownedLaid16 = true;
			TArray<float> Wr; Wr.Init(-1.f, 1);
			Generator->DropLoot(Cache + CacheDir * 120.f, { Pc }, Wr);
			CaveLostLine16 += FString::Printf(TEXT("%sdrowned|%s|%.0f|%.0f|%.0f"), CaveLostLine16.IsEmpty() ? TEXT("") : TEXT(";"), *Pc.ToString(), Cache.X + CacheDir.X * 120.f, Cache.Y + CacheDir.Y * 120.f, Cache.Z);
		}
	}
	UE_LOG(LogRDCave16d, Log, TEXT("RDCAVE16 (%d,%d): %s across a %s of %.0f m, its cache at (%.0f, %.0f)"), Coord.X, Coord.Y, bFlood ? TEXT("water") : TEXT("rubble"), bSpur ? TEXT("side tunnel to nowhere") : TEXT("loop's tunnel"), Run.Length / 100.f, Cache.X, Cache.Y);
}

void ARDSection::ClearRubble16(int32 K)
{
	if (!CaveRubble16.IsValidIndex(K) || CaveRubble16[K].Hits < 0) return;
	FCaveRubble16& Rb = CaveRubble16[K];
	for (UPrimitiveComponent* C : Rb.Comps) if (IsValid(C)) { CaveComps16.Remove(C); C->DestroyComponent(); }
	Rb.Comps.Reset();
	const FIntPoint CacheT = WorldToLocal(Rb.Cache);
	for (const FIntPoint& T : Rb.Tiles) if (In(T) && T != CacheT) Blocked[Idx(T)] = false;          // (the cache chest's own tile stays blocked (PR #119's review))
	Rb.Hits = -1;
	if (Generator)
	{
		Generator->RubbleCleared16.Add(FIntVector(Coord.X, Coord.Y, Rb.Index));
		Generator->PlaySoundAt(TEXT("Env.BodyFall"), Rb.At);
	}
}

void ARDDungeonGenerator::StrikeRubble16(const FVector& From, const FVector& Fw, float Reach, FName Gear)
{
	if (!bCave16) return;
	for (const TPair<FIntPoint, TObjectPtr<ARDSection>>& Kv : Sections)
	{
		ARDSection* S = Kv.Value;
		if (!IsValid(S)) continue;
		for (int32 K = 0; K < S->CaveRubble16.Num(); ++K)
		{
			ARDSection::FCaveRubble16& Rb = S->CaveRubble16[K];
			if (Rb.Hits < 0) continue;
			const FVector D = (Rb.At - From) * FVector(1, 1, 0);
			if (D.Size() > Reach + 160.f || FMath::Abs(Rb.At.Z - From.Z) > 300.f || FVector::DotProduct(D.GetSafeNormal(), Fw) < 0.3f) continue;
			const bool bPick = RubbleBreakers16.Contains(Gear);
			const bool bHero = !RubbleHero16.IsNone() && CurrentHero == RubbleHero16;
			if (!bPick && !bHero)
			{
				PlaySoundAt(TEXT("Player.Hit.Axe"), Rb.At);
				if (PlayerCombat) PlayerCombat->ShowMessage(TEXT("The rubble does not move: a miner's pick would break it"));
				continue;
			}
			if (bPick || ++Rb.Hits >= RubbleHeroHits16)
			{
				S->ClearRubble16(K);
				if (PlayerCombat) PlayerCombat->ShowMessage(TEXT("The rubble breaks: the way is open"));
			}
			else
			{
				PlaySoundAt(TEXT("Player.Hit.Axe"), Rb.At);
				if (PlayerCombat) PlayerCombat->ShowMessage(FString::Printf(TEXT("The rubble shifts (%d of %d blows)"), Rb.Hits, RubbleHeroHits16));
			}
		}
	}
}

// ================================================================================================ the lost blade
FName ARDDungeonGenerator::LostBladeOf16() const
{
	if (LostBlades16.Num() == 0) return NAME_None;
	const URDGameInstance* GI = URDGameInstance::Of(this);
	const FString Key = GI && !GI->CaveKey15.IsEmpty() ? GI->CaveKey15 : FString(TEXT("cave"));
	if (GI && GI->LostBladeCaves16.Contains(Key)) return NAME_None;          // (taken: this cave's is gone)
	return LostBlades16[GetTypeHash(Key) % (uint32)LostBlades16.Num()];
}

void ARDDungeonGenerator::NoteLostBladeTaken16(const TArray<FName>& Things)
{
	if (!bCave16 || (LostBlades16.Num() == 0 && DrownedPieces16.Num() == 0)) return;
	URDGameInstance* GI = URDGameInstance::Of(this);
	if (!GI) return;
	for (const FName& T : Things)
	{
		// (any band of a lost blade: its name ends with the blade's own)
		const FString S = T.ToString();
		const FString Key = !GI->CaveKey15.IsEmpty() ? GI->CaveKey15 : FString(TEXT("cave"));
		if (DrownedPieces16.Contains(T)) { GI->DrownedCaves16.AddUnique(Key); continue; }          // (the drowned knight's piece of this cave (PR #120's review))
		if (!LostBlades16.ContainsByPredicate([&S](const FName& B) { return S.EndsWith(B.ToString()); })) continue;
		GI->LostBladeCaves16.AddUnique(Key);
		UE_LOG(LogRDCave16d, Log, TEXT("RDCAVE16 the lost %s taken: %s lays it no more"), *S, *Key);
	}
}

void ARDSection::CaveLostBlade16()
{
	// (deep in the cave: the first set two rings out from the start laid this run, in its lowest kit room, by its middle)
	if (!Generator || Generator->bLostBladeLaid16 || FMath::Max(FMath::Abs(Coord.X), FMath::Abs(Coord.Y)) < 2) return;
	UWorld* W = GetWorld();
	if (!bBuildInteractive || !W || !W->IsGameWorld()) return;
	const FName Base = Generator->LostBladeOf16();
	if (Base.IsNone()) return;
	// (its band: the highest whose tier the set's reaches (a cave's blade as strong as its tier's weapons))
	FName Blade = Base;
	{
		const int32 T = Generator->GlobalTier(Generator->TierOf(Coord));
		int32 BestT = -1;
		for (const TCHAR* Band : { TEXT(""), TEXT("Fine "), TEXT("Masterwork "), TEXT("Exalted "), TEXT("Celestial "), TEXT("Divine ") })
		{
			const FName Nm(*(FString(Band) + Base.ToString()));
			const int32 Ix = Generator->FindItem(Nm);
			if (Ix < 0) continue;
			const int32 It = Generator->Items[Ix].Tiers.Num() > 0 ? Generator->Items[Ix].Tiers[0] : 1;
			if (It <= T && It > BestT) { BestT = It; Blade = Nm; }
		}
	}
	int32 Low = -1;
	for (int32 I = 0; I < CavePlaced16.Num(); ++I)
		if (CavePlaced16[I].Kit >= 0 && Rooms[I].Kind != ERDRoomKind::Junction && CaveRoomTiles16.IsValidIndex(I) && CaveRoomTiles16[I].Num() > 0 && (Low < 0 || CavePlaced16[I].Z < CavePlaced16[Low].Z)) Low = I;
	if (Low < 0) return;
	// (on a floor tile of the room nearest its middle that nothing stands on)
	const float S = Generator->TileSize;
	const FVector Mid = GetActorLocation() + FVector((CavePlaced16[Low].At.X + 0.5f) * S, (CavePlaced16[Low].At.Y + 0.5f) * S, CavePlaced16[Low].Z);
	FIntPoint Best(-1, -1); float BestD = 1e9f;
	for (const FIntPoint& T : CaveRoomTiles16[Low])
	{
		if (!In(T) || Blocked[Idx(T)]) continue;
		const float D = FVector::Dist2D(TileWorld(T, 0.f), Mid);
		if (D < BestD) { BestD = D; Best = T; }
	}
	if (Best.X < 0) return;
	const FVector At = TileWorld(Best, CaveFloorAt16(Best));
	if (Generator->LostSkeleton16)
	{
		UStaticMeshComponent* C = NewObject<UStaticMeshComponent>(this);
		C->SetMobility(EComponentMobility::Movable);
		C->SetStaticMesh(Generator->LostSkeleton16);
		C->SetupAttachment(RootComponent);
		C->SetRelativeTransform(FTransform(Generator->LostSkeletonTurn16 + FRotator(0.f, (float)(Seed % 360), 0.f), At - GetActorLocation()));
		C->SetCollisionProfileName(UCollisionProfile::NoCollision_ProfileName);
		C->RegisterComponent();
		CaveComps16.Add(C);
	}
	const FVector PileAt = At + FVector(70.f, 0.f, 0.f);
	TArray<float> Wr; Wr.Init(-1.f, 1);
	Generator->DropLoot(PileAt, { Blade }, Wr);
	Generator->bLostBladeLaid16 = true;
	CaveLostLine16 += FString::Printf(TEXT("%slost|%s|%.0f|%.0f|%.0f"), CaveLostLine16.IsEmpty() ? TEXT("") : TEXT(";"), *Blade.ToString(), PileAt.X, PileAt.Y, PileAt.Z);          // (beside the drowned piece's line, not over it)
	UE_LOG(LogRDCave16d, Log, TEXT("RDCAVE16 (%d,%d): the lost %s by a skeleton in room %d"), Coord.X, Coord.Y, *Blade.ToString(), Low);
}

TArray<FString> ARDDungeonGenerator::GetCaveRubble16(FIntPoint Section) const
{
	TArray<FString> Out;
	const ARDSection* S = GetSection(Section);
	if (!S) return Out;
	for (const ARDSection::FCaveRubble16& Rb : S->CaveRubble16)
		Out.Add(FString::Printf(TEXT("rubble|%d|%.0f|%.0f|%.0f|%d|%d|%.0f|%.0f|%.0f"), Rb.Index, Rb.At.X, Rb.At.Y, Rb.At.Z, Rb.Hits < 0 ? 1 : 0, FMath::Max(Rb.Hits, 0), Rb.Cache.X, Rb.Cache.Y, Rb.Cache.Z));
	if (!S->CaveLostLine16.IsEmpty()) { TArray<FString> Ls; S->CaveLostLine16.ParseIntoArray(Ls, TEXT(";")); Out.Append(Ls); }
	for (const ARDSection::FCaveFlood16& Fl : S->CaveFloods16)
		if (Fl.Pts.Num() > 1) Out.Add(FString::Printf(TEXT("flood|%.0f|%.0f|%.0f|%.0f|%.0f|%.0f|%.0f|%d"), Fl.Pts[0].X, Fl.Pts[0].Y, Fl.Pts[0].Z, Fl.Pts.Last().X, Fl.Pts.Last().Y, Fl.Pts.Last().Z, Fl.WaterZ, Fl.Pts.Num()));
	return Out;
}

bool ARDDungeonGenerator::IsWalkableAt16(FVector At) const
{
	const ARDSection* S = GetSection(WorldToSection(At));
	return S && S->IsWalkable(S->WorldToLocal(At));
}

// ================================================================================================ her weapons
void URDCombatComponent::ApplyWeaponLook16(UStaticMeshComponent* C, const FRDWeaponDef& W) const
{
	if (!C || !Generator) return;
	const TObjectPtr<UMaterialInterface>* Mt = W.Item.IsNone() ? nullptr : Generator->WeaponLooks16.Find(W.Item);
	if (Mt && *Mt) { for (int32 I = 0; I < C->GetNumMaterials(); ++I) C->SetMaterial(I, *Mt); }
	else C->EmptyOverrideMaterials();
}

bool URDCombatComponent::IsLightless16(int32 Index) const
{
	return Generator && Generator->Weapons.IsValidIndex(Index) && !Generator->Weapons[Index].Item.IsNone() && Generator->Lightless16.Contains(Generator->Weapons[Index].Item);
}

bool URDCombatComponent::MendWith16(FName Item)
{
	// (a thing that mends a weapon no repair item can: the shard blade and its geode shards)
	if (!Generator || GetItemCount(Item) <= 0) return false;
	SyncWear();
	for (int32 I = 0; I < Generator->Weapons.Num(); ++I)
	{
		const FRDWeaponDef& W = Generator->Weapons[I];
		const FRDMend16* Md = W.Item.IsNone() ? nullptr : Generator->MendOnly16.Find(W.Item);
		if (!Md || !Md->By.Contains(Item) || W.Durability <= 0.f || !Wear.IsValidIndex(I) || Wear[I] >= W.Durability - 0.01f) continue;
		Wear[I] = FMath::Min(W.Durability, Wear[I] + W.Durability * Md->Share);
		RemoveItem(Item, 1);
		ShowMessage(FString::Printf(TEXT("The %s mends your %s: %.0f / %.0f"), *Item.ToString().ToLower(), *W.Name.ToString(), Wear[I], W.Durability));
		return true;
	}
	return false;
}
