// The user's list of 2026-11-22 (docs/improvements16.txt; the plan docs/improvements16_plan.md), its tenth phase: the caves' crafting
// materials and their recipes. Their items (SourceArt/caves/treasure16.json, 945 items) are on every map; a container draws the caves' own
// items only in a cave (CaveItems16), and there a cave's gear, rings, tomes and scrolls come from them alone, while its potions, food,
// repair items and materials are drawn as anywhere. A cave knows its region by its tower's biome (the game instance's CaveBiome16, set
// at the mouth): a geode's colour, the cold's frost quartz and the heat's sun-glass are found only in their regions' caves. Veins of
// deepiron in the rooms' walls and growths of glowcap and grave-moss on their floors hold harvest piles. Three new buffs: darksight (a dim
// light of the buff's metres on her), poison guarded (a poison's blows less) and lamp oil (the torch and ankh burn longer).
#include "RD/RDDungeonGenerator.h"
#include "RD/RDSection.h"
#include "RD/RDCombat.h"
#include "RD/RDGameInstance.h"
#include "Components/PointLightComponent.h"
#include "Components/StaticMeshComponent.h"
#include "Engine/CollisionProfile.h"
#include "Engine/StaticMesh.h"
#include "Engine/World.h"
#include "GameFramework/Pawn.h"
DEFINE_LOG_CATEGORY_STATIC(LogRDCave16b, Log, All);

// ================================================================================================ the region and the draws
int32 ARDDungeonGenerator::CaveRegion16() const
{
	const URDGameInstance* GI = URDGameInstance::Of(this);
	const FString B = GI ? GI->CaveBiome16 : FString();
	if (B.IsEmpty()) return -1;
	for (int32 I = 0; I < CaveRegions16.Num(); ++I) if (CaveRegions16[I].Biomes.Contains(B)) return I;
	return -1;
}

FString ARDDungeonGenerator::GetCaveRegion16() const
{
	const int32 R = CaveRegion16();
	const URDGameInstance* GI = URDGameInstance::Of(this);
	return FString::Printf(TEXT("%s|%s"), R >= 0 ? *CaveRegions16[R].Name.ToString() : TEXT("none"), GI ? *GI->CaveBiome16 : TEXT(""));
}

void ARDDungeonGenerator::SetCaveBiome16(const FString& Biome)
{
	if (URDGameInstance* GI = URDGameInstance::Of(this)) GI->CaveBiome16 = Biome;
}

bool ARDDungeonGenerator::CaveItemAllowed16(const FRDItemDef& It) const
{
	if (CaveItems16.Num() == 0) return true;
	const bool bCaveItem = CaveItems16.Contains(It.Name);
	// (outside a cave: none of the caves' own; their draws and sums as before)
	if (!bCave16) return !bCaveItem;
	// (a region's own items: only in its region's caves; with no region known (a cave played from the editor) none of them)
	// (an item two regions share (frost quartz in the cold lands and the mountains) is found in both: it is left out only if some region
	// names it and the cave's does not)
	const int32 Rg = CaveRegion16();
	bool bRegional = false;
	for (const FRDCaveRegion16& Rr : CaveRegions16) bRegional |= Rr.Items.Contains(It.Name);
	if (bRegional && !(CaveRegions16.IsValidIndex(Rg) && CaveRegions16[Rg].Items.Contains(It.Name))) return false;
	// (a cave's gear, rings, tomes and scrolls: the caves' own only)
	switch (It.Kind)
	{
	case ERDItemKind::Weapon: case ERDItemKind::Armour: case ERDItemKind::Shield: case ERDItemKind::Ring: case ERDItemKind::Tome: case ERDItemKind::Scroll:
		return bCaveItem;
	default:
		return true;
	}
}

bool ARDDungeonGenerator::CaveMayDraw16(FName Item) const
{
	const int32 Ix = FindItem(Item);
	return Ix >= 0 && CaveItemAllowed16(Items[Ix]);
}

FString ARDDungeonGenerator::GetCaveCraft16(FName Item) const
{
	const FRDRecipe* Rc = Recipes.FindByPredicate([&](const FRDRecipe& R) { return R.Item == Item; });
	if (!Rc) return TEXT("none|no recipe");
	const FName St = RecipeStation(*Rc);
	return FString::Printf(TEXT("%s|%s"), St.IsNone() ? TEXT("") : *St.ToString(), *RecipeRefusal(*Rc));
}

