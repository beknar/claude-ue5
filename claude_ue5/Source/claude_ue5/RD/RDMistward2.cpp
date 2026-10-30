// mistward_castle and random_dungeonmagic_level5: the user's third list (docs/improvements2.txt, 2026-10-27). Each rule is a
// switch of the generator ("Mistward2"), off on the other levels:
//   bTrapOutline     a trap the Rogue has seen: its plate or rune outlined in red, a red ring on the floor at its reach
//   bInventoryTabs   the inventory in five tabs (Q / E, LB / RB, a click), found weapons stacked, the anvil's counts
//   bQuickSlots      ten quick slots (1 to 0, the D-pad left / right), filled from the inventory
//   bHelmetToggle    H shows or hides the worn set's helmet
//   bShieldBlock     the Warrior blocks with her shield (the right mouse button or LT held)
//   bKeepStartGear   her starting weapon and shield never break and never drop
//   bWeaponPickups   the armories' tables hold weapons and shields of the tier, taken up with F
//   bSpecialRooms    shrines, healing / speed / mana fountains, arenas, trap gauntlets, vaults and their keys, throne rooms
//   bBossSlashes         a boss gives the Warrior a slash (the Stylized Slashes pack): it goes on a weapon, comes off, goes on another
#include "RD/RDCombat.h"
#include "RD/RDDungeonGenerator.h"
#include "RD/RDSection.h"
#include "RD/RDMonster.h"
#include "RD/RDMistward.h"
#include "Components/StaticMeshComponent.h"
#include "Components/SkeletalMeshComponent.h"
#include "Components/PointLightComponent.h"
#include "Components/CapsuleComponent.h"
#include "Engine/StaticMesh.h"
#include "Engine/SkeletalMesh.h"
#include "Engine/World.h"
#include "GameFramework/Character.h"
#include "GameFramework/CharacterMovementComponent.h"
#include "GameFramework/PlayerController.h"
#include "Kismet/GameplayStatics.h"
#include "NiagaraComponent.h"
#include "NiagaraSystem.h"
#include "Animation/AnimInstance.h"
#include "Animation/AnimMontage.h"
#include "Animation/AnimSequenceBase.h"
#include "Materials/MaterialInterface.h"
#include "Algo/Reverse.h"
#include "Algo/Sort.h"
#include "Rendering/SkeletalMeshRenderData.h"
#include "Rendering/SkeletalMeshLODRenderData.h"
#include "Rendering/SkinWeightVertexBuffer.h"

DEFINE_LOG_CATEGORY_STATIC(LogRDMistward2, Log, All);

static const FName RDM2Slot(TEXT("DefaultSlot"));
static const FName RDM2Interactive(TEXT("RDInteractive"));
/** an effect that does not destroy itself, ended for good: a pack's system outlives a plain Deactivate */
static void RDM2EndFx(UFXSystemComponent* F) { if (F) { F->DeactivateImmediate(); F->DestroyComponent(); } }
/** how far a knock carries a monster for each cm/s of launch speed (measured: 300 cm/s, 1.09 m) */
static constexpr float RDM2KnockCmPerSpeed = 0.36f;

/** a share (0..1) from a hash: the third list's rolls draw from no stream the play uses */
static float RDM2Roll(uint32 A, uint32 B) { return (float)(HashCombine(A, B * 2654435761u + 0x9E37u) % 100000u) / 100000.f; }

static FString RDM2EffectName(ERDSlashEffect E)
{
	switch (E)
	{
	case ERDSlashEffect::Burn: return TEXT("burn"); case ERDSlashEffect::Slow: return TEXT("slow"); case ERDSlashEffect::Poison: return TEXT("poison");
	case ERDSlashEffect::Swift: return TEXT("swift"); case ERDSlashEffect::Drain: return TEXT("drain"); case ERDSlashEffect::Knockback: return TEXT("knockback");
	case ERDSlashEffect::Regen: return TEXT("regen"); case ERDSlashEffect::Evade: return TEXT("evade"); case ERDSlashEffect::Shield: return TEXT("shield");
	case ERDSlashEffect::Chain: return TEXT("chain"); case ERDSlashEffect::Blind: return TEXT("blind"); case ERDSlashEffect::Tide: return TEXT("tide");
	case ERDSlashEffect::Inferno: return TEXT("inferno"); case ERDSlashEffect::Curse: return TEXT("curse"); case ERDSlashEffect::Haste: return TEXT("haste");
	case ERDSlashEffect::Deflect: return TEXT("deflect"); case ERDSlashEffect::Magma: return TEXT("magma"); case ERDSlashEffect::Void: return TEXT("void");
	case ERDSlashEffect::Stun: return TEXT("stun"); default: return TEXT("prismatic");
	}
}

// ================================================================================================ the inventory's tabs and stacks
int32 URDCombatComponent::TabOfLine(const FString& Line)
{
	FString Kind; if (!Line.Split(TEXT("|"), &Kind, nullptr)) Kind = Line;
	if (Kind == TEXT("weapon") || Kind == TEXT("carried") || Kind == TEXT("ability")) return 0;
	if (Kind == TEXT("armour") || Kind == TEXT("shield") || Kind == TEXT("torch") || Kind == TEXT("helmet")) return 1;
	if (Kind == TEXT("item")) return 2;
	if (Kind == TEXT("component") || Kind == TEXT("repair")) return 3;
	return 4;          // (rings, tomes, teleport rings, slashes, keys)
}

void URDCombatComponent::SetInventoryTab(int32 Tab)
{
	const int32 T = ((Tab % NumTabs) + NumTabs) % NumTabs;
	if (T == InvTab) return;
	InvTab = T; InventoryCursor = 0; ResetListView();
	PlayUiSound(TEXT("Player.Inventory"), TEXT("Player.Inventory"));
}

TArray<FString> URDCombatComponent::TabLines(int32 Tab) const
{
	TArray<FString> Out;
	for (const FString& L : GetAllInventoryLines()) if (TabOfLine(L) == Tab) Out.Add(L);
	return Out;
}

void URDCombatComponent::StackedWeaponLines(TArray<FString>& Out) const
{
	// (copies of a found weapon as worn as each other, with the same slash, are one line: "x 3"; the one in her hands stays a
	// line of its own)
	struct FRow { FString Key; int32 Index; int32 Count; };
	TArray<FRow> Rows;
	for (int32 I = 0; I < Generator->Weapons.Num(); ++I)
	{
		const FRDWeaponDef& W = Generator->Weapons[I];
		const FString Key = W.Item.IsNone() || I == WeaponIndex ? FString::Printf(TEXT("#%d"), I)
			: FString::Printf(TEXT("%s|%.0f|%s"), *W.Item.ToString(), GetWeaponWear(I), *W.Slash.ToString());
		FRow* R = Rows.FindByPredicate([&Key](const FRow& X) { return X.Key == Key; });
		if (R) ++R->Count; else Rows.Add({ Key, I, 1 });
	}
	for (const FRow& R : Rows)
	{
		const FRDWeaponDef& W = Generator->Weapons[R.Index];
		Out.Add(FString::Printf(TEXT("weapon|%s|%.0f|%.0f|%d|%d|%s"), *W.Name.ToString(), W.Durability > 0.f ? GetWeaponWear(R.Index) : 0.f, W.Durability, R.Index, R.Count,
			W.Slash.IsNone() ? TEXT("") : *W.Slash.ToString()));
	}
}

// ================================================================================================ quick slots
int32 URDCombatComponent::WeaponOfSlot(int32 Slot) const
{
	if (!Generator || !QuickSlots.IsValidIndex(Slot) || QuickSlots[Slot].IsNone() || IsAbility(QuickSlots[Slot])) return -1;
	const FName N = QuickSlots[Slot];
	if (Generator->Weapons.IsValidIndex(WeaponIndex) && Generator->Weapons[WeaponIndex].Name == N) return WeaponIndex;
	for (int32 I = 0; I < Generator->Weapons.Num(); ++I) if (Generator->Weapons[I].Name == N && !Generator->Weapons[I].bAlongside) return I;
	return -1;
}

int32 URDCombatComponent::GetQuickSlotOfDrawn() const
{
	if (!Generator || !Generator->Weapons.IsValidIndex(WeaponIndex)) return -1;
	return QuickSlots.IndexOfByKey(Generator->Weapons[WeaponIndex].Name);
}

void URDCombatComponent::FillQuickSlots()
{
	if (!Generator) return;
	if (QuickSlots.Num() < 10) QuickSlots.SetNum(10);
	// (a slot naming a weapon she has no more, or an ability not her hero's, is empty; each weapon or spell of hers not on the
	// bar and not taken off it goes into the first empty slot, or a new one at the end: the bar holds them all (the user's of
	// 2026-10-29: the Martial Artist's eleventh, Spinning Kick, had no slot and the D-pad never reached it))
	const TArray<FName> Ab = GetAbilities();
	for (FName& N : QuickSlots)
		if (!N.IsNone() && (IsAbility(N) ? !Ab.Contains(N) : !Generator->Weapons.ContainsByPredicate([&N](const FRDWeaponDef& W) { return W.Name == N && !W.bAlongside; }))) N = NAME_None;
	for (const FRDWeaponDef& W : Generator->Weapons)
	{
		if (W.bAlongside || QuickSlots.Contains(W.Name) || QuickOff.Contains(W.Name)) continue;
		const int32 E = QuickSlots.IndexOfByKey(NAME_None);
		if (E == INDEX_NONE) QuickSlots.Add(W.Name); else QuickSlots[E] = W.Name;
	}
	CompactQuickTail();
	if (!ReadyAbility.IsNone() && !QuickSlots.Contains(ReadyAbility)) ReadyAbility = NAME_None;
	LastWeaponCount = Generator->Weapons.Num(); LastWeaponSig = WeaponSig();
	UpdateQuickFirst();
}

TArray<FName> URDCombatComponent::GetAbilities() const
{
	TArray<FName> Out;
	if (!Generator) return Out;
	if (Generator->RollClip && Generator->bRogueControls) Out.Add(TEXT("@Dodge"));
	// (both made with the attack button when ready: the Rogue's controls' (the PR review's find: a dash readied under other
	// controls could never be made))
	if (Generator->DashClip && Generator->bRogueControls) Out.Add(TEXT("@Dash"));
	return Out;
}

