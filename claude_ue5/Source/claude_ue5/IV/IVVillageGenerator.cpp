#include "IV/IVVillageGenerator.h"
#include "IV/IVSection.h"
#include "Engine/World.h"
#include "EngineUtils.h"
#include "GameFramework/Pawn.h"
#include "GameFramework/PlayerController.h"
#include "Kismet/GameplayStatics.h"
#include "Misc/DateTime.h"
#include "Components/PostProcessComponent.h"
#include "Materials/MaterialInstanceDynamic.h"

DEFINE_LOG_CATEGORY_STATIC(LogIsoVillageGen, Log, All);

static const float TwoPi = 2.f * PI;

static uint32 Mix(uint32 A, uint32 B, uint32 C = 0, uint32 D = 0)
{
	uint32 H = A * 0x9e3779b1u;
	H ^= B + 0x85ebca6bu + (H << 6) + (H >> 2);
	H ^= C + 0xc2b2ae35u + (H << 6) + (H >> 2);
	H ^= D + 0x27d4eb2fu + (H << 6) + (H >> 2);
	H ^= H >> 16; H *= 0x7feb352du; H ^= H >> 15; H *= 0x846ca68bu; H ^= H >> 16;
	return H;
}
static float Rnd(uint32 A, uint32 B, uint32 C = 0, uint32 D = 0) { return (Mix(A, B, C, D) & 0xffffff) / 16777216.f; }
static float WrapPi(float A) { A = FMath::Fmod(A + PI, TwoPi); if (A < 0.f) A += TwoPi; return A - PI; }
/** angle from A0 anticlockwise to A1, in (0, 2 pi] (lane angles are not normalised) */
static float AngleSpan(float A0, float A1) { float D = FMath::Fmod(A1 - A0, TwoPi); if (D <= 0.f) D += TwoPi; return D; }
/** smooth periodic noise in an angle, -1..1 */
static float AngNoise(uint32 Seed, float Th)
{
	return 0.5f * FMath::Sin(2.f * Th + TwoPi * Rnd(Seed, 11)) + 0.3f * FMath::Sin(3.f * Th + TwoPi * Rnd(Seed, 12)) + 0.2f * FMath::Sin(5.f * Th + TwoPi * Rnd(Seed, 13));
}

/** do two building sites (boxes in their own frames) overlap; A is grown by Margin */
static bool LotsOverlap(const FIVLot& A, const FIVLot& B, float M, float Margin)
{
	auto Axes = [](const FIVLot& L, FVector2D& Fx, FVector2D& Fy) { const float Y = FMath::DegreesToRadians(L.Yaw); Fx = FVector2D(FMath::Cos(Y), FMath::Sin(Y)); Fy = FVector2D(-Fx.Y, Fx.X); };
	FVector2D Ax, Ay, Bx, By; Axes(A, Ax, Ay); Axes(B, Bx, By);
	const FVector2D Ha(A.CellsX * M * 0.5f + Margin, A.CellsY * M * 0.5f + Margin), Hb(B.CellsX * M * 0.5f, B.CellsY * M * 0.5f);
	const FVector2D D = B.Center - A.Center;
	for (const FVector2D& N : { Ax, Ay, Bx, By })
	{
		const float Ra = Ha.X * FMath::Abs(FVector2D::DotProduct(Ax, N)) + Ha.Y * FMath::Abs(FVector2D::DotProduct(Ay, N));
		const float Rb = Hb.X * FMath::Abs(FVector2D::DotProduct(Bx, N)) + Hb.Y * FMath::Abs(FVector2D::DotProduct(By, N));
		if (FMath::Abs(FVector2D::DotProduct(D, N)) > Ra + Rb) return false;
	}
	return true;
}

AIVVillageGenerator::AIVVillageGenerator()
{
	PrimaryActorTick.bCanEverTick = true;
	PrimaryActorTick.TickInterval = 0.f;
	RootComponent = CreateDefaultSubobject<USceneComponent>(TEXT("Root"));
	RevealPost = CreateDefaultSubobject<UPostProcessComponent>(TEXT("RevealPost"));
	RevealPost->SetupAttachment(RootComponent);
	RevealPost->bUnbound = true;
	RevealPost->Priority = 10.f;
}

FString AIVVillageGenerator::KindName(EIVBuildingKind K)
{
	switch (K)
	{
	case EIVBuildingKind::Cottage: return TEXT("Cottage");
	case EIVBuildingKind::Farmhouse: return TEXT("Farmhouse");
	case EIVBuildingKind::Tavern: return TEXT("Tavern");
	case EIVBuildingKind::Smithy: return TEXT("Smithy");
	case EIVBuildingKind::Bakery: return TEXT("Bakery");
	case EIVBuildingKind::Store: return TEXT("General store");
	case EIVBuildingKind::Workshop: return TEXT("Carpenter");
	case EIVBuildingKind::Barn: return TEXT("Barn");
	case EIVBuildingKind::Storehouse: return TEXT("Storehouse");
	case EIVBuildingKind::Church: return TEXT("Church");
	case EIVBuildingKind::Manor: return TEXT("Elder's hall");
	default: return TEXT("House");
	}
}

AActor* AIVVillageGenerator::GetTrackedActor() const
{
	return TrackedActor ? TrackedActor.Get() : UGameplayStatics::GetPlayerPawn(this, 0);
}

// ------------------------------------------------------------------------------------------------ sections
FIntPoint AIVVillageGenerator::WorldToSection(FVector L) const
{
	return FIntPoint(FMath::FloorToInt(L.X / SectionSize + 0.5f), FMath::FloorToInt(L.Y / SectionSize + 0.5f));
}

FVector2D AIVVillageGenerator::SectionMin(FIntPoint S) const
{
	return FVector2D((S.X - 0.5f) * SectionSize, (S.Y - 0.5f) * SectionSize);
}

