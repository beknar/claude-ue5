// Brokenspire (docs/brokenspire.txt): the town in play and the castle's side of it.
//   - the town: its people (ARDTownsfolk at the plan's posts), the Mistward Hall's guards (tier 1, kept to their room), the
//     Mistgate (walked into, it opens Mistward Castle), the services (the trader buys and sells, the healer heals, the smith
//     mends and has his anvil, the temple blesses, the storehouse keeps her things, the circle knows the circles found, the
//     board posts bounties), talk and quests (the elder, the scholar, the guard captain), the gate barred
//   - both: gold (kills, containers), her things and the purse between the levels (URDGameInstance), the quests' counters
//   - the castle: the way back to the town (an arch in its great hall, the Escape menu's line)
#include "RD/RDDungeonGenerator.h"
#include "RD/RDSection.h"
#include "RD/RDCombat.h"
#include "RD/RDMonster.h"
#include "RD/RDTown.h"
#include "RD/RDGameInstance.h"
#include "RD/RDMistward.h"
#include "Components/CapsuleComponent.h"
#include "Components/SkeletalMeshComponent.h"
#include "Components/PointLightComponent.h"
#include "NiagaraComponent.h"
#include "Animation/AnimSequenceBase.h"
#include "GameFramework/Character.h"
#include "GameFramework/CharacterMovementComponent.h"
#include "GameFramework/GameModeBase.h"
#include "GameFramework/PlayerController.h"
#include "Kismet/GameplayStatics.h"
#include "Engine/World.h"
#include "InputCoreTypes.h"
#include "Misc/CommandLine.h"
#include "Misc/Parse.h"
#include "Misc/Paths.h"

DEFINE_LOG_CATEGORY_STATIC(LogRDTownGame, Log, All);

static FString RDTRoleName(ERDTownRole R)
{
	const UEnum* E = StaticEnum<ERDTownRole>();
	return E ? E->GetNameStringByValue((int64)R) : FString();
}

static const FIntPoint RDTGDir4[4] = { FIntPoint(-1, 0), FIntPoint(1, 0), FIntPoint(0, -1), FIntPoint(0, 1) };

// ================================================================================================ the townsfolk
ARDTownsfolk::ARDTownsfolk()
{
	PrimaryActorTick.bCanEverTick = true;
	Capsule = CreateDefaultSubobject<UCapsuleComponent>(TEXT("Capsule"));
	Capsule->InitCapsuleSize(34.f, 90.f);
	Capsule->SetCollisionProfileName(TEXT("BlockAllDynamic"));
	Capsule->SetCanEverAffectNavigation(false);
	RootComponent = Capsule;
	Body = CreateDefaultSubobject<USkeletalMeshComponent>(TEXT("Body"));
	Body->SetupAttachment(Capsule);
	Body->SetCollisionEnabled(ECollisionEnabled::NoCollision);
	Body->SetAnimationMode(EAnimationMode::AnimationSingleNode);
	// (a hundred of them in the town: only the ones on the screen are posed)
	Body->VisibilityBasedAnimTickOption = EVisibilityBasedAnimTickOption::OnlyTickPoseWhenRendered;
	Body->bEnableUpdateRateOptimizations = true;
}

void ARDTownsfolk::Init(ARDDungeonGenerator* InGenerator, ARDSection* InSection, int32 InDef, const FVector& InPost, float InYaw, float InWander, uint32 InSeed)
{
	Gen = InGenerator; Section = InSection; Def = InDef; Post = InPost; Wander = InWander; HomeYaw = InYaw;
	R.Initialize((int32)InSeed);
	if (!Gen || !Gen->Townsfolk.IsValidIndex(Def)) return;
	const FRDTownsfolkDef& D = Gen->Townsfolk[Def];
	TownRole = D.Role; Title = D.Title; Calling = D.Calling;
	// (a small town of the wilderness: its own people, its name in their titles)
	if (!Gen->bTownHome) { Title.ReplaceInline(TEXT("Brokenspire"), *Gen->TownName); Calling.ReplaceInline(TEXT("Brokenspire"), *Gen->TownName); }
	Body->SetSkeletalMeshAsset(D.Mesh);
	Body->SetRelativeLocationAndRotation(FVector(0, 0, -HalfHeight + D.MeshZ), FRotator(0, D.MeshYaw, 0));
	Body->SetRelativeScale3D(FVector(D.Scale));
	for (USkeletalMesh* P : D.Parts)
	{
		if (!P) continue;
		USkeletalMeshComponent* C = NewObject<USkeletalMeshComponent>(this);
		C->SetSkeletalMeshAsset(P);
		C->SetupAttachment(Body);
		C->SetCollisionEnabled(ECollisionEnabled::NoCollision);
		C->RegisterComponent();
		C->SetLeaderPoseComponent(Body);
	}
	IdleAnim = D.Idle; WalkAnim = D.Walk;
	// (the walk clip's ground speed at this body's size: a child at 0.8 strides 0.8 as far. The clip plays at least 0.8 of its
	// speed and the body moves exactly as far as its feet do: at the role's 120 cm/s every walker's clip ran at half speed
	// (0.51) and its feet slid, and the children's legs looked still (the user's of 2026-11-02))
	ClipSpeed = FMath::Max(D.WalkClipSpeed, 10.f) * FMath::Max(D.Scale, 0.3f);
	Speed = FMath::Clamp(D.WalkSpeed, ClipSpeed * 0.8f, ClipSpeed * 1.2f);
	bWalkClip = true; SetClip(false);
	Body->SetPosition(R.FRandRange(0.f, 2.f));
	NextTrip = R.FRandRange(2.f, 9.f);
}

void ARDTownsfolk::SetClip(bool bWalk)
{
	bWalkClip = bWalk;
	// (on the way to serve a table it carries its tray: the carry walk and stand, when its body has them)
	const bool bCarry = (Act == 1 || Act == 2) && WorkKind() == TEXT("CarryIdle");
	UAnimationAsset* Carry = bCarry ? WorkClip(bWalk ? TEXT("CarryWalk") : TEXT("CarryIdle")) : nullptr;
	UAnimationAsset* A = Carry ? Carry : bWalk && WalkAnim ? WalkAnim.Get() : IdleAnim.Get();
	PlayAnim(A, bWalk && WalkAnim ? Speed / ClipSpeed : 1.f);
}

void ARDTownsfolk::PlayAnim(UAnimationAsset* A, float Rate)
{
	if (!A) return;
	if (A == CurAnim && FMath::IsNearlyEqual(Rate, CurRate, 0.01f)) return;
	CurAnim = A; CurRate = Rate;
	Body->PlayAnimation(A, true);
	Body->SetPlayRate(Rate);
}

void ARDTownsfolk::FaceToward(const FVector& P, float Seconds)
{
	FaceAt = P; FaceUntil = GetWorld()->GetTimeSeconds() + Seconds;
	Path.Reset(); SetClip(false);
}

void ARDDungeonGenerator::TownLinePool(int32 InDef, ERDTownRole InRole, TArray<FString>& Out) const
{
	// (its def's own lines, then its role's for the town she is in: that town's, and the shared ones unless that town's are
	// its alone (Heaven's modern people))
	Out.Reset();
	if (Townsfolk.IsValidIndex(InDef)) Out.Append(Townsfolk[InDef].Lines);
	const FString Here = bTownHome ? FString(TEXT("Brokenspire")) : TownName;
	const FName Rn(*RDTRoleName(InRole));
	const bool bOnlyHere = RoleLines.ContainsByPredicate([&](const FRDRoleLines& L) { return L.Role == Rn && L.Town == Here && L.bOnly; });
	for (const FRDRoleLines& L : RoleLines)
	{
		if (L.Role != Rn) continue;
		if (L.Town.IsEmpty() ? bOnlyHere : L.Town != Here) continue;
		if (!L.ExceptTown.IsEmpty())
		{
			TArray<FString> Ex; L.ExceptTown.ParseIntoArray(Ex, TEXT(","));
			if (Ex.Contains(Here)) continue;
		}
		for (const FString& Ln : L.Lines) Out.AddUnique(Ln);
	}
}

void ARDTownsfolk::MakeLinePool()
{
	bPoolMade = true; LinePool.Reset(); LineBag.Reset(); LinesSaid = 0; LastSaid = -1; PoolOwn = OwnLines;
	if (OwnLines.Num() > 0) LinePool = OwnLines;
	else if (Gen && Gen->Townsfolk.IsValidIndex(Def)) Gen->TownLinePool(Def, TownRole, LinePool);
}

int32 ARDTownsfolk::GetLinePoolSize()
{
	if (!bPoolMade) MakeLinePool();
	return LinePool.Num();
}

FString ARDTownsfolk::GetRoleName() const { return RDTRoleName(TownRole); }

FString ARDTownsfolk::NextLine()
{
	if (!Gen || !Gen->Townsfolk.IsValidIndex(Def)) return FString();
	// (the list of 2026-11-10: its def's lines and its role's for the town (at least 30 a job), drawn from a shuffled bag: no line
	// again until all have been said; the first time its def's first, its greeting)
	if (!bPoolMade || OwnLines != PoolOwn) MakeLinePool();
	if (LinePool.Num() == 0) return FString();
	if (LinesSaid == 0) { ++LinesSaid; LastSaid = 0; return LinePool[0]; }
	if (LineBag.Num() == 0)
	{
		// (the first bag leaves out the greeting just said)
		for (int32 I = LinesSaid == 1 && LinePool.Num() > 1 ? 1 : 0; I < LinePool.Num(); ++I) LineBag.Add(I);
		for (int32 I = LineBag.Num() - 1; I > 0; --I) LineBag.Swap(I, R.RandRange(0, I));
		// (the next drawn is the bag's last: never the line just said (PR #41's review: a repeat at every bag's edge))
		if (LineBag.Num() > 1 && LineBag.Last() == LastSaid) LineBag.Swap(0, LineBag.Num() - 1);
	}
	++LinesSaid;
	LastSaid = LineBag.Pop();
	return LinePool[LastSaid];
}

void ARDTownsfolk::Tick(float Dt)
{
	Super::Tick(Dt);
	const float Now = GetWorld()->GetTimeSeconds();
	// (the list of 2026-11-04: on the open ground's rise and fall, at its own height over it)
	if (Section && Section->TownLiftW.Num() > 0 && !bInBed)          // (in bed it lies on the bed's top)
	{
		const FVector P = GetActorLocation();
		const float Lz = Section->TownLiftAt(FVector2D(P));
		// (spawned on the flat floor's height, the lift not in it: the PR review's find, taken off it a townsperson posted on a
		// rise walked sunk by it everywhere, one in a hollow floating)
		if (FloorZ0 < -1e8f) FloorZ0 = P.Z;
		if (FMath::Abs(P.Z - (FloorZ0 + Lz)) > 0.5f) SetActorLocation(FVector(P.X, P.Y, FloorZ0 + Lz));
	}
	// (the list of 2026-11-11: a guard fights a monster that has come into its town (RDList11.cpp))
	if (TickGuardFight(Dt, Now)) return;
	const FVector L = GetActorLocation();
	auto Turn = [&](const FVector& Dir, float Rate)
	{
		if (Dir.IsNearlyZero(1.f)) return;
		SetActorRotation(FRotator(0.f, FMath::RInterpConstantTo(GetActorRotation(), Dir.Rotation(), Dt, Rate).Yaw, 0.f));
	};
	// (she spoke to it: it turns to her and stands; at work it keeps at it where it is (a seated customer turned away from the
	// table))
	if (Now < FaceUntil)
	{
		// (woken to serve (a keeper, a quest's giver, PR #41's review): up out of bed to face her, back in it once she has gone)
		if (bInBed) { bInBed = false; SetActorLocationAndRotation(PreBed, FRotator(0.f, HomeYaw, 0.f)); }
		if (Act != 3) { Turn(FaceAt - GetActorLocation(), 240.f); SetClip(false); }
		return;
	}
	// (the list of 2026-11-10's sixth phase: a traveller on the wilds' roads: RDWild10.cpp)
	if (bRoadWalker) { TickRoad(Dt); return; }
	// (its day: home at evening, asleep at night; asleep, it stands where it is, or keeps its seat)
	TickDay(Now);
	// (the list of 2026-11-10: asleep, in its bed, lying, on its Sleep clip; awake, out of it where it stood before)
	if (bInBed && !bSleeping)
	{
		bInBed = false; SetActorLocationAndRotation(PreBed, FRotator(0.f, HomeYaw, 0.f)); SetClip(false);
		return;          // (PR #41's review: the rest of the tick read where it lay)
	}
	if (bSleeping && Path.Num() == 0)
	{
		if (bHasBed)
		{
			// (a keeper still at its work when it falls asleep (the innkeeper at the bar) leaves it for its bed: asleep at work it was
			// counted asleep and stood there)
			if (Act != 0) EndWork();
			if (!bInBed)
			{
				PreBed = GetActorLocation(); bInBed = true;
				SetActorLocationAndRotation(BedAt + FVector(0.f, 0.f, 92.f), FRotator(0.f, BedYaw, 0.f));
				UAnimationAsset* Sl = WorkClip(TEXT("Sleep"));
				if (Sl) PlayAnim(Sl, 1.f); else SetClip(false);
			}
			return;
		}
		if (Act != 3) SetClip(false);
		return;
	}
	// (the last steps onto its place of work, straight, through the fence's gap or between the stools)
	if (Act == 2)
	{
		FVector D = GlideTo - L; D.Z = 0.f;
		if (D.Size() < 6.f) { BeginWork(Now); return; }
		SetActorLocation(L + D.GetSafeNormal() * FMath::Min(Speed * 0.8f * Dt, D.Size()), false);
		Turn(D, 360.f);
		SetClip(true);
		return;
	}
	if (Path.Num() > 0)
	{
		FVector D = Path[0] - L; D.Z = 0.f;
		if (D.Size() < 40.f)
		{
			Path.RemoveAt(0);
			if (Path.Num() == 0)
			{
				if (Act == 1) { Act = 2; return; }
				SetClip(false); NextTrip = Now + R.FRandRange(4.f, 14.f);
			}
			return;
		}
		// (a closed door on the way: it opens it, as a monster does, and it closes again behind)
		if (Section)
		{
			// (a boarded door never opens: the walk is given up, or it waited there for good (the PR review's find))
			const int32 Door = Section->OpenDoorAhead(L, D, 160.f, true);
			if (Door == 1) { Path.Reset(); SetClip(false); NextTrip = Now + R.FRandRange(1.f, 3.f); if (Act == 1) { EndWork(); NextTrip = Now + 2.f; } return; }
			if (Door == 0) { SetClip(false); return; }
		}
		const FVector Step = D.GetSafeNormal() * FMath::Min(Speed * Dt, D.Size());
		FHitResult Hit;
		SetActorLocation(L + Step, true, &Hit);
		if (Hit.bBlockingHit)
		{
			Path.Reset(); SetClip(false); NextTrip = Now + R.FRandRange(1.f, 3.f);
			// (going to work: near it, the rest straight; else tried again, given up after three)
			if (Act == 1)
			{
				if (FVector::Dist2D(L, GlideTo) < 320.f) Act = 2;
				else if (++GoFails >= 3) { EndWork(); NextTrip = Now + 2.f; }
			}
			return;
		}
		Turn(D, 300.f);
		SetClip(true);
		return;
	}
	if (TickWork(Now, Dt)) return;
	// standing: back to its own way of facing; now and then a walk within its round (not while it is home for the evening)
	if (bWentHome) return;
	if (Wander <= 0.f || !Section)
	{
		if (FVector::Dist2D(L, Post) < 60.f) Turn(FRotator(0, HomeYaw, 0).Vector(), 90.f);
		// (a farmstead's family: back at its work once she has gone)
		if (!StandWork.IsNone())
		{
			if (UAnimationAsset* Wc = WorkClip(StandWork)) PlayAnim(Wc, 1.f);
			if (!PropComp && !StandProp.IsNone()) SetProp(StandProp);
		}
		return;
	}
	if (Now < NextTrip) return;
	NextTrip = Now + R.FRandRange(5.f, 12.f);
	// (a few tries: a point of its round can be beyond the wall or in a house; the militia's lane runs along the wall)
	TArray<FVector> P;
	for (int32 Try = 0; Try < 6 && P.Num() < 2; ++Try)
	{
		const FVector To = Post + FRotator(0, R.FRandRange(0.f, 360.f), 0).RotateVector(FVector(R.FRandRange(Wander * 0.25f, Wander), 0, 0));
		P = Section->FindPathWorld(L, To);
		if (P.Num() > 150) P.Reset();
	}
	if (P.Num() < 2)
	{
		// (three trips with no way found: it stands where nothing leads; back to the nearest tile something does)
		if (++NoPathTrips >= 3 && Section) { NoPathTrips = 0; const FIntPoint T = Section->WorldToLocal(L); for (int32 Rr = 1; Rr <= 6; ++Rr) { bool bDone = false; for (int32 Dx = -Rr; Dx <= Rr && !bDone; ++Dx) for (int32 Dy = -Rr; Dy <= Rr && !bDone; ++Dy) { const FIntPoint Q = T + FIntPoint(Dx, Dy); if (Section->IsWalkable(Q) && Section->RoomAtLocal(Q) == Section->RoomAtLocal(T)) { const FVector W = Section->LocalToWorld(Q); SetActorLocation(FVector(W.X, W.Y, L.Z)); Post = GetActorLocation(); bDone = true; } } if (bDone) break; } }
		NextTrip = Now + R.FRandRange(2.f, 4.f);
		return;
	}
	NoPathTrips = 0;
	P.RemoveAt(0);
	for (FVector& Q : P) Q.Z = L.Z;
	Path = P; ++Walks;
}

bool ARDTownsfolk::TickDay(float Now)
{
	bSleeping = false;
	if (!Gen || !Gen->bDayNight || HomeBld < 0 || !Section) return false;
	const float H = Gen->GetTownHour();
	const bool bNight = H >= 22.f || H < 6.f;
	// (in bed: where it lay down from (its way to its post in the morning starts there, on the floor))
	const FVector L = bInBed ? PreBed : GetActorLocation();
	if (bResident_)
	{
		// (a resident: home from 19 o'clock to half past six; the way there or back once, when its hour turns)
		const bool bWant = H >= 19.f || H < 6.5f;
		if (bWant != bWentHome)
		{
			// (its work left for the evening, taken up again in the morning)
			if (Act != 0) EndWork();
			bWentHome = bWant; HomeFails = 0; HomeRetryAt = Now + 3.f;
			TArray<FVector> P = Section->FindPathWorld(L, bWant ? HomeIn : Post);
			if (P.Num() >= 2) { P.RemoveAt(0); for (FVector& Q : P) Q.Z = L.Z; Path = P; ++Walks; }
			else if (bWant) SetActorLocation(FVector(HomeIn.X, HomeIn.Y, L.Z));       // (no way found: it is home all the same)
			NextTrip = Now + R.FRandRange(5.f, 12.f);
		}
		// (the list of 2026-11-10: stopped on the way home (two of a household at one door, a door): tried again, then put inside;
		// once a walk ended it was never made again, and half the town stood in the streets all night)
		if (bWant && Path.Num() == 0 && Act == 0 && !bInBed && Now >= HomeRetryAt && (HomeRetryAt = Now + 3.f, Section->TownBuildingAt(L) != HomeBld))
		{
			TArray<FVector> P = ++HomeFails <= 3 ? Section->FindPathWorld(L, HomeIn) : TArray<FVector>();
			if (P.Num() >= 2) { P.RemoveAt(0); for (FVector& Q : P) Q.Z = L.Z; Path = P; ++Walks; }
			else { SetActorLocation(FVector(HomeIn.X, HomeIn.Y, L.Z)); HomeFails = 0; }
		}
		bSleeping = bNight && bWentHome && Path.Num() == 0 && Section->TownBuildingAt(L) == HomeBld;
		return Path.Num() > 0;
	}
	// (a keeper, a soldier, the innkeeper: asleep at night where they work)
	bSleeping = bNight && Section->TownBuildingAt(L) == HomeBld;
	return false;
}

