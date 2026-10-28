// random_dungeoncombat_level: the player's side of the fighting. The dungeon generator (bCombat) puts this component on
// the player pawn when play begins. It carries the three melee weapons of the generator's Weapons list (a mesh in her
// right hand, for some a shield on her left arm), her hit points and what each weapon does:
//   1 / 2 / 3 (D-pad left / up / right)   draw that weapon
//   left mouse button (X or RT)           attack: one of the weapon's attack clips is played over her locomotion as a
//                                          dynamic montage; at the clip's hit time every monster within the weapon's
//                                          reach and arc in front of her takes the weapon's damage
// Monsters hit her through ApplyDamage. Out of a fight her hit points come back slowly; at 0 she falls, and stands up
// again in the middle of the start section with full hit points. Tests and the demo reel drive the same functions
// (SetScriptedOnly keeps the real keys out).
// What is heard of her comes from here too (the generator's Sounds "Player.*"): a footstep for every stride on the
// ground (walking and running have their own sets; nothing else is heard of her moving), the swing and her effort,
// the weapon landing, her voice when she is hurt or falls. A blow she takes throws
// blood from her (the generator's URDBloodComponent).
// A weapon may be a spell (FRDWeaponDef::bSpell, random_dungeonmagic_level): the cast clip plays the same way, a charge
// burns on her hand until the release, and at the hit time a bolt leaves the hand and flies after the monster she
// turned to (one in front of her within the spell's reach that she can see); it bursts on the first monster or wall it
// meets. E casts it too (the left hand stays on WASD). Sounds "Player.Charge.<spell>", "Player.Cast.<spell>",
// "Player.Hit.<spell>" (the burst).
// The magic levels have a layout of their own (generator bCasterControls): on the gamepad RB attacks with the weapon in
// her hand, LB casts the spell (the one cast alongside it, or the drawn weapon when that is a spell), LT switches
// between walking and running (R on the keyboard), X opens (the generator), D-pad left / up / right draw weapon 1 / 2 / 3.
// random_dungeonmagic_level3 (generator bRogueControls): two daggers (a mesh in each hand) and a crossbow (a spell whose
// bolt is a mesh shot from the weapon, the next bolt lying on it until she has loaded again); the one not drawn is
// carried on her (FRDWeaponDef::HolsterBone). 1 / 2, the mouse wheel or Y switch, the left mouse button or RB uses the
// one in her hands, B rolls: toward the way she is moving (backward when she stands), moved by a root motion source
// while her clip plays in place; blows miss her for most of it (generator RollDodge).
// random_dungeonmagic_level4 (generator Heroes): she is the hero chosen in the menu, and the generator's fields are hers.
// Mana (generator PlayerMaxMana) comes back slowly (ManaPerSecond); a spell takes its ManaCost and is refused without it.
// Melee blows do MeleeBonus more, a ranged weapon's bolts RangedBonus more. Hit points do not come back by themselves
// (RegenPerSecond 0): potions and food do. What she finds in the containers goes into her inventory (I, Tab, the
// gamepad's Start: it pauses the game), with her weapons, which she wields from there.
#pragma once

#include "CoreMinimal.h"
#include "Components/ActorComponent.h"
#include "RDTypes.h"
#include "RDCombat.generated.h"

class ARDDungeonGenerator;
class ARDMonster;
class UStaticMeshComponent;
class USkeletalMeshComponent;
class UFXSystemComponent;
class UFXSystemAsset;
class UPointLightComponent;
class APlayerController;

UCLASS(ClassGroup = (RandomDungeon))
class CLAUDE_UE5_API URDCombatComponent : public UActorComponent
{
	GENERATED_BODY()

public:
	URDCombatComponent();
	void Init(ARDDungeonGenerator* InGenerator);

	UPROPERTY(BlueprintReadOnly, Category = "RandomDungeon|Combat") int32 Kills = 0;
	UPROPERTY(BlueprintReadOnly, Category = "RandomDungeon|Combat") int32 AttacksMade = 0;
	UPROPERTY(BlueprintReadOnly, Category = "RandomDungeon|Combat") int32 HitsLanded = 0;
	UPROPERTY(BlueprintReadOnly, Category = "RandomDungeon|Combat") int32 HitsTaken = 0;
	UPROPERTY(BlueprintReadOnly, Category = "RandomDungeon|Combat") int32 Deaths = 0;
	UPROPERTY(BlueprintReadOnly, Category = "RandomDungeon|Combat") float DamageDealt = 0.f;
	UPROPERTY(BlueprintReadOnly, Category = "RandomDungeon|Combat") float DamageTaken = 0.f;

