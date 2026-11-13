// The list of 2026-11-12's third phase: twenty kinds of ruins in the wilderness ("have at least 20 kinds of ruins"; "add these
// ruin types in the wilderness: temple ruins, castle and fortress ruins, abbey and monastery ruins, jungle-swallowed cities, tells,
// barrows and burial mounds, megalithic monuments, rock-cut architecture, cliff dwellings, underground cities and catacombs,
// submerged ruins, ash-buried cities, sand-buried cities, amphitheaters and theaters, infrastructure ruins, ghost towns, industrial
// ruins, war ruins and memorials, exclusion-zone ruins, follies"). A wild place of kind "ruins" is one of WildRuinKinds (924, from
// SourceArt/wilderness/ruins12.json) chosen from its id among the kinds of its biome; its parts are laid from pack meshes
// (WildPieces, "r12_<name>#<n>") by a small layout language, from the place's own random stream (the world's other draws
// untouched), with a container or two (the wild boxes, kept looted under keys of their own) and, for some, guardians.
#include "RD/RDDungeonGenerator.h"
#include "RD/RDWild.h"
#include "RD/RDGameInstance.h"
#include "RD/RDCombat.h"
#include "RD/RDMonster.h"
#include "RD/RDSection.h"
#include "Components/StaticMeshComponent.h"
#include "ProceduralMeshComponent.h"
#include "Engine/StaticMesh.h"
#include "PhysicsEngine/BodySetup.h"
#include "Kismet/GameplayStatics.h"

DEFINE_LOG_CATEGORY_STATIC(LogRDRuin12, Log, All);

namespace
{
	/** a part's line as key=value pairs */
	TMap<FString, FString> RDR12Parse(const FString& Line)
	{
		TMap<FString, FString> Out;
		TArray<FString> Kv; Line.ParseIntoArray(Kv, TEXT(";"), true);
		for (const FString& S : Kv)
		{
			FString K, V;
			if (S.Split(TEXT("="), &K, &V)) Out.Add(K.TrimStartAndEnd(), V.TrimStartAndEnd());
		}
		return Out;
	}
	/** a number or a range "lo-hi" drawn from R (a leading minus is a sign, not a range) */
	float RDR12Num(const TMap<FString, FString>& M, const TCHAR* Key, float Def, FRandomStream& R)
	{
		const FString* V = M.Find(Key);
		if (!V || V->IsEmpty()) return Def;
		const int32 Dash = V->Find(TEXT("-"), ESearchCase::CaseSensitive, ESearchDir::FromStart, 1);
		if (Dash > 0) return R.FRandRange(FCString::Atof(*V->Left(Dash)), FCString::Atof(*V->Mid(Dash + 1)));
		return FCString::Atof(**V);
	}
	/** a ruin's container keys: above the farms' (1 << 40), the houses' (2 << 40); a place's n-th */
	int64 RDR12Key(int32 PlaceId, int32 N) { return (3LL << 40) + (int64)(uint32)PlaceId * 8 + FMath::Clamp(N, 0, 7); }
}

namespace
{
	/** water a ruin can stand in (over 30 cm deep), and ground with none at all (the shore) */
	bool RDR12Deep(const FRDWildWorld& W, const FVector2D& At) { FRDWSample S; W.Sample(At.X, At.Y, S, false); return S.WaterKind != 0 && S.Water > S.H + 0.3f; }
	bool RDR12Dry(const FRDWildWorld& W, const FVector2D& At) { FRDWSample S; W.Sample(At.X, At.Y, S, false); return S.WaterKind == 0 || S.Water <= S.H; }
}

