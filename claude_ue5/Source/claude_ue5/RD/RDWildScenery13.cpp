// The list of 2026-11-14 (docs/improvements13.txt): the biomes' scenery ("for these biomes: grasslands, meadows, plains, farms,
// savannahs, cold steppes, and burned plains, these are a list of scenery that are in them ..."; the lists for the forests, the high
// lands, the canyons, the volcanoes, the polar lands and the waters after it). The world places a piece of scenery in most cells of a
// 600 m grid (FRDWildWorld::SceneryIn: a kind of the region, beside a road, at a crossroads, on a rise, in a hollow or by water as its
// kind asks); here a chunk lays it by the ruins' layout language (LayWildParts: its pieces, landforms, effects and containers), and
// the game runs what it holds: what F does there (its uses: a hive's honey, a fishing spot, a notice post's rumour, a fairy ring by
// night), what hurts there (its hazards: a burrow's tunnels giving way, a hive's bees, something under a pond's surface), its herd
// (migrating across a road, stampeding when she comes too near), its ambush (monsters lying low in the tall grass) and the far
// storms over the open lands. Data: SourceArt/wilderness/scenery13.json (926).
#include "RD/RDDungeonGenerator.h"
#include "RD/RDWild.h"
#include "RD/RDGameInstance.h"
#include "RD/RDCombat.h"
#include "RD/RDMonster.h"
#include "RD/RDSection.h"
#include "Components/StaticMeshComponent.h"
#include "NiagaraComponent.h"
#include "NiagaraSystem.h"
#include "Engine/StaticMesh.h"
#include "Kismet/GameplayStatics.h"
#include "GameFramework/Character.h"
#include "RD/RDTown.h"

DEFINE_LOG_CATEGORY_STATIC(LogRDScen13, Log, All);

namespace
{
	/** a scenery's keys: its chests (7 << 40), its uses taken for good (8 << 40), each + its id x 8 + n (the structures' are 5 and 6) */
	constexpr int64 RDS13BoxKeys = 7LL << 40, RDS13UseKeys = 8LL << 40;
	/** a herd's beasts killed for good (9 << 40) + its id x 32 + n (PR #65's review: a herd laid again came back whole) */
	constexpr int64 RDS13HerdKeys = 9LL << 40;
	TMap<FString, FString> RDS13Parse(const FString& Line)
	{
		TMap<FString, FString> Out;
		TArray<FString> Kv; Line.ParseIntoArray(Kv, TEXT(";"), true);
		for (const FString& S : Kv) { FString K, V; if (S.Split(TEXT("="), &K, &V)) Out.Add(K.TrimStartAndEnd(), V.TrimStartAndEnd()); }
		return Out;
	}
	float RDS13Num(const TMap<FString, FString>& M, const TCHAR* K, float Def) { const FString* V = M.Find(K); return V && !V->IsEmpty() ? FCString::Atof(**V) : Def; }
	/** the hours a thing shows at: "" always, "day" 6:30-19:30, "night" 20:00-5:30, "dusk" 18:00-21:30 and 4:30-6:30 */
	bool RDS13InHours(const FString& Hours, float H)
	{
		if (Hours.IsEmpty()) return true;
		if (Hours == TEXT("day")) return H >= 6.5f && H < 19.5f;
		if (Hours == TEXT("night")) return H >= 20.f || H < 5.5f;
		if (Hours == TEXT("dusk")) return (H >= 18.f && H < 21.5f) || (H >= 4.5f && H < 6.5f);
		return true;
	}
	const TCHAR* RDS13Compass(const FVector2D& D)
	{
		static const TCHAR* N[8] = { TEXT("north"), TEXT("north-east"), TEXT("east"), TEXT("south-east"), TEXT("south"), TEXT("south-west"), TEXT("west"), TEXT("north-west") };
		const float A = FMath::RadiansToDegrees(FMath::Atan2(D.Y, D.X));
		return N[((int32)FMath::RoundToInt((A < 0.f ? A + 360.f : A) / 45.f)) % 8];
	}
}

