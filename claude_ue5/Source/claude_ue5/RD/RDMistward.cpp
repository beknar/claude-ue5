// mistward_castle: the rules of 2026-10-26 (docs/improvements.txt). See RDMistward.h and the generator's "Mistward" fields.
#include "RD/RDMistward.h"
#include "RD/RDDungeonGenerator.h"
#include "RD/RDSection.h"
#include "RD/RDMonster.h"
#include "RD/RDCombat.h"
#include "RD/RDInputSim.h"
#include "UObject/UObjectIterator.h"
#include "Components/StaticMeshComponent.h"
#include "Components/SkeletalMeshComponent.h"
#include "Components/MaterialBillboardComponent.h"
#include "Components/PointLightComponent.h"
#include "Components/CapsuleComponent.h"
#include "Engine/StaticMesh.h"
#include "Engine/SkeletalMesh.h"
#include "Engine/Texture2D.h"
#include "Engine/World.h"
#include "GameFramework/Character.h"
#include "GameFramework/CharacterMovementComponent.h"
#include "Kismet/GameplayStatics.h"
#include "Materials/MaterialInstanceDynamic.h"
#include "NiagaraComponent.h"
#include "NiagaraFunctionLibrary.h"
#include "NiagaraSystem.h"
#include "NiagaraSystemInstance.h"
#include "NiagaraSystemInstanceController.h"
#include "NiagaraEmitterInstance.h"
#include "Particles/ParticleSystem.h"
#include "Particles/ParticleSystemComponent.h"
#include "Animation/AnimationAsset.h"
#include "Animation/AnimSequenceBase.h"

DEFINE_LOG_CATEGORY_STATIC(LogRDMistward, Log, All);

UFXSystemComponent* RDMSpawnFx(UObject* Ctx, UFXSystemAsset* Asset, const FVector& At, const FRotator& Rot, float Scale, USceneComponent* AttachTo, bool bUserScale, bool bAutoDestroy)
{
	if (!Asset || !Ctx) return nullptr;
	if (UNiagaraSystem* Ns = Cast<UNiagaraSystem>(Asset))
	{
		const FVector S = bUserScale ? FVector(1.f) : FVector(Scale);
		UNiagaraComponent* C = AttachTo
			? UNiagaraFunctionLibrary::SpawnSystemAttached(Ns, AttachTo, NAME_None, At, Rot, S, EAttachLocation::KeepRelativeOffset, bAutoDestroy, ENCPoolMethod::None, false)
			: UNiagaraFunctionLibrary::SpawnSystemAtLocation(Ctx, Ns, At, Rot, S, bAutoDestroy, false, ENCPoolMethod::None, false);
		if (!C) return nullptr;
		if (bUserScale) C->SetVariableFloat(TEXT("User.Scale"), Scale);
		C->Activate(true);
		return C;
	}
	if (UParticleSystem* Ps = Cast<UParticleSystem>(Asset))
		return AttachTo ? UGameplayStatics::SpawnEmitterAttached(Ps, AttachTo, NAME_None, At, Rot, FVector(Scale), EAttachLocation::KeepRelativeOffset, bAutoDestroy)
		                : UGameplayStatics::SpawnEmitterAtLocation(Ctx, Ps, At, Rot, FVector(Scale), bAutoDestroy);
	return nullptr;
}

int32 RDNiagaraParticles(const UNiagaraComponent* C)
{
	if (!C) return 0;
	const FNiagaraSystemInstanceControllerConstPtr Ctl = C->GetSystemInstanceController();
	if (!Ctl.IsValid() || !Ctl->IsValid()) return 0;
	int32 Num = 0;
	if (const FNiagaraSystemInstance* SI = Ctl->GetSystemInstance_Unsafe()) for (const FNiagaraEmitterInstanceRef& E : SI->GetEmitters()) Num += E->GetNumParticles();
	return Num;
}

/** the way out of a prison cell (its frame: the cell's middle, facing the room): the door's half of the front is [-2, 148] from
 *  the front's middle (RDSection's prison cells); Doorway inside in front of that gap, Exit out in the room before it */
static void RDMCellWay(const FTransform& Frame, float TileSize, FVector& Doorway, FVector& Exit)
{
	const FVector Fw = Frame.GetRotation().GetForwardVector(), Rt = Frame.GetRotation().GetRightVector();
	const FVector Gap = Frame.GetLocation() + Fw * (TileSize * 0.5f) + Rt * 73.f;
	Doorway = Gap - Fw * 70.f;
	Exit = Gap + Fw * (TileSize * 0.6f);
}

static int32 RDMParticles(const UFXSystemComponent* F)
{
	if (const UNiagaraComponent* C = Cast<UNiagaraComponent>(F)) return RDNiagaraParticles(C);
	return F && F->IsActive() ? 1 : 0;
}

// ================================================================================================ the loot pile
ARDLootPile::ARDLootPile()
{
	PrimaryActorTick.bCanEverTick = true;
	Root = CreateDefaultSubobject<USceneComponent>(TEXT("Root"));
	RootComponent = Root;
}

void ARDLootPile::Init(ARDDungeonGenerator* G, const TArray<FName>& InThings, const TArray<float>& InWear)
{
	Things = InThings; Wear = InWear;
	if (!G) return;
	// (rings of pictures over it, one for each kind of thing: twelve to a ring, each ring wider and higher than the last
	// (until 2026-10-27 at most twelve: a richer pack showed only part of what lay there))
	TArray<FName> Kinds;
	for (const FName& N : Things) Kinds.AddUnique(N);
	const int32 Num = Kinds.Num();
	for (int32 I = 0; I < Num; ++I)
	{
		const int32 Ix = G->FindItem(Kinds[I]);
		FName Icon = Ix >= 0 ? G->Items[Ix].Icon : NAME_None;
		// (a found weapon's picture: the weapon it is)
		if (Ix >= 0 && Icon.IsNone()) for (const FRDWeaponFit& F : G->Items[Ix].WeaponFits) if (!F.Weapon.Icon.IsNone()) { Icon = F.Weapon.Icon; break; }
		const FRDUIArt* Art = Icon.IsNone() ? nullptr : G->UIArt.Find(Icon);
		if (!Art || !Art->Texture || !G->IconMaterial) continue;
		UMaterialInstanceDynamic* Mi = UMaterialInstanceDynamic::Create(G->IconMaterial, this);
		Mi->SetTextureParameterValue(TEXT("Icon"), Art->Texture);
		UMaterialBillboardComponent* B = NewObject<UMaterialBillboardComponent>(this);
		B->SetupAttachment(Root);
		B->AddElement(Mi, nullptr, false, 26.f, 26.f, nullptr);
		B->RegisterComponent();
		Icons.Add(B);
		B->SetRelativeLocation(IconPlace(Icons.Num() - 1, 0.f));
	}
	Pictures = Icons.Num();
	if (G->LootPileFx) Fx = RDMSpawnFx(this, G->LootPileFx, FVector::ZeroVector, FRotator::ZeroRotator, G->LootPileFxScale, Root, false, false);
	Light = NewObject<UPointLightComponent>(this);
	Light->SetupAttachment(Root);
	Light->SetRelativeLocation(FVector(0, 0, 80));
	Light->SetIntensityUnits(ELightUnits::Candelas);
	Light->SetIntensity(30.f); Light->SetLightColor(FLinearColor(1.f, 0.78f, 0.35f)); Light->SetAttenuationRadius(500.f); Light->SetCastShadows(false);
	Light->RegisterComponent();
}

