// The wilderness's farmsteads (the user's list of 2026-11-08b, docs/improvements9.txt: "on the farm terrain, there should also be
// farm houses, barns, fenced in animals, and farm families to go with the farms"). FRDWildWorld::FarmsteadsIn says where each
// stands (a croft field's yard); a chunk lays its farmsteads as it lays its places: the farmhouse, the barn beside it, a fenced
// paddock with a big kind of the town's farm animals in it and a hen run with a small kind, a trough, hay, a well, a cart, a
// woodpile, a scarecrow out in the plots; the family at their work (the town's work clips): the farmer tending a plot's edge,
// the farmwife feeding the paddock, a farmhand by the barn, a child by the well. F at one of them: they turn to her and say a
// line of their own (WildFarmLines). Everything is the chunk's (its components and Props): it goes with the chunk.
#include "RD/RDDungeonGenerator.h"
#include "RD/RDWild.h"
#include "RD/RDTown.h"
#include "RD/RDCombat.h"
#include "RD/RDSection.h"
#include "Components/StaticMeshComponent.h"
#include "Components/SkeletalMeshComponent.h"
#include "ProceduralMeshComponent.h"
#include "Engine/StaticMesh.h"
#include "Engine/World.h"

DEFINE_LOG_CATEGORY_STATIC(LogRDWildFarm, Log, All);

namespace
{
	// the farm's frame: a point u metres along its way and v across it
	FORCEINLINE FVector2D RDWFAt(const FRDWildPlace& P, float U, float V)
	{
		const float A = FMath::DegreesToRadians(P.Yaw);
		const FVector2D Fw(FMath::Cos(A), FMath::Sin(A)), Sd(-Fw.Y, Fw.X);
		return P.At + Fw * U + Sd * V;
	}
}