bool URDCombatComponent::UseAbility(FName Ability)
{
	if (!GetAbilities().Contains(Ability)) return false;
	const bool bDone = Ability == TEXT("@Dash") ? StartDash() : StartRoll(FVector::ZeroVector);
	// (made: no longer ready; refused (still in a move): it stays ready for the next press (the PR review's find))
	if (bDone) { ++AbilitiesUsed; ReadyAbility = NAME_None; }
	UpdateQuickFirst();
	return bDone;
}

int32 URDCombatComponent::GetQuickCursor() const
{
	if (!ReadyAbility.IsNone()) { const int32 R = QuickSlots.IndexOfByKey(ReadyAbility); if (R != INDEX_NONE) return R; }
	return GetQuickSlotOfDrawn();
}

void URDCombatComponent::CompactQuickTail()
{
	// (an empty slot past the tenth is dropped and the ones after it close up: moving one from slot 11 to a new slot left a
	// hole the D-pad and the counters stepped over (the PR review's find); the first ten keep their numbers, empty or not)
	for (int32 I = QuickSlots.Num() - 1; I >= 10; --I) if (QuickSlots[I].IsNone()) QuickSlots.RemoveAt(I);
}

void URDCombatComponent::UpdateQuickFirst()
{
	// (the bar shows ten slots: the chosen one stays in sight, the view moving no more than it must)
	const int32 Cur = GetQuickCursor(), Last = FMath::Max(0, QuickSlots.Num() - 10);
	if (Cur >= 0) { if (Cur < QuickFirst) QuickFirst = Cur; else if (Cur >= QuickFirst + 10) QuickFirst = Cur - 9; }
	QuickFirst = FMath::Clamp(QuickFirst, 0, Last);
}

uint32 URDCombatComponent::WeaponSig() const
{
	uint32 H = Generator ? (uint32)Generator->Weapons.Num() : 0u;
	if (Generator) for (const FRDWeaponDef& W : Generator->Weapons) H = HashCombine(H, GetTypeHash(W.Name));
	return H;
}

bool URDCombatComponent::AssignQuickSlot(int32 Slot, int32 Index)
{
	if (!Generator || !Generator->Weapons.IsValidIndex(Index)) return false;
	const FRDWeaponDef& W = Generator->Weapons[Index];
	if (W.bAlongside) { SetMessage(FString::Printf(TEXT("%s is always at hand: it takes no slot"), *W.Name.ToString())); return false; }
	return AssignQuickEntry(Slot, W.Name);
}

bool URDCombatComponent::AssignQuickEntry(int32 Slot, FName Entry)
{
	if (!Generator || Entry.IsNone()) return false;
	const bool bAbility = IsAbility(Entry);
	if (bAbility ? !GetAbilities().Contains(Entry) : !Generator->Weapons.ContainsByPredicate([&Entry](const FRDWeaponDef& W) { return W.Name == Entry && !W.bAlongside; })) return false;
	if (QuickSlots.Num() < 10) QuickSlots.SetNum(10);
	if (Slot < 0 || Slot > QuickSlots.Num()) return false;
	const FString Nm = bAbility ? Entry.ToString().Mid(1) : Entry.ToString();
	const int32 From = QuickSlots.IndexOfByKey(Entry);
	if (From == Slot)
	{
		// (put where it is: off the bar, and kept off)
		QuickSlots[Slot] = NAME_None; QuickOff.Add(Entry);
		if (ReadyAbility == Entry) ReadyAbility = NAME_None;
		CompactQuickTail();
		SetMessage(FString::Printf(TEXT("%s is off the quick bar"), *Nm));
	}
	else
	{
		if (Slot == QuickSlots.Num()) QuickSlots.Add(NAME_None);
		// (the one in that slot goes where this came from: the two change places)
		const FName Was = QuickSlots[Slot];
		if (From != INDEX_NONE) QuickSlots[From] = Was;
		QuickSlots[Slot] = Entry; QuickOff.Remove(Entry);
		// (coming from off the bar: the one it took the place of goes to the first empty slot, or a new one at the end)
		if (From == INDEX_NONE && !Was.IsNone())
		{
			const int32 E = QuickSlots.IndexOfByKey(NAME_None);
			if (E == INDEX_NONE) QuickSlots.Add(Was); else QuickSlots[E] = Was;
		}
		CompactQuickTail();
		SetMessage(FString::Printf(TEXT("%s in quick slot %s"), *Nm, *SlotLabel(Slot)));
	}
	PlayUiSound(TEXT("Player.Inventory"), TEXT("Player.Inventory"));
	UpdateQuickFirst();
	return true;
}

bool URDCombatComponent::SelectQuickSlot(int32 Slot)
{
	if (QuickSlots.IsValidIndex(Slot) && IsAbility(QuickSlots[Slot])) return UseAbility(QuickSlots[Slot]);
	const int32 I = WeaponOfSlot(Slot);
	if (I < 0) return false;
	ReadyAbility = NAME_None;
	if (I != WeaponIndex) SelectWeapon(I);
	UpdateQuickFirst();
	return true;
}

void URDCombatComponent::CycleQuickSlot(int32 Step)
{
	// (every slot of the bar, the ones past the tenth too; an ability is made ready, not made)
	const int32 N = QuickSlots.Num();
	if (N == 0) return;
	const int32 From = GetQuickCursor();
	for (int32 K = 1; K <= N; ++K)
	{
		const int32 S = (((From < 0 ? (Step > 0 ? -1 : 0) : From) + Step * K) % N + N) % N;
		if (!QuickSlots.IsValidIndex(S) || QuickSlots[S].IsNone()) continue;
		if (IsAbility(QuickSlots[S]))
		{
			if (!GetAbilities().Contains(QuickSlots[S])) continue;
			ReadyAbility = QuickSlots[S];
			SetMessage(FString::Printf(TEXT("%s ready: the attack button makes it"), *QuickSlots[S].ToString().Mid(1)));
			PlayUiSound(TEXT("Player.Draw"), TEXT("Player.Inventory"));
			UpdateQuickFirst();
			return;
		}
		const int32 Wi = WeaponOfSlot(S);
		if (Wi < 0) continue;
		if (Wi == WeaponIndex && ReadyAbility.IsNone()) continue;
		ReadyAbility = NAME_None;
		if (Wi != WeaponIndex) SelectWeapon(Wi);
		UpdateQuickFirst();
		return;
	}
}

// ================================================================================================ the helmet
// (a set of armour is one mesh: its helmet is the sections whose vertices her head bone (or one under it) moves, measured on
// the mesh's own skin weights: (LOD, section, vertices) of each)
static TArray<FIntVector> RDM2HelmetSections(const USkeletalMeshComponent* C)
{
	TArray<FIntVector> Out;
	USkeletalMesh* M = C ? C->GetSkeletalMeshAsset() : nullptr;
	const FSkeletalMeshRenderData* RD = M ? M->GetResourceForRendering() : nullptr;
	if (!RD) return Out;
	const FReferenceSkeleton& RS = M->GetRefSkeleton();
	const int32 Head = RS.FindBoneIndex(TEXT("head"));
	if (Head == INDEX_NONE) return Out;
	auto UnderHead = [&](int32 B) { while (B != INDEX_NONE) { if (B == Head) return true; B = RS.GetParentIndex(B); } return false; };
	for (int32 L = 0; L < RD->LODRenderData.Num(); ++L)
	{
		const FSkeletalMeshLODRenderData& LOD = RD->LODRenderData[L];
		const FSkinWeightVertexBuffer* SW = LOD.GetSkinWeightVertexBuffer();
		if (!SW || !SW->GetNeedsCPUAccess() || SW->GetNumVertices() == 0) continue;
		for (int32 S = 0; S < LOD.RenderSections.Num(); ++S)
		{
			const FSkelMeshRenderSection& Sec = LOD.RenderSections[S];
			int32 Hd = 0, Num = 0;
			const uint32 Step = FMath::Max<uint32>(1, Sec.NumVertices / 400);
			for (uint32 V = Sec.BaseVertexIndex; V < Sec.BaseVertexIndex + Sec.NumVertices && V < SW->GetNumVertices(); V += Step)
			{
				const FSkinWeightInfo Wi = SW->GetVertexSkinWeights(V);
				int32 Best = -1; uint16 BestW = 0;
				for (int32 K = 0; K < MAX_TOTAL_INFLUENCES; ++K) if (Wi.InfluenceWeights[K] > BestW && Sec.BoneMap.IsValidIndex(Wi.InfluenceBones[K])) { BestW = Wi.InfluenceWeights[K]; Best = Sec.BoneMap[Wi.InfluenceBones[K]]; }
				++Num; if (Best >= 0 && UnderHead(Best)) ++Hd;
			}
			if (Num > 0 && Hd >= Num * 0.7f) Out.Add(FIntVector(L, S, (int32)Sec.NumVertices));
		}
	}
	return Out;
}

TArray<USkeletalMeshComponent*> URDCombatComponent::GetHelmetMeshes() const
{
	TArray<USkeletalMeshComponent*> Out;
	for (USkeletalMeshComponent* C : ArmourComps) if (C && RDM2HelmetSections(C).Num() > 0) Out.Add(C);
	return Out;
}

bool URDCombatComponent::HasHelmet() const
{
	// (the sections are read from the mesh's skin weights: once for the set she wears; the inventory's lines ask for it
	// several times a frame (the PR review's find))
	if (HelmetCacheFor != WornArmour || HelmetCacheMeshes != ArmourComps.Num()) { HelmetCacheFor = WornArmour; HelmetCacheMeshes = ArmourComps.Num(); bHelmetCache = GetHelmetMeshes().Num() > 0; }
	return bHelmetCache;
}

TArray<FString> URDCombatComponent::GetHelmetLines() const
{
	TArray<FString> Out;
	for (USkeletalMeshComponent* C : ArmourComps)
		for (const FIntVector& H : RDM2HelmetSections(C))
			Out.Add(FString::Printf(TEXT("%s|%d|%d|%d|%d"), *C->GetSkeletalMeshAsset()->GetName(), H.X, H.Y, H.Z, bHelmetHidden ? 1 : 0));
	return Out;
}

