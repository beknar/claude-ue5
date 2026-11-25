// The game saved to disk (RDSave.h): written by the generator (SaveGameNow, WildAutosave), read back by the Escape menu's Load
// page or the hero menu's CONTINUE (URDSaveGame::LoadAndOpen); she is put back where she was once the level has loaded
// (TickTown for Brokenspire itself, TickWild for the wilderness and the other towns).
#include "RD/RDSave.h"
#include "RD/RDDungeonGenerator.h"
#include "RD/RDGameInstance.h"
#include "RD/RDCombat.h"
#include "RD/RDSection.h"
#include "Kismet/GameplayStatics.h"
#include "Serialization/MemoryWriter.h"
#include "Serialization/MemoryReader.h"
#include "Serialization/ObjectAndNameAsStringProxyArchive.h"
#include "GameFramework/Character.h"
#include "GameFramework/CharacterMovementComponent.h"
#include "HAL/PlatformTime.h"
#include "HAL/FileManager.h"
#include "Misc/Paths.h"
#include "Engine/World.h"

DEFINE_LOG_CATEGORY_STATIC(LogRDSave, Log, All);

namespace
{
	void RDSerializeGame(URDGameInstance* GI, TArray<uint8>& Bytes, bool bLoad)
	{
		if (bLoad)
		{
			FMemoryReader R(Bytes, true);
			FObjectAndNameAsStringProxyArchive Ar(R, true); Ar.ArIsSaveGame = true; Ar.ArNoDelta = true;
			// (a save made before the caves' records holds none of them: the session's own must not stay (PR #121's review))
			GI->LiftedRelics16.Reset(); GI->LostBladeCaves16.Reset(); GI->DrownedCaves16.Reset(); GI->Paintings16.Reset(); GI->PaintingsApplied16.Reset(); GI->KnownCaves16.Reset(); GI->CaveMaps16.Reset(); GI->ContractsInCave16.Reset(); GI->RescuedTravellers16.Reset(); GI->CaveMouthsAttuned16.Reset(); GI->TowerKeys16.Reset(); GI->TowersClimbed16.Reset(); GI->TowerChests16.Reset();
			GI->Serialize(Ar);
		}
		else
		{
			FMemoryWriter W(Bytes, true);
			FObjectAndNameAsStringProxyArchive Ar(W, false); Ar.ArIsSaveGame = true; Ar.ArNoDelta = true;
			GI->Serialize(Ar);
		}
	}
}

