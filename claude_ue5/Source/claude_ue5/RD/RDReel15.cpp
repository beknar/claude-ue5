// The reel of 2026-11-18 (the user's: "use windows game bar to make a demo reel showing off all six towns using a different
// character for each one, then show off a combat at Tier 3 using a full Tier 3 character for each character, fighting different
// enemies, then show off a wilderness encounter with all characters. Use captions that describe what's being seen for each scene
// that is out of the way of the action"; then "build this reel with voice-over narrating the scenes").
// A pilot over three levels' generators (Brokenspire's wilds, Mistward Castle, the wilds again), its stage kept in the game
// instance: the six towns, a hero each (in through the gate, then the landmark over its dungeon); in the castle's third tier each
// hero in balance6.json's tier-3 kit against a pack of her own kind of monster (the game's autoplay plays her); in the wilds round
// Brokenspire each hero met by an encounter of the director's roaming kinds. Each scene's caption is drawn at the top of the screen
// (ARDHUD::DrawReelCaption); its narration's words go into the timeline (the done file) for the voice-over mixed in afterwards
// (pipeline/blender_numpy/reel15_cut.py). In the packaged game: -RDReel15 [-RDShowReady=<file>] [-RDShowGo=<file>]
// [-RDShowDone=<file>] (the recorder's files: ready once Brokenspire stands, the go when the recording runs, done at the end, with
// the timeline: "<seconds from the go>|scene|<name>|<title>|<line>|<narration>", "<s>|end|<name>", "<s>|note|<what>");
// in play from Python: StartReel15 (a rehearsal; Go empty: at once; bShots: a HighResShot in each scene).
#include "RD/RDDungeonGenerator.h"
#include "RD/RDSection.h"
#include "RD/RDCombat.h"
#include "RD/RDMonster.h"
#include "RD/RDWild.h"
#include "RD/RDGameInstance.h"
#include "GameFramework/Character.h"
#include "GameFramework/CharacterMovementComponent.h"
#include "GameFramework/PlayerController.h"
#include "Kismet/GameplayStatics.h"
#include "Kismet/KismetSystemLibrary.h"
#include "Misc/FileHelper.h"
#include "Misc/Paths.h"
#include "Misc/CommandLine.h"
#include "Misc/Parse.h"
#include "Misc/App.h"
#include "Engine/World.h"

DEFINE_LOG_CATEGORY_STATIC(LogRDReel15, Log, All);

namespace
{
	// (the stages: 0-5 the towns, 6-11 the castle's fights, 12-17 the wilds' encounters, 18 the end)
	constexpr int32 RD15Towns = 0, RD15Fights = 6, RD15Wilds = 12, RD15End = 18;
	const TCHAR* RD15Hero[6] = { TEXT("Warrior"), TEXT("Mage"), TEXT("Warlock"), TEXT("Rogue"), TEXT("Summoner"), TEXT("MartialArtist") };
	const TCHAR* RD15HeroWho[6] = { TEXT("the Warrior"), TEXT("the Mage"), TEXT("the Warlock"), TEXT("the Rogue"), TEXT("the Summoner"), TEXT("the Martial Artist") };
	const TCHAR* RD15City[6] = { TEXT("Brokenspire"), TEXT("Vel Morrath"), TEXT("Ashenreach"), TEXT("Graymourne"), TEXT("Kethrys Spire"), TEXT("Heaven") };
	const float RD15CityHour[6] = { 10.5f, 11.f, 12.f, 11.5f, 12.5f, 13.f };
	// (each town's two shots: in through its gate, then its landmark over the way down into its dungeon (MistgateAt))
	const TCHAR* RD15LineA[6] = {
		TEXT("The starting town: in through the gate along the cobbled main road"),
		TEXT("The holy city in the mountains: its pale stone streets"),
		TEXT("The forge city at the edge of a burned plain: soot-dark stone"),
		TEXT("The fog-bound port: its streets in the sea fog"),
		TEXT("The mage city among the glaciers"),
		TEXT("The modern city by the volcano: towers, streets and traffic") };
	const TCHAR* RD15SayA[6] = {
		TEXT("Six towns, six heroes. First, Brokenspire, the starting town. The Warrior walks in along the cobbled main road."),
		TEXT("Vel Morrath, the holy city in the mountains, with the Mage. Pale stone streets lead to its heart."),
		TEXT("Ashenreach, the forge city on the edge of a burned plain. The Warlock walks its soot dark streets."),
		TEXT("Graymourne, the fog bound port. The Rogue slips in through the sea fog."),
		TEXT("Kethrys Spire, the mage city among the glaciers, with the Summoner."),
		TEXT("And Heaven, the modern city by the volcano. The Martial Artist walks among its towers.") };
	const TCHAR* RD15LineB[6] = {
		TEXT("Mistward Castle at the town's far end: its Mistgate opens on the dungeon"),
		TEXT("The cathedral at its middle: beneath the altar, a stair down to the catacombs"),
		TEXT("The foundry at its heart: its gate leads down into The War Engine"),
		TEXT("The sluice house over the way down into the sewers"),
		TEXT("The black tower, 69 m tall: its dungeon is inside it"),
		TEXT("The fortress at its middle, held by defenders with firearms") };
	const TCHAR* RD15SayB[6] = {
		TEXT("At the far end stands Mistward Castle. Its Mistgate opens on the dungeon, five tiers deep."),
		TEXT("Its cathedral stands at the middle. A stair beneath the altar leads down into the catacombs."),
		TEXT("The great foundry stands at its heart. Its gate leads down into the War Engine, a dungeon of machines."),
		TEXT("The sluice house guards the way down into the sewers, where the drowned wait."),
		TEXT("Its black tower rises almost seventy metres over the roofs. The tower's dungeon is inside it."),
		TEXT("At its middle stands the fortress, held by troopers with firearms: the deepest dungeon of all.") };
	// (balance6.json's kits for a hero arriving at tier 3 (880's balance; 868's balance step plays them), and the tier's potions,
	// two of each, as 868's kit(); the Rogue without its Ember Slash (ApplySlash refused it on her own weapons))
	struct FRD15Kit { const TCHAR* Weapon; const TCHAR* Armour; const TCHAR* Shield; const TCHAR* Ring1; const TCHAR* Ring2; const TCHAR* Slash; const TCHAR* Tomes; };
	const FRD15Kit RD15Kit[6] = {
		{ TEXT("Templar Sword"), TEXT("Crocodile Warrior’s Armour"), TEXT("Heraldic Shield"), TEXT("HP Potency Ring 4"), nullptr, TEXT("Ember Slash"), nullptr },
		{ nullptr, nullptr, nullptr, TEXT("Magic Potency Ring 4"), nullptr, nullptr, TEXT("Frost Shard,Ash Ward,Bone Spear,Chain Lightning,Iron Skin") },
		{ nullptr, TEXT("Crocodile Warrior’s Armour"), nullptr, TEXT("HP Potency Ring 4"), nullptr, nullptr, TEXT("Frost Shard,Bone Spear,Chain Lightning") },
		{ nullptr, TEXT("Orc Bruiser’s Armour"), nullptr, TEXT("Dexterity Ring 4"), nullptr, nullptr, nullptr },
		{ nullptr, nullptr, nullptr, TEXT("Magic Potency Ring 4"), nullptr, nullptr, nullptr },
		{ nullptr, TEXT("Desert Hero’s Armour"), nullptr, TEXT("HP Potency Ring 4"), TEXT("Dexterity Ring 4"), nullptr, nullptr } };
	const TCHAR* RD15Potions[3] = { TEXT("Rare Healing Potion"), TEXT("Rare Mana Potion"), TEXT("Rare Speed Potion") };
	// (how each fights, for the narration)
	const TCHAR* RD15Way[6] = {
		TEXT("with the Templar Sword and the Ember Slash"),
		TEXT("with Frost Shard, Bone Spear and Chain Lightning"),
		TEXT("with her blade and her spells"),
		TEXT("from stealth, with crossbow and daggers"),
		TEXT("calling her summons to fight beside her"),
		TEXT("with fists, kicks and chi") };
	const float RD15ShotA = 11.f, RD15ShotB = 12.f, RD15FightMin = 15.f, RD15FightMax = 55.f;
	float RD15Ease(float T) { T = FMath::Clamp(T, 0.f, 1.f); return T * T * (3.f - 2.f * T); }
	/** a kind's name as words ("SkeletonWarrior" -> "Skeleton Warrior") */
	FString RD15Words(const FString& S)
	{
		FString O;
		for (int32 I = 0; I < S.Len(); ++I)
		{
			const TCHAR C = S[I];
			if (C == TEXT('_')) { O += TEXT(' '); continue; }
			if (I > 0 && FChar::IsUpper(C) && FChar::IsLower(S[I - 1])) O += TEXT(' ');
			O += C;
		}
		return O;
	}
	FString RD15Plural(const FString& S)
	{
		if (S.EndsWith(TEXT("man"))) return S.LeftChop(3) + TEXT("men");
		if (S.EndsWith(TEXT("f"))) return S.LeftChop(1) + TEXT("ves");
		if (S.EndsWith(TEXT("y")) && S.Len() > 1 && !FString(TEXT("aeiou")).Contains(FString(1, &S[S.Len() - 2]))) return S.LeftChop(1) + TEXT("ies");
		if (S.EndsWith(TEXT("s")) || S.EndsWith(TEXT("x")) || S.EndsWith(TEXT("ch")) || S.EndsWith(TEXT("sh"))) return S + TEXT("es");
		return S + TEXT("s");
	}
	const TCHAR* RD15Count[7] = { TEXT("no"), TEXT("one"), TEXT("two"), TEXT("three"), TEXT("four"), TEXT("five"), TEXT("six") };
}

