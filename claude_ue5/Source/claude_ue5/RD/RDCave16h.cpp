// The user's list of 2026-11-22 (docs/improvements16.txt, "things that link back to the open world"; the plan docs/improvements16_plan.md),
// its sixteenth phase: the caves and the wilds.
// - a cave's treasure map: read in the cave, it shows a ruin or a structure near the broken tower over it; back in the wilds the place is
//   marked and a chest lies buried there (the buried chests of the list of 2026-11-20's twelfth phase, their spot at the place itself);
// - a contract beast that retreats underground: struck under half its hit points near a broken tower, it flees into the tower's cave,
//   and the contract is finished there (it waits in the cave's first set's deepest room);
// - a lost traveller found alive deep inside: freed, they find their way out; back in the wilds they settle at the last camp she
//   cleared, or wait to be brought home: the next town she comes to pays for them;
// - a waystone fragment: used in its cave, the cave's mouth is a place of the map she can travel to;
// - the tower's key: the cave's last boss leaves it; at the broken tower's foot it opens a lift to a platform at the top: the land
//   round it marked and revealed, and a chest.
#include "RD/RDDungeonGenerator.h"
#include "RD/RDSection.h"
#include "RD/RDCombat.h"
#include "RD/RDGameInstance.h"
#include "RD/RDWild.h"
#include "RD/RDMistward.h"
#include "RD/RDMonster.h"
#include "RD/RDTown.h"
#include "Components/StaticMeshComponent.h"
#include "Components/BoxComponent.h"
#include "Components/PointLightComponent.h"
#include "GameFramework/Character.h"
#include "GameFramework/CharacterMovementComponent.h"
#include "Kismet/GameplayStatics.h"
#include "Engine/World.h"
DEFINE_LOG_CATEGORY_STATIC(LogRDCave16h, Log, All);

// ("cave:<i>_<j>": a landmark tower's square)
static bool RDC16hCellOf(const FString& Key, FIntPoint& Cell)
{
	FString C, A, B;
	if (!Key.Split(TEXT(":"), nullptr, &C) || !C.Split(TEXT("_"), &A, &B) || !A.IsNumeric() || !B.IsNumeric()) return false;
	Cell = FIntPoint(FCString::Atoi(*A), FCString::Atoi(*B));
	return true;
}

// ================================================================================================ the things used
int32 ARDDungeonGenerator::UseCaveThing16(FName Item)
{
	// (-1: not one of these; 0: refused, kept; 1: used up)
	if (Item.IsNone() || (Item != CaveMapItem16 && Item != CaveFragmentItem16)) return -1;
	URDGameInstance* GI = URDGameInstance::Of(this);
	FIntPoint Cell;
	if (!GI || !bCave16 || !RDC16hCellOf(GI->CaveKey15, Cell))
	{
		if (PlayerCombat) PlayerCombat->ShowMessage(Item == CaveMapItem16 ? FString(TEXT("The map's marks are of the land over a cave: read it in a cave beneath a broken tower"))
			: FString(TEXT("The fragment hums only in a cave beneath a broken tower")));
		return 0;
	}
	if (Item == CaveMapItem16)
	{
		int32 N = 0;
		for (const FString& M : GI->CaveMaps16) if (M.StartsWith(GI->CaveKey15 + TEXT("|"))) ++N;
		GI->CaveMaps16.Add(FString::Printf(TEXT("%s|%d|-1"), *GI->CaveKey15, N));
		if (PlayerCombat) PlayerCombat->ShowMessage(TEXT("The map shows a place on the land over this cave, a chest buried there: it is marked on your map in the wilds"));
		UE_LOG(LogRDCave16h, Log, TEXT("RDCAVE16 a cave map read in %s (its %d)"), *GI->CaveKey15, N);
		return 1;
	}
	if (GI->CaveMouthsAttuned16.Contains(Cell)) { if (PlayerCombat) PlayerCombat->ShowMessage(TEXT("This cave's mouth is already among the places you can travel to")); return 0; }
	GI->CaveMouthsAttuned16.Add(Cell);
	if (PlayerCombat) PlayerCombat->ShowMessage(TEXT("The fragment settles into the cave's stone: its mouth is a place you can travel to from your map"));
	UE_LOG(LogRDCave16h, Log, TEXT("RDCAVE16 the mouth of %s attuned"), *GI->CaveKey15);
	return 1;
}

FName ARDDungeonGenerator::CaveLinkThing16(FIntPoint Section, int32 Index) const
{
	// (a cave's container that holds anything: a treasure map or a waystone fragment now and then, on streams of their own; a fragment
	// only while this cave's mouth is not attuned)
	if (!bCave16) return NAME_None;
	FRandomStream Rm((int32)HashCombine(HashCombine((uint32)SessionSeed ^ 0x3A916u, GetTypeHash(Section)), GetTypeHash(Index * 7907 + 11)));
	if (!CaveMapItem16.IsNone() && FindItem(CaveMapItem16) >= 0 && Rm.FRand() < CaveMapShare16) return CaveMapItem16;
	FRandomStream Rf((int32)HashCombine(HashCombine((uint32)SessionSeed ^ 0xF4A616u, GetTypeHash(Section)), GetTypeHash(Index * 7907 + 11)));
	if (!CaveFragmentItem16.IsNone() && FindItem(CaveFragmentItem16) >= 0 && Rf.FRand() < CaveFragmentShare16)
	{
		const URDGameInstance* GI = URDGameInstance::Of(this);
		FIntPoint Cell;
		if (!(GI && RDC16hCellOf(GI->CaveKey15, Cell) && GI->CaveMouthsAttuned16.Contains(Cell))) return CaveFragmentItem16;
	}
	return NAME_None;
}