// ================================================================================================ her combat component
bool URDCombatComponent::IsAfflicted() const
{
	const UWorld* W = GetWorld();
	const float Now = W ? W->GetTimeSeconds() : 0.f;
	return (PoisonDps > 0.f && Now < PoisonUntil) || (WeakShare > 0.f && Now < WeakUntil) || (SlowMeShare > 0.f && Now < SlowMeUntil);
}

float URDCombatComponent::GetBlessLeft() const
{
	const UWorld* W = GetWorld();
	return W ? FMath::Max(0.f, BlessUntil - W->GetTimeSeconds()) : 0.f;
}

bool URDCombatComponent::RemoveFoundWeapon(int32 Index, float& WearLeft)
{
	if (!Generator || !Generator->Weapons.IsValidIndex(Index) || Generator->Weapons[Index].Item.IsNone() || Generator->Weapons[Index].bScroll) return false;
	SyncWear();
	WearLeft = Wear.IsValidIndex(Index) ? Wear[Index] : -1.f;
	const FRDWeaponDef W = Generator->Weapons[Index];
	if (AttackTime >= 0.f && AttackIndex == Index) EndAttack();
	const bool bDrawn = Index == WeaponIndex;
	if (!W.Slash.IsNone()) AddItem(W.Slash, 1);
	DropWeaponAt(Index);
	if (bDrawn)
	{
		WeaponIndex = -1;
		for (int32 I = 0; I < Generator->Weapons.Num(); ++I) if (!Generator->Weapons[I].bAlongside && !Generator->Weapons[I].bScroll) { SelectWeapon(I); break; }
	}
	InventoryCursor = FMath::Clamp(InventoryCursor, 0, FMath::Max(0, GetInventoryLines().Num() - 1));
	return true;
}

// ================================================================================================ gold and prices
int32 ARDDungeonGenerator::GetGold() const
{
	const URDGameInstance* GI = URDGameInstance::Of(this);
	return GI ? GI->Gold : 0;
}

void ARDDungeonGenerator::AddGold(int32 Amount, const FString& Why)
{
	URDGameInstance* GI = URDGameInstance::Of(this);
	if (!GI || Amount == 0) return;
	GI->Gold = FMath::Max(0, GI->Gold + Amount);
	if (Amount > 0) { GI->Count(TEXT("gold"), Amount); if (PlayerCombat) PlayerCombat->ShowMessage(Why.IsEmpty() ? FString::Printf(TEXT("+%d gold"), Amount) : FString::Printf(TEXT("+%d gold  (%s)"), Amount, *Why)); }
	UE_LOG(LogRDTownGame, Log, TEXT("RDGOLD %+d (%s): %d"), Amount, *Why, GI->Gold);
}

int32 ARDDungeonGenerator::GetGameTier() const
{
	// (the rebalance to tier 25: the game's tier, the deepest opened in any dungeon of the chain in the game's tiers (Vel
	// Morrath's first is 6); until then 1-5 by the dungeons' own tiers)
	return FMath::Clamp(GameGlobalTier(), 1, GameTierMax);
}

static float RDTierPrice(int32 Tier);
int32 ARDDungeonGenerator::HorsePriceNow() const { return FMath::RoundToInt(HorseDef.Price * RDTierPrice(GetGameTier())); }

static float RDTierPrice(int32 Tier)
{
	// (1 to 8 over the first five tiers as before; past them about 17 % a tier: 185 at tier 25, 405 at tier 30)
	static const float K[5] = { 1.f, 2.f, 3.5f, 5.5f, 8.f };
	return Tier <= 5 ? K[FMath::Clamp(Tier, 1, 5) - 1] : 8.f * FMath::Pow(1.17f, (float)(FMath::Min(Tier, ARDDungeonGenerator::GameTierMax) - 5));
}

// (what a kill or a container pays by the game's tier: x the tier over the first five as before, then growing as the prices do
// (PR #34's review: gold by the level's own 1-5 against prices to 185 left the town's services out of reach past the castle))
static float RDTierGold(int32 Tier) { return Tier <= 5 ? (float)FMath::Max(Tier, 1) : 5.f * RDTierPrice(Tier) / 8.f; }

// (the list of 2026-11-10's seventh phase: the things used up (potions, food, scrolls, repair items, torches) are priced past tier 5
// by the gold a kill pays, so one costs as many kills at every tier as at tier 5. 910 lays the potions, food and scrolls again in
// every band of five tiers under one name, and a potion heals a share of her hit points at any tier: priced by its own tier alone,
// a healing potion cost 12 gold at tier 25, where a kill pays 116 times tier 1's. A step to its copy's tier (PR #44's review) made
// a stronger potion cheaper than a weaker one between tiers 6 and 9 and paid 28 % to buy one and sell it once the next tier
// opened; growing with the game's tier, the store's sell share (0.35) keeps that from paying)
static bool RDUsedUp(ERDItemKind K)
{
	return K == ERDItemKind::Healing || K == ERDItemKind::Mana || K == ERDItemKind::Speed || K == ERDItemKind::Food || K == ERDItemKind::Scroll
		|| K == ERDItemKind::Repair || K == ERDItemKind::Torch;
}
static float RDUsedUpScale(int32 Gt) { return Gt <= 5 ? 1.f : RDTierGold(Gt) / RDTierGold(5); }

// (an item's lowest tier, and its highest at or under the game's: the copy of it the game has reached)
static int32 RDLowTier(const FRDItemDef& It) { int32 T = 99; for (const int32 X : It.Tiers) T = FMath::Min(T, X); return It.Tiers.Num() ? T : 1; }
static int32 RDReachedTier(const FRDItemDef& It, int32 Gt)
{
	int32 T = 0; for (const int32 X : It.Tiers) if (X <= Gt) T = FMath::Max(T, X);
	return It.Tiers.Num() == 0 ? 1 : T;
}

int32 ARDDungeonGenerator::PriceOf(FName Item) const
{
	const int32 Ix = FindItem(Item);
	if (Ix < 0) return 0;
	const FRDItemDef& It = Items[Ix];
	const int32 T = RDLowTier(It);
	float Base = 10.f;
	switch (It.Kind)
	{
	case ERDItemKind::Healing: case ERDItemKind::Mana: Base = 8.f + It.Amount * 40.f; break;
	case ERDItemKind::Speed: Base = 12.f; break;
	case ERDItemKind::Food: Base = 4.f; break;
	case ERDItemKind::Armour: Base = 60.f; break;
	case ERDItemKind::Weapon: Base = 40.f; break;
	case ERDItemKind::Component: Base = 3.f; break;
	case ERDItemKind::Repair: Base = 16.f; break;
	case ERDItemKind::Ring: Base = 80.f; break;
	case ERDItemKind::Tome: Base = 120.f; break;
	case ERDItemKind::Shield: Base = 40.f; break;
	case ERDItemKind::Torch: Base = 6.f; break;
	case ERDItemKind::Slash: Base = 100.f; break;
	case ERDItemKind::Scroll: Base = 25.f; break;
	default: return 0;                   // (teleport rings, keys: not for sale)
	}
	return FMath::Max(1, FMath::RoundToInt(Base * RDTierPrice(T) * (RDUsedUp(It.Kind) ? RDUsedUpScale(GetGameTier()) : 1.f)));
}

TArray<FName> ARDDungeonGenerator::TownStock() const
{
	// (potions of every kind, food, repair items and the scrolls a hero of hers reads, of the tiers she has opened)
	TArray<FName> Out;
	const int32 T = GetGameTier();
	const FRDHeroDef* H = FindHero(CurrentHero);
	for (const FRDItemDef& It : Items)
	{
		if (RDLowTier(It) > T) continue;
		const bool bScroll = It.Kind == ERDItemKind::Scroll;
		// (a scroll of the last two tiers the game has reached: by its copy's tier (910's), else none past tier 6)
		const int32 Ti = RDReachedTier(It, T);
		if (bScroll && !(H && H->ScrollTypes.Num() > 0)) continue;
		if (It.Kind == ERDItemKind::Healing || It.Kind == ERDItemKind::Mana || It.Kind == ERDItemKind::Speed || It.Kind == ERDItemKind::Food || It.Kind == ERDItemKind::Repair
			|| (bScroll && Ti >= T - 1) || It.Kind == ERDItemKind::Torch)
			Out.Add(It.Name);
	}
	return Out;
}

// ================================================================================================ her things between the levels
void ARDDungeonGenerator::SaveCarry()
{
	URDGameInstance* GI = URDGameInstance::Of(this);
	if (!GI || !PlayerCombat) return;
	FRDCarry C; C.bValid = true; C.Hero = CurrentHero;
	PlayerCombat->GatherDroppable(C.Things, C.Wear);
	C.WornArmour = PlayerCombat->GetWornArmour();
	C.WornShield = PlayerCombat->GetWornShield();
	for (int32 K = 0; K < 8; ++K) { const FName Rg = PlayerCombat->GetWornRing((ERDRingKind)K); if (!Rg.IsNone()) C.WornRings.Add(Rg); }
	if (const FRDHeroDef* H = FindHero(CurrentHero))
	{
		TArray<FRDWeaponDef> Base; StartWeaponsOf(*H, Base);
		for (const FRDWeaponDef& W : Weapons)
			if (W.SpellIndex >= 0 && W.Item.IsNone() && !W.bScroll && !Base.ContainsByPredicate([&](const FRDWeaponDef& B) { return B.Name == W.Name; })) C.Learned.Add(W.Name);
	}
	C.WeaponsUnlocked = WeaponsUnlocked;
	C.Health = PlayerCombat->GetHealth(); C.Mana = PlayerCombat->GetMana();
	C.Blessing = PlayerCombat->GetBlessing(); C.BlessLeft = PlayerCombat->GetBlessLeft(); C.BlessDamage = PlayerCombat->GetBlessDamage(); C.BlessArmour = PlayerCombat->GetBlessArmour();
	if (Weapons.IsValidIndex(PlayerCombat->GetWeaponIndex())) C.Drawn = Weapons[PlayerCombat->GetWeaponIndex()].Name;
	// (the rest of her as she is (the user's of 2026-11-06): statistics, what is on her and for how long, cooldowns, energy, the
	// quick bar, the torch lit, her starting shield's wear, her summons: RDCarry.cpp)
	PlayerCombat->GatherState(C);
	GI->Carry = C;
	// (the game is hers: a hero switched in play (tests) would otherwise start a new game in the next level, her things lost)
	GI->GameHero = CurrentHero;
	// (what the level keeps for the game: the castle's tiers and its first set's looted containers, the town's looted ones)
	if (!bTown)
	{
		// (each dungeon its own: Mistward Castle's fields, the catacombs' under their key (2026-11-06))
		for (const int32 T : TiersOpened) GI->TiersOf(DungeonKey).AddUnique(T);
		for (const FIntVector& K : LootedContainers) if (K.X == 0 && K.Y == 0) GI->StartLootedOf(DungeonKey).AddUnique(K.Z);
	}
	else for (const FIntVector& K : LootedContainers) if (K.X == 0 && K.Y == 0) GI->TownLooted.AddUnique(K.Z);
	// (her things where she fell go with the game, laid again when she comes back to this level (the PR review's find: they
	// went with the level))
	const FName Here(bTown ? TEXT("town") : DungeonKey.IsEmpty() ? TEXT("castle") : *DungeonKey);
	for (const ARDLootPile* Lp : LootPiles)
		if (IsValid(Lp) && Lp->bHers && Lp->Things.Num() > 0)
		{
			FRDCarry Pile; Pile.bValid = true; Pile.Hero = Here; Pile.Things = Lp->Things; Pile.Wear = Lp->Wear; Pile.WornShield = Lp->WornShield;
			GI->HerPiles.Add(Pile);
		}
	UE_LOG(LogRDTownGame, Log, TEXT("RDCARRY saved %s: %d things, armour %s, shield %s, %d rings, %d learned, %.0f hp, %d gold"), *CurrentHero.ToString(), C.Things.Num(),
		*C.WornArmour.ToString(), *C.WornShield.ToString(), C.WornRings.Num(), C.Learned.Num(), C.Health, GI->Gold);
}

bool ARDDungeonGenerator::RestoreCarry()
{
	URDGameInstance* GI = URDGameInstance::Of(this);
	if (!GI || !PlayerCombat || !GI->Carry.bValid || GI->Carry.Hero != CurrentHero) return false;
	const FRDCarry C = GI->Carry;
	PlayerCombat->ClearItems();
	// (the shield her hero starts with is hers for good (bKeepStartGear): what she carried leaves one copy of it out, so it is
	// put back first; the one she wore goes on below)
	if (bKeepStartGear) if (const FName* Sh = StartShield.Find(CurrentHero); Sh && FindItem(*Sh) >= 0) PlayerCombat->AddItem(*Sh, 1);
	// (her hero's own weapons, the spells she learned, the chi attacks she gained; then everything found, as she had it)
	if (C.WeaponsUnlocked > WeaponsUnlocked) UnlockHeroWeapons(C.WeaponsUnlocked - WeaponsUnlocked);
	for (const FName& Sp : C.Learned) if (!PlayerCombat->KnowsSpell(Sp)) PlayerCombat->LearnSpell(Sp);
	PlayerCombat->TakeBack(C.Things, C.Wear, true, C.WornShield);
	if (!C.WornArmour.IsNone() && PlayerCombat->GetItemCount(C.WornArmour) > 0 && PlayerCombat->GetWornArmour() != C.WornArmour) PlayerCombat->WearArmour(C.WornArmour);
	for (const FName& Rg : C.WornRings) if (PlayerCombat->GetItemCount(Rg) > 0) PlayerCombat->WearRing(Rg);
	PlayerCombat->RefreshMaxima();
	if (C.Health > 0.f) PlayerCombat->SetHealth(C.Health);
	if (C.Mana >= 0.f) PlayerCombat->SetMana(C.Mana);
	if (!C.Blessing.IsEmpty() && C.BlessLeft > 1.f) PlayerCombat->Bless(C.Blessing, C.BlessDamage, C.BlessArmour, 0.f, C.BlessLeft);
	if (!C.Drawn.IsNone()) { const int32 Dw = Weapons.IndexOfByPredicate([&](const FRDWeaponDef& W) { return W.Name == C.Drawn; }); if (Dw >= 0 && !Weapons[Dw].bAlongside) PlayerCombat->SelectWeapon(Dw); }
	// (the rest of her as she left the other level: RDCarry.cpp; her summons come to her side once she stands here)
	PlayerCombat->RestoreState(C);
#if !UE_BUILD_SHIPPING
	CarryArrivedLines = PlayerCombat->GetStateLines();          // (for the tests; her summons waiting to come to her side among them)
#endif
	PlayerCombat->ShowMessage(bTown ? FString::Printf(TEXT("%s"), *TownName) : !DungeonTitle.IsEmpty() ? DungeonTitle : FString(TEXT("Mistward Castle")));
	UE_LOG(LogRDTownGame, Log, TEXT("RDCARRY restored %s: %d things, %d weapons, armour %s, %.0f hp"), *CurrentHero.ToString(), C.Things.Num(), Weapons.Num(), *PlayerCombat->GetWornArmour().ToString(), PlayerCombat->GetHealth());
	return true;
}

bool ARDDungeonGenerator::EnterCastle()
{
	if (!bTown || CastleLevel.IsEmpty() || bTownTraveling) return false;
	LastTravel = TEXT("castle");
	if (bTravelDryRun) return true;
	TravelToDungeon(CastleLevel, TEXT("castle"));
	return true;
}

void ARDDungeonGenerator::TravelToDungeon(const FString& Level, const FString& Why)
{
	// (the town's side of every trip down into a dungeon: Mistward Castle by the Mistgate, Vel Morrath's catacombs by the stair
	// beneath its altar)
	WildAutosave(Why);
	SaveCarry();
	if (URDGameInstance* GI = URDGameInstance::Of(this))
	{
		// (her state as she leaves, for the tests: set on the travel only (the town's autosave as she came in wrote it too); a
		// shipped game makes no lines)
#if !UE_BUILD_SHIPPING
		if (PlayerCombat) GI->CarryLeftLines = PlayerCombat->GetStateLines();
#endif
		GI->Arrive = Why;
		// (from another town (its circle, or Vel Morrath's stair): its state into the store, Brokenspire's back into the fields
		// the level reads when she comes back (it always comes back as Brokenspire): else Brokenspire took that town's looted
		// chests and guards, and wrote them over its own in the store at its next unload)
		if (bWild && !bTownHome && GetSection(FIntPoint::ZeroValue))
		{
			SaveTownState();
			const FRDTownSave* B = GI->TownStore.Find(HomeTownName);
			GI->TownLooted = B ? B->Looted : TArray<int32>(); GI->GuardsDead = B ? B->GuardsDead : TArray<int32>();
			GI->CurrentTown = HomeTownName;
		}
	}
	bTownTraveling = true;
	UE_LOG(LogRDTownGame, Log, TEXT("RDTRAVEL into %s (%s) from %s as %s"), *Level, *Why, *TownName, *CurrentHero.ToString());
	UGameplayStatics::OpenLevel(this, FName(*Level), true, FString::Printf(TEXT("Hero=%s"), *CurrentHero.ToString()));
}

bool ARDDungeonGenerator::ReturnToTown()
{
	if (!bTownLink || bTown || TownLevel.IsEmpty() || bTownTraveling) return false;
	if (PlayerCombat && PlayerCombat->IsDead()) return false;
	LastTravel = TEXT("town");
	if (bTravelDryRun) return true;
	SaveCarry();
	if (URDGameInstance* GI = URDGameInstance::Of(this))
	{
		GI->Arrive = TEXT("castle");
		// (from the catacombs (2026-11-06): back before the cathedral of the town she went down from, out in the wilderness: put
		// there as a loaded game is (TickWildLoad builds the town round her))
		if (!DungeonKey.IsEmpty() && !GI->ReturnAt.IsZero())
		{
			GI->Arrive = TEXT("save"); GI->LoadAt = GI->ReturnAt; GI->LoadYaw = GI->ReturnYaw; GI->bLoadPending = true;
		}
#if !UE_BUILD_SHIPPING
		if (PlayerCombat) GI->CarryLeftLines = PlayerCombat->GetStateLines();
#endif
	}
	bTownTraveling = true;
	UE_LOG(LogRDTownGame, Log, TEXT("RDTRAVEL back to %s as %s"), *TownLevel, *CurrentHero.ToString());
	UGameplayStatics::OpenLevel(this, FName(*TownLevel), true, FString::Printf(TEXT("Hero=%s"), *CurrentHero.ToString()));
	return true;
}