// ------------------------------------------------------------------------------------------------ laying one
void ARDDungeonGenerator::LayWildScenery(ARDWildChunk* C, const FRDWildPlace& P)
{
	if (!C || !Wild || !WildSceneryKinds.IsValidIndex(P.Scenery)) return;
	const FRDWildSceneryKind& K = WildSceneryKinds[P.Scenery];
	FRandomStream R((int32)FRDWildWorld::Hash(P.Id, 0x1313, Wild->Seed));
	FRuinLaid Rec; Rec.Id = P.Id; Rec.Yaw = P.Yaw; Rec.At = P.At; Rec.Name = P.Name; Rec.Kind = P.Scenery;
	LayWildParts(C, P, K, P.At, P.At, P.Yaw, R, RDS13BoxKeys, Rec);
	Rec.Guards = K.Guards;
	if (K.Guards > 0) SpawnWildMonsters(C, P);
	const FRotator Frame(0.f, P.Yaw, 0.f);
	auto WorldOf = [&](const TMap<FString, FString>& M)
	{
		const FVector2D Xy = P.At + FVector2D(Frame.RotateVector(FVector(RDS13Num(M, TEXT("x"), 0.f), RDS13Num(M, TEXT("y"), 0.f), 0.0)));
		const FVector W(Xy.X * 100.0, Xy.Y * 100.0, 0.0);
		return FVector(W.X, W.Y, WildPartsGroundZ(W) + RDS13Num(M, TEXT("z"), 0.f) * 100.f);
	};
	// (what F does there)
	WildSceneryUses.RemoveAll([&](const FSceneryUse& U) { return U.Id == P.Id || !U.Chunk.IsValid(); });
	for (int32 I = 0; I < K.Uses.Num(); ++I)
	{
		const TMap<FString, FString> M = RDS13Parse(K.Uses[I]);
		FSceneryUse U; U.Id = P.Id; U.Kind = P.Scenery; U.Use = I; U.At = WorldOf(M); U.Reach = RDS13Num(M, TEXT("r"), 2.5f) * 100.f; U.Chunk = C;
		U.Reuse = RDS13Num(M, TEXT("reuse"), 0.f);          // (read once: the prompt asks every frame (PR #65's review))
		if (RDS13Num(M, TEXT("edge"), 0.f) > 0.5f && Rec.Comps.Num() > 0 && Rec.Comps[0].IsValid())
		{
			// (out along the frame's +X from the first piece's middle to the edge of its bounds, 1.5 m on: at its foot)
			const FBox Bb = Rec.Comps[0]->Bounds.GetBox();
			const FVector2D Dir(FMath::Cos(FMath::DegreesToRadians(P.Yaw)), FMath::Sin(FMath::DegreesToRadians(P.Yaw)));
			FVector2D Q(Bb.GetCenter());
			for (int32 St = 0; St < 400 && Bb.IsInsideXY(FVector(Q.X, Q.Y, Bb.GetCenter().Z)); ++St) Q += Dir * 25.0;
			Q += Dir * 150.0;
			U.At = FVector(Q.X, Q.Y, WildGroundZ(FVector(Q.X, Q.Y, 0.0)));
		}
		WildSceneryUses.Add(U);
	}
	// (what hurts there)
	// (a hazard's id is its scenery's x 8 + n (PR #65's review: compared with the scenery's own, the old ones were never taken out))
	WildSceneryHazards.RemoveAll([&](const FSceneryHazard& H) { return H.Id / 8 == P.Id || !H.Chunk.IsValid(); });
	for (int32 I = 0; I < K.Hazards.Num(); ++I)
	{
		const TMap<FString, FString> M = RDS13Parse(K.Hazards[I]);
		FSceneryHazard H; H.Id = P.Id * 8 + I; H.Kind = FName(*M.FindRef(TEXT("kind"))); H.At = WorldOf(M); H.R = RDS13Num(M, TEXT("r"), 5.f) * 100.f; H.P = RDS13Num(M, TEXT("p"), 1.f); H.Chunk = C;
		H.Who = M.FindRef(TEXT("who")); H.Hide = M.FindRef(TEXT("hide")); H.Named = M.FindRef(TEXT("named")); H.Msg = M.FindRef(TEXT("msg")); H.Count = FMath::Max(1, (int32)RDS13Num(M, TEXT("n"), 1.f));
		if (!H.Hide.IsEmpty())
		{
			// (the piece it moves: of the laid ones whose mesh's name has Hide in it, the nearest to its point by the piece's middle (a
			// snag that falls, a scarecrow that wakes)); where it stands, its turn, its foot and its height. (PR #66's review: only one
			// within 5 m of its point by the component's origin: ten snags over 18 m left about half the snags' hazards with none)
			float Best = 1e9f;
			for (const TWeakObjectPtr<UPrimitiveComponent>& Wc : Rec.Comps)
			{
				const UStaticMeshComponent* Sc = Cast<UStaticMeshComponent>(Wc.Get());
				if (!Sc || !Sc->GetStaticMesh() || !Sc->GetStaticMesh()->GetName().Contains(H.Hide)) continue;
				H.Cands.Add(Wc);
				const float D = FVector::Dist2D(Sc->Bounds.Origin, H.At);
				if (D < Best) { Best = D; H.Comp = Wc; }
			}
			if (UPrimitiveComponent* Hc = H.Comp.Get())
			{
				const FBox Bb = Hc->Bounds.GetBox();
				H.Rot0 = Hc->GetComponentQuat(); H.Loc0 = Hc->GetComponentLocation();
				H.Pivot = FVector(Bb.GetCenter().X, Bb.GetCenter().Y, Bb.Min.Z); H.Length = Bb.GetSize().Z;
			}
		}
		if (H.Kind == TEXT("hunt") && !H.Who.IsEmpty())
		{
			// (a waterhole's hunters: the predators that come for the herd now and then, laid with it, gone with its chunk)
			FRandomStream Rw((int32)FRDWildWorld::Hash(H.Id, 0x1318, Wild->Seed));
			for (int32 Hn = 0, N = FMath::Max(1, (int32)RDS13Num(M, TEXT("n"), 2.f)); Hn < N; ++Hn)
			{
				const float A = Rw.FRandRange(0.f, 2.f * PI);
				if (ARDWildAnimal* An = SpawnWildAnimalAt(FName(*H.Who), H.At + FVector(FMath::Cos(A), FMath::Sin(A), 0.f) * H.R * 1.2f)) { An->HerdId = P.Id; C->Props.Add(An); H.Hunters.Add(An); }
			}
		}
		WildSceneryHazards.Add(H);
	}
	// (its people: standing at their places, saying their own lines; the structures' list keeps them for F)
	for (int32 I = 0; I < K.Folk.Num(); ++I)
	{
		TArray<FString> F; K.Folk[I].ParseIntoArray(F, TEXT("|"), false);
		if (F.Num() < 3) continue;
		const int32 Def = Townsfolk.IndexOfByPredicate([&](const FRDTownsfolkDef& X) { return X.Mesh && X.Name.ToString().StartsWith(F[0]); });
		if (Def < 0) { UE_LOG(LogRDScen13, Warning, TEXT("RDSCEN %s: no townsfolk %s"), *K.Name.ToString(), *F[0]); continue; }
		const FVector2D Xy = P.At + FVector2D(Frame.RotateVector(FVector(F.Num() > 3 ? FCString::Atof(*F[3]) : 0.0, F.Num() > 4 ? FCString::Atof(*F[4]) : 0.0, 0.0)));
		const FVector Q(Xy.X * 100.0, Xy.Y * 100.0, WildPartsGroundZ(FVector(Xy.X * 100.0, Xy.Y * 100.0, 0.0)) + 92.f);
		FActorSpawnParameters Sp; Sp.SpawnCollisionHandlingOverride = ESpawnActorCollisionHandlingMethod::AlwaysSpawn;
		const float Yw = P.Yaw + 180.f;
		if (ARDTownsfolk* T = GetWorld()->SpawnActor<ARDTownsfolk>(ARDTownsfolk::StaticClass(), FTransform(FRotator(0, Yw, 0), Q), Sp))
		{
			T->Init(this, nullptr, Def, Q, Yw, 0.f, FRDWildWorld::Hash(P.Id, 0x1319 + I, Wild->Seed));
			T->SetTitle(F[1]);
			F[2].ParseIntoArray(T->OwnLines, TEXT("/"), true);
			WildSiteFolk.Add(T);
			C->Props.Add(T);
		}
	}
	// (its effects, shown at their hours)
	for (int32 I = 0; I < Rec.Fx.Num(); ++I) WildSceneryFxOn.Add({ Rec.Fx[I], Rec.FxHours.IsValidIndex(I) ? Rec.FxHours[I] : FString() });
	// (its herd: the beasts round its middle, going with its chunk)
	WildSceneryHerds.RemoveAll([&](const FSceneryHerd& H) { return H.Id == P.Id; });
	if (!K.Herd.IsEmpty())
	{
		const TMap<FString, FString> M = RDS13Parse(K.Herd);
		FString First, Rest; K.Herd.Split(TEXT(";"), &First, &Rest); if (First.IsEmpty()) First = K.Herd;
		FString Kind, Count; if (!First.Split(TEXT(":"), &Kind, &Count)) { Kind = First; Count = TEXT("6"); }
		FSceneryHerd Hd; Hd.Id = P.Id; Hd.Home = P.At; Hd.Way = FVector2D(FMath::Cos(FMath::DegreesToRadians(P.Yaw)), FMath::Sin(FMath::DegreesToRadians(P.Yaw)));
		Hd.bMigrate = RDS13Num(M, TEXT("migrate"), 0.f) > 0.5f; Hd.bStampede = RDS13Num(M, TEXT("stampede"), 0.f) > 0.5f;
		// (a pen: the herd kept within it (metres round its middle, moved by x, y), as a shepherd's goats)
		Hd.Pen = RDS13Num(M, TEXT("pen"), 0.f);
		if (Hd.Pen > 0.f) Hd.Home = P.At + FVector2D(Frame.RotateVector(FVector(RDS13Num(M, TEXT("x"), 0.f), RDS13Num(M, TEXT("y"), 0.f), 0.0)));
		FRandomStream Rh((int32)FRDWildWorld::Hash(P.Id, 0x1314, Wild->Seed));
		const int32 N = FMath::Clamp(FCString::Atoi(*Count), 1, 30);
		const float Spread = RDS13Num(M, TEXT("r"), 18.f) * 100.f;
		const URDGameInstance* GI = URDGameInstance::Of(this);
		for (int32 I = 0; I < N; ++I)
		{
			// (every beast's draws made, its killed ones left out: the others keep their places)
			const float A = Rh.FRandRange(0.f, 2.f * PI), D = FMath::Sqrt(Rh.FRand()) * (Hd.Pen > 0.f ? Hd.Pen * 60.f : Spread);
			if (GI && GI->WildKilled.Contains(RDS13HerdKeys + (int64)(uint32)P.Id * 32 + I)) continue;
			if (ARDWildAnimal* An = SpawnWildAnimalAt(FName(*Kind.TrimStartAndEnd()), FVector(Hd.Home.X * 100.0 + FMath::Cos(A) * D, Hd.Home.Y * 100.0 + FMath::Sin(A) * D, 0.0)))
			{
				An->HerdId = P.Id; An->HerdIndex = I;
				C->Props.Add(An);
				Hd.Animals.Add(An);
			}
		}
		if (Hd.Animals.Num() > 0) WildSceneryHerds.Add(Hd);
	}
	WildSceneryLaid.RemoveAll([&](const FRuinLaid& X) { return X.Id == P.Id; });
	WildSceneryLaid.Add(Rec);
	WildPartsLand.Reset();          // (its rises: done with, for what is laid next)
	UE_LOG(LogRDScen13, Log, TEXT("RDSCEN %s (%s): %d pieces, %d boxes, %d fx, %d uses, %d hazards at (%.0f, %.0f)"), *P.Name, *K.Name.ToString(), Rec.Pieces, Rec.Boxes, Rec.Fx.Num(), K.Uses.Num(), K.Hazards.Num(), P.At.X, P.At.Y);
}

