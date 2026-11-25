// The user's list of 2026-11-22 (docs/improvements16.txt, "the movement of vehicles in heaven is not natural..."; the plan
// docs/improvements16_plan.md), its twenty-third phase, Heaven's traffic:
// - a road graph: each street's run between its crossings has a lane each way (on the right); a lane ends at its stop line before a
//   crossing (or turns back where its street ends), and a car crosses to the next lane on a curve;
// - each car has a driver (a townsperson seated on the Drive clip) with a goal tree: home, work, lunch, errands by the hour, each an
//   address (the lane by the building's door), a route over the graph to the nearest free parking bay there, parked a while, on again;
// - the laws: a red light stops it at its line (amber too when it can stop), a stop sign stops it fully before it goes, a left turn
//   yields to the oncoming, no car enters a crossing a car is crossing near its way, it keeps its distance to the car ahead, to her
//   and to pedestrians, easing in and out (its speed by the room ahead);
// - buses: two loops through the bus stops, stopping at each; townsfolk wait at the stops, board and get off (passengers seated);
// - by distance: collision within 30 m, the drivers drawn within 60 m, the cars within 200 m, the far ones moved four times a second.
#include "RD/RDDungeonGenerator.h"
#include "RD/RDSection.h"
#include "RD/RDTown.h"
#include "Components/SkeletalMeshComponent.h"
#include "Animation/AnimSingleNodeInstance.h"
#include "Kismet/GameplayStatics.h"
DEFINE_LOG_CATEGORY_STATIC(LogRDHeaven23, Log, All);

static TAutoConsoleVariable<int32> CVarRDTraffic23(TEXT("rd.Traffic23"), 1, TEXT("Heaven's traffic: 1 driving, 0 standing still (tests)"));

namespace
{
	const float RDH23Lane = 220.f;          // (the lane's line from the street's middle, on the right)
	const float RDH23Gap = 260.f;           // (the least room kept to the car ahead, bumper to bumper)
	const float RDH23Acc = 260.f, RDH23Dec = 520.f;
	FVector RDH23Bez(const FVector& A, const FVector& B, const FVector& C, float T) { const float U = 1.f - T; return A * (U * U) + B * (2.f * U * T) + C * (T * T); }
	FVector RDH23BezD(const FVector& A, const FVector& B, const FVector& C, float T) { return (B - A) * (2.f * (1.f - T)) + (C - B) * (2.f * T); }
	/** two cars' footprints (middle, heading, length, width) closer than the margin: separating axes in 2D */
	bool RDH23Overlap(const FVector& Pa, float Ya, float La, float Wa, const FVector& Pb, float Yb, float Lb, float Wb, float Mg)
	{
		const FVector2D D(Pb.X - Pa.X, Pb.Y - Pa.Y);
		const FVector2D Ua(FMath::Cos(FMath::DegreesToRadians(Ya)), FMath::Sin(FMath::DegreesToRadians(Ya))), Va(-Ua.Y, Ua.X);
		const FVector2D Ub(FMath::Cos(FMath::DegreesToRadians(Yb)), FMath::Sin(FMath::DegreesToRadians(Yb))), Vb(-Ub.Y, Ub.X);
		const float Ha = La * 0.5f + Mg * 0.5f, Wa_ = Wa * 0.5f + Mg * 0.5f, Hb = Lb * 0.5f + Mg * 0.5f, Wb_ = Wb * 0.5f + Mg * 0.5f;
		for (const FVector2D& N : { Ua, Va, Ub, Vb })
		{
			const float Ra = Ha * FMath::Abs(FVector2D::DotProduct(Ua, N)) + Wa_ * FMath::Abs(FVector2D::DotProduct(Va, N));
			const float Rb = Hb * FMath::Abs(FVector2D::DotProduct(Ub, N)) + Wb_ * FMath::Abs(FVector2D::DotProduct(Vb, N));
			if (FMath::Abs(FVector2D::DotProduct(D, N)) > Ra + Rb) return false;
		}
		return true;
	}
}

bool ARDSection::CurveClear23(int32 I, const FVector& P0, const FVector& P1, const FVector& P2, float T0, float T1, float Margin, bool bStillTight) const
{
	// (its footprint along the curve from T0 to T1 against every other car's now (parked ones in their bays left out))
	const FCar23& Cr = Cars23[I];
	// (twelve places along it: at six a bus's turn passed between two of them 4 cm from a car at its line, entered, and stuck there)
	const int32 Ns = T1 - T0 > 0.3f ? 12 : 5;
	for (int32 K = 0; K <= Ns; ++K)
	{
		const float T = FMath::Lerp(T0, T1, K / (float)Ns);
		const FVector P = RDH23Bez(P0, P1, P2, T);
		const float Yw = RDH23BezD(P0, P1, P2, FMath::Clamp(T, 0.01f, 0.99f)).Rotation().Yaw;
		for (int32 O = 0; O < Cars23.Num(); ++O)
		{
			const FCar23& Oc = Cars23[O];
			if (O == I || Oc.State == 3 || FVector::Dist2D(Oc.Pos, P) > 1600.f) continue;
			// (on its curve, one that came onto the crossing after it gives way to it: two that each held the other stood 4 minutes)
			// (by its footprint alone, no margin: skipped altogether, a bus came into the back of a car that had come on after it)
			const bool bLater = bStillTight && Cr.State == 1 && Oc.State == 1 && (Oc.Entered > Cr.Entered || (Oc.Entered == Cr.Entered && O > I));
			// (a car standing at another lane's line waits outside the crossing: only its own footprint counts, no margin (counted with
			// the margin the buses stood 5 minutes at a green; left out, a bus's turn swept 50 cm into one))
			const bool bAtLine = Oc.State == 0 && Oc.V < 30.f && Oc.Lane != Cr.Lane && Lanes23.IsValidIndex(Oc.Lane) && Lanes23[Oc.Lane].Len - Oc.S < Oc.Len * 0.5f + 300.f;
			// (on its curve, a car standing still anywhere counts by its footprint alone: queued in a lane beside a turning bus it waited
			// for the bus, and the bus for it, for minutes)
			const bool bTight = bAtLine || bLater || (bStillTight && Oc.State == 0 && Oc.V < 30.f);
			// (before it goes, 30 cm kept from a car at its line; on its way, its footprint alone)
			if (RDH23Overlap(P, Yw, Cr.Len, Cr.Wid, Oc.Pos, Oc.Yaw, Oc.Len, Oc.Wid, bTight ? (bStillTight ? 0.f : 30.f) : Margin)) return false;
		}
	}
	return true;
}

// ------------------------------------------------------------------------------------------------ the road graph
FVector ARDSection::LanePoint23(int32 L, float S) const
{
	const FLane23& Ln = Lanes23[L];
	return Ln.A + Ln.Way * S;
}

