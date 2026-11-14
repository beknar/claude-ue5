// The list of 2026-11-12's fifth phase: the structures of the wilds ("add these quest types that can be found in the wilderness ...
// they should have some kind of physical structure that holds them, like this list of structures: cave system, canyon or gorge,
// cliff face or aerie, mountain pass, waterfall grotto ... ruined fortress, watchtower ... a titan's carcass ..."; "how to make the
// wilderness more interesting? there should be more structure types found in the wilderness ... those structures can have
// containers, traps, hold prisoners"). The world places them (FRDWildWorld::SitesIn, a place of kind "site" with its kind's index);
// a chunk lays each by the ruins' layout language (LayWildParts) from WildSiteKinds (924 sites, SourceArt/wilderness/sites12.json),
// with its chests, its guards (SpawnWildMonsters), its prisoners (townsfolk in cages: F frees them) and its traps (spikes underfoot).
// The quests a structure holds are RDWildQuest12.cpp's.
#include "RD/RDDungeonGenerator.h"
#include "RD/RDWild.h"
#include "RD/RDGameInstance.h"
#include "RD/RDCombat.h"
#include "RD/RDMonster.h"
#include "RD/RDSection.h"
#include "RD/RDTown.h"
#include "Components/StaticMeshComponent.h"
#include "Components/SkeletalMeshComponent.h"
#include "ProceduralMeshComponent.h"
#include "Animation/AnimSequence.h"
#include "Engine/StaticMesh.h"
#include "Kismet/GameplayStatics.h"

DEFINE_LOG_CATEGORY_STATIC(LogRDSite12, Log, All);

namespace
{
	/** a structure's keys: its chests (5 << 40), its prisoners (6 << 40), each + its id x 8 + n */
	constexpr int64 RDS12BoxKeys = 5LL << 40, RDS12FreedKeys = 6LL << 40;
	constexpr float RDS12TrapReachCm = 90.f;
}