int32 ARDLootPile::GetEffectParticles() const { return RDMParticles(Fx); }

void ARDLootPile::Tick(float Dt)
{
	Super::Tick(Dt);
	Age += Dt;
	// (the pictures turn slowly round it and bob)
	for (int32 I = 0; I < Icons.Num(); ++I) if (UMaterialBillboardComponent* B = Icons[I]) B->SetRelativeLocation(IconPlace(I, Age));
}

FVector ARDLootPile::IconPlace(int32 I, float T) const
{
	// (twelve to a ring; the last ring holds what is left over)
	const int32 Num = FMath::Max(Pictures > 0 ? Pictures : Icons.Num(), 1);
	const int32 Ring = I / 12, InRing = FMath::Min(12, Num - Ring * 12);
	const float A = 2.f * PI * (I % 12) / FMath::Max(InRing, 1) + T * (Ring % 2 ? -0.45f : 0.6f);
	const float Rr = Num > 1 ? 55.f + 32.f * Ring : 0.f;
	return FVector(FMath::Cos(A) * Rr, FMath::Sin(A) * Rr, 95.f + 34.f * Ring + 18.f * (I % 2) + 6.f * FMath::Sin(T * 2.f + I));
}

// ================================================================================================ the teleporter
ARDTeleporter::ARDTeleporter()
{
	PrimaryActorTick.bCanEverTick = true;
	Root = CreateDefaultSubobject<USceneComponent>(TEXT("Root"));
	RootComponent = Root;
}

void ARDTeleporter::Init(ARDDungeonGenerator* G, int32 InTier, bool bWithRing)
{
	Tier = InTier;
	if (!G) return;
	if (G->PadMesh)
	{
		Pad = NewObject<UStaticMeshComponent>(this);
		Pad->SetStaticMesh(G->PadMesh);
		Pad->SetupAttachment(Root);
		Pad->SetRelativeTransform(G->PadTransform);
		Pad->SetCollisionEnabled(ECollisionEnabled::NoCollision);
		Pad->RegisterComponent();
	}
	if (G->PadFx) Fx = RDMSpawnFx(this, G->PadFx, FVector(0, 0, 5), FRotator::ZeroRotator, G->PadFxScale, Root, true, false);
	Light = NewObject<UPointLightComponent>(this);
	Light->SetupAttachment(Root);
	Light->SetRelativeLocation(FVector(0, 0, 120));
	Light->SetIntensityUnits(ELightUnits::Candelas);
	Light->SetIntensity(60.f); Light->SetLightColor(FLinearColor(0.45f, 0.7f, 1.f)); Light->SetAttenuationRadius(700.f); Light->SetCastShadows(false);
	Light->RegisterComponent();
	if (G->TeleportRingMesh)
	{
		Ring = NewObject<UStaticMeshComponent>(this);
		Ring->SetStaticMesh(G->TeleportRingMesh);
		Ring->SetupAttachment(Root);
		Ring->SetCollisionEnabled(ECollisionEnabled::NoCollision);
		Ring->RegisterComponent();
		// (a ring a few cm across, shown at a size she can see from the doorway)
		const FBoxSphereBounds B = G->TeleportRingMesh->GetBounds();
		const float K = 22.f / FMath::Max((float)B.SphereRadius, 0.5f);
		Ring->SetRelativeScale3D(FVector(K));
		Ring->SetRelativeLocation(FVector(0, 0, 105) - B.Origin * K);
	}
	ShowRing(bWithRing);
}

void ARDTeleporter::ShowRing(bool bShow)
{
	bRing = bShow;
	if (Ring) Ring->SetVisibility(bShow);
}

void ARDTeleporter::Tick(float Dt)
{
	Super::Tick(Dt);
	Age += Dt;
	if (Ring && bRing) Ring->SetRelativeRotation(FRotator(20.f * FMath::Sin(Age), Age * 70.f, 0.f));
	if (Light) Light->SetIntensity(55.f + 15.f * FMath::Sin(Age * 3.f));
}

// ================================================================================================ the prisoner
ARDPrisoner::ARDPrisoner()
{
	PrimaryActorTick.bCanEverTick = true;
	Root = CreateDefaultSubobject<USceneComponent>(TEXT("Root"));
	RootComponent = Root;
	Body = CreateDefaultSubobject<USkeletalMeshComponent>(TEXT("Body"));
	Body->SetupAttachment(Root);
	Body->SetCollisionEnabled(ECollisionEnabled::NoCollision);
	Body->SetAnimationMode(EAnimationMode::AnimationSingleNode);
}

void ARDPrisoner::Init(const FRDPrisonerDef& Def, const FVector& Doorway, const FVector& Exit, const FVector& Away)
{
	Title = Def.Title.IsEmpty() ? Def.Name.ToString() : Def.Title;
	Body->SetSkeletalMeshAsset(Def.Mesh);
	Body->SetRelativeLocationAndRotation(FVector(0, 0, Def.MeshZ), FRotator(0, Def.MeshYaw, 0));
	for (USkeletalMesh* P : Def.Parts)
	{
		if (!P) continue;
		USkeletalMeshComponent* C = NewObject<USkeletalMeshComponent>(this);
		C->SetSkeletalMeshAsset(P);
		C->SetupAttachment(Body);
		C->SetCollisionEnabled(ECollisionEnabled::NoCollision);
		C->RegisterComponent();
		C->SetLeaderPoseComponent(Body);
	}
	IdleAnim = Def.Idle; WalkAnim = Def.Walk; ThanksAnim = Def.Thanks;
	Speed = Def.WalkSpeed; ClipSpeed = FMath::Max(Def.WalkClipSpeed, 10.f);
	DoorAt = Doorway; ExitAt = Exit; AwayAt = Away; Leg = 0;
	if (IdleAnim) { Body->PlayAnimation(IdleAnim, true); Body->SetPosition(FMath::FRandRange(0.f, 2.f)); }
}

void ARDPrisoner::Free()
{
	if (State != 0) return;
	State = 1; StateTime = 0.f;
	if (ThanksAnim) Body->PlayAnimation(ThanksAnim, false);
}