void ARDSection::BuildRoads23()
{
	Lanes23.Reset(); LanesOut23.Reset(); Bays23.Reset(); BusStops23.Reset(); BusRoutes23.Reset();
	const float M = Generator->TileSize;
	// (the square's and the facility's streets are left to people: cars keep off them (PR #33's review: cars across the paved square))
	FIntRect Keep = TownSquare;
	if (TownBlds.IsValidIndex(CastleBld)) Keep.Union(FIntRect(TownBlds[CastleBld].Min, TownBlds[CastleBld].Max));
	Keep.InflateRect(3);
	TMap<int64, int32> LaneOf;          // (run * 2 + dir side) -> lane
	for (int32 Ri = 0; Ri < Runs19.Num(); ++Ri)
	{
		const FRun19& Ru = Runs19[Ri];
		if (Ru.E - Ru.S < 3) continue;
		auto Tile = [&](int32 A, int32 C) { return Ru.bX ? FIntPoint(A, C) : FIntPoint(C, A); };
		const FIntRect Rr(Tile(Ru.S, Ru.C0), Tile(Ru.E, Ru.C1) + (Ru.bX ? FIntPoint(0, 0) : FIntPoint(0, 0)));
		bool bKeep = false;
		for (int32 A = Ru.S; A < Ru.E && !bKeep; ++A) for (int32 C = Ru.C0; C < Ru.C1; ++C) if (Keep.Contains(Tile(A, C))) { bKeep = true; break; }
		if (bKeep) continue;
		const FVector Av = (TileWorld(Tile(Ru.S + 1, Ru.C0)) - TileWorld(Tile(Ru.S, Ru.C0))).GetSafeNormal2D();
		auto Mw = [&](float A) { const FVector P0 = (TileWorld(Tile(Ru.S, Ru.C0)) + TileWorld(Tile(Ru.S, Ru.C1 - 1))) * 0.5f; return P0 + Av * ((A - Ru.S) * M); };
		const bool bZebra = Ru.E - Ru.S >= 4;
		for (int32 Dir = -1; Dir <= 1; Dir += 2)
		{
			FLane23 Ln; Ln.Run = Ri; Ln.Dir = Dir; Ln.bAlongX = Ru.bX;
			Ln.Way = Av * (float)Dir;
			const FVector Right(-Ln.Way.Y, Ln.Way.X, 0.f);
			const bool bInJ = Dir > 0 ? Ru.bStartJ : Ru.bEndJ, bOutJ = Dir > 0 ? Ru.bEndJ : Ru.bStartJ;
			const int32 InJ = Dir > 0 ? Ru.StartJ : Ru.EndJ, OutJ = Dir > 0 ? Ru.EndJ : Ru.StartJ;
			const int32 Zin = Dir > 0 ? Ru.S : Ru.E - 1, Zout = Dir > 0 ? Ru.E - 1 : Ru.S;
			// (it begins past the crossing's zebra and ends at its stop line before the next (as 19 laid them), or a tile in from a
			// street's end where it turns back)
			const FVector Ain = bInJ ? Mw(Zin) + Ln.Way * (bZebra ? 170.f : 60.f) : Mw(Zin) - Ln.Way * 60.f;
			// (its line 2.3 m behind the zebra's (19's paint): the crossings are three tiles, and a bus's turn swept over cars at the painted
			// line)
			const FVector Bout = bOutJ ? Mw(Zout) - Ln.Way * (bZebra ? 420.f : 120.f) : Mw(Zout) + Ln.Way * 40.f;
			Ln.A = Ain + Right * RDH23Lane; Ln.B = Bout + Right * RDH23Lane;
			Ln.Len = FMath::Max(100.f, (float)FVector::DotProduct(Ln.B - Ln.A, Ln.Way));
			Ln.FromJ = bInJ && Junctions19.IsValidIndex(InJ) && !Junctions19[InJ].bPlaza ? InJ : -1;
			Ln.ToJ = bOutJ && Junctions19.IsValidIndex(OutJ) && !Junctions19[OutJ].bPlaza ? OutJ : -1;
			if (Ln.ToJ >= 0) { Ln.Signal = Junctions19[Ln.ToJ].Signal; Ln.bStopSign = Ln.Signal < 0; }
			const int32 Li = Lanes23.Add(Ln);
			LaneOf.Add((int64)Ri * 2 + (Dir > 0 ? 1 : 0), Li);
			if (Ln.FromJ >= 0) LanesOut23.FindOrAdd(Ln.FromJ).Add(Li);
		}
	}
	for (FLane23& Ln : Lanes23) { if (const int32* R_ = LaneOf.Find((int64)Ln.Run * 2 + (Ln.Dir > 0 ? 0 : 1))) Ln.Reverse = *R_; }
	// ---- the bays: the lay-bys and lots without a parked car (19's hashes), each on the lane whose right it is on
	for (const FPark19& Pk : Parks19)
	{
		const FRun19& Ru = Runs19[Pk.Run];
		auto Tile = [&](int32 A, int32 C) { return Ru.bX ? FIntPoint(A, C) : FIntPoint(C, A); };
		const FVector Av = (TileWorld(Tile(Ru.S + 1, Ru.C0)) - TileWorld(Tile(Ru.S, Ru.C0))).GetSafeNormal2D();
		const FVector Cv = (TileWorld(Tile(Ru.S, Ru.C0 + 1)) - TileWorld(Tile(Ru.S, Ru.C0))).GetSafeNormal2D();
		const FVector Rp(-Av.Y, Av.X, 0.f);
		const FVector Out = Cv * (float)Pk.Side;
		const int32 Dir = (Out | Rp) > 0.f ? 1 : -1;
		const int32* Li = LaneOf.Find((int64)Pk.Run * 2 + (Dir > 0 ? 1 : 0));
		if (!Li) continue;
		const int32 Ck = Pk.Side > 0 ? Ru.C1 : Ru.C0 - 1, Cd = Pk.Side > 0 ? Ru.C1 + 1 : Ru.C0 - 2;
		auto Add = [&](const FVector& C, float Yaw)
		{
			FBay23 B; B.Lane = *Li; B.At = C; B.Yaw = Yaw;
			B.S = (float)FVector::DotProduct(C - Lanes23[*Li].A, Lanes23[*Li].Way);
			if (B.S > 400.f && B.S < Lanes23[*Li].Len - 300.f) Bays23.Add(B);
		};
		if (!Pk.bLot)
		{
			if (HashCombine(GetTypeHash(Tile(Pk.A, Ck)), 0xCA75u) % 100u < 75u) continue;          // (a parked car stands there)
			Add((TileWorld(Tile(Pk.A, Ck)) + TileWorld(Tile(Pk.A + 1, Ck))) * 0.5f, (Av * (float)Dir).Rotation().Yaw);
		}
		else
			for (int32 A = Pk.A; A < Pk.B; ++A)
			{
				if (HashCombine(GetTypeHash(Tile(A, Ck)), 0x7075u) % 100u < 67u) continue;
				Add((TileWorld(Tile(A, Ck)) + TileWorld(Tile(A, Cd))) * 0.5f, Out.Rotation().Yaw);
			}
	}
	// ---- the bus stops: each on the lane whose right side it stands by (within 9 m of its line), where the lane runs past it
	for (const FTownSpot& Sp : TownSpots)
	{
		if (Sp.Kind != TS_StreetProp || Sp.Bld != 1) continue;
		int32 BestL = -1; float BestD = 900.f, BestS = 0.f;
		for (int32 L = 0; L < Lanes23.Num(); ++L)
		{
			const FLane23& Ln = Lanes23[L];
			const float S = (float)FVector::DotProduct(Sp.At - Ln.A, Ln.Way);
			if (S < 500.f || S > Ln.Len - 400.f) continue;
			const FVector Right(-Ln.Way.Y, Ln.Way.X, 0.f);
			const float Side = (float)FVector::DotProduct(Sp.At - Ln.A, Right);
			if (Side > 0.f && Side < BestD) { BestD = Side; BestL = L; BestS = S; }
		}
		if (BestL < 0) continue;
		FStop23 St; St.Lane = BestL; St.S = BestS; St.At = Sp.At; St.Yaw = Sp.Yaw;
		BusStops23.Add(St);
	}
	// ---- the buses' two loops: the stops split by which side of the town's middle they stand (east and west), each loop going from
	// stop to nearest stop and back to its first
	if (BusStops23.Num() >= 2)
	{
		FVector Mid = FVector::ZeroVector; for (const FStop23& St : BusStops23) Mid += St.At; Mid /= BusStops23.Num();
		TArray<int32> Side[2];
		for (int32 K = 0; K < BusStops23.Num(); ++K) Side[BusStops23[K].At.X < Mid.X ? 0 : 1].Add(K);
		if (Side[0].Num() == 0 || Side[1].Num() == 0) { Side[0].Reset(); Side[1].Reset(); for (int32 K = 0; K < BusStops23.Num(); ++K) Side[K % 2].Add(K); }
		for (int32 R_ = 0; R_ < 2; ++R_)
		{
			TArray<int32> Left = Side[R_], Loop;
			if (Left.Num() == 0) continue;
			int32 At = Left[0]; Left.RemoveAt(0); Loop.Add(At);
			while (Left.Num() > 0 && Loop.Num() < 6)
			{
				int32 Bi = 0; float Bd = 1e30f;
				for (int32 J = 0; J < Left.Num(); ++J) { const float D = FVector::Dist2D(BusStops23[Left[J]].At, BusStops23[At].At); if (D < Bd) { Bd = D; Bi = J; } }
				At = Left[Bi]; Left.RemoveAt(Bi); Loop.Add(At);
			}
			if (Loop.Num() >= 2 || (Loop.Num() == 1 && BusStops23.Num() > 0)) BusRoutes23.Add(Loop);
		}
	}
	UE_LOG(LogRDHeaven23, Log, TEXT("RDHEAVEN23 roads: %d lanes, %d free bays, %d bus stops, %d bus loops"), Lanes23.Num(), Bays23.Num(), BusStops23.Num(), BusRoutes23.Num());
}

TArray<int32> ARDSection::NextLanes23(int32 L) const
{
	TArray<int32> Out;
	const FLane23& Ln = Lanes23[L];
	if (Ln.ToJ >= 0)
		if (const TArray<int32>* Os = LanesOut23.Find(Ln.ToJ))
			for (const int32 O : *Os) if (O != Ln.Reverse && Lanes23[O].Run != Ln.Run) Out.Add(O);
	// (a street's end, or a crossing with no way on: back along the other lane)
	if (Out.Num() == 0 && Lanes23.IsValidIndex(Ln.Reverse)) Out.Add(Ln.Reverse);
	return Out;
}

bool ARDSection::Route23(int32 From, int32 To, TArray<int32>& Out) const
{
	// (the shortest way by length over the lanes (a few hundred: a plain Dijkstra over an array))
	Out.Reset();
	if (!Lanes23.IsValidIndex(From) || !Lanes23.IsValidIndex(To)) return false;
	if (From == To) return true;
	const int32 Nn = Lanes23.Num();
	TArray<float> D; D.Init(1e30f, Nn); TArray<int32> Prev; Prev.Init(-1, Nn); TArray<bool> Done; Done.Init(false, Nn);
	D[From] = 0.f;
	for (int32 It = 0; It < Nn; ++It)
	{
		int32 U = -1; float Ud = 1e30f;
		for (int32 K = 0; K < Nn; ++K) if (!Done[K] && D[K] < Ud) { Ud = D[K]; U = K; }
		if (U < 0 || U == To) break;
		Done[U] = true;
		for (const int32 V : NextLanes23(U))
		{
			const float W = Lanes23[V].Len + (V == Lanes23[U].Reverse ? 1500.f : 300.f);          // (a turn back costs: drivers go round)
			if (D[U] + W < D[V]) { D[V] = D[U] + W; Prev[V] = U; }
		}
	}
	if (Prev[To] < 0) return false;
	for (int32 C = To; C != From && C >= 0; C = Prev[C]) Out.Insert(C, 0);
	return true;
}

