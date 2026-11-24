// The user's list of 2026-11-20 (docs/improvements15.txt; the plan docs/improvements15_plan.md), its thirteenth phase: monster contracts
// (docs/wilderness_ideas.md's idea 5).
//   - Every wild town's board posts ContractsPerBoard15 named beasts (Contracts15, from SourceArt/wilderness/contracts15.json), each of a
//     wild kind, tiers over its land's, with a lair 3 to 6 km out of the town on dry gentle ground.
//   - Taken, three signs lie on the way from the town to the lair (tracks, a kill, a shed thing: a glow she reads with F); the map marks the
//     next unread one, then the lair. The three read, she knows the beast's weakness: it takes ContractWeakShare15 more from her blows.
//   - The beast comes out at its lair as she comes within 400 m; killed by her, its contract is done, and its bounty is paid at the board
//     that posted it (gold by its tier).
// Every one on a stream and ids of its own: nothing else moves.
#include "RD/RDDungeonGenerator.h"
#include "RD/RDWild.h"
#include "RD/RDGameInstance.h"
#include "RD/RDCombat.h"
#include "RD/RDMonster.h"
#include "Components/StaticMeshComponent.h"
#include "Components/PointLightComponent.h"
#include "Materials/MaterialInstanceDynamic.h"
#include "Kismet/GameplayStatics.h"
#include "Engine/World.h"
DEFINE_LOG_CATEGORY_STATIC(LogRDList15l, Log, All);

static constexpr float RDL15BeastReachCm = 40000.f, RDL15BeastGoneCm = 60000.f;

void ARDDungeonGenerator::ParseContracts15() const
{
	if (bContractsParsed15) return;
	bContractsParsed15 = true;
	ContractKinds15.Reset();
	for (const FString& L : Contracts15)
	{
		// ("name|kind|hp|tier up|weakness|offer|sign~sign~sign")
		TArray<FString> F; L.ParseIntoArray(F, TEXT("|"), false);
		if (F.Num() < 7) { UE_LOG(LogRDList15l, Warning, TEXT("RDCONTRACT15 a line of %d fields: %s"), F.Num(), *L); continue; }
		FContractKind15 K;
		K.Name = F[0]; K.Kind = FName(*F[1]); K.Hp = FCString::Atof(*F[2]); K.TierUp = FCString::Atoi(*F[3]); K.Weak = F[4]; K.Offer = F[5];
		F[6].ParseIntoArray(K.Signs, TEXT("~"), true);
		K.Monster = Monsters.IndexOfByPredicate([&](const FRDMonsterDef& D) { return D.Name == K.Kind; });
		if (K.Monster < 0 || K.Signs.Num() != 3) { UE_LOG(LogRDList15l, Warning, TEXT("RDCONTRACT15 %s: no kind %s or not three signs"), *K.Name, *F[1]); continue; }
		ContractKinds15.Add(K);
	}
}

int32 ARDDungeonGenerator::ContractTownHere15() const
{
	// (the town she is in: Brokenspire (its plan 0) or the wild town of its name; none while the world is made (PR #105's review: its Init runs
	// on a worker))
	if (!Wild || !IsWildReady()) return -1;
	if (bTownHome) return Wild->Towns.IndexOfByPredicate([](const FRDWildTown& T) { return T.Style == 0; });
	return Wild->Towns.IndexOfByPredicate([&](const FRDWildTown& T) { return T.Name == TownName; });
}

