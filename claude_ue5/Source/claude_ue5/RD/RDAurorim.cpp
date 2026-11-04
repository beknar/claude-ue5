// mistward_castle's final boss (the user's spec of 2026-11-03; RDAurorim.h): Aurorim, the angel of four wings.
//   the monster   levitates (its mesh over its capsule, bobbing; down on the floor dead), throws a lance from afar (its shot
//                 carries a mesh: FRDMonsterDef's RangedMesh), calls a beam of light down from above at middle range (a mark on
//                 the floor, then the light: FRDMonsterDef's Beam*), and punches with wind round its fists (FistFx)
//   the generator when the last tier reaches the tiers' share it waits in a room of it she has explored, with 6 to 10 of the
//                 tier's monsters, scaled as the tier's boss; beside it the door to Brokenspire, sealed. Its death: its loot (the
//                 best of the last tier's things her hero can use), FinalBossGold, the castle conquered, the door open
//   the door      an arch with a grating in it; open, the grating sinks into the floor, a light fills the arch, and walking into
//                 it takes her to Brokenspire (ReturnToTown: before the castle's door)
#include "RD/RDAurorim.h"
#include "RD/RDDungeonGenerator.h"
#include "RD/RDMonster.h"
#include "RD/RDSection.h"
#include "RD/RDCombat.h"
#include "RD/RDMistward.h"
#include "RD/RDGameInstance.h"
#include "Components/CapsuleComponent.h"
#include "Components/SkeletalMeshComponent.h"
#include "Components/StaticMeshComponent.h"
#include "Engine/StaticMesh.h"
#include "Engine/StaticMeshActor.h"
#include "Engine/World.h"
#include "GameFramework/Character.h"
#include "GameFramework/CharacterMovementComponent.h"
#include "Kismet/GameplayStatics.h"
#include "NiagaraComponent.h"
#include "NiagaraFunctionLibrary.h"
#include "NiagaraSystem.h"
#include "Misc/CommandLine.h"
#include "Misc/FileHelper.h"
#include "Misc/Paths.h"
#include "Misc/Parse.h"

DEFINE_LOG_CATEGORY_STATIC(LogRDAurorim, Log, All);

namespace
{
	/** an effect on a bone of a mesh, following it (its scale into User.Scale or its component's) */
	UFXSystemComponent* RDAUFxOnBone(UFXSystemAsset* Asset, USkeletalMeshComponent* M, FName Bone, float Scale, bool bUser)
	{
		UNiagaraSystem* Ns = Cast<UNiagaraSystem>(Asset);
		if (!Ns || !M) return nullptr;
		UNiagaraComponent* C = UNiagaraFunctionLibrary::SpawnSystemAttached(Ns, M, Bone, FVector::ZeroVector, FRotator::ZeroRotator, FVector(1.f),
			EAttachLocation::SnapToTarget, false, ENCPoolMethod::None, false);
		if (!C) return nullptr;
		// (its place follows the bone; its turn and size stay its own: the bone's scale is the monster's)
		C->SetUsingAbsoluteRotation(true); C->SetUsingAbsoluteScale(true);
		C->SetWorldScale3D(FVector(bUser ? 1.f : Scale));
		if (bUser) C->SetVariableFloat(TEXT("User.Scale"), Scale);
		C->Activate(true);
		return C;
	}
	/** the floor under a point (a trace down), or the point */
	FVector RDAUFloor(UWorld* W, const FVector& At, const AActor* Ignore)
	{
		FHitResult H; FCollisionQueryParams Q(SCENE_QUERY_STAT(RDAuFloor), false, Ignore);
		FCollisionObjectQueryParams O; O.AddObjectTypesToQuery(ECC_WorldStatic); O.AddObjectTypesToQuery(ECC_WorldDynamic);
		if (W && W->LineTraceSingleByObjectType(H, At + FVector(0, 0, 50.f), At - FVector(0, 0, 600.f), O, Q)) return H.ImpactPoint;
		return At;
	}
}

// ================================================================================================ the monster
void ARDMonster::SetupBoss(const FRDMonsterDef& Def)
{
	// (the mesh's own height without the hover now in it: Empower calls this again on a monster just made)
	BaseMeshZ = GetMesh()->GetRelativeLocation().Z - HoverNow;
	HoverHeight = Def.HoverHeight; HoverBob = Def.HoverBob; HoverPeriod = FMath::Max(Def.HoverPeriod, 0.2f);
	RangedMesh = Def.RangedMesh; RangedMeshScale = Def.RangedMeshScale; RangedMeshRot = Def.RangedMeshRot;
	const ARDDungeonGenerator* G = Section ? Section->Generator.Get() : nullptr;
	bSkyBeam = Def.bSkyBeam && Def.BeamClip && G && G->bFinalBossOn;
	BeamMin = Def.BeamMin; BeamMax = Def.BeamMax; BeamShare = Def.BeamDamage; BeamRadius = Def.BeamRadius; BeamDelay = FMath::Max(Def.BeamDelay, 0.1f);
	BeamClip = Def.BeamClip; BeamRelease = FMath::Clamp(Def.BeamRelease, 0.05f, 0.95f);
	BeamFx = Def.BeamFx; BeamMarkFx = Def.BeamMarkFx; BeamHitFx = Def.BeamHitFx; BeamFxScale = Def.BeamFxScale; BeamMarkScale = Def.BeamMarkScale;
	bBeamFxUser = Def.bBeamFxUserScale; bBeamMarkUser = Def.bBeamMarkUserScale; bBeamHitUser = Def.bBeamHitUserScale;
	// (its wait scales as its blows' interval does with its tier, as its shot's)
	BeamWait = Def.BeamCooldown * (Def.AttackInterval > 0.f ? AttackInterval / Def.AttackInterval : 1.f);
	BeamWaitLeft = FMath::Max(BeamWaitLeft, 1.5f);
	FistFx = Def.FistFx; FistFxScale = Def.FistFxScale; FistFxUser = Def.FistFxUserScale; FistBones = Def.FistBones;
}

void ARDMonster::TickHover(float Dt)
{
	// (a blow cut short by a flinch, a stun or its death: the wind off its fists)
	if (FistFxLive.Num() > 0 && (AttackTime < 0.f || bDead)) EndFistFx();
	if (HoverHeight <= 0.f) return;
	HoverTime += Dt;
	const float Want = bDead ? 0.f : HoverHeight + HoverBob * FMath::Sin(2.f * PI * HoverTime / HoverPeriod);
	HoverNow = FMath::FInterpTo(HoverNow, Want, Dt, bDead ? 2.5f : 6.f);
	USkeletalMeshComponent* M = GetMesh();
	const FVector Rel = M->GetRelativeLocation();
	M->SetRelativeLocation(FVector(Rel.X, Rel.Y, BaseMeshZ + HoverNow));
}

bool ARDMonster::TrySkyBeam(AActor* P, const FVector& D, float Dist, float Dz, float Gap, float Dt)
{
	if (!bSkyBeam || !P || BeamWaitLeft > 0.f || AttackCooldown > 0.f || !BeamClip) return false;
	// (out of its blows' reach, in its range, not far above or below: the light falls where its foe stands)
	if (Gap <= Reach * 1.5f || Dist < BeamMin || Dist > BeamMax || Dz > 300.f) return false;
	Face(D, Dt);
	if (FVector::DotProduct(D.GetSafeNormal(), GetActorForwardVector()) < 0.8f) { SetWalkingAnim(false); return true; }
	GetMesh()->PlayAnimation(BeamClip, false);
	AttackLen = RDClipLength(BeamClip); AttackHit = AttackLen * BeamRelease; AttackTime = 0.f; bHitDone = false;
	bBeamSwing = true; bRangedSwing = false;
	++AttacksMade;
	if (ARDDungeonGenerator* G = Section ? Section->Generator.Get() : nullptr) G->PlaySoundAt(SndAttack, GetActorLocation());
	VoiceTimer = FMath::Max(VoiceTimer, 2.f);
	return true;
}