// ================================================================================================ play begins, the town is built
void ARDDungeonGenerator::BeginTownPlay()
{
	URDGameInstance* GI = URDGameInstance::Of(this);
	// (autoplay is the castle's: asked of the town, the castle is opened with it)
	if (bTown && !CastleLevel.IsEmpty())
		if (const AGameModeBase* GM = GetWorld()->GetAuthGameMode(); GM && !UGameplayStatics::ParseOption(GM->OptionsString, TEXT("Autoplay")).IsEmpty())
		{
			bOpeningMenu = true;
			UGameplayStatics::OpenLevel(this, FName(*CastleLevel), true, GM->OptionsString.StartsWith(TEXT("?")) ? GM->OptionsString.Mid(1) : GM->OptionsString);
			return;
		}
	if (GI && (GI->GameHero != CurrentHero || GI->GamesStarted == 0)) GI->NewGame(CurrentHero);
	if (bTown)
	{
		int32 Want = StartSeed;
		if (GI)
		{
			if (GI->TownSeed == 0) GI->TownSeed = bTownNewSeed && FixedSessionSeed == 0 ? (int32)(FDateTime::Now().GetTicks() % 2000000000) + 1 : StartSeed;
			Want = GI->TownSeed;
			for (const int32 K : GI->TownLooted) LootedContainers.Add(FIntVector(0, 0, K));
			for (const int32 T : GI->CastleTiers) TiersOpened.AddUnique(T);
		}
		if (Want != StartSeed)
		{
			// (another town than the one saved: the saved one goes, BeginPlay builds this one)
			for (auto& KV : Sections) if (KV.Value) KV.Value->Destroy();
			Sections.Reset();
			StartSeed = Want;
		}
		UE_LOG(LogRDTownGame, Log, TEXT("RDTOWN play: seed %d (%s)"), StartSeed, GI ? TEXT("the game's") : TEXT("no game instance"));
		BeginDayNight();
	}
	else if (bTownLink && GI)
	{
		// (Mistward Castle: the tiers she opened stay open, the first set's opened containers stay opened; the catacombs the same,
		// their own (their DungeonKey))
		const TArray<int32> Tiers = GI->TiersOf(DungeonKey);
		for (const int32 T : Tiers) TiersOpened.AddUnique(T);
		for (const int32 K : GI->StartLootedOf(DungeonKey)) LootedContainers.Add(FIntVector(0, 0, K));
		// (a tier open from an earlier visit: its boss, if she has not killed it, and its guarded ring (PlaceRingGuard skips a
		// ring she has) are set again once she has seen a room of the tier before (the PR review's find: CheckTierOpenings
		// passes an open tier by, so they were never set again))
		for (const int32 T : Tiers)
		{
			if (T < 2) continue;
			if (bBossEncounters && GI->GetCounter(URDGameInstance::DungeonCounter(DungeonKey, FString::Printf(TEXT("bossdone:%d"), T))) == 0) RestoredBossTiers.AddUnique(T);
			if (bRingGuards) RestoredRingTiers.AddUnique(T);
		}
		// (the final boss: slain for the game; placed and not slain before she left, set again once a room of the last tier is
		// seen (its share counted again from nothing would have kept him away))
		if (bFinalBossOn)
		{
			bFinalBossSlain = GI->GetCounter(TEXT("finalboss")) > 0;
			bFinalRestorePending = !bFinalBossSlain && GI->GetCounter(TEXT("finalboss:placed")) > 0;
		}
		GI->Count(URDGameInstance::DungeonCounter(DungeonKey, TEXT("enter")));
	}
}

void ARDDungeonGenerator::AfterTownBuilt()
{
	bTownPlaced = false; bTownTraveling = false;
	// (her things she left lying in this level when she went: laid again by where she comes in, a pile beside the next)
	auto LayPiles = [this](const FVector& At, const FVector& Side)
	{
		URDGameInstance* GI = URDGameInstance::Of(this);
		if (!GI || At.IsZero()) return;
		const FName Here(bTown ? TEXT("town") : DungeonKey.IsEmpty() ? TEXT("castle") : *DungeonKey);
		int32 N = 0;
		for (int32 I = GI->HerPiles.Num() - 1; I >= 0; --I)
		{
			const FRDCarry Pile = GI->HerPiles[I];
			if (Pile.Hero != Here) continue;
			GI->HerPiles.RemoveAt(I);
			if (ARDLootPile* Lp = DropLoot(At + Side * (-150.f + 150.f * (N % 3)) + FVector(0.f, 0.f, 100.f), Pile.Things, Pile.Wear)) { Lp->bHers = true; Lp->WornShield = Pile.WornShield; ++N; }
		}
		if (N > 0) UE_LOG(LogRDTownGame, Log, TEXT("RDCARRY %d of her piles laid again in the %s"), N, *Here.ToString());
	};
	if (bTown)
	{
		SpawnTownPeople();
		SpawnTownGuards();
		ARDSection* S = GetSection(FIntPoint::ZeroValue);
		if (S)
		{
			FActorSpawnParameters Sp; Sp.SpawnCollisionHandlingOverride = ESpawnActorCollisionHandlingMethod::AlwaysSpawn;
			if (MistgateFx) MistgateFx->Destroy();
			if (CircleFx) CircleFx->Destroy();
			// (the Mistgate is Brokenspire's: the wilderness's small towns' keeps have none)
			// (and the holy city's stair down into the catacombs, 2026-11-06)
			if (bTownHome || HasTownDungeon()) if (ARDTeleporter* T = GetWorld()->SpawnActor<ARDTeleporter>(ARDTeleporter::StaticClass(), FTransform(S->MistgateAt + S->MistgateNormal * 160.f), Sp)) { T->Init(this, 0, false); MistgateFx = T; }
			for (const ARDSection::FTownSpot& Ts : S->TownSpots)
				if (Ts.Kind == TS_Circle) if (ARDTeleporter* T = GetWorld()->SpawnActor<ARDTeleporter>(ARDTeleporter::StaticClass(), FTransform(Ts.At + FVector(0, 0, 3.f)), Sp)) { T->Init(this, 0, false); CircleFx = T; }
		}
		LayPiles(GetStartRoomCenter(), FVector(0.f, 1.f, 0.f));
		return;
	}
	if (bTownLink && !TownLevel.IsEmpty())
	{
		// the way back: an arch on a free tile of the great hall, near its middle and off its lanes
		const FVector C = GetStartRoomCenter();
		ARDSection* S = GetSection(FIntPoint::ZeroValue);
		if (!S) return;
		const int32 Room = S->RoomAt(C);
		FVector Best = C; float BestD = MAX_flt;
		for (const FVector& T : S->GetRoomFreeTiles(Room))
		{
			const float D = FMath::Abs(FVector::Dist2D(T, C) - 750.f);
			if (D < BestD) { BestD = D; Best = T; }
		}
		CastleWayBack = Best;
		FActorSpawnParameters Sp; Sp.SpawnCollisionHandlingOverride = ESpawnActorCollisionHandlingMethod::AlwaysSpawn;
		if (CastleWayBackActor) CastleWayBackActor->Destroy();
		if (ARDTeleporter* T = GetWorld()->SpawnActor<ARDTeleporter>(ARDTeleporter::StaticClass(), FTransform(Best + FVector(0, 0, 3.f)), Sp)) { T->Init(this, 0, false); CastleWayBackActor = T; }
		// (beside the arch, not on it: F there takes her back to the town)
		const FVector In = (C - Best).GetSafeNormal2D().IsNearlyZero() ? FVector(1.f, 0.f, 0.f) : (C - Best).GetSafeNormal2D();
		LayPiles(Best + In * 400.f, FVector(-In.Y, In.X, 0.f));
	}
}

void ARDDungeonGenerator::SpawnTownPeople()
{
	for (ARDTownsfolk* P : TownPeople) if (IsValid(P)) P->Destroy();
	TownPeople.Reset();
	ARDSection* S = GetSection(FIntPoint::ZeroValue);
	if (!S) return;
	// (the beds put for the last people: made again for these)
	S->ClearMadeTownBeds();
	TMap<ERDTownRole, TArray<int32>> ByRole;
	// (a town with people of its own for a role (Vel Morrath, 2026-11-06: its archbishop, monks, templars...) has those in that
	// role; the shared ones (no town) fill the others)
	const FString Here = bTownHome ? FString() : TownName;
	TSet<ERDTownRole> OwnRoles;
	if (!Here.IsEmpty()) for (const FRDTownsfolkDef& Df : Townsfolk) if (Df.Town == Here && Df.Mesh) OwnRoles.Add(Df.Role);
	for (int32 I = 0; I < Townsfolk.Num(); ++I)
	{
		const ERDTownRole Ro = Townsfolk[I].Role;
		const FRDTownsfolkDef& Df = Townsfolk[I];
		if (!Df.Town.IsEmpty() && Df.Town != Here) continue;              // (another town's)
		if (Df.Town.IsEmpty() && OwnRoles.Contains(Ro)) continue;          // (this town has its own in this role)
		// (a small town of the wilderness has no elder, scholar or captain of its own: Brokenspire's quests are Brokenspire's)
		if (!bTownHome && Df.Town.IsEmpty() && (Ro == ERDTownRole::Elder || Ro == ERDTownRole::Scholar || Ro == ERDTownRole::Captain)) continue;
		if (Df.Mesh) for (int32 K = 0; K < FMath::Max(1, Df.Count); ++K) ByRole.FindOrAdd(Ro).Add(I);
	}
	TMap<ERDTownRole, int32> Used;
	TMap<int32, int32> InHome;          // (a household's members inside the door side by side: one spot made them stop on each other)
	FActorSpawnParameters Sp; Sp.SpawnCollisionHandlingOverride = ESpawnActorCollisionHandlingMethod::AlwaysSpawn;
	for (int32 K = 0; K < S->TownPosts.Num(); ++K)
	{
		const ARDSection::FTownPost& Po = S->TownPosts[K];
		const TArray<int32>* Defs = ByRole.Find(Po.Role);
		if (!Defs || Defs->Num() == 0) continue;
		int32& U = Used.FindOrAdd(Po.Role);
		const int32 D = (*Defs)[(U++ + (Po.Role == ERDTownRole::Townsfolk ? Po.Index : 0)) % Defs->Num()];
		// (a post on a tile something stands on (a stall, a tree, a building's wall): the nearest free tile of the same
		// ground, outdoors or the same room, a ring at a time)
		FVector At = Po.At;
		const FIntPoint T0 = S->WorldToLocal(At);
		const int32 Room0 = S->RoomAtLocal(T0);
		if (!S->IsWalkable(T0))
			for (int32 Rr = 1; Rr <= 4; ++Rr)
			{
				bool bFound = false;
				for (int32 Dx = -Rr; Dx <= Rr && !bFound; ++Dx)
					for (int32 Dy = -Rr; Dy <= Rr && !bFound; ++Dy)
					{
						if (FMath::Max(FMath::Abs(Dx), FMath::Abs(Dy)) != Rr) continue;
						const FIntPoint Q = T0 + FIntPoint(Dx, Dy);
						if (S->IsWalkable(Q) && S->RoomAtLocal(Q) == Room0) { At = S->LocalToWorld(Q); bFound = true; }
					}
				if (bFound) break;
			}
		ARDTownsfolk* T = GetWorld()->SpawnActor<ARDTownsfolk>(ARDTownsfolk::StaticClass(), FTransform(FRotator(0, Po.Yaw, 0), At + FVector(0, 0, 92.f)), Sp);
		if (!T) continue;
		T->Init(this, S, D, At + FVector(0, 0, 92.f), Po.Yaw, Po.Wander, HashCombine((uint32)StartSeed, (uint32)K * 7919u));
		// (its building: a keeper's where it works (its post inside); a resident's home, a step inside its door)
		if (S->TownBlds.IsValidIndex(Po.Bld))
		{
			const ARDSection::FTownBld& Hb = S->TownBlds[Po.Bld];
			// (the list of 2026-11-10: a home's child lives there as a grown-up does: in at evening, asleep at night)
			const bool bResident = Po.Role == ERDTownRole::Townsfolk || Po.Role == ERDTownRole::Child;
			const FVector Out = FVector(RDTGDir4[Hb.DoorSide].X, RDTGDir4[Hb.DoorSide].Y, 0.f);
			static const float RDTGHomeSide[3] = { 0.f, 95.f, -95.f };
			const float Side = bResident ? RDTGHomeSide[InHome.FindOrAdd(Po.Bld)++ % 3] : 0.f;
			T->SetHome(Po.Bld, bResident ? S->LocalToWorld(Hb.DoorTile) - Out * 230.f + FVector(Out.Y, -Out.X, 0.f) * Side + FVector(0, 0, 92.f) : At + FVector(0, 0, 92.f), bResident);
		}
		TownPeople.Add(T);
	}
	UE_LOG(LogRDTownGame, Log, TEXT("RDTOWN %d townspeople at %d posts"), TownPeople.Num(), S->TownPosts.Num());
	if (bTownBeds) AssignTownBeds(S);          // (the list of 2026-11-10: a bed for each sleeper)
	// (the third list: their rounds of work, the tavern's customers, the pens' animals, the spits)
	SpawnTownLife();
}

void ARDDungeonGenerator::SpawnTownGuards()
{
	for (ARDMonster* M : TownGuards) if (IsValid(M)) M->Destroy();
	TownGuards.Reset();
	ARDSection* S = GetSection(FIntPoint::ZeroValue);
	if (!S || S->CastleHallRoom < 0 || Monsters.Num() == 0 || !bTownHome) return;
	// (5 to 10 of tier 1, the number and kinds from the town's seed; the ones she killed this game stay dead)
	FRandomStream R((int32)HashCombine((uint32)StartSeed, 0x6A4Du));
	TownGuardsPlanned = R.RandRange(FMath::Min(TownGuardsMin, TownGuardsMax), FMath::Max(TownGuardsMin, TownGuardsMax));
	TArray<int32> Kinds;
	for (int32 K = 0; K < Monsters.Num(); ++K) if (Monsters[K].Tier == 1 && Monsters[K].Mesh) Kinds.Add(K);
	if (Kinds.Num() == 0) MonsterKindsFor(FIntPoint::ZeroValue, Kinds);
	if (Kinds.Num() == 0) { UE_LOG(LogRDTownGame, Warning, TEXT("RDTOWN no monster kind for the Mistward Hall's guards")); return; }
	TArray<FVector> Free = S->GetRoomFreeTiles(S->CastleHallRoom);
	for (int32 I = Free.Num() - 1; I > 0; --I) Free.Swap(I, R.RandRange(0, I));
	// (not within 4 m of the hall's door from the entry, nor in front of the Mistgate: room to come in and to leave)
	Free.RemoveAll([&](const FVector& P) { return FVector::Dist2D(P, S->MistgateAt) < 450.f; });
	const URDGameInstance* GI = URDGameInstance::Of(this);
	for (int32 G = 0; G < TownGuardsPlanned && G < Free.Num(); ++G)
	{
		const int32 Kind = Kinds[R.RandRange(0, Kinds.Num() - 1)];
		if (GI && GI->GuardsDead.Contains(G)) continue;
		ARDMonster* M = SpawnMonsterKind(Kind, Free[G], 1, 1.f, 1.f, 1.f, TEXT("Mistward Hall guard"));
		if (!M) continue;
		M->HomeRoom = S->CastleHallRoom; M->GuardIndex = G;
		TownGuards.Add(M);
	}
	UE_LOG(LogRDTownGame, Log, TEXT("RDTOWN %d of %d guards in the Mistward Hall (room %d)"), TownGuards.Num(), TownGuardsPlanned, S->CastleHallRoom);
}

void ARDDungeonGenerator::RebuildTown(int32 Seed)
{
	if (!bTown) return;
	CloseTownPanel();
	for (ARDTownsfolk* P : TownPeople) if (IsValid(P)) P->Destroy();
	TownPeople.Reset();
	for (ARDMonster* M : TownGuards) if (IsValid(M)) M->Destroy();
	TownGuards.Reset();
	for (auto& KV : Sections) if (KV.Value) KV.Value->Destroy();
	Sections.Reset(); MapData.Reset(); LootedContainers.Reset(); Building = nullptr;
	if (URDGameInstance* GI = URDGameInstance::Of(this)) { GI->TownSeed = Seed != 0 ? Seed : (int32)(FDateTime::Now().GetTicks() % 2000000000) + 1; GI->TownLooted.Reset(); GI->GuardsDead.Reset(); StartSeed = GI->TownSeed; }
	else if (Seed != 0) StartSeed = Seed;
	SpawnSection(FIntPoint::ZeroValue, false);
	ReleaseTownSatHold(); TownSatStep = 0; TownSatWait = 0.f;          // (the new town's picture from above; the old one not drawn meanwhile)
	AfterTownBuilt();
	UE_LOG(LogRDTownGame, Log, TEXT("RDTOWN rebuilt from seed %d"), StartSeed);
}

