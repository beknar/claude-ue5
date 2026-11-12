// The user's list of 2026-11-11 (docs/improvements11.txt), its third phase: the Warlock's thirteen curses ("need warlock only
// spell list ... Curse of Rot ... Doom"), each a Curse spell with its CurseEffect (RDTypes.h): what each does to a monster
// (ARDMonster: its curse state, read where it takes hurt, swings, shoots, dies and ticks), their release
// (URDCombatComponent::ReleaseCurse11), the Warlock's own tomes (FRDSpellDef::OnlyHeroes: HeroCanLearnSpell, TomeSpellOf).
// The data (names, mana, tiers, looks) is 918 spells3's.
#include "RD/RDDungeonGenerator.h"
#include "RD/RDMonster.h"
#include "RD/RDSection.h"
#include "RD/RDCombat.h"
#include "Components/CapsuleComponent.h"
#include "GameFramework/CharacterMovementComponent.h"
#include "NiagaraComponent.h"
#include "Engine/World.h"

DEFINE_LOG_CATEGORY_STATIC(LogRDList11c, Log, All);

namespace
{
	const TCHAR* RDL11CurseName(ERDCurseEffect E)
	{
		static const TCHAR* N[] = { TEXT("none"), TEXT("rot"), TEXT("lethargy"), TEXT("hunted"), TEXT("greed"), TEXT("silence"), TEXT("withering"),
		                            TEXT("brittle"), TEXT("leech"), TEXT("dread"), TEXT("contagion"), TEXT("ruin"), TEXT("kinship"), TEXT("doom") };
		const int32 K = (int32)E;
		return K >= 0 && K < (int32)ERDCurseEffect::Count ? N[K] : TEXT("?");
	}
	/** a roll in [0, 1) from two numbers: never a stream the play draws from */
	float RDL11Roll(uint32 A, uint32 B) { return (float)(HashCombine(A, B * 2654435761u + 0x51C1u) % 100000u) / 100000.f; }
	/** Kinship's sharing does not share what it shares */
	bool GRDL11Sharing = false;
}

// ================================================================================================ the curses on a monster
void ARDMonster::Curse11(ERDCurseEffect E, float Seconds, float Amount, FName Element, int32 Group)
{
	if (bDead || E == ERDCurseEffect::None || E == ERDCurseEffect::Count || !GetWorld()) return;
	const float Now = GetWorld()->GetTimeSeconds();
	const int32 K = (int32)E;
	const bool bWas = Now < C11Until[K];
	if (E == ERDCurseEffect::Rot)
	{
		// (stacks up to three: each its own poison over its time; a stack whose poison has run out is free again (PR #48's
		// review: counted until the whole curse ended, a fourth cast while one poison was left did nothing))
		for (float& End : RotEnds)
			if (End <= Now) { End = Now + Seconds; AddBurn(Amount, Seconds, 0.f); break; }
		C11Until[K] = FMath::Max(C11Until[K], Now + Seconds); C11Amount[K] = Amount;
		return;
	}
	C11Until[K] = FMath::Max(bWas ? C11Until[K] : 0.f, Now + Seconds);
	C11Amount[K] = bWas ? FMath::Max(C11Amount[K], Amount) : Amount;
	switch (E)
	{
	case ERDCurseEffect::Ruin: RuinElement = Element; break;
	case ERDCurseEffect::Kinship: KinGroup = Group; break;
	case ERDCurseEffect::Doom: if (!bWas) DoomTaken = 0.f; break;
	case ERDCurseEffect::Dread: DreadTaken = 0.f; AttackTime = -1.f; Path.Reset(); break;
	case ERDCurseEffect::Lethargy: SlowFor(0.3f, Seconds); break;
	case ERDCurseEffect::Silence:
		// (a shot or beam already in its wind-up is broken off: it would have gone off at its hit time (PR #48's review))
		if (AttackTime >= 0.f && (bRangedSwing || bBeamSwing))
		{
			AttackTime = -1.f; bRangedSwing = bBeamSwing = false; bHitDone = true; ++SilencedRefusals;
			bWalkingAnim = true; SetWalkingAnim(false);
		}
		break;
	default: break;
	}
}

void ARDMonster::EndCurse11(ERDCurseEffect E)
{
	const int32 K = (int32)E;
	if (K > 0 && K < (int32)ERDCurseEffect::Count) C11Until[K] = -100.f;
}

bool ARDMonster::HasCurse11(ERDCurseEffect E) const
{
	const int32 K = (int32)E;
	return K > 0 && K < (int32)ERDCurseEffect::Count && GetWorld() && GetWorld()->GetTimeSeconds() < C11Until[K];
}

