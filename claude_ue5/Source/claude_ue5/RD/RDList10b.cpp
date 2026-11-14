// The user's list of 2026-11-10 (docs/improvements10.txt), its second phase's rules that are the generator's:
//   - "when the tier boss appears, a teleporter back to the first dungeon room or to brokenspire should spawn there with him":
//     a pad in his room as he is set (PlaceBoss, so a boss set again after a trip has his too); F takes her to the first room,
//     [G] turns it to the town on a level with a way back (ReturnToTown);
//   - "a library's bookshelves should contain either scrolls of that tier or below or crafting components for scrolls of that
//     tier or below, could also contain tomes": each shelf (ARDSection::Shelves, from the library's furnishing) is searched with F
//     once; what it holds is drawn from a stream of its own (the set, the shelf, the session's seed), as a container's is;
//   - "if the player walks under a structure that blocks sight of her, make the structure see-through": the town's instanced
//     pieces that stand between her and the camera (where the camera is, and where its boom would put it), but what she stands
//     on, are hidden while they stand there; a hidden copy of each keeps its collision (only the camera passes through it:
//     bolts, sight lines and traces still meet it), so the boom no longer stops on them and the camera stays out where it was.
#include "RD/RDDungeonGenerator.h"
#include "RD/RDSection.h"
#include "RD/RDMistward.h"
#include "RD/RDCombat.h"
#include "Components/CapsuleComponent.h"
#include "Components/InstancedStaticMeshComponent.h"
#include "Camera/PlayerCameraManager.h"
#include "Engine/StaticMesh.h"
#include "Engine/World.h"
#include "GameFramework/Character.h"
#include "GameFramework/CharacterMovementComponent.h"
#include "GameFramework/PlayerController.h"
#include "GameFramework/SpringArmComponent.h"
#include "Kismet/GameplayStatics.h"
#include "HAL/PlatformTime.h"

DEFINE_LOG_CATEGORY_STATIC(LogRDList10b, Log, All);

// ================================================================================================ the boss's teleporter
bool ARDDungeonGenerator::CanBossPortToTown() const
{
	return bTownLink && !bTown && !TownLevel.IsEmpty();
}

void ARDDungeonGenerator::PlaceBossPort(int32 Tier, ARDSection* S, int32 Room, const TArray<FVector>& Free, const TArray<FVector>& Spots)
{
	if (!S || !GetWorld()) return;
	if (TObjectPtr<ARDTeleporter>* Old = BossPortActors.Find(Tier); Old && IsValid(*Old)) return;
	// (the free tile farthest from the room's middle that none of him and his band stands on (PR #39's review: in a small room
	// the band's spots run to the last tile, Free[min(N-1, 1+2I)], and their parts would lie on the pad, F taking them first))
	FVector At = S->GetRoomCenter(Room);
	for (int32 I = Free.Num() - 1; I >= 0; --I)
		if (!Spots.ContainsByPredicate([&](const FVector& P) { return FVector::Dist2D(P, Free[I]) < 100.f; })) { At = Free[I]; break; }
	FActorSpawnParameters Sp; Sp.SpawnCollisionHandlingOverride = ESpawnActorCollisionHandlingMethod::AlwaysSpawn;
	ARDTeleporter* A = GetWorld()->SpawnActor<ARDTeleporter>(ARDTeleporter::StaticClass(), FTransform(At), Sp);
	if (!A) return;
	A->Init(this, 0, false);
	BossPorts.Add(Tier, At); BossPortActors.Add(Tier, A);
	UE_LOG(LogRDList10b, Log, TEXT("RDBOSSPORT tier %d at (%.0f, %.0f, %.0f) in room %d of (%d,%d) (%d free tiles, %d taken by him and his band)"),
	       Tier, At.X, At.Y, At.Z, Room, S->Coord.X, S->Coord.Y, Free.Num(), Spots.Num());
}

