// Brokenspire (docs/brokenspire.txt): the town's building kinds and outdoor things (RDTownPlan.cpp lays them out), and the
// townspeople (ARDTownsfolk: the NPC packs' bodies on their own clips, as the prisoners; no controller). Those with
// functionality (the elder, the scholar, the guard captain) give quests and tell what is happening; the others say a line
// of their own when she speaks to them (F) and turn to her.
#pragma once

#include "CoreMinimal.h"
#include "GameFramework/Actor.h"
#include "RDTypes.h"
#include "RDTown.generated.h"

class ARDDungeonGenerator;
class ARDSection;
class USkeletalMeshComponent;
class UCapsuleComponent;

/** the town's buildings */
/** (Vel Morrath's holy city, 2026-11-06 (RDHoly.cpp): the cathedral at its middle over the catacombs, the monastery) */
enum ERDTownKind : uint8 { TK_Castle, TK_Smithy, TK_Store, TK_Healer, TK_Temple, TK_Storehouse, TK_Tavern, TK_Home, TK_Chapel, TK_Barracks, TK_Witch,
	TK_Cathedral, TK_Monastery, TK_Count };
/** what stands outdoors, and the services inside the buildings (the counter, the basin, the altar, the stash, the smith's
 *  place by his anvil, the tavern's bar); the holy city's statues, fountain and wayside shrines */
enum ERDTownSpot : uint8 { TS_Well, TS_Board, TS_Circle, TS_Stall, TS_Still, TS_Mill, TS_Grave, TS_Graveyard, TS_Tower, TS_Gate, TS_Lamp, TS_Tent,
	TS_Counter, TS_Basin, TS_Altar, TS_Stash, TS_Smith, TS_Bar, TS_Statue, TS_Fountain, TS_Shrine };

/** the kinds of place a townsperson's round of work is made of (the third list, 2026-11-02): a cooking pot, a spit, a garden,
 *  a pen, a tavern's seat, serving at a tavern's table, chatting (the well, the square), the smithy, the bar, a camp's fire */
enum ERDTownWorkGroup : uint8 { TW_Pot, TW_Spit, TW_Garden, TW_Pen, TW_Seat, TW_Serve, TW_Chat, TW_Smithy, TW_Bar, TW_Camp, TW_Count };

inline FString RDTownKindName(uint8 Kind)
{
	static const TCHAR* Names[] = { TEXT("castle"), TEXT("smithy"), TEXT("store"), TEXT("healer"), TEXT("temple"), TEXT("storehouse"), TEXT("tavern"),
	                                TEXT("home"), TEXT("chapel"), TEXT("barracks"), TEXT("witch's hut"), TEXT("cathedral"), TEXT("monastery") };
	return Kind < TK_Count ? FString(Names[Kind]) : FString(TEXT("?"));
}

inline FString RDTownSpotName(uint8 Kind)
{
	static const TCHAR* Names[] = { TEXT("well"), TEXT("board"), TEXT("circle"), TEXT("stall"), TEXT("still"), TEXT("mill"), TEXT("grave"), TEXT("graveyard"),
	                                TEXT("tower"), TEXT("gate"), TEXT("lamp"), TEXT("tent"), TEXT("counter"), TEXT("basin"), TEXT("altar"), TEXT("stash"), TEXT("smith"), TEXT("bar"),
	                                TEXT("statue"), TEXT("fountain"), TEXT("shrine") };
	return Kind <= TS_Shrine ? FString(Names[Kind]) : FString(TEXT("?"));
}