// ------------------------------------------------------------------------------------------------ the game round her
void ARDDungeonGenerator::TickWildScenery13(float Dt, const FVector& Her)
{
	if (!IsWildReady() || !PlayerCombat) return;
	UWorld* W = GetWorld();
	const float Now = W->GetTimeSeconds();
	const FVector2D H2(Her.X / 100.0, Her.Y / 100.0);
	TickWildStorm13(Dt, Her);
	// ---- the hazards, every frame (a handful near her)
	const ACharacter* Ch = Cast<ACharacter>(UGameplayStatics::GetPlayerPawn(this, 0));
	const float Feet = Her.Z - (Ch ? Ch->GetSimpleCollisionHalfHeight() : 90.f);
	if (!PlayerCombat->IsDead())
		for (FSceneryHazard& Hz : WildSceneryHazards)
		{
			if (!Hz.Chunk.IsValid()) continue;
			const float D = FVector::Dist2D(Hz.At, Her);
			const bool bIn = D < Hz.R && FMath::Abs(Feet - Hz.At.Z) < 250.f;
			if (Hz.Kind == TEXT("collapse"))
			{
				// (a burrow town's tunnels: the ground gives way under her, and what dug them comes up once)
				if (!bIn || Now < Hz.ReadyAt) continue;
				Hz.ReadyAt = Now + 25.f; ++Hz.Sprung; ++WildHazardsSprung;
				PlayerCombat->HurtByTrap(0.06f * Hz.P, 0.5f, 2.5f, TEXT("The ground gives way into a tunnel"));
				// (its diggers: of the monsters whose name says so, else the region's; 5 m round her (PR #66's review: one rule for a
				// scenery's monsters, SpawnSceneryMonsters))
				if (Hz.Sprung == 1 && bCombat) SpawnSceneryMonsters(Hz.Chunk.Get(), TEXT("Rat+Pangolin"), 2, FString(), Her, (uint32)Hz.Id, 500.f, 0.7f, 40.f);
				UE_LOG(LogRDScen13, Log, TEXT("RDSCENHAZ collapse at (%.0f, %.0f), %d"), Hz.At.X, Hz.At.Y, Hz.Sprung);
			}
			else if (Hz.Kind == TEXT("sting"))
			{
				// (a hive's bees: she lingers by it a breath and a half, and they come out at her while she stays near)
				Hz.In = bIn ? Hz.In + Dt : FMath::Max(0.f, Hz.In - Dt * 2.f);
				if (Hz.In < 1.5f || Now < Hz.ReadyAt) continue;
				Hz.ReadyAt = Now + 1.4f; ++Hz.Sprung; ++WildHazardsSprung;
				PlayerCombat->HurtByTrap(0.03f * Hz.P, 0.15f, 1.f, TEXT("Bees! The hive's swarm stings you"));
			}
			else if (Hz.Kind == TEXT("heat"))
			{
				// (smouldering ground: a burn every second she stands on it)
				if (!bIn || Now < Hz.ReadyAt) continue;
				Hz.ReadyAt = Now + 1.f; ++Hz.Sprung; ++WildHazardsSprung;
				PlayerCombat->HurtByTrap(0.025f * Hz.P, 0.f, 0.f, TEXT("The ground smoulders under you"));
			}
			else if (Hz.Kind == TEXT("wakes"))
			{
				// (one of the scarecrows is not a scarecrow: as she comes near it, it is gone and what it was stands there, once a play)
				if (!bIn || WildScenerySprung.Contains(Hz.Id)) continue;
				WildScenerySprung.Add(Hz.Id); ++Hz.Sprung; ++WildHazardsSprung;
				FVector L = Hz.At;
				if (UPrimitiveComponent* Hc = Hz.Comp.Get()) { L = FVector(Hc->Bounds.Origin.X, Hc->Bounds.Origin.Y, Hz.At.Z); Hc->SetVisibility(false); Hc->SetCollisionEnabled(ECollisionEnabled::NoCollision); }
				else
				{
					// (nothing hidden that it was: it rises 8 m from her, toward the hazard's middle (phase 2: risen where she stood, the
					// Ash Wyrm never stood at all))
					FVector2D Dh = FVector2D(Hz.At) - FVector2D(Her);
					if (Dh.Size() < 300.f) { const float Ah = (Hz.Id % 360) * PI / 180.f; Dh = FVector2D(FMath::Cos(Ah), FMath::Sin(Ah)); }
					Dh.Normalize();
					L = FVector(Her.X + Dh.X * 800.f, Her.Y + Dh.Y * 800.f, Hz.At.Z);
				}
				SpawnSceneryMonsters(Hz.Chunk.Get(), Hz.Who, Hz.Count, Hz.Named, L, (uint32)Hz.Id);
				PlayerCombat->ShowMessage(!Hz.Msg.IsEmpty() ? Hz.Msg : FString::Printf(TEXT("%s turns its head toward you."), Hz.Named.IsEmpty() ? TEXT("The scarecrow") : *Hz.Named));
			}
			else if (Hz.Kind == TEXT("fall"))
			{
				// (a charred snag: as she comes near it falls, toward her, over 1.2 s; under it at the end, a heavy blow)
				if (Hz.Start < 0.f)
				{
					if (!bIn) continue;
					// (the snag nearest her comes down (PR #66's review: the one bound by the hazard's point could stand 18 m off her))
					float Bd = 1e18f;
					for (const TWeakObjectPtr<UPrimitiveComponent>& Wc : Hz.Cands)
						if (UPrimitiveComponent* Cc = Wc.Get()) { const float Dd = FVector::DistSquared2D(Cc->Bounds.Origin, Her); if (Dd < Bd) { Bd = Dd; Hz.Comp = Wc; } }
					UPrimitiveComponent* Hn = Hz.Comp.Get();
					if (!Hn) continue;
					const FBox Bb = Hn->Bounds.GetBox();
					Hz.Rot0 = Hn->GetComponentQuat(); Hz.Loc0 = Hn->GetComponentLocation();
					Hz.Pivot = FVector(Bb.GetCenter().X, Bb.GetCenter().Y, Bb.Min.Z); Hz.Length = Bb.GetSize().Z;
					Hz.Start = Now; Hz.FallDir = (FVector2D(Her) - FVector2D(Hz.Pivot)).GetSafeNormal(); ++WildHazardsSprung;
					if (Hz.FallDir.IsNearlyZero()) Hz.FallDir = FVector2D(1, 0);
					PlayerCombat->ShowMessage(TEXT("A crack overhead: the burned tree is coming down!"));
				}
				UPrimitiveComponent* Hc = Hz.Comp.Get();
				if (!Hc) continue;
				const float T = FMath::Clamp((Now - Hz.Start) / 1.2f, 0.f, 1.f);
				if (Hz.Sprung > 0) continue;
				const FVector Axis = FVector::CrossProduct(FVector::UpVector, FVector(Hz.FallDir, 0.0)).GetSafeNormal();
				const FQuat Q(Axis, FMath::DegreesToRadians(84.f * T * T));
				Hc->SetWorldLocationAndRotation(Hz.Pivot + Q.RotateVector(Hz.Loc0 - Hz.Pivot), Q * Hz.Rot0);
				if (T < 1.f) continue;
				++Hz.Sprung;
				const FVector2D Dh = FVector2D(Her) - FVector2D(Hz.Pivot);
				const float Along = (float)FVector2D::DotProduct(Dh, Hz.FallDir), Across = (float)FMath::Abs(FVector2D::CrossProduct(Hz.FallDir, Dh));
				if (Along > 0.f && Along < Hz.Length && Across < 160.f) PlayerCombat->HurtByTrap(0.15f * Hz.P, 0.4f, 2.f, TEXT("The burned tree crashes down on you"));
			}
			else if (Hz.Kind == TEXT("hunt"))
			{
				// (a waterhole's hunt: while she is near, now and then a predator runs down one of the herd, and the herd scatters)
				ARDWildAnimal* Prey = Hz.Prey.Get();
				ARDWildAnimal* Hunter = nullptr;
				for (const TWeakObjectPtr<ARDWildAnimal>& Wh : Hz.Hunters) if (ARDWildAnimal* A = Wh.Get(); A && !A->IsDead()) { Hunter = A; break; }
				if (!Hunter) continue;
				if (Prey && !Prey->IsDead())
				{
					if (FVector::Dist2D(Hunter->GetActorLocation(), Prey->GetActorLocation()) < 260.f)
					{
						bWildPredatorKill = true; Prey->TakeHit(1e6f, Hunter->GetActorLocation()); bWildPredatorKill = false; ++Hz.Kills; ++Hz.Sprung; ++WildHazardsSprung; Hz.Prey.Reset();
						if (FSceneryHerd* Hd = WildSceneryHerds.FindByPredicate([&](const FSceneryHerd& X) { return X.Id == Hz.Id / 8; }))
							for (const TWeakObjectPtr<ARDWildAnimal>& Wa : Hd->Animals)
								if (ARDWildAnimal* A = Wa.Get(); A && !A->IsDead())
								{
									const FVector Away = (A->GetActorLocation() - Hunter->GetActorLocation()).GetSafeNormal2D();
									A->Drive(A->GetActorLocation() + Away * 6000.f, true, 8.f);
								}
						Hunter->Drive(Hunter->GetActorLocation(), false, 20.f);
					}
					else if (Now >= Hz.In) { Hunter->Drive(Prey->GetActorLocation(), true, 3.f); Hz.In = Now + 0.4f; }
					continue;
				}
				if (D > Hz.R || Now < Hz.ReadyAt) continue;
				Hz.ReadyAt = Now + 60.f;
				const FSceneryHerd* Hd = WildSceneryHerds.FindByPredicate([&](const FSceneryHerd& X) { return X.Id == Hz.Id / 8; });
				if (!Hd) continue;
				float Best = 1e9f;
				for (const TWeakObjectPtr<ARDWildAnimal>& Wa : Hd->Animals)
					if (ARDWildAnimal* A = Wa.Get(); A && !A->IsDead()) { const float Dd = FVector::Dist2D(A->GetActorLocation(), Hunter->GetActorLocation()); if (Dd < Best) { Best = Dd; Hz.Prey = A; } }
				if (Hz.Prey.IsValid()) { Hunter->Drive(Hz.Prey->GetActorLocation(), true, 3.f); Hz.In = Now + 0.4f; }
			}
			else if (Hz.Kind == TEXT("lurker"))
			{
				// (something under a pond's surface: she wades in near it, and it rises, once a play)
				if (!bIn || WildScenerySprung.Contains(Hz.Id)) continue;
				FRDWSample S; Wild->Sample(H2.X, H2.Y, S, false);
				if (S.WaterKind == 0 || Wild->ToZ(S.Water) < Feet + 10.f) continue;
				WildScenerySprung.Add(Hz.Id); ++Hz.Sprung; ++WildHazardsSprung;
				PlayerCombat->ShowMessage(TEXT("Something rises from under the surface!"));
				if (bCombat)
				{
					TArray<int32> Kinds; WildKindsForTier(Wild->TierAt(H2.X, H2.Y), Kinds);
					TArray<int32> Wet; for (int32 Ki = 0; Ki < Monsters.Num(); ++Ki) if (Monsters[Ki].Mesh && (Monsters[Ki].Name.ToString().Contains(TEXT("Drown")) || Monsters[Ki].Name.ToString().Contains(TEXT("Deep")) || Monsters[Ki].Name.ToString().Contains(TEXT("Croc")))) Wet.Add(Ki);
					if (Wet.Num() > 0) Kinds = Wet;
					if (Kinds.Num() > 0)
					{
						FRandomStream Rm((int32)FRDWildWorld::Hash(Hz.Id, 0x1316, Wild->Seed));
						FVector L(Her.X + 350.f, Her.Y, 0.f); L.Z = WildGroundZ(L);
						if (ARDMonster* Mo = SpawnWildMonsterAt(Monsters[Kinds[Rm.RandRange(0, Kinds.Num() - 1)]], L, 180.f, (int32)Rm.GetUnsignedInt(), Wild->TierAt(H2.X, H2.Y), 1.f, TEXT("Thing in the Pond")))
						{ Mo->bHunting = true; Mo->HuntUntil = Now + 60.f; if (Hz.Chunk.IsValid()) Hz.Chunk->Props.Add(Mo); }
					}
				}
			}
		}
	// ---- the herds: the stampede's trampling every frame, their walking four times a second
	WildSceneryHerds.RemoveAll([](const FSceneryHerd& Hd) { return !Hd.Animals.ContainsByPredicate([](const TWeakObjectPtr<ARDWildAnimal>& A) { return A.IsValid(); }); });
	for (FSceneryHerd& Hd : WildSceneryHerds)
	{
		if (Now >= Hd.StampedeUntil || PlayerCombat->IsDead() || Now < Hd.NextHit) continue;
		for (const TWeakObjectPtr<ARDWildAnimal>& Wa : Hd.Animals)
		{
			const ARDWildAnimal* A = Wa.Get();
			if (!A || A->IsDead() || FVector::Dist2D(A->GetActorLocation(), Her) > A->BodyRadius() + 70.f) continue;
			Hd.NextHit = Now + 1.f; ++Hd.Hits;
			PlayerCombat->HurtByTrap(0.08f, 0.35f, 1.2f, TEXT("Trampled by the stampede"));
			break;
		}
	}
	WildSceneryLook -= Dt;
	if (WildSceneryLook > 0.f) return;
	WildSceneryLook = 0.25f;
	// (the ones laid far from her are gone with their chunks)
	WildSceneryLaid.RemoveAll([&](const FRuinLaid& X) { return FVector2D::Distance(X.At, H2) > 3000.f; });
	WildSceneryUses.RemoveAll([](const FSceneryUse& U) { return !U.Chunk.IsValid(); });
	WildSceneryHazards.RemoveAll([](const FSceneryHazard& Hz) { return !Hz.Chunk.IsValid(); });
	WildSceneryFxOn.RemoveAll([](const FSceneryFx& F) { return !F.Comp.IsValid(); });
	// (the effects by the hour)
	for (const FSceneryFx& F : WildSceneryFxOn)
	{
		UNiagaraComponent* Nc = F.Comp.Get();
		const bool bOn = RDS13InHours(F.Hours, TownHour);
		if (bOn != Nc->IsVisible()) { Nc->SetVisibility(bOn); if (bOn) Nc->Activate(true); else Nc->Deactivate(); }
	}
	// (told as she comes: its name and a line of what it is; an ambush sprung as she comes within its reach)
	for (const FRuinLaid& X : WildSceneryLaid)
	{
		if (!WildSceneryKinds.IsValidIndex(X.Kind)) continue;
		const FRDWildSceneryKind& K = WildSceneryKinds[X.Kind];
		const float D = FVector2D::Distance(X.At, H2);
		// (phase 2: told once no other line is under 2 s old: a farmstead discovered in the same tick hid the old orchard's line)
		if (!WildSceneryTold.Contains(X.Id) && D < 35.f && Now - PlayerCombat->MessageTime >= 2.f)
		{
			WildSceneryTold.Add(X.Id); WildSceneryToldAt.Add(X.Id, Now);
			PlayerCombat->ShowMessage(FString::Printf(TEXT("%s: %s"), *K.Title, *K.Text));
			WildLastEngaged = Now;
			WildEngagements.Add(FString::Printf(TEXT("%.1f|scenery|%s|%.0f|%.0f"), Now, *K.Name.ToString(), X.At.X, X.At.Y));
		}
		if (K.AmbushR > 0.f && WildSection && !WildScenerySprung.Contains(-X.Id - 1))
		{
			const bool bSpring = D < K.AmbushR;
			for (ARDMonster* Mo : WildSection->SpawnedMonsters)
			{
				if (!IsValid(Mo) || Mo->IsDead() || Mo->WildKey < 0 || Mo->WildKey / 16 != (int64)X.Id) continue;
				if (!bSpring) { Mo->NoticeCap = 250.f; continue; }
				Mo->NoticeCap = -1.f; Mo->bHunting = true; Mo->HuntUntil = Now + 45.f;
			}
			if (bSpring)
			{
				WildScenerySprung.Add(-X.Id - 1); ++WildHazardsSprung;
				PlayerCombat->ShowMessage(TEXT("The grass moves against the wind: something was lying in wait!"));
				UE_LOG(LogRDScen13, Log, TEXT("RDSCENAMBUSH %s at %.0f m"), *K.Name.ToString(), D);
			}
		}
	}
	// (the herds: a migration walks its herd back and forth along its way across 140 m; a stampede sets it running when she comes
	// within 16 m (or a test sets it off), through and past her)
	for (FSceneryHerd& Hd : WildSceneryHerds)
	{
		// (a herd far from her rests: its beasts' ticks off past 250 m (PR #65's review: every herd of the chunks laid ticked))
		for (const TWeakObjectPtr<ARDWildAnimal>& Wa : Hd.Animals)
			if (ARDWildAnimal* A = Wa.Get(); A && !A->IsDead()) A->SetDormant(FVector2D::Distance(FVector2D(A->GetActorLocation()) / 100.0, H2) > 250.0);
		FVector2D Mid(0, 0); int32 N = 0;
		for (const TWeakObjectPtr<ARDWildAnimal>& Wa : Hd.Animals) if (const ARDWildAnimal* A = Wa.Get(); A && !A->IsDead()) { Mid += FVector2D(A->GetActorLocation()) / 100.0; ++N; }
		if (N == 0) continue;
		Mid /= N;
		const float* Told = WildSceneryToldAt.Find(Hd.Id);
		if (Hd.bStampede && Hd.StampedeUntil < 0.f && FVector2D::Distance(Mid, H2) < 16.f && (!Told || Now - *Told > 3.f)) StartWildStampede(Hd.Id);
		if (Now < Hd.StampedeUntil) continue;
		if (Hd.Pen > 0.f)
		{
			// (one wandered out of its pen walks back in, to a spot within its inner half)
			for (const TWeakObjectPtr<ARDWildAnimal>& Wa : Hd.Animals)
			{
				ARDWildAnimal* A = Wa.Get();
				if (!A || A->IsDead() || A->GetState() == 3) continue;
				if (FVector2D::Distance(FVector2D(A->GetActorLocation()) / 100.0, Hd.Home) < Hd.Pen * 0.85f) continue;
				const float Ang = FMath::Frac(Now * 0.37f + A->Def) * 2.f * PI;
				A->Drive(FVector((Hd.Home.X + FMath::Cos(Ang) * Hd.Pen * 0.4f) * 100.0, (Hd.Home.Y + FMath::Sin(Ang) * Hd.Pen * 0.4f) * 100.0, 0.0), false, 6.f);
			}
			continue;
		}
		if (!Hd.bMigrate) continue;
		Hd.Phase += 0.25f * 0.045f;
		const FVector2D Goal = Hd.Home + Hd.Way * 70.0 * FMath::Sin(Hd.Phase);
		for (const TWeakObjectPtr<ARDWildAnimal>& Wa : Hd.Animals)
		{
			ARDWildAnimal* A = Wa.Get();
			if (!A || A->IsDead() || A->GetState() == 3) continue;
			if (A->GetState() == 2 && FMath::Frac(Now * 0.25f + A->Def * 0.37f) > 0.1f) continue;
			const FVector2D Off = (FVector2D(A->GetActorLocation()) / 100.0 - Mid).GetClampedToMaxSize(15.0);
			A->Drive(FVector((Goal.X + Off.X) * 100.0, (Goal.Y + Off.Y) * 100.0, 0.0), false, 6.f);
		}
	}
}