int32 AIVVillageGenerator::SectionSeed(FIntPoint S) const
{
	const uint32 Base = IsStartSection(S) ? (uint32)StartSeed : (uint32)SessionSeed;
	return (int32)(Mix(Base, (uint32)(S.X * 7919 + 3), (uint32)(S.Y * 104729 + 17)) & 0x7fffffff);
}

bool AIVVillageGenerator::IsSectionGenerated(FIntPoint S) const { return Sections.Contains(S) && Sections[S] != nullptr; }
AIVSection* AIVVillageGenerator::GetSection(FIntPoint S) const { const TObjectPtr<AIVSection>* P = Sections.Find(S); return P ? P->Get() : nullptr; }
TArray<FIntPoint> AIVVillageGenerator::GetSectionCoords() const { TArray<FIntPoint> Out; Sections.GetKeys(Out); return Out; }

// ------------------------------------------------------------------------------------------------ plan
float AIVVillageGenerator::RingBase(int32 K) const
{
	if (K <= 0) return SquareRadius;
	// (ring 1 keeps its distance from the square: two rows of houses fit between them)
	const float Off = K == 1 ? 0.f : (Rnd(PlanSeed(K), 21, K) - 0.5f) * 500.f;
	return FirstRingRadius + (K - 1) * RingSpacing + Off;
}

float AIVVillageGenerator::RingRadius(int32 K, float Th) const
{
	const uint32 S = Mix(PlanSeed(K), 22, K);
	if (K <= 0) return SquareRadius + 200.f * AngNoise(S, Th) + 260.f * FMath::Cos(2.f * (Th - TwoPi * Rnd(S, 23)));
	const float Amp = K == 1 ? 300.f : FMath::Min(360.f + 70.f * K, 700.f);
	return RingBase(K) + Amp * AngNoise(S, Th);
}

int32 AIVVillageGenerator::BandAt(float R, float Th) const
{
	if (R < RingRadius(0, Th)) return -1;
	int32 B = FMath::Max(0, FMath::FloorToInt((R - FirstRingRadius) / RingSpacing) + 1);
	while (R >= RingRadius(B + 1, Th)) ++B;
	while (B > 0 && R < RingRadius(B, Th)) --B;
	return B;
}

float AIVVillageGenerator::Density(float R) const
{
	// shoulder to shoulder in the core, thinning into farmsteads; never empty (hamlet clusters far out)
	const float D = 1.f - FMath::Clamp((R - 8000.f) / 9000.f, 0.f, 1.f) * 0.4f - FMath::Clamp((R - 17000.f) / 13000.f, 0.f, 1.f) * 0.15f;
	const float Hamlet = 0.22f * FMath::Max(0.f, FMath::Sin(R / 9500.f));
	return FMath::Clamp(D + (R > 30000.f ? Hamlet : 0.f), 0.42f, 1.f);
}

/** main road m: its angle winds with the distance from the centre (continuous across the bands) */
float AIVVillageGenerator::MainAngle(int32 M, float R) const
{
	const uint32 S = Mix(StartSeed, 31, M);
	const float Base = TwoPi * (M + 0.5f * (Rnd(S, 1) - 0.5f)) / 3.f + TwoPi * Rnd(StartSeed, 32);
	return Base + 0.13f * FMath::Sin(R / 8200.f + TwoPi * Rnd(S, 2)) + 0.06f * FMath::Sin(R / 3100.f + TwoPi * Rnd(S, 3));
}

const AIVVillageGenerator::FBandInfo& AIVVillageGenerator::Band(int32 B) const
{
	if (CacheSessionSeed != SessionSeed) { BandCache.Reset(); LotCache.Reset(); CacheSessionSeed = SessionSeed; }
	if (const FBandInfo* F = BandCache.Find(B)) return *F;
	FBandInfo I;
	const uint32 S = Mix(PlanSeed(B + 1), 41, B);
	const float Rmid = 0.5f * (RingBase(B) + RingBase(B + 1));
	const int32 Want = B == 0 ? 5 : FMath::Max(6, FMath::RoundToInt(TwoPi * Rmid / SpokeSpacing));
	// the three main roads first, in angular order; the lanes share out the gaps between them (so the lanes of a band
	// are always in angular order: a block is the stretch between one lane and the next)
	struct FM { float A; int32 M; };
	FM Ms[3];
	for (int32 M = 0; M < 3; ++M) { float A = FMath::Fmod(MainAngle(M, Rmid), TwoPi); if (A < 0.f) A += TwoPi; Ms[M] = { A, M }; }
	if (Ms[0].A > Ms[1].A) Swap(Ms[0], Ms[1]);
	if (Ms[1].A > Ms[2].A) Swap(Ms[1], Ms[2]);
	if (Ms[0].A > Ms[1].A) Swap(Ms[0], Ms[1]);
	int32 Seq = 0;
	for (int32 G = 0; G < 3; ++G)
	{
		const float A0 = Ms[G].A; float A1 = Ms[(G + 1) % 3].A; if (A1 <= A0) A1 += TwoPi;
		const float Gap = A1 - A0;
		const int32 Nl = FMath::Max(0, FMath::RoundToInt(Gap / (TwoPi / Want)) - 1);
		I.Base.Add(A0); I.Bulge.Add(0.f); I.Main.Add((int8)Ms[G].M);
		for (int32 K = 1; K <= Nl; ++K, ++Seq)
		{
			I.Base.Add(A0 + Gap * (K + (Rnd(S, 2, Seq) - 0.5f) * 0.36f) / (Nl + 1));
			I.Bulge.Add((Rnd(S, 3, Seq) - 0.5f) * 2.f * 520.f / Rmid);
			I.Main.Add(-1);
		}
	}
	I.N = I.Base.Num();
	return BandCache.Add(B, I);
}