bool ARDDungeonGenerator::SaveGameNow(const FString& Slot, const FString& Why, const FString& Name)
{
	URDGameInstance* GI = URDGameInstance::Of(this);
	APawn* Her = UGameplayStatics::GetPlayerPawn(this, 0);
	if (!GI || !Her || !(bTown || bTownLink)) return false;
	if (PlayerCombat && PlayerCombat->IsDead()) return false;
	const double T0 = FPlatformTime::Seconds();
	// what the level keeps goes into the game instance (as before the Mistgate), on a copy of the fields it touches: the game
	// goes on with them as they were
	const TArray<FRDCarry> Piles = GI->HerPiles;
	const TArray<int32> Looted = GI->TownLooted, Guards = GI->GuardsDead;
	const TMap<FString, FRDTownSave> Store = GI->TownStore;
	const FString Current = GI->CurrentTown;
	SaveCarry();
	FString Place = bTown ? TownName : !DungeonTitle.IsEmpty() ? DungeonTitle : FString(TEXT("Mistward Castle"));
	if (bTown && bWild && IsWildReady())
	{
		GI->WildRevealKeys.Reset(); GI->WildRevealBits.Reset();
		for (const auto& Kv : WildRevealed) { GI->WildRevealKeys.Add(Kv.Key); for (const uint64 B : Kv.Value) GI->WildRevealBits.Add((int64)B); }
		GI->WildFound = WildFound.Array();
		// (the town loaded is the game instance's current town; the level starts with Brokenspire: its state goes in the
		// fields Brokenspire reads, the others' in the store)
		if (GetSection(FIntPoint::ZeroValue)) SaveTownState();
		if (!bTownHome)
		{
			const FRDTownSave* B = GI->TownStore.Find(HomeTownName);
			GI->TownLooted = B ? B->Looted : TArray<int32>(); GI->GuardsDead = B ? B->GuardsDead : TArray<int32>();
			GI->CurrentTown = HomeTownName;
		}
		if (!IsInTownWalls(Her->GetActorLocation()))
		{
			FRDWSample S; Wild->Sample(Her->GetActorLocation().X / 100.0, Her->GetActorLocation().Y / 100.0, S, false);
			double Dt; const int32 Ti = Wild->NearestTown(Her->GetActorLocation().X / 100.0, Her->GetActorLocation().Y / 100.0, Dt);
			Place = FString::Printf(TEXT("the wilds: %s, %.0f km from %s"), *Wild->BiomeName(S.Biome), Dt / 1000.0, Ti >= 0 ? *Wild->Towns[Ti].Name : TEXT("anywhere"));
		}
	}
	if (bTown) { GI->TownHour = TownHour; GI->TownDay = TownDay; }
	URDSaveGame* Sv = Cast<URDSaveGame>(UGameplayStatics::CreateSaveGameObject(URDSaveGame::StaticClass()));
	Sv->SavedAt = FDateTime::Now();
	Sv->Level = UWorld::RemovePIEPrefix(GetWorld()->GetOutermost()->GetName());
	Sv->Hero = CurrentHero; Sv->At = Her->GetActorLocation(); Sv->Yaw = Her->GetActorRotation().Yaw;
	Sv->Why = Why; Sv->Place = Place; Sv->bInTown = bTown; Sv->Name = Name;
	// (the list of 2026-11-16: the world it was made in; an older world's give-back still waiting (loaded in the castle, saved there)
	// done first, so what is written is whole (PR #89's review))
	if (GI->bOldWorld) GiveBackWildQuests14();
	Sv->WorldVer = URDSaveGame::WorldVersion;
	RDSerializeGame(GI, Sv->Game, false);
	// (the game goes on as it was)
	GI->HerPiles = Piles; GI->TownLooted = Looted; GI->GuardsDead = Guards; GI->TownStore = Store; GI->CurrentTown = Current;
	const bool bOk = UGameplayStatics::SaveGameToSlot(Sv, Slot, 0);
	LastSaveTime = GetWorld()->GetTimeSeconds(); LastSaveRealTime = FPlatformTime::Seconds(); LastSaveReveal = WildRevealVersion; ++SavesWritten; LastSaveSlot = Slot; LastSaveWhy = Why;
	UE_LOG(LogRDSave, Log, TEXT("RDSAVE %s (%s): %s, %s, %d bytes, %.1f ms, %s"), *Slot, *Why, *Sv->Level, *Place, Sv->Game.Num(), (FPlatformTime::Seconds() - T0) * 1000.0, bOk ? TEXT("ok") : TEXT("FAILED"));
	return bOk;
}

void ARDDungeonGenerator::WildAutosave(const FString& Why)
{
	if (!bAutosave) return;
	// (a moment between two: finding places one after another writes once; a journey's two are kept)
	const float Now = GetWorld()->GetTimeSeconds();
	const bool bForce = Why.Contains(TEXT("travel")) || Why == TEXT("quit") || Why == TEXT("castle") || Why == TEXT("catacombs");
	if (!bForce && SavesWritten > 0 && Now - LastSaveTime < 8.f) return;
	SaveGameNow(TEXT("autosave"), Why);
}

bool ARDDungeonGenerator::LoadGameFrom(const FString& Slot)
{
	if (bMenuDryRun) { LastMenuAction = TEXT("load ") + Slot; return UGameplayStatics::DoesSaveGameExist(Slot, 0); }
	// (a slot with no save, or one that cannot be read: said, and the menu stays open)
	if (URDSaveGame::Info(Slot).IsEmpty())
	{
		if (PlayerCombat) PlayerCombat->ShowMessage(Slot == TEXT("autosave") ? TEXT("There is no autosave to load") : TEXT("There is no saved game to load"));
		return false;
	}
	SetMenuOpen(false);
	if (URDSaveGame::LoadAndOpen(this, Slot)) return true;
	if (PlayerCombat) PlayerCombat->ShowMessage(TEXT("The game could not be loaded"));
	return false;
}