float ARDMonster::CurseLeft11(ERDCurseEffect E) const
{
	const int32 K = (int32)E;
	return K > 0 && K < (int32)ERDCurseEffect::Count && GetWorld() ? FMath::Max(0.f, C11Until[K] - GetWorld()->GetTimeSeconds()) : 0.f;
}

float ARDMonster::CurseAmount11(ERDCurseEffect E) const
{
	const int32 K = (int32)E;
	return HasCurse11(E) ? C11Amount[K] : 0.f;
}

TArray<FString> ARDMonster::GetCurseLines() const
{
	TArray<FString> Out;
	for (int32 K = 1; K < (int32)ERDCurseEffect::Count; ++K)
	{
		const ERDCurseEffect E = (ERDCurseEffect)K;
		if (!HasCurse11(E)) continue;
		FString More;
		if (E == ERDCurseEffect::Rot) More = FString::Printf(TEXT("stacks %d"), RotStacksNow());
		else if (E == ERDCurseEffect::Ruin) More = RuinElement.ToString();
		else if (E == ERDCurseEffect::Kinship) More = FString::Printf(TEXT("group %d"), KinGroup);
		else if (E == ERDCurseEffect::Doom) More = FString::Printf(TEXT("taken %.1f"), DoomTaken);
		else if (E == ERDCurseEffect::Dread) More = FString::Printf(TEXT("taken %.1f"), DreadTaken);
		Out.Add(FString::Printf(TEXT("%s|%.2f|%.3f|%s"), RDL11CurseName(E), CurseLeft11(E), C11Amount[K], *More));
	}
	return Out;
}

void ARDMonster::HealBy(float Amount)
{
	if (bDead || Amount <= 0.f) return;
	// (Withering Brand: the heal it gets is its share less; no monster here heals itself, so there is no regeneration to stop)
	if (HasCurse11(ERDCurseEffect::Withering)) Amount *= FMath::Clamp(1.f - C11Amount[(int32)ERDCurseEffect::Withering], 0.f, 1.f);
	Health = FMath::Min(MaxHealth, Health + Amount);
}

bool ARDMonster::HoldFor11(float Seconds)
{
	if (bDead || !GetWorld()) return false;
	const ARDDungeonGenerator* G = Section ? Section->Generator.Get() : nullptr;
	if (bFinalBoss && G && G->FinalBossPoise > 0.f)
	{
		const float Now = GetWorld()->GetTimeSeconds();
		if (Now - LastFlinchTime < G->FinalBossPoise) { ++FlinchesShrugged; return false; }
		LastFlinchTime = Now;
	}
	StunFor(Seconds);
	return true;
}

bool ARDMonster::HasAnyCurse11() const
{
	const float Now = GetWorld() ? GetWorld()->GetTimeSeconds() : 0.f;
	for (int32 K = 1; K < (int32)ERDCurseEffect::Count; ++K) if (Now < C11Until[K]) return true;
	return false;
}

int32 ARDMonster::RotStacksNow() const
{
	const float Now = GetWorld() ? GetWorld()->GetTimeSeconds() : 0.f;
	int32 N = 0;
	for (const float End : RotEnds) N += End > Now ? 1 : 0;
	return N;
}

bool ARDMonster::IsAfraid() const { return HasCurse11(ERDCurseEffect::Dread); }
bool ARDMonster::IsSilenced() const { return HasCurse11(ERDCurseEffect::Silence); }

void ARDMonster::SunderFor(float Share, float Seconds)
{
	const float Now = GetWorld()->GetTimeSeconds();
	SunderShare = Now < SunderUntil ? FMath::Max(SunderShare, Share) : Share; SunderUntil = FMath::Max(SunderUntil, Now + Seconds);
}

void ARDMonster::WeakenFor(float Share, float Seconds)
{
	const float Now = GetWorld()->GetTimeSeconds();
	WeakenShare = Now < WeakenUntil ? FMath::Max(WeakenShare, Share) : Share; WeakenUntil = FMath::Max(WeakenUntil, Now + Seconds);
}

float ARDMonster::BlowMul() const
{
	const float W = GetWorld() && GetWorld()->GetTimeSeconds() < WeakenUntil ? WeakenShare : 0.f;
	return FMath::Clamp(1.f - FMath::Max(GetCurseShare(), W), 0.f, 1.f);
}