UCLASS()
class CLAUDE_UE5_API ARDTownsfolk : public AActor
{
	GENERATED_BODY()
public:
	ARDTownsfolk();
	/** the generator's Townsfolk entry it is, its role, name and calling */
	UPROPERTY(VisibleAnywhere, BlueprintReadOnly, Category = "RandomDungeon|Brokenspire") int32 Def = -1;
	UPROPERTY(VisibleAnywhere, BlueprintReadOnly, Category = "RandomDungeon|Brokenspire") ERDTownRole TownRole = ERDTownRole::Townsfolk;
	UPROPERTY(VisibleAnywhere, BlueprintReadOnly, Category = "RandomDungeon|Brokenspire") FString Title;
	UPROPERTY(VisibleAnywhere, BlueprintReadOnly, Category = "RandomDungeon|Brokenspire") FString Calling;
	/** where it belongs and how far it wanders from there (0: it stands) */
	UPROPERTY(VisibleAnywhere, BlueprintReadOnly, Category = "RandomDungeon|Brokenspire") FVector Post = FVector::ZeroVector;
	UPROPERTY(VisibleAnywhere, BlueprintReadOnly, Category = "RandomDungeon|Brokenspire") float Wander = 0.f;
	/** paths walked (tests) */
	UPROPERTY(BlueprintReadOnly, Category = "RandomDungeon|Brokenspire") int32 Walks = 0;
	void Init(ARDDungeonGenerator* InGenerator, ARDSection* InSection, int32 InDef, const FVector& InPost, float InYaw, float InWander, uint32 InSeed);
	/** turns to face a point for a while (she spoke to it) */
	void FaceToward(const FVector& P, float Seconds = 6.f);
	/** one of its lines (the first time its first) */
	FString NextLine();
	UFUNCTION(BlueprintCallable, BlueprintPure, Category = "RandomDungeon|Brokenspire") bool IsWalking() const { return Path.Num() > 0; }
	USkeletalMeshComponent* GetBody() const { return Body; }
	/** its building (the town's day, 2026-11-02): a keeper works in it, a resident goes in at evening (19 o'clock) and out in
	 *  the morning (half past six); asleep from 22 to 6 when it is inside a building (its torches then burn out) */
	void SetHome(int32 Bld, const FVector& Inside, bool bResident) { HomeBld = Bld; HomeIn = Inside; bResident_ = bResident; }
	UFUNCTION(BlueprintCallable, BlueprintPure, Category = "RandomDungeon|Brokenspire") bool IsSleeping() const { return bSleeping; }
	UFUNCTION(BlueprintCallable, BlueprintPure, Category = "RandomDungeon|Brokenspire") int32 GetHomeBuilding() const { return HomeBld; }
	UFUNCTION(BlueprintCallable, BlueprintPure, Category = "RandomDungeon|Brokenspire") bool IsResident() const { return bResident_; }
	/** its round of work (the third list, 2026-11-02: "have a finite state machine that loops between at least 3 activities
	 *  for NPCs and have different timers for each NPC so that they drift between at least 3 different jobs"): the places of
	 *  the section's TownWorks it goes between in turn (-1 a stroll about its post), and its own range of seconds at each.
	 *  The states: none (its old round), going (a tile path to the place), gliding (the last steps straight onto it), working
	 *  (its work's clip, its prop in its hand), strolling. A place someone else has is passed over. */
	void SetJobs(const TArray<int32>& InJobs, float InMin, float InMax);
	const TArray<int32>& GetJobs() const { return Jobs; }
	/** "<state>|<place>|<kind>|<seconds left>|<jobs done>|<kinds done, comma>|<places, comma>|<min s>|<max s>" (tests) */
	UFUNCTION(BlueprintCallable, BlueprintPure, Category = "RandomDungeon|Brokenspire") FString GetWorkState() const;
	int32 GetWorkAt() const { return WorkAt; }
	bool IsAtWork() const { return Act == 3; }
	/** the clip it plays now (tests) */
	UFUNCTION(BlueprintCallable, BlueprintPure, Category = "RandomDungeon|Brokenspire") FString GetClipName() const;
protected:
	virtual void Tick(float Dt) override;
private:
	TArray<int32> Jobs;
	int32 JobI = -1, WorkAt = -1, GoFails = 0, JobsDone = 0;
	float WorkUntil = 0.f, JobMin = 20.f, JobMax = 40.f;
	/** 0 none, 1 going, 2 gliding, 3 working, 4 strolling */
	uint8 Act = 0;
	TSet<FString> KindsDone;
	FVector GlideTo = FVector::ZeroVector;
	UPROPERTY(Transient) TObjectPtr<class UStaticMeshComponent> PropComp;
	UPROPERTY(Transient) TObjectPtr<UAnimationAsset> CurAnim;
	float CurRate = 1.f;
	void PlayAnim(UAnimationAsset* A, float Rate);
	void NextJob(float Now);
	void BeginWork(float Now);
	void EndWork();
	void SetProp(FName Prop);
	UAnimationAsset* WorkClip(FName Kind) const;
	/** the work's kind and whether it carries a tray on the way (serving) */
	FName WorkKind() const;
	/** true when the round of work took the frame */
	bool TickWork(float Now, float Dt);
	UPROPERTY() TObjectPtr<UCapsuleComponent> Capsule;
	UPROPERTY() TObjectPtr<USkeletalMeshComponent> Body;
	UPROPERTY(Transient) TObjectPtr<ARDDungeonGenerator> Gen;
	UPROPERTY(Transient) TObjectPtr<ARDSection> Section;
	UPROPERTY(Transient) TObjectPtr<UAnimationAsset> IdleAnim;
	UPROPERTY(Transient) TObjectPtr<UAnimationAsset> WalkAnim;
	TArray<FVector> Path;
	FRandomStream R;
	float Speed = 110.f, ClipSpeed = 150.f, NextTrip = 0.f, FaceUntil = -100.f, HomeYaw = 0.f, HalfHeight = 90.f;
	FVector FaceAt = FVector::ZeroVector;
	int32 LinesSaid = 0, NoPathTrips = 0;
	bool bWalkClip = false;
	/** its height over the ground where the ground is level (the list of 2026-11-04: the open ground rises and falls) */
	float FloorZ0 = -1e9f;
	void SetClip(bool bWalk);
	int32 HomeBld = -1;
	FVector HomeIn = FVector::ZeroVector;
	bool bResident_ = false, bWentHome = false, bSleeping = false;
	/** the town's hour's part of its day: in or out, asleep or awake; true while it walks to where its hour wants it */
	bool TickDay(float Now);
	friend class ARDDungeonGenerator;
};

