// The list of 2026-11-12's fifth phase: the quests found in the wilds ("add these quest types that can be found in the wilderness
// ... implement these quests for the locations above": a monster bounty, a lair clearing, a legendary hunt, an infestation, hold the
// pass, a survey, a lost ruin, a buried cache, a lost expedition, trailblazing, a rare ingredient, a live capture, taming a mount,
// search and rescue, an escort, a manhunt, an urgent delivery, stranded, weathering a disaster, an investigation, a restless spirit,
// a blight's cleansing, a sacred site, a territory dispute, a frontier outpost, each with its twist). A structure holds one quest
// (its kind's Quests, by its id: WildSiteQuestOf); its giver stands there. A quest is its stages (FRDWildQuestDef::Stages, the
// key=value lines of SourceArt/wilderness/quests12.json, 924 quests), done the way a player does them: F on a person or a thing,
// coming to a point, killing what it sends, keeping someone alive on the way, at an hour, in a storm. Its state is in the game
// instance's counters (saved): "wq12:<site>" the stage (1 the first; 90 done, 91 failed), ":p" its progress, ":c" a choice.
#include "RD/RDDungeonGenerator.h"
#include "RD/RDWild.h"
#include "RD/RDGameInstance.h"
#include "RD/RDCombat.h"
#include "RD/RDMonster.h"
#include "RD/RDSection.h"
#include "RD/RDTown.h"
#include "Components/StaticMeshComponent.h"
#include "Engine/StaticMesh.h"
#include "Kismet/GameplayStatics.h"
#include "GameFramework/Character.h"
#include "RD/RDHorse.h"

DEFINE_LOG_CATEGORY_STATIC(LogRDQuest12, Log, All);

namespace
{
	TMap<FString, FString> RDQ12Parse(const FString& Line)
	{
		TMap<FString, FString> Out;
		TArray<FString> Kv; Line.ParseIntoArray(Kv, TEXT(";"), true);
		for (const FString& S : Kv) { FString K, V; if (S.Split(TEXT("="), &K, &V)) Out.Add(K.TrimStartAndEnd(), V.TrimStartAndEnd()); }
		return Out;
	}
	int32 RDQ12Int(const TMap<FString, FString>& M, const TCHAR* K, int32 Def) { const FString* V = M.Find(K); return V && !V->IsEmpty() ? FCString::Atoi(**V) : Def; }
	float RDQ12Num(const TMap<FString, FString>& M, const TCHAR* K, float Def) { const FString* V = M.Find(K); return V && !V->IsEmpty() ? FCString::Atof(**V) : Def; }
	constexpr int32 RDQ12Done = 90, RDQ12Failed = 91;
	/** "the hunter" / "a pilgrim" as said */
	FString RDQ12The(const FString& T) { const bool bArt = T.StartsWith(TEXT("a ")) || T.StartsWith(TEXT("an ")) || T.StartsWith(TEXT("the ")); return bArt ? T.Left(1).ToUpper() + T.Mid(1) : TEXT("The ") + T.ToLower(); }
}

// ------------------------------------------------------------------------------------------------ state
int32 ARDDungeonGenerator::WildQuestStage(int32 Site) const
{
	const URDGameInstance* GI = URDGameInstance::Of(this);
	return GI ? GI->GetCounter(FString::Printf(TEXT("wq12:%d"), Site)) : 0;
}

void ARDDungeonGenerator::SetWildQuestStage(FQuestRun& Run, int32 Stage)
{
	URDGameInstance* GI = URDGameInstance::Of(this);
	if (!GI) return;
	GI->Counters.Add(FString::Printf(TEXT("wq12:%d"), Run.Site), Stage);
	GI->Counters.Add(FString::Printf(TEXT("wq12:%d:p"), Run.Site), 0);
	Run.Stage = Stage; Run.Progress = 0; Run.bBegun = false; Run.StageAt = GetWorld()->GetTimeSeconds();
	ClearQuestStageActors(Run);
}

const FRDWildQuestDef* ARDDungeonGenerator::QuestOfRun(const FQuestRun& Run) const
{
	return WildQuests.IsValidIndex(Run.Quest) ? &WildQuests[Run.Quest] : nullptr;
}

void ARDDungeonGenerator::ClearQuestStageActors(FQuestRun& Run)
{
	for (const TWeakObjectPtr<ARDMonster>& W : Run.Mons) if (ARDMonster* M = W.Get(); M && !M->IsDead()) M->Destroy();
	Run.Mons.Reset();
	for (FQuestThing& T : Run.Things) if (UStaticMeshComponent* C = T.Mesh.Get()) C->DestroyComponent();
	Run.Things.Reset();
	// (PR #58's review: a wild horse not tamed goes with the stage (laid again, a new one was made and the old one left), and a
	// storm the stage held is let go (left held, it stood over the whole world))
	if (ARDHorse* Hz = Cast<ARDHorse>(Run.Horse.Get()); Hz && !Hz->bHers) Hz->Destroy();
	Run.Horse = nullptr;
	if (Run.bHeldWeather) { Run.bHeldWeather = false; SetWeatherNamed(TEXT("auto"), false); }
	// (the quest's people stay through its stages: the boy found is the boy walked home, the side chosen the one followed)
	Run.Folk.RemoveAll([](const TWeakObjectPtr<ARDTownsfolk>& W) { return !W.IsValid(); });
}

const TMap<FString, FString>& ARDDungeonGenerator::QuestStageSpec(FQuestRun& Run)
{
	if (Run.MStage != Run.Stage)
	{
		const FRDWildQuestDef* Q = QuestOfRun(Run);
		Run.M = Q && Q->Stages.IsValidIndex(Run.Stage - 1) ? RDQ12Parse(Q->Stages[Run.Stage - 1]) : TMap<FString, FString>();
		Run.MStage = Run.Stage;
	}
	return Run.M;
}

ARDMonster* ARDDungeonGenerator::SpawnWildMonsterAt(const FRDMonsterDef& Def, const FVector& Ground, float Yaw, int32 Seed, int32 Tier, float Hp, const FString& Named)
{
	ARDSection* Ws = EnsureWildSection();
	if (!Ws) return nullptr;
	const FVector L(Ground.X, Ground.Y, Ground.Z + Def.CapsuleHalfHeight + 10.f);
	FActorSpawnParameters Sp; Sp.SpawnCollisionHandlingOverride = ESpawnActorCollisionHandlingMethod::AdjustIfPossibleButAlwaysSpawn;
	ARDMonster* M = GetWorld()->SpawnActor<ARDMonster>(ARDMonster::StaticClass(), FTransform(FRotator(0, Yaw, 0), L), Sp);
	if (!M) return nullptr;
	M->SpawnIndex = -1; M->bOpenGround = true; M->HomeAt = L; M->WildKey = -1;
	M->Setup(Ws, Def, Seed);
	M->Empower(Tier, Hp, 1.f, 1.f, Named);
	Ws->SpawnedMonsters.Add(M);
	return M;
}