bool ARDMonster::IsEliteOrBoss() const
{
	if (bBoss || bFinalBoss || bHellElite) return true;
	const ARDDungeonGenerator* G = Section ? Section->Generator.Get() : nullptr;
	return G && MaxHealth > G->GetMonsterHealth(Section->Coord) * DiffHealthMul * 1.25f;
}

float ARDMonster::CurseDamageIn(float Amount, AActor* From)
{
	ARDDungeonGenerator* G = Section ? Section->Generator.Get() : nullptr;
	if (!G || !GetWorld()) return Amount;
	const float Now = GetWorld()->GetTimeSeconds();
	URDCombatComponent* Pc = G->GetPlayerCombat();
	const AActor* Her = Pc ? Pc->GetOwner() : nullptr;
	const bool bHers = Her && From == Her;
	// (her weapon's blow, bolt or slash; a spell's hit carries its element; a burn's tick, a burst or a turned blow nothing (PR
	// #48's review: "no element" had counted as a weapon's blow, and a burning brittle monster was knocked down every tick))
	const bool bWeapon = G->HitElement == RDHitWeapon();
	const bool bDirect = !G->HitElement.IsNone();
	float A = Amount;
	if (Now < SunderUntil) A *= 1.f + SunderShare;
	if (HasCurse11(ERDCurseEffect::Brittle) && bWeapon && bHers) A *= 1.f + C11Amount[(int32)ERDCurseEffect::Brittle];
	if (HasCurse11(ERDCurseEffect::Dread)) A *= 1.f + C11Amount[(int32)ERDCurseEffect::Dread];
	if (HasCurse11(ERDCurseEffect::Ruin) && bDirect && !bWeapon && G->HitElement == RuinElement) A *= 1.f + C11Amount[(int32)ERDCurseEffect::Ruin];
	// (her blows and spells twice as hard: on the hunted its 10 %, on the brittle a weapon's 10 % (knocking it down))
	if (bHers && bDirect && !GRDL11Sharing)
	{
		const bool bHunted = HasCurse11(ERDCurseEffect::Hunted), bBrittle = HasCurse11(ERDCurseEffect::Brittle) && bWeapon;
		const float Chance = (bHunted ? C11Amount[(int32)ERDCurseEffect::Hunted] : 0.f) + (bBrittle ? G->CurseCritChance : 0.f);
		if (Chance > 0.f && RDL11Roll(GetUniqueID(), (uint32)(++CritRolls)) < Chance)
		{
			A *= 2.f; ++CritsTaken; ++Pc->CritsDealt;
			if (bBrittle && !bDead && HoldFor11(1.2f)) ++KnockedDown;
		}
	}
	// (Leech Hex: a share of every hurt it takes, by anyone, heals her)
	if (HasCurse11(ERDCurseEffect::Leech) && Pc && !Pc->IsDead()) { const float H = A * C11Amount[(int32)ERDCurseEffect::Leech]; Pc->HealBy(H); LeechGiven += H; }
	// (Chains of Kinship: a share of it split among the others bound with it)
	if (HasCurse11(ERDCurseEffect::Kinship) && KinGroup >= 0 && !GRDL11Sharing)
	{
		TArray<ARDMonster*> O;
		for (ARDMonster* M : G->GetMonsters()) if (M != this && IsValid(M) && !M->IsDead() && M->KinGroup == KinGroup && M->HasCurse11(ERDCurseEffect::Kinship)) O.Add(M);
		if (O.Num() > 0)
		{
			const float Share = A * C11Amount[(int32)ERDCurseEffect::Kinship];
			A -= Share; KinShared += Share;
			GRDL11Sharing = true;
			for (ARDMonster* M : O) M->ApplyDamageEx(Share / O.Num(), From, nullptr, false, false);
			GRDL11Sharing = false;
		}
	}
	if (HasCurse11(ERDCurseEffect::Doom)) DoomTaken += A;
	return A;
}

void ARDMonster::CurseAfterHit(float Amount)
{
	if (!GetWorld()) return;
	const float Now = GetWorld()->GetTimeSeconds();
	// (the fear ends early once it has taken a tenth of its hit points)
	if (HasCurse11(ERDCurseEffect::Dread)) { DreadTaken += Amount; if (DreadTaken >= MaxHealth * 0.1f) C11Until[(int32)ERDCurseEffect::Dread] = Now; }
	// (Doom: under a fifth of its hit points before its time, it dies; a boss takes the burst instead)
	if (HasCurse11(ERDCurseEffect::Doom) && Health > 0.f && Health < MaxHealth * 0.2f && !bBoss && !bFinalBoss) { Health = 0.f; bDoomExecuted = true; }
}