void ARDDungeonGenerator::StartReel15(const FString& Go, const FString& Done, bool bShots, int32 FromStage)
{
	URDGameInstance* GI = URDGameInstance::Of(this);
	if (!GI) return;
	GI->bReelRead = true; GI->bReel = true; GI->ReelStage = FMath::Clamp(FromStage, 0, 18); GI->ReelGo = Go; GI->ReelDone = Done; GI->bReelShots = bShots;
	GI->bReelGoing = false; GI->ReelLog.Reset(); GI->ReelRescues = 0;
	Reel15Sub = 0; Reel15T = 0.f; bReel15Travel = false;
	UE_LOG(LogRDReel15, Log, TEXT("RDREEL15 armed (go %s)"), Go.IsEmpty() ? TEXT("at once") : *Go);
}

FString ARDDungeonGenerator::GetReel15State() const
{
	const URDGameInstance* GI = URDGameInstance::Of(this);
	if (!GI) return TEXT("no game instance");
	return FString::Printf(TEXT("%d|%d|%d|%.1f|%d|%s"), GI->bReel ? 1 : 0, GI->ReelStage, Reel15Sub, Reel15T, GI->ReelRescues, GI->ReelLog.Num() > 0 ? *GI->ReelLog.Last() : TEXT(""));
}

void ARDDungeonGenerator::Reel15Mark(const FString& What)
{
	URDGameInstance* GI = URDGameInstance::Of(this);
	if (!GI) return;
	const FString L = FString::Printf(TEXT("%.2f|%s"), FPlatformTime::Seconds() - GI->ReelT0, *What);
	GI->ReelLog.Add(L);
	UE_LOG(LogRDReel15, Log, TEXT("RDREEL15 %s"), *L);
}

void ARDDungeonGenerator::Reel15Scene(const FString& Name, const FString& Title, const FString& Line, const FString& Say)
{
	ReelCaptionTitle = Title; ReelCaptionLine = Line;
	Reel15SceneName = Name;
	Reel15Mark(FString::Printf(TEXT("scene|%s|%s|%s|%s"), *Name, *Title.Replace(TEXT("|"), TEXT("/")), *Line.Replace(TEXT("|"), TEXT("/")), *Say.Replace(TEXT("|"), TEXT("/"))));
}

void ARDDungeonGenerator::Reel15End()
{
	if (Reel15SceneName.IsEmpty()) return;
	Reel15Mark(TEXT("end|") + Reel15SceneName);
	Reel15SceneName.Reset();
	ReelCaptionTitle.Reset(); ReelCaptionLine.Reset();
}

void ARDDungeonGenerator::Reel15Shot(const FString& Name)
{
	URDGameInstance* GI = URDGameInstance::Of(this);
	if (!GI || !GI->bReelShots) return;
#if !UE_BUILD_SHIPPING
	UKismetSystemLibrary::ExecuteConsoleCommand(this, TEXT("HighResShot 1280x720"), UGameplayStatics::GetPlayerController(this, 0));
	Reel15Mark(TEXT("shot|") + Name);
#endif
}

void ARDDungeonGenerator::Reel15Switch(int32 K)
{
	// (the last hero's summons go with her, and nothing she carried is the next one's)
	StopAutoplay(TEXT("the reel's next hero"));
	for (ARDMonster* A : GetAllies()) if (IsValid(A)) A->Destroy();
	CarrySummons.Reset(); CarrySummonShares.Reset();
	const bool bOk = SwitchHero(FName(RD15Hero[K]));
	Reel15Mark(FString::Printf(TEXT("note|hero %s%s"), RD15Hero[K], bOk ? TEXT("") : TEXT(" REFUSED")));
}

