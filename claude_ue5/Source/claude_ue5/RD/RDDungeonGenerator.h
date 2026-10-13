// random_dungeon_level: procedural dungeon. The world is a grid of 252 m sections (84 x 84 tiles of 3 m, the dungeon kits'
// module); each section holds 7 x 7 blocks, one room (or a hallway junction) per block, joined by 3 m hallways along the
// block centre lines (a random spanning tree plus loops: every room is reachable). Hallways leave each section edge at
// fixed rows (block rows 1, 3, 5), so neighbouring sections always join up. The start section (centred on the origin, the
// great hall in its middle) is built in the editor with a fixed seed and saved with the level; in play, when the player
// comes near the edge of the generated dungeon heading outward, the next section is generated (fresh seed each session,
// never saved) with the same reveal effect as random_level (post-process scan wave + border curtain). Doors and containers
// open with F, M shows the full map (the HUD draws a minimap of generated / discovered rooms), monsters wander between rooms.
// random_dungeoncombat_level is the same dungeon with bCombat on: the player gets a URDCombatComponent (hit points, the
// melee weapons of Weapons), the monsters fight. A monster's hit points and damage are the player's hit points and her
// average damage a blow, times the tier of its section (StartMonster* in the start section, RuntimeMonster* in every
// section generated in play) and its kind's factors. bStylizedMap draws the maps as a miniature of the dungeon.
#pragma once

#include "CoreMinimal.h"
#include "GameFramework/Actor.h"
#include "RDTypes.h"
#include "RDDungeonGenerator.generated.h"

class ARDSection;
class ARDMonster;
class URDCombatComponent;
class UMaterialInterface;
class UMaterialInstanceDynamic;
class UPostProcessComponent;
class UNiagaraSystem;

UCLASS()
class CLAUDE_UE5_API ARDDungeonGenerator : public AActor
{
	GENERATED_BODY()

public:
	ARDDungeonGenerator();

