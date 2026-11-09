#include "RD/RDDungeonGenerator.h"
#include "Framework/Application/SlateApplication.h"
#include "Framework/Application/IInputProcessor.h"
#include "RD/RDSave.h"
#include "RD/RDGameInstance.h"
#include "RD/RDSection.h"
#include "RD/RDMonster.h"
#include "RD/RDCombat.h"
#include "RD/RDBlood.h"
#include "AudioDevice.h"
#include "AudioMixerBlueprintLibrary.h"
#include "Misc/CommandLine.h"
#include "HAL/IConsoleManager.h"
#include "Misc/FileHelper.h"
#include "Misc/App.h"
#include "Components/AudioComponent.h"
#include "Sound/SoundAttenuation.h"
#include "Sound/SoundBase.h"
#include "Sound/SoundWave.h"
#include "GameFramework/Character.h"
#include "GameFramework/CharacterMovementComponent.h"
#include "Engine/World.h"
#include "EngineUtils.h"
#include "GameFramework/Pawn.h"
#include "GameFramework/PlayerController.h"
#include "GameFramework/GameModeBase.h"
#include "Kismet/GameplayStatics.h"
#include "Misc/DateTime.h"
#include "Components/PostProcessComponent.h"
#include "Materials/MaterialInstanceDynamic.h"
#include "InputCoreTypes.h"
#include "EnhancedInputSubsystems.h"
#include "InputMappingContext.h"
#include "InputAction.h"
#include "Engine/LocalPlayer.h"
#include "Components/CapsuleComponent.h"
#include "Kismet/KismetSystemLibrary.h"
#include "Framework/Commands/InputBindingManager.h"
#include "Framework/Commands/UICommandInfo.h"
#include "Framework/Commands/InputChord.h"
#include "Misc/ConfigCacheIni.h"
#include "Misc/ScopeExit.h"
#include "NiagaraSystem.h"
#include "RD/RDMistward.h"

DEFINE_LOG_CATEGORY_STATIC(LogRandomDungeonGen, Log, All);

static TAutoConsoleVariable<int32> CVarRDHeroMenu(TEXT("rd.HeroMenu"), 1,
	TEXT("1: a dungeon level with heroes and a MenuLevel, played without ?Hero=, opens its menu first. 0: it plays its DefaultHero (scripted tests, reel renders)."));

static const int32 RDSoundSeed = 90417;
// (the list of 2026-11-08b: the gamepad's Start held this long with nothing open opens the Escape menu)
static constexpr double RDStartHoldSeconds = 0.5;
static const FName RDFireKeys[3] = { TEXT("Env.Torch"), TEXT("Env.Brazier"), TEXT("Env.Hearth") };
static const FName RDMusicKeys[4] = { TEXT("Music.Explore"), TEXT("Music.Combat"), TEXT("Atmos.Explore"), TEXT("Atmos.Combat") };

ARDDungeonGenerator::ARDDungeonGenerator()
{
	PrimaryActorTick.bCanEverTick = true;
	PrimaryActorTick.TickInterval = 0.f;
	PrimaryActorTick.bTickEvenWhenPaused = true;          // (her inventory pauses the game and is worked from Tick)
	RootComponent = CreateDefaultSubobject<USceneComponent>(TEXT("Root"));
	RevealPost = CreateDefaultSubobject<UPostProcessComponent>(TEXT("RevealPost"));
	RevealPost->SetupAttachment(RootComponent);
	RevealPost->bUnbound = true;
	RevealPost->Priority = 10.f;
}

FString ARDDungeonGenerator::KindName(ERDRoomKind K)
{
	switch (K)
	{
	case ERDRoomKind::Hall: return TEXT("Great hall");
	case ERDRoomKind::Barracks: return TEXT("Barracks");
	case ERDRoomKind::Prison: return TEXT("Prison cells");
	case ERDRoomKind::Torture: return TEXT("Torture chamber");
	case ERDRoomKind::Storeroom: return TEXT("Storeroom");
	case ERDRoomKind::Armory: return TEXT("Armory");
	case ERDRoomKind::Kitchen: return TEXT("Kitchen");
	case ERDRoomKind::Library: return TEXT("Library");
	case ERDRoomKind::Chapel: return TEXT("Chapel");
	case ERDRoomKind::Crypt: return TEXT("Crypt");
	case ERDRoomKind::Treasury: return TEXT("Treasury");
	case ERDRoomKind::GuardRoom: return TEXT("Guard room");
	case ERDRoomKind::Forge: return TEXT("Forge");
	case ERDRoomKind::Shrine: return TEXT("Shrine");
	case ERDRoomKind::HealFountain: return TEXT("Healing fountain");
	case ERDRoomKind::SpeedFountain: return TEXT("Fountain of speed");
	case ERDRoomKind::ManaFountain: return TEXT("Fountain of mana");
	case ERDRoomKind::Arena: return TEXT("Arena");
	case ERDRoomKind::TrapGauntlet: return TEXT("Trap gauntlet");
	case ERDRoomKind::Vault: return TEXT("Vault");
	case ERDRoomKind::ThroneRoom: return TEXT("Throne room");
	default: return TEXT("Hallway junction");
	}
}

AActor* ARDDungeonGenerator::GetTrackedActor() const
{
	return TrackedActor ? TrackedActor.Get() : UGameplayStatics::GetPlayerPawn(this, 0);
}

FIntPoint ARDDungeonGenerator::WorldToTile(FVector L) const
{
	// (the grid's origin is the loaded town's middle in the wilderness: 0 everywhere else)
	return FIntPoint(FMath::FloorToInt((L.X - GridOrigin.X) / TileSize), FMath::FloorToInt((L.Y - GridOrigin.Y) / TileSize));
}

FIntPoint ARDDungeonGenerator::SectionMinTile(FIntPoint S) const
{
	const int32 H = SectionTiles / 2;
	return FIntPoint(S.X * SectionTiles - H, S.Y * SectionTiles - H);
}

FIntPoint ARDDungeonGenerator::WorldToSection(FVector L) const
{
	const FIntPoint T = WorldToTile(L);
	const int32 H = SectionTiles / 2;
	return FIntPoint(FMath::FloorToInt((float)(T.X + H) / SectionTiles), FMath::FloorToInt((float)(T.Y + H) / SectionTiles));
}

FVector ARDDungeonGenerator::TileCenter(FIntPoint T) const
{
	float Z = 0.f;
	if (bTierFloors)
	{
		const int32 H = SectionTiles / 2;
		const FIntPoint S(FMath::FloorToInt((float)(T.X + H) / SectionTiles), FMath::FloorToInt((float)(T.Y + H) / SectionTiles));
		Z = SectionFloorZ(S);
		// (a stair's tile: its own height on the ramp)
		if (const ARDSection* Sec = GetSection(S))
		{
			Z += Sec->StairRiseAt(T - SectionMinTile(S));
		}
	}
	return FVector(GridOrigin.X + (T.X + 0.5f) * TileSize, GridOrigin.Y + (T.Y + 0.5f) * TileSize, Z);
}

int32 ARDDungeonGenerator::SectionSeed(FIntPoint S) const
{
	const uint32 Base = IsStartSection(S) ? (uint32)StartSeed : (uint32)SessionSeed;
	return (int32)HashCombine(HashCombine(Base, GetTypeHash(S.X * 7919 + 3)), GetTypeHash(S.Y * 104729 + 17));
}

bool ARDDungeonGenerator::IsSectionGenerated(FIntPoint S) const { return Sections.Contains(S) && Sections[S] != nullptr; }
ARDSection* ARDDungeonGenerator::GetSection(FIntPoint S) const { const TObjectPtr<ARDSection>* P = Sections.Find(S); return P ? P->Get() : nullptr; }
TArray<FIntPoint> ARDDungeonGenerator::GetSectionCoords() const { TArray<FIntPoint> Out; Sections.GetKeys(Out); return Out; }

FVector ARDDungeonGenerator::GetStartRoomCenter() const
{
	// (Brokenspire: the town square; she comes back to life there)
	if (bTown) { FVector Sq; if (GetTownPlace(TEXT("square"), Sq)) return Sq; }
	// the great hall is the start section's centre block (3, 3): its lanes cross at the origin tile
	if (ARDSection* S = GetSection(FIntPoint::ZeroValue))
	{
		const int32 R = S->RoomAt(FVector(GridOrigin.X + TileSize * 0.5f, GridOrigin.Y + TileSize * 0.5f, 0));
		if (R >= 0) return S->GetRoomCenter(R);
	}
	return FVector(0, 0, 0);
}

ARDSection* ARDDungeonGenerator::SpawnSection(FIntPoint S, bool bEditorBuild, bool bReveal)
{
	UWorld* W = GetWorld();
	FActorSpawnParameters P; P.SpawnCollisionHandlingOverride = ESpawnActorCollisionHandlingMethod::AlwaysSpawn;
	const FIntPoint T0 = SectionMinTile(S);
	ARDSection* Sec = W->SpawnActor<ARDSection>(ARDSection::StaticClass(), FTransform(FVector(GridOrigin.X + T0.X * TileSize, GridOrigin.Y + T0.Y * TileSize, SectionFloorZ(S))), P);
	if (!Sec) return nullptr;
#if WITH_EDITOR
	if (bEditorBuild) { Sec->SetActorLabel(FString::Printf(TEXT("RD_Section_%d_%d"), S.X, S.Y)); Sec->SetFolderPath(TEXT("RandomDungeon/Sections")); }
#endif
	Sections.Add(S, Sec);
	if (bReveal && W->IsGameWorld() && !bEditorBuild)
	{
		// runtime: shell and doors now, the furnishing spread over the next frames (Tick)
		Sec->BeginGenerate(this, S, SectionSeed(S), false);
		Building = Sec;
	}
	else Sec->Generate(this, S, SectionSeed(S), bEditorBuild);
	++SectionsGenerated;
	if (bReveal && bRevealEffect) StartReveal(Sec);
	return Sec;
}

void ARDDungeonGenerator::StartReveal(ARDSection* Sec)
{
	UWorld* W = GetWorld();
	const float Now = W->GetTimeSeconds();
	const float SS = SectionTiles * TileSize;
	const FVector2D Min = Sec->GetSectionMin(), Max = Min + FVector2D(SS);
	const AActor* Who = GetTrackedActor();
	const FVector L = Who ? Who->GetActorLocation() : FVector((Min + Max) * 0.5, 0.0);
	const FVector2D O(FMath::Clamp((float)L.X, (float)Min.X, (float)Max.X), FMath::Clamp((float)L.Y, (float)Min.Y, (float)Max.Y));
	if (RevealMID)
	{
		const int32 Slot = NextRevealSlot++ % RevealSlots;
		RevealMID->SetVectorParameterValue(*FString::Printf(TEXT("Rect%d"), Slot), FLinearColor(Min.X, Min.Y, Max.X, Max.Y));
		RevealMID->SetVectorParameterValue(*FString::Printf(TEXT("Info%d"), Slot), FLinearColor(O.X, O.Y, Now, 1.f));
	}
	if (RevealCurtainMaterial) Sec->ShowCurtain(RevealCurtainMaterial, Now, RevealCurtainHeight, RevealDuration + 0.5f);
	LastRevealTime = Now; LastRevealSection = Sec->Coord;
	// the new section is heard from where it meets the dungeon (a rumble, far-reaching)
	PlaySoundAt(TEXT("Env.Generate"), FVector(O.X, O.Y, 150.f));
	PlaySoundAt(TEXT("Env.GenerateHit"), FVector(O.X, O.Y, 150.f));
	if (FRDSectionMap* M = MapData.Find(Sec->Coord)) M->GeneratedTime = Now;
	UE_LOG(LogRandomDungeonGen, Log, TEXT("RDGEN reveal (%d,%d) t=%.3f from (%.0f,%.0f) tracked (%.0f,%.0f): %d rooms, %d doors, %d containers, %d monsters, %d instances, %d lights, %.0f ms"),
		Sec->Coord.X, Sec->Coord.Y, Now, O.X, O.Y, L.X, L.Y, Sec->GetNumRooms(), Sec->GetNumDoors(), Sec->GetNumContainers(), Sec->SpawnedMonsters.Num(),
		Sec->NumInstances, Sec->NumLights, Sec->GenerateMs);
}

void ARDDungeonGenerator::ClearAll()
{
	UWorld* W = GetWorld();
	for (auto& KV : Sections) if (KV.Value) KV.Value->Destroy();
	Sections.Reset();
	for (TActorIterator<ARDSection> It(W); It; ++It) It->Destroy();
	for (TActorIterator<ARDMonster> It(W); It; ++It) It->Destroy();
	Queue.Reset(); MapData.Reset();
	Building = nullptr;
	SectionsGenerated = 0;
}

void ARDDungeonGenerator::BuildStartSection()
{
	ClearAll();
	SpawnSection(FIntPoint::ZeroValue, !GetWorld()->IsGameWorld());
	MapData.Reset();      // map data is play state (rebuilt by ActivateForPlay)
	Modify();
	UE_LOG(LogRandomDungeonGen, Log, TEXT("RDGEN start section built"));
}

bool ARDDungeonGenerator::GenerateSectionNow(FIntPoint S)
{
	if (IsSectionGenerated(S)) return false;
	// (one being built over frames is finished first: SpawnSection takes Building over, and the other one was left half
	// built for good, never recorded, its set never cleared)
	if (Building) { while (!Building->ContinueGenerate(1e9)) {} Building = nullptr; }
	ARDSection* Sec = SpawnSection(S, false, true);
	if (Sec && Building == Sec) { while (!Sec->ContinueGenerate(1e9)) {} Building = nullptr; }
	return Sec != nullptr;
}

void ARDDungeonGenerator::Enqueue(FIntPoint S)
{
	if ((bOneRoom || bTown) && !IsStartSection(S)) return;          // (martial_arts: the one room, nothing beyond it; Brokenspire: the town alone)
	if (!IsSectionGenerated(S) && !Queue.Contains(S) && IsSectionAllowed(S)) Queue.Add(S);
}

// ------------------------------------------------------------------------------------------------ tiers (level 5)
bool ARDDungeonGenerator::IsTierOpen(int32 Tier) const
{
	if (MaxTier <= 0) return true;
	if (Tier > MaxTier) return false;
	if (Tier <= 1) return true;
	// (mistward: the share rule of 2026-10-26: TierOpenShare of the tier before's rooms explored, monsters killed, chests
	// and trunks looted, each over all of its sets of rooms, the ones she has not reached counted without building them)
	if (TierOpenShare < 1.f)
	{
		// (once open, open for good: a set found bigger when built than its census said must not shut it again)
		if (TiersOpened.Contains(Tier)) return true;
		if (!IsTierOpen(Tier - 1)) return false;
		FIntVector Done, All;
		if (!GetTierTally(Tier - 1, Done, All)) return false;
		auto Enough = [this](int32 D, int32 A) { return D >= FMath::CeilToInt(A * TierOpenShare - 1e-3f); };
		return Enough(Done.X, All.X) && Enough(Done.Y, All.Y) && Enough(Done.Z, All.Z);
	}
	// (every tier before it open and the one just before cleared: tiers open in order; tier 2 too, once the start section
	// is cleared: the user's rule, 2026-10-24)
	return GetTierCleared(Tier - 1) >= TierSize(Tier - 1) && IsTierOpen(Tier - 1);
}

bool ARDDungeonGenerator::IsSectionAllowed(FIntPoint S) const
{
	return MaxTier <= 0 || IsTierOpen(TierOf(S));
}

int32 ARDDungeonGenerator::GetTierCleared(int32 Tier) const
{
	int32 Num = 0;
	for (const auto& KV : Progress) if (KV.Value.bCleared && TierOf(KV.Key) == Tier) ++Num;
	return Num;
}

int32 ARDDungeonGenerator::GetOpenTiers() const
{
	if (MaxTier <= 0) return 0;
	int32 T = 1;
	while (T < MaxTier && IsTierOpen(T + 1)) ++T;
	return T;
}

bool ARDDungeonGenerator::GetSectionProgress(FIntPoint S, FRDSectionProgress& Out) const
{
	const FRDSectionProgress* P = Progress.Find(S);
	if (!P) return false;
	Out = *P;
	return true;
}

int32 ARDDungeonGenerator::GetSealKind(FIntPoint S, FIntPoint Next) const
{
	if (MaxTier <= 0 || IsSectionAllowed(Next)) return 0;
	return TierOf(Next) > MaxTier ? 2 : 1;
}

bool ARDDungeonGenerator::IsMonsterKilled(FIntPoint S, int32 Index) const
{
	const FRDSectionProgress* P = Progress.Find(S);
	return P && P->Killed.Contains(Index);
}

void ARDDungeonGenerator::RecordSection(ARDSection* S)
{
	if (!S || MaxTier <= 0) return;
	FRDSectionProgress& P = Progress.FindOrAdd(S->Coord);
	if (P.Rooms == 0 && P.Chests.Num() == 0 && P.Monsters == 0)
	{
		// (the first time it is generated: what there is to do in it; a section generated again has the same)
		P.Coord = S->Coord; P.Tier = TierOf(S->Coord);
		if (const FRDSectionMap* M = MapData.Find(S->Coord)) for (const FRDMapRect& R : M->Rects) if (!R.bCorridor) ++P.Rooms;
		P.Chests = S->GetChestKeys();
		P.Monsters = S->MonstersPlanned;
		UE_LOG(LogRandomDungeonGen, Log, TEXT("RDTIER section (%d,%d) tier %d: %d rooms, %d chests and trunks, %d monsters"), S->Coord.X, S->Coord.Y, P.Tier, P.Rooms, P.Chests.Num(), P.Monsters);
		// (mistward: what it was counted to hold before it was built must be what it holds)
		if (const FIntVector* C = CensusCache.Find(S->Coord))
			if (C->X != P.Rooms || C->Y != P.Chests.Num() || C->Z != P.Monsters)
				UE_LOG(LogRandomDungeonGen, Warning, TEXT("RDCENSUS (%d,%d) counted %d rooms, %d chests, %d monsters; built %d, %d, %d"), S->Coord.X, S->Coord.Y, C->X, C->Y, C->Z, P.Rooms, P.Chests.Num(), P.Monsters);
	}
	// (mistward: the boss and the guards of a room of it come back with it)
	if (Encounters.Num() > 0) RespawnEncounters(S);
	UpdateProgress(S->Coord);
}