void ARDDungeonGenerator::ClearBossPorts()
{
	for (TPair<int32, TObjectPtr<ARDTeleporter>>& A : BossPortActors) if (IsValid(A.Value)) A.Value->Destroy();
	BossPortActors.Reset(); BossPorts.Reset(); BossPortChoice = 0; BossPortUses = 0;
}

int32 ARDDungeonGenerator::BossPortNear(const FVector& From, float Reach) const
{
	int32 Best = 0; float Bd = Reach;
	for (const TPair<int32, FVector>& P : BossPorts)
	{
		const float D = FVector::Dist2D(P.Value, From);
		if (D < Bd && FMath::Abs(P.Value.Z - From.Z) < 300.f) { Bd = D; Best = P.Key; }
	}
	return Best;
}

TArray<FString> ARDDungeonGenerator::GetBossPortLines() const
{
	TArray<FString> Out;
	for (const TPair<int32, FVector>& P : BossPorts) Out.Add(FString::Printf(TEXT("%d|%.1f|%.1f|%.1f"), P.Key, P.Value.X, P.Value.Y, P.Value.Z));
	return Out;
}

FString ARDDungeonGenerator::BossPortDescribe(const FVector& From) const
{
	if (BossPortNear(From) <= 0) return FString();
	if (!CanBossPortToTown()) return TEXT("teleport back to the first room");
	return BossPortChoice == 1 ? FString::Printf(TEXT("teleport to %s    [G] the first room"), *WayBackName())
	                           : FString::Printf(TEXT("teleport back to the first room    [G] to %s"), *WayBackName());
}

FString ARDDungeonGenerator::BossPortUse(const FVector& From)
{
	const int32 T = BossPortNear(From);
	URDCombatComponent* Pc = GetPlayerCombat();
	if (T <= 0 || !Pc) return FString();
	if (IsArenaHolding()) { RefuseArenaExit(TEXT("pad")); return TEXT("arena barred"); }
	if (BossPortChoice == 1 && CanBossPortToTown())
	{
		++BossPortUses;
		UE_LOG(LogRDList10b, Log, TEXT("RDBOSSPORT tier %d: to %s"), T, *WayBackName());
		if (ReturnToTown()) return TEXT("town");
		Pc->ShowMessage(TEXT("The teleporter does not answer: the way back is shut"));
		return TEXT("pad");
	}
	APlayerController* PC = UGameplayStatics::GetPlayerController(this, 0);
	ACharacter* Her = PC ? Cast<ACharacter>(PC->GetPawn()) : nullptr;
	if (!Her) return FString();
	// (the first room's set is there before she is)
	GenerateSectionNow(FIntPoint::ZeroValue);
	if (TeleportFx) RDMSpawnFx(this, TeleportFx, Her->GetActorLocation(), FRotator::ZeroRotator, 1.f, nullptr, true, true);
	const FVector To = GetStartRoomCenter() + FVector(0.f, 0.f, Her->GetCapsuleComponent()->GetScaledCapsuleHalfHeight() + 10.f);
	Her->SetActorLocation(To, false, nullptr, ETeleportType::TeleportPhysics);
	Her->GetCharacterMovement()->StopMovementImmediately();
	if (TeleportFx) RDMSpawnFx(this, TeleportFx, To, FRotator::ZeroRotator, 1.f, nullptr, true, true);
	PlaySoundAt(TEXT("Env.Generate"), To);
	++Teleports; ++BossPortUses;
	Pc->ShowMessage(TEXT("The teleporter carries you back to the first room"));
	UE_LOG(LogRDList10b, Log, TEXT("RDBOSSPORT tier %d: to the first room (%.0f, %.0f, %.0f)"), T, To.X, To.Y, To.Z);
	return TEXT("teleport");
}

// ================================================================================================ the library's shelves