int32 AIVVillageGenerator::SpokeCount(int32 B) const { return Band(FMath::Max(B, 0)).N; }
bool AIVVillageGenerator::IsMainSpoke(int32 B, int32 Index) const { const FBandInfo& I = Band(FMath::Max(B, 0)); return I.Main[((Index % I.N) + I.N) % I.N] >= 0; }

float AIVVillageGenerator::SpokeAngle(int32 B, int32 Index, float T) const
{
	const FBandInfo& I = Band(FMath::Max(B, 0));
	const int32 K = ((Index % I.N) + I.N) % I.N;
	if (I.Main[K] >= 0)
	{
		float Th = MainAngle(I.Main[K], FMath::Lerp(RingBase(B), RingBase(B + 1), T));
		for (int32 It = 0; It < 2; ++It) Th = MainAngle(I.Main[K], FMath::Lerp(RingRadius(B, Th), RingRadius(B + 1, Th), T));
		return Th;
	}
	return I.Base[K] + I.Bulge[K] * FMath::Sin(PI * T);
}

FVector2D AIVVillageGenerator::SpokePoint(int32 B, int32 Index, float T) const
{
	const float Th = SpokeAngle(B, Index, T);
	const float R = FMath::Lerp(RingRadius(B, Th), RingRadius(B + 1, Th), T);
	return FVector2D(R * FMath::Cos(Th), R * FMath::Sin(Th));
}

float AIVVillageGenerator::RoadDistance(FVector2D P, int32& Type) const
{
	const float R = P.Size(), Th = FMath::Atan2(P.Y, P.X);
	const float R0 = RingRadius(0, Th);
	if (R < R0) { Type = 3; return R - R0; }
	const int32 B = BandAt(R, Th);
	const float Ra = RingRadius(B, Th), Rb = RingRadius(B + 1, Th);
	float Best = 1e9f; Type = 2;
	// the rings on both sides (ring 0 is the edge of the square)
	{ const float D = (R - Ra) - RingHalf(B); if (D < Best) { Best = D; Type = B == 0 ? 3 : 2; } }
	{ const float D = (Rb - R) - RingHalf(B + 1); if (D < Best) { Best = D; Type = 2; } }
	const FBandInfo& I = Band(B);
	const float T = FMath::Clamp((R - Ra) / FMath::Max(Rb - Ra, 1.f), 0.f, 1.f);
	for (int32 K = 0; K < I.N; ++K)
	{
		const float A = I.Main[K] >= 0 ? MainAngle(I.Main[K], R) : I.Base[K] + I.Bulge[K] * FMath::Sin(PI * T);
		const float D = FMath::Abs(WrapPi(Th - A)) * R - (I.Main[K] >= 0 ? MainRoadHalfWidth : LaneHalfWidth);
		if (D < Best) { Best = D; Type = I.Main[K] >= 0 ? 1 : 0; }
	}
	return Best;
}

int32 AIVVillageGenerator::ChurchSector() const
{
	// the widest block on the square
	const FBandInfo& I = Band(0);
	int32 Best = 0; float BestW = -1.f;
	for (int32 K = 0; K < I.N; ++K)
	{
		const float W = AngleSpan(SpokeAngle(0, K, 0.f), SpokeAngle(0, K + 1, 0.f));
		if (W > BestW) { BestW = W; Best = K; }
	}
	return Best;
}

const TArray<FIVLot>& AIVVillageGenerator::GetLots(int32 B) const
{
	Band(B);      // (resets the caches when the session seed changed)
	if (const TArray<FIVLot>* L = LotCache.Find(B)) return *L;
	TArray<FIVLot> Out;
	BuildLots(B, Out);
	return LotCache.Add(B, MoveTemp(Out));
}