FString ARDDungeonGenerator::Reel15Kit(int32 K, int32 Part)
{
	URDCombatComponent* Pc = PlayerCombat;
	if (!Pc) return FString();
	const FRD15Kit& Kt = RD15Kit[K];
	TArray<FString> Got, Missing;
	auto Has = [&](const TCHAR* N) { return N && FindItem(FName(N)) >= 0; };
	if (Part == 0)
	{
		Pc->ClearItems();
		for (const TCHAR* R : { Kt.Ring1, Kt.Ring2 }) if (R) { if (Has(R)) { Pc->AddItem(FName(R), 1); if (Pc->WearRing(FName(R))) Got.Add(R); else Missing.Add(FString(R) + TEXT(" (refused)")); } else Missing.Add(R); }
		if (Kt.Armour) { if (Has(Kt.Armour)) { Pc->AddItem(FName(Kt.Armour), 1); if (Pc->WearArmour(FName(Kt.Armour))) Got.Add(Kt.Armour); else Missing.Add(FString(Kt.Armour) + TEXT(" (refused)")); } else Missing.Add(Kt.Armour); }
		if (Kt.Shield) { if (Has(Kt.Shield)) { Pc->AddItem(FName(Kt.Shield), 1); if (Pc->WearShield(FName(Kt.Shield))) Got.Add(Kt.Shield); else Missing.Add(FString(Kt.Shield) + TEXT(" (refused)")); } else Missing.Add(Kt.Shield); }
		if (Kt.Tomes)
		{
			TArray<FString> Ts; FString(Kt.Tomes).ParseIntoArray(Ts, TEXT(","));
			for (const FString& T : Ts)
			{
				const FName Tome(*(TEXT("Tome of ") + T));
				if (FindItem(Tome) < 0) { Missing.Add(Tome.ToString()); continue; }
				Pc->AddItem(Tome, 1);
				if (Pc->KnowsSpell(FName(*T))) Got.Add(T); else Missing.Add(T + TEXT(" (not learned)"));
			}
		}
		if (const FRDHeroDef* H = FindHero(CurrentHero); H && H->LockedWeapons.Num() > 0) { const int32 N = UnlockHeroWeapons(H->UnlockPerBoss * 2); Got.Add(FString::Printf(TEXT("%d locked arts"), N)); }
		for (const TCHAR* P : RD15Potions) { if (Has(P)) Pc->AddItem(FName(P), 2); else Missing.Add(P); }
		if (Kt.Weapon) { if (Has(Kt.Weapon)) Pc->AddItem(FName(Kt.Weapon), 1); else Missing.Add(Kt.Weapon); }
	}
	else
	{
		int32 Wi = -1;
		if (Kt.Weapon)
		{
			const FName W(Kt.Weapon);
			Wi = Weapons.IndexOfByPredicate([W](const FRDWeaponDef& D) { return D.Item == W; });
			if (Wi >= 0) { Pc->SelectWeapon(Wi); Got.Add(Kt.Weapon); } else Missing.Add(FString(Kt.Weapon) + TEXT(" (no weapon)"));
		}
		if (Kt.Slash)
		{
			if (Wi < 0) Wi = Weapons.IndexOfByPredicate([](const FRDWeaponDef& D) { return !D.bScroll && (!D.bSpell || D.BoltMesh); });
			if (Wi >= 0 && Has(Kt.Slash)) { Pc->AddItem(FName(Kt.Slash), 1); if (Pc->ApplySlash(FName(Kt.Slash), Wi)) Got.Add(FString::Printf(TEXT("%s on %s"), Kt.Slash, *Weapons[Wi].Name.ToString())); else Missing.Add(FString(Kt.Slash) + TEXT(" (refused)")); }
			else Missing.Add(Kt.Slash);
		}
		Pc->SetHealth(Pc->GetMaxHealth()); Pc->SetMana(Pc->GetMaxMana()); Pc->SetDexEnergy(Pc->GetMaxDexEnergy());
		Got.Add(FString::Printf(TEXT("%.0f hp"), Pc->GetMaxHealth()));
	}
	const FString Out = FString::Join(Got, TEXT(", ")) + (Missing.Num() > 0 ? TEXT(" | MISSING ") + FString::Join(Missing, TEXT(", ")) : FString());
	Reel15Mark(FString::Printf(TEXT("note|kit %s %d: %s"), RD15Hero[K], Part, *Out));
	return Out;
}

void ARDDungeonGenerator::Reel15Camera(float Dt, float Pitch)
{
	APlayerController* PC = UGameplayStatics::GetPlayerController(this, 0);
	APawn* Her = PC ? PC->GetPawn() : nullptr;
	if (!Her) return;
	// (over her shoulder toward the middle of her and the foes still standing near: the fight in the frame)
	const FVector L = Her->GetActorLocation();
	FVector C = L; int32 N = 1;
	for (const TWeakObjectPtr<ARDMonster>& M : Reel15Foes)
		if (M.IsValid() && !M->IsDead() && FVector::Dist2D(M->GetActorLocation(), L) < 3000.f) { C += M->GetActorLocation(); ++N; }
	C /= (float)N;
	const FVector D = (C - L) * FVector(1, 1, 0);
	const float Want = D.Size() > 60.f ? D.Rotation().Yaw : Her->GetActorRotation().Yaw;
	const FRotator R = FMath::RInterpTo(PC->GetControlRotation(), FRotator(Pitch, Want, 0.f), Dt, 2.2f);
	PC->SetControlRotation(FRotator(R.Pitch, R.Yaw, 0.f));
}

