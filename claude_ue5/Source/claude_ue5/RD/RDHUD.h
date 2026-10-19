// random_dungeon_level HUD: minimap (top right; generated rooms dim, discovered rooms lit, the player, nearby monsters,
// new sections flashing as they generate), the full map on M (everything discovered), and a prompt next to a door or
// container ("F  open door").
// random_dungeoncombat_level adds (the generator's bStylizedMap / bCombat): both maps drawn as a miniature of the dungeon
// (stone floors coloured by room, walls with a lit and a shaded edge, paving joints, doors, chests, flickering torches;
// every room named on the full map), a status panel in the bottom right corner (hit points, the three weapons with
// their damage, kills), a bar over each monster in the fight, the damage numbers, a red flash when she is hurt.
// With the generator's bTacticalMaps (every dungeon level, pipeline/unreal/821) both maps are tactical: the minimap dark
// monochrome terrain with a feathered rim under bright markers, the big map a see-through wireframe centred on her over
// the game (see DrawTacticalMinimap / DrawTacticalMap).
#pragma once

#include "CoreMinimal.h"
#include "GameFramework/HUD.h"
#include "RDTypes.h"
#include "RDUIArt.h"
#include "RDHUD.generated.h"

class ARDDungeonGenerator;

UCLASS()
class CLAUDE_UE5_API ARDHUD : public AHUD
{
	GENERATED_BODY()

public:
	/** minimap: metres across */
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "RandomDungeon") float MinimapMeters = 120.f;
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "RandomDungeon") float MinimapPixels = 300.f;
	/** the stylised minimap shows less of the dungeon, larger (metres across) */
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "RandomDungeon") float StylizedMinimapMeters = 84.f;
	/** the generator's bTacticalMaps: the big map shows this many metres from the top of the screen to the bottom */
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "RandomDungeon") float TacticalMapMeters = 110.f;

	virtual void DrawHUD() override;
	/** tests: the painted pieces (the generator's UIArt) drawn in the last frame */
	UFUNCTION(BlueprintCallable, BlueprintPure, Category = "RandomDungeon|Interface") TArray<FName> GetArtDrawn() const { return ArtDrawn; }

private:
	// ---- random_dungeonmagic_level4's painted interface (the generator's UIArt; none on the other levels: plain boxes)
	FRDUIDraw UI;
	TArray<FName> ArtDrawn;
	/** a panel's painted board stretched round A..B (it reaches Ext beyond them: its frame sits round what is in it) */
	bool Board(FName Name, const FVector2D& A, const FVector2D& B, float Sc, float Ext);
	/** a painted piece stretched along A..B at the height of the box (its ends kept: a divider, a plaque) */
	bool Strip(FName Name, const FVector2D& A, const FVector2D& B, const FLinearColor& Tint = FLinearColor::White);
	/** the picture of her weapon I / of an item (NAME_None: none) */
	FName WeaponIcon(int32 I) const;
	FName ItemIcon(FName Item) const;
	UPROPERTY(Transient) TObjectPtr<ARDDungeonGenerator> Gen;
	// ---- the tactical maps (generator bTacticalMaps)
	/** a white disc whose alpha falls off to its rim (made in play): the minimap's feathered backdrop, the soft dots */
	UPROPERTY(Transient) TObjectPtr<class UTexture2D> SoftDisc;
	UTexture2D* GetSoftDisc();
	/** every tile of the map data: 1 generated, 2 discovered, 4 hallway; rebuilt when the map data changes */
	TMap<FIntPoint, uint8> Tiles;
	int32 TileSig = 0;
	void CacheTiles();
	void DrawTacticalMinimap(float Sc, const FVector& L, float Yaw);
	void DrawTacticalMap(float Sc, const FVector& L, float Yaw);
	/** level 4's big map in the minimap's style: the painted board, its leather darkened by a vignette, the minimap's dark
	 *  tiles and lit walls fading out toward the board, the plaque, the compass, the key (DrawTacticalMap without the art) */
	void DrawPaintedMap(float Sc, const FVector& L, float Yaw);
	void SoftDot(const FVector2D& P, float R, const FLinearColor& C);
	void Star(const FVector2D& P, float R, const FLinearColor& C);
	void Diamond(const FVector2D& P, float R, const FLinearColor& C);
	void Triangle(const FVector2D& P, float R, const FLinearColor& C);
	/** a monster much stronger than its section's average (the strongest kinds) */
	bool IsElite(const class ARDMonster* M) const;
	/** what the maps mark, in world XY: 0 monster, 1 elite, 2 unopened chest or trunk, 3 hallway exit to a section not yet generated */
	struct FRDPoi { FVector2D W; int32 Kind; };
	void GatherPois(TArray<FRDPoi>& Out, const FVector& L, float SenseDistance);
	static FString KindCode(ERDRoomKind Kind);
	void DrawPlayerArrow(const FVector2D& P, float Yaw, float Size);
	void Box(const FVector2D& A, const FVector2D& B, const FLinearColor& C);
	void Frame(const FVector2D& A, const FVector2D& B, const FLinearColor& C, float T);
	/** the miniature: ToS maps world XY to the screen, everything is clipped to S0..S1 */
	void DrawDungeon(const FVector2D& S0, const FVector2D& S1, TFunctionRef<FVector2D(const FVector2D&)> ToS, float PixelsPerTile, bool bOnlyDiscovered, bool bLabels, float Sc);
	void DrawCombat(float Sc);
	// ---- random_dungeonmagic_level4 (generator Heroes)
	/** "FOUND  <item>" a moment after a container gave it, and what the inventory last did */
	void DrawNotices(float Sc);
	/** her inventory (it pauses the game): her weapons, then her potions and food; what the one under the cursor does */
	void DrawInventory(float Sc);
	/** what an item does, for her (its share in her hit points or mana) */
	FString DescribeItem(const FRDItemDef& It) const;
};