void URDCombatComponent::UpdateHelmet()
{
	for (USkeletalMeshComponent* C : ArmourComps)
	{
		if (!C) continue;
		const FSkeletalMeshRenderData* RD = C->GetSkeletalMeshAsset() ? C->GetSkeletalMeshAsset()->GetResourceForRendering() : nullptr;
		for (const FIntVector& H : RDM2HelmetSections(C))
			if (RD && RD->LODRenderData.IsValidIndex(H.X) && RD->LODRenderData[H.X].RenderSections.IsValidIndex(H.Y))
				C->ShowMaterialSection(RD->LODRenderData[H.X].RenderSections[H.Y].MaterialIndex, H.Y, !bHelmetHidden, H.X);
	}
}

bool URDCombatComponent::ToggleHelmet()
{
	if (!Generator || !Generator->bHelmetToggle) return false;
	if (!HasHelmet()) { SetMessage(WornArmour.IsNone() ? FString(TEXT("You wear no armour")) : FString::Printf(TEXT("The %s has no helmet"), *WornArmour.ToString().ToLower())); return false; }
	bHelmetHidden = !bHelmetHidden;
	UpdateHelmet();
	SetMessage(bHelmetHidden ? TEXT("Helmet hidden (H shows it again)") : TEXT("Helmet shown"));
	PlayUiSound(TEXT("Player.Inventory"), TEXT("Player.Inventory"));
	return true;
}

// ================================================================================================ blocking
void URDCombatComponent::SetBlocking(bool bOn)
{
	if (!Generator) return;
	// (only a hero who blocks, with a shield in her hand, standing, not swinging)
	if (bOn && (!Generator->HeroBlocks() || !IsShieldInHand() || bDead || AttackTime >= 0.f || RollTime >= 0.f || bInventoryOpen || bCraftOpen)) bOn = false;
	if (bOn == bBlocking) return;
	bBlocking = bOn;
	UpdateWalkSpeed();
	USkeletalMeshComponent* M = Body();
	UAnimInstance* AI = M ? M->GetAnimInstance() : nullptr;
	const TObjectPtr<UAnimSequenceBase>* Clip = Generator->BlockClip.Find(Generator->CurrentHero);
	if (AI && Clip && *Clip)
	{
		if (bOn)
		{
			// (the shield raised: the clip's moment held while she blocks)
			const float* T = Generator->BlockClipTime.Find(Generator->CurrentHero);
			if (UAnimMontage* Mo = AI->PlaySlotAnimationAsDynamicMontage(*Clip, RDM2Slot, 0.12f, 0.18f, 1.f, 1, -1.f, T ? *T : 0.f))
			{
				Mo->bEnableAutoBlendOut = false;
				AI->Montage_Pause(Mo);
				BlockMontage = Mo;
			}
		}
		else if (UAnimMontage* Mo = BlockMontage.Get())
		{
			AI->Montage_Resume(Mo);
			AI->Montage_Stop(0.18f, Mo);
			BlockMontage = nullptr;
		}
	}
	if (bOn) PlayUiSound(TEXT("Player.Draw"), TEXT("Player.Inventory"));
}

void URDCombatComponent::TickBlocking(const APlayerController* PC)
{
	if (!Generator || !Generator->HeroBlocks()) { if (bBlocking) SetBlocking(false); return; }
	const bool bDown = PC && (PC->IsInputKeyDown(EKeys::RightMouseButton) || PC->IsInputKeyDown(EKeys::Gamepad_LeftTrigger) || PC->GetInputAnalogKeyState(EKeys::Gamepad_LeftTriggerAxis) > 0.5f);
	bBlockKeyDown = bDown;
	if (!bScriptedOnly && bDown != bBlocking) SetBlocking(bDown);
}

// ================================================================================================ input of the third list (outside the inventory)
void URDCombatComponent::TickThirdListInput(const APlayerController* PC)
{
	if (!PC || !Generator || bInventoryOpen || bCraftOpen || bDead) return;
	if (Generator->bQuickSlots)
	{
		static const FKey Nums[10] = { EKeys::One, EKeys::Two, EKeys::Three, EKeys::Four, EKeys::Five, EKeys::Six, EKeys::Seven, EKeys::Eight, EKeys::Nine, EKeys::Zero };
		for (int32 K = 0; K < 10; ++K) if (PC->WasInputKeyJustPressed(Nums[K])) SelectQuickSlot(K);
		if (!Generator->bMapOpen)
		{
			if (PC->WasInputKeyJustPressed(EKeys::Gamepad_DPad_Right)) CycleQuickSlot(1);
			if (PC->WasInputKeyJustPressed(EKeys::Gamepad_DPad_Left)) CycleQuickSlot(-1);
		}
	}
	if (Generator->bHelmetToggle && PC->WasInputKeyJustPressed(EKeys::H)) ToggleHelmet();
}

// ================================================================================================ slashes
const FRDSlashDef* URDCombatComponent::SlashOf(int32 Index) const
{
	if (!Generator || !Generator->bBossSlashes || !Generator->Weapons.IsValidIndex(Index) || Generator->Weapons[Index].Slash.IsNone()) return nullptr;
	const int32 S = Generator->FindSlash(Generator->Weapons[Index].Slash);
	return S >= 0 ? &Generator->Slashes[S] : nullptr;
}

bool URDCombatComponent::BeginSlash(FName Slash)
{
	if (!Generator || bDead || GetItemCount(Slash) <= 0 || Generator->FindSlash(Slash) < 0) return false;
	if (!Generator->HeroSlashes()) { SetMessage(FString::Printf(TEXT("Only a warrior's weapons take the %s"), *Slash.ToString().ToLower())); return false; }
	SlashWith = Slash; SlashCursor = 0;
	if (GetSlashLines().Num() == 0) { SlashWith = NAME_None; SetMessage(TEXT("You have no weapon to put it on")); return false; }
	ResetListView();
	SetMessage(FString::Printf(TEXT("Choose the weapon the %s goes on"), *Slash.ToString().ToLower()));
	PlayUiSound(TEXT("Player.Inventory"), TEXT("Player.Inventory"));
	return true;
}

void URDCombatComponent::CancelSlash()
{
	if (!SlashWith.IsNone()) ResetListView();
	SlashWith = NAME_None; SlashCursor = 0;
}

TArray<FString> URDCombatComponent::GetSlashLines() const
{
	TArray<FString> Out;
	if (!Generator) return Out;
	// (every weapon of hers, melee or ranged: not a spell, not one cast alongside)
	for (int32 I = 0; I < Generator->Weapons.Num(); ++I)
	{
		const FRDWeaponDef& W = Generator->Weapons[I];
		if (W.bAlongside || (W.bSpell && !W.BoltMesh)) continue;
		Out.Add(FString::Printf(TEXT("weapon|%d|%s|%s"), I, *W.Name.ToString(), W.Slash.IsNone() ? TEXT("") : *W.Slash.ToString()));
	}
	return Out;
}

bool URDCombatComponent::SlashEntry(int32 Line)
{
	const TArray<FString> L = GetSlashLines();
	const int32 I = Line >= 0 ? Line : SlashCursor;
	if (!L.IsValidIndex(I)) return false;
	TArray<FString> P; L[I].ParseIntoArray(P, TEXT("|"), false);
	if (P.Num() < 3) return false;
	const bool bOk = ApplySlash(SlashWith, FCString::Atoi(*P[1]));
	if (bOk) CancelSlash();
	return bOk;
}

bool URDCombatComponent::ApplySlash(FName Slash, int32 Index)
{
	if (!Generator || bDead || !Generator->Weapons.IsValidIndex(Index) || GetItemCount(Slash) <= 0 || Generator->FindSlash(Slash) < 0 || !Generator->HeroSlashes()) return false;
	FRDWeaponDef& W = Generator->Weapons[Index];
	if (W.bAlongside || (W.bSpell && !W.BoltMesh)) return false;
	const FName Old = W.Slash;
	W.Slash = Slash;
	RemoveCarried(Slash, 1);
	if (!Old.IsNone()) AddItem(Old, 1);
	SetMessage(Old.IsNone() ? FString::Printf(TEXT("The %s is on your %s"), *Slash.ToString().ToLower(), *W.Name.ToString().ToLower())
	                        : FString::Printf(TEXT("The %s is on your %s (the %s back in your pack)"), *Slash.ToString().ToLower(), *W.Name.ToString().ToLower(), *Old.ToString().ToLower()));
	PlayUiSound(TEXT("Player.Craft"), TEXT("Player.Inventory"));
	UE_LOG(LogRDMistward2, Log, TEXT("RDSLASH %s on %s (%d)%s"), *Slash.ToString(), *W.Name.ToString(), Index, Old.IsNone() ? TEXT("") : *FString::Printf(TEXT(", %s off"), *Old.ToString()));
	InventoryCursor = FMath::Clamp(InventoryCursor, 0, FMath::Max(0, GetInventoryLines().Num() - 1));
	return true;
}

bool URDCombatComponent::RemoveSlash(int32 Index)
{
	if (!Generator || !Generator->Weapons.IsValidIndex(Index) || Generator->Weapons[Index].Slash.IsNone()) return false;
	FRDWeaponDef& W = Generator->Weapons[Index];
	const FName Old = W.Slash;
	W.Slash = NAME_None;
	AddItem(Old, 1);
	SetMessage(FString::Printf(TEXT("You take the %s off your %s"), *Old.ToString().ToLower(), *W.Name.ToString().ToLower()));
	PlayUiSound(TEXT("Player.Inventory"), TEXT("Player.Inventory"));
	UE_LOG(LogRDMistward2, Log, TEXT("RDSLASH %s off %s (%d)"), *Old.ToString(), *W.Name.ToString(), Index);
	return true;
}

float URDCombatComponent::GetHaste() const { return GetWorld() && GetWorld()->GetTimeSeconds() < HasteUntil ? HasteShare : 0.f; }
float URDCombatComponent::GetSlashEvade() const { return GetWorld() && GetWorld()->GetTimeSeconds() < SlashEvadeUntil ? SlashEvadeShare : 0.f; }
bool URDCombatComponent::HasSlashShield() const { return bSlashShieldUp; }
float URDCombatComponent::GetSlashDeflect() const { return GetWorld() && GetWorld()->GetTimeSeconds() < DeflectUntil ? DeflectShare : 0.f; }

