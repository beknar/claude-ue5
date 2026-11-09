// The user's list of 2026-11-07 (docs/improvements8.txt) on the wilderness: "implement a console command that allows the
// character to choose how fast to run in the wilderness in order to make testing of the wilderness faster. choose from 1x /
// 5x / 10x / 15x / 20x / 30x / 40x". The console variable rd.WildRunSpeed (the editor's or a Development game's console, a
// Shipping game's own (RDConsole.cpp); the command line's -RDWildRunSpeed=<x> sets it at the start). Her top speed, her
// acceleration and her braking are multiplied while she is in the wilderness, outside a town's walls; in a town she runs as
// ever. While it is over 1 the chunks' collision is cooked at once (she outruns a worker's), and where the ground she runs
// onto is not made yet she is held on the world's height instead of falling through it.
#include "RD/RDDungeonGenerator.h"
#include "RD/RDCombat.h"
#include "RD/RDWild.h"
#include "GameFramework/Character.h"
#include "GameFramework/CharacterMovementComponent.h"
#include "HAL/IConsoleManager.h"
#include "Misc/CommandLine.h"
#include "Misc/Parse.h"
#include "ProceduralMeshComponent.h"

DEFINE_LOG_CATEGORY_STATIC(LogRDWild8, Log, All);

static TAutoConsoleVariable<float> CVarRDWildRunSpeed(TEXT("rd.WildRunSpeed"), 1.f,
	TEXT("Her running speed in the wilderness (outside the towns' walls), for testing: 1, 5, 10, 15, 20, 30 or 40 (another number takes the nearest)."));

float ARDDungeonGenerator::WildRunSpeedChoice(float Asked)
{
	static const float Choices[] = { 1.f, 5.f, 10.f, 15.f, 20.f, 30.f, 40.f };
	float Best = 1.f;
	for (const float C : Choices) if (FMath::Abs(C - Asked) < FMath::Abs(Best - Asked)) Best = C;
	return Best;
}

void ARDDungeonGenerator::SetWildRunSpeed(float Factor)
{
	// (as typed at the console: set by code it ranks under a console's setting, and once the speed had been typed the
	// command line's and the tests' calls were refused with only a warning; PR #27's review)
	CVarRDWildRunSpeed->Set(WildRunSpeedChoice(Factor), ECVF_SetByConsole);
}

float ARDDungeonGenerator::GetWildRunSpeed() const
{
	return WildRunSpeedChoice(CVarRDWildRunSpeed.GetValueOnGameThread());
}

void ARDDungeonGenerator::TickWildRunSpeed(APawn* P)
{
	// (the command line's once a game: a Shipping game's only way)
	if (!bWildRunCmdRead)
	{
		bWildRunCmdRead = true;
		float Cmd = 0.f;
		if (FParse::Value(FCommandLine::Get(), TEXT("RDWildRunSpeed="), Cmd) && Cmd > 0.f) SetWildRunSpeed(Cmd);
	}
	ACharacter* Ch = Cast<ACharacter>(P);
	UCharacterMovementComponent* CM = Ch ? Ch->GetCharacterMovement() : nullptr;
	if (!CM || !PlayerCombat) return;
	const FVector L = Ch->GetActorLocation();
	const float Asked = GetWildRunSpeed();
	const float Want = (IsWildReady() && !IsInTownWalls(L)) ? Asked : 1.f;
	// (a new pawn (another hero, a respawn) comes with its own movement at 1x: applied again to it from its own base, never
	// the last pawn's; PR #27's review)
	if (WildRunMove.Get() != CM) { WildRunMove = CM; WildRunApplied = 1.f; }
	if (Want != WildRunApplied || PlayerCombat->WildRunFactor != Want)
	{
		// (her acceleration and braking with it: at 1200 cm/s² she would take two minutes to come up to 40 times her run)
		if (WildRunApplied == 1.f && Want != 1.f) { WildRunBaseAccel = CM->MaxAcceleration; WildRunBaseBrake = CM->BrakingDecelerationWalking; }
		CM->MaxAcceleration = WildRunBaseAccel * Want;
		CM->BrakingDecelerationWalking = WildRunBaseBrake * Want;
		PlayerCombat->WildRunFactor = Want;
		PlayerCombat->RefreshWalkSpeed();
		if (Asked != WildRunLogged)
		{
			WildRunLogged = Asked;
			UE_LOG(LogRDWild8, Log, TEXT("RDWILD8 run speed in the wilderness: %.0fx (now %.0fx)"), Asked, Want);
			if (Asked != 1.f || WildRunApplied != 1.f) PlayerCombat->ShowMessage(FString::Printf(TEXT("Run speed in the wilderness: %.0fx"), Asked));
		}
		WildRunApplied = Want;
	}
	// (where the ground is not made yet under her (no chunk, or its collision not there): held on the world's height)
	if (WildRunApplied > 1.f)
	{
		const FIntPoint C(FMath::FloorToInt(L.X / 100.0 / WildChunkM), FMath::FloorToInt(L.Y / 100.0 / WildChunkM));
		const TObjectPtr<ARDWildChunk>* K = WildChunks.Find(C);
		// (made, and its collision there under her: a chunk asked before she sped up cooks its collision on a worker after it
		// is made; a trace against that component alone says whether it has been cooked yet; PR #27's review)
		bool bGround = K && *K && !(*K)->bMaking && (*K)->GroundCollision;
		if (bGround)
		{
			FHitResult Hit;
			bGround = (*K)->GroundCollision->LineTraceComponent(Hit, FVector(L.X, L.Y, L.Z + 5000.f), FVector(L.X, L.Y, L.Z - 20000.f), FCollisionQueryParams(SCENE_QUERY_STAT(RDWildRunGround), false));
		}
		if (!bGround)
		{
			const float Z = WildGroundZ(L) + Ch->GetSimpleCollisionHalfHeight() + 2.f;
			if (L.Z < Z) { Ch->SetActorLocation(FVector(L.X, L.Y, Z), false, nullptr, ETeleportType::TeleportPhysics); CM->Velocity.Z = FMath::Max(CM->Velocity.Z, 0.f); ++WildRunHeld; }
		}
	}
}