// ================================================================================================ in the cave: the traveller, the beast, the key
void ARDSection::CaveTravellerSet16()
{
	// (a set beyond the first, one in TravellerShare16 by a hash of its seed: a lost traveller in its deepest room, unless rescued already)
	if (ARDPrisoner* Old = CaveTraveller16.Get()) { OtherActors.Remove(Old); Old->Destroy(); }
	CaveTraveller16.Reset();
	UWorld* W = GetWorld();
	if (!Generator || !W || !W->IsGameWorld() || !bBuildInteractive || Generator->PrisonerDefs.Num() == 0 || Coord == FIntPoint::ZeroValue) return;
	if ((float)(HashCombine((uint32)Seed, 0x7A4E116u) % 10000u) / 10000.f >= Generator->TravellerShare16) return;
	const URDGameInstance* GI = URDGameInstance::Of(this);
	const FString Here = FString::Printf(TEXT("%s|%d_%d|"), GI ? *GI->CaveKey15 : TEXT(""), Coord.X, Coord.Y);
	if (GI) for (const FString& T : GI->RescuedTravellers16) if (T.Contains(TEXT("|") + Here)) return;
	int32 Deep = -1; float DeepZ = 1e9f;
	for (int32 I = 0; I < CavePlaced16.Num(); ++I)
		if (CavePlaced16[I].Kit >= 0 && Rooms[I].Kind != ERDRoomKind::Junction && CaveRoomTiles16.IsValidIndex(I) && CaveRoomTiles16[I].Num() >= 6 && CavePlaced16[I].Z < DeepZ) { DeepZ = CavePlaced16[I].Z; Deep = I; }
	if (Deep < 0) return;
	const float S = Generator->TileSize;
	const FVector2D Mid((CavePlaced16[Deep].At.X + 0.5f) * S, (CavePlaced16[Deep].At.Y + 0.5f) * S);
	// (stood on a walkable tile of the room near its middle, on the floor a trace finds)
	FVector At = GetActorLocation() + FVector(Mid.X, Mid.Y, CavePlaced16[Deep].Z + 60.f);
	float BestD = 1e9f;
	const FVector Want = At;
	for (const FIntPoint& T : CaveRoomTiles16[Deep])
	{
		const FVector Tw = GetActorLocation() + FVector((T.X + 0.5f) * S, (T.Y + 0.5f) * S, CavePlaced16[Deep].Z + 60.f);
		const float D = FVector::Dist2D(Tw, Want); if (D < BestD) { BestD = D; At = Tw; }
	}
	FHitResult H;
	if (W->LineTraceSingleByChannel(H, At + FVector(0, 0, 200.f), At - FVector(0, 0, 600.f), ECC_Visibility)) At = H.ImpactPoint;
	const uint32 Hh = HashCombine((uint32)Seed, 0x7A4E2u);
	const FRDPrisonerDef& D = Generator->PrisonerDefs[Hh % (uint32)Generator->PrisonerDefs.Num()];
	if (!D.Mesh) return;
	FActorSpawnParameters Sp; Sp.SpawnCollisionHandlingOverride = ESpawnActorCollisionHandlingMethod::AlwaysSpawn;
	const float Yaw = (float)(Hh % 360u);
	ARDPrisoner* P = W->SpawnActor<ARDPrisoner>(ARDPrisoner::StaticClass(), FTransform(FRotator(0, Yaw, 0), At), Sp);
	if (!P) return;
	// (freed, a short way toward the room's open middle and out of sight: walked straight, nothing between (PR #123's review: a random
	// way walked into the rock))
	FVector Fw = (Want - At).GetSafeNormal2D();
	if (Fw.IsNearlyZero()) Fw = FRotator(0, Yaw, 0).Vector();
	const float Go = FMath::Clamp((float)FVector::Dist2D(Want, At), 60.f, 180.f);
	P->Init(D, At + Fw * Go / 3.f, At + Fw * Go * 2.f / 3.f, At + Fw * Go);
	OtherActors.Add(P);          // (not MistActors: the castle's cells clear every prisoner there, and took the traveller (the first test))
	CaveTraveller16 = P;
	CaveTravellerName16 = Generator->TravellerNames16.Num() > 0 ? Generator->TravellerNames16[(Hh >> 8) % (uint32)Generator->TravellerNames16.Num()] : FString(TEXT("A lost traveller"));
	UE_LOG(LogRDCave16h, Log, TEXT("RDCAVE16 (%d,%d): %s, lost, in room %d at (%.0f, %.0f, %.0f)"), Coord.X, Coord.Y, *CaveTravellerName16, Deep, At.X, At.Y, At.Z);
}

ARDPrisoner* ARDDungeonGenerator::TravellerNear16(const FVector& From, float Reach, ARDSection** OutS) const
{
	if (!bCave16) return nullptr;
	for (const TPair<FIntPoint, TObjectPtr<ARDSection>>& Kv : Sections)
	{
		ARDSection* S = Kv.Value;
		if (!IsValid(S)) continue;
		ARDPrisoner* P = S->CaveTraveller16.Get();
		if (P && !P->IsFreed() && FVector::Dist2D(P->GetActorLocation(), From) < Reach && FMath::Abs(P->GetActorLocation().Z - From.Z) < 250.f) { if (OutS) *OutS = S; return P; }
	}
	return nullptr;
}

bool ARDDungeonGenerator::TravellerFirst16(const FVector& From, float Reach, float OtherD) const
{
	const ARDPrisoner* P = TravellerNear16(From, Reach);
	if (!P) return false;
	const float Dp = FVector::Dist2D(P->GetActorLocation(), From);
	if (Dp >= OtherD) return false;
	for (const ARDLootPile* L : LootPiles) if (IsValid(L) && FVector::Dist2D(L->GetActorLocation(), From) < Dp) return false;
	// (as the painting: an anvil, a table, a painting nearer takes F (PR #123's review))
	FVector An, Pa;
	if (FindNearestAnvil(From, Dp, An) || !StationDescribe(From, Dp).IsEmpty()) return false;
	if (PaintingNear16(From, Dp, &Pa) && FVector::Dist2D(Pa, From) < Dp) return false;
	return true;
}

FString ARDDungeonGenerator::FreeTraveller16(const FVector& From, float Reach)
{
	ARDSection* S = nullptr;
	ARDPrisoner* P = TravellerNear16(From, Reach, &S);
	URDGameInstance* GI = URDGameInstance::Of(this);
	if (!P || !S || !GI) return FString();
	P->Free();
	const FString Name = S->CaveTravellerName16;
	GI->RescuedTravellers16.Add(FString::Printf(TEXT("%s|%s|%d_%d|0"), *Name, *GI->CaveKey15, S->Coord.X, S->Coord.Y));
	if (PlayerCombat) PlayerCombat->ShowMessage(FString::Printf(TEXT("%s: \"I thought I would die down here!\" They follow your trail out: look for them in the wilds"), *Name));
	UE_LOG(LogRDCave16h, Log, TEXT("RDCAVE16 %s rescued in %s (%d,%d)"), *Name, *GI->CaveKey15, S->Coord.X, S->Coord.Y);
	return TEXT("traveller");
}