TArray<FName> ARDDungeonGenerator::ShelfLootOf(FIntPoint Section, int32 Index) const
{
	TArray<FName> Out;
	const int32 T = GlobalTier(TierOf(Section));
	// (of this tier or below: an item of no tiers is of every tier)
	auto Low = [T](const FRDItemDef& It) { if (It.Tiers.Num() == 0) return true; for (const int32 X : It.Tiers) if (X <= T) return true; return false; };
	// (a scroll's parts: those of a scroll recipe whose scroll is of this tier or below)
	TSet<FName> Parts;
	for (const FRDRecipe& Rc : Recipes)
	{
		const int32 Pi = FindItem(Rc.Item);
		if (Pi < 0 || Items[Pi].Kind != ERDItemKind::Scroll || !Low(Items[Pi])) continue;
		for (const FRDRecipePart& Pt : Rc.Parts) for (const FName& N : Pt.AnyOf) Parts.Add(N);
	}
	// (the kind first: "either scrolls ... or crafting components for scrolls ..., could also contain tomes": scrolls 45 %, their
	// parts 40 %, a tome 15 % (by the items' weights alone the tomes' were nine in ten, 868 l10f's census); then one of that kind
	// by the items' weights)
	auto KindOf = [&](const FRDItemDef& It) -> int32
	{
		if (!Low(It)) return -1;
		if (It.Kind == ERDItemKind::Scroll) return 0;
		if (It.Kind == ERDItemKind::Component && Parts.Contains(It.Name)) return 1;
		if (It.Kind == ERDItemKind::Tome) return 2;
		return -1;
	};
	// (a stream of its own for each shelf: what it holds does not depend on the order she searches them in)
	FRandomStream R((int32)HashCombine(HashCombine((uint32)SessionSeed ^ 0x5E1Fu, GetTypeHash(Section)), GetTypeHash(Index * 131 + 7)));
	if (R.FRand() >= ShelfLootChance) return Out;
	float Sum[3] = { 0.f, 0.f, 0.f };
	for (const FRDItemDef& It : Items) if (const int32 Kd = KindOf(It); Kd >= 0) Sum[Kd] += FMath::Max(It.Weight, 0.1f);
	static const float RDShelfShare[3] = { 0.45f, 0.40f, 0.15f };
	float Total = 0.f; for (int32 Kd = 0; Kd < 3; ++Kd) if (Sum[Kd] > 0.f) Total += RDShelfShare[Kd];
	if (Total <= 0.f) return Out;
	const int32 N = R.FRand() < 0.3f ? 2 : 1;
	for (int32 K = 0; K < N; ++K)
	{
		float Uk = R.FRand() * Total; int32 Kd = 0;
		for (; Kd < 3; ++Kd) { if (Sum[Kd] <= 0.f) continue; Uk -= RDShelfShare[Kd]; if (Uk < 0.f) break; }
		if (Kd >= 3) for (Kd = 2; Kd > 0 && Sum[Kd] <= 0.f; --Kd) {}
		float U = R.FRand() * Sum[Kd];
		const FRDItemDef* Got = nullptr;
		for (const FRDItemDef& It : Items) { if (KindOf(It) != Kd) continue; Got = &It; U -= FMath::Max(It.Weight, 0.1f); if (U < 0.f) break; }
		if (!Got) continue;
		// (a spell tome is one of the spells of the set's tier, by the table's chances, as in a container)
		if (Got->Kind == ERDItemKind::Tome && Got->Spell.IsNone())
		{
			const FName Sp = TomeSpellOf(Section, 50000 + Index, K);
			if (const FName Ti = TomeItemOf(Sp); !Ti.IsNone()) Out.Add(Ti);
			continue;
		}
		Out.Add(Got->Name);
	}
	return Out;
}

