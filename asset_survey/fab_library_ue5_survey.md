# Fab library: what works in UE5, and which animations drive which models

Source: `I:\game assets\3d epicgames media packs\VaultCache\FabLibrary`. Unity packages were read in place (no extraction).
**UE5-usable:** FBX (skeletal meshes, static meshes, animations) and textures (TGA/PNG/PSD/JPG). **Unity-only:** .mat/.prefab/.controller/.anim/.unity - materials must be rebuilt in UE5; Unity .anim clips need conversion.

## Packs at a glance

| Pack | Skinned models | Static meshes | FBX anim clips | Unity-only .anim | Textures | Rig(s) |
|---|---|---|---|---|---|---|
| 10 Creatures Pack | 10 | 0 | 0 | 0 | 41 | UE Mannequin-style |
| 14 Orcs Pack | 34 | 30 | 92 | 0 | 182 | UE Mannequin-style, Weapon/prop rig |
| Adventure Characters Pack | 10 | 8 | 0 | 0 | 82 | UE Mannequin-style, Weapon/prop rig |
| Aliens Warrior Pack | 16 | 4 | 52 | 0 | 87 | UE Mannequin-style, Weapon/prop rig |
| Animals Warrior Pack | 5 | 5 | 92 | 0 | 88 | UE Mannequin-style |
| Astronauts Pack | 6 | 0 | 9 | 0 | 70 | UE Mannequin-style, Weapon/prop rig |
| Baby In Capsule | 8 | 0 | 1 | 1 | 15 | 3ds Max CAT (humanoid) |
| Cartoon Zombies Pack | 11 | 25 | 85 | 0 | 46 | 3ds Max CAT (creature), 3ds Max CAT (humanoid), UE Mannequin-style |
| Creatures Insects Pack | 5 | 0 | 86 | 0 | 24 | UE Mannequin-style |
| Creatures Mega Pack | 33 | 0 | 184 | 0 | 89 | 3ds Max CAT (creature), Custom, Maya AdvancedSkeleton |
| Creeping Creatures Pack | 11 | 0 | 34 | 0 | 32 | Arms-only (FPS), Custom, UE Mannequin-style, Weapon/prop rig |
| Customized Post Apocalyptic Characters | 2 | 12 | 1 | 0 | 110 | Humanoid (Mixamo-style names), Mixamo, UE Mannequin-style |
| Cyber Characters Pack | 4 | 4 | 0 | 0 | 58 | UE Mannequin-style |
| Dwarfs Pack | 6 | 21 | 94 | 0 | 116 | UE Mannequin-style, Weapon/prop rig |
| Dystopia Soldiers Pack | 12 | 7 | 137 | 0 | 148 | Custom, UE Mannequin-style, Weapon/prop rig |
| Fantasy Animal Pack | 10 | 14 | 125 | 0 | 44 | 3ds Max CAT (creature), UE Mannequin-style, Weapon/prop rig |
| Fantasy Enemies Pack | 10 | 14 | 0 | 0 | 50 | UE Mannequin-style, Weapon/prop rig |
| Fantasy Warriors Pack | 5 | 6 | 0 | 0 | 49 | UE Mannequin-style |
| Female Soldiers Pack | scan error: unexpected end of data | | | | | |
| Fighters Pack | 15 | 0 | 0 | 0 | 81 | UE Mannequin-style |
| FPS ANIMATIONS PISTOL TACTICAL SHIELD | 5 | 1 | 50 | 0 | 44 | UE Mannequin-style, Weapon/prop rig |
| FPS Automatic Rifle 01 Animations | 6 | 12 | 57 | 0 | 43 | UE Mannequin-style, Weapon/prop rig |
| FPS Automatic Rifle 02 Animations | 4 | 1 | 55 | 0 | 19 | UE Mannequin-style, Weapon/prop rig |
| FPS Automatic-Shotgun Animations | 4 | 1 | 62 | 0 | 18 | UE Mannequin-style, Weapon/prop rig |
| FPS Devices | 2 | 4 | 33 | 0 | 41 | UE Mannequin-style, Weapon/prop rig |
| FPS Pistol And Knife Animations | 4 | 2 | 61 | 0 | 43 | UE Mannequin-style, Weapon/prop rig |
| FPS Pistol Single | 4 | 1 | 64 | 0 | 39 | UE Mannequin-style, Weapon/prop rig |
| FPS Rocket Launcher Animations | 4 | 0 | 46 | 0 | 13 | UE Mannequin-style, Weapon/prop rig |
| FPS Sci-Fi Hands Empty | 2 | 0 | 56 | 0 | 24 | UE Mannequin-style, Weapon/prop rig |
| FPS Sniper Rifle 03 Animations | 4 | 1 | 50 | 0 | 22 | UE Mannequin-style, Weapon/prop rig |
| FPS Sniper Rifle Large Calibre Animations | 4 | 1 | 46 | 0 | 16 | UE Mannequin-style, Weapon/prop rig |
| FPS STARTER PACK | 56 | 23 | 57 | 0 | 337 | 3ds Max CAT (creature), UE Mannequin-style, Weapon/prop rig |
| Geek Room | 1 | 69 | 1 | 0 | 51 | UE Mannequin-style |
| Humanoids Creatures Pack | 5 | 0 | 41 | 0 | 29 | UE Mannequin-style |
| Humanoids Monsters Pack | 5 | 0 | 45 | 0 | 20 | UE Mannequin-style |
| Knights Pack | 6 | 12 | 0 | 0 | 164 | UE Mannequin-style, Weapon/prop rig |
| Military Drones | 6 | 1 | 30 | 0 | 24 | UE Mannequin-style, Weapon/prop rig |
| Military Pack | 15 | 44 | 36 | 0 | 345 | 3ds Max CAT (creature), 3ds Max CAT (humanoid), Custom, UE Mannequin-style, Weapon/prop rig |
| Monster In Capsule | 2 | 8 | 7 | 0 | 31 | UE Mannequin-style |
| Monsters Underwater Pack | 5 | 0 | 41 | 0 | 25 | UE Mannequin-style |
| NPC Beggars Pack | 8 | 23 | 19 | 0 | 128 | UE Mannequin-style |
| NPC Characters Female Pack | 5 | 0 | 0 | 0 | 87 | UE Mannequin-style |
| NPC Characters Male Pack | 3 | 2 | 0 | 0 | 39 | UE Mannequin-style |
| NPC Charaters Kids Pack | 5 | 0 | 0 | 0 | 126 | UE Mannequin-style |
| NPC Dystopia Characters | 1 | 0 | 0 | 0 | 29 | UE Mannequin-style |
| NPC King And Queen | 5 | 2 | 0 | 0 | 71 | UE Mannequin-style |
| NPC Prisoners | 2 | 0 | 0 | 0 | 32 | UE Mannequin-style |
| NPC Sailor Adventure | 8 | 1 | 0 | 0 | 41 | UE Mannequin-style, Weapon/prop rig |
| Old Gangster | 1 | 2 | 1 | 0 | 28 | UE Mannequin-style |
| Parasites Pack | 5 | 1 | 65 | 0 | 20 | 3ds Max CAT (humanoid) |
| Primitive Characters Pack | 4 | 11 | 0 | 0 | 78 | UE Mannequin-style |
| Sci-Fi Characters Pack | 6 | 3 | 0 | 0 | 74 | UE Mannequin-style, Weapon/prop rig |
| Sci-Fi Characters Pack Vol 2 | 8 | 5 | 79 | 0 | 127 | UE Mannequin-style, Weapon/prop rig |
| Sci-FI Creocapsule | 3 | 1 | 2 | 0 | 39 | Weapon/prop rig |
| Sci-Fi Experimental | 0 | 1 | 2 | 0 | 19 | Arms-only (FPS), Weapon/prop rig |
| Sci-Fi Hands With Knife Animation | 2 | 1 | 34 | 0 | 30 | UE Mannequin-style, Weapon/prop rig |
| Sci-Fi Line With 3 Creatures | 4 | 4 | 2 | 0 | 28 | UE Mannequin-style, Weapon/prop rig |
| Sci-Fi Mercenaries Pack | 18 | 12 | 0 | 0 | 76 | UE Mannequin-style, Weapon/prop rig |
| Soldier Future 01 | 3 | 0 | 0 | 0 | 45 | UE Mannequin-style, Weapon/prop rig |
| Soldier Future 02 | 4 | 0 | 0 | 0 | 57 | UE Mannequin-style, Weapon/prop rig |
| Soldier Future 03 | 3 | 0 | 0 | 0 | 38 | UE Mannequin-style, Weapon/prop rig |
| Tactical Masks | 10 | 1 | 0 | 0 | 13 | UE Mannequin-style |
| Underwater odyssey | 17 | 0 | 0 | 0 | 54 | 3ds Max Biped, UE Mannequin-style |
| Viking Customized | 21 | 17 | 0 | 0 | 202 | UE Mannequin-style, Weapon/prop rig |

## Per pack: models, and which animations drive them

An animation set **plays on** a model when at least 90% of its animated bones exist in that model's skeleton (import the clips onto that model's skeleton in UE5). `UE Mannequin-style` models without their own clips can use any UE5 mannequin animation through the IK Retargeter (auto chain mapping).

### 10 Creatures Pack
- **UE Mannequin-style** models (10; auto-retargets with UE5 mannequin animations): Creature_01, Creature_02, Creature_03, Creature_04, Creature_05, Creature_06, Creature_07, Creature_08, Creature_09, Creature_10
- No clips of their own: Creature_01, Creature_02, Creature_03, Creature_04, Creature_05, Creature_06, Creature_07, Creature_08, Creature_09, Creature_10

### 14 Orcs Pack
- **UE Mannequin-style** models (31; auto-retargets with UE5 mannequin animations): All_animations_on_one_timeline, Azrak_Mesh, Costalmed_Mesh, Dardan_Mesh, Gnur_Mesh, Kanit_Mesh, Magur_Mesh, Orc_01_Mesh, Orc_02_Mesh, Orc_03_Mesh, Orc_04_Mesh, Orc_05_Mesh, Orc_06_Mesh, Orc_Girra_Mesh, Orc_Kani@Attack(1), Orc_Kani@Attack(2), Orc_Kani@Attack(3), Orc_Kani@Attack(4), Orc_Kani@Dead, Orc_Kani@Dead_L, Orc_Kani@Dead_R, Orc_Kani@Get_Hit, Orc_Kani@Idle, Orc_Kani@Idle_Other, Orc_Kani@Jump, Orc_Kani@Run, Orc_Kani@Shout, Orc_Kani@Walk, Orc_Ursag_Mesh, Skeleton_Mesh, Sufferer_Mesh
- **Weapon/prop rig** models (3; own animations only): Cell_Mesh, Orc_03_Weapon, Orc_04_Weapon_Mesh
- **66 clips** (UE Mannequin-style, 61 bones) -> plays on: Azrak_Mesh, Costalmed_Mesh, Dardan_Mesh, Magur_Mesh, Orc_01_Mesh, Orc_02_Mesh, Orc_03_Mesh, Orc_04_Mesh, Orc_05_Mesh, Orc_06_Mesh, Orc_Girra_Mesh, Skeleton_Mesh, Sufferer_Mesh; also fits models in: Fantasy Animal Pack (1)
  - Attack_1, Attack_2, Attack_3, Attack_4, Attack_5, Attack_6, Attack_7, Attack_8, Dead_1, Dead_1_Without_Weapon, Dead_2, Dead_2_Without_Weapon, Dead_3, Dead_4, Dead_Left_Without_Weapon, Dead_Right_Without_Weapon, Get_Hit_1, Get_Hit_1_Without_Weapon, Get_Hit_2, Get_Hit_2_Without_Weapon, Idle, Idle_2_Without_Weapon, Idle_3_Without_Weapon, Idle_Othe, Idle_Other_02, Idle_Sit, Idle_Sit_Without_Weapon, Idle_Swim, Idle_Without_Weapon, Jump, Jump_Without_Weapon, Run, Run_Back, Run_Back_Without_Weapon, Run_Left, Run_Left_Without_Weapon, Run_Right, Run_Right_Without_Weapon, Run_Without_Weapon, Shout, Shout_Without_Weapon, Swim, Take_Weapon, Turn_Right, Turn_Right_Sit, Turn_Right_Sit_Without_Weapon, Turn_Right_Without_Weapon, Turn_left, Turn_left_Sit, Turn_left_Sit_Without_Weapon, Turn_left_Without_Weapon, Walk_Back, Walk_Back_Sit, Walk_Back_Sit_Without_Weapon, Walk_Back_Without_Weapon, Walk_Left, Walk_Left_Sit, Walk_Left_Sit_Without_Weapon, Walk_Left_Without_Weapon, Walk_Right, Walk_Right_Sit_Without_Weapon, Walk_Right_Without_Weapon, Walk_Sit, Walk_Sit_Right, Walk_Sit_Without_Weapon, Walk_Without_Weapon
- **26 clips** (UE Mannequin-style, 60 bones) -> plays on: Azrak_Mesh, Costalmed_Mesh, Dardan_Mesh, Kanit_Mesh, Magur_Mesh, Orc_01_Mesh, Orc_02_Mesh, Orc_03_Mesh, Orc_04_Mesh, Orc_05_Mesh, Orc_06_Mesh, Orc_Girra_Mesh, Orc_Ursag_Mesh, Skeleton_Mesh, Sufferer_Mesh; also fits models in: Fantasy Animal Pack (1)
  - Run_Back_Root, Run_Back_Without_Weapon_Root, Run_Left_Root, Run_Left_Without_Weapon_Root, Run_Right_Root, Run_Right_Without_Weapon_Root, Run_Root, Run_Without_Weapon_Root, Swim_Root, Walk, Walk_Back_Root, Walk_Back_Sit_Root, Walk_Back_Sit_Without_Weapon_Root, Walk_Back_Without_Weapon_Root, Walk_Left_Root, Walk_Left_Sit_Root, Walk_Left_Sit_Without_Weapon_Root, Walk_Left_Without_Weapon_Root, Walk_Right_Root, Walk_Right_Sit_Without_Weapon_Root, Walk_Right_Without_Weapon_Root, Walk_Root, Walk_Sit_Right_Root, Walk_Sit_Root, Walk_Sit_Without_Weapon_Root, Walk_Without_Weapon_Root
- No clips of their own: All_animations_on_one_timeline, Cell_Mesh, Gnur_Mesh, Orc_03_Weapon, Orc_04_Weapon_Mesh, Orc_Kani@Attack(1), Orc_Kani@Attack(2), Orc_Kani@Attack(3), Orc_Kani@Attack(4), Orc_Kani@Dead, Orc_Kani@Dead_L, Orc_Kani@Dead_R, Orc_Kani@Get_Hit, Orc_Kani@Idle, Orc_Kani@Idle_Other, Orc_Kani@Jump, Orc_Kani@Run, Orc_Kani@Shout, Orc_Kani@Walk
- Static meshes (30): Azrak_Weapon_Mesh, Bone_mesh01, Bone_mesh02, Bone_mesh03, Bone_mesh04, Bone_mesh05, Bone_mesh06, Bone_mesh07, Bone_mesh08, Bone_mesh09, Bone_mesh10, Costalmed_Weapon_Mesh, Dardan_Weapon_Mesh, Gnur_Weapon_Mesh, Kanit_Weaopn_Mesh, Magur_Weapon_Mesh, Mesh, Mesh_01, Mesh_02, Mesh_03, Mesh_Head, Orc_01_Weapon_Mesh, Orc_03_Weapon_2, Orc_05_Weapon_Mesh, Orc_06_Weapon_01_Mesh, Orc_06_Weapon_02_Mesh, Orc_Girra_Weapon_Mesh, Orc_Weapon_Mesh, Weapon_Mesh