void ARDDungeonGenerator::TickCaveContract16()
{
	// (a contract beast that fled into this cave: in the first set's deepest room once the set is built, once a visit)
	URDGameInstance* GI = URDGameInstance::Of(this);
	if (!bCave16 || !GI || bCaveContractLaid16) return;
	const ARDSection* S0 = GetSection(FIntPoint::ZeroValue);
	if (!S0 || S0->IsBuilding()) return;
	bCaveContractLaid16 = true;
	for (const FString& E : GI->ContractsInCave16)
	{
		TArray<FString> F; E.ParseIntoArray(F, TEXT("|"), false);
		if (F.Num() < 6 || F[1] != GI->CaveKey15) continue;
		const int32 Kind = Monsters.IndexOfByPredicate([&F](const FRDMonsterDef& M) { return M.Name.ToString() == F[2]; });
		if (Kind < 0) { UE_LOG(LogRDCave16h, Warning, TEXT("RDCAVE16 contract beast %s: no kind %s on this level"), *F[5], *F[2]); continue; }
		// (the deepest room of the first set but the one she starts in, by the rooms' own floors (a cave room's centre is the set's height:
		// PR #123's review), stood on its walkable tile nearest its middle, on the floor a trace finds)
		FVector At;
		if (!S0->CaveDeepSpot16(GetStartRoomCenter(), At)) continue;
		const int32 TierUp = FMath::Max(0, FCString::Atoi(*F[3]) - (GI->CaveTier15 > 0 ? GI->CaveTier15 : 1));
		const float Hp = FCString::Atof(*F[4]) * (1.f + 0.35f * TierUp);
		ARDMonster* M = SpawnMonsterKind(Kind, At + FVector(0, 0, 100.f), 1, Hp, 1.f + 0.15f * TierUp, 1.15f, F[5]);
		if (!M) continue;
		CaveContractBeast16 = M; CaveContractId16 = FCString::Atoi(*F[0]);
		UE_LOG(LogRDCave16h, Log, TEXT("RDCAVE16 contract beast %s (%s) waits in the first set's deepest room at (%.0f, %.0f, %.0f)"), *F[5], *F[2], At.X, At.Y, At.Z);
		break;          // (one a visit)
	}
}

void ARDDungeonGenerator::OnCaveContractKilled16(ARDMonster* Monster, bool bHers)
{
	URDGameInstance* GI = URDGameInstance::Of(this);
	if (!GI || !Monster || CaveContractBeast16.Get() != Monster) return;
	CaveContractBeast16.Reset();
	if (!bHers) return;
	const int32 Id = CaveContractId16;
	GI->ContractsDone15.AddUnique(Id);
	GI->ContractsInCave16.RemoveAll([Id](const FString& E) { return FCString::Atoi(*E) == Id && E.StartsWith(FString::FromInt(Id) + TEXT("|")); });
	if (PlayerCombat) PlayerCombat->ShowMessage(TEXT("The contract's beast is slain in its cave: claim the bounty at the board"));
	UE_LOG(LogRDCave16h, Log, TEXT("RDCAVE16 contract %d done in the cave"), Id);
}

void ARDDungeonGenerator::CaveBossKey16()
{
	// (a cave's last boss: the broken tower's key, kept with the game)
	URDGameInstance* GI = URDGameInstance::Of(this);
	FIntPoint Cell;
	if (!GI || !RDC16hCellOf(GI->CaveKey15, Cell)) return;
	GI->TowerKeys16.AddUnique(Cell);
	UE_LOG(LogRDCave16h, Log, TEXT("RDCAVE16 the key of the broken tower %d_%d"), Cell.X, Cell.Y);
}

// ================================================================================================ in the wilds
bool ARDDungeonGenerator::CaveMouthPlace16(int32 Id, FRDWildPlace& Out) const
{
	if (Id < CaveMouthIdBase16 || Id >= CaveMouthIdBase16 + (1 << 20) || !IsWildReady()) return false;
	int32 I = ((Id - CaveMouthIdBase16) >> 10) & 0x3FF, J = (Id - CaveMouthIdBase16) & 0x3FF;
	I -= 512; J -= 512;
	FVector2D S;
	if (!WildTowerSite13(I, J, S)) return false;
	// (the mouth's way out as LayCaveMouth15 lays it: the tower's turn by its site's hash, the gap between two buttresses)
	const float Yaw = (float)(FRDWildWorld::Hash((int32)S.X, (int32)S.Y, Wild->Seed) % 360u);
	const FVector Out3 = FRotator(0.f, Yaw, 0.f).RotateVector(FVector(FMath::Cos(FMath::DegreesToRadians(CaveGapDeg15)), -FMath::Sin(FMath::DegreesToRadians(CaveGapDeg15)), 0.f));
	Out.Id = Id; Out.Kind = TEXT("cave"); Out.Name = TEXT("the cave beneath the broken tower");
	Out.At = S + FVector2D(Out3.X, Out3.Y) * (CaveFootRadius15 / 100.0 + 8.0);
	Out.H = Wild->Height(Out.At.X, Out.At.Y); Out.Town = -1; Out.Yaw = FMath::RadiansToDegrees(FMath::Atan2(Out3.Y, Out3.X));
	return true;
}

int32 ARDDungeonGenerator::CaveMouthIdOf16(FIntPoint Cell) { return CaveMouthIdBase16 + (((Cell.X + 512) & 0x3FF) << 10) + ((Cell.Y + 512) & 0x3FF); }

void ARDDungeonGenerator::AddCaveMouths16(TArray<FRDWildPlace>& Out) const
{
	const URDGameInstance* GI = URDGameInstance::Of(this);
	if (!GI) return;
	for (const FIntPoint& C : GI->CaveMouthsAttuned16) { FRDWildPlace P; if (CaveMouthPlace16(CaveMouthIdOf16(C), P)) Out.Add(P); }
}