void ARDPrisoner::Tick(float Dt)
{
	Super::Tick(Dt);
	if (State == 0 || State == 4) return;
	StateTime += Dt;
	auto WalkTo = [&](const FVector& To) -> bool
	{
		FVector D = To - GetActorLocation(); D.Z = 0.f;
		if (D.Size() < 25.f) return true;
		const FVector Step = D.GetSafeNormal() * FMath::Min(Speed * Dt, D.Size());
		SetActorLocation(GetActorLocation() + Step);
		SetActorRotation(FRotator(0.f, FMath::RInterpConstantTo(GetActorRotation(), D.Rotation(), Dt, 360.f).Yaw, 0.f));
		return false;
	};
	if (State == 1)
	{
		const float Len = ThanksAnim ? FMath::Max(Cast<UAnimSequenceBase>(ThanksAnim) ? Cast<UAnimSequenceBase>(ThanksAnim)->GetPlayLength() : 1.5f, 1.f) : 1.5f;
		if (StateTime > FMath::Min(Len, 3.f)) { State = 2; StateTime = 0.f; if (WalkAnim) { Body->PlayAnimation(WalkAnim, true); Body->SetPlayRate(Speed / ClipSpeed); } }
		return;
	}
	if (State == 2)
	{
		// (to the door's gap, out of the cell, then away down the room; gone after a while whatever. Straight from the cell's
		// middle she walked through its bars.)
		const FVector Legs[3] = { DoorAt, ExitAt, AwayAt };
		if (Leg < 3 && StateTime > 0.f && WalkTo(Legs[Leg])) ++Leg;
		if (Leg >= 3 || StateTime > 9.f) { State = 3; StateTime = 0.f; }
		return;
	}
	if (State == 3)
	{
		// (fades: shrinks into the floor and is gone)
		const float K = FMath::Clamp(1.f - StateTime / 1.2f, 0.f, 1.f);
		SetActorScale3D(FVector(FMath::Max(K, 0.02f)));
		if (K <= 0.f) { State = 4; SetActorHiddenInGame(true); SetLifeSpan(0.5f); }
	}
}

// ================================================================================================ the generator: themes, tiers
FName ARDDungeonGenerator::ThemeOf(FIntPoint S) const
{
	if (TierThemes.Num() == 0) return NAME_None;
	const FName T = TierThemes[FMath::Clamp(TierOf(S) - 1, 0, TierThemes.Num() - 1)];
	if (T == TEXT("Mixed"))
	{
		if (MixedThemes.Num() == 0) return NAME_None;
		const uint32 H = HashCombine(GetTypeHash(S.X * 92821 + 7), GetTypeHash(S.Y * 68917 + 3));
		const FName M = MixedThemes[H % (uint32)MixedThemes.Num()];
		return M == TEXT("None") ? NAME_None : M;
	}
	return T == TEXT("None") ? NAME_None : T;
}

bool ARDDungeonGenerator::GetTierTally(int32 Tier, FIntVector& Done, FIntVector& All) const
{
	Done = All = FIntVector::ZeroValue;
	if (MaxTier <= 0 || Tier < 1) return false;
	bool bComplete = true;
	const int32 Rr = Tier - 1;
	for (int32 X = -Rr; X <= Rr; ++X)
		for (int32 Y = -Rr; Y <= Rr; ++Y)
		{
			const FIntPoint S(X, Y);
			if (TierOf(S) != Tier) continue;
			if (const FRDSectionProgress* P = Progress.Find(S); P && (P->Rooms > 0 || P->Monsters > 0 || P->Chests.Num() > 0))
			{
				All += FIntVector(P->Rooms, P->Monsters, P->Chests.Num());
				Done += FIntVector(P->RoomsExplored, FMath::Min(P->Killed.Num(), P->Monsters), P->ChestsLooted);
				continue;
			}
			// (a set she has not reached: what it would hold, counted without building it)
			if (const FIntVector* C = CensusCache.Find(S)) { All += FIntVector(C->X, C->Z, C->Y); continue; }
			bComplete = false;
			CensusQueue.AddUnique(S);
		}
	return bComplete;
}

void ARDDungeonGenerator::TickCensus()
{
	// (two a frame: a set of rooms planned and furnished without building, a few milliseconds)
	for (int32 K = 0; K < 2 && CensusQueue.Num() > 0; ++K)
	{
		const FIntPoint S = CensusQueue[0]; CensusQueue.RemoveAt(0);
		if (CensusCache.Contains(S)) continue;
		int32 Rooms = 0, Chests = 0, Mons = 0;
		const double T0 = FPlatformTime::Seconds();
		if (ARDSection::Census(this, S, SectionSeed(S), Rooms, Chests, Mons))
		{
			CensusCache.Add(S, FIntVector(Rooms, Chests, Mons));
			UE_LOG(LogRDMistward, Log, TEXT("RDCENSUS (%d,%d) tier %d: %d rooms, %d chests and trunks, %d monsters (%.1f ms)"), S.X, S.Y, TierOf(S), Rooms, Chests, Mons, (FPlatformTime::Seconds() - T0) * 1000.0);
		}
	}
	if (CensusQueue.Num() == 0 && TierOpenShare < 1.f) CheckTierOpenings();
}

void ARDDungeonGenerator::CheckTierOpenings()
{
	if (MaxTier <= 0 || TierOpenShare >= 1.f) return;
	for (int32 T = 2; T <= MaxTier; ++T)
	{
		if (TiersOpened.Contains(T)) continue;
		if (!IsTierOpen(T)) break;
		TiersOpened.Add(T);
		TierNotice = FString::Printf(TEXT("TIER %d IS OPEN"), T);
		TierNoticeTime = GetWorld() ? GetWorld()->GetTimeSeconds() : 0.f;
		RefreshSeals();
		if (const AActor* Who = GetTrackedActor()) PlaySoundAt(TEXT("Env.Generate"), Who->GetActorLocation());
		UE_LOG(LogRDMistward, Log, TEXT("RDTIER tier %d is open (%.0f%% of tier %d)"), T, TierOpenShare * 100.f, T - 1);
		OnTierOpened(T);
	}
}

void ARDDungeonGenerator::OnTierOpened(int32 Tier)
{
	if (bBossEncounters) PlaceBoss(Tier);
	// (the ring next tick: the container whose opening tipped the share has not given its things yet, and one of them may be
	// that very ring)
	if (bRingGuards) PendingRingTiers.AddUnique(Tier);
}