### Adventure Characters Pack
- **UE Mannequin-style** models (5; auto-retargets with UE5 mannequin animations): Adventure_01_Mesh, Adventure_02_Mesh, Adventure_03, Adventure_04, Adventure_05
- **Weapon/prop rig** models (5; own animations only): Gun, Sniper_Rifle_Basic, Sniper_Rifle_Cartridge, Sniper_Rifle_Full, Sniper_Rifle_Full_Without_Cartridge
- No clips of their own: Adventure_01_Mesh, Adventure_02_Mesh, Adventure_03, Adventure_04, Adventure_05, Gun, Sniper_Rifle_Basic, Sniper_Rifle_Cartridge, Sniper_Rifle_Full, Sniper_Rifle_Full_Without_Cartridge
- Static meshes (8): Adventure_01_Knife, Adventure_04_Guitar, Bita_Mesh, Club, Knife, Shield, Sniper_Rifle_Bullet, Sniper_Rifle_Sleeve

### Aliens Warrior Pack
- **UE Mannequin-style** models (5; auto-retargets with UE5 mannequin animations): Alien_Warrior_01, Alien_Warrior_02, Alien_Warrior_03, Alien_Warrior_04, Alien_Warrior_05
- **Weapon/prop rig** models (11; own animations only): SK_Alien_Weapon_04_Full_01, SK_Alien_Weapon_04_Full_02, SK_Alien_Weapon_04_One_L_01, SK_Alien_Weapon_04_One_L_02, SK_Alien_Weapon_04_One_R_01, SK_Alien_Weapon_04_One_R_02, SK_Alien_Weapon_04_Without_Weapon_01, SK_Alien_Weapon_04_Without_Weapon_02, SK_Sci_Fi_Automatic_Sniper_Rifle_Basic, SK_Sci_Fi_Automatic_Sniper_Rifle_Cartridge, SK_Sci_Fi_Automatic_Sniper_Rifle_Full
- **9 clips** (Weapon/prop rig, 14 bones) -> plays on: SK_Alien_Weapon_04_Full_01, SK_Alien_Weapon_04_Full_02, SK_Alien_Weapon_04_One_L_01, SK_Alien_Weapon_04_One_L_02, SK_Alien_Weapon_04_One_R_01, SK_Alien_Weapon_04_One_R_02, SK_Alien_Weapon_04_Without_Weapon_01, SK_Alien_Weapon_04_Without_Weapon_02
  - , _45_45_Down_L, _45_45_Down_R, _45_45_Up_L, _45_45_Up_R, _45_Down, _45_L, _45_R, _45_Up
- **43 clips** (UE Mannequin-style, 60 bones) -> plays on: Alien_Warrior_01, Alien_Warrior_02, Alien_Warrior_03, Alien_Warrior_04, Alien_Warrior_05; also fits models in: Fantasy Animal Pack (1)
  - Attack_01, Attack_02, Attack_03, Attack_04, Attack_05, Dead_01, Dead_02, Get_Hit, Get_Hit_02, Idle_01, Idle_02, Idle_03, Jump, Reload, Rotate_90_45_Down_Left, Rotate_90_45_Down_Right, Rotate_90_45_Up_Left, Rotate_90_45_Up_Right, Rotate_90_Down, Rotate_90_Left, Rotate_90_Right, Rotate_90_Up, Run, Run_Back, Run_Back_Root, Run_Fast, Run_Fast_Root, Run_Left, Run_Left_Root, Run_Right, Run_Right_Root, Run_Root, Shot_01, Shot_02, Shot_03, Walk, Walk_Back, Walk_Back_Root, Walk_Left, Walk_Left_Root, Walk_Right, Walk_Right_Root, Walk_Root
- No clips of their own: SK_Sci_Fi_Automatic_Sniper_Rifle_Basic, SK_Sci_Fi_Automatic_Sniper_Rifle_Cartridge, SK_Sci_Fi_Automatic_Sniper_Rifle_Full
- Static meshes (4): Alien_Warrior_02_Mace, Alien_Warrior_05_Weapon, Alien_Weapon_01, SM_Sci_Fi_Automatic_Sniper_Rifle_Sleeve

### Animals Warrior Pack
- **UE Mannequin-style** models (5; auto-retargets with UE5 mannequin animations): Bear_Warrior_Mesh, Bull_Mesh, Elephant_Mesh, Warrior_02_Mesh, Warrior_Crocodile_Mesh
- **67 clips** (UE Mannequin-style, 61 bones) -> plays on: Bear_Warrior_Mesh, Bull_Mesh, Warrior_02_Mesh, Warrior_Crocodile_Mesh; also fits models in: Fantasy Animal Pack (1)
  - Attack_1, Attack_2, Attack_3, Attack_4, Attack_5, Attack_6, Attack_7, Attack_8, Dead_1, Dead_1_Without_Weapon, Dead_2, Dead_2_Without_Weapon, Dead_3, Dead_4, Dead_Left_Without_Weapon, Dead_Right_Without_Weapon, Get_Hit_1, Get_Hit_1_Without_Weapon, Get_Hit_2, Get_Hit_2_Without_Weapon, Idle, Idle_2_Without_Weapon, Idle_3_Without_Weapon, Idle_Othe, Idle_Other_02, Idle_Sit, Idle_Sit_Without_Weapon, Idle_Swim, Idle_Without_Weapon, Jump, Jump_Without_Weapon, Run, Run_Back, Run_Back_Without_Weapon, Run_Left, Run_Left_Without_Weapon, Run_Right, Run_Right_Without_Weapon, Run_Without_Weapon, Shout, Shout_Without_Weapon, Swim, Take_Weapon, Turn_Right, Turn_Right_Sit, Turn_Right_Sit_Without_Weapon, Turn_Right_Without_Weapon, Turn_left, Turn_left_Sit, Turn_left_Sit_Without_Weapon, Turn_left_Without_Weapon, Walk, Walk_Back, Walk_Back_Sit, Walk_Back_Sit_Without_Weapon, Walk_Back_Without_Weapon, Walk_Left, Walk_Left_Sit, Walk_Left_Sit_Without_Weapon, Walk_Left_Without_Weapon, Walk_Right, Walk_Right_Sit_Without_Weapon, Walk_Right_Without_Weapon, Walk_Sit, Walk_Sit_Right, Walk_Sit_Without_Weapon, Walk_Without_Weapon
- **25 clips** (UE Mannequin-style, 60 bones) -> plays on: Bear_Warrior_Mesh, Bull_Mesh, Elephant_Mesh, Warrior_02_Mesh, Warrior_Crocodile_Mesh; also fits models in: Fantasy Animal Pack (1)
  - Run_Back_Root, Run_Back_Without_Weapon_Root, Run_Left_Root, Run_Left_Without_Weapon_Root, Run_Right_Root, Run_Right_Without_Weapon_Root, Run_Root, Run_Without_Weapon_Root, Swim_Root, Walk_Back_Root, Walk_Back_Sit_Root, Walk_Back_Sit_Without_Weapon_Root, Walk_Back_Without_Weapon_Root, Walk_Left_Root, Walk_Left_Sit_Root, Walk_Left_Sit_Without_Weapon_Root, Walk_Left_Without_Weapon_Root, Walk_Right_Root, Walk_Right_Sit_Without_Weapon_Root, Walk_Right_Without_Weapon_Root, Walk_Root, Walk_Sit_Right_Root, Walk_Sit_Root, Walk_Sit_Without_Weapon_Root, Walk_Without_Weapon_Root
- Static meshes (5): Bear_Warrior_Weapon_Mesh, Bull_Weapon_Mesh, Sword_Mesh, Warrior_Crocodile_Weapon_Mesh, Weapon_Mesh

### Astronauts Pack
- **UE Mannequin-style** models (5; auto-retargets with UE5 mannequin animations): Astronaut_Mesh, Astronaut_Pilot_Mesh, Astronaut_Soldier_Mesh, Man_Mesh, Woman_Mesh
- **Weapon/prop rig** models (1; own animations only): Astronaut_Soldier_Weapon_Mesh
- **3 clips** (UE Mannequin-style, 55 bones) -> plays on: Astronaut_Mesh, Astronaut_Pilot_Mesh, Astronaut_Soldier_Mesh, Man_Mesh, Woman_Mesh; also fits models in: 10 Creatures Pack (10), 14 Orcs Pack (15), Adventure Characters Pack (5), Aliens Warrior Pack (5), Animals Warrior Pack (5), Cartoon Zombies Pack (1), Creatures Insects Pack (5), Creeping Creatures Pack (5), Customized Post Apocalyptic Characters (1), Cyber Characters Pack (4), Dwarfs Pack (5), Dystopia Soldiers Pack (7), FPS Pistol And Knife Animations (1), Fantasy Animal Pack (1), Fantasy Enemies Pack (7), Fantasy Warriors Pack (5), Fighters Pack (13), Geek Room (1), Humanoids Creatures Pack (4), Humanoids Monsters Pack (5), Knights Pack (5), Military Pack (9), Monster In Capsule (2), Monsters Underwater Pack (5), NPC Beggars Pack (7), NPC Characters Female Pack (5), NPC Characters Male Pack (3), NPC Charaters Kids Pack (5), NPC Dystopia Characters (1), NPC King And Queen (5), NPC Prisoners (2), NPC Sailor Adventure (7), Old Gangster (1), Primitive Characters Pack (4), Sci-Fi Characters Pack (5), Sci-Fi Characters Pack Vol 2 (7), Sci-Fi Line With 3 Creatures (1), Sci-Fi Mercenaries Pack (13), Soldier Future 01 (1), Soldier Future 02 (1), Soldier Future 03 (1), Tactical Masks (10), Viking Customized (18)
  - Fly_01, Fly_02, Idle
- **6 clips** (Weapon/prop rig, 10 bones) -> plays on: Astronaut_Soldier_Weapon_Mesh
  - Close, Open, Rotation_45_Left, Rotation_45_Right, Rotation_90_Down, Rotation_90_Up

### Baby In Capsule
- **3ds Max CAT (humanoid)** models (8; retarget via manual IK-rig chains): Baby, Baby_In_Capsule_Full, Capsule, Capsule_Witout_Wiares, Capsule_Witout_Wiares_And_Glass, Glass, Mask, Wiares
- **1 clips** (3ds Max CAT (humanoid), 59 bones) -> plays on: Baby, Baby_In_Capsule_Full, Capsule, Capsule_Witout_Wiares, Capsule_Witout_Wiares_And_Glass, Glass, Mask, Wiares
  - 
- Unity-only .anim clips (1): Animation

### Cartoon Zombies Pack
- **3ds Max CAT (creature)** models (4; own animations only): Gunner_Mesh, Rat_Mesh, Thak_Mesh, Сhicken_Mesh
- **3ds Max CAT (humanoid)** models (6; retarget via manual IK-rig chains): Drinker_Mesh, Fat_Zombie_Mesh, Mask_Mesh, Medic_Mesh, Monster_Mesh, Soldier_Mesh
- **UE Mannequin-style** models (1; auto-retargets with UE5 mannequin animations): Boy_Mesh
- **11 clips** (3ds Max CAT (humanoid), 39 bones) -> plays on: Drinker_Mesh, Fat_Zombie_Mesh, Mask_Mesh, Medic_Mesh, Monster_Mesh, Soldier_Mesh
  - Attack_1, Attack_2, Attack_Boom, Dead, Get_Hit, Idle, Jump, Walk, Walk_Fast, Walk_Fast_Z, Walk_Z
- **6 clips** (3ds Max CAT (creature), 13 bones) -> plays on: Thak_Mesh
  - Attack, Dead, Get_Hit, Idle, Move, Move_Z
- **10 clips** (3ds Max CAT (creature), 22 bones) -> plays on: Drinker_Mesh, Fat_Zombie_Mesh, Gunner_Mesh, Medic_Mesh, Monster_Mesh, Soldier_Mesh
  - Attack_1, Attack_2, Dead, Get_Hit, Idle, Jump, Run, Run_Z, Walk, Walk_Z
- **10 clips** (3ds Max CAT (humanoid), 47 bones) -> plays on: Medic_Mesh, Monster_Mesh; also fits models in: Baby In Capsule (8), Parasites Pack (1)
  - Attack_1, Attack_2, Dead, Get_Hit, Idle, Jump, Run, Run_Z, Walk, Walk_Z
- **6 clips** (3ds Max CAT (creature), 28 bones) -> plays on: Rat_Mesh
  - Attack, Dead, Get_Hit, Idle, Walk, Walk_Z
- **11 clips** (3ds Max CAT (humanoid), 40 bones) -> plays on: Drinker_Mesh, Fat_Zombie_Mesh, Mask_Mesh, Medic_Mesh, Monster_Mesh, Soldier_Mesh; also fits models in: Baby In Capsule (8), Parasites Pack (1)
  - Attack_1, Attack_2, Dead, Get_Hit, Idle, Jump, Run, Run_Z, Shout, Walk, Walk_Z
- **10 clips** (3ds Max CAT (creature), 20 bones) -> plays on: Сhicken_Mesh
  - Attack_1, Dead, Get_Hit, Idle, Jump, Run, Run_Z, Shout, Walk, Walk_Z
- **10 clips** (3ds Max CAT (humanoid), 38 bones) -> plays on: Drinker_Mesh, Fat_Zombie_Mesh, Mask_Mesh, Medic_Mesh, Monster_Mesh, Soldier_Mesh
  - Attack_1, Attack_2, Dead, Get_Hit, Idle, Jump, Run, Run_Z, Walk, Walk_Z
- **11 clips** (3ds Max CAT (humanoid), 48 bones) -> plays on: Medic_Mesh, Monster_Mesh; also fits models in: Baby In Capsule (8), Parasites Pack (1)
  - Attack_1, Attack_2, Dead, Get_Hit, Idle, Jump, Run, Run_Z, Shout, Walk, Walk_Z
- No clips of their own: Boy_Mesh
- Static meshes (25): Barrel_Mesh, Block_Mesh, Box_2_Mesh, Box_Mesh, Building_1_Mesh, Building_2_Mesh, Building_3_Mesh, Building_4_Mesh, Cone_Mesh, Donut_Mesh, Fence_2_Mesh, Fence_Mesh, Flower_Mesh, Garbage_Mesh, Grass_Mesh, Ground_Mesh, Hydrant_Mesh, Pillar_Mesh, Sign_Mesh, Stand_Mesh, Tire_Mesh, Tower_Mesh, Tree_Mesh, Wires_Mesh, Woods_Mesh