void ARDDungeonGenerator::UpdateProgress(FIntPoint S)
{
	FRDSectionProgress* P = Progress.Find(S);
	if (!P || MaxTier <= 0) return;
	P->RoomsExplored = 0;
	if (const FRDSectionMap* M = MapData.Find(S)) for (const FRDMapRect& R : M->Rects) if (!R.bCorridor && R.bDiscovered) ++P->RoomsExplored;
	P->ChestsLooted = 0;
	for (const int32 K : P->Chests) if (IsContainerLooted(S, K)) ++P->ChestsLooted;
	// (mistward: the share rule opens a tier when enough of the one before is done, whether a set is cleared or not)
	ON_SCOPE_EXIT { if (TierOpenShare < 1.f) CheckTierOpenings(); };
	if (P->bCleared) return;
	if (P->RoomsExplored < P->Rooms || P->ChestsLooted < P->Chests.Num() || P->Killed.Num() < P->Monsters) return;
	P->bCleared = true;
	const int32 T = P->Tier, Done = GetTierCleared(T), All = TierSize(T);
	const float Now = GetWorld() ? GetWorld()->GetTimeSeconds() : 0.f;
	TierNoticeTime = Now;
	if (TierOpenShare < 1.f) TierNotice = Done >= All ? FString::Printf(TEXT("TIER %d CLEARED"), T) : FString::Printf(TEXT("SET CLEARED  -  TIER %d: %d / %d"), T, Done, All);
	else if (Done >= All && T < MaxTier && IsTierOpen(T + 1))
	{
		TierNotice = FString::Printf(TEXT("TIER %d IS OPEN"), T + 1);
		RefreshSeals();
		if (const AActor* Who = GetTrackedActor()) PlaySoundAt(TEXT("Env.Generate"), Who->GetActorLocation());
	}
	else if (Done >= All && T >= MaxTier) TierNotice = FString::Printf(TEXT("TIER %d CLEARED: THE DUNGEON IS YOURS"), T);
	else if (Done >= All) TierNotice = FString::Printf(TEXT("TIER %d CLEARED"), T);       // (a tier before it is not cleared yet)
	else TierNotice = FString::Printf(TEXT("SET CLEARED  -  TIER %d: %d / %d"), T, Done, All);
	UE_LOG(LogRandomDungeonGen, Log, TEXT("RDTIER section (%d,%d) cleared: tier %d %d / %d%s"), S.X, S.Y, T, Done, All, Done >= All ? TEXT(" (tier done)") : TEXT(""));
}

void ARDDungeonGenerator::RefreshSeals()
{
	for (auto& KV : Sections) if (KV.Value && !KV.Value->IsBuilding()) KV.Value->UpdateSeals();
}

bool ARDDungeonGenerator::DebugClearSection(FIntPoint S, int32 LeaveMonsters, FVector Near)
{
	ARDSection* Sec = GetSection(S);
	FRDSectionProgress* P = Progress.Find(S);
	if (!Sec || !P || Sec->IsBuilding()) return false;        // (still being built: nothing recorded yet)
	if (FRDSectionMap* M = MapData.Find(S)) for (FRDMapRect& R : M->Rects) R.bDiscovered = true;
	for (const int32 K : P->Chests) LootedContainers.Add(FIntVector(S.X, S.Y, K));
	// (the ones left alive: the nearest to Near)
	TArray<ARDMonster*> Live;
	for (ARDMonster* Mo : Sec->SpawnedMonsters) if (Mo && !Mo->IsDead()) Live.Add(Mo);
	Live.Sort([Near](const ARDMonster& A, const ARDMonster& B) { return FVector::DistSquared(A.GetActorLocation(), Near) < FVector::DistSquared(B.GetActorLocation(), Near); });
	// (mistward: a boss, a guard, a monster in a cell is none of the set's planned monsters: it stays)
	Live.RemoveAll([](const ARDMonster* M) { return M->SpawnIndex < 0; });
	TSet<int32> Keep;
	for (int32 I = 0; I < Live.Num() && I < LeaveMonsters; ++I) Keep.Add(Live[I]->SpawnIndex);
	for (int32 I = 0; I < P->Monsters; ++I) if (!Keep.Contains(I)) P->Killed.AddUnique(I);
	for (ARDMonster* Mo : Live) if (!Keep.Contains(Mo->SpawnIndex)) Mo->Destroy();
	Sec->SpawnedMonsters.RemoveAll([](const TObjectPtr<ARDMonster>& M) { return !IsValid(M); });
	UpdateProgress(S);
	return P->bCleared;
}

FString ARDDungeonGenerator::DescribeSealNear(FVector From, float MaxDistance) const
{
	if (MaxTier <= 0) return FString();
	const FIntPoint Here = WorldToSection(From);
	for (int32 Dx = -1; Dx <= 1; ++Dx)
		for (int32 Dy = -1; Dy <= 1; ++Dy)
			if (const ARDSection* S = GetSection(Here + FIntPoint(Dx, Dy)))
			{
				TArray<int32> Kinds;
				const TArray<FVector> At = S->GetSealPoints(Kinds);
				for (int32 I = 0; I < At.Num(); ++I)
				{
					if (FVector::Dist2D(At[I], From) > MaxDistance) continue;
					if (Kinds[I] == 2) return TEXT("The dungeon ends here");
					const int32 T = TierOf(S->Coord) + 1;
					if (TierOpenShare < 1.f)
					{
						FIntVector D, A;
						const bool bAll = GetTierTally(T - 1, D, A);
						const int32 Pct = FMath::RoundToInt(TierOpenShare * 100.f);
						if (!bAll) return FString::Printf(TEXT("Sealed: tier %d opens at %d%% of tier %d's rooms, monsters and chests"), T, Pct, T - 1);
						return FString::Printf(TEXT("Sealed: tier %d opens at %d%% of tier %d  -  rooms %d / %d   monsters %d / %d   chests %d / %d"), T, Pct, T - 1,
							D.X, FMath::CeilToInt(A.X * TierOpenShare - 1e-3f), D.Y, FMath::CeilToInt(A.Y * TierOpenShare - 1e-3f), D.Z, FMath::CeilToInt(A.Z * TierOpenShare - 1e-3f));
					}
					return FString::Printf(TEXT("Sealed: clear every set of rooms of tier %d to open tier %d  (%d / %d cleared)"), T - 1, T, GetTierCleared(T - 1), TierSize(T - 1));
				}
			}
	return FString();
}

int32 ARDDungeonGenerator::GetNumMonsters() const { return GetMonsters().Num(); }

float ARDDungeonGenerator::GetAverageWeaponDamage() const
{
	float Sum = 0.f; int32 Num = 0;
	for (const FRDWeaponDef& W : Weapons) if (W.Mesh) { Sum += W.Damage; ++Num; }
	return Num > 0 ? Sum / Num : 20.f;
}

float ARDDungeonGenerator::GetMonsterHealth(FIntPoint Section) const
{
	const float Ref = MonsterReferenceHealth > 0.f ? MonsterReferenceHealth : PlayerMaxHealth;
	// (level 5: by the tier of its rooms)
	if (MaxTier > 0 && TierHealth.Num() > 0) return Ref * TierValueAt(TierHealth, TierOf(Section), 1.f);
	return Ref * (IsStartSection(Section) ? StartMonsterHealth : RuntimeMonsterHealth);
}

float ARDDungeonGenerator::GetMonsterDamage(FIntPoint Section) const
{
	const float Ref = MonsterReferenceBlow > 0.f ? MonsterReferenceBlow : GetAverageWeaponDamage();
	if (MaxTier > 0 && TierDamage.Num() > 0) return Ref * TierValueAt(TierDamage, TierOf(Section), 1.f);
	return Ref * (IsStartSection(Section) ? StartMonsterDamage : RuntimeMonsterDamage);
}

// ------------------------------------------------------------------------------------------------ heroes, items
const FRDHeroDef* ARDDungeonGenerator::FindHero(FName Name) const
{
	for (const FRDHeroDef& H : Heroes) if (H.Name == Name) return &H;
	return nullptr;
}

FName ARDDungeonGenerator::ChosenHero() const
{
	if (Heroes.Num() == 0) return NAME_None;
	if (const AGameModeBase* GM = GetWorld() ? GetWorld()->GetAuthGameMode() : nullptr)
	{
		const FString Opt = UGameplayStatics::ParseOption(GM->OptionsString, TEXT("Hero"));
		if (!Opt.IsEmpty() && FindHero(FName(*Opt))) return FName(*Opt);
	}
	return FindHero(DefaultHero) ? DefaultHero : Heroes[0].Name;
}

bool ARDDungeonGenerator::ApplyHero(FName Name)
{
	const FRDHeroDef* H = FindHero(Name);
	if (!H) return false;
	CurrentHero = H->Name;
	StartWeaponsOf(*H, Weapons);
	WeaponsUnlocked = 0;          // (her own locked weapons from the first: the Martial Artist's count kept gave the Summoner's boss nothing (868 all))
	DashClip = H->DashClip;
	PlayerMaxHealth = H->MaxHealth;
	PlayerMaxMana = H->MaxMana; ManaPerSecond = H->ManaPerSecond;
	MeleeBonus = H->MeleeBonus; RangedBonus = H->RangedBonus;
	PlayerTitle = H->Title;
	bRogueControls = H->bRogueControls;
	RollClip = H->RollClip; RollBackClip = H->RollBackClip;
	ControlsKeys = H->ControlsKeys; ControlsPad = H->ControlsPad;
	UE_LOG(LogRandomDungeonGen, Log, TEXT("RDHERO %s: %d weapons, %.0f hit points, %.0f mana (%.1f a second), melee +%.0f%%, ranged +%.0f%%"),
		*Name.ToString(), Weapons.Num(), PlayerMaxHealth, PlayerMaxMana, ManaPerSecond, MeleeBonus * 100.f, RangedBonus * 100.f);
	return true;
}

bool ARDDungeonGenerator::SwitchHero(FName Name)
{
	const FRDHeroDef* H = FindHero(Name);
	APlayerController* PC = UGameplayStatics::GetPlayerController(this, 0);
	if (!H || !H->PawnClass || !PC) return false;
	APawn* Old = PC->GetPawn();
	const FTransform T = Old ? Old->GetActorTransform() : FTransform(GetStartRoomCenter() + FVector(0, 0, 100.f));
	if (PlayerCombat) PlayerCombat->SetInventoryOpen(false);
	// (the summons another hero brought from the other level are hers, not the new hero's (the PR review's find))
	CarrySummons.Reset(); CarrySummonShares.Reset();
	ApplyHero(Name);
	PlayerCombat = nullptr;         // (Tick gives the new pawn its own)
	if (Old) { PC->UnPossess(); Old->Destroy(); }
	FActorSpawnParameters P;
	P.SpawnCollisionHandlingOverride = ESpawnActorCollisionHandlingMethod::AdjustIfPossibleButAlwaysSpawn;
	APawn* New = GetWorld()->SpawnActor<APawn>(H->PawnClass, T, P);
	if (!New) return false;
	PC->Possess(New);
	return true;
}

int32 ARDDungeonGenerator::FindItem(FName Name) const
{
	for (int32 I = 0; I < Items.Num(); ++I) if (Items[I].Name == Name) return I;
	return -1;
}

FString ARDDungeonGenerator::ArmourRefusal(const FRDItemDef& It, const FString& Label) const
{
	static const TCHAR* WeightName[3] = { TEXT("light"), TEXT("medium"), TEXT("heavy") };
	const FString Who = PlayerTitle.ToLower();
	if (const FRDHeroDef* H = FindHero(CurrentHero))
		if (!H->Wears.Contains(It.ArmourWeight))
		{
			if (H->Wears.Num() == 0) return FString::Printf(TEXT("The %s wears no armour"), *Who);
			TArray<FString> Ws;
			for (int32 K = 0; K < 3; ++K) if (H->Wears.Contains((ERDArmourWeight)K)) Ws.Add(WeightName[K]);
			FString List = Ws.Last();
			if (Ws.Num() > 1) { Ws.Pop(); List = FString::Join(Ws, TEXT(", ")) + TEXT(" and ") + List; }
			return FString::Printf(TEXT("The %s is %s: the %s wears only %s armour"), *Label, WeightName[(int32)It.ArmourWeight], *Who, *List);
		}
	if (!It.Fits.ContainsByPredicate([this](const FRDArmourFit& F) { return F.Hero == CurrentHero && F.Meshes.Num() > 0; }))
		return FString::Printf(TEXT("The %s was not made for the %s"), *Label, *Who);
	return FString();
}

FName ARDDungeonGenerator::LootOf(FIntPoint Section, int32 Index) const
{
	const TArray<FName> L = LootListOf(Section, Index);
	return L.Num() > 0 ? L[0] : NAME_None;
}

TArray<int32> ARDDungeonGenerator::GetStartRoomContainers() const
{
	TArray<int32> Out;
	ARDSection* S = GetSection(FIntPoint::ZeroValue);
	if (!S) return Out;
	const int32 Room = S->RoomAt(GetStartRoomCenter());
	if (Room < 0) return Out;
	for (int32 I = 0; I < S->GetNumContainers(); ++I)
		if (S->RoomAt(S->GetContainerLocation(I)) == Room) Out.Add(I);
	return Out;
}

TArray<FName> ARDDungeonGenerator::LootListOf(FIntPoint Section, int32 Index) const
{
	TArray<FName> Out;
	// (mistward: what the rules put in it come first: the guarded ring)
	if (const TArray<FName>* F = ForcedLoot.Find(FIntVector(Section.X, Section.Y, Index))) Out.Append(*F);
	if (!bStartLoot || Items.Num() == 0 || (!IsStartSection(Section) && !bLootAllSections)) return Out;
	const int32 Max = FMath::Max(MaxItemsPerContainer, 1);
	// (level 5: an item may be found only in some tiers of rooms; level 4's items have no tiers: everywhere)
	// (the rebalance to tier 25: an item's tiers are the game's: this level's tier through GlobalTier)
	const int32 Tier = TierOf(Section);
	auto InTier = [this, Tier](const FRDItemDef& It) { return ItemOfTier(It, Tier); };
	// what is put in the start room's containers: one to each in turn
	if (StartRoomItems.Num() > 0 && IsStartSection(Section))
	{
		const TArray<int32> Room = GetStartRoomContainers();
		const int32 K = Room.Find(Index);
		if (K != INDEX_NONE)
			for (int32 J = K; J < StartRoomItems.Num() && Out.Num() < Max; J += Room.Num())
				if (FindItem(StartRoomItems[J]) >= 0) Out.Add(StartRoomItems[J]);
	}
	// (level 5: a container holds anything at all only so often; the start room's own items are there whatever it says)
	if (!ContainerHoldsLoot(Section, Index)) return Out;
	float Sum = 0.f;
	for (const FRDItemDef& It : Items) if (InTier(It)) Sum += FMath::Max(It.Weight, 0.f);
	if (Sum <= 0.f) return Out;
	// (a stream of its own for each container: what it holds does not depend on the order she opens them in, and the
	// play's streams are not drawn from; the first pick is the one level 4 had)
	FRandomStream R((int32)HashCombine(HashCombine((uint32)SessionSeed, GetTypeHash(Section)), GetTypeHash(Index * 7907 + 11)));
	auto Pick = [&]() -> FName
	{
		float U = R.FRand() * Sum;
		FName Last = NAME_None;
		for (const FRDItemDef& It : Items)
		{
			if (!InTier(It) || It.Weight <= 0.f) continue;
			Last = It.Name; U -= It.Weight;
			if (U < 0.f) return It.Name;
		}
		return Last;
	};
	const FName First = Pick();
	const int32 N = Max > 1 ? R.RandRange(1, Max) : 1;
	TArray<FName> Picked = { First };
	while (Picked.Num() < N) Picked.Add(Pick());
	for (int32 K = 0; K < Picked.Num(); ++K)
	{
		if (Out.Num() >= Max) break;
		// (level 5: a spell tome is one of the spells of the section's tier, by the table's drop chances)
		const int32 Ix = FindItem(Picked[K]);
		if (Ix >= 0 && Items[Ix].Kind == ERDItemKind::Tome && Items[Ix].Spell.IsNone())
		{
			const FName Sp = TomeSpellOf(Section, Index, K);
			if (!Sp.IsNone() && FindItem(TomeItemName(Sp)) >= 0) Out.Add(TomeItemName(Sp));
			continue;
		}
		Out.Add(Picked[K]);
	}
	return Out;
}

bool ARDDungeonGenerator::ContainerHoldsLoot(FIntPoint Section, int32 Index) const
{
	if (ContainerLootChance >= 1.f) return true;
	const uint32 H = HashCombine(HashCombine((uint32)SessionSeed ^ 0x51A7u, GetTypeHash(Section)), GetTypeHash(Index * 37 + 3));
	return (float)(H % 100000u) / 100000.f < ContainerLootChance;
}

// ------------------------------------------------------------------------------------------------ spells, rings (level 5)
int32 ARDDungeonGenerator::FindSpell(FName Name) const
{
	for (int32 I = 0; I < Spells.Num(); ++I) if (Spells[I].Name == Name) return I;
	return -1;
}