const ARDDungeonGenerator::FRuinPick& ARDDungeonGenerator::WildRuinPickOf(const FRDWildPlace& P) const
{
	// (one answer a place, worked out once: the kind, the scan for water and the ruin's middle and shore were asked four or
	// five times for each ruin as its chunk was made, each scan its own (PR #56's review: the kind's scan and the middle's were
	// on different grids, and the middle could miss the water the kind had found))
	if (const FRuinPick* Got = WildRuinPicks.Find(P.Id)) return *Got;
	FRuinPick& Pk = WildRuinPicks.Add(P.Id);
	Pk.Centre = Pk.Shore = P.At;
	if (!Wild || P.Kind != TEXT("ruins") || !P.Quest.IsEmpty() || WildRuinKinds.Num() == 0) return Pk;
	const FString Bn = Wild->Biomes.IsValidIndex(P.Biome) ? Wild->Biomes[P.Biome].Name : FString();
	auto Fits = [&](const FRDWildRuinKind& K) { return K.Biomes.Contains(TEXT("*")) || K.Biomes.Contains(Bn); };
	// (water within 300 m: the submerged ruins' ground. A place is never on water nor on land under 2 m: of the 340 ruins round
	// Brokenspire none had water within 30 m, nor within 80 m. Only where a water kind fits the biome: rings out every 25 m,
	// eight ways each, the nearest wet sample first)
	bool bWet = false; FVector2D Hit = P.At, Way(1, 0);
	if (WildRuinKinds.ContainsByPredicate([&](const FRDWildRuinKind& K) { return K.bWater && Fits(K); }))
		for (float Rr = 25.f; Rr <= 300.f && !bWet; Rr += 25.f)
			for (int32 I = 0; I < 8 && !bWet; ++I)
			{
				const FVector2D D(FMath::Cos(I * PI / 4.f), FMath::Sin(I * PI / 4.f));
				if (RDR12Deep(*Wild, P.At + D * Rr)) { bWet = true; Hit = P.At + D * Rr; Way = D; }
			}
	float Sum = 0.f;
	TArray<float> W; W.SetNumZeroed(WildRuinKinds.Num());
	for (int32 I = 0; I < WildRuinKinds.Num(); ++I)
	{
		const FRDWildRuinKind& K = WildRuinKinds[I];
		if ((K.bWater && !bWet) || !Fits(K)) continue;
		W[I] = FMath::Max(K.Weight, 0.f); Sum += W[I];
	}
	if (Sum <= 0.f) return Pk;
	float Pick = (FRDWildWorld::Hash(P.Id, 0x1212, Wild->Seed) & 0xFFFFFF) / float(0x1000000) * Sum;
	for (int32 I = 0; I < W.Num() && Pk.Kind < 0; ++I) { if (W[I] <= 0.f) continue; if (Pick < W[I]) Pk.Kind = I; else Pick -= W[I]; }
	for (int32 I = W.Num() - 1; I >= 0 && Pk.Kind < 0; --I) if (W[I] > 0.f) Pk.Kind = I;
	if (Pk.Kind < 0 || !WildRuinKinds[Pk.Kind].bWater) return Pk;
	// (into the water the kind found: its edge walked back to the metre, the middle 12 m past it if that is still deep (a stream
	// may be narrower: then the wet sample itself), the shore the first ground with no water at all from 3 m before the edge)
	FVector2D Edge = Hit;
	for (int32 S = 1; S <= 25; ++S) { const FVector2D Q = Hit - Way * float(S); if (!RDR12Deep(*Wild, Q)) break; Edge = Q; }
	const FVector2D Mid = Edge + Way * 12.f;
	Pk.Centre = RDR12Deep(*Wild, Mid) ? Mid : Hit;
	Pk.Shore = P.At;
	for (int32 S = 3; S <= 40; ++S) { const FVector2D Q = Edge - Way * float(S); if (RDR12Dry(*Wild, Q)) { Pk.Shore = Q; break; } }
	return Pk;
}

int32 ARDDungeonGenerator::WildRuinKindOf(const FRDWildPlace& P) const { return WildRuinPickOf(P).Kind; }

FVector2D ARDDungeonGenerator::WildRuinCentre(const FRDWildPlace& P, FVector2D* Shore) const
{
	const FRuinPick& Pk = WildRuinPickOf(P);
	if (Shore) *Shore = Pk.Shore;
	return Pk.Centre;
}