void ARDDungeonGenerator::SpawnSceneryMonsters(ARDWildChunk* C, const FString& Who, int32 N, const FString& Named, const FVector& At, uint32 Salt, float Ring, float Hp, float Hunt)
{
	if (!bCombat || !IsWildReady() || !GetWorld()) return;
	const FVector2D A2(At.X / 100.0, At.Y / 100.0);
	TArray<int32> Kinds; WildKindsForTier(Wild->TierAt(A2.X, A2.Y), Kinds);
	TArray<FString> Parts; Who.ParseIntoArray(Parts, TEXT("+"), true);
	TArray<int32> Named2;
	for (int32 Ki = 0; Ki < Monsters.Num(); ++Ki)
		if (Monsters[Ki].Mesh && Parts.ContainsByPredicate([&](const FString& Pt) { return Monsters[Ki].Name.ToString().Contains(Pt, ESearchCase::CaseSensitive); })) Named2.Add(Ki);
	if (Named2.Num() > 0) Kinds = Named2;
	if (Kinds.Num() == 0) return;
	FRandomStream Rm((int32)FRDWildWorld::Hash((int32)Salt, 0x131A, Wild->Seed));
	const APawn* Her = UGameplayStatics::GetPlayerPawn(this, 0);
	const float Now = GetWorld()->GetTimeSeconds();
	for (int32 I = 0; I < FMath::Clamp(N, 1, 8); ++I)
	{
		const float A = Rm.FRandRange(0.f, 2.f * PI), D = Ring > 0.f ? Ring : N > 1 ? Rm.FRandRange(100.f, 350.f) : 0.f;
		FVector L(At.X + FMath::Cos(A) * D, At.Y + FMath::Sin(A) * D, 0.f); L.Z = WildGroundZ(L);
		const float Yaw = Ring > 0.f ? FMath::RadiansToDegrees(A) + 180.f : Her ? FMath::RadiansToDegrees(FMath::Atan2(Her->GetActorLocation().Y - L.Y, Her->GetActorLocation().X - L.X)) : 0.f;
		if (ARDMonster* Mo = SpawnWildMonsterAt(Monsters[Kinds[Rm.RandRange(0, Kinds.Num() - 1)]], L, Yaw, (int32)Rm.GetUnsignedInt(), Wild->TierAt(A2.X, A2.Y), Hp, Named))
		{ Mo->bHunting = true; Mo->HuntUntil = Now + Hunt; if (C) C->Props.Add(Mo); }
	}
}