FName ARDDungeonGenerator::TomeSpellOf(FIntPoint Section, int32 Index, int32 Pick) const
{
	const int32 Tier = TierOf(Section);
	// (the rebalance to tier 25: "mage spells need to be limited to 1 gained per tier": a tome found in a tier of a dungeon is
	// the spell of that tier's place (Slot: the dungeons' tiers in the chain's order); with no spell placed, as before)
	if (Spells.ContainsByPredicate([](const FRDSpellDef& S) { return S.Slot > 0; }))
	{
		const int32 Want = FMath::Max(ChainIndexHere(), 0) * 5 + Tier;
		const FRDSpellDef* Sp = Spells.FindByPredicate([Want](const FRDSpellDef& S) { return S.Slot == Want; });
		return Sp ? Sp->Name : NAME_None;
	}
	float Sum = 0.f;
	for (const FRDSpellDef& S : Spells) if (S.Tier == Tier) Sum += FMath::Max(S.DropChance, 0.f);
	if (Sum <= 0.f) return NAME_None;
	const uint32 H = HashCombine(HashCombine((uint32)SessionSeed ^ 0x70E3u, GetTypeHash(Section)), GetTypeHash(Index * 211 + Pick * 13 + 1));
	float U = (float)(H % 1000003u) / 1000003.f * Sum;
	FName Last = NAME_None;
	for (const FRDSpellDef& S : Spells)
	{
		if (S.Tier != Tier || S.DropChance <= 0.f) continue;
		Last = S.Name; U -= S.DropChance;
		if (U < 0.f) return S.Name;
	}
	return Last;
}

bool ARDDungeonGenerator::HeroLearns(ERDSpellType Type) const
{
	const FRDHeroDef* H = FindHero(CurrentHero);
	return H && H->Learns.Contains(Type);
}

bool ARDDungeonGenerator::HeroWearsRing(ERDRingKind Kind) const
{
	const FRDHeroDef* H = FindHero(CurrentHero);
	return H && H->RingKinds.Contains(Kind);
}

bool ARDDungeonGenerator::MakeSpellWeapon(int32 SpellIndex, FRDWeaponDef& Out) const
{
	const FRDHeroDef* H = FindHero(CurrentHero);
	if (!H || !Spells.IsValidIndex(SpellIndex)) return false;
	// (her cast clips: those of her first spell that is not a crossbow's)
	const FRDWeaponDef* Base = H->Weapons.FindByPredicate([](const FRDWeaponDef& W) { return W.bSpell && !W.BoltMesh; });
	if (!Base) return false;
	const FRDSpellDef& S = Spells[SpellIndex];
	Out = *Base;
	Out.Name = S.Name; Out.SpellIndex = SpellIndex; Out.bAlongside = false;
	Out.Damage = S.Damage; Out.ManaCost = S.Mana; Out.Cooldown = S.Cooldown; Out.Reach = S.Reach;
	Out.BoltSpeed = S.BoltSpeed; Out.BoltTurnRate = 260.f; Out.BoltSplash = S.Splash;
	Out.ChargeEffect = S.CastFx; Out.ChargeEffectScale = S.CastFxScale;
	Out.BoltEffect = S.BoltFx; Out.BoltEffectScale = S.BoltFxScale; Out.BoltCoreEffect = nullptr;
	Out.BurstEffect = S.ImpactFx; Out.BurstEffectScale = S.ImpactFxScale; Out.BurstFlameEffect = nullptr; Out.LimbFx.Reset(); Out.BoltRange = 0.f; Out.BurstLife = 0.f;          // (a chi attack's own: the PR review's find)
	Out.SpellLightColor = S.LightColor; Out.SpellLightIntensity = S.LightIntensity;
	Out.SoundKey = S.SoundKey; Out.Icon = S.Icon;
	Out.Durability = 0.f; Out.Item = NAME_None; Out.SpeedRating = Out.DamageRating = 0; Out.WeaponType.Reset();
	return true;
}

bool ARDDungeonGenerator::BreakdownOf(const FString& Type, int32 Tier, TArray<FName>& OutItems, TArray<int32>& Counts) const
{
	OutItems.Reset(); Counts.Reset();
	for (const FRDBreakdown& B : Breakdowns)
	{
		if (!B.Types.ContainsByPredicate([&Type](const FString& T) { return T.Equals(Type, ESearchCase::IgnoreCase); })) continue;
		for (int32 K = 0; K < B.Gives.Num(); ++K)
		{
			OutItems.Add(B.Gives[K]);
			Counts.Add(FMath::Max(1, (B.PerTier.IsValidIndex(K) ? B.PerTier[K] : 1) * FMath::Max(Tier, 1)));
		}
		return OutItems.Num() > 0;
	}
	return false;
}

void ARDDungeonGenerator::MonsterKindsFor(FIntPoint Section, TArray<int32>& Out) const
{
	Out.Reset();
	const int32 Tier = TierOf(Section);
	const bool bTiers = MaxTier > 0 && Monsters.ContainsByPredicate([](const FRDMonsterDef& D) { return D.Tier > 0; });
	for (int32 I = 0; I < Monsters.Num(); ++I)
		if (Monsters[I].Mesh && Monsters[I].Weight > 0.f && (!bTiers || Monsters[I].Tier == Tier)) Out.Add(I);
	// (a tier without kinds of its own: the nearest tier's below it, then above)
	for (int32 D = 1; bTiers && Out.Num() == 0 && D < 6; ++D)
		for (int32 I = 0; I < Monsters.Num(); ++I)
			if (Monsters[I].Mesh && Monsters[I].Weight > 0.f && (Monsters[I].Tier == Tier - D || Monsters[I].Tier == Tier + D)) Out.Add(I);
}

// ------------------------------------------------------------------------------------------------ allies, corpses (level 5)
TArray<ARDMonster*> ARDDungeonGenerator::GetAllies() const
{
	TArray<ARDMonster*> Out;
	for (ARDMonster* A : Allies) if (IsValid(A) && !A->IsDead()) Out.Add(A);
	return Out;
}

TArray<ARDMonster*> ARDDungeonGenerator::GetCorpsesNear(FVector At, float Radius) const
{
	TArray<ARDMonster*> Out;
	for (const auto& KV : Sections)
		if (KV.Value) for (ARDMonster* M : KV.Value->SpawnedMonsters)
			if (IsValid(M) && M->IsDead() && M->IsCorpse() && FVector::Dist2D(M->GetActorLocation(), At) <= Radius) Out.Add(M);
	Out.Sort([At](const ARDMonster& A, const ARDMonster& B) { return FVector::DistSquared(A.GetActorLocation(), At) < FVector::DistSquared(B.GetActorLocation(), At); });
	return Out;
}

void ARDDungeonGenerator::ConsumeCorpse(ARDMonster* Corpse)
{
	if (!Corpse) return;
	if (Corpse->Section && Corpse->SpawnIndex >= 0)
		if (FRDSectionProgress* P = Progress.Find(Corpse->Section->Coord)) { P->Consumed.AddUnique(Corpse->SpawnIndex); P->Corpses.Remove(Corpse->SpawnIndex); }
	if (Corpse->Section) Corpse->Section->SpawnedMonsters.Remove(Corpse);
	Allies.Remove(Corpse);
	Corpse->Destroy();
}

bool ARDDungeonGenerator::RaiseAlly(ARDMonster* Corpse, float Seconds, float HealthShare)
{
	if (!IsValid(Corpse) || !Corpse->IsDead() || !Corpse->IsCorpse()) return false;
	// (it leaves its section's monsters: her blows and spells pass it by; its death stays counted)
	if (Corpse->Section && Corpse->SpawnIndex >= 0)
		if (FRDSectionProgress* P = Progress.Find(Corpse->Section->Coord)) { P->Consumed.AddUnique(Corpse->SpawnIndex); P->Corpses.Remove(Corpse->SpawnIndex); }
	if (Corpse->Section) Corpse->Section->SpawnedMonsters.Remove(Corpse);
	Corpse->BecomeAlly(Seconds, Corpse->GetMaxHealth() * HealthShare, Corpse->GetDamage());
	Allies.AddUnique(Corpse);
	return true;
}

ARDMonster* ARDDungeonGenerator::SummonAlly(FName Kind, FVector At, float Strength)
{
	// (one at a time: the champion she has is healed and comes to her)
	for (ARDMonster* A : Allies)
		if (IsValid(A) && !A->IsDead() && A->IsChampion())
		{
			A->BecomeAlly(0.f, A->GetMaxHealth(), A->GetDamage());
			A->SetActorLocation(At + FVector(0, 0, A->GetCapsuleComponent()->GetScaledCapsuleHalfHeight() + 5.f), false, nullptr, ETeleportType::TeleportPhysics);
			return A;
		}
	const FRDMonsterDef* Def = Monsters.FindByPredicate([Kind](const FRDMonsterDef& D) { return D.Name == Kind && D.Mesh; });
	ARDSection* Sec = GetSection(WorldToSection(At));
	if (!Def || !Sec) return nullptr;
	FActorSpawnParameters Sp; Sp.SpawnCollisionHandlingOverride = ESpawnActorCollisionHandlingMethod::AdjustIfPossibleButAlwaysSpawn;
	ARDMonster* M = GetWorld()->SpawnActor<ARDMonster>(ARDMonster::StaticClass(), FTransform(FRotator::ZeroRotator, At + FVector(0, 0, Def->CapsuleHalfHeight + 5.f)), Sp);
	if (!M) return nullptr;
	M->Setup(Sec, *Def, (int32)HashCombine((uint32)SessionSeed, 0x4B11u));
	// (as strong as Strength of a monster of the last tier)
	const int32 T = FMath::Max(MaxTier, 1);
	const float Ref = MonsterReferenceHealth > 0.f ? MonsterReferenceHealth : PlayerMaxHealth;
	const float Blow = MonsterReferenceBlow > 0.f ? MonsterReferenceBlow : GetAverageWeaponDamage();
	M->BecomeAlly(0.f, FMath::RoundToFloat(Ref * TierValueAt(TierHealth, T, 1.f) * Strength), FMath::RoundToFloat(Blow * TierValueAt(TierDamage, T, 1.f) * Strength));
	M->SetChampion(true);
	Allies.Add(M);
	return M;
}

void ARDDungeonGenerator::TickAllies(float Dt)
{
	Allies.RemoveAll([](const TObjectPtr<ARDMonster>& A) { return !IsValid(A); });
	// (an ally walks the tile grid of the section it is in: it moves to another section's as it crosses into it)
	for (ARDMonster* A : Allies)
	{
		if (A->IsDead()) continue;
		ARDSection* S = GetSection(WorldToSection(A->GetActorLocation()));
		if (S && S != A->Section) A->Section = S;
		if (!IsValid(A->Section)) A->Section = GetSection(FIntPoint::ZeroValue);
	}
}

// ------------------------------------------------------------------------------------------------ volumes, the menu (level 5)
int32 ARDDungeonGenerator::SoundCategory(FName Key)
{
	const FString K = Key.ToString();
	if (K.StartsWith(TEXT("Music."))) return 3;
	if (K.StartsWith(TEXT("Env.")) || K.StartsWith(TEXT("Atmos.")) || K.StartsWith(TEXT("Weather."))) return 2;
	return 1;
}

void ARDDungeonGenerator::LoadUserVolumes()
{
	static const TCHAR* Names[4] = { TEXT("Overall"), TEXT("Action"), TEXT("Environment"), TEXT("Music") };
	for (int32 I = 0; I < 4; ++I)
	{
		float V = 1.f;
		if (GConfig && GConfig->GetFloat(TEXT("RandomDungeon.Volume"), Names[I], V, GGameUserSettingsIni)) UserVolumes[I] = FMath::Clamp(V, 0.f, 1.f);
	}
}

void ARDDungeonGenerator::SetUserVolume(int32 Category, float Value)
{
	static const TCHAR* Names[4] = { TEXT("Overall"), TEXT("Action"), TEXT("Environment"), TEXT("Music") };
	const int32 C = FMath::Clamp(Category, 0, 3);
	UserVolumes[C] = FMath::Clamp(FMath::RoundToFloat(Value * 100.f) / 100.f, 0.f, 1.f);
	if (GConfig) { GConfig->SetFloat(TEXT("RandomDungeon.Volume"), Names[C], UserVolumes[C], GGameUserSettingsIni); GConfig->Flush(false, GGameUserSettingsIni); }
	ApplyUserVolumes();
}

void ARDDungeonGenerator::ApplyUserVolumes()
{
	// (what is playing now: the music and atmosphere layers, the fires' loops; a one-shot gets it when it starts)
	for (int32 L = 0; L < MusicComps.Num(); ++L)
		if (UAudioComponent* A = MusicComps[L]) A->SetVolumeMultiplier(UserVolumeOf(RDMusicKeys[L]));
	for (int32 I = 0; I < FireComps.Num() && I < FireVoices.Num(); ++I)
	{
		const FRDSoundSet* Set = Sounds.Find(RDFireKeys[FMath::Min<int32>(FireVoices[I].Kind, 2)]);
		if (FireComps[I] && Set) FireComps[I]->SetVolumeMultiplier(Set->Volume * SoundVolume * UserVolumeOf(RDFireKeys[0]));
	}
}

void ARDDungeonGenerator::BackToMainMenu()
{
	// (the cursor back on the line that opened the page: with Save and Load on the main page, "1" was Save, and Back then
	// Enter overwrote her saved game)
	const FName From = MenuPage == 2 ? FName(TEXT("load")) : MenuPage == 3 ? FName(TEXT("save")) : FName(TEXT("options"));
	MenuPage = 0;
	MenuCursor = FMath::Max(0, MenuItems().IndexOfByKey(From));
}

TArray<FName> ARDDungeonGenerator::MenuItems() const
{
	// (level 5: the four volumes and its three buttons on one page; mistward4: a main page and an Options page)
	static const FName Vol[4] = { TEXT("vol0"), TEXT("vol1"), TEXT("vol2"), TEXT("vol3") };
	if (!bOptionsMenu) return { Vol[0], Vol[1], Vol[2], Vol[3], TEXT("resume"), TEXT("hero"), TEXT("quit") };
	// (Brokenspire: the castle's way back to the town)
	if (MenuPage == 0 && bTownLink && !bTown && !TownLevel.IsEmpty()) return { TEXT("resume"), TEXT("save"), TEXT("load"), TEXT("options"), TEXT("town"), TEXT("hero"), TEXT("quit") };
	// (Brokenspire and the wilderness: the game saved and loaded (the user's choice of 2026-11-03))
	if (MenuPage == 0 && bTown) return { TEXT("resume"), TEXT("save"), TEXT("load"), TEXT("options"), TEXT("hero"), TEXT("quit") };
	if (MenuPage == 0) return { TEXT("resume"), TEXT("options"), TEXT("hero"), TEXT("quit") };
	// (the list of 2026-11-04: the saves on disk by their names, newest first (the autosave among them); the Save page's name)
	if (MenuPage == 2)
	{
		TArray<FName> L;
		for (const FString& S : GetSaveSlots())
		{
			FString Slot, Rest; S.Split(TEXT("|"), &Slot, &Rest);
			L.Add(Slot == TEXT("autosave") ? FName(TEXT("loadauto")) : FName(*(TEXT("load:") + Slot)));
			if (L.Num() >= 8) break;
		}
		if (!L.Contains(FName(TEXT("loadauto")))) L.Insert(FName(TEXT("loadauto")), 0);
		L.Add(TEXT("back"));
		return L;
	}
	if (MenuPage == 3) return { TEXT("savename"), TEXT("savedo"), TEXT("back") };
	return { Vol[0], Vol[1], Vol[2], Vol[3], TEXT("controls"), TEXT("res"), TEXT("mode"), TEXT("apply"), TEXT("back") };
}

static int32 RDMenuVolumeOf(const FName& Id)
{
	const FString S = Id.ToString();
	return S.StartsWith(TEXT("vol")) ? FCString::Atoi(*S.RightChop(3)) : -1;
}

TArray<FString> ARDDungeonGenerator::GetMenuLines() const
{
	static const TCHAR* VolLabel[4] = { TEXT("Overall volume"), TEXT("Action sounds"), TEXT("Environment sounds"), TEXT("Music") };
	static const TCHAR* ModeName[3] = { TEXT("Fullscreen"), TEXT("Windowed fullscreen"), TEXT("Windowed") };
	TArray<FString> Out;
	for (const FName& Id : MenuItems())
	{
		const int32 V = RDMenuVolumeOf(Id);
		if (V >= 0) Out.Add(FString::Printf(TEXT("volume|%s|%.2f"), VolLabel[V], UserVolumes[V]));
		else if (Id == TEXT("resume")) Out.Add(TEXT("button|Resume"));
		else if (Id == TEXT("options")) Out.Add(TEXT("button|Options"));
		else if (Id == TEXT("save")) Out.Add(TEXT("button|Save the game"));
		else if (Id == TEXT("load")) Out.Add(TEXT("button|Load a game"));
		else if (Id == TEXT("loadauto") || Id == TEXT("loadsave") || Id.ToString().StartsWith(TEXT("load:")))
		{
			const FString Slot = Id == TEXT("loadauto") ? FString(TEXT("autosave")) : Id == TEXT("loadsave") ? FString(TEXT("save")) : Id.ToString().RightChop(5);
			const FString Info = GetSaveInfo(Slot);
			TArray<FString> P; Info.ParseIntoArray(P, TEXT("|"), false);
			const FString What = Id == TEXT("loadauto") ? FString(TEXT("Autosave")) : (P.Num() >= 6 && !P[5].IsEmpty() ? P[5] : FString(TEXT("Saved game")));
			Out.Add(P.Num() >= 4 ? FString::Printf(TEXT("button|%s: %s, %s (%s)"), *What, *P[2], *P[0], *P[3]) : FString::Printf(TEXT("button|%s: none"), *What));
		}
		else if (Id == TEXT("savename")) Out.Add(FString::Printf(TEXT("text|Name|%s"), *SaveNameText.Replace(TEXT("|"), TEXT(" "))));
		else if (Id == TEXT("savedo"))
		{
			const bool bOver = URDSaveGame::Info(SlotForName(SaveNameText)).Len() > 0;
			Out.Add(bOver ? FString(TEXT("button|Save (over the save of that name)")) : FString(TEXT("button|Save")));
		}
		else if (Id == TEXT("hero")) Out.Add(bTown || bTownLink ? FString(TEXT("button|Choose another hero (a new game)")) : FString(TEXT("button|Choose another hero")));
		else if (Id == TEXT("town")) Out.Add(FString::Printf(TEXT("button|Return to %s"), *WayBackName()));
		else if (Id == TEXT("quit")) Out.Add(TEXT("button|Quit"));
		else if (Id == TEXT("controls")) Out.Add(FString::Printf(TEXT("choice|Controls hint|%s"), bControlsShown ? TEXT("On") : TEXT("Off")));
		else if (Id == TEXT("res"))
			// (windowed fullscreen covers the screen whatever the size chosen: the engine sizes that window to the screen)
			Out.Add(PendingWindowMode == 1 ? FString(TEXT("choice|Resolution|the screen's own (windowed fullscreen)"))
			                               : FString::Printf(TEXT("choice|Resolution|%d x %d"), PendingResolution.X, PendingResolution.Y));
		else if (Id == TEXT("mode")) Out.Add(FString::Printf(TEXT("choice|Display mode|%s"), ModeName[FMath::Clamp(PendingWindowMode, 0, 2)]));
		else if (Id == TEXT("apply")) Out.Add(TEXT("button|Apply display settings"));
		else if (Id == TEXT("back")) Out.Add(TEXT("button|Back"));
	}
	return Out;
}

