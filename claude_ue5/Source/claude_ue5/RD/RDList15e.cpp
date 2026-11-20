// The user's list of 2026-11-20 (docs/improvements15.txt; the plan docs/improvements15_plan.md), its sixth phase: the town.
// Item 1, "the cows in town can walk through each other": a pen's animals keep apart (each a round body of half its length and width:
// a walk's target taken away from its mates, a step that would take it into one not made, one standing in another eased out), the
// wilds' paddocks the same (one class). Item 20, "The First Warden ... appears as not completed even after slaying the Tier 1 boss":
// a quest's "boss" goal counts Mistward Castle's tiers whose boss she has slain (the castle's own bossdone counters, a kill before the
// quest was taken too: the user's choice), and the quest is offered from the start (934 town). Item 21 is the HUD's (RDTownHUD.cpp),
// item 22 the fires' (RDWild10.cpp, RDWildFarm11.cpp).
#include "RD/RDDungeonGenerator.h"
#include "RD/RDTown.h"
#include "RD/RDGameInstance.h"
#include "RD/RDWild.h"
#include "Engine/World.h"
#include "RD/RDSection.h"
#include "NiagaraComponent.h"
#include "NiagaraFunctionLibrary.h"
#include "Kismet/GameplayStatics.h"
#include "GameFramework/Pawn.h"
#include "Components/InstancedStaticMeshComponent.h"
DEFINE_LOG_CATEGORY_STATIC(LogRDList15e, Log, All);

// ================================================================================================ item 20: the castle's bosses
int32 ARDDungeonGenerator::CastleBossesSlain15() const
{
	// (the castle's own tiers: its counters carry no dungeon's key (Vel Morrath's are "vel_morrath:bossdone:<tier>"))
	const URDGameInstance* GI = URDGameInstance::Of(this);
	if (!GI) return 0;
	int32 N = 0;
	for (int32 T = 1; T <= RDGameTierMax; ++T) if (GI->GetCounter(FString::Printf(TEXT("bossdone:%d"), T)) > 0) ++N;
	return N;
}

void ARDDungeonGenerator::DebugSetCounter15(const FString& Key, int32 Value)
{
	if (URDGameInstance* GI = URDGameInstance::Of(this)) { if (Value == 0) GI->Counters.Remove(Key); else GI->Counters.Add(Key, Value); }
}

void ARDDungeonGenerator::DebugForgetQuest15(FName Id)
{
	if (URDGameInstance* GI = URDGameInstance::Of(this)) GI->Quests.RemoveAll([Id](const FRDQuestState& S) { return S.Id == Id; });
}

// ================================================================================================ item 22: the hearths burn
UNiagaraComponent* ARDDungeonGenerator::SpawnHearth15(USceneComponent* Parent, const FVector& At)
{
	if (!HearthFx15 || !Parent) return nullptr;
	// (once a place: a section laid again, a chunk made again, ask again for the same hearth)
	HearthFires15.RemoveAll([](const TWeakObjectPtr<UNiagaraComponent>& W) { return !W.IsValid(); });
	for (const TWeakObjectPtr<UNiagaraComponent>& W : HearthFires15) if (FVector::DistSquared(W->GetComponentLocation(), At) < 400.f) return W.Get();
	UNiagaraComponent* C = UNiagaraFunctionLibrary::SpawnSystemAttached(HearthFx15, Parent, NAME_None, At, FRotator::ZeroRotator, FVector(HearthFxScale15),
		EAttachLocation::KeepWorldPosition, false, ENCPoolMethod::None, true, false);          // (no pre-cull: one spawned out of view never drew, PR #60;
		// kept, not destroyed when done: the effect's distance culling ended one made far from her for good (the second run's town had none)
	if (C) HearthFires15.Add(C);
	return C;
}