FString ARDDungeonGenerator::GetSaveInfo(const FString& Slot) const
{
	// (read again a second after the last read, or after a save)
	const double Now = FPlatformTime::Seconds();
	if (const TPair<double, FString>* C = SaveInfoCache.Find(Slot); C && Now - C->Key < 1.0 && C->Key > LastSaveRealTime) return C->Value;
	const FString I = URDSaveGame::Info(Slot);
	SaveInfoCache.Add(Slot, TPair<double, FString>(Now, I));
	return I;
}

void ARDDungeonGenerator::TickWildLoad()
{
	// (a game loaded: once the world is made, she is put back where she was: in another town (loaded now), or out in the wilds)
	URDGameInstance* GI = URDGameInstance::Of(this);
	if (!GI || !GI->bLoadPending || !IsWildReady()) return;
	GI->bLoadPending = false;
	APawn* Her = UGameplayStatics::GetPlayerPawn(this, 0);
	if (!Her) return;
	const FVector At = GI->LoadAt;
	double Dt; const int32 Ti = Wild->NearestTown(At.X / 100.0, At.Y / 100.0, Dt);
	// (each town its own size: Vel Morrath is the home town's, the others small)
	const double Half = (Ti == 0 ? HomeSectionTiles : Ti > 0 && Wild->Towns[Ti].Tiles > 0 ? Wild->Towns[Ti].Tiles : WildSmallTownTiles) * TileSize / 200.0;
	// (in its square, not a circle round its middle: a save in a town's corner was put out in the wilds, the town built
	// round her after)
	const bool bInSquare = Ti >= 0 && FMath::Max(FMath::Abs(At.X / 100.0 - Wild->Towns[Ti].Site.X), FMath::Abs(At.Y / 100.0 - Wild->Towns[Ti].Site.Y)) < Half + 50.0;
	if (Ti > 0 && bInSquare)
	{
		WildDropAll(); LoadWildTown(Ti, true);
		Her->SetActorLocation(FVector(At.X, At.Y, 120.0), false, nullptr, ETeleportType::TeleportPhysics);
	}
	else if (Ti != 0 || !bInSquare) WildPutHer(At.X / 100.0, At.Y / 100.0);
	else Her->SetActorLocation(FVector(At.X, At.Y, 120.0), false, nullptr, ETeleportType::TeleportPhysics);
	if (APlayerController* PC = UGameplayStatics::GetPlayerController(this, 0)) PC->SetControlRotation(FRotator(-10.f, GI->LoadYaw, 0.f));
	Her->SetActorRotation(FRotator(0.f, GI->LoadYaw, 0.f));
	if (ACharacter* Ch = Cast<ACharacter>(Her)) Ch->GetCharacterMovement()->StopMovementImmediately();
	++LoadsArrived;
	UE_LOG(LogRDSave, Log, TEXT("RDSAVE loaded: she is back at (%.0f, %.0f)"), At.X, At.Y);
}

// ------------------------------------------------------------------------------------------------ reading a save
bool URDSaveGame::LoadAndOpen(UObject* Ctx, const FString& Slot)
{
	URDGameInstance* GI = URDGameInstance::Of(Ctx);
	URDSaveGame* Sv = Cast<URDSaveGame>(UGameplayStatics::LoadGameFromSlot(Slot, 0));
	if (!GI || !Sv || Sv->Game.Num() == 0 || Sv->Level.IsEmpty()) return false;
	RDSerializeGame(GI, Sv->Game, true);
	GI->GameHero = Sv->Hero; GI->GamesStarted = FMath::Max(GI->GamesStarted, 1);
	// (put back where she was only in a town's level: the castle reads none of it, and a flag left set there moved her to
	// the castle's coordinates out in the wilds once she came back)
	GI->Arrive = Sv->bInTown ? TEXT("save") : FString(); GI->LoadAt = Sv->At; GI->LoadYaw = Sv->Yaw; GI->bLoadPending = Sv->bInTown;
	// (the list of 2026-11-16's eleventh phase: a save of an older world (the continent at 300 km, its places' ids by its old frame):
	// its wild state dropped; made in the wilds' level, she wakes in Brokenspire's square (TickTown with nothing to arrive by))
	GI->bOldWorld = false;          // (a flag left from an earlier load is no business of this one: PR #89's review)
	if (Sv->WorldVer < WorldVersion)
	{
		DropOldWorld(GI, Sv->WorldVer);
		if (Sv->bInTown) { GI->Arrive.Reset(); GI->bLoadPending = false; }
	}
	UE_LOG(LogRDSave, Log, TEXT("RDSAVE loading %s: %s as %s (%s)"), *Slot, *Sv->Level, *Sv->Hero.ToString(), *Sv->Place);
	UGameplayStatics::OpenLevel(Ctx, FName(*Sv->Level), true, FString::Printf(TEXT("Hero=%s"), *Sv->Hero.ToString()));
	return true;
}

