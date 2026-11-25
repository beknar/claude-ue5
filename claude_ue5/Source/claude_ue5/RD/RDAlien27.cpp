// The list of 2026-11-22's twenty-seventh phase: the fortress's tiers 3 to 5 an open alien world (947 world).
//
// The user's words: "eventually opening up into a wider open world that uses the Alien Planet, using its procedural content generation
// graphs to generate areas that can be explored by the player for Tiers 3-5". The pack's graphs read a landscape and splines, which the
// game's sets of tiles have not (the survey of the pack, docs/levels/heaven.md): the game lays the pack's own baked clusters (the
// LI_* level instances its graphs copy, read once by 947 world into AlienClusters27) itself, as the caves lay the Hyper kit's dressing.
//
// A set whose theme is open (OpenThemes27, the generator's) keeps its plan of rooms and hallways and its tiles (monsters, maps,
// progress and saves are unchanged), but:
//  - no walls, ceilings, doorways, doors, columns, torches or things hung from a ceiling; no room lights (the sun lights it);
//  - every tile of the set is ground; where the plan has no tile (Type 0) a ridge of rocks stands, and next to a walked tile an
//    invisible blocker as tall as a room keeps her and the monsters' sight out of it;
//  - the clearings (rooms) and paths (hallways) are dressed with the pack's clusters: plants and pebbles to walk through, and spike
//    rocks and trees that block the tiles they stand on (never a lane's: the ways through stay);
//  - the shut tiers are sealed by a force wall across the path;
//  - the sky, the sun and the fog come up as she walks out under them, and go as she walks back in.
// No draw is taken from the plan's stream: each tile and room has a stream of its own.

#include "RD/RDSection.h"
#include "RD/RDDungeonGenerator.h"
#include "Components/InstancedStaticMeshComponent.h"
#include "Components/StaticMeshComponent.h"
#include "Components/BoxComponent.h"
#include "Components/DirectionalLightComponent.h"
#include "Components/SkyAtmosphereComponent.h"
#include "Components/SkyLightComponent.h"
#include "Components/ExponentialHeightFogComponent.h"
#include "Engine/CollisionProfile.h"
#include "GameFramework/Pawn.h"
#include "Kismet/GameplayStatics.h"
#include "Engine/World.h"
#include "Misc/CommandLine.h"
#include "Misc/Parse.h"

static uint32 RDA27Hash(uint32 A, uint32 B, uint32 C)
{
	uint32 H = A * 0x9E3779B1u ^ (B + 0x7F4A7C15u) * 0x85EBCA6Bu ^ (C + 0x165667B1u) * 0xC2B2AE35u;
	H ^= H >> 15; H *= 0x2C1B3C6Du; H ^= H >> 12; H *= 0x297A2D39u; H ^= H >> 15;
	return H;
}

bool ARDSection::IsOpenTheme27() const
{
	return Generator && !Theme.IsNone() && Generator->OpenThemes27.Contains(Theme);
}

void ARDSection::AlienSolid27(FIntPoint T)
{
	const float S = Generator->TileSize;
	const FVector C = TileWorld(T);
	FRandomStream Ra((int32)RDA27Hash((uint32)Seed, (uint32)(T.X * 131 + 7), (uint32)(T.Y * 977 + 3)));
	AddPieceAt(Generator->AlienGround27, C, 90.f * Ra.RandRange(0, 3));
	++AlienGround27N;
	// (next to a walked tile (eight ways): the blocker, and the ridge's rocks close round the walked ground)
	bool bEdge = false;
	for (int32 Dx = -1; Dx <= 1 && !bEdge; ++Dx)
		for (int32 Dy = -1; Dy <= 1; ++Dy)
		{
			const FIntPoint Nb(T.X + Dx, T.Y + Dy);
			if ((Dx || Dy) && In(Nb) && Type[Idx(Nb)] != 0) { bEdge = true; break; }
		}
	if (bEdge)
	{
		AddPieceAt(Generator->AlienBlock27, C, 0.f);
		++AlienBlockers27N;
	}
	if (Generator->AlienRocks27.Num() == 0) return;
	// (a ridge: two or three rocks a tile at its edge, one tile in three inside it, bigger)
	const int32 K = bEdge ? Ra.RandRange(2, 3) : (Ra.FRand() < 0.34f ? 1 : 0);
	for (int32 I = 0; I < K; ++I)
	{
		const FName Rk = Generator->AlienRocks27[Ra.RandRange(0, Generator->AlienRocks27.Num() - 1)];
		const float Sc = bEdge ? Ra.FRandRange(1.6f, 2.6f) : Ra.FRandRange(2.4f, 4.0f);
		const FVector P = C + FVector(Ra.FRandRange(-0.3f, 0.3f) * S, Ra.FRandRange(-0.3f, 0.3f) * S, -Ra.FRandRange(0.f, 25.f));
		AddPiece(Rk, FTransform(FRotator(Ra.FRandRange(-6.f, 6.f), Ra.FRandRange(0.f, 360.f), Ra.FRandRange(-6.f, 6.f)), P, FVector(Sc)), true);
		++AlienRocks27N;
	}
}