void ARDDungeonGenerator::LayWildSite(ARDWildChunk* C, const FRDWildPlace& P)
{
	if (!C || !Wild || !WildSiteKinds.IsValidIndex(P.Site)) return;
	const FRDWildSiteKind& K = WildSiteKinds[P.Site];
	FRandomStream R((int32)FRDWildWorld::Hash(P.Id, 0x1216, Wild->Seed));
	FRuinLaid Rec; Rec.Id = P.Id; Rec.Yaw = P.Yaw; Rec.At = P.At; Rec.Name = P.Name; Rec.Kind = P.Site;
	LayWildParts(C, P, K, P.At, P.At, P.Yaw, R, RDS12BoxKeys, Rec);
	Rec.Guards = K.Guards;
	// (its prisoners: a cage each on a ring round its middle, a captive in it; freed ones stay freed (their keys in WildKilled))
	URDGameInstance* GI = URDGameInstance::Of(this);
	FRandomStream Rp((int32)FRDWildWorld::Hash(P.Id, 0x1217, Wild->Seed));
	const int32 Folk = Townsfolk.IndexOfByPredicate([&](const FRDTownsfolkDef& X) { return X.Mesh && X.Name.ToString().StartsWith(TEXT("Refugee")); });
	for (int32 I = 0; I < K.Prisoners; ++I)
	{
		// (on its front sides, 45 to 75 degrees off its front, 6 to 8 m out: away from the chests, which stand at its back (a chest
		// beside a cage took her F, as a nearer container does))
		const float A = FMath::DegreesToRadians(P.Yaw + (I % 2 ? -1.f : 1.f) * (45.f + 30.f * (I / 2)) + Rp.FRandRange(-8.f, 8.f)), D = Rp.FRandRange(6.f, 8.f);
		const FVector2D Xy = P.At + FVector2D(FMath::Cos(A), FMath::Sin(A)) * D;
		const int64 Key = RDS12FreedKeys + (int64)(uint32)P.Id * 8 + I;
		const bool bFreed = GI && GI->WildKilled.Contains(Key);
		TArray<UStaticMesh*> Cages; WildPiecesOf(TEXT("s12_cage#"), Cages);
		UStaticMeshComponent* Cage = nullptr;
		if (Cages.Num() > 0 && !bFreed)
		{
			UStaticMesh* M = Cages[Rp.RandRange(0, Cages.Num() - 1)];
			const float Bh = FMath::Max((float)M->GetBoundingBox().GetSize().Z, 1.f);
			const float Sc = 220.f / Bh;
			Cage = LayRuinPiece(C, M, FVector(Xy.X * 100.0, Xy.Y * 100.0, 0.0), FRotator(0.f, P.Yaw + Rp.FRandRange(0.f, 360.f), 0.f), FVector(Sc), 3.f, true);
			if (Cage) { Rec.Comps.Add(Cage); Rec.Lifts.Add(0.f); ++Rec.Pieces; }
		}
		if (Folk < 0) continue;
		const FVector Q(Xy.X * 100.0, Xy.Y * 100.0, WildGroundZ(FVector(Xy.X * 100.0, Xy.Y * 100.0, 0.0)) + 92.f);
		FActorSpawnParameters Sp; Sp.SpawnCollisionHandlingOverride = ESpawnActorCollisionHandlingMethod::AlwaysSpawn;
		if (ARDTownsfolk* T = GetWorld()->SpawnActor<ARDTownsfolk>(ARDTownsfolk::StaticClass(), FTransform(FRotator(0, P.Yaw + 180.f, 0), Q), Sp))
		{
			T->Init(this, nullptr, Folk, Q, P.Yaw + 180.f, 0.f, Rp.GetUnsignedInt());
			T->SetTitle(bFreed ? TEXT("Freed captive") : TEXT("Prisoner"));
			T->OwnLines = bFreed ? TArray<FString>{ TEXT("You saved my life out here."), TEXT("I'll find my way home now.") }
				: TArray<FString>{ TEXT("Please, get me out of this cage!"), TEXT("They'll be back soon, hurry!") };
			T->WildSiteKey = Key; T->WildSiteCage = Cage; T->bWildGiven = bFreed;
			WildSiteFolk.Add(T);
			C->Props.Add(T);
		}
	}
	// (its traps: spikes on the ways in, 6 to 12 m out (none in its opening's middle, which the quests use))
	TArray<UStaticMesh*> Spikes; WildPiecesOf(TEXT("s12_spikes#"), Spikes);
	for (int32 I = 0; I < K.Traps && Spikes.Num() > 0; ++I)
	{
		const float A = FMath::DegreesToRadians(P.Yaw + 40.f + 280.f * (I + 0.5f) / K.Traps + Rp.FRandRange(-10.f, 10.f)), D = Rp.FRandRange(6.f, 12.f);
		const FVector2D Xy = P.At + FVector2D(FMath::Cos(A), FMath::Sin(A)) * D;
		UStaticMesh* M = Spikes[Rp.RandRange(0, Spikes.Num() - 1)];
		const FVector Bs = M->GetBoundingBox().GetSize();
		const float Sc = 120.f / FMath::Max((float)FMath::Max(Bs.X, Bs.Y), 1.f);
		if (UStaticMeshComponent* Tm = LayRuinPiece(C, M, FVector(Xy.X * 100.0, Xy.Y * 100.0, 0.0), FRotator(0.f, Rp.FRandRange(0.f, 360.f), 0.f), FVector(Sc), 6.f, false))
		{
			Rec.Comps.Add(Tm); Rec.Lifts.Add(0.f); ++Rec.Pieces;
			FSiteTrap Tr; Tr.At = FVector(Xy.X * 100.0, Xy.Y * 100.0, WildGroundZ(FVector(Xy.X * 100.0, Xy.Y * 100.0, 0.0))); Tr.Key = (int64)P.Id * 8 + I; Tr.SiteId = P.Id;
			WildSiteTraps.RemoveAll([&](const FSiteTrap& X) { return X.Key == Tr.Key; });
			WildSiteTraps.Add(Tr);
		}
	}
	// (the living beast's back: a beast the size of a hill with a camp on its back, walking a slow round about the place)
	if (K.Name == TEXT("beastback") && WildBeastMesh)
	{
		USkeletalMeshComponent* Bc = NewObject<USkeletalMeshComponent>(C);
		Bc->SetSkeletalMesh(WildBeastMesh);
		Bc->SetupAttachment(C->Ground);
		Bc->SetRelativeScale3D(FVector(WildBeastScale));
		Bc->SetCollisionEnabled(ECollisionEnabled::QueryOnly);
		Bc->SetCollisionResponseToAllChannels(ECR_Ignore);
		Bc->SetCollisionResponseToChannel(ECC_Visibility, ECR_Block);
		Bc->RegisterComponent();
		if (WildBeastWalk) Bc->PlayAnimation(WildBeastWalk, true);
		// (the camp on its back: the platform mesh following the body's bones (the pack's "build" mesh is the platform alone:
		// laid as the beast, it walked the round as a platform in the air))
		if (WildBeastBuild)
		{
			USkeletalMeshComponent* Pc = NewObject<USkeletalMeshComponent>(C);
			Pc->SetSkeletalMesh(WildBeastBuild);
			Pc->SetupAttachment(Bc);
			Pc->SetCollisionEnabled(ECollisionEnabled::NoCollision);
			Pc->RegisterComponent();
			Pc->SetLeaderPoseComponent(Bc);
		}
		FWildBeast Bs; Bs.Comp = Bc; Bs.Centre = P.At; Bs.Angle = FMath::DegreesToRadians(P.Yaw); Bs.SiteId = P.Id;
		WildBeasts.RemoveAll([&](const FWildBeast& X) { return X.SiteId == P.Id; });
		WildBeasts.Add(Bs);
	}
	WildSitesLaid.RemoveAll([&](const FRuinLaid& X) { return X.Id == P.Id; });
	WildSitesLaid.Add(Rec);
	QuestSiteLaid(P);          // (its quest's giver, RDWildQuest12.cpp)
	UE_LOG(LogRDSite12, Log, TEXT("RDSITE %s (%s): %d pieces, %d containers, %d prisoners, %d traps at (%.0f, %.0f)"), *P.Name, *K.Name.ToString(), Rec.Pieces, Rec.Boxes, K.Prisoners, K.Traps, P.At.X, P.At.Y);
}

