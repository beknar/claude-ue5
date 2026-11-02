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
	Speed = D.WalkSpeed; ClipSpeed = FMath::Max(D.WalkClipSpeed, 10.f);
	bWalkClip = true; SetClip(false);
	Body->SetPosition(R.FRandRange(0.f, 2.f));
	NextTrip = R.FRandRange(2.f, 9.f);
}

void ARDTownsfolk::SetClip(bool bWalk)
{
	if (bWalk == bWalkClip) return;
	bWalkClip = bWalk;
	UAnimationAsset* A = bWalk && WalkAnim ? WalkAnim.Get() : IdleAnim.Get();
	if (A) Body->PlayAnimation(A, true);
	Body->SetPlayRate(bWalk && WalkAnim ? FMath::Clamp(Speed / ClipSpeed, 0.5f, 1.8f) : 1.f);
}

void ARDTownsfolk::FaceToward(const FVector& P, float Seconds)
{
	FaceAt = P; FaceUntil = GetWorld()->GetTimeSeconds() + Seconds;
	Path.Reset(); SetClip(false);
}

FString ARDTownsfolk::NextLine()
{
	if (!Gen || !Gen->Townsfolk.IsValidIndex(Def)) return FString();
	const TArray<FString>& L = Gen->Townsfolk[Def].Lines;
	if (L.Num() == 0) return FString();
	const int32 I = LinesSaid == 0 ? 0 : R.RandRange(0, L.Num() - 1);
	++LinesSaid;
	return L[I];
}