UStaticMeshComponent* ARDDungeonGenerator::LayRuinPiece(ARDWildChunk* C, UStaticMesh* M, const FVector& At, const FRotator& Rot, const FVector& Scale, float Sink, bool bCollide)
{
	if (!C || !M) return nullptr;
	// (by its box, not its origin: the packs' origins are anywhere (a pillar's 1.4 m under it, a dome's 15 m); its box's middle at
	// the point, its lowest corner as turned on the lowest ground under its four corners)
	const FBox B = M->GetBoundingBox();
	const FTransform T(Rot, FVector::ZeroVector, Scale);
	FVector Lo(1e9), Hi(-1e9);
	for (int32 I = 0; I < 8; ++I)
	{
		const FVector Pc((I & 1) ? B.Max.X : B.Min.X, (I & 2) ? B.Max.Y : B.Min.Y, (I & 4) ? B.Max.Z : B.Min.Z);
		const FVector Q = T.TransformPosition(Pc);
		Lo = Lo.ComponentMin(Q); Hi = Hi.ComponentMax(Q);
	}
	const FVector Mid = (Lo + Hi) * 0.5f;
	float G = 1e9f;
	for (int32 I = 0; I < 5; ++I)
	{
		const FVector2D Off = I == 4 ? FVector2D(0, 0) : FVector2D((I & 1) ? Hi.X - Mid.X : Lo.X - Mid.X, (I & 2) ? Hi.Y - Mid.Y : Lo.Y - Mid.Y) * 0.8f;
		G = FMath::Min(G, WildGroundZ(FVector(At.X + Off.X, At.Y + Off.Y, 0.0)));
	}
	const FVector W(At.X - Mid.X, At.Y - Mid.Y, G + At.Z - Lo.Z - Sink);
	UStaticMeshComponent* Sm = NewObject<UStaticMeshComponent>(C);
	Sm->SetStaticMesh(M);
	Sm->SetupAttachment(C->Ground);
	Sm->SetRelativeLocation(W - C->GetActorLocation());
	Sm->SetRelativeRotation(Rot);
	Sm->SetRelativeScale3D(Scale);
	if (!bCollide) Sm->SetCollisionEnabled(ECollisionEnabled::NoCollision);
	Sm->RegisterComponent();
	C->PlaceProps.Add(Sm);
	return Sm;
}