int32 URDCombatComponent::GetSlashFxAlive() const
{
	int32 N = 0;
	for (const TObjectPtr<UFXSystemComponent>& C : SlashFxComps)
		if (IsValid(C)) { if (const UNiagaraComponent* Nc = Cast<UNiagaraComponent>(C)) N += RDNiagaraParticles(Nc); else if (C->IsActive()) ++N; }
	return N;
}

void URDCombatComponent::PlaySwingSlash(const FRDSlashDef& S, const FVector& Dir)
{
	AActor* O = GetOwner();
	if (!O || !S.Fx) return;
	// (the pack's slashes sweep across their own forward: set before her at chest height, turned the way she faces)
	const FVector D = (Dir * FVector(1, 1, 0)).GetSafeNormal(1e-3f, O->GetActorForwardVector());
	const FVector At = O->GetActorLocation() + D * 60.f + FVector(0, 0, 20.f);
	if (UFXSystemComponent* F = RDMSpawnFx(O, S.Fx, At, D.Rotation(), S.FxScale, nullptr, false, true)) SlashFxComps.Add(F);
	SlashFxComps.RemoveAll([](const TObjectPtr<UFXSystemComponent>& C) { return !IsValid(C); });
}

void URDCombatComponent::SlashHit(const FRDSlashDef& S, ARDMonster* Mo, float Dmg, const FVector& At, bool bPrimary)
{
	AActor* O = GetOwner();
	if (!Mo || !O || !Generator) return;
	const float Now = GetWorld()->GetTimeSeconds();
	auto Hurt = [&](ARDMonster* M, float Amount, const FVector& Where)
	{
		if (!M || M->IsDead() || Amount <= 0.f) return;
		const bool bKilled = M->ApplyDamageEx(Amount, O, &Where, false, false);
		Generator->AddHitText(M->GetActorLocation() + FVector(0, 0, M->GetCapsuleComponent()->GetScaledCapsuleHalfHeight() + 30.f), Amount, false);
		DamageDealt += Amount; SlashBonusDealt += Amount;
		if (bKilled) ++Kills;
	};
	auto Impact = [&](const FVector& Where)
	{
		if (S.ImpactFx) if (UFXSystemComponent* F = RDMSpawnFx(O, S.ImpactFx, Where, FRotator::ZeroRotator, S.ImpactFxScale, nullptr, false, true)) SlashFxComps.Add(F);
	};
	auto Near = [&](const FVector& C, float R, ARDMonster* Not) { TArray<ARDMonster*> Out; for (ARDMonster* M : Generator->GetMonsters()) if (IsValid(M) && M != Not && !M->IsDead() && !M->IsAlly() && FVector::Dist2D(M->GetActorLocation(), C) <= R && FMath::Abs(M->GetActorLocation().Z - C.Z) < 300.f) Out.Add(M); return Out; };
	Impact(At);
	if (bPrimary) Hurt(Mo, S.Bonus * WeakMul() * (1.f + GetBlessDamage()), At);
	ERDSlashEffect E = S.Effect;
	float Amount = S.Amount, Secs = S.Seconds;
	// (prismatic: one of four at random, by a hash of her hits; each with its own tier-1 numbers)
	if (E == ERDSlashEffect::Prismatic)
	{
		const int32 K = (int32)(HashCombine((uint32)HitsLanded, Mo->GetUniqueID()) % 4u);
		static const ERDSlashEffect Pick[4] = { ERDSlashEffect::Burn, ERDSlashEffect::Slow, ERDSlashEffect::Poison, ERDSlashEffect::Drain };
		static const float Amt[4] = { 0.5f, 0.25f, 12.f, 0.3f }, Sec[4] = { 3.f, 2.f, 4.f, 0.f };
		E = Pick[K]; Amount = Amt[K]; Secs = Sec[K];
		SlashProcs.FindOrAdd(TEXT("prismatic"))++;
	}
	const FVector L = O->GetActorLocation();
	const FVector Away = ((Mo->GetActorLocation() - L) * FVector(1, 1, 0)).GetSafeNormal(1e-3f, O->GetActorForwardVector());
	// (a slash's effect on her is renewed, not added again: food effects add up, and a hit a second (or a sweep's three
	// monsters) kept several of the Verdant Slash's 1.5 HP/s on her at once (the PR review's find))
	auto Renew = [this](ERDItemKind Kind, float Amt, float Secs_, FName Name)
	{
		FEffect* E = Effects.FindByPredicate([&](const FEffect& X) { return X.Kind == Kind && X.Item == Name; });
		if (E) { E->Amount = Amt; E->Left = FMath::Max(E->Left, Secs_); }
		else Effects.Add({ Kind, Amt, Secs_, Name });
	};
	switch (E)
	{
	case ERDSlashEffect::Burn: if (!Mo->IsDead()) Mo->AddBurn((Dmg + S.Bonus) * Amount / FMath::Max(Secs, 0.1f), Secs, 0.f); break;
	case ERDSlashEffect::Slow: if (!Mo->IsDead()) Mo->SlowFor(Amount, Secs); break;
	case ERDSlashEffect::Poison: if (!Mo->IsDead()) Mo->AddBurn(Amount / FMath::Max(Secs, 0.1f), Secs, 0.f); break;
	case ERDSlashEffect::Swift: Renew(ERDItemKind::Speed, Amount, Secs, S.Name); UpdateWalkSpeed(); break;
	case ERDSlashEffect::Drain: HealBy((Dmg + S.Bonus) * Amount); break;
	// (Knock takes a launch velocity: 300 cm/s carried a monster 1.09 m (the test), so a push of N cm is N / 0.36 cm/s)
	case ERDSlashEffect::Knockback: if (!Mo->IsDead()) Mo->Knock(Away * Amount / RDM2KnockCmPerSpeed); break;
	case ERDSlashEffect::Regen: Renew(ERDItemKind::Food, Amount / FMath::Max(MaxHealth, 1.f), Secs, S.Name); break;
	case ERDSlashEffect::Evade: SlashEvadeShare = Amount; SlashEvadeUntil = Now + Secs; break;
	case ERDSlashEffect::Shield: if (Now >= SlashShieldReadyAt) { bSlashShieldUp = true; SlashShieldReadyAt = Now + Secs; Impact(L + FVector(0, 0, 40.f)); } break;
	case ERDSlashEffect::Chain:
	{
		TArray<ARDMonster*> Ms = Near(Mo->GetActorLocation(), S.Radius, Mo);
		Ms.Sort([&](const ARDMonster& A, const ARDMonster& B) { return FVector::DistSquared(A.GetActorLocation(), Mo->GetActorLocation()) < FVector::DistSquared(B.GetActorLocation(), Mo->GetActorLocation()); });
		for (int32 K = 0; K < Ms.Num() && K < S.Count; ++K) { Impact(Ms[K]->GetActorLocation()); Hurt(Ms[K], (Dmg + S.Bonus) * Amount, Ms[K]->GetActorLocation()); }
		break;
	}
	case ERDSlashEffect::Blind: if (!Mo->IsDead()) Mo->BlindFor(Amount, Secs); break;
	case ERDSlashEffect::Tide:
	{
		// (an arc before her: every monster in it slowed and pushed away)
		const FVector Fw = O->GetActorForwardVector();
		for (ARDMonster* M : Near(L, 450.f, nullptr))
		{
			const FVector D = (M->GetActorLocation() - L) * FVector(1, 1, 0);
			if (D.Size() > 80.f && FVector::DotProduct(D.GetSafeNormal(), Fw) < 0.35f) continue;
			M->SlowFor(Amount, Secs); M->Knock(D.GetSafeNormal() * S.Radius / RDM2KnockCmPerSpeed);
		}
		break;
	}
	case ERDSlashEffect::Inferno:
	{
		for (ARDMonster* M : Near(Mo->GetActorLocation(), S.Radius, Mo)) { Impact(M->GetActorLocation()); Hurt(M, Dmg + S.Bonus, M->GetActorLocation()); }
		for (ARDMonster* M : Near(Mo->GetActorLocation(), S.Radius, nullptr)) M->AddBurn((Dmg + S.Bonus) * Amount / FMath::Max(Secs, 0.1f), Secs, 0.f);
		break;
	}
	case ERDSlashEffect::Curse: if (!Mo->IsDead()) Mo->CurseFor(Amount, Secs); break;
	case ERDSlashEffect::Haste: HasteShare = Amount; HasteUntil = Now + Secs; break;
	case ERDSlashEffect::Deflect: DeflectShare = Amount; DeflectUntil = Now + Secs; break;
	case ERDSlashEffect::Magma:
	{
		FSlashArea A; A.At = Mo->GetActorLocation() - FVector(0, 0, Mo->GetCapsuleComponent()->GetScaledCapsuleHalfHeight()); A.Radius = S.Radius; A.Dps = Amount; A.Left = Secs;
		if (S.ImpactFx) A.Fx = RDMSpawnFx(O, S.ImpactFx, A.At + FVector(0, 0, 5.f), FRotator::ZeroRotator, S.ImpactFxScale * 1.6f, nullptr, false, false);
		SlashAreas.Add(A);
		break;
	}
	case ERDSlashEffect::Void:
	{
		FSlashArea A; A.At = Mo->GetActorLocation(); A.Radius = S.Radius; A.Pull = 650.f; A.Slow = Amount; A.Left = 1.2f;
		SlashAreas.Add(A);
		for (ARDMonster* M : Near(A.At, A.Radius, nullptr)) M->SlowFor(Amount, 3.f);
		break;
	}
	case ERDSlashEffect::Stun:
	{
		float& Ready = StunReadyAt.FindOrAdd(Mo->GetUniqueID());
		if (Now >= Ready && !Mo->IsDead()) { Mo->StunFor(Secs); Ready = Now + S.Radius; }
		else { SlashProcs.FindOrAdd(TEXT("stun_wait"))++; return; }
		break;
	}
	default: break;
	}
	SlashProcs.FindOrAdd(RDM2EffectName(E))++;
}