/** the gamepad's Start as the device sends it (see StartKeys) */
class FRDStartKeys : public IInputProcessor
{
public:
	TWeakObjectPtr<ARDDungeonGenerator> Owner;
	virtual void Tick(const float, FSlateApplication&, TSharedRef<ICursor>) override {}
	virtual bool HandleKeyDownEvent(FSlateApplication&, const FKeyEvent& E) override
	{
		if (E.GetKey() == EKeys::Gamepad_Special_Right && !E.IsRepeat())
			if (ARDDungeonGenerator* G = Owner.Get()) { G->bRawStartDown = true; G->bRawStartSeen = true; G->RawStartDownAt = FPlatformTime::Seconds(); }
		return false;
	}
	virtual bool HandleKeyUpEvent(FSlateApplication&, const FKeyEvent& E) override
	{
		if (E.GetKey() == EKeys::Gamepad_Special_Right) if (ARDDungeonGenerator* G = Owner.Get()) G->bRawStartDown = false;
		return false;
	}
	virtual const TCHAR* GetDebugName() const override { return TEXT("RDStartKeys"); }
};

void ARDDungeonGenerator::ResetStartHold()
{
	StartHeldSince = -1.0;
	RawStartHandledAt = RawStartDownAt;
	if (PlayerCombat) PlayerCombat->bStartTapped = false;
}

void ARDDungeonGenerator::EndPlay(const EEndPlayReason::Type Reason)
{
	if (StartKeys.IsValid() && FSlateApplication::IsInitialized()) FSlateApplication::Get().UnregisterInputPreProcessor(StartKeys);
	StartKeys.Reset();
	// (the clouds' render-target mode as it was before this level's sky set it: RDSky.cpp)
	if (VrtModeWas >= 0)
		if (IConsoleVariable* V = IConsoleManager::Get().FindConsoleVariable(TEXT("r.VolumetricRenderTarget.Mode"))) { V->Set(VrtModeWas, ECVF_SetByCode); VrtModeWas = -1; }
	Super::EndPlay(Reason);
}

void ARDDungeonGenerator::SetMenuOpen(bool bOpen)
{
	if (bOpen == bMenuOpen || !bEscapeMenu) return;
	ResetStartHold();
	bMenuOpen = bOpen; bMenuDragging = false;
	APlayerController* PC = UGameplayStatics::GetPlayerController(this, 0);
	if (bOpen)
	{
		// (the inventory or the anvil open under it are shut first: one panel at a time)
		if (PlayerCombat) { PlayerCombat->SetInventoryOpen(false); PlayerCombat->SetCraftingOpen(false); }
		MenuCursor = 0; MenuPage = 0;
		if (bMenuPausesGame) UGameplayStatics::SetGamePaused(this, true);
		if (PC) { PC->SetShowMouseCursor(true); FInputModeGameAndUI M; M.SetHideCursorDuringCapture(false); PC->SetInputMode(M); }
	}
	else
	{
		UGameplayStatics::SetGamePaused(this, false);
		if (PC) { PC->SetShowMouseCursor(false); PC->SetInputMode(FInputModeGameOnly()); }
	}
	if (PlayerCombat && PlayerCombat->GetOwner()) PlaySoundAt(TEXT("Player.Inventory"), PlayerCombat->GetOwner()->GetActorLocation());
}

void ARDDungeonGenerator::MoveMenuCursor(int32 Step)
{
	const int32 N = FMath::Max(MenuItems().Num(), 1);
	MenuCursor = ((MenuCursor + Step) % N + N) % N;
}

void ARDDungeonGenerator::StepMenuValue(int32 Step)
{
	const TArray<FName> It = MenuItems();
	if (!It.IsValidIndex(MenuCursor)) return;
	const FName Id = It[MenuCursor];
	const int32 V = RDMenuVolumeOf(Id);
	if (V >= 0) { SetUserVolume(V, UserVolumes[V] + 0.05f * Step); return; }
	// (mistward4's choices: the controls hint on / off, a resolution, a display mode; the last two wait for Apply)
	if (Id == TEXT("controls")) SetControlsHintShown(!bControlsShown);
	else if (Id == TEXT("res") && PendingWindowMode != 1)
	{
		const TArray<FString> Ch = GetResolutionChoices();
		if (Ch.Num() == 0) return;
		int32 K = Ch.IndexOfByKey(FString::Printf(TEXT("%dx%d"), PendingResolution.X, PendingResolution.Y));
		K = K < 0 ? 0 : ((K + Step) % Ch.Num() + Ch.Num()) % Ch.Num();
		FString Xs, Ys; Ch[K].Split(TEXT("x"), &Xs, &Ys);
		PendingResolution = FIntPoint(FCString::Atoi(*Xs), FCString::Atoi(*Ys));
	}
	else if (Id == TEXT("mode")) PendingWindowMode = ((PendingWindowMode + Step) % 3 + 3) % 3;
}

bool ARDDungeonGenerator::ActivateMenuLine(int32 Line)
{
	const TArray<FName> It = MenuItems();
	const int32 L = Line >= 0 ? Line : MenuCursor;
	if (!It.IsValidIndex(L)) return false;
	const FName Id = It[L];
	if (RDMenuVolumeOf(Id) >= 0) return false;
	if (Id == TEXT("resume")) { LastMenuAction = TEXT("resume"); SetMenuOpen(false); return true; }
	if (Id == TEXT("options")) { LastMenuAction = TEXT("options"); OpenOptionsPage(); return true; }
	if (Id == TEXT("back")) { LastMenuAction = TEXT("back"); BackToMainMenu(); return true; }
	if (Id == TEXT("save"))
	{
		// (the list of 2026-11-04: a page to name it on, the place and the day offered as its name)
		LastMenuAction = TEXT("save");
		MenuPage = 3; MenuCursor = 0;
		if (SaveNameText.IsEmpty())
		{
			const APawn* Her = UGameplayStatics::GetPlayerPawn(this, 0);
			const bool bWilds = bWild && Her && IsWildReady() && !IsInTownWalls(Her->GetActorLocation());
			SaveNameText = FString::Printf(TEXT("%s day %d"), bWilds ? TEXT("The wilds") : (bTown ? *TownName : !DungeonTitle.IsEmpty() ? *DungeonTitle : TEXT("Mistward Castle")), TownDay);
		}
		return true;
	}
	if (Id == TEXT("savename")) { LastMenuAction = TEXT("savename"); MenuCursor = 1; return true; }
	if (Id == TEXT("savedo"))
	{
		LastMenuAction = TEXT("savedo");
		const FString Nm = SaveNameText.TrimStartAndEnd();
		if (Nm.IsEmpty()) { if (PlayerCombat) PlayerCombat->ShowMessage(TEXT("Give the save a name first")); return false; }
		const FString Slot = SlotForName(Nm);
		const bool bOk = bMenuDryRun || SaveGameNow(Slot, TEXT("menu"), Nm);
		if (PlayerCombat) PlayerCombat->ShowMessage(bOk ? FString::Printf(TEXT("The game is saved as \"%s\""), *Nm) : FString(TEXT("The game could not be saved")));
		if (bOk) BackToMainMenu();
		return bOk;
	}
	if (Id == TEXT("load")) { LastMenuAction = TEXT("load"); MenuPage = 2; MenuCursor = 0; SaveSlotsAt = -10.0; return true; }
	if (Id == TEXT("loadauto") || Id == TEXT("loadsave")) { LastMenuAction = Id.ToString(); return LoadGameFrom(Id == TEXT("loadauto") ? TEXT("autosave") : TEXT("save")); }
	if (Id.ToString().StartsWith(TEXT("load:"))) { LastMenuAction = Id.ToString(); return LoadGameFrom(Id.ToString().RightChop(5)); }
	if (Id == TEXT("apply")) { LastMenuAction = TEXT("apply"); return ApplyDisplaySettings(); }
	if (Id == TEXT("controls") || Id == TEXT("res") || Id == TEXT("mode")) { LastMenuAction = Id.ToString(); MenuCursor = L; StepMenuValue(1); return true; }
	if (Id == TEXT("town"))
	{
		LastMenuAction = TEXT("town");
		if (bMenuDryRun) return true;
		if (PlayerCombat && PlayerCombat->IsDead()) return false;
		SetMenuOpen(false);
		return ReturnToTown();
	}
	if (Id == TEXT("hero"))
	{
		LastMenuAction = TEXT("hero");
		if (bMenuDryRun || MenuLevel.IsEmpty()) return !MenuLevel.IsEmpty();
		SetMenuOpen(false);
		UGameplayStatics::OpenLevel(this, FName(*MenuLevel));
		return true;
	}
	// (only Quit quits: an item without a branch here did, when anything not named fell through to it (the PR review's find))
	if (Id != TEXT("quit")) return false;
	LastMenuAction = TEXT("quit");
	if (bMenuDryRun) return true;
	SetMenuOpen(false);
	WildAutosave(TEXT("quit"));
	// (in the editor this ends play and leaves the editor as it was; a game quits)
	UKismetSystemLibrary::QuitGame(this, UGameplayStatics::GetPlayerController(this, 0), EQuitPreference::Quit, false);
	return true;
}

void ARDDungeonGenerator::TickSaveNameKeys(APlayerController* PC)
{
	// (the keys as typed: letters (shift for capitals, the first a capital), digits, space, - and ', Backspace; 40 at most)
	if (!PC) return;
	static const FKey Letters[26] = { EKeys::A, EKeys::B, EKeys::C, EKeys::D, EKeys::E, EKeys::F, EKeys::G, EKeys::H, EKeys::I, EKeys::J, EKeys::K, EKeys::L, EKeys::M,
		EKeys::N, EKeys::O, EKeys::P, EKeys::Q, EKeys::R, EKeys::S, EKeys::T, EKeys::U, EKeys::V, EKeys::W, EKeys::X, EKeys::Y, EKeys::Z };
	static const FKey Digits[10] = { EKeys::Zero, EKeys::One, EKeys::Two, EKeys::Three, EKeys::Four, EKeys::Five, EKeys::Six, EKeys::Seven, EKeys::Eight, EKeys::Nine };
	const bool bShift = PC->IsInputKeyDown(EKeys::LeftShift) || PC->IsInputKeyDown(EKeys::RightShift);
	for (int32 K = 0; K < 26; ++K)
		if (PC->WasInputKeyJustPressed(Letters[K]) && SaveNameText.Len() < 40)
		{
			const bool bCap = bShift || SaveNameText.IsEmpty() || SaveNameText.EndsWith(TEXT(" "));
			SaveNameText.AppendChar((TCHAR)((bCap ? 'A' : 'a') + K));
		}
	for (int32 K = 0; K < 10; ++K) if (PC->WasInputKeyJustPressed(Digits[K]) && SaveNameText.Len() < 40) SaveNameText.AppendChar((TCHAR)('0' + K));
	if (PC->WasInputKeyJustPressed(EKeys::SpaceBar) && SaveNameText.Len() < 40 && !SaveNameText.EndsWith(TEXT(" "))) SaveNameText.AppendChar(TEXT(' '));
	if (PC->WasInputKeyJustPressed(EKeys::Hyphen) && SaveNameText.Len() < 40) SaveNameText.AppendChar(TEXT('-'));
	if (PC->WasInputKeyJustPressed(EKeys::Apostrophe) && SaveNameText.Len() < 40) SaveNameText.AppendChar(TEXT('\''));
	// (the list of 2026-11-08b: "holding down the backspace key should backspace multiple times": held, it goes on after a
	// moment (0.4 s), a letter every 50 ms, until it is let go or the name is empty; real time, the menu pauses the game)
	{
		const double Now = FPlatformTime::Seconds();
		if (PC->WasInputKeyJustPressed(EKeys::BackSpace)) { if (SaveNameText.Len() > 0) SaveNameText.LeftChopInline(1); SaveBackAt = Now + 0.4; }
		else if (PC->IsInputKeyDown(EKeys::BackSpace) && SaveBackAt > 0.0 && Now >= SaveBackAt) { if (SaveNameText.Len() > 0) SaveNameText.LeftChopInline(1); SaveBackAt = Now + 0.05; }
		else if (!PC->IsInputKeyDown(EKeys::BackSpace)) SaveBackAt = 0.0;
	}
	if (PC->WasInputKeyJustPressed(EKeys::Delete)) SaveNameText.Reset();
}

void ARDDungeonGenerator::TickMenu(APlayerController* PC)
{
	if (!bEscapeMenu || !PC) return;
	if (PlayerCombat && PlayerCombat->IsScriptedOnly()) return;
	// (mistward4: Escape on the Options page goes back to the main page; on the main page it closes the menu)
	if (PC->WasInputKeyJustPressed(EKeys::Escape)) { if (bMenuOpen && MenuPage > 0) BackToMainMenu(); else SetMenuOpen(!bMenuOpen); return; }
	// (the list of 2026-11-08b: "the esc menu is inaccessible from the gamepad". Start opens the inventory; held half a second
	// with nothing open it opens this menu instead (the inventory takes a shorter press when it is let go: bStartTapped). With
	// the menu open, Start closes it (or goes back a page), as B does. Start's press and release come from the device itself
	// (StartKeys) once it has sent one; a flush of the controller's keys does not end a hold)
	{
		const FKey St = EKeys::Gamepad_Special_Right;
		const double Now = FPlatformTime::Seconds();
		const bool bListOpen = PlayerCombat && (PlayerCombat->IsInventoryOpen() || PlayerCombat->IsCraftingOpen());
		bool bPressed = false, bDown = false;
		if (RawStartDownAt > RawStartHandledAt) { bPressed = true; RawStartHandledAt = RawStartDownAt; }
		if (bRawStartSeen) bDown = bRawStartDown;
		else { bPressed = PC->WasInputKeyJustPressed(St); bDown = PC->IsInputKeyDown(St); }
		if (bPressed)
		{
			if (bMenuOpen) { ResetStartHold(); if (MenuPage > 0) BackToMainMenu(); else SetMenuOpen(false); return; }
			StartHeldSince = bListOpen ? -1.0 : Now;
		}
		if (StartHeldSince >= 0.0)
		{
			if (!bDown) { if (PlayerCombat) PlayerCombat->bStartTapped = true; StartHeldSince = -1.0; }
			else if (Now - StartHeldSince >= RDStartHoldSeconds) { SetMenuOpen(true); ResetStartHold(); ++MenuOpensByStart; return; }
		}
	}
	if (!bMenuOpen) return;
	auto Pressed = [PC](std::initializer_list<FKey> Keys) { for (const FKey& K : Keys) if (PC->WasInputKeyJustPressed(K)) return true; return false; };
	// (the Save page: the letters type its name; the arrows choose; Enter saves)
	if (MenuPage == 3)
	{
		TickSaveNameKeys(PC);
		if (Pressed({ EKeys::Up, EKeys::Gamepad_DPad_Up })) MoveMenuCursor(-1);
		if (Pressed({ EKeys::Down, EKeys::Gamepad_DPad_Down })) MoveMenuCursor(1);
		if (Pressed({ EKeys::Enter, EKeys::Gamepad_FaceButton_Bottom }))
		{
			const TArray<FName> It3 = MenuItems();
			if (It3.IsValidIndex(MenuCursor) && It3[MenuCursor] == TEXT("back")) BackToMainMenu();
			else ActivateMenuLine(It3.IndexOfByKey(FName(TEXT("savedo"))));
			return;
		}
	}
	else
	{
	if (Pressed({ EKeys::W, EKeys::Up, EKeys::Gamepad_DPad_Up })) MoveMenuCursor(-1);
	if (Pressed({ EKeys::S, EKeys::Down, EKeys::Gamepad_DPad_Down })) MoveMenuCursor(1);
	if (Pressed({ EKeys::A, EKeys::Left, EKeys::Gamepad_DPad_Left })) StepMenuValue(-1);
	if (Pressed({ EKeys::D, EKeys::Right, EKeys::Gamepad_DPad_Right })) StepMenuValue(1);
	if (Pressed({ EKeys::Enter, EKeys::SpaceBar, EKeys::Gamepad_FaceButton_Bottom })) { ActivateMenuLine(); return; }
	}
	if (Pressed({ EKeys::Gamepad_FaceButton_Right })) { if (MenuPage > 0) BackToMainMenu(); else SetMenuOpen(false); return; }
	// the mouse: a line under it is chosen; a click on a button presses it, on a slider's track (or dragging along it)
	// sets the volume where it is
	float Mx = 0.f, My = 0.f;
	if (!PC->GetMousePosition(Mx, My)) return;
	const FVector2D M(Mx, My);
	float Dx = 0.f, Dy = 0.f;
	PC->GetInputMouseDelta(Dx, Dy);
	if (!PC->IsInputKeyDown(EKeys::LeftMouseButton)) bMenuDragging = false;
	const TArray<FName> It = MenuItems();
	for (int32 I = 0; I < MenuRowBoxes.Num() && I < It.Num(); ++I)
	{
		const bool bIn = MenuRowBoxes[I].IsInside(M);
		if (bIn && (Dx != 0.f || Dy != 0.f || PC->WasInputKeyJustPressed(EKeys::LeftMouseButton))) MenuCursor = I;
		const int32 V = RDMenuVolumeOf(It[I]);
		if (V >= 0 && MenuTrackBoxes.IsValidIndex(I))
		{
			const FBox2D& T = MenuTrackBoxes[I];
			const bool bOnTrack = T.ExpandBy(10.f).IsInside(M);
			if (PC->WasInputKeyJustPressed(EKeys::LeftMouseButton) && bOnTrack) { bMenuDragging = true; MenuCursor = I; }
			if (bMenuDragging && MenuCursor == I && PC->IsInputKeyDown(EKeys::LeftMouseButton) && T.GetSize().X > 1.f)
				SetUserVolume(V, (M.X - T.Min.X) / T.GetSize().X);
		}
		else if (bIn && PC->WasInputKeyJustPressed(EKeys::LeftMouseButton)) { ActivateMenuLine(I); return; }
	}
}

