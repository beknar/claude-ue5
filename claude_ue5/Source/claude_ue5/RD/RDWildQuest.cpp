// Brokenspire's captain's two quests in the wilderness (2026-11-07; town.json's "wild:wolves" and "wild:patrol", offered as
// "later" until the gate opened): their places are FRDWildWorld::QuestPlaces (the Mill Road Den beside the road to
// Ashenreach, the Old Watchtower beside the road to Vel Morrath), laid out by RDWildPlaces.cpp. A quest's progress is read
// from the world's state, not a counter taken from when it was accepted (the castle's rule: a quest could otherwise ask for
// what is already done): the den's pack from the kills kept (WildKilled), the patrol from the find (a counter set once).
#include "RD/RDDungeonGenerator.h"
#include "RD/RDWild.h"
#include "RD/RDMonster.h"
#include "RD/RDCombat.h"
#include "RD/RDGameInstance.h"
#include "Kismet/GameplayStatics.h"

DEFINE_LOG_CATEGORY_STATIC(LogRDWildQuest, Log, All);

namespace
{
	/** she finds the patrol within this of their remains (metres) */
	constexpr double RDWQFindM = 6.0;
	/** the remains lie this far before the watchtower's doorway (metres; the tower's ring is about 4 m across) */
	constexpr double RDWQRemainsM = 7.0;
}

FVector2D ARDDungeonGenerator::WildQuestRemainsAt(const FRDWildPlace& P) const
{
	const float A = FMath::DegreesToRadians(P.Yaw);
	return P.At + FVector2D(FMath::Cos(A), FMath::Sin(A)) * RDWQRemainsM;
}

int32 ARDDungeonGenerator::WildQuestProgress(const FString& Goal) const
{
	const URDGameInstance* GI = URDGameInstance::Of(this);
	if (!GI || !IsWildReady()) return GI ? FMath::Min(GI->GetCounter(Goal), 1) : 0;
	const FRDWildPlace* P = Wild->QuestPlaceFor(Goal);
	if (!P) return 0;
	if (P->Quest == TEXT("wolves"))
	{
		// (every one of the den's pack: their keys are the place's id x 16 + their index)
		const int32 N = WildQuestMonsters(*P);
		for (int32 I = 0; I < N; ++I) if (!GI->WildKilled.Contains((int64)P->Id * 16 + I)) return 0;
		return 1;
	}
	return FMath::Min(GI->GetCounter(Goal), 1);
}

void ARDDungeonGenerator::WildQuestOnKill(const ARDMonster* M)
{
	if (!M || M->WildKey < 0 || !IsWildReady()) return;
	const FRDWildPlace* P = Wild->QuestPlaceFor(TEXT("wild:wolves"));
	if (!P || M->WildKey / 16 != (int64)P->Id) return;
	URDGameInstance* GI = URDGameInstance::Of(this);
	if (!GI || GI->GetCounter(TEXT("wild:wolves")) > 0 || WildQuestProgress(TEXT("wild:wolves")) < 1) return;
	GI->CountMax(TEXT("wild:wolves"), 1);
	if (PlayerCombat) PlayerCombat->ShowMessage(TEXT("The Mill Road's pack is dead: the captain will want to hear it"));
	UE_LOG(LogRDWildQuest, Log, TEXT("RDQUEST wild:wolves done: the %s's pack killed"), *P->Name);
}

void ARDDungeonGenerator::TickWildQuests(const FVector2D& AtM)
{
	if (!IsWildReady()) return;
	URDGameInstance* GI = URDGameInstance::Of(this);
	if (!GI || GI->GetCounter(TEXT("wild:patrol")) > 0) return;
	const FRDWildPlace* P = Wild->QuestPlaceFor(TEXT("wild:patrol"));
	if (!P || FVector2D::Distance(WildQuestRemainsAt(*P), AtM) > RDWQFindM) return;
	if (!PlayerCombat || PlayerCombat->IsDead()) return;
	GI->CountMax(TEXT("wild:patrol"), 1);
	PlayerCombat->ShowMessage(TEXT("The lost patrol: five of the watch, dead before the old watchtower's door"));
	UE_LOG(LogRDWildQuest, Log, TEXT("RDQUEST wild:patrol done: the remains found at %s (%.0f, %.0f)"), *P->Name, P->At.X, P->At.Y);
}

bool ARDDungeonGenerator::IsWildQuestShown(int32 PlaceId) const
{
	if (!IsWildReady() || PlaceId < FRDWildWorld::QuestIdBase || PlaceId >= FRDWildWorld::TownIdBase) return false;
	const URDGameInstance* GI = URDGameInstance::Of(this);
	if (!GI) return false;
	for (const FRDQuestDef& Q : Quests)
	{
		const FRDWildPlace* P = Wild->QuestPlaceFor(Q.Goal);
		if (!P || P->Id != PlaceId) continue;
		const FRDQuestState* St = GI->FindQuest(Q.Id);
		if (St && St->State == 1) return true;
	}
	return false;
}

TArray<FString> ARDDungeonGenerator::GetWildQuestLines() const
{
	TArray<FString> Out;
	if (!IsWildReady()) return Out;
	const URDGameInstance* GI = URDGameInstance::Of(this);
	for (const FRDWildPlace& P : Wild->QuestPlaces)
	{
		const FString Goal = TEXT("wild:") + P.Quest;
		const int32 N = WildQuestMonsters(P);
		int32 Killed = 0;
		if (GI) for (int32 I = 0; I < 16; ++I) if (GI->WildKilled.Contains((int64)P.Id * 16 + I)) ++Killed;
		const FVector2D Rm = P.Quest == TEXT("patrol") ? WildQuestRemainsAt(P) : P.At;
		Out.Add(FString::Printf(TEXT("%s|%d|%s|%.1f|%.1f|%s|%d|%d|%d|%.1f|%.1f|%.1f|%d"), *Goal, P.Id, *P.Name, P.At.X, P.At.Y, *P.Kind, N, Killed, WildQuestProgress(Goal),
			Rm.X, Rm.Y, P.Yaw, IsWildQuestShown(P.Id) ? 1 : 0));
	}
	return Out;
}
