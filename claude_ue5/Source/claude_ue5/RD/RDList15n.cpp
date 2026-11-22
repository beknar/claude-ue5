// The user's list of 2026-11-20 (docs/improvements15.txt; the plan docs/improvements15_plan.md), its fifteenth phase: story encounters
// (docs/wilderness_ideas.md's idea 8). The encounter director's kinds with a Story15 (SourceArt/wilderness/stories15.json, 941):
//   - "courier": a courier comes up to her by her name with a letter from someone she has met (the last person of the wilds who gave her
//     something, a contract's board, or Brokenspire's elder), and its gift.
//   - "chased": someone running from monsters on her way; the monsters dead and the one chased alive, they thank her and give; dead, it is
//     lost.
//   - "cart": a carter by a cart off its wheel; F at the cart helps lift it, and the carter gives.
//   - "rival": a rival adventurer of her own (StoryRivalName15) going for a place laid ahead of her from the far side; there first, she
//     has it; the rival first, it is emptied, and the rival says so. Each meeting is counted for the game.
// Every one on a stream and ids of its own: nothing else moves.
#include "RD/RDDungeonGenerator.h"
#include "RD/RDWild.h"
#include "RD/RDGameInstance.h"
#include "RD/RDCombat.h"
#include "RD/RDTown.h"
#include "RD/RDMonster.h"
#include "Components/StaticMeshComponent.h"
#include "Kismet/GameplayStatics.h"
#include "Engine/World.h"
DEFINE_LOG_CATEGORY_STATIC(LogRDList15n, Log, All);

void ARDDungeonGenerator::RecordMet15(const FString& Who)
{
	// (someone she has met, for a letter: the last eight kept, the newest last)
	URDGameInstance* GI = URDGameInstance::Of(this);
	if (!GI || Who.IsEmpty()) return;
	GI->MetPeople15.Remove(Who);
	GI->MetPeople15.Add(Who);
	while (GI->MetPeople15.Num() > 8) GI->MetPeople15.RemoveAt(0);
}

ARDTownsfolk* ARDDungeonGenerator::SpawnStoryFolk15(const FString& Def, const FVector2D& AtCm, float Yaw, uint32 Seed, const FString& Title, const TArray<FString>& Lines)
{
	int32 D = Townsfolk.IndexOfByPredicate([&](const FRDTownsfolkDef& X) { return X.Mesh && X.Name.ToString() == Def; });
	if (D < 0) D = Townsfolk.IndexOfByPredicate([&](const FRDTownsfolkDef& X) { return X.Mesh && X.Name.ToString().StartsWith(TEXT("Townsman")); });
	if (D < 0 || !GetWorld()) return nullptr;
	const FVector Q(AtCm.X, AtCm.Y, WildGroundZ(FVector(AtCm.X, AtCm.Y, 0.f)) + 92.f);
	FActorSpawnParameters Sp; Sp.SpawnCollisionHandlingOverride = ESpawnActorCollisionHandlingMethod::AlwaysSpawn;
	ARDTownsfolk* T = GetWorld()->SpawnActor<ARDTownsfolk>(ARDTownsfolk::StaticClass(), FTransform(FRotator(0, Yaw, 0), Q), Sp);
	if (!T) return nullptr;
	T->Init(this, nullptr, D, Q, Yaw, 0.f, Seed);
	T->SetTitle(Title);
	T->OwnLines = Lines;
	WildRoamFolk.Add(T);          // (the director's people: talked to and given by F, among the wilds' people)
	return T;
}

static FString RDStoryTitle15(const FString& Title)
{
	// ("a fleeing traveller" -> "A fleeing traveller")
	FString T = Title;
	if (T.Len() > 0) T[0] = FChar::ToUpper(T[0]);
	return T;
}

static void RDStoryWalk15(ARDTownsfolk* T, const FVector& To)
{
	if (!T) return;
	T->bRoadWalker = true;
	T->RoadPath.Reset();
	T->RoadPath.Add(To);
}