void ARDMonster::ReleaseBeam(AActor* P)
{
	ARDDungeonGenerator* G = Section ? Section->Generator.Get() : nullptr;
	if (!G || !P) return;
	// (where its foe stands now, on the floor: the mark, and the light a moment after; one who moves on is spared)
	const FVector At = RDAUFloor(GetWorld(), P->GetActorLocation(), P);
	const float Sc = GetMesh()->GetComponentScale().X / FMath::Max(GetMesh()->GetRelativeScale3D().X, 0.01f);
	G->QueueSkyBeam(this, At, BeamDelay, BeamRadius, Damage * BeamShare * (1.f - GetCurseShare()), BeamFx, BeamMarkFx, BeamHitFx, BeamFxScale, BeamMarkScale * FMath::Max(Sc, 0.5f),
		bBeamFxUser, bBeamMarkUser, bBeamHitUser);
	++BeamsCast;
}

void ARDMonster::StartFistFx()
{
	EndFistFx();
	for (const FName Bone : FistBones)
		for (int32 K = 0; K < FistFx.Num(); ++K)
			if (UFXSystemComponent* C = RDAUFxOnBone(FistFx[K], GetMesh(), Bone, FistFxScale.IsValidIndex(K) ? FistFxScale[K] : 1.f, FistFxUser.IsValidIndex(K) && FistFxUser[K]))
			{
				FistFxLive.Add(C); ++FistFxMade;
			}
}

void ARDMonster::EndFistFx()
{
	for (const TWeakObjectPtr<UFXSystemComponent>& W : FistFxLive)
		if (UFXSystemComponent* C = W.Get()) { C->DeactivateImmediate(); C->DestroyComponent(); }
	FistFxLive.Reset();
}

// ------------------------------------------------------------------------------------------------ his tactics (2026-11-04)
void ARDMonster::MakeFinalBoss(float WaitScale)
{
	bFinalBoss = true;
	const float S = FMath::Clamp(WaitScale, 0.2f, 2.f);
	RangedWait *= S; BeamWait *= S;
}

bool ARDMonster::CircleClear(FVector& Dir, const FVector& Fw, float In)
{
	// (a sphere a little under his capsule's width, low enough to meet the furniture, 1.6 m along the way)
	const FVector L = GetActorLocation() - FVector(0, 0, GetCapsuleComponent()->GetScaledCapsuleHalfHeight() * 0.4f);
	const float Rad = GetCapsuleComponent()->GetScaledCapsuleRadius() * 0.8f;
	FCollisionQueryParams Q(SCENE_QUERY_STAT(RDAuCircle), false, this);
	auto Way = [&](float Sign, float I) { return (FVector(-Fw.Y, Fw.X, 0.f) * Sign + Fw * I).GetSafeNormal2D(); };
	// (the way wanted either way round; then straight round her (along a wall at his back), then round and a little in)
	const TPair<float, float> Tries[] = { { CircleSign, In }, { -CircleSign, In }, { CircleSign, 0.f }, { -CircleSign, 0.f }, { CircleSign, 0.6f }, { -CircleSign, 0.6f } };
	for (const TPair<float, float>& T : Tries)
	{
		const float Sign = T.Key;
		const FVector W = Way(Sign, T.Value);
		if (!GetWorld()->SweepTestByChannel(L, L + W * 160.f, FQuat::Identity, ECC_Visibility, FCollisionShape::MakeSphere(Rad), Q))
		{
			if (Sign != CircleSign) { CircleSign = Sign; CircleFlip = 4.f; }
			Dir = W;
			return true;
		}
	}
	return false;
}

bool ARDMonster::TickFinalHold(AActor* P, const FVector& D, float Dist, float Dz, float Dt)
{
	ARDDungeonGenerator* G = Section ? Section->Generator.Get() : nullptr;
	if (!G || !P || Dz > 300.f || !G->FinalBossHolds(this)) return false;
	const float Near = G->FinalBossHold.X, Far = FMath::Max(G->FinalBossHold.Y, Near + 100.f);
	if (Dist > Far) return false;             // (farther: the chase brings him in to his lance's and light's range)
	const FVector L = GetActorLocation();
	// (her out of his sight (round a corner, behind a pillar): the chase brings him where he sees her)
	FCollisionQueryParams Qs(SCENE_QUERY_STAT(RDAuHoldSight), false, this); Qs.AddIgnoredActor(P);
	FCollisionObjectQueryParams O; O.AddObjectTypesToQuery(ECC_WorldStatic);
	if (GetWorld()->LineTraceTestByObjectType(L + FVector(0, 0, 60.f), P->GetActorLocation() + FVector(0, 0, 60.f), O, Qs)) return false;
	Face(D, Dt);
	const FVector Fw = D.GetSafeNormal();
	// (round her, turning now and then; out when she is nearer than his range's near end, in a little past its middle)
	CircleFlip -= Dt;
	if (CircleFlip <= 0.f) { CircleSign = -CircleSign; CircleFlip = 4.f; }
	const float In = Dist < Near ? -FMath::Clamp((Near - Dist) / 300.f, 0.4f, 1.5f) : (Dist > (Near + Far) * 0.5f ? 0.3f : 0.f);
	FVector Dir;
	if (!CircleClear(Dir, Fw, In))
	{
		// (walled in both ways round: straight back from her if that is clear, else he stands)
		Dir = Dist < Near ? -Fw : FVector::ZeroVector;
	}
	// (stuck on something the sweep missed (one of his band): the other way round)
	StuckTime = GetVelocity().Size2D() < 40.f ? StuckTime + Dt : 0.f;
	if (StuckTime > 0.7f) { StuckTime = 0.f; CircleSign = -CircleSign; CircleFlip = 4.f; }
	GetCharacterMovement()->MaxWalkSpeed = WalkSpeed * SpeedMul();
	if (!Dir.IsZero()) AddMovementInput(Dir, 0.85f);
	bCircling = true; HoldSeconds += Dt;
	const float Speed = GetVelocity().Size2D();
	SetWalkingAnim(Speed > 25.f);
	if (bWalkingAnim) GetMesh()->SetPlayRate(FMath::Clamp(Speed / ClipSpeed, 0.4f, 1.6f));
	return true;
}

void ARDMonster::CircleStep(const FVector& D, float Gap, float Dt)
{
	Face(D, Dt);
	CircleFlip -= Dt;
	if (CircleFlip <= 0.f) { CircleSign = -CircleSign; CircleFlip = 3.f; }
	// (round her at his reach: a little in as the step round carries him out, a little out when he is on her)
	const float In = Gap > Reach * 0.45f ? 0.35f : (Gap < Reach * 0.15f ? -0.3f : 0.f);
	FVector Dir;
	if (!CircleClear(Dir, D.GetSafeNormal(), In)) { SetWalkingAnim(false); return; }
	AddMovementInput(Dir, 0.45f);
	bCircling = true; CircleSeconds += Dt;
	SetWalkingAnim(GetVelocity().Size2D() > 25.f);
}

TArray<FString> ARDMonster::GetFistFxLines() const
{
	// (each effect round a fist: its system, its bone, how far it is from that bone (cm), its live particles)
	TArray<FString> Out;
	for (const TWeakObjectPtr<UFXSystemComponent>& W : FistFxLive)
	{
		const UFXSystemComponent* C = W.Get();
		if (!C) continue;
		const FName Bone = C->GetAttachSocketName();
		const float Off = FVector::Dist(C->GetComponentLocation(), GetMesh()->GetSocketLocation(Bone));
		const UNiagaraComponent* Nc = Cast<UNiagaraComponent>(C);
		Out.Add(FString::Printf(TEXT("%s|%s|%.1f|%d"), Nc && Nc->GetAsset() ? *Nc->GetAsset()->GetName() : TEXT("?"), *Bone.ToString(), Off, Nc ? RDNiagaraParticles(Nc) : 0));
	}
	return Out;
}