void ARDDungeonGenerator::TickCaveLinks16(float Dt, const FVector& Her)
{
	CaveLinkLook16 -= Dt;
	if (CaveLinkLook16 > 0.f || !IsWildReady()) return;
	CaveLinkLook16 = 1.f;
	URDGameInstance* GI = URDGameInstance::Of(this);
	if (!GI) return;
	const FVector2D H2(Her.X / 100.0, Her.Y / 100.0);
	// ---- the attuned mouths: places found (travel targets)
	for (const FIntPoint& C : GI->CaveMouthsAttuned16) { const int32 Mid = CaveMouthIdOf16(C); if (!WildFound.Contains(Mid)) { WildFound.Add(Mid); CaveLinkMarked16.Add(Mid); } }
	// ---- the cave maps: each its place (a ruin or a structure near the tower, the map's n-th nearest not taken by another), its chest's
	// spot at the place itself (TreasureSpots15 told before the buried chests ask), the place marked
	for (FString& E : GI->CaveMaps16)
	{
		TArray<FString> F; E.ParseIntoArray(F, TEXT("|"), false);
		FIntPoint Cell; FVector2D S;
		if (F.Num() < 3 || !RDC16hCellOf(F[0], Cell) || !WildTowerSite13(Cell.X, Cell.Y, S)) continue;
		int32 Target = FCString::Atoi(*F[2]);
		if (Target < 0)
		{
			TArray<FRDWildPlace> Ps, Cand;
			GatherPlacesAndSites16(S, CaveMapKm16 * 1000.0, Ps);
			TSet<int32> Taken;
			for (const FString& O : GI->CaveMaps16) { TArray<FString> G; O.ParseIntoArray(G, TEXT("|"), false); if (G.Num() >= 3) Taken.Add(FCString::Atoi(*G[2])); }
			for (const FRDWildPlace& P : Ps)
			{
				const bool bSite = P.Id >= FRDWildWorld::SiteIdBase && P.Id < FRDWildWorld::FarmIdBase;
				bool bRuin = P.Kind == TEXT("ruins") && P.Id < FRDWildWorld::QuestIdBase && !RuinHasMap15(P);
				if (bRuin) { const int32 Rk = WildRuinKindOf(P); if (Rk >= 0 && WildRuinKinds[Rk].bWater) bRuin = false; }          // (no water kind: their middles lie in the water (PR #123's review))
				if ((!bSite && !bRuin) || P.Town >= 0 || Taken.Contains(P.Id) || GI->TreasuresDug15.Contains(P.Id) || FVector2D::Distance(P.At, S) > CaveMapKm16 * 1000.0) continue;
				if (!Cand.ContainsByPredicate([&P](const FRDWildPlace& Q) { return Q.Id == P.Id; })) Cand.Add(P);
			}
			Cand.Sort([&S](const FRDWildPlace& A, const FRDWildPlace& B) { return FVector2D::DistSquared(A.At, S) < FVector2D::DistSquared(B.At, S); });
			{
				FVector2D Sp;
				Cand.RemoveAll([this, &Sp](const FRDWildPlace& P) { return !CaveMapSpot16(P, Sp); });          // (a place with no spot for its chest is passed over)
			}
			if (Cand.Num() == 0) { UE_LOG(LogRDCave16h, Log, TEXT("RDCAVE16 cave map %s: no ruin or structure within %.0f km"), *E, CaveMapKm16); E = F[0] + TEXT("|") + F[1] + TEXT("|-2"); continue; }
			Target = Cand[0].Id;
			E = F[0] + TEXT("|") + F[1] + TEXT("|") + FString::FromInt(Target);
			GI->TreasureMaps15.AddUnique(Target);
			WildMarked15.Add(Target); GI->WildMarked15.AddUnique(Target); CaveLinkMarked16.Add(Target); WildMarkedCacheFor15 = -1;
			if (PlayerCombat) PlayerCombat->ShowMessage(FString::Printf(TEXT("The cave's map: %s is marked on your map, a chest buried there"), *Cand[0].Name));
			UE_LOG(LogRDCave16h, Log, TEXT("RDCAVE16 cave map %s points at %s (%d) at (%.0f, %.0f), %.1f km from its tower"), *F[0], *Cand[0].Name, Target, Cand[0].At.X, Cand[0].At.Y, FVector2D::Distance(Cand[0].At, S) / 1000.0);
			WildAutosave(TEXT("found"));
		}
		if (Target < 0 || GI->TreasuresDug15.Contains(Target)) continue;
		// (the chest's spot at the place, told to the buried chests before they ask (CaveMapSpot16: the same spot every look))
		if (!TreasureSpots15.Contains(Target) || TreasureSpots15[Target].Landmark != TEXT("cave map"))
		{
			FRDWildPlace P; FVector2D Sp;
			if (!Wild->FindPlace(Target, P) || !CaveMapSpot16(P, Sp)) continue;
			FTreasureSpot15 T; T.LmAt = P.At; T.Landmark = TEXT("cave map"); T.Spot = Sp;
			TreasureSpots15.Add(Target, T);
		}
	}
	// ---- the rescued travellers: settled at the last camp she cleared, else waiting to be brought home (the next town pays)
	for (FString& E : GI->RescuedTravellers16)
	{
		TArray<FString> F; E.ParseIntoArray(F, TEXT("|"), false);
		if (F.Num() < 4) continue;
		if (F[3] == TEXT("0"))
		{
			if (GI->CampsCleared15.Num() > 0)
			{
				F[3] = FString::Printf(TEXT("c%d"), GI->CampsCleared15.Last());
				FRDWildPlace Cp; const bool bCamp = Wild->FindPlace(GI->CampsCleared15.Last(), Cp);
				if (PlayerCombat) PlayerCombat->ShowMessage(FString::Printf(TEXT("%s has settled at the camp you cleared%s%s"), *F[0], bCamp ? TEXT(" at ") : TEXT(""), bCamp ? *Cp.Name : TEXT("")));
				if (FReclaimLaid15* L = CampsLaid15.Find(GI->CampsCleared15.Last())) { for (const TWeakObjectPtr<AActor>& T : L->Folk) if (AActor* A = T.Get()) A->Destroy(); for (const TWeakObjectPtr<USceneComponent>& C : L->Comps) if (USceneComponent* Cc = C.Get()) Cc->DestroyComponent(); CampsLaid15.Remove(GI->CampsCleared15.Last()); }          // (laid again with them)
			}
			else
			{
				F[3] = TEXT("2");
				if (PlayerCombat) PlayerCombat->ShowMessage(FString::Printf(TEXT("%s made it out of the cave and waits for you: bring word to the next town you come to"), *F[0]));
			}
			E = FString::Join(F, TEXT("|"));
			WildAutosave(TEXT("found"));
		}
		else if (F[3] == TEXT("2") && WildTownIdx >= 0 && Wild->Towns.IsValidIndex(WildTownIdx) && FVector2D::Distance(Wild->Towns[WildTownIdx].Site, H2) < 250.0)
		{
			const int32 Tier = FMath::Clamp(Wild->TierAt(H2.X, H2.Y), 1, GameTierMax);
			const int32 Gold = FMath::RoundToInt(RescueGold16 * (1.f + 0.35f * (Tier - 1)));
			AddGold(Gold, TEXT("a traveller brought home"));
			F[3] = TEXT("3"); E = FString::Join(F, TEXT("|"));
			if (PlayerCombat) PlayerCombat->ShowMessage(FString::Printf(TEXT("%s's family in %s thank you for bringing them home: %d gold"), *F[0], *Wild->Towns[WildTownIdx].Name, Gold));
			UE_LOG(LogRDCave16h, Log, TEXT("RDCAVE16 %s brought home to %s: %d gold"), *F[0], *Wild->Towns[WildTownIdx].Name, Gold);
			WildAutosave(TEXT("found"));
		}
	}
	TickTowerLift16(H2);
}

void ARDDungeonGenerator::AddRescuedSettlers16(int32 CampId, const FVector2D& Fire, float Yaw, TArray<TWeakObjectPtr<AActor>>& Folk)
{
	const URDGameInstance* GI = URDGameInstance::Of(this);
	if (!GI) return;
	int32 K = 0;
	for (const FString& E : GI->RescuedTravellers16)
	{
		TArray<FString> F; E.ParseIntoArray(F, TEXT("|"), false);
		if (F.Num() < 4 || F[3] != FString::Printf(TEXT("c%d"), CampId)) continue;
		const float A = FMath::DegreesToRadians(Yaw + 140.f + 40.f * K);
		const FVector2D At = Fire + FVector2D(FMath::Cos(A), FMath::Sin(A)) * 3.2;
		TArray<FString> Lines;
		for (const FString& L : TravellerLines16) Lines.Add(L);
		if (ARDTownsfolk* T = SpawnReclaimFolk15(At, Yaw + 140.f + 40.f * K + 180.f, (uint32)CampId * 13u + K, (K % 2) ? TEXT("Townswoman") : TEXT("Townsman"), F[0] + TEXT(", rescued from a cave"), Lines))
			Folk.Add(T);
		++K;
	}
}