bool ARDDungeonGenerator::PickExploredRoom(int32 Tier, int32 Salt, ARDSection*& OutSection, int32& OutRoom) const
{
	OutSection = nullptr; OutRoom = -1;
	const AActor* Her = GetTrackedActor();
	const FVector L = Her ? Her->GetActorLocation() : FVector::ZeroVector;
	const ARDSection* HerS = GetSection(WorldToSection(L));
	const int32 HerRoom = HerS ? HerS->RoomAt(L) : -1;
	struct FC { ARDSection* S; int32 Room; float D; };
	TArray<FC> Cands;
	for (const auto& KV : Sections)
	{
		ARDSection* S = KV.Value;
		if (!S || S->IsBuilding() || TierOf(KV.Key) != Tier) continue;
		const FRDSectionMap* M = MapData.Find(KV.Key);
		if (!M) continue;
		for (int32 RI = 0; RI < S->GetNumRooms() && RI < M->Rects.Num(); ++RI)
		{
			const FRDMapRect& R = M->Rects[RI];
			if (R.bCorridor || !R.bDiscovered || (S == HerS && RI == HerRoom)) continue;
			if (S->GetRoomFreeTiles(RI).Num() < 6) continue;
			Cands.Add({ S, RI, (float)FVector::Dist2D(S->GetRoomCenter(RI), L) });
		}
	}
	if (Cands.Num() == 0) return false;
	// (not right beside her, not far off: among the nearer half, by a hash of the session and the tier)
	Cands.Sort([](const FC& A, const FC& B) { return A.D < B.D; });
	TArray<FC> Pick;
	for (const FC& C : Cands) if (C.D > 1200.f) Pick.Add(C);
	if (Pick.Num() == 0) Pick = Cands;
	const int32 Half = FMath::Max(1, (Pick.Num() + 1) / 2);
	const uint32 H = HashCombine((uint32)SessionSeed ^ 0xB055u, GetTypeHash(Tier * 31 + Salt));
	const FC& C = Pick[H % (uint32)Half];
	OutSection = C.S; OutRoom = C.Room;
	return true;
}

ARDMonster* ARDDungeonGenerator::SpawnMonsterKind(int32 Kind, const FVector& At, int32 Tier, float HealthMul, float DamageMul, float ScaleMul, const FString& Title)
{
	if (!Monsters.IsValidIndex(Kind) || !Monsters[Kind].Mesh) return nullptr;
	ARDSection* Sec = GetSection(WorldToSection(At));
	if (!Sec) return nullptr;
	const FRDMonsterDef& Def = Monsters[Kind];
	FActorSpawnParameters Sp; Sp.SpawnCollisionHandlingOverride = ESpawnActorCollisionHandlingMethod::AdjustIfPossibleButAlwaysSpawn;
	ARDMonster* M = GetWorld()->SpawnActor<ARDMonster>(ARDMonster::StaticClass(), FTransform(FRotator(0, FMath::FRandRange(0.f, 360.f), 0), At + FVector(0, 0, Def.CapsuleHalfHeight + 5.f)), Sp);
	if (!M) return nullptr;
	M->SpawnIndex = -1;           // (not one of its set's planned monsters: the tiers do not count it)
	M->Setup(Sec, Def, (int32)HashCombine((uint32)SessionSeed, GetTypeHash(At.X * 13.0 + At.Y * 7.0)));
	M->Empower(Tier, HealthMul, DamageMul, ScaleMul, Title);
	Sec->SpawnedMonsters.Add(M);
	return M;
}

ARDMonster* ARDDungeonGenerator::SpawnMonsterNamed(FName Kind, FVector At, int32 Tier, float HealthMul, float DamageMul, float ScaleMul)
{
	const int32 K = Monsters.IndexOfByPredicate([Kind](const FRDMonsterDef& D) { return D.Name == Kind; });
	return SpawnMonsterKind(K, At, Tier, HealthMul, DamageMul, ScaleMul);
}

void ARDDungeonGenerator::PlaceBoss(int32 Tier)
{
	ARDSection* S = nullptr; int32 Room = -1;
	if (!PickExploredRoom(Tier - 1, 1, S, Room)) { UE_LOG(LogRDMistward, Warning, TEXT("RDBOSS tier %d: no explored room of tier %d to set it in"), Tier, Tier - 1); return; }
	FEncounter E; E.Tier = Tier; E.bBoss = true; E.Section = S->Coord; E.Room = Room; E.At = S->GetRoomCenter(Room);
	TArray<int32> Kinds; MonsterKindsFor(FIntPoint(Tier - 1, 0), Kinds);
	if (Kinds.Num() == 0) return;
	FRandomStream R((int32)HashCombine((uint32)SessionSeed ^ 0xB055u, GetTypeHash(Tier)));
	// (the boss: the strongest kind of the tier; its band: 3 to 6 of the tier's)
	int32 Boss = Kinds[0];
	for (const int32 K : Kinds) if (Monsters[K].HealthFactor > Monsters[Boss].HealthFactor) Boss = K;
	const int32 Band = R.RandRange(BossMinions.X, BossMinions.Y);
	TArray<FVector> Free = S->GetRoomFreeTiles(Room);
	Free.Sort([&E](const FVector& A, const FVector& B) { return FVector::DistSquared(A, E.At) < FVector::DistSquared(B, E.At); });
	if (Free.Num() == 0) return;
	E.Kinds.Add(Boss); E.Spots.Add(Free[0]);
	for (int32 I = 0; I < Band && I + 1 < Free.Num(); ++I) { E.Kinds.Add(Kinds[R.RandRange(0, Kinds.Num() - 1)]); E.Spots.Add(Free[FMath::Min(Free.Num() - 1, 1 + I * 2)]); }
	E.Dead.Init(false, E.Kinds.Num());
	E.Label = FString::Printf(TEXT("TIER %d BOSS: %s"), Tier, *(Monsters[Boss].Title.IsEmpty() ? Monsters[Boss].Name.ToString() : Monsters[Boss].Title).ToUpper());
	Encounters.Add(E);
	RespawnEncounters(S);
	// ("in the armory", the room's kind; "see your map": the boss's mark is on it)
	FString Where = TEXT("A ROOM YOU HAVE SEEN");
	if (const FRDSectionMap* M = MapData.Find(S->Coord); M && M->Rects.IsValidIndex(Room)) Where = TEXT("THE ") + KindName(M->Rects[Room].Kind).ToUpper();
	TierNotice = FString::Printf(TEXT("TIER %d IS OPEN  -  A BOSS WAITS IN %s (SEE YOUR MAP)"), Tier, *Where);
	UE_LOG(LogRDMistward, Log, TEXT("RDBOSS tier %d: %s and %d more in room %d of (%d,%d)"), Tier, *Monsters[Boss].Name.ToString(), E.Kinds.Num() - 1, Room, S->Coord.X, S->Coord.Y);
}