void AIVVillageGenerator::BuildLots(int32 B, TArray<FIVLot>& Out) const
{
	const FBandInfo& I = Band(B);
	const uint32 S = Mix(PlanSeed(B + 1), 51, B);
	const float M = Module;
	const int32 Church = B == 0 ? ChurchSector() : -1;
	// landmarks on the square, handed out to the square row in walking order: (kind, depth cells, width cells)
	struct FMark { EIVBuildingKind K; int32 X, Y; };
	const FMark Marks[] = { { EIVBuildingKind::Tavern, 2, 4 }, { EIVBuildingKind::Bakery, 2, 2 }, { EIVBuildingKind::Smithy, 2, 3 }, { EIVBuildingKind::Store, 2, 3 },
		{ EIVBuildingKind::Manor, 2, 4 }, { EIVBuildingKind::Workshop, 2, 2 }, { EIVBuildingKind::Store, 2, 3 }, { EIVBuildingKind::Cottage, 2, 3 } };
	int32 NextMark = 0;
	auto Normal = [this](int32 Ring, float Th)
	{
		// outward normal of the ring curve r = R(theta)
		const float E = 0.004f;
		const float R = RingRadius(Ring, Th), dR = (RingRadius(Ring, Th + E) - RingRadius(Ring, Th - E)) / (2.f * E);
		const FVector2D Rh(FMath::Cos(Th), FMath::Sin(Th)), Thh(-FMath::Sin(Th), FMath::Cos(Th));
		return (Rh - Thh * (dR / FMath::Max(R, 1.f))).GetSafeNormal();
	};
	// never on a road, never into a neighbour (the rows of a shallow block can meet back to back)
	auto Accept = [this, &Out, M](const FIVLot& L, const FVector2D& Front, float W, float D)
	{
		const FVector2D Fy(-Front.Y, Front.X);
		for (int32 Cx = -1; Cx <= 1; ++Cx)
			for (int32 Cy = -1; Cy <= 1; ++Cy)
			{
				int32 Ty;
				if (RoadDistance(L.Center + Front * (Cx * D * 0.5f) + Fy * (Cy * W * 0.5f), Ty) < 70.f) return false;
			}
		for (int32 K = 0; K < Out.Num(); ++K) if (LotsOverlap(L, Out[K], M, 140.f)) return false;
		Out.Add(L);
		return true;
	};
	for (int32 Sec = 0; Sec < I.N; ++Sec)
	{
		if (Sec == Church)
		{
			// the church stands alone in its block: door on the square, nave running back to the ring street
			const float A0 = SpokeAngle(0, Sec, 0.3f);
			const float A1 = A0 + AngleSpan(A0, SpokeAngle(0, Sec + 1, 0.3f));
			const float Th = 0.5f * (A0 + A1);
			FIVLot L; L.Band = 0; L.Sector = Sec; L.Row = 0; L.Index = 0; L.FixedKind = (int32)EIVBuildingKind::Church;
			L.CellsY = 2;
			const float Front = RingRadius(0, Th) + 420.f, Back = RingRadius(1, Th) - RingHalf(1) - 380.f;
			L.CellsX = FMath::Clamp(FMath::FloorToInt((Back - Front) / M), 4, 6);
			const FVector2D Nm = Normal(0, Th);
			const FVector2D P0 = FVector2D(FMath::Cos(Th), FMath::Sin(Th)) * Front;
			L.Center = P0 + Nm * (L.CellsX * M * 0.5f);
			L.Yaw = FMath::RadiansToDegrees(FMath::Atan2(-Nm.Y, -Nm.X));
			L.Radius = L.Center.Size(); L.Id = Mix(S, 61, Sec, 0);
			Out.Add(L);
			continue;
		}
		for (int32 Row = 0; Row < 2; ++Row)
		{
			const int32 Ring = B + Row;                          // the ring this row fronts
			const float Hw = RingHalf(Ring);
			const float TRow = Row == 0 ? 0.12f : 0.88f;
			const float A0 = SpokeAngle(B, Sec, TRow);
			const float A1 = A0 + AngleSpan(A0, SpokeAngle(B, Sec + 1, TRow));
			const float ThMid = 0.5f * (A0 + A1);
			const float BandDepth = RingRadius(B + 1, ThMid) - RingRadius(B, ThMid);
			// arc length is measured on the tighter side of the row (fronts converge outside a ring, backs inside it)
			const float Rho = Row == 0 ? RingRadius(Ring, ThMid) + Hw + 150.f : RingRadius(Ring, ThMid) - Hw - 150.f - 2.f * M;
			const float Margin0 = SpokeHalf(B, Sec) + 260.f, Margin1 = SpokeHalf(B, Sec + 1) + 260.f;
			const float Len = (A1 - A0) * Rho - Margin0 - Margin1;
			if (Len < 2.f * M) continue;
			const uint32 RS = Mix(S, 62, Sec, Row);
			struct FTmp { float S0; FIVLot L; float Setback; };
			TArray<FTmp> Row_;
			float Sx = 0.f;
			for (int32 K = 0; K < 40; ++K)
			{
				int32 Cx = 2, Cy = 2; int32 Fixed = -1;
				const float U = Rnd(RS, 1, K);
				if (B == 0 && Row == 0)
				{
					const FMark& Mk = Marks[NextMark % UE_ARRAY_COUNT(Marks)];
					Cx = Mk.X; Cy = Mk.Y; Fixed = (int32)Mk.K;
					if (Sx + Cy * M > Len) { Cy = FMath::FloorToInt((Len - Sx) / M); if (Cy < 2) break; if (Cy == 2 && Mk.K == EIVBuildingKind::Tavern) Cy = 2; }
					++NextMark;
				}
				else
				{
					// (depth, width): eaves to the street mostly, some gables to the street, a few deep houses
					if (U < 0.16f) { Cx = 2; Cy = 2; }
					else if (U < 0.54f) { Cx = 2; Cy = 3; }
					else if (U < 0.72f) { Cx = 2; Cy = 4; }
					else if (U < 0.86f) { Cx = 3; Cy = 2; }
					else { Cx = 4; Cy = 3; }
					const float Avail = BandDepth * 0.5f - Hw - 420.f;
					if (Cx * M > Avail) Cx = 2;
					if (Cx * M > Avail) break;
					while (Cy > 2 && Sx + Cy * M > Len) --Cy;
					if (Sx + Cy * M > Len) break;
				}
				FTmp T; T.S0 = Sx; T.L.CellsX = Cx; T.L.CellsY = Cy; T.L.FixedKind = Fixed; T.L.Band = B; T.L.Sector = Sec; T.L.Row = Row; T.L.Index = K;
				T.Setback = (B == 0 && Row == 0) ? 260.f + 200.f * Rnd(RS, 2, K) : 140.f + 240.f * Rnd(RS, 2, K);
				Row_.Add(T);
				const float Dn = Density(RingBase(Ring));
				Sx += Cy * M + 220.f + 420.f * Rnd(RS, 3, K) + (1.f - Dn) * 1100.f * Rnd(RS, 4, K);
			}
			if (Row_.Num() == 0) continue;
			const FTmp& Last = Row_.Last();
			const float Used = Last.S0 + Last.L.CellsY * M;
			const float Shift = Margin0 + FMath::Max(0.f, Len - Used) * (0.3f + 0.4f * Rnd(RS, 5));
			for (FTmp& T : Row_)
			{
				const float W = T.L.CellsY * M, D = T.L.CellsX * M;
				const float Th = A0 + (Shift + T.S0 + W * 0.5f) / Rho;
				const FVector2D Nm = Normal(Ring, Th);
				const FVector2D OnRing = FVector2D(FMath::Cos(Th), FMath::Sin(Th)) * RingRadius(Ring, Th);
				const float Off = Hw + T.Setback + D * 0.5f;
				T.L.Center = OnRing + Nm * (Row == 0 ? Off : -Off);
				const FVector2D Front = Row == 0 ? -Nm : Nm;
				T.L.Yaw = FMath::RadiansToDegrees(FMath::Atan2(Front.Y, Front.X));
				T.L.Radius = T.L.Center.Size();
				T.L.Id = Mix(S, 63 + Row, Sec, T.L.Index);
				Accept(T.L, Front, W, D);
			}
		}
	}
	// houses along the three main roads as well, between the ring rows, facing the road
	for (int32 K = 0; K < I.N; ++K)
	{
		if (I.Main[K] < 0) continue;
		const float Th = SpokeAngle(B, K, 0.5f);
		const float Depth = RingRadius(B + 1, Th) - RingRadius(B, Th);
		const float Lead = 1450.f;                             // the ring rows and their yards
		const float Len = Depth - 2.f * Lead;
		if (Len < 2.f * M) continue;
		for (int32 Sd = -1; Sd <= 1; Sd += 2)
		{
			const uint32 RS = Mix(S, 66, K, Sd + 1);
			float Sx = Rnd(RS, 9) * 200.f;
			for (int32 J = 0; J < 6; ++J)
			{
				const float U = Rnd(RS, 1, J);
				int32 Cy = U < 0.25f ? 2 : U < 0.8f ? 3 : 4;
				while (Cy > 2 && Sx + Cy * M > Len) --Cy;
				if (Sx + Cy * M > Len) break;
				const float W = Cy * M, D = 2.f * M;
				const float T = (Lead + Sx + W * 0.5f) / Depth;
				const FVector2D P = SpokePoint(B, K, T), Tg = (SpokePoint(B, K, T + 0.02f) - SpokePoint(B, K, T - 0.02f)).GetSafeNormal(), Nm(-Tg.Y, Tg.X);
				FIVLot L; L.Band = B; L.Sector = K; L.Row = Sd < 0 ? 2 : 3; L.Index = J; L.CellsX = 2; L.CellsY = Cy;
				L.Center = P + Nm * ((float)Sd * (MainRoadHalfWidth + 150.f + 220.f * Rnd(RS, 2, J) + D * 0.5f));
				const FVector2D Front = Nm * (float)-Sd;
				L.Yaw = FMath::RadiansToDegrees(FMath::Atan2(Front.Y, Front.X));
				L.Radius = L.Center.Size(); L.Id = Mix(S, Sd < 0 ? 67 : 68, K, J);
				Accept(L, Front, W, D);
				Sx += W + 240.f + 450.f * Rnd(RS, 3, J) + (1.f - Density(L.Radius)) * 900.f * Rnd(RS, 4, J);
			}
		}
	}
}

