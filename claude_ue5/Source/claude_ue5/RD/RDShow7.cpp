// The reel of the user's list of 2026-11-04 (docs/improvements7.txt: "create a gamebar reel showing off the new changes
// above"): a showcase pilot in the town and the wilderness, a beat at a time, each with its caption (the message plaque):
// the sky and the sun, the narrow cobbles, a painted sign, a garden harvested, a pen's gate opened and its animal that stops
// her, the tavern lit at night with its food, the oven, the mill, the town's rise and fall, the portcullis and its lever, the
// road out, the map's fields (while it covers the view she is put in the meadows), the animals that run, the weather, the
// dusk, the stars and the moon, a save named. In the packaged game: -RDShow7 [-RDShowReady=<file>] [-RDShowGo=<file>]
// [-RDShowDone=<file>] (the recorder's files: ready once the town stands, the go when the recording runs, done at the end);
// in play from Python: StartShow7 (a rehearsal). The pilot moves her by putting her and turning the view: no tile paths.
#include "RD/RDDungeonGenerator.h"
#include "RD/RDSection.h"
#include "RD/RDCombat.h"
#include "RD/RDWild.h"
#include "RD/RDGameInstance.h"
#include "RD/RDTown.h"
#include "GameFramework/Character.h"
#include "GameFramework/CharacterMovementComponent.h"
#include "GameFramework/PlayerController.h"
#include "Kismet/GameplayStatics.h"
#include "Misc/FileHelper.h"
#include "Misc/Paths.h"
#include "Misc/CommandLine.h"
#include "Misc/Parse.h"
#include "Engine/World.h"
#include "Components/InstancedStaticMeshComponent.h"
#include "Materials/MaterialInterface.h"

DEFINE_LOG_CATEGORY_STATIC(LogRDShow7, Log, All);

namespace
{
	/** the beats, in order, and how long each lasts (s) */
	enum ERDShow7Beat : int32 { S7_Sky, S7_Cobbles, S7_Sign, S7_Garden, S7_Pen, S7_Tavern, S7_Oven, S7_Mill, S7_Hills, S7_Gate, S7_Road, S7_Map, S7_Animals,
		S7_Rain, S7_Dusk, S7_Night, S7_Save, S7_Count };
	const float RD7ShowSeconds[S7_Count] = { 9.f, 9.f, 8.f, 8.f, 12.f, 11.f, 8.f, 8.f, 8.f, 20.f, 14.f, 12.f, 14.f, 16.f, 12.f, 12.f, 16.f };
	const TCHAR* RD7ShowCaption[S7_Count] = {
		TEXT("Brokenspire under a moving sky: clouds of many sizes, the sun high"),
		TEXT("The cobbled streets: a strip three people wide, trodden earth beside it"),
		TEXT("Each trade's sign painted in a medieval hand, fitted to its board"),
		TEXT("A garden harvested for its crops (they grow again the next day)"),
		TEXT("A pen's gate opens for her; inside, the animals stand in her way"),
		TEXT("The tavern at night: candles on the tables, lamps over the seats, food to take"),
		TEXT("A kitchen's bread oven bakes the gardens' wheat into bread"),
		TEXT("The mill: its house built round its sails, which turn high over the ground"),
		TEXT("The open ground rises and falls; the buildings stand on level ground"),
		TEXT("The portcullis stops her until a lever raises it"),
		TEXT("The road out of the gate, the land rolling away in hills and hollows"),
		TEXT("The map: fields of every shape, the regions flowing into each other"),
		TEXT("Deer, hares and squirrels by their land: come too near and they run"),
		TEXT("The weather: rain, then a storm and its wind"),
		TEXT("The day ends: the sun goes down behind the clouds"),
		TEXT("A clear night: the stars and the moon, the land moonlit, fireflies"),
		TEXT("Save the game under a name of her own") };
	float RD7Ease(float T) { T = FMath::Clamp(T, 0.f, 1.f); return T * T * (3.f - 2.f * T); }
}