### Creatures Insects Pack
- **UE Mannequin-style** models (5; auto-retargets with UE5 mannequin animations): Creature_Insect_01_Mesh, Creature_Insect_02_Mesh, Creature_Insect_03_Mesh, Creature_Insect_04_Mesh, Creature_Insect_05_Mesh
- **55 clips** (UE Mannequin-style, 61 bones) -> plays on: Creature_Insect_01_Mesh, Creature_Insect_02_Mesh, Creature_Insect_03_Mesh, Creature_Insect_04_Mesh, Creature_Insect_05_Mesh; also fits models in: Fantasy Animal Pack (1)
  - Attack_1, Attack_10, Attack_2, Attack_3, Attack_4, Attack_5, Attack_6, Attack_7, Attack_8, Attack_9, Dead_1, Dead_2, Dead_3, Dead_4, Get_Hit, Get_Hit_Back, Get_Hit_Left, Get_Hit_Right, Idle_1, Idle_2, Jump, Run, Run_Back, Run_Left, Run_Right, Shout_1, Shout_2, Sit_Attack_5, Sit_Attack_6, Sit_Attack_7, Sit_Attack_8, Sit_Attack_From_Ground, Sit_Down_On_Ground_&_Up, Sit_Eat, Sit_Eat_Loop, Sit_Jump_From_The_Ceiling, Sit_Lies_On_The_Ground_Pose, Sit_On_The_Celing_Idle, Sit_Rebound_Bacward, Sit_Rebound_Left, Sit_Rebound_Right, Sit_Rotation_Left, Sit_Rotation_Right, Sit_Sit_Run_02, Sit_Sleep, Sit_Up_&_Shout, Sit_Walk_Back, Sit_Walk_Left, Sit_Walk_Right, Turn_Right, Walk, Walk_Back, Walk_Left, Walk_Right, urn_Left
- **31 clips** (UE Mannequin-style, 60 bones) -> plays on: Creature_Insect_01_Mesh, Creature_Insect_02_Mesh, Creature_Insect_03_Mesh, Creature_Insect_04_Mesh, Creature_Insect_05_Mesh; also fits models in: Fantasy Animal Pack (1)
  - Run_Back_Root, Run_Left_Root, Run_Right_Root, Run_Root, Sit_Attack_1, Sit_Attack_2, Sit_Attack_3, Sit_Attack_4, Sit_Dead_1, Sit_Dead_2, Sit_Dead_3, Sit_Get_Hit_1, Sit_Get_Hit_2, Sit_Idle_1, Sit_Idle_2, Sit_Jump, Sit_Out_Of_ Ground, Sit_Run, Sit_Run_02_Root, Sit_Run_Root, Sit_Shout, Sit_Walk, Sit_Walk_Back_Root, Sit_Walk_Left_Root, Sit_Walk_Right_Root, Sit_Walk_Root, Sit_jump_On_The_Ground, Walk_Back_Root, Walk_Left_Root, Walk_Right_Root, Walk_Root

### Creatures Mega Pack
- **3ds Max CAT (creature)** models (13; own animations only): Cocoon, Cocoon@Idle 01, Mesh, Organic_trap@Attack, Organic_trap@Dead, Organic_trap@Get_hit, Organic_trap@Idle, Poisonous_claw@Attack, Poisonous_claw@Dead, Poisonous_claw@Get_hit, Poisonous_claw@Idle, Poisonous_claw@Idle_oher
- **Custom** models (5; own animations only): Daemon, Fat, Mutant, Rock, Troll
- **Maya AdvancedSkeleton** models (15; retarget via manual IK-rig chains): Alien, Bug, Character_01, Creepy, Creepy@Attack(1), Devourer, Exterminator, Horned, Hunter, Insect, Nasty, Pangolin, Ripper_dog, Spider, Titan
- **10 clips** (Maya AdvancedSkeleton, 62 bones) -> plays on: Devourer
  - Attack(1), Attack(2), Attack(3), Death, GetHit, Idle, Jump, Run, Shout, Walk
- **11 clips** (Maya AdvancedSkeleton, 45 bones) -> plays on: Alien, Character_01, Exterminator, Horned, Titan
  - Attack(1), Attack(2), Attack(3), Death, GetHit, Idle, Jump, Run, Shout, Shout2, Walk
- **7 clips** (Maya AdvancedSkeleton, 37 bones) -> plays on: Insect
  - Attack(1), Attack(2), Attack(3), Death, Flying, GetHit, Idle
- **9 clips** (Maya AdvancedSkeleton, 38 bones) -> plays on: Spider
  - Attack(1), Attack(2), Attack(3), Death, GetHit, Idle, Jump, Shout, Walk
- **10 clips** (Maya AdvancedSkeleton, 56 bones) -> plays on: Alien, Character_01, Exterminator, Horned
  - Attack(1), Attack(2), Attack(3), Death, GetHit, Idle, Jump, Run, Shout, Walk
- **10 clips** (Maya AdvancedSkeleton, 48 bones) -> plays on: Ripper_dog
  - Attack(1), Attack(2), Attack(3), Death, GetHit, Idle, Jump, Run, Shout, Walk
- **10 clips** (Custom, 50 bones) -> plays on: Daemon, Fat, Rock
  - Attack(1), Attack(2), Attack(3), Death, GetHit, Idle, Jump, Run, Shout, Walk
- **10 clips** (Custom, 55 bones) -> plays on: Daemon
  - Attack(1), Attack(2), Attack(3), Death, GetHit, Idle, Jump, Run, Shout, Walk
- **10 clips** (Maya AdvancedSkeleton, 69 bones) -> plays on: Hunter
  - Attack(1), Attack(2), Attack(3), Death, GetHit, Idle, Jump, Run, Shout, Walk
- **11 clips** (Custom, 46 bones) -> plays on: Mutant
  - Attack(1), Attack(2), Attack(2)1, Attack(3), Death, GetHit, Idle, Jump, Run, Shout, Walk
- **8 clips** (Maya AdvancedSkeleton, 67 bones) -> plays on: Creepy
  - Attack(2), Attack(3), Death, GetHit, Idle, Run, Shout, Walk
- **10 clips** (Custom, 55 bones) -> plays on: Rock, Troll
  - Attack(1), Attack(2), Attack(3), Death, GetHit, Idle, Jump, Run, Shout, Walk
- **8 clips** (Maya AdvancedSkeleton, 45 bones) -> plays on: Nasty
  - Attack(1), Attack(2), Attack(3), Death, GetHit, Idle, Shout, Walk
- **10 clips** (Maya AdvancedSkeleton, 44 bones) -> plays on: Alien, Bug, Character_01, Exterminator, Horned
  - Attack(1), Attack(2), Attack(3), Death, GetHit, Idle, Jump, Run, Shout, Walk
- **10 clips** (Maya AdvancedSkeleton, 64 bones) -> plays on: Alien, Exterminator, Horned
  - Attack(1), Attack(2), Attack(3), Death, GetHit, Idle, Jump, Run, Shout, Walk
- **10 clips** (Maya AdvancedSkeleton, 62 bones) -> plays on: Alien, Exterminator, Horned
  - Attack(1), Attack(2), Attack(3), Death, GetHit, Idle, Jump, Run, Shout, Walk
- **10 clips** (Maya AdvancedSkeleton, 72 bones) -> plays on: Exterminator
  - Attack(1), Attack(2), Attack(3), Death, GetHit, Idle, Jump, Run, Shout, Walk
- **10 clips** (Custom, 62 bones) -> plays on: Rock
  - Attack(1), Attack(2), Attack(3), Death, GetHit, Idle, Jump, Run, Shout, Walk
- **10 clips** (Maya AdvancedSkeleton, 49 bones) -> plays on: Pangolin
  - Attack(1), Attack(2), Attack(3), Death, GetHit, Idle, Jump, Run, Shout, Walk
- No clips of their own: Cocoon, Cocoon@Idle 01, Creepy@Attack(1), Mesh, Organic_trap@Attack, Organic_trap@Dead, Organic_trap@Get_hit, Organic_trap@Idle, Poisonous_claw@Attack, Poisonous_claw@Dead, Poisonous_claw@Get_hit, Poisonous_claw@Idle, Poisonous_claw@Idle_oher

### Creeping Creatures Pack
- **Custom** models (1; own animations only): Chein_Mesh
- **UE Mannequin-style** models (5; auto-retargets with UE5 mannequin animations): Creature_01_Mesh, Creature_02_Mesh, Creature_03_Mesh, Creature_04_Mesh, Creature_05_Mesh
- **Weapon/prop rig** models (5; own animations only): Eye_Mesh, Gut_01_Mesh, Gut_02_Mesh, Gut_03_Mesh, Man_In_Gut_Mesh
- **9 clips** (Arms-only (FPS), 47 bones) -> plays on: Creature_01_Mesh, Creature_02_Mesh, Creature_03_Mesh, Creature_04_Mesh, Creature_05_Mesh; also fits models in: 10 Creatures Pack (10), 14 Orcs Pack (15), Adventure Characters Pack (5), Aliens Warrior Pack (5), Animals Warrior Pack (5), Astronauts Pack (5), Cartoon Zombies Pack (1), Creatures Insects Pack (5), Cyber Characters Pack (2), Dwarfs Pack (5), Dystopia Soldiers Pack (6), FPS Pistol And Knife Animations (1), Fantasy Animal Pack (1), Fantasy Enemies Pack (7), Fantasy Warriors Pack (5), Fighters Pack (13), Geek Room (1), Humanoids Creatures Pack (4), Humanoids Monsters Pack (5), Knights Pack (5), Military Pack (7), Monster In Capsule (2), Monsters Underwater Pack (5), NPC Beggars Pack (7), NPC Characters Female Pack (5), NPC Characters Male Pack (3), NPC Charaters Kids Pack (5), NPC Dystopia Characters (1), NPC King And Queen (5), NPC Prisoners (2), NPC Sailor Adventure (7), Old Gangster (1), Primitive Characters Pack (4), Sci-Fi Characters Pack (5), Sci-Fi Characters Pack Vol 2 (7), Sci-Fi Line With 3 Creatures (1), Sci-Fi Mercenaries Pack (13), Soldier Future 01 (1), Soldier Future 02 (1), Soldier Future 03 (1), Tactical Masks (10), Viking Customized (15)
  - Crawl_Out_Of_The_Ground, Dead_01, Eat, Idle_The_Ceiling, Jump_From_The_Ceiling, Walk_Back_Root, Walk_Left_Root, Walk_Right_Root, Walk_Root
- **23 clips** (Arms-only (FPS), 48 bones) -> plays on: Creature_01_Mesh, Creature_02_Mesh, Creature_03_Mesh, Creature_04_Mesh, Creature_05_Mesh; also fits models in: 14 Orcs Pack (13), Animals Warrior Pack (4), Creatures Insects Pack (5), Dwarfs Pack (5), Dystopia Soldiers Pack (2), Fantasy Animal Pack (1), Fighters Pack (7), Humanoids Monsters Pack (5), Monsters Underwater Pack (3), Sci-Fi Characters Pack Vol 2 (1)
  - Attack_01, Attack_02, Attack_03, Attack_04, Attack_05, Attack_06, Dead_02, Dead_03, Eat_Loop, Get_HIt, Get_Left, Get_Right, Idle_01, Idle_02, Idle_03, Jump, Shout, Turn_Left, Turn_Right, Walk, Walk_Back, Walk_Left, Walk_Right
- **2 clips** (Weapon/prop rig, 7 bones) -> plays on: Man_In_Gut_Mesh
  - Anim_Man_In_Bag_Idle, Idle
- No clips of their own: Chein_Mesh, Eye_Mesh, Gut_01_Mesh, Gut_02_Mesh, Gut_03_Mesh

### Customized Post Apocalyptic Characters
- **Mixamo** models (1; auto-retargets (UE5 recognises Mixamo)): Samba Dancing
- **UE Mannequin-style** models (1; auto-retargets with UE5 mannequin animations): Megapost_Character_Fix
- **1 clips** (Humanoid (Mixamo-style names), 75 bones) -> plays on: _no model in this pack shares this skeleton_
  - HumanoidCrouch
- No clips of their own: Megapost_Character_Fix, Samba Dancing
- Static meshes (12): Bita_Mesh, Gun02_Mesh, Gun02_Sleeve_Mesh, Gun_Mesh, Gun_Sleeve_Mesh, Ice_Axe_Mesh, Knife_Mesh, Rifle_Mesh, Rifle_Sleeve_Mesh, Sniper_Rifle_Mesh, Sniper_Rifle_Sleeve_Mesh, Star_Axe

### Cyber Characters Pack
- **UE Mannequin-style** models (4; auto-retargets with UE5 mannequin animations): CyberHucker_Mesh, CyberHunter_Mesh, Cyber_Soldier_Mesh, Prisoner_Mesh
- No clips of their own: CyberHucker_Mesh, CyberHunter_Mesh, Cyber_Soldier_Mesh, Prisoner_Mesh
- Static meshes (4): Automatic_Rifle_Mesh, Automatic_Rifle_Mesh01, Rifle_Sleve_Mesh

### Dwarfs Pack
- **UE Mannequin-style** models (5; auto-retargets with UE5 mannequin animations): Dwaf_Orme_Mesh, Dwarf_Agvid_Mesh, Dwarf_Bedvar_Mesh, Dwarf_Broddi_Mesh, Dwarf_King_Mesh
- **Weapon/prop rig** models (1; own animations only): Crossbow_Mesh
- **67 clips** (UE Mannequin-style, 61 bones) -> plays on: Dwaf_Orme_Mesh, Dwarf_Agvid_Mesh, Dwarf_Bedvar_Mesh, Dwarf_Broddi_Mesh, Dwarf_King_Mesh; also fits models in: Fantasy Animal Pack (1)
  - Attack_1, Attack_2, Attack_3, Attack_4, Attack_5, Attack_6, Attack_7, Attack_8, Dead_1, Dead_1_Without_Weapon, Dead_2, Dead_2_Without_Weapon, Dead_3, Dead_4, Dead_Left_Without_Weapon, Dead_Right_Without_Weapon, Get_Hit_1, Get_Hit_1_Without_Weapon, Get_Hit_2, Get_Hit_2_Without_Weapon, Idle, Idle_2_Without_Weapon, Idle_3_Without_Weapon, Idle_Othe, Idle_Other_02, Idle_Sit, Idle_Sit_Without_Weapon, Idle_Swim, Idle_Without_Weapon, Jump, Jump_Without_Weapon, Run, Run_Back, Run_Back_Without_Weapon, Run_Left, Run_Left_Without_Weapon, Run_Right, Run_Right_Without_Weapon, Run_Without_Weapon, Shout, Shout_Without_Weapon, Swim, Take_Weapon, Turn_Right, Turn_Right_Sit, Turn_Right_Sit_Without_Weapon, Turn_Right_Without_Weapon, Turn_left, Turn_left_Sit, Turn_left_Sit_Without_Weapon, Turn_left_Without_Weapon, Walk, Walk_Back, Walk_Back_Sit, Walk_Back_Sit_Without_Weapon, Walk_Back_Without_Weapon, Walk_Left, Walk_Left_Sit, Walk_Left_Sit_Without_Weapon, Walk_Left_Without_Weapon, Walk_Right, Walk_Right_Sit_Without_Weapon, Walk_Right_Without_Weapon, Walk_Sit, Walk_Sit_Right, Walk_Sit_Without_Weapon, Walk_Without_Weapon