int32 ARDDungeonGenerator::MakeStory15(const FRDWildPoiKind& K, const FVector2D& At, FRandomStream& Rs)
{
	const APawn* Her = UGameplayStatics::GetPlayerPawn(this, 0);
	URDGameInstance* GI = URDGameInstance::Of(this);
	if (!Her || !GI || !PlayerCombat) return 0;
	const FVector H = Her->GetActorLocation();
	FStory15 S; S.Kind = FName(*K.Story15); S.Id = ++StoriesMade15; S.At = FVector(At.X, At.Y, WildGroundZ(FVector(At.X, At.Y, 0.f))); S.Since = GetWorld()->GetTimeSeconds();
	S.Title = K.Title;
	const float Yaw = FMath::RadiansToDegrees(FMath::Atan2(H.Y - At.Y, H.X - At.X));
	TArray<FString> Lines; K.Text.ParseIntoArray(Lines, TEXT("|"), true);
	auto Gift = [&](ARDTownsfolk* T, bool bNow) { T->WildGift = K.Gift; T->WildGiftGold = K.GiftGold; T->bWildGiven = !bNow; };
	if (S.Kind == TEXT("courier"))
	{
		// (a letter from someone she has met, to her by her name)
		const FString Sender = GI->MetPeople15.Num() > 0 ? GI->MetPeople15.Last() : StoryDefaultSender15;
		const FString Letter = StoryLetters15.Num() > 0 ? StoryLetters15[Rs.RandRange(0, StoryLetters15.Num() - 1)] : FString(TEXT("Safe travels."));
		const FString Hero = CurrentHero.ToString();
		TArray<FString> Say;
		Say.Add(FString::Printf(TEXT("%s? You are the %s they speak of? A letter for you, from %s: \"%s\""), *Hero, *Hero.ToLower(), *Sender, *Letter.Replace(TEXT("{hero}"), *Hero)));
		ARDTownsfolk* T = SpawnStoryFolk15(K.Folk, At, Yaw, Rs.GetUnsignedInt(), K.Title, Say);
		if (!T) return 0;
		Gift(T, true);
		RDStoryWalk15(T, H + (FVector(At.X, At.Y, H.Z) - H).GetSafeNormal2D() * 250.f);          // (up to her, 2.5 m short)
		S.Person = T; S.Detail = Sender;
	}
	else if (S.Kind == TEXT("chased"))
	{
		ARDTownsfolk* T = SpawnStoryFolk15(K.Folk, At, Yaw, Rs.GetUnsignedInt(), K.Title, Lines);
		if (!T) return 0;
		Gift(T, false);          // (nothing to give until it is safe)
		RDStoryWalk15(T, H);
		S.Person = T;
		// (its pursuers, 15 to 22 m behind it on the far side from her, after her and it)
		TArray<int32> Kinds; WildKindsForTier(Wild->TierAt(At.X / 100.0, At.Y / 100.0), Kinds);
		ARDSection* Ws = EnsureWildSection();
		if (Kinds.Num() > 0 && Ws)
		{
			const FRDMonsterDef& Def = Monsters[Kinds[Rs.RandRange(0, Kinds.Num() - 1)]];
			const FVector2D Back = (FVector2D(At) - FVector2D(H)).GetSafeNormal();
			for (int32 I = 0; I < FMath::Max(StoryPursuers15, 1); ++I)
			{
				const FVector2D Q = FVector2D(At) + Back.GetRotated(Rs.FRandRange(-30.f, 30.f)) * Rs.FRandRange(1500.f, 2200.f);
				if (ARDMonster* M = SpawnWildMonsterAt(Def, FVector(Q.X, Q.Y, WildGroundZ(FVector(Q.X, Q.Y, 0.f))), Yaw, (int32)Rs.GetUnsignedInt(), Wild->TierAt(Q.X / 100.0, Q.Y / 100.0), 1.f, FString()))
				{
					M->bHunting = true; M->HuntUntil = GetWorld()->GetTimeSeconds() + 90.f;
					WildRoamers.Add(M); S.Pursuers.Add(M);
				}
			}
		}
		if (S.Pursuers.Num() == 0) { T->Destroy(); return 0; }
	}
	else if (S.Kind == TEXT("cart"))
	{
		// (the cart off its wheel, tipped over on one side; the carter beside it)
		TArray<UStaticMesh*> Ms; WildPiecesOf(TEXT("cart"), Ms);
		if (Ms.Num() == 0) return 0;
		UStaticMeshComponent* C = NewObject<UStaticMeshComponent>(this);
		C->SetStaticMesh(Ms[0]);
		C->SetCollisionEnabled(ECollisionEnabled::QueryAndPhysics); C->SetCollisionResponseToAllChannels(ECR_Block);
		C->RegisterComponent();
		const float* Ks = WildPieceScale.Find(FName(*Ms[0]->GetName()));
		S.CartYaw = Yaw + 90.f;
		C->SetWorldTransform(FTransform(FRotator(0.f, S.CartYaw, StoryCartTilt15), S.At + FVector(0, 0, -10.f), FVector(Ks ? *Ks : 1.f)));
		S.Cart = C;
		const FVector2D Toward = (FVector2D(H) - FVector2D(At)).GetSafeNormal();
		const FVector2D Side = FVector2D(At) + FVector2D(-Toward.Y, Toward.X) * 320.f;          // (beside it, not between her and it: there F talked to him, not to the cart)
		ARDTownsfolk* T = SpawnStoryFolk15(K.Folk, Side, Yaw, Rs.GetUnsignedInt(), K.Title, Lines);
		if (!T) { C->DestroyComponent(); return 0; }
		Gift(T, false);          // (it gives once the cart is up)
		S.Person = T;
	}
	else if (S.Kind == TEXT("rival"))
	{
		// (a place laid ahead of her (the kind's Place), the rival from its far side, as far again as she is)
		FRDWildPoiKind Pk = K; Pk.Folk.Reset(); Pk.Animals.Reset();
		const int32 Before = WildPoiLive.Num();
		if (MakeWildEncounter11(Pk, At, Rs) == 0) return 0;
		const FRDWildPoiLive* L = nullptr;
		for (int32 I = WildPoiLive.Num() - 1; I >= 0 && I >= Before - 1; --I) if (FVector::Dist2D(WildPoiLive[I].At, S.At) < 2000.f) { L = &WildPoiLive[I]; break; }
		if (!L) return 0;
		S.PoiId = L->Id; S.At = L->At; S.Detail = WildPoiKinds.IsValidIndex(L->Kind) ? WildPoiKinds[L->Kind].Title : FString(TEXT("the place"));
		const FVector2D Away = (FVector2D(S.At) - FVector2D(H)).GetSafeNormal();
		const FVector2D From = FVector2D(S.At) + Away * FMath::Max(FVector2D::Distance(FVector2D(S.At), FVector2D(H)) * StoryRivalLead15, 1500.f);
		const int32 Met = GI->Counters.FindRef(TEXT("rival15:met"));
		TArray<FString> Say; Say.Add(Met == 0 ? StoryRivalHello15 : StoryRivalAgain15);
		ARDTownsfolk* T = SpawnStoryFolk15(StoryRivalDef15, From, Yaw + 180.f, Rs.GetUnsignedInt(), StoryRivalName15, Say);
		if (!T) return 0;
		T->bWildGiven = true;          // (a rival gives nothing)
		RDStoryWalk15(T, S.At);
		S.Person = T;
		GI->Counters.FindOrAdd(TEXT("rival15:met"))++;
		PlayerCombat->ShowMessage(FString::Printf(TEXT("%s is making for %s ahead: get there first"), *StoryRivalName15, *S.Detail));
	}
	else return 0;
	S.State = TEXT("on");
	Stories15.Add(S);
	StoryLog15.Add(FString::Printf(TEXT("%s|%d|on|%s"), *S.Kind.ToString(), S.Id, *S.Detail));
	UE_LOG(LogRDList15n, Log, TEXT("RDSTORY15 %s %d begun at (%.0f, %.0f) m: %s"), *S.Kind.ToString(), S.Id, S.At.X / 100.f, S.At.Y / 100.f, *S.Detail);
	return 1;
}