void ARDDungeonGenerator::StartShow7(const FString& Go, const FString& Done)
{
	Show7Go = Go; Show7Done = Done; Show7Beat = -1; Show7T = 0.f; bShow7On = true; bShow7Going = Go.IsEmpty(); Show7Log.Reset();
	// (nothing comes at her while it runs)
	Show7Aggro = AggroDistance; AggroDistance = 0.f;
	UE_LOG(LogRDShow7, Log, TEXT("RDSHOW7 armed (go %s)"), Go.IsEmpty() ? TEXT("at once") : *Go);
}

FString ARDDungeonGenerator::GetShow7State() const
{
	return FString::Printf(TEXT("%d|%d|%.1f|%s"), bShow7On ? 1 : 0, Show7Beat, Show7T, *FString::Join(Show7Log, TEXT(" / ")));
}

void ARDDungeonGenerator::TickShow7(float RealDt, APlayerController* PC)
{
	// (the command line, once a game)
	if (URDGameInstance* GI = URDGameInstance::Of(this); GI && !GI->bShow7Read && bTown && bWild)
	{
		GI->bShow7Read = true;
		if (FParse::Param(FCommandLine::Get(), TEXT("RDShow7")))
		{
			FString Go, Done, Ready;
			FParse::Value(FCommandLine::Get(), TEXT("RDShowGo="), Go); FParse::Value(FCommandLine::Get(), TEXT("RDShowDone="), Done); FParse::Value(FCommandLine::Get(), TEXT("RDShowReady="), Ready);
			StartShow7(Go, Done); Show7Ready = Ready;
		}
	}
	if (!bShow7On || !PC) return;
	ACharacter* Her = Cast<ACharacter>(PC->GetPawn());
	ARDSection* S = GetSection(FIntPoint::ZeroValue);
	// (from the map on she is out in the wilds, the town dropped: its section is gone)
	if (!Her || !PlayerCombat || !IsWildReady() || (!S && Show7Beat < S7_Map - 1)) return;
	// (ready once the town stands; the recording's go)
	if (!bShow7Going)
	{
		if (!Show7Ready.IsEmpty() && !FPaths::FileExists(Show7Ready)) FFileHelper::SaveStringToFile(TEXT("ready"), *Show7Ready);
		if (!FPaths::FileExists(Show7Go)) return;
		bShow7Going = true;
	}
	const FVector Sq = S ? S->LocalToWorld(FIntPoint((S->TownSquare.Min.X + S->TownSquare.Max.X) / 2, (S->TownSquare.Min.Y + S->TownSquare.Max.Y) / 2)) : FVector::ZeroVector;
	const FVector Gate = S ? S->TownGate : FVector::ZeroVector, Out = S ? S->TownGateOut.GetSafeNormal2D() : FVector(1, 0, 0), Across(-Out.Y, Out.X, 0.f);
	auto PutAt = [&](const FVector& P, float Yaw, float Pitch)
	{
		const float Zg = S ? S->GetActorLocation().Z + S->TownLiftAt(FVector2D(P)) : WildGroundZ(P);
		Her->SetActorLocation(FVector(P.X, P.Y, (bWild && !IsInTownWalls(P) && FVector::Dist2D(P, Gate) > 3000.f ? WildGroundZ(P) : Zg) + 100.f), false, nullptr, ETeleportType::TeleportPhysics);
		Her->SetActorRotation(FRotator(0.f, Yaw, 0.f)); Her->GetCharacterMovement()->StopMovementImmediately();
		PC->SetControlRotation(FRotator(Pitch, Yaw, 0.f));
	};
	auto LookYaw = [](const FVector& A, const FVector& B) { return (B - A).Rotation().Yaw; };
	auto Walk = [&](const FVector& To, float Scale)
	{
		const FVector D = (To - Her->GetActorLocation()).GetSafeNormal2D();
		if (FVector::Dist2D(To, Her->GetActorLocation()) > 80.f) Her->AddMovementInput(D, Scale);
	};
	auto Pan = [&](float Yaw0, float Yaw1, float Pitch0, float Pitch1, float U) { const float E = RD7Ease(U); PC->SetControlRotation(FRotator(FMath::Lerp(Pitch0, Pitch1, E), FMath::Lerp(Yaw0, Yaw1, E), 0.f)); };
	// ---- a new beat: its setting
	const bool bNew = Show7Beat < 0 || Show7T >= RD7ShowSeconds[Show7Beat];
	if (bNew)
	{
		if (Show7Beat >= 0) Show7Log.Add(FString::Printf(TEXT("%d done"), Show7Beat));
		++Show7Beat; Show7T = 0.f; Show7Step = 0;
		if (Show7Beat >= S7_Count)
		{
			bShow7On = false; AggroDistance = Show7Aggro;
			SetMenuOpen(false); SetMapOpen(false);
			if (!Show7Done.IsEmpty()) FFileHelper::SaveStringToFile(FString::Join(Show7Log, TEXT(" | ")), *Show7Done);
			UE_LOG(LogRDShow7, Log, TEXT("RDSHOW7 done: %s"), *FString::Join(Show7Log, TEXT(" | ")));
			return;
		}
		PlayerCombat->ShowMessage(RD7ShowCaption[Show7Beat]);
		Show7A = FVector::ZeroVector; Show7B = FVector::ZeroVector; Show7Yaw = 0.f;
		switch (Show7Beat)
		{
		case S7_Sky: SetTownHour(9.5f); SetWeather(1, true); { const FVector P = Sq + Across * 700.f; PutAt(P, LookYaw(Sq, Gate) + 180.f, 26.f); } break;
		case S7_Cobbles:
		{
			// (on the main road between the gate and the square, walking toward the square)
			Show7A = Gate + (Sq - Gate) * 0.55f; Show7B = Sq;
			PutAt(Show7A, LookYaw(Show7A, Sq), -22.f);
			break;
		}
		case S7_Sign:
		{
			// (in front of a painted face of a trade's sign (its plane, MI_BS_Sign_<WORDS>, faces its local +Z), the one nearest the
			// square: 3 m off it, the view turned so that the board is beside her head, not behind it. The sign's own transform
			// put her before a wall twice: the face planes are what the town's test measures)
			FTransform Best; float Bd = 1e18f; bool bFound = false;
			TInlineComponentArray<UInstancedStaticMeshComponent*> Ics(S);
			for (UInstancedStaticMeshComponent* C : Ics)
			{
				const UMaterialInterface* M = C ? C->GetMaterial(0) : nullptr;
				if (!M || !M->GetName().StartsWith(TEXT("MI_BS_Sign_"))) continue;
				for (int32 K = 0; K < C->GetInstanceCount(); ++K)
				{
					FTransform T; C->GetInstanceTransform(K, T, true);
					const float D = FVector::DistSquared2D(T.GetLocation(), Sq);
					if (D >= Bd) continue;
					// (a face whose view is clear: from it out to where the camera ends up behind her (a corner pressed the camera
					// against a wall in one town), and down to her feet there)
					const FVector Fc = T.GetLocation(), Nrm = T.GetUnitAxis(EAxis::Z).GetSafeNormal2D();
					if (Nrm.IsNearlyZero()) continue;
					FHitResult Hit; FCollisionQueryParams Qp(SCENE_QUERY_STAT(RDShow7Sign), false, Her);
					if (GetWorld()->LineTraceSingleByChannel(Hit, Fc + Nrm * 20.f, Fc + Nrm * 700.f, ECC_Visibility, Qp)) continue;
					if (GetWorld()->LineTraceSingleByChannel(Hit, Fc + Nrm * 300.f, Fc + Nrm * 300.f - FVector(0, 0, 140.f), ECC_Visibility, Qp) && Hit.Distance < 100.f) continue;
					Bd = D; Best = T; bFound = true;
				}
			}
			if (bFound)
			{
				const FVector Fc = Best.GetLocation(), Nrm = Best.GetUnitAxis(EAxis::Z).GetSafeNormal2D();          // (the engine's plane: its face is its Z, stood up)
				const FVector Cam = Fc + Nrm * 300.f;
				PutAt(FVector(Cam.X, Cam.Y, 0.f), LookYaw(Cam, Fc) + 22.f, 12.f);          // (10 degrees left the board half behind her head: the camera is 3 m further back)
				UE_LOG(LogRDShow7, Log, TEXT("RDSHOW7 sign face %s normal %s, she at %s"), *Fc.ToString(), *Nrm.ToString(), *Cam.ToString());
			}
			break;
		}
		case S7_Garden:
			if (S->TownGardens.Num() > 0) { const FVector G = S->TownGardens[0].At; const FVector P = G + FVector(S->TownGardens[0].Half.X + 70.f, 0.f, 0.f); PutAt(P, LookYaw(P, G), -25.f); Show7A = P; }
			break;
		case S7_Pen:
		{
			int32 Gi = -1;
			const TArray<FString> L = S->GetTownImproveLines();
			for (const FString& Ln : L) if (Ln.StartsWith(TEXT("pengate|"))) { TArray<FString> P; Ln.ParseIntoArray(P, TEXT("|")); Show7A = FVector(FCString::Atof(*P[3]), FCString::Atof(*P[4]), 0.f); Gi = FCString::Atoi(*P[1]); break; }
			if (Gi >= 0 && S->TownPens.Num() > 0)
			{
				// (the pen whose gate this is: the nearest)
				int32 Pi = 0; float Bd = 1e9f;
				for (int32 K = 0; K < S->TownPens.Num(); ++K) { const float D = FVector::Dist2D(S->TownPens[K].At, Show7A); if (D < Bd) { Bd = D; Pi = K; } }
				Show7B = S->TownPens[Pi].At; Show7Yaw = (float)Gi;          // (the gate's door, opened by the beat: F took a townsperson standing nearer once)
				const FVector Outw = (Show7A - Show7B).GetSafeNormal2D();
				const FVector P = Show7A + Outw * 220.f;
				PutAt(P, LookYaw(P, Show7B), -14.f);
			}
			break;
		}
		case S7_Tavern:
		{
			SetTownHour(20.6f);
			for (const auto& B : S->TownBlds)
				if (B.Kind == TK_Tavern)
				{
					const FVector C = (S->LocalToWorld(B.Min) + S->LocalToWorld(B.Max - FIntPoint(1, 1))) * 0.5f;
					Show7B = C;
					const FVector Dr = S->LocalToWorld(B.DoorTile);
					const FVector P = Dr + (C - Dr) * 0.25f;
					PutAt(P, LookYaw(P, C), -16.f); Show7A = P;
					break;
				}
			break;
		}
		case S7_Oven:
		{
			SetTownHour(12.f);
			// (the oven nearest the tavern)
			int32 Oi = -1; float Bd = 1e9f;
			for (int32 K = 0; K < S->TownOvens.Num(); ++K) { const float D = FVector::Dist2D(S->TownOvens[K], Show7B); if (D < Bd) { Bd = D; Oi = K; } }
			if (Oi >= 0)
			{
				const FVector O = S->TownOvens[Oi];
				for (const FVector& Dd : { FVector(220, 0, 0), FVector(-220, 0, 0), FVector(0, 220, 0), FVector(0, -220, 0) })
				{
					PutAt(O + Dd, LookYaw(O + Dd, O), -10.f);
					if (TownThingDescribe(Her->GetActorLocation()).Contains(TEXT("oven"))) break;
				}
				PlayerCombat->AddItem(TEXT("Wheat"), 2);
			}
			break;
		}
		case S7_Mill:
		{
			SetTownHour(13.f);
			for (const auto& Sp : S->TownSpots)
				if (Sp.Kind == TS_Mill) { const FVector P = Sp.At + (Sq - Sp.At).GetSafeNormal2D() * 2600.f; PutAt(P, LookYaw(P, Sp.At), 14.f); Show7A = P; Show7B = Sp.At; break; }
			break;
		}
		case S7_Hills:
		{
			// (the highest open ground, seen low from 14 m)
			FVector Best = Sq; float Bh = -1e9f;
			const FVector L0 = S->GetActorLocation();
			for (int32 I = 4; I < S->GetTownTiles() - 4; I += 2)
				for (int32 J = 4; J < S->GetTownTiles() - 4; J += 2)
				{
					const FVector P(L0.X + (I + 0.5f) * TileSize, L0.Y + (J + 0.5f) * TileSize, 0.f);
					if (!S->InsideTownBorder(FVector2D(P))) continue;
					const float H = S->TownLiftAt(FVector2D(P));
					if (H > Bh) { Bh = H; Best = P; }
				}
			// (she stands on it and looks back over the town: the ground falls away to the level streets)
			PutAt(Best, LookYaw(Best, Sq), -12.f); Show7A = Best; Show7B = Sq;
			break;
		}
		case S7_Gate:
		{
			SetTownHour(10.5f);
			// (shut it first, at once, if it is up)
			if (S->IsPortcullisUp()) S->PullTownLever(0, Gate);
			const FVector P = Gate - Out * 600.f;
			PutAt(P, LookYaw(P, Gate), 6.f); Show7A = P;
			break;
		}
		case S7_Road:
		{
			// (on a road out of Brokenspire, 300 m from the gate, walking along it)
			// (where the world's sample says road on a ring 450 m round the gate, and on to where it crosses the ring at 560 m: the
			// polyline's points did not land on the drawn road)
			FVector P = Gate + Out * 45000.f, Ahead = P + Out * 3000.f;
			if (Wild.IsValid())
			{
				auto RoadOn = [&](double X, double Y) { FRDWSample O; Wild->Sample(X, Y, O, false); return O.Road > 0.8f; };
				const double Gx = Gate.X / 100.0, Gy = Gate.Y / 100.0;
				// (the crossing furthest out of the gate's way: the ring also crosses the roads leaving the town's other side)
				bool bA = false; FVector2D A(0, 0); double Ba = -1e18;
				for (int32 K = 0; K < 2828; ++K) { const double An = 2.0 * PI * K / 2828.0; const FVector2D Q(Gx + 450.0 * FMath::Cos(An), Gy + 450.0 * FMath::Sin(An)); const double Dt = (Q.X - Gx) * Out.X + (Q.Y - Gy) * Out.Y; if (Dt > Ba && Dt > 150.0 && RoadOn(Q.X, Q.Y)) { Ba = Dt; A = Q; bA = true; } }
				if (bA)
				{
					double Bd = 1e18; FVector2D B = A;
					for (int32 K = 0; K < 3520; ++K) { const double An = 2.0 * PI * K / 3520.0; const FVector2D Q(Gx + 560.0 * FMath::Cos(An), Gy + 560.0 * FMath::Sin(An)); const double D = FVector2D::DistSquared(Q, A); if (D < Bd && D < 250.0 * 250.0 && RoadOn(Q.X, Q.Y)) { Bd = D; B = Q; } }
					P = FVector(A.X * 100.0, A.Y * 100.0, 0.0); Ahead = FVector(B.X * 100.0, B.Y * 100.0, 0.0);
				}
				UE_LOG(LogRDShow7, Log, TEXT("RDSHOW7 road %s: %s to %s"), bA ? TEXT("found") : TEXT("not found"), *P.ToString(), *Ahead.ToString());
			}
			WildPutHer(P.X / 100.0, P.Y / 100.0);
			Show7Yaw = LookYaw(P, Ahead);
			Her->SetActorRotation(FRotator(0.f, Show7Yaw, 0.f)); PC->SetControlRotation(FRotator(-8.f, Show7Yaw - 25.f, 0.f));
			Show7A = Ahead;
			break;
		}
		case S7_Map:
			SetMapOpen(true);
			break;
		case S7_Animals:
		{
			SetMapOpen(false);
			const FVector Hl = Her->GetActorLocation(), Fw = Her->GetActorForwardVector();
			SpawnWildAnimalAt(TEXT("Deer"), Hl + Fw * 900.f + FVector(0, 0, 0));
			SpawnWildAnimalAt(TEXT("Hare"), Hl + Fw * 1100.f + Her->GetActorRightVector() * 400.f);
			Show7A = Hl + Fw * 900.f;
			PC->SetControlRotation(FRotator(-6.f, Fw.Rotation().Yaw, 0.f));
			break;
		}
		case S7_Rain: SetTownHour(11.f); SetWeather(4, true); break;
		case S7_Dusk: SetWeather(1, true); SetTownHour(17.6f); break;
		case S7_Night: SetWeather(0, true); SetTownHour(23.6f); break;
		case S7_Save: SetWeather(1, true); SetTownHour(8.5f); SetMenuOpen(true); break;
		default: break;
		}
		UE_LOG(LogRDShow7, Log, TEXT("RDSHOW7 beat %d: %s"), Show7Beat, RD7ShowCaption[Show7Beat]);
		return;
	}
	// ---- the beat going on
	Show7T += RealDt;
	const float U = Show7T / RD7ShowSeconds[Show7Beat];
	const float Yaw = PC->GetControlRotation().Yaw;
	switch (Show7Beat)
	{
	case S7_Sky: Pan(LookYaw(Sq, Gate) + 180.f, LookYaw(Sq, Gate) + 300.f, 26.f, 36.f, U); break;
	case S7_Cobbles: Walk(Show7B, 1.f); break;
	case S7_Garden: if (Show7Step == 0 && Show7T > 2.5f) { Show7Step = 1; Show7Log.Add(TEXT("garden ") + TownThingInteract(Her->GetActorLocation())); } break;
	case S7_Pen:
		if (Show7Step == 0 && Show7T > 2.5f) { Show7Step = 1; S->PushDoor((int32)Show7Yaw, Her->GetActorLocation()); Show7Log.Add(TEXT("pen gate opened")); }
		if (Show7Step == 1 && Show7T > 4.5f) Walk(Show7B, 0.6f);
		break;
	case S7_Tavern:
		Pan(LookYaw(Show7A, Show7B) - 25.f, LookYaw(Show7A, Show7B) + 30.f, -16.f, -12.f, U);
		if (Show7Step == 0 && Show7T > 6.f)
		{
			// (the food on the nearest table)
			int32 Best = -1; float Bd = 1e9f;
			for (int32 K = 0; K < S->TownFoods.Num(); ++K) if (!S->TownFoods[K].bTaken) { const float D = FVector::Dist2D(S->TownFoods[K].At, Show7B); if (D < Bd) { Bd = D; Best = K; } }
			if (Best >= 0) { const FVector F = S->TownFoods[Best].At; PutAt(F + FVector(110.f, 0, 0), LookYaw(F + FVector(110.f, 0, 0), F), -30.f); Show7Log.Add(TEXT("food ") + TownThingInteract(Her->GetActorLocation())); }
			Show7Step = 1;
		}
		break;
	case S7_Oven:
		if (Show7Step == 0 && Show7T > 1.5f) { Show7Step = 1; Show7Log.Add(TEXT("oven ") + TownThingInteract(Her->GetActorLocation())); }
		if (Show7Step == 1 && Show7T > 4.f) { Show7Step = 2; Show7Log.Add(PlayerCombat->Craft(TEXT("Bread")) ? TEXT("bread baked") : TEXT("no bread")); }
		if (Show7Step == 2 && Show7T > 6.8f) { Show7Step = 3; PlayerCombat->SetCraftingOpen(false); PlayerCombat->SetCraftStation(NAME_None); }
		break;
	case S7_Mill: Pan(LookYaw(Show7A, Show7B) - 6.f, LookYaw(Show7A, Show7B) + 6.f, 14.f, 22.f, U); break;
	case S7_Hills: Pan(LookYaw(Show7A, Show7B) - 35.f, LookYaw(Show7A, Show7B) + 35.f, -12.f, -8.f, U); break;
	case S7_Gate:
	{
		// (into the portcullis, stopped; to the lever and pull it; watch it rise; out through the gate)
		if (Show7Step == 0) { Walk(Gate + Out * 300.f, 1.f); if (Show7T > 3.f) Show7Step = 1; }
		else if (Show7Step == 1)
		{
			const FVector Lv = Gate + Across * 320.f - Out * 105.f - Out * 110.f;
			PutAt(Lv, LookYaw(Lv, Gate + Across * 320.f), -10.f);
			Show7Log.Add(TEXT("lever ") + TownThingInteract(Her->GetActorLocation()));
			Show7Step = 2;
		}
		else if (Show7Step == 2 && Show7T > 5.f) { const FVector P = Gate - Out * 900.f + Across * 150.f; PutAt(P, LookYaw(P, Gate), 8.f); Show7Step = 3; }
		else if (Show7Step == 3 && Show7T > 15.f) Show7Step = 4;
		else if (Show7Step == 4) Walk(Gate + Out * 1500.f, 1.f);
		break;
	}
	case S7_Road: Walk(Show7A, 1.f); if (Show7T > 3.f) Pan(Show7Yaw - 25.f, Show7Yaw + 40.f, -8.f, -5.f, (Show7T - 3.f) / 11.f); break;
	case S7_Map:
		// (while the map covers the view: she is put in the nearest meadows, the chunks made there)
		if (Show7Step == 0 && Show7T > 2.f)
		{
			Show7Step = 1;
			double Bd = 1e18; FVector2D Best(9000.0, -4000.0);
			const int32 Mb = Wild->BiomeIndex.Contains(TEXT("meadows")) ? Wild->BiomeIndex[TEXT("meadows")] : -1;
			for (int32 K = 0; K < Wild->CellBiome.Num(); ++K)
				if (Wild->CellBiome[K] == Mb) { const double D = Wild->CellSite[K].Size(); if (D < Bd) { Bd = D; Best = Wild->CellSite[K]; } }
			WildPutHer(Best.X, Best.Y);
		}
		break;
	case S7_Animals: if (Show7T > 2.f) Walk(Show7A, 0.7f); break;
	case S7_Rain:
		if (Show7Step == 0 && Show7T > 8.f) { Show7Step = 1; SetWeather(5, true); }
		Pan(Yaw, Yaw + 0.4f, 0.f, 4.f, U);
		break;
	case S7_Dusk:
		SetTownHour(17.6f + 1.4f * RD7Ease(U));
		Pan(Yaw, Yaw + 0.3f, 6.f, 10.f, U);
		break;
	case S7_Night: Pan(Yaw, Yaw + 0.4f, 8.f, 38.f, U); break;
	case S7_Save:
	{
		// (the menu's Save page, the name typed a letter at a time, Enter; the Load page with it)
		static const TCHAR* Name = TEXT("Meadows at dawn");
		if (Show7Step == 0 && Show7T > 1.5f) { Show7Step = 1; const int32 I = MenuItems().IndexOfByKey(FName(TEXT("save"))); ActivateMenuLine(I); SaveNameText.Reset(); }
		if (Show7Step == 1)
		{
			const int32 Want = FMath::Clamp(FMath::FloorToInt((Show7T - 2.f) * 6.f), 0, FCString::Strlen(Name));
			SaveNameText = FString(Name).Left(Want);
			if (Want >= FCString::Strlen(Name) && Show7T > 6.f) { Show7Step = 2; const int32 I = MenuItems().IndexOfByKey(FName(TEXT("savedo"))); Show7Log.Add(ActivateMenuLine(I) ? TEXT("saved") : TEXT("not saved")); }
		}
		if (Show7Step == 2 && Show7T > 8.f) { Show7Step = 3; const int32 I = MenuItems().IndexOfByKey(FName(TEXT("load"))); ActivateMenuLine(I); }
		break;
	}
	default: break;
	}
}
