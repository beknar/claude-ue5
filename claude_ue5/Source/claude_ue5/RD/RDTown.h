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
enum ERDTownKind : uint8 { TK_Castle, TK_Smithy, TK_Store, TK_Healer, TK_Temple, TK_Storehouse, TK_Tavern, TK_Home, TK_Chapel, TK_Barracks, TK_Witch, TK_Count };
/** what stands outdoors, and the services inside the buildings (the counter, the basin, the altar, the stash, the smith's
 *  place by his anvil, the tavern's bar) */
enum ERDTownSpot : uint8 { TS_Well, TS_Board, TS_Circle, TS_Stall, TS_Still, TS_Mill, TS_Grave, TS_Graveyard, TS_Tower, TS_Gate, TS_Lamp, TS_Tent,
	TS_Counter, TS_Basin, TS_Altar, TS_Stash, TS_Smith, TS_Bar };

inline FString RDTownKindName(uint8 Kind)
{
	static const TCHAR* Names[] = { TEXT("castle"), TEXT("smithy"), TEXT("store"), TEXT("healer"), TEXT("temple"), TEXT("storehouse"), TEXT("tavern"),
	                                TEXT("home"), TEXT("chapel"), TEXT("barracks"), TEXT("witch's hut") };
	return Kind < TK_Count ? FString(Names[Kind]) : FString(TEXT("?"));
}

inline FString RDTownSpotName(uint8 Kind)
{
	static const TCHAR* Names[] = { TEXT("well"), TEXT("board"), TEXT("circle"), TEXT("stall"), TEXT("still"), TEXT("mill"), TEXT("grave"), TEXT("graveyard"),
	                                TEXT("tower"), TEXT("gate"), TEXT("lamp"), TEXT("tent"), TEXT("counter"), TEXT("basin"), TEXT("altar"), TEXT("stash"), TEXT("smith"), TEXT("bar") };
	return Kind <= TS_Bar ? FString(Names[Kind]) : FString(TEXT("?"));
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
protected:
	virtual void Tick(float Dt) override;
private:
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
	void SetClip(bool bWalk);
	int32 HomeBld = -1;
	FVector HomeIn = FVector::ZeroVector;
	bool bResident_ = false, bWentHome = false, bSleeping = false;
	/** the town's hour's part of its day: in or out, asleep or awake; true while it walks to where its hour wants it */
	bool TickDay(float Now);
};