const ARDSection* ARDDungeonGenerator::ShelfNear(const FVector& From, int32& OutIndex) const
{
	OutIndex = -1;
	const ARDSection* Best = nullptr; float Bd = 1e9f;
	for (const TPair<FIntPoint, TObjectPtr<ARDSection>>& Kv : Sections)
	{
		const ARDSection* S = Kv.Value;
		if (!IsValid(S)) continue;
		for (int32 I = 0; I < S->Shelves.Num(); ++I)
		{
			const ARDSection::FShelf& Sh = S->Shelves[I];
			if (ShelvesSearched.Contains(FIntVector(S->Coord.X, S->Coord.Y, I)) || FMath::Abs(Sh.At.Z - From.Z) > 200.f) continue;
			// (from her to the shelf's front, within reach)
			const FVector Front = Sh.At + FRotator(0, Sh.Yaw, 0).RotateVector(FVector(Sh.Depth * 0.5f, 0, 0));
			const float D = FVector::Dist2D(Front, From);
			if (D < 160.f && D < Bd) { Bd = D; Best = S; OutIndex = I; }
		}
	}
	// (a door or a container nearer than it is what F does, in any set round her (PR #39's review: a shelf by a set's border
	// took F from the next set's door))
	if (Best)
	{
		const FIntPoint Here = WorldToSection(From);
		for (int32 Dx = -1; Dx <= 1; ++Dx)
			for (int32 Dy = -1; Dy <= 1; ++Dy)
				if (const ARDSection* S = GetSection(Here + FIntPoint(Dx, Dy)))
				{
					bool bD = false; int32 Di = -1;
					if (S->FindNearestInteractive(From, Bd, bD, Di) < Bd) { OutIndex = -1; return nullptr; }
				}
	}
	return Best;
}

FString ARDDungeonGenerator::ShelfDescribe(const FVector& From) const
{
	int32 I = -1;
	return ShelfNear(From, I) ? FString(TEXT("search the bookshelf")) : FString();
}

FString ARDDungeonGenerator::ShelfSearch(const FVector& From)
{
	int32 I = -1;
	const ARDSection* S = PlayerCombat ? ShelfNear(From, I) : nullptr;
	if (!S) return FString();
	ShelvesSearched.Add(FIntVector(S->Coord.X, S->Coord.Y, I)); ++ShelvesSearchedCount;
	const TArray<FName> Got = ShelfLootOf(S->Coord, I);
	TArray<FString> Names;
	for (const FName& N : Got) if (FindItem(N) >= 0) { PlayerCombat->AddItem(N, 1); Names.Add(N.ToString()); }
	if (Names.Num() == 0) PlayerCombat->ShowMessage(TEXT("You search the bookshelf: dusty books, nothing of use"));
	else { PlayerCombat->ShowMessage(FString::Printf(TEXT("You search the bookshelf:  %s"), *FString::Join(Names, TEXT(", ")))); PlaySoundAt(TEXT("Player.Loot"), From); }
	UE_LOG(LogRDList10b, Log, TEXT("RDSHELF (%d,%d) %d searched: %s"), S->Coord.X, S->Coord.Y, I, Names.Num() ? *FString::Join(Names, TEXT(", ")) : TEXT("nothing"));
	return TEXT("shelf");
}

TArray<FString> ARDDungeonGenerator::GetShelfLines() const
{
	TArray<FString> Out;
	for (const TPair<FIntPoint, TObjectPtr<ARDSection>>& Kv : Sections)
		if (const ARDSection* S = Kv.Value; IsValid(S))
			for (int32 I = 0; I < S->Shelves.Num(); ++I)
			{
				const ARDSection::FShelf& Sh = S->Shelves[I];
				const FVector Front = Sh.At + FRotator(0, Sh.Yaw, 0).RotateVector(FVector(Sh.Depth * 0.5f, 0, 0));
				Out.Add(FString::Printf(TEXT("%d|%d|%d|%.1f|%.1f|%.1f|%d|%d|%.1f|%.1f"), S->Coord.X, S->Coord.Y, I, Sh.At.X, Sh.At.Y, Sh.At.Z, Sh.Room,
				                        ShelvesSearched.Contains(FIntVector(S->Coord.X, S->Coord.Y, I)) ? 1 : 0, Front.X, Front.Y));
			}
	return Out;
}

// ================================================================================================ see-through structures
namespace
{
	/** a piece can hide her when its top stands this far over her feet (what is lower she stands on or steps over) */
	constexpr float RDSeeAbove = 60.f;
	constexpr int32 RDSeeMax = 160;
}