void ARDDungeonGenerator::SpawnWildFarm(ARDWildChunk* C, const FRDWildPlace& P)
{
	if (!C || !IsWildReady()) return;
	FRandomStream R((int32)FRDWildWorld::Hash(P.Id, 77, Wild->Seed));
	const FVector O = C->GetActorLocation();
	FRDWildFarmRec Rec; Rec.Id = P.Id; Rec.Name = P.Name; Rec.At = P.At; Rec.Yaw = P.Yaw; Rec.Chunk = C;
	auto Pick = [&](const FString& Prefix, const FString& Or) -> UStaticMesh*
	{
		TArray<UStaticMesh*> Ms; WildPiecesOf(Prefix, Ms);
		if (Ms.Num() == 0 && !Or.IsEmpty()) WildPiecesOf(Or, Ms);
		return Ms.Num() > 0 ? Ms[R.RandRange(0, Ms.Num() - 1)] : nullptr;
	};
	auto Comp = [&](UStaticMesh* M, const FTransform& T, bool bCollide) -> UStaticMeshComponent*
	{
		UStaticMeshComponent* Sm = NewObject<UStaticMeshComponent>(C);
		Sm->SetStaticMesh(M);
		Sm->SetupAttachment(C->Ground);
		Sm->SetRelativeTransform(T);
		if (!bCollide) Sm->SetCollisionEnabled(ECollisionEnabled::NoCollision);
		Sm->RegisterComponent();
		C->PlaceProps.Add(Sm);
		++Rec.Props;
		return Sm;
	};
	auto ScaleOf = [&](const UStaticMesh* M) { const float* Ks = WildPieceScale.Find(FName(*M->GetName())); return Ks ? *Ks : 1.f; };
	// one piece at a point of the farm's frame (metres), turned from the farm's way, sunk (cm at its scale)
	// (the mesh's own middle (its box's) on the point: a pack's origin can be at a corner or an end)
	auto PutMesh = [&](UStaticMesh* M, float U, float V, float Yaw, float Sink = 10.f, bool bCollide = true) -> UStaticMeshComponent*
	{
		if (!M) return nullptr;
		const float Sc = ScaleOf(M);
		const FVector2D At = RDWFAt(P, U, V);
		const float Z = WildGroundZ(FVector(At.X * 100.0, At.Y * 100.0, 0.0));
		const FQuat Q = FRotator(0.f, P.Yaw + Yaw, 0.f).Quaternion();
		const FVector Mid = M->GetBoundingBox().GetCenter();
		// (its foot on the ground: the box's bottom, not the origin (a fence's origin is its middle))
		const FVector Off = Q.RotateVector(FVector(Mid.X, Mid.Y, 0.0) * Sc) + FVector(0.0, 0.0, M->GetBoundingBox().Min.Z * Sc);
		return Comp(M, FTransform(Q, FVector(At.X * 100.0, At.Y * 100.0, Z - Sink * Sc) - Off - O, FVector(Sc)), bCollide);
	};
	auto Put = [&](const FString& Prefix, const FString& Or, float U, float V, float Yaw, float Sink = 10.f, bool bCollide = true) -> UStaticMeshComponent*
	{
		return PutMesh(Pick(Prefix, Or), U, V, Yaw, Sink, bCollide);
	};
	// a mesh's half sizes along and across the farm's way (metres, at its scale, not turned)
	auto HalfOf = [&](const UStaticMesh* M) { if (!M) return FVector2D(4.f, 4.f); const FVector E = M->GetBoundingBox().GetSize() * ScaleOf(M) / 200.0; return FVector2D(E.X, E.Y); };
	// a fence from A to B (the farm's frame, metres): its pieces end to end along the line, each stretched a little to fill it,
	// its long side along the line whichever axis that is in its mesh, its middle on the line
	auto Fence = [&](const FVector2D& A, const FVector2D& B, UStaticMesh* M)
	{
		if (!M) return;
		const FVector2D Wa = RDWFAt(P, A.X, A.Y), Wb = RDWFAt(P, B.X, B.Y);
		const double Len = FVector2D::Distance(Wa, Wb) * 100.0;
		if (Len < 30.0) return;
		const FBox Bx = M->GetBoundingBox();
		const FVector Ext = Bx.GetSize(), Mid = Bx.GetCenter();
		const bool bAlongY = Ext.Y > Ext.X;
		const float Sc = ScaleOf(M);
		const double Piece = FMath::Max((bAlongY ? Ext.Y : Ext.X) * Sc, 50.0);
		const int32 N = FMath::Max(1, FMath::RoundToInt(Len / Piece));
		const double Stretch = Len / (N * Piece);
		const FVector2D Dir = (Wb - Wa).GetSafeNormal();
		const float Yaw = FMath::RadiansToDegrees(FMath::Atan2(Dir.Y, Dir.X)) - (bAlongY ? 90.f : 0.f);
		const FVector Sc3 = bAlongY ? FVector(Sc, Sc * Stretch, Sc) : FVector(Sc * Stretch, Sc, Sc);
		const FQuat Q = FRotator(0.f, Yaw, 0.f).Quaternion();
		for (int32 K = 0; K < N; ++K)
		{
			const FVector2D Cp = Wa + Dir * ((K + 0.5) * Len / N / 100.0);
			const float Z = WildGroundZ(FVector(Cp.X * 100.0, Cp.Y * 100.0, 0.0));
			// (the mesh's own middle onto the line: its origin may be at an end post)
			const FVector Off = Q.RotateVector(FVector(Mid.X, Mid.Y, 0.0) * Sc3) + FVector(0.0, 0.0, Bx.Min.Z * Sc3.Z);
			Comp(M, FTransform(Q, FVector(Cp.X * 100.0, Cp.Y * 100.0, Z - 8.f * Sc) - Off - O, Sc3), true);
		}
	};
	// a fenced rectangle in the farm's frame (middle u, v; half sizes along and across its way, metres), a gate's gap of Gap m
	// in the middle of the side toward the farmhouse (its -v side when it lies on the +v side, and the other way)
	auto Pen = [&](float U, float V, float Hu, float Hv, float Gap)
	{
		const FVector2D A(U - Hu, V - Hv), B(U + Hu, V - Hv), Cc(U + Hu, V + Hv), D(U - Hu, V + Hv);
		const bool bGapLow = V > 0.f;      // (the side nearer the house's line v 0)
		// (one fence the whole pen round)
		UStaticMesh* M = Pick(TEXT("paddock"), TEXT("fence"));
		Fence(A, FVector2D(A.X, D.Y), M); Fence(B, Cc, M);
		const FVector2D Lo0 = A, Lo1 = B, Hi0 = D, Hi1 = Cc;
		auto Gapped = [&](const FVector2D& S0, const FVector2D& S1)
		{
			const FVector2D Mm = (S0 + S1) * 0.5f, Dd = (S1 - S0).GetSafeNormal();
			Fence(S0, Mm - Dd * (Gap * 0.5f), M); Fence(Mm + Dd * (Gap * 0.5f), S1, M);
		};
		if (bGapLow) { Gapped(Lo0, Lo1); Fence(Hi0, Hi1, M); } else { Fence(Lo0, Lo1, M); Gapped(Hi0, Hi1); }
		++Rec.FenceGap;
	};
	auto Animals = [&](bool bBig, float U, float V, float Hu, float Hv, uint32 Salt)
	{
		TArray<int32> Kinds;
		for (int32 K = 0; K < TownAnimals.Num(); ++K)
			if (TownAnimals[K].Mesh && (TownAnimals[K].HalfSize.X > 50.f) == bBig) Kinds.Add(K);
		if (Kinds.Num() == 0) return;
		const int32 Kd = Kinds[R.RandRange(0, Kinds.Num() - 1)];
		const FRDTownAnimalDef& D = TownAnimals[Kd];
		const int32 N = FMath::Min(R.RandRange(FMath::Min(D.PenMin, D.PenMax), FMath::Max(D.PenMin, D.PenMax)), WildFarmAnimalsMax);
		const FVector2D Mid = RDWFAt(P, U, V);
		const FVector PenAt(Mid.X * 100.0, Mid.Y * 100.0, WildGroundZ(FVector(Mid.X * 100.0, Mid.Y * 100.0, 0.0)));
		// (kept its body's half length off the fence, 20 cm more, as the town's pens)
		const FVector2D Half(Hu * 100.f - 40.f, Hv * 100.f - 40.f);
		const FVector2D H = (Half - FVector2D(D.HalfSize.X, D.HalfSize.X)).ComponentMax(FVector2D(5.f, 5.f));
		Rec.PenAt = PenAt; Rec.PenHalf = Half; Rec.PenYaw = P.Yaw;
		// (the ground's height over the pen, once: the animals read it as they walk (PR #30's review))
		const float Rg = FMath::Sqrt(FMath::Square(Hu) + FMath::Square(Hv)) * 100.f + 100.f;
		constexpr int32 Gn = 6;
		TArray<float> Grid; Grid.SetNumUninitialized(Gn * Gn);
		const FVector2D G0(PenAt.X - Rg, PenAt.Y - Rg); const float Gs = 2.f * Rg / (Gn - 1);
		for (int32 I = 0; I < Gn; ++I) for (int32 J = 0; J < Gn; ++J) Grid[I * Gn + J] = WildGroundZ(FVector(G0.X + I * Gs, G0.Y + J * Gs, 0.0));
		FActorSpawnParameters Sp; Sp.SpawnCollisionHandlingOverride = ESpawnActorCollisionHandlingMethod::AlwaysSpawn;
		for (int32 K = 0; K < N; ++K)
		{
			FVector At = PenAt + FRotator(0.f, P.Yaw, 0.f).RotateVector(FVector(R.FRandRange(-H.X, H.X), R.FRandRange(-H.Y, H.Y), 0.f));
			At.Z = WildGroundZ(At);
			ARDTownAnimal* A = GetWorld()->SpawnActor<ARDTownAnimal>(ARDTownAnimal::StaticClass(), FTransform(FRotator(0, R.FRandRange(0.f, 360.f), 0), At), Sp);
			if (!A) continue;
			A->bWildGround = true; A->PenYaw = P.Yaw;
			A->GroundGrid = Grid; A->GroundO = G0; A->GroundStep = Gs; A->GroundN = Gn;
			A->Init(this, Kd, -1, PenAt, Half, HashCombine((uint32)P.Id, Salt + (uint32)K * 2654435761u));
			C->Props.Add(A);
			Rec.Animals.Add(A);
			Rec.AnimalPens.Add(FVector4(PenAt.X, PenAt.Y, Half.X, Half.Y));
		}
	};
	// ---- the buildings: the farmhouse on the field's point, the barn beside it, turned the same way; everything else laid out
	// from their sizes (the yard is 34 m round)
	UStaticMesh* HouseM = Pick(TEXT("farmhouse"), TEXT("house"));
	UStaticMesh* BarnM = Pick(TEXT("barn"), TEXT("house"));
	const FVector2D Hh = HalfOf(HouseM), Bh = HalfOf(BarnM);
	PutMesh(HouseM, 0.f, 0.f, 0.f, 25.f);
	const float BarnV = Hh.Y + Bh.Y + 3.f;
	PutMesh(BarnM, 0.f, BarnV, 0.f, 15.f);
	// ---- the paddock (7 x 5.5 m half sizes) on the house's other side, its gate toward the house; the hen run behind the house
	const float PadV = -(Hh.Y + 3.f + 5.5f);
	Pen(0.f, PadV, 7.f, 5.5f, 2.6f);
	Animals(true, 0.f, PadV, 7.f, 5.5f, 11u);
	const FVector PenBig = Rec.PenAt; const FVector2D PenBigHalf = Rec.PenHalf;
	Put(TEXT("trough"), TEXT("hay"), -5.5f, PadV, 90.f, 5.f);
	Put(TEXT("hay"), FString(), 5.f, PadV - 3.5f, R.FRandRange(0.f, 360.f), 5.f);
	const float RunU = -(Hh.X + 2.f + 2.5f);
	Pen(RunU, 0.5f, 2.5f, 3.f, 1.4f);
	Animals(false, RunU, 0.5f, 2.5f, 3.f, 23u);
	// (the record's pen is the paddock: the hen run's animals are read against the paddock's and their own)
	Rec.PenAt = PenBig; Rec.PenHalf = PenBigHalf;
	// ---- the yard's things before the house: the well, the cart, the woodpile by the house's side, a scarecrow in the plots
	const float FrontU = Hh.X + 6.f;
	Put(TEXT("well"), FString(), FrontU, 4.f, R.FRandRange(0.f, 360.f));
	Put(TEXT("cart"), FString(), FrontU - 1.f, -6.f, R.FRandRange(-30.f, 30.f) + 90.f);
	Put(TEXT("woodpile"), TEXT("log"), -Hh.X * 0.5f, Hh.Y + 1.2f, 0.f, 3.f);
	Put(TEXT("scarecrow"), FString(), 40.f, R.FRandRange(-12.f, 12.f), R.FRandRange(0.f, 360.f), 15.f);
	// ---- the family: whose work is where, the defs' bodies (the shared ones: the townsmen for the farmer and the farmhand, the
	// townswomen for the farmwife (by name: the first picture's farmwife was a man), the children for the child)
	TArray<int32> Men, Women, Kids;
	for (int32 I = 0; I < Townsfolk.Num(); ++I)
	{
		const FRDTownsfolkDef& Df = Townsfolk[I];
		if (!Df.Mesh || !Df.Town.IsEmpty()) continue;
		const FString Nm = Df.Name.ToString();
		if (Df.Role == ERDTownRole::Child) Kids.Add(I);
		else if (Df.Role == ERDTownRole::Townsfolk) (Nm.Contains(TEXT("woman")) ? Women : Men).Add(I);
	}
	// (the plot the farmer tends: the nearest sown croft plot's edge, looked for out of the yard on eight ways)
	FVector2D TendAt = RDWFAt(P, 30.f, 0.f); float TendYaw = P.Yaw;
	{
		const float Fw0 = Wild->FarmWeight(P.At.X, P.At.Y);
		for (int32 K = 0; K < 8; ++K)
		{
			const float A = FMath::DegreesToRadians(P.Yaw + 45.f * K);
			const FVector2D Dd(FMath::Cos(A), FMath::Sin(A));
			FRDWFarm Fm; Wild->FarmAt(P.At.X + Dd.X * 38.0, P.At.Y + Dd.Y * 38.0, Fw0, Fm);
			if (Fm.Kind == 2 && Fm.Crop >= 0 && Fm.Field > 0.6f) { TendAt = P.At + Dd * 35.5f; TendYaw = FMath::RadiansToDegrees(A); break; }
		}
	}
	struct FWho { const TCHAR* Role; int32 Body; FVector2D At; float Yaw; const TCHAR* Work; const TCHAR* Prop; };   // (Body: 0 a man, 1 a woman, 2 a child)
	// (the farmwife outside the paddock's gate, facing in; the farmhand before the barn, the child by the well, each facing the
	// yard's middle before the house)
	const FVector2D Gate = RDWFAt(P, 1.8f, PadV + 5.5f + 1.1f);
	const FVector2D Yard = RDWFAt(P, FrontU - 2.f, 0.f);
	auto Facing = [&](const FVector2D& From, const FVector2D& To) { return FMath::RadiansToDegrees(FMath::Atan2(To.Y - From.Y, To.X - From.X)); };
	const FVector2D HandAt = RDWFAt(P, Bh.X + 1.5f, BarnV), KidAt = RDWFAt(P, FrontU + 1.2f, 5.6f);
	const FWho Family[] = {
		{ TEXT("farmer"), 0, TendAt, TendYaw, TEXT("Tend"), nullptr },
		{ TEXT("farmwife"), 1, Gate, P.Yaw - 90.f, TEXT("Scatter"), TEXT("Bowl") },
		{ TEXT("farmhand"), 0, HandAt, Facing(HandAt, Yard), TEXT("Talk"), nullptr },
		{ TEXT("child"), 2, KidAt, Facing(KidAt, Yard), nullptr, nullptr } };
	// (how many: the farmer and the farmwife always, a farmhand on two farms of three, a child on half)
	const bool bHand = R.FRand() < 0.67f, bKid = R.FRand() < 0.5f;
	FActorSpawnParameters Sp; Sp.SpawnCollisionHandlingOverride = ESpawnActorCollisionHandlingMethod::AlwaysSpawn;
	for (int32 K = 0; K < UE_ARRAY_COUNT(Family); ++K)
	{
		const FWho& Wh = Family[K];
		if ((K == 2 && !bHand) || (K == 3 && !bKid)) continue;
		const TArray<int32>& Pool = Wh.Body == 2 ? Kids : Wh.Body == 1 ? Women : Men;
		if (Pool.Num() == 0) continue;
		const int32 D = Pool[(int32)(FRDWildWorld::Hash(P.Id, 300 + K, Wild->Seed) % (uint32)Pool.Num())];
		const FVector At(Wh.At.X * 100.0, Wh.At.Y * 100.0, WildGroundZ(FVector(Wh.At.X * 100.0, Wh.At.Y * 100.0, 0.0)) + 92.f);
		ARDTownsfolk* T = GetWorld()->SpawnActor<ARDTownsfolk>(ARDTownsfolk::StaticClass(), FTransform(FRotator(0, Wh.Yaw, 0), At), Sp);
		if (!T) continue;
		T->Init(this, nullptr, D, At, Wh.Yaw, 0.f, HashCombine((uint32)P.Id, (uint32)K * 7919u));
		T->SetTitle(FString::Printf(TEXT("%s of %s"), Wh.Role, *P.Name));
		if (Wh.Work) T->SetStandWork(Wh.Work, Wh.Prop ? FName(Wh.Prop) : NAME_None);
		// (its lines: its own role's and every one's)
		for (const FString& L : WildFarmLines)
		{
			FString Who, Line;
			if (!L.Split(TEXT("|"), &Who, &Line)) continue;
			if (Who == Wh.Role || Who == TEXT("any")) T->OwnLines.Add(Line.Replace(TEXT("{farm}"), *P.Name));
		}
		C->Props.Add(T);
		Rec.Folk.Add(T);
	}
	WildFarms.RemoveAll([](const FRDWildFarmRec& F) { return !F.Chunk.IsValid(); });
	WildFarms.RemoveAll([&](const FRDWildFarmRec& F) { return F.Id == P.Id; });
	UE_LOG(LogRDWildFarm, Log, TEXT("RDWILD farmstead %s (%d): %d props, %d animals, %d folk"), *P.Name, P.Id, Rec.Props, Rec.Animals.Num(), Rec.Folk.Num());
	WildFarms.Add(MoveTemp(Rec));
}