void ARDDungeonGenerator::PlaceRingGuard(int32 Tier)
{
	// (the rings of the tier before: 2(T-1)-1 and 2(T-1); the Magic Potency Ring, as the user's list names it ("the magic
	// potency ring 1 or 2"), for every hero. Until 2026-10-27 it was her kind of ring (hit points for the Warrior, dexterity
	// for the Rogue): the audit of the list found that departed from its words)
	const ERDRingKind Kind = ERDRingKind::Magic;
	const TCHAR* Base = TEXT("Magic Potency Ring");
	const int32 A = 2 * (Tier - 1) - 1, B = 2 * (Tier - 1);
	const FName RA(*FString::Printf(TEXT("%s %d"), Base, A)), RB(*FString::Printf(TEXT("%s %d"), Base, B));
	const URDCombatComponent* Pc = GetPlayerCombat();
	if (!Pc || FindItem(RA) < 0) return;
	if (Pc->GetItemCount(RA) > 0 || Pc->GetItemCount(RB) > 0 || Pc->GetWornRing(Kind) == RA || Pc->GetWornRing(Kind) == RB) return;
	ARDSection* S = nullptr; int32 Room = -1;
	if (!PickExploredRoom(Tier - 1, 2, S, Room)) return;
	TArray<int32> Kinds; MonsterKindsFor(FIntPoint(Tier - 1, 0), Kinds);
	if (Kinds.Num() == 0) return;                // (no guards to set: no ring either)
	// (in a container of the room she has not opened; or a chest of it at all; else none: the ring lies on the guards' spot)
	// (a container's index in the set as built and its key, which stays when the set is built again, are not the same
	// number: the key goes into ForcedLoot and the map's looted test, the index gives the place)
	int32 Key = -1, Index = -1;
	for (int32 I = 0; I < S->GetNumContainers(); ++I)
		if (S->RoomAt(S->GetContainerLocation(I)) == Room && !S->IsContainerLooted(I)) { Key = S->ContainerKey(I); Index = I; break; }
	FEncounter E; E.Tier = Tier; E.Section = S->Coord; E.Room = Room; E.Ring = RA;
	E.At = Index >= 0 ? S->GetContainerLocation(Index) : S->GetRoomCenter(Room);
	if (Key >= 0) { E.RingKey = FIntVector(S->Coord.X, S->Coord.Y, Key); ForcedLoot.FindOrAdd(E.RingKey).AddUnique(RA); }
	// (every container of the room already opened: the ring lies on the floor in the middle of the room, a pile she takes
	// up with F, as her own things are when she falls)
	else if (ARDLootPile* Lp = DropLoot(E.At + FVector(0, 0, 100.f), { RA }, { -1.f })) { Lp->bHers = false; E.At = Lp->GetActorLocation(); }
	FRandomStream R((int32)HashCombine((uint32)SessionSeed ^ 0x61A2u, GetTypeHash(Tier)));
	TArray<FVector> Free = S->GetRoomFreeTiles(Room);
	Free.Sort([&E](const FVector& P, const FVector& Q) { return FVector::DistSquared(P, E.At) < FVector::DistSquared(Q, E.At); });
	for (int32 I = 0; I < GuardCount && I < Free.Num(); ++I) { E.Kinds.Add(Kinds[R.RandRange(0, Kinds.Num() - 1)]); E.Spots.Add(Free[FMath::Min(Free.Num() - 1, I + 1)]); }
	E.Dead.Init(false, E.Kinds.Num());
	E.Label = FString::Printf(TEXT("%s (guarded)"), *RA.ToString());
	Encounters.Add(E);
	RespawnEncounters(S);
	UE_LOG(LogRDMistward, Log, TEXT("RDRING tier %d: %s put in container %d of room %d of (%d,%d), %d guards"), Tier, *RA.ToString(), Key, Room, S->Coord.X, S->Coord.Y, E.Kinds.Num());
}

void ARDDungeonGenerator::RespawnEncounters(ARDSection* S)
{
	if (!S) return;
	for (FEncounter& E : Encounters)
	{
		if (E.Section != S->Coord) continue;
		E.Live.SetNum(E.Kinds.Num());
		for (int32 I = 0; I < E.Kinds.Num(); ++I)
		{
			if (E.Dead[I] || (E.Live[I].IsValid() && !E.Live[I]->IsDead())) continue;
			const bool bBoss = E.bBoss && I == 0;
			ARDMonster* M = SpawnMonsterKind(E.Kinds[I], E.Spots[I], E.Tier, bBoss ? BossHealth : 1.f, bBoss ? BossDamage : 1.f, bBoss ? BossScale : 1.f,
				bBoss ? FString::Printf(TEXT("BOSS  %s"), *(Monsters[E.Kinds[I]].Title.IsEmpty() ? Monsters[E.Kinds[I]].Name.ToString() : Monsters[E.Kinds[I]].Title)) : FString());
			if (M) { M->bBoss = bBoss; E.Live[I] = M; }
		}
	}
}

TArray<FString> ARDDungeonGenerator::GetEncounterLines() const
{
	TArray<FString> Out;
	for (const FEncounter& E : Encounters)
		for (int32 I = 0; I < E.Kinds.Num(); ++I)
		{
			const ARDMonster* M = E.Live.IsValidIndex(I) ? E.Live[I].Get() : nullptr;
			const FVector P = M ? M->GetActorLocation() : E.Spots[I];
			const FString Kd = E.bBoss ? (I == 0 ? TEXT("boss") : TEXT("band")) : TEXT("guard");
			Out.Add(FString::Printf(TEXT("%s|%.0f|%.0f|%.0f|%s|%d|%d|%s|%.0f"), *Kd, P.X, P.Y, P.Z, *Monsters[E.Kinds[I]].Name.ToString(), (M && !M->IsDead()) ? 1 : 0, E.Tier,
				*E.Label, M ? M->GetMaxHealth() : 0.f));
		}
	for (const FEncounter& E : Encounters)
		if (!E.Ring.IsNone()) Out.Add(FString::Printf(TEXT("ring|%.0f|%.0f|%.0f|%s|%d|%d|%d|%d"), E.At.X, E.At.Y, E.At.Z, *E.Ring.ToString(), E.RingKey.Z, E.Tier, E.Section.X, E.Section.Y));
	return Out;
}

// ================================================================================================ the loot pile (her death)
ARDLootPile* ARDDungeonGenerator::DropLoot(const FVector& At, const TArray<FName>& Things, const TArray<float>& Wear)
{
	if (Things.Num() == 0) return nullptr;
	FActorSpawnParameters Sp; Sp.SpawnCollisionHandlingOverride = ESpawnActorCollisionHandlingMethod::AlwaysSpawn;
	// (on the floor under her)
	FVector Floor = At;
	FHitResult H;
	if (GetWorld()->LineTraceSingleByChannel(H, At + FVector(0, 0, 50), At - FVector(0, 0, 400), ECC_Visibility)) Floor = H.ImpactPoint;
	ARDLootPile* P = GetWorld()->SpawnActor<ARDLootPile>(ARDLootPile::StaticClass(), FTransform(Floor + FVector(0, 0, 2)), Sp);
	if (!P) return nullptr;
	P->Init(this, Things, Wear);
	LootPiles.Add(P);
	UE_LOG(LogRDMistward, Log, TEXT("RDLOOTPILE %d things dropped at (%.0f, %.0f), %d pictures"), Things.Num(), Floor.X, Floor.Y, P->Pictures);
	return P;
}