FString ARDDungeonGenerator::WildSiteTalk(ARDTownsfolk* T)
{
	if (!T || !WildSiteFolk.Contains(TWeakObjectPtr<ARDTownsfolk>(T))) return FString();
	if (T->WildQuestSite != 0) return WildQuestTalk(T);
	if (T->WildSiteKey == 0 || T->bWildGiven) return FString();
	// (a prisoner freed: the cage taken away, a word and what they had hidden, kept freed for the game)
	URDGameInstance* GI = URDGameInstance::Of(this);
	if (GI) GI->WildKilled.Add(T->WildSiteKey);
	if (UStaticMeshComponent* Cg = T->WildSiteCage.Get()) { Cg->SetVisibility(false); Cg->SetCollisionEnabled(ECollisionEnabled::NoCollision); }
	T->bWildGiven = true; T->SetTitle(TEXT("Freed captive"));
	T->OwnLines = { TEXT("You saved my life out here."), TEXT("I'll find my way home now.") };
	const int32 Gold = WildGoldAt(15, T->GetActorLocation());
	if (Gold > 0) AddGold(Gold, TEXT("from a freed captive"));
	TownCount(TEXT("wild:freed"));
	if (PlayerCombat) PlayerCombat->ShowMessage(FString::Printf(TEXT("You free the prisoner: \"Thank you! Take this, it's all I kept hidden from them.\" (%d gold)"), Gold));
	PlaySoundAt(TEXT("Player.Loot"), T->GetActorLocation());
	UE_LOG(LogRDSite12, Log, TEXT("RDSITE a prisoner freed (%lld): %d gold"), T->WildSiteKey, Gold);
	return TEXT("freed");
}

void ARDDungeonGenerator::TickWildSites12(float Dt, const FVector& Her)
{
	if (!PlayerCombat || PlayerCombat->IsDead()) return;
	const float Now = GetWorld()->GetTimeSeconds();
	// (the laid ones far from her are gone with their chunks)
	WildSitesLaid.RemoveAll([&](const FRuinLaid& X) { return FVector2D::Distance(X.At, FVector2D(Her.X, Her.Y) / 100.0) > 3000.f; });
	WildSiteTraps.RemoveAll([&](const FSiteTrap& X) { return FVector::Dist2D(X.At, Her) > 300000.f; });
	WildSiteFolk.RemoveAll([](const TWeakObjectPtr<ARDTownsfolk>& W) { return !W.IsValid(); });
	// (the beasts walk their round: along the circle at their speed, turned along it, on the ground)
	WildBeasts.RemoveAll([](const FWildBeast& B) { return !B.Comp.IsValid(); });
	for (FWildBeast& B : WildBeasts)
	{
		USkeletalMeshComponent* Bc = B.Comp.Get();
		const float Rr = FMath::Max(WildBeastRadius, 5.f) * 100.f;
		B.Angle += WildBeastSpeed * Dt / Rr;
		const FVector W(B.Centre.X * 100.0 + FMath::Cos(B.Angle) * Rr, B.Centre.Y * 100.0 + FMath::Sin(B.Angle) * Rr, 0.0);
		// (the elephant's head is its mesh's +Y (its head bone 346 cm along +Y, its tail 335 along -Y): turned by the angle, +Y lies
		// along the round's way, (-sin, cos); at the angle + 90 it walked sideways, its head to the middle)
		Bc->SetWorldLocationAndRotation(FVector(W.X, W.Y, WildGroundZ(W)), FRotator(0.f, FMath::RadiansToDegrees(B.Angle), 0.f));
	}
	// (a trap stepped on: a share of her hit points and a slow; set again a minute on)
	const ACharacter* Ch = Cast<ACharacter>(UGameplayStatics::GetPlayerPawn(this, 0));
	const float Feet = Her.Z - (Ch ? Ch->GetSimpleCollisionHalfHeight() : 90.f);
	for (FSiteTrap& Tr : WildSiteTraps)
	{
		if (Now < Tr.ReadyAt || FVector::Dist2D(Tr.At, Her) > RDS12TrapReachCm || FMath::Abs(Feet - Tr.At.Z) > 80.f) continue;
		Tr.ReadyAt = Now + 60.f;
		PlayerCombat->HurtByTrap(0.15f, 0.4f, 3.f, TEXT("Spikes! You step on a hidden trap"));
		++WildTrapsSprung;
		UE_LOG(LogRDSite12, Log, TEXT("RDSITE a trap sprung at (%.0f, %.0f)"), Tr.At.X, Tr.At.Y);
	}
}