void ARDDungeonGenerator::LayWildRuin(ARDWildChunk* C, const FRDWildPlace& P, const FRDWildRuinKind& K)
{
	if (!C || !Wild) return;
	FRandomStream R((int32)FRDWildWorld::Hash(P.Id, 0x1213, Wild->Seed));
	FVector2D Shore;
	const FVector2D O = WildRuinCentre(P, &Shore);
	const float Yaw0 = P.Yaw;
	const FRotator Frame(0.f, Yaw0, 0.f);
	FRuinLaid Rec; Rec.Id = P.Id; Rec.Yaw = P.Yaw; Rec.Kind = WildRuinKinds.IndexOfByPredicate([&](const FRDWildRuinKind& X) { return X.Name == K.Name; }); Rec.At = O; Rec.Name = P.Name;
	int32 BoxN = 0;
	for (const FString& Line : K.Parts)
	{
		const TMap<FString, FString> M = RDR12Parse(Line);
		const FString L = M.FindRef(TEXT("L"));
		const FString Pre = M.FindRef(TEXT("p"));
		const FString BoxPiece = M.FindRef(TEXT("box"));
		TArray<UStaticMesh*> Ms;
		if (!Pre.IsEmpty()) WildPiecesOf(Pre, Ms);
		if (Ms.Num() == 0 && BoxPiece.IsEmpty()) { UE_LOG(LogRDRuin12, Verbose, TEXT("RDRUIN %s: no pieces %s"), *K.Name.ToString(), *Pre); continue; }
		const int32 N = FMath::Max(1, FMath::RoundToInt(RDR12Num(M, TEXT("n"), 1.f, R)));
		const int32 N2 = FMath::Max(1, FMath::RoundToInt(RDR12Num(M, TEXT("n2"), 1.f, R)));
		const float Rad = RDR12Num(M, TEXT("r"), 8.f, R), Rad2 = RDR12Num(M, TEXT("r2"), Rad, R);
		const float Ox = RDR12Num(M, TEXT("x"), 0.f, R), Oy = RDR12Num(M, TEXT("y"), 0.f, R), Oz = RDR12Num(M, TEXT("z"), 0.f, R);
		const float A0 = RDR12Num(M, TEXT("a"), L == TEXT("ring") ? R.FRandRange(0.f, 360.f) : 0.f, R);
		const float Span = RDR12Num(M, TEXT("span"), 360.f, R);
		const float Keep = RDR12Num(M, TEXT("keep"), 1.f, R);
		const float Jit = RDR12Num(M, TEXT("jit"), 0.f, R);
		const FString YawMode = M.Contains(TEXT("yaw")) ? M.FindRef(TEXT("yaw")) : FString(TEXT("along"));
		const bool bCol = RDR12Num(M, TEXT("col"), 1.f, R) > 0.5f;
		// (the instances' places in the place's frame (metres) and their yaw before the frame's)
		struct FAt { FVector2D Xy; float Yaw; float Z; };
		TArray<FAt> Ats;
		auto Add = [&](float X, float Y, float Yw, float Z) { Ats.Add({ FVector2D(X + Ox, Y + Oy), Yw, Z + Oz }); };
		if (L == TEXT("at")) for (int32 I = 0; I < N; ++I) Add(0.f, 0.f, 0.f, 0.f);
		else if (L == TEXT("ring") || L == TEXT("arc"))
		{
			const bool bFull = Span >= 359.f;
			for (int32 I = 0; I < N; ++I)
			{
				const float Ad = bFull ? A0 + I * 360.f / N : A0 - Span * 0.5f + (N > 1 ? Span * I / (N - 1) : Span * 0.5f);
				const float A = FMath::DegreesToRadians(Ad);
				Add(FMath::Cos(A) * Rad, FMath::Sin(A) * Rad, Ad, 0.f);
			}
		}
		else if (L == TEXT("tiers"))
		{
			// (rows of an amphitheatre: row i an arc of radius r + i x dr, dz higher, pieces sp metres apart along it)
			const float Dr = RDR12Num(M, TEXT("dr"), 1.f, R), Dz = RDR12Num(M, TEXT("dz"), 0.5f, R), Sp = FMath::Max(RDR12Num(M, TEXT("sp"), 3.f, R), 0.5f);
			for (int32 Row = 0; Row < N2; ++Row)
			{
				const float Rr = Rad + Row * Dr;
				const int32 Nr = FMath::Max(2, FMath::CeilToInt(FMath::DegreesToRadians(Span) * Rr / Sp));
				for (int32 I = 0; I <= Nr; ++I)
				{
					const float Ad = A0 - Span * 0.5f + Span * I / Nr;
					const float A = FMath::DegreesToRadians(Ad);
					Add(FMath::Cos(A) * Rr, FMath::Sin(A) * Rr, Ad, Row * Dz);
				}
			}
		}
		else if (L == TEXT("line"))
		{
			const FVector2D D(FMath::Cos(FMath::DegreesToRadians(A0)), FMath::Sin(FMath::DegreesToRadians(A0)));
			for (int32 I = 0; I < N; ++I) { const float T = N > 1 ? -Rad * 0.5f + Rad * I / (N - 1) : 0.f; Add(D.X * T, D.Y * T, A0, 0.f); }
		}
		else if (L == TEXT("rect"))
		{
			// (a rectangle's walls, r along X and r2 along Y: n pieces on each X side, n2 on each Y side, along their side)
			for (int32 S = 0; S < 2; ++S)
				for (int32 I = 0; I < N; ++I) Add(-Rad * 0.5f + Rad * (I + 0.5f) / N, (S ? 1.f : -1.f) * Rad2 * 0.5f, S ? 0.f : 180.f, 0.f);
			for (int32 S = 0; S < 2; ++S)
				for (int32 I = 0; I < N2; ++I) Add((S ? 1.f : -1.f) * Rad * 0.5f, -Rad2 * 0.5f + Rad2 * (I + 0.5f) / N2, S ? 90.f : 270.f, 0.f);
		}
		else if (L == TEXT("grid"))
		{
			for (int32 I = 0; I < N; ++I) for (int32 J = 0; J < N2; ++J) Add((I - (N - 1) * 0.5f) * Rad, (J - (N2 - 1) * 0.5f) * Rad2, 0.f, 0.f);
		}
		else           // scatter
		{
			const float R0 = RDR12Num(M, TEXT("r0"), 0.f, R);
			for (int32 I = 0; I < N; ++I)
			{
				const float A = R.FRandRange(0.f, 2.f * PI), D = FMath::Sqrt(R.FRandRange(R0 * R0 / FMath::Max(Rad * Rad, 1.f), 1.f)) * Rad;
				Add(FMath::Cos(A) * D, FMath::Sin(A) * D, FMath::RadiansToDegrees(A), 0.f);
			}
		}
		for (const FAt& A : Ats)
		{
			// (every instance makes the same draws, kept or not, so a part's kept pieces stay where they were)
			const float Kept = R.FRand();
			const FVector2D J(R.FRandRange(-Jit, Jit), R.FRandRange(-Jit, Jit));
			float Yw = YawMode == TEXT("face") ? A.Yaw + 180.f : YawMode == TEXT("out") ? A.Yaw : YawMode == TEXT("rand") ? R.FRandRange(0.f, 360.f) : YawMode == TEXT("tangent") ? A.Yaw + 90.f : YawMode == TEXT("fixed") ? 0.f : A.Yaw;
			Yw += RDR12Num(M, TEXT("yawadd"), 0.f, R) + R.FRandRange(-1.f, 1.f) * RDR12Num(M, TEXT("yawjit"), 0.f, R);
			const float Tilt = RDR12Num(M, TEXT("tilt"), 0.f, R);
			const float Pitch = (RDR12Num(M, TEXT("lie"), 0.f, R) > 0.5f ? 90.f : 0.f) + R.FRandRange(-Tilt, Tilt);
			const float Roll = R.FRandRange(-Tilt, Tilt);
			const float Hm = RDR12Num(M, TEXT("h"), 0.f, R), Sm = RDR12Num(M, TEXT("s"), 1.f, R);
			const float Sx = RDR12Num(M, TEXT("sx"), 1.f, R), Sy = RDR12Num(M, TEXT("sy"), 1.f, R), Sz = RDR12Num(M, TEXT("sz"), 1.f, R);
			const float Sink = RDR12Num(M, TEXT("sink"), 5.f, R);
			UStaticMesh* Mesh = Ms.Num() > 0 ? Ms[R.RandRange(0, Ms.Num() - 1)] : nullptr;
			if (Kept > Keep) continue;
			const FVector2D Lxy = A.Xy + J;
			// (land=1: on the shore by the water the ruin stands in, not the ruin's middle moved into the water)
			const FVector2D Base = RDR12Num(M, TEXT("land"), 0.f, R) > 0.5f ? Shore : O;
			const FVector2D Wxy = Base + FVector2D(Frame.RotateVector(FVector(Lxy.X, Lxy.Y, 0.0)));
			const float Wyaw = Yaw0 + Yw;
			// (wild=1: a piece of the places' table laid as the villages lay theirs, by its origin at the table's scale: a house so
			// laid gets its doors, its inside and its furniture (FitWildHouse))
			if (RDR12Num(M, TEXT("wild"), 0.f, R) > 0.5f)
			{
				if (UStaticMeshComponent* Pc = LayWildPiece(C, Pre, Wxy, Wyaw, Sm, Sink, bCol, false, R)) { ++Rec.Pieces; Rec.Comps.Add(Pc); Rec.Lifts.Add(-1.f); }
				continue;
			}
			if (!BoxPiece.IsEmpty())
			{
				// (a container: the dungeon's piece by name, on the ground, kept looted under the place's key)
				const FVector Wp(Wxy.X * 100.0, Wxy.Y * 100.0, WildGroundZ(FVector(Wxy.X * 100.0, Wxy.Y * 100.0, 0.0)) + A.Z * 100.f);
				if (AddWildBox(C, FName(*BoxPiece), FTransform(FRotator(0.f, Wyaw, 0.f), Wp), FName(TEXT("chest")), RDR12Key(P.Id, BoxN), K.Loot)) { ++BoxN; ++Rec.Boxes; }
				continue;
			}
			if (!Mesh) continue;
			// (its size: h metres high (its box's height as it stands), else s times its own)
			const FBox B = Mesh->GetBoundingBox();
			const float Bh = FMath::Max((float)(Pitch > 45.f ? B.GetSize().X : B.GetSize().Z), 1.f);
			const float Sc = Hm > 0.f ? Hm * 100.f / Bh : Sm;
			const FRotator Rot(Pitch, Wyaw, Roll);
			// (its sink: with a height in metres, centimetres of the piece as laid (only stretched by sz); with a scale, centimetres
			// of the mesh scaled. Scaled by each mesh's own size, one part's pillars sank 75 to 300 cm (PR #56's review))
			const float SinkCm = (Hm > 0.f ? Sink : Sink * Sc) * Sz;
			if (UStaticMeshComponent* Pc = LayRuinPiece(C, Mesh, FVector(Wxy.X * 100.0, Wxy.Y * 100.0, A.Z * 100.f), Rot, FVector(Sc * Sx, Sc * Sy, Sc * Sz), SinkCm, bCol)) { ++Rec.Pieces; Rec.Comps.Add(Pc); Rec.Lifts.Add(A.Z * 100.f); }
		}
	}
	Rec.Guards = K.Guards;
	WildRuinsLaid.RemoveAll([&](const FRuinLaid& X) { return X.Id == P.Id; });
	WildRuinsLaid.Add(Rec);
	UE_LOG(LogRDRuin12, Log, TEXT("RDRUIN %s (%s): %d pieces, %d containers at (%.0f, %.0f)"), *P.Name, *K.Name.ToString(), Rec.Pieces, Rec.Boxes, O.X, O.Y);
}