// ------------------------------------------------------------------------------------------------ points
FVector2D ARDDungeonGenerator::QuestPoint(const FQuestRun& Run, const FString& Spec, int32 Salt) const
{
	const FVector2D O = Run.P.At;
	if (!Wild) return O;
	const uint32 H = FRDWildWorld::Hash(Run.Site, 0x7000 + Salt, Wild->Seed);
	const float A0 = (H & 0xFFFF) / 65536.f * 2.f * PI;
	auto Gentle = [&](const FVector2D& Q)
	{
		FRDWSample S; Wild->Sample(Q.X, Q.Y, S, false);
		if (S.WaterKind != 0 || S.Road > 0.2f) return false;
		return WildLairRelief(Q) < 3.f;
	};
	// (the quest's own far point: one way from the structure, 250 to 450 m, on gentle dry ground)
	auto Far = [&]()
	{
		const uint32 Hf = FRDWildWorld::Hash(Run.Site, 0x7FFF, Wild->Seed);
		const float Af = (Hf & 0xFFFF) / 65536.f * 2.f * PI;
		for (int32 K = 0; K < 12; ++K)
			for (const float Rr : { 320.f, 260.f, 400.f, 450.f })
			{
				const float A = Af + K * PI / 6.f;
				const FVector2D Q = O + FVector2D(FMath::Cos(A), FMath::Sin(A)) * Rr;
				if (Gentle(Q)) return Q;
			}
		return O + FVector2D(FMath::Cos(Af), FMath::Sin(Af)) * 320.f;
	};
	if (Spec == TEXT("site")) return O;
	if (Spec == TEXT("near"))
	{
		for (int32 K = 0; K < 8; ++K) { const FVector2D Q = O + FVector2D(FMath::Cos(A0 + K * PI / 4.f), FMath::Sin(A0 + K * PI / 4.f)) * 32.f; if (Gentle(Q)) return Q; }
		return O + FVector2D(FMath::Cos(A0), FMath::Sin(A0)) * 32.f;
	}
	if (Spec == TEXT("far")) return Far();
	if (Spec.StartsWith(TEXT("trail")))
	{
		// (trail:i/n: the i-th of n points on the way out to the far point, a little off its line)
		FString L, Rt; int32 I = 1, N = 3;
		if (Spec.Split(TEXT(":"), &L, &Rt)) { FString A, B; if (Rt.Split(TEXT("/"), &A, &B)) { I = FCString::Atoi(*A); N = FMath::Max(1, FCString::Atoi(*B)); } }
		const FVector2D F = Far();
		const FVector2D Side = FVector2D(-(F - O).Y, (F - O).X).GetSafeNormal();
		FVector2D Q = FMath::Lerp(O, F, I / float(N + 1)) + Side * ((I % 2) ? 18.f : -18.f);
		for (int32 K = 0; K < 6 && !Gentle(Q); ++K) Q += Side * 6.f;
		return Q;
	}
	if (Spec == TEXT("town"))
	{
		double D = 0.0; const int32 Ti = Wild->NearestTown(O.X, O.Y, D);
		return Wild->Towns.IsValidIndex(Ti) ? Wild->Towns[Ti].Site : O;
	}
	if (Spec == TEXT("water"))
	{
		// (rings every 20 m out to 2 km, 24 ways: a stream is a few metres wide, and a structure of the plains may have none
		// within 600 m)
		for (float Rr = 20.f; Rr <= 2000.f; Rr += 20.f)
			for (int32 K = 0; K < 24; ++K)
			{
				const FVector2D Q = O + FVector2D(FMath::Cos(A0 + K * PI / 12.f), FMath::Sin(A0 + K * PI / 12.f)) * Rr;
				FRDWSample S; Wild->Sample(Q.X, Q.Y, S, false);
				if (S.WaterKind != 0 && S.Water > S.H)
				{
					// (its edge: back toward the structure to the first dry ground)
					const FVector2D Way = (O - Q).GetSafeNormal(); FVector2D E = Q;
					for (int32 St = 0; St < 40; ++St) { E += Way; FRDWSample Se; Wild->Sample(E.X, E.Y, Se, false); if (Se.WaterKind == 0 || Se.Water <= Se.H) break; }
					return E + Way * 2.f;
				}
			}
		return O;
	}
	if (Spec.StartsWith(TEXT("shelter")) || Spec.StartsWith(TEXT("place:")))
	{
		// (the nearest place of a kind (a shelter: a cave, a house, a village or a camp, 100 m to 1.5 km off: one by the structure
		// was reached at once, a storm weathered where it began, and one 4.9 km off was no run before a storm; "shelter5" within
		// 5 km, the stranded's night) a named kind within 25 km (the ruins are one in about 100 square km: the nearest of one
		// structure's was 12.2 km off), else the structure itself; a ruin by its laid middle, which may lie off its place)
		const bool bShelter = Spec.StartsWith(TEXT("shelter"));
		FString Kind = bShelter ? FString() : Spec.Mid(6);
		const float Km = bShelter ? (Spec.Len() > 7 ? FCString::Atof(*Spec.Mid(7)) : 1.5f) : 25.f;
		FRDWildPlace Got; FVector2D At;
		if (FindNearestWildPlace(O.X, O.Y, Km, [&](const FRDWildPlace& P, FVector2D& A)
			{
				if (Kind.IsEmpty() ? ((P.Kind != TEXT("cave") && P.Kind != TEXT("house") && P.Kind != TEXT("village") && P.Kind != TEXT("camp")) || FVector2D::Distance(P.At, O) < 100.f) : P.Kind != Kind) return false;
				A = P.Kind == TEXT("ruins") ? WildRuinCentre(P) : P.At; return true;
			}, Got, At)) return At;
		return O;
	}
	return O;
}

// ------------------------------------------------------------------------------------------------ the people and the things
ARDTownsfolk* ARDDungeonGenerator::SpawnQuestFolk(FQuestRun& Run, FName QRole, const FString& Title, const FString& Def, const TArray<FString>& Lines, const FVector2D& At)
{
	if (Townsfolk.Num() == 0) return nullptr;
	int32 D = Townsfolk.IndexOfByPredicate([&](const FRDTownsfolkDef& X) { return X.Mesh && !Def.IsEmpty() && X.Name.ToString().StartsWith(Def); });
	if (D < 0) D = Townsfolk.IndexOfByPredicate([&](const FRDTownsfolkDef& X) { return X.Mesh && X.Name.ToString().StartsWith(TEXT("Townsman")); });
	if (D < 0) return nullptr;
	FRandomStream Rs((int32)HashCombine((uint32)Run.Site, GetTypeHash(QRole)));
	const float Yaw = Rs.FRandRange(0.f, 360.f);
	const FVector Q(At.X * 100.0, At.Y * 100.0, WildGroundZ(FVector(At.X * 100.0, At.Y * 100.0, 0.0)) + 92.f);
	FActorSpawnParameters Sp; Sp.SpawnCollisionHandlingOverride = ESpawnActorCollisionHandlingMethod::AlwaysSpawn;
	ARDTownsfolk* T = GetWorld()->SpawnActor<ARDTownsfolk>(ARDTownsfolk::StaticClass(), FTransform(FRotator(0, Yaw, 0), Q), Sp);
	if (!T) return nullptr;
	T->Init(this, nullptr, D, Q, Yaw, 0.f, Rs.GetUnsignedInt());
	T->SetTitle(Title);
	T->OwnLines = Lines;
	T->WildQuestSite = Run.Site; T->WildQuestRole = QRole;
	T->bWildGiven = true;          // (no gift: what a quest gives it gives at its end)
	Run.Folk.Add(T);
	WildSiteFolk.Add(T);
	return T;
}