void ARDTownsfolk::Tick(float Dt)
{
	Super::Tick(Dt);
	const float Now = GetWorld()->GetTimeSeconds();
	const FVector L = GetActorLocation();
	auto Turn = [&](const FVector& Dir, float Rate)
	{
		if (Dir.IsNearlyZero(1.f)) return;
		SetActorRotation(FRotator(0.f, FMath::RInterpConstantTo(GetActorRotation(), Dir.Rotation(), Dt, Rate).Yaw, 0.f));
	};
	// (she spoke to it: it turns to her and stands)
	if (Now < FaceUntil) { Turn(FaceAt - L, 240.f); SetClip(false); return; }
	if (Path.Num() > 0)
	{
		FVector D = Path[0] - L; D.Z = 0.f;
		if (D.Size() < 40.f) { Path.RemoveAt(0); if (Path.Num() == 0) { SetClip(false); NextTrip = Now + R.FRandRange(4.f, 14.f); } return; }
		// (a closed door on the way: it opens it, as a monster does, and it closes again behind)
		if (Section)
		{
			const FIntPoint Cur = Section->WorldToLocal(L), Ahead = Section->WorldToLocal(L + D.GetSafeNormal() * 160.f);
			if (Ahead != Cur && FMath::Abs(Ahead.X - Cur.X) + FMath::Abs(Ahead.Y - Cur.Y) == 1)
			{
				const int32 Dr = Section->DoorBetween(Cur, Ahead);
				if (Dr >= 0 && !Section->IsDoorOpenIndex(Dr))
				{
					if (!Section->IsTargetOpen(true, Dr) && Section->BoardedDoorBld(Dr) < 0) Section->ToggleDoor(Dr, L, true);
					SetClip(false);
					return;
				}
			}
		}
		const FVector Step = D.GetSafeNormal() * FMath::Min(Speed * Dt, D.Size());
		FHitResult Hit;
		SetActorLocation(L + Step, true, &Hit);
		if (Hit.bBlockingHit) { Path.Reset(); SetClip(false); NextTrip = Now + R.FRandRange(1.f, 3.f); return; }
		Turn(D, 300.f);
		SetClip(true);
		return;
	}
	// standing: back to its own way of facing; now and then a walk within its round
	if (Wander <= 0.f || !Section)
	{
		if (FVector::Dist2D(L, Post) < 60.f) Turn(FRotator(0, HomeYaw, 0).Vector(), 90.f);
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

// ================================================================================================ her combat component
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
	int32 T = 1;
	for (const int32 O : TiersOpened) T = FMath::Max(T, O);
	if (const URDGameInstance* GI = URDGameInstance::Of(this)) for (const int32 O : GI->CastleTiers) T = FMath::Max(T, O);
	return FMath::Clamp(T, 1, 5);
}

static float RDTierPrice(int32 Tier) { static const float K[5] = { 1.f, 2.f, 3.5f, 5.5f, 8.f }; return K[FMath::Clamp(Tier, 1, 5) - 1]; }

int32 ARDDungeonGenerator::PriceOf(FName Item) const
{
	const int32 Ix = FindItem(Item);
	if (Ix < 0) return 0;
	const FRDItemDef& It = Items[Ix];
	int32 T = 1;
	if (It.Tiers.Num() > 0) { T = 99; for (const int32 X : It.Tiers) T = FMath::Min(T, X); }
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
	return FMath::Max(1, FMath::RoundToInt(Base * RDTierPrice(T)));
}

TArray<FName> ARDDungeonGenerator::TownStock() const
{
	// (potions of every kind, food, repair items and the scrolls a hero of hers reads, of the tiers she has opened)
	TArray<FName> Out;
	const int32 T = GetGameTier();
	const FRDHeroDef* H = FindHero(CurrentHero);
	for (const FRDItemDef& It : Items)
	{
		int32 Ti = 1;
		if (It.Tiers.Num() > 0) { Ti = 99; for (const int32 X : It.Tiers) Ti = FMath::Min(Ti, X); }
		if (Ti > T) continue;
		const bool bScroll = It.Kind == ERDItemKind::Scroll;
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
	GI->Carry = C;
	// (the game is hers: a hero switched in play (tests) would otherwise start a new game in the next level, her things lost)
	GI->GameHero = CurrentHero;
	// (what the level keeps for the game: the castle's tiers and its first set's looted containers, the town's looted ones)
	if (!bTown)
	{
		for (const int32 T : TiersOpened) GI->CastleTiers.AddUnique(T);
		for (const FIntVector& K : LootedContainers) if (K.X == 0 && K.Y == 0) GI->CastleStartLooted.AddUnique(K.Z);
	}
	else for (const FIntVector& K : LootedContainers) if (K.X == 0 && K.Y == 0) GI->TownLooted.AddUnique(K.Z);
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
	PlayerCombat->ShowMessage(bTown ? FString::Printf(TEXT("%s"), *TownName) : FString(TEXT("Mistward Castle")));
	UE_LOG(LogRDTownGame, Log, TEXT("RDCARRY restored %s: %d things, %d weapons, armour %s, %.0f hp"), *CurrentHero.ToString(), C.Things.Num(), Weapons.Num(), *PlayerCombat->GetWornArmour().ToString(), PlayerCombat->GetHealth());
	return true;
}

bool ARDDungeonGenerator::EnterCastle()
{
	if (!bTown || CastleLevel.IsEmpty() || bTownTraveling) return false;
	LastTravel = TEXT("castle");
	if (bTravelDryRun) return true;
	SaveCarry();
	if (URDGameInstance* GI = URDGameInstance::Of(this)) GI->Arrive = TEXT("castle");
	bTownTraveling = true;
	UE_LOG(LogRDTownGame, Log, TEXT("RDTRAVEL into %s as %s"), *CastleLevel, *CurrentHero.ToString());
	UGameplayStatics::OpenLevel(this, FName(*CastleLevel), true, FString::Printf(TEXT("Hero=%s"), *CurrentHero.ToString()));
	return true;
}

bool ARDDungeonGenerator::ReturnToTown()
{
	if (!bTownLink || bTown || TownLevel.IsEmpty() || bTownTraveling) return false;
	if (PlayerCombat && PlayerCombat->IsDead()) return false;
	LastTravel = TEXT("town");
	if (bTravelDryRun) return true;
	SaveCarry();
	if (URDGameInstance* GI = URDGameInstance::Of(this)) GI->Arrive = TEXT("castle");
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
	}
	else if (bTownLink && GI)
	{
		// (Mistward Castle: the tiers she opened stay open, the first set's opened containers stay opened)
		for (const int32 T : GI->CastleTiers) TiersOpened.AddUnique(T);
		for (const int32 K : GI->CastleStartLooted) LootedContainers.Add(FIntVector(0, 0, K));
		GI->Count(TEXT("enter"));
	}
}

void ARDDungeonGenerator::AfterTownBuilt()
{
	bTownPlaced = false; bTownTraveling = false;
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
			if (ARDTeleporter* T = GetWorld()->SpawnActor<ARDTeleporter>(ARDTeleporter::StaticClass(), FTransform(S->MistgateAt + S->MistgateNormal * 160.f), Sp)) { T->Init(this, 0, false); MistgateFx = T; }
			for (const ARDSection::FTownSpot& Ts : S->TownSpots)
				if (Ts.Kind == TS_Circle) if (ARDTeleporter* T = GetWorld()->SpawnActor<ARDTeleporter>(ARDTeleporter::StaticClass(), FTransform(Ts.At + FVector(0, 0, 3.f)), Sp)) { T->Init(this, 0, false); CircleFx = T; }
		}
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
	}
}

