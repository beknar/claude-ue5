// The user's list of 2026-11-22 (docs/improvements16.txt: "vary the Heaven dungeon with soldier variants, medics, differently colored/
// designed drones and differently colored/designed mechs from the Dystopia and Sci-fi packs. also use aliens and monsters from the Aliens
// Warrior Pack"; the plan docs/improvements16_plan.md), its twenty-fifth phase, the fortress's defenders (947 monsters): the kinds are
// data (SourceArt/heaven_fortress/defenders25.json); what they need of the game beyond the castle's monsters is here: a medic heals its
// side (FRDMonsterDef's Heal*), and a kind's colour or design is its materials slot by slot (FRDMonsterDef::Materials, RDMonster.cpp).
#include "RD/RDMonster.h"
#include "RD/RDDungeonGenerator.h"
#include "RD/RDSection.h"
#include "Components/CapsuleComponent.h"
#include "Components/SkeletalMeshComponent.h"
#include "GameFramework/CharacterMovementComponent.h"
#include "NiagaraComponent.h"
#include "NiagaraFunctionLibrary.h"
#include "Particles/ParticleSystem.h"
#include "Kismet/GameplayStatics.h"
DEFINE_LOG_CATEGORY_STATIC(LogRDFortress25, Log, All);

float RDClipLength(const UAnimationAsset* A);

void ARDMonster::SetupHeal(const FRDMonsterDef& Def)
{
	bHeals = Def.bHeals;
	if (!bHeals) return;
	HealRange = Def.HealRange; HealShare = FMath::Clamp(Def.HealShare, 0.f, 1.f); HealBelow = FMath::Clamp(Def.HealBelow, 0.f, 0.9f);
	HealWait = FMath::Max(Def.HealCooldown, 0.5f); HealRelease = FMath::Clamp(Def.HealRelease, 0.05f, 0.95f);
	HealClip = Def.HealClip ? Def.HealClip.Get() : (AttackAnims.Num() > 0 ? AttackAnims[0].Get() : nullptr);
	HealFx = Def.HealFx; HealFxScale = Def.HealFxScale;
	// (its first heal not at once: a hash of its kind and place, never a stream of the play)
	const uint32 H = HashCombine(GetTypeHash(Def.Name), GetTypeHash(FIntPoint(FMath::RoundToInt(GetActorLocation().X), FMath::RoundToInt(GetActorLocation().Y))));
	HealWaitLeft = 1.f + (float)(H % 1000u) / 1000.f;
}

bool ARDMonster::TryHeal(float Dt)
{
	ARDDungeonGenerator* G = Section ? Section->Generator.Get() : nullptr;
	if (!G || !HealClip) return false;
	if (HealWaitLeft > 0.f) { HealWhy25 = TEXT("wait"); return false; }
	if (AttackCooldown > 0.f) { HealWhy25 = TEXT("cooldown"); return false; }
	if (IsSilenced()) { HealWhy25 = TEXT("silenced"); return false; }
	FString Why = TEXT("none");
	// (the most hurt of its side within reach, with a sight line from its chest to theirs; itself too)
	ARDMonster* Best = nullptr; float BestShare = 0.f;
	const FVector L = GetActorLocation();
	FCollisionObjectQueryParams O; O.AddObjectTypesToQuery(ECC_WorldStatic); O.AddObjectTypesToQuery(ECC_WorldDynamic);
	for (ARDMonster* M : G->GetMonsters())
	{
		if (!IsValid(M) || M->IsDead() || M->IsAlly() || M->GetMaxHealth() <= 0.f) continue;
		if (M->IsEliteOrBoss()) { if (1.f - M->GetHealth() / M->GetMaxHealth() >= HealBelow) Why = TEXT("elite"); continue; }          // (no boss or elite is healed (PR #132's review))
		const float Missing = 1.f - M->GetHealth() / M->GetMaxHealth();
		if (Missing < HealBelow || Missing <= BestShare) continue;
		// (one medic a patient: another's patient is left to it)
		bool bTaken = false;
		for (ARDMonster* Om : G->GetMonsters()) if (Om != this && IsValid(Om) && Om->bHealSwing && Om->HealTarget.Get() == M) bTaken = true;
		if (bTaken) { Why = TEXT("taken"); continue; }
		if (FVector::Dist(M->GetActorLocation(), L) > HealRange) continue;
		if (M != this)
		{
			FCollisionQueryParams Q(SCENE_QUERY_STAT(RDHealSight), false, this); Q.AddIgnoredActor(M);
			if (GetWorld()->LineTraceTestByObjectType(L + FVector(0, 0, 40.f), M->GetActorLocation() + FVector(0, 0, 40.f), O, Q)) { Why = TEXT("sight"); continue; }
		}
		Best = M; BestShare = Missing;
	}
	if (!Best) { HealWhy25 = Why; return false; }
	HealWhy25 = TEXT("heal");
	FVector D = Best->GetActorLocation() - L; D.Z = 0.f;
	if (Best != this)
	{
		Face(D, Dt);
		if (!D.IsNearlyZero() && FVector::DotProduct(D.GetSafeNormal(), GetActorForwardVector()) < 0.85f) { SetWalkingAnim(false); return true; }          // (turning to it)
	}
	GetCharacterMovement()->StopMovementImmediately();
	GetMesh()->PlayAnimation(HealClip, false);
	AttackLen = RDClipLength(HealClip); AttackHit = AttackLen * HealRelease; AttackTime = 0.f; bHitDone = false;
	bHealSwing = true; bRangedSwing = false; bBeamSwing = false;
	HealTarget = Best;
	return true;
}

void ARDMonster::ReleaseHeal()
{
	ARDMonster* T = HealTarget.Get();
	if (!T || T->IsDead()) return;
	const float Before = T->GetHealth();
	// (a share of the patient's hit points, at most twice the medic's own share's worth (a stronger kind is not healed by its size))
	T->HealBy(HealShare * FMath::Min(T->GetMaxHealth(), 2.f * MaxHealth));
	const float Got = T->GetHealth() - Before;
	++HealsGiven; HealedTotal += Got;
	if (HealFx)
	{
		if (UNiagaraSystem* N = Cast<UNiagaraSystem>(HealFx.Get()))
		{
			if (UNiagaraComponent* C = UNiagaraFunctionLibrary::SpawnSystemAttached(N, T->GetRootComponent(), NAME_None, FVector::ZeroVector, FRotator::ZeroRotator, FVector(1.f), EAttachLocation::KeepRelativeOffset, true, ENCPoolMethod::None, false))
				C->SetVariableFloat(TEXT("User.Scale"), HealFxScale);
		}
		else if (UParticleSystem* Ps = Cast<UParticleSystem>(HealFx.Get())) UGameplayStatics::SpawnEmitterAttached(Ps, T->GetRootComponent(), NAME_None, FVector::ZeroVector, FRotator::ZeroRotator, FVector(HealFxScale));
	}
	UE_LOG(LogRDFortress25, Log, TEXT("RDFORTRESS25 %s healed %s: %.0f hit points (%d heals)"), *MonsterName.ToString(), *T->MonsterName.ToString(), Got, HealsGiven);
}
