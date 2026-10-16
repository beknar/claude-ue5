#include "RD/RDDungeonGenerator.h"
#include "RD/RDSection.h"
#include "RD/RDMonster.h"
#include "RD/RDCombat.h"
#include "RD/RDBlood.h"
#include "AudioDevice.h"
#include "AudioMixerBlueprintLibrary.h"
#include "Misc/CommandLine.h"
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
#include "Kismet/GameplayStatics.h"
#include "Misc/DateTime.h"
#include "Components/PostProcessComponent.h"
#include "Materials/MaterialInstanceDynamic.h"
#include "InputCoreTypes.h"

DEFINE_LOG_CATEGORY_STATIC(LogRandomDungeonGen, Log, All);

static const int32 RDSoundSeed = 90417;
static const FName RDFireKeys[3] = { TEXT("Env.Torch"), TEXT("Env.Brazier"), TEXT("Env.Hearth") };
static const FName RDMusicKeys[4] = { TEXT("Music.Explore"), TEXT("Music.Combat"), TEXT("Atmos.Explore"), TEXT("Atmos.Combat") };

ARDDungeonGenerator::ARDDungeonGenerator()
{
	PrimaryActorTick.bCanEverTick = true;
	PrimaryActorTick.TickInterval = 0.f;
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
	default: return TEXT("Hallway junction");
	}
}

AActor* ARDDungeonGenerator::GetTrackedActor() const
{
	return TrackedActor ? TrackedActor.Get() : UGameplayStatics::GetPlayerPawn(this, 0);
}

FIntPoint ARDDungeonGenerator::WorldToTile(FVector L) const
{
	return FIntPoint(FMath::FloorToInt(L.X / TileSize), FMath::FloorToInt(L.Y / TileSize));
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
	return FVector((T.X + 0.5f) * TileSize, (T.Y + 0.5f) * TileSize, 0.f);
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
	// the great hall is the start section's centre block (3, 3): its lanes cross at the origin tile
	if (ARDSection* S = GetSection(FIntPoint::ZeroValue))
	{
		const int32 R = S->RoomAt(FVector(TileSize * 0.5f, TileSize * 0.5f, 0));
		if (R >= 0) return S->GetRoomCenter(R);
	}
	return FVector(0, 0, 0);
}

ARDSection* ARDDungeonGenerator::SpawnSection(FIntPoint S, bool bEditorBuild, bool bReveal)
{
	UWorld* W = GetWorld();
	FActorSpawnParameters P; P.SpawnCollisionHandlingOverride = ESpawnActorCollisionHandlingMethod::AlwaysSpawn;
	const FIntPoint T0 = SectionMinTile(S);
	ARDSection* Sec = W->SpawnActor<ARDSection>(ARDSection::StaticClass(), FTransform(FVector(T0.X * TileSize, T0.Y * TileSize, 0.f)), P);
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
	ARDSection* Sec = SpawnSection(S, false, true);
	if (Sec && Building == Sec) { while (!Sec->ContinueGenerate(1e9)) {} Building = nullptr; }
	return Sec != nullptr;
}

void ARDDungeonGenerator::Enqueue(FIntPoint S)
{
	if (!IsSectionGenerated(S) && !Queue.Contains(S)) Queue.Add(S);
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
	return PlayerMaxHealth * (IsStartSection(Section) ? StartMonsterHealth : RuntimeMonsterHealth);
}

float ARDDungeonGenerator::GetMonsterDamage(FIntPoint Section) const
{
	return GetAverageWeaponDamage() * (IsStartSection(Section) ? StartMonsterDamage : RuntimeMonsterDamage);
}

void ARDDungeonGenerator::MeanMonsterFactors(float& Health, float& Damage) const
{
	float W = 0.f, H = 0.f, D = 0.f;
	for (const FRDMonsterDef& M : Monsters) if (M.Mesh) { W += M.Weight; H += M.Weight * M.HealthFactor; D += M.Weight * M.DamageFactor; }
	Health = W > 0.f && H > 0.f ? H / W : 1.f; Damage = W > 0.f && D > 0.f ? D / W : 1.f;
}