int32 ARDSection::AlienCluster27(FRandomStream& Ra, const FVector& At, bool bBlocking, int32 RI)
{
	TArray<int32> Pick;
	for (int32 I = 0; I < Generator->AlienClusters27.Num(); ++I) if (Generator->AlienClusters27[I].bBlocks == bBlocking && Generator->AlienClusters27[I].Parts.Num() > 0) Pick.Add(I);
	if (Pick.Num() == 0) return 0;
	const FRDAlienCluster27& Cl = Generator->AlienClusters27[Pick[Ra.RandRange(0, Pick.Num() - 1)]];
	const float Yaw = Ra.FRandRange(0.f, 360.f);
	const float Sc = bBlocking ? 1.f : Ra.FRandRange(0.8f, 1.15f);
	const FTransform Base(FRotator(0, Yaw, 0), At, FVector(Sc));
	if (bBlocking)
	{
		// (its footprint: kept off the lanes, off every other footprint and off a container's way in, its tiles blocked)
		const FVector2D Sz = Cl.Half * 2.f * Sc;
		if (RI >= 0 && Rooms.IsValidIndex(RI) && !LaneFree(Rooms[RI], At, FMath::Max(Sz.X, Sz.Y) * 0.5f)) return 0;
		if (Generator->bTidyFurniture && !FootFree(At, Yaw, Sz, false)) return 0;
		if (Generator->bTidyFurniture) AddFoot(At, Yaw, Sz, false, TEXT("Alien27.Cluster"));
		MarkBlocked(At, Yaw, Sz, false);
		AlienBlocking27.Add(FVector(At.X, At.Y, At.Z));
	}
	int32 Made = 0;
	for (const FRDAlienPart27& Pt : Cl.Parts)
	{
		const FTransform W = Pt.Xf * Base;
		AddPiece(Pt.Piece, W, !bBlocking);
		++Made;
	}
	++AlienClusters27N; AlienParts27N += Made;
	return Made;
}

void ARDSection::AlienDress27(int32 RI)
{
	const FRoom& Rm = Rooms[RI];
	const float S = Generator->TileSize;
	FRandomStream Ra((int32)RDA27Hash((uint32)Seed ^ 0xA1E7u, (uint32)RI, 0x27u));
	// (the ground's clusters: plants, pebbles, moss on a share of the room's tiles)
	for (int32 X = Rm.Min.X; X < Rm.Max.X; ++X)
		for (int32 Y = Rm.Min.Y; Y < Rm.Max.Y; ++Y)
		{
			const FIntPoint T(X, Y);
			if (!In(T) || Owner[Idx(T)] != RI) continue;
			if (Ra.FRand() >= Generator->AlienDressShare27) continue;
			const FVector P = TileWorld(T) + FVector(Ra.FRandRange(-0.35f, 0.35f) * S, Ra.FRandRange(-0.35f, 0.35f) * S, 0.f);
			AlienCluster27(Ra, P, false, RI);
		}
	// (the spike rocks and trees: a few a clearing, in its quadrants, blocking their tiles)
	if (Rm.Kind == ERDRoomKind::Junction) return;
	const int32 W = Rm.Max.X - Rm.Min.X, H = Rm.Max.Y - Rm.Min.Y;
	if (W < 4 || H < 4) return;
	const int32 Want = FMath::Min(Generator->AlienBlockersPerRoom27, (W * H) / 16 + 1);
	for (int32 Tries = 0, Done = 0; Tries < Want * 6 && Done < Want; ++Tries)
	{
		const FIntPoint T(Ra.RandRange(Rm.Min.X + 1, Rm.Max.X - 2), Ra.RandRange(Rm.Min.Y + 1, Rm.Max.Y - 2));
		if (!In(T) || Owner[Idx(T)] != RI || T.X == Rm.Lane.X || T.Y == Rm.Lane.Y || Blocked[Idx(T)]) continue;
		if (AlienCluster27(Ra, TileWorld(T), true, RI) > 0) ++Done;
	}
}

