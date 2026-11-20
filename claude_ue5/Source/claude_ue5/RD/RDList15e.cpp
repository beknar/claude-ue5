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
	// (once a place: a section laid again asks again for the same hearth; its parent's own children are looked at, PR #98's review)
	for (USceneComponent* Ch : Parent->GetAttachChildren())
		if (UNiagaraComponent* N = Cast<UNiagaraComponent>(Ch); N && N->GetAsset() == HearthFx15 && FVector::DistSquared(N->GetComponentLocation(), At) < 400.f) return N;
	if ((++HearthPrune15 & 31) == 0) HearthFires15.RemoveAll([](const TWeakObjectPtr<UNiagaraComponent>& W) { return !W.IsValid(); });
	UNiagaraComponent* C = UNiagaraFunctionLibrary::SpawnSystemAttached(HearthFx15, Parent, NAME_None, At, FRotator::ZeroRotator, FVector(HearthFxScale15),
		EAttachLocation::KeepWorldPosition, false, ENCPoolMethod::None, true, false);          // (no pre-cull: one spawned out of view never drew, PR #60;
		// not destroyed when done: the town's lights-out rule's DeactivateImmediate destroyed the fires it reached (a whole run had none)
	if (C) HearthFires15.Add(C);
	return C;
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
/** the gap between two animals' bodies as boxes on the ground (each its half length along its facing, half width across): the most
 *  any axis of the two boxes keeps them apart, negative when they overlap; Push the way that takes A out of B the shortest */
static float RDT15BoxGap(const FVector& Pa, float Ya, const FVector2D& Ha, const FVector& Pb, float Yb, const FVector2D& Hb, FVector* Push = nullptr)
{
	const FVector Ua = FRotator(0.f, Ya, 0.f).Vector(), Va(-Ua.Y, Ua.X, 0.f), Ub = FRotator(0.f, Yb, 0.f).Vector(), Vb(-Ub.Y, Ub.X, 0.f);
	const FVector D(Pb.X - Pa.X, Pb.Y - Pa.Y, 0.f);
	const FVector Axes[4] = { Ua, Va, Ub, Vb };
	float Best = -BIG_NUMBER; FVector BestAx = Ua;
	for (const FVector& N : Axes)
	{
		const float Ra = Ha.X * FMath::Abs(FVector::DotProduct(Ua, N)) + Ha.Y * FMath::Abs(FVector::DotProduct(Va, N));
		const float Rb = Hb.X * FMath::Abs(FVector::DotProduct(Ub, N)) + Hb.Y * FMath::Abs(FVector::DotProduct(Vb, N));
		const float Dn = FVector::DotProduct(D, N), Sep = FMath::Abs(Dn) - Ra - Rb;
		if (Sep > Best) { Best = Sep; BestAx = Dn > 0.f ? -N : N; }
	}
	if (Push) *Push = BestAx;
	return Best;
}

FVector2D ARDTownAnimal::GetHalfSize15() const
{
	return Gen && Gen->TownAnimals.IsValidIndex(Def) ? Gen->TownAnimals[Def].HalfSize : FVector2D(50.f, 50.f);
}

void ARDTownAnimal::Register15()
{
	if (!Gen || !Gen->bPenApart15 || bLoose || !Gen->TownAnimals.IsValidIndex(Def)) return;
	Half15 = Gen->TownAnimals[Def].HalfSize.ComponentMax(FVector2D(10.f, 10.f));
	PenKey15 = FIntPoint(FMath::RoundToInt(PenAt.X / 10.f), FMath::RoundToInt(PenAt.Y / 10.f));
	// (PR #98's review: the pens of the chunks dropped leave entries of dead animals: every 64th registration takes the empty ones out)
	if ((++Gen->PenPrune15 & 63) == 0)
		for (auto It = Gen->PenMates15.CreateIterator(); It; ++It)
		{
			It.Value().RemoveAll([](const TWeakObjectPtr<ARDTownAnimal>& A) { return !A.IsValid(); });
			if (It.Value().Num() == 0) It.RemoveCurrent();
		}
	TArray<TWeakObjectPtr<ARDTownAnimal>>& M = Gen->PenMates15.FindOrAdd(PenKey15);
	M.RemoveAll([](const TWeakObjectPtr<ARDTownAnimal>& A) { return !A.IsValid(); });
	M.AddUnique(this);
	// (laid where a mate already stands: moved to a free spot of its pen, from its own stream, on the ground there (PR #98's review))
	if (Crowded15(GetActorLocation(), GetActorRotation().Yaw))
	{
		const float Rr = Half15.Size();
		const FVector2D H = (PenHalf - FVector2D(Rr, Rr)).ComponentMax(FVector2D(5.f, 5.f));
		FVector At = FreeSpot15(this->R, H);
		At.Z = bWildGround && GroundN > 1 ? GroundZAt(At) : GetActorLocation().Z;
		SetActorLocation(At, false);
	}
}