bool ARDDungeonGenerator::TakeLootNear(const FVector& From, float Reach)
{
	URDCombatComponent* Pc = GetPlayerCombat();
	ARDLootPile* Best = nullptr; float BestD = Reach;
	for (ARDLootPile* P : LootPiles) if (IsValid(P)) { const float D = FVector::Dist2D(P->GetActorLocation(), From); if (D < BestD) { BestD = D; Best = P; } }
	if (!Best || !Pc) return false;
	Pc->TakeBack(Best->Things, Best->Wear, Best->bHers);
	LootPiles.Remove(Best);
	PlaySoundAt(TEXT("Player.Loot"), Best->GetActorLocation());
	Best->Destroy();
	return true;
}

// ================================================================================================ tests' input, as the devices send it
FString ARDDungeonGenerator::SlateKey(FKey Key, bool bDown) { return RDInputSim::Key(GetWorld(), Key, bDown); }
FString ARDDungeonGenerator::SlateMouseMove(FVector2D Pixel) { return RDInputSim::MouseMove(GetWorld(), Pixel); }
FString ARDDungeonGenerator::SlateMouseButton(FVector2D Pixel, FKey Button, bool bDown) { return RDInputSim::MouseButton(GetWorld(), Pixel, Button, bDown); }
FString ARDDungeonGenerator::SlateWheel(FVector2D Pixel, float Delta) { return RDInputSim::Wheel(GetWorld(), Pixel, Delta); }
FString ARDDungeonGenerator::SlateClearView() { return RDInputSim::ClearView(GetWorld()); }
int32 ARDDungeonGenerator::SlateRestoreView() { return RDInputSim::RestoreView(); }
int32 ARDDungeonGenerator::SlateRestoreAnyView() { return RDInputSim::RestoreView(); }

int32 ARDDungeonGenerator::GetParticlesNear(FVector At, float Radius) const
{
	int32 Num = 0;
	const UWorld* W = GetWorld();
	for (TObjectIterator<UNiagaraComponent> It; It; ++It)
		if (It->GetWorld() == W && FVector::DistSquared(It->GetComponentLocation(), At) <= Radius * Radius) Num += RDNiagaraParticles(*It);
	return Num;
}

// ================================================================================================ teleporters
FName ARDDungeonGenerator::TeleportRingOf(int32 Tier) const
{
	for (const FRDItemDef& It : Items) if (It.Kind == ERDItemKind::Teleport && It.TeleportTier == Tier) return It.Name;
	return NAME_None;
}

int32 ARDDungeonGenerator::PadNear(FVector From, float Reach) const
{
	int32 Best = 0; float BestD = Reach;
	for (const TPair<int32, FVector>& P : Pads) { const float D = FVector::Dist2D(P.Value, From); if (D < BestD && FMath::Abs(P.Value.Z - From.Z) < 300.f) { BestD = D; Best = P.Key; } }
	return Best;
}

TArray<int32> ARDDungeonGenerator::GetPadDestinations() const
{
	TArray<int32> Out;
	const URDCombatComponent* Pc = GetPlayerCombat();
	for (const TPair<int32, FVector>& P : Pads)
		if (P.Key > 1 && Pc && !TeleportRingOf(P.Key).IsNone() && Pc->GetItemCount(TeleportRingOf(P.Key)) > 0) Out.Add(P.Key);
	Out.Sort();
	return Out;
}

bool ARDDungeonGenerator::TeleportToTier(int32 Tier)
{
	const FVector* At = Pads.Find(Tier);
	APlayerController* PC = UGameplayStatics::GetPlayerController(this, 0);
	ACharacter* Her = PC ? Cast<ACharacter>(PC->GetPawn()) : nullptr;
	if (!At || !Her) return false;
	// (its set of rooms is there before she is)
	if (const FIntPoint* S = PadSections.Find(Tier)) GenerateSectionNow(*S);
	if (TeleportFx) RDMSpawnFx(this, TeleportFx, Her->GetActorLocation(), FRotator::ZeroRotator, 1.f, nullptr, true, true);
	// (beside the pad, not on it: F there would send her straight back)
	const FVector To = *At + FVector(180.f, 0.f, Her->GetCapsuleComponent()->GetScaledCapsuleHalfHeight() + 10.f);
	Her->SetActorLocation(To, false, nullptr, ETeleportType::TeleportPhysics);
	Her->GetCharacterMovement()->StopMovementImmediately();
	if (TeleportFx) RDMSpawnFx(this, TeleportFx, To, FRotator::ZeroRotator, 1.f, nullptr, true, true);
	PlaySoundAt(TEXT("Env.Generate"), To);
	++Teleports;
	if (URDCombatComponent* Pc = GetPlayerCombat()) Pc->ShowMessage(Tier == 1 ? FString(TEXT("The ring carries you back to the first tier's teleporter")) : FString::Printf(TEXT("The teleporter carries you to tier %d"), Tier));
	UE_LOG(LogRDMistward, Log, TEXT("RDTELEPORT to tier %d at (%.0f, %.0f)"), Tier, To.X, To.Y);
	return true;
}

FString ARDDungeonGenerator::DescribePadNear(const FVector& From) const
{
	const int32 T = PadNear(From);
	if (T <= 0) return FString();
	if (T > 1 && !PadRingsTaken.Contains(T)) return FString::Printf(TEXT("take the teleport ring of tier %d"), T);
	if (T > 1) return TEXT("teleport to the first tier");
	const TArray<int32> D = GetPadDestinations();
	if (D.Num() == 0) return TEXT("teleporter: a tier's teleport ring takes you on");
	const int32 Ch = D.Contains(PadChoice) ? PadChoice : D.Last();
	return D.Num() > 1 ? FString::Printf(TEXT("teleport to tier %d    [G] another tier"), Ch) : FString::Printf(TEXT("teleport to tier %d"), Ch);
}

FString ARDDungeonGenerator::UsePadNear(const FVector& From)
{
	const int32 T = PadNear(From);
	URDCombatComponent* Pc = GetPlayerCombat();
	if (T <= 0 || !Pc) return FString();
	if (T > 1 && !PadRingsTaken.Contains(T))
	{
		const FName Ring = TeleportRingOf(T);
		if (!Ring.IsNone()) Pc->AddItem(Ring, 1);
		PadRingsTaken.Add(T);
		if (TObjectPtr<ARDTeleporter>* A = PadActors.Find(T); A && *A) (*A)->ShowRing(false);
		Pc->ShowMessage(FString::Printf(TEXT("You take the %s: use it (I) to go back to the first tier's teleporter"), *Ring.ToString().ToLower()));
		PlaySoundAt(TEXT("Player.Loot"), From);
		return TEXT("ring");
	}
	if (T > 1) { TeleportToTier(1); return TEXT("teleport"); }
	const TArray<int32> D = GetPadDestinations();
	if (D.Num() == 0) { Pc->ShowMessage(TEXT("The teleporter is dark: find a tier's teleport ring on its pad first")); return TEXT("pad"); }
	TeleportToTier(D.Contains(PadChoice) ? PadChoice : D.Last());
	return TEXT("teleport");
}