void ARDDungeonGenerator::SpawnQuestThing(FQuestRun& Run, const FString& Prefix, const FVector2D& At, float HeightM, FName Item)
{
	TArray<UStaticMesh*> Ms; WildPiecesOf(Prefix, Ms);
	ARDWildChunk* C = WildChunkAtCm(FVector2D(At.X * 100.0, At.Y * 100.0));
	FQuestThing Th; Th.At = FVector(At.X * 100.0, At.Y * 100.0, WildGroundZ(FVector(At.X * 100.0, At.Y * 100.0, 0.0))); Th.Item = Item;
	if (C && Ms.Num() > 0)
	{
		UStaticMesh* M = Ms[FRDWildWorld::Hash(Run.Site, Run.Things.Num(), 17u) % (uint32)Ms.Num()];
		const float Bh = FMath::Max((float)M->GetBoundingBox().GetSize().Z, 1.f);
		Th.Mesh = LayRuinPiece(C, M, Th.At, FRotator(0.f, (float)(GetTypeHash(At.X) % 360), 0.f), FVector(HeightM * 100.f / Bh), 2.f, false);
	}
	Run.Things.Add(Th);
}

void ARDDungeonGenerator::SpawnQuestMonsters(FQuestRun& Run, int32 N, const FString& KindSpec, const FString& Named, float Hp, const FVector2D& At, float Ring)
{
	if (!bCombat || Monsters.Num() == 0) return;
	ARDSection* Ws = EnsureWildSection();
	if (!Ws) return;
	TArray<int32> Kinds; WildKindsForTier(Run.P.Tier, Kinds);
	if (!KindSpec.IsEmpty())
	{
		TArray<int32> Named2;
		for (int32 K = 0; K < Monsters.Num(); ++K) if (Monsters[K].Mesh && Monsters[K].Name.ToString().Contains(KindSpec)) Named2.Add(K);
		if (Named2.Num() > 0) Kinds = Named2;
	}
	if (Kinds.Num() == 0) return;
	FRandomStream R((int32)FRDWildWorld::Hash(Run.Site, 0x7100 + Run.Stage * 16 + Run.Mons.Num(), Wild ? Wild->Seed : 0u));
	const FRDMonsterDef& Def = Monsters[Kinds[R.RandRange(0, Kinds.Num() - 1)]];
	// (by the difficulty, as the places' and the director's: hell's quarter more (PR #58's review))
	for (int32 I = 0; I < DifficultyCount(N); ++I)
	{
		const float A = R.FRandRange(0.f, 2.f * PI), D = Ring > 0.f ? Ring * 100.f : R.FRandRange(150.f, 600.f);
		FVector L(At.X * 100.0 + FMath::Cos(A) * D, At.Y * 100.0 + FMath::Sin(A) * D, 0.0);
		L.Z = WildGroundZ(L);
		const float Yaw = R.FRandRange(0.f, 360.f);
		const int32 Seed = (int32)R.GetUnsignedInt();
		if (ARDMonster* M = SpawnWildMonsterAt(Def, L, Yaw, Seed, Run.P.Tier, Hp, Named)) Run.Mons.Add(M);
	}
}

// ------------------------------------------------------------------------------------------------ a structure's quest laid with it
void ARDDungeonGenerator::QuestSiteLaid(const FRDWildPlace& P)
{
	const FName Qn = WildSiteQuestOf(P);
	const int32 Qi = WildQuests.IndexOfByPredicate([&](const FRDWildQuestDef& Q) { return Q.Name == Qn; });
	if (Qi < 0) return;
	FQuestRun& Run = WildQuestRuns.FindOrAdd(P.Id);
	const bool bNew = Run.Site == 0;
	Run.Site = P.Id; Run.P = P; Run.Quest = Qi;
	const URDGameInstance* GI = URDGameInstance::Of(this);
	// (stranded: the quest goes on from the shore she woke on, not the structure (PR #58's review: laid again, the structure's
	// place undid it); kept in the counters, so a load keeps it too)
	if (GI && GI->Counters.Contains(FString::Printf(TEXT("wq12:%d:sx"), P.Id)))
	{
		Run.P.At = FVector2D(GI->GetCounter(FString::Printf(TEXT("wq12:%d:sx"), P.Id)), GI->GetCounter(FString::Printf(TEXT("wq12:%d:sy"), P.Id)));
		Run.bStrandedAway = WildQuestStage(P.Id) < RDQ12Done;
	}
	Run.Stage = WildQuestStage(P.Id);
	Run.Progress = GI ? GI->GetCounter(FString::Printf(TEXT("wq12:%d:p"), P.Id)) : 0;
	Run.Choice = GI ? GI->GetCounter(FString::Printf(TEXT("wq12:%d:c"), P.Id)) : 0;
	if (Run.Stage >= RDQ12Done) return;
	// (its giver at the structure, made again with its chunk (the chunk's people go with it))
	Run.Folk.RemoveAll([](const TWeakObjectPtr<ARDTownsfolk>& W) { return !W.IsValid(); });
	if (!Run.Folk.ContainsByPredicate([](const TWeakObjectPtr<ARDTownsfolk>& W) { return W->WildQuestRole == TEXT("giver"); }))
	{
		const FRDWildQuestDef& Q = WildQuests[Qi];
		const float A = FMath::DegreesToRadians(P.Yaw);
		SpawnQuestFolk(Run, TEXT("giver"), Q.GiverTitle, Q.Giver, { Q.Offer }, P.At + FVector2D(FMath::Cos(A), FMath::Sin(A)) * 9.f);
	}
	// (a stage under way: what it laid before is taken away (PR #58's review: laid again on top of it, a choice had two pairs,
	// a tame two horses), then laid again as she comes; its one-time start (a deadline, the delivery's medicine) is not redone)
	if (!bNew && Run.bBegun) { ClearQuestStageActors(Run); Run.bBegun = false; }
}