TArray<FString> ARDDungeonGenerator::GetCaveNodes16(FIntPoint Section) const
{
	const ARDSection* S = GetSection(Section);
	return S ? S->CaveNodeLines16 : TArray<FString>();
}

// ================================================================================================ the veins and growths
void ARDSection::CaveNodesSet16()
{
	// (in each kit room: its veins on the walls (a ray out from the room's middle across a floor tile by its edge meets the wall), its
	// growths on its floor; a harvest pile before each. A set built again lays none twice (the generator's CaveNodesLaid16); the mesh
	// stays when the pile is taken (the vein worked out))
	CaveNodeLines16.Reset();
	UWorld* W = GetWorld();
	if (!Generator || !W || !W->IsGameWorld() || Generator->CaveNodes16.Num() == 0) return;
	FRandomStream R(Seed ^ 0x0DE16);
	FCollisionQueryParams Q(SCENE_QUERY_STAT(RDCave16Node), true);
	const float S = Generator->TileSize;
	const FVector O = GetActorLocation();
	const int32 Rg = Generator->CaveRegion16();
	int32 Ord = 0;
	for (int32 RI = 0; RI < CavePlaced16.Num(); ++RI)
	{
		if (CavePlaced16[RI].Kit < 0 || Rooms[RI].Kind == ERDRoomKind::Junction || !CaveRoomTiles16.IsValidIndex(RI) || CaveRoomTiles16[RI].Num() == 0) continue;
		const TArray<FIntPoint>& Tiles = CaveRoomTiles16[RI];
		const FVector Mid = O + FVector((CavePlaced16[RI].At.X + 0.5f) * S, (CavePlaced16[RI].At.Y + 0.5f) * S, CavePlaced16[RI].Z + 150.f);
		for (const FRDCaveNode16& Nd : Generator->CaveNodes16)
		{
			const int32 Want = R.RandRange(Nd.PerRoom.X, FMath::Max(Nd.PerRoom.X, Nd.PerRoom.Y));
			for (int32 K = 0; K < Want; ++K)
			{
				const FIntPoint Tl = Tiles[R.RandRange(0, Tiles.Num() - 1)];
				const int32 Count = R.RandRange(Nd.Count.X, FMath::Max(Nd.Count.X, Nd.Count.Y));
				const float Sc = R.FRandRange(Nd.Scale.X, Nd.Scale.Y), Yw = R.FRandRange(0.f, 360.f);
				const FIntVector Key(Coord.X, Coord.Y, Ord++);
				if (!Nd.Mesh || Nd.Item.IsNone() || (!Nd.Region.IsNone() && (Rg < 0 || Generator->CaveRegions16[Rg].Name != Nd.Region))) continue;
				FHitResult H; FVector At, PileAt; FRotator Turn(0.f, Yw, 0.f);
				const FVector T3 = TileWorld(Tl, CaveFloorAt16(Tl));
				if (Nd.bWall)
				{
					const FVector Way = (FVector(T3.X, T3.Y, Mid.Z) - Mid).GetSafeNormal2D();
					if (Way.IsNearlyZero() || !W->LineTraceSingleByChannel(H, Mid, Mid + Way * 4000.f, ECC_Visibility, Q) || H.ImpactNormal.Z > 0.6f) continue;
					Turn = FRotator(0.f, H.ImpactNormal.Rotation().Yaw, 0.f);
					FHitResult F;
					const FVector Out = FVector(H.ImpactNormal.X, H.ImpactNormal.Y, 0.f).GetSafeNormal();
					const FVector Front = H.ImpactPoint + Out * 110.f;
					if (!W->LineTraceSingleByChannel(F, Front + FVector(0, 0, 100.f), Front - FVector(0, 0, 500.f), ECC_Visibility, Q)) continue;
					PileAt = F.ImpactPoint;
					// (the vein at the wall's foot, 25 cm out from it (on the wall 1.5 m up the first stood half in the rock, unseen))
					At = FVector(H.ImpactPoint.X, H.ImpactPoint.Y, F.ImpactPoint.Z) + Out * 25.f;
				}
				else
				{
					if (!W->LineTraceSingleByChannel(H, T3 + FVector(0, 0, 300.f), T3 - FVector(0, 0, 400.f), ECC_Visibility, Q)) continue;
					At = H.ImpactPoint;
					// (the pile beside it, on the floor: traced, and none against a wall (PR #117's review))
					const FVector Side = FRotator(0.f, Yw, 0.f).RotateVector(FVector(70.f, 0.f, 0.f));
					FHitResult F, Wl;
					if (W->LineTraceSingleByChannel(Wl, At + FVector(0, 0, 60.f), At + Side + FVector(0, 0, 60.f), ECC_Visibility, Q)) continue;
					if (!W->LineTraceSingleByChannel(F, At + Side + FVector(0, 0, 150.f), At + Side - FVector(0, 0, 300.f), ECC_Visibility, Q)) continue;
					PileAt = F.ImpactPoint;
				}
				UStaticMeshComponent* C = NewObject<UStaticMeshComponent>(this);
				C->SetMobility(EComponentMobility::Static);
				C->SetStaticMesh(Nd.Mesh);
				if (Nd.Material) C->SetMaterial(0, Nd.Material);
				C->SetupAttachment(RootComponent);
				C->SetRelativeTransform(FTransform(Turn, At, FVector(Sc)).GetRelativeTransform(GetActorTransform()));
				C->SetCollisionProfileName(UCollisionProfile::NoCollision_ProfileName);
				C->RegisterComponent();
				CaveComps16.Add(C);
				CaveNodeLines16.Add(FString::Printf(TEXT("node|%s|%.0f|%.0f|%.0f|%d"), *Nd.Item.ToString(), PileAt.X, PileAt.Y, PileAt.Z, Nd.bWall ? 1 : 0));
				if (Generator->CaveNodesLaid16.Contains(Key)) continue;
				Generator->CaveNodesLaid16.Add(Key);
				TArray<FName> Things; for (int32 J = 0; J < Count; ++J) Things.Add(Nd.Item);
				if (Generator->DropHarvest(PileAt, Things, Generator->TierOf(Coord))) --Generator->Harvests;          // (laid, not cut from a kill: out of the harvests' count (PR #117's review))
			}
		}
	}
	UE_LOG(LogRDCave16b, Log, TEXT("RDCAVE16 (%d,%d): %d veins and growths"), Coord.X, Coord.Y, CaveNodeLines16.Num());
}