// ================================================================================================ the tower's lift and top
void ARDDungeonGenerator::DropTowerTop16()
{
	for (TWeakObjectPtr<USceneComponent>& C : TowerComps16) if (USceneComponent* P = C.Get()) P->DestroyComponent();
	TowerComps16.Reset(); TowerChestId16 = -1; TowerChestMesh16.Reset(); TowerTopCell16 = FIntPoint(INT32_MAX, INT32_MAX); TowerTopZ16 = 0.f;
}

void ARDDungeonGenerator::TickTowerLift16(const FVector2D& H2)
{
	// (the lift's door at the standing tower's foot, the other side from the cave's mouth; the top laid when she rides up)
	UStaticMeshComponent* Lm = WildLandmark.Get();
	if (!Lm || FVector2D::Distance(WildLandmarkAt, H2) > 1500.0)
	{
		TowerDoorAt16 = FVector::ZeroVector;
		if (TowerTopCell16.X != INT32_MAX) DropTowerTop16();
		return;
	}
	const FIntPoint Cell(FMath::FloorToInt(WildLandmarkAt.X / WildLandmarkCellM), FMath::FloorToInt(WildLandmarkAt.Y / WildLandmarkCellM));
	if (TowerTopCell16.X != INT32_MAX && TowerTopCell16 != Cell) DropTowerTop16();
	const float A = FMath::DegreesToRadians(CaveGapDeg15);
	const FVector Out = Lm->GetComponentTransform().TransformVectorNoScale(FVector(FMath::Cos(A), -FMath::Sin(A), 0.f)).GetSafeNormal2D();
	const FVector2D F2 = WildLandmarkAt * 100.0 - FVector2D(Out) * (CaveFootRadius15 + 150.f);
	TowerDoorAt16 = FVector(F2.X, F2.Y, Wild->ToZ(Wild->Height(F2.X / 100.0, F2.Y / 100.0)));
	TowerDoorOut16 = -Out;
	TowerDoorCell16 = Cell;
	// (she stands inside the tower's foot, under its top (a save made up there, loaded on the ground): put out at the lift's door)
	if (APawn* Her = UGameplayStatics::GetPlayerPawn(this, 0))
	{
		const FVector L = Her->GetActorLocation();
		const bool bOnTop = TowerTopCell16 == Cell && FMath::Abs(L.Z - TowerTopZ16) < 600.f;
		if (!bOnTop && FVector2D::Distance(FVector2D(L.X, L.Y) / 100.0, WildLandmarkAt) * 100.0 < CaveFootRadius15 - 300.f && L.Z < Lm->Bounds.GetBox().Min.Z + 0.5f * (Lm->Bounds.GetBox().Max.Z - Lm->Bounds.GetBox().Min.Z))
		{
			Her->SetActorLocation(TowerDoorAt16 + TowerDoorOut16 * 250.f + FVector(0, 0, 110.f), false, nullptr, ETeleportType::TeleportPhysics);
			UE_LOG(LogRDCave16h, Log, TEXT("RDCAVE16 she stood inside the tower %d_%d: put out at its lift's door"), Cell.X, Cell.Y);
		}
	}
}

bool ARDDungeonGenerator::LayTowerTop16()
{
	// (the top: the highest height at which traces out from the tower's axis meet its walls all round (six of eight within 30 m), a stone
	// platform there inside the walls, a ring of hidden walls at its rim (a broken top has gaps), a chest on it)
	UStaticMeshComponent* Lm = WildLandmark.Get();
	UWorld* W = GetWorld();
	if (!Lm || !W) return false;
	if (TowerTopCell16 == TowerDoorCell16 && TowerComps16.Num() > 0) return true;
	DropTowerTop16();
	const FBox B = Lm->Bounds.GetBox();
	const FVector Ax(WildLandmarkAt.X * 100.0, WildLandmarkAt.Y * 100.0, 0.0);
	FCollisionQueryParams Q(SCENE_QUERY_STAT(RDTowerTop16), true);
	// (the tower's collision is shapes a trace from inside never meets: its top is found from outside. Straight down its axis first: a top of
	// its own over half its height is stood on; else the highest height where traces in from 40 m meet it on six ways of eight, the
	// platform laid over the broken top there, as wide as the tower (PR-time: from the axis out nothing was met, "the lift's chains are broken"))
	float TopZ = 0.f, Rad = 0.f;
	auto RingAt = [&](float Z, float& OutR) -> int32
	{
		int32 Hits = 0; TArray<float> Ds;
		for (int32 K = 0; K < 8; ++K)
		{
			const FVector Wy = FRotator(0.f, K * 45.f, 0.f).Vector();
			FHitResult H;
			const FVector From = FVector(Ax.X, Ax.Y, Z) + Wy * 4000.f;
			if (W->LineTraceSingleByChannel(H, From, FVector(Ax.X, Ax.Y, Z), ECC_Visibility, Q) && H.GetComponent() == Lm) { ++Hits; Ds.Add(4000.f - H.Distance); }
		}
		if (Ds.Num() > 0) { Ds.Sort(); OutR = Ds[Ds.Num() / 2]; }
		return Hits;
	};
	FHitResult Hd;
	const bool bTopDown = W->LineTraceSingleByChannel(Hd, FVector(Ax.X, Ax.Y, B.Max.Z + 500.f), FVector(Ax.X, Ax.Y, B.Min.Z), ECC_Visibility, Q) && Hd.GetComponent() == Lm
		&& Hd.ImpactPoint.Z > B.Min.Z + (B.Max.Z - B.Min.Z) * 0.5f && Hd.ImpactNormal.Z > 0.7f;
	for (float Z = B.Max.Z - 100.f; Z > B.Min.Z + (B.Max.Z - B.Min.Z) * 0.5f && Rad <= 0.f; Z -= 200.f)
	{
		float R0 = 0.f;
		if (RingAt(Z, R0) >= 6) { TopZ = Z; Rad = R0; }
	}
	if (Rad <= 0.f) { UE_LOG(LogRDCave16h, Warning, TEXT("RDCAVE16 the tower's top: no ring of walls found from outside")); return false; }
	const bool bOwnFloor = bTopDown && Hd.ImpactPoint.Z > TopZ - 400.f;
	const float FloorZ = bOwnFloor ? Hd.ImpactPoint.Z : TopZ + 120.f;
	const float R = FMath::Clamp(Rad - 60.f, 300.f, 1600.f);
	auto Comp = [this](UStaticMesh* Sm, const FTransform& T, bool bHid) -> UStaticMeshComponent*
	{
		UStaticMeshComponent* C = NewObject<UStaticMeshComponent>(this);
		C->SetStaticMesh(Sm); C->SetMobility(EComponentMobility::Movable);
		C->SetCollisionEnabled(ECollisionEnabled::QueryAndPhysics); C->SetCollisionResponseToAllChannels(ECR_Block);
		C->SetHiddenInGame(bHid); C->SetCastShadow(!bHid);
		C->RegisterComponent(); C->SetWorldTransform(T);
		TowerComps16.Add(C);
		return C;
	};
	UStaticMesh* Cyl = LoadObject<UStaticMesh>(nullptr, TEXT("/Engine/BasicShapes/Cylinder.Cylinder"));
	UStaticMesh* Cube = LoadObject<UStaticMesh>(nullptr, TEXT("/Engine/BasicShapes/Cube.Cube"));
	if (!Cyl || !Cube) return false;
	if (!bOwnFloor)
	{
		UStaticMeshComponent* P = Comp(Cyl, FTransform(FRotator::ZeroRotator, FVector(Ax.X, Ax.Y, FloorZ - 20.f), FVector(R * 2.f / 100.f, R * 2.f / 100.f, 0.4f)), false);
		if (UMaterialInterface* M = Lm->GetMaterial(0)) P->SetMaterial(0, M);
	}
	for (int32 K = 0; K < 16; ++K)
	{
		const float Ang = K * 22.5f;
		const FVector Wy = FRotator(0.f, Ang, 0.f).Vector();
		Comp(Cube, FTransform(FRotator(0.f, Ang, 0.f), FVector(Ax.X, Ax.Y, FloorZ + 120.f) + Wy * (R + 10.f), FVector(0.2f, R * 0.42f / 100.f, 2.4f)), true);
	}
	// (the chest on the platform, its body and lid as the buried chests lay them, unopened)
	const URDGameInstance* GI = URDGameInstance::Of(this);
	TowerChestId16 = -1; TowerChestMesh16.Reset();
	if (!(GI && GI->TowerChests16.Contains(TowerDoorCell16)))
		if (const FRDPiece* Pc = Piece(TEXT("Chest")); Pc && Pc->Mesh)
		{
			const FVector At(Ax.X + R * 0.55f, Ax.Y, FloorZ);
			const FTransform Wt(FRotator(0.f, 180.f, 0.f), At);
			UStaticMeshComponent* Body = Comp(Pc->Mesh, Pc->Adjust * Wt, false);
			if (Pc->Moving) Comp(Pc->Moving, FTransform(Wt.GetRotation() * Pc->Adjust.GetRotation(), Wt.TransformPosition(Pc->Hinge), Pc->Adjust.GetScale3D()), false);
			TowerChestAt16 = At; TowerChestId16 = 1; TowerChestMesh16 = Body;
		}
	UPointLightComponent* Lt = NewObject<UPointLightComponent>(this);
	Lt->SetIntensityUnits(ELightUnits::Candelas); Lt->SetIntensity(30.f); Lt->SetAttenuationRadius(R * 1.6f); Lt->SetLightColor(FLinearColor(1.f, 0.8f, 0.55f)); Lt->SetCastShadows(false);
	Lt->RegisterComponent(); Lt->SetWorldLocation(FVector(Ax.X, Ax.Y, FloorZ + 300.f)); TowerComps16.Add(Lt);
	TowerTopCell16 = TowerDoorCell16; TowerTopZ16 = FloorZ; TowerTopRadius16 = R;
	UE_LOG(LogRDCave16h, Log, TEXT("RDCAVE16 the tower %d_%d's top: floor %.0f m over its foot (%s), %.1f m across"), TowerDoorCell16.X, TowerDoorCell16.Y,
		(FloorZ - B.Min.Z) / 100.f, bOwnFloor ? TEXT("its own") : TEXT("a platform"), R * 2.f / 100.f);
	return true;
}

