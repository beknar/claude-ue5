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

bool ARDDungeonGenerator::SaveGameNow(const FString& Slot, const FString& Why)
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
	FString Place = bTown ? TownName : FString(TEXT("Mistward Castle"));
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
	Sv->Why = Why; Sv->Place = Place; Sv->bInTown = bTown;
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
	const bool bForce = Why.Contains(TEXT("travel")) || Why == TEXT("quit") || Why == TEXT("castle");
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
	const double Half = (Ti == 0 ? HomeSectionTiles : WildSmallTownTiles) * TileSize / 200.0;
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
	UE_LOG(LogRDSave, Log, TEXT("RDSAVE loading %s: %s as %s (%s)"), *Slot, *Sv->Level, *Sv->Hero.ToString(), *Sv->Place);
	UGameplayStatics::OpenLevel(Ctx, FName(*Sv->Level), true, FString::Printf(TEXT("Hero=%s"), *Sv->Hero.ToString()));
	return true;
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
			H.Info = FString::Printf(TEXT("%s|%s|%s|%s|%s"), *Sv->SavedAt.ToString(TEXT("%Y-%m-%d %H:%M")), *Lv, *Sv->Place, *Sv->Hero.ToString(), *Sv->Why);
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
	FString Best; FDateTime Bt = FDateTime::MinValue();
	for (const TCHAR* S : { TEXT("save"), TEXT("autosave") })
	{
		FString I; FDateTime T;
		if (ReadHead(S, I, T) && T > Bt) { Bt = T; Best = S; }
	}
	return Best;
}