// ------------------------------------------------------------------------------------------------ F
FString ARDDungeonGenerator::WildQuestTalk(ARDTownsfolk* T)
{
	if (!T || T->WildQuestSite == 0) return FString();
	FQuestRun* Run = WildQuestRuns.Find(T->WildQuestSite);
	const FRDWildQuestDef* Q = Run ? QuestOfRun(*Run) : nullptr;
	if (!Run || !Q) return FString();
	const FString Who = RDQ12The(T->Title);
	// (the giver: the quest taken; after it, the stage's line)
	if (T->WildQuestRole == TEXT("giver") && Run->Stage == 0)
	{
		SetWildQuestStage(*Run, 1);
		// (its first stage begun at once: its point and marker are there as the quest is taken, not a tick later (a player
		// who set off at once could leave its 4 km before it began, and it never would))
		if (Q->Stages.IsValidIndex(0)) BeginWildQuestStage(*Run, RDQ12Parse(Q->Stages[0]));
		if (PlayerCombat) PlayerCombat->ShowMessage(FString::Printf(TEXT("%s:  \"%s\"  (quest: %s)"), *Who, *Q->Offer, *Q->Title));
		UE_LOG(LogRDQuest12, Log, TEXT("RDQUEST12 %s taken at %s (%d)"), *Q->Name.ToString(), *T->Title, T->WildQuestSite);
		return TEXT("quest");
	}
	if (Run->Stage < 1 || Run->Stage >= RDQ12Done || !Q->Stages.IsValidIndex(Run->Stage - 1)) return FString();
	const TMap<FString, FString> M = QuestStageSpec(*Run);
	const FString Do = M.FindRef(TEXT("do"));
	// (a talk: the one it names; a choice: either side, which is the choice)
	if ((Do == TEXT("talk") && T->WildQuestRole == FName(*M.FindRef(TEXT("who")))) || (Do == TEXT("choose") && (T->WildQuestRole == TEXT("a") || T->WildQuestRole == TEXT("b"))))
	{
		if (Do == TEXT("choose"))
		{
			Run->Choice = T->WildQuestRole == TEXT("a") ? 1 : 2;
			if (URDGameInstance* GI = URDGameInstance::Of(this)) GI->Counters.Add(FString::Printf(TEXT("wq12:%d:c"), Run->Site), Run->Choice);
		}
		const FString Say = M.FindRef(Do == TEXT("choose") ? (Run->Choice == 1 ? TEXT("say_a") : TEXT("say_b")) : TEXT("line"));
		if (PlayerCombat && !Say.IsEmpty()) PlayerCombat->ShowMessage(FString::Printf(TEXT("%s:  \"%s\""), *Who, *Say));
		AdvanceWildQuest(*Run);
		return TEXT("quest");
	}
	// (an escort's or a delivery's person at its end)
	if (Do == TEXT("deliver") && T->WildQuestRole == FName(*M.FindRef(TEXT("who"))) && Run->Progress > 0) { AdvanceWildQuest(*Run); return TEXT("quest"); }
	return FString();
}

FString ARDDungeonGenerator::WildQuestInteract(const FVector& From)
{
	// (a quest's thing within reach: a clue, a flower, a nest, a grave, the stones; the nearest)
	for (auto& Kv : WildQuestRuns)
	{
		FQuestRun& Run = Kv.Value;
		const FRDWildQuestDef* Q = QuestOfRun(Run);
		if (!Q || Run.Stage < 1 || Run.Stage >= RDQ12Done || !Q->Stages.IsValidIndex(Run.Stage - 1)) continue;
		const TMap<FString, FString>& M = QuestStageSpec(Run);
		const FString Do = M.FindRef(TEXT("do"));
		for (FQuestThing& Th : Run.Things)
		{
			if (Th.bTaken || FVector::Dist2D(Th.At, From) > 230.f || FMath::Abs(Th.At.Z - From.Z) > 250.f) continue;
			// (only at its hours: the flower at night, the rite at dawn)
			if (const FString* Hr = M.Find(TEXT("hours")))
			{
				FString A, B; Hr->Split(TEXT("-"), &A, &B);
				const float H0 = FCString::Atof(*A), H1 = FCString::Atof(*B), Now = GetTownHour();
				const bool bIn = H0 <= H1 ? (Now >= H0 && Now < H1) : (Now >= H0 || Now < H1);
				if (!bIn) { if (PlayerCombat) PlayerCombat->ShowMessage(M.FindRef(TEXT("not_now"))); return TEXT("quest_wait"); }
			}
			if (Do == TEXT("capture")) continue;
			Th.bTaken = true;
			if (UStaticMeshComponent* C = Th.Mesh.Get()) { C->SetVisibility(false); C->SetCollisionEnabled(ECollisionEnabled::NoCollision); }
			if (!Th.Item.IsNone() && PlayerCombat && FindItem(Th.Item) >= 0) PlayerCombat->AddItem(Th.Item, 1);
			++Run.Progress;
			if (URDGameInstance* GI = URDGameInstance::Of(this)) GI->Counters.Add(FString::Printf(TEXT("wq12:%d:p"), Run.Site), Run.Progress);
			if (PlayerCombat) PlayerCombat->ShowMessage(FString::Printf(TEXT("%s (%d of %d)"), *M.FindRef(TEXT("take")), Run.Progress, RDQ12Int(M, TEXT("n"), 1)));
			PlaySoundAt(TEXT("Player.Loot"), Th.At);
			return TEXT("quest_thing");
		}
		// (a capture: the beast beaten down within reach, bound)
		if (Do == TEXT("capture"))
			for (const TWeakObjectPtr<ARDMonster>& W : Run.Mons)
				if (ARDMonster* Mo = W.Get(); Mo && !Mo->IsDead() && Mo->GetHealth() <= Mo->GetMaxHealth() * 0.3f && FVector::Dist2D(Mo->GetActorLocation(), From) < 300.f)
				{
					Mo->Destroy();
					if (PlayerCombat) PlayerCombat->ShowMessage(M.FindRef(TEXT("take")));
					AdvanceWildQuest(Run);
					return TEXT("quest_capture");
				}
		// (a tamed horse: walked up to, not run at, three times)
		if (Do == TEXT("tame"))
			if (AActor* Hz = Run.Horse.Get(); Hz && FVector::Dist2D(Hz->GetActorLocation(), From) < 320.f)
			{
				const APawn* Her = UGameplayStatics::GetPlayerPawn(this, 0);
				if (Her && Her->GetVelocity().Size2D() > 260.f) { if (PlayerCombat) PlayerCombat->ShowMessage(TEXT("The horse shies away from you: come to it slowly")); return TEXT("quest_wait"); }
				++Run.Progress;
				if (PlayerCombat) PlayerCombat->ShowMessage(FString::Printf(TEXT("%s (%d of 3)"), Run.Progress >= 3 ? TEXT("The horse lets you mount it: it is yours") : TEXT("The horse lets you near and eats from your hand"), Run.Progress));
				if (Run.Progress >= 3) { TameWildHorse(Run); AdvanceWildQuest(Run); }
				return TEXT("quest_tame");
			}
	}
	return FString();
}

// ------------------------------------------------------------------------------------------------ the stages
void ARDDungeonGenerator::AdvanceWildQuest(FQuestRun& Run)
{
	const FRDWildQuestDef* Q = QuestOfRun(Run);
	if (!Q) return;
	// (the next stage of this branch: one marked for the other choice is passed by)
	int32 Next = Run.Stage + 1;
	while (Q->Stages.IsValidIndex(Next - 1))
	{
		const FString If = RDQ12Parse(Q->Stages[Next - 1]).FindRef(TEXT("if"));
		if (If.IsEmpty() || (If == TEXT("a") && Run.Choice == 1) || (If == TEXT("b") && Run.Choice == 2)) break;
		++Next;
	}
	UE_LOG(LogRDQuest12, Log, TEXT("RDQUEST12 %s at %d: stage %d done"), *Q->Name.ToString(), Run.Site, Run.Stage);
	if (!Q->Stages.IsValidIndex(Next - 1)) { FinishWildQuest(Run, true); return; }
	SetWildQuestStage(Run, Next);
}