bool ARDDungeonGenerator::StartWildStampede(int32 Id)
{
	FSceneryHerd* Hd = WildSceneryHerds.FindByPredicate([&](const FSceneryHerd& X) { return X.Id == Id; });
	const APawn* Her = UGameplayStatics::GetPlayerPawn(this, 0);
	if (!Hd || !Her || !GetWorld()) return false;
	const float Now = GetWorld()->GetTimeSeconds();
	FVector2D Mid(0, 0); int32 N = 0;
	for (const TWeakObjectPtr<ARDWildAnimal>& Wa : Hd->Animals) if (const ARDWildAnimal* A = Wa.Get(); A && !A->IsDead()) { Mid += FVector2D(A->GetActorLocation()) / 100.0; ++N; }
	if (N == 0) return false;
	Mid /= N;
	// (along the herd's way, toward her side: through where she stands and 90 m past it)
	const FVector2D H2 = FVector2D(Her->GetActorLocation()) / 100.0;
	const FVector2D Dir = FVector2D::DotProduct(H2 - Mid, Hd->Way) >= 0.0 ? Hd->Way : -Hd->Way;
	for (const TWeakObjectPtr<ARDWildAnimal>& Wa : Hd->Animals)
	{
		ARDWildAnimal* A = Wa.Get();
		if (!A || A->IsDead()) continue;
		const FVector2D From = FVector2D(A->GetActorLocation()) / 100.0;
		// (each on its own line along the way, the herd's spread across it kept, that line passing by her within a few metres)
		const FVector2D Side(-Dir.Y, Dir.X);
		const float Across = FMath::Clamp((float)FVector2D::DotProduct(From - H2, Side), -6.f, 6.f);
		const FVector2D To = H2 + Side * Across + Dir * 90.0;
		A->Drive(FVector(To.X * 100.0, To.Y * 100.0, 0.0), true, 9.f);
	}
	Hd->StampedeUntil = Now + 8.f; ++Hd->Stampedes;
	if (PlayerCombat) PlayerCombat->ShowMessage(TEXT("The herd panics: a stampede comes thundering your way!"));
	++WildHazardsSprung;
	UE_LOG(LogRDScen13, Log, TEXT("RDSCENSTAMPEDE herd %d: %d beasts"), Id, N);
	return true;
}

// ------------------------------------------------------------------------------------------------ F at one
bool ARDDungeonGenerator::WildSceneryFirst(const FVector& From) const
{
	// (the nearest of a scenery's use, a point of interest, a wild door or container and a person takes F (PR #65's review: the
	// battlefield's search took F from its chest 4.5 m from it))
	const FSceneryUse* U = WildSceneryUseNear(From);
	if (!U) return false;
	const float Du = FVector::Dist2D(U->At, From);
	if (const FRDWildPoiLive* P = WildPoiNear(From, 320.f); P && FVector::Dist2D(P->At, From) < Du) return false;
	int32 Di = -1;
	if (const ARDWildChunk* C = bWildHouseInsides ? WildDoorNear(From, 190.f, Di) : nullptr; C && C->Doors.IsValidIndex(Di) && FVector::Dist2D(C->Doors[Di].At, From) < Du) return false;
	if (const ARDTownsfolk* T = WildFolkForF(From); T && FVector::Dist2D(T->GetActorLocation(), From) < Du) return false;
	return true;
}

bool ARDDungeonGenerator::IsWildSceneryUsed(const FSceneryUse& U) const
{
	if (!WildSceneryKinds.IsValidIndex(U.Kind) || !WildSceneryKinds[U.Kind].Uses.IsValidIndex(U.Use)) return true;
	const int64 Key = RDS13UseKeys + (int64)(uint32)U.Id * 8 + U.Use;
	if (U.Reuse > 0.f) { const float* R = WildSceneryReadyAt.Find((int32)(Key & 0x7FFFFFFF)); return R && GetWorld() && GetWorld()->GetTimeSeconds() < *R; }
	const URDGameInstance* GI = URDGameInstance::Of(this);
	return GI && GI->WildKilled.Contains(Key);
}

const ARDDungeonGenerator::FSceneryUse* ARDDungeonGenerator::WildSceneryUseNear(const FVector& From) const
{
	const FSceneryUse* Best = nullptr; float BestD = 1e9f;
	for (const FSceneryUse& U : WildSceneryUses)
	{
		if (!U.Chunk.IsValid()) continue;
		const float D = FVector::Dist2D(U.At, From);
		if (D > U.Reach || D >= BestD || FMath::Abs(U.At.Z - From.Z) > 300.f || IsWildSceneryUsed(U)) continue;
		BestD = D; Best = &U;
	}
	return Best;
}

FString ARDDungeonGenerator::WildSceneryDescribe(const FVector& From) const
{
	const FSceneryUse* U = WildSceneryUseNear(From);
	if (!U) return FString();
	const TMap<FString, FString> M = RDS13Parse(WildSceneryKinds[U->Kind].Uses[U->Use]);
	const FString Do = M.FindRef(TEXT("do"));
	FString Verb = M.FindRef(TEXT("verb"));
	if (Verb.IsEmpty())
		Verb = Do == TEXT("loot") ? TEXT("search") : Do == TEXT("honey") ? TEXT("take honey from") : Do == TEXT("fish") ? TEXT("fish at") : Do == TEXT("forage") ? TEXT("gather from")
		     : Do == TEXT("milestone") || Do == TEXT("rumour") ? TEXT("read") : Do == TEXT("heal") ? TEXT("rest at") : Do == TEXT("buff") ? TEXT("pray at") : Do == TEXT("fairy") ? TEXT("step into")
		     : Do == TEXT("offer") ? TEXT("leave an offering at") : Do == TEXT("trade") ? TEXT("trade at") : TEXT("look at");
	FString What = M.FindRef(TEXT("what"));
	if (What.IsEmpty()) What = WildSceneryKinds[U->Kind].Title.ToLower();
	return FString::Printf(TEXT("%s the %s"), *Verb, *What);
}