// ------------------------------------------------------------------------------------------------ build
AIVSection* AIVVillageGenerator::SpawnSection(FIntPoint S, bool bEditorBuild, bool bReveal)
{
	UWorld* W = GetWorld();
	FActorSpawnParameters P; P.SpawnCollisionHandlingOverride = ESpawnActorCollisionHandlingMethod::AlwaysSpawn;
	const FVector2D Min = SectionMin(S);
	AIVSection* Sec = W->SpawnActor<AIVSection>(AIVSection::StaticClass(), FTransform(FVector(Min.X, Min.Y, 0.f)), P);
	if (!Sec) return nullptr;
#if WITH_EDITOR
	if (bEditorBuild) { Sec->SetActorLabel(FString::Printf(TEXT("IV_Section_%d_%d"), S.X, S.Y)); Sec->SetFolderPath(TEXT("IsoVillage/Sections")); }
#endif
	Sections.Add(S, Sec);
	if (bReveal && W->IsGameWorld() && !bEditorBuild)
	{
		// runtime: planned now, built over the next frames (Tick); the reveal starts when it is complete
		Sec->BeginGenerate(this, S, SectionSeed(S), false);
		Building = Sec;
	}
	else Sec->Generate(this, S, SectionSeed(S), bEditorBuild);
	++SectionsGenerated;
	return Sec;
}

void AIVVillageGenerator::StartReveal(AIVSection* Sec)
{
	UWorld* W = GetWorld();
	const float Now = W->GetTimeSeconds();
	const FVector2D Min = Sec->GetSectionMin(), Max = Min + FVector2D(SectionSize);
	const AActor* Who = GetTrackedActor();
	const FVector L = Who ? Who->GetActorLocation() : FVector((Min + Max) * 0.5, 0.0);
	const FVector2D O(FMath::Clamp((float)L.X, (float)Min.X, (float)Max.X), FMath::Clamp((float)L.Y, (float)Min.Y, (float)Max.Y));
	if (bRevealEffect)
	{
		if (RevealMID)
		{
			const int32 Slot = NextRevealSlot++ % RevealSlots;
			RevealMID->SetVectorParameterValue(*FString::Printf(TEXT("Rect%d"), Slot), FLinearColor(Min.X, Min.Y, Max.X, Max.Y));
			RevealMID->SetVectorParameterValue(*FString::Printf(TEXT("Info%d"), Slot), FLinearColor(O.X, O.Y, Now, 1.f));
		}
		if (RevealCurtainMaterial) Sec->ShowCurtain(RevealCurtainMaterial, Now, RevealCurtainHeight, RevealDuration + 0.5f);
	}
	LastRevealTime = Now; LastRevealSection = Sec->Coord;
	if (FIVSectionMap* M = MapData.Find(Sec->Coord)) M->GeneratedTime = Now;
	UE_LOG(LogIsoVillageGen, Log, TEXT("IVGEN reveal (%d,%d) t=%.3f from (%.0f,%.0f) tracked (%.0f,%.0f): %d buildings, %d doors, %d containers, %d instances, %d lights, %.0f ms"),
		Sec->Coord.X, Sec->Coord.Y, Now, O.X, O.Y, L.X, L.Y, Sec->GetNumBuildings(), Sec->GetNumDoors(), Sec->GetNumContainers(), Sec->NumInstances, Sec->NumLights, Sec->GenerateMs);
}