FString ARDDungeonGenerator::MoveEditorStopKey(bool bShift)
{
	// (the editor's "stop play" command, Escape by default, is the PlayWorld context's StopPlaySession)
	const TSharedPtr<FUICommandInfo> Cmd = FInputBindingManager::Get().FindCommandInContext(TEXT("PlayWorld"), TEXT("StopPlaySession"));
	if (!Cmd.IsValid()) return TEXT("no PlayWorld.StopPlaySession command (no editor?)");
	const FInputChord Want(EKeys::Escape, bShift ? EModifierKey::Shift : EModifierKey::None);
	Cmd->SetActiveChord(Want, EMultipleKeyBindingIndex::Primary);
	FInputBindingManager::Get().NotifyActiveChordChanged(*Cmd, EMultipleKeyBindingIndex::Primary);
	FInputBindingManager::Get().SaveInputBindings();
	return FString::Printf(TEXT("PlayWorld.StopPlaySession: %s"), *Cmd->GetInputText().ToString());
}

void ARDDungeonGenerator::UpdateMapScrollInput(APlayerController* PC)
{
	const bool bWant = bMapOpen && bTacticalMaps;
	if (bWant == bMapScrollInput || !PC || !PC->GetLocalPlayer()) return;
	UEnhancedInputLocalPlayerSubsystem* EI = ULocalPlayer::GetSubsystem<UEnhancedInputLocalPlayerSubsystem>(PC->GetLocalPlayer());
	if (!EI) return;
	if (!MapScrollContext)
	{
		// (an action that consumes its keys: the contexts under it do not see them; the generator reads the keys itself)
		MapScrollAction = NewObject<UInputAction>(this, TEXT("IA_RD_MapScroll"));
		MapScrollAction->bConsumeInput = true;
		MapScrollContext = NewObject<UInputMappingContext>(this, TEXT("IMC_RD_MapScroll"));
		for (const FKey& K : { EKeys::Up, EKeys::Down, EKeys::Left, EKeys::Right }) MapScrollContext->MapKey(MapScrollAction, K);
		// (Brokenspire's map zooms and is dragged: the mouse, its wheel and the right stick are the map's while it is open, or
		// the camera turned behind it)
		if (bTown) for (const FKey& K : { EKeys::Mouse2D, EKeys::MouseX, EKeys::MouseY, EKeys::MouseWheelAxis, EKeys::Gamepad_Right2D, EKeys::Gamepad_RightX, EKeys::Gamepad_RightY })
			MapScrollContext->MapKey(MapScrollAction, K);
	}
	if (bWant) EI->AddMappingContext(MapScrollContext, 1000);
	else EI->RemoveMappingContext(MapScrollContext);
	bMapScrollInput = bWant;
}

bool ARDDungeonGenerator::ReloadSection(FIntPoint Coord)
{
	if (IsStartSection(Coord)) return false;
	TObjectPtr<ARDSection>* S = Sections.Find(Coord);
	if (!S || !*S || *S == Building) return false;
	(*S)->Destroy(); Sections.Remove(Coord); ++SectionsRemoved;
	Enqueue(Coord);
	return true;
}

void ARDDungeonGenerator::OnContainerOpened(ARDSection* Section, int32 Index, const FVector& At)
{
	if (!Section || !PlayerCombat) return;
	const TArray<FName> List = LootListOf(Section->Coord, Index);
	// (Brokenspire: gold in it, and the game remembers it was opened)
	const int32 GoldBefore = GetGold();
	if (bTown || bTownLink) TownOnContainer(Section, Index, At);
	if (List.Num() == 0)
	{
		// (level 5: one container in three holds anything; one that held nothing says so)
		if (ContainerLootChance < 1.f && GetGold() == GoldBefore) { PlayerCombat->ShowMessage(TEXT("Empty: nothing inside")); ++ContainersEmpty; }
		return;
	}
	for (int32 K = 0; K < List.Num(); ++K) PlayerCombat->AddItem(List[K], LootCountIn(List, Section->Coord, Index, K));
	LastFound = List[0]; LastFoundList = List; LastFoundTime = GetWorld()->GetTimeSeconds(); ItemsFound += List.Num();
	PlaySoundAt(TEXT("Player.Loot"), At);
	UE_LOG(LogRandomDungeonGen, Log, TEXT("RDLOOT %s from container %d of section (%d, %d)"), *FString::JoinBy(List, TEXT(", "), [](const FName& N) { return N.ToString(); }),
		Index, Section->Coord.X, Section->Coord.Y);
}

void ARDDungeonGenerator::MeanMonsterFactors(float& Health, float& Damage, FIntPoint Section) const
{
	float W = 0.f, H = 0.f, D = 0.f;
	TArray<int32> Kinds; MonsterKindsFor(Section, Kinds);
	for (const int32 K : Kinds) { const FRDMonsterDef& M = Monsters[K]; W += M.Weight; H += M.Weight * M.HealthFactor; D += M.Weight * M.DamageFactor; }
	Health = W > 0.f && H > 0.f ? H / W : 1.f; Damage = W > 0.f && D > 0.f ? D / W : 1.f;
}

void ARDDungeonGenerator::OnMonsterKilled(ARDMonster* Monster)
{
	++MonstersKilled;
	UE_LOG(LogRandomDungeonGen, Log, TEXT("RDCOMBAT %s killed (%d)"), Monster ? *Monster->MonsterName.ToString() : TEXT("?"), MonstersKilled);
	// (Brokenspire: its gold, the quests' counters)
	if (bTown || bTownLink)
	{
		bool bBossOf = false;
		for (const FEncounter& E : Encounters)
			if (E.bBoss && !E.bThrone && E.Live.Num() > 0 && E.Live[0].Get() == Monster)
			{
				bBossOf = true;
				// (the tier's boss is dead for the game: coming back into the castle does not set it again; the final boss has its own)
				if (bTownLink && !E.bFinal) TownCountMax(DungeonCounterName(FString::Printf(TEXT("bossdone:%d"), E.Tier)), 1);
			}
		TownOnKill(Monster, bBossOf);
	}
	// (the wilderness: one killed stays dead when its chunk is made again)
	if (Monster && Monster->WildKey >= 0)
	{
		if (URDGameInstance* GI = URDGameInstance::Of(this)) GI->WildKilled.AddUnique(Monster->WildKey);
		WildQuestOnKill(Monster);
	}
	// (mistward: one of a boss's band or a ring's guards stays dead)
	bool bBossKill = false;
	for (FEncounter& E : Encounters)
		for (int32 I = 0; I < E.Live.Num(); ++I)
			if (E.Live[I].Get() == Monster)
			{
				E.Dead[I] = true;
				if (E.bBoss && I == 0) bBossKill = true;
				// (a dungeon with no final boss: its last tier's boss is the dungeon's, and drops the next dungeon's key and map (the
				// list of 2026-11-08b))
				if (E.bBoss && I == 0 && !E.bFinal && !E.bThrone && MaxTier > 0 && E.Tier == MaxTier && !bFinalBossOn && Monster)
				{
					DropNextDungeonKey(Monster->GetActorLocation());
					// (the rebalance to tier 25: this dungeon's ability for the Summoner, the Rogue and the Martial Artist is hers now:
					// its bossdone:5 counter was written above (TownCountMax), which StartWeaponsOf reads)
					GrantLaterWeapons(true);
				}
				// (the final boss is no tier's boss: OnFinalBossKilled gives his notice and reward, no slash or chi attack here)
				if (E.bBoss && I == 0 && !E.bFinal)
				{
					TierNotice = E.bThrone ? FString(TEXT("THE USURPER IS SLAIN")) : FString::Printf(TEXT("THE BOSS OF TIER %d IS SLAIN"), E.Tier); TierNoticeTime = GetWorld()->GetTimeSeconds();
					if (E.bThrone) RoomUses.FindOrAdd(TEXT("usurper"))++;
					// (the third list: a slash of its tier for her weapons, when her hero takes slashes)
					const FName Sl = GiveBossSlash(E.Tier, Monster ? Monster->GetActorLocation() : E.At);
					if (!Sl.IsNone()) TierNotice += FString::Printf(TEXT("  -  THE %s IS YOURS"), *Sl.ToString().ToUpper());
					// (the Martial Artist: a tier's boss (not a usurper) teaches her the next of her locked weapons, her chi attacks)
					if (!E.bThrone)
						if (const FRDHeroDef* H = FindHero(CurrentHero); H && H->LockedWeapons.Num() > 0)
						{
							const int32 Before = WeaponsUnlocked;
							if (UnlockHeroWeapons(H->UnlockPerBoss) > 0)
							{
								TArray<FString> Names;
								for (int32 K = Before; K < WeaponsUnlocked; ++K) Names.Add(H->LockedWeapons[K].Name.ToString().ToUpper());
								TierNotice += TEXT("  -  YOU LEARN ") + FString::Join(Names, TEXT(" AND "));
							}
						}
				}
			}
	// (the final boss: its loot, the gold, the castle conquered, the door to Brokenspire open)
	if (Monster && Monster->bFinalBoss) OnFinalBossKilled(Monster);
	// (the list of 2026-10-30: its parts float over it until she takes them; a boss's or a usurper's are more)
	if (bHarvest && Monster) HarvestKill(Monster, bBossKill);
	// (the tiers: it stays dead, also when its section is generated again)
	if (Monster && Monster->Section && Monster->SpawnIndex >= 0)
		if (FRDSectionProgress* P = Progress.Find(Monster->Section->Coord))
		{
			P->Killed.AddUnique(Monster->SpawnIndex);
			// (level 5: where it lies, for its corpse when the section is generated again)
			if (bKeepCorpses) P->Corpses.Add(Monster->SpawnIndex, Monster->GetActorTransform());
			UpdateProgress(Monster->Section->Coord);
		}
}

void ARDDungeonGenerator::AddHitText(const FVector& At, float Amount, bool bOnPlayer)
{
	const float Now = GetWorld()->GetTimeSeconds();
	HitTexts.RemoveAll([Now](const FHitText& T) { return Now - T.Time > 1.5f; });
	HitTexts.Add({ At, Amount, Now, bOnPlayer });
}

void ARDDungeonGenerator::RestartPlay(int32 Seed)
{
	if (Seed != 0) SessionSeed = Seed;
	for (auto It = Sections.CreateIterator(); It; ++It)
	{
		if (IsStartSection(It->Key) && It->Value) continue;
		if (It->Value) It->Value->Destroy();
		It.RemoveCurrent();
	}
	Queue.Reset(); Building = nullptr; MapData.Reset(); HitTexts.Reset();
	if (Blood) Blood->Clear();
	SoundCounts.Reset(); LastSoundPick.Reset(); SoundR.Initialize(RDSoundSeed);
	StopMusic();
	SectionsGenerated = Sections.Num(); SectionsRemoved = 0; MonstersKilled = 0; bMapOpen = false; MapPan = FVector2D::ZeroVector; LastRevealTime = -100.f;
	LootedContainers.Reset();
	Progress.Reset(); TierNotice.Reset(); TierNoticeTime = -100.f;     // (the tiers start again: only tier 1 open)
	for (ARDMonster* A : Allies) if (A) A->Destroy();
	Allies.Reset();
	CarrySummons.Reset(); CarrySummonShares.Reset();          // (no summons brought from the other level called after a restart)
	ResetMistward5();          // (mistward5: no shot of before in the air, no audience, autoplay ended)
	ResetFinal();              // (the final boss: not placed, its door and its lights from above gone)
	// (mistward: what the rules set waiting, her dropped things, the pads, the cells, the traps start again)
	for (const FEncounter& E : Encounters) for (const TWeakObjectPtr<ARDMonster>& M : E.Live) if (M.IsValid()) M->Destroy();
	// (and every other monster that is none of a set's planned ones (a boss's band, a guard, one a teleport trap brought, a
	// caged one): the start set is kept, and a restart left 60 of them standing in it after a few runs)
	for (auto& KV : Sections)
		if (ARDSection* S = KV.Value)
		{
			for (ARDMonster* M : S->SpawnedMonsters) if (IsValid(M) && M->SpawnIndex < 0) M->Destroy();
			S->SpawnedMonsters.RemoveAll([](const TObjectPtr<ARDMonster>& M) { return !IsValid(M) || M->IsActorBeingDestroyed(); });
		}
	Encounters.Reset(); ForcedLoot.Reset(); TiersOpened.Reset(); CensusCache.Reset(); CensusQueue.Reset();
	for (ARDLootPile* P : LootPiles) if (IsValid(P)) P->Destroy();
	LootPiles.Reset(); Harvests = HarvestRolls = 0;
	Pads.Reset(); PadSections.Reset(); PadRingsTaken.Reset(); PadActors.Reset(); PadChoice = 0; Teleports = 0;
	CellsOpened.Reset(); PrisonersFreed = CellBreakouts = 0;
	SpentTraps.Reset(); DisarmKey = FIntVector(0, 0, -1); TrapsTriggered = TrapsDisarmed = TrapHits = 0; LastTrap.Reset();
	TrapR.Initialize((int32)HashCombine((uint32)SessionSeed, 0x7D15u)); PendingRingTiers.Reset(); RestoredBossTiers.Reset(); RestoredRingTiers.Reset();
	// (the third list: the tables' weapons back, the fixtures full, the arenas and vaults as they were, the slashes not given)
	for (const TWeakObjectPtr<ARDMonster>& M : ArenaMonsters) if (M.IsValid()) M->Destroy();
	ArenaMonsters.Reset(); ArenaRoom = -1; ArenaWave = 0; ArenaWavesBeaten = 0;
	TakenPickups.Reset(); PickupsTaken = 0; UsedFixtures.Reset(); ArenasWon.Reset(); VaultsOpened.Reset(); RoomUses.Reset(); SlashesGiven.Reset();
	SlashR.Initialize((int32)HashCombine((uint32)SessionSeed, 0x51A5u));
	ItemsFound = 0; LastFound = NAME_None; LastFoundList.Reset();
	// (the weapons she found are gone: hers are the hero's again)
	if (const FRDHeroDef* H = Heroes.Num() > 0 ? FindHero(CurrentHero) : nullptr) StartWeaponsOf(*H, Weapons);
	WeaponsUnlocked = 0;          // (a new run: none of her locked weapons gained yet)
	// (martial_arts: the room's monsters come again from none)
	for (const TWeakObjectPtr<ARDMonster>& M : OneRoomLive) if (M.IsValid()) M->Destroy();
	OneRoomLive.Reset(); OneRoomSpawned = 0; OneRoomNext = 0.f;
	for (auto& KV : Sections) KV.Value->ActivateForPlay();
	if (PlayerCombat)
	{
		PlayerCombat->ResetWeapons();
		PlayerCombat->ClearItems();                // (nothing found yet, no armour on)
		PlayerCombat->Revive(true);
		// (after Revive: WearShield refuses while she is down)
		if (const FName* Sh = StartShield.Find(CurrentHero); Sh && FindItem(*Sh) >= 0) { PlayerCombat->AddItem(*Sh, 1); PlayerCombat->WearShield(*Sh); }
		PlayerCombat->Kills = PlayerCombat->AttacksMade = PlayerCombat->HitsLanded = PlayerCombat->HitsTaken = PlayerCombat->Deaths = 0;
		PlayerCombat->DamageDealt = PlayerCombat->DamageTaken = 0.f;
		PlayerCombat->LastHurtTime = PlayerCombat->LastHitTime = PlayerCombat->DeathTime = -100.f;
		PlayerCombat->SelectWeapon(0);
	}
}

TArray<ARDMonster*> ARDDungeonGenerator::GetMonsters() const
{
	TArray<ARDMonster*> Out;
	for (const auto& KV : Sections) if (KV.Value) for (ARDMonster* M : KV.Value->SpawnedMonsters) if (M) Out.Add(M);
	// (the wilderness's: its own section, not on the grid)
	if (WildSection) for (ARDMonster* M : WildSection->SpawnedMonsters) if (IsValid(M)) Out.Add(M);
	return Out;
}