void ARDDungeonGenerator::FinishWildQuest(FQuestRun& Run, bool bWon)
{
	const FRDWildQuestDef* Q = QuestOfRun(Run);
	SetWildQuestStage(Run, bWon ? RDQ12Done : RDQ12Failed);
	Run.bStrandedAway = false;          // (PR #58's review: the leash holds again once the quest is over)
	if (!Q) return;
	if (bWon)
	{
		const int32 Gold = WildGoldAt(Q->Gold, FVector(Run.P.At.X * 100.0, Run.P.At.Y * 100.0, 0.0));
		if (Gold > 0) AddGold(Gold, Q->Title.ToLower());
		TArray<FString> Ts; Q->Things.ParseIntoArray(Ts, TEXT(";"), true);
		for (const FString& T : Ts) { FString Nm, Cn; if (!T.Split(TEXT("|"), &Nm, &Cn)) { Nm = T; Cn = TEXT("1"); } if (FindItem(FName(*Nm)) >= 0 && PlayerCombat) PlayerCombat->AddItem(FName(*Nm), FMath::Max(1, FCString::Atoi(*Cn))); }
		TownCount(TEXT("wild:quests"));
		if (PlayerCombat) PlayerCombat->ShowMessage(FString::Printf(TEXT("Quest done: %s (%d gold)"), *Q->Title, Gold));
		Run.GoldGiven = Gold;
	}
	else if (PlayerCombat) PlayerCombat->ShowMessage(FString::Printf(TEXT("Quest failed: %s"), *Q->Title));
	UE_LOG(LogRDQuest12, Log, TEXT("RDQUEST12 %s at %d: %s"), *Q->Name.ToString(), Run.Site, bWon ? TEXT("done") : TEXT("failed"));
	// (the giver thanks her and stays; the others go once the quest is over)
	for (int32 I = Run.Folk.Num() - 1; I >= 0; --I)
	{
		ARDTownsfolk* T = Run.Folk[I].Get();
		if (!T) { Run.Folk.RemoveAt(I); continue; }
		if (T->WildQuestRole == TEXT("giver")) { T->OwnLines = { TEXT("You have done more than I could ask."), TEXT("Safe roads to you.") }; T->bRoadWalker = false; continue; }
		T->Destroy(); Run.Folk.RemoveAt(I);
	}
}