void URDCombatComponent::TickSlashAreas(float Dt)
{
	for (int32 I = SlashAreas.Num() - 1; I >= 0; --I)
	{
		FSlashArea& A = SlashAreas[I];
		A.Left -= Dt; A.Acc += Dt;
		if (Generator)
			for (ARDMonster* M : Generator->GetMonsters())
			{
				if (!IsValid(M) || M->IsDead() || M->IsAlly() || FVector::Dist2D(M->GetActorLocation(), A.At) > A.Radius) continue;
				if (A.Pull > 0.f) M->PullToward(A.At, A.Pull, Dt);
				if (A.Dps > 0.f && A.Acc >= 0.5f) { if (M->ApplyDamageEx(A.Dps * 0.5f, GetOwner(), nullptr, false, false)) ++Kills; DamageDealt += A.Dps * 0.5f; SlashBonusDealt += A.Dps * 0.5f; }
			}
		if (A.Acc >= 0.5f) A.Acc -= 0.5f;
		if (A.Left <= 0.f) { RDM2EndFx(A.Fx.Get()); SlashAreas.RemoveAt(I); }
	}
}

bool URDCombatComponent::ApplySlashHitNow(int32 Index, ARDMonster* Target)
{
	const FRDSlashDef* S = SlashOf(Index);
	if (!S || !Target || Target->IsDead()) return false;
	PlaySwingSlash(*S, Target->GetActorLocation() - GetOwner()->GetActorLocation());
	SlashHit(*S, Target, GetDamageOf(Index), Target->GetActorLocation(), true);
	return true;
}

// ================================================================================================ blessings and fountains
void URDCombatComponent::Bless(const FString& Name, float Damage, float Armour, float Speed, float Seconds)
{
	BlessName = Name; BlessDmg = Damage; BlessArm = Armour; BlessUntil = GetWorld()->GetTimeSeconds() + Seconds;
	if (Speed > 0.f) { Effects.Add({ ERDItemKind::Speed, Speed, Seconds, FName(*Name) }); UpdateWalkSpeed(); }
}

FString URDCombatComponent::GetBlessing() const { return GetWorld() && GetWorld()->GetTimeSeconds() < BlessUntil ? BlessName : FString(); }
float URDCombatComponent::GetBlessDamage() const { return GetWorld() && GetWorld()->GetTimeSeconds() < BlessUntil ? BlessDmg : 0.f; }
float URDCombatComponent::GetBlessArmour() const { return GetWorld() && GetWorld()->GetTimeSeconds() < BlessUntil ? BlessArm : 0.f; }

bool URDCombatComponent::DrinkFountain(ERDRoomKind Kind)
{
	if (!Generator || bDead) return false;
	switch (Kind)
	{
	case ERDRoomKind::HealFountain:
	{
		if (Health >= MaxHealth) { SetMessage(TEXT("Your hit points are full: the fountain keeps its water")); return false; }
		const float Before = Health;
		Health = FMath::Min(MaxHealth, Health + MaxHealth * Generator->FountainHeal);
		SetMessage(FString::Printf(TEXT("You drink from the healing fountain:  +%.0f HP"), Health - Before));
		break;
	}
	case ERDRoomKind::SpeedFountain:
		Effects.Add({ ERDItemKind::Speed, Generator->FountainSpeed, Generator->FountainSpeedSeconds, TEXT("Fountain of speed") });
		UpdateWalkSpeed();
		SetMessage(FString::Printf(TEXT("You drink from the fountain of speed:  +%.0f%% speed for %.0f s"), Generator->FountainSpeed * 100.f, Generator->FountainSpeedSeconds));
		break;
	case ERDRoomKind::ManaFountain:
	{
		if (MaxMana <= 0.f) { SetMessage(FString::Printf(TEXT("%s has no mana: the fountain keeps its water"), *Generator->PlayerTitle)); return false; }
		if (Mana >= MaxMana) { SetMessage(TEXT("Your mana is full: the fountain keeps its water")); return false; }
		const float Before = Mana;
		Mana = MaxMana;
		SetMessage(FString::Printf(TEXT("You drink from the fountain of mana:  +%.0f mana"), Mana - Before));
		break;
	}
	default: return false;
	}
	if (AActor* O = GetOwner()) Generator->PlaySoundAt(TEXT("Player.Drink"), O->GetActorLocation());
	return true;
}

FName URDCombatComponent::StartShieldOf() const
{
	const FName* S = Generator ? Generator->StartShield.Find(Generator->CurrentHero) : nullptr;
	return S ? *S : NAME_None;
}

// ================================================================================================ the generator: pickups
UStaticMesh* ARDDungeonGenerator::PickupMeshOf(FName Item) const
{
	const int32 Ix = FindItem(Item);
	if (Ix < 0) return nullptr;
	for (const FRDWeaponFit& F : Items[Ix].WeaponFits)
	{
		UStaticMesh* M = Items[Ix].Kind == ERDItemKind::Shield ? F.Weapon.OffHandMesh.Get() : F.Weapon.Mesh.Get();
		if (M) return M;
	}
	return nullptr;
}

FName ARDDungeonGenerator::PickupItemFor(FIntPoint Section, int32 Index) const
{
	// (weapons, three in four, and shields of the set's tier that have a mesh to lay down)
	const int32 Tier = TierOf(Section);
	TArray<FName> Wpn, Shd;
	for (const FRDItemDef& It : Items)
	{
		if ((It.Kind != ERDItemKind::Weapon && It.Kind != ERDItemKind::Shield) || (It.Tiers.Num() > 0 && !It.Tiers.Contains(Tier)) || !PickupMeshOf(It.Name)) continue;
		(It.Kind == ERDItemKind::Weapon ? Wpn : Shd).Add(It.Name);
	}
	const uint32 H = HashCombine(HashCombine((uint32)SessionSeed ^ 0x9C4Bu, GetTypeHash(Section)), GetTypeHash(Index * 131 + 7));
	const bool bShield = Shd.Num() > 0 && (Wpn.Num() == 0 || H % 4u == 3u);
	const TArray<FName>& From = bShield ? Shd : Wpn;
	return From.Num() > 0 ? From[(H >> 3) % (uint32)From.Num()] : NAME_None;
}

TArray<FString> ARDDungeonGenerator::GetPickupLines() const
{
	TArray<FString> Out;
	for (const auto& KV : Sections)
		if (const ARDSection* S = KV.Value)
			for (int32 I = 0; I < S->Pickups.Num(); ++I)
			{
				const ARDSection::FPickup& P = S->Pickups[I];
				Out.Add(FString::Printf(TEXT("%d|%d|%d|%s|%.0f|%.0f|%.0f|%d|%d"), KV.Key.X, KV.Key.Y, I, *P.Item.ToString(), P.At.X, P.At.Y, P.At.Z,
					TakenPickups.Contains(FIntVector(KV.Key.X, KV.Key.Y, I)) ? 1 : 0, P.Mesh.IsValid() && P.Mesh->IsVisible() ? 1 : 0));
			}
	return Out;
}

// ================================================================================================ the generator: special rooms
bool ARDDungeonGenerator::IsRoomLocked(FIntPoint Section, int32 Room) const
{
	const ARDSection* S = GetSection(Section);
	if (!S || Room < 0) return false;
	if (S->GetRoomKindEnum(Room) == ERDRoomKind::Vault && !VaultsOpened.Contains(FIntVector(Section.X, Section.Y, Room))) return true;
	return ArenaRoom == Room && ArenaSection == Section;
}

TArray<FString> ARDDungeonGenerator::GetSpecialRoomLines() const
{
	TArray<FString> Out;
	for (const auto& KV : Sections)
		if (const ARDSection* S = KV.Value)
			for (const ARDSection::FFixture& F : S->Fixtures)
			{
				const FIntVector Key(KV.Key.X, KV.Key.Y, F.Room);
				const int32 Done = F.Kind == ERDRoomKind::Arena ? (ArenasWon.Contains(Key) ? 1 : 0) : F.Kind == ERDRoomKind::Vault ? (VaultsOpened.Contains(Key) ? 1 : 0) : UsedFixtures.Contains(Key) ? 1 : 0;
				Out.Add(FString::Printf(TEXT("%d|%d|%d|%s|%.0f|%.0f|%.0f|%d"), KV.Key.X, KV.Key.Y, F.Room, *KindName(F.Kind), F.At.X, F.At.Y, F.At.Z, Done));
			}
	return Out;
}

int32 ARDDungeonGenerator::GetArenaLeft() const
{
	int32 N = 0;
	for (const TWeakObjectPtr<ARDMonster>& M : ArenaMonsters) if (M.IsValid() && !M->IsDead()) ++N;
	return N;
}

/** Count items of a tier (not slashes, keys, teleport rings or components), by a hash: the rewards of the special rooms */
static TArray<FName> RDM2TierItems(const ARDDungeonGenerator* G, int32 Tier, uint32 Salt, int32 Count)
{
	TArray<FName> Pool;
	for (const FRDItemDef& It : G->Items)
		if (It.Weight > 0.f && (It.Tiers.Num() == 0 || It.Tiers.Contains(Tier)) && It.Kind != ERDItemKind::Slash && It.Kind != ERDItemKind::Key && It.Kind != ERDItemKind::Teleport
			&& It.Kind != ERDItemKind::Component && It.Kind != ERDItemKind::Tome) Pool.Add(It.Name);
	// (distinct things: a draw that repeats one is drawn again (a gauntlet's chest held two of its three once))
	TArray<FName> Out;
	for (int32 K = 0; Out.Num() < FMath::Min(Count, Pool.Num()) && K < Count * 16; ++K) Out.AddUnique(Pool[HashCombine(Salt, (uint32)K * 7919u + 13u) % (uint32)Pool.Num()]);
	return Out;
}