bool ARDDungeonGenerator::WildRuinInPiece(const FRuinLaid& X, const FVector& L, float Radius, float HalfHeight) const
{
	// (a capsule there against each colliding piece's own collision: a long cairn turned across the ground fills its box's
	// corners with nothing, and the box called a guard beside it inside)
	const FCollisionShape Cap = FCollisionShape::MakeCapsule(Radius, FMath::Max(HalfHeight, Radius));
	for (const TWeakObjectPtr<UStaticMeshComponent>& W : X.Comps)
	{
		UStaticMeshComponent* Sm = W.Get();
		if (!Sm || Sm->GetCollisionEnabled() == ECollisionEnabled::NoCollision) continue;
		if (!Sm->Bounds.GetBox().ExpandBy(Radius + 10.f).IsInside(L)) continue;
		if (Sm->OverlapComponent(L, FQuat::Identity, Cap)) return true;
	}
	return false;
}

void ARDDungeonGenerator::TickWildRuins12(float Dt, const FVector& Her)
{
	WildRuinLook -= Dt;
	if (WildRuinLook > 0.f || !PlayerCombat) return;
	WildRuinLook = 1.f;
	const FVector2D H(Her.X / 100.0, Her.Y / 100.0);
	// (the ones laid far from her are gone with their chunks: forgotten past 3 km)
	WildRuinsLaid.RemoveAll([&](const FRuinLaid& X) { return FVector2D::Distance(X.At, H) > 3000.f; });
	for (const FRuinLaid& X : WildRuinsLaid)
	{
		if (!WildRuinKinds.IsValidIndex(X.Kind) || WildRuinsTold.Contains(X.Id) || FVector2D::Distance(X.At, H) > 30.f) continue;
		WildRuinsTold.Add(X.Id);
		const FRDWildRuinKind& K = WildRuinKinds[X.Kind];
		PlayerCombat->ShowMessage(FString::Printf(TEXT("%s: %s"), *K.Title, *K.Text));
	}
}