void ARDDungeonGenerator::TickReel15(float RealDt)
{
	URDGameInstance* GI = URDGameInstance::Of(this);
	if (!GI) return;
	// (the command line, once a game)
	if (!GI->bReelRead)
	{
		GI->bReelRead = true;
		if (FParse::Param(FCommandLine::Get(), TEXT("RDReel15")))
		{
			FString Go, Done, Ready;
			FParse::Value(FCommandLine::Get(), TEXT("RDShowGo="), Go); FParse::Value(FCommandLine::Get(), TEXT("RDShowDone="), Done); FParse::Value(FCommandLine::Get(), TEXT("RDShowReady="), Ready);
			StartReel15(Go, Done, false, 0); GI->ReelReady = Ready;
		}
	}
	if (!GI->bReel) return;
	APlayerController* PC = UGameplayStatics::GetPlayerController(this, 0);
	ACharacter* Her = PC ? Cast<ACharacter>(PC->GetPawn()) : nullptr;
	if (!PC) return;
	const float Dt = FMath::Min(RealDt, 0.1f);
	Reel15T += Dt;
	int32& Stage = GI->ReelStage;
	auto Next = [this](int32 Sub) { Reel15Sub = Sub; Reel15T = 0.f; };
	// ---- ready (Brokenspire built round her, the wilds ready) and the go
	if (!GI->bReelGoing)
	{
		const ARDSection* S0 = GetSection(FIntPoint::ZeroValue);
		if (!(bTown && bWild && IsWildReady() && S0 && !S0->IsBuilding() && PlayerCombat && bTownPlaced && Her)) { Reel15T = 0.f; return; }
		if (Reel15T < 3.f) return;
		if (!GI->ReelReady.IsEmpty() && !FPaths::FileExists(GI->ReelReady)) FFileHelper::SaveStringToFile(TEXT("ready"), *GI->ReelReady);
		if (!GI->ReelGo.IsEmpty() && !FPaths::FileExists(GI->ReelGo)) return;
		GI->bReelGoing = true; GI->ReelT0 = FPlatformTime::Seconds();
		bAutoplayIgnorePlayer = true;          // (Game Bar's Win+Alt+R reaches the game)
		Reel15Mark(TEXT("note|go"));
		Next(0);
	}
	if (!Her) return;
	// (nothing of the director's own while the reel runs: its scenes are the reel's)
	if (bWild && GetWorld()) WildLastEngaged = GetWorld()->GetTimeSeconds();
	// ================================================================ the six towns
	if (Stage < RD15Fights)
	{
		const int32 K = Stage;
		if (!bTown || !bWild) return;
		ARDSection* S = GetSection(FIntPoint::ZeroValue);
		if (Reel15Sub == 0)
		{
			if (CurrentHero != FName(RD15Hero[K])) { if (Reel15T > 0.5f) { Reel15Switch(K); Reel15T = 0.f; } return; }
			if (!PlayerCombat || Reel15T < 1.5f) return;
			if (TownName != RD15City[K])
			{
				if (!bReel15Travel)
				{
					bReel15Travel = true; bTravelForced = true;
					const bool bOk = WildTravelToTown(RD15City[K]);
					bTravelForced = false;
					Reel15Mark(FString::Printf(TEXT("note|travel to %s%s"), RD15City[K], bOk ? TEXT("") : *(TEXT(" REFUSED: ") + WildTravelRefusal)));
					if (!bOk) { ++Stage; bReel15Travel = false; Next(0); }
				}
				Reel15Ready = 0.f;
				return;
			}
			if (!S || S->IsBuilding() || bTownLoading || !IsWildReady() || bTownTraveling) { Reel15Ready = 0.f; return; }
			Reel15Ready += Dt;
			if (Reel15Ready < 3.f) return;
			SetTownHour(RD15CityHour[K]); SetWeather(1, true);
			PlayerCombat->SetRunMode(true);
			const FVector Gate = S->TownGate, Out = S->TownGateOut.GetSafeNormal2D();
			const FVector Sq = S->LocalToWorld(FIntPoint((S->TownSquare.Min.X + S->TownSquare.Max.X) / 2, (S->TownSquare.Min.Y + S->TownSquare.Max.Y) / 2));
			const FVector Lm = !S->MistgateAt.IsZero() ? S->MistgateAt : Sq;
			const FVector P0 = Gate - Out * 700.f;
			Reel15Path = S->FindPathWorld(P0, Lm);
			if (Reel15Path.Num() == 0) Reel15Path.Add(Lm);
			// (the landmark's shot: from the open ground 40 to 70 m off it, the landmark's face and top in sight from her eyes and the
			// camera's room behind her. The first rehearsal took a point of the way in 32 m off: the way runs on into the building, and
			// it stood her in Brokenspire's castle hall among its guards, in Vel Morrath's cathedral and before five walls)
			Reel15B = FVector::ZeroVector;
			{
				FCollisionQueryParams Qv(SCENE_QUERY_STAT(RDReel15View), false, Her);
				FCollisionObjectQueryParams Ov; Ov.AddObjectTypesToQuery(ECC_WorldStatic); Ov.AddObjectTypesToQuery(ECC_WorldDynamic);
				const float Z0 = S->GetActorLocation().Z;
				float Best = -MAX_flt;
				TArray<FVector> Cands;
				for (const FVector& Pp : Reel15Path) Cands.Add(Pp);
				for (int32 Ai = 0; Ai < 24; ++Ai)
					for (const float Rr : { 4000.f, 5000.f, 6000.f, 7000.f })
					{
						const float An = FMath::DegreesToRadians(Ai * 15.f);
						Cands.Add(Lm + FVector(FMath::Cos(An), FMath::Sin(An), 0.f) * Rr);
					}
				for (const FVector& C0 : Cands)
				{
					const float D = FVector::Dist2D(C0, Lm);
					if (D < 3500.f || D > 7500.f || S->RoomAt(C0) >= 0 || !S->InsideTownBorder(FVector2D(C0)) || !IsInTownWalls(C0)) continue;
					const FVector G(C0.X, C0.Y, Z0 + S->TownLiftAt(FVector2D(C0)));
					const FVector Eye = G + FVector(0, 0, 170.f), Back = (G - Lm).GetSafeNormal2D();
					// (nothing standing on the spot itself: a cart, a stall, a tree)
					if (GetWorld()->LineTraceTestByObjectType(G + FVector(0, 0, 250.f), G + FVector(0, 0, 40.f), Ov, Qv)) continue;
					float Sc = -FMath::Abs(D - 5000.f) * 0.3f;
					if (GetWorld()->LineTraceTestByObjectType(Eye, Lm + FVector(0, 0, 600.f), Ov, Qv)) Sc -= 3000.f;
					if (GetWorld()->LineTraceTestByObjectType(Eye, Lm + FVector(0, 0, 1800.f), Ov, Qv)) Sc -= 1500.f;
					if (GetWorld()->LineTraceTestByObjectType(Eye, G + Back * 500.f + FVector(0, 0, 260.f), Ov, Qv)) Sc -= 4000.f;
					if (Sc > Best) { Best = Sc; Reel15B = C0; }
				}
				Reel15Mark(FString::Printf(TEXT("note|%s's landmark seen from %.0f m (score %.0f)"), RD15City[K], Reel15B.IsZero() ? 0.f : FVector::Dist2D(Reel15B, Lm) / 100.f, Best));
			}
			if (Reel15B.IsZero()) Reel15B = Lm + (Gate - Lm).GetSafeNormal2D() * 4500.f;
			Reel15A = Lm;
			auto PutTown = [&](const FVector& P, const FVector& LookAt, float Pitch)
			{
				const float Z = S->GetActorLocation().Z + S->TownLiftAt(FVector2D(P)) + 100.f;
				const float Yaw = (LookAt - P).Rotation().Yaw;
				Her->SetActorLocation(FVector(P.X, P.Y, Z), false, nullptr, ETeleportType::TeleportPhysics);
				Her->SetActorRotation(FRotator(0.f, Yaw, 0.f)); Her->GetCharacterMovement()->StopMovementImmediately();
				PC->SetControlRotation(FRotator(Pitch, Yaw, 0.f));
			};
			PutTown(P0, Reel15Path[0], -6.f);
			Reel15Scene(FString::Printf(TEXT("town%d_gate"), K), FString::Printf(TEXT("%s  -  %s"), *FString(RD15City[K]).ToUpper(), *FString(RD15HeroWho[K]).ToUpper()), RD15LineA[K], RD15SayA[K]);
			Next(1);
			return;
		}
		if (!S) return;
		if (Reel15Sub == 1)
		{
			// (in along the way, running; the view eased round to where she goes; never on into the landmark's way down)
			while (Reel15Path.Num() > 1 && FVector::Dist2D(Reel15Path[0], Her->GetActorLocation()) < 150.f) Reel15Path.RemoveAt(0);
			const FVector To = Reel15Path[0];
			const FVector D = (To - Her->GetActorLocation()).GetSafeNormal2D();
			if (FVector::Dist2D(Her->GetActorLocation(), Reel15A) > 2500.f && S->RoomAt(To) < 0 && !D.IsNearlyZero()) Her->AddMovementInput(D, 1.f);
			if (!D.IsNearlyZero()) { const FRotator R = FMath::RInterpTo(PC->GetControlRotation(), FRotator(-6.f, D.Rotation().Yaw, 0.f), Dt, 2.f); PC->SetControlRotation(FRotator(R.Pitch, R.Yaw, 0.f)); }
			if (Reel15T > 5.f && Reel15T - Dt <= 5.f) Reel15Shot(Reel15SceneName);
			if (Reel15T >= RD15ShotA)
			{
				Reel15End();
				const float Z = S->GetActorLocation().Z + S->TownLiftAt(FVector2D(Reel15B)) + 100.f;
				const float Yaw = (Reel15A - Reel15B).Rotation().Yaw;
				Her->SetActorLocation(FVector(Reel15B.X, Reel15B.Y, Z), false, nullptr, ETeleportType::TeleportPhysics);
				Her->SetActorRotation(FRotator(0.f, Yaw, 0.f)); Her->GetCharacterMovement()->StopMovementImmediately();
				PC->SetControlRotation(FRotator(6.f, Yaw - 20.f, 0.f));
				Reel15Yaw = Yaw;
				Reel15Scene(FString::Printf(TEXT("town%d_landmark"), K), FString::Printf(TEXT("%s  -  %s"), *FString(RD15City[K]).ToUpper(), *FString(RD15HeroWho[K]).ToUpper()), RD15LineB[K], RD15SayB[K]);
				Next(2);
			}
			return;
		}
		if (Reel15Sub == 2)
		{
			// (a slow pan across the landmark, the view rising to its top)
			const float U = RD15Ease(Reel15T / RD15ShotB);
			PC->SetControlRotation(FRotator(FMath::Lerp(6.f, 17.f, U), Reel15Yaw + FMath::Lerp(-20.f, 20.f, U), 0.f));
			if (Reel15T > 6.f && Reel15T - Dt <= 6.f) Reel15Shot(Reel15SceneName);
			if (Reel15T >= RD15ShotB) { Reel15End(); ++Stage; bReel15Travel = false; Next(0); }
			return;
		}
		return;
	}
	// ================================================================ tier 3 in Mistward Castle
	if (Stage < RD15Wilds)
	{
		const int32 K = Stage - RD15Fights;
		if (bTown)
		{
			// (out of the last town: into the castle, as the Warrior)
			if (CurrentHero != FName(RD15Hero[K])) { if (Reel15T > 0.5f) { Reel15Switch(K); Reel15T = 0.f; } return; }
			if (!PlayerCombat || Reel15T < 1.5f || bReel15Travel) return;
			bReel15Travel = true;
			const bool bOk = EnterCastle();
			Reel15Mark(bOk ? FString(TEXT("note|travel to the castle")) : FString(TEXT("note|travel to the castle REFUSED")));
			if (!bOk) { Stage = RD15Wilds; bReel15Travel = false; Next(0); }
			return;
		}
		const FIntPoint Set(2, 0);
		const float Span = SectionTiles * TileSize;
		if (!bReel15Set)
		{
			// (the tiers to 3 open, a set of tier 3 built while she is held over it, its own monsters gone)
			if (Reel15Sub == 0)
			{
				const ARDSection* S0 = GetSection(FIntPoint::ZeroValue);
				if (!S0 || S0->IsBuilding() || !PlayerCombat || Reel15T < 2.f) return;
				DebugOpenTiers(3, false);
				Her->GetCharacterMovement()->SetMovementMode(MOVE_Flying);
				Her->SetActorLocation(FVector(Set.X * Span, Set.Y * Span, 400.f), false, nullptr, ETeleportType::TeleportPhysics);
				GenerateSectionNow(Set);
				Reel15Mark(TEXT("note|tier 3 set asked for"));
				Next(10);
				return;
			}
			ARDSection* Ss = GetSection(Set);
			if (!Ss || Ss->IsBuilding())
			{
				Her->SetActorLocation(FVector(Set.X * Span, Set.Y * Span, 400.f), false, nullptr, ETeleportType::TeleportPhysics);
				if (Reel15T > 90.f) { Reel15Mark(TEXT("note|the tier 3 set was not built")); Stage = RD15Wilds; Next(0); }
				return;
			}
			Her->GetCharacterMovement()->SetMovementMode(MOVE_Walking);
			DebugClearSection(Set, 0, Ss->GetRoomCenter(0));
			// (its rooms by free floor, the largest first: a fight a room)
			TArray<TPair<int32, int32>> Rs;
			// (ordinary rooms only: the recording's Mage walked into an arena, which began its waves, barred its doors and held her and
			// every later hero in it while their packs stood in rooms beyond; no shrine, fountain, vault, trap hall, throne room or cells)
			for (int32 Ri = 0; Ri < Ss->GetNumRooms(); ++Ri) if ((uint8)Ss->GetRoomKindEnum(Ri) < (uint8)ERDRoomKind::Junction && Ss->GetRoomKindEnum(Ri) != ERDRoomKind::Prison) Rs.Add(TPair<int32, int32>(Ri, Ss->GetRoomFreeTiles(Ri).Num()));
			Rs.Sort([](const TPair<int32, int32>& A, const TPair<int32, int32>& B) { return A.Value > B.Value; });
			Reel15Rooms.Reset();
			for (const auto& R : Rs) if (Reel15Rooms.Num() < 6 && R.Value >= 12) Reel15Rooms.Add(R.Key);
			if (Reel15Rooms.Num() == 0 && Rs.Num() > 0) Reel15Rooms.Add(Rs[0].Key);
			Her->SetActorLocation(Ss->GetRoomCenter(Reel15Rooms.Num() > 0 ? Reel15Rooms[0] : 0) + FVector(0, 0, 120.f), false, nullptr, ETeleportType::TeleportPhysics);
			bReel15Set = true;
			Reel15Mark(FString::Printf(TEXT("note|tier 3 set built: %d rooms for the fights"), Reel15Rooms.Num()));
			Next(1);
			return;
		}
		ARDSection* Ss = GetSection(Set);
		if (!Ss) return;
		switch (Reel15Sub)
		{
		case 1:
			if (CurrentHero != FName(RD15Hero[K])) { if (Reel15T > 0.3f) { Reel15Switch(K); Reel15T = 0.f; } return; }
			if (!PlayerCombat || Reel15T < 2.f) return;
			Reel15Kit(K, 0);
			Next(2);
			return;
		case 2:
		{
			if (Reel15T < 0.5f) return;
			const FString Kit = Reel15Kit(K, 1);
			// (her stand and their spot, 7.5 to 11 m apart in the room, the camera's room behind her, them in sight)
			const int32 Room = Reel15Rooms.Num() > 0 ? Reel15Rooms[K % Reel15Rooms.Num()] : 0;
			const TArray<FVector> Tiles = Ss->GetRoomFreeTiles(Room);
			FCollisionQueryParams Q(SCENE_QUERY_STAT(RDReel15), false, Her);
			FCollisionObjectQueryParams O; O.AddObjectTypesToQuery(ECC_WorldStatic); O.AddObjectTypesToQuery(ECC_WorldDynamic);
			FVector Stand = Ss->GetRoomCenter(Room), Spot = Stand + FVector(900.f, 0, 0); float Best = -MAX_flt;
			for (int32 A = 0; A < Tiles.Num(); ++A)
				for (int32 B = 0; B < Tiles.Num(); ++B)
				{
					const float D = FVector::Dist2D(Tiles[A], Tiles[B]);
					if (D < 750.f || D > 1100.f) continue;
					float Sc = -FMath::Abs(D - 900.f) - FVector::Dist2D((Tiles[A] + Tiles[B]) * 0.5f, Ss->GetRoomCenter(Room)) * 0.2f;
					if (Sc <= Best) continue;
					const FVector Back = (Tiles[A] - Tiles[B]).GetSafeNormal2D();
					if (GetWorld()->LineTraceTestByObjectType(Tiles[A] + FVector(0, 0, 180.f), Tiles[A] + Back * 400.f + FVector(0, 0, 230.f), O, Q)) Sc -= 5000.f;
					if (GetWorld()->LineTraceTestByObjectType(Tiles[A] + FVector(0, 0, 150.f), Tiles[B] + FVector(0, 0, 150.f), O, Q)) Sc -= 3000.f;
					if (Sc > Best) { Best = Sc; Stand = Tiles[A]; Spot = Tiles[B]; }
				}
			TArray<FVector> Near = Tiles;
			Near.Sort([Spot](const FVector& A, const FVector& B) { return FVector::DistSquared2D(A, Spot) < FVector::DistSquared2D(B, Spot); });
			Near.RemoveAll([Stand](const FVector& P) { return FVector::Dist2D(P, Stand) < 600.f; });
			// (a kind of the tier for each hero, her own: not the tier's strongest (its boss's kind))
			TArray<int32> Kinds; MonsterKindsFor(Set, Kinds);
			int32 Strong = -1;
			for (const int32 Kd : Kinds) if (Strong < 0 || Monsters[Kd].HealthFactor > Monsters[Strong].HealthFactor) Strong = Kd;
			if (Kinds.Num() > 1) Kinds.Remove(Strong);
			Kinds.Sort();
			const int32 Kind = Kinds.Num() > 0 ? Kinds[(K * 5 + 2) % Kinds.Num()] : -1;
			Reel15Foes.Reset();
			Reel15Aggro = AggroDistance; Reel15Lose = LoseDistance; AggroDistance = 0.f;
			for (int32 I = 0; I < 5 && Kind >= 0; ++I)
			{
				const FVector At = Near.IsValidIndex(I) ? Near[I] : Spot + FVector(0, (I - 1) * 200.f, 0);
				if (ARDMonster* M = SpawnMonsterKind(Kind, At, 3)) { M->HomeRoom = Room; Reel15Foes.Add(M); }
			}
			Her->SetActorLocation(Stand + FVector(0, 0, 120.f), false, nullptr, ETeleportType::TeleportPhysics);
			const float Yaw = (Spot - Stand).Rotation().Yaw;
			Her->SetActorRotation(FRotator(0.f, Yaw, 0.f)); Her->GetCharacterMovement()->StopMovementImmediately();
			PC->SetControlRotation(FRotator(-14.f, Yaw, 0.f));
			const FString Kn = Kind >= 0 ? (Monsters[Kind].Title.IsEmpty() ? RD15Words(Monsters[Kind].Name.ToString()) : Monsters[Kind].Title) : FString(TEXT("monster"));
			const int32 N = Reel15Foes.Num();
			const FString Many = RD15Plural(Kn).ToLower();
			Reel15Scene(FString::Printf(TEXT("fight%d"), K), FString::Printf(TEXT("MISTWARD CASTLE, TIER 3  -  %s"), *FString(RD15HeroWho[K]).ToUpper()),
				FString::Printf(TEXT("In her tier-3 kit, against %s %s (the game's autoplay plays her)"), RD15Count[FMath::Clamp(N, 0, 6)], *Many),
				FString::Printf(TEXT("%s%s, in her tier three kit, %s, against %s %s."), K == 0 ? TEXT("Next, a tier three fight for every hero, deep in Mistward Castle. ") : TEXT(""),
					*FString(RD15HeroWho[K]).Replace(TEXT("the "), TEXT("The ")), RD15Way[K], RD15Count[FMath::Clamp(N, 0, 6)], *Many));
			Reel15Mark(FString::Printf(TEXT("note|fight %s: %d %s (kind %d of %d), room %d, %.0f m apart, kit %s"), RD15Hero[K], N, *Kn, Kind, Kinds.Num(), Room, FVector::Dist2D(Stand, Spot) / 100.f, *Kit));
			Next(3);
			return;
		}
		default: break;
		}
	}
	// ================================================================ the wilds round Brokenspire
	else if (Stage < RD15End)
	{
		const int32 K = Stage - RD15Wilds;
		if (!bTown)
		{
			// (out of the castle, back to Brokenspire, once the last fight is over)
			if (Reel15T < 1.f || bReel15Travel) return;
			bReel15Travel = true;
			const bool bOk = ReturnToTown();
			Reel15Mark(bOk ? FString(TEXT("note|travel back to Brokenspire")) : FString(TEXT("note|travel back REFUSED")));
			if (!bOk) { Stage = RD15End; Next(0); }
			return;
		}
		else
		{
			if (!bWild || !IsWildReady() || !bTownPlaced || !PlayerCombat) { if (Reel15Sub == 0) Reel15T = 0.f; return; }
			switch (Reel15Sub)
			{
			case 0:
				if (Reel15T < 2.5f) return;
				if (CurrentHero != FName(RD15Hero[K])) { Reel15Switch(K); Next(1); return; }
				Next(1);
				return;
			case 1:
				if (!PlayerCombat || Reel15T < 2.f) return;
				Reel15Kit(K, 0);
				Next(2);
				return;
			case 2:
			{
				if (Reel15T < 0.5f) return;
				Reel15Kit(K, 1);
				// (a spot round Brokenspire, a way each 60 degrees round it, 1.6 to 3.5 km out: dry, no lava, off the roads, out of every
				// town, flat for 12 m round and on toward where the encounter will be)
				FVector2D B(0, 0);
				for (const FRDWildTown& T : Wild->Towns) if (T.Name == TEXT("Brokenspire")) B = T.Site;
				const ARDSection* S0 = GetSection(FIntPoint::ZeroValue);
				const FVector Out0 = S0 ? S0->TownGateOut.GetSafeNormal2D() : FVector(1, 0, 0);
				FVector2D Pick(0, 0), Way(1, 0); bool bFound = false;
				auto Ok = [&](double X, double Y)
				{
					FRDWSample Sm; Wild->Sample(X, Y, Sm, false);
					if (Sm.WaterKind != 0 || Sm.Lava > 0.1f || Sm.Road > 0.3f || IsInTownWalls(FVector(X * 100.0, Y * 100.0, 0.0))) return false;
					const float H = Wild->Height(X, Y);
					for (const FVector2D& O : { FVector2D(12, 0), FVector2D(-12, 0), FVector2D(0, 12), FVector2D(0, -12) }) if (FMath::Abs(Wild->Height(X + O.X, Y + O.Y) - H) > 1.6f) return false;
					return true;
				};
				// (out of the farms round the town, 2.5 to 9 km out, each in a biome not met yet where one can be found)
				auto BiomeAt = [&](const FVector2D& P) { FRDWSample Sm; Wild->Sample(P.X, P.Y, Sm, false); return Wild->BiomeName(Sm.Biome); };
				for (int32 Pass = 0; Pass < 3 && !bFound; ++Pass)
					for (int32 Turn = 0; Turn < 21 && !bFound; ++Turn)
					{
						const float An = Out0.Rotation().Yaw + K * 60.f + Turn * 17.f;
						const FVector2D Dir(FMath::Cos(FMath::DegreesToRadians(An)), FMath::Sin(FMath::DegreesToRadians(An)));
						for (double R = 2500.0; R <= 9000.0 && !bFound; R += 250.0)
						{
							const FVector2D P = B + Dir * R;
							const FString Bn = BiomeAt(P);
							if (Pass < 2 && Bn == TEXT("farms")) continue;
							if (Pass == 0 && Reel15Biomes.Contains(Bn)) continue;
							if (!Ok(P.X, P.Y) || !Ok(P.X + Dir.X * 24.0, P.Y + Dir.Y * 24.0) || !Ok(P.X + Dir.X * 12.0, P.Y + Dir.Y * 12.0)) continue;
							Pick = P; Way = Dir; bFound = true; Reel15Biomes.Add(Bn);
						}
					}
				if (!bFound) { Pick = B + FVector2D(Out0.X, Out0.Y) * 2000.0; Way = FVector2D(Out0.X, Out0.Y); }
				WildPutHer(Pick.X, Pick.Y);
				const float Yaw = FVector(Way.X, Way.Y, 0.f).Rotation().Yaw;
				Her->SetActorRotation(FRotator(0.f, Yaw, 0.f)); PC->SetControlRotation(FRotator(-12.f, Yaw, 0.f));
				Reel15A = FVector(Way.X, Way.Y, 0.f);
				SetTownHour(10.f + K * 0.8f); SetWeather(1, true);
				Reel15Mark(FString::Printf(TEXT("note|wild spot %s: (%.0f, %.0f) m, %.1f km from Brokenspire%s"), RD15Hero[K], Pick.X, Pick.Y, FVector2D::Distance(Pick, B) / 1000.0, bFound ? TEXT("") : TEXT(" (no spot found: on the gate's way)")));
				Next(20);
				return;
			}
			case 20:
			{
				// (the chunks round her made and she on the ground: then the encounter, 22 to 26 m ahead)
				if (Reel15T < 2.5f) return;
				if (!Her->GetCharacterMovement()->IsMovingOnGround() && Reel15T < 6.f) return;
				ARDSection* Ws = EnsureWildSection();
				const bool bPack = (K % 2) == 1;
				const FName Kn = bPack ? FName(TEXT("roam_pack")) : FName(TEXT("roam_ambush"));
				const FRDWildPoiKind* Pk = WildPoiKinds.FindByPredicate([Kn](const FRDWildPoiKind& X) { return X.Name == Kn; });
				TArray<int32> Kinds; WildKindsForTier(3, Kinds);
				Kinds.Sort();
				int32 Kind = Kinds.Num() > 0 ? Kinds[(K * 7 + 3) % Kinds.Num()] : -1;
				// (the Summoner: her summons do not answer in the wilds (no set under them): two of the tier's weakest kind for her
				// fire alone; three Orc Raiders stood after 55 s in the rehearsals)
				if (K == 4) for (const int32 Kd : Kinds) if (Monsters[Kd].HealthFactor < Monsters[Kind].HealthFactor) Kind = Kd;
				const FVector L = Her->GetActorLocation(), Fw = Reel15A, Rt(-Fw.Y, Fw.X, 0.f);
				const int32 N = K == 4 ? 2 : 4;
				Reel15Foes.Reset();
				const float Now = GetWorld()->GetTimeSeconds();
				for (int32 I = 0; I < N && Ws && Kind >= 0; ++I)
				{
					FVector Q = L + Fw * (2200.f + 150.f * (I % 2)) + Rt * ((I - (N - 1) * 0.5f) * 380.f);
					Q.Z = WildGroundZ(Q);
					const float Yw = (L - Q).Rotation().Yaw;
					if (ARDMonster* M = SpawnWildMonsterAt(Monsters[Kind], Q, Yw, (int32)HashCombine((uint32)SessionSeed, (uint32)(K * 31 + I)), 3, 1.f, FString()))
					{
						M->bHunting = true; M->HuntUntil = Now + 60.f;
						WildRoamers.Add(M); Reel15Foes.Add(M);
					}
				}
				const FString Kname = Kind >= 0 ? (Monsters[Kind].Title.IsEmpty() ? RD15Words(Monsters[Kind].Name.ToString()) : Monsters[Kind].Title) : FString(TEXT("monster"));
				const FString Many = RD15Plural(Kname).ToLower();
				FRDWSample Sm; Wild->Sample(L.X / 100.0, L.Y / 100.0, Sm, false);
				const FString Biome = Wild->BiomeName(Sm.Biome);
				FVector2D B(0, 0);
				for (const FRDWildTown& T : Wild->Towns) if (T.Name == TEXT("Brokenspire")) B = T.Site;
				const float Km = FVector2D::Distance(FVector2D(L.X / 100.0, L.Y / 100.0), B) / 1000.f;
				if (Pk && !Pk->Text.IsEmpty()) PlayerCombat->ShowMessage(Pk->Text);
				const FString What = bPack ? FString(TEXT("a prowling pack")) : FString(TEXT("an ambush"));
				Reel15Scene(FString::Printf(TEXT("wild%d"), K), FString::Printf(TEXT("THE WILDS  -  %s"), *FString(RD15HeroWho[K]).ToUpper()),
					FString::Printf(TEXT("%s, %.1f km from Brokenspire: %s, %s %s of tier 3%s"), *Biome.Left(1).ToUpper().Append(Biome.Mid(1)), Km, *What, RD15Count[FMath::Clamp(Reel15Foes.Num(), 0, 6)], *Many,
						K == 4 ? TEXT(" (her summons do not answer out here)") : TEXT("")),
					FString::Printf(TEXT("%s%s, %.0f kilometres from Brokenspire. %s: %s %s come at %s.%s"), K == 0 ? TEXT("Last, the wilderness: the ") : TEXT("The "), *Biome, Km,
						bPack ? TEXT("A pack is on her trail") : TEXT("An ambush"), RD15Count[FMath::Clamp(Reel15Foes.Num(), 0, 6)], *Many, RD15HeroWho[K],
						K == 4 ? TEXT(" Out here her summons cannot answer, so she fights with fire.") : TEXT("")));
				Reel15Mark(FString::Printf(TEXT("note|encounter %s: %s, %d %s (kind %d of %d)"), RD15Hero[K], *Kn.ToString(), Reel15Foes.Num(), *Kname, Kind, Kinds.Num()));
				Reel15Aggro = AggroDistance; Reel15Lose = LoseDistance;
				Next(3);
				return;
			}
			default: break;
			}
		}
	}
	else
	{
		// ================================================================ the end
		Reel15End();
		GI->bReel = false;
		StopAutoplay(TEXT("the reel's end"));
		if (PlayerCombat) PlayerCombat->ShowMessage(FString());
		Reel15Mark(FString::Printf(TEXT("note|done: %d rescues"), GI->ReelRescues));
		if (!GI->ReelDone.IsEmpty()) FFileHelper::SaveStringToFile(FString::Join(GI->ReelLog, TEXT("\n")), *GI->ReelDone, FFileHelper::EEncodingOptions::ForceUTF8WithoutBOM);
		UE_LOG(LogRDReel15, Log, TEXT("RDREEL15 done"));
		return;
	}
	// ================================================================ a fight (the castle's or the wilds'): 3 the pause, 4 the fight, 5 after it
	URDCombatComponent* Pc = PlayerCombat;
	if (!Pc) return;
	const bool bWildFight = Stage >= RD15Wilds;
	const int32 K = bWildFight ? Stage - RD15Wilds : Stage - RD15Fights;
	Reel15Foes.RemoveAll([](const TWeakObjectPtr<ARDMonster>& M) { return !M.IsValid(); });
	const bool bAllDown = !Reel15Foes.ContainsByPredicate([](const TWeakObjectPtr<ARDMonster>& M) { return M.IsValid() && !M->IsDead(); });
	if (Reel15Sub == 3)
	{
		Reel15Camera(Dt, -14.f);
		if (Reel15T < 2.f) return;
		if (Reel15Aggro >= 0.f) { AggroDistance = Reel15Aggro; LoseDistance = Reel15Lose; Reel15Aggro = -1.f; }
		bAutoplayIgnorePlayer = true;
		StartAutoplay(RD15FightMax + 10.f, false);
		AutoplayOnly = Reel15Foes;
		Pc->ShowMessage(FString());          // (not "any key takes over": nobody does in a reel)
		Reel15Down = -1.f;
		Next(4);
		return;
	}
	if (Reel15Sub == 4)
	{
		Reel15Camera(Dt, -14.f);
		// (kept standing: under a third of her hit points she is set at three fifths (counted, and said in the report))
		if (!Pc->IsDead() && Pc->GetHealth() < Pc->GetMaxHealth() * 0.33f) { Pc->SetHealth(Pc->GetMaxHealth() * 0.6f); ++GI->ReelRescues; Reel15Mark(FString::Printf(TEXT("note|rescue %d of %s"), GI->ReelRescues, RD15Hero[K])); }
		if (Reel15T > 4.f && Reel15T - Dt <= 4.f) Reel15Shot(Reel15SceneName);
		if (bAllDown && Reel15Down < 0.f) Reel15Down = Reel15T;
		const bool bDone = (bAllDown && Reel15T - Reel15Down >= 3.f && Reel15T >= RD15FightMin) || Reel15T >= RD15FightMax || Pc->IsDead();
		if (!bDone) return;
		StopAutoplay(TEXT("the reel's fight"));
		Pc->ShowMessage(FString());
		int32 Left = 0; for (const TWeakObjectPtr<ARDMonster>& M : Reel15Foes) if (M.IsValid() && !M->IsDead()) ++Left;
		Reel15Mark(FString::Printf(TEXT("note|fight over: %s, %d left standing, %.1f s, her %.0f of %.0f hp%s"), RD15Hero[K], Left, Reel15Down >= 0.f ? Reel15Down : Reel15T, Pc->GetHealth(), Pc->GetMaxHealth(), Pc->IsDead() ? TEXT(", SHE FELL") : TEXT("")));
		Reel15End();
		// (the rest of a pack left standing: gone before the next scene)
		for (const TWeakObjectPtr<ARDMonster>& M : Reel15Foes) if (M.IsValid() && !M->IsDead()) M->Destroy();
		Reel15Foes.Reset();
		++Stage; bReel15Travel = false;
		Next(Stage < RD15Wilds ? 1 : 0);
		return;
	}
}