	UFUNCTION(BlueprintCallable, Category = "RandomDungeon|Combat") void SelectWeapon(int32 Index);
	/** false while another attack is still going, or she is down */
	UFUNCTION(BlueprintCallable, Category = "RandomDungeon|Combat") bool StartAttack();
	/** an attack with that weapon of the generator's list (the drawn one, or a spell cast alongside it) */
	UFUNCTION(BlueprintCallable, Category = "RandomDungeon|Combat") bool StartAttackWith(int32 Index);
	/** the spell cast alongside the drawn weapon (FRDWeaponDef::bAlongside): what the right mouse button and E do */
	UFUNCTION(BlueprintCallable, Category = "RandomDungeon|Combat") bool StartSpell();
	/** the weapon of the attack going on (-1: none) */
	UFUNCTION(BlueprintCallable, BlueprintPure, Category = "RandomDungeon|Combat") int32 GetAttackIndex() const { return AttackTime >= 0.f ? AttackIndex : -1; }
	/** the generator's index of the spell cast alongside (-1: none) */
	UFUNCTION(BlueprintCallable, BlueprintPure, Category = "RandomDungeon|Combat") int32 GetAlongsideSpell() const;
	UFUNCTION(BlueprintCallable, Category = "RandomDungeon|Combat") void ApplyDamage(float Amount, AActor* From);
	/** full hit points, standing in the middle of the start section */
	UFUNCTION(BlueprintCallable, Category = "RandomDungeon|Combat") void Revive(bool bToStart = true);
	UFUNCTION(BlueprintCallable, Category = "RandomDungeon|Combat") void SetScriptedOnly(bool bOnly) { bScriptedOnly = bOnly; }
	/** tests: a key pressed (or let go) as if on the keyboard, through her player controller: the input mapping, her
	 *  movement and the combat keys read it as a real press. It stays down until it is let go. */
	UFUNCTION(BlueprintCallable, Category = "RandomDungeon|Combat") bool SimulateKey(FKey Key, bool bDown);
	/** tests: a stick or trigger axis (Gamepad_LeftX ...) held at Value as if on the gamepad, until it is set back to 0 */
	UFUNCTION(BlueprintCallable, Category = "RandomDungeon|Combat") bool SimulateAxis(FKey Key, float Value);
	/** the magic levels (generator bCasterControls): walking or running, switched with R or the left trigger. Her
	 *  character's MoveScale reads it from its RunMode variable (pipeline/unreal/819), which this sets. */
	UFUNCTION(BlueprintCallable, Category = "RandomDungeon|Combat") void SetRunMode(bool bRun);
	UFUNCTION(BlueprintCallable, BlueprintPure, Category = "RandomDungeon|Combat") bool IsRunMode() const { return bRunMode; }
	/** the magic levels: the last input came from a gamepad (the HUD shows its controls) rather than the keyboard and mouse */
	UFUNCTION(BlueprintCallable, BlueprintPure, Category = "RandomDungeon|Combat") bool IsUsingGamepad() const { return bUsingGamepad; }
	UFUNCTION(BlueprintCallable, BlueprintPure, Category = "RandomDungeon|Combat") float GetHealth() const { return Health; }
	UFUNCTION(BlueprintCallable, BlueprintPure, Category = "RandomDungeon|Combat") float GetMaxHealth() const { return MaxHealth; }
	UFUNCTION(BlueprintCallable, BlueprintPure, Category = "RandomDungeon|Combat") bool IsDead() const { return bDead; }
	UFUNCTION(BlueprintCallable, BlueprintPure, Category = "RandomDungeon|Combat") bool IsAttacking() const { return AttackTime >= 0.f; }
	UFUNCTION(BlueprintCallable, BlueprintPure, Category = "RandomDungeon|Combat") int32 GetWeaponIndex() const { return WeaponIndex; }
	UFUNCTION(BlueprintCallable, BlueprintPure, Category = "RandomDungeon|Combat") FName GetWeaponName() const;
	UFUNCTION(BlueprintCallable, BlueprintPure, Category = "RandomDungeon|Combat") float GetWeaponDamage() const;
	UFUNCTION(BlueprintCallable, BlueprintPure, Category = "RandomDungeon|Combat") float GetWeaponReach() const;
	/** seconds of the running attack (-1: none) and its length */
	UFUNCTION(BlueprintCallable, BlueprintPure, Category = "RandomDungeon|Combat") float GetAttackTime() const { return AttackTime; }
	UFUNCTION(BlueprintCallable, BlueprintPure, Category = "RandomDungeon|Combat") float GetAttackLength() const { return AttackLen; }
	/** the weapon in her hand (and the shield), for tests */
	UFUNCTION(BlueprintCallable, BlueprintPure, Category = "RandomDungeon|Combat") UStaticMeshComponent* GetWeaponMesh() const { return WeaponComp; }
	UFUNCTION(BlueprintCallable, BlueprintPure, Category = "RandomDungeon|Combat") UStaticMeshComponent* GetOffHandMesh() const { return OffHandComp; }
	UPROPERTY(BlueprintReadOnly, Category = "RandomDungeon|Combat") int32 StepsTaken = 0;
	/** spells: bolts cast, bolts that burst (on a monster / on a wall or at the end of their reach) */
	UPROPERTY(BlueprintReadOnly, Category = "RandomDungeon|Combat") int32 BoltsCast = 0;
	UPROPERTY(BlueprintReadOnly, Category = "RandomDungeon|Combat") int32 BoltsOnMonsters = 0;
	UPROPERTY(BlueprintReadOnly, Category = "RandomDungeon|Combat") int32 BoltsElsewhere = 0;
	/** where the last bolt left her hand and where it burst, how far it flew (cm) */
	UPROPERTY(BlueprintReadOnly, Category = "RandomDungeon|Combat") FVector LastBoltFrom = FVector::ZeroVector;
	UPROPERTY(BlueprintReadOnly, Category = "RandomDungeon|Combat") FVector LastBurstAt = FVector::ZeroVector;
	UPROPERTY(BlueprintReadOnly, Category = "RandomDungeon|Combat") float LastBoltFlown = 0.f;
	UFUNCTION(BlueprintCallable, BlueprintPure, Category = "RandomDungeon|Combat") bool IsSpell() const;
	/** bolts in the air now, and where (tests, the reel's record) */
	UFUNCTION(BlueprintCallable, BlueprintPure, Category = "RandomDungeon|Combat") TArray<FVector> GetBolts() const;
	/** the monster she turned to for the last attack (none: nothing in reach) */
	UFUNCTION(BlueprintCallable, BlueprintPure, Category = "RandomDungeon|Combat") ARDMonster* GetLastTarget() const { return LastTarget.Get(); }
	/** particles alive now in the spells' effects (charge, bolts, bursts) within Radius of Location (0: anywhere), and in
	 *  how many systems: what is seen, for tests (a count a frame old) */
	UFUNCTION(BlueprintCallable, Category = "RandomDungeon|Combat") int32 GetSpellParticles(FVector Location, float Radius, int32& Systems) const;
	/** the charge on her hand burns now */
	UFUNCTION(BlueprintCallable, BlueprintPure, Category = "RandomDungeon|Combat") bool IsCharging() const;
	/** the next (Step 1) or the one before (-1) of the weapons she draws */
	UFUNCTION(BlueprintCallable, Category = "RandomDungeon|Combat") void NextWeapon(int32 Step);
	/** the roll (generator RollClip): toward Dir (zero: the way she is moving, or backward when she stands; a way behind
	 *  her is a roll backward, facing as she does). False while one is going, just after one, in the air or down */
	UFUNCTION(BlueprintCallable, Category = "RandomDungeon|Combat") bool StartRoll(FVector Dir);
	UFUNCTION(BlueprintCallable, BlueprintPure, Category = "RandomDungeon|Combat") bool IsRolling() const { return RollTime >= 0.f; }
	UFUNCTION(BlueprintCallable, BlueprintPure, Category = "RandomDungeon|Combat") bool IsRollingBack() const { return RollTime >= 0.f && bRollBack; }
	/** blows miss her now (the middle of a roll) */
	UFUNCTION(BlueprintCallable, BlueprintPure, Category = "RandomDungeon|Combat") bool IsDodging() const;
	UPROPERTY(BlueprintReadOnly, Category = "RandomDungeon|Combat") int32 Rolls = 0;
	/** blows that missed her because she was rolling */
	UPROPERTY(BlueprintReadOnly, Category = "RandomDungeon|Combat") int32 DodgedHits = 0;
	/** a weapon carried on her while another is drawn (tests): its mesh, or its off-hand mesh */
	UFUNCTION(BlueprintCallable, BlueprintPure, Category = "RandomDungeon|Combat") UStaticMeshComponent* GetHolsterMesh(int32 Index, bool bOffHand) const;
	/** the bolt lying ready on the drawn weapon (tests) */
	UFUNCTION(BlueprintCallable, BlueprintPure, Category = "RandomDungeon|Combat") UStaticMeshComponent* GetLoadedBoltMesh() const { return LoadedBoltComp; }
	/** bolt meshes in flight and stuck where they struck (tests) */
	UFUNCTION(BlueprintCallable, BlueprintPure, Category = "RandomDungeon|Combat") int32 GetStuckBolts() const { return Stuck.Num(); }
	/** world time she was last hurt / last hit something (HUD) */
	float LastHurtTime = -100.f, LastHitTime = -100.f, DeathTime = -100.f;