void ARDDungeonGenerator::TickStories15(float Dt, const FVector& Her)
{
	if (Stories15.Num() == 0 || !IsWildReady()) return;
	URDGameInstance* GI = URDGameInstance::Of(this);
	const float Now = GetWorld()->GetTimeSeconds();
	for (int32 I = Stories15.Num() - 1; I >= 0; --I)
	{
		FStory15& S = Stories15[I];
		ARDTownsfolk* T = S.Person.Get();
		auto End = [&](const TCHAR* State, const FString& Say)
		{
			S.State = State;
			StoryLog15.Add(FString::Printf(TEXT("%s|%d|%s|%s"), *S.Kind.ToString(), S.Id, State, *S.Detail));
			if (!Say.IsEmpty() && PlayerCombat) PlayerCombat->ShowMessage(Say);
			UE_LOG(LogRDList15n, Log, TEXT("RDSTORY15 %s %d %s"), *S.Kind.ToString(), S.Id, State);
		};
		if (S.State == TEXT("on"))
		{
			if (S.Kind == TEXT("courier"))
			{
				// (up to her as she moves; done once it has given)
				if (T && !T->IsWildDead14() && FVector::Dist2D(T->GetActorLocation(), Her) > 400.f && T->RoadPath.Num() <= 1) RDStoryWalk15(T, Her + (T->GetActorLocation() - Her).GetSafeNormal2D() * 250.f);
				else if (T && FVector::Dist2D(T->GetActorLocation(), Her) <= 300.f) T->RoadPath.Reset();          // (beside her: it waits to be spoken to)
				if (T && T->bWildGiven) End(TEXT("done"), FString());          // (a courier is no one met: a letter never comes from one)
				else if (!T) End(TEXT("gone"), FString());          // (taken away with her far off: no one's failure)
				else if (T->IsWildDead14()) End(TEXT("failed"), FString());
			}
			else if (S.Kind == TEXT("chased"))
			{
				int32 Alive = 0;
				for (const TWeakObjectPtr<ARDMonster>& M : S.Pursuers) if (M.IsValid() && !M->IsDead()) ++Alive;
				if (!T) End(TEXT("gone"), FString());
				else if (T->IsWildDead14()) End(TEXT("failed"), FString::Printf(TEXT("%s did not get away"), *RDStoryTitle15(S.Title)));
				else if (Alive == 0)
				{
					T->bWildGiven = false;          // (now it has something to give)
					T->RoadPath.Reset();          // (it stops running: she speaks to it where it stands)
					if (T->OwnLines.Num() > 1) T->OwnLines.RemoveAt(0);          // (its first line was its cry for help)
					End(TEXT("saved"), FString::Printf(TEXT("%s is safe: speak with them"), *RDStoryTitle15(S.Title)));
				}
			}
			else if (S.Kind == TEXT("rival"))
			{
				const float Dh = FVector::Dist2D(Her, S.At), Dr = T ? FVector::Dist2D(T->GetActorLocation(), S.At) : 1e9f;
				if (Dh < StoryRivalReachCm15)
				{
					if (GI) GI->Counters.FindOrAdd(TEXT("rival15:won"))++;
					if (T) { T->OwnLines = { StoryRivalLost15 }; RDStoryWalk15(T, T->GetActorLocation() + (T->GetActorLocation() - S.At).GetSafeNormal2D() * 4000.f); }
					End(TEXT("won"), FString::Printf(TEXT("You reach %s before %s. \"%s\""), *S.Detail, *StoryRivalName15, *StoryRivalLost15));
				}
				else if (Dr < 250.f || (T && T->RoadPath.Num() == 0 && Dr < 600.f))
				{
					MarkWildPoiUsed15(S.PoiId);          // (its things taken: used, as she would have)
					if (GI) GI->Counters.FindOrAdd(TEXT("rival15:lost"))++;
					if (T) T->OwnLines = { StoryRivalWon15 };
					End(TEXT("lost"), FString::Printf(TEXT("%s got to %s first and took what was there. \"%s\""), *StoryRivalName15, *S.Detail, *StoryRivalWon15));
				}
			}
		}
		else if (S.State == TEXT("saved") || S.State == TEXT("mended"))
		{
			if (T && T->bWildGiven) { RecordMet15(T->Title); End(TEXT("done"), FString()); }
		}
		// (gone when ended and she is 150 m off, or begun and she 400 m off)
		const bool bEnded = S.State != TEXT("on") && S.State != TEXT("saved") && S.State != TEXT("mended");
		const float Far = FVector::Dist2D(Her, S.At);
		if ((bEnded && Far > 15000.f) || Far > 40000.f || Now - S.Since > 900.f)
		{
			if (T) T->Destroy();
			if (UStaticMeshComponent* C = S.Cart.Get()) C->DestroyComponent();
			Stories15.RemoveAt(I);
		}
	}
	if (StoryLog15.Num() > 200) StoryLog15.RemoveAt(0, StoryLog15.Num() - 200);
}