void ARDDungeonGenerator::TickWildFarms()
{
	while (WildFarmQueue.Num() > 0)
	{
		const TPair<TWeakObjectPtr<ARDWildChunk>, FRDWildPlace> Q = WildFarmQueue[0];
		WildFarmQueue.RemoveAt(0);
		if (ARDWildChunk* C = Q.Key.Get(); IsValid(C)) { SpawnWildFarm(C, Q.Value); return; }    // (a chunk dropped before its turn: the next)
	}
}

ARDTownsfolk* ARDDungeonGenerator::WildFolkForF(const FVector& From) const
{
	// (as the town's people: within 2 m, and a door or a container of a loaded town nearer than them takes F (PR #30's review:
	// the farm folk took F before Brokenspire's rule))
	if (!bWild) return nullptr;
	ARDTownsfolk* T = NearestWildFolk(From, 200.f);
	if (!T) return nullptr;
	const float D = FVector::Dist2D(T->GetActorLocation(), From);
	if (const ARDSection* S0 = GetSection(FIntPoint::ZeroValue)) { bool bD0 = false; int32 I0 = -1; if (S0->FindNearestInteractive(From, D, bD0, I0) < D - 30.f) return nullptr; }
	return T;
}

ARDTownsfolk* ARDDungeonGenerator::NearestWildFolk(const FVector& From, float Reach) const
{
	ARDTownsfolk* Best = nullptr; float Bd = Reach;
	for (const FRDWildFarmRec& F : WildFarms)
		for (const TWeakObjectPtr<ARDTownsfolk>& W : F.Folk)
			if (ARDTownsfolk* T = W.Get(); IsValid(T))
			{
				const float D = FVector::Dist2D(T->GetActorLocation(), From);
				if (D < Bd && FMath::Abs(T->GetActorLocation().Z - From.Z) < 200.f) { Bd = D; Best = T; }
			}
	return Best;
}