void ARDSection::AlienCorridor27(int32 CI)
{
	const FCorr& C = Corrs[CI];
	const float S = Generator->TileSize;
	FRandomStream Ra((int32)RDA27Hash((uint32)Seed ^ 0xC0A7u, (uint32)CI, 0x27u));
	for (int32 X = C.Min.X; X < C.Max.X; ++X)
		for (int32 Y = C.Min.Y; Y < C.Max.Y; ++Y)
		{
			const FIntPoint T(X, Y);
			if (!In(T) || Type[Idx(T)] == 0 || Ra.FRand() >= Generator->AlienDressShare27 * 0.5f) continue;
			AlienCluster27(Ra, TileWorld(T) + FVector(Ra.FRandRange(-0.3f, 0.3f) * S, Ra.FRandRange(-0.3f, 0.3f) * S, 0.f), false, -1);
		}
}

void ARDSection::AlienSeal27(const FVector& Border, const FVector& Out)
{
	// (a force wall across the path: the generator's AlienForce27, stretched to the hallway's width and a room's height)
	const FRDPiece* P = Generator->Piece(Generator->AlienForce27);
	if (!P || !P->Mesh) return;
	const float TS = Generator->TileSize, Hh = Generator->RoomHeight;
	UStaticMeshComponent* C = NewObject<UStaticMeshComponent>(this);
	C->SetMobility(EComponentMobility::Movable);
	C->SetStaticMesh(P->Mesh);
	if (P->Material) C->SetMaterial(0, P->Material);
	C->SetupAttachment(RootComponent);
	C->SetCollisionEnabled(ECollisionEnabled::NoCollision);
	C->SetCastShadow(false);
	C->RegisterComponent();
	const FVector Sz = P->Size;
	const FVector Sc(1.f, (TS * 1.0f) / FMath::Max(Sz.Y, 1.f), Hh / FMath::Max(Sz.Z, 1.f));
	C->SetWorldTransform(P->Adjust * FTransform((-Out).Rotation(), Border - Out * 24.f, Sc));
	C->ComponentTags.Add(TEXT("AlienForce27"));
	SealComps.Add(C);
}

FString ARDSection::GetAlienStats27() const
{
	return FString::Printf(TEXT("open=%d|ground=%d|blockers=%d|rocks=%d|clusters=%d|parts=%d|blocking=%d"),
		IsOpenTheme27() ? 1 : 0, AlienGround27N, AlienBlockers27N, AlienRocks27N, AlienClusters27N, AlienParts27N, AlienBlocking27.Num());
}

bool ARDSection::IsTileBlocked27(FVector At) const
{
	const FIntPoint T = WorldToLocal(At);
	return In(T) && Blocked.Num() == N * N && Blocked[Idx(T)] != 0;
}

// ------------------------------------------------------------------------------------------------ the sky
bool ARDDungeonGenerator::IsOpenAt27(FVector At) const
{
	if (OpenThemes27.Num() == 0) return false;
	const FName T = ThemeOf(WorldToSection(At));
	return !T.IsNone() && OpenThemes27.Contains(T);
}