// ------------------------------------------------------------------------------------------------ the drivers' goals
int32 ARDSection::AddressLane23(int32 Bld, float& OutS) const
{
	// (the lane passing the building's door on its right, nearest the door's outside tile)
	OutS = 0.f;
	if (!TownBlds.IsValidIndex(Bld)) return -1;
	static const FIntPoint D4[4] = { FIntPoint(-1, 0), FIntPoint(1, 0), FIntPoint(0, -1), FIntPoint(0, 1) };
	const FVector Door = TileWorld(TownBlds[Bld].DoorTile + D4[TownBlds[Bld].DoorSide]);
	int32 Best = -1; float Bd = 2500.f;
	for (int32 L = 0; L < Lanes23.Num(); ++L)
	{
		const FLane23& Ln = Lanes23[L];
		const float S = (float)FVector::DotProduct(Door - Ln.A, Ln.Way);
		if (S < 0.f || S > Ln.Len) continue;
		const FVector Right(-Ln.Way.Y, Ln.Way.X, 0.f);
		const float Side = (float)FVector::DotProduct(Door - Ln.A, Right);
		if (Side < -100.f) continue;
		if (FMath::Abs(Side) < Bd) { Bd = FMath::Abs(Side); Best = L; OutS = S; }
	}
	return Best;
}

int32 ARDSection::GoalOf23(const FCar23& Cr, float Hour) const
{
	// (the goal tree by the hour: work in the morning and afternoon, lunch at noon, errands late in the afternoon, home in the evening
	// and at night; each driver's own times moved by its seed so they do not all go at once)
	const float Sh = ((Cr.Seed >> 4) % 90u) / 60.f - 0.75f;          // (-45 to +45 minutes)
	const float H = FMath::Fmod(Hour - Sh + 24.f, 24.f);
	if (H >= 7.f && H < 11.5f) return 1;
	if (H >= 11.5f && H < 13.f) return 2;
	if (H >= 13.f && H < 16.5f) return 1;
	if (H >= 16.5f && H < 18.5f) return 3;
	return 0;
}

int32 ARDSection::GoalBuilding23(const FCar23& Cr, int32 Goal) const
{
	switch (Goal)
	{
	case 0: return Cr.Home;
	case 1: return Cr.Work;
	case 2: return Cr.Lunch;
	default: return Cr.Errand;
	}
}

void ARDSection::SetGoal23(int32 Ci, float Hour)
{
	FCar23& Cr = Cars23[Ci];
	Cr.Goal = GoalOf23(Cr, Hour);
	const int32 Bld = GoalBuilding23(Cr, Cr.Goal);
	float S = 0.f;
	const int32 Al = AddressLane23(Bld, S);
	// (its bay: the free one nearest the address (within 120 m), else it drives on round the block and tries again)
	int32 Bi = -1; float Bd = 12000.f;
	const FVector Addr = Al >= 0 ? LanePoint23(Al, S) : FVector::ZeroVector;
	for (int32 K = 0; K < Bays23.Num() && Al >= 0; ++K)
	{
		if (Bays23[K].Car >= 0) continue;
		const float D = FVector::Dist2D(Bays23[K].At, Addr);
		if (D < Bd) { Bd = D; Bi = K; }
	}
	if (Cr.Bay >= 0 && Bays23.IsValidIndex(Cr.Bay) && Bays23[Cr.Bay].Car == Ci) Bays23[Cr.Bay].Car = -1;
	Cr.Bay = Bi;
	if (Bi >= 0) Bays23[Bi].Car = Ci;
	Cr.GoalLane = Bi >= 0 ? Bays23[Bi].Lane : (Lanes23.IsValidIndex(Al) ? Al : FMath::Abs((int32)(Cr.Seed + Ci * 7)) % FMath::Max(1, Lanes23.Num()));
	Cr.GoalS = Bi >= 0 ? Bays23[Bi].S : S;
	Route23(Cr.Lane, Cr.GoalLane, Cr.Route);
}

// ------------------------------------------------------------------------------------------------ the cars made
USkeletalMeshComponent* ARDSection::SeatPerson23(USceneComponent* Pv, int32 Def, const FVector& At, FName Clip, bool bDriver)
{
	if (!Generator->Townsfolk.IsValidIndex(Def)) return nullptr;
	const FRDTownsfolkDef& Df = Generator->Townsfolk[Def];
	const TObjectPtr<UAnimationAsset>* A = Df.WorkClips.Find(Clip);
	if (!Df.Mesh || !A || !*A) return nullptr;
	USkeletalMeshComponent* Sk = NewObject<USkeletalMeshComponent>(this, NAME_None, RF_Transactional);
	Sk->SetSkeletalMesh(Df.Mesh);
	Sk->SetupAttachment(Pv);
	Sk->SetCollisionEnabled(ECollisionEnabled::NoCollision);
	Sk->SetCastShadow(false);
	Sk->VisibilityBasedAnimTickOption = EVisibilityBasedAnimTickOption::OnlyTickPoseWhenRendered;
	Sk->SetRelativeTransform(FTransform(FRotator(0.f, Df.MeshYaw, 0.f), At + FVector(0, 0, Df.MeshZ * 0.f), FVector(Df.Scale)));
	Sk->ComponentTags.Add(bDriver ? FName(TEXT("HeavenDriver23")) : FName(TEXT("HeavenRider23")));
	Sk->RegisterComponent();
	AddInstanceComponent(Sk);
	Sk->PlayAnimation(*A, true);
	if (UAnimSingleNodeInstance* In = Sk->GetSingleNodeInstance()) In->SetPosition(FMath::FRandRange(0.f, 3.f), false);
	return Sk;
}