// ================================================================================================ every frame
void ARDDungeonGenerator::TickTown(float Dt, APlayerController* PC)
{
	if (bTown) { TickDayNight(Dt); TickTownLights(Dt); TickTownLife(Dt); TickTownSatellite(Dt); TickSky7(Dt, PC); if (PC && PC->GetPawn()) { TickWildLife(Dt, PC->GetPawn()->GetActorLocation()); if (bWild) TickWildEncounters(Dt, PC->GetPawn()->GetActorLocation()); TickHorse(Dt); TickWild10(Dt, PC->GetPawn()->GetActorLocation()); TickWild11(Dt, PC->GetPawn()->GetActorLocation()); if (bWild) { TickWildSites12(Dt, PC->GetPawn()->GetActorLocation()); TickWildQuests12(Dt, PC->GetPawn()->GetActorLocation()); TickWildRuins12(Dt, PC->GetPawn()->GetActorLocation()); } } }
	APawn* P = PC ? PC->GetPawn() : nullptr;
	if (!P) return;
	ARDSection* S = GetSection(FIntPoint::ZeroValue);
	if (bTown && S && !bTownPlaced)
	{
		// (where she comes in: back from the castle before its door, else in the square by the elder)
		URDGameInstance* GI = URDGameInstance::Of(this);
		FVector At = GetStartRoomCenter() + FVector(0, 0, 100.f);
		float Yaw = P->GetActorRotation().Yaw;
		// (a game loaded: where she was; in the wilderness TickWildLoad puts her there once the world is made)
		if (GI && GI->Arrive == TEXT("save"))
		{
			if (bWild) { GI->Arrive.Reset(); bTownPlaced = true; return; }
			At = GI->LoadAt + FVector(0, 0, 20.f); Yaw = GI->LoadYaw; GI->bLoadPending = false;
		}
		if (GI && GI->Arrive == TEXT("castle") && S->TownBlds.IsValidIndex(S->CastleBld))
		{
			const ARDSection::FTownBld& C = S->TownBlds[S->CastleBld];
			const FVector Out = FVector(RDTGDir4[C.DoorSide].X, RDTGDir4[C.DoorSide].Y, 0.f);
			At = S->LocalToWorld(C.DoorTile) + Out * 600.f + FVector(0, 0, 100.f);
			Yaw = Out.Rotation().Yaw;
		}
		if (GI) GI->Arrive.Reset();
		P->SetActorLocation(At, false, nullptr, ETeleportType::TeleportPhysics);
		if (PC) PC->SetControlRotation(FRotator(-10.f, Yaw, 0.f));
		P->SetActorRotation(FRotator(0, Yaw, 0));
		if (ACharacter* Ch = Cast<ACharacter>(P)) Ch->GetCharacterMovement()->StopMovementImmediately();
		bTownPlaced = true;
		UE_LOG(LogRDTownGame, Log, TEXT("RDTOWN she comes in at (%.0f, %.0f)"), At.X, At.Y);
	}
	// (-RDTownGo=castle: a packaged game's test goes on into the castle at once, once a game: read once, kept in the game
	// instance (a static outlived play-in-editor sessions, and the command line was read every frame: the PR review's find))
	if (bTown && bTownPlaced)
		if (URDGameInstance* GI = URDGameInstance::Of(this); GI && !GI->bTownGoRead)
		{
			GI->bTownGoRead = true;
			FString Go;
			FParse::Value(FCommandLine::Get(), TEXT("RDTownGo="), Go);
			if (Go.IsEmpty()) {}
			else if (Go == TEXT("castle")) { EnterCastle(); return; }
			// (-RDTownGo=catacombs: the way down from the town she starts in (the packaged game's test of the catacombs: the city
			// is a long walk away); she comes back where she stood. Vel Morrath's catacombs by name: with no level given the way down
			// takes the town's own dungeon, so in Ashenreach or Graymourne it opened theirs (PR #25's review))
			else if (Go == TEXT("catacombs"))
			{
				if (!CatacombsLevel.IsEmpty() && DescendToCatacombs(P->GetActorLocation(), P->GetActorRotation().Yaw, CatacombsLevel)) return;
				UE_LOG(LogRDTownGame, Warning, TEXT("RDTOWN -RDTownGo=catacombs refused: %s"), CatacombsLevel.IsEmpty() ? TEXT("no catacombs level") : bTownTraveling ? TEXT("already travelling") : TEXT("the way down refused it"));
			}
			// (-RDTownGo=dungeon:<town>: down into that town's own dungeon from where she stands (2026-11-07: "dungeon:ashenreach",
			// "dungeon:graymourne"); she comes back where she stood)
			else if (Go.StartsWith(TEXT("dungeon:")))
			{
				const FString Want = Go.Mid(8);
				FString Level;
				for (const auto& Kv : TownDungeons) if (Kv.Key.Replace(TEXT(" "), TEXT("")).ToLower() == Want.Replace(TEXT(" "), TEXT("")).ToLower()) Level = Kv.Value;
				if (!Level.IsEmpty() && DescendToCatacombs(P->GetActorLocation(), P->GetActorRotation().Yaw, Level)) return;
				UE_LOG(LogRDTownGame, Warning, TEXT("RDTOWN -RDTownGo=%s refused: %s"), *Go, Level.IsEmpty() ? TEXT("no such town's dungeon") : bTownTraveling ? TEXT("already travelling") : TEXT("the way down refused it"));
			}
			// (-RDTownGo=town:<name>: out to a wilderness town (Vel Morrath: "town:velmorrath"), the packaged game's test of the
			// city: once the wilds are ready, by the map's fast travel; her mark written once it is built round her)
			else if (Go.StartsWith(TEXT("town:")) && bWild) GI->TownGoTown = Go.Mid(5);
			else UE_LOG(LogRDTownGame, Warning, TEXT("RDTOWN -RDTownGo=%s: not a way this level has"), *Go);
		}
	if (bTown && bTownPlaced)
		if (URDGameInstance* GI = URDGameInstance::Of(this); GI && !(GI->TownGoTown.IsEmpty() && GI->TownGoMark.IsEmpty()))
		{
			if (!GI->TownGoTown.IsEmpty() && IsWildReady())
			{
				if (WildTravelToTown(GI->TownGoTown)) { GI->TownGoMark = GI->TownGoTown.Replace(TEXT(" "), TEXT("")).ToLower(); UE_LOG(LogRDTownGame, Log, TEXT("RDTOWN -RDTownGo: out to %s"), *GI->TownGoTown); }
				else UE_LOG(LogRDTownGame, Warning, TEXT("RDTOWN -RDTownGo=town:%s refused: %s"), *GI->TownGoTown, *WildTravelRefusal);
				GI->TownGoTown.Reset();
			}
			const ARDSection* Here = GI->TownGoMark.IsEmpty() ? nullptr : GetSection(FIntPoint::ZeroValue);
			if (Here && !Here->IsBuilding() && !bTownLoading && TownName.Replace(TEXT(" "), TEXT("")).ToLower() == GI->TownGoMark)
			{
				WriteTestMark(TEXT("town"), TownName);
				UE_LOG(LogRDTownGame, Log, TEXT("RDTOWN -RDTownGo: %s built round her"), *TownName);
				GI->TownGoMark.Reset();
			}
		}
	// the Mistgate: walked into, Mistward Castle opens
	if (bTown && bTownHome && S && !bTownTraveling && !S->MistgateAt.IsZero() && FVector::Dist2D(P->GetActorLocation(), S->MistgateAt) < 170.f
		&& !(PlayerCombat && PlayerCombat->IsDead()))
		EnterCastle();
	// a city's way into its dungeon (the cathedral's stair, 2026-11-06; the foundry's gate, the sewer's mouth, 2026-11-07):
	// walked into, its level opens
	else if (HasTownDungeon() && S && !S->IsBuilding() && !bTownTraveling && !S->MistgateAt.IsZero() && FVector::Dist2D(P->GetActorLocation(), S->MistgateAt) < 170.f
		&& !(PlayerCombat && PlayerCombat->IsDead()))
		EnterCatacombs();
}

// ================================================================================================ the town map's zoom and drag
void ARDDungeonGenerator::TickTownMapInput(APlayerController* PC, float Dt)
{
	// (the third list of 2026-11-02: "you should be able to zoom the overhead map in and out and then move it around")
	if (!PC) return;
	const ARDSection* S = GetSection(FIntPoint::ZeroValue);
	const float Span = S ? (S->TownInner.Width() + 1) * TileSize : 48000.f;
	const float Z0 = MapZoom;
	const int32 Wheel = (PC->WasInputKeyJustPressed(EKeys::MouseScrollUp) ? 1 : 0) - (PC->WasInputKeyJustPressed(EKeys::MouseScrollDown) ? 1 : 0)
		+ (PC->WasInputKeyJustPressed(EKeys::Add) || PC->WasInputKeyJustPressed(EKeys::Equals) ? 1 : 0) - (PC->WasInputKeyJustPressed(EKeys::Subtract) || PC->WasInputKeyJustPressed(EKeys::Hyphen) ? 1 : 0);
	if (Wheel != 0) MapZoom *= FMath::Pow(1.25f, (float)Wheel);
	const float Rs = PC->GetInputAnalogKeyState(EKeys::Gamepad_RightY);
	if (FMath::Abs(Rs) > 0.2f) MapZoom *= FMath::Pow(2.2f, Rs * Dt);
	MapZoom = FMath::Clamp(MapZoom, 1.f, FMath::Max(1.f, MapZoomMax));
	// (moved as fast on the screen at every zoom: the arrow keys and the D-pad a third of the sheet a second)
	auto Down = [&](const FKey& K) { return PC->IsInputKeyDown(K) ? 1.f : 0.f; };
	const float Nn = Down(EKeys::Up) + Down(EKeys::Gamepad_DPad_Up) - Down(EKeys::Down) - Down(EKeys::Gamepad_DPad_Down);
	const float Ee = Down(EKeys::Right) + Down(EKeys::Gamepad_DPad_Right) - Down(EKeys::Left) - Down(EKeys::Gamepad_DPad_Left);
	MapPan += FVector2D(FMath::Clamp(Nn, -1.f, 1.f), FMath::Clamp(Ee, -1.f, 1.f)) * (Span * 0.35f / MapZoom) * Dt;
	// (a drag with the left mouse button: the map follows the pointer; the screen's x is the world's +Y, its y the world's -X)
	// (the list of 2026-11-12: a press is a click until it moves past the click's slop (TickMapPointer), only then a drag)
	if (PC->IsInputKeyDown(EKeys::LeftMouseButton) && !bMapPress && TownMapPxPerCm > 0.f)
	{
		float Mx = 0.f, My = 0.f;
		PC->GetInputMouseDelta(Mx, My);
		MapPan += FVector2D(-My, -Mx) * (TownMapDragPx / TownMapPxPerCm);
	}
	if (PC->WasInputKeyJustPressed(EKeys::C) || PC->WasInputKeyJustPressed(EKeys::Gamepad_RightThumbstick)) { MapPan = FVector2D::ZeroVector; MapZoom = 1.f; }
	const float Lim = Span * 0.5f;
	MapPan.X = FMath::Clamp(MapPan.X, -Lim, Lim); MapPan.Y = FMath::Clamp(MapPan.Y, -Lim, Lim);
	if (MapZoom != Z0) UE_LOG(LogRDTownGame, Verbose, TEXT("RDTOWN map zoom %.2f"), MapZoom);
}

// ================================================================================================ the lit buildings
void ARDDungeonGenerator::TickTownLights(float Dt)
{
	ARDSection* S = GetSection(FIntPoint::ZeroValue);
	if (!S || S->TownBlds.Num() == 0) return;
	TownLightsT -= Dt;
	if (TownLightsFor.Get() == S && TownLightsT > 0.f) return;
	TownLightsT = 1.f;
	if (TownLightsFor.Get() != S)
	{
		// (each light and flame inside a building's rectangle, 60 cm in from its edges' outsides: its torches' (a torch's light
		// stands 25 cm off the wall, its flame on the sconce); the castle's and what stands outdoors are left alone)
		TownBldLights.Reset(); TownBldLit.Reset(); TownBldPeople.Reset();
		TownLightsFor = S;
		const float M = TileSize;
		TInlineComponentArray<USceneComponent*> Cs(S);
		for (USceneComponent* C : Cs)
		{
			if (!C || !(C->IsA<UPointLightComponent>() || C->IsA<UNiagaraComponent>())) continue;
			const FVector L = C->GetComponentLocation();
			for (int32 BI = 0; BI < S->TownBlds.Num(); ++BI)
			{
				if (BI == S->CastleBld) continue;
				const ARDSection::FTownBld& B = S->TownBlds[BI];
				const FVector A = S->LocalToWorld(B.Min) - FVector(M * 0.5f - 60.f, M * 0.5f - 60.f, 0), Bm = S->LocalToWorld(B.Max - FIntPoint(1, 1)) + FVector(M * 0.5f - 60.f, M * 0.5f - 60.f, 0);
				if (L.X >= A.X && L.X <= Bm.X && L.Y >= A.Y && L.Y <= Bm.Y) { TownBldLights.FindOrAdd(BI).Add(C); break; }
			}
		}
	}
	TMap<int32, FIntPoint> People;
	for (const ARDTownsfolk* T : TownPeople)
	{
		if (!IsValid(T)) continue;
		const int32 BI = S->TownBuildingAt(T->GetActorLocation());
		if (BI < 0) continue;
		FIntPoint& Pp = People.FindOrAdd(BI);
		if (T->IsSleeping()) ++Pp.Y; else ++Pp.X;
	}
	TownBldPeople = People;
	for (auto& KV : TownBldLights)
	{
		const FIntPoint* Pp = People.Find(KV.Key);
		const bool bLit = !bDayNight || (Pp && Pp->X > 0);
		if (const bool* Was = TownBldLit.Find(KV.Key); Was && *Was == bLit) continue;
		TownBldLit.Add(KV.Key, bLit);
		for (const TWeakObjectPtr<USceneComponent>& W : KV.Value)
		{
			USceneComponent* C = W.Get();
			if (!C) continue;
			C->SetVisibility(bLit);
			if (UNiagaraComponent* Nc = Cast<UNiagaraComponent>(C)) { if (bLit) Nc->Activate(true); else Nc->DeactivateImmediate(); }
		}
	}
}

TArray<FString> ARDDungeonGenerator::GetTownLightLines() const
{
	TArray<FString> Out;
	const ARDSection* S = GetSection(FIntPoint::ZeroValue);
	if (!S) return Out;
	for (const auto& KV : TownBldLights)
	{
		const bool* Lit = TownBldLit.Find(KV.Key);
		const FIntPoint* Pp = TownBldPeople.Find(KV.Key);
		int32 On = 0;
		for (const TWeakObjectPtr<USceneComponent>& W : KV.Value) if (W.IsValid() && W->IsVisible()) ++On;
		Out.Add(FString::Printf(TEXT("%d|%s|%d|%d|%d|%d|%d"), KV.Key, *RDTownKindName(S->TownBlds.IsValidIndex(KV.Key) ? S->TownBlds[KV.Key].Kind : 0), Lit && *Lit ? 1 : 0,
			KV.Value.Num(), Pp ? Pp->X : 0, Pp ? Pp->Y : 0, On));
	}
	return Out;
}

// ================================================================================================ the showcase tour
void ARDDungeonGenerator::StartTownTour(float CastleAutoplaySeconds, const FString& GoFile)
{
	if (!bTown) return;
	bTourOn = true; bTourCmdRead = true; TourPhase = 0; TourT = 0.f; TourCastleSeconds = FMath::Max(0.f, CastleAutoplaySeconds); TourGo = GoFile;
	TourPath.Reset(); TourCheckT = 0.f; bTourJumped = false; TourStuckN = 0; TourDodgeUntil = -1.f;
	TourResult.Reset();
	UE_LOG(LogRDTownGame, Log, TEXT("RDTOUR begun: castle autoplay %.0f s, the run from %.0f m%s"), TourCastleSeconds, TourRunMeters, GoFile.IsEmpty() ? TEXT("") : *FString::Printf(TEXT(", waiting for %s"), *GoFile));
}

FString ARDDungeonGenerator::GetTownTourState() const
{
	const ARDSection* S = GetSection(FIntPoint::ZeroValue);
	const APawn* P = UGameplayStatics::GetPlayerPawn(this, 0);
	const float D = S && P && !S->MistgateAt.IsZero() ? FVector::Dist2D(P->GetActorLocation(), S->MistgateAt) / 100.f : -1.f;
	return FString::Printf(TEXT("%d|%.1f|%d|%.1f|%s"), bTourOn ? TourPhase : -1, TourT, TourPath.Num(), D, *TourResult);
}

void ARDDungeonGenerator::EndTownTour(const FString& Why)
{
	if (!bTourOn) return;
	bTourOn = false; TourResult = Why;
	if (IsTownPanelOpen()) CloseTownPanel();
	UE_LOG(LogRDTownGame, Log, TEXT("RDTOUR ended: %s"), *Why);
}