void ARDDungeonGenerator::GetDiscoveryStats(int32& Disc, int32& Gen) const
{
	Disc = Gen = 0;
	for (const auto& KV : MapData)
		for (const FRDMapRect& R : KV.Value.Rects) if (!R.bCorridor) { ++Gen; if (R.bDiscovered) ++Disc; }
}

FString ARDDungeonGenerator::InteractNearest(FVector From, float MaxDistance)
{
	ARDSection* Best = nullptr; bool bBestDoor = false; int32 BestI = -1; float BestD = MaxDistance;
	const FIntPoint Here = WorldToSection(From);
	for (int32 Dx = -1; Dx <= 1; ++Dx)
		for (int32 Dy = -1; Dy <= 1; ++Dy)
			if (ARDSection* S = GetSection(Here + FIntPoint(Dx, Dy)))
			{
				bool bDoor; int32 I;
				const float D = S->FindNearestInteractive(From, BestD, bDoor, I);
				if (I >= 0 && D < BestD) { BestD = D; Best = S; bBestDoor = bDoor; BestI = I; }
			}
	// (mistward: her dropped things, a teleporter pad, a trap she has seen (the Rogue disarms it) come before the rest)
	if (LootPiles.Num() > 0 && TakeLootNear(From, 260.f)) return TEXT("loot");
	// (Brokenspire: someone of the town, a service, the gate, a boarded door; the castle's way back)
	if (bTown || bTownLink) { const FString Tw = TownInteract(From); if (!Tw.IsEmpty()) return Tw; }
	// (the third list: an armory table's weapon, a shrine, a fountain, a vault's door)
	if (bSpecialRooms || bWeaponPickups) { const FString Sp = UseSpecialNear(From); if (!Sp.IsEmpty()) return Sp; }
	if (bTeleporters) { const FString Pd = UsePadNear(From); if (!Pd.IsEmpty()) return Pd; }
	if (Traps.Num() > 0 && BeginDisarmNear(From)) return TEXT("disarm");
	// (level 5: an anvil nearer than any door or container opens her crafting panel)
	FVector Anvil;
	if (PlayerCombat && Recipes.Num() > 0 && FindNearestAnvil(From, FMath::Min(BestD, AnvilReach), Anvil))
	{
		PlayerCombat->SetCraftStation(NAME_None);
		PlayerCombat->SetCraftingOpen(true);
		return TEXT("anvil");
	}
	if (!Best) return FString();
	if (bBestDoor && Best->IsDoorCell(BestI) && !Best->DescribeCell(BestI).IsEmpty())
	{
		// (mistward: a locked cell: a prisoner is let out; a monster's is locked from within, and opens when she is near)
		const int32 C = Best->CellOfDoor(BestI);
		if (Best->Cells.IsValidIndex(C) && Best->Cells[C].Occupant == 1) { Best->OpenCell(BestI); if (bTownLink) TownCount(DungeonCounterName(TEXT("prisoners"))); return TEXT("prisoner"); }
		if (PlayerCombat) PlayerCombat->ShowMessage(TEXT("The cell is locked from within"));
		return TEXT("cell locked");
	}
	if (bBestDoor) { Best->ToggleDoor(BestI, From); return Best->IsDoorCell(BestI) ? TEXT("cell door") : TEXT("door"); }
	Best->ToggleContainer(BestI);
	return Best->GetContainerKind(BestI);
}

void ARDDungeonGenerator::StartRecordingOutput(float Seconds)
{
	UAudioMixerBlueprintLibrary::StartRecordingOutput(this, Seconds, nullptr);
}

void ARDDungeonGenerator::StopRecordingOutput(const FString& Dir, const FString& Name)
{
	UAudioMixerBlueprintLibrary::StopRecordingOutput(this, EAudioRecordingExportType::WavFile, Name, Dir, nullptr, nullptr);
}

int32 ARDDungeonGenerator::FindRecipe(FName Item) const
{
	for (int32 I = 0; I < Recipes.Num(); ++I) if (Recipes[I].Item == Item) return I;
	return -1;
}

bool ARDDungeonGenerator::FindNearestAnvil(FVector From, float MaxDistance, FVector& At) const
{
	// (an anvil of the room she is in: not one behind a wall, in the room or the section next door)
	bool bFound = false; float BestD = MaxDistance;
	const ARDSection* S = GetSection(WorldToSection(From));
	const int32 Room = S ? S->RoomAt(From) : -1;
	if (Room < 0) return false;
	for (const FVector& A : S->GetAnvilPoints())
	{
		const float D = FVector::Dist2D(A, From);
		if (D < BestD && S->RoomAt(A) == Room) { BestD = D; At = A; bFound = true; }
	}
	return bFound;
}

TArray<FVector> ARDDungeonGenerator::GetAllAnvils() const
{
	TArray<FVector> Out;
	for (const auto& KV : Sections) if (KV.Value) Out.Append(KV.Value->GetAnvilPoints());
	return Out;
}

int32 ARDDungeonGenerator::LootCountOf(FIntPoint Section, int32 Index, int32 Pick) const
{
	return LootCountIn(LootListOf(Section, Index), Section, Index, Pick);
}

int32 ARDDungeonGenerator::LootCountIn(const TArray<FName>& L, FIntPoint Section, int32 Index, int32 Pick) const
{
	if (!L.IsValidIndex(Pick)) return 0;
	const int32 Ix = FindItem(L[Pick]);
	const int32 Max = Ix >= 0 ? FMath::Max(Items[Ix].FoundMax, 1) : 1;
	if (Max <= 1) return 1;
	const uint32 H = HashCombine(HashCombine((uint32)SessionSeed ^ 0x2C3Du, GetTypeHash(Section)), GetTypeHash(Index * 131 + Pick * 17 + 5));
	return 1 + (int32)(H % (uint32)Max);
}

FString ARDDungeonGenerator::DescribeNearest(FVector From, float MaxDistance) const
{
	const ARDSection* Best = nullptr; bool bBestDoor = false; int32 BestI = -1; float BestD = MaxDistance;
	const FIntPoint Here = WorldToSection(From);
	for (int32 Dx = -1; Dx <= 1; ++Dx)
		for (int32 Dy = -1; Dy <= 1; ++Dy)
			if (const ARDSection* S = GetSection(Here + FIntPoint(Dx, Dy)))
			{
				bool bDoor; int32 I;
				const float D = S->FindNearestInteractive(From, BestD, bDoor, I);
				if (I >= 0 && D < BestD) { BestD = D; Best = S; bBestDoor = bDoor; BestI = I; }
			}
	// (mistward: her dropped things, a pad, a trap she sees)
	// (the nearest within reach, the one F takes (TakeLootNear): the first in the list named another pile beside it, the PR
	// review's find)
	const ARDLootPile* Lp = nullptr; float LpD = 260.f;
	for (const ARDLootPile* P : LootPiles) if (IsValid(P)) { const float D = FVector::Dist2D(P->GetActorLocation(), From); if (D < LpD) { LpD = D; Lp = P; } }
	if (Lp)
		{
			// (hers, where she fell; or something the rules laid on the floor: the guarded ring; or a dead monster's parts)
			if (Lp->bHers) return FString::Printf(TEXT("take up your things (%d)"), Lp->GetNumThings());
			if (Lp->bHarvest) return FString::Printf(TEXT("harvest the parts (%d)"), Lp->GetNumThings());
			return Lp->GetNumThings() == 1 ? FString::Printf(TEXT("take the %s"), *Lp->Things[0].ToString().ToLower()) : FString::Printf(TEXT("take up what lies here (%d)"), Lp->GetNumThings());
		}
	if (bTown || bTownLink) { const FString Tw = TownDescribe(From); if (!Tw.IsEmpty()) return Tw; }
	if (bSpecialRooms || bWeaponPickups) { const FString Sp = DescribeSpecialNear(From); if (!Sp.IsEmpty()) return Sp; }
	if (bTeleporters) { const FString Pd = DescribePadNear(From); if (!Pd.IsEmpty()) return Pd; }
	if (Traps.Num() > 0) { const FString Tr = DescribeTrapNear(From); if (!Tr.IsEmpty()) return Tr; }
	FVector Anvil;
	if (Recipes.Num() > 0 && FindNearestAnvil(From, FMath::Min(BestD, AnvilReach), Anvil)) return TEXT("use the anvil");
	if (!Best) return FString();
	if (bBestDoor && Best->IsDoorCell(BestI)) { const FString Cl = Best->DescribeCell(BestI); if (!Cl.IsEmpty()) return Cl; }
	// (a lever reached by the doors' longer reach: named as a lever, not "open door" (the PR review's find))
	if (bBestDoor && Best->GetDoorKind(BestI) == TEXT("lever")) return Best->IsPortcullisUp() ? TEXT("pull the lever (lower the portcullis)") : TEXT("pull the lever (raise the portcullis)");
	FString What = bBestDoor ? (Best->IsDoorCell(BestI) ? TEXT("cell door") : Best->GetDoorKind(BestI) == TEXT("gate") ? TEXT("gate") : TEXT("door")) : Best->GetContainerKind(BestI);
	What.ReplaceInline(TEXT("2"), TEXT(""));
	return FString::Printf(TEXT("%s %s"), Best->IsTargetOpen(bBestDoor, BestI) ? TEXT("close") : TEXT("open"), *What);
}

void ARDDungeonGenerator::UpdateDiscovery(const FVector& L)
{
	const FIntPoint T = WorldToTile(L);
	const FIntPoint S = WorldToSection(L);
	FRDSectionMap* M = MapData.Find(S);
	if (!M) return;
	bool bRoom = false;
	for (FRDMapRect& R : M->Rects)
	{
		if (R.bDiscovered) continue;
		// rooms: once she is inside (or in their doorway); hallways: within 4 tiles of her along them
		const int32 Pad = R.bCorridor ? 4 : 0;
		if (T.X >= R.Min.X - Pad && T.Y >= R.Min.Y - Pad && T.X < R.Max.X + Pad && T.Y < R.Max.Y + Pad) { R.bDiscovered = true; bRoom |= !R.bCorridor; }
	}
	if (bRoom) UpdateProgress(S);       // (a room explored: the tiers count it)
}

void ARDDungeonGenerator::BeginPlay()
{
	Super::BeginPlay();
	// (the list of 2026-11-08b: the gamepad's Start as the device sends it, for the Escape menu's hold)
	if (bEscapeMenu && !StartKeys.IsValid() && FSlateApplication::IsInitialized())
	{
		TSharedRef<FRDStartKeys> K = MakeShared<FRDStartKeys>(); K->Owner = this;
		StartKeys = K; FSlateApplication::Get().RegisterInputPreProcessor(K);
	}
	SessionSeed = FixedSessionSeed != 0 ? FixedSessionSeed : (int32)(FDateTime::Now().GetTicks() & 0x7fffffff);
	if (bRevealEffect && RevealPostMaterial)
	{
		RevealMID = UMaterialInstanceDynamic::Create(RevealPostMaterial, this);
		for (int32 Slot = 0; Slot < RevealSlots; ++Slot) RevealMID->SetVectorParameterValue(*FString::Printf(TEXT("Info%d"), Slot), FLinearColor(0, 0, -1e6f, 0));
		RevealPost->Settings.WeightedBlendables.Array.Add(FWeightedBlendable(1.f, RevealMID));
	}
	SoundR.Initialize(RDSoundSeed);
	if (bEscapeMenu) LoadUserVolumes();
	if (bOptionsMenu) { LoadOptions(); ApplyDisplayFromCommandLine(); }
	// (the non-realtime audio device loses spatialised sources: see bSpatializeSounds)
	bSpatializeNow = bSpatializeSounds && !FParse::Param(FCommandLine::Get(), TEXT("deterministicaudio"));
	Attenuations.Reset();
	if (FParse::Value(FCommandLine::Get(), TEXT("RDSoundTest="), SoundTestDir)) { SoundTestStep = -1; SoundTestLog.Reset(); }
	if (bCombat && BloodDropMesh)
	{
		Blood = NewObject<URDBloodComponent>(this, TEXT("RDBlood"));
		Blood->RegisterComponent();
		Blood->Init(this);
	}
	StopMusic();
	// (no hero chosen, as when the level is played from the editor: the menu first; it opens this level again with ?Hero=)
	if (Heroes.Num() > 0 && !MenuLevel.IsEmpty() && CVarRDHeroMenu.GetValueOnGameThread() != 0)
	{
		const AGameModeBase* GM = GetWorld()->GetAuthGameMode();
		if (GM && UGameplayStatics::ParseOption(GM->OptionsString, TEXT("Hero")).IsEmpty())
		{
			bOpeningMenu = true;
			UE_LOG(LogRandomDungeonGen, Log, TEXT("RDHERO no hero chosen: opening the menu %s"), *MenuLevel);
			UGameplayStatics::OpenLevel(this, FName(*MenuLevel));
			return;
		}
	}
	// (the hero chosen in the menu: her weapons, hit points and controls become the generator's before anything reads them)
	if (Heroes.Num() > 0) ApplyHero(ChosenHero());
#if WITH_EDITORONLY_DATA
	// (level 5: in the editor a pack's effect is compiled the first time it is used, and shows nothing for the seconds that
	// takes (the Apocalypse's: 9 s after its cast): every spell's effects are asked for now, while she walks the first rooms)
	if (Spells.Num() > 0)
	{
		TSet<UNiagaraSystem*> Seen;
		auto Warm = [&Seen](UFXSystemAsset* A) { if (UNiagaraSystem* N = Cast<UNiagaraSystem>(A); N && !Seen.Contains(N)) { Seen.Add(N); N->RequestCompile(false); } };
		for (const FRDSpellDef& S : Spells) { Warm(S.CastFx); Warm(S.BoltFx); Warm(S.ImpactFx); Warm(S.AreaFx); Warm(S.ShieldFx); }
		UE_LOG(LogRandomDungeonGen, Log, TEXT("RDSPELL %d effects asked to compile"), Seen.Num());
	}
	// (the third list: the slashes' effects and the rooms' glows likewise)
	if (bBossSlashes || bSpecialRooms)
	{
		int32 Num = 0;
		auto Warm2 = [&Num](UFXSystemAsset* A) { if (UNiagaraSystem* N = Cast<UNiagaraSystem>(A)) { N->RequestCompile(false); ++Num; } };
		for (const FRDSlashDef& S : Slashes) { Warm2(S.Fx); Warm2(S.ImpactFx); }
		Warm2(ShrineFx); Warm2(HealFountainFx); Warm2(SpeedFountainFx); Warm2(ManaFountainFx); Warm2(BlessFx);
		UE_LOG(LogRandomDungeonGen, Log, TEXT("RDSLASH %d effects asked to compile"), Num);
	}
#endif
	SlashR.Initialize((int32)HashCombine((uint32)SessionSeed, 0x51A5u));
	MapData.Reset();
	for (auto It = Sections.CreateIterator(); It; ++It) if (!It->Value) It.RemoveCurrent();
	// (Brokenspire: the game's town (its seed), what was looted and opened in it or in the castle)
	if (bTown || bTownLink) { BeginTownPlay(); if (bOpeningMenu) return; }
	if (Sections.Num() == 0) SpawnSection(FIntPoint::ZeroValue, false);
	else for (auto& KV : Sections) KV.Value->ActivateForPlay();
	if (bTown || bTownLink) AfterTownBuilt();
	UE_LOG(LogRandomDungeonGen, Log, TEXT("RDGEN play: %d start sections, session seed %d, %d monsters"), Sections.Num(), SessionSeed, GetNumMonsters());
}