FString ARDDungeonGenerator::TowerDescribe16(const FVector& From, float Reach) const
{
	if (!bWild) return FString();
	const URDGameInstance* GI = URDGameInstance::Of(this);
	if (TowerTopCell16.X != INT32_MAX && FMath::Abs(From.Z - TowerTopZ16) < 400.f && FVector::Dist2D(From, FVector(WildLandmarkAt.X * 100.0, WildLandmarkAt.Y * 100.0, 0.0)) < TowerTopRadius16 + 200.f)
	{
		// (the lift a point at the platform's middle (marked by its light), the chest by its place; each only when no pile F reaches is
		// nearer (PR #123's review: anywhere on the top F took the lift, and the chest's things lay there for good))
		const FVector Lift(WildLandmarkAt.X * 100.0, WildLandmarkAt.Y * 100.0, TowerTopZ16);
		float PileD = Reach;
		for (const ARDLootPile* L : LootPiles) if (IsValid(L)) PileD = FMath::Min(PileD, (float)FVector::Dist2D(L->GetActorLocation(), From));
		const float Cd = TowerChestId16 > 0 ? FVector::Dist2D(TowerChestAt16, From) : 1e9f, Ld = FVector::Dist2D(Lift, From);
		if (Cd < Reach && Cd <= Ld && Cd < PileD) return TEXT("open the tower's chest");
		if (Ld < Reach && Ld < PileD) return TEXT("take the lift down");
		return FString();
	}
	if (!TowerDoorAt16.IsZero() && FVector::Dist2D(TowerDoorAt16, From) < Reach + 100.f && FMath::Abs(TowerDoorAt16.Z - From.Z) < 300.f)
		return GI && GI->TowerKeys16.Contains(TowerDoorCell16) ? FString(TEXT("take the lift to the tower's top")) : FString(TEXT("a locked iron door (its key is in the cave below)"));
	return FString();
}

