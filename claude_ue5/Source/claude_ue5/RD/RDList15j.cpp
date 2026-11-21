// The user's list of 2026-11-20 (docs/improvements15.txt; the plan docs/improvements15_plan.md), its eleventh phase: named roaming
// monsters and the map's danger (docs/wilderness_ideas.md's idea 3, and idea 9 in part).
//   - Roamers: in RoamerChance15 of the regions' cells (the world's CellM) a named creature walks a round of its own (a ring 700 to
//     1300 m across round a spot of the cell's own stream), RoamerTierUp15 tiers over its region's, some only by night or in storms.
//     Laid when she comes within 2.5 km of where it is on its round; it walks on along its round (its home moved) while it hunts
//     nobody. Seen within 150 m, its round is marked on her map with a skull; slain, it stays dead for the game and drops its named ring
//     (one of RoamerRings15, items of weight 0: never found anywhere else) once.
//   - The map's danger: the major roads drawn in their tier's colour (a band of five tiers a colour), with a key (RDWildHUD.cpp).
// Its own streams and ids only: no place, structure or scenery moves.
#include "RD/RDDungeonGenerator.h"
#include "RD/RDWild.h"
#include "RD/RDGameInstance.h"
#include "RD/RDCombat.h"
#include "RD/RDMonster.h"
#include "RD/RDMistward.h"
#include "Kismet/GameplayStatics.h"
#include "Engine/World.h"
DEFINE_LOG_CATEGORY_STATIC(LogRDList15j, Log, All);

bool ARDDungeonGenerator::RoamerOf15(FIntPoint Cell, FRoamer15& Out) const
{
	// (a pure function of the seed, worked out once a cell)
	if (const FRoamer15* Got = RoamerCache15.Find(Cell)) { Out = *Got; return Got->Kind >= 0; }
	FRoamer15 R;
	const FRDWildWorld& W = *Wild;
	const double X0 = W.Xs + Cell.X * W.CellM, Y0 = W.Yw + Cell.Y * W.CellM;
	if (RoamerNames15.Num() > 0 && RoamerRings15.Num() > 0 && X0 >= W.Xs && Y0 >= W.Yw && X0 + W.CellM <= W.Xn && Y0 + W.CellM <= W.Ye
		&& FRDWildWorld::Rand01(Cell.X, Cell.Y, W.Seed + 1701u) < RoamerChance15)
		for (int32 Try = 0; Try < 6 && R.Kind < 0; ++Try)
		{
			const FVector2D C(X0 + (0.3 + 0.4 * FRDWildWorld::Rand01(Cell.X * 11 + Try, Cell.Y, W.Seed + 1702u)) * W.CellM, Y0 + (0.3 + 0.4 * FRDWildWorld::Rand01(Cell.X, Cell.Y * 11 + Try, W.Seed + 1703u)) * W.CellM);
			FRDWSample Q; W.Sample(C.X, C.Y, Q, false);
			if (Q.WaterKind != 0) continue;
			double Dt = 1e12; W.NearestTown(C.X, C.Y, Dt);
			if (Dt < 3000.0) continue;
			const uint32 H = FRDWildWorld::Hash(Cell.X, Cell.Y, W.Seed + 1704u);
			R.RegionTier = FMath::Clamp(W.TierAt(C.X, C.Y), 1, GameTierMax);
			R.Tier = FMath::Clamp(R.RegionTier + RoamerTierUp15, 1, GameTierMax);
			TArray<int32> Kinds; WildKindsForTier(R.Tier, Kinds);
			Kinds.RemoveAll([this](int32 K) { return !Monsters.IsValidIndex(K) || Monsters[K].Weight <= 0.f; });
			if (Kinds.Num() == 0) break;
			R.Kind = Kinds[H % (uint32)Kinds.Num()];
			R.C = C; R.Radius = 350.f + 300.f * FRDWildWorld::Rand01(Cell.X, Cell.Y, W.Seed + 1705u);
			R.Phase = FRDWildWorld::Rand01(Cell.X, Cell.Y, W.Seed + 1706u) * 2.f * PI;
			const float U = FRDWildWorld::Rand01(Cell.X, Cell.Y, W.Seed + 1707u);
			R.When = U < 0.6f ? 0 : U < 0.85f ? 1 : 2;          // (always, by night, in storms)
			const FString& First = RoamerNames15[(H >> 8) % (uint32)RoamerNames15.Num()];
			const FString Epithet = RoamerEpithets15.Num() > 0 ? RoamerEpithets15[(H >> 16) % (uint32)RoamerEpithets15.Num()] : FString(TEXT("Wanderer"));
			R.Name = FString::Printf(TEXT("%s the %s"), *First, *Epithet);
			R.Ring = RoamerRings15[(H >> 20) % (uint32)RoamerRings15.Num()];
			R.Id = (Cell.X & 0x3FF) << 10 | (Cell.Y & 0x3FF);
		}
	RoamerCache15.Add(Cell, R);
	Out = R;
	return R.Kind >= 0;
}