// ================================================================================================ the door
ARDFinalDoor::ARDFinalDoor()
{
	PrimaryActorTick.bCanEverTick = true;
	Pivot = CreateDefaultSubobject<USceneComponent>(TEXT("Pivot")); RootComponent = Pivot;
	Frame = CreateDefaultSubobject<UStaticMeshComponent>(TEXT("Frame")); Frame->SetupAttachment(Pivot);
	Gate = CreateDefaultSubobject<UStaticMeshComponent>(TEXT("Gate")); Gate->SetupAttachment(Pivot);
	for (UStaticMeshComponent* C : { Frame.Get(), Gate.Get() })
	{
		C->SetMobility(EComponentMobility::Movable);
		C->SetCollisionEnabled(ECollisionEnabled::QueryAndPhysics);
		C->SetCollisionResponseToAllChannels(ECR_Block);
		C->SetCollisionResponseToChannel(ECC_Camera, ECR_Ignore);
	}
}

void ARDFinalDoor::Init(ARDDungeonGenerator* Gen, UStaticMesh* FrameMesh, UStaticMesh* GateMesh, UFXSystemAsset* Fx, float Height, float FxScale)
{
	Generator = Gen; GlowFx = Fx; GlowScale = FxScale;
	float Sc = 1.f;
	if (FrameMesh)
	{
		Frame->SetStaticMesh(FrameMesh);
		const FBox B = FrameMesh->GetBoundingBox();
		Sc = Height / FMath::Max(B.Max.Z - B.Min.Z, 1.f);
		Frame->SetRelativeScale3D(FVector(Sc));
		// (its bottom's middle on the pivot)
		Frame->SetRelativeLocation(FVector(-(B.Min.X + B.Max.X) * 0.5f * Sc, -(B.Min.Y + B.Max.Y) * 0.5f * Sc, -B.Min.Z * Sc));
		// (the arch's opening: a little over half its width, to where its point begins)
		OpenWidth = (B.Max.X - B.Min.X) * Sc * 0.5f; OpenHeight = Height * 0.68f;
	}
	if (GateMesh)
	{
		Gate->SetStaticMesh(GateMesh);
		const FBox G = GateMesh->GetBoundingBox();
		const FVector S(OpenWidth / FMath::Max(G.Max.X - G.Min.X, 1.f), 2.f, OpenHeight / FMath::Max(G.Max.Z - G.Min.Z, 1.f));
		Gate->SetRelativeScale3D(S);
		GateZ0 = -G.Min.Z * S.Z;
		Gate->SetRelativeLocation(FVector(-(G.Min.X + G.Max.X) * 0.5f * S.X, -(G.Min.Y + G.Max.Y) * 0.5f * S.Y, GateZ0));
	}
	else Gate->SetVisibility(false);
}

void ARDFinalDoor::Open()
{
	if (bOpen) return;
	bOpen = true;
	if (GlowFx && !Glow)
		Glow = RDMSpawnFx(this, GlowFx, FVector(0, 0, OpenHeight * 0.45f), FRotator::ZeroRotator, GlowScale, Pivot, false, false);
	if (ARDDungeonGenerator* G = Generator.Get()) G->PlaySoundAt(TEXT("Env.Generate"), GetActorLocation());
	UE_LOG(LogRDAurorim, Log, TEXT("RDFINAL the door to Brokenspire is open at (%.0f, %.0f)"), GetActorLocation().X, GetActorLocation().Y);
}

FVector ARDFinalDoor::GetApproach(float Out) const
{
	// (its face looks along its +Y: into the room)
	return GetActorLocation() + GetActorRightVector() * Out;
}

void ARDFinalDoor::Tick(float Dt)
{
	Super::Tick(Dt);
	if (!bOpen) return;
	if (OpenAlpha < 1.f)
	{
		// (the grating sinks into the floor over two seconds; past half way she can walk in)
		OpenAlpha = FMath::Min(1.f, OpenAlpha + Dt / 2.f);
		const FVector Rel = Gate->GetRelativeLocation();
		Gate->SetRelativeLocation(FVector(Rel.X, Rel.Y, GateZ0 - OpenAlpha * (OpenHeight + 30.f)));
		if (OpenAlpha > 0.5f) Gate->SetCollisionEnabled(ECollisionEnabled::NoCollision);
		if (OpenAlpha >= 1.f) Gate->SetVisibility(false);
	}
	ARDDungeonGenerator* G = Generator.Get();
	if (bTravelled || !G || OpenAlpha < 0.5f) return;
	const APawn* Her = UGameplayStatics::GetPlayerPawn(this, 0);
	const URDCombatComponent* Pc = G->GetPlayerCombat();
	if (!Her || (Pc && Pc->IsDead())) return;
	// (in the opening: within its width, at its face (its depth is the arch's), not above it)
	const FVector L = GetActorTransform().InverseTransformPosition(Her->GetActorLocation());
	const float Depth = Frame->Bounds.BoxExtent.Size2D() > 0.f ? FMath::Min(Frame->Bounds.BoxExtent.X, Frame->Bounds.BoxExtent.Y) : 60.f;
	const bool bInOpening = FMath::Abs(L.X) < OpenWidth * 0.5f && L.Y < Depth + 90.f && L.Y > -Depth - 60.f && L.Z < OpenHeight + 100.f;
	if (!bArmed) { bArmed = OpenAlpha >= 1.f && !bInOpening; return; }
	if (bInOpening)
	{
		bTravelled = true;
		UE_LOG(LogRDAurorim, Log, TEXT("RDFINAL she walks through the door to Brokenspire"));
		G->ReturnToTown();
	}
}

FString ARDFinalDoor::GetDoorState() const
{
	const FVector L = GetActorLocation(), F = GetActorRightVector();
	const UNiagaraComponent* Nc = Cast<UNiagaraComponent>(Glow.Get());
	return FString::Printf(TEXT("%d|%.2f|%d|%.0f|%.0f|%.0f|%.2f|%.2f|%.0f|%.0f|%.0f|%d|%d|%d"), bOpen ? 1 : 0, OpenAlpha, bTravelled ? 1 : 0, L.X, L.Y, L.Z, F.X, F.Y,
		OpenWidth, OpenHeight, Gate->GetRelativeLocation().Z, Gate->GetCollisionEnabled() != ECollisionEnabled::NoCollision ? 1 : 0, Glow ? 1 : 0, Nc ? RDNiagaraParticles(Nc) : 0);
}

// ================================================================================================ the generator
FString ARDDungeonGenerator::GetTierShareLine(int32 Tier) const
{
	FIntVector Done, All;
	const bool bComplete = GetTierTally(Tier, Done, All);
	return FString::Printf(TEXT("%d/%d|%d/%d|%d/%d|%d"), Done.X, All.X, Done.Y, All.Y, Done.Z, All.Z, bComplete ? 1 : 0);
}

void ARDDungeonGenerator::CheckFinalBoss()
{
	if (!bFinalBossOn || bFinalBossPlaced || bFinalBossSlain || FinalBossKind.IsNone() || MaxTier <= 0 || bTown) return;
	if (MaxTier > 1 && !TiersOpened.Contains(MaxTier)) return;
	// (the last tier at the tiers' share, its sets she has not reached counted without building them)
	FIntVector Done, All;
	if (!GetTierTally(MaxTier, Done, All) || All.X <= 0) return;
	auto Enough = [this](int32 D, int32 A) { return D >= FMath::CeilToInt(A * FMath::Min(TierOpenShare, 1.f) - 1e-3f); };
	if (!(Enough(Done.X, All.X) && Enough(Done.Y, All.Y) && Enough(Done.Z, All.Z))) return;
	UE_LOG(LogRDAurorim, Log, TEXT("RDFINAL tier %d at its share: %d/%d rooms, %d/%d killed, %d/%d looted"), MaxTier, Done.X, All.X, Done.Y, All.Y, Done.Z, All.Z);
	// (no room for him yet (none explored big enough, or only hers): tried again in 10 s, not every second)
	if (!PlaceFinalBoss()) FinalRestoreTry = 10.f;
}