FString ARDDungeonGenerator::WildSceneryInteract(const FVector& From)
{
	const FSceneryUse* Up = WildSceneryUseNear(From);
	if (!Up || !PlayerCombat || !IsWildReady()) return FString();
	const FSceneryUse U = *Up;
	const FRDWildSceneryKind& K = WildSceneryKinds[U.Kind];
	const TMap<FString, FString> M = RDS13Parse(K.Uses[U.Use]);
	const FString Do = M.FindRef(TEXT("do"));
	const float Now = GetWorld()->GetTimeSeconds();
	FString Said = M.FindRef(TEXT("text"));
	FRandomStream R((int32)HashCombine((uint32)U.Id, (uint32)FMath::RoundToInt(Now * 10.f)));
	auto Give = [&]()
	{
		TArray<FString> Things; M.FindRef(TEXT("things")).ParseIntoArray(Things, TEXT(","), true);
		TArray<FName> Got = RollWildThings(Things, R);
		// (a search always finds something: its first thing when every chance failed (the battlefield's iron came as "nothing" one time
		// in five, under a line saying she pried it loose))
		if (Got.Num() == 0 && Things.Num() > 0) { FString First; Things[0].Split(TEXT("|"), &First, nullptr); if (FindItem(FName(*First)) >= 0) Got.Add(FName(*First)); }
		TMap<FName, int32> N; for (const FName& G : Got) N.FindOrAdd(G) += 1;
		TArray<FString> Parts;
		for (const auto& Kv : N) { PlayerCombat->AddItem(Kv.Key, Kv.Value); Parts.Add(FString::Printf(TEXT("%d %s"), Kv.Value, *Kv.Key.ToString())); }
		return Parts.Num() > 0 ? FString::Join(Parts, TEXT(", ")) : FString(TEXT("nothing"));
	};
	if (Do == TEXT("fairy") && !RDS13InHours(TEXT("night"), TownHour))
	{
		PlayerCombat->ShowMessage(TEXT("Nothing stirs in the ring by daylight. Come back after dark."));
		return TEXT("scenery");
	}
	if (Do == TEXT("loot") || Do == TEXT("forage") || Do == TEXT("fish") || Do == TEXT("honey"))
	{
		const FString Got = Give();
		Said = FString::Printf(TEXT("%s%sYou take %s"), *Said, Said.IsEmpty() ? TEXT("") : TEXT("  "), *Got);
		// (a hive defended: half the time its bees come out at her)
		if (Do == TEXT("honey") && R.FRand() < 0.5f) PlayerCombat->HurtByTrap(0.04f, 0.15f, 1.f, TEXT("The bees defend their hive"));
	}
	else if (Do == TEXT("climb"))
	{
		// (up a boulder or a butte: she is set on its top (traced down at tx, ty from tz + 4 m), and the land round it shows on the map
		// (reveal metres): "good for climbing and vantage points")
		APawn* Her = UGameplayStatics::GetPlayerPawn(this, 0);
		FVector Top = FVector::ZeroVector; bool bTop = false;
		for (const FRuinLaid& X : WildSceneryLaid)
		{
			if (X.Id != U.Id) continue;
			const FVector2D Txy = X.At + FVector2D(FRotator(0.f, X.Yaw, 0.f).RotateVector(FVector(RDS13Num(M, TEXT("tx"), 0.f), RDS13Num(M, TEXT("ty"), 0.f), 0.0)));
			const float G = WildGroundZ(FVector(Txy.X * 100.0, Txy.Y * 100.0, 0.0));
			FHitResult Hit;
			FCollisionQueryParams Qp(SCENE_QUERY_STAT(RDScenClimb), true); if (Her) Qp.AddIgnoredActor(Her);
			const FVector Above(Txy.X * 100.0, Txy.Y * 100.0, G + (RDS13Num(M, TEXT("tz"), 5.f) + 4.f) * 100.f);
			if (GetWorld()->LineTraceSingleByChannel(Hit, Above, FVector(Above.X, Above.Y, G - 100.f), ECC_WorldStatic, Qp) && Hit.ImpactPoint.Z > G + 150.f) { Top = Hit.ImpactPoint; bTop = true; }
			break;
		}
		if (!bTop || !Her) { PlayerCombat->ShowMessage(TEXT("There is no way up from here.")); return TEXT("scenery"); }
		Her->SetActorLocation(Top + FVector(0, 0, 100.f), false, nullptr, ETeleportType::TeleportPhysics);
		const float Rv = RDS13Num(M, TEXT("reveal"), 0.f);
		if (Rv > 0.f) RevealWild(FVector2D(Top) / 100.0, Rv);
		if (Said.IsEmpty()) Said = TEXT("You climb to the top.");
		if (Rv > 0.f) Said += FString::Printf(TEXT("  From up here you can see %.1f km round you: the map fills in."), Rv / 1000.f);
	}
	else if (Do == TEXT("tracks"))
	{
		// (a wallow's tracks: of what lairs nearest within 3 km, which way and how far)
		FRDWildPlace Got; FVector2D At;
		const FVector2D F2(From.X / 100.0, From.Y / 100.0);
		if (FindNearestWildPlace(F2.X, F2.Y, 3.f, [&](const FRDWildPlace& P, FVector2D& A) { if (P.Kind != TEXT("lair") && P.Kind != TEXT("spawn")) return false; A = P.At; return true; }, Got, At))
			Said = FString::Printf(TEXT("%s%sTracks of something big lead %s, toward %s, %.1f km off."), *Said, Said.IsEmpty() ? TEXT("") : TEXT("  "), RDS13Compass(At - F2), *Got.Name, FVector2D::Distance(At, F2) / 1000.0);
		else Said = FString::Printf(TEXT("%s%sOnly deer and boar have come this way."), *Said, Said.IsEmpty() ? TEXT("") : TEXT("  "));
	}
	else if (Do == TEXT("offer") || Do == TEXT("trade"))
	{
		// (an offering left (a cairn's: "where travelers leave an offering"): its blessing; a trade: what is given for what is had)
		FString Gn, Gc = TEXT("1"); M.FindRef(TEXT("give")).Split(TEXT("|"), &Gn, &Gc);
		if (Gn.IsEmpty()) Gn = M.FindRef(TEXT("give"));
		const int32 Need = FMath::Max(1, FCString::Atoi(*Gc));
		// (what a trade gives, read before anything is taken (PR #66's review: a "get" with no count or an item the table lacks took her
		// things for nothing))
		FString Rn, Rc = TEXT("1"); M.FindRef(TEXT("get")).Split(TEXT("|"), &Rn, &Rc);
		if (Rn.IsEmpty()) Rn = M.FindRef(TEXT("get"));
		if (Do == TEXT("trade") && FindItem(FName(*Rn)) < 0)
		{
			UE_LOG(LogRDScen13, Warning, TEXT("RDSCEN %s: a trade for %s, which is no item"), *K.Name.ToString(), *Rn);
			return TEXT("scenery");
		}
		if (FindItem(FName(*Gn)) < 0 || PlayerCombat->GetItemCount(FName(*Gn)) < Need)
		{
			PlayerCombat->ShowMessage(FString::Printf(TEXT("You have no %s to %s."), *Gn.ToLower(), Do == TEXT("offer") ? TEXT("leave here") : TEXT("trade")));
			return TEXT("scenery");
		}
		PlayerCombat->RemoveItem(FName(*Gn), Need);
		if (Do == TEXT("offer"))
		{
			const float Dm = RDS13Num(M, TEXT("dmg"), 0.1f), Ar = RDS13Num(M, TEXT("armour"), 0.1f), Sp = RDS13Num(M, TEXT("speed"), 0.f), Sec = RDS13Num(M, TEXT("secs"), 600.f);
			const FString Name = M.Contains(TEXT("name")) ? M[TEXT("name")] : K.Title;
			PlayerCombat->Bless(Name, Dm, Ar, Sp, Sec);
			Said = FString::Printf(TEXT("%s%sYou leave %d %s. %s: your blows %.0f%% stronger, %.0f%% less of each blow reaches you, for %.0f minutes"), *Said, Said.IsEmpty() ? TEXT("") : TEXT("  "), Need, *Gn, *Name, Dm * 100.f, Ar * 100.f, Sec / 60.f);
		}
		else
		{
			const int32 Got = FMath::Max(1, FCString::Atoi(*Rc));
			PlayerCombat->AddItem(FName(*Rn), Got);
			Said = FString::Printf(TEXT("%s%sYou trade %d %s for %d %s."), *Said, Said.IsEmpty() ? TEXT("") : TEXT("  "), Need, *Gn, Got, *Rn);
		}
	}
	else if (Do == TEXT("heal")) { PlayerCombat->SetHealth(PlayerCombat->GetMaxHealth()); PlayerCombat->SetMana(PlayerCombat->GetMaxMana()); if (Said.IsEmpty()) Said = TEXT("You rest: your wounds close, your mana comes back"); }
	else if (Do == TEXT("buff") || Do == TEXT("fairy"))
	{
		const float Dm = RDS13Num(M, TEXT("dmg"), 0.12f), Ar = RDS13Num(M, TEXT("armour"), 0.1f), Sp = RDS13Num(M, TEXT("speed"), 0.f), Sec = RDS13Num(M, TEXT("secs"), 300.f);
		const FString Name = M.Contains(TEXT("name")) ? M[TEXT("name")] : K.Title;
		PlayerCombat->Bless(Name, Dm, Ar, Sp, Sec);
		Said = FString::Printf(TEXT("%s%s%s: your blows %.0f%% stronger, %.0f%% less of each blow reaches you, for %.0f minutes"), *Said, Said.IsEmpty() ? TEXT("") : TEXT("  "), *Name, Dm * 100.f, Ar * 100.f, Sec / 60.f);
	}
	else if (Do == TEXT("milestone"))
	{
		TArray<TPair<double, int32>> Ds;
		for (int32 T = 0; T < Wild->Towns.Num(); ++T) Ds.Add({ FVector2D::Distance(Wild->Towns[T].Site, FVector2D(From.X / 100.0, From.Y / 100.0)), T });
		Ds.Sort([](const TPair<double, int32>& A, const TPair<double, int32>& B) { return A.Key < B.Key; });
		TArray<FString> Parts;
		for (int32 I = 0; I < FMath::Min(2, Ds.Num()); ++I)
		{
			const FRDWildTown& T = Wild->Towns[Ds[I].Value];
			Parts.Add(FString::Printf(TEXT("%s %.1f km %s"), *T.Name, Ds[I].Key / 1000.0, RDS13Compass(T.Site - FVector2D(From.X / 100.0, From.Y / 100.0))));
		}
		Said = FString::Printf(TEXT("%s%s%s"), *Said, Said.IsEmpty() ? TEXT("It reads:  ") : TEXT("  "), *FString::Join(Parts, TEXT(";  ")));
	}
	else if (Do == TEXT("rumour"))
	{
		// (a notice of the nearest structure of the wilds within 8 km: which way, how far)
		FRDWildPlace Got; FVector2D At;
		const FVector2D F2(From.X / 100.0, From.Y / 100.0);
		bool bGot = false; double Best = 8000.0;
		const FIntPoint C0 = Wild->SiteCellOf(F2.X, F2.Y);
		for (int32 I = -3; I <= 3; ++I) for (int32 J = -3; J <= 3; ++J)
		{
			TArray<FRDWildPlace> Ps; Wild->SitesIn(C0 + FIntPoint(I, J), Ps);
			for (const FRDWildPlace& P : Ps) { const double D = FVector2D::Distance(P.At, F2); if (D < Best) { Best = D; Got = P; At = P.At; bGot = true; } }
		}
		Said = bGot ? FString::Printf(TEXT("%s%sA notice tells of %s, %.1f km %s of here."), *Said, Said.IsEmpty() ? TEXT("") : TEXT("  "), *Got.Name, Best / 1000.0, RDS13Compass(At - F2))
		            : (Said.IsEmpty() ? FString(TEXT("The notices are too weathered to read.")) : Said);
	}
	// (what it wakes: "spawn=<name part>:<n>:<title>" (the barred cellar's))
	if (const FString Sp = M.FindRef(TEXT("spawn")); !Sp.IsEmpty())
	{
		TArray<FString> Q; Sp.ParseIntoArray(Q, TEXT(":"), false);
		SpawnSceneryMonsters(U.Chunk.Get(), Q.Num() > 0 ? Q[0] : FString(), Q.Num() > 1 ? FCString::Atoi(*Q[1]) : 1, Q.Num() > 2 ? Q[2] : FString(), U.At, (uint32)(U.Id * 8 + U.Use));
	}
	PlayerCombat->ShowMessage(Said);
	const int64 Key = RDS13UseKeys + (int64)(uint32)U.Id * 8 + U.Use;
	if (const float Re = RDS13Num(M, TEXT("reuse"), 0.f); Re > 0.f) WildSceneryReadyAt.Add((int32)(Key & 0x7FFFFFFF), Now + Re);
	else if (URDGameInstance* GI = URDGameInstance::Of(this)) GI->WildKilled.AddUnique(Key);
	++WildSceneryUsed; WildLastEngaged = Now;
	WildEngagements.Add(FString::Printf(TEXT("%.1f|used|%s|%s"), Now, *K.Name.ToString(), *Said.Left(120)));
	UE_LOG(LogRDScen13, Log, TEXT("RDSCENUSE %s %s: %s"), *K.Name.ToString(), *Do, *Said);
	return TEXT("scenery");
}