- **27 clips** (UE Mannequin-style, 60 bones) -> plays on: Dwaf_Orme_Mesh, Dwarf_Agvid_Mesh, Dwarf_Bedvar_Mesh, Dwarf_Broddi_Mesh, Dwarf_King_Mesh; also fits models in: Fantasy Animal Pack (1)
  - Run_Back_Root, Run_Back_Without_Weapon_Root, Run_Left_Root, Run_Left_Without_Weapon_Root, Run_Right_Root, Run_Right_Without_Weapon_Root, Run_Root, Run_Without_Weapon_Root, Swim_Root, Sword_Hit, Sword_Idle, Walk_Back_Root, Walk_Back_Sit_Root, Walk_Back_Sit_Without_Weapon_Root, Walk_Back_Without_Weapon_Root, Walk_Left_Root, Walk_Left_Sit_Root, Walk_Left_Sit_Without_Weapon_Root, Walk_Left_Without_Weapon_Root, Walk_Right_Root, Walk_Right_Sit_Without_Weapon_Root, Walk_Right_Without_Weapon_Root, Walk_Root, Walk_Sit_Right_Root, Walk_Sit_Root, Walk_Sit_Without_Weapon_Root, Walk_Without_Weapon_Root
- No clips of their own: Crossbow_Mesh
- Static meshes (21): Arrow_Mesh, Axe_Mesh, Bottle_Mesh, Cup_Mesh, Dwarf_Bedvar_Hammer_Mesh, Forceps_01_Mesh, Forceps_02_Mesh, Forge_Axe_Mesh, Forge_Blade_Mesh, Forge_Forceps_Mesh, Forge_Small_Hummer_Mesh, Forge_Stithy_Mesh, Forge_Stump_Mesh, Forge_Sword_Handle_Mesh, Forgе_Big_Hummer_Mesh, Hammer_Mesh, Hobnail_Mesh, Shield_Mesh, Spear_Mesh, Tools_For_Animations, Trone_Mesh

### Dystopia Soldiers Pack
- **Custom** models (3; own animations only): SK_Tank_Full, SK_Tank_Full_02, SK_Tank_Full_03
- **UE Mannequin-style** models (7; auto-retargets with UE5 mannequin animations): Dystopia_Mech_Mesh, Dystopia_Mutant_soldier, Dystopia_Soldier_02_Mesh, Dystopia_Soldier_Mesh, Dystopian_general, Medic_Dystopia, Pilot_Mesh
- **Weapon/prop rig** models (2; own animations only): Dystopia_Mech_Hoses_Mesh, SK_Dystopia_Airship
- **9 clips** (Weapon/prop rig, 9 bones) -> plays on: SK_Dystopia_Airship
  - _Fly, _Idle, _Landing, _Rotation_90_L, _Rotation_90_R, _Shot_01, _Shot_02, _Shot_03, _Takeoff
- **1 clips** (Weapon/prop rig, 8 bones) -> plays on: SK_Dystopia_Airship
  - _Fly_Root
- **31 clips** (Custom, 6 bones) -> plays on: SK_Tank_Full, SK_Tank_Full_02, SK_Tank_Full_03
  - _Flight_Back, _Flight_Back_Root, _Flight_Forward, _Flight_Forward_Root, _Flight_Left, _Flight_Left_Root, _Flight_Right, _Flight_Right_Root, _Idle, _Landing, _Muzzle_Down, _Muzzle_Up, _Rotation_45_L, _Rotation_45_R, _Rotation_90_L, _Rotation_90_R, _Shot_Mashinegun, _Shot_Muzzle, _Takeoff, _Tower_45_Muzzle_10_L, _Tower_45_Muzzle_10_R, _Tower_45_Muzzle_45_L, _Tower_45_Muzzle_45_R, _Tower_90_Muzzle_10_L, _Tower_90_Muzzle_10_R, _Tower_90_Muzzle_45_L, _Tower_90_Muzzle_45_R, _Tower_Rotation_45_L, _Tower_Rotation_45_R, _Tower_Rotation_90_L, _Tower_Rotation_90_r
- **94 clips** (UE Mannequin-style, 60 bones) -> plays on: Dystopia_Mutant_soldier, Dystopia_Soldier_02_Mesh, Dystopia_Soldier_Mesh, Dystopian_general, Medic_Dystopia, Pilot_Mesh; also fits models in: Fantasy Animal Pack (1)
  - 02_Jump, 02_Reload, 02_Right_Root, 02_Root, 02_Shot, 02_Walk, 02_Walk_Back, 02_Walk_Back_Root, 02_Walk_Left, 02_Walk_Left_Root, 02_Walk_Right, 02_Walk_Right_Root, 02_Walk_Root, Attack_01, Attack_02, Attack_03, Attack_04, Attack_05, Dead_01, Dead_02, Disembarkation, Fly, Fly_Back, Fly_Back_Root, Fly_Dead, Fly_Fast, Fly_Fast_Landing, Fly_Fast_Left, Fly_Fast_Left_Root, Fly_Fast_Right, Fly_Fast_Right_Root, Fly_Fast_Root, Fly_Fast_Start, Fly_Get_Hit, Fly_Get_Hit_Left, Fly_Get_Hit_Right, Fly_Idle, Fly_Landing, Fly_Left, Fly_Left_Root, Fly_Reload, Fly_Right, Fly_Right_Root, Fly_Root, Fly_Rotate_90_45_Down_Left, Fly_Rotate_90_45_Down_Right, Fly_Rotate_90_45_Up_Left, Fly_Rotate_90_45_Up_Right, Fly_Rotate_90_Down, Fly_Rotate_90_Left, Fly_Rotate_90_Right, Fly_Rotate_90_Up, Fly_Shot_01, Fly_Shot_02, Fly_Shot_03, Fly_Start, Get_Hit, Get_Hit_02, Idle_01, Idle_02, Idle_03, Jump, Landing, Mech_Run, Reload, Rotate_90_45_Down_Left, Rotate_90_45_Down_Right, Rotate_90_45_Up_Left, Rotate_90_45_Up_Right, Rotate_90_Down, Rotate_90_Left, Rotate_90_Right, Rotate_90_Up, Run, Run_Back, Run_Back_Root, Run_Fast, Run_Fast_Root, Run_Left, Run_Left_Root, Run_Right, Run_Right_Root, Run_Root, Shot_01, Shot_02, Shot_03, Walk, Walk_Back, Walk_Back_Root, Walk_Left, Walk_Left_Root, Walk_Right, Walk_Right_Root, Walk_Root
- **2 clips** (UE Mannequin-style, 57 bones) -> plays on: Dystopia_Mech_Mesh, Dystopia_Mutant_soldier, Dystopia_Soldier_02_Mesh, Dystopia_Soldier_Mesh, Dystopian_general, Medic_Dystopia, Pilot_Mesh
  - Close, Open
- No clips of their own: Dystopia_Mech_Hoses_Mesh
- Static meshes (7): Dystopia_Airship, Dystopia_Mech_Rifle_Mesh, Dystopia_Mech_Sword_Mesh, Dystopia_Soldier_Weapon_Mesh, Grenade_Mesh, Sleeve_Mesh, Tank

### Fantasy Animal Pack
- **3ds Max CAT (creature)** models (5; own animations only): Bull_Fantasy, Camel, Fantasy_Animal, Fantasy_Dragon, Fantasy_Elephant_Full
- **UE Mannequin-style** models (1; auto-retargets with UE5 mannequin animations): Character
- **Weapon/prop rig** models (4; own animations only): Banner_01, Banner_02, Banner_Stand, Fantasy_Elephant_Build_Full
- **21 clips** (3ds Max CAT (creature), 34 bones) -> plays on: Fantasy_Animal
  - Attack_01, Attack_02, Climb_On_Animal, Dead_01, Dead_02, Get_Hit_01, Get_Hit_02, Get_Off_Animal, Idle_01, Idle_02, Jump, Jump_End, Jump_Loop, Jump_Start, Rotation_L_90, Rotation_L_90_Back, Rotation_R_90, Rotation_R_90_Back, Run, Shout, Walk
- **1 clips** (3ds Max CAT (creature), 37 bones) -> plays on: Bull_Fantasy
  - Run_Root
- **22 clips** (UE Mannequin-style, 60 bones) -> plays on: Character
  - Attack_01, Attack_02, Climb_Get_Off_Animal, Climb_On_Animal, Dead, Dead_01, Dead_02, Get_Hit_01, Get_Hit_02, Idle_01, Idle_02, Jump, Jump_End, Jump_Loop, Jump_Start, Rotation_L_90, Rotation_L_90_Back, Rotation_R_90, Rotation_R_90_Back, Run, Shout, Walk
- **15 clips** (3ds Max CAT (creature), 38 bones) -> plays on: Fantasy_Dragon
  - Flight_45_L, Flight_45_L_Root, Flight_45_R, Flight_45_R_Root, Flight_Root, Run_45_L, Run_45_L_Root, Run_45_R, Run_45_R_Root, Run_Root, Walk_45_L, Walk_45_R, Walk_Root, Walk_Root_45_L, Walk_Root_45_R
- **2 clips** (3ds Max CAT (creature), 36 bones) -> plays on: Bull_Fantasy
  - Attack_01, Walk
- **23 clips** (3ds Max CAT (creature), 43 bones) -> plays on: Fantasy_Dragon
  - Attack_01, Attack_02, Attack_03, Attack_Fire, Dead, Flight, Flight_Dead, Flight_Get_Hit, Flight_Idle, Flight_Rotation_90_L, Flight_Rotation_90_R, Flight_Soar, Get_Hit_01, Get_Hit_02, Idle_01, Idle_02, Landing, Rotation_90_L, Rotation_90_R, Run, Shout, Takeoff, Walk
- **2 clips** (3ds Max CAT (creature), 34 bones) -> plays on: Fantasy_Elephant_Full
  - Run_Root, Walk_Root
- **1 clips** (3ds Max CAT (creature), 35 bones) -> plays on: Bull_Fantasy
  - Walk_Root
- **4 clips** (3ds Max CAT (creature), 38 bones) -> plays on: Bull_Fantasy
  - Dead, Idle_01, Idle_02, Run
- **2 clips** (3ds Max CAT (creature), 31 bones) -> plays on: Fantasy_Animal
  - Run_Root, Walk_Root
- **2 clips** (3ds Max CAT (creature), 34 bones) -> plays on: Camel
  - Run_Root, Walk_Root
- **4 clips** (3ds Max CAT (creature), 39 bones) -> plays on: _no model in this pack shares this skeleton_
  - Idle_02, Rotation_90_L_Back, Rotation_90_R, Rotation_90_R_Back
- **1 clips** (3ds Max CAT (creature), 42 bones) -> plays on: Bull_Fantasy
  - Get_Hit
- **11 clips** (3ds Max CAT (creature), 35 bones) -> plays on: Camel
  - Dead, Get_Hit_01, Get_Hit_02, Idle_01, Idle_02, Jump, Jump_End, Jump_Loop, Jump_Start, Run, Walk
- **1 clips** (UE Mannequin-style, 68 bones) -> plays on: _no model in this pack shares this skeleton_
  - Male_Body
- **13 clips** (3ds Max CAT (creature), 35 bones) -> plays on: Fantasy_Elephant_Full
  - Attack_01, Attack_02, Dead_01, Dead_02, Get_Hit_01, Get_Hit_02, Get_Hit_03, Idle_01, Idle_03, Idle_04, Rotation_90_L, Run, Walk
- No clips of their own: Banner_01, Banner_02, Banner_Stand, Fantasy_Elephant_Build_Full
- Static meshes (14): Barrel, Box, Carpet, Cloth_02, Cloth_03, Cloth_04, Cloth_05, Horn, Ladder, Pot_01, Pot_02, Shield_03, Shield_04, Shield_06

### Fantasy Enemies Pack
- **UE Mannequin-style** models (7; auto-retargets with UE5 mannequin animations): Befouler, Davil, Davil_Polygons_Cut, Demon_Mesh, Executioner, Troll, Troll_Polygons_Cut
- **Weapon/prop rig** models (3; own animations only): Arms_Legs_With_Bones, Davil_Tail, Davil_Tail_Polygons_Cut
- No clips of their own: Arms_Legs_With_Bones, Befouler, Davil, Davil_Polygons_Cut, Davil_Tail, Davil_Tail_Polygons_Cut, Demon_Mesh, Executioner, Troll, Troll_Polygons_Cut
- Static meshes (14): Befouler_Arm_01, Befouler_Arm_02, Befouler_Arm_03, Befouler_Arm_04, Befouler_Head_04, Befouler_Head_05, Befouler_Head_06, Befouler_Leg_01, Befouler_Leg_02, Befouler_Weapon, Demon_Axe_Mesh, Executioner_Axe, Troll_Axe, Troll_Axe_02

### Fantasy Warriors Pack
- **UE Mannequin-style** models (5; auto-retargets with UE5 mannequin animations): Dark_Knight_02, Demonic_Warrior, Fantasy_Hero_02, Fantasy_Hero_Character, Fantasy_Witch
- No clips of their own: Dark_Knight_02, Demonic_Warrior, Fantasy_Hero_02, Fantasy_Hero_Character, Fantasy_Witch
- Static meshes (6): Dark_Knight_02_Sword, Demonic_Warrior_Sword, Fantasy_Hero_02_Shield, Fantasy_Hero_02_Spear, Fantasy_Hero_Weapon, Fantasy_Witch_Weapon

### Female Soldiers Pack
- **Could not be read:** unexpected end of data - the download is incomplete; re-download it from Fab.

### Fighters Pack
- **UE Mannequin-style** models (15; auto-retargets with UE5 mannequin animations): FIghter_14_Mesh, Fighter_01_Mesh, Fighter_02_Mesh, Fighter_03_Mesh, Fighter_04_Mesh, Fighter_05_Mesh, Fighter_06_Mesh, Fighter_07_Mesh, Fighter_08_Mesh, Fighter_09_Mesh, Fighter_10_Mesh, Fighter_11_Mesh, Fighter_12_Mesh, Fighter_13_Mesh, Fighter_15_Mesh
- No clips of their own: FIghter_14_Mesh, Fighter_01_Mesh, Fighter_02_Mesh, Fighter_03_Mesh, Fighter_04_Mesh, Fighter_05_Mesh, Fighter_06_Mesh, Fighter_07_Mesh, Fighter_08_Mesh, Fighter_09_Mesh, Fighter_10_Mesh, Fighter_11_Mesh, Fighter_12_Mesh, Fighter_13_Mesh, Fighter_15_Mesh

### FPS ANIMATIONS PISTOL TACTICAL SHIELD
- **UE Mannequin-style** models (2; auto-retargets with UE5 mannequin animations): Hands_04_Mesh, Hands_Pistol_Shield
- **Weapon/prop rig** models (3; own animations only): Pistol, Pistol_Cartridge, Shield
- **24 clips** (UE Mannequin-style, 60 bones) -> plays on: Hands_04_Mesh, Hands_Pistol_Shield; also fits models in: Fantasy Animal Pack (1)
  - Attack_01, Attack_02, Attack_03, Block_Get_Hit, Block_Idle, Get_Weapon, Hide, Idle_01, Idle_02, Idle_Aim, Idle_Sight, Jump, Reload_01, Reload_02, Run_01, Run_02, Shot, Shot_Aim, Shot_Sight, Walk_01, Walk_02, Walk_Aim, Walk_Sight, Weapon_Inspection
- **1 clips** (UE Mannequin-style, 110 bones) -> plays on: _no model in this pack shares this skeleton_
  - Weapon_Inspection
- **23 clips** (UE Mannequin-style, 64 bones) -> plays on: Hands_Pistol_Shield; also fits models in: FPS Pistol And Knife Animations (1)
  - Attack_01, Attack_02, Attack_03, Block_Get_Hit, Block_Idle, Get_Weapon, Hide, Idle_01, Idle_02, Idle_Aim, Idle_Sight, Jump, Reload_01, Reload_02, Run_01, Run_02, Shot, Shot_Aim, Shot_Sight, Walk_01, Walk_02, Walk_Aim, Walk_Sight
