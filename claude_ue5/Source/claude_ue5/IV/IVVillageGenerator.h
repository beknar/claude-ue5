// random_isometric_village_level: procedural nucleated village seen from a fixed isometric camera.
// The plan is one village around one hub: a cobbled square at the origin (well, market stalls, the church, the tavern and
// the craftsmen's houses facing it), ring streets closing around it (RingRadius) and short lanes between the rings
// (spokes, staggered from band to band so no road runs straight for long; three main roads wind out from the square).
// Houses stand shoulder to shoulder along the rings facing the street, their gardens filling the block behind. The plan
// is a pure function of the plan seeds, so every 250 m section - whatever order they are generated in - continues the
// same rings and lanes: the village grows as one clustered whole, thinning into farmsteads and fields away from the hub.
// Villagers (AIVVillager, three for every ten buildings of a section) wander its streets; they exist in play only.
// The start section (centred on the origin) is built in the editor with a fixed seed and saved; in play the next section
// is generated when the player nears the edge of the generated village (fresh seed each session, never saved), with
// random_level's reveal effect. Buildings are assembled from the House Forge kit so that the roof and the camera-side
// walls of the house she is in (and anything else hiding its floor) can be cut away. Doors and containers open with F.
#pragma once

#include "CoreMinimal.h"
#include "GameFramework/Actor.h"
#include "IVTypes.h"
#include "IVVillageGenerator.generated.h"

class AIVSection;
class AIVVillager;
class UMaterialInterface;
class UMaterialInstanceDynamic;
class UPostProcessComponent;
class UNiagaraSystem;

UCLASS()
class CLAUDE_UE5_API AIVVillageGenerator : public AActor
{
	GENERATED_BODY()

public:
	AIVVillageGenerator();