// ------------------------------------------------------------------------------------------------ the far sights
void ARDDungeonGenerator::TickWildStorm13(float Dt, const FVector& Her)
{
	UWorld* W = GetWorld();
	const float Now = W->GetTimeSeconds();
	const FVector2D H2(Her.X / 100.0, Her.Y / 100.0);
	if (UStaticMeshComponent* Cl = WildStormCloud.Get())
	{
		// (it drifts along its way; it goes when its time is up or it is 16 km off)
		const float Drift = WildFarSights.IsValidIndex(WildFarSightOn) ? WildFarSights[WildFarSightOn].Drift : 9.f;
		WildStormAt += WildStormWay * (double(Drift) * Dt);
		const double Km = FVector2D::Distance(WildStormAt, H2) / 1000.0;
		Cl->SetWorldLocation(FVector(WildStormAt.X * 100.0, WildStormAt.Y * 100.0, Wild->ToZ(Wild->Height(WildStormAt.X, WildStormAt.Y))));
		if (Now > WildStormUntil || Km > 16.0) ForceWildFarSight(NAME_None, 0.f);
		return;
	}
	WildStormLook -= Dt;
	if (WildStormLook > 0.f) return;
	WildStormLook = 30.f;
	// (a draw every half minute from the session's seed and the time, never the play's streams: of the sights of her region, each by
	// its own chance)
	const FString Bn = Wild->BiomeName(Wild->BiomeAt(H2.X, H2.Y));
	for (int32 I = 0; I < WildFarSights.Num(); ++I)
	{
		const FRDWildFarSight& F = WildFarSights[I];
		if (!F.Mesh || !F.Biomes.Contains(Bn)) continue;
		const float U = FRDWildWorld::Rand01((int32)SessionSeed + I * 7919, FMath::RoundToInt(Now / 30.f), 0x5170u);
		if (U >= F.Chance * 0.25f) continue;
		ForceWildFarSight(F.Name, FMath::Lerp(F.Km.X, F.Km.Y, FRDWildWorld::Rand01((int32)SessionSeed + I, FMath::RoundToInt(Now / 30.f), 0x5171u)));
		return;
	}
}

void ARDDungeonGenerator::ForceWildStorm(float Km) { ForceWildFarSight(TEXT("storm"), Km); }

void ARDDungeonGenerator::ForceWildFarSight(FName Name, float Km)
{
	if (UStaticMeshComponent* C = WildStormCloud.Get()) C->DestroyComponent();
	WildStormCloud.Reset(); WildFarSightOn = -1;
	const APawn* Her = UGameplayStatics::GetPlayerPawn(this, 0);
	const int32 Si = WildFarSights.IndexOfByPredicate([&](const FRDWildFarSight& F) { return F.Name == Name; });
	if (Km <= 0.f || !Her || !IsWildReady() || Si < 0 || !WildFarSights[Si].Mesh) return;
	const FRDWildFarSight& F = WildFarSights[Si];
	const float Now = GetWorld()->GetTimeSeconds();
	const FVector2D H2 = FVector2D(Her->GetActorLocation()) / 100.0;
	const float A = FRDWildWorld::Rand01((int32)SessionSeed, FMath::RoundToInt(Now), 0x5172u) * 2.f * PI;
	WildStormAt = H2 + FVector2D(FMath::Cos(A), FMath::Sin(A)) * (Km * 1000.0);
	// (drifting across her view, not at her)
	WildStormWay = FVector2D(-FMath::Sin(A), FMath::Cos(A));
	WildStormUntil = Now + F.Seconds;
	const FVector L(WildStormAt.X * 100.0, WildStormAt.Y * 100.0, Wild->ToZ(Wild->Height(WildStormAt.X, WildStormAt.Y)));
	// (its mesh (scenery13_kit.py's: the storm cell 3.4 km across, the smoke plume 1.8 km high) at its own size, its origin on the
	// ground under it, seen from the whole of the land round it; an effect alone was not seen from 6 km)
	UStaticMeshComponent* Sm = NewObject<UStaticMeshComponent>(this);
	Sm->SetStaticMesh(F.Mesh);
	Sm->SetupAttachment(GetRootComponent());
	Sm->SetUsingAbsoluteLocation(true); Sm->SetUsingAbsoluteRotation(true); Sm->SetUsingAbsoluteScale(true);
	Sm->SetWorldRotation(FRotator(0.f, FMath::RadiansToDegrees(A), 0.f));
	Sm->SetWorldLocation(L);
	Sm->SetCollisionEnabled(ECollisionEnabled::NoCollision);
	Sm->SetCastShadow(false);
	Sm->SetCachedMaxDrawDistance(0.f); Sm->bNeverDistanceCull = true;
	Sm->RegisterComponent();
	WildStormCloud = Sm; WildFarSightOn = Si;
	UE_LOG(LogRDScen13, Log, TEXT("RDFARSIGHT %s %.1f km off at (%.0f, %.0f)"), *Name.ToString(), Km, WildStormAt.X, WildStormAt.Y);
}

FString ARDDungeonGenerator::GetWildStormLine() const
{
	const APawn* Her = UGameplayStatics::GetPlayerPawn(this, 0);
	const bool bOn = WildStormCloud.IsValid();
	const double Km = Her ? FVector2D::Distance(WildStormAt, FVector2D(Her->GetActorLocation()) / 100.0) / 1000.0 : -1.0;
	return FString::Printf(TEXT("%s|%.0f|%.0f|%.2f|%d"), WildFarSights.IsValidIndex(WildFarSightOn) ? *WildFarSights[WildFarSightOn].Name.ToString() : TEXT("none"), WildStormAt.X, WildStormAt.Y, Km, bOn ? 1 : 0);
}