void AIVVillageGenerator::ClearAll()
{
	UWorld* W = GetWorld();
	for (auto& KV : Sections) if (KV.Value) KV.Value->Destroy();
	Sections.Reset();
	for (TActorIterator<AIVSection> It(W); It; ++It) It->Destroy();
	Queue.Reset(); MapData.Reset();
	Building = nullptr; InsideBuilding = -1;
	SectionsGenerated = 0;
}

void AIVVillageGenerator::BuildStartSection()
{
	ClearAll();
	BandCache.Reset(); LotCache.Reset();
	SpawnSection(FIntPoint::ZeroValue, !GetWorld()->IsGameWorld());
	MapData.Reset();      // map data is play state (rebuilt by ActivateForPlay)
	Modify();
	UE_LOG(LogIsoVillageGen, Log, TEXT("IVGEN start section built"));
}

bool AIVVillageGenerator::GenerateSectionNow(FIntPoint S)
{
	if (IsSectionGenerated(S)) return false;
	AIVSection* Sec = SpawnSection(S, false, true);
	if (Sec && Building == Sec) { while (!Sec->ContinueGenerate(1e9)) {} Building = nullptr; StartReveal(Sec); }
	return Sec != nullptr;
}

void AIVVillageGenerator::Enqueue(FIntPoint S)
{
	if (!IsSectionGenerated(S) && !Queue.Contains(S)) Queue.Add(S);
}

void AIVVillageGenerator::GetVillageStats(int32& Buildings, int32& Visited, int32& NumSections) const
{
	Buildings = Visited = 0; NumSections = MapData.Num();
	for (const auto& KV : MapData) for (const FIVMapBuilding& B : KV.Value.Buildings) { ++Buildings; if (B.bVisited) ++Visited; }
}

// ------------------------------------------------------------------------------------------------ interaction
FString AIVVillageGenerator::InteractNearest(FVector From, float MaxDistance)
{
	AIVSection* Best = nullptr; bool bBestDoor = false; int32 BestI = -1; float BestD = MaxDistance;
	const FIntPoint Here = WorldToSection(From);
	for (int32 Dx = -1; Dx <= 1; ++Dx)
		for (int32 Dy = -1; Dy <= 1; ++Dy)
			if (AIVSection* S = GetSection(Here + FIntPoint(Dx, Dy)))
			{
				bool bDoor; int32 I;
				const float D = S->FindNearestInteractive(From, BestD, bDoor, I);
				if (I >= 0 && D < BestD) { BestD = D; Best = S; bBestDoor = bDoor; BestI = I; }
			}
	if (!Best) return FString();
	if (bBestDoor) { Best->ToggleDoor(BestI, From); return Best->GetDoorKind(BestI); }
	Best->ToggleContainer(BestI);
	return Best->GetContainerKind(BestI);
}

FString AIVVillageGenerator::DescribeNearest(FVector From, float MaxDistance) const
{
	const AIVSection* Best = nullptr; bool bBestDoor = false; int32 BestI = -1; float BestD = MaxDistance;
	const FIntPoint Here = WorldToSection(From);
	for (int32 Dx = -1; Dx <= 1; ++Dx)
		for (int32 Dy = -1; Dy <= 1; ++Dy)
			if (const AIVSection* S = GetSection(Here + FIntPoint(Dx, Dy)))
			{
				bool bDoor; int32 I;
				const float D = S->FindNearestInteractive(From, BestD, bDoor, I);
				if (I >= 0 && D < BestD) { BestD = D; Best = S; bBestDoor = bDoor; BestI = I; }
			}
	if (!Best) return FString();
	const FString What = bBestDoor ? Best->GetDoorKind(BestI) : Best->GetContainerKind(BestI);
	return FString::Printf(TEXT("%s %s"), Best->IsTargetOpen(bBestDoor, BestI) ? TEXT("close") : TEXT("open"), *What);
}

// ------------------------------------------------------------------------------------------------ cutaway
void AIVVillageGenerator::UpdateCutaway(const FVector& L)
{
	// which building is she in (its own section, or a neighbour's when she stands near a border)
	FIntPoint NewS = FIntPoint::ZeroValue; int32 NewB = -1;
	if (bCutaway)
	{
		const FIntPoint Here = WorldToSection(L);
		for (int32 Dx = -1; Dx <= 1 && NewB < 0; ++Dx)
			for (int32 Dy = -1; Dy <= 1 && NewB < 0; ++Dy)
				if (AIVSection* S = GetSection(Here + FIntPoint(Dx, Dy)))
				{
					// (hysteresis: once inside she stays "inside" until she is well out of the doorway)
					const bool bSame = InsideBuilding >= 0 && S->Coord == InsideSection;
					const int32 I = S->BuildingAt(L, bSame ? InsideBuilding : -1);
					if (I >= 0) { NewS = S->Coord; NewB = I; }
				}
	}
	if (NewB == InsideBuilding && (NewB < 0 || NewS == InsideSection)) return;
	// restore everything, then cut away the new building and whatever hides its floor from the camera
	for (auto& KV : Sections) if (KV.Value) KV.Value->ClearCutaway();
	InsideSection = NewS; InsideBuilding = NewB;
	if (NewB < 0) return;
	AIVSection* Sec = GetSection(NewS);
	if (!Sec) { InsideBuilding = -1; return; }
	Sec->EnterBuilding(NewB);
	TArray<FVector> Floor;
	Sec->GetBuildingFloorSamples(NewB, Floor);
	const FVector U = ToCamera();
	for (int32 Dx = -1; Dx <= 1; ++Dx)
		for (int32 Dy = -1; Dy <= 1; ++Dy)
			if (AIVSection* S = GetSection(NewS + FIntPoint(Dx, Dy)))
				S->CutOccluders(Floor, U, S == Sec ? NewB : -1);
}