- **2 clips** (Weapon/prop rig, 7 bones) -> plays on: Pistol
  - Shield_Reload_01, Shield_Shot
- No clips of their own: Pistol_Cartridge, Shield
- Static meshes (1): Pistol_Sleeve

### FPS Automatic Rifle 01 Animations
- **UE Mannequin-style** models (2; auto-retargets with UE5 mannequin animations): Automatic_Rifle_01_With_Hands, Hands_04_Mesh
- **Weapon/prop rig** models (4; own animations only): Automatic_Rifle_01_Cartridge, Automatic_Rifle_01_With_Cartridge, Automatic_Rifle_01_Without_Cartridge, Automatic_Rifle_01_Without_Cartridge_And_Parts
- **27 clips** (UE Mannequin-style, 60 bones) -> plays on: Automatic_Rifle_01_With_Hands, Hands_04_Mesh; also fits models in: Fantasy Animal Pack (1)
  - Attack_01, Attack_02, Attack_03, Block_Get_Hit, Get_Weapon_01, Hide_Weapon, Idle_01, Idle_02, Idle_Aim, Idle_Block, Idle_Sight, Inspection, Inspection_Cartridge, Jump, Jump_End, Jump_Start, Jump_loop, Reload, Run_01, Run_02, Shot, Shot_Aim, Shot_Sight, Walk_01, Walk_02, Walk_Aim, Walk_Sight
- **27 clips** (UE Mannequin-style, 62 bones) -> plays on: Automatic_Rifle_01_With_Hands
  - Attack_01, Attack_02, Attack_03, Block_Get_Hit, Get_Weapon_01, Hide_Weapon, Idle_01, Idle_02, Idle_Aim, Idle_Block, Idle_Sight, Inspection_Cartridge, Jump, Jump_End, Jump_Loop, Jump_Start, Reload, Run_01, Run_02, Shot, Shot_Aim, Shot_Sight, Walk_01, Walk_02, Walk_Aim, Walk_Sight, Weapon_Inspection
- **1 clips** (Weapon/prop rig, 2 bones) -> plays on: _no model in this pack shares this skeleton_
  - Reload
- **2 clips** (Weapon/prop rig, 6 bones) -> plays on: Automatic_Rifle_01_With_Cartridge, Automatic_Rifle_01_With_Hands, Automatic_Rifle_01_Without_Cartridge, Automatic_Rifle_01_Without_Cartridge_And_Parts
  - Reload_Without_Arms, Rifle_01_Shot_Without_Arms
- No clips of their own: Automatic_Rifle_01_Cartridge
- Static meshes (12): Automatic_Rifle_01_FlashLight_01, Automatic_Rifle_01_FlashLight_02, Automatic_Rifle_01_FlashLight_03, Automatic_Rifle_01_Sight_01, Automatic_Rifle_01_Sight_02, Automatic_Rifle_01_Sight_03, Automatic_Rifle_01_Sight_04, Automatic_Rifle_01_Silencers_01, Automatic_Rifle_01_Silencers_02, Automatic_Rifle_01_Silencers_03, Automatic_Rifle_01_Silencers_04, Automatic_Rifle_01_Sleeve

### FPS Automatic Rifle 02 Animations
- **UE Mannequin-style** models (2; auto-retargets with UE5 mannequin animations): Hands_04_Mesh, Hands_AutoRifle_02
- **Weapon/prop rig** models (2; own animations only): AutoRifle_Cartridge, AutoRifle_Full
- **26 clips** (UE Mannequin-style, 60 bones) -> plays on: Hands_04_Mesh, Hands_AutoRifle_02; also fits models in: Fantasy Animal Pack (1)
  - Attack_01, Attack_02, Attack_03, Get_Weapon, Hide, Idle_01, Idle_02, Idle_Aim, Inspection_Cartridge, Inspection_Weapon, Jump, Jump_End, Jump_Loop, Jump_Start, Reload, Run_01, Run_02, Run_03, Run_04, Shot, Shot_Aim, Walk_01, Walk_02, Walk_03, Walk_04, Walk_Aim
- **2 clips** (Weapon/prop rig, 8 bones) -> plays on: AutoRifle_Full, Hands_AutoRifle_02
  - Reload, Shot
- **26 clips** (UE Mannequin-style, 62 bones) -> plays on: Hands_AutoRifle_02
  - Aim_Idle, Aim_Walk, Attack_01, Attack_02, Attack_03, Get_Weapon, Hide, Idle_01, Idle_02, Inspection_Cartridge, Inspection_Weapon, Jump, Jump_End, Jump_Loop, Jump_Start, Reload, Run_01, Run_02, Run_03, Run_04, Shot, Shot_Aim, Walk_01, Walk_02, Walk_03, Walk_04
- **1 clips** (Weapon/prop rig, 2 bones) -> plays on: _no model in this pack shares this skeleton_
  - Reload
- No clips of their own: AutoRifle_Cartridge
- Static meshes (1): AutoRifle_Sleeve

### FPS Automatic-Shotgun Animations
- **UE Mannequin-style** models (2; auto-retargets with UE5 mannequin animations): Automatic_Shotgun_And_Hands, Hands_04_Mesh
- **Weapon/prop rig** models (2; own animations only): Automatic_Shotgun_Cartridge, Automatic_Shotgun_Full
- **1 clips** (Weapon/prop rig, 11 bones) -> plays on: Automatic_Shotgun_And_Hands, Automatic_Shotgun_Full
  - Shot
- **30 clips** (UE Mannequin-style, 60 bones) -> plays on: Automatic_Shotgun_And_Hands, Hands_04_Mesh; also fits models in: Fantasy Animal Pack (1)
  - Attack_01, Attack_02, Attack_03, Attack_04, Get_Weapon, Hide, Idle_01, Idle_02, Idle_03, Idle_04, Idle_Sight, Inspection_Cartridge, Inspection_Weapon, Jump, Jump_End, Jump_Loop, Jump_Start, Reload, Run_01, Run_02, Run_03, Run_04, Shot, Shot_02, Shot_Sight, Walk_01, Walk_02, Walk_03, Walk_04, Walk_Sight
- **1 clips** (Weapon/prop rig, 2 bones) -> plays on: _no model in this pack shares this skeleton_
  - Reload
- **30 clips** (UE Mannequin-style, 67 bones) -> plays on: Automatic_Shotgun_And_Hands
  - Attack_01, Attack_02, Attack_03, Attack_04, Get_Weapon, Hide, Idle_01, Idle_02, Idle_03, Idle_04, Idle_Sight, Inspection_Cartridge, Inspection_Weapon, Jump, Jump_End, Jump_Start, Loop, Reload, Run_01, Run_02, Run_03, Run_04, Shot, Shot_02, Shot_Sight, Walk_01, Walk_02, Walk_03, Walk_04, Walk_Sight
- No clips of their own: Automatic_Shotgun_Cartridge
- Static meshes (1): Automatic_Shotgun_Bullet

### FPS Devices
- **UE Mannequin-style** models (1; auto-retargets with UE5 mannequin animations): Hands_04
- **Weapon/prop rig** models (1; own animations only): Camera
- **33 clips** (UE Mannequin-style, 60 bones) -> plays on: Hands_04; also fits models in: Fantasy Animal Pack (1)
  - Action, Action_01, Action_02, Action_03, Action_04, Action_Idle, Attack_01, Attack_02, Get, Get_HIt, Get_Hit, Hide, Idle, Idle_01, Idle_02, Idle_03, Idle_Other, Jump, Jump_End, Jump_Loop, Jump_Start, Run, Run_01, Run_02, Talk, Video, Video_End, Video_Loop, Video_Start, Walk, Walk_01, Walk_02, Watching_Video
- No clips of their own: Camera
- Static meshes (4): Listening_Device, Phone, Tablet, Walkie_Talkie

### FPS Pistol And Knife Animations
- **UE Mannequin-style** models (2; auto-retargets with UE5 mannequin animations): Hands_04_Mesh, Pistol_Knife
- **Weapon/prop rig** models (2; own animations only): Pistol, Pistol_Cartridge
- **28 clips** (UE Mannequin-style, 60 bones) -> plays on: Hands_04_Mesh, Pistol_Knife; also fits models in: Fantasy Animal Pack (1)
  - Attack_01, Attack_02, Attack_03, Attack_04, Attack_05, Get_Hit_Block, Get_Weapon, Hide, Idle_01, Idle_02, Idle_Aim, Idle_Block, Idle_Sight, Inspect_Cartridge, Jump, Reload_01, Reload_02, Run_01, Run_02, Shot, Shot_Aim, Shot_Sight, Walk_01, Walk_02, Walk_Aim, Walk_Sight, Weapon_Inspection_01, Weapon_Inspection_02
- **31 clips** (UE Mannequin-style, 64 bones) -> plays on: Pistol_Knife
  - Attack_01, Attack_02, Attack_03, Attack_04, Attack_05, Get_Hit_Block, Get_Weapon, Hide, Idle_01, Idle_02, Idle_Aim, Idle_Block, Idle_Sight, Inspect_Cartridge, Jump, Jump_End, Jump_Loop, Jump_Start, Reload_01, Reload_02, Run_01, Run_02, Shot, Shot_Aim, Shot_Sight, Walk_01, Walk_02, Walk_Aim, Walk_Sight, Weapon_Inspection_01, Weapon_Inspection_02
- **2 clips** (Weapon/prop rig, 7 bones) -> plays on: Pistol
  - Without_Arms_Reload_01, Without_Arms_Shot
- No clips of their own: Pistol_Cartridge
- Static meshes (2): Knife, Pistol_Sleeve

### FPS Pistol Single
- **UE Mannequin-style** models (2; auto-retargets with UE5 mannequin animations): Hands_04_Mesh, Hands_04_With_Pistol
- **Weapon/prop rig** models (2; own animations only): Pistol, Pistol_Cartridge
- **1 clips** (Weapon/prop rig, 2 bones) -> plays on: _no model in this pack shares this skeleton_
  - Reload_02
- **30 clips** (UE Mannequin-style, 60 bones) -> plays on: Hands_04_Mesh, Hands_04_With_Pistol; also fits models in: Fantasy Animal Pack (1)
  - Attack_01, Attack_02, Attack_03, Attack_04, Block_Get_Hit, Block_Idle, Get_Weapon_01, Get_Weapon_02, Hands_Up, Hide, Idle_01, Idle_02, Idle_03, Idle_Aim, Idle_Sight, Jump, Lie_Down_On_The_Ground, Reload_01, Reload_02, Run_01, Run_02, Shot, Shot_Aim, Shot_Sight, Walk_01, Walk_02, Walk_03, Walk_Aim, Walk_Sight, Weapon_Inspection
- **30 clips** (UE Mannequin-style, 63 bones) -> plays on: Hands_04_With_Pistol; also fits models in: FPS Pistol And Knife Animations (1)
  - Attack_01, Attack_02, Attack_03, Attack_04, Block_Get_Hit, Block_Idle, Get_Weapon_01, Get_Weapon_02, Hands_Up, Hide, Idle_01, Idle_02, Idle_03, Idle_Aim, Idle_Sight, Jump, Lie_Down_On_The_Ground, Reload_01, Reload_02, Run_01, Run_02, Shot, Shot_Aim, Shot_Sight, Walk_01, Walk_02, Walk_03, Walk_Aim, Walk_Sight, Weapon_Inspection
- **3 clips** (Weapon/prop rig, 7 bones) -> plays on: Pistol
  - Get_Weapon_02, Reload_02, Shot
- No clips of their own: Pistol_Cartridge
- Static meshes (1): Pistol_Sleeve

### FPS Rocket Launcher Animations
- **UE Mannequin-style** models (2; auto-retargets with UE5 mannequin animations): Hands_04_Mesh, Hands_Rocket_Launcher
- **Weapon/prop rig** models (2; own animations only): Rocket, Rocket_Launcher
- **23 clips** (UE Mannequin-style, 60 bones) -> plays on: Hands_04_Mesh, Hands_Rocket_Launcher; also fits models in: Fantasy Animal Pack (1)
  - Attack_01, Attack_02, Get_Weapon, Hide, Idle_01, Idle_02, Idle_Aim, Idle_Sight, Inspection_Weapon, Jump, Jump_End, Jump_Loop, Jump_Start, Reload, Run_01, Run_02, Shot, Shot_Aim, Shot_Sight, Walk_01, Walk_02, Walk_Aim, Walk_Sight
- **23 clips** (UE Mannequin-style, 59 bones) -> plays on: Hands_04_Mesh, Hands_Rocket_Launcher
  - Attack_01, Attack_02, Get_Weapon, Hide, Idle_01, Idle_02, Idle_Aim, Idle_Sight, Inspection_Weapon, Jump, Jump_End, Jump_Loop, Jump_Start, Reload, Run_01, Run_02, Shot, Shot_Aim, Shot_Sight, Walk_01, Walk_02, Walk_Aim, Walk_Sight
- No clips of their own: Rocket, Rocket_Launcher

### FPS Sci-Fi Hands Empty
- **UE Mannequin-style** models (1; auto-retargets with UE5 mannequin animations): Sci_Fi_Hands_Full_With_Shield
- **Weapon/prop rig** models (1; own animations only): Sci_Fi_Shield
- **27 clips** (UE Mannequin-style, 161 bones) -> plays on: _no model in this pack shares this skeleton_
  - Attack_01, Attack_02, Attack_03, Attack_04, Block_Get_Hit, Block_Idle, Computer_Idle, Energy_Attack_01, Get, Hide, Idle, Idle_Fight, Idle_Other, Jump, Jump_End, Jump_Loop, Jump_Start, Run_01, Run_02, Shield_Get, Shield_Get_Hit, Shield_Hide, Shield_Idle, Shield_Run, Shield_Walk, Walk_01, Walk_02
- **27 clips** (UE Mannequin-style, 93 bones) -> plays on: Sci_Fi_Hands_Full_With_Shield
  - Attack_01, Attack_02, Attack_03, Attack_04, Block_Get_Hit, Block_Idle, Computer_Idle, Energy_Attack_01, Get, Hide, Idle, Idle_Fight, Idle_Other, Jump, Jump_End, Jump_Loop, Jump_Start, Run_01, Run_02, Shield_Get, Shield_Get_Hit, Shield_Hide, Shield_Idle, Shield_Run, Shield_Walk, Walk_01, Walk_02
- **2 clips** (Weapon/prop rig, 16 bones) -> plays on: Sci_Fi_Hands_Full_With_Shield, Sci_Fi_Shield
  - Close, Open

### FPS Sniper Rifle 03 Animations
- **UE Mannequin-style** models (2; auto-retargets with UE5 mannequin animations): Hands_04_Mesh, Hands_With_Sniper_Rifle_03
- **Weapon/prop rig** models (2; own animations only): Sniper_Rifle_03_Cartridge, Sniper_Rifle_03_Full
- **1 clips** (Weapon/prop rig, 6 bones) -> plays on: Hands_With_Sniper_Rifle_03, Sniper_Rifle_03_Full
  - Shot
- **24 clips** (UE Mannequin-style, 60 bones) -> plays on: Hands_04_Mesh, Hands_With_Sniper_Rifle_03; also fits models in: Fantasy Animal Pack (1)
  - Aim_Idle, Aim_Shot, Aim_Walk, Attack_01, Attack_02, Attack_03, Get_Weapon, Hide, Idle_01, Idle_02, Idle_03, Inspection_Cartridge, Inspection_Weapon, Jump, Jump_End, Jump_Loop, Jump_Start, Reload, Run_01, Run_02, Shot, Walk_01, Walk_02, Walk_03