void URDSaveGame::DropOldWorld(URDGameInstance* GI, int32 FromVersion)
{
	if (!GI) return;
	GI->WildRevealKeys.Reset(); GI->WildRevealBits.Reset(); GI->WildFound.Reset(); GI->WildKilled.Reset();
	GI->WildMarked15.Reset(); GI->WildLookoutsClimbed15.Reset(); GI->RoamersSeen15.Reset(); GI->RoamersSlain15.Reset(); GI->CollectiblesTaken15.Reset(); GI->TreasureMapsTaken15.Reset(); GI->TreasureMaps15.Reset(); GI->TreasuresDug15.Reset(); GI->ContractSigns15.Reset(); GI->CampsCleared15.Reset(); GI->CampsClearedDay15.Reset(); GI->CampsResettledFrom15.Reset(); GI->RuinsResettled15.Reset(); GI->ReclaimKeys15.Reset(); GI->WaystonesLit15.Reset();          // (the waystones' ids are the old world's cells)          // (the camps' and ruins' ids are the old world's places)          // (a contract's id is its town's and slot's: taken, done and paid stay; its signs' places moved)          // (the old world's ids; what she bought stays)          // (the list of 2026-11-20's tenth phase: the lookouts' marks, by the old ids)
	// (the structures' quests (wq12:<site>...) by the old places' ids, the captain's (wild:...) by the old places: their counters gone;
	// the captain's quests given back to him (StartWild, which has the quests' table: bOldWorld))
	TArray<FString> Gone;
	for (const TPair<FString, int32>& C : GI->Counters) if (C.Key.StartsWith(TEXT("wq12:")) || C.Key.StartsWith(TEXT("wild:"))) Gone.Add(C.Key);
	for (const FString& K : Gone) GI->Counters.Remove(K);
	// (a way back from a city's dungeon to the old city's gate: home to Brokenspire instead)
	GI->ReturnAt = FVector::ZeroVector; GI->ReturnTown.Reset(); GI->ForgetTower24();          // (a load in the tower builds it from its default seed (PR #131's review))
	GI->bOldWorld = true;
	UE_LOG(LogRDSave, Log, TEXT("RDSAVE a save of the world's version %d (now %d): its wild state dropped (%d counters)"), FromVersion, WorldVersion, Gone.Num());
}

bool URDSaveGame::ReadHead(const FString& Slot, FString& OutInfo, FDateTime& OutSavedAt)
{
	// (the hero menu asks every 2 s: each ask loaded and deserialized both slots, which grow with the map revealed; a slot is
	// read again only when its file's timestamp changes)
	struct FHead { FDateTime Stamp; FString Info; FDateTime SavedAt; bool bOk = false; };
	static TMap<FString, FHead> Cache;
	const FString Path = FPaths::ProjectSavedDir() / TEXT("SaveGames") / (Slot + TEXT(".sav"));
	const FDateTime Stamp = IFileManager::Get().GetTimeStamp(*Path);
	if (Stamp == FDateTime::MinValue()) { Cache.Remove(Slot); return false; }
	FHead& H = Cache.FindOrAdd(Slot);
	if (H.Stamp != Stamp)
	{
		H = FHead(); H.Stamp = Stamp;
		if (const URDSaveGame* Sv = Cast<URDSaveGame>(UGameplayStatics::LoadGameFromSlot(Slot, 0)); Sv && Sv->Game.Num() > 0 && !Sv->Level.IsEmpty())
		{
			FString Lv = Sv->Level; int32 Sl; if (Lv.FindLastChar(TEXT('/'), Sl)) Lv = Lv.Mid(Sl + 1);
			H.Info = FString::Printf(TEXT("%s|%s|%s|%s|%s|%s"), *Sv->SavedAt.ToString(TEXT("%Y-%m-%d %H:%M")), *Lv, *Sv->Place, *Sv->Hero.ToString(), *Sv->Why, *Sv->Name.Replace(TEXT("|"), TEXT(" ")));
			H.SavedAt = Sv->SavedAt; H.bOk = true;
		}
	}
	OutInfo = H.Info; OutSavedAt = H.SavedAt;
	return H.bOk;
}