FVector2D ARDDungeonGenerator::RoamerAt15(const FRoamer15& R) const
{
	// (where it is on its round now: once round in RoamerRoundSeconds15 of the world's clock)
	const double T = GetWorld() ? GetWorld()->GetTimeSeconds() : 0.0;
	const double A = R.Phase + 2.0 * PI * T / FMath::Max(RoamerRoundSeconds15, 60.f);
	return R.C + FVector2D(FMath::Cos(A), FMath::Sin(A)) * R.Radius;
}

bool ARDDungeonGenerator::RoamerOut15(const FRoamer15& R) const
{
	return R.When == 0 || (R.When == 1 && IsWildNight15()) || (R.When == 2 && Weather == 5);
}

void ARDDungeonGenerator::TickRoamers15(float Dt, const FVector& Her)
{
	RoamerLook15 -= Dt;
	if (RoamerLook15 > 0.f || !IsWildReady() || RoamerNames15.Num() == 0) return;
	RoamerLook15 = 1.f;
	URDGameInstance* GI = URDGameInstance::Of(this);
	const FVector2D H2(Her.X / 100.0, Her.Y / 100.0);
	const FIntPoint Lc = Wild->LookoutCellOf(H2.X, H2.Y);
	TSet<int32> Near;
	for (int32 I = -1; I <= 1; ++I) for (int32 J = -1; J <= 1; ++J)
	{
		FRoamer15 R;
		if (!RoamerOf15(Lc + FIntPoint(I, J), R)) continue;
		const bool bSlain = GI && GI->RoamersSlain15.Contains(R.Id);
		const FVector2D P = RoamerAt15(R);
		TWeakObjectPtr<ARDMonster>* Have = Roamers15.Find(R.Id);
		ARDMonster* M = Have ? Have->Get() : nullptr;
		const bool bBusy = M && !M->IsDead() && M->IsAggro();
		const bool bWant = !bSlain && RoamerOut15(R) && FVector2D::Distance(P, H2) < RoamerReachM15;
		if (bWant || bBusy) Near.Add(R.Id);
		if (bWant && !M)
		{
			const FVector Ground(P.X * 100.0, P.Y * 100.0, WildGroundZ(FVector(P.X * 100.0, P.Y * 100.0, 0.0)));
			M = SpawnWildMonsterAt(Monsters[R.Kind], Ground, 0.f, (int32)FRDWildWorld::Hash(R.Id, 1708, Wild->Seed), R.Tier, RoamerHp15, R.Name);
			if (M)
			{
				M->WildLeash = 20000.f;
				Roamers15.Add(R.Id, M);
				UE_LOG(LogRDList15j, Log, TEXT("RDROAMER15 %s (%s, tier %d in a tier-%d region) out at (%.0f, %.0f)"), *R.Name, *Monsters[R.Kind].Name.ToString(), R.Tier, R.RegionTier, P.X, P.Y);
			}
		}
		if (!M || M->IsDead()) continue;
		// (on its round: its home moved along it while it hunts nobody)
		if (!M->IsAggro()) M->HomeAt = FVector(P.X * 100.0, P.Y * 100.0, WildGroundZ(FVector(P.X * 100.0, P.Y * 100.0, 0.0)) + 100.f);
		// (seen within 150 m: marked on her map, told once)
		if (GI && !GI->RoamersSeen15.Contains(R.Id) && FVector::Dist2D(M->GetActorLocation(), Her) < 15000.f)
		{
			GI->RoamersSeen15.AddUnique(R.Id);
			if (PlayerCombat) PlayerCombat->ShowMessage(FString::Printf(TEXT("%s roams these lands (tier %d): marked on your map"), *R.Name, R.Tier));
		}
	}
	// (gone where it is no longer wanted: out of reach, out of its hours, and hunting nobody)
	for (auto It = Roamers15.CreateIterator(); It; ++It)
	{
		ARDMonster* M = It.Value().Get();
		if (!M) { It.RemoveCurrent(); continue; }
		if (Near.Contains(It.Key()) || M->IsDead()) continue;
		M->Destroy();
		It.RemoveCurrent();
	}
}

bool ARDDungeonGenerator::OnRoamerKilled15(ARDMonster* Monster)
{
	if (!Monster) return false;
	int32 Id = -1;
	for (const auto& Kv : Roamers15) if (Kv.Value.Get() == Monster) { Id = Kv.Key; break; }
	if (Id < 0) return false;
	URDGameInstance* GI = URDGameInstance::Of(this);
	if (GI && GI->RoamersSlain15.Contains(Id)) return true;
	if (GI) GI->RoamersSlain15.AddUnique(Id);
	// (its ring, once: the cell's roamer from its id)
	FRoamer15 R;
	const FIntPoint Cell((Id >> 10) & 0x3FF, Id & 0x3FF);
	if (RoamerOf15(Cell, R) && !R.Ring.IsNone())
	{
		if (ARDLootPile* Pile = DropLoot(Monster->GetActorLocation(), { R.Ring }, { 0.f })) Pile->bHers = false;
		if (PlayerCombat) PlayerCombat->ShowMessage(FString::Printf(TEXT("%s is slain: %s is yours to take"), *R.Name, *R.Ring.ToString()));
	}
	UE_LOG(LogRDList15j, Log, TEXT("RDROAMER15 %s slain (%d)"), *R.Name, Id);
	WildAutosave(TEXT("found"));
	return true;
}