void ARDDungeonGenerator::TickOpen27Go()
{
	// (0: not asked; 1: waiting for the start set; 2: she is in tier 3's set, waiting for the sky; 3: done)
	if (Open27Go == 0 && FParse::Param(FCommandLine::Get(), TEXT("RDOpen27"))) Open27Go = 1;
	if (Open27Go == 0 || Open27Go == 3) return;
	APawn* Her = UGameplayStatics::GetPlayerPawn(this, 0);
	if (!Her) return;
	const FIntPoint S3(2, 0);
	if (Open27Go == 1)
	{
		if (!IsSectionGenerated(FIntPoint(0, 0))) return;
		DebugOpenTiers(3, false);
		if (!IsSectionGenerated(S3)) GenerateSectionNow(S3);
		ARDSection* S = GetSection(S3);
		if (!S || S->IsBuilding()) return;
		for (int32 I = 0; I < S->GetNumRooms(); ++I)
		{
			const FVector C = S->GetRoomCenter(I);
			if (C.IsNearlyZero()) continue;
			Her->SetActorLocation(C + FVector(0, 0, 120.f), false, nullptr, ETeleportType::TeleportPhysics);
			break;
		}
		Open27Go = 2;
		return;
	}
	ARDSection* S = GetSection(S3);
	if (Open27Go == 2 && S && AlienSky27 >= 0.99f)
	{
		WriteTestMark(TEXT("open27"), FString::Printf(TEXT("%s sky=%.2f"), *S->GetAlienStats27(), AlienSky27));
		UE_LOG(LogTemp, Log, TEXT("RDOPEN27 %s sky=%.2f"), *S->GetAlienStats27(), AlienSky27);
		Open27Go = 3;
	}
}

void ARDDungeonGenerator::TickAlienSky27(float Dt)
{
	if (OpenThemes27.Num() == 0) return;
	UWorld* W = GetWorld();
	if (!W || !W->IsGameWorld()) return;
	TickOpen27Go();
	const APawn* Her = UGameplayStatics::GetPlayerPawn(this, 0);
	const bool bOut = Her && IsOpenAt27(Her->GetActorLocation());
	const float Want = bOut ? 1.f : 0.f;
	if (FMath::IsNearlyEqual(AlienSky27, Want) && (AlienSun27 || !bOut)) return;
	if (!AlienSun27)
	{
		AlienSun27 = NewObject<UDirectionalLightComponent>(this, TEXT("AlienSun27"));
		AlienSun27->SetMobility(EComponentMobility::Movable);
		AlienSun27->SetupAttachment(RootComponent);
		AlienSun27->SetLightColor(AlienSunColor27);
		AlienSun27->SetAtmosphereSunLight(true);
		AlienSun27->SetCastShadows(true);
		AlienSun27->RegisterComponent();
		AlienSun27->SetWorldRotation(AlienSunRot27);
		AlienAtmos27 = NewObject<USkyAtmosphereComponent>(this, TEXT("AlienAtmos27"));
		AlienAtmos27->SetupAttachment(RootComponent);
		AlienAtmos27->SetRayleighScattering(AlienRayleigh27);
		AlienAtmos27->SetMieScatteringScale(AlienMie27);
		AlienAtmos27->RegisterComponent();
		AlienSkyLight27 = NewObject<USkyLightComponent>(this, TEXT("AlienSkyLight27"));
		AlienSkyLight27->SetMobility(EComponentMobility::Movable);
		AlienSkyLight27->SetupAttachment(RootComponent);
		AlienSkyLight27->bRealTimeCapture = true;
		AlienSkyLight27->RegisterComponent();
		AlienFog27 = NewObject<UExponentialHeightFogComponent>(this, TEXT("AlienFog27"));
		AlienFog27->SetupAttachment(RootComponent);
		AlienFog27->SetFogInscatteringColor(AlienFogColor27);
		AlienFog27->RegisterComponent();
		AlienFog27->SetWorldLocation(GetActorLocation() + FVector(0, 0, -200.f));
		AddInstanceComponent(AlienSun27); AddInstanceComponent(AlienAtmos27); AddInstanceComponent(AlienSkyLight27); AddInstanceComponent(AlienFog27);
	}
	// (eased over a second and a half, as she walks out of the building's last hallway)
	AlienSky27 = FMath::FInterpConstantTo(AlienSky27, Want, Dt, 0.7f);
	const bool bOn = AlienSky27 > 0.001f;
	AlienSun27->SetIntensity(AlienSunLux27 * AlienSky27);
	AlienSun27->SetVisibility(bOn);
	AlienAtmos27->SetVisibility(bOn);
	AlienSkyLight27->SetIntensity(AlienSkyLight27Scale * AlienSky27);
	AlienSkyLight27->SetVisibility(bOn);
	AlienFog27->SetFogDensity(AlienFogDensity27 * AlienSky27);
	AlienFog27->SetVisibility(bOn);
}

float ARDDungeonGenerator::GetAlienSky27() const { return AlienSky27; }