void ARDDungeonGenerator::TickTownTour(float RealDt)
{
	// (the command line, once a game: -RDTownTour=<castle autoplay seconds> [-RDTourGo=<file>] [-RDTourRun=<m>])
	if (!bTourCmdRead)
	{
		URDGameInstance* GI = URDGameInstance::Of(this);
		bTourCmdRead = true;
		if (!GI || GI->bTourRead) return;
		GI->bTourRead = true;
		float Secs = 0.f; FString Go;
		if (!FParse::Value(FCommandLine::Get(), TEXT("RDTownTour="), Secs)) return;
		FParse::Value(FCommandLine::Get(), TEXT("RDTourGo="), Go);
		FParse::Value(FCommandLine::Get(), TEXT("RDTourRun="), TourRunMeters);
		StartTownTour(Secs, Go);
		return;
	}
	if (!bTourOn || bTownTraveling) return;
	ARDSection* S = GetSection(FIntPoint::ZeroValue);
	APlayerController* PC = UGameplayStatics::GetPlayerController(this, 0);
	ACharacter* Her = PC ? Cast<ACharacter>(PC->GetPawn()) : nullptr;
	if (!S || !Her || !PlayerCombat || !bTownPlaced) return;
	// (she fell (the Mistward Hall's guards): the tour ends there, said so; nobody pushes a dead body on)
	if (PlayerCombat->IsDead()) { EndTownTour(TEXT("she fell")); return; }
	const float Dt = FMath::Min(RealDt, 0.1f);
	TourT += Dt;
	const int32 Elder = FindTownsfolk(ERDTownRole::Elder);
	ARDTownsfolk* E = Elder >= 0 ? TownPeople[Elder].Get() : nullptr;
	const FVector Gate = S->MistgateAt + S->MistgateNormal * 120.f;
	auto Face = [&](const FVector& To, float Pitch)
	{
		const FVector D = (To - Her->GetActorLocation()).GetSafeNormal2D();
		if (D.IsNearlyZero()) return;
		Her->SetActorRotation(FRotator(0, D.Rotation().Yaw, 0));
		PC->SetControlRotation(FRotator(Pitch, D.Rotation().Yaw, 0));
	};
	auto MakePath = [&]()
	{
		TourPath = S->FindPathWorld(Her->GetActorLocation(), Gate);
		if (TourPath.Num() > 0) TourPath.RemoveAt(0);
	};
	switch (TourPhase)
	{
	case 0:
		// (waiting for the recording to begin: the file looked for four times a second)
		if (!TourGo.IsEmpty())
		{
			TourCheckT += Dt;
			if (TourCheckT < 0.25f) break;
			TourCheckT = 0.f;
			if (!FPaths::FileExists(TourGo)) break;
		}
		TourPhase = 1; TourT = 0.f;
		UE_LOG(LogRDTownGame, Log, TEXT("RDTOUR go"));
		break;
	case 1:
		// (before the elder, put now (the recording's setup can take a while, and he wanders): a step and a half in front of
		// him on a free tile of his ground, the nearest to that point, facing him)
		if (E)
		{
			const FVector Want = E->GetActorLocation() + E->GetActorForwardVector() * 150.f;
			const FIntPoint T0 = S->WorldToLocal(Want), Te = S->WorldToLocal(E->GetActorLocation());
			const int32 Room = S->RoomAtLocal(Te);
			FVector At = Want; bool bFound = S->IsWalkable(T0) && T0 != Te && S->RoomAtLocal(T0) == Room;
			float BestD = MAX_flt;
			for (int32 Rr = 1; Rr <= 3 && !bFound; ++Rr)
				for (int32 Dx = -Rr; Dx <= Rr; ++Dx)
					for (int32 Dy = -Rr; Dy <= Rr; ++Dy)
					{
						const FIntPoint Q = T0 + FIntPoint(Dx, Dy);
						if (Q == Te || !S->IsWalkable(Q) || S->RoomAtLocal(Q) != Room) continue;
						const FVector W = S->LocalToWorld(Q);
						const float D = FVector::Dist2D(W, Want);
						if (D < BestD) { BestD = D; At = W; }
					}
			Her->SetActorLocation(FVector(At.X, At.Y, Her->GetActorLocation().Z), false, nullptr, ETeleportType::TeleportPhysics);
			Her->GetCharacterMovement()->StopMovementImmediately();
			Face(E->GetActorLocation(), -8.f);
		}
		TourPhase = 2; TourT = 0.f;
		break;
	case 2:
		if (E) E->FaceToward(Her->GetActorLocation(), 12.f);
		if (TourT > 1.5f)
		{
			// (his panel, as F would open it; no pointer on the screen)
			if (E && OpenTownPanel(TEXT("talk"), Elder)) PC->SetShowMouseCursor(false);
			TourPhase = 3; TourT = 0.f;
		}
		break;
	case 3:
		// (a question asked: his answer. Only a question: the first line can be a quest to take, which would change the game)
		if (TourT > 1.8f && TourT - Dt <= 1.8f)
		{
			const int32 Ask = TownLines.IndexOfByPredicate([](const FTownLine& L) { return L.Act == TEXT("ask"); });
			if (Ask >= 0) ActivateTownEntry(Ask);
		}
		if (TourT > 5.5f)
		{
			CloseTownPanel(); PC->SetShowMouseCursor(false);
			// (the third list: the town's life next, then the map)
			TourPhase = 6; TourT = 0.f; TourLife.Reset(); TourLifeI = -1;
		}
		break;
	case 6:
	{
		// (the town's life: up to three places someone is working at now, of different kinds (a pot or a spit, a pen, a seat or a
		// garden), four seconds each, seen from 3.8 m off to one side of the worker, facing it)
		if (TourLifeI < 0)
		{
			for (const TArray<FName>& Kinds : TArray<TArray<FName>>{ { TEXT("Stir"), TEXT("Crank") }, { TEXT("Scatter") }, { TEXT("SitDrink"), TEXT("SitTalk"), TEXT("Tend") } })
			{
				for (int32 W = 0; W < S->TownWorks.Num(); ++W)
				{
					const ARDTownsfolk* By = TownWorkBy.IsValidIndex(W) ? TownWorkBy[W].Get() : nullptr;
					if (!Kinds.Contains(S->TownWorks[W].Kind) || !By || !By->IsAtWork() || By->GetWorkAt() != W) continue;
					TourLife.Add(W); break;
				}
			}
			TourLifeI = 0; TourT = 0.f;
			UE_LOG(LogRDTownGame, Log, TEXT("RDTOUR the town's life: %d places being worked"), TourLife.Num());
		}
		if (!TourLife.IsValidIndex(TourLifeI)) { TourPhase = 4; TourT = 0.f; break; }
		if (TourT - Dt <= 0.f)
		{
			const ARDSection::FTownWork& Tw = S->TownWorks[TourLife[TourLifeI]];
			const FVector Fw = FRotator(0, Tw.Yaw + 28.f, 0).RotateVector(FVector(380.f, 0, 0));
			Her->SetActorLocation(FVector(Tw.At.X + Fw.X, Tw.At.Y + Fw.Y, Her->GetActorLocation().Z), false, nullptr, ETeleportType::TeleportPhysics);
			Her->GetCharacterMovement()->StopMovementImmediately();
			Face(Tw.At, -12.f);
			UE_LOG(LogRDTownGame, Log, TEXT("RDTOUR life %d: %s at (%.0f, %.0f)"), TourLifeI, *Tw.Kind.ToString(), Tw.At.X, Tw.At.Y);
		}
		if (TourT > 4.f) { ++TourLifeI; TourT = 0.f; }
		break;
	}
	case 4:
		if (TourT > 0.6f && TourT - Dt <= 0.6f)
		{
			// (the way: over the ground to the castle's door, through its rooms to the Mistgate)
			SetMapOpen(true);
			MakePath();
		}
		// (the map zoomed in on where she stands (the third list), then back out to the whole town)
		if (bMapOpen && TourT > 0.6f)
		{
			const float Zt = TourT < 2.2f ? FMath::Lerp(1.f, 2.6f, FMath::Clamp((TourT - 0.9f) / 1.0f, 0.f, 1.f)) : FMath::Lerp(2.6f, 1.f, FMath::Clamp((TourT - 3.2f) / 0.9f, 0.f, 1.f));
			MapZoom = Zt;
			const FVector Mid = (S->LocalToWorld(S->TownInner.Min) + S->LocalToWorld(S->TownInner.Max - FIntPoint(1, 1))) * 0.5f;
			MapPan = (FVector2D(Her->GetActorLocation()) - FVector2D(Mid)) * FMath::Clamp((Zt - 1.f) / 1.6f, 0.f, 1.f);
		}
		// (while the map covers the view: up the way to TourRunMeters before its end (the whole way from the square is about
		// 210 m, 80 s at her run), facing along it)
		if (TourT > 2.5f && !bTourJumped)
		{
			bTourJumped = true;
			if (TourPath.Num() > 2 && TourRunMeters > 0.f)
			{
				float Left = 0.f; int32 K = TourPath.Num() - 1;
				while (K > 0 && Left < TourRunMeters * 100.f) { Left += FVector::Dist2D(TourPath[K], TourPath[K - 1]); --K; }
				if (K > 0)
				{
					const FVector At = TourPath[K];
					Her->SetActorLocation(FVector(At.X, At.Y, Her->GetActorLocation().Z), false, nullptr, ETeleportType::TeleportPhysics);
					Her->GetCharacterMovement()->StopMovementImmediately();
					Face(TourPath[K + 1], -10.f);
					TourPath.RemoveAt(0, K + 1);
					UE_LOG(LogRDTownGame, Log, TEXT("RDTOUR up the way to %.0f m before the Mistgate (%.0f, %.0f)"), Left / 100.f, At.X, At.Y);
				}
			}
		}
		if (TourT > 4.6f)
		{
			SetMapOpen(false);
			if (TourPath.Num() == 0) MakePath();
			PlayerCombat->SetRunMode(true);
			if (URDGameInstance* GI = URDGameInstance::Of(this)) GI->TourCastleSeconds = TourCastleSeconds;
			TourCheckAt = Her->GetActorLocation(); TourCheckT = 0.f; TourStuckN = 0;
			TourPhase = 5; TourT = 0.f;
			UE_LOG(LogRDTownGame, Log, TEXT("RDTOUR the run: %d path points, %.0f m to the Mistgate"), TourPath.Num(), FVector::Dist2D(Her->GetActorLocation(), S->MistgateAt) / 100.f);
		}
		break;
	case 5:
	{
		// (a run that does not arrive (a door that never opens, the guards in the way): through the Mistgate after the time,
		// said so in the log and in the tour's state)
		if (TourT > TourRunTimeout) { EndTownTour(TEXT("the run took too long: the Mistgate opened for her")); EnterCastle(); return; }
		const FVector L = Her->GetActorLocation();
		while (TourPath.Num() > 0 && FVector::Dist2D(L, TourPath[0]) < 90.f) TourPath.RemoveAt(0);
		const FVector Goal = TourPath.Num() > 0 ? TourPath[0] : S->MistgateAt;
		FVector D = Goal - L; D.Z = 0.f; D = D.GetSafeNormal();
		// (stuck twice running: a sidestep, one way then the other, past what holds her (a guard, a stall's corner))
		if (TourT < TourDodgeUntil) D = FRotator(0.f, TourDodgeSign * 70.f, 0.f).RotateVector(D);
		S->OpenDoorAhead(L, D, 200.f, false);
		Her->AddMovementInput(D, 1.f);
		// (the view follows her way, eased)
		const FRotator Cr = PC->GetControlRotation();
		PC->SetControlRotation(FRotator(-10.f, FMath::RInterpTo(FRotator(0, Cr.Yaw, 0), FRotator(0, D.Rotation().Yaw, 0), Dt, 2.5f).Yaw, 0.f));
		// (stuck 2 s: the way found again from where she stands, a jump; again: the sidestep)
		TourCheckT += Dt;
		if (TourCheckT > 2.f)
		{
			if (FVector::Dist2D(L, TourCheckAt) < 80.f)
			{
				++TourStuckN;
				MakePath();
				Her->Jump();
				if (TourStuckN >= 2) { TourDodgeSign = (TourStuckN % 2 == 0) ? 1.f : -1.f; TourDodgeUntil = TourT + 0.9f; }
				UE_LOG(LogRDTownGame, Log, TEXT("RDTOUR stuck at (%.0f, %.0f) (%d): the way again, %d points"), L.X, L.Y, TourStuckN, TourPath.Num());
			}
			else TourStuckN = 0;
			TourCheckAt = L; TourCheckT = 0.f;
		}
		break;
	}
	default: break;
	}
}

// ================================================================================================ F in the town
/** a title that says its own article ("a townswoman on the road to ...") is said as it is; another takes "the" */
static FString RDTTheTitle(const FString& T, bool bCap) { const bool bArt = T.StartsWith(TEXT("a ")) || T.StartsWith(TEXT("an ")); return bArt ? (bCap ? T.Left(1).ToUpper() + T.Mid(1) : T) : (bCap ? TEXT("The ") : TEXT("the ")) + T; }
/** a role F wakes to serve at night: a quest's giver or a keeper of a service */
static bool RDTServes(ERDTownRole R)
{
	return R == ERDTownRole::Elder || R == ERDTownRole::Scholar || R == ERDTownRole::Captain || R == ERDTownRole::Smith || R == ERDTownRole::Trader
		|| R == ERDTownRole::Healer || R == ERDTownRole::Priest || R == ERDTownRole::Keeper;
}

FString ARDDungeonGenerator::TownDescribe(const FVector& From) const
{
	if (!bTown)
	{
		if (bTownLink && !CastleWayBack.IsZero() && FVector::Dist2D(From, CastleWayBack) < 260.f && FMath::Abs(From.Z - CastleWayBack.Z) < 250.f) return FString::Printf(TEXT("return to %s"), *WayBackName());
		return TableFoodDescribe(From);          // (the list of 2026-11-10: a prep table's food in the castle)
	}
	if (IsTownPanelOpen()) return FString();
	// (a farmstead's family out in the wilds (the list of 2026-11-08b))
	// (the list of 2026-11-10's sixth phase: a wild house's door, before the wild folk when it is the nearer (PR #43's review))
	{
		int32 Di = -1; const ARDWildChunk* Dc = bWild && bWildHouseInsides ? WildDoorNear(From, 190.f, Di) : nullptr;
		const ARDTownsfolk* Wf = WildFolkForF(From);
		if (Dc && (!Wf || FVector::Dist2D(Dc->Doors[Di].At, From) < FVector::Dist2D(Wf->GetActorLocation(), From))) return WildDoorDescribe(From);
		if (Wf) return FString::Printf(TEXT("talk to %s"), *RDTTheTitle(Wf->Title, false));
	}
	// (someone near: talk)
	int32 Who = -1; float Best = 240.f;
	for (int32 I = 0; I < TownPeople.Num(); ++I)
		if (const ARDTownsfolk* T = TownPeople[I]; IsValid(T) && !(bTownSkipSleepers && T->IsSleeping() && !RDTServes(T->TownRole))) { const float D = FVector::Dist2D(T->GetActorLocation(), From); if (D < Best && FMath::Abs(T->GetActorLocation().Z - From.Z) < 200.f) { Best = D; Who = I; } }
	// (a door or a container nearer than them: that is what F does)
	if (Who >= 0) if (const ARDSection* S0 = GetSection(FIntPoint::ZeroValue)) { bool bD0 = false; int32 I0 = -1; if (Best > 160.f || S0->FindNearestInteractive(From, Best, bD0, I0) < Best - 30.f) Who = -1; }
	if (Who >= 0)
	{
		// (one asleep who only talks: what else F reaches comes first; a keeper or a quest's giver wakes to serve)
		if (TownPeople[Who]->IsSleeping() && !RDTServes(TownPeople[Who]->TownRole))
		{
			bTownSkipSleepers = true; const FString Else = TownDescribe(From); bTownSkipSleepers = false;
			return Else.IsEmpty() ? FString::Printf(TEXT("%s (asleep)"), *TownPeople[Who]->Title) : Else;
		}
		return FString::Printf(TEXT("talk to %s"), *TownPeople[Who]->Title);
	}
	if (const FString Th = TownThingDescribe(From); !Th.IsEmpty()) return Th;
	const ARDSection* S = GetSection(FIntPoint::ZeroValue);
	if (!S) return FString();
	for (const ARDSection::FTownSpot& Sp : S->TownSpots)
	{
		const float D = FVector::Dist2D(Sp.At, From);
		switch (Sp.Kind)
		{
		case TS_Counter: if (D < 260.f) return TEXT("trade"); break;
		case TS_Basin: if (D < 260.f) return TEXT("be healed"); break;
		case TS_Altar: if (D < 330.f) return TEXT("pray at the altar"); break;
		case TS_Stable: if (D < 420.f && !bMounted) return HasHorse() ? FString(TEXT("the stable: call your horse")) : FString::Printf(TEXT("the stable: a horse for %d gold"), HorsePriceNow()); break;
		case TS_Stash: if (D < 240.f) return TEXT("open your storage"); break;
		case TS_Smith: if (D < 230.f) return TEXT("the smith's work"); break;
		case TS_Circle: if (D < 620.f) return TEXT("touch the teleport circle"); break;
		case TS_Board: if (D < 260.f) return TEXT("read the quest board"); break;
		case TS_Gate: if (D < 520.f && !bWild) return TEXT("the gate (barred)"); break;
		default: break;
		}
	}
	bool bDoor = false; int32 I = -1;
	if (S->FindNearestInteractive(From, 260.f, bDoor, I) < 1e8f && bDoor && S->BoardedDoorBld(I) >= 0) return TEXT("pry the boards loose");
	return FString();
}

FString ARDDungeonGenerator::TownInteract(const FVector& From)
{
	if (!bTown)
	{
		if (bTownLink && !CastleWayBack.IsZero() && FVector::Dist2D(From, CastleWayBack) < 260.f && FMath::Abs(From.Z - CastleWayBack.Z) < 250.f) { ReturnToTown(); return TEXT("town"); }
		return TableFoodTake(From);          // (the list of 2026-11-10: a prep table's food in the castle)
	}
	if (TownPanelClosedFrame == GFrameCounter) return TEXT("closed");
	// (the list of 2026-11-12: a wild quest's thing within reach (a clue, a flower, a beast beaten down, a horse))
	if (bWild) if (const FString Qd = WildQuestInteract(From); !Qd.IsEmpty()) return Qd;
	// (a farmstead's family: they turn to her and say a line of their own)
	{
		int32 Di = -1; const ARDWildChunk* Dc = bWild && bWildHouseInsides ? WildDoorNear(From, 190.f, Di) : nullptr;
		const ARDTownsfolk* Wf0 = WildFolkForF(From);
		if (Dc && (!Wf0 || FVector::Dist2D(Dc->Doors[Di].At, From) < FVector::Dist2D(Wf0->GetActorLocation(), From))) return WildDoorInteract(From);
	}
	if (ARDTownsfolk* Wf = WildFolkForF(From))
	{
		Wf->FaceToward(From, 8.f);
		// (the list of 2026-11-12: a structure's prisoner freed, a quest's person spoken to)
		if (const FString Did = WildSiteTalk(Wf); !Did.IsEmpty()) return Did;
		// (a farm's people only: the director's travellers are not farm folk (PR #50's review))
		if (!WildRoamFolk.Contains(TWeakObjectPtr<ARDTownsfolk>(Wf))) TownCount(TEXT("talk:farm"));
		const FString Line = Wf->NextLine();
		LastBark = FString::Printf(TEXT("%s|%s"), *Wf->Title, *Line);
		if (PlayerCombat && !Line.IsEmpty()) PlayerCombat->ShowMessage(FString::Printf(TEXT("%s:  \"%s\""), *RDTTheTitle(Wf->Title, true), *Line));
		// (the list of 2026-11-11: one met on the way gives her what they have, the first time she speaks to them)
		if ((!Wf->WildGift.IsEmpty() || Wf->WildGiftGold > 0) && GiveWildGift(Wf)) return TEXT("gift");
		return TEXT("bark");
	}
	int32 Who = -1; float Best = 240.f;
	for (int32 I = 0; I < TownPeople.Num(); ++I)
		if (const ARDTownsfolk* T = TownPeople[I]; IsValid(T) && !(bTownSkipSleepers && T->IsSleeping() && !RDTServes(T->TownRole))) { const float D = FVector::Dist2D(T->GetActorLocation(), From); if (D < Best && FMath::Abs(T->GetActorLocation().Z - From.Z) < 200.f) { Best = D; Who = I; } }
	if (Who >= 0) if (const ARDSection* S0 = GetSection(FIntPoint::ZeroValue)) { bool bD0 = false; int32 I0 = -1; if (Best > 160.f || S0->FindNearestInteractive(From, Best, bD0, I0) < Best - 30.f) Who = -1; }
	if (Who >= 0)
	{
		ARDTownsfolk* T = TownPeople[Who];
		// (the list of 2026-11-10: asleep, it sleeps on: no turning, no line; what else F reaches comes first (PR #41's review); a keeper
		// or a quest's giver wakes to serve)
		if (T->IsSleeping() && !RDTServes(T->TownRole))
		{
			bTownSkipSleepers = true; const FString Else = TownInteract(From); bTownSkipSleepers = false;
			if (!Else.IsEmpty()) return Else;
			if (PlayerCombat) PlayerCombat->ShowMessage(FString::Printf(TEXT("The %s is asleep"), *T->Title.ToLower()));
			return TEXT("asleep");
		}
		T->FaceToward(From, 8.f);
		TownCount(FString::Printf(TEXT("talk:%s"), *RDTRoleName(T->TownRole)));
		// (the elder, the scholar, the captain: their panel; a keeper: a word and the service of the building; the others a line)
		if (T->TownRole == ERDTownRole::Elder || T->TownRole == ERDTownRole::Scholar || T->TownRole == ERDTownRole::Captain) { OpenTownPanel(TEXT("talk"), Who); return TEXT("talk"); }
		const FString Line = T->NextLine();
		LastBark = FString::Printf(TEXT("%s|%s"), *T->Title, *Line);
		if (PlayerCombat && !Line.IsEmpty()) PlayerCombat->ShowMessage(FString::Printf(TEXT("%s:  \"%s\""), *T->Title, *Line));
		const FName Service = T->TownRole == ERDTownRole::Smith ? FName(TEXT("smith")) : T->TownRole == ERDTownRole::Trader ? FName(TEXT("store")) : T->TownRole == ERDTownRole::Healer ? FName(TEXT("healer"))
		                    : T->TownRole == ERDTownRole::Priest ? FName(TEXT("temple")) : T->TownRole == ERDTownRole::Keeper ? FName(TEXT("stash")) : NAME_None;
		if (!Service.IsNone()) { OpenTownPanel(Service, Who); TownBody = Line; }
		return TEXT("bark");
	}
	if (const FString Th = TownThingInteract(From); !Th.IsEmpty()) return Th;
	ARDSection* S = GetSection(FIntPoint::ZeroValue);
	if (!S) return FString();
	for (const ARDSection::FTownSpot& Sp : S->TownSpots)
	{
		const float D = FVector::Dist2D(Sp.At, From);
		FName Panel = NAME_None;
		switch (Sp.Kind)
		{
		case TS_Counter: if (D < 260.f) Panel = TEXT("store"); break;
		case TS_Basin: if (D < 260.f) Panel = TEXT("healer"); break;
		case TS_Altar: if (D < 330.f) Panel = TEXT("temple"); break;
		case TS_Stable: if (D < 420.f && !bMounted) Panel = TEXT("stable"); break;
		case TS_Stash: if (D < 240.f) Panel = TEXT("stash"); break;
		case TS_Smith: if (D < 230.f) Panel = TEXT("smith"); break;
		case TS_Circle: if (D < 620.f) Panel = TEXT("circle"); break;
		case TS_Board: if (D < 260.f) Panel = TEXT("board"); break;
		case TS_Gate:
			if (D < 520.f && !bWild)
			{
				if (PlayerCombat) PlayerCombat->ShowMessage(TEXT("The gate is barred: the wilderness beyond is not safe yet (it opens in a later chapter)"));
				return TEXT("gate");
			}
			break;
		default: break;
		}
		if (!Panel.IsNone()) { OpenTownPanel(Panel); return Panel.ToString(); }
	}
	bool bDoor = false; int32 I = -1;
	if (S->FindNearestInteractive(From, 260.f, bDoor, I) < 1e8f && bDoor)
	{
		const int32 Bi = S->BoardedDoorBld(I);
		if (Bi >= 0)
		{
			S->PryBoards(Bi);
			TownCount(TEXT("boards"));
			PlaySoundAt(TEXT("Player.Break"), From);
			if (PlayerCombat) PlayerCombat->ShowMessage(TEXT("You pry the boards loose: the door is free"));
			return TEXT("boards");
		}
	}
	return FString();
}