/** a farm animal in its pen (the third list, 2026-11-02): the generator's TownAnimals mesh on its own clips (no controller):
 *  it stands, grazes and walks to another place in the pen in turn, each for a while of its own; kept inside its pen */
UCLASS()
class CLAUDE_UE5_API ARDTownAnimal : public AActor
{
	GENERATED_BODY()
public:
	ARDTownAnimal();
	void Init(ARDDungeonGenerator* InGenerator, int32 InDef, int32 InPen, const FVector& InPenAt, const FVector2D& InPenHalf, uint32 InSeed);
	UPROPERTY(VisibleAnywhere, BlueprintReadOnly, Category = "RandomDungeon|Brokenspire") int32 Def = -1;
	UPROPERTY(VisibleAnywhere, BlueprintReadOnly, Category = "RandomDungeon|Brokenspire") int32 Pen = -1;
	/** 0 standing, 1 grazing, 2 walking; the changes of state so far (tests) */
	UFUNCTION(BlueprintCallable, BlueprintPure, Category = "RandomDungeon|Brokenspire") int32 GetState() const { return State; }
	UFUNCTION(BlueprintCallable, BlueprintPure, Category = "RandomDungeon|Brokenspire") int32 GetChanges() const { return Changes; }
	USkeletalMeshComponent* GetBody() const { return Body; }
protected:
	virtual void Tick(float Dt) override;
private:
	UPROPERTY() TObjectPtr<USceneComponent> Root;
	UPROPERTY() TObjectPtr<USkeletalMeshComponent> Body;
	UPROPERTY() TObjectPtr<class UBoxComponent> Collider;
	UPROPERTY(Transient) TObjectPtr<ARDDungeonGenerator> Gen;
	FRandomStream R;
	FVector PenAt = FVector::ZeroVector, To = FVector::ZeroVector;
	FVector2D PenHalf = FVector2D(200.f, 200.f);
	int32 State = 0, Changes = 0;
	float Until = 0.f, Speed = 40.f;
	void SetState(int32 S, float Now);
};