// ------------------------------------------------------------------------------------------------ nav
bool AIVVillageGenerator::NavBlocked(const FVector2D& P) const
{
	// a section's grid reaches NavMargin past its border (houses standing across it): near a border the neighbours
	// are asked too. Free = generated ground (or a house floor reaching out over ground not generated yet).
	const FIntPoint S0 = WorldToSection(FVector(P, 0.f));
	const FVector2D Mn = SectionMin(S0);
	const float Mg = AIVSection::NavMargin;
	const int32 X0 = P.X - Mn.X < Mg ? -1 : 0, X1 = Mn.X + SectionSize - P.X < Mg ? 1 : 0;
	const int32 Y0 = P.Y - Mn.Y < Mg ? -1 : 0, Y1 = Mn.Y + SectionSize - P.Y < Mg ? 1 : 0;
	bool bFloor = false;
	for (int32 Dx = X0; Dx <= X1; ++Dx)
		for (int32 Dy = Y0; Dy <= Y1; ++Dy)
			if (const AIVSection* S = GetSection(S0 + FIntPoint(Dx, Dy)))
			{
				const int32 V = S->NavAt(P);
				if (V == 1) return true;
				if (V == 2) bFloor = true;
			}
	return !(bFloor || IsSectionGenerated(S0));
}

bool AIVVillageGenerator::IsWalkable(FVector L) const
{
	return !NavBlocked(FVector2D(L.X, L.Y));
}

TArray<FVector> AIVVillageGenerator::FindPath(FVector From, FVector To, int32 MaxCells) const
{
	// A* over the sections' 50 cm grids (global cell coordinates), 8-connected; doorways are portal edges between the
	// cell outside a door and the cell inside it
	TArray<FVector> Out;
	const float G = AIVSection::NavCell;
	auto Cell = [G](const FVector2D& P) { return FIntPoint(FMath::FloorToInt(P.X / G), FMath::FloorToInt(P.Y / G)); };
	auto Center = [G](const FIntPoint& C) { return FVector2D((C.X + 0.5f) * G, (C.Y + 0.5f) * G); };
	TMap<FIntPoint, bool> Known; Known.Reserve(8192);
	auto Blocked = [this, &Center, &Known](const FIntPoint& C)
	{
		if (const bool* K = Known.Find(C)) return *K;
		return Known.Add(C, NavBlocked(Center(C)));
	};
	auto Snap = [&](FIntPoint& C)
	{
		if (!Blocked(C)) return true;
		for (int32 D = 1; D <= 4; ++D)
			for (int32 Dx = -D; Dx <= D; ++Dx)
				for (int32 Dy = -D; Dy <= D; ++Dy)
					if (FMath::Max(FMath::Abs(Dx), FMath::Abs(Dy)) == D && !Blocked(C + FIntPoint(Dx, Dy))) { C += FIntPoint(Dx, Dy); return true; }
		return false;
	};
	FIntPoint A = Cell(FVector2D(From.X, From.Y)), B = Cell(FVector2D(To.X, To.Y));
	if (!Snap(A) || !Snap(B)) return Out;
	TMultiMap<FIntPoint, FIntPoint> Portals;
	for (const auto& KV : Sections) if (KV.Value) KV.Value->AppendPortals(Portals);
	struct FNode { float F, Gc; FIntPoint C; };
	auto Pred = [](const FNode& X, const FNode& Y) { return X.F < Y.F; };
	auto Heur = [&B](const FIntPoint& C) { const int32 Dx = FMath::Abs(C.X - B.X), Dy = FMath::Abs(C.Y - B.Y); return (float)FMath::Max(Dx, Dy) + 0.4142f * FMath::Min(Dx, Dy); };
	TArray<FNode> Open; Open.Reserve(4096);
	TMap<FIntPoint, FIntPoint> Prev; Prev.Reserve(8192);
	TMap<FIntPoint, float> Best; Best.Reserve(8192);
	Open.HeapPush(FNode{ Heur(A), 0.f, A }, Pred); Prev.Add(A, A); Best.Add(A, 0.f);
	static const FIntPoint D8[8] = { FIntPoint(1, 0), FIntPoint(-1, 0), FIntPoint(0, 1), FIntPoint(0, -1), FIntPoint(1, 1), FIntPoint(1, -1), FIntPoint(-1, 1), FIntPoint(-1, -1) };
	bool bFound = false;
	for (int32 Expanded = 0; Open.Num() > 0 && Expanded < MaxCells; )
	{
		FNode N; Open.HeapPop(N, Pred, EAllowShrinking::No);
		if (N.Gc > Best.FindRef(N.C) + 1e-3f) continue;      // (a cheaper way to it was found meanwhile)
		if (N.C == B) { bFound = true; break; }
		++Expanded;
		auto Relax = [&](const FIntPoint& M, float Cost)
		{
			const float Gn = N.Gc + Cost;
			if (const float* Old = Best.Find(M)) if (*Old <= Gn) return;
			Best.Add(M, Gn); Prev.Add(M, N.C);
			Open.HeapPush(FNode{ Gn + Heur(M), Gn, M }, Pred);
		};
		for (int32 K = 0; K < 8; ++K)
		{
			const FIntPoint M = N.C + D8[K];
			if (Blocked(M)) continue;
			// diagonals never cut a corner
			if (K >= 4 && (Blocked(N.C + FIntPoint(D8[K].X, 0)) || Blocked(N.C + FIntPoint(0, D8[K].Y)))) continue;
			Relax(M, K < 4 ? 1.f : 1.4142f);
		}
		TArray<FIntPoint> Ps; Portals.MultiFind(N.C, Ps);
		for (const FIntPoint& M : Ps) Relax(M, 6.f);       // (a doorway: a little dearer than the 2.2 m it spans)
	}
	if (!bFound) return Out;
	TArray<FIntPoint> Chain;
	for (FIntPoint C = B; ; C = Prev[C]) { Chain.Add(C); if (C == A) break; }
	Algo::Reverse(Chain);
	// keep the turning points (and both ends of every portal jump)
	for (int32 K = 0; K < Chain.Num(); ++K)
	{
		const bool bEnd = K == 0 || K == Chain.Num() - 1;
		bool bKeep = bEnd;
		if (!bEnd)
		{
			const FIntPoint D0 = Chain[K] - Chain[K - 1], D1 = Chain[K + 1] - Chain[K];
			bKeep = D0 != D1 || FMath::Abs(D0.X) > 1 || FMath::Abs(D0.Y) > 1 || FMath::Abs(D1.X) > 1 || FMath::Abs(D1.Y) > 1;
		}
		if (bKeep) Out.Add(FVector(Center(Chain[K]), 0.f));
	}
	return Out;
}

