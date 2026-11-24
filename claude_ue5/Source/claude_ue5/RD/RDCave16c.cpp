// The user's list of 2026-11-22 (docs/improvements16.txt; the plan docs/improvements16_plan.md), its eleventh phase: the geodes
// cut at the librarian's table into scroll inks (each ink stands in for a scroll recipe's reagent: 945 items) or socket stones. A
// weapon or a set of armour holds one stone; a stone set in it adds its colour's bonus (the generator's SocketStones16) while the
// weapon is in her hands or the armour on her: red her blows, white a blow on her less, blue warmth and yellow cooling against the
// climate, green her hit points back, violet her speed.
#include "RD/RDCombat.h"
#include "RD/RDDungeonGenerator.h"

FString RDSocketWords16(const FRDSocket16& Sk);

FName URDCombatComponent::HandGear16() const { return WeaponGear16(WeaponIndex); }

float URDCombatComponent::GetSocketDamage16(int32 Index) const
{
	if (!Generator || Sockets16.Num() == 0) return 0.f;
	float B = 0.f;
	const FName Wg = WeaponGear16(Index);
	for (const FName Gear : { Wg, WornArmour == Wg ? NAME_None : WornArmour })
	{
		const FName* St = Gear.IsNone() ? nullptr : Sockets16.Find(Gear);
		const FRDSocket16* Sk = St ? Generator->SocketStones16.Find(*St) : nullptr;
		if (Sk && Sk->Stat == TEXT("damage")) B += Sk->Amount;
	}
	return B;
}

FName URDCombatComponent::WeaponGear16(int32 Index) const
{
	if (!Generator || !Generator->Weapons.IsValidIndex(Index)) return NAME_None;
	const FRDWeaponDef& W = Generator->Weapons[Index];
	if (W.bSpell && !W.BoltMesh) return NAME_None;          // (magic and chi attacks: no socket)
	if (W.bScroll) return NAME_None;
	return W.Item.IsNone() ? W.Name : W.Item;
}

float URDCombatComponent::GetSocketBonus16(FName Stat) const
{
	if (!Generator || Stat.IsNone() || Sockets16.Num() == 0) return 0.f;
	float B = 0.f;
	auto Add = [&](FName Gear)
	{
		const FName* St = Gear.IsNone() ? nullptr : Sockets16.Find(Gear);
		const FRDSocket16* Sk = St ? Generator->SocketStones16.Find(*St) : nullptr;
		if (Sk && Sk->Stat == Stat) B += Sk->Amount;
	};
	const FName Hand = HandGear16();
	Add(Hand);
	if (WornArmour != Hand) Add(WornArmour);
	return B;
}

bool URDCombatComponent::SetSocket16(FName Stone)
{
	if (!Generator || GetItemCount(Stone) <= 0) return false;
	const FRDSocket16* Sk = Generator->SocketStones16.Find(Stone);
	if (!Sk) return false;
	const FName Hand = HandGear16();
	FName Into;
	if (!Hand.IsNone() && !Sockets16.Contains(Hand)) Into = Hand;
	else if (!WornArmour.IsNone() && !Sockets16.Contains(WornArmour)) Into = WornArmour;
	// (both full: the one filled longer ago (PR #118's review: every stone went to the weapon's, the armour's never changed))
	else if (!Hand.IsNone() && !WornArmour.IsNone()) Into = SocketSerial16.FindRef(Hand) <= SocketSerial16.FindRef(WornArmour) ? Hand : WornArmour;
	else if (!Hand.IsNone()) Into = Hand;
	else if (!WornArmour.IsNone()) Into = WornArmour;
	if (Into.IsNone())
	{
		ShowMessage(TEXT("Nothing to set it in: take a weapon in your hands or wear armour"));
		return false;
	}
	FString Back;
	if (const FName* Old = Sockets16.Find(Into))
	{
		AddItem(*Old, 1);
		Back = FString::Printf(TEXT(" (the %s back in your pack)"), *Old->ToString().ToLower());
	}
	RemoveItem(Stone, 1);
	Sockets16.Add(Into, Stone); SocketSerial16.Add(Into, ++SocketNext16);
	UpdateWalkSpeed();
	ShowMessage(FString::Printf(TEXT("The %s is set in your %s%s"), *Stone.ToString().ToLower(), *Into.ToString(), *Back));
	return true;
}