// ------------------------------------------------------------------------------------------------ tests
TArray<FString> ARDDungeonGenerator::GetWildSceneryLines() const
{
	TArray<FString> Out;
	for (const FRuinLaid& X : WildSceneryLaid)
	{
		const FRDWildSceneryKind* K = WildSceneryKinds.IsValidIndex(X.Kind) ? &WildSceneryKinds[X.Kind] : nullptr;
		int32 Stand = 0;
		if (WildSection)
			for (const TObjectPtr<ARDMonster>& Mo : WildSection->SpawnedMonsters)
				if (IsValid(Mo) && !Mo->IsDead() && Mo->WildKey >= 0 && Mo->WildKey / 16 == (int64)X.Id) ++Stand;
		int32 FxOn = 0; for (const TWeakObjectPtr<UNiagaraComponent>& F : X.Fx) if (F.IsValid() && F->IsVisible()) ++FxOn;
		int32 Herd = 0; if (const FSceneryHerd* Hd = WildSceneryHerds.FindByPredicate([&](const FSceneryHerd& H) { return H.Id == X.Id; })) for (const auto& A : Hd->Animals) if (A.IsValid()) ++Herd;
		Out.Add(FString::Printf(TEXT("scen|%d|%s|%s|%.1f|%.1f|%d|%d|%d|%d|%d|%d|%d|%d|%.1f|%s"), X.Id, K ? *K->Name.ToString() : TEXT("?"), K ? *K->Title : TEXT(""), X.At.X, X.At.Y, X.Pieces, X.Boxes, Stand,
			K ? K->Uses.Num() : 0, K ? K->Hazards.Num() : 0, X.Fx.Num(), FxOn, Herd, X.Yaw, *X.Name));
	}
	return Out;
}

TArray<FString> ARDDungeonGenerator::GetWildSceneryPieceLines(int32 Id) const
{
	return PieceLinesOf(WildSceneryLaid.FindByPredicate([&](const FRuinLaid& R) { return R.Id == Id; }));
}

TArray<FString> ARDDungeonGenerator::GetWildSceneryThingLines(int32 Id) const
{
	TArray<FString> Out;
	for (const FSceneryUse& U : WildSceneryUses)
	{
		if (U.Id != Id || !WildSceneryKinds.IsValidIndex(U.Kind)) continue;
		const TMap<FString, FString> M = RDS13Parse(WildSceneryKinds[U.Kind].Uses[U.Use]);
		Out.Add(FString::Printf(TEXT("use|%d|%s|%.0f|%.0f|%.0f|%d"), U.Use, *M.FindRef(TEXT("do")), U.At.X, U.At.Y, U.At.Z, IsWildSceneryUsed(U) ? 1 : 0));
	}
	for (const FSceneryHazard& Hz : WildSceneryHazards)
		if (Hz.Id / 8 == Id) Out.Add(FString::Printf(TEXT("haz|%s|%.0f|%.0f|%.0f|%.0f|%d"), *Hz.Kind.ToString(), Hz.At.X, Hz.At.Y, Hz.At.Z, Hz.R, Hz.Sprung));
	if (const FSceneryHerd* Hd = WildSceneryHerds.FindByPredicate([&](const FSceneryHerd& H) { return H.Id == Id; }))
	{
		int32 N = 0; for (const auto& A : Hd->Animals) if (A.IsValid()) ++N;
		Out.Add(FString::Printf(TEXT("herd|%d|%d|%d|%d|%d"), N, Hd->Stampedes, Hd->Hits, Hd->bMigrate ? 1 : 0, Hd->bStampede ? 1 : 0));
		for (const auto& Wa : Hd->Animals) if (const ARDWildAnimal* A = Wa.Get()) Out.Add(FString::Printf(TEXT("ani|%.0f|%.0f|%d"), A->GetActorLocation().X, A->GetActorLocation().Y, A->GetState()));
	}
	return Out;
}

FString ARDDungeonGenerator::FindWildScenery(FName Kind, float X, float Y, float MaxKm) const
{
	if (!IsWildReady()) return FString();
	const int32 Want = WildSceneryKinds.IndexOfByPredicate([&](const FRDWildSceneryKind& K) { return K.Name == Kind; });
	if (Want < 0) return FString();
	// (rings of the 600 m cells out from the point, past the first ring that holds one until none nearer can be left)
	const FIntPoint C0 = Wild->SceneryCellOf(X, Y);
	const int32 Rmax = FMath::CeilToInt(MaxKm * 1000.0 / FRDWildWorld::SceneryCellM);
	double Best = FMath::Square(MaxKm * 1000.0); FRDWildPlace Got; bool bGot = false;
	for (int32 Ring = 0; Ring <= Rmax; ++Ring)
	{
		if (bGot && FMath::Square(FMath::Max(0.0, (Ring - 1) * FRDWildWorld::SceneryCellM - 400.0)) > Best) break;
		for (int32 I = -Ring; I <= Ring; ++I)
			for (int32 J = -Ring; J <= Ring; ++J)
			{
				if (FMath::Max(FMath::Abs(I), FMath::Abs(J)) != Ring) continue;
				TArray<FRDWildPlace> Ps; Wild->SceneryIn(C0 + FIntPoint(I, J), Ps);
				for (const FRDWildPlace& P : Ps)
				{
					if (P.Scenery != Want) continue;
					const double D = FVector2D::DistSquared(P.At, FVector2D(X, Y));
					if (D < Best) { Best = D; Got = P; bGot = true; }
				}
			}
	}
	return bGot ? FString::Printf(TEXT("%d|%.1f|%.1f|%.1f|%s"), Got.Id, Got.At.X, Got.At.Y, Got.Yaw, *Got.Name) : FString();
}

TArray<FString> ARDDungeonGenerator::CountWildScenery(float X, float Y, float MaxKm) const
{
	TArray<FString> Out;
	if (!IsWildReady()) return Out;
	TArray<int32> N; N.SetNumZeroed(WildSceneryKinds.Num());
	const FIntPoint C0 = Wild->SceneryCellOf(X, Y);
	const int32 Rmax = FMath::CeilToInt(MaxKm * 1000.0 / FRDWildWorld::SceneryCellM);
	int32 Cells = 0;
	for (int32 I = -Rmax; I <= Rmax; ++I)
		for (int32 J = -Rmax; J <= Rmax; ++J)
		{
			TArray<FRDWildPlace> Ps; Wild->SceneryIn(C0 + FIntPoint(I, J), Ps); ++Cells;
			for (const FRDWildPlace& P : Ps) if (N.IsValidIndex(P.Scenery)) N[P.Scenery]++;
		}
	for (int32 K = 0; K < WildSceneryKinds.Num(); ++K) Out.Add(FString::Printf(TEXT("%s|%d"), *WildSceneryKinds[K].Name.ToString(), N[K]));
	Out.Add(FString::Printf(TEXT("cells|%d"), Cells));
	return Out;
}

TArray<FString> ARDDungeonGenerator::FindWildChannels(FString Kind, float X, float Y, float MaxKm, int32 MaxN) const
{
	TArray<FString> Out;
	if (!IsWildReady()) return Out;
	TArray<TPair<double, int32>> Got;
	for (int32 I = 0; I < Wild->Channels.Num(); ++I)
	{
		const FRDWildWorld::FChannel& C = Wild->Channels[I];
		if (!Wild->ChannelNames.IsValidIndex(C.Kind) || (!Kind.IsEmpty() && Wild->ChannelNames[C.Kind] != Kind)) continue;
		const double D = FVector2D::Distance(C.P[C.P.Num() / 2], FVector2D(X, Y));
		if (D <= MaxKm * 1000.0) Got.Add({ D, I });
	}
	Got.Sort([](const TPair<double, int32>& A, const TPair<double, int32>& B) { return A.Key < B.Key; });
	for (int32 K = 0; K < FMath::Min(MaxN, Got.Num()); ++K)
	{
		const FRDWildWorld::FChannel& C = Wild->Channels[Got[K].Value];
		const FVector2D Mp = C.P[C.P.Num() / 2];
		Out.Add(FString::Printf(TEXT("chan|%d|%s|%.1f|%.1f|%.1f|%.1f|%d"), Got[K].Value, *Wild->ChannelNames[C.Kind], Mp.X, Mp.Y, C.W, C.D, C.P.Num()));
	}
	return Out;
}

TArray<FString> ARDDungeonGenerator::GetWildChannelProfile(int32 Index, int32 Point, float HalfM) const
{
	TArray<FString> Out;
	if (!IsWildReady() || !Wild->Channels.IsValidIndex(Index)) return Out;
	const FRDWildWorld::FChannel& C = Wild->Channels[Index];
	const int32 I = FMath::Clamp(Point, 1, C.P.Num() - 2);
	const FVector2D Dir = (C.P[I + 1] - C.P[I - 1]).GetSafeNormal(), Side(-Dir.Y, Dir.X);
	for (float O = -HalfM; O <= HalfM + 0.01f; O += 1.f)
	{
		const FVector2D Q = C.P[I] + Side * O;
		Out.Add(FString::Printf(TEXT("%.1f|%.2f|%.2f"), O, Wild->Height(Q.X, Q.Y), Wild->BareHeight(Q.X, Q.Y)));
	}
	return Out;
}

TArray<FString> ARDDungeonGenerator::FindWildCrossroads(float X, float Y, float MaxKm) const
{
	TArray<FString> Out;
	if (!IsWildReady()) return Out;
	for (const FVector2D& Q : Wild->Crossroads) if (FVector2D::Distance(Q, FVector2D(X, Y)) <= MaxKm * 1000.0) Out.Add(FString::Printf(TEXT("%.1f|%.1f"), Q.X, Q.Y));
	return Out;
}