bool ARDDungeonGenerator::StartArena(FIntPoint Section, int32 Room)
{
	ARDSection* S = GetSection(Section);
	if (!S || S->GetRoomKindEnum(Room) != ERDRoomKind::Arena || ArenaRoom >= 0 || ArenasWon.Contains(FIntVector(Section.X, Section.Y, Room))) return false;
	ArenaSection = Section; ArenaRoom = Room; ArenaWave = 0; ArenaMonsters.Reset();
	S->ShutRoomDoors(Room);
	RoomUses.FindOrAdd(TEXT("arena_begun"))++;
	TierNotice = FString::Printf(TEXT("THE ARENA  -  SURVIVE %d WAVES"), ArenaWaves); TierNoticeTime = GetWorld()->GetTimeSeconds();
	UE_LOG(LogRDMistward2, Log, TEXT("RDARENA begun in room %d of (%d,%d)"), Room, Section.X, Section.Y);
	ArenaWave = -1;          // (the first wave comes on the next tick)
	return true;
}

void ARDDungeonGenerator::TickArena(float Dt)
{
	URDCombatComponent* Pc = GetPlayerCombat();
	APawn* Her = UGameplayStatics::GetPlayerPawn(this, 0);
	if (!Pc || !Her) return;
	ARDSection* S = ArenaRoom >= 0 ? GetSection(ArenaSection) : nullptr;
	if (ArenaRoom < 0)
	{
		// (she steps well into an arena not yet won: it begins)
		const FVector L = Her->GetActorLocation();
		ARDSection* Hs = GetSection(WorldToSection(L));
		const int32 Rm = Hs ? Hs->RoomAt(L) : -1;
		if (Rm < 0 || Hs->GetRoomKindEnum(Rm) != ERDRoomKind::Arena || ArenasWon.Contains(FIntVector(Hs->Coord.X, Hs->Coord.Y, Rm)) || Pc->IsDead()) return;
		FVector2D Mn, Mx; Hs->GetRoomBounds(Rm, Mn, Mx);
		if (FMath::Min(FMath::Min(L.X - Mn.X, Mx.X - L.X), FMath::Min(L.Y - Mn.Y, Mx.Y - L.Y)) < 260.f) return;
		StartArena(Hs->Coord, Rm);
		return;
	}
	// (she fell or the set is gone: the arena is lost, its monsters go, its doors open again)
	if (!S || Pc->IsDead())
	{
		for (const TWeakObjectPtr<ARDMonster>& M : ArenaMonsters) if (M.IsValid() && !M->IsDead()) M->Destroy();
		ArenaMonsters.Reset(); ArenaRoom = -1;
		UE_LOG(LogRDMistward2, Log, TEXT("RDARENA lost"));
		return;
	}
	if (GetArenaLeft() > 0) return;
	++ArenaWave;
	if (ArenaWave > 0) ++ArenaWavesBeaten;
	const int32 Tier = TierOf(ArenaSection);
	if (ArenaWave >= ArenaWaves)
	{
		// (won: the doors open, its reward lies in the middle)
		const FIntVector Key(ArenaSection.X, ArenaSection.Y, ArenaRoom);
		ArenasWon.Add(Key);
		const FVector C = S->GetRoomCenter(ArenaRoom);
		const TArray<FName> Got = RDM2TierItems(this, Tier, HashCombine((uint32)SessionSeed ^ 0xA7E4u, GetTypeHash(Key)), 3);
		if (ARDLootPile* Lp = DropLoot(C + FVector(0, 0, 100.f), Got, TArray<float>())) Lp->bHers = false;
		ArenaRoom = -1; ArenaMonsters.Reset();
		RoomUses.FindOrAdd(TEXT("arena_won"))++;
		TierNotice = TEXT("THE ARENA IS WON  -  ITS PRIZE LIES IN THE MIDDLE"); TierNoticeTime = GetWorld()->GetTimeSeconds();
		PlaySoundAt(TEXT("Env.Generate"), Her->GetActorLocation());
		UE_LOG(LogRDMistward2, Log, TEXT("RDARENA won: %d waves, prize %d things"), ArenaWaves, Got.Num());
		return;
	}
	// (the next wave: 2 + the tier of the tier's monsters, at the free tiles farthest from her)
	TArray<int32> Kinds; MonsterKindsFor(ArenaSection, Kinds);
	if (Kinds.Num() == 0) { ArenaRoom = -1; return; }
	TArray<FVector> Spots = S->GetRoomFreeTilesNear(ArenaRoom, Her->GetActorLocation());
	Algo::Reverse(Spots);
	const int32 Count = 2 + Tier;
	for (int32 K = 0; K < Count && Spots.Num() > 0; ++K)
	{
		const int32 Kind = Kinds[HashCombine((uint32)SessionSeed ^ 0xA7E5u, (uint32)(ArenaWave * 31 + K)) % (uint32)Kinds.Num()];
		if (ARDMonster* M = SpawnMonsterKind(Kind, Spots[K % Spots.Num()], Tier, 1.f, 1.f, 1.f, FString::Printf(TEXT("ARENA  WAVE %d"), ArenaWave + 1))) ArenaMonsters.Add(M);
	}
	// (a wave that came to nobody (no free tile, no monster made) is not a wave beaten: the arena ends unwon, its doors
	// unlocked, no prize (the PR review's find: three empty waves won it))
	if (ArenaMonsters.Num() == 0)
	{
		UE_LOG(LogRDMistward2, Warning, TEXT("RDARENA wave %d spawned nobody: the arena ends unwon"), ArenaWave + 1);
		ArenaRoom = -1; if (ArenaWave > 0) --ArenaWavesBeaten;
		return;
	}
	TierNotice = FString::Printf(TEXT("THE ARENA  -  WAVE %d OF %d"), ArenaWave + 1, ArenaWaves); TierNoticeTime = GetWorld()->GetTimeSeconds();
	UE_LOG(LogRDMistward2, Log, TEXT("RDARENA wave %d: %d monsters"), ArenaWave + 1, ArenaMonsters.Num());
}

FString ARDDungeonGenerator::DescribeSpecialNear(const FVector& From) const
{
	const FIntPoint Here = WorldToSection(From);
	for (int32 Dx = -1; Dx <= 1; ++Dx)
		for (int32 Dy = -1; Dy <= 1; ++Dy)
			if (const ARDSection* S = GetSection(Here + FIntPoint(Dx, Dy)))
			{
				if (bWeaponPickups)
					for (int32 I = 0; I < S->Pickups.Num(); ++I)
						if (!TakenPickups.Contains(FIntVector(S->Coord.X, S->Coord.Y, I)) && S->Pickups[I].Mesh.IsValid() && FVector::Dist2D(S->Pickups[I].At, From) < 200.f)
							return FString::Printf(TEXT("take the %s"), *S->Pickups[I].Item.ToString().ToLower());
				if (!bSpecialRooms) continue;
				for (const ARDSection::FFixture& F : S->Fixtures)
				{
					if (FVector::Dist2D(F.At, From) > 280.f) continue;
					const bool bUsed = UsedFixtures.Contains(FIntVector(S->Coord.X, S->Coord.Y, F.Room));
					switch (F.Kind)
					{
					case ERDRoomKind::Shrine: return bUsed ? TEXT("the shrine is silent") : TEXT("pray at the shrine");
					case ERDRoomKind::HealFountain: return bUsed ? TEXT("the fountain is dry") : TEXT("drink from the healing fountain");
					case ERDRoomKind::SpeedFountain: return bUsed ? TEXT("the fountain is dry") : TEXT("drink from the fountain of speed");
					case ERDRoomKind::ManaFountain: return bUsed ? TEXT("the fountain is dry") : TEXT("drink from the fountain of mana");
					default: break;
					}
				}
				// (a vault's door)
				for (int32 I = 0; I < S->GetNumDoors(); ++I)
				{
					const int32 Rm = S->DoorRoom(I);
					if (Rm < 0 || S->GetRoomKindEnum(Rm) != ERDRoomKind::Vault || FVector::Dist2D(S->GetDoorLocation(I), From) > 240.f) continue;
					if (VaultsOpened.Contains(FIntVector(S->Coord.X, S->Coord.Y, Rm))) continue;
					const URDCombatComponent* Pc = GetPlayerCombat();
					return Pc && Pc->GetItemCount(VaultKeyItem) > 0 ? TEXT("unlock the vault (your key)") : TEXT("the vault is locked: its key lies in a chest of these rooms");
				}
			}
	return FString();
}