FString ARDDungeonGenerator::TowerInteract16(const FVector& From, float Reach)
{
	const FString D = TowerDescribe16(From, Reach);
	if (D.IsEmpty()) return FString();
	URDGameInstance* GI = URDGameInstance::Of(this);
	APawn* Her = UGameplayStatics::GetPlayerPawn(this, 0);
	if (!GI || !Her) return FString();
	auto Put = [Her](const FVector& At) { Her->SetActorLocation(At, false, nullptr, ETeleportType::TeleportPhysics); if (ACharacter* Ch = Cast<ACharacter>(Her)) Ch->GetCharacterMovement()->StopMovementImmediately(); };
	if (D.StartsWith(TEXT("a locked"))) { if (PlayerCombat) PlayerCombat->ShowMessage(TEXT("The lift's iron door is locked: its key lies in the cave below, with the cave's last guardian")); return TEXT("tower locked"); }
	if (D == TEXT("take the lift to the tower's top"))
	{
		if (!LayTowerTop16()) { if (PlayerCombat) PlayerCombat->ShowMessage(TEXT("The lift's chains are broken")); return TEXT("tower broken"); }
		Put(FVector(WildLandmarkAt.X * 100.0 - TowerTopRadius16 * 0.3f, WildLandmarkAt.Y * 100.0, TowerTopZ16 + 110.f));
		// (the land round it: revealed, its places marked, as from a lookout; once a tower)
		RevealWild(WildLandmarkAt, TowerRevealM16);
		int32 Marked = 0;
		if (!GI->TowersClimbed16.Contains(TowerDoorCell16))
		{
			GI->TowersClimbed16.Add(TowerDoorCell16);
			TArray<FRDWildPlace> Ps;
			GatherPlacesAndSites16(WildLandmarkAt, TowerRevealM16, Ps);
			for (const FRDWildPlace& P : Ps)
			{
				if (P.Town >= 0 || P.Id >= FRDWildWorld::QuestIdBase || FVector2D::Distance(P.At, WildLandmarkAt) > TowerRevealM16 || WildFound.Contains(P.Id) || WildMarked15.Contains(P.Id)) continue;
				WildMarked15.Add(P.Id); GI->WildMarked15.AddUnique(P.Id); CaveLinkMarked16.Add(P.Id); ++Marked;
			}
			WildMarkedCacheFor15 = -1;
			bTowerSaveDue16 = true;          // (saved at the foot: a save on the top would load her on the ground under it (PR #123's review))
		}
		TowerMarked16 = Marked;
		if (PlayerCombat) PlayerCombat->ShowMessage(FString::Printf(TEXT("The lift creaks up the broken tower: the land below lies open%s"), Marked > 0 ? *FString::Printf(TEXT(", %d places marked on your map"), Marked) : TEXT("")));
		UE_LOG(LogRDCave16h, Log, TEXT("RDCAVE16 up the tower %d_%d: %d places marked"), TowerDoorCell16.X, TowerDoorCell16.Y, Marked);
		return TEXT("tower up");
	}
	if (D == TEXT("take the lift down"))
	{
		Put(TowerDoorAt16 + TowerDoorOut16 * 250.f + FVector(0, 0, 110.f));
		if (bTowerSaveDue16) { bTowerSaveDue16 = false; WildAutosave(TEXT("found")); }
		return TEXT("tower down");
	}
	if (D == TEXT("open the tower's chest") && TowerChestId16 > 0)
	{
		GI->TowerChests16.AddUnique(TowerDoorCell16);
		const int32 Tier = FMath::Clamp(Wild->TierAt(WildLandmarkAt.X, WildLandmarkAt.Y), 1, GameTierMax);
		TArray<int32> Pool; float Sum = 0.f;
		for (int32 I = 0; I < Items.Num(); ++I)
			if (Items[I].Weight > 0.f && Items[I].Tiers.Contains(Tier) && Items[I].Kind != ERDItemKind::Recipe && Items[I].Kind != ERDItemKind::Key && CaveItemAllowed16(Items[I])) { Pool.Add(I); Sum += Items[I].Weight; }
		FRandomStream Rs((int32)FRDWildWorld::Hash(TowerDoorCell16.X, TowerDoorCell16.Y, Wild->Seed + 1990u));
		TArray<FName> Things;
		for (int32 N = 0; N < TowerChestItems16 && Pool.Num() > 0; ++N)
		{
			float U = Rs.FRand() * Sum; int32 Pick = Pool.Last();
			for (const int32 I : Pool) { U -= Items[I].Weight; if (U <= 0.f) { Pick = I; break; } }
			Things.Add(Items[Pick].Name);
		}
		const int32 Gold = FMath::RoundToInt(TowerChestGold16 * (1.f + 0.35f * (Tier - 1)));
		AddFoundGold16(Gold, TEXT("the tower's chest"));
		TArray<float> Wear; Wear.Init(0.f, Things.Num());
		if (ARDLootPile* Pile = DropLoot(TowerChestAt16 + FVector(-90.f, 0.f, 60.f), Things, Wear)) Pile->bHers = false;
		TowerChestId16 = 0;
		LastTowerChest16 = FString::Printf(TEXT("%d|%d|%s"), Tier, Gold, *FString::JoinBy(Things, TEXT(","), [](const FName& N) { return N.ToString(); }));
		if (PlayerCombat) PlayerCombat->ShowMessage(FString::Printf(TEXT("The tower's chest: %d gold and %d things (tier %d)"), Gold, Things.Num(), Tier));
		PlaySoundAt(TEXT("Player.Loot"), TowerChestAt16);
		bTowerSaveDue16 = true;
		return TEXT("tower chest");
	}
	return FString();
}

TArray<FString> ARDDungeonGenerator::GetCaveLinks16() const
{
	// (for the tests: the game instance's records, the tower's door and top, the last chest)
	TArray<FString> Out;
	const URDGameInstance* GI = URDGameInstance::Of(this);
	if (GI)
	{
		for (const FString& M : GI->CaveMaps16) Out.Add(TEXT("map|") + M);
		for (const FString& C : GI->ContractsInCave16) Out.Add(TEXT("contract|") + C);
		for (const FString& T : GI->RescuedTravellers16) Out.Add(TEXT("traveller|") + T);
		for (const FIntPoint& C : GI->CaveMouthsAttuned16) Out.Add(FString::Printf(TEXT("mouth|%d|%d|%d"), C.X, C.Y, CaveMouthIdOf16(C)));
		for (const FIntPoint& C : GI->TowerKeys16) Out.Add(FString::Printf(TEXT("key|%d|%d"), C.X, C.Y));
		for (const FIntPoint& C : GI->TowersClimbed16) Out.Add(FString::Printf(TEXT("climbed|%d|%d"), C.X, C.Y));
		for (const FIntPoint& C : GI->TowerChests16) Out.Add(FString::Printf(TEXT("towerchest|%d|%d"), C.X, C.Y));
	}
	if (IsWildReady() && GI)
	{
		for (const FString& M : GI->CaveMaps16)
		{
			TArray<FString> F; M.ParseIntoArray(F, TEXT("|"), false);
			const int32 Id = F.Num() >= 3 ? FCString::Atoi(*F[2]) : -1;
			FRDWildPlace P;
			if (Id >= 0 && Wild->FindPlace(Id, P))
			{
				const FTreasureSpot15* T = TreasureSpots15.Find(Id);
				Out.Add(FString::Printf(TEXT("maptarget|%d|%.0f|%.0f|%.0f|%.0f|%s|%s"), Id, P.At.X, P.At.Y, T ? T->Spot.X : 0.0, T ? T->Spot.Y : 0.0, *P.Kind, *P.Name));
			}
		}
		for (const FIntPoint& C : GI->CaveMouthsAttuned16)
		{
			FRDWildPlace P;
			if (CaveMouthPlace16(CaveMouthIdOf16(C), P)) Out.Add(FString::Printf(TEXT("mouthat|%d|%.0f|%.0f|%d"), P.Id, P.At.X, P.At.Y, WildFound.Contains(P.Id) ? 1 : 0));
		}
	}
	if (!TowerDoorAt16.IsZero()) Out.Add(FString::Printf(TEXT("door|%d|%d|%.0f|%.0f|%.0f|%.3f|%.3f"), TowerDoorCell16.X, TowerDoorCell16.Y, TowerDoorAt16.X, TowerDoorAt16.Y, TowerDoorAt16.Z, TowerDoorOut16.X, TowerDoorOut16.Y));
	if (TowerTopCell16.X != INT32_MAX) Out.Add(FString::Printf(TEXT("top|%.0f|%.0f|%.0f|%.0f|%d"), WildLandmarkAt.X * 100.0, WildLandmarkAt.Y * 100.0, TowerTopZ16, TowerTopRadius16, TowerChestId16));
	if (!LastTowerChest16.IsEmpty()) Out.Add(TEXT("chest|") + LastTowerChest16);
	if (ARDMonster* M = CaveContractBeast16.Get()) Out.Add(FString::Printf(TEXT("beast|%d|%.0f|%.0f|%.0f|%s"), CaveContractId16, M->GetActorLocation().X, M->GetActorLocation().Y, M->GetActorLocation().Z, *M->GetName()));
	for (const TPair<FIntPoint, TObjectPtr<ARDSection>>& Kv : Sections)
		if (const ARDSection* S = Kv.Value; IsValid(S) && S->CaveTraveller16.IsValid())
		{
			const ARDPrisoner* P = S->CaveTraveller16.Get();
			Out.Add(FString::Printf(TEXT("lost|%d|%d|%.0f|%.0f|%.0f|%s|%d"), Kv.Key.X, Kv.Key.Y, P->GetActorLocation().X, P->GetActorLocation().Y, P->GetActorLocation().Z, *S->CaveTravellerName16, P->IsFreed() ? 1 : 0));
		}
	return Out;
}