void ARDSection::HeavenTraffic23()
{
	// (a replan (RestartPlay) makes the cars again: the old drivers and riders go with their cars, not left in the street)
	for (UActorComponent* C : GetComponentsByTag(USkeletalMeshComponent::StaticClass(), TEXT("HeavenDriver23"))) C->DestroyComponent();
	for (UActorComponent* C : GetComponentsByTag(USkeletalMeshComponent::StaticClass(), TEXT("HeavenRider23"))) C->DestroyComponent();
	for (FCar23& Cr : Cars23) if (USceneComponent* C = Cr.C.Get()) C->DestroyComponent(true);
	Cars23.Reset(); ResetTrafficCounts23();
	BuildRoads23();
	if (Lanes23.Num() == 0) return;
	TArray<const FRDPiece*> Kinds; TArray<FName> KindNames;
	for (int32 K = 1; K <= 6; ++K) { const FName Nk(*FString::Printf(TEXT("Heaven.Car_%d"), K)); if (const FRDPiece* P = Generator->Piece(Nk)) if (P->Mesh) { Kinds.Add(P); KindNames.Add(Nk); } }
	if (Kinds.Num() == 0) return;
	const FRDPiece* Bus = nullptr; TArray<const FRDPiece*> Small;
	for (const FRDPiece* P : Kinds) { if (P->Size.X > 900.f) Bus = P; else Small.Add(P); }
	if (Small.Num() == 0) Small = Kinds;
	// (the drivers and passengers: the town's own townsfolk with a Drive clip)
	const FString Here = Generator->TownName;
	TArray<int32> Folk;
	for (int32 D = 0; D < Generator->Townsfolk.Num(); ++D)
	{
		const FRDTownsfolkDef& Df = Generator->Townsfolk[D];
		if (Df.Mesh && Df.Role == ERDTownRole::Townsfolk && Df.WorkClips.Contains(TEXT("Drive")) && (Df.Town == Here || Df.Town.IsEmpty())) Folk.Add(D);
	}
	// (the buildings by kind for the goals)
	TArray<int32> Homes, Works, Foods, Shops;
	for (int32 B = 0; B < TownBlds.Num(); ++B)
	{
		if (B == CastleBld || TownBlds[B].bBoarded) continue;
		switch (TownBlds[B].Kind)
		{
		case TK_Home: Homes.Add(B); break;
		case TK_Office: case TK_SkyTower: case TK_Research: Works.Add(B); break;
		case TK_Tavern: Foods.Add(B); Works.Add(B); break;
		case TK_Shop: case TK_Store: Shops.Add(B); Foods.Add(B); Works.Add(B); break;
		default: Works.Add(B); break;
		}
	}
	if (Homes.Num() == 0) Homes = Works;
	if (Foods.Num() == 0) Foods = Works;
	if (Shops.Num() == 0) Shops = Works;
	auto Pick = [](const TArray<int32>& A, uint32 H) { return A.Num() > 0 ? A[H % (uint32)A.Num()] : -1; };
	const float Hour = Generator->GetTownHour();
	auto Make = [&](const FRDPiece* P, int32 Lane, float S, uint32 Hh, bool bBus_) -> int32
	{
		USceneComponent* Pv = AddPivot(RootComponent, FTransform::Identity);
		if (!Pv) return -1;
		UStaticMeshComponent* C = AddMesh(Pv, P->Mesh, P->Adjust, true);
		if (C) { if (P->Material) C->SetMaterial(0, P->Material); C->ComponentTags.Add(TEXT("HeavenCar")); }
		Pv->ComponentTags.Add(TEXT("HeavenCar"));
		FCar23 Cr; Cr.C = Pv; Cr.Body = C; Cr.Lane = Lane; Cr.S = S; Cr.Seed = Hh; Cr.bBus = bBus_;
		Cr.Len = (float)P->Size.X; Cr.Wid = (float)P->Size.Y;
		Cr.VMax = bBus_ ? 850.f : 950.f + (float)((Hh >> 12) % 300u);
		Cr.Home = Pick(Homes, Hh >> 3); Cr.Work = Pick(Works, Hh >> 9); Cr.Lunch = Pick(Foods, Hh >> 15); Cr.Errand = Pick(Shops, Hh >> 21);
		// (its driver, seated at the front left (the cars' front is their +X: right-hand traffic, the wheel on the left))
		const FVector Seat = bBus_ ? FVector(Cr.Len * Generator->BusSeat23.X, Cr.Wid * Generator->BusSeat23.Y, Generator->BusSeat23.Z)
		                           : FVector(Cr.Len * Generator->DriverSeat23.X, Cr.Wid * Generator->DriverSeat23.Y, Generator->DriverSeat23.Z);
		if (Folk.Num() > 0) { Cr.Driver = SeatPerson23(Pv, Folk[(Hh >> 5) % (uint32)Folk.Num()], Seat, TEXT("Drive"), true); Cr.DriverDef = Folk[(Hh >> 5) % (uint32)Folk.Num()]; }
		if (bBus_)
			for (int32 K = 0; K < 6; ++K)
			{
				// (its seats: two rows along the bus's length; shown as it carries people)
				const FVector At(Cr.Len * (0.22f - 0.11f * (K / 2)), Cr.Wid * (K % 2 ? 0.24f : -0.24f), Generator->BusSeat23.Z);
				USkeletalMeshComponent* Sk = Folk.Num() > 0 ? SeatPerson23(Pv, Folk[(Hh >> (K + 2)) % (uint32)Folk.Num()], At, TEXT("SitTalk"), false) : nullptr;
				if (Sk) Sk->SetVisibility(false);
				Cr.Riders.Add(Sk);
			}
		const int32 Ci = Cars23.Add(Cr);
		return Ci;
	};
	int32 Buses = 0;
	for (int32 R_ = 0; R_ < BusRoutes23.Num() && Bus; ++R_)
	{
		const FStop23& St = BusStops23[BusRoutes23[R_][0]];
		const int32 Ci = Make(Bus, St.Lane, FMath::Max(Bus->Size.X * 0.6f, St.S - 1500.f), HashCombine(0xB05u, (uint32)R_), true);
		if (Ci < 0) continue;
		FCar23& Cr = Cars23[Ci]; Cr.BusRoute = R_; Cr.BusNext = 0;
		Route23(Cr.Lane, St.Lane, Cr.Route); Cr.GoalLane = St.Lane; Cr.GoalS = St.S; Cr.Goal = 4;
		++Buses;
	}
	auto Free = [&](int32 L, float S) { for (const FCar23& O : Cars23) if (O.Lane == L && FMath::Abs(O.S - S) < 2000.f) return false; return true; };
	// (a car every 90 m of lane over all the lanes together (the lanes between crossings are mostly shorter than that: counted lane by
	// lane, 8 cars came of 142 lanes), none within 6 m of a lane's end)
	int32 Made = 0; float Acc = Generator->TrafficSpacing23 * 0.5f;
	for (int32 L = 0; L < Lanes23.Num(); ++L)
	{
		const FLane23& Ln = Lanes23[L];
		float S = Acc > Ln.Len ? -1.f : Acc;
		Acc -= Ln.Len;
		while (S >= 0.f)
		{
			if (S > 600.f && S < Ln.Len - 600.f && Free(L, S))
			{
				const uint32 Hh = HashCombine(GetTypeHash(FIntPoint(Ln.Run, Ln.Dir)), (uint32)Made * 2654435761u);
				const FRDPiece* P = Small[Hh % (uint32)Small.Num()];
				const int32 Ci = Make(P, L, S, Hh, false);
				if (Ci >= 0) { SetGoal23(Ci, Hour); ++Made; }
			}
			S += Generator->TrafficSpacing23; Acc += Generator->TrafficSpacing23;
			if (S > Ln.Len) break;
		}
		if (Acc < 0.f) Acc += Generator->TrafficSpacing23 * FMath::CeilToFloat(-Acc / Generator->TrafficSpacing23);
	}
	for (FCar23& Cr : Cars23) PlaceCar23(Cr);
	UE_LOG(LogRDHeaven23, Log, TEXT("RDHEAVEN23 traffic: %d cars with drivers (%d townsfolk to drive), %d buses"), Made, Folk.Num(), Buses);
}

void ARDSection::PlaceCar23(FCar23& Cr)
{
	USceneComponent* C = Cr.C.Get();
	if (!C) return;
	FVector P; FVector W;
	if (Cr.State == 1)
	{
		P = RDH23Bez(Cr.P0, Cr.P1, Cr.P2, Cr.T); W = RDH23BezD(Cr.P0, Cr.P1, Cr.P2, FMath::Clamp(Cr.T, 0.01f, 0.99f)).GetSafeNormal2D();
	}
	else if (Cr.State >= 2 && Bays23.IsValidIndex(Cr.Bay))
	{
		const FBay23& B = Bays23[Cr.Bay];
		const FVector Lp = LanePoint23(Cr.Lane, B.S);
		const float U = FMath::SmoothStep(0.f, 1.f, Cr.T);
		P = FMath::Lerp(Lp, B.At, U);
		W = FMath::Lerp(Lanes23[Cr.Lane].Way, FRotator(0, B.Yaw, 0).Vector(), U).GetSafeNormal2D();
	}
	else { P = LanePoint23(Cr.Lane, Cr.S); W = Lanes23[Cr.Lane].Way; }
	Cr.Pos = P; Cr.Yaw = W.Rotation().Yaw;
	C->SetWorldLocationAndRotation(FVector(P.X, P.Y, GetActorLocation().Z + 2.f), FRotator(0.f, Cr.Yaw, 0.f));
}

void ARDSection::CurveOf23(int32 L, int32 Nx, FVector& P0, FVector& P1, FVector& P2) const
{
	// (from the lane's line to the next lane's start; its control where the two lanes' lines meet; straight on, half way; back, out past the end)
	const FLane23& Ln = Lanes23[L]; const FLane23& Nl = Lanes23[Nx];
	P0 = Ln.B; P2 = Nl.A;
	const FVector D = Nl.A - Ln.B;
	if (FMath::Abs((float)FVector::CrossProduct(Ln.Way, Nl.Way).Z) > 0.3f)
	{
		const float Den = (float)(Ln.Way.X * Nl.Way.Y - Ln.Way.Y * Nl.Way.X);
		const float Tt = (float)((D.X * Nl.Way.Y - D.Y * Nl.Way.X) / Den);
		P1 = Ln.B + Ln.Way * FMath::Clamp(Tt, 50.f, 2500.f);
	}
	else if (FVector::DotProduct(Ln.Way, Nl.Way) > 0.f) P1 = (Ln.B + Nl.A) * 0.5f;
	else P1 = (Ln.B + Nl.A) * 0.5f + Ln.Way * 700.f;
}

float ARDDungeonGenerator::SignalAmberLeft23(float T, float Offset, bool bAlongX) const
{
	// (as SignalPhase19: the seconds left of this road's amber now (0 when it is not amber))
	const float G = FMath::Max(SignalGreen19, 1.f), A = FMath::Max(SignalAmber19, 0.5f), Rr = FMath::Max(SignalAllRed19, 0.f);
	const float C = 2.f * (G + A + Rr), Half = G + A + Rr;
	float Tt = FMath::Fmod(T + Offset, C); if (Tt < 0.f) Tt += C;
	const bool bXTurn = Tt < Half;
	if (bXTurn != bAlongX) return 0.f;
	const float U = bXTurn ? Tt : Tt - Half;
	return U >= G && U < G + A ? G + A - U : 0.f;
}