void ARDDungeonGenerator::OnMonsterKilled(ARDMonster* Monster)
{
	++MonstersKilled;
	UE_LOG(LogRandomDungeonGen, Log, TEXT("RDCOMBAT %s killed (%d)"), Monster ? *Monster->MonsterName.ToString() : TEXT("?"), MonstersKilled);
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
	SectionsGenerated = Sections.Num(); SectionsRemoved = 0; MonstersKilled = 0; bMapOpen = false; LastRevealTime = -100.f;
	for (auto& KV : Sections) KV.Value->ActivateForPlay();
	if (PlayerCombat)
	{
		PlayerCombat->Revive(true);
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
	if (!Best) return FString();
	if (bBestDoor) { Best->ToggleDoor(BestI, From); return Best->IsDoorCell(BestI) ? TEXT("cell door") : TEXT("door"); }
	Best->ToggleContainer(BestI);
	return Best->GetContainerKind(BestI);
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
	if (!Best) return FString();
	FString What = bBestDoor ? (Best->IsDoorCell(BestI) ? TEXT("cell door") : TEXT("door")) : Best->GetContainerKind(BestI);
	What.ReplaceInline(TEXT("2"), TEXT(""));
	return FString::Printf(TEXT("%s %s"), Best->IsTargetOpen(bBestDoor, BestI) ? TEXT("close") : TEXT("open"), *What);
}

void ARDDungeonGenerator::UpdateDiscovery(const FVector& L)
{
	const FIntPoint T = WorldToTile(L);
	const FIntPoint S = WorldToSection(L);
	FRDSectionMap* M = MapData.Find(S);
	if (!M) return;
	for (FRDMapRect& R : M->Rects)
	{
		if (R.bDiscovered) continue;
		// rooms: once she is inside (or in their doorway); hallways: within 4 tiles of her along them
		const int32 Pad = R.bCorridor ? 4 : 0;
		if (T.X >= R.Min.X - Pad && T.Y >= R.Min.Y - Pad && T.X < R.Max.X + Pad && T.Y < R.Max.Y + Pad) R.bDiscovered = true;
	}
}

void ARDDungeonGenerator::BeginPlay()
{
	Super::BeginPlay();
	SessionSeed = FixedSessionSeed != 0 ? FixedSessionSeed : (int32)(FDateTime::Now().GetTicks() & 0x7fffffff);
	if (bRevealEffect && RevealPostMaterial)
	{
		RevealMID = UMaterialInstanceDynamic::Create(RevealPostMaterial, this);
		for (int32 Slot = 0; Slot < RevealSlots; ++Slot) RevealMID->SetVectorParameterValue(*FString::Printf(TEXT("Info%d"), Slot), FLinearColor(0, 0, -1e6f, 0));
		RevealPost->Settings.WeightedBlendables.Array.Add(FWeightedBlendable(1.f, RevealMID));
	}
	SoundR.Initialize(RDSoundSeed);
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
	MapData.Reset();
	for (auto It = Sections.CreateIterator(); It; ++It) if (!It->Value) It.RemoveCurrent();
	if (Sections.Num() == 0) SpawnSection(FIntPoint::ZeroValue, false);
	else for (auto& KV : Sections) KV.Value->ActivateForPlay();
	UE_LOG(LogRandomDungeonGen, Log, TEXT("RDGEN play: %d start sections, session seed %d, %d monsters"), Sections.Num(), SessionSeed, GetNumMonsters());
}

void ARDDungeonGenerator::Tick(float Dt)
{
	Super::Tick(Dt);
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
			}
			// what she hears fades with the distance to her, not to the camera behind her
			if (Sounds.Num() > 0) PC->SetAudioListenerAttenuationOverride(P->GetRootComponent(), FVector::ZeroVector);
		}
		// the safety net: a fall out of the dungeon (through a gap that let her through) puts her back where she last stood
		if (ACharacter* Ch = Cast<ACharacter>(P); Ch && FallResetDepth > 0.f)
		{
			const FVector L = Ch->GetActorLocation();
			const float Floor = GetActorLocation().Z;
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
		if ((PC->WasInputKeyJustPressed(EKeys::F) || (bCasterControls && PC->WasInputKeyJustPressed(EKeys::Gamepad_FaceButton_Left))) && P) InteractNearest(P->GetActorLocation());
		if (PC->WasInputKeyJustPressed(EKeys::M) || (bCasterControls && PC->WasInputKeyJustPressed(EKeys::Gamepad_Special_Left))) bMapOpen = !bMapOpen;
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
				const float X0 = T0.X * TileSize, Y0 = T0.Y * TileSize;
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
	const float Volume = S->Volume * VolumeScale * SoundVolume;
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
		A->SetVolumeMultiplier(Set.Volume * SoundVolume);
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
}

void ARDDungeonGenerator::StartMusicLayer(int32 Layer, float FadeSeconds, bool bFromStart)
{
	const FRDSoundSet* Set = Sounds.Find(RDMusicKeys[Layer]);
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
		StartMusicLayer(0, 1.5f, true); StartMusicLayer(2, 1.5f, true);
	}
	const float Now = GetWorld()->GetTimeSeconds();
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