bool ARDDungeonGenerator::StoryCartFirst15(const FVector& From, float& Best, int32& Kind, int32& Id) const
{
	// (the rewards' nearest, its eighth kind: a cart off its wheel (2.2 m of its middle))
	bool bAny = false;
	for (const FStory15& S : Stories15)
		if (S.Kind == TEXT("cart") && S.State == TEXT("on") && S.Cart.IsValid())
		{
			const float D = FVector::Dist2D(S.At, From) - 150.f;          // (from its side, not its middle: it is 3 m long)
			if (D < Best && FMath::Abs(S.At.Z - From.Z) < 300.f) { Best = FMath::Max(D, 0.f); Kind = 8; Id = S.Id; bAny = true; }
		}
	return bAny;
}

FString ARDDungeonGenerator::MendStoryCart15(int32 Id)
{
	FStory15* S = Stories15.FindByPredicate([Id](const FStory15& X) { return X.Id == Id; });
	if (!S || S->State != TEXT("on")) return FString();
	if (UStaticMeshComponent* C = S->Cart.Get()) C->SetWorldRotation(FRotator(0.f, S->CartYaw, 0.f));
	if (ARDTownsfolk* T = S->Person.Get()) { T->bWildGiven = false; if (T->OwnLines.Num() > 1) T->OwnLines.RemoveAt(0); }
	S->State = TEXT("mended");
	StoryLog15.Add(FString::Printf(TEXT("cart|%d|mended|"), Id));
	if (PlayerCombat) PlayerCombat->ShowMessage(TEXT("You heave the cart up and the carter knocks the wheel home: speak with them"));
	UE_LOG(LogRDList15n, Log, TEXT("RDSTORY15 cart %d mended"), Id);
	return TEXT("mend");
}