	// ---- random_dungeonmagic_level4: mana, the hero's bonuses, her inventory (generator Heroes / Items)
	UFUNCTION(BlueprintCallable, BlueprintPure, Category = "RandomDungeon|Combat") float GetMana() const { return Mana; }
	UFUNCTION(BlueprintCallable, BlueprintPure, Category = "RandomDungeon|Combat") float GetMaxMana() const { return MaxMana; }
	/** tests: set her hit points / mana (clamped) */
	UFUNCTION(BlueprintCallable, Category = "RandomDungeon|Combat") void SetHealth(float Value) { Health = FMath::Clamp(Value, 0.f, MaxHealth); }
	UFUNCTION(BlueprintCallable, Category = "RandomDungeon|Combat") void SetMana(float Value) { Mana = FMath::Clamp(Value, 0.f, MaxMana); }
	/** what a blow or bolt of a weapon of the generator's list takes, with her bonus (melee or ranged) */
	UFUNCTION(BlueprintCallable, BlueprintPure, Category = "RandomDungeon|Combat") float GetDamageOf(int32 Index) const;
	/** casts refused for want of mana; world time of the last */
	UPROPERTY(BlueprintReadOnly, Category = "RandomDungeon|Combat") int32 CastsRefused = 0;
	float NoManaTime = -100.f;
	/** items she carries (the generator's Items by name) */
	UFUNCTION(BlueprintCallable, Category = "RandomDungeon|Combat") void AddItem(FName Name, int32 Count = 1);
	/** Count of an item taken from what she carries (a spare copy first) */
	UFUNCTION(BlueprintCallable, Category = "RandomDungeon|Combat") void RemoveItem(FName Name, int32 Count = 1) { RemoveCarried(Name, Count); }
	/** nothing carried, no armour on (the generator's RestartPlay) */
	UFUNCTION(BlueprintCallable, Category = "RandomDungeon|Combat") void ClearItems();
	UFUNCTION(BlueprintCallable, BlueprintPure, Category = "RandomDungeon|Combat") int32 GetItemCount(FName Name) const;
	/** drinks or eats one: false when she has none, or it would do nothing (full hit points or mana, no mana at all) */
	UFUNCTION(BlueprintCallable, Category = "RandomDungeon|Combat") bool UseItem(FName Name);
	UPROPERTY(BlueprintReadOnly, Category = "RandomDungeon|Combat") int32 ItemsUsed = 0;
	/** what is on her now: her speed's share more (the strongest speed potion), hit points a second (the foods together) */
	UFUNCTION(BlueprintCallable, BlueprintPure, Category = "RandomDungeon|Combat") float GetSpeedBonus() const;
	UFUNCTION(BlueprintCallable, BlueprintPure, Category = "RandomDungeon|Combat") float GetRegenPerSecond() const;
	/** her movement's top speed without potions (the character's own) */
	UFUNCTION(BlueprintCallable, BlueprintPure, Category = "RandomDungeon|Combat") float GetBaseWalkSpeed() const;
	struct FEffect { ERDItemKind Kind; float Amount; float Left; FName Item; };
	const TArray<FEffect>& GetEffects() const { return Effects; }
	/** the last thing the inventory did ("Drank a small healing potion  +10 HP") and when (HUD) */
	UPROPERTY(BlueprintReadOnly, Category = "RandomDungeon|Combat") FString Message;
	float MessageTime = -100.f;
	/** a line the HUD shows for a moment (level 5: a container that held nothing) */
	void ShowMessage(const FString& Text) { SetMessage(Text); }
	/** the inventory (I or Tab, the gamepad's Start): a list of her weapons, then the items she carries. Open, the game is
	 *  paused; W / S or the arrows, the wheel, the D-pad move the cursor, Enter, Space, E, the left mouse button or A
	 *  wield or use the one under it; I, Tab, Start or B close it. The generator works it every tick, paused or not. */
	UFUNCTION(BlueprintCallable, Category = "RandomDungeon|Combat") void SetInventoryOpen(bool bOpen);
	/** the open inventory pauses the game (off for the demo reel: the Movie Render Queue renders a world that goes on) */
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "RandomDungeon|Combat") bool bInventoryPausesGame = true;
	UFUNCTION(BlueprintCallable, BlueprintPure, Category = "RandomDungeon|Combat") bool IsInventoryOpen() const { return bInventoryOpen; }
	UFUNCTION(BlueprintCallable, BlueprintPure, Category = "RandomDungeon|Combat") int32 GetInventoryCursor() const { return InventoryCursor; }
	UFUNCTION(BlueprintCallable, Category = "RandomDungeon|Combat") void MoveInventoryCursor(int32 Step);
	/** wields the weapon / uses the item under the cursor */
	UFUNCTION(BlueprintCallable, Category = "RandomDungeon|Combat") bool UseInventoryEntry();
	/** the inventory's lines: "weapon|Sword" (her weapons, in the generator's order; a found one "weapon|<name>|<left>|
	 *  <full>"), then "item|<name>|<count>" (potions, food), "repair|<name>|<count>" (repair items), "armour|<name>|<1 when
	 *  she wears it>|<durability left>|<full>", "component|<name>|<count>" (crafting materials), "carried|<name>|<count>"
	 *  (weapons her hero cannot wield) (tests, HUD) */
	UFUNCTION(BlueprintCallable, BlueprintPure, Category = "RandomDungeon|Combat") TArray<FString> GetInventoryLines() const;
	/** every line whatever the tab (the third list's tabs show one tab's of them; weapons then stacked:
	 *  "weapon|<name>|<left>|<full>|<index>|<count>|<slash>", and "slash|<name>|<count>", "key|<name>|<count>",
	 *  "helmet|<1 hidden>|<set>") */
	UFUNCTION(BlueprintCallable, BlueprintPure, Category = "RandomDungeon|Combat") TArray<FString> GetAllInventoryLines() const;
	/** mistward (the generator's bMouseUI): the list's rows as the HUD drew them last ("<index>|<x0>|<y0>|<x1>|<y1>", canvas
	 *  pixels), the first row shown, and the first row the wheel scrolled to (-1: the list follows the cursor) (tests) */
	UFUNCTION(BlueprintCallable, BlueprintPure, Category = "RandomDungeon|Combat") TArray<FString> GetListRows() const;
	UFUNCTION(BlueprintCallable, BlueprintPure, Category = "RandomDungeon|Combat") int32 GetListFirst() const { return ListFirst; }
	UFUNCTION(BlueprintCallable, BlueprintPure, Category = "RandomDungeon|Combat") int32 GetListScroll() const { return ListScroll; }
	/** the pointer is shown (the inventory open with the mouse in use) */
	UFUNCTION(BlueprintCallable, BlueprintPure, Category = "RandomDungeon|Combat") bool IsPointerShown() const { return bPointerShown; }
	/** things used with a click (tests) */
	UPROPERTY(BlueprintReadOnly, Category = "RandomDungeon|Combat") int32 MouseUses = 0;
	/** the HUD's rows (written by ARDHUD::DrawInventory each frame) */
	TArray<TPair<int32, FBox2D>> ListRows;
	int32 ListFirst = 0, ListFit = 0, ListCount = 0, ListScroll = -1;

	// ---- random_dungeonmagic_level5: armour (an item of kind Armour she carries). Worn, its meshes (the fit made for her
	// hero) follow her body's pose; a blow on her takes its share less. One set at a time: wearing another takes the first
	// off; wearing the one she has on takes it off.
	/** puts the set on (or takes it off when she wears it): false when she does not carry it or it was not made for her */
	UFUNCTION(BlueprintCallable, Category = "RandomDungeon|Combat") bool WearArmour(FName Item);
	UFUNCTION(BlueprintCallable, Category = "RandomDungeon|Combat") void TakeOffArmour();
	UFUNCTION(BlueprintCallable, BlueprintPure, Category = "RandomDungeon|Combat") FName GetWornArmour() const { return WornArmour; }
	/** the share of a blow her armour takes off (0: none) */
	UFUNCTION(BlueprintCallable, BlueprintPure, Category = "RandomDungeon|Combat") float GetArmour() const;
	/** the worn set's meshes on her (tests) */
	UFUNCTION(BlueprintCallable, BlueprintPure, Category = "RandomDungeon|Combat") TArray<USkeletalMeshComponent*> GetArmourMeshes() const;
	/** tests: whether the worn armour follows her body as she is posed now, for a spread of the armour's vertices (Samples
	 *  in all) skinned on the CPU as they are drawn. Her skin: each one's nearest vertex of her body in the reference pose,
	 *  the change of their distance (cm; a plate skirt's vertex nearest the other leg changes as she runs). Her bones: a
	 *  vertex moved by one bone alone (98 %), its distance from where her bone of that name puts it (cm), and the same
	 *  had the armour stayed in its reference pose. Returns [skin samples, skin median, skin p95, bone samples, bone p95,
	 *  bone max, bone p95 left in the reference pose]; empty when a mesh's vertices cannot be read */
	UFUNCTION(BlueprintCallable, Category = "RandomDungeon|Combat") TArray<float> MeasureArmourFollow(int32 Samples = 400);
	/** a blow's damage before her armour and what it did (tests) */
	UPROPERTY(BlueprintReadOnly, Category = "RandomDungeon|Combat") float LastBlowBefore = 0.f;
	UPROPERTY(BlueprintReadOnly, Category = "RandomDungeon|Combat") float LastBlowTaken = 0.f;
	UPROPERTY(BlueprintReadOnly, Category = "RandomDungeon|Combat") int32 ArmourChanges = 0;
	void TickInventory(APlayerController* PC);
	/** armour's durability (the item's Durability): what is left of a set she carries (0, 0: none / it never wears). Each
	 *  blow that reaches her takes 1 off the worn set; at 0 it takes off half its share. A set found again while she carries
	 *  it is not kept twice: its pieces mend the one she has to full. */
	UFUNCTION(BlueprintCallable, BlueprintPure, Category = "RandomDungeon|Combat") float GetArmourWear(FName Item) const { const float* W = ArmourWear.Find(Item); return W ? *W : 0.f; }
	UFUNCTION(BlueprintCallable, BlueprintPure, Category = "RandomDungeon|Combat") float GetArmourDurability(FName Item) const;
	/** tests and the reel: set what is left of a set's durability */
	UFUNCTION(BlueprintCallable, Category = "RandomDungeon|Combat") void SetArmourWear(FName Item, float Value);
	/** the share of her speed the worn set takes (0: none) */
	UFUNCTION(BlueprintCallable, BlueprintPure, Category = "RandomDungeon|Combat") float GetArmourSlow() const;
	UPROPERTY(BlueprintReadOnly, Category = "RandomDungeon|Combat") int32 ArmourWornOut = 0;

	// ---- random_dungeonmagic_level5: repairs. Enter on a repair item in the inventory lists what it can mend (her armour
	// sets, the weapons she found); Enter on one gives it back the item's share of its full durability (up to full) and
	// uses the item up; Backspace or B goes back to the inventory.
	UFUNCTION(BlueprintCallable, Category = "RandomDungeon|Combat") bool BeginRepair(FName Item);
	UFUNCTION(BlueprintCallable, Category = "RandomDungeon|Combat") void CancelRepair();
	UFUNCTION(BlueprintCallable, BlueprintPure, Category = "RandomDungeon|Combat") bool IsPickingRepair() const { return !RepairWith.IsNone(); }
	UFUNCTION(BlueprintCallable, BlueprintPure, Category = "RandomDungeon|Combat") FName GetRepairItem() const { return RepairWith; }
	/** what the repair item can mend: "armour|<set>|<left>|<full>|<after>", "weapon|<index>|<name>|<left>|<full>|<after>" */
	UFUNCTION(BlueprintCallable, BlueprintPure, Category = "RandomDungeon|Combat") TArray<FString> GetRepairLines() const;
	UFUNCTION(BlueprintCallable, BlueprintPure, Category = "RandomDungeon|Combat") int32 GetRepairCursor() const { return RepairCursor; }
	UFUNCTION(BlueprintCallable, Category = "RandomDungeon|Combat") void MoveRepairCursor(int32 Step);
	/** mends the line under the cursor (or Line, when 0 or more) */
	UFUNCTION(BlueprintCallable, Category = "RandomDungeon|Combat") bool RepairEntry(int32 Line = -1);
	UPROPERTY(BlueprintReadOnly, Category = "RandomDungeon|Combat") int32 ItemsRepaired = 0;

	// ---- random_dungeonmagic_level5: crafting at an anvil (the generator opens it: F or X at an anvil). The game pauses as
	// for the inventory; W / S choose a recipe, Enter makes it, F, I, Tab, Backspace or B close it.
	UFUNCTION(BlueprintCallable, Category = "RandomDungeon|Combat") void SetCraftingOpen(bool bOpen);
	UFUNCTION(BlueprintCallable, BlueprintPure, Category = "RandomDungeon|Combat") bool IsCraftingOpen() const { return bCraftOpen; }
	UFUNCTION(BlueprintCallable, BlueprintPure, Category = "RandomDungeon|Combat") int32 GetCraftCursor() const { return CraftCursor; }
	UFUNCTION(BlueprintCallable, Category = "RandomDungeon|Combat") void MoveCraftCursor(int32 Step);
	/** the recipes: "recipe|<item>|<1 she can make it>|<part label>:<have>:<need>;..." */
	UFUNCTION(BlueprintCallable, BlueprintPure, Category = "RandomDungeon|Combat") TArray<FString> GetCraftLines() const;
	/** how many of a recipe part she carries (any of its kinds together) */
	int32 PartHave(const FRDRecipePart& Part) const;
	/** what making a recipe takes of each kind, all its parts drawn from one count (false: she lacks some) */
	bool PlanCraft(const FRDRecipe& Recipe, TMap<FName, int32>& Take) const;
	UFUNCTION(BlueprintCallable, BlueprintPure, Category = "RandomDungeon|Combat") bool CanCraft(FName Item) const;
	/** makes one (false: no such recipe, or she lacks what it takes); uses the parts up */
	UFUNCTION(BlueprintCallable, Category = "RandomDungeon|Combat") bool Craft(FName Item);
	UFUNCTION(BlueprintCallable, Category = "RandomDungeon|Combat") bool CraftEntry();
	UPROPERTY(BlueprintReadOnly, Category = "RandomDungeon|Combat") int32 ItemsCrafted = 0;
	/** the frame the crafting panel was shut on (the generator's F, read after it in the same frame, must not open it again) */
	uint64 CraftClosedFrame = 0;

	// ---- random_dungeonmagic_level5: weapons found in the containers (items of kind Weapon). One her hero can wield (the
	// item has a fit for her) joins her weapons as she finds it, with its durability: every attack of it that hits a monster
	// (a blow, a bolt) takes 1 off, and at 0 it breaks and is gone (she draws the next one). The weapons she starts with
	// never break. One she cannot wield stays among her items.
	/** what is left of a weapon's durability, and its full durability (0, 0: it never breaks) */
	UFUNCTION(BlueprintCallable, BlueprintPure, Category = "RandomDungeon|Combat") float GetWeaponWear(int32 Index) const { return Wear.IsValidIndex(Index) ? Wear[Index] : 0.f; }
	UFUNCTION(BlueprintCallable, BlueprintPure, Category = "RandomDungeon|Combat") float GetWeaponDurability(int32 Index) const;
	/** weapons that broke */
	UPROPERTY(BlueprintReadOnly, Category = "RandomDungeon|Combat") int32 WeaponsBroken = 0;
	UPROPERTY(BlueprintReadOnly, Category = "RandomDungeon|Combat") FName LastBroken;
	/** found weapons she took up (wieldable) / kept as items (not for her) */
	UPROPERTY(BlueprintReadOnly, Category = "RandomDungeon|Combat") int32 WeaponsTaken = 0;
	/** tests: set what is left of a weapon's durability */
	UFUNCTION(BlueprintCallable, Category = "RandomDungeon|Combat") void SetWeaponWear(int32 Index, float Value) { if (Wear.IsValidIndex(Index)) Wear[Index] = Value; }
	/** the hero's own weapons again, the first drawn (the generator's RestartPlay) */
	UFUNCTION(BlueprintCallable, Category = "RandomDungeon|Combat") void ResetWeapons();
	/** a weapon item: she takes it up (true) or it is not made for her hero (false) */
	bool TakeWeapon(FName Item);
	/** the sound name of a weapon (its SoundKey, else its name) */
	static FName WeaponSound(const FRDWeaponDef& W) { return W.SoundKey.IsNone() ? W.Name : W.SoundKey; }

	// ---- random_dungeonmagic_level5: the spell table (the generator's Spells). A spell of her weapons (FRDWeaponDef::SpellIndex)
	// does at its release what its Kind says; spells have cooldowns; tomes teach new ones (Learns on her hero's card).
	// Monsters' abilities poison, weaken or slow her; Dispel Hex ends them. Rings add to her mana, hit points or ranged
	// damage. At an anvil she breaks the weapons she found down into crafting materials.
	bool IsScriptedOnly() const { return bScriptedOnly; }
	/** seconds before a weapon of the generator's list can be cast again (0: ready) */
	UFUNCTION(BlueprintCallable, BlueprintPure, Category = "RandomDungeon|Spells") float GetCooldownLeft(int32 Index) const;
	/** the spell joins her weapons (false: her hero does not learn its type, or she knows it) */
	UFUNCTION(BlueprintCallable, Category = "RandomDungeon|Spells") bool LearnSpell(FName Spell);
	UFUNCTION(BlueprintCallable, BlueprintPure, Category = "RandomDungeon|Spells") bool KnowsSpell(FName Spell) const;
	UPROPERTY(BlueprintReadOnly, Category = "RandomDungeon|Spells") int32 SpellsLearned = 0;
	/** spells released (each kind's own count: tests), blows a ward took, blows turned back, deaths cheated, blows she
	 *  slipped under a veil, blows a sanctum or rune took */
	UPROPERTY(BlueprintReadOnly, Category = "RandomDungeon|Spells") TMap<FName, int32> SpellsReleased;
	UPROPERTY(BlueprintReadOnly, Category = "RandomDungeon|Spells") int32 WardBlocks = 0;
	UPROPERTY(BlueprintReadOnly, Category = "RandomDungeon|Spells") int32 Reflected = 0;
	UPROPERTY(BlueprintReadOnly, Category = "RandomDungeon|Spells") int32 PactSaves = 0;
	UPROPERTY(BlueprintReadOnly, Category = "RandomDungeon|Spells") int32 Evaded = 0;
	UPROPERTY(BlueprintReadOnly, Category = "RandomDungeon|Spells") int32 ZoneBlocks = 0;
	UPROPERTY(BlueprintReadOnly, Category = "RandomDungeon|Spells") int32 CooldownRefusals = 0;
	/** hit points back (a drain, a dark fire's burn) */
	UFUNCTION(BlueprintCallable, Category = "RandomDungeon|Spells") void HealBy(float Amount);
	/** a burn's or a cloud's hurt counts as hers */
	void CountSpellDamage(float Amount);
	/** monsters do not see her (Shadow Veil) */
	UFUNCTION(BlueprintCallable, BlueprintPure, Category = "RandomDungeon|Spells") bool IsVeiled() const;
	/** what is on her: "<label>|<seconds left>|<good 1 / bad 0>" (spells, poison, weakness, slowness) */
	UFUNCTION(BlueprintCallable, BlueprintPure, Category = "RandomDungeon|Spells") TArray<FString> GetBuffLines() const;
	/** a monster's blow carried its ability (poison, weaken, slow) with Power (its tier's) */
	UFUNCTION(BlueprintCallable, Category = "RandomDungeon|Spells") void ApplyMonsterAbility(ERDMonsterAbility Ability, float Power, float Blow);
	/** her poison, weakness and slowness end (Dispel Hex) */
	UFUNCTION(BlueprintCallable, Category = "RandomDungeon|Spells") void ClearAfflictions();
	UFUNCTION(BlueprintCallable, BlueprintPure, Category = "RandomDungeon|Spells") bool IsPoisoned() const;
	UFUNCTION(BlueprintCallable, BlueprintPure, Category = "RandomDungeon|Spells") float GetWeakness() const;
	UFUNCTION(BlueprintCallable, BlueprintPure, Category = "RandomDungeon|Spells") float GetSlowness() const;
	/** the shares her shields take now (tests): ward hits left, ward pool left, armour from Iron Skin */
	UFUNCTION(BlueprintCallable, BlueprintPure, Category = "RandomDungeon|Spells") int32 GetWardHits() const;
	UFUNCTION(BlueprintCallable, BlueprintPure, Category = "RandomDungeon|Spells") float GetWardPool() const;
	UFUNCTION(BlueprintCallable, BlueprintPure, Category = "RandomDungeon|Spells") float GetSkinBonus() const;
	/** the spells' areas on the ground now (clouds, burning ground, rifts, meteor storms; tests) */
	UFUNCTION(BlueprintCallable, BlueprintPure, Category = "RandomDungeon|Spells") int32 GetSpellAreas() const { return Areas.Num(); }
	/** tests: the release of a spell of her weapons without its clip (at the monster she faces, or Target) */
	UFUNCTION(BlueprintCallable, Category = "RandomDungeon|Spells") bool CastSpellNow(int32 Index, ARDMonster* Target = nullptr);
	// ---- rings
	/** puts a ring on (the one of its kind she wore comes off) or takes it off; false: she does not carry it, or her hero
	 *  does not wear its kind */
	UFUNCTION(BlueprintCallable, Category = "RandomDungeon|Rings") bool WearRing(FName Item);
	UFUNCTION(BlueprintCallable, BlueprintPure, Category = "RandomDungeon|Rings") FName GetWornRing(ERDRingKind Kind) const { const FName* N = WornRings.Find((uint8)Kind); return N ? *N : NAME_None; }
	/** the share more her worn ring of a kind gives (0: none) */
	UFUNCTION(BlueprintCallable, BlueprintPure, Category = "RandomDungeon|Rings") float GetRingBonus(ERDRingKind Kind) const;
	// ---- breaking found weapons down at an anvil
	/** a found weapon of her weapons (Index) or one she carries but cannot wield (Item) broken into materials */
	UFUNCTION(BlueprintCallable, Category = "RandomDungeon|Crafting") bool BreakDownWeapon(int32 Index);
	UFUNCTION(BlueprintCallable, Category = "RandomDungeon|Crafting") bool BreakDownItem(FName Item);
	UPROPERTY(BlueprintReadOnly, Category = "RandomDungeon|Crafting") int32 WeaponsBrokenDown = 0;
	/** what a weapon item breaks into ("<item>:<count>;...", "" none) */
	FString BreakdownText(FName Item, const FString& Type) const;

	// ---- mistward_castle: traps hold her (a snare, a pit), shields, a torch, armour kept set by set, her things dropped
	/** she cannot move for Seconds (a snare, a pit) */
	UFUNCTION(BlueprintCallable, Category = "RandomDungeon|Mistward") void HoldFor(float Seconds);
	UFUNCTION(BlueprintCallable, BlueprintPure, Category = "RandomDungeon|Mistward") bool IsHeld() const;
	/** the shield in her left hand (an item of kind Shield; none: none), and its share of a blow now (0 while it is not in
	 *  her hand: a two-handed weapon or a bow drawn, the torch held) */
	UFUNCTION(BlueprintCallable, BlueprintPure, Category = "RandomDungeon|Mistward") FName GetWornShield() const { return WornShield; }
	UFUNCTION(BlueprintCallable, BlueprintPure, Category = "RandomDungeon|Mistward") float GetShieldShare() const;
	UFUNCTION(BlueprintCallable, BlueprintPure, Category = "RandomDungeon|Mistward") bool IsShieldInHand() const;
	/** what is left of a carried shield's (or armour set's) durability: the copy worn (or the first), and the spare copies */
	UFUNCTION(BlueprintCallable, BlueprintPure, Category = "RandomDungeon|Mistward") float GetShieldWear(FName Item) const { const float* W = ArmourWear.Find(Item); return W ? *W : 0.f; }
	UFUNCTION(BlueprintCallable, BlueprintPure, Category = "RandomDungeon|Mistward") TArray<float> GetSpares(FName Item) const { const TArray<float>* S = Spares.Find(Item); return S ? *S : TArray<float>(); }
	/** puts the shield in her left hand (or takes it off when it is there): false when she does not carry it or cannot */
	UFUNCTION(BlueprintCallable, Category = "RandomDungeon|Mistward") bool WearShield(FName Item);
	/** the torch in her left hand (on / off; false: she has none) */
	UFUNCTION(BlueprintCallable, Category = "RandomDungeon|Mistward") bool HoldTorch(bool bHold);
	UFUNCTION(BlueprintCallable, BlueprintPure, Category = "RandomDungeon|Mistward") bool IsTorchHeld() const { return bTorchHeld; }
	/** the torch's light on her (tests) */
	UFUNCTION(BlueprintCallable, BlueprintPure, Category = "RandomDungeon|Mistward") UPointLightComponent* GetTorchLight() const { return TorchLight; }
	UFUNCTION(BlueprintCallable, BlueprintPure, Category = "RandomDungeon|Mistward") UStaticMeshComponent* GetLeftHandMesh() const { return LeftComp; }
	/** blows her shield took, shields broken */
	UPROPERTY(BlueprintReadOnly, Category = "RandomDungeon|Mistward") int32 ShieldBlocks = 0;
	UPROPERTY(BlueprintReadOnly, Category = "RandomDungeon|Mistward") int32 ShieldsBroken = 0;
	UPROPERTY(BlueprintReadOnly, Category = "RandomDungeon|Mistward") float LastShieldTook = 0.f;
	/** everything she found (not the weapons her hero starts with): what drops when she falls; Wear: durability left (-1 none) */
	void GatherDroppable(TArray<FName>& Things, TArray<float>& WearOut) const;
	/** her dropped things taken up again */
	void TakeBack(const TArray<FName>& Things, const TArray<float>& WearIn, bool bHers = true, FName Rewear = NAME_None);
	/** breaking a set of armour or a shield down at an anvil (a spare first; the one worn only when it is the last) */
	UFUNCTION(BlueprintCallable, Category = "RandomDungeon|Crafting") bool BreakDownGear(FName Item);
	UPROPERTY(BlueprintReadOnly, Category = "RandomDungeon|Mistward") int32 GearBrokenDown = 0;

	// ---- the third list (docs/improvements2.txt; RDMistward2.cpp): tabs, stacks, quick slots, the helmet, blocking, slashes
	/** the inventory's tab (0 weapons, 1 armour, 2 potions and food, 3 crafting, 4 magic) when the generator's bInventoryTabs */
	UFUNCTION(BlueprintCallable, BlueprintPure, Category = "RandomDungeon|Mistward2") int32 GetInventoryTab() const { return InvTab; }
	UFUNCTION(BlueprintCallable, Category = "RandomDungeon|Mistward2") void SetInventoryTab(int32 Tab);
	static constexpr int32 NumTabs = 5;
	/** the tab a line of the inventory belongs in (by its kind, the first field) */
	static int32 TabOfLine(const FString& Line);
	/** the HUD's tabs as it drew them (the pointer clicks them); "<x0>|<y0>|<x1>|<y1>" each (tests) */
	TArray<FBox2D> TabBoxes;
	UFUNCTION(BlueprintCallable, BlueprintPure, Category = "RandomDungeon|Mistward2") TArray<FString> GetTabBoxes() const
	{
		TArray<FString> Out;
		for (const FBox2D& B : TabBoxes) Out.Add(FString::Printf(TEXT("%.1f|%.1f|%.1f|%.1f"), B.Min.X, B.Min.Y, B.Max.X, B.Max.Y));
		return Out;
	}
	/** the quick slots (bQuickSlots): each the name of a weapon or spell of hers (none: empty) */
	UFUNCTION(BlueprintCallable, BlueprintPure, Category = "RandomDungeon|Mistward2") TArray<FName> GetQuickSlots() const { return QuickSlots; }
	/** a weapon of her list (Index) into a slot (0..9); false: no such weapon, or one cast alongside */
	UFUNCTION(BlueprintCallable, Category = "RandomDungeon|Mistward2") bool AssignQuickSlot(int32 Slot, int32 Index);
	/** draws what a slot holds (false: empty, or not hers any more) */
	UFUNCTION(BlueprintCallable, Category = "RandomDungeon|Mistward2") bool SelectQuickSlot(int32 Slot);
	/** the next (Step 1) or the one before (-1) filled slot after the drawn one */
	UFUNCTION(BlueprintCallable, Category = "RandomDungeon|Mistward2") void CycleQuickSlot(int32 Step);
	/** the slot the drawn weapon is in (-1: none), the slot the gamepad's Y puts the chosen row into */
	UFUNCTION(BlueprintCallable, BlueprintPure, Category = "RandomDungeon|Mistward2") int32 GetQuickSlotOfDrawn() const;
	UFUNCTION(BlueprintCallable, BlueprintPure, Category = "RandomDungeon|Mistward2") int32 GetAssignSlot() const { return AssignSlot; }
	/** her weapon list's index of the weapon a slot names (-1: none) */
	int32 WeaponOfSlot(int32 Slot) const;
	/** slots filled the first time and as she finds weapons or learns spells */
	void FillQuickSlots();
	/** the worn set's helmet shown or hidden (bHelmetToggle); false: the set has none */
	UFUNCTION(BlueprintCallable, Category = "RandomDungeon|Mistward2") bool ToggleHelmet();
	UFUNCTION(BlueprintCallable, BlueprintPure, Category = "RandomDungeon|Mistward2") bool HasHelmet() const;
	UFUNCTION(BlueprintCallable, BlueprintPure, Category = "RandomDungeon|Mistward2") bool IsHelmetHidden() const { return bHelmetHidden; }
	/** the worn set's meshes that have a helmet (tests) */
	UFUNCTION(BlueprintCallable, BlueprintPure, Category = "RandomDungeon|Mistward2") TArray<USkeletalMeshComponent*> GetHelmetMeshes() const;
	/** its helmet's sections (those her head bone moves): "<mesh>|<lod>|<section>|<vertices>|<1 hidden>" (tests) */
	UFUNCTION(BlueprintCallable, BlueprintPure, Category = "RandomDungeon|Mistward2") TArray<FString> GetHelmetLines() const;
	/** blocking with the shield (the generator's bShieldBlock): held on the right mouse button or LT; tests set it */
	UFUNCTION(BlueprintCallable, BlueprintPure, Category = "RandomDungeon|Mistward2") bool IsBlocking() const { return bBlocking; }
	UFUNCTION(BlueprintCallable, Category = "RandomDungeon|Mistward2") void SetBlocking(bool bOn);
	/** blows taken while blocking; the share the block took of the last */
	UPROPERTY(BlueprintReadOnly, Category = "RandomDungeon|Mistward2") int32 BlockedHits = 0;
	UPROPERTY(BlueprintReadOnly, Category = "RandomDungeon|Mistward2") float LastShieldShare = 0.f;
	UPROPERTY(BlueprintReadOnly, Category = "RandomDungeon|Mistward2") float LastShieldWear = 0.f;
	/** a slash put on a weapon of hers (her list's Index), the one there before back in her pack (false: not hers to put on) */
	UFUNCTION(BlueprintCallable, Category = "RandomDungeon|Mistward2") bool ApplySlash(FName Slash, int32 Index);
	/** the slash on a weapon taken off, back into her pack */
	UFUNCTION(BlueprintCallable, Category = "RandomDungeon|Mistward2") bool RemoveSlash(int32 Index);
	/** choosing the weapon a slash goes on (Enter on a slash in the inventory): its lines "weapon|<index>|<name>|<slash on it>" */
	UFUNCTION(BlueprintCallable, BlueprintPure, Category = "RandomDungeon|Mistward2") bool IsPickingSlash() const { return !SlashWith.IsNone(); }
	UFUNCTION(BlueprintCallable, BlueprintPure, Category = "RandomDungeon|Mistward2") FName GetSlashItem() const { return SlashWith; }
	UFUNCTION(BlueprintCallable, BlueprintPure, Category = "RandomDungeon|Mistward2") TArray<FString> GetSlashLines() const;
	UFUNCTION(BlueprintCallable, BlueprintPure, Category = "RandomDungeon|Mistward2") int32 GetSlashCursor() const { return SlashCursor; }
	/** the slash list's cursor a line down or up, as W / S move it (a reel's pilot) */
	UFUNCTION(BlueprintCallable, Category = "RandomDungeon|Mistward2") void MoveSlashCursor(int32 Step) { const int32 N = GetSlashLines().Num(); if (N > 0) SlashCursor = ((SlashCursor + Step) % N + N) % N; }
	UFUNCTION(BlueprintCallable, Category = "RandomDungeon|Mistward2") bool BeginSlash(FName Slash);
	UFUNCTION(BlueprintCallable, Category = "RandomDungeon|Mistward2") void CancelSlash();
	UFUNCTION(BlueprintCallable, Category = "RandomDungeon|Mistward2") bool SlashEntry(int32 Line = -1);
	/** a slash's work, counted by its effect's name (tests): hits that carried it; what each did */
	UPROPERTY(BlueprintReadOnly, Category = "RandomDungeon|Mistward2") TMap<FString, int32> SlashProcs;
	UPROPERTY(BlueprintReadOnly, Category = "RandomDungeon|Mistward2") float SlashBonusDealt = 0.f;
	/** the slash's effects on her now: haste (attack speed), evasion, the crystal's shield, deflection (tests, the HUD) */
	UFUNCTION(BlueprintCallable, BlueprintPure, Category = "RandomDungeon|Mistward2") float GetHaste() const;
	UFUNCTION(BlueprintCallable, BlueprintPure, Category = "RandomDungeon|Mistward2") float GetSlashEvade() const;
	UFUNCTION(BlueprintCallable, BlueprintPure, Category = "RandomDungeon|Mistward2") bool HasSlashShield() const;
	UFUNCTION(BlueprintCallable, BlueprintPure, Category = "RandomDungeon|Mistward2") float GetSlashDeflect() const;
	/** tests: a hit of a weapon's slash on a monster now (its bonus and effect), as a blow that landed would */
	UFUNCTION(BlueprintCallable, Category = "RandomDungeon|Mistward2") bool ApplySlashHitNow(int32 Index, ARDMonster* Target);
	/** the slash effects in the world now (swing and hit systems alive; tests) */
	UFUNCTION(BlueprintCallable, BlueprintPure, Category = "RandomDungeon|Mistward2") int32 GetSlashFxAlive() const;
	/** the slash of a weapon of hers (none) */
	const FRDSlashDef* SlashOf(int32 Index) const;
	/** a shrine's blessing on her: its name, until when, and what it gives (her blows' share more, blows on her a share less;
	 *  swiftness goes in as a speed effect) */
	UFUNCTION(BlueprintCallable, Category = "RandomDungeon|Mistward2") void Bless(const FString& Name, float Damage, float Armour, float Speed, float Seconds);
	UFUNCTION(BlueprintCallable, BlueprintPure, Category = "RandomDungeon|Mistward2") FString GetBlessing() const;
	UFUNCTION(BlueprintCallable, BlueprintPure, Category = "RandomDungeon|Mistward2") float GetBlessDamage() const;
	UFUNCTION(BlueprintCallable, BlueprintPure, Category = "RandomDungeon|Mistward2") float GetBlessArmour() const;
	/** a fountain's draught: hit points (a share of hers), speed (a share, seconds), mana (all of it); false: it would do nothing */
	bool DrinkFountain(ERDRoomKind Kind);
	/** the shield her hero starts with (bKeepStartGear: it never breaks and stays with her) */
	FName StartShieldOf() const;
	/** the slash effects' areas (burning ground, a void's pull) */
	struct FSlashArea { FVector At = FVector::ZeroVector; float Radius = 0.f, Dps = 0.f, Left = 0.f, Pull = 0.f, Slow = 0.f, Acc = 0.f; TWeakObjectPtr<UFXSystemComponent> Fx; };
	TArray<FSlashArea> SlashAreas;
	void TickSlashAreas(float Dt);

	virtual void TickComponent(float DeltaTime, ELevelTick TickType, FActorComponentTickFunction* ThisTickFunction) override;