float ARDTownAnimal::MinGap15(const FVector& At, float Yaw) const
{
	const TArray<TWeakObjectPtr<ARDTownAnimal>>* M = Gen ? Gen->PenMates15.Find(PenKey15) : nullptr;
	float G = BIG_NUMBER;
	if (!M) return G;
	for (const TWeakObjectPtr<ARDTownAnimal>& W : *M)
	{
		const ARDTownAnimal* O = W.Get();
		if (!O || O == this || O->bDead14) continue;
		G = FMath::Min(G, RDT15BoxGap(At, Yaw, Half15, O->GetActorLocation(), O->GetActorRotation().Yaw, O->Half15));
	}
	return G;
}

FVector ARDTownAnimal::FreeSpot15(FRandomStream& Rs, const FVector2D& H) const
{
	// (somewhere in its pen no mate stands nor is walking to, whichever way either then faces: their half lengths apart and 20 cm; the
	// first of a few tries clear of all, else the last tried)
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
				const float Need = Half15.X + O->Half15.X + 20.f;
				if (FVector::Dist2D(At, O->GetActorLocation()) < Need || (O->State == 2 && FVector::Dist2D(At, O->To) < Need)) { bClear = false; break; }
			}
		if (bClear) break;
	}
	return At;
}

void ARDTownAnimal::Apart15(float Dt)
{
	// (standing in a mate: eased out along the shortest way out of its box, half the overlap each, a second at most its walk, kept inside
	// its pen)
	const TArray<TWeakObjectPtr<ARDTownAnimal>>* M = Gen ? Gen->PenMates15.Find(PenKey15) : nullptr;
	if (!M) return;
	const FVector L = GetActorLocation();
	const float Yaw = GetActorRotation().Yaw;
	FVector Push = FVector::ZeroVector;
	for (const TWeakObjectPtr<ARDTownAnimal>& W : *M)
	{
		const ARDTownAnimal* O = W.Get();
		if (!O || O == this || O->bDead14) continue;
		FVector Way;
		const float Gap = RDT15BoxGap(L, Yaw, Half15, O->GetActorLocation(), O->GetActorRotation().Yaw, O->Half15, &Way);
		if (Gap >= 0.f) continue;
		if (FVector::Dist2D(L, O->GetActorLocation()) < 1.f) Way = FVector(1.f, 0.f, 0.f).RotateAngleAxis((float)((GetUniqueID() * 37u) % 360u), FVector::UpVector);
		Push += Way * (-Gap * 0.5f + 1.f);
	}
	if (Push.IsNearlyZero(0.5f)) return;
	FVector N = L + Push.GetClampedToMaxSize(FMath::Max(Speed, 60.f) * Dt);
	const FRotator Pr(0.f, PenYaw, 0.f);
	FVector Lp = Pr.UnrotateVector(N - PenAt);
	const float Rr = FMath::Min(Half15.X, Half15.Y);
	const FVector2D H = (PenHalf - FVector2D(Rr, Rr)).ComponentMax(FVector2D(5.f, 5.f));
	Lp.X = FMath::Clamp(Lp.X, -H.X, H.X); Lp.Y = FMath::Clamp(Lp.Y, -H.Y, H.Y);
	N = PenAt + Pr.RotateVector(FVector(Lp.X, Lp.Y, 0.f)); N.Z = L.Z;
	if (bWildGround && GroundN > 1) N.Z = GroundZAt(N);
	SetActorLocation(N, false);
}