void ARDDungeonGenerator::ClearSeeThrough()
{
	for (const FSeeHidden& H : SeeHidden)
	{
		if (H.C.IsValid()) H.C->UpdateInstanceTransform(H.I, H.T, true, true, true);
		if (H.Proxy.IsValid())
		{
			H.Proxy->UpdateInstanceTransform(H.ProxyI, FTransform(FQuat::Identity, FVector(0, 0, -1e6), FVector(0.001f)), true, true, true);
			if (H.C.IsValid()) SeeProxyFree.FindOrAdd(H.C).Add(H.ProxyI);
		}
	}
	SeeHidden.Reset();
}

TArray<FString> ARDDungeonGenerator::GetSeeThroughLines() const
{
	TArray<FString> Out;
	for (const FSeeHidden& H : SeeHidden)
		if (H.C.IsValid() && H.C->GetStaticMesh())
			Out.Add(FString::Printf(TEXT("%s|%.1f|%.1f|%.1f|%d"), *H.C->GetStaticMesh()->GetName(), H.T.GetLocation().X, H.T.GetLocation().Y, H.T.GetLocation().Z, H.Proxy.IsValid() ? 1 : 0));
	return Out;
}

void ARDDungeonGenerator::TickSeeThrough(float Dt)
{
	SeeThroughClock += Dt;
	if (SeeThroughClock < SeeThroughNext) return;
	SeeThroughNext = SeeThroughClock + 0.1f;
	UWorld* W = GetWorld();
	APlayerController* PC = UGameplayStatics::GetPlayerController(this, 0);
	ACharacter* Her = PC ? Cast<ACharacter>(PC->GetPawn()) : nullptr;
	if (!W || !Her) { if (SeeHidden.Num() > 0) ClearSeeThrough(); return; }
	const float Hh = Her->GetCapsuleComponent()->GetScaledCapsuleHalfHeight();
	const FVector Feet = Her->GetActorLocation() - FVector(0, 0, Hh);
	const FVector Head = Her->GetActorLocation() + FVector(0, 0, Hh * 0.7f);
	// (where the camera is, and where its boom would put it with nothing in the way: a roof the boom stops under is between them)
	TArray<FVector> Ends;
	if (PC->PlayerCameraManager) Ends.Add(PC->PlayerCameraManager->GetCameraLocation());
	if (const USpringArmComponent* Boom = Her->FindComponentByClass<USpringArmComponent>())
	{
		const FRotator Rt = Boom->GetTargetRotation();
		const FVector Pivot = Boom->GetComponentLocation() + Boom->TargetOffset;
		Ends.Add(Pivot - Rt.Vector() * Boom->TargetArmLength + FRotationMatrix(Rt).TransformVector(Boom->SocketOffset));
	}
	// (the pieces hidden already: kept while a line from her to the camera still crosses their box)
	for (FSeeHidden& H : SeeHidden)
	{
		if (!H.C.IsValid() || !H.C->GetStaticMesh()) continue;
		const FBox Bx = H.C->GetStaticMesh()->GetBoundingBox().TransformBy(H.T);
		for (const FVector& E : Ends)
			if (FMath::LineBoxIntersection(Bx, Head, E, E - Head)) { H.Until = SeeThroughClock + SeeThroughHold; break; }
	}
	// (the new ones: every piece of her set (and the sets beside it) whose box the line meets: the town's roofs
	// have no collision, so no trace finds them; the pieces' boxes on a grid, made once a set)
	for (auto It = SeeGrids.CreateIterator(); It; ++It) if (!It.Key().IsValid()) It.RemoveCurrent();          // (dropped sets' grids go)
	TArray<ARDSection*> Near;
	const FIntPoint Here = WorldToSection(Her->GetActorLocation());
	// (a set still being built over frames has no grid yet (PR #39's review: made then, it held the pieces flushed so far and
	// never the later roofs))
	for (int32 Dx = -1; Dx <= 1; ++Dx) for (int32 Dy = -1; Dy <= 1; ++Dy) if (ARDSection* S = GetSection(Here + FIntPoint(Dx, Dy)); S && !S->IsBuilding()) Near.Add(S);
	for (const FVector& E : Ends)
	{
		const FVector2D Lo(FMath::Min(Head.X, E.X), FMath::Min(Head.Y, E.Y)), Hi(FMath::Max(Head.X, E.X), FMath::Max(Head.Y, E.Y));
		for (ARDSection* S : Near)
		{
			FSeeGrid& Gd = SeeGridOf(S);
			TSet<int32> Seen;
			for (int32 Gx = FMath::FloorToInt(Lo.X / 400.f); Gx <= FMath::FloorToInt(Hi.X / 400.f); ++Gx)
				for (int32 Gy = FMath::FloorToInt(Lo.Y / 400.f); Gy <= FMath::FloorToInt(Hi.Y / 400.f); ++Gy)
				{
					const TArray<int32>* Cl = Gd.Cells.Find(FIntPoint(Gx, Gy));
					if (!Cl) continue;
					for (const int32 Ri : *Cl)
					{
						if (Seen.Contains(Ri) || SeeHidden.Num() >= RDSeeMax) continue;
						Seen.Add(Ri);
						const FSeeRef& Rf = Gd.Refs[Ri];
						// (what she stands on stays: the floor, the walk under her, a step; a wall or roof between her and the camera goes
						// (884 k10i: in a home the camera was pressed into its walls, nothing over her crossed the line))
						if (Rf.B.Max.Z < Feet.Z + RDSeeAbove || !Rf.C.IsValid()) continue;
						if (Rf.B.IsInsideXY(Her->GetActorLocation()) && Rf.B.Min.Z < Feet.Z + 30.f) continue;          // (a piece round her feet)
						if (!FMath::LineBoxIntersection(Rf.B, Head, E, E - Head)) continue;
						HideSeeThrough(Rf.C.Get(), Rf.I);
					}
				}
		}
	}
	// (back as they were once no line has crossed them for a while)
	for (int32 I = SeeHidden.Num() - 1; I >= 0; --I)
	{
		FSeeHidden& H = SeeHidden[I];
		if (H.C.IsValid() && H.Until > SeeThroughClock) continue;
		if (H.C.IsValid()) H.C->UpdateInstanceTransform(H.I, H.T, true, true, true);
		if (H.Proxy.IsValid()) { H.Proxy->UpdateInstanceTransform(H.ProxyI, FTransform(FQuat::Identity, FVector(0, 0, -1e6), FVector(0.001f)), true, true, true); if (H.C.IsValid()) SeeProxyFree.FindOrAdd(H.C).Add(H.ProxyI); }
		SeeHidden.RemoveAtSwap(I);
	}
}