// ================================================================================================ her buffs
float URDCombatComponent::GetEffectMax16(ERDItemKind K) const
{
	float B = 0.f;
	for (const FEffect& E : Effects) if (E.Kind == K) B = FMath::Max(B, E.Amount);
	return B;
}

void URDCombatComponent::TickDarksight16()
{
	// (darksight: a dim, shadowless light of the buff's metres round her while it lasts, gone with it)
	const float M = GetEffectMax16(ERDItemKind::Darksight);
	APawn* P = Cast<APawn>(GetOwner());
	if (M <= 0.f || !P || !Generator)
	{
		if (DarkLight16) { DarkLight16->DestroyComponent(); DarkLight16 = nullptr; }
		return;
	}
	if (!DarkLight16)
	{
		DarkLight16 = NewObject<UPointLightComponent>(P);
		DarkLight16->SetMobility(EComponentMobility::Movable);
		DarkLight16->SetupAttachment(P->GetRootComponent());
		DarkLight16->SetRelativeLocation(FVector(0.f, 0.f, 80.f));
		DarkLight16->SetIntensityUnits(ELightUnits::Candelas);
		DarkLight16->SetLightColor(FLinearColor(0.75f, 0.85f, 1.f));
		DarkLight16->SetCastShadows(false);
		DarkLight16->RegisterComponent();
	}
	DarkLight16->SetIntensity(Generator->CaveDarksightCandelas16);
	DarkLight16->SetAttenuationRadius(M * 100.f);
}

FString URDCombatComponent::GetCaveBuffs16() const
{
	return FString::Printf(TEXT("darksight|%.0f|poisonguard|%.2f|oil|%.2f"), DarkLight16 ? DarkLight16->AttenuationRadius : 0.f,
		GetEffectMax16(ERDItemKind::PoisonGuard), GetEffectMax16(ERDItemKind::LampOil));
}