TArray<FString> ARDDungeonGenerator::GetRoamers15(float Km) const
{
	TArray<FString> Out;
	const APawn* Her = UGameplayStatics::GetPlayerPawn(this, 0);
	if (!Her || !IsWildReady()) return Out;
	const URDGameInstance* GI = URDGameInstance::Of(this);
	const FVector2D H2(Her->GetActorLocation().X / 100.0, Her->GetActorLocation().Y / 100.0);
	const int32 Rr = FMath::CeilToInt(Km * 1000.0 / Wild->CellM);
	const FIntPoint Lc = Wild->LookoutCellOf(H2.X, H2.Y);
	for (int32 I = -Rr; I <= Rr; ++I) for (int32 J = -Rr; J <= Rr; ++J)
	{
		FRoamer15 R;
		if (!RoamerOf15(Lc + FIntPoint(I, J), R) || FVector2D::Distance(R.C, H2) > Km * 1000.0) continue;
		const FVector2D P = RoamerAt15(R);
		const TWeakObjectPtr<ARDMonster>* Have = Roamers15.Find(R.Id);
		const ARDMonster* M = Have ? Have->Get() : nullptr;
		const FVector Ma = M ? M->GetActorLocation() : FVector::ZeroVector;
		Out.Add(FString::Printf(TEXT("%d|%s|%s|%d|%d|%d|%.1f|%.1f|%.0f|%.1f|%.1f|%d|%d|%d|%s|%.0f|%.0f|%d"), R.Id, *R.Name, *Monsters[R.Kind].Name.ToString(), R.Tier, R.RegionTier, R.When,
			R.C.X, R.C.Y, R.Radius, P.X, P.Y, M && !M->IsDead() ? 1 : 0, GI && GI->RoamersSeen15.Contains(R.Id) ? 1 : 0, GI && GI->RoamersSlain15.Contains(R.Id) ? 1 : 0,
			*R.Ring.ToString(), Ma.X, Ma.Y, RoamerOut15(R) ? 1 : 0));
	}
	return Out;
}

void ARDDungeonGenerator::DrawRoamerMarks15(TFunctionRef<void(const FVector2D& AtM, const FString& Name)> Each) const
{
	// (the map's skulls: the rounds of the roamers she has seen and not slain)
	const URDGameInstance* GI = URDGameInstance::Of(this);
	if (!GI || !IsWildReady()) return;
	for (const int32 Id : GI->RoamersSeen15)
	{
		if (GI->RoamersSlain15.Contains(Id)) continue;
		FRoamer15 R;
		if (RoamerOf15(FIntPoint((Id >> 10) & 0x3FF, Id & 0x3FF), R)) Each(R.C, R.Name);
	}
}

FLinearColor ARDDungeonGenerator::RoadTierColor15(int32 Tier)
{
	// (a band of five tiers a colour: 1-5 green, 6-10 yellow, 11-15 orange, 16-20 red, 21-25 violet, 26-30 near black)
	static const FLinearColor C[6] = { FLinearColor(0.42f, 0.78f, 0.36f), FLinearColor(0.92f, 0.84f, 0.30f), FLinearColor(0.95f, 0.55f, 0.20f),
		FLinearColor(0.88f, 0.22f, 0.18f), FLinearColor(0.62f, 0.32f, 0.85f), FLinearColor(0.18f, 0.12f, 0.16f) };
	return C[FMath::Clamp((Tier - 1) / 5, 0, 5)];
}

TArray<FString> ARDDungeonGenerator::GetRoadTiers15(float Km) const
{
	// (tests: the major roads' segments within Km of her, "x m|y m|tier|r|g|b" of each segment's middle, as the map draws them)
	TArray<FString> Out;
	const APawn* Her = UGameplayStatics::GetPlayerPawn(this, 0);
	if (!Her || !IsWildReady()) return Out;
	const FVector2D H2(Her->GetActorLocation().X / 100.0, Her->GetActorLocation().Y / 100.0);
	const FBox2D Vw(H2 - FVector2D(Km * 1000.0), H2 + FVector2D(Km * 1000.0));
	TArray<int32> In; Wild->RoadsIn(Vw, false, In);
	for (const int32 Ri : In)
	{
		const TArray<FVector2D>& P = Wild->Roads[Ri].P;
		for (int32 K = 0; K + 1 < P.Num(); K += 8)
		{
			const FVector2D Mid = (P[K] + P[K + 1]) * 0.5;
			if (!Vw.IsInside(Mid)) continue;
			const int32 T = Wild->TierAt(Mid.X, Mid.Y);
			const FLinearColor Cl = RoadTierColor15(T);
			Out.Add(FString::Printf(TEXT("%.0f|%.0f|%d|%.2f|%.2f|%.2f"), Mid.X, Mid.Y, T, Cl.R, Cl.G, Cl.B));
		}
	}
	return Out;
}