ARDDungeonGenerator::FSeeGrid& ARDDungeonGenerator::SeeGridOf(ARDSection* S)
{
	if (FSeeGrid* G = SeeGrids.Find(S)) return *G;
	FSeeGrid& Gd = SeeGrids.Add(S);
	const double T0 = FPlatformTime::Seconds();
	// (the hidden ones at their places as they were, looked up by component and instance)
	TMap<TPair<const UInstancedStaticMeshComponent*, int32>, FTransform> Was;
	for (const FSeeHidden& H : SeeHidden) if (H.C.IsValid()) Was.Add({ H.C.Get(), H.I }, H.T);
	TArray<UInstancedStaticMeshComponent*> Comps; S->GetComponents<UInstancedStaticMeshComponent>(Comps);
	for (UInstancedStaticMeshComponent* C : Comps)
	{
		if (!C || !C->GetStaticMesh() || C->ComponentHasTag(TEXT("RDSeeProxy")) || !C->IsVisible() || C->bHiddenInGame) continue;
		// (not the grass, flowers and small things: under the height a piece needs to hide her, or faded with distance)
		const FBox Mb = C->GetStaticMesh()->GetBoundingBox();
		if (C->InstanceEndCullDistance > 0 || Mb.GetSize().Z < RDSeeAbove) continue;
		for (int32 I = 0; I < C->GetInstanceCount(); ++I)
		{
			FTransform T;
			if (!C->GetInstanceTransform(I, T, true)) continue;
			if (const FTransform* Wt = Was.Find({ C, I })) T = *Wt;
			const FBox B = Mb.TransformBy(T);
			if (B.GetSize().GetMax() > 4000.f) continue;          // (nothing that big is a piece over her)
			const int32 Ri = Gd.Refs.Add({ C, I, B });
			for (int32 Gx = FMath::FloorToInt(B.Min.X / 400.f); Gx <= FMath::FloorToInt(B.Max.X / 400.f); ++Gx)
				for (int32 Gy = FMath::FloorToInt(B.Min.Y / 400.f); Gy <= FMath::FloorToInt(B.Max.Y / 400.f); ++Gy)
					Gd.Cells.FindOrAdd(FIntPoint(Gx, Gy)).Add(Ri);
		}
	}
	UE_LOG(LogRDList10b, Log, TEXT("RDSEETHROUGH grid of (%d,%d): %d pieces in %d cells, %.1f ms"), S->Coord.X, S->Coord.Y, Gd.Refs.Num(), Gd.Cells.Num(), (FPlatformTime::Seconds() - T0) * 1000.0);
	return Gd;
}