- **24 clips** (UE Mannequin-style, 62 bones) -> plays on: Hands_With_Sniper_Rifle_03
  - Aim_Idle, Aim_Shot, Aim_Walk, Attack_01, Attack_02, Attack_03, Get_Weapon, Hide, Idle_01, Idle_02, Idle_03, Inspection_Cartridge, Inspection_Weapon, Jump, Jump_End, Jump_Loop, Jump_Start, Reload, Run_01, Run_02, Shot, Walk_01, Walk_02, Walk_03
- **1 clips** (Weapon/prop rig, 2 bones) -> plays on: _no model in this pack shares this skeleton_
  - Cartridge_Reload
- No clips of their own: Sniper_Rifle_03_Cartridge
- Static meshes (1): Sniper_Rifle_03_Sleeve

### FPS Sniper Rifle Large Calibre Animations
- **UE Mannequin-style** models (2; auto-retargets with UE5 mannequin animations): Hands_04_Mesh, Hands_Sniper_Rifle_Full
- **Weapon/prop rig** models (2; own animations only): Sniper_Rifle_Cartridge, Sniper_Rifle_Full
- **22 clips** (UE Mannequin-style, 60 bones) -> plays on: Hands_04_Mesh, Hands_Sniper_Rifle_Full; also fits models in: Fantasy Animal Pack (1)
  - Attack_01, Attack_02, Get_Weapon, Hide, Idle_01, Idle_02, Idle_03, Inspection_Cartridge, Inspection_Weapon, Jump, Jump_End, Jump_Loop, Jump_Start, Reload, Run_01, Run_02, Shot, Shot_Sight, Sight_Idle, Walk_01, Walk_02, Walk_Sight
- **1 clips** (Weapon/prop rig, 9 bones) -> plays on: Hands_Sniper_Rifle_Full, Sniper_Rifle_Full
  - Shot
- **22 clips** (UE Mannequin-style, 65 bones) -> plays on: Hands_Sniper_Rifle_Full
  - Attack_01, Attack_02, Get_Weapon, Hide, Idle_01, Idle_02, Idle_03, Inspection_Cartridge, Inspection_Weapon, Jump, Jump_End, Jump_Loop, Jump_Start, Reload, Run_01, Run_02, Shot, Shot_Sight, Sight_Idle, Walk_01, Walk_02, Walk_Sight
- **1 clips** (Weapon/prop rig, 2 bones) -> plays on: _no model in this pack shares this skeleton_
  - Reload
- No clips of their own: Sniper_Rifle_Cartridge
- Static meshes (1): Sniper_Rifle_Sleeve

### FPS STARTER PACK
- **3ds Max CAT (creature)** models (1; own animations only): Shield_Full_Mesh
- **UE Mannequin-style** models (21; auto-retargets with UE5 mannequin animations): Hands_010_Mesh, Hands_011_Mesh, Hands_012_Mesh, Hands_013_Mesh, Hands_014_Mesh, Hands_015_Mesh, Hands_016_Mesh, Hands_017_Mesh, Hands_018_Mesh, Hands_019_Mesh, Hands_01_Mesh, Hands_020_Mesh, Hands_02_Mesh, Hands_03_Mesh, Hands_04_Mesh, Hands_05_Mesh, Hands_06_Mesh, Hands_07_Mesh, Hands_08_Mesh, Hands_09_Mesh, Hands_Ful
- **Weapon/prop rig** models (34; own animations only): Chicken_Mesh, Chocolate_01_Mesh, Chocolate_02_Mesh, Chocolate_03@Hide, Chocolate_03_Mesh, Cookie@Hide, Cookie_Mesh, Fish_Mesh, Flask_Mesh, Hands_Chocolate_02@Hide, Jar_Mesh, Juce_Mesh, Lemonade_Bottle_Mesh, Lighter_Mesh, Marshmallows_Mesh, Meatball_Fork_Mesh, Meatball_Mesh, Mug_Mesh, Porridge_Plate_Mesh, Porridge_Spoon_Mesh, Pot_Mesh, Pot_Spoon_Mesh, Sardines_Fork_Mesh, Sardines_Mesh, Sausage_Mesh, Shaker_Mesh, Soda_Mesh, Spoon_Mesh, Sprats_Fork_Mesh, Sprats_Mesh, Stun_Gun_Mesh, Syringe_01_Mesh, Syringe_02_Mesh, Syringe_03_Mesh
- **1 clips** (Weapon/prop rig, 4 bones) -> plays on: Lemonade_Bottle_Mesh
  - Open_Close
- **1 clips** (Weapon/prop rig, 2 bones) -> plays on: _no model in this pack shares this skeleton_
  - Push
- **1 clips** (Weapon/prop rig, 2 bones) -> plays on: _no model in this pack shares this skeleton_
  - Hide
- **1 clips** (Weapon/prop rig, 2 bones) -> plays on: _no model in this pack shares this skeleton_
  - Spoon
- **1 clips** (Weapon/prop rig, 2 bones) -> plays on: _no model in this pack shares this skeleton_
  - Rotation
- **1 clips** (Weapon/prop rig, 3 bones) -> plays on: _no model in this pack shares this skeleton_
  - Close
- **31 clips** (UE Mannequin-style, 60 bones) -> plays on: Hands_010_Mesh, Hands_011_Mesh, Hands_012_Mesh, Hands_013_Mesh, Hands_014_Mesh, Hands_015_Mesh, Hands_016_Mesh, Hands_017_Mesh, Hands_018_Mesh, Hands_019_Mesh, Hands_01_Mesh, Hands_020_Mesh, Hands_02_Mesh, Hands_03_Mesh, Hands_04_Mesh, Hands_05_Mesh, Hands_06_Mesh, Hands_07_Mesh, Hands_08_Mesh, Hands_09_Mesh, Hands_Ful; also fits models in: Fantasy Animal Pack (1)
  - Attack_01, Attack_02, Attack_03, Attack_04, Attack_05, Attack_06, Beckon, Block, Block_Get_Hit, Block_Idle, Close_Of_Fire_Idle, Close_Of_Fire_Walk, Down, Drink, Eat, Finger_Up, Get_Hit, Idle, Idle_Block, Idle_Other, Idle_Other_01, Idle_Other_02, Jump, Run, Run_02, Take, Up, Using, Walk, Watch, Watch_Idle
- **1 clips** (Weapon/prop rig, 2 bones) -> plays on: _no model in this pack shares this skeleton_
  - Push
- **2 clips** (Weapon/prop rig, 2 bones) -> plays on: _no model in this pack shares this skeleton_
  - Close, Open
- **1 clips** (Weapon/prop rig, 7 bones) -> plays on: Sardines_Mesh
  - Open
- **1 clips** (Weapon/prop rig, 11 bones) -> plays on: Meatball_Mesh
  - Open
- **1 clips** (Weapon/prop rig, 7 bones) -> plays on: Sprats_Mesh
  - Open
- **1 clips** (Weapon/prop rig, 2 bones) -> plays on: _no model in this pack shares this skeleton_
  - Fork
- **1 clips** (Weapon/prop rig, 2 bones) -> plays on: _no model in this pack shares this skeleton_
  - Hide
- **1 clips** (Weapon/prop rig, 5 bones) -> plays on: Jar_Mesh
  - Open
- **1 clips** (Weapon/prop rig, 2 bones) -> plays on: _no model in this pack shares this skeleton_
  - Open_Close
- **1 clips** (Weapon/prop rig, 2 bones) -> plays on: _no model in this pack shares this skeleton_
  - Fork
- **1 clips** (Weapon/prop rig, 2 bones) -> plays on: _no model in this pack shares this skeleton_
  - Hide
- **1 clips** (Weapon/prop rig, 2 bones) -> plays on: _no model in this pack shares this skeleton_
  - Close
- **1 clips** (Weapon/prop rig, 3 bones) -> plays on: _no model in this pack shares this skeleton_
  - Food
- **1 clips** (Weapon/prop rig, 6 bones) -> plays on: Porridge_Plate_Mesh
  - Open
- **1 clips** (Weapon/prop rig, 3 bones) -> plays on: _no model in this pack shares this skeleton_
  - Open_Close
- **1 clips** (Weapon/prop rig, 2 bones) -> plays on: _no model in this pack shares this skeleton_
  - Hide
- **1 clips** (Weapon/prop rig, 2 bones) -> plays on: _no model in this pack shares this skeleton_
  - Push
- **1 clips** (Weapon/prop rig, 2 bones) -> plays on: _no model in this pack shares this skeleton_
  - Rotation
- **1 clips** (Weapon/prop rig, 2 bones) -> plays on: _no model in this pack shares this skeleton_
  - Rotation
- No clips of their own: Chicken_Mesh, Chocolate_01_Mesh, Chocolate_02_Mesh, Chocolate_03@Hide, Chocolate_03_Mesh, Cookie@Hide, Cookie_Mesh, Fish_Mesh, Flask_Mesh, Hands_Chocolate_02@Hide, Juce_Mesh, Lighter_Mesh, Marshmallows_Mesh, Meatball_Fork_Mesh, Mug_Mesh, Porridge_Spoon_Mesh, Pot_Mesh, Pot_Spoon_Mesh, Sardines_Fork_Mesh, Sausage_Mesh, Shaker_Mesh, Shield_Full_Mesh, Soda_Mesh, Spoon_Mesh, Sprats_Fork_Mesh, Stun_Gun_Mesh, Syringe_01_Mesh, Syringe_02_Mesh, Syringe_03_Mesh
- Static meshes (23): Axe_01_Mesh, Axe_02_Mesh, Binoculars_Mesh, Bita_Mesh, Candle_Mesh, Club_Mesh, Flashlight_01_Mesh, Flashlight_02_Mesh, Gas_Spray_Mesh, Ice_Axe_Mesh, Knife_010_Mesh, Knife_01_Mesh, Knife_02_Mesh, Knife_03_Mesh, Knife_04_Mesh, Knife_05_Mesh, Knife_06_Mesh, Knife_07_Mesh, Knife_08_Mesh, Knife_09_Mesh, PC_Mesh, Star_Axe_Mesh, Torch_Mesh

### Geek Room
- **UE Mannequin-style** models (1; auto-retargets with UE5 mannequin animations): Girl_for_room
- **1 clips** (UE Mannequin-style, 60 bones) -> plays on: Girl_for_room; also fits models in: Fantasy Animal Pack (1)
  - Idle
- Static meshes (69): Geek_room_Battery, Geek_room_Blanket, Geek_room_Blower, Geek_room_Bottle_01, Geek_room_Bottle_02, Geek_room_Bottle_03, Geek_room_Bottle_04, Geek_room_Bottle_05, Geek_room_Bottle_cap, Geek_room_Box, Geek_room_Box_Food_01, Geek_room_Box_Food_02, Geek_room_Bucket, Geek_room_Ceiling, Geek_room_Ceiling_Plinth_01, Geek_room_Ceiling_Plinth_02, Geek_room_Ceiling_Plinth_03, Geek_room_Ceiling_Plinth_04, Geek_room_Chair, Geek_room_Cork_from_the_bottle_01, Geek_room_Cork_from_the_bottle_02, Geek_room_Crumpled_box, Geek_room_Cup, Geek_room_Door, Geek_room_Doorway, Geek_room_Floor, Geek_room_Floor_skirting_board_01, Geek_room_Floor_skirting_board_02, Geek_room_Floor_skirting_board_03, Geek_room_Floor_skirting_board_04 ...

### Humanoids Creatures Pack
- **UE Mannequin-style** models (5; auto-retargets with UE5 mannequin animations): Creature_01_Mesh, Creature_02_Mesh, Creature_03_Mesh, Creature_04_Mesh, Creature_05_Mesh
- **33 clips** (UE Mannequin-style, 61 bones) -> plays on: _no model in this pack shares this skeleton_; also fits models in: Fantasy Animal Pack (1)
  - Attack_1, Attack_10, Attack_2, Attack_3, Attack_4, Attack_5, Attack_6, Attack_7, Attack_8, Attack_9, Dead_1, Dead_2, Dead_3, Dead_4, Get_Hit, Get_Hit_Back, Get_Hit_Left, Get_Hit_Right, Idle_1, Idle_2, Jump, Run, Run_Back, Run_Left, Run_Right, Shout_1, Shout_2, Turn_Right, Walk, Walk_Back, Walk_Left, Walk_Right, urn_Left
- **8 clips** (UE Mannequin-style, 60 bones) -> plays on: Creature_02_Mesh, Creature_03_Mesh, Creature_04_Mesh, Creature_05_Mesh; also fits models in: Fantasy Animal Pack (1)
  - Run_Back_Root, Run_Left_Root, Run_Right_Root, Run_Root, Walk_Back_Root, Walk_Left_Root, Walk_Right_Root, Walk_Root
- No clips of their own: Creature_01_Mesh

### Humanoids Monsters Pack
- **UE Mannequin-style** models (5; auto-retargets with UE5 mannequin animations): Monster_01_Mesh, Monster_02_Mesh, Monster_03_Mesh, Monster_04_Mesh, Monster_05_Mesh
- **22 clips** (UE Mannequin-style, 61 bones) -> plays on: Monster_01_Mesh, Monster_02_Mesh, Monster_03_Mesh, Monster_04_Mesh, Monster_05_Mesh; also fits models in: Fantasy Animal Pack (1)
  - Sit_Attack_5, Sit_Attack_6, Sit_Attack_7, Sit_Attack_8, Sit_Attack_From_Ground, Sit_Down_On_Ground_&_Up, Sit_Eat, Sit_Eat_Loop, Sit_Jump_From_The_Ceiling, Sit_Lies_On_The_Ground_Pose, Sit_On_The_Celing_Idle, Sit_Rebound_Bacward, Sit_Rebound_Left, Sit_Rebound_Right, Sit_Rotation_Left, Sit_Rotation_Right, Sit_Sit_Run_02, Sit_Sleep, Sit_Up_&_Shout, Sit_Walk_Back, Sit_Walk_Left, Sit_Walk_Right
- **23 clips** (UE Mannequin-style, 60 bones) -> plays on: Monster_01_Mesh, Monster_02_Mesh, Monster_03_Mesh, Monster_04_Mesh, Monster_05_Mesh; also fits models in: Fantasy Animal Pack (1)
  - Sit_Attack_1, Sit_Attack_2, Sit_Attack_3, Sit_Attack_4, Sit_Dead_1, Sit_Dead_2, Sit_Dead_3, Sit_Get_Hit_1, Sit_Get_Hit_2, Sit_Idle_1, Sit_Idle_2, Sit_Jump, Sit_Out_Of_ Ground, Sit_Run, Sit_Run_02_Root, Sit_Run_Root, Sit_Shout, Sit_Walk, Sit_Walk_Back_Root, Sit_Walk_Left_Root, Sit_Walk_Right_Root, Sit_Walk_Root, Sit_jump_On_The_Ground