// ------------------------------------------------------------------------------------------------ the traffic's tick
void ARDSection::TickTraffic23(float Dt, const FVector& Her)
{
	if (Cars23.Num() == 0 || Dt <= 0.f) return;
	const UWorld* Wd = GetWorld();
	const float Now = Wd ? Wd->GetTimeSeconds() : 0.f;
	const bool bRun = CVarRDTraffic23.GetValueOnGameThread() != 0;
	const float Hour = Generator->GetTownHour();
	// (by distance: the far cars a quarter second at a time, the near every frame)
	FarClock23 += Dt;
	const bool bFarTick = FarClock23 >= 0.25f;
	const float FarDt = FarClock23;
	if (bFarTick) FarClock23 = 0.f;
	// (who is crossing which crossing now, for the right of way)
	TMap<int32, TArray<int32>> InJ;
	for (int32 I = 0; I < Cars23.Num(); ++I) if (Cars23[I].State == 1 && Lanes23.IsValidIndex(Cars23[I].Lane) && Lanes23[Cars23[I].Lane].ToJ >= 0) InJ.FindOrAdd(Lanes23[Cars23[I].Lane].ToJ).Add(I);
	// (each lane's cars by their place along it: the car ahead of each)
	TMap<int32, TArray<int32>> OnLane;
	// (one turning into its bay is still in its lane until it is in (left out, the car behind drove through it))
	for (int32 I = 0; I < Cars23.Num(); ++I) if (Cars23[I].State == 0 || Cars23[I].State == 4 || (Cars23[I].State == 2 && Cars23[I].T < 0.85f)) OnLane.FindOrAdd(Cars23[I].Lane).Add(I);
	for (TPair<int32, TArray<int32>>& Kv : OnLane) Kv.Value.Sort([this](int32 A, int32 B) { return Cars23[A].S < Cars23[B].S; });
	for (int32 I = 0; I < Cars23.Num(); ++I)
	{
		FCar23& Cr = Cars23[I];
		USceneComponent* Cc = Cr.C.Get();
		if (!Cc || !Lanes23.IsValidIndex(Cr.Lane)) continue;
		const float DistHer = FVector::Dist2D(Cr.Pos, Her);
		const bool bFar = DistHer > 15000.f;
		if (bFar && !bFarTick) continue;
		const float Ddt = bFar ? FarDt : Dt;
		// (by distance: drawn within 200 m, its driver within 60 m, its collision within 30 m)
		const bool bShow = DistHer < 20000.f, bDriver = DistHer < 6000.f, bCol = DistHer < 3000.f;
		if (bShow != Cr.bShown) { Cr.bShown = bShow; Cc->SetVisibility(bShow, true); }
		if (bShow && bDriver != Cr.bDriverShown)
		{
			Cr.bDriverShown = bDriver;
			if (USkeletalMeshComponent* Dr = Cr.Driver.Get()) Dr->SetVisibility(bDriver);
			for (int32 K = 0; K < Cr.Riders.Num(); ++K) if (USkeletalMeshComponent* Rd = Cr.Riders[K].Get()) Rd->SetVisibility(bDriver && K < Cr.Passengers);
		}
		if (bCol != Cr.bCol) { Cr.bCol = bCol; if (UStaticMeshComponent* B = Cr.Body.Get()) B->SetCollisionEnabled(bCol ? ECollisionEnabled::QueryAndPhysics : ECollisionEnabled::NoCollision); }
		if (!bRun) continue;
		const FLane23& Ln = Lanes23[Cr.Lane];
		// ---- parked: in, waiting, out
		if (Cr.State == 2)
		{
			Cr.T = FMath::Min(1.f, Cr.T + Ddt / 2.5f); PlaceCar23(Cr); if (Bays23.IsValidIndex(Cr.Bay)) Cr.S = Bays23[Cr.Bay].S;
			if (Cr.T >= 1.f) { Cr.State = 3; ++Parks23; Cr.Until = Now + (Cr.Goal == 0 && GoalOf23(Cr, Hour) == 0 ? 90.f : 20.f + (float)((Cr.Seed >> 7) % 40u)); Cr.V = 0.f; }
			continue;
		}
		if (Cr.State == 3)
		{
			if (Now < Cr.Until) continue;
			// (home at night stays home: looked at again later)
			if (GoalOf23(Cr, Hour) == Cr.Goal) { Cr.Until = Now + 10.f; continue; }
			// (out only when the lane behind the bay is clear for 15 m)
			bool bClear = true;
			if (const TArray<int32>* Os = OnLane.Find(Cr.Lane))
				for (const int32 O : *Os)
					if (O != I && Cars23[O].S < Bays23[Cr.Bay].S + Cr.Len && (Cars23[O].S > Bays23[Cr.Bay].S - 3000.f || (Cars23[O].V > 200.f && Cars23[O].S > Bays23[Cr.Bay].S - 4000.f))) bClear = false;
			// (and nothing crossing into the lane behind it)
			for (const FCar23& Oc : Cars23) if (Oc.State == 1 && Oc.Next == Cr.Lane && Bays23[Cr.Bay].S < 4000.f) bClear = false;
			if (!bClear) continue;
			Cr.State = 4; Cr.T = 1.f; Cr.S = Bays23[Cr.Bay].S;
			continue;
		}
		if (Cr.State == 4)
		{
			Cr.T = FMath::Max(0.f, Cr.T - Ddt / 2.5f); PlaceCar23(Cr);
			if (Cr.T <= 0.f) { Cr.State = 0; Cr.V = 0.f; SetGoal23(I, Hour); }
			continue;
		}
		// ---- crossing a crossing on its curve
		if (Cr.State == 1)
		{
			// (no car crossing near its way ahead: it waits on the curve)
			// (its footprint a few metres on along the curve against every car's now: by footprints, not distances (a distance from
			// the curve held a car going straight behind the car waiting at the other side's line, and the town locked up))
			const FVector Ahead = RDH23Bez(Cr.P0, Cr.P1, Cr.P2, FMath::Min(1.f, Cr.T + 0.25f));
			const float Step = FMath::Min(1.f, Cr.T + 250.f / FMath::Max(Cr.CrossLen, 100.f));
			bool bBlocked = !CurveClear23(I, Cr.P0, Cr.P1, Cr.P2, FMath::Min(1.f, Cr.T + 0.02f), Step, 80.f, true);
			// (the lane it goes into has room)
			if (const TArray<int32>* Os = OnLane.Find(Cr.Next))
				for (const int32 O : *Os) if (Cars23[O].S - Cars23[O].Len * 0.5f < Cr.Len * 0.5f + RDH23Gap * 0.5f && Cr.T > 0.6f) bBlocked = true;
			if (FVector::Dist2D(Her, Ahead) < 350.f) bBlocked = true;
			for (const FVector& Y : CarYield22) if (FVector::Dist2D(Y, Ahead) < 300.f) bBlocked = true;
			float Vt = bBlocked ? 0.f : 650.f;
			// (the next lane's last car: the curve ends with the lane's gap kept (onto a queue at the crossing's speed it stopped dead))
			if (const TArray<int32>* Qs = OnLane.Find(Cr.Next); Qs && Qs->Num() > 0)
			{
				const FCar23& Q = Cars23[(*Qs)[0]];
				const float Gq = Q.S - Q.Len * 0.5f + (1.f - Cr.T) * Cr.CrossLen - Cr.Len * 0.5f - RDH23Gap;
				Vt = FMath::Min(Vt, FMath::Sqrt(2.f * RDH23Dec * 0.8f * FMath::Max(Gq, 0.f)));
			}
			Cr.Why = bBlocked ? 7 : 0;
			if (Cr.V < 15.f) { if (Cr.StillSince < 0.f) Cr.StillSince = Now; } else Cr.StillSince = -1.f;
			Cr.V = Cr.V < Vt ? FMath::Min(Vt, Cr.V + RDH23Acc * Ddt) : FMath::Max(Vt, Cr.V - RDH23Dec * 1.5f * Ddt);
			Cr.T += Cr.V * Ddt / FMath::Max(Cr.CrossLen, 100.f);
			if (Cr.T >= 1.f)
			{
				Cr.State = 0; Cr.Lane = Cr.Next; Cr.S = 0.f; Cr.bStoppedHere = false; Cr.StopAt = -1.f;
				if (Cr.Route.Num() > 0 && Cr.Route[0] == Cr.Lane) Cr.Route.RemoveAt(0);
			}
			PlaceCar23(Cr);
			continue;
		}
		// ---- its goal looked at again every 10 s: the hour moves on (a car never at its bay kept its morning goal all day)
		if (!Cr.bBus && Now >= Cr.Rethink)
		{
			Cr.Rethink = Now + 10.f;
			if (GoalOf23(Cr, Hour) != Cr.Goal) SetGoal23(I, Hour);
		}
		// ---- along its lane: the room ahead (the car ahead, her, a pedestrian, its stop line or its bay or stop)
		float Room = 1e9f; uint8 Why = 0;
		auto Hold = [&](float R_, uint8 W_) { if (R_ < Room) { Room = R_; Why = W_; } };
		if (const TArray<int32>* Os = OnLane.Find(Cr.Lane))
			for (const int32 O : *Os)
				if (O != I && Cars23[O].S > Cr.S) { Hold(Cars23[O].S - Cars23[O].Len * 0.5f - Cr.S - Cr.Len * 0.5f - RDH23Gap, 1); break; }
		// (a car of this lane gone onto its crossing is still ahead of its queue (left out, the next one rolled into its back while it
		// waited on its curve's start))
		for (int32 O = 0; O < Cars23.Num(); ++O)
			if (O != I && Cars23[O].State == 1 && Cars23[O].Lane == Cr.Lane)
				Hold(Ln.Len + Cars23[O].T * Cars23[O].CrossLen - Cars23[O].Len * 0.5f - Cr.S - Cr.Len * 0.5f - RDH23Gap, 1);
		// (a car crossing into this lane's start, not yet clear of it)
		for (int32 O = 0; O < Cars23.Num(); ++O)
			if (O != I && Cars23[O].State == 1 && Cars23[O].Next == Cr.Lane && Cars23[O].T > 0.5f && Cr.S < 300.f) Hold(0.f, 8);
		// (a car on a crossing, its body over the lane's end (a turning bus): the footprint 1.5 m ahead must keep off it (a queued car
		// rolled 50 cm into a bus, and the bus waited on it two minutes))
		// (and off the rest of its way: a car that drew up to its line inside a bus's turn still to come held the bus for minutes, and
		// the bus held it)
		for (int32 O = 0; O < Cars23.Num(); ++O)
		{
			const FCar23& Oc = Cars23[O];
			if (O == I || Oc.State != 1 || Oc.Lane == Cr.Lane || FVector::Dist2D(Oc.Pos, Cr.Pos) > 2500.f) continue;
			for (int32 K = 0; K <= 4; ++K)
			{
				const float T = FMath::Lerp(Oc.T, 1.f, K / 4.f);
				const FVector P = RDH23Bez(Oc.P0, Oc.P1, Oc.P2, T);
				const float Yw = RDH23BezD(Oc.P0, Oc.P1, Oc.P2, FMath::Clamp(T, 0.01f, 0.99f)).Rotation().Yaw;
				if (RDH23Overlap(Cr.Pos + Ln.Way * 150.f, Cr.Yaw, Cr.Len, Cr.Wid, P, Yw, Oc.Len, Oc.Wid, 40.f) && !RDH23Overlap(Cr.Pos, Cr.Yaw, Cr.Len, Cr.Wid, P, Yw, Oc.Len, Oc.Wid, 0.f)) { Hold(0.f, 7); break; }
			}
		}
		const FVector Right(-Ln.Way.Y, Ln.Way.X, 0.f);
		auto Obstacle = [&](const FVector& P, float Half)
		{
			const FVector D = P - Cr.Pos;
			const float Al = (float)FVector::DotProduct(D, Ln.Way), Si = FMath::Abs((float)FVector::DotProduct(D, Right));
			if (Al > 0.f && Al < 2500.f && Si < 260.f) return Al - Cr.Len * 0.5f - Half - 150.f;
			return 1e9f;
		};
		if (FMath::Abs(Her.Z - Cr.Pos.Z) < 400.f) Hold(Obstacle(Her, 40.f), 2);
		for (const FVector& Y : CarYield22) Hold(Obstacle(Y, 40.f), 3);
		// (its stop: the bus's stop, the car's bay, or the line before the crossing when it must stop there)
		const bool bAtGoalLane = Cr.Lane == Cr.GoalLane;
		float StopS = -1.f;
		if (bAtGoalLane && Cr.GoalS >= Cr.S - 50.f && (Cr.bBus || Cr.Bay >= 0)) StopS = Cr.GoalS;
		bool bMayGo = true; uint8 WhyStop = 0;
		// (once it has decided to go on a green or amber within its braking distance, still moving, the light turning red does not stop
		// it dead at the line; held by anything (a car ahead), it decides again (committed while held, three went through red))
		if (StopS < 0.f && Ln.ToJ >= 0)
		{
			const float ToLine = Ln.Len - Cr.S - Cr.Len * 0.5f;
			if (Ln.Signal >= 0 && Signals19.IsValidIndex(Ln.Signal))
			{
				const int32 Ph = Generator->SignalPhase19(Now, Signals19[Ln.Signal].Offset, Ln.bAlongX);
				// (red stops it. Amber: it goes on when it reaches the line before the amber ends; else it stops when it can stop at its
				// usual braking; closer than that it goes on (a car that went on later than that ran the red; one that stopped later
				// stopped dead))
				const float Brake = Cr.V * Cr.V / (2.f * RDH23Dec) + 50.f;
				bool bStop = Ph == 0;
				if (Ph == 1)
				{
					const float Left = Generator->SignalAmberLeft23(Now, Signals19[Ln.Signal].Offset, Ln.bAlongX);
					const bool bMakesIt = Cr.V > 100.f && ToLine / Cr.V < Left - 0.3f;
					bStop = !bMakesIt && ToLine > Brake * 0.6f;
				}
				if (bStop) { bMayGo = false; WhyStop = 4; }
			}
			else if (Ln.bStopSign && !Cr.bStoppedHere) { bMayGo = false; WhyStop = 5; }
			// (a left turn yields to what comes the other way)
			int32 Nx = Cr.Route.Num() > 0 ? Cr.Route[0] : -1;
			if (!NextLanes23(Cr.Lane).Contains(Nx)) { const TArray<int32> Op = NextLanes23(Cr.Lane); Nx = Op.Num() ? Op[(Cr.Seed + (uint32)Cr.Lane) % (uint32)Op.Num()] : -1; if (Nx >= 0) { Cr.Route.Reset(); Cr.Route.Add(Nx); } }
			if (bMayGo && Lanes23.IsValidIndex(Nx) && FVector::CrossProduct(Ln.Way, Lanes23[Nx].Way).Z < -0.5f)
				for (int32 O = 0; O < Cars23.Num(); ++O)
				{
					const FCar23& Oc = Cars23[O];
					if (O == I || Oc.State != 0 || !Lanes23.IsValidIndex(Oc.Lane)) continue;
					const FLane23& Ol = Lanes23[Oc.Lane];
					// (to one coming on, moving: one standing at its line (waiting to turn left too) is no reason, or two waited for
					// each other two minutes)
					// (and to one standing at the other line with its way open, that goes straight on or turns right: it will come)
					bool bComes = Oc.V > 150.f;
					if (!bComes && Ol.Len - Oc.S < Oc.Len * 0.5f + 300.f && Oc.Route.Num() > 0 && Lanes23.IsValidIndex(Oc.Route[0]))
						bComes = FVector::CrossProduct(Ol.Way, Lanes23[Oc.Route[0]].Way).Z >= -0.5f;
					if (Ol.ToJ == Ln.ToJ && FVector::DotProduct(Ol.Way, Ln.Way) < -0.8f && Ol.Len - Oc.S < 3500.f && bComes) { bMayGo = false; WhyStop = 6; break; }
				}
			// (its whole curve clear of every car now, the waiting ones at the other lines too (a bus's turn swept over a car at its
			// line), at the line only: further back nothing is decided)
			// (looked at from its braking distance on, so a blocked curve slows it, not stops it dead at the line (from 6 to 8 m/s to 0
			// in a quarter second))
			if (bMayGo && Ln.Len - Cr.S < Cr.V * Cr.V / (2.f * RDH23Dec * 0.8f) + Cr.Len * 0.5f + 300.f && Lanes23.IsValidIndex(Nx))
			{
				FVector Q0, Q1, Q2; CurveOf23(Cr.Lane, Nx, Q0, Q1, Q2);
				// (held 20 s by that alone, it goes: its curve is still guarded step by step)
				if (!CurveClear23(I, Q0, Q1, Q2, 0.05f, 1.f, 60.f) && !(Cr.Why == 7 && Cr.StillSince >= 0.f && Now - Cr.StillSince > 20.f)) { bMayGo = false; WhyStop = 7; }
				// (the crossing reserved: its whole way against the rest of the way of every car crossing it now (two turning across each
				// other from opposite sides went in the same moment, each seeing the other at its line, and stood locked in the middle))
				for (int32 O = 0; O < Cars23.Num() && bMayGo; ++O)
				{
					const FCar23& Oc = Cars23[O];
					if (O == I || Oc.State != 1 || !Lanes23.IsValidIndex(Oc.Lane) || Lanes23[Oc.Lane].ToJ != Ln.ToJ) continue;
					for (int32 A = 0; A <= 8 && bMayGo; ++A)
					{
						const float Ta = A / 8.f;
						const FVector Pa = RDH23Bez(Q0, Q1, Q2, Ta); const float Ya = RDH23BezD(Q0, Q1, Q2, FMath::Clamp(Ta, 0.01f, 0.99f)).Rotation().Yaw;
						for (int32 B = 0; B <= 6; ++B)
						{
							const float Tb = FMath::Lerp(Oc.T, 1.f, B / 6.f);
							const FVector Pb = RDH23Bez(Oc.P0, Oc.P1, Oc.P2, Tb); const float Yb = RDH23BezD(Oc.P0, Oc.P1, Oc.P2, FMath::Clamp(Tb, 0.01f, 0.99f)).Rotation().Yaw;
							if (RDH23Overlap(Pa, Ya, Cr.Len, Cr.Wid, Pb, Yb, Oc.Len, Oc.Wid, 40.f)) { bMayGo = false; WhyStop = 7; break; }
						}
					}
				}
			}
			if (!bMayGo) StopS = Ln.Len;
		}
		if (StopS >= 0.f) Hold(StopS - Cr.S - (Cr.bBus || Cr.Bay >= 0 && bAtGoalLane ? 0.f : Cr.Len * 0.5f), (Cr.bBus || Cr.Bay >= 0) && bAtGoalLane ? 9 : WhyStop);
		// (its speed from the room: easing to a stop that ends at the room, and up to its limit)
		float Vt = FMath::Min(Cr.VMax, FMath::Sqrt(2.f * RDH23Dec * 0.8f * FMath::Max(Room, 0.f)));
		// (down to the crossing's speed by the line: no step from its street speed onto the curve)
		if (Ln.ToJ >= 0 || Lanes23.IsValidIndex(Ln.Reverse)) Vt = FMath::Min(Vt, FMath::Sqrt(650.f * 650.f + 2.f * RDH23Dec * 0.8f * FMath::Max(Ln.Len - Cr.S, 0.f)));
		Cr.V = Cr.V < Vt ? FMath::Min(Vt, Cr.V + RDH23Acc * Ddt) : FMath::Max(Vt, Cr.V - RDH23Dec * 1.6f * Ddt);
		if (Room < -30.f) Cr.V = 0.f;
		Cr.Why = Room < 3000.f ? Why : 0;
		if (Cr.V < 15.f) { if (Cr.StillSince < 0.f) Cr.StillSince = Now; } else Cr.StillSince = -1.f;
		Cr.S = FMath::Min(Cr.S + Cr.V * Ddt, Ln.Len);
		// ---- what happens at the stop
		if (StopS >= 0.f && Cr.V < 15.f && StopS - Cr.S < 120.f + (Cr.bBus || Cr.Bay >= 0 ? 0.f : Cr.Len * 0.5f))
		{
			if (Cr.bBus && bAtGoalLane)
			{
				// (a bus at its stop: 6 s, some get off, those waiting get on; then to the next stop of its loop)
				if (Cr.StopAt < 0.f) { Cr.StopAt = Now; BusArrive23(I); }
				if (Now - Cr.StopAt >= Generator->BusDwell23)
				{
					Cr.StopAt = -1.f;
					const TArray<int32>& Loop = BusRoutes23[Cr.BusRoute];
					Cr.BusNext = (Cr.BusNext + 1) % Loop.Num();
					const FStop23& St = BusStops23[Loop[Cr.BusNext]];
					Cr.GoalLane = St.Lane; Cr.GoalS = St.S;
					if (St.Lane == Cr.Lane && St.S <= Cr.S + 100.f) { TArray<int32> Nx = NextLanes23(Cr.Lane); Route23(Nx.Num() ? Nx[0] : Cr.Lane, St.Lane, Cr.Route); if (Nx.Num()) Cr.Route.Insert(Nx[0], 0); }
					else Route23(Cr.Lane, St.Lane, Cr.Route);
				}
			}
			else if (!Cr.bBus && Cr.Bay >= 0 && bAtGoalLane)
			{
				// (at its bay: in it)
				Cr.State = 2; Cr.T = 0.f; ++Arrivals23;
			}
			else if (Ln.bStopSign && !Cr.bStoppedHere)
			{
				// (a stop sign: a full stop of a second, then on when the crossing is clear)
				if (Cr.StopAt < 0.f) Cr.StopAt = Now;
				if (Now - Cr.StopAt >= 1.f) { Cr.bStoppedHere = true; ++StopSignStops23; Cr.StopAt = -1.f; }
			}
		}
		// ---- at the line with the way open: onto the crossing (or back at a street's end)
		if (Cr.S >= Ln.Len - 1.f && bMayGo && (StopS < 0.f || !bAtGoalLane))
		{
			if (Ln.bStopSign && !Cr.bStoppedHere) ++StopSignRolls23;          // (never: a stop not made)
			if (Ln.Signal >= 0 && Signals19.IsValidIndex(Ln.Signal) && Generator->SignalPhase19(Now, Signals19[Ln.Signal].Offset, Ln.bAlongX) == 0) ++RedRuns23;
			int32 Nx = Cr.Route.Num() > 0 ? Cr.Route[0] : -1;
			const TArray<int32> Opts = NextLanes23(Cr.Lane);
			if (!Opts.Contains(Nx)) { Nx = Opts.Num() ? Opts[(Cr.Seed + (uint32)Cr.S) % (uint32)Opts.Num()] : -1; if (Nx >= 0 && Cr.Goal >= 0 && !Cr.bBus) Route23(Nx, Cr.GoalLane, Cr.Route); }
			if (Nx >= 0)
			{
				Cr.Next = Nx; Cr.State = 1; Cr.T = 0.f; Cr.Entered = Now;
				CurveOf23(Cr.Lane, Nx, Cr.P0, Cr.P1, Cr.P2);
				Cr.CrossLen = 0.f; FVector Pr = Cr.P0;
				for (int32 K = 1; K <= 8; ++K) { const FVector Q = RDH23Bez(Cr.P0, Cr.P1, Cr.P2, K / 8.f); Cr.CrossLen += FVector::Dist2D(Pr, Q); Pr = Q; }
				// (no clamp onto the curve: it eases down to the crossing's speed on it (clamped, three went from 10.7 to 6.5 m/s at once))
			}
		}
		PlaceCar23(Cr);
	}
	// (the closest two cars' footprints apart, for the tests: by their middles less their half lengths along the line between them)
	if (bFarTick)
		for (int32 I = 0; I < Cars23.Num(); ++I)
			for (int32 J = I + 1; J < Cars23.Num(); ++J)
			{
				const FCar23& A = Cars23[I]; const FCar23& B = Cars23[J];
				if (A.State >= 2 && A.State <= 3 && B.State >= 2 && B.State <= 3) continue;
				const float D = FVector::Dist2D(A.Pos, B.Pos);
				if (D > 1500.f) continue;
				// (the largest margin at which their footprints keep apart, to 5 cm (the projection on the line between their middles read
				// a bus beside a parked car 2.4 m "into" it))
				float Gp = -50.f;
				if (!RDH23Overlap(A.Pos, A.Yaw, A.Len, A.Wid, B.Pos, B.Yaw, B.Len, B.Wid, 0.f))
				{
					float Lo = 0.f, Hi = 1000.f;
					for (int32 It = 0; It < 8; ++It) { const float Mi = (Lo + Hi) * 0.5f; if (RDH23Overlap(A.Pos, A.Yaw, A.Len, A.Wid, B.Pos, B.Yaw, B.Len, B.Wid, Mi)) Hi = Mi; else Lo = Mi; }
					Gp = Lo;
				}
				if (Gp < MinGap23) { MinGap23 = Gp; MinGapWhat23 = FString::Printf(TEXT("gap|%d|%d|%d|%d|%d|%d|%.0f|%.0f|%.0f|%d|%d"), I, J, A.State, B.State, A.Lane, B.Lane, (A.Pos.X + B.Pos.X) * 0.5f, (A.Pos.Y + B.Pos.Y) * 0.5f, Gp, A.bBus ? 1 : 0, B.bBus ? 1 : 0); }
			}
}