// ------------------------------------------------------------------------------------------------ play
void AIVVillageGenerator::BeginPlay()
{
	Super::BeginPlay();
	SessionSeed = FixedSessionSeed != 0 ? FixedSessionSeed : (int32)(FDateTime::Now().GetTicks() & 0x7fffffff);
	BandCache.Reset(); LotCache.Reset(); CacheSessionSeed = SessionSeed;
	if (bRevealEffect && RevealPostMaterial)
	{
		RevealMID = UMaterialInstanceDynamic::Create(RevealPostMaterial, this);
		for (int32 Slot = 0; Slot < RevealSlots; ++Slot) RevealMID->SetVectorParameterValue(*FString::Printf(TEXT("Info%d"), Slot), FLinearColor(0, 0, -1e6f, 0));
		RevealPost->Settings.WeightedBlendables.Array.Add(FWeightedBlendable(1.f, RevealMID));
	}
	if (SilhouetteMaterial) RevealPost->Settings.WeightedBlendables.Array.Add(FWeightedBlendable(1.f, SilhouetteMaterial));
	MapData.Reset();
	InsideBuilding = -1;
	for (auto It = Sections.CreateIterator(); It; ++It) if (!It->Value) It.RemoveCurrent();
	if (Sections.Num() == 0) SpawnSection(FIntPoint::ZeroValue, false);
	else for (auto& KV : Sections) KV.Value->ActivateForPlay();
	int32 Nb = 0; for (auto& KV : Sections) Nb += KV.Value->GetNumBuildings();
	UE_LOG(LogIsoVillageGen, Log, TEXT("IVGEN play: %d start sections, %d buildings, session seed %d"), Sections.Num(), Nb, SessionSeed);
}

void AIVVillageGenerator::Tick(float Dt)
{
	Super::Tick(Dt);
	const AActor* Pawn = GetTrackedActor();
	if (Pawn)
	{
		const FVector L = Pawn->GetActorLocation(), V = Pawn->GetVelocity();
		// the section TriggerDistance ahead of her along each axis she is moving on
		for (int32 Axis = 0; Axis < 2; ++Axis)
		{
			const float Vx = Axis == 0 ? V.X : V.Y;
			if (FMath::Abs(Vx) < 30.f) continue;
			FVector A = L; (Axis == 0 ? A.X : A.Y) += FMath::Sign(Vx) * TriggerDistance;
			Enqueue(WorldToSection(A));
		}
		if (FMath::Abs(V.X) >= 30.f && FMath::Abs(V.Y) >= 30.f)
			Enqueue(WorldToSection(L + FVector(FMath::Sign(V.X), FMath::Sign(V.Y), 0) * TriggerDistance));
		// safety: a missing neighbour close to her is generated whatever her direction
		const FIntPoint Here = WorldToSection(L);
		Enqueue(Here);
		for (int32 Dx = -1; Dx <= 1; ++Dx)
			for (int32 Dy = -1; Dy <= 1; ++Dy)
			{
				const FIntPoint C = Here + FIntPoint(Dx, Dy);
				if (IsSectionGenerated(C)) continue;
				const FVector2D Mn = SectionMin(C);
				const float Ex = FMath::Max3((float)Mn.X - (float)L.X, 0.f, (float)L.X - ((float)Mn.X + SectionSize));
				const float Ey = FMath::Max3((float)Mn.Y - (float)L.Y, 0.f, (float)L.Y - ((float)Mn.Y + SectionSize));
				if (FMath::Sqrt(Ex * Ex + Ey * Ey) < SafetyDistance) Enqueue(C);
			}
		// far runtime sections are dropped (they come back identical: same session seed; the map keeps them)
		if (UnloadSectionDistance > 0)
		{
			for (auto It = Sections.CreateIterator(); It; ++It)
			{
				if (IsStartSection(It->Key) || !It->Value || It->Value == Building) continue;
				if (FMath::Max(FMath::Abs(It->Key.X - Here.X), FMath::Abs(It->Key.Y - Here.Y)) > UnloadSectionDistance)
				{
					if (InsideBuilding >= 0 && InsideSection == It->Key) InsideBuilding = -1;
					It->Value->Destroy(); It.RemoveCurrent(); ++SectionsRemoved;
				}
			}
		}
		UpdateCutaway(L);
	}
	// a section being built gets a few ms a frame; the next queued one starts when it is done
	if (Building)
	{
		if (Building->ContinueGenerate(FrameBudgetMs / 1000.0))
		{
			AIVSection* Done = Building; Building = nullptr;
			StartReveal(Done);
			InsideBuilding = -2;      // re-evaluate the cutaway (a new neighbour may hide the house she is in)
		}
		return;
	}
	while (Queue.Num() > 0)
	{
		const FIntPoint C = Queue[0]; Queue.RemoveAt(0);
		if (IsSectionGenerated(C)) continue;
		SpawnSection(C, false, true);
		break;
	}
}