FString ARDDungeonGenerator::UseSpecialNear(const FVector& From)
{
	URDCombatComponent* Pc = GetPlayerCombat();
	if (!Pc) return FString();
	const FIntPoint Here = WorldToSection(From);
	for (int32 Dx = -1; Dx <= 1; ++Dx)
		for (int32 Dy = -1; Dy <= 1; ++Dy)
			if (ARDSection* S = GetSection(Here + FIntPoint(Dx, Dy)))
			{
				// (an armory table's weapon or shield: taken up, gone from the table for good)
				if (bWeaponPickups)
				{
					int32 Best = -1; float BestD = 200.f;
					for (int32 I = 0; I < S->Pickups.Num(); ++I)
						if (!TakenPickups.Contains(FIntVector(S->Coord.X, S->Coord.Y, I)) && S->Pickups[I].Mesh.IsValid())
							if (const float D = FVector::Dist2D(S->Pickups[I].At, From); D < BestD) { BestD = D; Best = I; }
					if (Best >= 0)
					{
						ARDSection::FPickup& P = S->Pickups[Best];
						TakenPickups.Add(FIntVector(S->Coord.X, S->Coord.Y, Best)); ++PickupsTaken;
						if (UStaticMeshComponent* M = P.Mesh.Get()) M->DestroyComponent();
						Pc->AddItem(P.Item, 1);
						Pc->ShowMessage(FString::Printf(TEXT("You take the %s from the table"), *P.Item.ToString().ToLower()));
						LastFound = P.Item; LastFoundList = { P.Item }; LastFoundTime = GetWorld()->GetTimeSeconds(); ++ItemsFound;
						PlaySoundAt(TEXT("Player.Loot"), P.At);
						UE_LOG(LogRDMistward2, Log, TEXT("RDPICKUP %s taken from (%d,%d) %d"), *P.Item.ToString(), S->Coord.X, S->Coord.Y, Best);
						return TEXT("pickup");
					}
				}
				if (!bSpecialRooms) continue;
				for (int32 I = 0; I < S->Fixtures.Num(); ++I)
				{
					const ARDSection::FFixture& F = S->Fixtures[I];
					if (FVector::Dist2D(F.At, From) > 280.f) continue;
					const FIntVector Key(S->Coord.X, S->Coord.Y, F.Room);
					if (F.Kind == ERDRoomKind::Shrine)
					{
						if (UsedFixtures.Contains(Key)) { Pc->ShowMessage(TEXT("The shrine is silent: it gave its blessing")); return TEXT("shrine used"); }
						// (one of three blessings, by a hash of the session and the shrine)
						const int32 K = (int32)(HashCombine((uint32)SessionSeed ^ 0x5B12u, GetTypeHash(Key)) % 3u);
						static const TCHAR* Names[3] = { TEXT("Blessing of might"), TEXT("Blessing of the bulwark"), TEXT("Blessing of swiftness") };
						Pc->Bless(Names[K], K == 0 ? 0.25f : 0.f, K == 1 ? 0.25f : 0.f, K == 2 ? 0.2f : 0.f, BlessSeconds);
						Pc->ShowMessage(FString::Printf(TEXT("%s:  %s for %.0f s"), Names[K], K == 0 ? TEXT("your blows +25%") : K == 1 ? TEXT("blows on you 25% less") : TEXT("+20% speed"), BlessSeconds));
						if (BlessFx) if (const AActor* O = Pc->GetOwner()) RDMSpawnFx(this, BlessFx, O->GetActorLocation(), FRotator::ZeroRotator, 1.f, nullptr, false, true);
						UsedFixtures.Add(Key); S->DimFixture(I); RoomUses.FindOrAdd(TEXT("shrine"))++;
						PlaySoundAt(TEXT("Player.Cast.Fire"), F.At);
						UE_LOG(LogRDMistward2, Log, TEXT("RDSHRINE %s at (%d,%d) room %d"), Names[K], Key.X, Key.Y, Key.Z);
						return TEXT("shrine");
					}
					if (F.Kind == ERDRoomKind::HealFountain || F.Kind == ERDRoomKind::SpeedFountain || F.Kind == ERDRoomKind::ManaFountain)
					{
						if (UsedFixtures.Contains(Key)) { Pc->ShowMessage(TEXT("The fountain is dry")); return TEXT("fountain dry"); }
						if (!Pc->DrinkFountain(F.Kind)) return TEXT("fountain kept");
						UsedFixtures.Add(Key); S->DimFixture(I);
						RoomUses.FindOrAdd(F.Kind == ERDRoomKind::HealFountain ? TEXT("heal_fountain") : F.Kind == ERDRoomKind::SpeedFountain ? TEXT("speed_fountain") : TEXT("mana_fountain"))++;
						UE_LOG(LogRDMistward2, Log, TEXT("RDFOUNTAIN %s at (%d,%d) room %d"), *KindName(F.Kind), Key.X, Key.Y, Key.Z);
						return TEXT("fountain");
					}
				}
				// (a vault's door: her key opens it for good)
				for (int32 I = 0; I < S->GetNumDoors(); ++I)
				{
					const int32 Rm = S->DoorRoom(I);
					if (Rm < 0 || S->GetRoomKindEnum(Rm) != ERDRoomKind::Vault || FVector::Dist2D(S->GetDoorLocation(I), From) > 240.f) continue;
					const FIntVector Key(S->Coord.X, S->Coord.Y, Rm);
					if (VaultsOpened.Contains(Key)) continue;
					if (Pc->GetItemCount(VaultKeyItem) <= 0) { Pc->ShowMessage(TEXT("The vault is locked: its key lies in a chest of these rooms")); PlaySoundAt(TEXT("Env.CellClose"), S->GetDoorLocation(I)); return TEXT("vault locked"); }
					VaultsOpened.Add(Key);
					Pc->RemoveItem(VaultKeyItem, 1);
					S->ToggleDoor(I, From);
					Pc->ShowMessage(TEXT("Your key turns: the vault is open"));
					RoomUses.FindOrAdd(TEXT("vault"))++;
					UE_LOG(LogRDMistward2, Log, TEXT("RDVAULT opened at (%d,%d) room %d"), Key.X, Key.Y, Key.Z);
					return TEXT("vault");
				}
			}
	return FString();
}

FName ARDDungeonGenerator::GiveBossSlash(int32 Tier, const FVector& At)
{
	if (!bBossSlashes || Slashes.Num() == 0 || !HeroSlashes() || !PlayerCombat) return NAME_None;
	// (one of the slashes of its tier (the nearest tier that has some), from the session's own stream)
	TArray<int32> Of;
	for (int32 D = 0; D < 5 && Of.Num() == 0; ++D)
		for (int32 I = 0; I < Slashes.Num(); ++I) if (FMath::Abs(Slashes[I].Tier - Tier) == D && FindItem(Slashes[I].Name) >= 0) Of.Add(I);
	if (Of.Num() == 0) return NAME_None;
	if (SlashR.GetInitialSeed() == 0) SlashR.Initialize((int32)HashCombine((uint32)SessionSeed, 0x51A5u));
	const FRDSlashDef& S = Slashes[Of[SlashR.RandRange(0, Of.Num() - 1)]];
	PlayerCombat->AddItem(S.Name, 1);
	SlashesGiven.Add(S.Name);
	PlayerCombat->ShowMessage(FString::Printf(TEXT("The boss leaves you the %s:  +%.0f %s,  %s  (I: put it on a weapon)"), *S.Name.ToString(), S.Bonus, *S.Type.ToLower(), *S.Text));
	if (S.ImpactFx) RDMSpawnFx(this, S.ImpactFx, At + FVector(0, 0, 60.f), FRotator::ZeroRotator, S.ImpactFxScale * 1.5f, nullptr, false, true);
	PlaySoundAt(TEXT("Player.Loot"), At);
	UE_LOG(LogRDMistward2, Log, TEXT("RDSLASH %s given for a tier %d boss"), *S.Name.ToString(), Tier);
	return S.Name;
}

// ================================================================================================ the section: the third list's play part
void ARDSection::OutlineTrap(int32 Index)
{
	if (!TrapList.IsValidIndex(Index) || !Generator) return;
	FTrapInst& T = TrapList[Index];
	if (T.State != 0) return;
	// (its plate or rune drawn over in red; a red ring on the floor at the reach it goes off within)
	for (TWeakObjectPtr<USceneComponent>& C : T.Comps)
		if (UStaticMeshComponent* M = Cast<UStaticMeshComponent>(C.Get()); M && !M->ComponentHasTag(TEXT("RDOutline")) && Generator->TrapOutlineMaterial) M->SetOverlayMaterial(Generator->TrapOutlineMaterial);
	if (Generator->TrapRingMesh && !T.Comps.ContainsByPredicate([](const TWeakObjectPtr<USceneComponent>& C) { return C.IsValid() && C->ComponentHasTag(TEXT("RDOutline")); }))
	{
		const FRDTrapDef& D = Generator->Traps[T.Def];
		UStaticMeshComponent* R = NewObject<UStaticMeshComponent>(this);
		R->ComponentTags.Add(RDM2Interactive); R->ComponentTags.Add(TEXT("RDOutline"));
		R->SetMobility(EComponentMobility::Movable);
		R->SetStaticMesh(Generator->TrapRingMesh);
		R->SetCollisionEnabled(ECollisionEnabled::NoCollision);
		R->SetCastShadow(false);
		if (Generator->TrapRingMaterial) R->SetMaterial(0, Generator->TrapRingMaterial);
		R->SetupAttachment(RootComponent);
		R->RegisterComponent();
		const FBox Bx = Generator->TrapRingMesh->GetBoundingBox();
		const float Sz = FMath::Max(Bx.GetSize().X, 1.f);
		const float K = (FMath::Max(D.Radius, 60.f) * 2.f + 40.f) / Sz;
		R->SetWorldTransform(FTransform(FRotator(0, T.Yaw, 0), T.At + FVector(0, 0, 3.f), FVector(K, K, 1.f)));
		T.Comps.Add(R);
		// (and a red glow over it: in a torch-lit room the ring alone read as a faint arc from 6 m (the test's pictures))
		if (Generator->TrapGlowCandelas <= 0.f) { UE_LOG(LogRDMistward2, Log, TEXT("RDTRAP outlined: %s (%d) in (%d,%d)"), *D.Name.ToString(), Index, Coord.X, Coord.Y); return; }
		UPointLightComponent* Lt = NewObject<UPointLightComponent>(this);
		Lt->ComponentTags.Add(RDM2Interactive); Lt->ComponentTags.Add(TEXT("RDOutline"));
		Lt->SetMobility(EComponentMobility::Movable);
		Lt->SetupAttachment(RootComponent);
		Lt->SetIntensityUnits(ELightUnits::Candelas);
		Lt->SetIntensity(Generator->TrapGlowCandelas);
		Lt->SetLightColor(FLinearColor(1.f, 0.06f, 0.03f));
		Lt->SetAttenuationRadius(FMath::Max(D.Radius, 60.f) * 2.f + 220.f);
		Lt->SetCastShadows(false);
		Lt->RegisterComponent();
		Lt->SetWorldLocation(T.At + FVector(0, 0, 70.f));
		T.Comps.Add(Lt);
	}
	UE_LOG(LogRDMistward2, Log, TEXT("RDTRAP outlined: %s (%d) in (%d,%d)"), *Generator->Traps[T.Def].Name.ToString(), Index, Coord.X, Coord.Y);
}