void ARDSection::BusArrive23(int32 Ci)
{
	FCar23& Cr = Cars23[Ci];
	const FStop23* St = nullptr;
	int32 Si = -1;
	if (BusRoutes23.IsValidIndex(Cr.BusRoute)) { Si = BusRoutes23[Cr.BusRoute][Cr.BusNext]; St = BusStops23.IsValidIndex(Si) ? &BusStops23[Si] : nullptr; }
	if (!St) return;
	// (some get off (a third, at least one when it carries any), those waiting get on)
	const int32 Off = Cr.Passengers > 0 ? FMath::Max(1, Cr.Passengers / 3 + (int32)((Cr.Seed + (uint32)Cr.Passengers) % 2u)) : 0;
	const int32 Got = FMath::Min(Off, Cr.Passengers);
	Cr.Passengers -= Got;
	const int32 On = Generator->BoardBus23(Si, St->At, St->Yaw, Got, 6 - Cr.Passengers);
	Cr.Passengers += On;
	BusStops23[Si].Boarded += On; BusStops23[Si].Alighted += Got;
	Boarded23 += On; Alighted23 += Got; ++BusStops23Made;
	for (int32 K = 0; K < Cr.Riders.Num(); ++K) if (USkeletalMeshComponent* Rd = Cr.Riders[K].Get()) Rd->SetVisibility(Cr.bDriverShown && K < Cr.Passengers);
	UE_LOG(LogRDHeaven23, Log, TEXT("RDHEAVEN23 bus %d at stop %d: %d off, %d on, %d aboard"), Ci, Si, Got, On, Cr.Passengers);
}