TArray<FString> ARDDungeonGenerator::GetWildRuinLines() const
{
	TArray<FString> Out;
	for (const FRuinLaid& X : WildRuinsLaid)
	{
		// (its guards as they stand: the living ones of its place (their keys its id x 16 + n), and those inside a piece's box)
		int32 Stand = 0, Inside = 0;
		if (WildSection)
			for (const TObjectPtr<ARDMonster>& Mo : WildSection->SpawnedMonsters)
			{
				if (!IsValid(Mo) || Mo->IsDead() || Mo->WildKey < 0 || Mo->WildKey / 16 != (int64)X.Id) continue;
				++Stand;
				if (WildRuinInPiece(X, Mo->GetActorLocation(), Mo->GetSimpleCollisionRadius() * 0.8f, Mo->GetSimpleCollisionHalfHeight() * 0.8f)) ++Inside;
			}
		Out.Add(FString::Printf(TEXT("ruin|%d|%s|%s|%.1f|%.1f|%d|%d|%d|%s|%.1f|%d|%d"), X.Id, WildRuinKinds.IsValidIndex(X.Kind) ? *WildRuinKinds[X.Kind].Name.ToString() : TEXT("?"),
			WildRuinKinds.IsValidIndex(X.Kind) ? *WildRuinKinds[X.Kind].Title : TEXT(""), X.At.X, X.At.Y, X.Pieces, X.Boxes, X.Guards, *X.Name, X.Yaw, Stand, Inside));
	}
	return Out;
}