void ARDDungeonGenerator::SpawnTownPeople()
{
	for (ARDTownsfolk* P : TownPeople) if (IsValid(P)) P->Destroy();
	TownPeople.Reset();
	ARDSection* S = GetSection(FIntPoint::ZeroValue);
	if (!S) return;
	TMap<ERDTownRole, TArray<int32>> ByRole;
	for (int32 I = 0; I < Townsfolk.Num(); ++I) if (Townsfolk[I].Mesh) for (int32 K = 0; K < FMath::Max(1, Townsfolk[I].Count); ++K) ByRole.FindOrAdd(Townsfolk[I].Role).Add(I);
	TMap<ERDTownRole, int32> Used;
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
		TownPeople.Add(T);
	}
	UE_LOG(LogRDTownGame, Log, TEXT("RDTOWN %d townspeople at %d posts"), TownPeople.Num(), S->TownPosts.Num());
}

void ARDDungeonGenerator::SpawnTownGuards()
{
	for (ARDMonster* M : TownGuards) if (IsValid(M)) M->Destroy();
	TownGuards.Reset();
	ARDSection* S = GetSection(FIntPoint::ZeroValue);
	if (!S || S->CastleHallRoom < 0 || Monsters.Num() == 0) return;
	// (5 to 10 of tier 1, the number and kinds from the town's seed; the ones she killed this game stay dead)
	FRandomStream R((int32)HashCombine((uint32)StartSeed, 0x6A4Du));
	TownGuardsPlanned = R.RandRange(FMath::Min(TownGuardsMin, TownGuardsMax), FMath::Max(TownGuardsMin, TownGuardsMax));
	TArray<int32> Kinds;
	for (int32 K = 0; K < Monsters.Num(); ++K) if (Monsters[K].Tier == 1 && Monsters[K].Mesh) Kinds.Add(K);
	if (Kinds.Num() == 0) MonsterKindsFor(FIntPoint::ZeroValue, Kinds);
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
	AfterTownBuilt();
	UE_LOG(LogRDTownGame, Log, TEXT("RDTOWN rebuilt from seed %d"), StartSeed);
}