TArray<FString> ARDSection::GetTraffic23Lines() const
{
	TArray<FString> Out;
	int32 Buses = 0, Drivers = 0; for (const FCar23& Cr : Cars23) { Buses += Cr.bBus ? 1 : 0; Drivers += Cr.Driver.IsValid() ? 1 : 0; }
	const UWorld* Wd = GetWorld(); const float Now = Wd ? Wd->GetTimeSeconds() : 0.f;
	Out.Add(FString::Printf(TEXT("traffic|%d|%d|%d|%d|%d|%d|%d|%d|%d|%d|%d|%d|%d|%.0f|%d"), Lanes23.Num(), Bays23.Num(), BusStops23.Num(), Cars23.Num(), Buses, Drivers,
		RedRuns23, StopSignStops23, StopSignRolls23, Boarded23, Alighted23, Parks23, Arrivals23, MinGap23, BusRoutes23.Num()));
	for (int32 I = 0; I < Cars23.Num(); ++I)
	{
		const FCar23& Cr = Cars23[I];
		const FLane23* Ln = Lanes23.IsValidIndex(Cr.Lane) ? &Lanes23[Cr.Lane] : nullptr;
		int32 Ph = -1;
		if (Ln && Ln->Signal >= 0 && Signals19.IsValidIndex(Ln->Signal)) Ph = Generator->SignalPhase19(Now, Signals19[Ln->Signal].Offset, Ln->bAlongX);
		const FVector Dp = Cr.Driver.IsValid() ? Cr.Driver->GetComponentLocation() : FVector::ZeroVector;
		const FVector Rt = Ln ? FVector(-Ln->Way.Y, Ln->Way.X, 0.f) : FVector::ZeroVector;
		Out.Add(FString::Printf(TEXT("car|%d|%.0f|%.0f|%.1f|%.0f|%.0f|%d|%d|%.0f|%.0f|%d|%d|%d|%d|%d|%d|%.0f|%d|%.0f|%.0f|%.0f|%d|%d|%.1f|%.0f"), I, Cr.Pos.X, Cr.Pos.Y, Cr.Yaw, Cr.Len, Cr.Wid, Cr.State, Cr.Lane,
			Cr.S, Cr.V, Cr.Goal, Cr.Driver.IsValid() ? 1 : 0, Cr.bBus ? 1 : 0, Cr.Passengers, Ph, Ln && Ln->bStopSign ? 1 : 0, Ln ? Ln->Len : 0.f, Cr.Route.Num(), Dp.X, Dp.Y, Dp.Z, Cr.GoalLane,
			(int32)Cr.Why, Cr.StillSince >= 0.f ? Now - Cr.StillSince : 0.f, Ln ? (float)FVector::DotProduct(Cr.Pos - Ln->A, Rt) : 0.f));
	}
	if (!MinGapWhat23.IsEmpty()) Out.Add(MinGapWhat23);
	for (int32 L = 0; L < Lanes23.Num(); ++L)
	{
		const FLane23& Ln = Lanes23[L];
		Out.Add(FString::Printf(TEXT("lane|%d|%d|%d|%.0f|%.0f|%.0f|%.0f|%d|%d|%d|%d"), L, Ln.Run, Ln.Dir, Ln.A.X, Ln.A.Y, Ln.B.X, Ln.B.Y, Ln.ToJ, Ln.Signal, Ln.bStopSign ? 1 : 0, Ln.bAlongX ? 1 : 0));
	}
	for (int32 K = 0; K < BusStops23.Num(); ++K)
		Out.Add(FString::Printf(TEXT("busstop|%d|%.0f|%.0f|%d|%.0f|%d|%d|%d"), K, BusStops23[K].At.X, BusStops23[K].At.Y, BusStops23[K].Lane, BusStops23[K].S, Generator->BusWaiting23(K), BusStops23[K].Boarded, BusStops23[K].Alighted));
	return Out;
}