TArray<FString> ARDDungeonGenerator::GetWildFarmLines() const
{
	TArray<FString> Out;
	if (!IsWildReady()) return Out;
	for (const FRDWildFarmRec& F : WildFarms)
	{
		if (!F.Chunk.IsValid()) continue;
		int32 Na = 0, Nf = 0;
		for (const TWeakObjectPtr<ARDTownAnimal>& A : F.Animals) if (A.IsValid()) ++Na;
		for (const TWeakObjectPtr<ARDTownsfolk>& T : F.Folk) if (T.IsValid()) ++Nf;
		Out.Add(FString::Printf(TEXT("farm|%d|%s|%.1f|%.1f|%.0f|%.1f|%d|%d|%d|%.0f|%.0f|%.0f|%.0f|%.1f"), F.Id, *F.Name, F.At.X, F.At.Y,
			WildGroundZ(FVector(F.At.X * 100.0, F.At.Y * 100.0, 0.0)), F.Yaw, F.Props, Na, Nf, F.PenAt.X, F.PenAt.Y, F.PenHalf.X, F.PenHalf.Y, F.PenYaw));
		for (int32 Ai = 0; Ai < F.Animals.Num(); ++Ai)
		{
			const ARDTownAnimal* A = F.Animals[Ai].Get();
			if (!A) continue;
			const FVector L = A->GetActorLocation();
			// (in the pen it was put in (the paddock or the hen run), its fence 30 cm out from the half sizes it keeps to)
			const FVector4 Pn = F.AnimalPens.IsValidIndex(Ai) ? F.AnimalPens[Ai] : FVector4(F.PenAt.X, F.PenAt.Y, F.PenHalf.X, F.PenHalf.Y);
			const FVector Lp = FRotator(0.f, -F.PenYaw, 0.f).RotateVector(L - FVector(Pn.X, Pn.Y, L.Z));
			const bool bIn = FMath::Abs(Lp.X) <= Pn.Z + 30.f && FMath::Abs(Lp.Y) <= Pn.W + 30.f;
			Out.Add(FString::Printf(TEXT("animal|%d|%s|%.0f|%.0f|%.0f|%d|%d|%.0f"), F.Id, TownAnimals.IsValidIndex(A->Def) ? *TownAnimals[A->Def].Name.ToString() : TEXT("?"),
				L.X, L.Y, L.Z, bIn ? 1 : 0, A->GetState(), WildGroundZ(L)));
		}
		for (const TWeakObjectPtr<ARDTownsfolk>& Tw : F.Folk)
		{
			const ARDTownsfolk* T = Tw.Get();
			if (!T) continue;
			const FVector L = T->GetActorLocation();
			Out.Add(FString::Printf(TEXT("folk|%d|%s|%.0f|%.0f|%.0f|%s|%.0f|%s"), F.Id, *T->Title, L.X, L.Y, L.Z, *T->GetClipName(), WildGroundZ(L),
				Townsfolk.IsValidIndex(T->Def) ? *Townsfolk[T->Def].Name.ToString() : TEXT("?")));
		}
	}
	return Out;
}

