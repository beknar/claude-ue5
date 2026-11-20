// The user's list of 2026-11-20 (docs/improvements15.txt; the plan docs/improvements15_plan.md), its fifth phase: items.
// Item 15, "claiming a piece of equipment that is not a potion should not make the same [sound] a potion does, it should be some kind of
// thump or thud": what she takes sounds as gear (Player.Loot.Gear, 934 items: the Quest Game pack's heavy drop and heavy book, chosen by
// their measured low end) unless every thing is a potion. Item 17, "the ankh of revealing and torch should be able to be repaired via the
// repair items": each burns down while held lit (its Durability, seconds), goes out at 0, and the repair items restore it as they do
// armour (the repair list takes anything with a gear durability). Item 19, the teleporters' G on the pad: the right stick pressed
// (R3, used elsewhere only on an open map), and the prompts name the key of the device in use. Items 10, 12 and 16 are the stage's data,
// the traps' (RDTraps.cpp) and the ankh's (RDList10c.cpp).
#include "RD/RDDungeonGenerator.h"
#include "RD/RDCombat.h"
#include "Engine/World.h"
#include "GameFramework/PlayerController.h"
DEFINE_LOG_CATEGORY_STATIC(LogRDList15d, Log, All);

// ================================================================================================ item 15: the gear's thud
FName ARDDungeonGenerator::LootSound15(const TArray<FName>& Things) const
{
	static const FName Loot(TEXT("Player.Loot")), Gear(TEXT("Player.Loot.Gear"));
	if (!bGearThud15 || !Sounds.Contains(Gear)) return Loot;
	for (const FName& N : Things)
	{
		const int32 Ix = FindItem(N);
		const ERDItemKind K = Ix >= 0 ? Items[Ix].Kind : ERDItemKind::Component;
		if (K != ERDItemKind::Healing && K != ERDItemKind::Mana && K != ERDItemKind::Speed) return Gear;
	}
	return Things.Num() > 0 ? Loot : Gear;
}

bool ARDDungeonGenerator::DebugDropLoot15(FVector At, const TArray<FName>& Things)
{
	return DropLoot(At, Things, TArray<float>()) != nullptr;
}

// ================================================================================================ item 19: the teleporters' key
bool ARDDungeonGenerator::TripKeyPressed15(const APlayerController* PC) const
{
	if (!PC) return false;
	if (PC->WasInputKeyJustPressed(EKeys::G)) return true;
	// (the right stick pressed: free while no map is open in every layout (it centres an open map))
	return bPadTripButton15 && !bMapOpen && PC->WasInputKeyJustPressed(EKeys::Gamepad_RightThumbstick);
}

FString ARDDungeonGenerator::TripKeyName15() const
{
	return bPadTripButton15 && PlayerCombat && PlayerCombat->IsUsingGamepad() ? FString(TEXT("[R3]")) : FString(TEXT("[G]"));
}

// ================================================================================================ item 17: the light burns down
bool URDCombatComponent::IsBurningLight15(int32 Ix) const
{
	if (!Generator || !Generator->bLightBurn15 || !Generator->Items.IsValidIndex(Ix) || Generator->Items[Ix].Durability <= 0.f) return false;
	const ERDItemKind K = Generator->Items[Ix].Kind;
	return K == ERDItemKind::Torch || K == ERDItemKind::Light;
}

float URDCombatComponent::GetLightLeft15(FName Item) const
{
	const int32 Ix = Generator ? Generator->FindItem(Item) : -1;
	if (!IsBurningLight15(Ix)) return -1.f;
	const float* W = ArmourWear.Find(Item);
	return W ? *W : Generator->Items[Ix].Durability;
}

void URDCombatComponent::SetLightLeft15(FName Item, float Seconds)
{
	if (GetLightLeft15(Item) >= 0.f) ArmourWear.Add(Item, FMath::Max(0.f, Seconds));
}

void URDCombatComponent::TickLightBurn15(float Dt)
{
	if (!Generator || !bTorchHeld || TorchItem.IsNone() || Dt <= 0.f) return;
	const int32 Ix = Generator->FindItem(TorchItem);
	if (!IsBurningLight15(Ix)) return;
	float& W = ArmourWear.FindOrAdd(TorchItem, Generator->Items[Ix].Durability);
	W = FMath::Max(0.f, W - Dt);
	if (W > 0.f) return;
	// (burned down. One of several (a stack of torches shares this timer, PR #97's review) is used up and the next lit whole; the
	// last stays, burned out, until a repair item restores it)
	const FName It = TorchItem;
	if (GetItemCount(It) > 1)
	{
		RemoveCarried(It, 1); W = Generator->Items[Ix].Durability;
		SetMessage(FString::Printf(TEXT("The %s burns out; you light another (%d left)"), *It.ToString().ToLower(), GetItemCount(It)));
		return;
	}
	// (out, said once: forced out if HoldTorch refuses (she lies dead), or the message would come every tick)
	if (!HoldTorch(false)) { bTorchHeld = false; UpdateLeftHand(); }
	SetMessage(FString::Printf(TEXT("The %s has burned out: a repair item restores it"), *It.ToString().ToLower()));
	UE_LOG(LogRDList15d, Log, TEXT("RDLIGHT15 %s burned out"), *It.ToString());
}