// ================================================================================================ counting, gold from kills and containers
void ARDDungeonGenerator::TownCount(const FString& Key, int32 Amount)
{
	if (URDGameInstance* GI = URDGameInstance::Of(this)) GI->Count(Key, Amount);
}

void ARDDungeonGenerator::TownCountMax(const FString& Key, int32 Value)
{
	if (URDGameInstance* GI = URDGameInstance::Of(this)) GI->CountMax(Key, Value);
}

int32 ARDDungeonGenerator::WildGoldAt(int32 Base, const FVector& At) const
{
	// (the wilds' tier is the game's already)
	return Base <= 0 ? 0 : FMath::RoundToInt(Base * RDTierGold(IsWildReady() ? Wild->TierAt(At.X / 100.0, At.Y / 100.0) : 1));
}

void ARDDungeonGenerator::TownOnKill(ARDMonster* M, bool bBossKill)
{
	if (!M || M->IsAlly()) return;
	// (the monster's tier in the game's: a dungeon's own through its base, the wilds' already the game's)
	const float T = RDTierGold(GlobalTier(FMath::Max(1, M->Tier)));
	// (the roll a hash of the monster, not a stream the play draws from)
	const uint32 H = HashCombine(GetTypeHash(M->GetUniqueID()), (uint32)SessionSeed ^ 0x601Du);
	int32 Gold = FMath::RoundToInt(FMath::Lerp(KillGold.X, KillGold.Y, (H % 1000u) / 999.f) * T);
	if (bBossKill || M->bBoss) Gold += FMath::RoundToInt(BossGold * T);
	// (the list of 2026-11-11: Curse of Greed: half as much gold again, and a thing besides one time in seven or so)
	if (M->HasCurse11(ERDCurseEffect::Greed))
	{
		const int32 More = FMath::RoundToInt(Gold * M->CurseAmount11(ERDCurseEffect::Greed));
		Gold += More; GreedGold += More;
		if ((float)(HashCombine(H, 0x6EEDu) % 1000u) / 1000.f < 0.15f && M->Section)
		{
			const FName Thing = LootOf(M->Section->Coord, (int32)(H % 997u) + 4000);
			// (the monster's, not her things (PR #48's review: a pile is hers by default))
			if (!Thing.IsNone()) { TArray<float> Wr; Wr.Add(-1.f); if (ARDLootPile* Pl = DropLoot(M->GetActorLocation(), { Thing }, Wr)) { Pl->bHers = false; ++GreedThings; } }
		}
	}
	if (Gold > 0) AddGold(Gold, bBossKill || M->bBoss ? TEXT("the boss's hoard") : FString());
	if (bTown)
	{
		if (M->GuardIndex >= 0)
		{
			TownCount(TEXT("guards"));
			if (URDGameInstance* GI = URDGameInstance::Of(this)) GI->GuardsDead.AddUnique(M->GuardIndex);
		}
		return;
	}
	TownCount(TEXT("kills"));
	TownCount(FString::Printf(TEXT("kind:%s"), *M->MonsterName.ToString()));
	if (bBossKill || M->bBoss) TownCount(TEXT("boss"));
	// (another dungeon's kills under its key too: Vel Morrath's quests count the catacombs' (2026-11-06))
	if (!DungeonKey.IsEmpty())
	{
		TownCount(DungeonCounterName(TEXT("kills")));
		if (bBossKill || M->bBoss) TownCount(DungeonCounterName(TEXT("boss")));
	}
}

void ARDDungeonGenerator::TownOnContainer(ARDSection* Section, int32 Key, const FVector& At)
{
	if (!Section) return;
	const float T = bTown ? 1.f : RDTierGold(GlobalTier(FMath::Max(1, TierOf(Section->Coord))));
	const uint32 H = HashCombine(HashCombine((uint32)(bTown ? StartSeed : SessionSeed), GetTypeHash(Section->Coord)), (uint32)Key * 2654435761u ^ 0x60D1u);
	if ((H % 1000u) / 1000.f < ContainerGoldChance)
	{
		const int32 Gold = FMath::RoundToInt(FMath::Lerp(ContainerGold.X, ContainerGold.Y, ((H >> 10) % 1000u) / 999.f) * T);
		AddGold(Gold, TEXT("in the container"));
	}
	if (URDGameInstance* GI = URDGameInstance::Of(this); GI && Section->Coord == FIntPoint::ZeroValue)
		(bTown ? GI->TownLooted : GI->CastleStartLooted).AddUnique(Key);
}

// ================================================================================================ quests
int32 ARDDungeonGenerator::QuestProgress(const FRDQuestDef& Q) const
{
	const URDGameInstance* GI = URDGameInstance::Of(this);
	if (!GI) return 0;
	// (counted whole: the highest tier open; the Mistward Hall's guards, who stay dead once killed: ones killed before the
	// quest was taken count, or the quest could ask for more than are left)
	// (both read from the state itself, not a counter beside it (the PR review's finds): the tier from the tiers open, so a
	// tier opened by any way counts; the guards from the ones dead in this town, so a town built again starts over)
	// (Mistward Castle's own tiers: the catacombs' do not count for Brokenspire's quests (PR #23's review))
	if (Q.Goal == TEXT("tier")) return FMath::Max(GI->GetCounter(Q.Goal), DungeonTierReached(FString()));
	// (a dungeon's own tier ("vel_morrath:tier", the catacombs' deepest floor opened): whole, as the castle's, from its tiers)
	if (Q.Goal.EndsWith(TEXT(":tier"))) return FMath::Max(GI->GetCounter(Q.Goal), DungeonTierReached(Q.Goal.LeftChop(5)));
	if (Q.Goal == TEXT("guards")) return GI->GuardsDead.Num();
	// (the wilderness's (2026-11-07): read from the world, whole: the den's pack dead, the patrol found)
	if (Q.Goal.StartsWith(TEXT("wild:"))) return WildQuestProgress(Q.Goal);
	const FRDQuestState* St = GI->FindQuest(Q.Id);
	const int32 Base = St ? St->Base : 0;
	return FMath::Max(0, GI->GetCounter(Q.Goal) - Base);
}

static FString RDQuestStateOf(const URDGameInstance* GI, const FRDQuestDef& Q, int32 Progress, bool bWildOpen)
{
	// (the wilderness's quests wait on a level without it, and until it is ready (as the accept does: PR #25's review, offered
	// before it was, a quest was then refused); since 2026-11-07 Brokenspire's gate opens on it)
	// (only a quest not taken yet waits: one taken, ready or done keeps its state while the wilds start again after a trip
	// (PR #26's review))
	const FRDQuestState* St = GI ? GI->FindQuest(Q.Id) : nullptr;
	if ((!St || St->State == 0) && !bWildOpen && Q.Goal.StartsWith(TEXT("wild:"))) return TEXT("later");
	if (!St || St->State == 0) return TEXT("offered");
	if (St->State == 2) return TEXT("done");
	return Progress >= Q.Count ? TEXT("ready") : TEXT("taken");
}

TArray<FString> ARDDungeonGenerator::GetQuestLines() const
{
	TArray<FString> Out;
	const URDGameInstance* GI = URDGameInstance::Of(this);
	for (const FRDQuestDef& Q : Quests)
	{
		const int32 P = QuestProgress(Q);
		Out.Add(FString::Printf(TEXT("%s|%s|%s|%s|%d|%d|%s"), *Q.Id.ToString(), *Q.Giver.ToString(), *Q.Title, *RDQuestStateOf(GI, Q, P, bWild && IsWildReady()), FMath::Min(P, Q.Count), Q.Count, *Q.Hint));
	}
	// (the list of 2026-11-12: the wilds' quests under way, their stage's line)
	for (const FString& L : GetWildQuestRunLines())
	{
		TArray<FString> F; L.ParseIntoArray(F, TEXT("|"), false);
		if (F.Num() < 15) continue;
		const int32 St = FCString::Atoi(*F[3]);
		if (St < 1 || St >= 90) continue;
		const FRDWildQuestDef* Wq = WildQuests.FindByPredicate([&](const FRDWildQuestDef& D) { return D.Name.ToString() == F[2]; });
		Out.Add(FString::Printf(TEXT("wq12:%s|Wild|%s|taken|%s|%s|%s"), *F[1], Wq ? *Wq->Title : *F[2], *F[5], *F[6], *F[14]));
	}
	return Out;
}

bool ARDDungeonGenerator::IsQuestHere(const FRDQuestDef& Q) const
{
	return Q.Town == (bTownHome ? FString() : TownName);
}

TArray<FString> ARDDungeonGenerator::GetQuestLinesHere() const
{
	// (the quests of the town she is in: a giver's mark is keyed by role, and Vel Morrath's archbishop is an Elder as
	// Brokenspire's elder is (PR #23's review: each showed the other's "!" and "?"))
	TArray<FString> Out;
	const URDGameInstance* GI = URDGameInstance::Of(this);
	for (const FRDQuestDef& Q : Quests)
	{
		if (!IsQuestHere(Q)) continue;
		const int32 P = QuestProgress(Q);
		Out.Add(FString::Printf(TEXT("%s|%s|%s|%s|%d|%d|%s"), *Q.Id.ToString(), *Q.Giver.ToString(), *Q.Title, *RDQuestStateOf(GI, Q, P, bWild && IsWildReady()), FMath::Min(P, Q.Count), Q.Count, *Q.Hint));
	}
	return Out;
}

bool ARDDungeonGenerator::TownQuestAction(FName Act, FName Id)
{
	URDGameInstance* GI = URDGameInstance::Of(this);
	const FRDQuestDef* Q = Quests.FindByPredicate([Id](const FRDQuestDef& D) { return D.Id == Id; });
	if (!GI || !Q) return false;
	FRDQuestState* St = GI->FindQuest(Id);
	if (Act == TEXT("accept"))
	{
		if (St && St->State > 0) return false;
		// (the wilderness's need the wilderness: Brokenspire's level with its gate open)
		if (Q->Goal.StartsWith(TEXT("wild:")) && (!bWild || !IsWildReady())) { SetTownNote(TEXT("The wilderness beyond the gate is not open yet")); return false; }
		FRDQuestState N; N.Id = Id; N.State = 1; N.Base = Q->Goal == TEXT("tier") || Q->Goal == TEXT("guards") || Q->Goal.StartsWith(TEXT("wild:")) ? 0 : GI->GetCounter(Q->Goal);
		if (St) *St = N; else GI->Quests.Add(N);
		TownBody = Q->Offer;
		SetTownNote(FString::Printf(TEXT("Quest taken: %s"), *Q->Title));
		PlaySoundAt(TEXT("Player.Loot"), PlayerCombat && PlayerCombat->GetOwner() ? PlayerCombat->GetOwner()->GetActorLocation() : GetActorLocation());
		UE_LOG(LogRDTownGame, Log, TEXT("RDQUEST taken %s (%s, base %d)"), *Id.ToString(), *Q->Goal, N.Base);
		return true;
	}
	if (Act == TEXT("turnin"))
	{
		if (!St || St->State != 1 || QuestProgress(*Q) < Q->Count) return false;
		St->State = 2;
		TownBody = Q->Done;
		if (Q->Gold > 0) AddGold(Q->Gold, Q->Title);
		if (!Q->RewardItem.IsNone() && PlayerCombat) PlayerCombat->AddItem(Q->RewardItem, 1);
		GI->Count(TEXT("quests"));
		SetTownNote(Q->RewardItem.IsNone() ? FString::Printf(TEXT("Quest done: %s  (+%d gold)"), *Q->Title, Q->Gold)
		                                   : FString::Printf(TEXT("Quest done: %s  (+%d gold, %s)"), *Q->Title, Q->Gold, *Q->RewardItem.ToString()));
		UE_LOG(LogRDTownGame, Log, TEXT("RDQUEST done %s: %d gold, %s"), *Id.ToString(), Q->Gold, *Q->RewardItem.ToString());
		return true;
	}
	return false;
}

// ================================================================================================ the panel
void ARDDungeonGenerator::SetTownNote(const FString& Text)
{
	TownNote = Text;
	TownNoteTime = GetWorld() ? GetWorld()->GetTimeSeconds() : 0.f;
}

int32 ARDDungeonGenerator::FindTownsfolk(ERDTownRole InRole) const
{
	for (int32 I = 0; I < TownPeople.Num(); ++I) if (IsValid(TownPeople[I]) && TownPeople[I]->TownRole == InRole) return I;
	return -1;
}

bool ARDDungeonGenerator::OpenTownPanel(FName Kind, int32 Who)
{
	if (!bTown || !PlayerCombat || PlayerCombat->IsDead() || Kind.IsNone()) return false;
	if (PlayerCombat->IsInventoryOpen()) PlayerCombat->SetInventoryOpen(false);
	if (PlayerCombat->IsCraftingOpen()) PlayerCombat->SetCraftingOpen(false);
	const bool bWasOpen = IsTownPanelOpen();
	TownPanel = Kind; TownWho = Who; TownTab = 0; TownCursor = 0; TownNote.Reset(); TownBody.Reset();
	ResetStartHold();          // (a Start pressed before the panel is not acted on when it shuts: PR #29's review)
	// (a key or the stick held as it opens waits to be let go before it steps the cursor: TickTownPanel)
	if (!bWasOpen) TownRepeatDir = 2;
	BuildTownLines();
	if (!bWasOpen)
	{
		if (PlayerCombat->bInventoryPausesGame) UGameplayStatics::SetGamePaused(this, true);
		if (APlayerController* PC = UGameplayStatics::GetPlayerController(this, 0)) { PC->SetShowMouseCursor(true); FInputModeGameAndUI M; M.SetHideCursorDuringCapture(false); PC->SetInputMode(M); }
		if (PlayerCombat->GetOwner()) PlaySoundAt(TEXT("Player.Inventory"), PlayerCombat->GetOwner()->GetActorLocation());
	}
	UE_LOG(LogRDTownGame, Log, TEXT("RDTOWN panel %s (%d lines)"), *Kind.ToString(), TownLines.Num());
	return true;
}

void ARDDungeonGenerator::CloseTownPanel()
{
	if (!IsTownPanelOpen()) return;
	TownPanel = NAME_None; TownWho = -1; TownLines.Reset(); TownRowBoxes.Reset(); TownTabBoxes.Reset();
	TownPanelClosedFrame = GFrameCounter;
	ResetStartHold();
	UGameplayStatics::SetGamePaused(this, false);
	if (APlayerController* PC = UGameplayStatics::GetPlayerController(this, 0)) { PC->SetShowMouseCursor(false); PC->SetInputMode(FInputModeGameOnly()); }
}

TArray<FString> ARDDungeonGenerator::GetTownPanelLines() const
{
	TArray<FString> Out;
	for (const FTownLine& L : TownLines) Out.Add(FString::Printf(TEXT("%s|%s|%s|%d"), *L.Act.ToString(), *L.Label, *L.Tag, L.bOn ? 1 : 0));
	return Out;
}

void ARDDungeonGenerator::MoveTownCursor(int32 Step)
{
	const int32 N = TownLines.Num();
	if (N == 0) { TownCursor = 0; return; }
	TownCursor = ((TownCursor + Step) % N + N) % N;
}

void ARDDungeonGenerator::SetTownTab(int32 Tab)
{
	if (TownPanel != TEXT("store") && TownPanel != TEXT("stash")) return;
	TownTab = FMath::Clamp(Tab, 0, 1); TownCursor = 0;
	BuildTownLines();
}

/** a found weapon's or a carried thing's line for the sell and storage lists: "w:<index>" / "i:<name>" */
static void RDTownThingLines(const ARDDungeonGenerator* G, const URDCombatComponent* Pc, TArray<ARDDungeonGenerator::FTownLine>& Out, FName Act, bool bPrices)
{
	for (int32 I = 0; I < G->Weapons.Num(); ++I)
	{
		const FRDWeaponDef& W = G->Weapons[I];
		if (W.Item.IsNone() || W.bScroll) continue;
		ARDDungeonGenerator::FTownLine L; L.Act = Act; L.Arg = FString::Printf(TEXT("w:%d"), I);
		L.Label = W.Item.ToString();
		const float Full = Pc->GetWeaponDurability(I), Left = Pc->GetWeaponWear(I);
		const int32 P = bPrices ? FMath::Max(1, FMath::RoundToInt(G->PriceOf(W.Item) * G->SellShare * (Full > 0.f ? FMath::Clamp(Left / Full, 0.2f, 1.f) : 1.f))) : 0;
		L.Tag = bPrices ? FString::Printf(TEXT("+%d g"), P) : (Full > 0.f ? FString::Printf(TEXT("%.0f/%.0f"), Left, Full) : FString());
		L.Detail = FString::Printf(TEXT("A weapon you found%s"), I == Pc->GetWeaponIndex() ? TEXT(", in your hands now") : TEXT(""));
		Out.Add(L);
	}
	for (const FRDItemDef& It : G->Items)
	{
		const int32 N = Pc->GetItemCount(It.Name);
		if (N <= 0 || It.Kind == ERDItemKind::Teleport || It.Kind == ERDItemKind::Key) continue;
		// (what she wears is not sold or stored while she wears it: the copies beyond it are)
		int32 Free = N;
		if (Pc->GetWornArmour() == It.Name || Pc->GetWornShield() == It.Name) --Free;
		for (int32 K = 0; K < 8; ++K) if (Pc->GetWornRing((ERDRingKind)K) == It.Name) --Free;
		if (Free <= 0) continue;
		const int32 P = bPrices ? FMath::Max(1, FMath::RoundToInt(G->PriceOf(It.Name) * G->SellShare)) : 0;
		if (bPrices && G->PriceOf(It.Name) <= 0) continue;
		ARDDungeonGenerator::FTownLine L; L.Act = Act; L.Arg = FString::Printf(TEXT("i:%s"), *It.Name.ToString());
		L.Label = Free > 1 ? FString::Printf(TEXT("%s  x %d"), *It.Name.ToString(), Free) : It.Name.ToString();
		L.Tag = bPrices ? FString::Printf(TEXT("+%d g"), P) : FString();
		L.Detail = It.Looks.IsEmpty() ? FString::Printf(TEXT("You carry %d"), N) : It.Looks;
		Out.Add(L);
	}
}