// ------------------------------------------------------------------------------------------------ the generator: the people at the stops
int32 ARDDungeonGenerator::BusWaiting23(int32 Stop) const
{
	int32 N_ = 0;
	for (const FBusWait23& W : BusWait23) if (W.Stop == Stop && W.F.IsValid()) ++N_;
	return N_;
}

int32 ARDDungeonGenerator::BoardBus23(int32 Stop, const FVector& At, float Yaw, int32 Off, int32 Room)
{
	// (those getting off walk away as pedestrians; those waiting get on, as many as there are seats)
	ARDSection* S = GetSection(FIntPoint::ZeroValue);
	const FVector Rw = FRotator(0, Yaw, 0).Vector();
	for (int32 K = 0; K < Off && S && GetWorld(); ++K)
	{
		FActorSpawnParameters Sp; Sp.SpawnCollisionHandlingOverride = ESpawnActorCollisionHandlingMethod::AlwaysSpawn;
		const FVector P = At - Rw * 120.f + FVector(Rw.Y, -Rw.X, 0.f) * (K * 70.f - 70.f) + FVector(0, 0, 92.f);
		int32 D = -1;
		for (int32 J = 0; J < Townsfolk.Num() && D < 0; ++J) { const int32 Q = (J + K * 7 + Stop * 3 + PedsMade22) % Townsfolk.Num(); if (Townsfolk[Q].Mesh && Townsfolk[Q].Role == ERDTownRole::Townsfolk && (Townsfolk[Q].Town == TownName || Townsfolk[Q].Town.IsEmpty())) D = Q; }
		if (D < 0) break;
		ARDTownsfolk* F = GetWorld()->SpawnActor<ARDTownsfolk>(ARDTownsfolk::StaticClass(), FTransform(FRotator(0, Yaw + 180.f, 0), P), Sp);
		if (!F) continue;
		F->Init(this, S, D, P, Yaw + 180.f, 0.f, HashCombine((uint32)StartSeed, (uint32)(++PedsMade22) * 7919u));
		F->bPave22 = true; F->SetTitle(FString::Printf(TEXT("%s off the bus"), *F->Title));
		Peds22.Add(F); TownPeople.Add(F);
	}
	int32 On = 0;
	for (int32 K = BusWait23.Num() - 1; K >= 0 && On < Room; --K)
	{
		if (BusWait23[K].Stop != Stop) continue;
		if (ARDTownsfolk* F = BusWait23[K].F.Get()) { TownPeople.Remove(F); F->Destroy(); ++On; }
		BusWait23.RemoveAt(K);
	}
	return On;
}

void ARDDungeonGenerator::TickBusStops23(const FVector& Her, ARDSection* S, bool bNight)
{
	// (now and then someone comes to wait at a stop within 150 m of her, up to three a stop; none at night; they go when she is far)
	for (int32 K = BusWait23.Num() - 1; K >= 0; --K)
	{
		ARDTownsfolk* F = BusWait23[K].F.Get();
		if (!F || FVector::Dist2D(F->GetActorLocation(), Her) > 20000.f) { if (F) { TownPeople.Remove(F); F->Destroy(); } BusWait23.RemoveAt(K); }
	}
	if (bNight || !S || !GetWorld()) return;
	for (int32 Si = 0; Si < S->BusStops23.Num(); ++Si)
	{
		const ARDSection::FStop23& St = S->BusStops23[Si];
		if (FVector::Dist2D(St.At, Her) > 15000.f || BusWaiting23(Si) >= 3) continue;
		const uint32 H = HashCombine((uint32)Si, (uint32)(BusWaitMade23 * 2654435761u));
		if (H % 100u >= 18u) { ++BusWaitMade23; continue; }          // (about one in five looks a second)
		int32 D = -1;
		for (int32 J = 0; J < Townsfolk.Num() && D < 0; ++J) { const int32 Q = (J + (int32)(H >> 8)) % Townsfolk.Num(); if (Townsfolk[Q].Mesh && Townsfolk[Q].Role == ERDTownRole::Townsfolk && (Townsfolk[Q].Town == TownName || Townsfolk[Q].Town.IsEmpty())) D = Q; }
		if (D < 0) return;
		const FVector Rw = FRotator(0, St.Yaw, 0).Vector();
		const int32 N_ = BusWaiting23(Si);
		const FVector P = St.At - Rw * 140.f + FVector(Rw.Y, -Rw.X, 0.f) * (N_ * 80.f - 80.f) + FVector(0, 0, 92.f);
		FActorSpawnParameters Sp; Sp.SpawnCollisionHandlingOverride = ESpawnActorCollisionHandlingMethod::AlwaysSpawn;
		ARDTownsfolk* F = GetWorld()->SpawnActor<ARDTownsfolk>(ARDTownsfolk::StaticClass(), FTransform(FRotator(0, St.Yaw, 0), P), Sp);
		if (!F) continue;
		F->Init(this, S, D, P, St.Yaw, 0.f, HashCombine((uint32)StartSeed ^ 0xB57u, (uint32)(++BusWaitMade23) * 7919u));
		F->SetTitle(FString::Printf(TEXT("%s waiting for the bus"), *F->Title));
		FBusWait23 W; W.Stop = Si; W.F = F; BusWait23.Add(W); TownPeople.Add(F);
	}
}

TArray<FString> ARDDungeonGenerator::GetTraffic23() const
{
	const ARDSection* S = GetSection(FIntPoint::ZeroValue);
	return S ? S->GetTraffic23Lines() : TArray<FString>();
}