ARDMonster* ARDDungeonGenerator::GetFinalBoss() const
{
	for (const FEncounter& E : Encounters)
		if (E.bFinal && E.Live.Num() > 0) return E.Live[0].Get();
	return nullptr;
}

bool ARDDungeonGenerator::PlaceFinalBoss()
{
	const int32 Boss = Monsters.IndexOfByPredicate([this](const FRDMonsterDef& D) { return D.Name == FinalBossKind; });
	if (Boss < 0 || !Monsters[Boss].Mesh) { UE_LOG(LogRDAurorim, Warning, TEXT("RDFINAL no monster %s"), *FinalBossKind.ToString()); return false; }
	ARDSection* S = nullptr; int32 Room = -1;
	// (the showcase: the room it chose)
	if (bFinalShowOn && FinalShowRoom >= 0) { S = GetSection(FinalShowSet); Room = FinalShowRoom; }
	if ((!S || Room < 0) && !PickExploredRoom(FMath::Max(MaxTier, 1), 7, S, Room)) { UE_LOG(LogRDAurorim, Warning, TEXT("RDFINAL no explored room of tier %d to set him in"), MaxTier); return false; }
	FEncounter E; E.Tier = FMath::Max(MaxTier, 1); E.bBoss = true; E.bFinal = true; E.Section = S->Coord; E.Room = Room; E.At = S->GetRoomCenter(Room);
	TArray<int32> Kinds; MonsterKindsFor(FIntPoint(FMath::Max(MaxTier - 1, 0), 0), Kinds);
	Kinds.Remove(Boss);
	FRandomStream R((int32)HashCombine((uint32)SessionSeed ^ 0xA0A0u, GetTypeHash(MaxTier)));
	const int32 Band = Kinds.Num() > 0 ? R.RandRange(FinalBossMinions.X, FinalBossMinions.Y) : 0;
	TArray<FVector> Free = S->GetRoomFreeTiles(Room);
	if (Free.Num() == 0) return false;
	Free.Sort([&E](const FVector& A, const FVector& B) { return FVector::DistSquared(A, E.At) < FVector::DistSquared(B, E.At); });
	E.Kinds.Add(Boss); E.Spots.Add(Free[0]);
	// (his band round him: every other free tile out from him while there are enough, then every one; with more of them than
	// tiles, round the tiles again, each round set off from the tile's middle a different way (never stacked, never on him))
	const int32 Others = Free.Num() - 1;
	const int32 Step = Others > 2 * Band ? 2 : 1;
	for (int32 I = 0; I < Band; ++I)
	{
		E.Kinds.Add(Kinds[R.RandRange(0, Kinds.Num() - 1)]);
		const int32 K = I * Step;
		const int32 Turn = Others > 0 ? K / Others : I + 1;
		const FVector Base = Others > 0 ? Free[1 + K % Others] : Free[0];
		const float A = Turn * 2.1f;
		E.Spots.Add(Base + (Turn > 0 ? FVector(FMath::Cos(A), FMath::Sin(A), 0.f) * TileSize * 0.35f : FVector::ZeroVector));
	}
	E.Dead.Init(false, E.Kinds.Num());
	const FString Name = Monsters[Boss].Title.IsEmpty() ? Monsters[Boss].Name.ToString() : Monsters[Boss].Title;
	E.Label = FString::Printf(TEXT("FINAL BOSS: %s"), *Name.ToUpper());
	// (the door: against a wall of the room, the farthest from its middle, looking in. A wall: nothing to walk on behind the
	// tile and no door there (a hallway or a doorway behind it is the room's way out, which the sealed arch would block))
	const FVector C = S->GetRoomCenter(Room);
	float BestD = -1.f; FVector DoorAt = FVector::ZeroVector, Out = FVector::ZeroVector;
	static const FVector Dirs[4] = { FVector(1, 0, 0), FVector(-1, 0, 0), FVector(0, 1, 0), FVector(0, -1, 0) };
	auto FindWall = [&](bool bOffHim)
	{
		for (const FVector& T : Free)
			for (const FVector& Dd : Dirs)
			{
				const FVector Nb = T + Dd * TileSize;
				if (S->RoomAt(Nb) == Room) continue;
				const FIntPoint Tl = S->WorldToLocal(T), Nl = S->WorldToLocal(Nb);
				if (S->IsWalkable(Nl) || S->DoorBetween(Tl, Nl) >= 0) continue;
				if (FVector::DotProduct((T - C) * FVector(1, 1, 0), Dd) < 0.f) continue;
				if (bOffHim && FVector::DistSquared(T, E.Spots[0]) < FMath::Square(TileSize * 1.5f)) continue;     // (not on him)
				const float Dc = FVector::Dist2D(T, C);
				if (Dc > BestD) { BestD = Dc; DoorAt = T + Dd * (TileSize * 0.5f - 30.f); Out = -Dd; }
			}
	};
	FindWall(true);
	if (BestD < 0.f) FindWall(false);       // (a small room: beside him rather than none)
	Encounters.Add(E);
	RespawnEncounters(S);
	if (BestD >= 0.f)
	{
		FActorSpawnParameters Sp; Sp.SpawnCollisionHandlingOverride = ESpawnActorCollisionHandlingMethod::AlwaysSpawn;
		// (its face, its +Y, looks into the room)
		const FRotator Rot(0.f, FMath::RadiansToDegrees(FMath::Atan2(Out.Y, Out.X)) - 90.f, 0.f);
		FinalDoor = GetWorld()->SpawnActor<ARDFinalDoor>(ARDFinalDoor::StaticClass(), FTransform(Rot, FVector(DoorAt.X, DoorAt.Y, DoorAt.Z)), Sp);
		if (FinalDoor) FinalDoor->Init(this, FinalDoorFrame, FinalDoorGate, FinalDoorFx, FinalDoorHeight, FinalDoorFxScale);
	}
	bFinalBossPlaced = true;
	if (bTownLink) TownCountMax(TEXT("finalboss:placed"), 1);
	FString Where = TEXT("A ROOM YOU HAVE SEEN");
	if (const FRDSectionMap* M = MapData.Find(S->Coord); M && M->Rects.IsValidIndex(Room)) Where = TEXT("THE ") + KindName(M->Rects[Room].Kind).ToUpper();
	TierNotice = FString::Printf(TEXT("TIER %d HALF CLEARED  -  %s WAITS IN %s (SEE YOUR MAP)"), E.Tier, *Name.ToUpper(), *Where); TierNoticeTime = GetWorld()->GetTimeSeconds();
	if (const AActor* Who = GetTrackedActor()) PlaySoundAt(TEXT("Env.Generate"), Who->GetActorLocation());
	UE_LOG(LogRDAurorim, Log, TEXT("RDFINAL %s and %d more in room %d of (%d,%d); the door %s"), *Name, E.Kinds.Num() - 1, Room, S->Coord.X, S->Coord.Y,
		FinalDoor ? *FString::Printf(TEXT("at (%.0f, %.0f)"), FinalDoor->GetActorLocation().X, FinalDoor->GetActorLocation().Y) : TEXT("not placed (no wall)"));
	return true;
}