void ARDDungeonGenerator::BeginWildQuestStage(FQuestRun& Run, const TMap<FString, FString>& M)
{
	Run.bBegun = true;
	// (PR #58's review: a stage is begun again each time it is laid again (she went more than 4 km off and came back, its
	// structure's chunk laid again, a load); what it lays is laid each time, its one-time start (a deadline, the delivery's
	// medicine, a defence's waves) only the first time, recorded in the counters ("wq12:<site>:s", the stage started))
	URDGameInstance* SGI = URDGameInstance::Of(this);
	const FString SKey = FString::Printf(TEXT("wq12:%d:s"), Run.Site);
	const bool bFirst = !SGI || SGI->GetCounter(SKey) != Run.Stage;
	if (SGI) SGI->Counters.Add(SKey, Run.Stage);
	const FString Do = M.FindRef(TEXT("do"));
	const FString At = M.Contains(TEXT("at")) ? M.FindRef(TEXT("at")) : FString(TEXT("site"));
	Run.Point = QuestPoint(Run, At, Run.Stage);
	const int32 N = RDQ12Int(M, TEXT("n"), 1);
	if (PlayerCombat && M.Contains(TEXT("say"))) PlayerCombat->ShowMessage(M.FindRef(TEXT("say")));
	if (Do == TEXT("talk"))
	{
		// (the one to speak to: the giver when it names them, else a person at the point)
		const FName Who(*M.FindRef(TEXT("who")));
		if (Who != TEXT("giver") && !Run.Folk.ContainsByPredicate([&](const TWeakObjectPtr<ARDTownsfolk>& W) { return W.IsValid() && W->WildQuestRole == Who; }))
			SpawnQuestFolk(Run, Who, M.FindRef(TEXT("title")), M.FindRef(TEXT("def")), { M.FindRef(TEXT("line")) }, Run.Point);
	}
	else if (Do == TEXT("choose"))
	{
		// (each side made only if not standing already)
		const FVector2D Side = FVector2D(-(Run.Point - Run.P.At).Y, (Run.Point - Run.P.At).X).GetSafeNormal() * 4.f;
		auto Has = [&](FName R) { return Run.Folk.ContainsByPredicate([&](const TWeakObjectPtr<ARDTownsfolk>& W) { return W.IsValid() && W->WildQuestRole == R; }); };
		if (!Has(TEXT("a"))) SpawnQuestFolk(Run, TEXT("a"), M.FindRef(TEXT("title_a")), M.FindRef(TEXT("def_a")), { M.FindRef(TEXT("line_a")) }, Run.Point + Side);
		if (!Has(TEXT("b"))) SpawnQuestFolk(Run, TEXT("b"), M.FindRef(TEXT("title_b")), M.FindRef(TEXT("def_b")), { M.FindRef(TEXT("line_b")) }, Run.Point - Side);
	}
	else if (Do == TEXT("kill") || Do == TEXT("capture"))
		SpawnQuestMonsters(Run, N, M.FindRef(TEXT("kind")), M.FindRef(TEXT("named")), RDQ12Num(M, TEXT("hp"), 1.f), Run.Point, 0.f);
	else if (Do == TEXT("collect") || Do == TEXT("rite") || Do == TEXT("cleanse"))
	{
		// (laid again: only what is left to take (a rite's or a cleansing's thing once taken stands as taken: its guardians come))
		if (Do != TEXT("collect") && Run.Progress >= 1) { FQuestThing Th; Th.At = FVector(Run.Point.X * 100.0, Run.Point.Y * 100.0, 0.0); Th.bTaken = true; Run.Things.Add(Th); }
		for (int32 I = Do == TEXT("collect") ? Run.Progress : (Run.Progress >= 1 ? 1 : 0); I < (Do == TEXT("collect") ? N : 1); ++I)
		{
			const float A = I * 2.f * PI / FMath::Max(N, 1) + 0.7f;
			SpawnQuestThing(Run, M.FindRef(TEXT("thing")), Run.Point + (Do == TEXT("collect") && N > 1 ? FVector2D(FMath::Cos(A), FMath::Sin(A)) * 6.f : FVector2D::ZeroVector), RDQ12Num(M, TEXT("h"), 0.6f), FName(*M.FindRef(TEXT("item"))));
		}
	}
	else if (Do == TEXT("escort"))
	{
		// (the one to bring: kept on through the stages after (a survivor walked home); they follow her)
		const FName Who(*M.FindRef(TEXT("who")));
		ARDTownsfolk* T = nullptr;
		for (const TWeakObjectPtr<ARDTownsfolk>& W : Run.Folk) if (W.IsValid() && W->WildQuestRole == Who) T = W.Get();
		Run.Point = QuestPoint(Run, M.Contains(TEXT("to")) ? M.FindRef(TEXT("to")) : FString(TEXT("site")), Run.Stage + 40);
		if (!T)
		{
			// (beside her, or where they wait when the end is where she stands (a shelter that is the structure itself: the family
			// out with their flock, to be brought in))
			FVector2D From = FVector2D(UGameplayStatics::GetPlayerPawn(this, 0)->GetActorLocation()) / 100.0 + FVector2D(2.f, 2.f);
			if (FVector2D::Distance(From, Run.Point) < 60.f) From = QuestPoint(Run, TEXT("far"), Run.Stage + 60);
			T = SpawnQuestFolk(Run, Who, M.FindRef(TEXT("title")), M.FindRef(TEXT("def")), { M.FindRef(TEXT("line")) }, From);
		}
		Run.Kept = T;
		if (T) T->bRoadWalker = true;
		Run.bAmbushed = false;
	}
	// (a defence's time starts when she is at its point (the tick): begun from afar (a load, her way back) it failed at once
	// for her being more than 60 m off (PR #58's review))
	else if (Do == TEXT("defend")) { if (bFirst) { Run.Deadline = 0.f; Run.Waves = 0; } }
	else if (Do == TEXT("deliver"))
	{
		// (the medicine given once; the time set once (a load sets it again: the clock is the session's))
		if (bFirst || Run.Deadline <= 0.f) Run.Deadline = GetWorld()->GetTimeSeconds() + RDQ12Num(M, TEXT("secs"), 720.f);
		if (bFirst && PlayerCombat && M.Contains(TEXT("item")) && FindItem(FName(*M.FindRef(TEXT("item")))) >= 0) PlayerCombat->AddItem(FName(*M.FindRef(TEXT("item"))), 1);
	}
	else if (Do == TEXT("survive"))
	{
		if (bFirst || Run.Deadline <= 0.f) Run.Deadline = GetWorld()->GetTimeSeconds() + RDQ12Num(M, TEXT("secs"), 120.f);
		if (M.Contains(TEXT("weather"))) { SetWeatherNamed(M.FindRef(TEXT("weather")), true); Run.bHeldWeather = true; }
	}
	else if (Do == TEXT("tame"))
	{
		if (bFirst) Run.Progress = 0;
		// (a wild horse, not hers (the stable's grey's coat), standing where the stage puts it)
		Run.Horse = SpawnHorseAt(FVector(Run.Point.X * 100.0, Run.Point.Y * 100.0, WildGroundZ(FVector(Run.Point.X * 100.0, Run.Point.Y * 100.0, 0.0))), Run.P.Yaw, false);
	}
	else if (Do == TEXT("strand"))
	{
		// (stranded: she wakes on a shore 1.5 km off with what she carries; the way back is hers to find)
		const FVector2D S = QuestPoint(Run, TEXT("water"), Run.Stage);
		const FVector2D Way = (S - Run.P.At).GetSafeNormal();
		FVector2D To = S + Way * 1500.f;
		for (int32 K = 0; K < 12; ++K)
		{
			FRDWSample Sq; Wild->Sample(To.X, To.Y, Sq, false);
			if (Sq.WaterKind == 0 && WildLairRelief(To) < 3.f) break;
			To = S + FVector2D(Way.X * FMath::Cos(K * 0.5f) - Way.Y * FMath::Sin(K * 0.5f), Way.X * FMath::Sin(K * 0.5f) + Way.Y * FMath::Cos(K * 0.5f)) * 1500.f;
		}
		// (she is put there at the next quest tick, not here: WildPutHer lays chunks, and a structure's chunk adds its run to
		// WildQuestRuns, which may move the run this holds (PR #58's review))
		bWildStrandPending = true; WildStrandTo = To;
		// (the quest goes on from where she woke: its next points are found round her there; kept for a load)
		Run.P.At = To; Run.bStrandedAway = true;
		if (SGI) { SGI->Counters.Add(FString::Printf(TEXT("wq12:%d:sx"), Run.Site), FMath::RoundToInt(To.X)); SGI->Counters.Add(FString::Printf(TEXT("wq12:%d:sy"), Run.Site), FMath::RoundToInt(To.Y)); }
		AdvanceWildQuest(Run);
		return;
	}
	else if (Do == TEXT("reward")) { FinishWildQuest(Run, true); return; }
}