bool ARDDungeonGenerator::ContractOf15(int32 Id, FContract15& Out) const
{
	if (const FContract15* Got = ContractCache15.Find(Id)) { Out = *Got; return Got->Line >= 0; }
	if (!Wild || !IsWildReady()) return false;          // (not cached: asked again once the world is made (PR #105's review))
	FContract15 C; C.Id = Id; C.Town = Id / 16;
	ParseContracts15();
	const int32 Slot = Id % 16, N = ContractKinds15.Num();
	if (Wild->Towns.IsValidIndex(C.Town) && N > 0 && Slot < FMath::Min(ContractsPerBoard15, N))          // (never more slots than beasts: one would come twice)
	{
		const FRDWildTown& T = Wild->Towns[C.Town];
		// (the board's beasts: one by the town's hash, the next ones after it, never one twice on a board)
		const int32 L0 = (int32)(FRDWildWorld::Hash(C.Town, 1840, Wild->Seed) % (uint32)N);
		const int32 Line = (L0 + Slot) % N;
		auto Dry = [this](const FVector2D& Q, bool bGentle) -> bool
		{
			if (Q.X < Wild->Xs + 500.0 || Q.X > Wild->Xn - 500.0 || Q.Y < Wild->Yw + 500.0 || Q.Y > Wild->Ye - 500.0) return false;
			FRDWSample S; Wild->Sample(Q.X, Q.Y, S, false);
			if (S.WaterKind != 0 || S.Road > 0.05f || S.Lava > 0.05f) return false;
			if (!bGentle) return true;
			const double H0 = Wild->Height(Q.X, Q.Y);
			for (int32 K = 0; K < 4; ++K) if (FMath::Abs(Wild->Height(Q.X + 4.0 * FMath::Cos(K * PI / 2.0), Q.Y + 4.0 * FMath::Sin(K * PI / 2.0)) - H0) > 1.5) return false;
			return true;
		};
		for (int32 Try = 0; Try < 24 && C.Line < 0; ++Try)
		{
			const double A = FRDWildWorld::Rand01(Id, 1841 + Try, Wild->Seed) * 2.0 * PI;
			const double D = 3000.0 + 3000.0 * FRDWildWorld::Rand01(Id, 1870 + Try, Wild->Seed);
			const FVector2D Lair = T.Site + FVector2D(FMath::Cos(A), FMath::Sin(A)) * D;
			double Dt = 1e12; Wild->NearestTown(Lair.X, Lair.Y, Dt);
			if (Dt < 1500.0 || !Dry(Lair, true)) continue;
			// (the signs on the way: at 30, 55 and 80 % of it, stepped aside up to 120 m to dry ground)
			const FVector2D Way = Lair - T.Site, Side = FVector2D(-Way.Y, Way.X).GetSafeNormal();
			bool bAll = true;
			for (int32 S = 0; S < 3 && bAll; ++S)
			{
				const FVector2D P = T.Site + Way * (0.30 + 0.25 * S);
				bool bGot = false;
				for (int32 K = 0; K < 13 && !bGot; ++K)
				{
					const FVector2D Q = P + Side * (K == 0 ? 0.0 : (K % 2 ? 1.0 : -1.0) * 20.0 * ((K + 1) / 2));
					if (Dry(Q, false)) { C.Sign[S] = Q; bGot = true; }
				}
				bAll = bGot;
			}
			if (!bAll) continue;
			C.Lair = Lair; C.Line = Line;
			C.Tier = FMath::Clamp(Wild->TierAt(Lair.X, Lair.Y) + ContractKinds15[Line].TierUp, 1, GameTierMax);
		}
	}
	ContractCache15.Add(Id, C);
	Out = C;
	return C.Line >= 0;
}

int32 ARDDungeonGenerator::ContractSignsRead15(int32 Id) const
{
	const URDGameInstance* GI = URDGameInstance::Of(this);
	int32 N = 0;
	if (GI) for (int32 S = 0; S < 3; ++S) N += GI->ContractSigns15.Contains(Id * 4 + S) ? 1 : 0;
	return N;
}