// ================================================================================================ every frame
void ARDDungeonGenerator::TickTown(float Dt, APlayerController* PC)
{
	APawn* P = PC ? PC->GetPawn() : nullptr;
	if (!P) return;
	ARDSection* S = GetSection(FIntPoint::ZeroValue);
	if (bTown && S && !bTownPlaced)
	{
		// (where she comes in: back from the castle before its door, else in the square by the elder)
		URDGameInstance* GI = URDGameInstance::Of(this);
		FVector At = GetStartRoomCenter() + FVector(0, 0, 100.f);
		float Yaw = P->GetActorRotation().Yaw;
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
	// (-RDTownGo=castle: a packaged game's test goes on into the castle at once, once a run)
	static bool bRDTownGoDone = false;
	FString Go;
	if (bTown && bTownPlaced && !bRDTownGoDone && FParse::Value(FCommandLine::Get(), TEXT("RDTownGo="), Go) && Go == TEXT("castle")) { bRDTownGoDone = true; EnterCastle(); return; }
	// the Mistgate: walked into, Mistward Castle opens
	if (bTown && S && !bTownTraveling && !S->MistgateAt.IsZero() && FVector::Dist2D(P->GetActorLocation(), S->MistgateAt) < 170.f
		&& !(PlayerCombat && PlayerCombat->IsDead()))
		EnterCastle();
}

// ================================================================================================ F in the town
FString ARDDungeonGenerator::TownDescribe(const FVector& From) const
{
	if (!bTown)
	{
		if (bTownLink && !CastleWayBack.IsZero() && FVector::Dist2D(From, CastleWayBack) < 260.f && FMath::Abs(From.Z - CastleWayBack.Z) < 250.f) return FString::Printf(TEXT("return to %s"), *TownName);
		return FString();
	}
	if (IsTownPanelOpen()) return FString();
	// (someone near: talk)
	int32 Who = -1; float Best = 240.f;
	for (int32 I = 0; I < TownPeople.Num(); ++I)
		if (const ARDTownsfolk* T = TownPeople[I]; IsValid(T)) { const float D = FVector::Dist2D(T->GetActorLocation(), From); if (D < Best && FMath::Abs(T->GetActorLocation().Z - From.Z) < 200.f) { Best = D; Who = I; } }
	// (a door or a container nearer than them: that is what F does)
	if (Who >= 0) if (const ARDSection* S0 = GetSection(FIntPoint::ZeroValue)) { bool bD0 = false; int32 I0 = -1; if (Best > 160.f || S0->FindNearestInteractive(From, Best, bD0, I0) < Best - 30.f) Who = -1; }
	if (Who >= 0) return FString::Printf(TEXT("talk to %s"), *TownPeople[Who]->Title);
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
		case TS_Stash: if (D < 240.f) return TEXT("open your storage"); break;
		case TS_Smith: if (D < 230.f) return TEXT("the smith's work"); break;
		case TS_Circle: if (D < 620.f) return TEXT("touch the teleport circle"); break;
		case TS_Board: if (D < 260.f) return TEXT("read the quest board"); break;
		case TS_Gate: if (D < 520.f) return TEXT("the gate (barred)"); break;
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
		return FString();
	}
	if (TownPanelClosedFrame == GFrameCounter) return TEXT("closed");
	int32 Who = -1; float Best = 240.f;
	for (int32 I = 0; I < TownPeople.Num(); ++I)
		if (const ARDTownsfolk* T = TownPeople[I]; IsValid(T)) { const float D = FVector::Dist2D(T->GetActorLocation(), From); if (D < Best && FMath::Abs(T->GetActorLocation().Z - From.Z) < 200.f) { Best = D; Who = I; } }
	if (Who >= 0) if (const ARDSection* S0 = GetSection(FIntPoint::ZeroValue)) { bool bD0 = false; int32 I0 = -1; if (Best > 160.f || S0->FindNearestInteractive(From, Best, bD0, I0) < Best - 30.f) Who = -1; }
	if (Who >= 0)
	{
		ARDTownsfolk* T = TownPeople[Who];
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
		case TS_Stash: if (D < 240.f) Panel = TEXT("stash"); break;
		case TS_Smith: if (D < 230.f) Panel = TEXT("smith"); break;
		case TS_Circle: if (D < 620.f) Panel = TEXT("circle"); break;
		case TS_Board: if (D < 260.f) Panel = TEXT("board"); break;
		case TS_Gate:
			if (D < 520.f)
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

void ARDDungeonGenerator::TownOnKill(ARDMonster* M, bool bBossKill)
{
	if (!M || M->IsAlly()) return;
	const int32 T = FMath::Max(1, M->Tier);
	// (the roll a hash of the monster, not a stream the play draws from)
	const uint32 H = HashCombine(GetTypeHash(M->GetUniqueID()), (uint32)SessionSeed ^ 0x601Du);
	int32 Gold = FMath::RoundToInt(FMath::Lerp(KillGold.X, KillGold.Y, (H % 1000u) / 999.f) * T);
	if (bBossKill || M->bBoss) Gold += FMath::RoundToInt(BossGold * T);
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
}

void ARDDungeonGenerator::TownOnContainer(ARDSection* Section, int32 Key, const FVector& At)
{
	if (!Section) return;
	const int32 T = bTown ? 1 : FMath::Max(1, TierOf(Section->Coord));
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
	if (Q.Goal == TEXT("tier") || Q.Goal == TEXT("guards")) return GI->GetCounter(Q.Goal);
	const FRDQuestState* St = GI->FindQuest(Q.Id);
	const int32 Base = St ? St->Base : 0;
	return FMath::Max(0, GI->GetCounter(Q.Goal) - Base);
}

static FString RDQuestStateOf(const URDGameInstance* GI, const FRDQuestDef& Q, int32 Progress)
{
	if (Q.Goal.StartsWith(TEXT("wild:"))) return TEXT("later");
	const FRDQuestState* St = GI ? GI->FindQuest(Q.Id) : nullptr;
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
		Out.Add(FString::Printf(TEXT("%s|%s|%s|%s|%d|%d|%s"), *Q.Id.ToString(), *Q.Giver.ToString(), *Q.Title, *RDQuestStateOf(GI, Q, P), FMath::Min(P, Q.Count), Q.Count, *Q.Hint));
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
		if (Q->Goal.StartsWith(TEXT("wild:"))) { SetTownNote(TEXT("The wilderness beyond the gate is not open yet: this waits for a later chapter")); return false; }
		FRDQuestState N; N.Id = Id; N.State = 1; N.Base = Q->Goal == TEXT("tier") || Q->Goal == TEXT("guards") ? 0 : GI->GetCounter(Q->Goal);
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
	auto QuestLinesOf = [&](const FName Giver)
	{
		int32 Shown = 0;
		for (const FRDQuestDef& Q : Quests)
		{
			if (Q.Giver != Giver) continue;
			const int32 P = QuestProgress(Q);
			const FString St = RDQuestStateOf(GI, Q, P);
			const FRDQuestState* Before = Q.After.IsNone() ? nullptr : (GI ? GI->FindQuest(Q.After) : nullptr);
			const bool bOpen = Q.After.IsNone() || (Before && Before->State == 2);
			if (!bOpen || St == TEXT("done")) continue;
			// (the board posts three bounties at a time)
			if (Giver == TEXT("Board") && St == TEXT("offered") && ++Shown > 3) continue;
			const FString Arg = Q.Id.ToString();
			if (St == TEXT("later")) Add(TEXT("later"), Q.Title, TEXT("LATER"), Q.Offer + TEXT("\n\n(The wilderness beyond the gate is not open yet: this quest waits for a later chapter.)"), false, Arg);
			else if (St == TEXT("offered")) Add(TEXT("accept"), FString::Printf(TEXT("Quest: %s"), *Q.Title), Q.Gold > 0 ? FString::Printf(TEXT("%d g"), Q.Gold) : TEXT("NEW"), Q.Offer, true, Arg);
			else if (St == TEXT("ready")) Add(TEXT("turnin"), FString::Printf(TEXT("Done: %s"), *Q.Title), TEXT("REWARD"), Q.Done, true, Arg);
			else Add(TEXT("status"), Q.Title, FString::Printf(TEXT("%d / %d"), FMath::Min(P, Q.Count), Q.Count), Q.Hint, false, Arg);
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
		QuestLinesOf(TEXT("Board"));
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
		const float Miss = PlayerCombat ? PlayerCombat->GetMaxHealth() - PlayerCombat->GetHealth() : 0.f;
		const int32 Cost = FMath::Max(Miss > 0.5f ? 2 : 0, FMath::RoundToInt(Miss * 0.25f * RDTierPrice(T)));
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
	else if (TownPanel == TEXT("stash"))
	{
		TownTitle = TEXT("Your storage"); TownSub = TEXT("the storehouse keeps what you leave here, as long as the game lasts");
		if (TownTab == 0) { if (PlayerCombat) RDTownThingLines(this, PlayerCombat, TownLines, TEXT("deposit"), false); }
		else if (GI)
			for (int32 I = 0; I < GI->StashThings.Num(); ++I)
				Add(TEXT("withdraw"), GI->StashThings[I].ToString(), GI->StashWear.IsValidIndex(I) && GI->StashWear[I] >= 0.f ? FString::Printf(TEXT("%.0f"), GI->StashWear[I]) : FString(), TEXT("In your storage"), true, FString::FromInt(I));
		if (TownLines.Num() == 0) Add(TEXT("none"), TownTab == 0 ? TEXT("You carry nothing to store") : TEXT("Your storage is empty"), FString(), FString(), false);
		Add(TEXT("bye"), TEXT("Leave"), FString(), FString());
	}
	else if (TownPanel == TEXT("circle"))
	{
		TownTitle = TEXT("The teleport circle"); TownSub = TEXT("the stones know the circles you have found");
		if (TownBody.IsEmpty()) TownBody = TEXT("The runes wake under your hand. Any circle you find beyond the walls will answer this one, and this one will take you there.");
		if (GI) for (const FName& C : GI->CirclesFound) Add(C == FName(TEXT("Brokenspire")) ? FName(TEXT("here")) : FName(TEXT("travel")), C.ToString(), C == FName(TEXT("Brokenspire")) ? TEXT("YOU ARE HERE") : TEXT("TRAVEL"),
			C == FName(TEXT("Brokenspire")) ? TEXT("This circle") : TEXT("Step through"), C != FName(TEXT("Brokenspire")), C.ToString());
		Add(TEXT("none"), TEXT("No other circle found yet"), TEXT("LATER"), TEXT("They lie in the wilderness beyond the gate, which is not open yet."), false);
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
	if (!E.bOn && E.Act != TEXT("ask")) { SetTownNote(E.Act == TEXT("buy") || E.Act == TEXT("heal") || E.Act == TEXT("bless") || E.Act == TEXT("repair") ? TEXT("You have too little gold") : E.Detail); return false; }
	if (E.Act == TEXT("ask")) { TownBody = E.Detail; TownCount(TEXT("asked")); bOk = true; }
	else if (E.Act == TEXT("accept") || E.Act == TEXT("turnin")) bOk = TownQuestAction(E.Act, FName(*E.Arg));
	else if (E.Act == TEXT("status")) { TownBody = E.Detail; bOk = true; }
	else if (E.Act == TEXT("buy")) bOk = TownBuy(FName(*E.Arg));
	else if (E.Act == TEXT("sell")) bOk = TownSell(E.Arg);
	else if (E.Act == TEXT("heal")) bOk = TownHeal();
	else if (E.Act == TEXT("repair")) bOk = TownRepair(E.Arg);
	else if (E.Act == TEXT("anvil")) { CloseTownPanel(); if (PlayerCombat) PlayerCombat->SetCraftingOpen(true); return true; }
	else if (E.Act == TEXT("bless")) bOk = TownBless();
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

bool ARDDungeonGenerator::TownHeal()
{
	if (!PlayerCombat) return false;
	const float Miss = PlayerCombat->GetMaxHealth() - PlayerCombat->GetHealth();
	const int32 Cost = FMath::Max(Miss > 0.5f ? 2 : 0, FMath::RoundToInt(Miss * 0.25f * RDTierPrice(GetGameTier())));
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

// ================================================================================================ the panel's keys and pointer
void ARDDungeonGenerator::TickTownPanel(APlayerController* PC)
{
	if (!PC || !IsTownPanelOpen()) return;
	auto Pressed = [PC](std::initializer_list<FKey> Keys) { for (const FKey& K : Keys) if (PC->WasInputKeyJustPressed(K)) return true; return false; };
	if (Pressed({ EKeys::Escape, EKeys::BackSpace, EKeys::F, EKeys::Tab, EKeys::Gamepad_FaceButton_Right })) { CloseTownPanel(); return; }
	if (Pressed({ EKeys::W, EKeys::Up, EKeys::Gamepad_DPad_Up })) MoveTownCursor(-1);
	if (Pressed({ EKeys::S, EKeys::Down, EKeys::Gamepad_DPad_Down })) MoveTownCursor(1);
	if (Pressed({ EKeys::A, EKeys::Left, EKeys::Gamepad_DPad_Left, EKeys::Gamepad_LeftShoulder })) SetTownTab(0);
	if (Pressed({ EKeys::D, EKeys::Right, EKeys::Gamepad_DPad_Right, EKeys::Gamepad_RightShoulder })) SetTownTab(1);
	if (Pressed({ EKeys::Enter, EKeys::SpaceBar, EKeys::E, EKeys::Gamepad_FaceButton_Bottom })) { ActivateTownEntry(); return; }
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
		if (bClick) { ActivateTownEntry(I); return; }
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