void ARDDungeonGenerator::TickWildQuests12(float Dt, const FVector& Her)
{
	WildQuestLook -= Dt;
	// (the stranded put on her shore here, no run held)
	if (bWildStrandPending && IsWildReady()) { bWildStrandPending = false; WildPutHer(WildStrandTo.X, WildStrandTo.Y); return; }
	if (WildQuestLook > 0.f || !PlayerCombat || PlayerCombat->IsDead() || !IsWildReady()) return;
	WildQuestLook = 0.2f;
	const FVector2D H(Her.X / 100.0, Her.Y / 100.0);
	const float Now = GetWorld()->GetTimeSeconds();
	for (auto It = WildQuestRuns.CreateIterator(); It; ++It)
	{
		FQuestRun& Run = It.Value();
		const FRDWildQuestDef* Q = QuestOfRun(Run);
		// (far from her and not under way: its people go with their chunks; the run is kept for its state)
		if (!Q || Run.Stage < 1 || Run.Stage >= RDQ12Done || !Q->Stages.IsValidIndex(Run.Stage - 1)) continue;
		const TMap<FString, FString> M = QuestStageSpec(Run);
		const FString Do = M.FindRef(TEXT("do"));
		// (near: within 4 km of the structure or of the stage's own point (a ruin 9 km off is gone to from the structure, and
		// reached far from it); the point found once while the stage waits (PR #58's review: found five times a second, a water
		// search was 2,400 samples); a delivery runs wherever she is (its town is 8 km off and more: cleared half way, it was
		// given again and its time set again)
		if (!Run.bBegun && Run.PtStage != Run.Stage) { Run.PtWait = QuestPoint(Run, M.Contains(TEXT("at")) ? M.FindRef(TEXT("at")) : FString(TEXT("site")), Run.Stage); Run.PtStage = Run.Stage; }
		const FVector2D Pt = Run.bBegun ? Run.Point : Run.PtWait;
		const bool bRoams = Run.bStrandedAway || Do == TEXT("deliver");
		if (FVector2D::Distance(Run.P.At, H) > 4000.f && FVector2D::Distance(Pt, H) > 4000.f && !bRoams) { if (Run.bBegun) { ClearQuestStageActors(Run); Run.bBegun = false; } continue; }
		if (!Run.bBegun) BeginWildQuestStage(Run, M);
		if (Run.Stage >= RDQ12Done || !Run.bBegun) continue;
		// (the time since this run's last look: a storm's pause is the whole of it (PR #58's review: 0.2 s a look let the
		// storm's time run on outside at lower frame rates))
		const float Since = Run.LastLook >= 0.f ? Now - Run.LastLook : 0.2f;
		Run.LastLook = Now;
		const int32 N = RDQ12Int(M, TEXT("n"), 1);
		const float Reach = RDQ12Num(M, TEXT("r"), 10.f);
		if (Do == TEXT("goto"))
		{
			if (FVector2D::Distance(Run.Point, H) < Reach) { if (PlayerCombat && M.Contains(TEXT("found"))) PlayerCombat->ShowMessage(M.FindRef(TEXT("found"))); AdvanceWildQuest(Run); }
		}
		else if (Do == TEXT("kill"))
		{
			int32 Dead = 0, Gone = 0;
			for (const TWeakObjectPtr<ARDMonster>& W : Run.Mons) { const ARDMonster* Mo = W.Get(); if (!Mo) ++Gone; else if (Mo->IsDead()) ++Dead; }
			if (Run.Mons.Num() > 0 && Dead + Gone >= Run.Mons.Num() && Dead > 0) { if (PlayerCombat && M.Contains(TEXT("done"))) PlayerCombat->ShowMessage(M.FindRef(TEXT("done"))); AdvanceWildQuest(Run); }
			else if (Run.Mons.Num() == 0 || (Gone > 0 && Dead == 0 && Gone == Run.Mons.Num())) { Run.Mons.Reset(); SpawnQuestMonsters(Run, N, M.FindRef(TEXT("kind")), M.FindRef(TEXT("named")), RDQ12Num(M, TEXT("hp"), 1.f), Run.Point, 0.f); }
		}
		else if (Do == TEXT("collect"))
		{
			if (Run.Progress >= N) AdvanceWildQuest(Run);
		}
		else if (Do == TEXT("rite") || Do == TEXT("cleanse"))
		{
			// (the stones touched or the source cleansed (the thing taken): its guardians come, the stage ends when they are dead)
			if (Run.Things.Num() > 0 && Run.Things[0].bTaken)
			{
				if (Run.Mons.Num() == 0 && RDQ12Int(M, TEXT("guards"), 0) > 0) SpawnQuestMonsters(Run, RDQ12Int(M, TEXT("guards"), 0), M.FindRef(TEXT("kind")), M.FindRef(TEXT("named")), 1.f, Run.Point, 8.f);
				const bool bAll = !Run.Mons.ContainsByPredicate([](const TWeakObjectPtr<ARDMonster>& W) { return W.IsValid() && !W->IsDead(); });
				if (bAll) { if (PlayerCombat && M.Contains(TEXT("done"))) PlayerCombat->ShowMessage(M.FindRef(TEXT("done"))); AdvanceWildQuest(Run); }
			}
		}
		else if (Do == TEXT("escort"))
		{
			ARDTownsfolk* T = Run.Kept.Get();
			if (!T) { FinishWildQuest(Run, false); continue; }
			// (they follow her a few metres behind; an ambush half way; they are safe within 10 m of the end)
			const FVector Tl = T->GetActorLocation();
			if (FVector::Dist2D(Tl, Her) > 400.f) { T->RoadPath = { Her - (Her - Tl).GetSafeNormal2D() * 250.f }; }
			else T->RoadPath.Reset();
			const float Total = FVector2D::Distance(Run.P.At, Run.Point);
			if (!Run.bAmbushed && RDQ12Int(M, TEXT("ambush"), 0) > 0 && FVector2D::Distance(FVector2D(Tl) / 100.0, Run.Point) < Total * 0.55f)
			{
				Run.bAmbushed = true;
				SpawnQuestMonsters(Run, RDQ12Int(M, TEXT("ambush"), 0), M.FindRef(TEXT("kind")), M.FindRef(TEXT("named")), 1.f, FVector2D(Tl) / 100.0, 14.f);
				for (const TWeakObjectPtr<ARDMonster>& W : Run.Mons) if (ARDMonster* Mo = W.Get()) { Mo->bHunting = true; Mo->HuntUntil = Now + 60.f; }
				if (PlayerCombat && M.Contains(TEXT("ambush_say"))) PlayerCombat->ShowMessage(M.FindRef(TEXT("ambush_say")));
			}
			const bool bFoes = Run.Mons.ContainsByPredicate([](const TWeakObjectPtr<ARDMonster>& W) { return W.IsValid() && !W->IsDead(); });
			if (!bFoes && FVector2D::Distance(FVector2D(Tl) / 100.0, Run.Point) < 10.f)
			{
				T->bRoadWalker = false; T->RoadPath.Reset();
				if (PlayerCombat && M.Contains(TEXT("done"))) PlayerCombat->ShowMessage(M.FindRef(TEXT("done")));
				AdvanceWildQuest(Run);
			}
		}
		else if (Do == TEXT("defend"))
		{
			// (waves round the point until the time is up, from when she comes within 40 m of it; then she must stay within 60 m)
			const int32 Waves = RDQ12Int(M, TEXT("waves"), 3);
			const float Secs = RDQ12Num(M, TEXT("secs"), 60.f);
			if (Run.Deadline <= 0.f)
			{
				if (FVector2D::Distance(Run.Point, H) > 40.f) continue;
				Run.Deadline = Now + Secs; Run.NextWave = Now + 2.f; Run.Waves = 0;
			}
			if (Run.Waves < Waves && Now >= Run.NextWave)
			{
				SpawnQuestMonsters(Run, N, M.FindRef(TEXT("kind")), FString(), 1.f, Run.Point, 22.f);
				for (const TWeakObjectPtr<ARDMonster>& W : Run.Mons) if (ARDMonster* Mo = W.Get()) { Mo->bHunting = true; Mo->HuntUntil = Now + 90.f; }
				++Run.Waves; Run.NextWave = Now + Secs / Waves;
				if (PlayerCombat) PlayerCombat->ShowMessage(FString::Printf(TEXT("%s (wave %d of %d)"), *M.FindRef(TEXT("wave")), Run.Waves, Waves));
			}
			if (FVector2D::Distance(Run.Point, H) > 60.f) { FinishWildQuest(Run, false); continue; }
			if (Now >= Run.Deadline) { if (PlayerCombat && M.Contains(TEXT("done"))) PlayerCombat->ShowMessage(M.FindRef(TEXT("done"))); AdvanceWildQuest(Run); }
		}
		else if (Do == TEXT("deliver"))
		{
			// (to the town it names, before the time is up: she is in its square)
			if (Now > Run.Deadline) { FinishWildQuest(Run, false); continue; }
			const int32 Ti = Wild->Towns.IndexOfByPredicate([&](const FRDWildTown& T) { return FVector2D::Distance(T.Site, Run.Point) < 1.f; });
			if (Ti >= 0 && FVector2D::Distance(Wild->Towns[Ti].Site, H) < 120.f) { if (PlayerCombat && M.Contains(TEXT("done"))) PlayerCombat->ShowMessage(M.FindRef(TEXT("done"))); AdvanceWildQuest(Run); }
		}
		else if (Do == TEXT("survive"))
		{
			// (the storm's time runs only while she is in the shelter (out of it the end moves on with the clock: this tick's 0.2 s);
			// it is over once the time has run in there)
			if (FVector2D::Distance(Run.Point, H) >= Reach) Run.Deadline += Since;
			else if (Now > Run.Deadline) { SetWeatherNamed(TEXT("auto"), false); if (PlayerCombat && M.Contains(TEXT("done"))) PlayerCombat->ShowMessage(M.FindRef(TEXT("done"))); AdvanceWildQuest(Run); }
		}
		else if (Do == TEXT("capture"))
		{
			if (Run.Mons.Num() > 0 && !Run.Mons.ContainsByPredicate([](const TWeakObjectPtr<ARDMonster>& W) { return W.IsValid(); }))
			{
				// (killed instead of bound: a new one comes (a capture is a living one))
				Run.Mons.Reset();
				SpawnQuestMonsters(Run, 1, M.FindRef(TEXT("kind")), M.FindRef(TEXT("named")), RDQ12Num(M, TEXT("hp"), 1.f), Run.Point, 0.f);
			}
			for (const TWeakObjectPtr<ARDMonster>& W : Run.Mons) if (ARDMonster* Mo = W.Get(); Mo && Mo->IsDead()) { if (PlayerCombat) PlayerCombat->ShowMessage(TEXT("Dead is no use: beat it down and bind it alive")); Mo->Destroy(); }
		}
		else if (Do == TEXT("tame"))
		{
			// (a horse that sees her running near it bolts a little way)
			if (AActor* Hz = Run.Horse.Get())
				if (const APawn* P = UGameplayStatics::GetPlayerPawn(this, 0); P && P->GetVelocity().Size2D() > 300.f && FVector::Dist2D(P->GetActorLocation(), Hz->GetActorLocation()) < 900.f)
				{
					const FVector Away = (Hz->GetActorLocation() - P->GetActorLocation()).GetSafeNormal2D() * 600.f;
					FVector To = Hz->GetActorLocation() + Away; To.Z = WildGroundZ(To);
					Hz->SetActorLocation(To + FVector(0, 0, 10.f));
					if (Run.Progress > 0) { Run.Progress = 0; if (PlayerCombat) PlayerCombat->ShowMessage(TEXT("You ran at it: the horse bolts and its trust is lost")); }
				}
		}
	}
}