TArray<FString> ARDDungeonGenerator::GetWildSiteLines() const
{
	TArray<FString> Out;
	for (const FRuinLaid& X : WildSitesLaid)
	{
		int32 Stand = 0, Inside = 0, Pris = 0, Freed = 0, NTraps = 0;
		if (WildSection)
			for (const TObjectPtr<ARDMonster>& Mo : WildSection->SpawnedMonsters)
			{
				if (!IsValid(Mo) || Mo->IsDead() || Mo->WildKey < 0 || Mo->WildKey / 16 != (int64)X.Id) continue;
				++Stand;
				// (half its capsule: one brushing a gate's own triangle shape in its archway is not inside it)
				if (WildRuinInPiece(X, Mo->GetActorLocation(), Mo->GetSimpleCollisionRadius() * 0.5f, Mo->GetSimpleCollisionHalfHeight() * 0.5f)) ++Inside;
			}
		for (const TWeakObjectPtr<ARDTownsfolk>& W : WildSiteFolk)
			if (const ARDTownsfolk* T = W.Get(); T && T->WildSiteKey > 0 && (T->WildSiteKey - RDS12FreedKeys) / 8 == (int64)(uint32)X.Id) { ++Pris; if (T->bWildGiven) ++Freed; }
		for (const FSiteTrap& Tr : WildSiteTraps) if (Tr.SiteId == X.Id) ++NTraps;
		const bool bK = WildSiteKinds.IsValidIndex(X.Kind);
		Out.Add(FString::Printf(TEXT("site|%d|%s|%s|%.1f|%.1f|%d|%d|%d|%d|%d|%d|%d|%s|%.1f"), X.Id, bK ? *WildSiteKinds[X.Kind].Name.ToString() : TEXT("?"), bK ? *WildSiteKinds[X.Kind].Title : TEXT(""),
			X.At.X, X.At.Y, X.Pieces, X.Boxes, Stand, Inside, Pris, Freed, NTraps, *X.Name, X.Yaw));
	}
	return Out;
}

TArray<FString> ARDDungeonGenerator::GetWildBeastLines() const
{
	TArray<FString> Out;
	for (const FWildBeast& B : WildBeasts)
		if (const USkeletalMeshComponent* Bc = B.Comp.Get())
		{
			// (and its head bone's place, the first bone named for a head: the test reads which way it faces from it)
			FVector Hd = Bc->GetComponentLocation();
			if (const USkeletalMesh* Sm = Bc->GetSkeletalMeshAsset())
				for (int32 I = 0; I < Sm->GetRefSkeleton().GetNum(); ++I)
					if (Sm->GetRefSkeleton().GetBoneName(I).ToString().Contains(TEXT("Head"))) { Hd = Bc->GetBoneLocation(Sm->GetRefSkeleton().GetBoneName(I)); break; }
			Out.Add(FString::Printf(TEXT("beast|%d|%.0f|%.0f|%.0f|%.1f|%.0f|%.0f"), B.SiteId, Bc->GetComponentLocation().X, Bc->GetComponentLocation().Y, Bc->GetComponentLocation().Z, Bc->GetComponentRotation().Yaw, Hd.X, Hd.Y));
		}
	return Out;
}

TArray<FString> ARDDungeonGenerator::GetWildSitePieceLines(int32 Id) const
{
	return PieceLinesOf(WildSitesLaid.FindByPredicate([&](const FRuinLaid& R) { return R.Id == Id; }));
}