void ARDMonster::CurseOnDeath()
{
	ARDDungeonGenerator* G = Section ? Section->Generator.Get() : nullptr;
	if (!G || !GetWorld()) return;
	if (G->HuntedMark.Get() == this) G->HuntedMark = nullptr;
	// (Contagion: its curses go to up to three within 8 m, with the time they had left)
	if (!HasCurse11(ERDCurseEffect::Contagion)) return;
	TArray<ARDMonster*> Near;
	for (ARDMonster* M : G->GetMonsters())
		if (M != this && IsValid(M) && !M->IsDead() && !M->IsAlly() && FVector::Dist2D(M->GetActorLocation(), GetActorLocation()) <= 800.f && FMath::Abs(M->GetActorLocation().Z - GetActorLocation().Z) < 300.f) Near.Add(M);
	Near.Sort([this](const ARDMonster& A, const ARDMonster& B) { return FVector::DistSquared(A.GetActorLocation(), GetActorLocation()) < FVector::DistSquared(B.GetActorLocation(), GetActorLocation()); });
	for (int32 I = 0; I < Near.Num() && I < 3; ++I)
		for (int32 K = 1; K < (int32)ERDCurseEffect::Count; ++K)
		{
			const ERDCurseEffect E = (ERDCurseEffect)K;
			if (E == ERDCurseEffect::Contagion || E == ERDCurseEffect::Hunted || !HasCurse11(E)) continue;
			Near[I]->Curse11(E, CurseLeft11(E), C11Amount[K], RuinElement, KinGroup);
			++CursesSpread;
		}
}

void ARDMonster::TickCurses11(float Dt)
{
	ARDDungeonGenerator* G = Section ? Section->Generator.Get() : nullptr;
	if (!G || !GetWorld() || bDead) return;
	const float Now = GetWorld()->GetTimeSeconds();
	// (Doom's time is out: half of all it took meanwhile, at once)
	const int32 Kd = (int32)ERDCurseEffect::Doom;
	if (C11Until[Kd] > 0.f && Now >= C11Until[Kd])
	{
		const float B = DoomTaken * C11Amount[Kd];
		C11Until[Kd] = -100.f; DoomTaken = 0.f;
		if (B > 0.f)
		{
			DoomBurst = B;
			URDCombatComponent* Pc = G->GetPlayerCombat();
			const bool bKilled = ApplyDamageEx(B, Pc ? Pc->GetOwner() : nullptr, nullptr, true, true);
			G->AddHitText(GetActorLocation() + FVector(0, 0, GetCapsuleComponent()->GetScaledCapsuleHalfHeight() + 40.f), B, false);
			if (bKilled && Pc) ++Pc->Kills;
		}
	}
	if (G->HuntedMark.Get() == this && !HasCurse11(ERDCurseEffect::Hunted)) G->HuntedMark = nullptr;
}

bool ARDMonster::TickFear(float Dt)
{
	if (!IsAfraid() || bAlly || bDead) return false;
	ARDDungeonGenerator* G = Section ? Section->Generator.Get() : nullptr;
	const URDCombatComponent* Pc = G ? G->GetPlayerCombat() : nullptr;
	const AActor* Her = Pc ? Pc->GetOwner() : nullptr;
	if (!Her) return false;
	// (it runs from her, its blow given up)
	FVector Away = (GetActorLocation() - Her->GetActorLocation()) * FVector(1, 1, 0);
	Away = Away.GetSafeNormal(1e-3f, -GetActorForwardVector());
	AttackTime = -1.f; bAggro = true;
	GetCharacterMovement()->MaxWalkSpeed = WalkSpeed * 1.4f * SpeedMul();
	AddMovementInput(Away, 1.f);
	SetActorRotation(FRotator(0.f, FMath::RInterpConstantTo(GetActorRotation(), Away.Rotation(), Dt, 540.f).Yaw, 0.f));
	SetWalkingAnim(true);
	return true;
}

// ================================================================================================ the generator's side
ARDMonster* ARDDungeonGenerator::GetHuntedMark() const { return HuntedMark.Get(); }

float ARDDungeonGenerator::TestHit11(ARDMonster* M, float Amount, FName Element)
{
	if (!IsValid(M) || M->IsDead()) return 0.f;
	const float H0 = M->GetHealth();
	const FName Was = HitElement; HitElement = Element;
	M->ApplyDamage(Amount, PlayerCombat ? PlayerCombat->GetOwner() : nullptr);
	HitElement = Was;
	return H0 - M->GetHealth();
}