TArray<FString> URDCombatComponent::GetSockets16() const
{
	TArray<FString> Out;
	const FName Hand = HandGear16();
	for (const TPair<FName, FName>& Kv : Sockets16)
	{
		const FRDSocket16* Sk = Generator ? Generator->SocketStones16.Find(Kv.Value) : nullptr;
		const bool bOn = Kv.Key == Hand || Kv.Key == WornArmour;
		Out.Add(FString::Printf(TEXT("socket|%s|%s|%s|%.3f|%d"), *Kv.Key.ToString(), *Kv.Value.ToString(), Sk ? *Sk->Stat.ToString() : TEXT(""), Sk ? Sk->Amount : 0.f, bOn ? 1 : 0));
	}
	return Out;
}

FString URDCombatComponent::SocketWords16(FName Gear, bool bGearIn) const
{
	if (!Generator || Generator->SocketStones16.Num() == 0 || Gear.IsNone()) return FString();
	const int32 Ix = Generator->FindItem(Gear);
	const bool bGear = bGearIn || (Ix >= 0 && (Generator->Items[Ix].Kind == ERDItemKind::Armour || Generator->Items[Ix].Kind == ERDItemKind::Weapon));
	if (const FName* St = Sockets16.Find(Gear))
	{
		const FRDSocket16* Sk = Generator->SocketStones16.Find(*St);
		return FString::Printf(TEXT("  Its socket holds a %s (%s)."), *St->ToString().ToLower(), Sk ? *RDSocketWords16(*Sk) : TEXT(""));
	}
	if (const FRDSocket16* Sk = Generator->SocketStones16.Find(Gear))
		return FString::Printf(TEXT("  Use it to set it in the weapon in your hands (or, if that holds a stone, the armour you wear): %s while that weapon is in your hands or that armour on you."), *RDSocketWords16(*Sk));
	return bGear ? FString(TEXT("  Its socket is empty: a socket stone (cut from a cave's geode) can be set in it.")) : FString();
}

FString RDSocketWords16(const FRDSocket16& Sk)
{
	const float P = Sk.Amount * 100.f;
	if (Sk.Stat == TEXT("damage")) return FString::Printf(TEXT("your blows %.0f%% stronger"), P);
	if (Sk.Stat == TEXT("guard")) return FString::Printf(TEXT("each blow on you %.0f%% less"), P);
	if (Sk.Stat == TEXT("warm")) return FString::Printf(TEXT("the cold %.0f%% slower"), P);
	if (Sk.Stat == TEXT("cool")) return FString::Printf(TEXT("the heat %.0f%% slower"), P);
	if (Sk.Stat == TEXT("regen")) return FString::Printf(TEXT("%.1f%% of your hit points back a second"), P);
	if (Sk.Stat == TEXT("speed")) return FString::Printf(TEXT("you move %.0f%% faster"), P);
	return Sk.Stat.ToString();
}

void URDCombatComponent::TickSockets16(float Dt)
{
	if (Sockets16.Num() == 0 || bDead) return;
	const float R = GetSocketBonus16(TEXT("regen"));
	if (R > 0.f && Health < MaxHealth) Health = FMath::Min(MaxHealth, Health + R * MaxHealth * Dt);
	// (a weapon drawn or put away changes the stones working: her speed set again when a violet one comes or goes)
	const float Sp = GetSocketBonus16(TEXT("speed"));
	if (!FMath::IsNearlyEqual(Sp, SocketSpeedSeen16)) { SocketSpeedSeen16 = Sp; UpdateWalkSpeed(); }
}
