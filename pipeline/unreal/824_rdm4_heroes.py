"""random_dungeonmagic_level4: the Blueprints of the hero choice.
- BP_RDM4_WarriorCharacter: the Warrior (jrpg-fem5-tripo) for the magic levels' controls: a child of BP_SFC_Fem5Character
  (her 36 cm capsule, as in random_dungeoncombat_level). 819 gives her RunMode and the walk / run MoveScale as it gives
  the other three: run 819 after this.
- BP_RDM4_GameMode: a child of the C++ ARDHeroGameMode (the pawn is the hero of ?Hero=, else the generator's DefaultHero)
  with the third-person player controller and the dungeon HUD; the Warrior as the pawn when no hero is found.
The Mage, the Warlock and the Rogue are the magic levels' own characters (810, 817, 822). The menu level's game mode is
the C++ ARDHeroSelectGameMode itself (826). Idempotent. Args: none"""
import unreal
eal = unreal.EditorAssetLibrary; at = unreal.AssetToolsHelpers.get_asset_tools(); BEL = unreal.BlueprintEditorLibrary
G = "/Game/RandomDungeon/Blueprints"
WAR, GM = f"{G}/BP_RDM4_WarriorCharacter", f"{G}/BP_RDM4_GameMode"
PARENT = unreal.load_asset("/Game/SFCityLevel/Blueprints/BP_SFC_Fem5Character").generated_class()
if not eal.does_asset_exist(WAR):
    f = unreal.BlueprintFactory(); f.set_editor_property("parent_class", PARENT)
    at.create_asset("BP_RDM4_WarriorCharacter", G, unreal.Blueprint, f)
war = unreal.load_asset(WAR)
if BEL.get_blueprint_parent_class(war) != PARENT: BEL.reparent_blueprint(war, PARENT); print("RDM4 reparented", war.get_name())
BEL.compile_blueprint(war); eal.save_loaded_asset(war, only_if_is_dirty=False)
if not eal.does_asset_exist(GM):
    f = unreal.BlueprintFactory(); f.set_editor_property("parent_class", unreal.RDHeroGameMode)
    at.create_asset("BP_RDM4_GameMode", G, unreal.Blueprint, f)
gm = unreal.load_asset(GM)
if BEL.get_blueprint_parent_class(gm) != unreal.RDHeroGameMode.static_class(): BEL.reparent_blueprint(gm, unreal.RDHeroGameMode.static_class())
BEL.compile_blueprint(gm)
cdo = unreal.get_default_object(gm.generated_class())
cdo.set_editor_property("player_controller_class", unreal.load_asset("/Game/ThirdPerson/Blueprints/BP_ThirdPersonPlayerController").generated_class())
cdo.set_editor_property("hud_class", unreal.RDHUD.static_class())
cdo.set_editor_property("default_pawn_class", war.generated_class())
eal.save_loaded_asset(gm, only_if_is_dirty=False)
cdo = unreal.get_default_object(unreal.load_asset(GM).generated_class())
print("RDM4 heroes:", WAR, "parent", BEL.get_blueprint_parent_class(war).get_name(), "|", GM, "parent", BEL.get_blueprint_parent_class(gm).get_name(),
      "controller", cdo.get_editor_property("player_controller_class").get_name(), "hud", cdo.get_editor_property("hud_class").get_name(),
      "fallback pawn", cdo.get_editor_property("default_pawn_class").get_name())
import gc
for _n in [n for n in list(globals()) if not n.startswith("__") and n not in ("unreal", "gc")]: del globals()[_n]
gc.collect()