int32 ARDDungeonGenerator::AddContractLines15(TFunctionRef<void(const FString& Act, const FString& Label, const FString& Tag, const FString& Detail, bool bOn, const FString& Arg)> Add) const
{
	const int32 Town = ContractTownHere15();
	if (Town < 0 || Contracts15.Num() == 0) return 0;
	const URDGameInstance* GI = URDGameInstance::Of(this);
	int32 Lines = 0;
	for (int32 Slot = 0; Slot < ContractsPerBoard15; ++Slot)
	{
		const int32 Id = Town * 16 + Slot;
		FContract15 C;
		if (!ContractOf15(Id, C) || (GI && GI->ContractsPaid15.Contains(Id))) continue;
		const FContractKind15& K = ContractKinds15[C.Line];
		const int32 Gold = ContractGoldOf15(C);
		++Lines;
		const double Km = FVector2D::Distance(C.Lair, Wild->Towns[Town].Site) / 1000.0;
		if (GI && GI->ContractsDone15.Contains(Id))
			Add(TEXT("claim"), FString::Printf(TEXT("Claim the bounty on %s"), *K.Name), FString::Printf(TEXT("%d g"), Gold), TEXT("The beast is dead: the board pays what it promised."), true, FString::FromInt(Id));
		else if (GI && GI->ContractsTaken15.Contains(Id))
			Add(TEXT("none"), FString::Printf(TEXT("Contract: %s (taken)"), *K.Name), FString::Printf(TEXT("signs %d of 3"), ContractSignsRead15(Id)),
				FString::Printf(TEXT("Its lair lies %.1f km out. Read its signs on the way (marked on your map) to learn how to hurt it."), Km), false, FString());
		else
			Add(TEXT("contract"), FString::Printf(TEXT("Contract: %s"), *K.Name), FString::Printf(TEXT("tier %d  ·  %d g"), C.Tier, Gold),
				FString::Printf(TEXT("%s Its lair lies %.1f km out."), *K.Offer, Km), true, FString::FromInt(Id));
	}
	return Lines;
}

int32 ARDDungeonGenerator::ContractGoldOf15(const FContract15& C) const
{
	return FMath::RoundToInt(ContractGold15 * (1.f + 0.35f * (C.Tier - 1)));
}

bool ARDDungeonGenerator::TownContract15(FName Act, const FString& Arg)
{
	URDGameInstance* GI = URDGameInstance::Of(this);
	const int32 Id = FCString::Atoi(*Arg);
	FContract15 C;
	if (!GI || !ContractOf15(Id, C) || C.Town != ContractTownHere15()) return false;
	const FContractKind15& K = ContractKinds15[C.Line];
	if (Act == TEXT("contract"))
	{
		if (GI->ContractsTaken15.Contains(Id)) return false;
		GI->ContractsTaken15.AddUnique(Id);
		SetTownNote(FString::Printf(TEXT("You take the contract on %s. Its signs are marked on your map: read them on the way to learn its weakness."), *K.Name));
		TownCount(TEXT("contracts_taken"));
		WildAutosave(TEXT("found"));          // (as every find (PR #105's review))
		return true;
	}
	if (Act == TEXT("claim"))
	{
		if (!GI->ContractsDone15.Contains(Id) || GI->ContractsPaid15.Contains(Id)) return false;
		GI->ContractsPaid15.AddUnique(Id);
		const int32 Gold = ContractGoldOf15(C);
		AddGold(Gold, TEXT("a contract's bounty"));
		SetTownNote(FString::Printf(TEXT("The bounty on %s: %d gold."), *K.Name, Gold));
		TownCount(TEXT("contracts_paid"));
		WildAutosave(TEXT("found"));
		return true;
	}
	return false;
}