FString URDSaveGame::Info(const FString& Slot)
{
	FString I; FDateTime T;
	return ReadHead(Slot, I, T) ? I : FString();
}

FString URDSaveGame::Latest()
{
	const TArray<FString> All = AllSlots();
	return All.Num() > 0 ? All[0] : FString();
}

TArray<FString> URDSaveGame::AllSlots()
{
	// (the autosave, the old "save" and every named "save_<name>" in the save folder, newest first)
	TArray<FString> Files;
	IFileManager::Get().FindFiles(Files, *(FPaths::ProjectSavedDir() / TEXT("SaveGames") / TEXT("*.sav")), true, false);
	TArray<TPair<FDateTime, FString>> Got;
	for (const FString& F : Files)
	{
		const FString Slot = FPaths::GetBaseFilename(F);
		if (Slot != TEXT("autosave") && Slot != TEXT("save") && !Slot.StartsWith(TEXT("save_"))) continue;
		FString I; FDateTime T;
		if (ReadHead(Slot, I, T)) Got.Add({ T, Slot });
	}
	Got.Sort([](const TPair<FDateTime, FString>& A, const TPair<FDateTime, FString>& B) { return A.Key > B.Key; });
	TArray<FString> Out;
	for (const auto& G : Got) Out.Add(G.Value);
	return Out;
}

FString ARDDungeonGenerator::SlotForName(const FString& Name)
{
	FString S;
	for (const TCHAR C : Name.ToLower()) { if (FChar::IsAlnum(C)) S.AppendChar(C); else if ((C == TEXT(' ') || C == TEXT('-') || C == TEXT('_')) && !S.EndsWith(TEXT("_"))) S.AppendChar(TEXT('_')); }
	S.RemoveFromEnd(TEXT("_"));
	// (and the name's own hash: names that differ only in case or punctuation ("Brokenspire day 3", "brokenspire-day-3") are
	// two saves, and a name of punctuation alone never takes the old "save" slot (the PR review's find); the same name, the
	// same slot)
	const uint32 H = FCrc::StrCrc32(*Name.TrimStartAndEnd());
	return FString(TEXT("save_")) + (S.IsEmpty() ? FString() : S.Left(40) + TEXT("_")) + FString::Printf(TEXT("%06x"), H & 0xFFFFFFu);
}

TArray<FString> ARDDungeonGenerator::GetSaveSlots() const
{
	// (read again a second after the last read, or after a save)
	const double Now = FPlatformTime::Seconds();
	if (Now - SaveSlotsAt < 1.0 && SaveSlotsAt > LastSaveRealTime) return SaveSlotsCache;
	SaveSlotsAt = Now;
	SaveSlotsCache.Reset();
	for (const FString& Slot : URDSaveGame::AllSlots())
	{
		TArray<FString> P; URDSaveGame::Info(Slot).ParseIntoArray(P, TEXT("|"), false);
		if (P.Num() < 4) continue;
		const FString Nm = P.Num() >= 6 && !P[5].IsEmpty() ? P[5] : (Slot == TEXT("autosave") ? FString(TEXT("Autosave")) : FString(TEXT("Saved game")));
		SaveSlotsCache.Add(FString::Printf(TEXT("%s|%s|%s|%s|%s"), *Slot, *Nm, *P[0], *P[2], *P[3]));
	}
	return SaveSlotsCache;
}