	// ---- layout
	UPROPERTY(EditAnywhere, BlueprintReadOnly, Category = "IsoVillage|Layout") float SectionSize = 25000.f;
	UPROPERTY(EditAnywhere, BlueprintReadOnly, Category = "IsoVillage|Layout") int32 StartSeed = 20261012;
	/** generate the next section once the player is this close to the edge of the generated village (moving toward it) */
	UPROPERTY(EditAnywhere, BlueprintReadOnly, Category = "IsoVillage|Layout") float TriggerDistance = 3000.f;
	/** any missing section closer than this is generated whatever her direction */
	UPROPERTY(EditAnywhere, BlueprintReadOnly, Category = "IsoVillage|Layout") float SafetyDistance = 1500.f;
	/** runtime sections farther than this many sections are removed (0 = keep all); the map remembers them */
	UPROPERTY(EditAnywhere, BlueprintReadOnly, Category = "IsoVillage|Layout") int32 UnloadSectionDistance = 2;
	/** session seed for runtime sections (0 = random each play) */
	UPROPERTY(EditAnywhere, BlueprintReadOnly, Category = "IsoVillage|Layout") int32 FixedSessionSeed = 0;
	/** runtime sections are built over several frames: time budget per frame */
	UPROPERTY(EditAnywhere, BlueprintReadOnly, Category = "IsoVillage|Layout") float FrameBudgetMs = 5.f;
	/** generation and the cutaway follow this actor instead of the player pawn when set (cinematics) */
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "IsoVillage|Layout") TObjectPtr<AActor> TrackedActor;
	/** cinematics: doors open by themselves for the tracked actor within this distance (0 = off; the player uses F) */
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "IsoVillage|Layout") float TrackedAutoDoorDistance = 0.f;

	// ---- view (the player controller and the cutaway use the same angles; the pitch is fixed, the yaw turns in play)
	UPROPERTY(EditAnywhere, BlueprintReadOnly, Category = "IsoVillage|View") float IsoYaw = 45.f;
	UPROPERTY(EditAnywhere, BlueprintReadOnly, Category = "IsoVillage|View") float IsoPitch = -35.264f;
	/** roofs and camera-side walls are cut away while she is inside a building */
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "IsoVillage|View") bool bCutaway = true;
	/** how far the player has turned the view from IsoYaw (degrees; Q / E) */
	UPROPERTY(Transient, BlueprintReadOnly, Category = "IsoVillage|View") float ViewYawOffset = 0.f;
	UFUNCTION(BlueprintCallable, Category = "IsoVillage|View") void SetViewYawOffset(float Degrees);
	UFUNCTION(BlueprintCallable, BlueprintPure, Category = "IsoVillage|View") float GetViewYaw() const { return IsoYaw + ViewYawOffset; }
	/** in play r.Shadow.RadiusThreshold is lowered to this (0 = left alone): seen from 120 m away, people are too small to
	 *  cast a shadow at the engine's default */
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "IsoVillage|View") float ShadowRadiusThreshold = 0.001f;

	// ---- plan
	UPROPERTY(EditAnywhere, BlueprintReadOnly, Category = "IsoVillage|Plan") float SquareRadius = 2600.f;
	UPROPERTY(EditAnywhere, BlueprintReadOnly, Category = "IsoVillage|Plan") float FirstRingRadius = 6500.f;
	UPROPERTY(EditAnywhere, BlueprintReadOnly, Category = "IsoVillage|Plan") float RingSpacing = 5200.f;
	UPROPERTY(EditAnywhere, BlueprintReadOnly, Category = "IsoVillage|Plan") float SpokeSpacing = 7500.f;
	UPROPERTY(EditAnywhere, BlueprintReadOnly, Category = "IsoVillage|Plan") float LaneHalfWidth = 170.f;
	UPROPERTY(EditAnywhere, BlueprintReadOnly, Category = "IsoVillage|Plan") float RingHalfWidth = 210.f;
	UPROPERTY(EditAnywhere, BlueprintReadOnly, Category = "IsoVillage|Plan") float MainRoadHalfWidth = 280.f;
	/** rings 0..FixedRings and the bands between them use StartSeed (everything the start section can touch) */
	UPROPERTY(EditAnywhere, BlueprintReadOnly, Category = "IsoVillage|Plan") int32 FixedRings = 4;
	/** house kit module (wall length / floor tile) and storey height */
	UPROPERTY(EditAnywhere, BlueprintReadOnly, Category = "IsoVillage|Plan") float Module = 400.f;
	UPROPERTY(EditAnywhere, BlueprintReadOnly, Category = "IsoVillage|Plan") float WallHeight = 400.f;
	/** height of the house floor above the ground (kit foundation) */
	UPROPERTY(EditAnywhere, BlueprintReadOnly, Category = "IsoVillage|Plan") float FloorHeight = 0.f;
	/** rise of one roof piece (one cell across) */
	UPROPERTY(EditAnywhere, BlueprintReadOnly, Category = "IsoVillage|Plan") float RoofRise = 400.f;

	// ---- generation indicator (random_level's materials: M_RT_RevealPP / M_RT_RevealCurtain)
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "IsoVillage|Reveal") bool bRevealEffect = true;
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "IsoVillage|Reveal") TObjectPtr<UMaterialInterface> RevealPostMaterial;
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "IsoVillage|Reveal") TObjectPtr<UMaterialInterface> RevealCurtainMaterial;
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "IsoVillage|Reveal") float RevealDuration = 7.f;
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "IsoVillage|Reveal") float RevealCurtainHeight = 900.f;
	static constexpr int32 RevealSlots = 6;
	/** post process drawing her silhouette where something hides her (custom depth) */
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "IsoVillage|View") TObjectPtr<UMaterialInterface> SilhouetteMaterial;

	// ---- content
	/** named pieces (kit walls / floors / roofs per style, furniture, props, trees...) normalised to the village frame */
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "IsoVillage|Content") TMap<FName, FIVPiece> Pieces;
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "IsoVillage|Content") TMap<FName, TObjectPtr<UNiagaraSystem>> Effects;
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "IsoVillage|Content") TObjectPtr<UMaterialInterface> GroundMaterial;

	// ---- villagers (play only, never saved)
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "IsoVillage|Villagers") TArray<FIVVillagerDef> Villagers;
	/** villagers per building in every section (0.3: three for every ten buildings; 0 = none) */
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "IsoVillage|Villagers") float VillagerCoverage = 0.3f;
	/** she cannot walk through a villager (off for the cinematic's scripted walk) */
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "IsoVillage|Villagers") bool bVillagersBlockPawns = true;
	UFUNCTION(BlueprintCallable, Category = "IsoVillage|Villagers") TArray<AIVVillager*> GetVillagers() const;
	/** villagers ask before searching a path: one search a frame for the whole village */
	bool TakePathSlot();
	/** path searches by villagers so far: how many, how many found nothing, total and longest time (ms) */
	UPROPERTY(VisibleAnywhere, BlueprintReadOnly, Category = "IsoVillage|Villagers") int32 VillagerPaths = 0;
	UPROPERTY(VisibleAnywhere, BlueprintReadOnly, Category = "IsoVillage|Villagers") int32 VillagerPathFails = 0;
	UPROPERTY(VisibleAnywhere, BlueprintReadOnly, Category = "IsoVillage|Villagers") float VillagerPathMs = 0.f;
	UPROPERTY(VisibleAnywhere, BlueprintReadOnly, Category = "IsoVillage|Villagers") float VillagerPathMaxMs = 0.f;
	void NotePath(double Ms, bool bFound) { ++VillagerPaths; if (!bFound) ++VillagerPathFails; VillagerPathMs += (float)Ms; VillagerPathMaxMs = FMath::Max(VillagerPathMaxMs, (float)Ms); }

	// ---- state
	UPROPERTY(VisibleAnywhere, BlueprintReadOnly, Category = "IsoVillage") TMap<FIntPoint, TObjectPtr<AIVSection>> Sections;
	UPROPERTY(VisibleAnywhere, BlueprintReadOnly, Category = "IsoVillage") TMap<FIntPoint, FIVSectionMap> MapData;
	UPROPERTY(VisibleAnywhere, BlueprintReadOnly, Category = "IsoVillage") int32 SessionSeed = 0;
	UPROPERTY(VisibleAnywhere, BlueprintReadOnly, Category = "IsoVillage") int32 SectionsGenerated = 0;
	UPROPERTY(VisibleAnywhere, BlueprintReadOnly, Category = "IsoVillage") int32 SectionsRemoved = 0;
	UPROPERTY(BlueprintReadOnly, Category = "IsoVillage") bool bMapOpen = false;
	/** big map zoom (1 = the default scale) */
	UPROPERTY(BlueprintReadWrite, Category = "IsoVillage") float MapZoom = 1.f;

	/** (editor) clear everything and build the start section with StartSeed; saved with the level */
	UFUNCTION(CallInEditor, BlueprintCallable, Category = "IsoVillage") void BuildStartSection();
	UFUNCTION(CallInEditor, BlueprintCallable, Category = "IsoVillage") void ClearAll();

	// ---- sections
	UFUNCTION(BlueprintCallable, BlueprintPure, Category = "IsoVillage") FIntPoint WorldToSection(FVector Location) const;
	UFUNCTION(BlueprintCallable, BlueprintPure, Category = "IsoVillage") FVector2D SectionMin(FIntPoint Section) const;
	UFUNCTION(BlueprintCallable, Category = "IsoVillage") bool IsSectionGenerated(FIntPoint Section) const;
	UFUNCTION(BlueprintCallable, Category = "IsoVillage") AIVSection* GetSection(FIntPoint Section) const;
	UFUNCTION(BlueprintCallable, Category = "IsoVillage") TArray<FIntPoint> GetSectionCoords() const;
	UFUNCTION(BlueprintCallable, Category = "IsoVillage") bool GenerateSectionNow(FIntPoint Section);
	UFUNCTION(BlueprintCallable, Category = "IsoVillage") int32 GetQueueLength() const { return Queue.Num(); }
	UFUNCTION(BlueprintCallable, Category = "IsoVillage") bool IsBuildingSection() const { return Building != nullptr; }
	bool IsStartSection(FIntPoint S) const { return S == FIntPoint::ZeroValue; }
	int32 SectionSeed(FIntPoint S) const;
	UFUNCTION(BlueprintCallable, Category = "IsoVillage") AActor* GetTrackedActor() const;

	// ---- plan (pure functions of the plan seeds; angles in radians, distances in cm from the village centre)
	/** ring 0 = edge of the square, ring k >= 1 = the k-th ring street */
	UFUNCTION(BlueprintCallable, BlueprintPure, Category = "IsoVillage|Plan") float RingRadius(int32 Ring, float Theta) const;
	/** band b lies between ring b and ring b + 1; -1 = on the square */
	UFUNCTION(BlueprintCallable, BlueprintPure, Category = "IsoVillage|Plan") int32 BandAt(float R, float Theta) const;
	UFUNCTION(BlueprintCallable, BlueprintPure, Category = "IsoVillage|Plan") int32 SpokeCount(int32 Band) const;
	/** angle of a lane across its band (T = 0 on the inner ring, 1 on the outer ring) */
	UFUNCTION(BlueprintCallable, BlueprintPure, Category = "IsoVillage|Plan") float SpokeAngle(int32 Band, int32 Index, float T) const;
	UFUNCTION(BlueprintCallable, BlueprintPure, Category = "IsoVillage|Plan") bool IsMainSpoke(int32 Band, int32 Index) const;
	/** world point of a lane across its band */
	UFUNCTION(BlueprintCallable, BlueprintPure, Category = "IsoVillage|Plan") FVector2D SpokePoint(int32 Band, int32 Index, float T) const;
	/** distance to the nearest road edge (negative on a road); Type: 0 lane, 1 main road, 2 ring street, 3 the square */
	UFUNCTION(BlueprintCallable, BlueprintPure, Category = "IsoVillage|Plan") float RoadDistance(FVector2D P, int32& Type) const;
	/** how built-up the village is at this distance from the centre (1 = shoulder to shoulder) */
	UFUNCTION(BlueprintCallable, BlueprintPure, Category = "IsoVillage|Plan") float Density(float R) const;
	float RingBase(int32 Ring) const;
	float RingHalf(int32 Ring) const { return Ring <= 0 ? 0.f : Ring == 1 ? RingHalfWidth + 40.f : RingHalfWidth; }
	float SpokeHalf(int32 Band, int32 Index) const { return IsMainSpoke(Band, Index) ? MainRoadHalfWidth : LaneHalfWidth; }
	/** the building sites of a band (cached) */
	const TArray<FIVLot>& GetLots(int32 Band) const;
	/** sector of band 0 that holds the church */
	int32 ChurchSector() const;
	int32 PlanSeed(int32 RingOrBand) const { return RingOrBand <= FixedRings ? StartSeed : SessionSeed; }

	// ---- interaction
	/** toggles the nearest door or container within MaxDistance of From (what F does); returns a description or "" */
	UFUNCTION(BlueprintCallable, Category = "IsoVillage") FString InteractNearest(FVector From, float MaxDistance = 260.f);
	/** what F would do here ("open door", "close chest"...) or "" */
	UFUNCTION(BlueprintCallable, Category = "IsoVillage") FString DescribeNearest(FVector From, float MaxDistance = 260.f) const;
	UFUNCTION(BlueprintCallable, Category = "IsoVillage") void SetMapOpen(bool bOpen) { bMapOpen = bOpen; }
	/** buildings generated / entered so far */
	UFUNCTION(BlueprintCallable, Category = "IsoVillage") void GetVillageStats(int32& Buildings, int32& Visited, int32& NumSections) const;
	UFUNCTION(BlueprintCallable, Category = "IsoVillage") static FString KindName(EIVBuildingKind Kind);
	/** section + building index she is inside (-1: outdoors) */
	UFUNCTION(BlueprintCallable, Category = "IsoVillage") int32 GetCurrentBuilding(FIntPoint& Section) const { Section = InsideSection; return InsideBuilding; }
	/** walkable path between two world points over the generated sections (50 cm grid, doors passable); empty if none */
	UFUNCTION(BlueprintCallable, Category = "IsoVillage") TArray<FVector> FindPath(FVector From, FVector To, int32 MaxCells = 400000) const;
	/** nav grid: is this world point free for the player capsule */
	UFUNCTION(BlueprintCallable, Category = "IsoVillage") bool IsWalkable(FVector Location) const;
	bool NavBlocked(const FVector2D& P) const;
	/** FindPath; without bThroughDoors the path stays outdoors (or indoors) */
	TArray<FVector> FindPathEx(const FVector& From, const FVector& To, int32 MaxCells, bool bThroughDoors) const;

	const FIVPiece* Piece(FName Name) const { const FIVPiece* P = Pieces.Find(Name); return (P && (P->Mesh || P->ActorClass)) ? P : nullptr; }
	/** unit vector from the scene toward the camera */
	FVector ToCamera() const { return -FRotator(IsoPitch, GetViewYaw(), 0.f).Vector(); }
	/** the same for the view the level starts with (what is built does not depend on how the view is turned) */
	FVector ToCameraDefault() const { return -FRotator(IsoPitch, IsoYaw, 0.f).Vector(); }
	float LastRevealTime = -100.f;
	FIntPoint LastRevealSection = FIntPoint::ZeroValue;