FName ARDDungeonGenerator::PickFinalReward() const
{
	const int32 T = FMath::Max(MaxTier, 1);
	auto OfTier = [T](const FRDItemDef& It) { return It.Tiers.Contains(T); };
	// a weapon she wields (her best blow), else armour she wears (its best rating), else the best ring of her kind
	FName Best = NAME_None; float BestV = -1.f;
	for (const FRDItemDef& It : Items)
		if (It.Kind == ERDItemKind::Weapon && OfTier(It))
			for (const FRDWeaponFit& F : It.WeaponFits)
				if (F.Hero == CurrentHero && F.Weapon.Damage > BestV) { BestV = F.Weapon.Damage; Best = It.Name; }
	if (!Best.IsNone()) return Best;
	for (const FRDItemDef& It : Items)
		if (It.Kind == ERDItemKind::Armour && OfTier(It) && ArmourRefusal(It, It.Name.ToString()).IsEmpty() && It.DamageRating > BestV) { BestV = It.DamageRating; Best = It.Name; }
	if (!Best.IsNone()) return Best;
	const FString H = CurrentHero.ToString();
	const ERDRingKind Want = H.Contains(TEXT("Rogue")) ? ERDRingKind::Dexterity : (H.Contains(TEXT("Warrior")) || H.Contains(TEXT("Martial")) ? ERDRingKind::Health : ERDRingKind::Magic);
	for (const FRDItemDef& It : Items)
		if (It.Kind == ERDItemKind::Ring && It.RingKind == Want && It.Amount > BestV) { BestV = It.Amount; Best = It.Name; }
	return Best;
}

void ARDDungeonGenerator::OnFinalBossKilled(ARDMonster* Boss)
{
	if (bFinalBossSlain) return;
	bFinalBossSlain = true;
	if (bTownLink) TownCountMax(TEXT("finalboss"), 1);
	const FName Item = PickFinalReward();
	const FVector At = Boss ? Boss->GetActorLocation() : FVector::ZeroVector;
	if (!Item.IsNone())
		if (ARDLootPile* P = DropLoot(At + FVector(0, 0, 100.f), { Item }, { -1.f })) P->bHers = false;
	AddGold(FinalBossGold, TEXT("the final boss"));
	FinalReward = FString::Printf(TEXT("%s|%d"), *Item.ToString(), FinalBossGold);
	const FString Name = Boss && !Boss->Title.IsEmpty() ? Boss->Title : FinalBossKind.ToString();
	// (the lights he had called and not yet fallen go out with him)
	for (FSkyBeam& B : SkyBeams) if (UFXSystemComponent* M = B.Mark.Get()) { M->DeactivateImmediate(); M->DestroyComponent(); }
	SkyBeams.Reset();
	TierNotice = FinalDoor ? TEXT("MISTWARD CASTLE IS CONQUERED  -  THE DOOR TO BROKENSPIRE IS OPEN") : TEXT("MISTWARD CASTLE IS CONQUERED"); TierNoticeTime = GetWorld()->GetTimeSeconds();
	if (PlayerCombat) PlayerCombat->ShowMessage(FString::Printf(TEXT("Victory: %s falls. %d gold%s.%s"), *Name, FinalBossGold,
		Item.IsNone() ? TEXT("") : *FString::Printf(TEXT(", and %s lies where he fell"), *Item.ToString()), FinalDoor ? TEXT(" The door to Brokenspire is open.") : TEXT("")));
	if (FinalDoor) FinalDoor->Open();
	UE_LOG(LogRDAurorim, Log, TEXT("RDFINAL %s slain: %s, %d gold; the door %s"), *Name, *Item.ToString(), FinalBossGold, FinalDoor ? TEXT("opens") : TEXT("(none)"));
}

void ARDDungeonGenerator::QueueSkyBeam(ARDMonster* From, const FVector& At, float Delay, float Radius, float Damage, UFXSystemAsset* Fx, UFXSystemAsset* MarkFx, UFXSystemAsset* HitFx, float FxScale, float MarkScale, bool bFxUser, bool bMarkUser, bool bHitUser)
{
	FSkyBeam B; B.From = From; B.At = At; B.Left = Delay; B.Radius = Radius; B.Damage = Damage; B.Fx = Fx; B.HitFx = HitFx; B.FxScale = FxScale; B.bFxUser = bFxUser; B.bHitUser = bHitUser;
	if (MarkFx) B.Mark = RDMSpawnFx(this, MarkFx, At + FVector(0, 0, 3.f), FRotator::ZeroRotator, MarkScale, nullptr, bMarkUser, false);
	SkyBeams.Add(B);
	SkyBeamStats.FindOrAdd(TEXT("called"))++;
}

bool ARDDungeonGenerator::FinalBossHolds(const ARDMonster* Boss) const
{
	if (!Boss || !Boss->bFinalBoss || Boss->IsDead() || FinalBossHold.Y <= 0.f || FinalBandNear <= FinalBossCloseBand) return false;
	// (struck lately: he fights back)
	return GetWorld()->GetTimeSeconds() - Boss->LastHurtTime >= FinalBossStruckHold;
}

void ARDDungeonGenerator::TickFinal(float Dt)
{
	// (his band near him: his tactics hold him back while they fight)
	// (and any of them after her: he joins the fight from farther)
	FinalBandNear = 0; bFinalBandFighting = false;
	for (const FEncounter& E : Encounters)
		if (E.bFinal && E.Live.Num() > 0)
			if (const ARDMonster* B = E.Live[0].Get(); B && !B->IsDead())
				for (int32 I = 1; I < E.Live.Num(); ++I)
					if (const ARDMonster* M = E.Live[I].Get(); M && !M->IsDead())
					{
						if (FVector::Dist2D(M->GetActorLocation(), B->GetActorLocation()) < 2500.f) ++FinalBandNear;
						if (M->IsAggro() && !M->IsAlly()) bFinalBandFighting = true;
					}
	// the light from above: the mark's moment over, it falls
	if (SkyBeams.Num() > 0)
	{
		URDCombatComponent* Pc = GetPlayerCombat();
		AActor* Her = Pc ? Pc->GetOwner() : nullptr;
		for (int32 I = SkyBeams.Num() - 1; I >= 0; --I)
		{
			FSkyBeam& B = SkyBeams[I];
			B.Left -= Dt;
			if (B.Left > 0.f) continue;
			if (UFXSystemComponent* M = B.Mark.Get()) { M->Deactivate(); ShotFxEnding.Add(TPair<TWeakObjectPtr<UFXSystemComponent>, float>(B.Mark, 0.3f)); }
			// (the light lasts a moment and fades: the pack's systems loop, they are ended)
			if (UFXSystemComponent* F = RDMSpawnFx(this, B.Fx, B.At, FRotator::ZeroRotator, B.FxScale, nullptr, B.bFxUser, false)) ShotFxEnding.Add(TPair<TWeakObjectPtr<UFXSystemComponent>, float>(F, 1.6f));
			if (UFXSystemComponent* F = RDMSpawnFx(this, B.HitFx, B.At, FRotator::ZeroRotator, B.FxScale, nullptr, B.bHitUser, false)) ShotFxEnding.Add(TPair<TWeakObjectPtr<UFXSystemComponent>, float>(F, 2.2f));
			PlaySoundAt(TEXT("Monster.ShotHit"), B.At);
			SkyBeamStats.FindOrAdd(TEXT("fell"))++;
			// (her within its round, not far above or below it; then her allies)
			auto Within = [&B](const AActor* A) { return A && FVector::Dist2D(A->GetActorLocation(), B.At) <= B.Radius && FMath::Abs(A->GetActorLocation().Z - B.At.Z) < 300.f; };
			if (Her && Pc && !Pc->IsDead() && Within(Her))
			{
				Pc->ApplyDamage(B.Damage, B.From.Get());
				SkyBeamStats.FindOrAdd(TEXT("on_her"))++;
				LastShotOnHer = FString::Printf(TEXT("%s|%.1f|%.1f|light from above"), B.From.IsValid() ? *B.From->MonsterName.ToString() : TEXT("?"), B.Damage, B.From.IsValid() ? B.From->GetDamage() : 0.f);
			}
			for (ARDMonster* Al : GetAllies())
				if (IsValid(Al) && !Al->IsDead() && Within(Al)) { Al->ApplyDamageAt(B.Damage, B.From.Get(), &B.At); SkyBeamStats.FindOrAdd(TEXT("on_ally"))++; }
			SkyBeams.RemoveAtSwap(I);
		}
	}
	// (the last tier's share looked at once a second; the final boss set again after a way back into the castle)
	FinalRestoreTry -= Dt;
	if (FinalRestoreTry > 0.f) return;
	FinalRestoreTry = 1.f;
	if (bFinalRestorePending && !bFinalBossPlaced && !bFinalBossSlain) { if (PlaceFinalBoss()) bFinalRestorePending = false; else FinalRestoreTry = 10.f; return; }
	CheckFinalBoss();
}