void ARDSection::AddPickup(FName Item, const FVector& P, float Yaw)
{
	FPickup Pk; Pk.Item = Item; Pk.At = P;
	const int32 Index = Pickups.Num();
	UStaticMesh* Mesh = Generator ? Generator->PickupMeshOf(Item) : nullptr;
	if (Mesh && bBuildInteractive && !bCensus && !Generator->TakenPickups.Contains(FIntVector(Coord.X, Coord.Y, Index)))
	{
		// (laid flat: its longest side across the table, its thinnest up; on the table's top, where the decoration lay)
		const FBox Bx = Mesh->GetBoundingBox();
		const FVector E = Bx.GetExtent();
		int32 Ax[3] = { 0, 1, 2 };
		Algo::Sort(Ax, [&E](int32 A, int32 B) { return E[A] > E[B]; });
		const FRotator Tr(0, Yaw, 0);
		FVector Img[3];
		Img[Ax[0]] = Tr.RotateVector(FVector(1, 0, 0)); Img[Ax[1]] = Tr.RotateVector(FVector(0, 1, 0)); Img[Ax[2]] = FVector::UpVector;
		FMatrix Rm(Img[0], Img[1], Img[2], FVector::ZeroVector);
		if (Rm.Determinant() < 0.f) { Img[Ax[1]] *= -1.f; Rm = FMatrix(Img[0], Img[1], Img[2], FVector::ZeroVector); }
		const FQuat Q(Rm);
		FBox Rb(ForceInit);
		for (int32 C = 0; C < 8; ++C)
			Rb += Q.RotateVector(FVector(C & 1 ? Bx.Max.X : Bx.Min.X, C & 2 ? Bx.Max.Y : Bx.Min.Y, C & 4 ? Bx.Max.Z : Bx.Min.Z));
		const FVector Loc(P.X - Rb.GetCenter().X, P.Y - Rb.GetCenter().Y, P.Z - Rb.Min.Z + 0.5f);
		UStaticMeshComponent* M = AddMesh(RootComponent, Mesh, FTransform(Q, Loc - GetActorLocation()), false);
		M->ComponentTags.Add(TEXT("RDPickup"));
		Pk.Mesh = M;
	}
	Pickups.Add(Pk);
}

void ARDSection::AssignSpecialRooms()
{
	// (a stream of its own after the plan: each room a draw for whether and a draw for which, so one room's choice never moves
	// another's; at most one of each kind in a set; not the great hall, a prison or a junction; big enough)
	FRandomStream RS((int32)HashCombine((uint32)Seed ^ 0x3C9A71B5u, 3u));
	struct FW { ERDRoomKind K; float W; int32 MinSide; };
	static const FW Kinds[] = { { ERDRoomKind::Shrine, 3, 5 }, { ERDRoomKind::HealFountain, 3, 5 }, { ERDRoomKind::SpeedFountain, 2, 5 }, { ERDRoomKind::ManaFountain, 2, 5 },
		{ ERDRoomKind::Arena, 2, 6 }, { ERDRoomKind::TrapGauntlet, 2, 5 }, { ERDRoomKind::Vault, 2, 5 }, { ERDRoomKind::ThroneRoom, 1, 6 } };
	TSet<ERDRoomKind> Used;
	const bool bStart = Generator->IsStartSection(Coord);
	for (int32 RI = 0; RI < Rooms.Num(); ++RI)
	{
		FRoom& Rm = Rooms[RI];
		const float U = RS.FRand(), V = RS.FRand();
		if (Rm.Kind == ERDRoomKind::Hall || Rm.Kind == ERDRoomKind::Prison || Rm.Kind == ERDRoomKind::Junction || U >= Generator->SpecialRoomShare) continue;
		const int32 Side = FMath::Min(Rm.Max.X - Rm.Min.X, Rm.Max.Y - Rm.Min.Y);
		// (the great hall's set keeps its first room: she starts beside it)
		if (bStart && FVector::Dist2D(TileWorld(Rm.Lane), Generator->GetStartRoomCenter()) < 1500.f) continue;
		float Sum = 0.f;
		for (const FW& K : Kinds) if (!Used.Contains(K.K) && Side >= K.MinSide) Sum += K.W;
		if (Sum <= 0.f) continue;
		float X = V * Sum;
		for (const FW& K : Kinds)
		{
			if (Used.Contains(K.K) || Side < K.MinSide) continue;
			X -= K.W;
			if (X <= 0.f) { Rm.Kind = K.K; Used.Add(K.K); break; }
		}
	}
}

int32 ARDSection::DoorRoom(int32 Door) const
{
	if (!Doors.IsValidIndex(Door) || Doors[Door].TileA.X < 0) return -1;
	return RoomAtLocal(Doors[Door].TileA);
}

void ARDSection::ShutRoomDoors(int32 Room)
{
	for (int32 I = 0; I < Doors.Num(); ++I)
		if (DoorRoom(I) == Room && Doors[I].Target > 0.5f) { Doors[I].Target = 0.f; Doors[I].bByMonster = false; }
}

TArray<FVector> ARDSection::GetRoomFreeTilesNear(int32 Index, const FVector& From) const
{
	TArray<FVector> T = GetRoomFreeTiles(Index);
	T.Sort([&From](const FVector& A, const FVector& B) { return FVector::DistSquared(A, From) < FVector::DistSquared(B, From); });
	return T;
}

void ARDSection::DimFixture(int32 Index)
{
	if (!Fixtures.IsValidIndex(Index)) return;
	if (UFXSystemComponent* F = Fixtures[Index].Fx.Get()) F->Deactivate();
}

void ARDSection::PlaceSpecial()
{
	UWorld* W = GetWorld();
	if (!Generator || !Generator->bSpecialRooms || bCensus || !W || !W->IsGameWorld()) return;
	const int32 Tier = Generator->TierOf(Coord);
	for (int32 I = 0; I < Fixtures.Num(); ++I)
	{
		FFixture& F = Fixtures[I];
		const FIntVector Key(Coord.X, Coord.Y, F.Room);
		// (a shrine's or fountain's glow while it has something to give)
		UFXSystemAsset* Fx = F.Kind == ERDRoomKind::Shrine ? Generator->ShrineFx.Get() : F.Kind == ERDRoomKind::HealFountain ? Generator->HealFountainFx.Get()
			: F.Kind == ERDRoomKind::SpeedFountain ? Generator->SpeedFountainFx.Get() : F.Kind == ERDRoomKind::ManaFountain ? Generator->ManaFountainFx.Get() : nullptr;
		if (Fx && !Generator->UsedFixtures.Contains(Key))
			if (UFXSystemComponent* C = RDMSpawnFx(this, Fx, F.At + FVector(0, 0, F.Kind == ERDRoomKind::Shrine ? 30.f : 60.f), FRotator::ZeroRotator, 1.f, RootComponent, false, false))
			{
				C->SetUsingAbsoluteLocation(true); C->SetWorldLocation(F.At + FVector(0, 0, F.Kind == ERDRoomKind::Shrine ? 30.f : 60.f));
				C->ComponentTags.Add(RDM2Interactive);
				F.Fx = C;
			}
		// (the throne room's usurper: an encounter of its own, kept as the bosses' are)
		if (F.Kind == ERDRoomKind::ThroneRoom)
		{
			const bool bHave = Generator->Encounters.ContainsByPredicate([&](const ARDDungeonGenerator::FEncounter& E) { return E.bThrone && E.Section == Coord && E.Room == F.Room; });
			TArray<int32> Kinds; Generator->MonsterKindsFor(Coord, Kinds);
			if (!bHave && Kinds.Num() > 0)
			{
				int32 Boss = Kinds[0];
				for (const int32 K : Kinds) if (Generator->Monsters[K].HealthFactor > Generator->Monsters[Boss].HealthFactor) Boss = K;
				ARDDungeonGenerator::FEncounter E; E.Tier = Tier; E.bBoss = true; E.bThrone = true; E.Section = Coord; E.Room = F.Room; E.At = F.At;
				E.Kinds.Add(Boss); E.Spots.Add(F.At); E.Dead.Init(false, 1);
				const FRDMonsterDef& Md = Generator->Monsters[Boss];
				E.Label = FString::Printf(TEXT("THE USURPER: %s"), *(Md.Title.IsEmpty() ? Md.Name.ToString() : Md.Title).ToUpper());
				Generator->Encounters.Add(E);
				UE_LOG(LogRDMistward2, Log, TEXT("RDTHRONE (%d,%d) room %d: the usurper %s"), Coord.X, Coord.Y, F.Room, *Md.Name.ToString());
			}
		}
	}
	// (the rewards: a vault's chests hold things of the tier above; a gauntlet's chest three things of its tier)
	for (const int32 Key : SpecialChests)
	{
		const int32 Room = Containers.IsValidIndex(Key) ? RoomAt(GetContainerLocation(Key)) : -1;
		if (Room < 0) continue;
		const bool bVault = Rooms[Room].Kind == ERDRoomKind::Vault;
		const int32 Ti = bVault ? FMath::Min(Tier + 1, FMath::Max(Generator->MaxTier, 1)) : Tier;
		const TArray<FName> Got = RDM2TierItems(Generator, Ti, HashCombine((uint32)Seed ^ 0xC4E5u, (uint32)Key * 97u), bVault ? 2 : 3);
		TArray<FName>& L = Generator->ForcedLoot.FindOrAdd(FIntVector(Coord.X, Coord.Y, Key));
		for (const FName& Nm : Got) L.AddUnique(Nm);
	}
	// (a vault's key in a chest or trunk of another room of the set, by a hash of the set: the same one every time)
	for (int32 RI = 0; RI < Rooms.Num(); ++RI)
	{
		if (Rooms[RI].Kind != ERDRoomKind::Vault || Generator->FindItem(Generator->VaultKeyItem) < 0) continue;
		TArray<int32> Cands;
		for (int32 I = 0; I < Containers.Num(); ++I)
		{
			if (Containers[I].Partner >= 0 && Containers[I].Partner < I) continue;
			const int32 R = RoomAt(GetContainerLocation(I));
			if (R >= 0 && R != RI && Rooms[R].Kind != ERDRoomKind::Vault && (Containers[I].Kind == TEXT("chest") || Containers[I].Kind == TEXT("trunk"))) Cands.Add(I);
		}
		if (Cands.Num() == 0) continue;
		const int32 Pick = Cands[HashCombine((uint32)Seed ^ 0x6E7Bu, (uint32)RI) % (uint32)Cands.Num()];
		Generator->ForcedLoot.FindOrAdd(FIntVector(Coord.X, Coord.Y, ContainerKey(Pick))).AddUnique(Generator->VaultKeyItem);
		UE_LOG(LogRDMistward2, Log, TEXT("RDVAULT (%d,%d) room %d: its key in container %d (room %d)"), Coord.X, Coord.Y, RI, ContainerKey(Pick), RoomAt(GetContainerLocation(Pick)));
	}
}