	// ---- layout
	UPROPERTY(EditAnywhere, BlueprintReadOnly, Category = "RandomDungeon|Layout") float TileSize = 300.f;
	UPROPERTY(EditAnywhere, BlueprintReadOnly, Category = "RandomDungeon|Layout") int32 SectionTiles = 84;
	UPROPERTY(EditAnywhere, BlueprintReadOnly, Category = "RandomDungeon|Layout") int32 BlockTiles = 12;
	UPROPERTY(EditAnywhere, BlueprintReadOnly, Category = "RandomDungeon|Layout") float RoomHeight = 600.f;
	UPROPERTY(EditAnywhere, BlueprintReadOnly, Category = "RandomDungeon|Layout") float CorridorHeight = 400.f;
	UPROPERTY(EditAnywhere, BlueprintReadOnly, Category = "RandomDungeon|Layout") int32 StartSeed = 20261011;
	/** generate the next section once the player is this close to the edge of the generated dungeon (moving toward it) */
	UPROPERTY(EditAnywhere, BlueprintReadOnly, Category = "RandomDungeon|Layout") float TriggerDistance = 4500.f;
	/** any missing section closer than this is generated whatever her direction */
	UPROPERTY(EditAnywhere, BlueprintReadOnly, Category = "RandomDungeon|Layout") float SafetyDistance = 1800.f;
	/** runtime sections farther than this many sections are removed (0 = keep all); the map remembers them */
	UPROPERTY(EditAnywhere, BlueprintReadOnly, Category = "RandomDungeon|Layout") int32 UnloadSectionDistance = 2;
	/** session seed for runtime sections (0 = random each play) */
	UPROPERTY(EditAnywhere, BlueprintReadOnly, Category = "RandomDungeon|Layout") int32 FixedSessionSeed = 0;
	/** runtime sections are furnished over several frames: time budget per frame */
	UPROPERTY(EditAnywhere, BlueprintReadOnly, Category = "RandomDungeon|Layout") float FrameBudgetMs = 6.f;
	/** share of rooms with a wandering monster */
	UPROPERTY(EditAnywhere, BlueprintReadOnly, Category = "RandomDungeon|Layout") float MonsterCoverage = 0.4f;
	/** generation follows this actor instead of the player pawn when set */
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "RandomDungeon|Layout") TObjectPtr<AActor> TrackedActor;
	/** cinematics: doors open by themselves for the tracked actor within this distance (0 = off; the player uses F) */
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "RandomDungeon|Layout") float TrackedAutoDoorDistance = 0.f;
	/** monsters block pawns (off for cinematics: a monster never stalls the scripted walk) */
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "RandomDungeon|Layout") bool bMonstersBlockPawns = true;

	// ---- fighting (random_dungeoncombat_level)
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "RandomDungeon|Combat") bool bCombat = false;
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "RandomDungeon|Combat") float PlayerMaxHealth = 100.f;
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "RandomDungeon|Combat") TArray<FRDWeaponDef> Weapons;
	/** the average monster of the start section against the player: hit points (x hers) and damage (x her average blow) */
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "RandomDungeon|Combat") float StartMonsterHealth = 0.5f;
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "RandomDungeon|Combat") float StartMonsterDamage = 0.45f;
	/** the same for the sections generated in play: on a par with her */
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "RandomDungeon|Combat") float RuntimeMonsterHealth = 1.f;
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "RandomDungeon|Combat") float RuntimeMonsterDamage = 1.f;
	/** a monster notices her within this distance (cm) when there is a way to her, and gives up beyond the other */
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "RandomDungeon|Combat") float AggroDistance = 1000.f;
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "RandomDungeon|Combat") float LoseDistance = 2200.f;
	/** a chasing monster moves at its walking speed times this, at most MaxChaseSpeed (she runs at 377 cm/s) */
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "RandomDungeon|Combat") float ChaseSpeedScale = 1.6f;
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "RandomDungeon|Combat") float MaxChaseSpeed = 290.f;
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "RandomDungeon|Combat") float CorpseSeconds = 8.f;
	/** her hit points come back at RegenPerSecond once she has not been hurt for RegenDelay seconds */
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "RandomDungeon|Combat") float RegenDelay = 6.f;
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "RandomDungeon|Combat") float RegenPerSecond = 4.f;
	/** at 0 hit points she lies this long, then stands in the middle of the start section again */
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "RandomDungeon|Combat") float RespawnSeconds = 3.5f;
	/** the maps as a miniature of the dungeon (floors by room, walls, doors, chests, torches) instead of plain rectangles */
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "RandomDungeon|Combat") bool bStylizedMap = false;
	UPROPERTY(BlueprintReadOnly, Category = "RandomDungeon|Combat") int32 MonstersKilled = 0;

	UFUNCTION(BlueprintCallable, BlueprintPure, Category = "RandomDungeon|Combat") URDCombatComponent* GetPlayerCombat() const { return PlayerCombat; }
	/** her average damage a blow over the weapons */
	UFUNCTION(BlueprintCallable, BlueprintPure, Category = "RandomDungeon|Combat") float GetAverageWeaponDamage() const;
	/** hit points / damage of the average monster of a section */
	UFUNCTION(BlueprintCallable, BlueprintPure, Category = "RandomDungeon|Combat") float GetMonsterHealth(FIntPoint Section) const;
	UFUNCTION(BlueprintCallable, BlueprintPure, Category = "RandomDungeon|Combat") float GetMonsterDamage(FIntPoint Section) const;
	/** weighted means of the monster kinds' factors (a monster's values are divided by them) */
	void MeanMonsterFactors(float& Health, float& Damage) const;
	void OnMonsterKilled(ARDMonster* Monster);
	/** a number that floats up where a blow landed (HUD) */
	struct FHitText { FVector At; float Amount; float Time; bool bOnPlayer; };
	TArray<FHitText> HitTexts;
	void AddHitText(const FVector& At, float Amount, bool bOnPlayer);
	/** demo reels and tests: the dungeon as it is when play begins (the start section's doors, containers and monsters
	 *  rebuilt from its seed, the sections generated in play removed, the map and the counters cleared, her at the start).
	 *  Seed (not 0) becomes the session seed: the sections generated from then on are the same every time. */
	UFUNCTION(BlueprintCallable, Category = "RandomDungeon|Combat") void RestartPlay(int32 Seed = 0);
	/** runtime sections are furnished within this many milliseconds a frame (a reel sets it high: built in one frame) */
	UFUNCTION(BlueprintCallable, Category = "RandomDungeon") void SetFrameBudget(float Milliseconds) { FrameBudgetMs = Milliseconds; }

	// ---- generation indicator (same materials as random_level: M_RT_RevealPP / M_RT_RevealCurtain)
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "RandomDungeon|Reveal") bool bRevealEffect = true;
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "RandomDungeon|Reveal") TObjectPtr<UMaterialInterface> RevealPostMaterial;
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "RandomDungeon|Reveal") TObjectPtr<UMaterialInterface> RevealCurtainMaterial;
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "RandomDungeon|Reveal") float RevealDuration = 7.f;
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "RandomDungeon|Reveal") float RevealCurtainHeight = 700.f;
	static constexpr int32 RevealSlots = 6;

	// ---- content
	/** named pieces (Floor_*, Ceil_*, Wall_*, Door_*, furniture, lights...) normalised to the dungeon frame */
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "RandomDungeon|Content") TMap<FName, FRDPiece> Pieces;
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "RandomDungeon|Content") TMap<FName, TObjectPtr<UNiagaraSystem>> Effects;
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "RandomDungeon|Content") TArray<FRDMonsterDef> Monsters;

	// ---- state
	UPROPERTY(VisibleAnywhere, BlueprintReadOnly, Category = "RandomDungeon") TMap<FIntPoint, TObjectPtr<ARDSection>> Sections;
	UPROPERTY(VisibleAnywhere, BlueprintReadOnly, Category = "RandomDungeon") TMap<FIntPoint, FRDSectionMap> MapData;
	UPROPERTY(VisibleAnywhere, BlueprintReadOnly, Category = "RandomDungeon") int32 SessionSeed = 0;
	UPROPERTY(VisibleAnywhere, BlueprintReadOnly, Category = "RandomDungeon") int32 SectionsGenerated = 0;
	UPROPERTY(VisibleAnywhere, BlueprintReadOnly, Category = "RandomDungeon") int32 SectionsRemoved = 0;
	UPROPERTY(BlueprintReadOnly, Category = "RandomDungeon") bool bMapOpen = false;

	/** (editor) clear everything and build the start section with StartSeed; saved with the level */
	UFUNCTION(CallInEditor, BlueprintCallable, Category = "RandomDungeon") void BuildStartSection();
	UFUNCTION(CallInEditor, BlueprintCallable, Category = "RandomDungeon") void ClearAll();

	UFUNCTION(BlueprintCallable, BlueprintPure, Category = "RandomDungeon") FIntPoint WorldToSection(FVector Location) const;
	UFUNCTION(BlueprintCallable, BlueprintPure, Category = "RandomDungeon") FIntPoint WorldToTile(FVector Location) const;
	/** first global tile of a section */
	UFUNCTION(BlueprintCallable, BlueprintPure, Category = "RandomDungeon") FIntPoint SectionMinTile(FIntPoint Section) const;
	UFUNCTION(BlueprintCallable, BlueprintPure, Category = "RandomDungeon") FVector TileCenter(FIntPoint Tile) const;
	UFUNCTION(BlueprintCallable, Category = "RandomDungeon") bool IsSectionGenerated(FIntPoint Section) const;
	UFUNCTION(BlueprintCallable, Category = "RandomDungeon") ARDSection* GetSection(FIntPoint Section) const;
	UFUNCTION(BlueprintCallable, Category = "RandomDungeon") TArray<FIntPoint> GetSectionCoords() const;
	UFUNCTION(BlueprintCallable, Category = "RandomDungeon") bool GenerateSectionNow(FIntPoint Section);
	UFUNCTION(BlueprintCallable, Category = "RandomDungeon") int32 GetQueueLength() const { return Queue.Num(); }
	/** centre of the start section's great hall (player spawn) */
	UFUNCTION(BlueprintCallable, Category = "RandomDungeon") FVector GetStartRoomCenter() const;
	/** toggles the nearest door or container within MaxDistance of From (what F does); returns a description or "" */
	UFUNCTION(BlueprintCallable, Category = "RandomDungeon") FString InteractNearest(FVector From, float MaxDistance = 260.f);
	/** what F would do here ("open door", "close chest"...) or "" */
	UFUNCTION(BlueprintCallable, Category = "RandomDungeon") FString DescribeNearest(FVector From, float MaxDistance = 260.f) const;
	UFUNCTION(BlueprintCallable, Category = "RandomDungeon") int32 GetNumMonsters() const;
	/** what M does (scripts / tests) */
	UFUNCTION(BlueprintCallable, Category = "RandomDungeon") void SetMapOpen(bool bOpen) { bMapOpen = bOpen; }
	UFUNCTION(BlueprintCallable, Category = "RandomDungeon") TArray<ARDMonster*> GetMonsters() const;
	/** discovered rooms / all rooms (generated) */
	UFUNCTION(BlueprintCallable, Category = "RandomDungeon") void GetDiscoveryStats(int32& DiscoveredRooms, int32& GeneratedRooms) const;
	UFUNCTION(BlueprintCallable, Category = "RandomDungeon") static FString KindName(ERDRoomKind Kind);

	bool IsStartSection(FIntPoint S) const { return S == FIntPoint::ZeroValue; }
	int32 SectionSeed(FIntPoint S) const;
	/** block rows / columns with a hallway across each section edge */
	static bool IsPortalBlock(int32 B) { return B == 1 || B == 3 || B == 5; }
	UFUNCTION(BlueprintCallable, Category = "RandomDungeon") AActor* GetTrackedActor() const;
	const FRDPiece* Piece(FName Name) const { const FRDPiece* P = Pieces.Find(Name); return (P && (P->Mesh || P->ActorClass)) ? P : nullptr; }
	/** world time of the last section reveal (HUD flash) */
	float LastRevealTime = -100.f;
	FIntPoint LastRevealSection = FIntPoint::ZeroValue;

protected:
	virtual void BeginPlay() override;
	virtual void Tick(float DeltaSeconds) override;

private:
	UPROPERTY(VisibleAnywhere, Category = "RandomDungeon|Reveal") TObjectPtr<UPostProcessComponent> RevealPost;
	UPROPERTY(Transient) TObjectPtr<UMaterialInstanceDynamic> RevealMID;
	UPROPERTY(Transient) TObjectPtr<ARDSection> Building;
	UPROPERTY(Transient) TObjectPtr<URDCombatComponent> PlayerCombat;
	int32 NextRevealSlot = 0;
	TArray<FIntPoint> Queue;
	ARDSection* SpawnSection(FIntPoint S, bool bEditorBuild, bool bReveal = false);
	void StartReveal(ARDSection* Section);
	void Enqueue(FIntPoint S);
	void UpdateDiscovery(const FVector& L);
};