void ARDDungeonGenerator::ResetFinal()
{
	for (FSkyBeam& B : SkyBeams) if (UFXSystemComponent* M = B.Mark.Get()) { M->DeactivateImmediate(); M->DestroyComponent(); }
	SkyBeams.Reset(); SkyBeamStats.Reset();
	if (FinalDoor) { if (FinalDoor->Glow) { FinalDoor->Glow->DeactivateImmediate(); FinalDoor->Glow->DestroyComponent(); } FinalDoor->Destroy(); }
	FinalDoor = nullptr;
	bFinalBossPlaced = false; bFinalBossSlain = false; bFinalRestorePending = false; FinalReward.Reset();
}

FString ARDDungeonGenerator::GetFinalBossState() const
{
	const FEncounter* E = Encounters.FindByPredicate([](const FEncounter& X) { return X.bFinal; });
	int32 BandAlive = 0;
	const ARDMonster* Boss = nullptr;
	if (E)
		for (int32 I = 0; I < E->Live.Num(); ++I)
		{
			const ARDMonster* M = E->Live[I].Get();
			if (I == 0) Boss = M;
			else if (M && !M->IsDead()) ++BandAlive;
		}
	return FString::Printf(TEXT("%d|%d|%d|%d|%d|%d|%d|%d|%.0f|%s|%s"), bFinalBossPlaced ? 1 : 0, bFinalBossSlain ? 1 : 0, FinalDoor && FinalDoor->bOpen ? 1 : 0,
		E ? E->Section.X : 0, E ? E->Section.Y : 0, E ? E->Room : -1, BandAlive, Boss && !Boss->IsDead() ? 1 : 0, Boss ? Boss->GetHealth() : 0.f, *FinalReward,
		*GetTierShareLine(FMath::Max(MaxTier, 1)));
}

TArray<FString> ARDDungeonGenerator::GetSkyBeamLines() const
{
	TArray<FString> Out;
	for (const FSkyBeam& B : SkyBeams) Out.Add(FString::Printf(TEXT("%.0f|%.0f|%.0f|%.2f|%.0f|%.1f"), B.At.X, B.At.Y, B.At.Z, B.Left, B.Radius, B.Damage));
	return Out;
}

// ================================================================================================ the showcase (a reel of the fight)
void ARDDungeonGenerator::StartFinalShow(const FString& Go, const FString& Done)
{
	bFinalShowOn = true; bFinalShowCmdRead = true; FinalShowPhase = 0; FinalShowT = FinalShowFightT = FinalShowCheck = 0.f;
	FinalShowGo = Go; FinalShowDone = Done; FinalShowResult.Reset(); FinalShowKit.Reset(); FinalShowGoLine.Reset();
	UE_LOG(LogRDAurorim, Log, TEXT("RDSHOW begun (%s)%s%s"), bTown ? TEXT("the town: into the castle") : TEXT("the castle"),
		Go.IsEmpty() ? TEXT("") : *FString::Printf(TEXT(", waits for %s"), *Go), Done.IsEmpty() ? TEXT("") : *FString::Printf(TEXT(", writes %s"), *Done));
}

FString ARDDungeonGenerator::GetFinalShowState() const
{
	const ARDMonster* Boss = GetFinalBoss();
	const FEncounter* E = Encounters.FindByPredicate([](const FEncounter& X) { return X.bFinal; });
	int32 Band = 0;
	if (E) for (int32 I = 1; I < E->Live.Num(); ++I) if (const ARDMonster* M = E->Live[I].Get(); M && !M->IsDead()) ++Band;
	return FString::Printf(TEXT("%d|%.1f|%.1f|%.0f|%.0f|%.0f|%d|%s|%s"), bFinalShowOn ? FinalShowPhase : -1, FinalShowT, FinalShowFightT,
		PlayerCombat ? PlayerCombat->GetHealth() : 0.f, PlayerCombat ? PlayerCombat->GetMaxHealth() : 0.f, Boss && !Boss->IsDead() ? Boss->GetHealth() : 0.f, Band, *FinalShowResult, *FinalShowKit);
}