protected:
	virtual void BeginPlay() override;
	virtual void EndPlay(const EEndPlayReason::Type Reason) override;
	virtual void Tick(float DeltaSeconds) override;

private:
	UPROPERTY(VisibleAnywhere, Category = "IsoVillage|Reveal") TObjectPtr<UPostProcessComponent> RevealPost;
	UPROPERTY(Transient) TObjectPtr<UMaterialInstanceDynamic> RevealMID;
	UPROPERTY(Transient) TObjectPtr<AIVSection> Building;
	int32 NextRevealSlot = 0;
	TArray<FIntPoint> Queue;
	FIntPoint InsideSection = FIntPoint::ZeroValue;
	int32 InsideBuilding = -1;
	bool bCutDirty = false;
	float LastCutTime = -1.f;
	float SavedShadowRadius = -1.f;
	uint64 PathFrame = 0;
	int32 PathsThisFrame = 0;
	struct FBandInfo { int32 N = 0; TArray<float> Base; TArray<float> Bulge; TArray<int8> Main; };
	mutable TMap<int32, FBandInfo> BandCache;
	mutable TMap<int32, TArray<FIVLot>> LotCache;
	mutable int32 CacheSessionSeed = -1;
	const FBandInfo& Band(int32 B) const;
	float MainAngle(int32 M, float R) const;
	void BuildLots(int32 Band, TArray<FIVLot>& Out) const;
	AIVSection* SpawnSection(FIntPoint S, bool bEditorBuild, bool bReveal = false);
	void StartReveal(AIVSection* Section);
	void Enqueue(FIntPoint S);
	void UpdateCutaway(const FVector& L);
};