// ================================================================================================ monsters' height (tests, the fix)
TArray<FString> ARDDungeonGenerator::MeasureMonsterHeights()
{
	TArray<FString> Out;
	for (ARDMonster* M : GetMonsters())
		if (M && !M->IsDead()) Out.Add(FString::Printf(TEXT("%s|%.1f|%.1f"), *M->MonsterName.ToString(), M->GetDrawnBottom(), M->GetMesh()->GetRelativeLocation().Z));
	return Out;
}

// ================================================================================================ the section: cells, the pad
int32 ARDSection::CellOfDoor(int32 Door) const
{
	for (int32 I = 0; I < Cells.Num(); ++I) if (Cells[I].Door == Door) return I;
	return -1;
}

void ARDSection::PlaceCellOccupants()
{
	UWorld* W = GetWorld();
	if (!Generator || !W || !W->IsGameWorld() || Generator->PrisonerDefs.Num() == 0 || bCensus) return;
	for (int32 I = MistActors.Num() - 1; I >= 0; --I) if (Cast<ARDPrisoner>(MistActors[I])) { MistActors[I]->Destroy(); MistActors.RemoveAt(I); }
	FRandomStream R((int32)HashCombine((uint32)Seed ^ 0xCE11u, 77u));
	const int32 Tier = Generator->TierOf(Coord);
	TArray<int32> Kinds; Generator->MonsterKindsFor(Coord, Kinds);
	for (int32 I = 0; I < Cells.Num(); ++I)
	{
		FCell& C = Cells[I];
		const float U = R.FRand(), V = R.FRand();
		const int32 Pick = R.RandRange(0, 1 << 20);
		C.Occupant = 0;
		if (U >= Generator->CellOccupied) continue;
		const bool bMonster = V < Generator->CellMonsterShare && Kinds.Num() > 0;
		const FIntVector Key(Coord.X, Coord.Y, I);
		if (Generator->CellsOpened.Contains(Key)) { C.bOpened = true; continue; }        // (freed, or broken out: gone)
		const FVector In_ = C.Frame.GetLocation();
		const FVector Fw = C.Frame.GetRotation().GetForwardVector();             // (toward the room)
		if (bMonster)
		{
			ARDMonster* M = Generator->SpawnMonsterKind(Kinds[Pick % Kinds.Num()], In_ + Fw * 20.f, Tier, 1.f, 1.f, 1.f);
			if (!M) continue;
			M->bCaged = true;
			M->SetActorRotation(FRotator(0, Fw.Rotation().Yaw, 0));
			C.Occupant = 2; C.Who = M;
		}
		else
		{
			const FRDPrisonerDef& D = Generator->PrisonerDefs[Pick % Generator->PrisonerDefs.Num()];
			if (!D.Mesh) continue;
			FActorSpawnParameters Sp; Sp.SpawnCollisionHandlingOverride = ESpawnActorCollisionHandlingMethod::AlwaysSpawn;
			const FVector At = In_ + Fw * 45.f;
			ARDPrisoner* P = W->SpawnActor<ARDPrisoner>(ARDPrisoner::StaticClass(), FTransform(FRotator(0, Fw.Rotation().Yaw, 0), At), Sp);
			if (!P) continue;
			// (out through the door's gap, then away across the room)
			FVector Doorway, Exit; RDMCellWay(C.Frame, Generator->TileSize, Doorway, Exit);
			P->Init(D, Doorway, Exit, Exit + Fw * 600.f);
			MistActors.Add(P);
			C.Occupant = 1; C.Who = P;
		}
	}
}

FString ARDSection::DescribeCell(int32 Door) const
{
	const int32 C = CellOfDoor(Door);
	if (C < 0 || Cells[C].bOpened || Cells[C].Occupant == 0) return FString();
	if (Cells[C].Occupant == 1)
	{
		const ARDPrisoner* P = Cast<ARDPrisoner>(Cells[C].Who.Get());
		return FString::Printf(TEXT("unlock the cell: free the %s"), P ? *P->Title.ToLower() : TEXT("prisoner"));
	}
	return TEXT("the cell is locked from within: something stirs");
}

bool ARDSection::OpenCell(int32 Door)
{
	const int32 Ci = CellOfDoor(Door);
	if (Ci < 0 || !Generator) return false;
	FCell& C = Cells[Ci];
	if (C.bOpened || C.Occupant == 0) return false;
	C.bOpened = true;
	Generator->CellsOpened.Add(FIntVector(Coord.X, Coord.Y, Ci));
	if (Doors.IsValidIndex(C.Door) && !IsTargetOpen(true, C.Door)) ToggleDoor(C.Door, C.Frame.GetLocation() + C.Frame.GetRotation().GetForwardVector() * 400.f);
	URDCombatComponent* Pc = Generator->GetPlayerCombat();
	if (C.Occupant == 1)
	{
		ARDPrisoner* P = Cast<ARDPrisoner>(C.Who.Get());
		if (P) P->Free();
		// (the thanks: a thing of the tier's, picked from what prisoners give, by the cell)
		const int32 Tier = Generator->TierOf(Coord);
		TArray<FName> Can;
		for (const FName& Rw : Generator->PrisonerRewards)
		{
			const int32 Ix = Generator->FindItem(Rw);
			if (Ix >= 0 && (Generator->Items[Ix].Tiers.Num() == 0 || Generator->Items[Ix].Tiers.Contains(Tier))) Can.Add(Rw);
		}
		if (Can.Num() == 0) Can = Generator->PrisonerRewards;
		const FName Gift = Can.Num() > 0 ? Can[HashCombine((uint32)Generator->SessionSeed, GetTypeHash(FIntVector(Coord.X, Coord.Y, Ci))) % (uint32)Can.Num()] : NAME_None;
		if (Pc && !Gift.IsNone())
		{
			Pc->AddItem(Gift, 1);
			Pc->ShowMessage(FString::Printf(TEXT("The %s thanks you and gives you %s"), P ? *P->Title.ToLower() : TEXT("prisoner"), *Gift.ToString().ToLower()));
			Generator->LastFound = Gift; Generator->LastFoundList = { Gift }; Generator->LastFoundTime = GetWorld()->GetTimeSeconds();
		}
		++Generator->PrisonersFreed;
		Generator->PlaySoundAt(TEXT("Player.Loot"), C.Frame.GetLocation());
		UE_LOG(LogRDMistward, Log, TEXT("RDPRISONER freed in cell %d of (%d,%d): gave %s"), Ci, Coord.X, Coord.Y, *Gift.ToString());
	}
	else if (ARDMonster* M = Cast<ARDMonster>(C.Who.Get()))
	{
		FVector Doorway, Exit; RDMCellWay(C.Frame, Generator->TileSize, Doorway, Exit);
		M->Release(Doorway, Exit);
		++Generator->CellBreakouts;
		UE_LOG(LogRDMistward, Log, TEXT("RDPRISONER the monster in cell %d of (%d,%d) is out"), Ci, Coord.X, Coord.Y);
	}
	return true;
}