TArray<FString> ARDDungeonGenerator::GetStories15() const
{
	// (tests: "story|kind|id|state|x|y|person x|y|z (cm)|alive|given|pursuers alive|detail" for each going, then the log's lines
	// "log|kind|id|state|detail", then "rival|met|won|lost", "met|<the people she has met, newest last, ~-joined>")
	TArray<FString> Out;
	for (const FStory15& S : Stories15)
	{
		const ARDTownsfolk* T = S.Person.Get();
		int32 Alive = 0; for (const TWeakObjectPtr<ARDMonster>& M : S.Pursuers) if (M.IsValid() && !M->IsDead()) ++Alive;
		const FVector P = T ? T->GetActorLocation() : FVector::ZeroVector;
		Out.Add(FString::Printf(TEXT("story|%s|%d|%s|%.0f|%.0f|%.0f|%.0f|%.0f|%d|%d|%d|%s"), *S.Kind.ToString(), S.Id, *S.State, S.At.X, S.At.Y, P.X, P.Y, P.Z,
			T && !T->IsWildDead14() ? 1 : 0, T && T->bWildGiven ? 1 : 0, Alive, *S.Detail));
	}
	for (const FString& L : StoryLog15) Out.Add(TEXT("log|") + L);
	const URDGameInstance* GI = URDGameInstance::Of(this);
	if (GI)
	{
		Out.Add(FString::Printf(TEXT("rival|%d|%d|%d"), GI->Counters.FindRef(TEXT("rival15:met")), GI->Counters.FindRef(TEXT("rival15:won")), GI->Counters.FindRef(TEXT("rival15:lost"))));
		Out.Add(TEXT("met|") + FString::Join(GI->MetPeople15, TEXT("~")));
	}
	return Out;
}

ARDMonster* ARDDungeonGenerator::GetStoryPursuer15(int32 Id, int32 N) const
{
	const FStory15* S = Stories15.FindByPredicate([Id](const FStory15& X) { return X.Id == Id; });
	return S && S->Pursuers.IsValidIndex(N) ? S->Pursuers[N].Get() : nullptr;
}