void ARDDungeonGenerator::Tick(float Dt)
{
	Super::Tick(Dt);
	++GenTicks;
	if (bOpeningMenu) return;
	// (mistward: the frame rate, smoothed over about a second of frames, from the real time between frames)
	if (bShowFps)
	{
		const float Real = (float)FApp::GetDeltaTime();
		if (Real > 1e-5f) FpsSmoothed = FpsSmoothed <= 0.f ? 1.f / Real : FMath::Lerp(FpsSmoothed, 1.f / Real, FMath::Clamp(Real * 2.f, 0.02f, 1.f));
	}
	// (mistward's pointer: after the player controller, every frame. A click is read as "just pressed", which holds for the
	// frame after the controller took it in: in an order that changed between frames, a quick click was not seen at all)
	if (bMouseUI)
		if (APlayerController* PPC = UGameplayStatics::GetPlayerController(this, 0); PPC && PPC != TickAfterController.Get())
		{
			AddTickPrerequisiteActor(PPC); TickAfterController = PPC;
		}
	// (it ticks while the game is paused: then only her inventory or the Escape menu, which paused it, is worked)
	const bool bPaused = GetWorld()->IsPaused();
	// (Brokenspire's showcase tour: on the real clock, also while its panel pauses the game)
	if (bTown && (bTourOn || !bTourCmdRead)) TickTownTour((float)FApp::GetDeltaTime());
	// (the list of 2026-11-04's showcase pilot: on the real clock, also under the menu and the oven's panel)
	if (bTown && bWild) TickShow7((float)FApp::GetDeltaTime(), UGameplayStatics::GetPlayerController(this, 0));
	// (Brokenspire: the town's panel takes the keys while it is open, Escape too)
	if (IsTownPanelOpen())
	{
		if (!PlayerCombat || PlayerCombat->IsDead()) CloseTownPanel();
		else if (APlayerController* TPC = UGameplayStatics::GetPlayerController(this, 0)) TickTownPanel(TPC);
		return;
	}
	if (APlayerController* MPC = UGameplayStatics::GetPlayerController(this, 0)) TickMenu(MPC);
	if (bMenuOpen) return;
	if (Heroes.Num() > 0 && PlayerCombat)
		if (APlayerController* PC = UGameplayStatics::GetPlayerController(this, 0)) PlayerCombat->TickInventory(PC);
	if (bPaused) return;
	TickAllies(Dt);
	TickCarrySummons();
	TickDungeonKeys();
	// input: F interacts, M toggles the map
	if (APlayerController* PC = UGameplayStatics::GetPlayerController(this, 0))
	{
		APawn* P = PC->GetPawn();
		if (bCombat && P && (!PlayerCombat || PlayerCombat->GetOwner() != P))
		{
			// the player gets her hit points and weapons
			PlayerCombat = P->FindComponentByClass<URDCombatComponent>();
			if (!PlayerCombat)
			{
				PlayerCombat = NewObject<URDCombatComponent>(P, TEXT("RDCombat"));
				PlayerCombat->RegisterComponent();
				PlayerCombat->Init(this);
				// (mistward: the game's own input mode, whatever the menu left: the camera follows the mouse unpressed)
				if (bMouseUI) { PC->SetShowMouseCursor(false); PC->SetInputMode(FInputModeGameOnly()); }
				// (mistward: the shield her hero starts with, on her arm)
				if (const FName* Sh = StartShield.Find(CurrentHero); Sh && FindItem(*Sh) >= 0) { PlayerCombat->AddItem(*Sh, 1); PlayerCombat->WearShield(*Sh); }
				// (Brokenspire: what she carried from the other level, in place of what her hero starts with)
				if (bTown || bTownLink) RestoreCarry();
			}
			// (a face that moves: the level's expression channels on her pawn)
			if (FaceChannels.Num() > 0 && !P->FindComponentByClass<URDFaceComponent>())
			{
				URDFaceComponent* F = NewObject<URDFaceComponent>(P, TEXT("RDFace"));
				F->Channels = FaceChannels; F->Cues = FaceCues; F->Seed = (int32)HashCombine((uint32)SessionSeed, 0x6A11u);
				F->MetaFace = FaceMeta;
				if (ACharacter* PCh = Cast<ACharacter>(P)) F->Mesh = PCh->GetMesh();
				F->RegisterComponent();
			}
			// what she hears fades with the distance to her, not to the camera behind her
			if (Sounds.Num() > 0) PC->SetAudioListenerAttenuationOverride(P->GetRootComponent(), FVector::ZeroVector);
		}
		// the safety net: a fall out of the dungeon (through a gap that let her through) puts her back where she last stood
		if (ACharacter* Ch = Cast<ACharacter>(P); Ch && FallResetDepth > 0.f)
		{
			const FVector L = Ch->GetActorLocation();
			// (the wilderness: the ground under her, not the level's floor)
			float Floor = bWild && IsWildReady() ? WildGroundZ(L) : GetActorLocation().Z;
			// (the catacombs: the floor of the set she is in, or the ramp's height on a stair)
			if (bTierFloors)
			{
				const FIntPoint Sn = WorldToSection(L);
				const ARDSection* Sec = GetSection(Sn);
				Floor = Sec ? Sec->FloorZAt(L) : SectionFloorZ(Sn);
			}
			if (L.Z < Floor - FallResetDepth)
			{
				const FVector To = bHasSafeSpot ? LastSafeSpot : GetStartRoomCenter() + FVector(0, 0, 100.f);
				Ch->SetActorLocation(To, false, nullptr, ETeleportType::TeleportPhysics);
				Ch->GetCharacterMovement()->StopMovementImmediately();
				++FallResets;
				UE_LOG(LogRandomDungeonGen, Warning, TEXT("RDGEN fell out at (%.0f, %.0f, %.0f): back to (%.0f, %.0f, %.0f)"), L.X, L.Y, L.Z, To.X, To.Y, To.Z);
			}
			else if (Ch->GetCharacterMovement()->IsMovingOnGround() && FMath::Abs(L.Z - Floor) < 250.f) { LastSafeSpot = L + FVector(0, 0, 5.f); bHasSafeSpot = true; }
		}
		if (Sounds.Num() > 0 && P)
		{
			// The listener, every tick. The viewport does this itself, but not for a play-in-editor window that does not
			// have the focus (it shares the editor's audio device): a reel rendered with the editor in the background had
			// every placed sound heard from wherever the listener was when the window lost the focus.
			if (FAudioDeviceHandle AD = GetWorld()->GetAudioDevice())
			{
				FVector Loc, Front, Right;
				PC->GetAudioListenerPosition(Loc, Front, Right);
				FTransform Listener(FRotationMatrix::MakeFromXY(Front, Right));
				Listener.SetTranslation(Loc);
				Listener.NormalizeRotation();
				AD->SetListener(GetWorld(), 0, Listener, Dt);
				FVector Att;
				if (PC->GetAudioListenerAttenuationOverridePosition(Att)) AD->SetListenerAttenuationOverride(0, Att);
			}
		}
		if ((PC->WasInputKeyJustPressed(EKeys::F) || (bCasterControls && PC->WasInputKeyJustPressed(EKeys::Gamepad_FaceButton_Left))) && P
			&& !(PlayerCombat && (PlayerCombat->IsCraftingOpen() || PlayerCombat->CraftClosedFrame == GFrameCounter)) && TownPanelClosedFrame != GFrameCounter
			&& !(bMapOpen && IsWildMapShown())) InteractNearest(P->GetActorLocation());
		if (bTown || bTownLink) TickTown(Dt, PC);
		if (bWild) TickWild(Dt, PC);
		if (PC->WasInputKeyJustPressed(EKeys::M) || (bCasterControls && PC->WasInputKeyJustPressed(EKeys::Gamepad_Special_Left))) SetMapOpen(!bMapOpen);
		// the big map scrolls under the arrow keys (the D-pad), C (the right stick pressed) brings it back over her
		UpdateMapScrollInput(PC);
		if (bMapOpen && bTacticalMaps && IsWildMapShown()) TickWildMapInput(PC, Dt);
		else if (bMapOpen && bTacticalMaps && bTown) TickTownMapInput(PC, Dt);
		else if (bMapOpen && bTacticalMaps)
		{
			auto Down = [&](const FKey& K) { return PC->IsInputKeyDown(K) ? 1.f : 0.f; };
			const float N = Down(EKeys::Up) + Down(EKeys::Gamepad_DPad_Up) - Down(EKeys::Down) - Down(EKeys::Gamepad_DPad_Down);
			const float E = Down(EKeys::Right) + Down(EKeys::Gamepad_DPad_Right) - Down(EKeys::Left) - Down(EKeys::Gamepad_DPad_Left);
			MapPan += FVector2D(FMath::Clamp(N, -1.f, 1.f), FMath::Clamp(E, -1.f, 1.f)) * MapPanSpeed * Dt;
			if (MapPan.Size() > MapPanMax) MapPan = MapPan.GetSafeNormal() * MapPanMax;
			if (PC->WasInputKeyJustPressed(EKeys::C) || PC->WasInputKeyJustPressed(EKeys::Gamepad_RightThumbstick)) CenterMap();
		}
	}
	// (mistward: the census of the sets she has not reached, the traps, the cells; G picks the first tier pad's destination)
	if (TierOpenShare < 1.f && MaxTier > 0 && !bTown)
	{
		// (the open tiers' sets are counted ahead, a few a frame, so that the next tier opens the moment it should)
		// (looked for twice a second: once all are counted the tallies say nothing new)
		const float Now_ = GetWorld()->GetTimeSeconds();
		if (CensusQueue.Num() == 0 && Now_ - CensusLookTime > 0.5f)
		{
			CensusLookTime = Now_;
			for (int32 T = 1; T < MaxTier && IsTierOpen(T); ++T) { FIntVector D, A; GetTierTally(T, D, A); if (CensusQueue.Num() > 0) break; }
		}
		if (CensusQueue.Num() > 0) TickCensus();
	}
	if (Traps.Num() > 0) TickTraps(Dt);
	if (bSpecialRooms) TickArena(Dt);          // (the third list: an arena begun, its waves)
	if (bArenaLock || bArenaCrowd) TickArenaHold(Dt);      // (mistward5: no way out; the audience)
	if (bMonsterRanged) TickMonsterShots(Dt);              // (mistward5: the monsters' shots in the air)
	if (bFinalBossOn) TickFinal(Dt);                       // (the final boss: the last tier's share, the light from above)
	if (bTown || bFinalBossOn) TickFinalShow(Dt);          // (the final boss's showcase: -RDFinalShow)
	TickGameSpeed();                                       // (the list of 2026-11-08b: rd.GameSpeed)
	if (!bAutoplayOptionRead) ReadAutoplayOption();        // (mistward5: ?Autoplay= / -Autoplay=)
	if (bAutoplay) TickAutoplay(Dt);
	if (bOneRoom) TickOneRoom(Dt);             // (martial_arts: the room's monsters)
	// (mistward: the rings to guard of a tier opened by the last container she opened, now that it has given what it held)
	if (PendingRingTiers.Num() > 0) { const TArray<int32> Ts = PendingRingTiers; PendingRingTiers.Reset(); for (const int32 T : Ts) PlaceRingGuard(T); }
	// (Brokenspire: the bosses and rings of the tiers open from an earlier visit, once a room of the tier before is seen)
	if ((RestoredBossTiers.Num() > 0 || RestoredRingTiers.Num() > 0) && GetWorld()->GetTimeSeconds() >= RestoredTryAt)
	{
		RestoredTryAt = GetWorld()->GetTimeSeconds() + 1.f;
		RestoredBossTiers.RemoveAll([this](int32 T) { return PlaceBoss(T); });
		RestoredRingTiers.RemoveAll([this](int32 T) { return PlaceRingGuard(T); });
	}
	if (PrisonerDefs.Num() > 0)
		if (APawn* Her = UGameplayStatics::GetPlayerPawn(this, 0))
		{
			const FIntPoint Here = WorldToSection(Her->GetActorLocation());
			for (int32 Dx = -1; Dx <= 1; ++Dx) for (int32 Dy = -1; Dy <= 1; ++Dy) if (ARDSection* S = GetSection(Here + FIntPoint(Dx, Dy))) S->TickCells(Dt, Her);
		}
	if (bTeleporters)
		if (APlayerController* PC = UGameplayStatics::GetPlayerController(this, 0); PC && PC->GetPawn() && PC->WasInputKeyJustPressed(EKeys::G) && PadNear(PC->GetPawn()->GetActorLocation()) == 1)
		{
			const TArray<int32> D = GetPadDestinations();
			if (D.Num() > 0) { const int32 I = D.Find(PadChoice); PadChoice = D[(I == INDEX_NONE ? 0 : I + 1) % D.Num()]; }
		}
	if (!SoundTestDir.IsEmpty()) TickSoundTest(Dt);
	else TickMusic(Dt);         // (the self test measures single sounds: no music under them, only the room tone)
	const AActor* Pawn = GetTrackedActor();
	if (Pawn)
	{
		const FVector L = Pawn->GetActorLocation(), V = Pawn->GetVelocity();
		const float SS = SectionTiles * TileSize;
		// the section TriggerDistance ahead of her along each axis she is moving on
		for (int32 Axis = 0; Axis < 2; ++Axis)
		{
			const float Vx = Axis == 0 ? V.X : V.Y;
			if (FMath::Abs(Vx) < 30.f) continue;
			FVector A = L; (Axis == 0 ? A.X : A.Y) += FMath::Sign(Vx) * TriggerDistance;
			Enqueue(WorldToSection(A));
		}
		// safety: a missing neighbour close to her is generated whatever her direction
		const FIntPoint Here = WorldToSection(L);
		Enqueue(Here);
		for (int32 Dx = -1; Dx <= 1; ++Dx)
			for (int32 Dy = -1; Dy <= 1; ++Dy)
			{
				const FIntPoint C = Here + FIntPoint(Dx, Dy);
				if (IsSectionGenerated(C)) continue;
				const FIntPoint T0 = SectionMinTile(C);
				const float X0 = GridOrigin.X + T0.X * TileSize, Y0 = GridOrigin.Y + T0.Y * TileSize;
				const float Ex = FMath::Max3(X0 - (float)L.X, 0.f, (float)L.X - (X0 + SS));
				const float Ey = FMath::Max3(Y0 - (float)L.Y, 0.f, (float)L.Y - (Y0 + SS));
				if (FMath::Sqrt(Ex * Ex + Ey * Ey) < SafetyDistance) Enqueue(C);
			}
		// far runtime sections are dropped (they come back identical: same session seed; the map keeps them)
		if (UnloadSectionDistance > 0)
		{
			for (auto It = Sections.CreateIterator(); It; ++It)
			{
				if (IsStartSection(It->Key) || !It->Value || It->Value == Building) continue;
				if (FMath::Max(FMath::Abs(It->Key.X - Here.X), FMath::Abs(It->Key.Y - Here.Y)) > UnloadSectionDistance)
				{
					It->Value->Destroy(); It.RemoveCurrent(); ++SectionsRemoved;
				}
			}
		}
		UpdateDiscovery(L);
		FireTimer -= Dt;
		if (FireTimer <= 0.f && Sounds.Num() > 0) { FireTimer = 0.2f; UpdateFireLoops(L); }
	}
	// a section being built gets ~6 ms a frame; the next queued one starts when it is done
	if (Building)
	{
		if (Building->ContinueGenerate(FrameBudgetMs / 1000.0)) Building = nullptr;
		return;
	}
	while (Queue.Num() > 0)
	{
		const FIntPoint C = Queue[0]; Queue.RemoveAt(0);
		if (IsSectionGenerated(C)) continue;
		SpawnSection(C, false, true);
		break;
	}
}

// ------------------------------------------------------------------------------------------------ sound
bool ARDDungeonGenerator::HasSound(FName Key) const
{
	const FRDSoundSet* S = Sounds.Find(Key);
	return S && S->Sounds.Num() > 0;
}

USoundAttenuation* ARDDungeonGenerator::GetAttenuation(const FRDSoundSet& Set)
{
	// one attenuation object per (inner radius, falloff) pair, made when first needed
	const int32 Key = FMath::RoundToInt(Set.InnerRadius) * 100000 + FMath::RoundToInt(Set.FalloffDistance);
	if (const TObjectPtr<USoundAttenuation>* Have = Attenuations.Find(Key)) return *Have;
	USoundAttenuation* A = NewObject<USoundAttenuation>(this);
	FSoundAttenuationSettings& T = A->Attenuation;
	T.bAttenuate = true; T.bSpatialize = bSpatializeNow;
	T.DistanceAlgorithm = EAttenuationDistanceModel::NaturalSound;
	T.dBAttenuationAtMax = -40.f;
	T.AttenuationShape = EAttenuationShape::Sphere;
	T.AttenuationShapeExtents = FVector(Set.InnerRadius);
	T.FalloffDistance = Set.FalloffDistance;
	// far sounds are duller too
	T.bAttenuateWithLPF = true;
	T.LPFRadiusMin = Set.InnerRadius + Set.FalloffDistance * 0.2f; T.LPFRadiusMax = Set.InnerRadius + Set.FalloffDistance;
	T.LPFFrequencyAtMin = 20000.f; T.LPFFrequencyAtMax = 2200.f;
	Attenuations.Add(Key, A);
	return A;
}

float ARDDungeonGenerator::GetSoundLevelAt(FName Key, float Distance) const
{
	const FRDSoundSet* S = Sounds.Find(Key);
	if (!S) return 0.f;
	if (S->b2D) return 1.f;
	const USoundAttenuation* A = const_cast<ARDDungeonGenerator*>(this)->GetAttenuation(*S);
	return A->Attenuation.Evaluate(FTransform::Identity, FVector(Distance, 0, 0));
}

bool ARDDungeonGenerator::PlaySoundAt(FName Key, FVector At, float VolumeScale, float PitchScale)
{
	const FRDSoundSet* S = Sounds.Find(Key);
	UWorld* W = GetWorld();
	if (!S || S->Sounds.Num() == 0 || !W || !W->IsGameWorld()) return false;
	// one of the set, not the same twice running (a random stream of its own: sound never changes the play)
	int32& Last = LastSoundPick.FindOrAdd(Key, -1);
	int32 I = SoundR.RandRange(0, S->Sounds.Num() - 1);
	if (S->Sounds.Num() > 1 && I == Last) I = (I + 1) % S->Sounds.Num();
	Last = I;
	USoundBase* Snd = S->Sounds[I];
	if (!Snd) return false;
	const float Volume = S->Volume * VolumeScale * SoundVolume * UserVolumeOf(Key);
	const float Pitch = S->Pitch * PitchScale * (1.f + SoundR.FRandRange(-S->PitchVariation, S->PitchVariation));
	if (S->b2D) UGameplayStatics::PlaySound2D(this, Snd, Volume, Pitch);
	else UGameplayStatics::PlaySoundAtLocation(this, Snd, At, FRotator::ZeroRotator, Volume, Pitch, 0.f, GetAttenuation(*S));
	++SoundCounts.FindOrAdd(Key);
	return true;
}

TArray<FVector> ARDDungeonGenerator::GetFireLoops() const
{
	TArray<FVector> Out;
	for (const FFireVoice& V : FireVoices) if (V.bOn) Out.Add(V.At);
	return Out;
}