### Knights Pack
- **UE Mannequin-style** models (5; auto-retargets with UE5 mannequin animations): Knight_01_Mesh, Knight_02_Mesh, Knight_03, Knight_04, Knight_05_Mesh
- **Weapon/prop rig** models (1; own animations only): Knight_01_Banner
- No clips of their own: Knight_01_Banner, Knight_01_Mesh, Knight_02_Mesh, Knight_03, Knight_04, Knight_05_Mesh
- Static meshes (12): Knight_01_Banner_Spear, Knight_01_Halberd, Knight_01_Halberd_Spear, Knight_01_Shield, Knight_01_Sword, Knight_02_Shield_Mesh, Knight_02_Sword_Mesh, Knight_03_Shield, Knight_03_Sword, Knight_04_Shield, Knight_04_Spear, Knight_05_Sword_Mesh

### Military Drones
- **UE Mannequin-style** models (1; auto-retargets with UE5 mannequin animations): Hands_04
- **Weapon/prop rig** models (5; own animations only): Joystick, Military_Drone, Military_Drone_01_Separate_Grenade_01, Military_Drone_01_Separate_Grenade_02, Military_Drone_02
- **1 clips** (Weapon/prop rig, 12 bones) -> plays on: _no model in this pack shares this skeleton_
  - Fly_Front
- **12 clips** (UE Mannequin-style, 60 bones) -> plays on: Hands_04; also fits models in: Fantasy Animal Pack (1)
  - Joystick_Drone_Сontrol, Joystick_Get, Joystick_Hide, Joystick_Idle, Joystick_Jump, Joystick_Jump_End, Joystick_Jump_Loop, Joystick_Jump_Start, Joystick_Run, Joystick_Start_Drone, Joystick_Stop_Drone, Joystick_Walk
- **17 clips** (Weapon/prop rig, 10 bones) -> plays on: Military_Drone, Military_Drone_02
  - Dropping_Grenade_01, Dropping_Grenade_02, Dropping_Grenade_03, Fly_Back, Fly_Back_Root, Fly_Front_Root, Fly_Left, Fly_Left_Root, Fly_Right, Fly_Right_Root, Idle, Landing, Rotation_L_45, Rotation_L_90, Rotation_R_45, Rotation_R_90, Takeoff
- No clips of their own: Joystick, Military_Drone_01_Separate_Grenade_01, Military_Drone_01_Separate_Grenade_02
- Static meshes (1): Grenade_01

### Military Pack
- **3ds Max CAT (creature)** models (1; own animations only): Dog_Mesh
- **3ds Max CAT (humanoid)** models (1; retarget via manual IK-rig chains): Solder_Mesh
- **Custom** models (1; own animations only): Elite_Soldier_Mesh
- **UE Mannequin-style** models (11; auto-retargets with UE5 mannequin animations): Diver_2_Mesh, Diver_Mesh, Investigator_Mesh, PBR_Soldier_Mesh_humanoid, Policeman_Mash, Soldier, Soldier_Gas_Mesh, Soldier_Marine_2, Soldier_Marine_Mesh, Soldier_Sapper, Soldier_Women_Mesh
- **Weapon/prop rig** models (1; own animations only): BackPack_Mesh
- **31 clips** (3ds Max CAT (humanoid), 59 bones) -> plays on: Solder_Mesh
  - (aiming)Dead, (aiming)Down, (aiming)Get_Hit, (aiming)Idle, (aiming)Jump, (aiming)Left, (aiming)Recharge, (aiming)Right, (aiming)Run, (aiming)Run_Back, (aiming)Run_Left, (aiming)Run_Right, (aiming)Sit_Ide, (aiming)Up, (aiming)Walk, (aiming)Walk_Back, (aiming)Walk_Back_Sit, (aiming)Walk_Left, (aiming)Walk_Left_Sit, (aiming)Walk_Right, (aiming)Walk_Right_Sit, (aiming)Walk_Sit, (aiming)_Single_Shot, Dead, Get_Hit, Idle, Jump, Run, Sit_Idle, Sit_Walk, Walk
- **5 clips** (3ds Max CAT (creature), 23 bones) -> plays on: Dog_Mesh
  - Dead, Get_Hit, Idle, Run, Walk
- No clips of their own: BackPack_Mesh, Diver_2_Mesh, Diver_Mesh, Elite_Soldier_Mesh, Investigator_Mesh, PBR_Soldier_Mesh_humanoid, Policeman_Mash, Soldier, Soldier_Gas_Mesh, Soldier_Marine_2, Soldier_Marine_Mesh, Soldier_Sapper, Soldier_Women_Mesh
- Static meshes (44): Armored_Box_Mesh, Arrow_Mesh, Automatic_Gun_Mesh, Automatic_Gun_Sleve_Mesh, Automatic_Rifle_05_Mesh, Automatic_Rifle_Mesh, Automatic_Rifle_Mesh01, Automatic_Rifle_Mesh02, Automatic_Rifle_Mesh03, Automatic_Rifle_Mesh04, Automatic_Rifle_Sleve_Mesh01, Automatic_Rifle_Sleve_Mesh03, Axe_Mesh, Drone_Mesh, Ferst_aid_mesh, Flashlight_Mesh, Grenade_Mesh, Grenade_gun_Mesh, Gun_02_Mesh, Gun_02_Sleeve_Mesh, Gun_03_Mesh, Gun_Mesh, Gun_Sleve_Mesh, Knife_Mesh, Rifle_Sleve_Mesh, Rocket_Mesh, Shotgun_Mesh, Shotgun_Sleve_Mesh, Sleeve_Mesh, Sniper_Rifle_02_Mesh ...

### Monster In Capsule
- **UE Mannequin-style** models (2; auto-retargets with UE5 mannequin animations): Monster_For_Capsule, NPC_Scientist
- **7 clips** (UE Mannequin-style, 60 bones) -> plays on: Monster_For_Capsule, NPC_Scientist; also fits models in: Fantasy Animal Pack (1)
  - Capsule, Idle_01, Idle_02, Idle_03, Idle_04, Idle_05, Idle_06
- Static meshes (8): Monster_Capsule_Basic, Monster_Capsule_Cable_01, Monster_Capsule_Cable_02, Monster_Capsule_Computer, Monster_Capsule_Detail, Monster_Capsule_Full, NPC_Scientist_Tablet, Tablet

### Monsters Underwater Pack
- **UE Mannequin-style** models (5; auto-retargets with UE5 mannequin animations): Monster_Underwater_01_Mesh, Monster_Underwater_02_Mesh, Monster_Underwater_03_Mesh, Monster_Underwater_04_Mesh, Monster_Underwater_05_Mesh
- **33 clips** (UE Mannequin-style, 61 bones) -> plays on: Monster_Underwater_02_Mesh, Monster_Underwater_03_Mesh, Monster_Underwater_04_Mesh; also fits models in: Fantasy Animal Pack (1)
  - Attack_1, Attack_10, Attack_2, Attack_3, Attack_4, Attack_5, Attack_6, Attack_7, Attack_8, Attack_9, Dead_1, Dead_2, Dead_3, Dead_4, Get_Hit, Get_Hit_Back, Get_Hit_Left, Get_Hit_Right, Idle_1, Idle_2, Jump, Run, Run_Back, Run_Left, Run_Right, Shout_1, Shout_2, Turn_Right, Walk, Walk_Back, Walk_Left, Walk_Right, urn_Left
- **8 clips** (UE Mannequin-style, 60 bones) -> plays on: Monster_Underwater_01_Mesh, Monster_Underwater_02_Mesh, Monster_Underwater_03_Mesh, Monster_Underwater_04_Mesh, Monster_Underwater_05_Mesh; also fits models in: Fantasy Animal Pack (1)
  - Run_Back_Root, Run_Left_Root, Run_Right_Root, Run_Root, Walk_Back_Root, Walk_Left_Root, Walk_Right_Root, Walk_Root

### NPC Beggars Pack
- **UE Mannequin-style** models (7; auto-retargets with UE5 mannequin animations): NPC_Beggar_01, NPC_Beggar_02, NPC_Beggar_03, NPC_Beggar_04, NPC_Beggar_05, NPC_Beggar_06, NPC_Beggar_07
- **19 clips** (UE Mannequin-style, 60 bones) -> plays on: NPC_Beggar_01, NPC_Beggar_02, NPC_Beggar_03, NPC_Beggar_04, NPC_Beggar_05, NPC_Beggar_06, NPC_Beggar_07; also fits models in: Fantasy Animal Pack (1)
  - Dead_01, Get_Hit_01, Get_Hit_02, Idle_01, Idle_02, Idle_03, Idle_04, Idle_05, Idle_06, Idle_07, Idle_08, Jump, Jump_End, Jump_Loop, Jump_Start, Run, Run_Root, Walk, Walk_Root
- Static meshes (23): NPC_Beggar_02_Pot, NPC_Beggar_02_Rag_01, NPC_Beggar_02_Rag_02, NPC_Beggar_02_Stones, NPC_Beggar_04_Block, NPC_Beggar_05_Bonfire, NPC_Beggar_05_Branch_01, NPC_Beggar_05_Branch_02, NPC_Beggar_05_Branch_03, NPC_Beggar_05_Coffin, NPC_Beggar_05_Rag, NPC_Beggar_05_Rat, NPC_Beggar_05_Stone, NPC_Beggar_05_Tombstone, NPC_Beggar_07_Coin, NPC_Beggar_07_Cup, NPC_Beggar_Arm_in_the_plate, NPC_Beggar_Blood_in_the_plate, NPC_Beggar_Coin, NPC_Beggar_Crutch_03_01, NPC_Beggar_Mug, NPC_Beggar_Plate, NPC_Beggar_Pot

### NPC Characters Female Pack
- **UE Mannequin-style** models (5; auto-retargets with UE5 mannequin animations): NPC_Character_female_01, NPC_Character_female_02, NPC_Character_female_03, NPC_Character_female_04, NPC_Character_female_05
- No clips of their own: NPC_Character_female_01, NPC_Character_female_02, NPC_Character_female_03, NPC_Character_female_04, NPC_Character_female_05

### NPC Characters Male Pack
- **UE Mannequin-style** models (3; auto-retargets with UE5 mannequin animations): NPC_Character_03, NPC_Character_04, NPC_Character_05
- No clips of their own: NPC_Character_03, NPC_Character_04, NPC_Character_05
- Static meshes (2): NPC_Character_01, NPC_Character_02

### NPC Charaters Kids Pack
- **UE Mannequin-style** models (5; auto-retargets with UE5 mannequin animations): NPC_Kid_01, NPC_Kid_02, NPC_Kid_03, NPC_Kid_04, NPC_Kid_05
- No clips of their own: NPC_Kid_01, NPC_Kid_02, NPC_Kid_03, NPC_Kid_04, NPC_Kid_05

### NPC Dystopia Characters
- **UE Mannequin-style** models (1; auto-retargets with UE5 mannequin animations): NPC_Distopia
- No clips of their own: NPC_Distopia

### NPC King And Queen
- **UE Mannequin-style** models (5; auto-retargets with UE5 mannequin animations): NPC_Executioner, NPC_King, NPC_Plague_doctor, NPC_Queen, NPC_Servant
- No clips of their own: NPC_Executioner, NPC_King, NPC_Plague_doctor, NPC_Queen, NPC_Servant
- Static meshes (2): NPC_Executioner_Axe, NPC_Plague_doctor_Walking_stick

### NPC Prisoners
- **UE Mannequin-style** models (2; auto-retargets with UE5 mannequin animations): Prisoners_Fem, Prisoners_Man
- No clips of their own: Prisoners_Fem, Prisoners_Man

### NPC Sailor Adventure
- **UE Mannequin-style** models (7; auto-retargets with UE5 mannequin animations): NPC_Sailor_Custom_01, NPC_Sailor_Custom_02, NPC_Sailor_Custom_03, NPC_Sailor_Custom_04, NPC_Sailor_Custom_05, NPC_Sailor_Custom_06, NPC_Sailor_Custom_Full
- **Weapon/prop rig** models (1; own animations only): NPC_Sailor_Custom_Gun_02
- No clips of their own: NPC_Sailor_Custom_01, NPC_Sailor_Custom_02, NPC_Sailor_Custom_03, NPC_Sailor_Custom_04, NPC_Sailor_Custom_05, NPC_Sailor_Custom_06, NPC_Sailor_Custom_Full, NPC_Sailor_Custom_Gun_02
- Static meshes (1): NPC_Sailor_Custom_Gun_01

### Old Gangster
- **UE Mannequin-style** models (1; auto-retargets with UE5 mannequin animations): NPC_Old_gangster
- **1 clips** (UE Mannequin-style, 60 bones) -> plays on: NPC_Old_gangster; also fits models in: Fantasy Animal Pack (1)
  - Walk
- Static meshes (2): NPC_Old_gangster_Bullet, NPC_Old_gangster_Submachine_gun

### Parasites Pack
- **3ds Max CAT (humanoid)** models (5; retarget via manual IK-rig chains): Mesh, Mesh_Alfa
- **11 clips** (3ds Max CAT (humanoid), 71 bones) -> plays on: Mesh
  - All_animations_on_one_timeline, Attack(1), Attack(2), Dead, Get_hit, Idle, Idle_other, Run, Shout, Walk, jump
- **10 clips** (3ds Max CAT (humanoid), 77 bones) -> plays on: Mesh
  - All_animations_on_one_timeline, Attack(1), Attack(2), Dead, Get hit, Run, Shout, Walk, idle, idle_other
- **12 clips** (3ds Max CAT (humanoid), 53 bones) -> plays on: Mesh
  - All_animations_on_one_timeline, Attack(1), Attack(2), Attack(3), Dead, Get_Hit, Idle, Idle_other, Jump, Run, Shout, Walk
- **21 clips** (3ds Max CAT (humanoid), 38 bones) -> plays on: Mesh_Alfa
  - All_animations_on_one_timeline, All_animations_on_one_timeline_1, Attack(1), Attack(1)_1, Attack(2), Attack(2)_1, Attack(3), Attack(Fire)_1, Attack_Fire, Dead, Dead_1, Emergence, Get_Hit_1, Get_hit, Idle, Idle_1, Jump_1, Run_1, Shout, Shout_1, Walk_1
- **11 clips** (3ds Max CAT (humanoid), 67 bones) -> plays on: Mesh
  - All_animations_on_one_timeline, Attack(1), Attack(2), Dead, Get_hit, Jump, Run, Shout, Walk, idle, idle_other
- Static meshes (1): stand2

### Primitive Characters Pack
- **UE Mannequin-style** models (4; auto-retargets with UE5 mannequin animations): Primitive_03, Primitive_04, Primitive_05, Primitive_Character_01
- No clips of their own: Primitive_03, Primitive_04, Primitive_05, Primitive_Character_01
- Static meshes (11): Primitive_02, Primitive_02_Torch, Primitive_02_Weapons_01, Primitive_02_Weapons_02, Primitive_03_Weapon_01, Primitive_03_Weapon_02, Primitive_04_Weapon, Primitive_Weapon_01, Primitive_Weapon_02, Primitive_Weapon_03, Primitive_Weapon_04

### Sci-Fi Characters Pack
- **UE Mannequin-style** models (5; auto-retargets with UE5 mannequin animations): Sci_Fi_Character_01_Mesh, Sci_Fi_Character_02_Mesh, Sci_Fi_Character_03_Mesh, Sci_Fi_Character_04, Sci_Fi_Character_05_Mesh
- **Weapon/prop rig** models (1; own animations only): Sci_Fi_Character_05_Weapon_Mesh
- No clips of their own: Sci_Fi_Character_01_Mesh, Sci_Fi_Character_02_Mesh, Sci_Fi_Character_03_Mesh, Sci_Fi_Character_04, Sci_Fi_Character_05_Mesh, Sci_Fi_Character_05_Weapon_Mesh
- Static meshes (3): Sci_Fi_Character_04_Weapon, Sci_Fi_Sword_01_Mesh, Sci_Fi_Sword_02_Mesh