void ARDDungeonGenerator::TickFinalShow(float RealDt)
{
	// (the command line, once a game: -RDFinalShow [-RDShowGo=<file>] [-RDShowDone=<file>])
	URDGameInstance* GI = URDGameInstance::Of(this);
	if (!bFinalShowCmdRead)
	{
		bFinalShowCmdRead = true;
		if (GI && !GI->bFinalShowRead)
		{
			GI->bFinalShowRead = true;
			GI->bFinalShow = FParse::Param(FCommandLine::Get(), TEXT("RDFinalShow"));
			FParse::Value(FCommandLine::Get(), TEXT("RDShowGo="), GI->FinalShowGo);
			FParse::Value(FCommandLine::Get(), TEXT("RDShowDone="), GI->FinalShowDone);
			FParse::Value(FCommandLine::Get(), TEXT("RDShowReady="), GI->FinalShowReady);
		}
		// (in the castle after the town: the show goes on there)
		if (GI && GI->bFinalShow && !bTown && bFinalBossOn) { StartFinalShow(GI->FinalShowGo, GI->FinalShowDone); FinalShowReady = GI->FinalShowReady; }
	}
	// the town: into the castle, once she stands in it
	if (bTown)
	{
		if (GI && GI->bFinalShow && !GI->bFinalShowEntered && bTownPlaced && PlayerCombat && !bTownTraveling)
		{
			GI->bFinalShowEntered = true;
			UE_LOG(LogRDAurorim, Log, TEXT("RDSHOW the town: into the castle"));
			EnterCastle();
		}
		return;
	}
	if (!bFinalShowOn) return;
	const float Dt = FMath::Min(RealDt, 0.1f);
	FinalShowT += Dt;
	APlayerController* PC = UGameplayStatics::GetPlayerController(this, 0);
	ACharacter* Her = PC ? Cast<ACharacter>(PC->GetPawn()) : nullptr;
	URDCombatComponent* Pc = PlayerCombat;
	if (!Her || !Pc) return;
	auto Done = [this](const FString& Why)
	{
		FinalShowResult = Why; FinalShowPhase = 9;
		StopAutoplay(TEXT("the showcase's end"));
		if (FinalShowAggro > 0.f) { AggroDistance = FinalShowAggro; LoseDistance = FinalShowLose; }
		// (with the go's measures, the fight's order and moves, and its length: a Shipping game writes no log)
		const FString Moves = FString::Printf(TEXT("his band's last fell at %.1f s; her first blow on him at %.1f s, %d of his band alive then; he held back circling %.1f s, ")
			TEXT("stepped round her %.1f s; she stepped round him %.1f s, left %d light marks, %d of %d lights fell on her; her lowest %.0f of %.0f hp; his %.0f hp ")
			TEXT("(a tier's boss's x%.2f), blows x%.2f, waits x%.2f"),
			FinalShowBandDoneT, FinalShowFirstHitT, FinalShowBandAtHit, FinalShowHoldS, FinalShowBossCircleS, AutoplayCircleSeconds,
			AutoplayStats.FindRef(TEXT("light marks left")), SkyBeamStats.FindRef(TEXT("on_her")), SkyBeamStats.FindRef(TEXT("fell")),
			FinalShowMinHp, PlayerCombat ? PlayerCombat->GetMaxHealth() : 0.f, FinalShowBossMaxHp, FinalBossHealth, FinalBossDamage, FinalBossWaitScale);
		if (!FinalShowDone.IsEmpty()) FFileHelper::SaveStringToFile(FString::Printf(TEXT("%s | %s | %s | the fight %.1f s"), *Why, *FinalShowGoLine, *Moves, FinalShowFightT), *FinalShowDone);
		UE_LOG(LogRDAurorim, Log, TEXT("RDSHOW moves: %s"), *Moves);
		UE_LOG(LogRDAurorim, Log, TEXT("RDSHOW done: %s (the fight %.1f s)"), *Why, FinalShowFightT);
	};
	auto Face = [&](const FVector& To)
	{
		const FVector D = (To - Her->GetActorLocation()).GetSafeNormal2D();
		if (D.IsNearlyZero()) return;
		Her->SetActorRotation(FRotator(0, D.Rotation().Yaw, 0));
		PC->SetControlRotation(FRotator(-12.f, D.Rotation().Yaw, 0));
	};
	switch (FinalShowPhase)
	{
	case 0:
	{
		// (the start set built and a moment given: her things are restored a few frames after her combat component is made)
		const ARDSection* S0 = GetSection(FIntPoint::ZeroValue);
		if (!S0 || S0->IsBuilding() || FinalShowT < 2.f) return;
		// the kit: every tier open (her growth), the best of everything she can use
		DebugOpenTiers(MaxTier, false);
		TArray<FString> Kit;
		FName Arm = NAME_None, Wpn = NAME_None, Shd = NAME_None, Heal = NAME_None; float Av = -1.f, Wv = -1.f, Sv = -1.f, Hv = -1.f;
		TMap<uint8, TPair<FName, float>> Rings;
		for (const FRDItemDef& It : Items)
		{
			// (the heroes are women: of two sets rated alike, the one made for a woman: Epic Plate (Female) over (Male))
			if (It.Kind == ERDItemKind::Armour && ArmourRefusal(It, It.Name.ToString()).IsEmpty()
				&& (It.DamageRating > Av || (It.DamageRating == Av && It.Name.ToString().Contains(TEXT("Female"))))) { Av = It.DamageRating; Arm = It.Name; }
			else if (It.Kind == ERDItemKind::Weapon) { for (const FRDWeaponFit& F : It.WeaponFits) if (F.Hero == CurrentHero && F.Weapon.Damage > Wv) { Wv = F.Weapon.Damage; Wpn = It.Name; } }
			else if (It.Kind == ERDItemKind::Shield && It.Amount > Sv) { Sv = It.Amount; Shd = It.Name; }
			else if (It.Kind == ERDItemKind::Healing && It.Amount > Hv) { Hv = It.Amount; Heal = It.Name; }
			else if (It.Kind == ERDItemKind::Ring) { TPair<FName, float>& B = Rings.FindOrAdd((uint8)It.RingKind, TPair<FName, float>(NAME_None, -1.f)); if (It.Amount > B.Value) B = TPair<FName, float>(It.Name, It.Amount); }
		}
		if (!Arm.IsNone()) { Pc->AddItem(Arm, 1); if (Pc->WearArmour(Arm)) Kit.Add(Arm.ToString()); }
		if (!Shd.IsNone()) { Pc->AddItem(Shd, 1); if (Pc->WearShield(Shd)) Kit.Add(Shd.ToString()); }
		for (const auto& Kv : Rings) if (!Kv.Value.Key.IsNone()) { Pc->AddItem(Kv.Value.Key, 1); if (Pc->WearRing(Kv.Value.Key)) Kit.Add(Kv.Value.Key.ToString()); }
		if (!Heal.IsNone()) { Pc->AddItem(Heal, 6); Kit.Add(FString::Printf(TEXT("6 %s"), *Heal.ToString())); }
		if (!Wpn.IsNone())
		{
			Pc->AddItem(Wpn, 1);
			const int32 Wi = Weapons.IndexOfByPredicate([Wpn](const FRDWeaponDef& W) { return W.Item == Wpn; });
			if (Wi >= 0)
			{
				Pc->SelectWeapon(Wi); Kit.Add(Wpn.ToString());
				// (the slash table's last slash on it)
				if (Slashes.Num() > 0)
				{
					const FName Sl = Slashes.Last().Name;
					Pc->AddItem(Sl, 1);
					if (Pc->ApplySlash(Sl, Wi)) Kit.Add(Sl.ToString());
				}
			}
		}
		Pc->SetHealth(Pc->GetMaxHealth());
		FinalShowKit = FString::Join(Kit, TEXT(", "));
		UE_LOG(LogRDAurorim, Log, TEXT("RDSHOW kit: %s; %.0f hit points"), *FinalShowKit, Pc->GetMaxHealth());
		// into a set of the last tier: held in the air over it while it is built (a set that far from her is dropped at once)
		FinalShowSet = FIntPoint(FMath::Max(MaxTier - 1, 1), 0);
		const float Span = SectionTiles * TileSize;
		Her->GetCharacterMovement()->SetMovementMode(MOVE_Flying);
		Her->SetActorLocation(FVector(FinalShowSet.X * Span, FinalShowSet.Y * Span, 400.f), false, nullptr, ETeleportType::TeleportPhysics);
		GenerateSectionNow(FinalShowSet);
		// (nobody comes at her before the recording begins)
		FinalShowAggro = AggroDistance; FinalShowLose = LoseDistance; AggroDistance = 0.f; LoseDistance = 1.f;
		FinalShowPhase = 1; FinalShowT = 0.f;
		return;
	}
	case 1:
	{
		ARDSection* S = GetSection(FinalShowSet);
		if (!S || S->IsBuilding()) { if (FinalShowT > 60.f) Done(TEXT("the set was not built")); return; }
		Her->GetCharacterMovement()->SetMovementMode(MOVE_Walking);
		const FVector C = S->GetRoomCenter(0);
		Her->SetActorLocation(C + FVector(0, 0, 120.f), false, nullptr, ETeleportType::TeleportPhysics);
		// (the set's own monsters gone and its rooms seen: him and his band only; then him, at once)
		DebugClearSection(FinalShowSet, 0, C);
		// (his room: the set's largest by its free floor (she is put in it a moment later; nobody fights before the go))
		{
			int32 BestN = -1; FinalShowRoom = -1;
			for (int32 Ri = 0; Ri < S->GetNumRooms(); ++Ri)
			{
				const int32 N = S->GetRoomFreeTiles(Ri).Num();
				if (N > BestN) { BestN = N; FinalShowRoom = Ri; }
			}
			UE_LOG(LogRDAurorim, Log, TEXT("RDSHOW his room: %d (%d free tiles)"), FinalShowRoom, BestN);
		}
		if (!PlaceFinalBoss()) { Done(TEXT("he could not be placed")); return; }
		FinalShowPhase = 2; FinalShowT = 0.f;
		return;
	}
	case 2:
	{
		// (her about 20 m from him in his room (his lance first, then his light as she closes, then his fists), on a tile with the
		// camera's room behind her (a bed behind her filled the first shot), facing him)
		ARDMonster* Boss = GetFinalBoss();
		const FEncounter* E = Encounters.FindByPredicate([](const FEncounter& X) { return X.bFinal; });
		ARDSection* S = E ? GetSection(E->Section) : nullptr;
		if (!Boss || !S || FinalShowT < 1.f) { if (FinalShowT > 10.f) Done(TEXT("no boss")); return; }
		const FVector B = Boss->GetActorLocation();
		FCollisionQueryParams Q(SCENE_QUERY_STAT(RDShowCam), false, Her); Q.AddIgnoredActor(Boss);
		FCollisionObjectQueryParams O; O.AddObjectTypesToQuery(ECC_WorldStatic); O.AddObjectTypesToQuery(ECC_WorldDynamic);
		FVector Best = FVector::ZeroVector; float BestScore = -MAX_flt;
		for (const FVector& T : S->GetRoomFreeTiles(E->Room))
		{
			const float D = FVector::Dist2D(T, B);
			float Score = -FMath::Abs(D - 2000.f);
			const FVector Back = (T - B).GetSafeNormal2D();
			if (GetWorld()->LineTraceTestByObjectType(T + FVector(0, 0, 180.f), T + Back * 400.f + FVector(0, 0, 230.f), O, Q)) Score -= 5000.f;      // (the camera's room)
			if (GetWorld()->LineTraceTestByObjectType(T + FVector(0, 0, 150.f), B + FVector(0, 0, 150.f), O, Q)) Score -= 3000.f;                    // (him in sight)
			if (Score > BestScore) { BestScore = Score; Best = T; }
		}
		if (!Best.IsZero()) Her->SetActorLocation(Best + FVector(0, 0, 120.f), false, nullptr, ETeleportType::TeleportPhysics);
		Face(B);
		// (him and his band kept in his room until the go: the recorder's wait (three Game Bar presses, 40 s) let them wander off
		// down the hallways, and autoplay hunted them one by one for three minutes)
		for (const TWeakObjectPtr<ARDMonster>& M : E->Live) if (M.IsValid()) M->HomeRoom = E->Room;
		Pc->SetHealth(Pc->GetMaxHealth());
		FinalShowPhase = 3; FinalShowT = 0.f;
		// (ready: the recorder may begin, then writes the go file)
		if (!FinalShowReady.IsEmpty()) FFileHelper::SaveStringToFile(TEXT("ready"), *FinalShowReady);
		UE_LOG(LogRDAurorim, Log, TEXT("RDSHOW she stands %.0f m from him"), FVector::Dist2D(Her->GetActorLocation(), B) / 100.f);
		return;
	}
	case 3:
	{
		// (waiting for the recording to begin: the go file, four times a second; facing him)
		if (ARDMonster* Boss = GetFinalBoss()) Face(Boss->GetActorLocation());
		if (!FinalShowGo.IsEmpty())
		{
			FinalShowCheck += Dt;
			if (FinalShowCheck < 0.25f) return;
			FinalShowCheck = 0.f;
			if (!FPaths::FileExists(FinalShowGo)) return;
		}
		// (he and his band come at her from the start: she stands farther from him than the castle's noticing distance (in a
		// rehearsal he stood 32 s while his band fought her); the castle's own back at the end)
		AggroDistance = FMath::Max(FinalShowAggro, 2600.f); LoseDistance = FMath::Max(FinalShowLose, 4000.f);
		StartAutoplay(900.f, false);
		bAutoplayIgnorePlayer = true;          // (no key takes over: Game Bar's hotkey reaches the game)
		// (him and his band only: the first recording's autoplay hunted another set's monsters for 80 s before it reached him)
		AutoplayOnly.Reset();
		if (const FEncounter* E = Encounters.FindByPredicate([](const FEncounter& X) { return X.bFinal; }))
		{
			float Far = 0.f; int32 Out = 0;
			ARDSection* Es = GetSection(E->Section);
			for (const TWeakObjectPtr<ARDMonster>& M : E->Live)
				if (M.IsValid())
				{
					M->HomeRoom = -1; if (!M->IsDead()) AutoplayOnly.Add(M);
					Far = FMath::Max(Far, FVector::Dist2D(M->GetActorLocation(), Her->GetActorLocation()));
					if (Es && Es->RoomAt(M->GetActorLocation()) != E->Room) ++Out;
				}
			const ARDMonster* Bo = GetFinalBoss();
			FinalShowGoLine = FString::Printf(TEXT("at the go: him %.0f m from her, the farthest of them %.0f m, %d of %d out of his room, her in it: %s; %s"),
				Bo ? FVector::Dist2D(Bo->GetActorLocation(), Her->GetActorLocation()) / 100.f : -1.f, Far / 100.f, Out, E->Live.Num(),
				Es && Es->RoomAt(Her->GetActorLocation()) == E->Room ? TEXT("yes") : TEXT("no"), *FinalShowKit);
		}
		UE_LOG(LogRDAurorim, Log, TEXT("RDSHOW autoplay fights only his %d"), AutoplayOnly.Num());
		FinalShowPhase = 4; FinalShowT = 0.f; FinalShowFightT = 0.f;
		FinalShowFirstHitT = FinalShowBandDoneT = -1.f; FinalShowBandAtHit = -1; FinalShowMinHp = Pc->GetHealth();
		FinalShowHoldS = FinalShowBossCircleS = 0.f; FinalShowBossMaxHp = GetFinalBoss() ? GetFinalBoss()->GetMaxHealth() : 0.f;
		SkyBeamStats.Reset();
		UE_LOG(LogRDAurorim, Log, TEXT("RDSHOW go: the fight (his %.0f hit points, his band %d near him)"), FinalShowBossMaxHp, FinalBandNear);
		return;
	}
	case 4:
		FinalShowFightT += Dt;
		FinalShowMinHp = FMath::Min(FinalShowMinHp, Pc->GetHealth());
		// (the fight's order: her first blow on him and his band then, the band's last death; his moves)
		if (const FEncounter* E = Encounters.FindByPredicate([](const FEncounter& X) { return X.bFinal; }))
		{
			int32 Band = 0;
			for (int32 I = 1; I < E->Live.Num(); ++I) if (const ARDMonster* M = E->Live[I].Get(); M && !M->IsDead()) ++Band;
			if (Band == 0 && FinalShowBandDoneT < 0.f) FinalShowBandDoneT = FinalShowFightT;
			if (const ARDMonster* Bo = E->Live.Num() > 0 ? E->Live[0].Get() : nullptr)
			{
				if (FinalShowFirstHitT < 0.f && Bo->GetHealth() < Bo->GetMaxHealth() - 0.5f)
				{
					FinalShowFirstHitT = FinalShowFightT; FinalShowBandAtHit = Band;
					UE_LOG(LogRDAurorim, Log, TEXT("RDSHOW her first blow on him at %.1f s, %d of his band alive"), FinalShowFightT, Band);
				}
				FinalShowHoldS = Bo->HoldSeconds; FinalShowBossCircleS = Bo->CircleSeconds;
			}
		}
		if (Pc->IsDead()) { FinalShowPhase = 5; FinalShowT = 0.f; FinalShowResult = TEXT("she fell"); return; }
		// (the combat goes on after his death while any of his band is after her: over once none has been for 3 s, or 40 s after
		// him at most (a rehearsal's autoplay went looting chests for a minute and a half with idle monsters left about the set))
		if (bFinalBossSlain)
		{
			if (FinalShowResult.IsEmpty()) { FinalShowResult = TEXT("he is slain"); FinalShowT = 0.f; FinalShowCheck = 0.f; }
			bool bFight = false;
			for (const ARDMonster* M : GetMonsters())
				if (M && !M->IsDead() && !M->IsAlly() && M->IsAggro() && FVector::Dist2D(M->GetActorLocation(), Her->GetActorLocation()) < 2500.f) { bFight = true; break; }
			FinalShowCheck = bFight ? 0.f : FinalShowCheck + Dt;
			if (FinalShowCheck < 3.f && FinalShowT < 40.f) return;
			const FEncounter* E = Encounters.FindByPredicate([](const FEncounter& X) { return X.bFinal; });
			int32 Band = 0;
			if (E) for (int32 I = 1; I < E->Live.Num(); ++I) if (const ARDMonster* M = E->Live[I].Get(); M && !M->IsDead()) ++Band;
			FinalShowPhase = 5; FinalShowT = 0.f; FinalShowResult = Band > 0 ? FString::Printf(TEXT("he is slain (%d of his band left, none after her)"), Band) : FString(TEXT("he is slain, and his band"));
			StopAutoplay(TEXT("the fight is over"));
			return;
		}
		if (FinalShowFightT > 900.f) Done(TEXT("the fight went on 15 minutes"));
		return;
	case 5:
		// (his loot, the notice, the door's grating going down: then the end)
		// (she turns to the door, its grating down and its light up)
		if (FinalShowResult.StartsWith(TEXT("he is slain")) && FinalShowT < 0.5f && FinalDoor) Face(FinalDoor->GetActorLocation());
		if (FinalShowT > 7.f) Done(FinalShowResult);
		return;
	default:
		return;
	}
}