void ARDDungeonGenerator::TameWildHorse(FQuestRun& Run)
{
	// (the list's "tame a mount: a wild horse becomes a second mount": hers now, and counted as a horse of hers; one is out at a
	// time, the other waits at the stables (the stable swaps them: SwapHorse; the call and a load bring the one she has out, in
	// its own coat); tamed with none bought, it is her only one and the stable still sells the bay)
	ARDHorse* Hz = Cast<ARDHorse>(Run.Horse.Get());
	URDGameInstance* GI = URDGameInstance::Of(this);
	if (!Hz || !GI) return;
	if (Horse && Horse != Hz) Horse->Destroy();
	Hz->bHers = true;
	Horse = Hz;
	GI->HorsesTamed++;
	if (!GI->bHorseOwned) { GI->bHorseOwned = true; GI->bTamedOnly = true; }
	GI->bRideTamed = true;
	Run.Horse = nullptr;
	TownCount(TEXT("wild:tamed"));
	UE_LOG(LogRDQuest12, Log, TEXT("RDQUEST12 a wild horse tamed at %d: %d horses of hers"), Run.Site, 1 + GI->HorsesTamed);
}

void ARDDungeonGenerator::SetWeatherNamed(const FString& Name, bool bHold)
{
	if (Name == TEXT("auto")) { bWeatherHeld = false; return; }
	for (int32 I = 0; I < NumWeathers; ++I) if (WeatherName(I) == Name) { SetWeather(I, true); bWeatherHeld = bHold; return; }
}

TArray<FString> ARDDungeonGenerator::GetWildQuestRunLines() const
{
	TArray<FString> Out;
	for (const auto& Kv : WildQuestRuns)
	{
		const FQuestRun& Run = Kv.Value;
		const FRDWildQuestDef* Q = QuestOfRun(Run);
		if (!Q) continue;
		const TMap<FString, FString> M = Q->Stages.IsValidIndex(Run.Stage - 1) ? RDQ12Parse(Q->Stages[Run.Stage - 1]) : TMap<FString, FString>();
		int32 Alive = 0; for (const TWeakObjectPtr<ARDMonster>& W : Run.Mons) if (W.IsValid() && !W->IsDead()) ++Alive;
		int32 Taken = 0; for (const FQuestThing& T : Run.Things) if (T.bTaken) ++Taken;
		Out.Add(FString::Printf(TEXT("wq|%d|%s|%d|%s|%d|%d|%d|%.1f|%.1f|%d|%d|%d|%d|%s|%d"), Run.Site, *Q->Name.ToString(), Run.Stage, *M.FindRef(TEXT("do")), Run.Progress, RDQ12Int(M, TEXT("n"), 1), Run.Choice,
			Run.Point.X, Run.Point.Y, Run.Mons.Num(), Alive, Run.Things.Num() - Taken, Run.GoldGiven, *M.FindRef(TEXT("hint")).Replace(TEXT("|"), TEXT("/")), Run.bBegun ? 1 : 0));
	}
	return Out;
}

TArray<FString> ARDDungeonGenerator::GetWildQuestFolkLines(int32 Site) const
{
	TArray<FString> Out;
	if (const FQuestRun* Run = WildQuestRuns.Find(Site))
		for (const TWeakObjectPtr<ARDTownsfolk>& W : Run->Folk)
			if (const ARDTownsfolk* T = W.Get()) Out.Add(FString::Printf(TEXT("%s|%s|%.0f|%.0f|%.0f"), *T->WildQuestRole.ToString(), *T->Title, T->GetActorLocation().X, T->GetActorLocation().Y, T->GetActorLocation().Z));
	return Out;
}

TArray<FString> ARDDungeonGenerator::GetWildQuestThingLines(int32 Site) const
{
	TArray<FString> Out;
	if (const FQuestRun* Run = WildQuestRuns.Find(Site))
	{
		for (const FQuestThing& T : Run->Things) Out.Add(FString::Printf(TEXT("thing|%.0f|%.0f|%.0f|%d"), T.At.X, T.At.Y, T.At.Z, T.bTaken ? 1 : 0));
		for (const TWeakObjectPtr<ARDMonster>& W : Run->Mons) if (const ARDMonster* M = W.Get()) Out.Add(FString::Printf(TEXT("monster|%.0f|%.0f|%.0f|%d|%.0f|%.0f"), M->GetActorLocation().X, M->GetActorLocation().Y, M->GetActorLocation().Z, M->IsDead() ? 1 : 0, M->GetHealth(), M->GetMaxHealth()));
		if (const AActor* Hz = Run->Horse.Get()) Out.Add(FString::Printf(TEXT("horse|%.0f|%.0f|%.0f|0"), Hz->GetActorLocation().X, Hz->GetActorLocation().Y, Hz->GetActorLocation().Z));
	}
	return Out;
}