### Sci-Fi Characters Pack Vol 2
- **UE Mannequin-style** models (7; auto-retargets with UE5 mannequin animations): Defender_Mesh, Omar_Mesh, Sci_Fi_09_Character, Sci_Fi_Character_06_Mesh, Sci_Fi_Character_07, Sci_Fi_Guard, Sci_Fi_Monster_Mesh
- **Weapon/prop rig** models (1; own animations only): Weapon_Mesh
- **78 clips** (UE Mannequin-style, 60 bones) -> plays on: Defender_Mesh, Omar_Mesh, Sci_Fi_09_Character, Sci_Fi_Character_06_Mesh, Sci_Fi_Character_07, Sci_Fi_Guard, Sci_Fi_Monster_Mesh; also fits models in: Fantasy Animal Pack (1)
  - Attack_01, Attack_02, Attack_03, Attack_04, Attack_05, Dead_01, Dead_02, Fly, Fly_Back, Fly_Back_Root, Fly_Dead, Fly_Fast, Fly_Fast_Landing, Fly_Fast_Left, Fly_Fast_Left_Root, Fly_Fast_Right, Fly_Fast_Right_Root, Fly_Fast_Root, Fly_Fast_Start, Fly_Get_Hit, Fly_Get_Hit_Left, Fly_Get_Hit_Right, Fly_Idle, Fly_Landing, Fly_Left, Fly_Left_Root, Fly_Reload, Fly_Right, Fly_Right_Root, Fly_Root, Fly_Rotate_90_45_Down_Left, Fly_Rotate_90_45_Down_Right, Fly_Rotate_90_45_Up_Left, Fly_Rotate_90_45_Up_Right, Fly_Rotate_90_Down, Fly_Rotate_90_Left, Fly_Rotate_90_Right, Fly_Rotate_90_Up, Fly_Shot_01, Fly_Shot_02, Fly_Shot_03, Fly_Start, Get_Hit, Get_Hit_02, Idle_01, Idle_02, Idle_03, Jump, Reload, Rotate_90_45_Down_Left, Rotate_90_45_Down_Right, Rotate_90_45_Up_Left, Rotate_90_45_Up_Right, Rotate_90_Down, Rotate_90_Left, Rotate_90_Right, Rotate_90_Up, Run, Run_Back, Run_Back_Root, Run_Fast, Run_Fast_Root, Run_Left, Run_Left_Root, Run_Right, Run_Right_Root, Run_Root, Shot_01, Shot_02, Shot_03, Walk, Walk_Back, Walk_Back_Root, Walk_Left, Walk_Left_Root, Walk_Right, Walk_Right_Root, Walk_Root
- **1 clips** (Weapon/prop rig, 4 bones) -> plays on: _no model in this pack shares this skeleton_
  - Rotation
- No clips of their own: Weapon_Mesh
- Static meshes (5): Sci_Fi_09_Blade, Sci_Fi_09_Shield, Sci_Fi_Guard_Weapon, Scythe_Mesh, Sleeve_Mesh

### Sci-FI Creocapsule
- **Weapon/prop rig** models (3; own animations only): Creo_Capsule_01, Creo_Capsule_02, Creo_Capsule_Organic_02
- **2 clips** (Weapon/prop rig, 2 bones) -> plays on: _no model in this pack shares this skeleton_
  - Close_Door, Open_Door
- No clips of their own: Creo_Capsule_01, Creo_Capsule_02, Creo_Capsule_Organic_02
- Static meshes (1): Creo_Capsule_Organic_01

### Sci-Fi Experimental
- **1 clips** (Arms-only (FPS), 21 bones) -> plays on: _no model in this pack shares this skeleton_
  - Heads
- **1 clips** (Weapon/prop rig, 21 bones) -> plays on: _no model in this pack shares this skeleton_
  - Bug
- Static meshes (1): Laboratory

### Sci-Fi Hands With Knife Animation
- **UE Mannequin-style** models (1; auto-retargets with UE5 mannequin animations): Sci_Fi_Hands_Full_With_Knife
- **Weapon/prop rig** models (1; own animations only): Sci_Fi_Shield
- **34 clips** (UE Mannequin-style, 94 bones) -> plays on: Sci_Fi_Hands_Full_With_Knife
  - _Attack_01, _Attack_02, _Attack_03, _Attack_04, _Attack_Energy, _Block_Get_Hit, _Get, _Hide, _Idle_01, _Idle_02, _Idle_Block, _Idle_Computer, _Inspection, _Jump, _Jump_End, _Jump_Loop, _Jump_Start, _Run_01, _Run_02, _Shield_Attack_01, _Shield_Attack_02, _Shield_Attack_03, _Shield_Get, _Shield_Get_Hit, _Shield_Hide, _Shield_Idle, _Shield_Jump, _Shield_Jump_End, _Shield_Jump_Loop, _Shield_Jump_Start, _Shield_Run, _Shield_Walk, _Walk_01, _Walk_02
- No clips of their own: Sci_Fi_Shield
- Static meshes (1): Sci_Fi_Knife

### Sci-Fi Line With 3 Creatures
- **UE Mannequin-style** models (1; auto-retargets with UE5 mannequin animations): Creatures
- **Weapon/prop rig** models (2; own animations only): Hooks, Line
- **2 clips** (UE Mannequin-style, 60 bones) -> plays on: Creatures; also fits models in: Fantasy Animal Pack (1)
  - Idle_01, Idle_02
- No clips of their own: Hooks, Line
- Static meshes (4): Stand, Station_Details, Station_Door_01, Station_Door_02

### Sci-Fi Mercenaries Pack
- **UE Mannequin-style** models (13; auto-retargets with UE5 mannequin animations): Head_Hunter, Marauder, Robot_Mesh, Sci_Fi_Worker, Sci_Fi_Worker_Cut_01, Sci_Fi_Worker_Cut_01_Pose_01, Sci_Fi_Worker_Cut_01_Pose_02, Sci_Fi_Worker_Cut_01_Pose_03, Sci_Fi_Worker_Cut_02, Sci_Fi_Worker_Cut_02_Pose_01, Sci_Fi_Worker_Cut_02_Pose_02, Sci_Fi_Worker_Cut_02_Pose_03, Seller
- **Weapon/prop rig** models (5; own animations only): Backpack, Head_Hunter_Gun, Marauder_Rifle_Cartrigde, Marauder_Rifle_Full, Marauder_Rifle_Full_Without_Cartrigde
- No clips of their own: Backpack, Head_Hunter, Head_Hunter_Gun, Marauder, Marauder_Rifle_Cartrigde, Marauder_Rifle_Full, Marauder_Rifle_Full_Without_Cartrigde, Robot_Mesh, Sci_Fi_Worker, Sci_Fi_Worker_Cut_01, Sci_Fi_Worker_Cut_01_Pose_01, Sci_Fi_Worker_Cut_01_Pose_02, Sci_Fi_Worker_Cut_01_Pose_03, Sci_Fi_Worker_Cut_02, Sci_Fi_Worker_Cut_02_Pose_01, Sci_Fi_Worker_Cut_02_Pose_02, Sci_Fi_Worker_Cut_02_Pose_03, Seller
- Static meshes (12): Balon, Bootle, Box, Cloth, Disk, Head_Hunter_Gun_Bullet, Head_Hunter_Gun_Sleeve, Lamp, PC, Pan, Suitcase, Wheel

### Soldier Future 01
- **UE Mannequin-style** models (1; auto-retargets with UE5 mannequin animations): Soldier_Future_01
- **Weapon/prop rig** models (2; own animations only): Automatic_Rifle, Automatic_Rifle_Cartridge
- No clips of their own: Automatic_Rifle, Automatic_Rifle_Cartridge, Soldier_Future_01

### Soldier Future 02
- **UE Mannequin-style** models (1; auto-retargets with UE5 mannequin animations): Soldier_Future_02
- **Weapon/prop rig** models (3; own animations only): Pistol, Pistol_Cartridge, Pistol_Muffler
- No clips of their own: Pistol, Pistol_Cartridge, Pistol_Muffler, Soldier_Future_02

### Soldier Future 03
- **UE Mannequin-style** models (1; auto-retargets with UE5 mannequin animations): Soldier_Future_03
- **Weapon/prop rig** models (2; own animations only): Rocket, Rocket_Launcher_Full
- No clips of their own: Rocket, Rocket_Launcher_Full, Soldier_Future_03

### Tactical Masks
- **UE Mannequin-style** models (10; auto-retargets with UE5 mannequin animations): Gas_mask_01, Gas_mask_02, Gas_mask_04, Gas_mask_05, Masks, Tactical_mask_01, Tactical_mask_02, Tactical_mask_03, Tactical_mask_04, Tactical_mask_05
- No clips of their own: Gas_mask_01, Gas_mask_02, Gas_mask_04, Gas_mask_05, Masks, Tactical_mask_01, Tactical_mask_02, Tactical_mask_03, Tactical_mask_04, Tactical_mask_05
- Static meshes (1): Gas_mask_03

### Underwater odyssey
- **3ds Max Biped** models (3; retarget via manual IK-rig chains): Sailor_02_Mesh, Sailor_2@Idle, Sailor_2@Idle_Other
- **UE Mannequin-style** models (14; auto-retargets with UE5 mannequin animations): All_animations_on_one_timeline, Sailor@Attack(1), Sailor@Attack(2), Sailor@Attack(3), Sailor@Attack(4), Sailor@Dead, Sailor@Get_Hit, Sailor@Idle, Sailor@Idle_Attack, Sailor@Idle_Other, Sailor@Jump, Sailor@Run, Sailor@Walk, Sailor_Mesh
- No clips of their own: All_animations_on_one_timeline, Sailor@Attack(1), Sailor@Attack(2), Sailor@Attack(3), Sailor@Attack(4), Sailor@Dead, Sailor@Get_Hit, Sailor@Idle, Sailor@Idle_Attack, Sailor@Idle_Other, Sailor@Jump, Sailor@Run, Sailor@Walk, Sailor_02_Mesh, Sailor_2@Idle, Sailor_2@Idle_Other, Sailor_Mesh

### Viking Customized
- **UE Mannequin-style** models (18; auto-retargets with UE5 mannequin animations): Viking_01, Viking_02, Viking_03, Viking_04, Viking_05, Viking_06, Viking_07, Viking_08, Viking_09, Viking_10, Viking_11, Viking_12, Viking_13, Viking_14, Viking_15, Viking_16, Viking_17, Viking_Full
- **Weapon/prop rig** models (3; own animations only): Viking_Banner_01, Viking_Banner_02, Viking_Banner_03
- No clips of their own: Viking_01, Viking_02, Viking_03, Viking_04, Viking_05, Viking_06, Viking_07, Viking_08, Viking_09, Viking_10, Viking_11, Viking_12, Viking_13, Viking_14, Viking_15, Viking_16, Viking_17, Viking_Banner_01, Viking_Banner_02, Viking_Banner_03, Viking_Full
- Static meshes (17): Viking_Axe_01, Viking_Axe_02, Viking_Club_01, Viking_Club_02, Viking_Hummer_01, Viking_Hummer_02, Viking_Knife_01, Viking_Knife_02, Viking_Shield_01, Viking_Shield_02, Viking_Shield_03, Viking_Shield_04, Viking_Spear_01, Viking_Spear_02, Viking_Spear_03, Viking_Sword_01, Viking_Sword_02

## Quixel Megascans environments (FBX + 4K textures - all UE5-ready)

Static scanned meshes (no animation). Import the FBX with their texture sets; the Displacement maps drive Nanite tessellation. Unreal-format versions with prebuilt materials are also available through the in-editor Fab tab.

- **African Slate Quarry**: 129 FBX (198 MB), 753 JPG; LODs={'0': 21, '1': 21, '2': 21, '3': 21, '-': 45}; tex res={'4K': 752}; maps={'Normal': 84, 'Ao': 82, 'Bump': 82, 'Cavity': 82, 'Displacement': 82, 'Gloss': 82, 'Roughness': 82, 'Specular': 82}; dirs={'fbx': 129}
- **Bazaar**: 86 FBX (78 MB), 857 JPG; LODs={'-': 86}; tex res={'4K': 856}; maps={'Cavity': 94, 'Displacement': 94, 'Gloss': 94, 'Normal': 94, 'Roughness': 94, 'Specular': 94, 'Bump': 88, 'Basecolor': 86}; dirs={'fbx': 86}
- **Junkyard**: 82 FBX (67 MB), 886 JPG; LODs={'-': 82}; tex res={'4K': 885}; maps={'Cavity': 94, 'Displacement': 94, 'Normal': 94, 'Roughness': 94, 'Specular': 94, 'Bump': 90, 'Ao': 88, 'Basecolor': 82}; dirs={'fbx': 82}
- **Old Mine**: 90 FBX (32 MB), 559 JPG; LODs={'-': 46, '0': 11, '1': 11, '2': 11, '3': 11}; tex res={'4K': 558}; maps={'Normal': 61, 'Ao': 60, 'Cavity': 60, 'Displacement': 60, 'Roughness': 60, 'Specular': 60, 'Bump': 56, 'Gloss': 54}; dirs={'fbx': 90}
- **Roadside Construction**: 60 FBX (29 MB), 666 JPG; LODs={'-': 36, '0': 8, '1': 8, '2': 8}; tex res={'4K': 665}; maps={'Basecolor': 71, 'Normal': 71, 'Cavity': 70, 'Displacement': 70, 'Roughness': 70, 'Specular': 70, 'Ao': 69, 'Bump': 69}; dirs={'fbx': 60}
  - high-detail zip: roadside_construction_high.zip: 795 entries {'': 70, '.jpg': 665, '.fbx': 60}; largest FBX [(2, 'xksldamqx.fbx'), (2, 'xjhteio.fbx'), (1, 'xg1gcdi.fbx')]
- **Saloon Interior**: 57 FBX (34 MB), 630 JPG; LODs={'-': 57}; tex res={'4K': 629}; maps={'Roughness': 70, 'Specular': 69, 'Ao': 68, 'Cavity': 68, 'Displacement': 68, 'Normal': 68, 'Bump': 66, 'Gloss': 64}; dirs={'fbx': 57}
- **Unfinished Building**: 38 FBX (16 MB), 646 JPG; LODs={'-': 38}; tex res={'4K': 645}; maps={'Specular': 78, 'Ao': 70, 'Cavity': 70, 'Displacement': 70, 'Gloss': 70, 'Normal': 70, 'Roughness': 70, 'Bump': 61}; dirs={'fbx': 38}
- **Warehouse**: 56 FBX (45 MB), 771 JPG; LODs={'-': 56}; tex res={'4K': 770}; maps={'Basecolor': 85, 'Specular': 85, 'Cavity': 82, 'Normal': 82, 'Roughness': 82, 'Displacement': 81, 'Ao': 78, 'Bump': 78}; dirs={'fbx': 56}
  - high-detail zip: warehouse_high.zip: 911 entries {'': 85, '.jpg': 770, '.fbx': 56}; largest FBX [(9, 'wbslaikga.fbx'), (2, 'wdqqeae.fbx'), (2, 'tlbjdbova.fbx')]