void ARDDungeonGenerator::TickContracts15(float Dt, const FVector& Her)
{
	ContractLook15 -= Dt;
	if (ContractLook15 > 0.f || !IsWildReady()) return;
	ContractLook15 = 0.5f;
	URDGameInstance* GI = URDGameInstance::Of(this);
	if (!GI) return;
	const FVector2D H2(Her.X / 100.0, Her.Y / 100.0);
	TSet<int32> WantSigns, WantBeasts;
	for (const int32 Id : GI->ContractsTaken15)
	{
		FContract15 C;
		if (GI->ContractsDone15.Contains(Id) || !ContractOf15(Id, C)) continue;
		const FContractKind15& K = ContractKinds15[C.Line];
		// (its signs within 150 m, unread: a glow of their own)
		for (int32 S = 0; S < 3; ++S)
		{
			const int32 Key = Id * 4 + S;
			if (GI->ContractSigns15.Contains(Key) || FVector2D::Distance(C.Sign[S], H2) > 150.0) continue;
			WantSigns.Add(Key);
			if (ContractSignsLaid15.Contains(Key)) continue;
			const FVector At(C.Sign[S].X * 100.0, C.Sign[S].Y * 100.0, WildGroundZ(FVector(C.Sign[S].X * 100.0, C.Sign[S].Y * 100.0, 0.0)) + 25.f);
			FRewardLaid15 R; R.At = At; R.Id = Key;
			MakeGlow15(R, At, FLinearColor(0.85f, 0.25f, 0.15f), 0.25f);
			ContractSignsLaid15.Add(Key, R);
		}
		// (the list of 2026-11-22's caves: fled into its cave, it is not at its lair)
		if (GI->ContractsInCave16.ContainsByPredicate([Id](const FString& E) { return E.StartsWith(FString::FromInt(Id) + TEXT("|")); })) continue;
		// (the beast at its lair within 400 m; its weakness known once the three signs are read)
		TWeakObjectPtr<ARDMonster>* Have = ContractBeasts15.Find(Id);
		ARDMonster* M = Have ? Have->Get() : nullptr;
		const float D = FVector2D::Distance(C.Lair, H2) * 100.f;
		if ((M && !M->IsDead() && (M->IsAggro() || D < RDL15BeastGoneCm)) || (!M && D < RDL15BeastReachCm)) WantBeasts.Add(Id);
		if (!M && D < RDL15BeastReachCm)
		{
			const FVector Ground(C.Lair.X * 100.0, C.Lair.Y * 100.0, WildGroundZ(FVector(C.Lair.X * 100.0, C.Lair.Y * 100.0, 0.0)));
			M = SpawnWildMonsterAt(Monsters[K.Monster], Ground, 0.f, (int32)FRDWildWorld::Hash(Id, 1880, Wild->Seed), C.Tier, K.Hp, K.Name);
			if (M)
			{
				M->WildLeash = 6000.f;
				ContractBeasts15.Add(Id, M);
				UE_LOG(LogRDList15l, Log, TEXT("RDCONTRACT15 %s (%s, tier %d) out at its lair (%.0f, %.0f)"), *K.Name, *K.Kind.ToString(), C.Tier, C.Lair.X, C.Lair.Y);
			}
		}
		if (M && !M->IsDead()) M->WeakShare15 = ContractSignsRead15(Id) >= 3 ? ContractWeakShare15 : 0.f;
		// (the list of 2026-11-22's caves: struck under half its hit points with a broken tower within ContractCaveKm16 of its lair, it
		// retreats underground into the tower's cave; the contract is finished there)
		if (M && !M->IsDead() && M->GetHealth() < 0.5f * M->GetMaxHealth() && WildLandmarkMesh)
		{
			FVector2D Ts; double Td = 0.0;
			if (NearestTowerSite15(C.Lair, 1, Ts, Td) && Td < ContractCaveKm16 * 1000.0)
			{
				const FIntPoint Cell(FMath::FloorToInt(Ts.X / WildLandmarkCellM), FMath::FloorToInt(Ts.Y / WildLandmarkCellM));
				GI->ContractsInCave16.Add(FString::Printf(TEXT("%d|cave:%d_%d|%s|%d|%.2f|%s"), Id, Cell.X, Cell.Y, *K.Kind.ToString(), C.Tier, K.Hp, *K.Name));
				ContractBeasts15.Remove(Id);
				M->Destroy();
				if (PlayerCombat) PlayerCombat->ShowMessage(FString::Printf(TEXT("%s retreats underground into the cave beneath the broken tower: finish it there"), *K.Name));
				UE_LOG(LogRDList15l, Log, TEXT("RDCONTRACT15 %s fled into cave:%d_%d (%.1f km from its lair)"), *K.Name, Cell.X, Cell.Y, Td / 1000.0);
				WildAutosave(TEXT("found"));
			}
		}
	}
	for (auto It = ContractSignsLaid15.CreateIterator(); It; ++It)
		if (!WantSigns.Contains(It.Key())) { DropReward15(It.Value()); It.RemoveCurrent(); }
	for (auto It = ContractBeasts15.CreateIterator(); It; ++It)
	{
		ARDMonster* M = It.Value().Get();
		if (!M) { It.RemoveCurrent(); continue; }
		if (WantBeasts.Contains(It.Key()) || M->IsDead()) continue;
		M->Destroy();
		It.RemoveCurrent();
	}
}

void ARDDungeonGenerator::DropReward15(FRewardLaid15& R)
{
	if (R.Mesh.IsValid()) R.Mesh->DestroyComponent();
	if (R.Lid.IsValid()) R.Lid->DestroyComponent();
	if (R.Light.IsValid()) R.Light->DestroyComponent();
}