TArray<FString> ARDSection::GetCellLines() const
{
	TArray<FString> Out;
	for (int32 I = 0; I < Cells.Num(); ++I)
	{
		const FCell& C = Cells[I]; const FVector L = C.Frame.GetLocation();
		const AActor* Who = C.Who.Get(); const FVector WL = Who ? Who->GetActorLocation() : FVector::ZeroVector;
		// (cell|door|occupant|opened|middle x y z|someone|where x y z|yaw: the way the cell faces, into the room)
		Out.Add(FString::Printf(TEXT("%d|%d|%d|%d|%.0f|%.0f|%.0f|%d|%.0f|%.0f|%.0f|%.1f"), I, C.Door, (int32)C.Occupant, C.bOpened ? 1 : 0, L.X, L.Y, L.Z,
			Who ? 1 : 0, WL.X, WL.Y, WL.Z, C.Frame.Rotator().Yaw));
	}
	return Out;
}

void ARDSection::TickCells(float Dt, APawn* Her)
{
	if (!Her || Cells.Num() == 0) return;
	const FVector L = Her->GetActorLocation();
	// (a monster in a cell unlocks it itself when she comes near, and comes for her)
	for (int32 I = 0; I < Cells.Num(); ++I)
	{
		FCell& C = Cells[I];
		if (C.bOpened || C.Occupant != 2) continue;
		// (killed in its cell (a bolt through the bars): the cell is spent, and stays so when the set is built again)
		const ARDMonster* Mo = Cast<ARDMonster>(C.Who.Get());
		if (!Mo || Mo->IsDead()) { C.bOpened = true; if (Generator) Generator->CellsOpened.Add(FIntVector(Coord.X, Coord.Y, I)); continue; }
		if (FVector::Dist2D(L, C.Frame.GetLocation()) < 520.f && FMath::Abs(L.Z - C.Frame.GetLocation().Z) < 250.f) OpenCell(C.Door);
	}
}

void ARDSection::PlacePad()
{
	UWorld* W = GetWorld();
	if (!Generator || !Generator->bTeleporters || !W || !W->IsGameWorld() || bCensus) return;
	for (int32 I = MistActors.Num() - 1; I >= 0; --I) if (Cast<ARDTeleporter>(MistActors[I])) { MistActors[I]->Destroy(); MistActors.RemoveAt(I); }
	PadRoom = -1;
	const int32 Tier = Generator->TierOf(Coord);
	int32 Want = 0;
	if (const FIntPoint* Have = Generator->PadSections.Find(Tier)) { if (*Have == Coord) Want = Tier; }
	else if (Tier == 1 ? Generator->IsStartSection(Coord) : true) Want = Tier;          // (each tier's first set of rooms generated)
	if (Want == 0) return;
	// (the room: the great hall in the first tier; else the largest room near the set's middle, on a free tile with free
	// neighbours, off the lanes, as the anvil's)
	FVector At;
	if (const FVector* Old = Generator->Pads.Find(Want); Old && Generator->PadSections.Contains(Want)) At = *Old;
	else
	{
		TArray<int32> Order;
		const int32 Start = Generator->IsStartSection(Coord) ? RoomAt(FVector(Generator->TileSize * 0.5f, Generator->TileSize * 0.5f, 0.f)) : -1;
		for (int32 RI = 0; RI < Rooms.Num(); ++RI) if (Rooms[RI].Kind != ERDRoomKind::Junction && Rooms[RI].Kind != ERDRoomKind::Prison && (Start < 0 || RI == Start)) Order.Add(RI);
		auto Area = [this](int32 RI) { const FRoom& Rm = Rooms[RI]; return (Rm.Max.X - Rm.Min.X) * (Rm.Max.Y - Rm.Min.Y); };
		Order.Sort([&](int32 A, int32 B) { return Area(A) != Area(B) ? Area(A) > Area(B) : A < B; });
		FIntPoint Pick(-1, -1);
		for (const int32 RI : Order)
		{
			const FRoom& Rm = Rooms[RI];
			auto Free = [&](FIntPoint T) { return In(T) && Type[Idx(T)] == 1 && !Blocked[Idx(T)] && RoomAtLocal(T) == RI; };
			const FVector2D Mid((Rm.Min.X + Rm.Max.X) * 0.5f, (Rm.Min.Y + Rm.Max.Y) * 0.5f);
			float PickD = MAX_flt;
			for (int32 X = Rm.Min.X + 1; X < Rm.Max.X - 1; ++X)
				for (int32 Y = Rm.Min.Y + 1; Y < Rm.Max.Y - 1; ++Y)
				{
					if (X == Rm.Lane.X || Y == Rm.Lane.Y) continue;
					const FIntPoint T(X, Y);
					if (!Free(T) || !Free(T + FIntPoint(1, 0)) || !Free(T + FIntPoint(-1, 0)) || !Free(T + FIntPoint(0, 1)) || !Free(T + FIntPoint(0, -1))) continue;
					// (not where the anvil is)
					bool bAnvil = false;
					for (const FVector& A : AnvilPoints) if (FVector::Dist2D(A, TileWorld(T)) < 400.f) bAnvil = true;
					if (bAnvil) continue;
					const float D = FVector2D::DistSquared(FVector2D(X + 0.5f, Y + 0.5f), Mid);
					if (D < PickD) { PickD = D; Pick = T; }
				}
			if (Pick.X >= 0) { PadRoom = RI; break; }
		}
		if (Pick.X < 0) return;
		At = TileWorld(Pick);
		Generator->Pads.Add(Want, At);
		Generator->PadSections.Add(Want, Coord);
	}
	PadRoom = RoomAt(At);
	FActorSpawnParameters Sp; Sp.SpawnCollisionHandlingOverride = ESpawnActorCollisionHandlingMethod::AlwaysSpawn;
	ARDTeleporter* T = W->SpawnActor<ARDTeleporter>(ARDTeleporter::StaticClass(), FTransform(At), Sp);
	if (!T) return;
	T->Init(Generator, Want, Want > 1 && !Generator->PadRingsTaken.Contains(Want));
	Generator->PadActors.Add(Want, T);
	MistActors.Add(T);
	UE_LOG(LogRDMistward, Log, TEXT("RDTELEPORT pad of tier %d in room %d of (%d,%d)"), Want, PadRoom, Coord.X, Coord.Y);
}