TArray<FString> ARDDungeonGenerator::GetWildSiteThingLines(int32 Id) const
{
	TArray<FString> Out;
	const float Now = GetWorld() ? GetWorld()->GetTimeSeconds() : 0.f;
	for (const TWeakObjectPtr<ARDTownsfolk>& W : WildSiteFolk)
		if (const ARDTownsfolk* T = W.Get(); T && T->WildSiteKey > 0 && (T->WildSiteKey - RDS12FreedKeys) / 8 == (int64)(uint32)Id)
			Out.Add(FString::Printf(TEXT("prisoner|%.0f|%.0f|%d"), T->GetActorLocation().X, T->GetActorLocation().Y, T->bWildGiven ? 1 : 0));
	for (const FSiteTrap& Tr : WildSiteTraps)
		if (Tr.SiteId == Id) Out.Add(FString::Printf(TEXT("trap|%.0f|%.0f|%d"), Tr.At.X, Tr.At.Y, Now >= Tr.ReadyAt ? 1 : 0));
	return Out;
}

FName ARDDungeonGenerator::WildSiteQuestOf(const FRDWildPlace& P) const
{
	if (!Wild || !WildSiteKinds.IsValidIndex(P.Site) || WildSiteKinds[P.Site].Quests.Num() == 0) return NAME_None;
	const TArray<FName>& Q = WildSiteKinds[P.Site].Quests;
	return Q[FRDWildWorld::Hash(P.Id, 0x1218, Wild->Seed) % (uint32)Q.Num()];
}

FString ARDDungeonGenerator::FindWildSite(FName Kind, FName Quest, float X, float Y, float MaxKm) const
{
	if (!Wild) return FString();
	const int32 Want = Kind.IsNone() ? -1 : WildSiteKinds.IndexOfByPredicate([&](const FRDWildSiteKind& K) { return K.Name == Kind; });
	if (!Kind.IsNone() && Want < 0) return FString();
	// (rings of the 2.5 km cells out from the point, past the first that holds one until no nearer can be left)
	const FIntPoint C0 = Wild->SiteCellOf(X, Y);
	const int32 Rmax = FMath::CeilToInt(MaxKm * 1000.0 / FRDWildWorld::SiteCellM);
	double Best = 1e18; FString Got;
	for (int32 Ring = 0; Ring <= Rmax; ++Ring)
	{
		if (!Got.IsEmpty() && FMath::Square(FMath::Max(0.0, (Ring - 1) * FRDWildWorld::SiteCellM)) > Best) break;
		for (int32 I = -Ring; I <= Ring; ++I)
			for (int32 J = -Ring; J <= Ring; ++J)
			{
				if (FMath::Max(FMath::Abs(I), FMath::Abs(J)) != Ring) continue;
				TArray<FRDWildPlace> Ps; Wild->SitesIn(C0 + FIntPoint(I, J), Ps);
				for (const FRDWildPlace& P : Ps)
				{
					if (Want >= 0 && P.Site != Want) continue;
					if (!Quest.IsNone() && WildSiteQuestOf(P) != Quest) continue;
					const double D = FVector2D::DistSquared(P.At, FVector2D(X, Y));
					if (D < Best) { Best = D; Got = FString::Printf(TEXT("%d|%.1f|%.1f|%.1f|%s"), P.Id, P.At.X, P.At.Y, P.Yaw, *P.Name); }
				}
			}
	}
	return Got;
}

TArray<FString> ARDDungeonGenerator::CountWildSites(float X, float Y, float MaxKm) const
{
	TArray<FString> Out;
	if (!Wild) return Out;
	TArray<int32> N; N.SetNumZeroed(WildSiteKinds.Num());
	TMap<FName, int32> Q;
	const FIntPoint C0 = Wild->SiteCellOf(X, Y);
	const int32 Rmax = FMath::CeilToInt(MaxKm * 1000.0 / FRDWildWorld::SiteCellM);
	for (int32 I = -Rmax; I <= Rmax; ++I)
		for (int32 J = -Rmax; J <= Rmax; ++J)
		{
			TArray<FRDWildPlace> Ps; Wild->SitesIn(C0 + FIntPoint(I, J), Ps);
			for (const FRDWildPlace& P : Ps) if (N.IsValidIndex(P.Site)) { ++N[P.Site]; Q.FindOrAdd(WildSiteQuestOf(P))++; }
		}
	for (int32 K = 0; K < WildSiteKinds.Num(); ++K) Out.Add(FString::Printf(TEXT("%s|%d"), *WildSiteKinds[K].Name.ToString(), N[K]));
	for (const auto& Kv : Q) Out.Add(FString::Printf(TEXT("quest:%s|%d"), *Kv.Key.ToString(), Kv.Value));
	return Out;
}