void ARDDungeonGenerator::MakeGlow15(FRewardLaid15& R, const FVector& At, const FLinearColor& Col, float Scale)
{
	if (RewardGlowMesh15)
	{
		UStaticMeshComponent* M = NewObject<UStaticMeshComponent>(this);
		M->SetStaticMesh(RewardGlowMesh15);
		if (RewardGlowMat15) { UMaterialInstanceDynamic* Md = UMaterialInstanceDynamic::Create(RewardGlowMat15, M); Md->SetVectorParameterValue(TEXT("Color"), Col); M->SetMaterial(0, Md); }
		M->SetCollisionEnabled(ECollisionEnabled::NoCollision); M->SetCastShadow(false);
		M->RegisterComponent();
		M->SetWorldTransform(FTransform(FRotator::ZeroRotator, At, FVector(Scale)));
		R.Mesh = M;
	}
	UPointLightComponent* L = NewObject<UPointLightComponent>(this);
	L->SetIntensityUnits(ELightUnits::Candelas); L->SetIntensity(8.f); L->SetLightColor(Col); L->SetAttenuationRadius(400.f); L->SetCastShadows(false);
	L->RegisterComponent();
	L->SetWorldLocation(At + FVector(0, 0, 40.f));
	R.Light = L;
}

FString ARDDungeonGenerator::ReadContractSign15(int32 Key)
{
	URDGameInstance* GI = URDGameInstance::Of(this);
	FContract15 C;
	const int32 Id = Key / 4, S = Key % 4;
	if (!GI || !ContractOf15(Id, C) || S > 2) return FString();
	if (FRewardLaid15* R = ContractSignsLaid15.Find(Key)) { DropReward15(*R); ContractSignsLaid15.Remove(Key); }
	GI->ContractSigns15.AddUnique(Key);
	const FContractKind15& K = ContractKinds15[C.Line];
	const int32 N = ContractSignsRead15(Id);
	if (PlayerCombat)
		PlayerCombat->ShowMessage(N >= 3 ? FString::Printf(TEXT("%s  You know %s now: %s (it takes %d%% more from your blows)"), *K.Signs[S], *K.Name, *K.Weak, FMath::RoundToInt(ContractWeakShare15 * 100.f))
			: FString::Printf(TEXT("%s  (signs of %s: %d of 3)"), *K.Signs[S], *K.Name, N));
	UE_LOG(LogRDList15l, Log, TEXT("RDCONTRACT15 %s: sign %d read (%d of 3)"), *K.Name, S, N);
	WildAutosave(TEXT("found"));
	return TEXT("sign");
}

bool ARDDungeonGenerator::OnContractKilled15(ARDMonster* Monster, bool bHers)
{
	if (!Monster) return false;
	int32 Id = -1;
	for (const auto& Kv : ContractBeasts15) if (Kv.Value.Get() == Monster) { Id = Kv.Key; break; }
	if (Id < 0) return false;
	ContractBeasts15.Remove(Id);
	// (a death that is no doing of hers (lightning, a predator) leaves the contract open: it comes out again)
	URDGameInstance* GI = URDGameInstance::Of(this);
	FContract15 C;
	if (!bHers || !GI || !ContractOf15(Id, C)) return true;
	GI->ContractsDone15.AddUnique(Id);
	if (PlayerCombat && Wild->Towns.IsValidIndex(C.Town))
		PlayerCombat->ShowMessage(FString::Printf(TEXT("%s is dead: claim its bounty at %s's board"), *ContractKinds15[C.Line].Name, *Wild->Towns[C.Town].Name));
	UE_LOG(LogRDList15l, Log, TEXT("RDCONTRACT15 %s killed (%d)"), *ContractKinds15[C.Line].Name, Id);
	WildAutosave(TEXT("found"));
	return true;
}

