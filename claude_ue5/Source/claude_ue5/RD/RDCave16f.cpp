// The user's list of 2026-11-22 (docs/improvements16.txt; the plan docs/improvements16_plan.md), its fourteenth phase: the charm
// slot, the Ring of the Echo, the glow-worm amulet, the miner's lucky stone, the cursed relics and the temple's lifting. The game had
// no amulet slot: a charm is a ring of a kind of its own (ERDRingKind::Charm), worn one at a time beside her rings, so it goes with
// her between the levels, into the save and her pile as the rings do. The Echo and the lucky stone are rings of kinds of their own.
// A charm's good and its cost are the generator's Charms16 (a stat and a share each); a cursed relic's cost is gone once a temple has
// lifted it (the game instance's LiftedRelics16, for that relic wherever she has it).
#include "RD/RDDungeonGenerator.h"
#include "RD/RDCombat.h"
#include "RD/RDGameInstance.h"
#include "RD/RDMonster.h"
#include "Engine/World.h"
DEFINE_LOG_CATEGORY_STATIC(LogRDCave16f, Log, All);

/** a lifting's price grows with the game's tier, as the temple's other services */
static float RDLiftTierScale16(int32 T) { return 1.f + 0.25f * (float)FMath::Max(T - 1, 0); }

// ================================================================================================ her charm
float URDCombatComponent::GetCharm16(FName Stat) const
{
	if (!Generator || Stat.IsNone()) return 0.f;
	const FName C = GetWornRing(ERDRingKind::Charm);
	const FRDCharm16* Ch = C.IsNone() ? nullptr : Generator->Charms16.Find(C);
	if (!Ch) return 0.f;
	float V = 0.f;
	if (Ch->Good == Stat) V += Ch->GoodAmount;
	if (Ch->Cost == Stat && !Generator->IsRelicLifted16(C)) V += Ch->CostAmount;
	return V;
}

void URDCombatComponent::TickCharms16(float Dt)
{
	if (bDead || !Generator || GetWornRing(ERDRingKind::Charm).IsNone()) return;
	// (a bleeding relic: a share of her hit points a second, never her last one)
	const float B = GetCharm16(TEXT("bleed"));
	if (B > 0.f && Health > 1.f)
	{
		BleedAcc16 += B * MaxHealth * Dt;
		if (BleedAcc16 >= 1.f) { const float D = FMath::FloorToFloat(BleedAcc16); BleedAcc16 -= D; Health = FMath::Max(1.f, Health - D); BledTotal16 += D; }
	}
	// (a charm's speed comes or goes with it: her top speed set again)
	const float Sp = GetCharm16(TEXT("speed"));
	if (!FMath::IsNearlyEqual(Sp, CharmSpeedSeen16)) { CharmSpeedSeen16 = Sp; UpdateWalkSpeed(); }
}

FString URDCombatComponent::CharmWords16(const FRDItemDef& It) const
{
	if (!Generator) return FString();
	auto Words = [](FName S, float A) -> FString
	{
		const float P = FMath::Abs(A) * 100.f;
		if (S == TEXT("damage")) return FString::Printf(TEXT("your blows %.0f%% %s"), P, A >= 0.f ? TEXT("stronger") : TEXT("weaker"));
		if (S == TEXT("guard")) return FString::Printf(TEXT("each blow on you %.0f%% %s"), P, A >= 0.f ? TEXT("less") : TEXT("more"));
		if (S == TEXT("speed")) return FString::Printf(TEXT("you move %.0f%% %s"), P, A >= 0.f ? TEXT("faster") : TEXT("slower"));
		if (S == TEXT("gold")) return FString::Printf(TEXT("%.0f%% more gold"), P);
		if (S == TEXT("notice")) return FString::Printf(TEXT("monsters notice you from %.0f%% %s"), P, A >= 0.f ? TEXT("farther") : TEXT("nearer"));
		if (S == TEXT("maxhp")) return FString::Printf(TEXT("%.0f%% %s hit points"), P, A >= 0.f ? TEXT("more") : TEXT("fewer"));
		if (S == TEXT("bleed")) return FString::Printf(TEXT("you bleed %.1f%% of your hit points a second (never your last)"), P);
		if (S == TEXT("light")) return FString::Printf(TEXT("a faint light of %.0f m round you, no torch needed"), A);
		return S.ToString();
	};
	if (It.RingKind == ERDRingKind::Echo) return FString::Printf(TEXT("While you wear it, monsters within %.0f m show on your maps as dim pings, seen or not."), It.Amount);
	if (It.RingKind == ERDRingKind::Lucky) return FString::Printf(TEXT("While you wear it, a vein or a growth you harvest gives %.0f%% more."), It.Amount * 100.f);
	const FRDCharm16* Ch = Generator->Charms16.Find(It.Name);
	if (!Ch) return TEXT("A charm: one at a time, beside your rings.");
	FString S = FString::Printf(TEXT("A charm (one at a time, beside your rings): %s."), *Words(Ch->Good, Ch->GoodAmount));
	if (!Ch->Cost.IsNone())
	{
		const bool bLifted = Generator->IsRelicLifted16(It.Name);
		S += bLifted ? FString::Printf(TEXT("  Its curse is lifted (it was: %s)."), *Words(Ch->Cost, Ch->CostAmount))
		             : FString::Printf(TEXT("  Cursed: %s.  A temple can lift the curse for gold."), *Words(Ch->Cost, Ch->CostAmount));
	}
	return S;
}