TArray<FString> ARDDungeonGenerator::GetWildRuinPieceLines(int32 Id) const
{
	TArray<FString> Out;
	const FRuinLaid* X = WildRuinsLaid.FindByPredicate([&](const FRuinLaid& R) { return R.Id == Id; });
	if (!X) return Out;
	for (int32 I = 0; I < X->Comps.Num(); ++I)
	{
		const UStaticMeshComponent* Sm = X->Comps[I].Get();
		if (!Sm) { Out.Add(TEXT("gone|0|0|0|0|0|-|-1")); continue; }
		const FBox B = Sm->Bounds.GetBox();
		const FVector Ce = B.GetCenter();
		// (solid: 1 its collision on and something in it to stop her (simple shapes, or its mesh as its collision), 0 on with nothing
		// to stop her (walked through), - off)
		const UBodySetup* Bs = Sm->GetStaticMesh() ? Sm->GetStaticMesh()->GetBodySetup() : nullptr;
		const bool bOn = Sm->GetCollisionEnabled() == ECollisionEnabled::QueryAndPhysics || Sm->GetCollisionEnabled() == ECollisionEnabled::PhysicsOnly;
		const bool bStops = Bs && (Bs->AggGeom.GetElementCount() > 0 || Bs->CollisionTraceFlag == CTF_UseComplexAsSimple);
		Out.Add(FString::Printf(TEXT("%s|%.0f|%.0f|%.0f|%.0f|%.0f|%s|%.0f"), Sm->GetStaticMesh() ? *Sm->GetStaticMesh()->GetName() : TEXT("?"), Ce.X, Ce.Y, B.Min.Z, B.Max.Z, WildGroundZ(FVector(Ce.X, Ce.Y, 0.0)),
			!bOn ? TEXT("-") : bStops ? TEXT("1") : TEXT("0"), X->Lifts.IsValidIndex(I) ? X->Lifts[I] : -1.f));
	}
	return Out;
}

FString ARDDungeonGenerator::FindWildRuin(FName Kind, float X, float Y, float MaxKm) const
{
	if (!Wild) return FString();
	const int32 Want = WildRuinKinds.IndexOfByPredicate([&](const FRDWildRuinKind& K) { return K.Name == Kind; });
	if (Want < 0) return FString();
	// (rings of the world's place cells out from the point: the nearest first)
	const FIntPoint C0 = Wild->PlaceCellOf(X, Y);
	const int32 Rmax = FMath::CeilToInt(MaxKm * 1000.0 / FRDWildWorld::PlaceCellM);
	for (int32 Ring = 0; Ring <= Rmax; ++Ring)
	{
		float Best = 1e18f; FString Got;
		for (int32 I = -Ring; I <= Ring; ++I)
			for (int32 J = -Ring; J <= Ring; ++J)
			{
				if (FMath::Max(FMath::Abs(I), FMath::Abs(J)) != Ring) continue;
				TArray<FRDWildPlace> Ps; Wild->PlacesIn(C0 + FIntPoint(I, J), Ps);
				for (const FRDWildPlace& P : Ps)
				{
					if (P.Kind != TEXT("ruins") || WildRuinKindOf(P) != Want) continue;
					const FVector2D Ce = WildRuinCentre(P);
					const float D = FVector2D::DistSquared(Ce, FVector2D(X, Y));
					if (D < Best) { Best = D; Got = FString::Printf(TEXT("%d|%.1f|%.1f|%.1f|%s"), P.Id, Ce.X, Ce.Y, P.Yaw, *P.Name); }
				}
			}
		if (!Got.IsEmpty()) return Got;
	}
	return FString();
}

TArray<FString> ARDDungeonGenerator::CountWildRuins(float X, float Y, float MaxKm) const
{
	TArray<FString> Out;
	if (!Wild) return Out;
	TArray<int32> N; N.SetNumZeroed(WildRuinKinds.Num() + 1);
	const FIntPoint C0 = Wild->PlaceCellOf(X, Y);
	const int32 Rmax = FMath::CeilToInt(MaxKm * 1000.0 / FRDWildWorld::PlaceCellM);
	for (int32 I = -Rmax; I <= Rmax; ++I)
		for (int32 J = -Rmax; J <= Rmax; ++J)
		{
			TArray<FRDWildPlace> Ps; Wild->PlacesIn(C0 + FIntPoint(I, J), Ps);
			for (const FRDWildPlace& P : Ps) if (P.Kind == TEXT("ruins") && P.Quest.IsEmpty()) { const int32 K = WildRuinKindOf(P); N[K >= 0 ? K : WildRuinKinds.Num()]++; }
		}
	for (int32 K = 0; K < WildRuinKinds.Num(); ++K) Out.Add(FString::Printf(TEXT("%s|%d"), *WildRuinKinds[K].Name.ToString(), N[K]));
	Out.Add(FString::Printf(TEXT("none|%d"), N.Last()));
	return Out;
}