void ARDDungeonGenerator::TickHearths15()
{
	// (once a second: a fire within 40 m of her that is not running (culled while she was far, or never begun) is begun again)
	const UWorld* W = GetWorld();
	if (!W || W->GetTimeSeconds() < HearthWakeAt15) return;
	HearthWakeAt15 = W->GetTimeSeconds() + 1.f;
	const APawn* Her = UGameplayStatics::GetPlayerPawn(this, 0);
	if (!Her) return;
	const FVector L = Her->GetActorLocation();
	for (const TWeakObjectPtr<UNiagaraComponent>& Wk : HearthFires15)
		if (UNiagaraComponent* C = Wk.Get(); C && !C->IsActive() && FVector::DistSquared(C->GetComponentLocation(), L) < FMath::Square(4000.f)) C->Activate(true);
}

TArray<FString> ARDDungeonGenerator::GetHearthFires15(FVector At, float Range) const
{
	TArray<FString> Out;
	for (const TWeakObjectPtr<UNiagaraComponent>& W : HearthFires15)
		if (const UNiagaraComponent* C = W.Get(); C && FVector::Dist2D(C->GetComponentLocation(), At) < Range)
		{
			const FVector L = C->GetComponentLocation();
			Out.Add(FString::Printf(TEXT("%.0f|%.0f|%.0f|%d"), L.X, L.Y, L.Z, C->IsActive() && C->IsVisible() ? 1 : 0));          // (burning: running and shown)
		}
	return Out;
}

void ARDSection::HideHearthCards15()
{
	if (!Generator || !Generator->bHearth15 || !Generator->HearthHideMat15) return;
	if (const UWorld* W = GetWorld(); !W || !W->IsGameWorld()) return;
	TArray<UInstancedStaticMeshComponent*> Is;
	GetComponents<UInstancedStaticMeshComponent>(Is);
	for (UInstancedStaticMeshComponent* C : Is)
		if (const UStaticMesh* M = C ? C->GetStaticMesh() : nullptr; M && M->GetName() == TEXT("SM_Kit_Fireplace") && C->GetNumMaterials() > 4)
			C->SetMaterial(4, Generator->HearthHideMat15);
}

// ================================================================================================ item 22: the wilds' hearths
TArray<FString> ARDDungeonGenerator::GetWildHearths15(FVector At, float Range) const
{
	TArray<FString> Out;
	for (const TPair<FIntPoint, TObjectPtr<ARDWildChunk>>& Kv : WildChunks)
		if (const ARDWildChunk* Ch = Kv.Value.Get())
			for (const FVector& F : Ch->HearthPoints15) if (FVector::Dist2D(F, At) < Range) Out.Add(FString::Printf(TEXT("%.0f|%.0f|%.0f"), F.X, F.Y, F.Z));
	return Out;
}

// ================================================================================================ item 1: a pen's animals apart
float ARDTownAnimal::GetHalfWidth15() const
{
	return Gen && Gen->TownAnimals.IsValidIndex(Def) ? FMath::Min(Gen->TownAnimals[Def].HalfSize.X, Gen->TownAnimals[Def].HalfSize.Y) : Rad15;
}

void ARDTownAnimal::Register15()
{
	if (!Gen || !Gen->bPenApart15 || bLoose || !Gen->TownAnimals.IsValidIndex(Def)) return;
	const FRDTownAnimalDef& D = Gen->TownAnimals[Def];
	Rad15 = FMath::Max((D.HalfSize.X + D.HalfSize.Y) * 0.5f, 10.f);
	PenKey15 = FIntPoint(FMath::RoundToInt(PenAt.X / 10.f), FMath::RoundToInt(PenAt.Y / 10.f));
	TArray<TWeakObjectPtr<ARDTownAnimal>>& M = Gen->PenMates15.FindOrAdd(PenKey15);
	M.RemoveAll([](const TWeakObjectPtr<ARDTownAnimal>& A) { return !A.IsValid(); });
	M.AddUnique(this);
	// (laid where a mate already stands: moved to a free spot of its pen, from its own stream)
	if (Crowded15(GetActorLocation()))
	{
		const FVector2D H = (PenHalf - FVector2D(Rad15, Rad15)).ComponentMax(FVector2D(5.f, 5.f));
		const FVector At = FreeSpot15(R, H);
		SetActorLocation(FVector(At.X, At.Y, GetActorLocation().Z), false);
	}
}