// ================================================================================================ the lifting
bool ARDDungeonGenerator::IsRelicLifted16(FName Relic) const
{
	const URDGameInstance* GI = URDGameInstance::Of(this);
	return GI && GI->LiftedRelics16.Contains(Relic);
}

int32 ARDDungeonGenerator::LiftPrice16(FName Relic) const
{
	const FRDCharm16* Ch = Charms16.Find(Relic);
	return Ch ? FMath::RoundToInt(Ch->LiftPrice * RDLiftTierScale16(GetGameTier())) : 0;
}

TArray<FString> ARDDungeonGenerator::GetLiftLines16() const
{
	// (a cursed relic she carries, not lifted yet: "lift|<relic>|<price>")
	TArray<FString> Out;
	if (!PlayerCombat) return Out;
	for (const TPair<FName, FRDCharm16>& Kv : Charms16)
		if (!Kv.Value.Cost.IsNone() && PlayerCombat->GetItemCount(Kv.Key) > 0 && !IsRelicLifted16(Kv.Key))
			Out.Add(FString::Printf(TEXT("lift|%s|%d"), *Kv.Key.ToString(), LiftPrice16(Kv.Key)));
	return Out;
}

bool ARDDungeonGenerator::TownLiftCurse16(const FString& Arg)
{
	URDGameInstance* GI = URDGameInstance::Of(this);
	const FName Relic(*Arg);
	const FRDCharm16* Ch = Charms16.Find(Relic);
	if (!GI || !PlayerCombat || !Ch || Ch->Cost.IsNone() || PlayerCombat->GetItemCount(Relic) <= 0) return false;
	if (IsRelicLifted16(Relic)) { SetTownNote(TEXT("Its curse is lifted already")); return false; }
	const int32 Price = LiftPrice16(Relic);
	if (GI->Gold < Price) { SetTownNote(FString::Printf(TEXT("The priest asks %d gold to lift it"), Price)); return false; }
	GI->Gold -= Price;
	GI->LiftedRelics16.AddUnique(Relic);
	PlayerCombat->RefreshMaxima();          // (her speed follows on her next tick: TickCharms16)
	SetTownNote(FString::Printf(TEXT("The priest lifts the curse from the %s"), *Relic.ToString()));
	UE_LOG(LogRDCave16f, Log, TEXT("RDCAVE16 the curse of %s lifted for %d gold"), *Relic.ToString(), Price);
	return true;
}

// ================================================================================================ the Echo's pings
void ARDDungeonGenerator::EchoPings16(const FVector& Her, float SenseCm, TArray<FVector2D>& Out) const
{
	Out.Reset();
	if (!PlayerCombat) return;
	const FName Ring = PlayerCombat->GetWornRing(ERDRingKind::Echo);
	const int32 Ix = Ring.IsNone() ? -1 : FindItem(Ring);
	if (Ix < 0) return;
	const float R = Items[Ix].Amount * 100.f;
	for (const ARDMonster* Mo : GetMonsters())
	{
		if (!Mo || Mo->IsDead()) continue;
		const float D = FVector::Dist2D(Mo->GetActorLocation(), Her);
		if (D > SenseCm && D <= R && FMath::Abs(Mo->GetActorLocation().Z - Her.Z) < 1200.f) Out.Add(FVector2D(Mo->GetActorLocation()));
	}
}

// ================================================================================================ the lucky stone
void ARDDungeonGenerator::LuckyHarvest16(TArray<FName>& Things) const
{
	// (more from a vein or a growth while the lucky stone is worn: its share of each of the caves' node things, rounded up)
	if (!PlayerCombat) return;
	const FName Ring = PlayerCombat->GetWornRing(ERDRingKind::Lucky);
	const int32 Ix = Ring.IsNone() ? -1 : FindItem(Ring);
	if (Ix < 0 || CaveNodes16.Num() == 0) return;
	TMap<FName, int32> N;
	for (const FName& T : Things) if (CaveNodes16.ContainsByPredicate([&T](const FRDCaveNode16& Nd) { return Nd.Item == T; })) ++N.FindOrAdd(T);
	for (const TPair<FName, int32>& Kv : N)
		for (int32 K = 0, More = FMath::CeilToInt(Kv.Value * Items[Ix].Amount); K < More; ++K) Things.Add(Kv.Key);
}