void ARDDungeonGenerator::UpdateFireLoops(const FVector& L)
{
	// the fires within earshot, nearest first
	struct FCand { FVector At; uint8 Kind; float D2; };
	TArray<FCand> Cands;
	const FIntPoint Here = WorldToSection(L);
	for (int32 Dx = -1; Dx <= 1; ++Dx)
		for (int32 Dy = -1; Dy <= 1; ++Dy)
			if (const ARDSection* S = GetSection(Here + FIntPoint(Dx, Dy)))
				for (const FRDFirePoint& F : S->FirePoints)
				{
					const FRDSoundSet* Set = Sounds.Find(RDFireKeys[FMath::Min<int32>(F.Kind, 2)]);
					if (!Set || Set->Sounds.Num() == 0) continue;
					const float D2 = FVector::DistSquared(F.At, L), Max = Set->InnerRadius + Set->FalloffDistance;
					if (D2 < Max * Max) Cands.Add({ F.At, F.Kind, D2 });
				}
	Cands.Sort([](const FCand& A, const FCand& B) { return A.D2 < B.D2; });
	if (Cands.Num() > FireLoopVoices) Cands.SetNum(FMath::Max(FireLoopVoices, 0));
	// a voice whose fire is no longer among them falls silent; the fires that have a voice keep it
	for (int32 I = 0; I < FireVoices.Num(); ++I)
	{
		FFireVoice& V = FireVoices[I];
		if (!V.bOn) continue;
		const int32 K = Cands.IndexOfByPredicate([&V](const FCand& C) { return C.Kind == V.Kind && C.At.Equals(V.At, 1.f); });
		if (K != INDEX_NONE) Cands.RemoveAt(K);
		else { V.bOn = false; if (FireComps[I]) FireComps[I]->FadeOut(0.3f, 0.f); }
	}
	for (const FCand& C : Cands)
	{
		int32 I = FireVoices.IndexOfByPredicate([](const FFireVoice& V) { return !V.bOn; });
		if (I == INDEX_NONE)
		{
			if (FireVoices.Num() >= FireLoopVoices) break;
			UAudioComponent* A = NewObject<UAudioComponent>(this);
			A->bAutoActivate = false; A->bAutoDestroy = false; A->bAllowSpatialization = bSpatializeNow;
			A->SetupAttachment(RootComponent);
			A->RegisterComponent();
			FireComps.Add(A);
			I = FireVoices.AddDefaulted();
		}
		const FRDSoundSet& Set = Sounds[RDFireKeys[FMath::Min<int32>(C.Kind, 2)]];
		USoundBase* Snd = Set.Sounds[SoundR.RandRange(0, Set.Sounds.Num() - 1)];
		UAudioComponent* A = FireComps[I];
		if (!Snd || !A) continue;
		A->Stop();
		A->SetWorldLocation(C.At);
		A->SetSound(Snd);
		A->AttenuationSettings = GetAttenuation(Set);
		A->SetVolumeMultiplier(Set.Volume * SoundVolume * UserVolumeOf(RDFireKeys[0]));
		A->SetPitchMultiplier(Set.Pitch * (1.f + SoundR.FRandRange(-Set.PitchVariation, Set.PitchVariation)));
		// (each fire starts somewhere else in its loop, or two torches side by side would beat as one)
		const USoundWave* Wave = Cast<USoundWave>(Snd);
		A->Play(Wave ? SoundR.FRandRange(0.f, FMath::Max(0.f, Wave->Duration - 0.5f)) : 0.f);
		FireVoices[I] = { C.At, C.Kind, true };
	}
}

FString ARDDungeonGenerator::DescribeListener() const
{
	FAudioDeviceHandle AD = GetWorld() ? GetWorld()->GetAudioDevice() : FAudioDeviceHandle();
	if (!AD) return TEXT("no audio device");
	FVector L = FVector::ZeroVector, A = FVector::ZeroVector;
	const bool bL = AD->GetListenerPosition(0, L, false), bA = AD->GetListenerPosition(0, A, true);
	return FString::Printf(TEXT("device %u%s: listener %s(%.0f, %.0f, %.0f), attenuation point %s(%.0f, %.0f, %.0f), %d voices"), AD.GetDeviceID(), AD->IsMainAudioDevice() ? TEXT(" (main)") : TEXT(""),
		bL ? TEXT("") : TEXT("none "), L.X, L.Y, L.Z, bA ? TEXT("") : TEXT("none "), A.X, A.Y, A.Z, AD->GetMaxChannels());
}

void ARDDungeonGenerator::SetUnfocusedVolume(float Multiplier)
{
	FApp::SetUnfocusedVolumeMultiplier(Multiplier);
}

// ------------------------------------------------------------------------------------------------ music and atmosphere
FString ARDDungeonGenerator::MusicLayerName(int32 Layer) const
{
	const UAudioComponent* A = MusicComps.IsValidIndex(Layer) ? MusicComps[Layer].Get() : nullptr;
	return A && A->Sound && A->IsPlaying() ? A->Sound->GetName() : FString();
}

void ARDDungeonGenerator::StopMusic()
{
	for (UAudioComponent* A : MusicComps) if (A) A->Stop();
	for (int32 I = 0; I < 4; ++I) { MusicPos[I] = 0.f; MusicIndex[I] = 0; }
	bMusicOn = bCombatMusic = false; LastFightTime = -100.f; MusicShifts = 0;
	MusicSceneKey = NAME_None; MusicRotateAt = -1.f; MusicPendingAt = -1.f;
}

FName ARDDungeonGenerator::MusicSceneFor() const
{
	// (the town's walls by day and by night, the wilds by day and by night; the castle and the other levels: Music.Explore)
	static const FName Explore(TEXT("Music.Explore"));
	if (!bTown) return Explore;
	const APawn* P = UGameplayStatics::GetPlayerPawn(this, 0);
	const bool bNight = DayLight < 0.3f;
	const bool bWilds = bWild && P && IsWildReady() && !IsInTownWalls(P->GetActorLocation());
	FName K(bWilds ? (bNight ? TEXT("Music.WildNight") : TEXT("Music.Wild")) : (bNight ? TEXT("Music.TownNight") : TEXT("Music.Town")));
	if (!Sounds.Contains(K)) K = FName(bWilds ? TEXT("Music.Wild") : TEXT("Music.Town"));
	return Sounds.Contains(K) ? K : Explore;
}

void ARDDungeonGenerator::StartMusicLayer(int32 Layer, float FadeSeconds, bool bFromStart)
{
	// (the wandering music: the scene's set (the list of 2026-11-04: the town's by day and by night, the wilds'), else the
	// level's Music.Explore)
	const FName Key = (Layer == 0 && !MusicSceneKey.IsNone() && Sounds.Contains(MusicSceneKey)) ? MusicSceneKey : RDMusicKeys[Layer];
	const FRDSoundSet* Set = Sounds.Find(Key);
	if (!Set || Set->Sounds.Num() == 0) return;
	USoundBase* Snd = Set->Sounds[MusicIndex[Layer] % Set->Sounds.Num()];
	if (!Snd) return;
	if (MusicComps.Num() < 4) MusicComps.SetNum(4);
	if (!MusicComps[Layer])
	{
		UAudioComponent* A = NewObject<UAudioComponent>(this);
		A->bAutoActivate = false; A->bAutoDestroy = false; A->bAllowSpatialization = false;
		A->SetupAttachment(RootComponent);
		A->RegisterComponent();
		MusicComps[Layer] = A;
	}
	// from its start, or on from where this layer was when it last played
	if (bFromStart) MusicPos[Layer] = 0.f;
	const USoundWave* Wave = Cast<USoundWave>(Snd);
	const float Start = Wave && Wave->Duration > 1.f ? FMath::Fmod(MusicPos[Layer], Wave->Duration) : 0.f;
	UAudioComponent* A = MusicComps[Layer];
	A->SetSound(Snd);
	A->SetPitchMultiplier(Set->Pitch);
	A->SetVolumeMultiplier(UserVolumeOf(RDMusicKeys[Layer]));        // (the player's volumes: the menu changes it as it plays)
	A->FadeIn(FadeSeconds, Set->Volume * MusicVolume, Start);
}

void ARDDungeonGenerator::TickMusic(float Dt)
{
	if (!bMusicOn)
	{
		// which wandering track this session has, and which battle track comes first: by the session seed
		bool bAny = false;
		for (const FName& K : RDMusicKeys) bAny |= HasSound(K);
		if (!bAny || !PlayerCombat) return;
		bMusicOn = true; bCombatMusic = false;
		MusicIndex[0] = MusicIndex[1] = FMath::Abs(SessionSeed % 1000);
		MusicSceneKey = MusicSceneFor(); MusicRotateAt = -1.f; MusicPendingAt = -1.f;
		StartMusicLayer(0, 1.5f, true); StartMusicLayer(2, 1.5f, true);
	}
	const float Now = GetWorld()->GetTimeSeconds();
	// (the list of 2026-11-04: "the music should change every so often. after 5-10 minutes, the music should change to another
	// appropriate song for the scene the player is in": a time of its own for each track, from the session's seed; and at
	// once when the scene changes (out of the town's walls, the night falling). The track fades out and the next fades in)
	if (MusicRotateAt < 0.f)
	{
		const uint32 H = HashCombine((uint32)SessionSeed ^ 0x3A51u, (uint32)MusicRotations * 2654435761u);
		MusicRotateAt = Now + FMath::Lerp(MusicRotateSeconds.X, MusicRotateSeconds.Y, (H % 1000u) / 999.f);
	}
	// (Brokenspire, its wilds and the castle only (the PR review's find: every dungeon level's music rotated too); a fight begun
	// in the fade-out leaves the new track to start from its beginning when the fight is over, not at the old one's place)
	const bool bRotate = bTown || bTownLink;
	if (MusicPendingAt > 0.f && Now >= MusicPendingAt)
	{
		MusicPendingAt = -1.f; MusicPos[0] = 0.f;
		if (!bCombatMusic) StartMusicLayer(0, 3.f, true);
	}
	else if (bRotate && MusicPendingAt < 0.f && !bCombatMusic)
	{
		const FName Scene = MusicSceneFor();
		if (Scene != MusicSceneKey || Now >= MusicRotateAt)
		{
			const bool bScene = Scene != MusicSceneKey;
			MusicSceneKey = Scene; ++MusicIndex[0]; ++MusicRotations;
			if (MusicComps.IsValidIndex(0) && MusicComps[0]) MusicComps[0]->FadeOut(3.f, 0.f);
			MusicPendingAt = Now + 3.1f;
			const uint32 H = HashCombine((uint32)SessionSeed ^ 0x3A51u, (uint32)MusicRotations * 2654435761u);
			MusicRotateAt = Now + 3.1f + FMath::Lerp(MusicRotateSeconds.X, MusicRotateSeconds.Y, (H % 1000u) / 999.f);
			UE_LOG(LogRandomDungeonGen, Log, TEXT("RDMUSIC %s: the next track of %s (%d)"), bScene ? TEXT("a new scene") : TEXT("its time"), *Scene.ToString(), MusicRotations);
		}
	}
	// a fight is on: blows fell a moment ago, or a monster near her is after her
	bool bFight = false;
	if (PlayerCombat && PlayerCombat->GetOwner() && !PlayerCombat->IsDead())
	{
		bFight = Now - PlayerCombat->LastHurtTime < 1.f || Now - PlayerCombat->LastHitTime < 1.f;
		const FVector L = PlayerCombat->GetOwner()->GetActorLocation();
		for (const auto& KV : Sections)
		{
			if (bFight || !KV.Value) continue;
			for (const ARDMonster* M : KV.Value->SpawnedMonsters)
				if (M && !M->IsDead() && M->IsAggro() && FVector::DistSquared(M->GetActorLocation(), L) < FMath::Square(CombatMusicDistance)) { bFight = true; break; }
		}
	}
	if (bFight) LastFightTime = Now;
	const bool bWant = Now - LastFightTime < CombatMusicHold;
	if (bWant != bCombatMusic)
	{
		// the pair that was playing fades out (quickly into a fight, slowly out of one) and the other comes in
		for (const int32 Layer : { bCombatMusic ? 1 : 0, bCombatMusic ? 3 : 2 })
			if (MusicComps.IsValidIndex(Layer) && MusicComps[Layer]) MusicComps[Layer]->FadeOut(bWant ? 0.8f : 2.5f, 0.f);
		bCombatMusic = bWant; ++MusicShifts;
		if (bWant) { StartMusicLayer(1, 0.35f, true); StartMusicLayer(3, 0.8f, true); }
		else { ++MusicIndex[1]; StartMusicLayer(0, 2.5f, false); StartMusicLayer(2, 2.5f, false); }      // (the next fight: the next battle track)
		UE_LOG(LogRandomDungeonGen, Log, TEXT("RDMUSIC %s: %s over %s"), bWant ? TEXT("battle") : TEXT("wandering"), *GetMusicTrack(), *GetAtmosphereTrack());
	}
	MusicPos[bCombatMusic ? 1 : 0] += Dt; MusicPos[bCombatMusic ? 3 : 2] += Dt;
}

// ------------------------------------------------------------------------------------------------ sound self test
// -RDSoundTest=<dir> (a game or play-in-editor session): records what the audio device puts out while one flat sound and
// the same placed sound at known places round her are played, writes <dir>/soundtest.wav and soundtest.txt, and quits.
// The recording shows what nobody can check by counting calls: that a placed sound is there at all, louder in the ear
// on its side, and quieter the farther it is.
void ARDDungeonGenerator::TickSoundTest(float Dt)
{
	APlayerController* PC = UGameplayStatics::GetPlayerController(this, 0);
	APawn* P = PC ? PC->GetPawn() : nullptr;
	if (!P || !PlayerCombat) return;
	struct FStep { float T; const TCHAR* What; const TCHAR* Key; float Forward, Right; };
	static const FStep Steps[] = {
		{ 1.0f, TEXT("flat"), TEXT("Player.Hurt"), 0.f, 0.f },
		{ 2.5f, TEXT("2 m ahead of her"), TEXT("Monster.Troll.Hurt"), 200.f, 0.f },
		{ 4.0f, TEXT("4 m to her right"), TEXT("Monster.Troll.Hurt"), 0.f, 400.f },
		{ 5.5f, TEXT("4 m to her left"), TEXT("Monster.Troll.Hurt"), 0.f, -400.f },
		{ 7.0f, TEXT("12 m ahead"), TEXT("Monster.Troll.Hurt"), 1200.f, 0.f },
		{ 8.5f, TEXT("25 m ahead"), TEXT("Monster.Troll.Hurt"), 2500.f, 0.f },
		{ 10.0f, TEXT("flat again"), TEXT("Player.Hurt"), 0.f, 0.f },
	};
	const int32 NumSteps = UE_ARRAY_COUNT(Steps);
	if (SoundTestStep < 0)
	{
		// (a few seconds for the level to settle)
		SoundTestTime += Dt;
		if (SoundTestTime < 5.f) return;
		// The wandering atmosphere (a low room tone) runs under the test. Without anything playing, the engine stops
		// processing the silent submix and the recording simply has no audio for those stretches: it came out up to three
		// seconds shorter than the test, with every sound earlier than its logged time.
		StartMusicLayer(2, 0.2f, true);
		FApp::SetUnfocusedVolumeMultiplier(1.f);
		PlayerCombat->SetScriptedOnly(true);
		UAudioMixerBlueprintLibrary::StartRecordingOutput(this, 20.f, nullptr);
		SoundTestStep = 0; SoundTestTime = 0.f;
		// (the steps are logged on the audio device's own clock, counted in the audio it has rendered: the recording's time.
		// The game's clock runs ahead of it whenever the device falls behind, and did by more than a second.)
		if (FAudioDeviceHandle AD = GetWorld()->GetAudioDevice()) SoundTestClock = AD->GetAudioClock();
		SoundTestLog.Add(FString::Printf(TEXT("sound test: %d sets, master %.2f, spatialised %d, %s"), Sounds.Num(), SoundVolume, bSpatializeNow ? 1 : 0, *DescribeListener()));
		return;
	}
	SoundTestTime += Dt;
	FAudioDeviceHandle Device = GetWorld()->GetAudioDevice();
	const float Heard = Device ? (float)(Device->GetAudioClock() - SoundTestClock) : SoundTestTime;
	FVector Cam; FRotator CamRot;
	PC->GetPlayerViewPoint(Cam, CamRot);
	const FVector Fw = FRotator(0, CamRot.Yaw, 0).Vector(), Rt = FRotator(0, CamRot.Yaw + 90.f, 0).Vector(), L = P->GetActorLocation();
	while (SoundTestStep < NumSteps && SoundTestTime >= Steps[SoundTestStep].T)
	{
		const FStep& St = Steps[SoundTestStep++];
		const FVector At = L + Fw * St.Forward + Rt * St.Right;
		const FRDSoundSet* Set = Sounds.Find(St.Key);
		if (!Set || Set->Sounds.Num() == 0 || !Set->Sounds[0]) { SoundTestLog.Add(FString::Printf(TEXT("%.2f | %s | %s | no such sound"), Heard, St.What, St.Key)); continue; }
		// (always the set's first sound at its own pitch: the levels of the steps can be compared)
		if (Set->b2D) UGameplayStatics::PlaySound2D(this, Set->Sounds[0], Set->Volume * SoundVolume, Set->Pitch);
		else UGameplayStatics::PlaySoundAtLocation(this, Set->Sounds[0], At, FRotator::ZeroRotator, Set->Volume * SoundVolume, Set->Pitch, 0.f, GetAttenuation(*Set));
		SoundTestLog.Add(FString::Printf(TEXT("%.2f | %s | %s | level by distance %.3f | game clock %.2f"), Heard, St.What, St.Key, GetSoundLevelAt(St.Key, FVector::Dist(At, L)), SoundTestTime));
	}
	if (SoundTestStep == NumSteps && SoundTestTime >= 12.f)
	{
		UAudioMixerBlueprintLibrary::StopRecordingOutput(this, EAudioRecordingExportType::WavFile, TEXT("soundtest"), SoundTestDir, nullptr, nullptr);
		SoundTestLog.Add(FString::Printf(TEXT("%.2f | end | %s | game clock %.2f"), Heard, *DescribeListener(), SoundTestTime));
		FFileHelper::SaveStringArrayToFile(SoundTestLog, *(SoundTestDir / TEXT("soundtest.txt")));
		++SoundTestStep;
	}
	if (SoundTestStep > NumSteps && SoundTestTime >= 14.f)
	{
		UE_LOG(LogRandomDungeonGen, Log, TEXT("RDSOUNDTEST done -> %s"), *SoundTestDir);
		SoundTestDir.Reset();
		if (!GIsEditor) FPlatformMisc::RequestExit(false);
	}
}