void ARDDungeonGenerator::BuildTownLines()
{
	TownLines.Reset();
	URDGameInstance* GI = URDGameInstance::Of(this);
	const int32 Gold = GetGold();
	auto Add = [&](FName Act, const FString& Label, const FString& Tag, const FString& Detail, bool bOn = true, const FString& Arg = FString())
	{
		FTownLine L; L.Act = Act; L.Label = Label; L.Tag = Tag; L.Detail = Detail; L.bOn = bOn; L.Arg = Arg;
		TownLines.Add(L);
	};
	const ARDTownsfolk* Who = TownPeople.IsValidIndex(TownWho) ? TownPeople[TownWho].Get() : nullptr;
	const FRDTownsfolkDef* Def = Who && Townsfolk.IsValidIndex(Who->Def) ? &Townsfolk[Who->Def] : nullptr;
	TownTitle = Who ? Who->Title : FString(); TownSub = Who ? Who->Calling : FString();
	const int32 T = GetGameTier();
	// (each town its own quests (Vel Morrath's archbishop's, 2026-11-06): a giver offers those of the town it stands in)
	const FString HereQ = bTownHome ? FString() : TownName;
	auto QuestLinesOf = [&](const FName Giver)
	{
		int32 Shown = 0;
		for (const FRDQuestDef& Q : Quests)
		{
			if (Q.Giver != Giver || Q.Town != HereQ) continue;
			const int32 P = QuestProgress(Q);
			const FString St = RDQuestStateOf(GI, Q, P, bWild && IsWildReady());
			const FRDQuestState* Before = Q.After.IsNone() ? nullptr : (GI ? GI->FindQuest(Q.After) : nullptr);
			const bool bOpen = Q.After.IsNone() || (Before && Before->State == 2);
			if (!bOpen || St == TEXT("done")) continue;
			// (the board posts three bounties at a time)
			if (Giver == TEXT("Board") && St == TEXT("offered") && ++Shown > 3) continue;
			const FString Arg = Q.Id.ToString();
			if (St == TEXT("later")) Add(TEXT("later"), Q.Title, TEXT("LATER"), Q.Offer + TEXT("\n\n(The wilderness beyond the gate is not open yet: this quest waits for it.)"), false, Arg);
			else if (St == TEXT("offered")) Add(TEXT("accept"), FString::Printf(TEXT("Quest: %s"), *Q.Title), Q.Gold > 0 ? FString::Printf(TEXT("%d g"), Q.Gold) : TEXT("NEW"), Q.Offer, true, Arg);
			else if (St == TEXT("ready")) Add(TEXT("turnin"), FString::Printf(TEXT("Done: %s"), *Q.Title), TEXT("REWARD"), Q.Done, true, Arg);
			else Add(TEXT("status"), Q.Title, FString::Printf(TEXT("%d / %d"), FMath::Min(P, Q.Count), Q.Count), Q.Hint, true, Arg);
		}
	};
	if (TownPanel == TEXT("talk") && Def)
	{
		if (TownBody.IsEmpty() && Def->Lines.Num() > 0) TownBody = Def->Lines[0];
		for (int32 I = 0; I < Def->Topics.Num(); ++I)
		{
			FString Q, A;
			if (!Def->Topics[I].Split(TEXT("|"), &Q, &A)) continue;
			Add(TEXT("ask"), Q, FString(), A, true, FString::FromInt(I));
		}
		QuestLinesOf(FName(*RDTRoleName(Who->TownRole)));
		Add(TEXT("bye"), TEXT("Farewell"), FString(), FString());
	}
	else if (TownPanel == TEXT("board"))
	{
		TownTitle = TEXT("The quest board"); TownSub = TEXT("bounties posted by the townsfolk and the watch");
		if (TownBody.IsEmpty()) TownBody = TEXT("Notes pinned over notes, some fresh, some faded. A few still ask for help, and one promises coin.");
		// (Brokenspire's bounties are Brokenspire's: a small town's board has only old notices)
		if (bTownHome || Quests.ContainsByPredicate([&](const FRDQuestDef& Q) { return Q.Giver == TEXT("Board") && Q.Town == HereQ; })) QuestLinesOf(TEXT("Board"));
		else Add(TEXT("none"), TEXT("Only faded notices"), FString(), TEXT("Lost cats, a cart for sale, a wedding long past. Nothing asks for your sword here."), false);
		Add(TEXT("bye"), TEXT("Step away"), FString(), FString());
	}
	else if (TownPanel == TEXT("store"))
	{
		TownTitle = TEXT("The trader's store"); TownSub = FString::Printf(TEXT("buy and sell  ·  you have %d gold"), Gold);
		if (TownTab == 0)
			for (const FName& It : TownStock())
			{
				const int32 Ix = FindItem(It); const int32 P = PriceOf(It);
				Add(TEXT("buy"), It.ToString(), FString::Printf(TEXT("%d g"), P), Ix >= 0 && !Items[Ix].Looks.IsEmpty() ? Items[Ix].Looks : FString::Printf(TEXT("You carry %d"), PlayerCombat ? PlayerCombat->GetItemCount(It) : 0), Gold >= P, It.ToString());
			}
		else if (PlayerCombat) RDTownThingLines(this, PlayerCombat, TownLines, TEXT("sell"), true);
		Add(TEXT("bye"), TEXT("Leave"), FString(), FString());
	}
	else if (TownPanel == TEXT("healer"))
	{
		TownTitle = TEXT("The healer's house"); TownSub = FString::Printf(TEXT("you have %d gold"), Gold);
		if (TownBody.IsEmpty()) TownBody = TEXT("Clean linen, bitter herbs, a basin of clear water. The healer looks as if she has not slept in days.");
		const int32 Cost = TownHealCost();
		Add(TEXT("heal"), TEXT("Be healed and cured"), Cost > 0 ? FString::Printf(TEXT("%d g"), Cost) : TEXT("FREE"),
			TEXT("All your hit points and mana back; poison, weakness and slowness taken away."), Gold >= Cost);
		for (const FName& It : TownStock())
		{
			const int32 Ix = FindItem(It);
			if (Ix < 0 || (Items[Ix].Kind != ERDItemKind::Healing && Items[Ix].Kind != ERDItemKind::Mana)) continue;
			Add(TEXT("buy"), It.ToString(), FString::Printf(TEXT("%d g"), PriceOf(It)), FString::Printf(TEXT("You carry %d"), PlayerCombat ? PlayerCombat->GetItemCount(It) : 0), Gold >= PriceOf(It), It.ToString());
		}
		Add(TEXT("bye"), TEXT("Leave"), FString(), FString());
	}
	else if (TownPanel == TEXT("smith"))
	{
		TownTitle = TEXT("The smithy"); TownSub = FString::Printf(TEXT("repairs and the anvil  ·  you have %d gold"), Gold);
		if (TownBody.IsEmpty()) TownBody = TEXT("The forge breathes. \"Bring it here. Whatever the castle did to it, I've seen worse.\"");
		int32 All = 0;
		TArray<FTownLine> Each;
		if (PlayerCombat)
		{
			for (int32 I = 0; I < Weapons.Num(); ++I)
			{
				if (Weapons[I].Item.IsNone() || Weapons[I].bScroll) continue;
				const float Full = PlayerCombat->GetWeaponDurability(I), Left = PlayerCombat->GetWeaponWear(I);
				if (Full <= 0.f || Left >= Full - 0.01f) continue;
				const FString Ref = FString::Printf(TEXT("w:%d"), I);
				const int32 C = RepairCost(Ref); All += C;
				FTownLine L; L.Act = TEXT("repair"); L.Arg = Ref; L.Label = FString::Printf(TEXT("Mend %s"), *Weapons[I].Item.ToString()); L.Tag = FString::Printf(TEXT("%d g"), C);
				L.Detail = FString::Printf(TEXT("%.0f of %.0f left"), Left, Full); L.bOn = Gold >= C; Each.Add(L);
			}
			for (const FRDItemDef& It : Items)
			{
				if ((It.Kind != ERDItemKind::Armour && It.Kind != ERDItemKind::Shield) || PlayerCombat->GetItemCount(It.Name) <= 0 || It.Durability <= 0.f) continue;
				const float Left = PlayerCombat->GetArmourWear(It.Name);
				if (Left >= It.Durability - 0.01f) continue;
				const FString Ref = FString::Printf(TEXT("a:%s"), *It.Name.ToString());
				const int32 C = RepairCost(Ref); All += C;
				FTownLine L; L.Act = TEXT("repair"); L.Arg = Ref; L.Label = FString::Printf(TEXT("Mend %s"), *It.Name.ToString()); L.Tag = FString::Printf(TEXT("%d g"), C);
				L.Detail = FString::Printf(TEXT("%.0f of %.0f left"), Left, It.Durability); L.bOn = Gold >= C; Each.Add(L);
			}
		}
		if (Each.Num() > 1) Add(TEXT("repair"), TEXT("Mend everything"), FString::Printf(TEXT("%d g"), All), TEXT("Every found weapon, set of armour and shield back to full"), Gold >= All, TEXT("all"));
		TownLines.Append(Each);
		if (Each.Num() == 0) Add(TEXT("none"), TEXT("Nothing of yours needs mending"), FString(), FString(), false);
		Add(TEXT("anvil"), TEXT("Use the anvil"), FString(), TEXT("Make repair items from materials, break down what you found"), Recipes.Num() > 0);
		Add(TEXT("bye"), TEXT("Leave"), FString(), FString());
	}
	else if (TownPanel == TEXT("temple"))
	{
		TownTitle = TEXT("The temple"); TownSub = FString::Printf(TEXT("you have %d gold"), Gold);
		if (TownBody.IsEmpty()) TownBody = TEXT("Candles gutter before an altar of grey stone. The priest's voice is low: \"The light still listens, here.\"");
		const int32 Cost = FMath::RoundToInt(20.f * RDTierPrice(T));
		Add(TEXT("bless"), TEXT("Ask for a blessing"), FString::Printf(TEXT("%d g"), Cost), TEXT("For ten minutes: your blows 10% stronger, 10% less of each blow reaches you. It goes with you into the castle."), Gold >= Cost);
		Add(TEXT("donate"), TEXT("Give an offering"), TEXT("5 g"), TEXT("For the refugees' bread"), Gold >= 5);
		Add(TEXT("bye"), TEXT("Leave"), FString(), FString());
	}
	else if (TownPanel == TEXT("stable"))
	{
		// (the eighth phase: a horse to buy, hers called)
		TownTitle = TEXT("The stable"); TownSub = FString::Printf(TEXT("you have %d gold"), Gold);
		if (TownBody.IsEmpty()) TownBody = TEXT("A grey stands in the straw, saddled and patient. The stable boy pats its neck: \"Fast as the wind on the open road.\"");
		const int32 Cost = HorsePriceNow();
		const URDGameInstance* HGI = URDGameInstance::Of(this);
		const bool bTamedOnly = HGI && HGI->bTamedOnly;
		if (!HasHorse() || bTamedOnly) Add(TEXT("buyhorse"), TEXT("Buy the horse"), FString::Printf(TEXT("%d g"), Cost), FString::Printf(TEXT("Yours for good: ridden, you go %.1f times as fast across the wilds (F beside it to ride, F again to get off; no blows from the saddle)"), HorseDef.SpeedMul), Gold >= Cost);
		if (HasHorse()) Add(TEXT("callhorse"), TEXT("Call your horse"), FString(), TEXT("It comes to your side"));
		// (the list of 2026-11-12: a bought bay and a tamed grey, one out at a time)
		if (HasHorse() && HGI && HGI->HorsesTamed > 0 && !bTamedOnly)
			Add(TEXT("swaphorse"), HGI->bRideTamed ? TEXT("Saddle your bay") : TEXT("Saddle your tamed grey"), FString(), TEXT("The other waits here in the stable"));
		Add(TEXT("bye"), TEXT("Leave"), FString(), FString());
	}
	else if (TownPanel == TEXT("stash"))
	{
		TownTitle = TEXT("Your storage"); TownSub = TEXT("the storehouse keeps what you leave here, as long as the game lasts");
		if (TownTab == 0) { if (PlayerCombat) RDTownThingLines(this, PlayerCombat, TownLines, TEXT("deposit"), false); }
		else if (GI)
		{
			// (the list of 2026-11-08b, docs/improvements9.txt: "in the take one back menu item, multiple of the same items need to
			// stack": one line a kind with how many, as the carried list has; a thing that wears (a weapon, a set of armour) stacks
			// only with its like at the same wear. The line takes back the last of them: the others keep their places)
			TArray<FString> Keys; TArray<int32> LastAt, Count;
			for (int32 I = 0; I < GI->StashThings.Num(); ++I)
			{
				const FString K = StashKey(I);
				const int32 At = Keys.Find(K);
				if (At == INDEX_NONE) { Keys.Add(K); LastAt.Add(I); Count.Add(1); }
				else { LastAt[At] = I; ++Count[At]; }
			}
			for (int32 Q = 0; Q < Keys.Num(); ++Q)
			{
				const int32 I = LastAt[Q];
				const float Wr = GI->StashWear.IsValidIndex(I) ? GI->StashWear[I] : -1.f;
				const FString Nm = GI->StashThings[I].ToString();
				Add(TEXT("withdraw"), Count[Q] > 1 ? FString::Printf(TEXT("%s  x %d"), *Nm, Count[Q]) : Nm, Wr >= 0.f ? FString::Printf(TEXT("%.0f"), Wr) : FString(),
					Count[Q] > 1 ? FString::Printf(TEXT("In your storage: %d"), Count[Q]) : TEXT("In your storage"), true, FString::FromInt(I));
			}
		}
		if (TownLines.Num() == 0) Add(TEXT("none"), TownTab == 0 ? TEXT("You carry nothing to store") : TEXT("Your storage is empty"), FString(), FString(), false);
		Add(TEXT("bye"), TEXT("Leave"), FString(), FString());
	}
	else if (TownPanel == TEXT("circle"))
	{
		TownTitle = TEXT("The teleport circle"); TownSub = TEXT("the stones know the circles you have found");
		if (TownBody.IsEmpty()) TownBody = TEXT("The runes wake under your hand. Any circle you find beyond the walls will answer this one, and this one will take you there.");
		// (the wilderness: each town she has found has its circle; this one is the town she is in)
		const FName Here_(*TownName);
		if (GI) for (const FName& C : GI->CirclesFound) Add(C == Here_ ? FName(TEXT("here")) : FName(TEXT("travel")), C.ToString(), C == Here_ ? TEXT("YOU ARE HERE") : TEXT("TRAVEL"),
			C == Here_ ? TEXT("This circle") : TEXT("Step through"), C != Here_, C.ToString());
		// (Mistward Castle: once the Mistward Hall's guards are all dead, or she has walked through the Mistgate once, the circle
		// takes her there (the user's of 2026-11-02: she had cleared the hall and the circle had no way to the dungeon))
		const bool bHallClear = TownGuardsPlanned > 0 && GetTownGuards().Num() == 0;
		const bool bBeenIn = GI && GI->GetCounter(TEXT("enter")) > 0;
		Add(TEXT("castle"), TEXT("Mistward Castle"), bHallClear || bBeenIn ? TEXT("TRAVEL") : TEXT("SEALED"),
			bHallClear || bBeenIn ? TEXT("The runes answer the Mistgate: step through into the castle's great hall.") : TEXT("The Mistward Hall's guards still hold the Mistgate: clear the hall, or walk through it once."),
			bHallClear || bBeenIn, TEXT("castle"));
		if (!bWild) Add(TEXT("none"), TEXT("No other circle found yet"), TEXT("LATER"), TEXT("They lie in the wilderness beyond the gate, which is not open yet."), false);
		else if (!GI || GI->CirclesFound.Num() < 2) Add(TEXT("none"), TEXT("No other circle found yet"), TEXT("FIND"), TEXT("Every town of the wilds has one: find a town, and its circle answers this one."), false);
		Add(TEXT("bye"), TEXT("Step away"), FString(), FString());
	}
	TownCursor = FMath::Clamp(TownCursor, 0, FMath::Max(0, TownLines.Num() - 1));
}

bool ARDDungeonGenerator::ActivateTownEntry(int32 Line)
{
	const int32 L = Line >= 0 ? Line : TownCursor;
	if (!TownLines.IsValidIndex(L)) return false;
	TownCursor = L;
	const FTownLine E = TownLines[L];
	bool bOk = false;
	if (E.Act == TEXT("bye")) { CloseTownPanel(); return true; }
	if (!E.bOn && E.Act != TEXT("ask")) { SetTownNote(E.Act == TEXT("buy") || E.Act == TEXT("heal") || E.Act == TEXT("bless") || E.Act == TEXT("repair") || E.Act == TEXT("buyhorse") ? TEXT("You have too little gold") : E.Detail); return false; }
	if (E.Act == TEXT("ask")) { TownBody = E.Detail; TownCount(TEXT("asked")); bOk = true; }
	else if (E.Act == TEXT("accept") || E.Act == TEXT("turnin")) bOk = TownQuestAction(E.Act, FName(*E.Arg));
	else if (E.Act == TEXT("status")) { TownBody = E.Detail; bOk = true; }
	else if (E.Act == TEXT("buy")) bOk = TownBuy(FName(*E.Arg));
	else if (E.Act == TEXT("sell")) bOk = TownSell(E.Arg);
	else if (E.Act == TEXT("heal")) bOk = TownHeal();
	else if (E.Act == TEXT("repair")) bOk = TownRepair(E.Arg);
	else if (E.Act == TEXT("anvil")) { CloseTownPanel(); if (PlayerCombat) PlayerCombat->SetCraftingOpen(true); return true; }
	else if (E.Act == TEXT("castle")) { CloseTownPanel(); TownCount(TEXT("circle_castle")); return EnterCastle(); }
	else if (E.Act == TEXT("travel") && bWild && IsWildReady())
	{
		// (a town's circle to another town's: fast travel, as from the map)
		const int32 Ti = Wild->Towns.IndexOfByPredicate([&E](const FRDWildTown& T) { return T.Name == E.Arg; });
		if (Ti < 0) return false;
		CloseTownPanel(); TownCount(TEXT("circle_travel"));
		return WildFastTravel(FRDWildWorld::TownIdBase + Ti);
	}
	else if (E.Act == TEXT("bless")) bOk = TownBless();
	else if (E.Act == TEXT("buyhorse")) { bOk = BuyHorse(); if (bOk) CloseTownPanel(); }
	else if (E.Act == TEXT("swaphorse")) { bOk = SwapHorse(); if (bOk) CloseTownPanel(); }
	else if (E.Act == TEXT("callhorse")) { bOk = CallHorse(); if (bOk) { SetTownNote(TEXT("Your horse comes")); CloseTownPanel(); } }
	else if (E.Act == TEXT("donate")) { AddGold(-5, TEXT("an offering")); TownCount(TEXT("offerings")); SetTownNote(TEXT("The priest bows his head: \"They will eat tonight.\"")); bOk = true; }
	else if (E.Act == TEXT("deposit")) bOk = TownDeposit(E.Arg);
	else if (E.Act == TEXT("withdraw")) bOk = TownWithdraw(FCString::Atoi(*E.Arg));
	if (IsTownPanelOpen()) BuildTownLines();
	return bOk;
}

// ================================================================================================ the services
bool ARDDungeonGenerator::TownBuy(FName Item)
{
	const int32 P = PriceOf(Item);
	if (!PlayerCombat || P <= 0 || GetGold() < P) { SetTownNote(TEXT("You have too little gold")); return false; }
	AddGold(-P, FString::Printf(TEXT("bought %s"), *Item.ToString()));
	PlayerCombat->AddItem(Item, 1);
	TownCount(TEXT("bought"));
	SetTownNote(FString::Printf(TEXT("You buy %s for %d gold"), *Item.ToString(), P));
	PlaySoundAt(TEXT("Player.Loot"), PlayerCombat->GetOwner()->GetActorLocation());
	return true;
}