void ARDDungeonGenerator::HideSeeThrough(UInstancedStaticMeshComponent* C, int32 Inst)
{
	if (!C || SeeHidden.ContainsByPredicate([&](const FSeeHidden& H) { return H.C.Get() == C && H.I == Inst; })) return;
	FTransform T;
	if (!C->GetInstanceTransform(Inst, T, true)) return;
	// (its collision kept: a hidden copy at its place that the camera and sight lines pass through; a piece of no collision (the
	// town's roofs) needs none)
	if (C->Mobility != EComponentMobility::Movable) C->SetMobility(EComponentMobility::Movable);
	TWeakObjectPtr<UInstancedStaticMeshComponent> Px;
	int32 Pi = -1;
	if (C->GetCollisionEnabled() != ECollisionEnabled::NoCollision)
	{
		TWeakObjectPtr<UInstancedStaticMeshComponent>& Pr = SeeProxies.FindOrAdd(C);
		if (!Pr.IsValid())
		{
			UInstancedStaticMeshComponent* P = NewObject<UInstancedStaticMeshComponent>(C->GetOwner());
			P->ComponentTags.Add(TEXT("RDSeeProxy"));
			P->SetStaticMesh(C->GetStaticMesh());
			P->SetMobility(EComponentMobility::Movable);
			P->SetupAttachment(C->GetOwner()->GetRootComponent());
			P->SetCollisionObjectType(C->GetCollisionObjectType());
			P->SetCollisionResponseToChannels(C->GetCollisionResponseToChannels());
			// (the camera alone passes it (PR #39's review: ignoring Visibility too let her bolts fly through a wall she could not
			// walk through, and the horse's clear-line and ground traces pass it))
			P->SetCollisionResponseToChannel(ECC_Camera, ECR_Ignore);
			P->SetCollisionEnabled(C->GetCollisionEnabled());
			P->SetHiddenInGame(true); P->SetCastShadow(false);
			P->RegisterComponent();
			C->GetOwner()->AddInstanceComponent(P);
			Pr = P;
		}
		Px = Pr;
		TArray<int32>& Fr = SeeProxyFree.FindOrAdd(C);
		if (Fr.Num() > 0) { Pi = Fr.Pop(); Px->UpdateInstanceTransform(Pi, T, true, true, true); }
		else Pi = Px->AddInstance(T, true);
	}
	FTransform Tiny = T; Tiny.SetScale3D(T.GetScale3D() * 0.001f);
	C->UpdateInstanceTransform(Inst, Tiny, true, true, true);
	FSeeHidden H; H.C = C; H.I = Inst; H.T = T; H.Until = SeeThroughClock + SeeThroughHold; H.Proxy = Px; H.ProxyI = Pi;
	SeeHidden.Add(H); ++SeeThroughTotal;
}