bool ARDDungeonGenerator::HeroCanLearnSpell(const FRDSpellDef& S) const
{
	return HeroLearns(S.Type) && (S.OnlyHeroes.Num() == 0 || S.OnlyHeroes.Contains(CurrentHero));
}

// ================================================================================================ the release
void URDCombatComponent::ReleaseCurse11(const FRDSpellDef& S, int32 SpellIndex)
{
	AActor* O = GetOwner();
	if (!O || !Generator) return;
	const ERDCurseEffect E = S.CurseEffect;
	auto Mark = [&](ARDMonster* Mo, float Secs)
	{
		// (the curse shows on it while it lasts)
		if (UFXSystemComponent* C = SpawnSpellFx(S.AreaFx, FVector::ZeroVector, FRotator::ZeroRotator, S.AreaFxScale, &S, Mo->GetRootComponent())) TimedFx.Add({ C, Secs, true });
	};
	const bool bArea = E == ERDCurseEffect::Lethargy || E == ERDCurseEffect::Dread || E == ERDCurseEffect::Kinship;
	if (bArea)
	{
		const FVector At = SpellTargetPoint(S.Reach);
		SpawnSpellFx(S.ImpactFx, At, FRotator::ZeroRotator, S.ImpactFxScale, &S);
		TArray<ARDMonster*> In;
		for (ARDMonster* Mo : Generator->GetMonsters())
		{
			if (!Mo || Mo->IsDead() || Mo->IsAlly()) continue;
			const FVector P = Mo->GetActorLocation();
			if (FVector::Dist2D(P, At) - Mo->GetCapsuleComponent()->GetScaledCapsuleRadius() > S.Radius || FMath::Abs(P.Z - At.Z) > 320.f) continue;
			In.Add(Mo);
		}
		// (Kinship binds the four nearest its point)
		if (E == ERDCurseEffect::Kinship)
		{
			In.Sort([&At](const ARDMonster& A, const ARDMonster& B) { return FVector::DistSquared(A.GetActorLocation(), At) < FVector::DistSquared(B.GetActorLocation(), At); });
			if (In.Num() > FMath::Max(S.Count, 2)) In.SetNum(FMath::Max(S.Count, 2));
		}
		const int32 Group = E == ERDCurseEffect::Kinship ? ++Generator->KinGroupNext : -1;
		for (ARDMonster* Mo : In) { Mo->Curse11(E, S.Duration, S.Amount, NAME_None, Group); Mark(Mo, S.Duration); }
		CursesCast.FindOrAdd(S.Name) += In.Num();
		if (In.Num() == 0) SetMessage(FString::Printf(TEXT("%s touches no enemy"), *S.Name.ToString()));
		return;
	}
	ARDMonster* T = LastTarget.Get();
	if (!T || T->IsDead()) T = PickTarget(S.Reach, true);
	if (!T) { SetMessage(FString::Printf(TEXT("No enemy in front of you for %s"), *S.Name.ToString())); return; }
	SpawnSpellFx(S.ImpactFx, T->GetActorLocation(), FRotator::ZeroRotator, S.ImpactFxScale, &S);
	float Secs = S.Duration, Amount = S.Amount;
	FName Element = NAME_None;
	switch (E)
	{
	case ERDCurseEffect::Rot: Amount = T->GetMaxHealth() * S.Amount / FMath::Max(Secs, 0.1f); break;          // (S.Amount: its hit points' share over the time)
	case ERDCurseEffect::Silence: if (T->IsEliteOrBoss()) Secs *= 0.5f; break;
	case ERDCurseEffect::Hunted:
		// (one mark at a time)
		if (ARDMonster* Old = Generator->HuntedMark.Get(); Old && Old != T) Old->EndCurse11(ERDCurseEffect::Hunted);
		Generator->HuntedMark = T;
		break;
	case ERDCurseEffect::Ruin: Element = LastCastElement.IsNone() ? FName(TEXT("shadow")) : LastCastElement; break;
	default: break;
	}
	T->Curse11(E, Secs, Amount, Element);
	Mark(T, Secs);
	CursesCast.FindOrAdd(S.Name)++;
	if (E == ERDCurseEffect::Ruin) SetMessage(FString::Printf(TEXT("%s: %s"), *S.Name.ToString(), *Element.ToString()));
	UE_LOG(LogRDList11c, Log, TEXT("RDCURSE %s on %s for %.1f s (%.3f)"), *S.Name.ToString(), *T->MonsterName.ToString(), Secs, Amount);
}