bool ARDDungeonGenerator::TownSell(const FString& Ref)
{
	if (!PlayerCombat) return false;
	FName Item; float Wl = -1.f; int32 P = 0;
	if (Ref.StartsWith(TEXT("w:")))
	{
		const int32 I = FCString::Atoi(*Ref.Mid(2));
		if (!Weapons.IsValidIndex(I)) return false;
		Item = Weapons[I].Item;
		const float Full = PlayerCombat->GetWeaponDurability(I), Left = PlayerCombat->GetWeaponWear(I);
		P = FMath::Max(1, FMath::RoundToInt(PriceOf(Item) * SellShare * (Full > 0.f ? FMath::Clamp(Left / Full, 0.2f, 1.f) : 1.f)));
		if (!PlayerCombat->RemoveFoundWeapon(I, Wl)) return false;
	}
	else
	{
		Item = FName(*Ref.Mid(2));
		if (PlayerCombat->GetItemCount(Item) <= 0 || PriceOf(Item) <= 0) return false;
		P = FMath::Max(1, FMath::RoundToInt(PriceOf(Item) * SellShare));
		PlayerCombat->RemoveItem(Item, 1);
	}
	AddGold(P, FString::Printf(TEXT("sold %s"), *Item.ToString()));
	TownCount(TEXT("sold"));
	SetTownNote(FString::Printf(TEXT("You sell %s for %d gold"), *Item.ToString(), P));
	return true;
}

int32 ARDDungeonGenerator::TownHealCost() const
{
	// (all she gets back is priced: hit points, mana and an affliction cured (the PR review's find: a Mage with no mana, or a
	// poisoned hero with her hit points full, was healed for free); 0 only when there is nothing to do)
	if (!PlayerCombat) return 0;
	const float Miss = FMath::Max(0.f, PlayerCombat->GetMaxHealth() - PlayerCombat->GetHealth());
	const float ManaMiss = FMath::Max(0.f, PlayerCombat->GetMaxMana() - PlayerCombat->GetMana());
	const bool bCure = PlayerCombat->IsAfflicted();
	// (her hit points and mana grow past tier 5 (TierGrowthHealth a tier): a point is priced down by that, or a whole heal would
	// cost the price's growth times hers)
	const int32 Gt = GetGameTier();
	const float K = RDTierPrice(Gt) / FMath::Pow(FMath::Max(TierGrowthHealth, 1.f), (float)FMath::Max(Gt - 5, 0));
	const int32 C = FMath::RoundToInt((Miss * 0.25f + ManaMiss * 0.1f) * K + (bCure ? 5.f : 0.f) * RDTierPrice(Gt));
	return Miss > 0.5f || ManaMiss > 0.5f || bCure ? FMath::Max(2, C) : 0;
}

bool ARDDungeonGenerator::TownHeal()
{
	if (!PlayerCombat) return false;
	const int32 Cost = TownHealCost();
	if (GetGold() < Cost) { SetTownNote(TEXT("You have too little gold")); return false; }
	if (Cost > 0) AddGold(-Cost, TEXT("the healer"));
	PlayerCombat->SetHealth(PlayerCombat->GetMaxHealth()); PlayerCombat->SetMana(PlayerCombat->GetMaxMana());
	PlayerCombat->ClearAfflictions();
	TownCount(TEXT("healed"));
	SetTownNote(Cost > 0 ? FString::Printf(TEXT("You are healed (%d gold)"), Cost) : FString(TEXT("You are well already: the healer only checks your bandages")));
	return true;
}

int32 ARDDungeonGenerator::RepairCost(const FString& Ref) const
{
	if (!PlayerCombat) return 0;
	if (Ref == TEXT("all"))
	{
		int32 C = 0;
		for (int32 I = 0; I < Weapons.Num(); ++I) if (!Weapons[I].Item.IsNone() && !Weapons[I].bScroll) C += RepairCost(FString::Printf(TEXT("w:%d"), I));
		for (const FRDItemDef& It : Items) if ((It.Kind == ERDItemKind::Armour || It.Kind == ERDItemKind::Shield) && PlayerCombat->GetItemCount(It.Name) > 0) C += RepairCost(FString::Printf(TEXT("a:%s"), *It.Name.ToString()));
		return C;
	}
	float Miss = 0.f, Full = 0.f; FName Item;
	if (Ref.StartsWith(TEXT("w:")))
	{
		const int32 I = FCString::Atoi(*Ref.Mid(2));
		if (!Weapons.IsValidIndex(I)) return 0;
		Item = Weapons[I].Item; Full = PlayerCombat->GetWeaponDurability(I); Miss = Full - PlayerCombat->GetWeaponWear(I);
	}
	else
	{
		Item = FName(*Ref.Mid(2));
		const int32 Ix = FindItem(Item);
		if (Ix < 0) return 0;
		Full = Items[Ix].Durability; Miss = Full - PlayerCombat->GetArmourWear(Item);
	}
	if (Full <= 0.f || Miss <= 0.01f) return 0;
	return FMath::Max(1, FMath::CeilToInt(Miss / Full * PriceOf(Item) * 0.3f));
}

bool ARDDungeonGenerator::TownRepair(const FString& Ref)
{
	if (!PlayerCombat) return false;
	const int32 C = RepairCost(Ref);
	if (C <= 0) { SetTownNote(TEXT("It needs no mending")); return false; }
	if (GetGold() < C) { SetTownNote(TEXT("You have too little gold")); return false; }
	auto Mend = [&](const FString& R)
	{
		if (R.StartsWith(TEXT("w:"))) { const int32 I = FCString::Atoi(*R.Mid(2)); PlayerCombat->SetWeaponWear(I, PlayerCombat->GetWeaponDurability(I)); }
		else { const FName N(*R.Mid(2)); const int32 Ix = FindItem(N); if (Ix >= 0) PlayerCombat->SetArmourWear(N, Items[Ix].Durability); }
	};
	if (Ref == TEXT("all"))
	{
		for (int32 I = 0; I < Weapons.Num(); ++I) if (!Weapons[I].Item.IsNone() && !Weapons[I].bScroll) Mend(FString::Printf(TEXT("w:%d"), I));
		for (const FRDItemDef& It : Items) if ((It.Kind == ERDItemKind::Armour || It.Kind == ERDItemKind::Shield) && PlayerCombat->GetItemCount(It.Name) > 0) Mend(FString::Printf(TEXT("a:%s"), *It.Name.ToString()));
	}
	else Mend(Ref);
	AddGold(-C, TEXT("the smith"));
	TownCount(TEXT("repaired"));
	PlaySoundAt(TEXT("Player.Hit.Sword"), PlayerCombat->GetOwner()->GetActorLocation(), 0.6f);
	SetTownNote(FString::Printf(TEXT("Mended for %d gold"), C));
	return true;
}

bool ARDDungeonGenerator::TownBless()
{
	if (!PlayerCombat) return false;
	const int32 Cost = FMath::RoundToInt(20.f * RDTierPrice(GetGameTier()));
	if (GetGold() < Cost) { SetTownNote(TEXT("You have too little gold")); return false; }
	AddGold(-Cost, TEXT("the temple"));
	PlayerCombat->Bless(TEXT("Blessing of the Spire"), 0.10f, 0.10f, 0.f, 600.f);
	TownCount(TEXT("blessed"));
	SetTownNote(TEXT("The Blessing of the Spire is on you (10 minutes)"));
	return true;
}

bool ARDDungeonGenerator::TownDeposit(const FString& Ref)
{
	URDGameInstance* GI = URDGameInstance::Of(this);
	if (!GI || !PlayerCombat) return false;
	FName Item; float Wl = -1.f;
	if (Ref.StartsWith(TEXT("w:")))
	{
		const int32 I = FCString::Atoi(*Ref.Mid(2));
		if (!Weapons.IsValidIndex(I)) return false;
		Item = Weapons[I].Item;
		if (!PlayerCombat->RemoveFoundWeapon(I, Wl)) return false;
	}
	else
	{
		Item = FName(*Ref.Mid(2));
		if (PlayerCombat->GetItemCount(Item) <= 0) return false;
		const int32 Ix = FindItem(Item);
		if (Ix >= 0 && (Items[Ix].Kind == ERDItemKind::Armour || Items[Ix].Kind == ERDItemKind::Shield)) Wl = PlayerCombat->GetArmourWear(Item);
		PlayerCombat->RemoveItem(Item, 1);
	}
	GI->StashThings.Add(Item); GI->StashWear.Add(Wl);
	TownCount(TEXT("stored"));
	SetTownNote(FString::Printf(TEXT("%s is in your storage"), *Item.ToString()));
	return true;
}

bool ARDDungeonGenerator::TownWithdraw(int32 Index)
{
	URDGameInstance* GI = URDGameInstance::Of(this);
	if (!GI || !PlayerCombat || !GI->StashThings.IsValidIndex(Index)) return false;
	const FName Item = GI->StashThings[Index];
	const float Wl = GI->StashWear.IsValidIndex(Index) ? GI->StashWear[Index] : -1.f;
	GI->StashThings.RemoveAt(Index); if (GI->StashWear.IsValidIndex(Index)) GI->StashWear.RemoveAt(Index);
	PlayerCombat->TakeBack({ Item }, { Wl }, false);
	SetTownNote(FString::Printf(TEXT("You take %s from your storage"), *Item.ToString()));
	return true;
}

FString ARDDungeonGenerator::TownLineThing(int32 Line) const
{
	if (!TownLines.IsValidIndex(Line)) return FString();
	const FTownLine& L = TownLines[Line];
	if (L.Act == TEXT("deposit")) return L.Arg.StartsWith(TEXT("i:")) ? L.Arg : FString();
	if (L.Act != TEXT("withdraw")) return FString();
	return StashKey(FCString::Atoi(*L.Arg));
}

FString ARDDungeonGenerator::StashKey(int32 I) const
{
	const URDGameInstance* GI = URDGameInstance::Of(this);
	if (!GI || !GI->StashThings.IsValidIndex(I)) return FString();
	const float Wr = GI->StashWear.IsValidIndex(I) ? GI->StashWear[I] : -1.f;
	return GI->StashThings[I].ToString() + (Wr >= 0.f ? FString::Printf(TEXT("|%.0f"), Wr) : FString());
}

// ================================================================================================ the panel's keys and pointer
void ARDDungeonGenerator::TickTownPanel(APlayerController* PC)
{
	if (!PC || !IsTownPanelOpen()) return;
	auto Pressed = [PC](std::initializer_list<FKey> Keys) { for (const FKey& K : Keys) if (PC->WasInputKeyJustPressed(K)) return true; return false; };
	if (Pressed({ EKeys::Escape, EKeys::BackSpace, EKeys::F, EKeys::Tab, EKeys::Gamepad_FaceButton_Right })) { CloseTownPanel(); return; }
	if (Pressed({ EKeys::W, EKeys::Up, EKeys::Gamepad_DPad_Up })) MoveTownCursor(-1);
	if (Pressed({ EKeys::S, EKeys::Down, EKeys::Gamepad_DPad_Down })) MoveTownCursor(1);
	// (held down, the cursor goes on after a moment, a step every 80 ms, as the inventory's does (the user's of 2026-11-07:
	// the storage could not be scrolled by holding the D-pad); the left stick the same. Armed only by a press made while the
	// panel is open, so a key held from before does not run it. Real time: a panel may pause the game)
	{
		auto Down = [PC](std::initializer_list<FKey> Keys) { for (const FKey& K : Keys) if (PC->IsInputKeyDown(K)) return true; return false; };
		const float Sy = PC->GetInputAnalogKeyState(EKeys::Gamepad_LeftY);
		const int32 Dir = (Down({ EKeys::W, EKeys::Up, EKeys::Gamepad_DPad_Up }) || Sy > 0.6f) ? -1 : (Down({ EKeys::S, EKeys::Down, EKeys::Gamepad_DPad_Down }) || Sy < -0.6f) ? 1 : 0;
		const bool bJust = Dir < 0 ? Pressed({ EKeys::W, EKeys::Up, EKeys::Gamepad_DPad_Up }) : Dir > 0 ? Pressed({ EKeys::S, EKeys::Down, EKeys::Gamepad_DPad_Down }) : false;
		const bool bStick = FMath::Abs(Sy) > 0.6f;
		const double Now = FPlatformTime::Seconds();
		if (Dir == 0) TownRepeatDir = 0;
		else if (bJust) { TownRepeatDir = Dir; TownRepeatAt = Now + 0.35; }
		else if (bStick && TownRepeatDir == 0) { MoveTownCursor(Dir); TownRepeatDir = Dir; TownRepeatAt = Now + 0.4; }
		else if (Dir == TownRepeatDir && Now >= TownRepeatAt) { MoveTownCursor(Dir); TownRepeatAt = Now + (bStick ? 0.15 : 0.08); }
	}
	if (Pressed({ EKeys::A, EKeys::Left, EKeys::Gamepad_DPad_Left, EKeys::Gamepad_LeftShoulder })) SetTownTab(0);
	if (Pressed({ EKeys::D, EKeys::Right, EKeys::Gamepad_DPad_Right, EKeys::Gamepad_RightShoulder })) SetTownTab(1);
	// (the list of 2026-11-08b: "in the storage, in the store a thing menu, when the button is held down to store something, it
	// should continue to store something until the button is let go": held after a moment (0.4 s), the same thing is stored
	// again every 0.15 s while she has it (taking back the same), then it stops; a found weapon is one thing and stops at once)
	auto UseHeld = [PC]() { for (const FKey& K : { EKeys::Enter, EKeys::SpaceBar, EKeys::E, EKeys::Gamepad_FaceButton_Bottom, EKeys::LeftMouseButton }) if (PC->IsInputKeyDown(K)) return true; return false; };
	auto Use = [this](int32 Line)
	{
		const int32 L = Line >= 0 ? Line : TownCursor;
		const bool bStore = TownPanel == TEXT("stash") && TownLines.IsValidIndex(L) && (TownLines[L].Act == TEXT("deposit") || TownLines[L].Act == TEXT("withdraw"));
		TownHoldAct = bStore ? TownLines[L].Act : NAME_None; TownHoldThing = bStore ? TownLineThing(L) : FString();
		TownHoldAt = FPlatformTime::Seconds() + 0.4;
		ActivateTownEntry(Line);
	};
	if (!TownHoldThing.IsEmpty())
	{
		if (!UseHeld()) { TownHoldThing.Reset(); TownHoldAct = NAME_None; }
		else if (FPlatformTime::Seconds() >= TownHoldAt)
		{
			int32 Again = INDEX_NONE;
			for (int32 I = 0; I < TownLines.Num() && Again == INDEX_NONE; ++I) if (TownLines[I].Act == TownHoldAct && TownLineThing(I) == TownHoldThing) Again = I;
			if (Again == INDEX_NONE) { TownHoldThing.Reset(); TownHoldAct = NAME_None; }
			else { TownCursor = Again; ActivateTownEntry(Again); ++TownHoldUses; TownHoldAt = FPlatformTime::Seconds() + 0.15; }
		}
	}
	if (Pressed({ EKeys::Enter, EKeys::SpaceBar, EKeys::E, EKeys::Gamepad_FaceButton_Bottom })) { Use(-1); return; }
	if (PC->WasInputKeyJustPressed(EKeys::MouseScrollUp)) MoveTownCursor(-1);
	if (PC->WasInputKeyJustPressed(EKeys::MouseScrollDown)) MoveTownCursor(1);
	float Mx = 0.f, My = 0.f;
	if (!PC->GetMousePosition(Mx, My)) return;
	const FVector2D M(Mx, My);
	float Dx = 0.f, Dy = 0.f; PC->GetInputMouseDelta(Dx, Dy);
	const bool bClick = PC->WasInputKeyJustPressed(EKeys::LeftMouseButton);
	for (int32 I = 0; I < TownTabBoxes.Num(); ++I) if (bClick && TownTabBoxes[I].IsInside(M)) { SetTownTab(I); return; }
	for (int32 I = 0; I < TownRowBoxes.Num() && I < TownLines.Num(); ++I)
	{
		if (!TownRowBoxes[I].IsInside(M)) continue;
		if (Dx != 0.f || Dy != 0.f || bClick) TownCursor = I;
		if (bClick) { Use(I); return; }
	}
}

// ================================================================================================ tests
TArray<FString> ARDDungeonGenerator::GetTownBuildingLines() const
{
	TArray<FString> Out;
	const ARDSection* S = GetSection(FIntPoint::ZeroValue);
	if (!S) return Out;
	for (int32 I = 0; I < S->TownBlds.Num(); ++I)
	{
		const ARDSection::FTownBld& B = S->TownBlds[I];
		const FVector C = (S->LocalToWorld(B.Min) + S->LocalToWorld(B.Max - FIntPoint(1, 1))) * 0.5f;
		const FVector D = S->GetDoorLocation(B.Door);
		Out.Add(FString::Printf(TEXT("%d|%s|%s|%d|%.0f|%.0f|%.0f|%.0f|%d|%d"), I, *RDTownKindName(B.Kind), *B.Label, B.State, C.X, C.Y, D.X, D.Y, B.Rooms.Num(), B.bBoarded ? 1 : 0));
	}
	return Out;
}

TArray<FString> ARDDungeonGenerator::GetTownSpotLines() const
{
	TArray<FString> Out;
	const ARDSection* S = GetSection(FIntPoint::ZeroValue);
	if (!S) return Out;
	for (const ARDSection::FTownSpot& Sp : S->TownSpots) Out.Add(FString::Printf(TEXT("%s|%.0f|%.0f|%.0f|%d"), *RDTownSpotName(Sp.Kind), Sp.At.X, Sp.At.Y, Sp.At.Z, Sp.Bld));
	return Out;
}

TArray<FString> ARDDungeonGenerator::GetTownsfolkLines() const
{
	TArray<FString> Out;
	for (int32 I = 0; I < TownPeople.Num(); ++I)
		if (const ARDTownsfolk* T = TownPeople[I]; IsValid(T))
		{
			const FVector L = T->GetActorLocation();
			Out.Add(FString::Printf(TEXT("%d|%s|%s|%s|%.0f|%.0f|%.0f|%d"), I, *RDTRoleName(T->TownRole), Townsfolk.IsValidIndex(T->Def) ? *Townsfolk[T->Def].Name.ToString() : TEXT("?"), *T->Title, L.X, L.Y, L.Z, T->Walks));
		}
	return Out;
}

bool ARDDungeonGenerator::GetTownPlace(const FString& What, FVector& At) const
{
	const ARDSection* S = GetSection(FIntPoint::ZeroValue);
	if (!S) return false;
	if (What == TEXT("square")) { At = (S->LocalToWorld(S->TownSquare.Min) + S->LocalToWorld(S->TownSquare.Max - FIntPoint(1, 1))) * 0.5f; return true; }
	if (What == TEXT("gate")) { At = S->TownGate; return true; }
	if (What == TEXT("mistgate")) { At = S->MistgateAt; return !At.IsZero(); }
	if (What == TEXT("castle door") && S->TownBlds.IsValidIndex(S->CastleBld))
	{
		const ARDSection::FTownBld& C = S->TownBlds[S->CastleBld];
		At = S->LocalToWorld(C.DoorTile) + FVector(RDTGDir4[C.DoorSide].X, RDTGDir4[C.DoorSide].Y, 0.f) * 450.f; return true;
	}
	for (const ARDSection::FTownSpot& Sp : S->TownSpots) if (RDTownSpotName(Sp.Kind) == What) { At = Sp.At; return true; }
	for (const ARDSection::FTownBld& B : S->TownBlds) if (RDTownKindName(B.Kind) == What) { At = S->LocalToWorld(B.DoorTile); return true; }
	return false;
}

TArray<ARDMonster*> ARDDungeonGenerator::GetTownGuards() const
{
	TArray<ARDMonster*> Out;
	for (ARDMonster* M : TownGuards) if (IsValid(M) && !M->IsDead()) Out.Add(M);
	return Out;
}