void ARDDungeonGenerator::DrawContractMarks15(TFunctionRef<void(const FVector2D& AtM, const FString& Name)> Each) const
{
	// (the map's marks of the contracts taken and not done: the next unread sign, then the lair)
	const URDGameInstance* GI = URDGameInstance::Of(this);
	if (!GI) return;
	for (const int32 Id : GI->ContractsTaken15)
	{
		FContract15 C;
		if (GI->ContractsDone15.Contains(Id) || !ContractOf15(Id, C)) continue;
		const FContractKind15& K = ContractKinds15[C.Line];
		int32 Next = -1;
		for (int32 S = 0; S < 3 && Next < 0; ++S) if (!GI->ContractSigns15.Contains(Id * 4 + S)) Next = S;
		// (fled into a cave: its mark is the tower over the cave)
		if (const FString* E = GI->ContractsInCave16.FindByPredicate([Id](const FString& X) { return X.StartsWith(FString::FromInt(Id) + TEXT("|")); }))
		{
			FVector2D Ts; double Td = 0.0;
			if (NearestTowerSite15(C.Lair, 1, Ts, Td)) { Each(Ts, FString::Printf(TEXT("%s's cave"), *K.Name)); continue; }
		}
		if (Next >= 0) Each(C.Sign[Next], FString::Printf(TEXT("Signs of %s"), *K.Name));
		else Each(C.Lair, FString::Printf(TEXT("%s's lair"), *K.Name));
	}
}

TArray<FString> ARDDungeonGenerator::GetContracts15() const
{
	// (tests: "id|town|name|kind|tier|state (open, taken, done, paid)|signs read|lair x|y|sign0 x|y|sign1 x|y|sign2 x|y|gold|beast laid|weak share" for
	// the boards of every town)
	TArray<FString> Out;
	const URDGameInstance* GI = URDGameInstance::Of(this);
	if (!Wild) return Out;
	for (int32 T = 0; T < Wild->Towns.Num(); ++T)
		for (int32 Slot = 0; Slot < ContractsPerBoard15; ++Slot)
		{
			const int32 Id = T * 16 + Slot;
			FContract15 C;
			if (!ContractOf15(Id, C)) continue;
			const FContractKind15& K = ContractKinds15[C.Line];
			const TCHAR* St = GI && GI->ContractsPaid15.Contains(Id) ? TEXT("paid") : GI && GI->ContractsDone15.Contains(Id) ? TEXT("done") : GI && GI->ContractsTaken15.Contains(Id) ? TEXT("taken") : TEXT("open");
			const TWeakObjectPtr<ARDMonster>* B = ContractBeasts15.Find(Id);
			const ARDMonster* M = B ? B->Get() : nullptr;
			Out.Add(FString::Printf(TEXT("%d|%s|%s|%s|%d|%s|%d|%.1f|%.1f|%.1f|%.1f|%.1f|%.1f|%.1f|%.1f|%d|%d|%.2f"), Id, *Wild->Towns[T].Name, *K.Name, *K.Kind.ToString(), C.Tier, St, ContractSignsRead15(Id),
				C.Lair.X, C.Lair.Y, C.Sign[0].X, C.Sign[0].Y, C.Sign[1].X, C.Sign[1].Y, C.Sign[2].X, C.Sign[2].Y, ContractGoldOf15(C), M && !M->IsDead() ? 1 : 0, M ? M->WeakShare15 : 0.f));
		}
	return Out;
}

void ARDDungeonGenerator::ForgetContract15(int32 Id)
{
	// (tests: the contract as it was before it was taken, its beast gone)
	URDGameInstance* GI = URDGameInstance::Of(this);
	if (GI) { GI->ContractsTaken15.Remove(Id); GI->ContractsDone15.Remove(Id); GI->ContractsPaid15.Remove(Id); for (int32 S = 0; S < 3; ++S) GI->ContractSigns15.Remove(Id * 4 + S); }
	for (int32 S = 0; S < 3; ++S) if (FRewardLaid15* R = ContractSignsLaid15.Find(Id * 4 + S)) { DropReward15(*R); ContractSignsLaid15.Remove(Id * 4 + S); }
	if (TWeakObjectPtr<ARDMonster>* B = ContractBeasts15.Find(Id)) { if (ARDMonster* M = B->Get()) M->Destroy(); ContractBeasts15.Remove(Id); }
}

ARDMonster* ARDDungeonGenerator::GetContractBeast15(int32 Id) const
{
	const TWeakObjectPtr<ARDMonster>* B = ContractBeasts15.Find(Id);
	return B ? B->Get() : nullptr;
}