private:
	// ---- the third list
	FString BlessName;
	float BlessUntil = -100.f, BlessDmg = 0.f, BlessArm = 0.f;
	int32 LastWeaponCount = -1;
	int32 InvTab = 0;
	TArray<FName> QuickSlots;
	int32 AssignSlot = 0;
	bool bHelmetHidden = false;
	bool bBlocking = false, bBlockKeyDown = false;
	/** the block's held pose (a paused montage: stopping the slot did not blend it out; it is resumed, then stopped) */
	TWeakObjectPtr<class UAnimMontage> BlockMontage;
	FName SlashWith;
	int32 SlashCursor = 0;
	float HasteUntil = -100.f, HasteShare = 0.f, SlashEvadeUntil = -100.f, SlashEvadeShare = 0.f, SlashShieldReadyAt = -100.f;
	bool bSlashShieldUp = false;
	float DeflectUntil = -100.f, DeflectShare = 0.f;
	/** per monster (its unique id): when the stun may hold it again */
	TMap<uint32, float> StunReadyAt;
	UPROPERTY(Transient) TArray<TObjectPtr<UFXSystemComponent>> SlashFxComps;
	bool bSwingFxDone = false;
	/** the swing's slash effect (at the hit's moment, along her facing) */
	void PlaySwingSlash(const FRDSlashDef& S, const FVector& Dir);
	/** a hit with a slash on a monster: its bonus (with Dmg, the hit's own damage, for the shares) and effect */
	void SlashHit(const FRDSlashDef& S, ARDMonster* Mo, float Dmg, const FVector& At, bool bPrimary = true);
	void TickBlocking(const class APlayerController* PC);
	void TickThirdListInput(const class APlayerController* PC);
	/** the inventory's lines of one tab (bInventoryTabs) */
	TArray<FString> TabLines(int32 Tab) const;
	/** the weapon lines with stacks: "weapon|<name>|<left>|<full>|<index>|<count>|<slash>" */
	void StackedWeaponLines(TArray<FString>& Out) const;
	void UpdateHelmet();
	// ---- level 5: spells on her and around her
	TMap<FName, float> ReadyAt;
	TMap<uint8, FName> WornRings;
	FRandomStream SpellR;
	float WardUntil = -100.f, WardPool = 0.f; int32 WardHits = 0;
	float SkinUntil = -100.f, SkinShare = 0.f, VeilUntil = -100.f, VeilEvade = 0.f, MirrorUntil = -100.f, MirrorShare = 0.f;
	float PactUntil = -100.f, PactShare = 0.f, DispelUntil = -100.f;
	FVector RuneAt = FVector::ZeroVector, SanctumAt = FVector::ZeroVector;
	float RuneRadius = 0.f, RuneUntil = -100.f, RuneShare = 0.f, SanctumRadius = 0.f, SanctumUntil = -100.f;
	float PoisonDps = 0.f, PoisonUntil = -100.f, PoisonAcc = 0.f, WeakShare = 0.f, WeakUntil = -100.f, SlowMeShare = 0.f, SlowMeUntil = -100.f;
	bool bSlowMeOn = false;
	TWeakObjectPtr<ARDMonster> DrainTarget;
	float DrainUntil = -100.f, DrainDps = 0.f, DrainShare = 0.f, DrainTick = 0.f, DrainWisp = 0.f; int32 DrainSpell = -1;
	struct FArea
	{
		ERDSpellKind Kind = ERDSpellKind::Cloud; FVector At = FVector::ZeroVector;
		float Radius = 0.f, Left = 0.f, Dps = 0.f, Slow = 0.f, Every = 0.f, FxTimer = 0.f, HurtTimer = 0.f, StrikeTimer = 0.f;
		int32 Spell = -1, Strikes = 0;
		TWeakObjectPtr<UFXSystemComponent> Fx;
	};
	TArray<FArea> Areas;
	/** the shields and glows on her, by the spell kind that put them there */
	TMap<uint8, TWeakObjectPtr<UFXSystemComponent>> Auras;
	const FRDSpellDef* SpellOf(int32 WeaponIndex) const;
	void ReleaseSpell(int32 WeaponIndex);
	void TickSpells(float Dt, float Now);
	void SetAura(ERDSpellKind Kind, const FRDSpellDef* S, bool bOn, float Seconds = 0.f);
	FVector SpellTargetPoint(float Reach) const;
	/** a spell's hurt on a monster (its numbers, its kill counted as hers) */
	void SpellHurt(ARDMonster* Mo, float Dmg, const FVector& Where, bool bWound);
	UFXSystemComponent* SpawnSpellFx(UFXSystemAsset* Asset, const FVector& At, const FRotator& Rot, float Scale, const FRDSpellDef* S, USceneComponent* AttachTo = nullptr, FName Socket = NAME_None);
	/** her hit points fall by Amount (poison, a nova's price): she falls at 0 unless a pact holds */
	void LoseHealth(float Amount);
	void Fall();
	void UpdateMaxima();
	float WeakMul() const;
	UPROPERTY(Transient) TObjectPtr<ARDDungeonGenerator> Generator;
	UPROPERTY(Transient) TObjectPtr<UStaticMeshComponent> WeaponComp;
	UPROPERTY(Transient) TObjectPtr<UStaticMeshComponent> OffHandComp;
	/** per weapon (2 x its index, + 1 the off hand): its meshes carried on her while it is not drawn */
	UPROPERTY(Transient) TArray<TObjectPtr<UStaticMeshComponent>> HolsterComps;
	UPROPERTY(Transient) TObjectPtr<UStaticMeshComponent> LoadedBoltComp;
	UPROPERTY(Transient) TArray<TObjectPtr<USkeletalMeshComponent>> ArmourComps;
	FName WornArmour;
	// ---- mistward
	FName WornShield;
	bool bTorchHeld = false;
	FName TorchItem;
	/** a list's cursor held on a key: it steps again after a moment, then quickly */
	int32 KeyRepeatDir = 0;
	double KeyRepeatAt = 0.0;
	float HeldUntil = -100.f;
	bool bHeldOn = false;
	/** the spare copies of a set of armour or a shield she carries (each copy's durability left) */
	TMap<FName, TArray<float>> Spares;
	UPROPERTY(Transient) TObjectPtr<UStaticMeshComponent> LeftComp;
	UPROPERTY(Transient) TObjectPtr<UPointLightComponent> TorchLight;
	UPROPERTY(Transient) TObjectPtr<UFXSystemComponent> TorchFlame;
	/** what her left hand shows: the drawn weapon's own off-hand mesh, her shield, or the torch */
	void UpdateLeftHand();
	const FRDWeaponFit* FitOf(FName Item) const;
	void WearDownShield(float Took);
	void ShowLoadedBolt(bool bShow);
	// ---- the roll
	float RollTime = -1.f, RollLen = 0.f, RollReadyAt = -100.f;
	bool bRollBack = false, bRollIgnoringMove = false;
	uint16 RollSourceId = 0;
	void EndRoll();
	float Health = 100.f, MaxHealth = 100.f;
	float Mana = 0.f, MaxMana = 0.f;
	/** her top speed is set from SavedWalkSpeed while she is slowed (an attack) or a speed potion is on her */
	bool bSpeedOverride = false;
	TMap<FName, int32> Carried;
	TArray<FName> CarriedOrder;
	TArray<FEffect> Effects;
	bool bInventoryOpen = false;
	int32 InventoryCursor = 0;
	float InventoryRepeat = 0.f;
	/** mistward: the pointer shown, where it was last tick (a row is chosen only when it moves) */
	bool bPointerShown = false;
	FVector2D LastPointer = FVector2D(-1.f, -1.f);
	/** the row the pointer used last and when: the second click of a double click is a press too, and used it again */
	int32 LastUseRow = -1;
	double LastUseTime = -100.0;
	void ResetListView();
	void ShowPointer(bool bShow);
	/** the mouse on a list: hover chooses, a click on the chosen row uses it, the wheel scrolls; true when it acted */
	void TickPointerList(APlayerController* PC, int32 Cur, TFunctionRef<void(int32)> Choose, TFunctionRef<void()> Use);
	TMap<FName, float> ArmourWear;
	FName RepairWith;
	int32 RepairCursor = 0;
	bool bCraftOpen = false;
	int32 CraftCursor = 0;
	void WearDownArmour();
	void RemoveCarried(FName Name, int32 Count);
	void PlayUiSound(FName Key, FName Fallback);
	void SetMessage(const FString& Text);
	void UpdateWalkSpeed();
	void TickEffects(float Dt);
	int32 WeaponIndex = -1, AttackIndex = -1;
	/** per weapon: which of its attack clips comes next */
	TArray<int32> NextOf;
	/** per weapon of the generator's list: what is left of its durability (0: it never breaks) */
	TArray<float> Wear;
	/** weapons whose durability ran out this tick (broken at the end of it: a bolt may still be on its way) */
	TArray<int32> PendingBreak;
	void SyncWear();
	void WearOut(int32 Index);
	void BreakWeapon(int32 Index);
	float AttackTime = -1.f, AttackLen = 0.f, AttackHit = 0.f, SavedWalkSpeed = 0.f;
	bool bHitDone = false, bDead = false, bScriptedOnly = false, bSlowed = false;
	float StaggerUntil = -100.f;
	// ---- the magic levels' controls (generator bCasterControls)
	bool bRunMode = false, bUsingGamepad = false, bRunToggleDown = false;
	void TickDevice(const APlayerController* PC);
	void TickCasterInput(const APlayerController* PC);
	// sound
	float StepDist = 0.f;
	bool bWhooshDone = false, bFallDone = false;
	void TickSounds(float Dt, float Now);
	const FRDWeaponDef* Weapon() const;
	/** the weapon of the attack going on (the drawn one when there is none) */
	const FRDWeaponDef* AttackWeapon() const;
	USkeletalMeshComponent* Body() const;
	void Strike();
	void EndAttack();
	void SetSlowed(bool bSlow);
	// ---- spells
	struct FBolt
	{
		FVector At = FVector::ZeroVector, Vel = FVector::ZeroVector;
		TWeakObjectPtr<ARDMonster> Target;
		TWeakObjectPtr<UFXSystemComponent> Fx, Core;
		TWeakObjectPtr<UPointLightComponent> Light;
		TWeakObjectPtr<UStaticMeshComponent> Mesh;
		float Flown = 0.f;
		int32 Weapon = 0;
		// level 5: a spell's bolt (its spell, its damage when not its weapon's), the monsters it passed through or jumped
		// from, jumps left; one that flies to a point (a meteor) or back to her (a drain's wisp: no hurt)
		int32 Spell = -1;
		float Dmg = -1.f;
		int32 ChainLeft = 0;
		bool bPierce = false, bGoal = false, bWisp = false;
		FVector Goal = FVector::ZeroVector;
		TArray<TWeakObjectPtr<ARDMonster>> Done;
	};
	void LaunchSpellBolt(int32 Spell, const FVector& From, ARDMonster* Target, float Dmg, int32 ChainLeft, const TArray<TWeakObjectPtr<ARDMonster>>& Done);
	void LaunchGoalBolt(int32 Spell, const FVector& From, const FVector& To, float Speed, bool bWisp);
	TArray<FBolt> Bolts;
	TWeakObjectPtr<ARDMonster> LastTarget;
	UPROPERTY(Transient) TObjectPtr<UFXSystemComponent> ChargeComp;
	/** every effect / light component the spells made (kept from the garbage collector; finished ones are dropped) */
	UPROPERTY(Transient) TArray<TObjectPtr<USceneComponent>> SpellComps;
	struct FFlash { TWeakObjectPtr<UPointLightComponent> Light; float Age = 0.f; float Peak = 0.f; };
	TArray<FFlash> Flashes;
	/** effects to stop after a while (the burst's flames) */
	struct FTimedFx { TWeakObjectPtr<UFXSystemComponent> Fx; float Left = 0.f; bool bKill = false; };   // (bKill: gone at once at the end, not left to die away)
	TArray<FTimedFx> TimedFx;
	/** bolts stuck where they struck, and how long they stay */
	struct FStuck { TWeakObjectPtr<UStaticMeshComponent> Mesh; float Left = 0.f; };
	TArray<FStuck> Stuck;
	void PlaceBoltMesh(UStaticMeshComponent* C, const FRDWeaponDef& W, const FVector& At, const FVector& Dir) const;
	UFXSystemComponent* SpawnFx(UFXSystemAsset* Asset, const FVector& At, const FRotator& Rot, float Scale, USceneComponent* AttachTo = nullptr, FName Socket = NAME_None);
	UPointLightComponent* MakeLight(const FVector& At, const FLinearColor& Color, float Intensity, float Radius);
	ARDMonster* PickTarget(float Reach, bool bNeedSight) const;
	bool CanSee(const FVector& From, const AActor* Target) const;
	void LaunchBolt();
	void TickBolts(float Dt);
	void Burst(FBolt& B, const FVector& At, ARDMonster* Direct);
	/** level 5: a spell's bolt bursts (or a meteor lands): its hurt, slow, burn, explosion, its next jump */
	void SpellBurst(FBolt& B, const FVector& At, ARDMonster* Direct);
	/** level 5: a piercing bolt passes through a monster: it is hurt, the bolt flies on */
	void SpellPierce(FBolt& B, ARDMonster* Mo, const FVector& At);
	void StopCharge();
};