bool ARDTownAnimal::Crowded15(const FVector& At) const
{
	const TArray<TWeakObjectPtr<ARDTownAnimal>>* M = Gen ? Gen->PenMates15.Find(PenKey15) : nullptr;
	if (!M) return false;
	for (const TWeakObjectPtr<ARDTownAnimal>& W : *M)
	{
		const ARDTownAnimal* O = W.Get();
		if (!O || O == this || O->bDead14) continue;
		if (FVector::Dist2D(At, O->GetActorLocation()) < Rad15 + O->Rad15) return true;
	}
	return false;
}

FVector ARDTownAnimal::FreeSpot15(FRandomStream& Rs, const FVector2D& H) const
{
	// (somewhere in its pen no mate stands nor is walking to: the first of a few tries clear of all, else the last tried)
	const TArray<TWeakObjectPtr<ARDTownAnimal>>* M = Gen ? Gen->PenMates15.Find(PenKey15) : nullptr;
	FVector At = PenAt;
	for (int32 K = 0; K < 8; ++K)
	{
		At = PenAt + FRotator(0.f, PenYaw, 0.f).RotateVector(FVector(Rs.FRandRange(-H.X, H.X), Rs.FRandRange(-H.Y, H.Y), 0.f));
		bool bClear = true;
		if (M)
			for (const TWeakObjectPtr<ARDTownAnimal>& W : *M)
			{
				const ARDTownAnimal* O = W.Get();
				if (!O || O == this || O->bDead14) continue;
				const float Need = Rad15 + O->Rad15 + 20.f;
				if (FVector::Dist2D(At, O->GetActorLocation()) < Need || (O->State == 2 && FVector::Dist2D(At, O->To) < Need)) { bClear = false; break; }
			}
		if (bClear) break;
	}
	return At;
}

void ARDTownAnimal::Apart15(float Dt)
{
	// (standing in a mate: eased out, half the overlap each a second at most its walk, kept inside its pen)
	const TArray<TWeakObjectPtr<ARDTownAnimal>>* M = Gen ? Gen->PenMates15.Find(PenKey15) : nullptr;
	if (!M) return;
	const FVector L = GetActorLocation();
	FVector Push = FVector::ZeroVector;
	for (const TWeakObjectPtr<ARDTownAnimal>& W : *M)
	{
		const ARDTownAnimal* O = W.Get();
		if (!O || O == this || O->bDead14) continue;
		FVector D = L - O->GetActorLocation(); D.Z = 0.f;
		const float Need = Rad15 + O->Rad15, Dd = D.Size();
		if (Dd >= Need) continue;
		const FVector U = Dd > 1.f ? D / Dd : FVector(1.f, 0.f, 0.f).RotateAngleAxis((float)((GetUniqueID() * 37u) % 360u), FVector::UpVector);
		Push += U * (Need - Dd) * 0.5f;
	}
	if (Push.IsNearlyZero(0.5f)) return;
	FVector N = L + Push.GetClampedToMaxSize(FMath::Max(Speed, 60.f) * Dt);
	// (inside its pen: in the pen's frame, within its half sizes less its body)
	const FRotator Pr(0.f, PenYaw, 0.f);
	FVector Lp = Pr.UnrotateVector(N - PenAt);
	const FVector2D H = (PenHalf - FVector2D(Rad15, Rad15)).ComponentMax(FVector2D(5.f, 5.f));
	Lp.X = FMath::Clamp(Lp.X, -H.X, H.X); Lp.Y = FMath::Clamp(Lp.Y, -H.Y, H.Y);
	N = PenAt + Pr.RotateVector(FVector(Lp.X, Lp.Y, 0.f)); N.Z = L.Z;
	if (bWildGround && GroundN > 1) N.Z = GroundZAt(N);
	SetActorLocation(N, false);
}