FString ARDDungeonGenerator::DebugNearestTower16(float Xm, float Ym) const
{
	FVector2D S; double D = 0.0;
	if (!IsWildReady() || !NearestTowerSite15(FVector2D(Xm, Ym), 2, S, D)) return FString();
	return FString::Printf(TEXT("%d|%d|%.0f|%.0f|%.0f"), FMath::FloorToInt(S.X / WildLandmarkCellM), FMath::FloorToInt(S.Y / WildLandmarkCellM), S.X, S.Y, D);
}

void ARDDungeonGenerator::GatherPlacesAndSites16(const FVector2D& At, double RadiusM, TArray<FRDWildPlace>& Out) const
{
	// (the places by the places' 2 km cells, the structures by their own 1.58 km cells (PR #123's review: the structures had been asked with
	// the places' cell numbers, 10 to 20 km off))
	const FIntPoint P0 = Wild->PlaceCellOf(At.X - RadiusM, At.Y - RadiusM), P1 = Wild->PlaceCellOf(At.X + RadiusM, At.Y + RadiusM);
	for (int32 A = P0.X; A <= P1.X; ++A) for (int32 B = P0.Y; B <= P1.Y; ++B) Wild->PlacesIn(FIntPoint(A, B), Out);
	const FIntPoint S0 = Wild->SiteCellOf(At.X - RadiusM, At.Y - RadiusM), S1 = Wild->SiteCellOf(At.X + RadiusM, At.Y + RadiusM);
	for (int32 A = S0.X; A <= S1.X; ++A) for (int32 B = S0.Y; B <= S1.Y; ++B) Wild->SitesIn(FIntPoint(A, B), Out);
}

bool ARDDungeonGenerator::CaveMapSpot16(const FRDWildPlace& P, FVector2D& Spot) const
{
	// (22 to 35 m from the place's middle, outside its pieces as the buried chests stand by a landmark: dry, off the roads and lava, gentle;
	// by the place's own hash, the same every look. None of 16: no spot (PR #123's review: the middle itself was the fallback, in a weir's
	// water or a keep's wall))
	for (int32 Try = 0; Try < 16; ++Try)
	{
		const float A = FRDWildWorld::Rand01(P.Id, 1960 + Try, Wild->Seed) * 2.f * PI, D = 22.f + 13.f * FRDWildWorld::Rand01(P.Id, 1980 + Try, Wild->Seed);
		const FVector2D Q = P.At + FVector2D(FMath::Cos(A), FMath::Sin(A)) * D;
		FRDWSample Sm; Wild->Sample(Q.X, Q.Y, Sm, false);
		if (Sm.WaterKind != 0 || Sm.Lava > 0.05f || Sm.Road > 0.05f) continue;
		const double H0 = Wild->Height(Q.X, Q.Y);
		bool bSteep = false;
		for (int32 K = 0; K < 4 && !bSteep; ++K) bSteep = FMath::Abs(Wild->Height(Q.X + 3.0 * FMath::Cos(K * PI / 2.0), Q.Y + 3.0 * FMath::Sin(K * PI / 2.0)) - H0) > 1.2;
		if (!bSteep) { Spot = Q; return true; }
	}
	return false;
}

bool ARDSection::CaveDeepSpot16(const FVector& Away, FVector& Out) const
{
	// (the room of the kit with the lowest floor, 15 m or more from Away, its walkable tile nearest its middle, on the floor)
	const float S = Generator ? Generator->TileSize : 300.f;
	int32 Deep = -1; float DeepZ = 1e9f;
	for (int32 I = 0; I < CavePlaced16.Num(); ++I)
	{
		if (CavePlaced16[I].Kit < 0 || !Rooms.IsValidIndex(I) || Rooms[I].Kind == ERDRoomKind::Junction || !CaveRoomTiles16.IsValidIndex(I) || CaveRoomTiles16[I].Num() < 6) continue;
		const FVector Mid = GetActorLocation() + FVector((CavePlaced16[I].At.X + 0.5f) * S, (CavePlaced16[I].At.Y + 0.5f) * S, CavePlaced16[I].Z);
		if (FVector::Dist2D(Mid, Away) < 1500.f) continue;
		if (CavePlaced16[I].Z < DeepZ) { DeepZ = CavePlaced16[I].Z; Deep = I; }
	}
	if (Deep < 0) return false;
	const FVector Want = GetActorLocation() + FVector((CavePlaced16[Deep].At.X + 0.5f) * S, (CavePlaced16[Deep].At.Y + 0.5f) * S, CavePlaced16[Deep].Z + 60.f);
	float BestD = 1e9f; Out = Want;
	for (const FIntPoint& T : CaveRoomTiles16[Deep])
	{
		const FVector Tw = GetActorLocation() + FVector((T.X + 0.5f) * S, (T.Y + 0.5f) * S, CavePlaced16[Deep].Z + 60.f);
		const float D = FVector::Dist2D(Tw, Want); if (D < BestD) { BestD = D; Out = Tw; }
	}
	FHitResult H;
	if (UWorld* W = GetWorld(); W && W->LineTraceSingleByChannel(H, Out + FVector(0, 0, 200.f), Out - FVector(0, 0, 600.f), ECC_Visibility)) Out = H.ImpactPoint;
	return true;
}

int32 ARDDungeonGenerator::ForgetCaveLinkMarks16()
{
	URDGameInstance* GI = URDGameInstance::Of(this);
	const int32 N = CaveLinkMarked16.Num();
	for (const int32 Id : CaveLinkMarked16) { WildMarked15.Remove(Id); WildFound.Remove(Id); if (GI) GI->WildMarked15.Remove(Id); }
	CaveLinkMarked16.Reset(); WildMarkedCacheFor15 = -1;
	return N;
}