FString ARDDungeonGenerator::GetWildFarmAt(float Xm, float Ym) const
{
	if (!IsWildReady()) return FString();
	FRDWFarm Fm; Wild->FarmAt(Xm, Ym, Wild->FarmWeight(Xm, Ym), Fm);
	return FString::Printf(TEXT("%d|%d,%d|%d,%d|%d|%.3f|%.4f|%.2f|%.2f|%d|%.3f|%.3f|%.3f|%.3f"), (int32)Fm.Kind, Fm.Great.X, Fm.Great.Y, Fm.Plot.X, Fm.Plot.Y, Fm.Crop, Fm.Field, Fm.Ang,
		Fm.StripW, Fm.StripOff, Fm.Strip, Fm.Furrow, Fm.Ridge, Wild->Height(Xm, Ym), Wild->BareHeight(Xm, Ym));
}

TArray<FString> ARDDungeonGenerator::FindWildFarmsteads(float Xm, float Ym, float Rm) const
{
	TArray<FString> Out;
	if (!IsWildReady()) return Out;
	TArray<FRDWildPlace> Ps;
	Wild->FarmsteadsIn(Xm - Rm, Ym - Rm, Xm + Rm, Ym + Rm, Ps);
	Ps.Sort([&](const FRDWildPlace& A, const FRDWildPlace& B) { return FVector2D::DistSquared(A.At, FVector2D(Xm, Ym)) < FVector2D::DistSquared(B.At, FVector2D(Xm, Ym)); });
	for (const FRDWildPlace& P : Ps)
		if (FVector2D::Distance(P.At, FVector2D(Xm, Ym)) <= Rm) Out.Add(FString::Printf(TEXT("%d|%s|%.1f|%.1f|%.1f"), P.Id, *P.Name, P.At.X, P.At.Y, P.Yaw));
	return Out;
}
