// mistward_castle, the list of 2026-10-31b (docs/improvements5.txt; pipeline/unreal/879): ceilings of more shapes and sizes
// (the generator's bCeilingStyles). Each rectangular room draws a style from a stream of its own after the plan (the layout,
// its furniture and its monsters are what they were):
//   flat      the tiles' ceiling, as before
//   raised    the same, 1 to 3 m higher (its walls stack up to it)
//   beamed    raised, with beams across it and one along it
//   sail dome / groin vault / barrel vault / cloister vault / hipped   a vault over the whole room, one mesh made here in its
//             ceiling's material, springing from where its walls end (a band of its wall's material closes any wall that
//             ends lower); the groin and barrel vaults carry ribs
#include "RD/RDSection.h"
#include "RD/RDDungeonGenerator.h"
#include "Engine/StaticMesh.h"
#include "Materials/MaterialInterface.h"
#include "ProceduralMeshComponent.h"

static const TCHAR* RDCeilNames[] = { TEXT("flat"), TEXT("raised"), TEXT("beamed"), TEXT("sail dome"), TEXT("groin vault"), TEXT("barrel vault"), TEXT("cloister vault"), TEXT("hipped") };

void ARDSection::StyleCeilings()
{
	const float S = Generator->TileSize, RH = Generator->RoomHeight;
	struct FW { uint8 Style; float W; };
	static const FW Kinds[] = { { 1, 1.f }, { 2, 1.2f }, { 3, 1.4f }, { 4, 1.4f }, { 5, 1.4f }, { 6, 1.f }, { 7, 0.8f } };
	float Sum = 0.f; for (const FW& K : Kinds) Sum += K.W;
	for (int32 RI = 0; RI < Rooms.Num(); ++RI)
	{
		FRoom& Rm = Rooms[RI];
		// (three draws a room, whatever it gets: one room's choice never moves another's)
		FRandomStream RS((int32)HashCombine((uint32)Seed ^ 0x7C3E11u, (uint32)RI * 2654435761u));
		const float U = RS.FRand(), V = RS.FRand(), Rk = RS.FRand();
		Rm.Ceil = 0; Rm.CeilRise = 0.f;
		if (Rm.Kind == ERDRoomKind::Junction || Rm.Shape != 0 || U >= Generator->CeilingStyleShare) continue;
		float X = V * Sum; uint8 Style = 1;
		for (const FW& K : Kinds) { X -= K.W; if (X <= 0.f) { Style = K.Style; break; } }
		Rm.Ceil = Style;
		const float HalfMin = FMath::Min(Rm.Max.X - Rm.Min.X, Rm.Max.Y - Rm.Min.Y) * S * 0.5f;
		if (Style <= 2)
		{
			// (raised: the whole room 1 to 3 m higher; its walls stack up to it)
			Rm.CeilRise = 100.f * (1 + FMath::Min((int32)(Rk * 3.f), 2));
			for (int32 Tx = Rm.Min.X; Tx < Rm.Max.X; ++Tx)
				for (int32 Ty = Rm.Min.Y; Ty < Rm.Max.Y; ++Ty)
					if (In(FIntPoint(Tx, Ty)) && Owner[Idx(FIntPoint(Tx, Ty))] == RI) CeilH[Idx(FIntPoint(Tx, Ty))] = RH + Rm.CeilRise;
		}
		else
		{
			// (a vault: round ones up to half the span, the sail dome and the hipped roof flatter)
			const bool bRound = Style == 4 || Style == 5 || Style == 6;
			const float K = bRound ? FMath::Lerp(0.55f, 1.f, Rk) : FMath::Lerp(0.35f, 0.65f, Rk);
			Rm.CeilRise = FMath::Min(HalfMin * K, Generator->CeilingMaxRise);
		}
	}
}

float ARDSection::VaultShape(uint8 Style, float U, float V, bool bAlongX)
{
	U = FMath::Clamp(U, -1.f, 1.f); V = FMath::Clamp(V, -1.f, 1.f);
	const float M = FMath::Max(FMath::Abs(U), FMath::Abs(V));
	switch (Style)
	{
	case 3: return (1.f - U * U) * (1.f - V * V);                                                     // sail dome
	case 4: return FMath::Min(FMath::Sqrt(1.f - U * U), FMath::Sqrt(1.f - V * V));                    // groin vault
	case 5:
	{
		const float A = bAlongX ? U : V, B = bAlongX ? V : U;                                           // barrel vault, its ends
		return FMath::Sqrt(1.f - B * B) * FMath::Sqrt(FMath::Max(0.f, 1.f - FMath::Pow(FMath::Abs(A), 8.f)));   // rounded down
	}
	case 6: return FMath::Sqrt(FMath::Max(0.f, 1.f - M * M));                                        // cloister vault
	case 7: return FMath::Clamp((1.f - M) * 1.6f, 0.f, 1.f);                                          // hipped, a flat top
	default: return 0.f;
	}
}

float ARDSection::VaultHeightAt(int32 RI, const FVector& P) const
{
	if (!Rooms.IsValidIndex(RI) || Rooms[RI].Ceil < 3 || !Generator) return -1.f;
	const FRoom& Rm = Rooms[RI];
	const FBox2D B = RoomBox(Rm, 0.f);
	const FVector2D C = B.GetCenter(), H = B.GetExtent();
	const float Spring = FMath::Max(RoomWallTop.IsValidIndex(RI) ? RoomWallTop[RI] : 0.f, Generator->RoomHeight);
	return Spring + Rm.CeilRise * VaultShape(Rm.Ceil, (P.X - C.X) / H.X, (P.Y - C.Y) / H.Y, H.X >= H.Y);
}

FString ARDSection::GetRoomCeiling(int32 I, float& Spring, float& Rise) const
{
	Spring = 0.f; Rise = 0.f;
	if (!Rooms.IsValidIndex(I) || !Generator) return FString();
	const FRoom& Rm = Rooms[I];
	Rise = Rm.CeilRise;
	Spring = Rm.Ceil >= 3 ? FMath::Max(RoomWallTop.IsValidIndex(I) ? RoomWallTop[I] : 0.f, Generator->RoomHeight) : CeilAt(Rm.Lane);
	return Rm.Ceil < UE_ARRAY_COUNT(RDCeilNames) ? RDCeilNames[Rm.Ceil] : TEXT("flat");
}

float ARDSection::GetCeilingHeightAt(FVector Location) const
{
	const int32 RI = RoomAt(Location);
	const float V = VaultHeightAt(RI, Location);
	return V > 0.f ? V : CeilAt(WorldToLocal(Location));
}

/** UE's procedural mesh draws a triangle's front where cross(V1 - V0, V2 - V0) points away from the viewer (the engine's
 *  CreateGridMeshTriangles: its grid seen from above has that cross pointing down). The pieces here are wound with the cross
 *  toward the side that should show, then turned over once before they go in (they were culled from the room: the vaults
 *  showed black) */
static void RD5Turn(TArray<int32>& T)
{
	for (int32 K = 0; K + 2 < T.Num(); K += 3) Swap(T[K + 1], T[K + 2]);
}

/** a mesh section of quads (a grid of Nu x Nv points), its triangles facing where Face points */
static void RD5AddGrid(TArray<FVector>& V, TArray<int32>& T, TArray<FVector>& Nm, TArray<FVector2D>& Uv, const TArray<FVector>& P, const TArray<FVector2D>& PUv, int32 Nu, int32 Nv, bool bFlip)
{
	const int32 Base = V.Num();
	V.Append(P); Uv.Append(PUv);
	Nm.AddZeroed(P.Num());
	for (int32 J = 0; J + 1 < Nv; ++J)
		for (int32 I = 0; I + 1 < Nu; ++I)
		{
			const int32 A = Base + J * Nu + I, B = A + 1, C = A + Nu, D = C + 1;
			if (!bFlip) { T.Append({ A, C, B, B, C, D }); }
			else { T.Append({ A, B, C, B, D, C }); }
		}
}

/** a rib or beam: a box of Width x Depth along a polyline, hanging Down from it (Down: each point's way into the room) */
static void RD5AddRib(TArray<FVector>& V, TArray<int32>& T, TArray<FVector>& Nm, TArray<FVector2D>& Uv, const TArray<FVector>& Line, const TArray<FVector>& Down, float Width, float Depth)
{
	const int32 Np = Line.Num();
	if (Np < 2) return;
	// three faces (two sides, the underside), each a strip of quads with its own corners (flat shading)
	for (int32 Face = 0; Face < 3; ++Face)
	{
		const int32 Base = V.Num();
		float Run = 0.f;
		for (int32 K = 0; K < Np; ++K)
		{
			const FVector Tn = (Line[FMath::Min(K + 1, Np - 1)] - Line[FMath::Max(K - 1, 0)]).GetSafeNormal();
			const FVector Dn = Down[K].GetSafeNormal();
			const FVector Sd = FVector::CrossProduct(Tn, Dn).GetSafeNormal() * (Width * 0.5f);
			if (K > 0) Run += FVector::Dist(Line[K], Line[K - 1]);
			FVector P0, P1;
			if (Face == 0) { P0 = Line[K] + Sd - Dn * 4.f; P1 = Line[K] + Sd + Dn * Depth; }
			else if (Face == 1) { P0 = Line[K] - Sd + Dn * Depth; P1 = Line[K] - Sd - Dn * 4.f; }
			else { P0 = Line[K] + Sd + Dn * Depth; P1 = Line[K] - Sd + Dn * Depth; }
			V.Add(P0); V.Add(P1);
			Uv.Add(FVector2D(Run / 100.f, 0.f)); Uv.Add(FVector2D(Run / 100.f, (Face == 2 ? Width : Depth) / 100.f));
			const FVector N = Face == 0 ? Sd.GetSafeNormal() : Face == 1 ? -Sd.GetSafeNormal() : Dn;
			Nm.Add(N); Nm.Add(N);
		}
		for (int32 K = 0; K + 1 < Np; ++K)
		{
			const int32 A = Base + K * 2, B = A + 1, C = A + 2, D = A + 3;
			T.Append({ A, C, B, B, C, D });
		}
	}
}

void ARDSection::ShellVaults()
{
	if (!Generator || !bBuildStatic) return;
	const float S = Generator->TileSize, RH = Generator->RoomHeight;
	const FVector Org = GetActorLocation();
	const FRDPiece* CeilP = Pc(TEXT("Ceil_Room"));
	UMaterialInterface* CeilMat = CeilP && CeilP->Mesh ? CeilP->Mesh->GetMaterial(0) : nullptr;
	for (int32 RI = 0; RI < Rooms.Num(); ++RI)
	{
		const FRoom& Rm = Rooms[RI];
		if (Rm.Ceil < 2) continue;
		const FRDPiece* WallP = ShellWall.IsValidIndex(RI) ? Pc(ShellWall[RI]) : nullptr;
		UMaterialInterface* WallMat = WallP && WallP->Mesh ? WallP->Mesh->GetMaterial(0) : CeilMat;
		UMaterialInterface* RibMat = Generator->CeilingRibMaterial ? Generator->CeilingRibMaterial.Get() : WallMat;
		UMaterialInterface* BeamMat = Generator->CeilingBeamMaterial ? Generator->CeilingBeamMaterial.Get() : RibMat;
		// (the room's box, 2 cm out past its walls' line: the walls stand in front of the vault's rim and its band)
		const FBox2D B = RoomBox(Rm, -2.f);
		const FVector2D C = B.GetCenter(), H = B.GetExtent();
		const bool bAlongX = H.X >= H.Y;
		UProceduralMeshComponent* M = NewObject<UProceduralMeshComponent>(this);
		M->SetupAttachment(RootComponent);
		// (query collision on the vault and its band: the camera stops under it as under a flat ceiling, and a test's traces find
		// it (a gap shows as a trace that goes through); no physics)
		M->SetCollisionProfileName(TEXT("BlockAll"));
		M->SetCollisionEnabled(ECollisionEnabled::QueryOnly);
		M->SetCastShadow(true);
		M->bUseAsyncCooking = false;
		M->RegisterComponent();
		AddInstanceComponent(M);
		M->SetWorldLocation(Org);
		int32 Sec = 0;
		if (Rm.Ceil == 2)
		{
			// beams: across the short way every 1.5 m or so, one along the middle; under the raised ceiling
			const float Top = CeilAt(Rm.Lane);
			TArray<FVector> V, Nm; TArray<int32> T; TArray<FVector2D> Uv;
			const float Long = bAlongX ? H.X : H.Y, Short = bAlongX ? H.Y : H.X;
			const int32 Nb = FMath::Max(2, FMath::RoundToInt(Long * 2.f / 160.f));
			for (int32 K = 1; K < Nb; ++K)
			{
				const float A = -Long + 2.f * Long * K / Nb;
				TArray<FVector> Line, Down;
				for (const float Bq : { -Short, Short })
				{
					const FVector2D Q = bAlongX ? FVector2D(C.X + A, C.Y + Bq) : FVector2D(C.X + Bq, C.Y + A);
					Line.Add(FVector(Q.X, Q.Y, Top) - Org); Down.Add(FVector(0, 0, -1));
				}
				RD5AddRib(V, T, Nm, Uv, Line, Down, 34.f, 42.f);
			}
			{
				TArray<FVector> Line, Down;
				for (const float Aq : { -Long, Long })
				{
					const FVector2D Q = bAlongX ? FVector2D(C.X + Aq, C.Y) : FVector2D(C.X, C.Y + Aq);
					Line.Add(FVector(Q.X, Q.Y, Top - 40.f) - Org); Down.Add(FVector(0, 0, -1));
				}
				RD5AddRib(V, T, Nm, Uv, Line, Down, 30.f, 34.f);
			}
			RD5Turn(T); M->CreateMeshSection(Sec, V, T, Nm, Uv, TArray<FColor>(), TArray<FProcMeshTangent>(), false);
			if (BeamMat) M->SetMaterial(Sec, BeamMat);
			++VaultMeshes;
			continue;
		}
		const float Spring = FMath::Max(RoomWallTop.IsValidIndex(RI) ? RoomWallTop[RI] : 0.f, RH);
		const float Rise = Rm.CeilRise;
		// ---- the vault: a grid denser near the walls (where the round ones turn steep), its UVs by the length along it
		const int32 Nu = FMath::Clamp(FMath::RoundToInt(H.X * 2.f / 45.f), 12, 90), Nv = FMath::Clamp(FMath::RoundToInt(H.Y * 2.f / 45.f), 12, 90);
		auto Param = [](int32 I, int32 N) { return -FMath::Cos(PI * (float)I / (float)(N - 1)); };
		TArray<FVector> P; P.SetNum(Nu * Nv);
		for (int32 J = 0; J < Nv; ++J)
			for (int32 I = 0; I < Nu; ++I)
			{
				const float U = Param(I, Nu), Vv = Param(J, Nv);
				P[J * Nu + I] = FVector(C.X + U * H.X, C.Y + Vv * H.Y, Spring + Rise * VaultShape(Rm.Ceil, U, Vv, bAlongX)) - Org;
			}
		TArray<FVector2D> PUv; PUv.SetNum(P.Num());
		TArray<float> RunU; RunU.Init(0.f, P.Num());
		TArray<float> RunV; RunV.Init(0.f, P.Num());
		for (int32 J = 0; J < Nv; ++J) for (int32 I = 1; I < Nu; ++I) RunU[J * Nu + I] = RunU[J * Nu + I - 1] + FVector::Dist(P[J * Nu + I], P[J * Nu + I - 1]);
		for (int32 I = 0; I < Nu; ++I) for (int32 J = 1; J < Nv; ++J) RunV[J * Nu + I] = RunV[(J - 1) * Nu + I] + FVector::Dist(P[J * Nu + I], P[(J - 1) * Nu + I]);
		const float UvTile = CeilP ? FMath::Max(CeilP->Size.X, 100.f) : S;
		for (int32 K = 0; K < P.Num(); ++K) PUv[K] = FVector2D(RunU[K] / UvTile, RunV[K] / UvTile);
		TArray<FVector> V, Nm; TArray<int32> T; TArray<FVector2D> Uv;
		RD5AddGrid(V, T, Nm, Uv, P, PUv, Nu, Nv, false);
		// (normals from the grid, turned down into the room)
		for (int32 J = 0; J < Nv; ++J)
			for (int32 I = 0; I < Nu; ++I)
			{
				const FVector Du = P[J * Nu + FMath::Min(I + 1, Nu - 1)] - P[J * Nu + FMath::Max(I - 1, 0)];
				const FVector Dv = P[FMath::Min(J + 1, Nv - 1) * Nu + I] - P[FMath::Max(J - 1, 0) * Nu + I];
				FVector Nn = FVector::CrossProduct(Du, Dv).GetSafeNormal();
				if (Nn.Z > 0.f) Nn = -Nn;
				if (Nn.IsNearlyZero()) Nn = FVector(0, 0, -1);
				Nm[J * Nu + I] = Nn;
			}
		// (the triangles must face down: check one against its normal and flip them all if not)
		if (T.Num() >= 3)
		{
			const FVector Fn = FVector::CrossProduct(V[T[1]] - V[T[0]], V[T[2]] - V[T[0]]);
			if (FVector::DotProduct(Fn, Nm[T[0]]) < 0.f) for (int32 K = 0; K + 2 < T.Num(); K += 3) Swap(T[K + 1], T[K + 2]);
		}
		RD5Turn(T); M->CreateMeshSection(Sec, V, T, Nm, Uv, TArray<FColor>(), TArray<FProcMeshTangent>(), true);
		if (CeilMat) M->SetMaterial(Sec, CeilMat);
		++Sec;
		// ---- the band: from the room's height up to the springing, round the room (it closes a wall that ends lower)
		if (Spring > RH + 2.f)
		{
			TArray<FVector> Bv, Bn; TArray<int32> Bt; TArray<FVector2D> Bu;
			const FVector2D Cn[5] = { FVector2D(B.Min.X, B.Min.Y), FVector2D(B.Max.X, B.Min.Y), FVector2D(B.Max.X, B.Max.Y), FVector2D(B.Min.X, B.Max.Y), FVector2D(B.Min.X, B.Min.Y) };
			for (int32 E = 0; E < 4; ++E)
			{
				const FVector A0(Cn[E].X, Cn[E].Y, RH - 10.f), A1(Cn[E + 1].X, Cn[E + 1].Y, RH - 10.f);
				const FVector2D In2 = (C - (Cn[E] + Cn[E + 1]) * 0.5f).GetSafeNormal();
				const FVector Nn(In2.X, In2.Y, 0.f);
				const int32 Base = Bv.Num();
				const float Len = FVector::Dist(A0, A1), Ht = Spring - RH + 12.f;
				Bv.Append({ A0 - Org, A1 - Org, A0 + FVector(0, 0, Ht) - Org, A1 + FVector(0, 0, Ht) - Org });
				Bn.Append({ Nn, Nn, Nn, Nn });
				Bu.Append({ FVector2D(0, 0), FVector2D(Len / S, 0), FVector2D(0, Ht / S), FVector2D(Len / S, Ht / S) });
				// (facing the room: wound so the front is toward Nn)
				const FVector Fn = FVector::CrossProduct(Bv[Base + 2] - Bv[Base], Bv[Base + 1] - Bv[Base]);
				if (FVector::DotProduct(Fn, Nn) > 0.f) Bt.Append({ Base, Base + 2, Base + 1, Base + 1, Base + 2, Base + 3 });
				else Bt.Append({ Base, Base + 1, Base + 2, Base + 1, Base + 3, Base + 2 });
			}
			RD5Turn(Bt); M->CreateMeshSection(Sec, Bv, Bt, Bn, Bu, TArray<FColor>(), TArray<FProcMeshTangent>(), true);
			if (WallMat) M->SetMaterial(Sec, WallMat);
			++Sec;
		}
		// ---- ribs: the groin vault's diagonals, the barrel vault's arches across it
		TArray<FVector> Rv, Rn; TArray<int32> Rt; TArray<FVector2D> Ru;
		auto SurfaceAt = [&](float U, float Vv) { return FVector(C.X + U * H.X, C.Y + Vv * H.Y, Spring + Rise * VaultShape(Rm.Ceil, U, Vv, bAlongX)) - Org; };
		auto NormalAt = [&](float U, float Vv)
		{
			const float E = 0.01f;
			const FVector Du = SurfaceAt(FMath::Min(U + E, 1.f), Vv) - SurfaceAt(FMath::Max(U - E, -1.f), Vv);
			const FVector Dv = SurfaceAt(U, FMath::Min(Vv + E, 1.f)) - SurfaceAt(U, FMath::Max(Vv - E, -1.f));
			FVector Nn = FVector::CrossProduct(Du, Dv).GetSafeNormal();
			return Nn.Z > 0.f ? -Nn : (Nn.IsNearlyZero() ? FVector(0, 0, -1) : Nn);
		};
		auto Rib = [&](TFunctionRef<FVector2D(float)> Along, float Width, float Depth)
		{
			TArray<FVector> Line, Down;
			for (int32 K = 0; K <= 40; ++K)
			{
				const float Tq = -FMath::Cos(PI * K / 40.f);
				const FVector2D Q = Along(Tq);
				Line.Add(SurfaceAt(Q.X, Q.Y)); Down.Add(NormalAt(FMath::Clamp(Q.X, -0.995f, 0.995f), FMath::Clamp(Q.Y, -0.995f, 0.995f)));
			}
			RD5AddRib(Rv, Rt, Rn, Ru, Line, Down, Width, Depth);
		};
		if (Rm.Ceil == 4)
		{
			Rib([](float Tq) { return FVector2D(Tq, Tq); }, 30.f, 22.f);
			Rib([](float Tq) { return FVector2D(Tq, -Tq); }, 30.f, 22.f);
		}
		else if (Rm.Ceil == 5)
		{
			const float Long = bAlongX ? H.X : H.Y;
			const int32 Na = FMath::Max(2, FMath::RoundToInt(Long * 2.f / 450.f));
			for (int32 K = 1; K < Na; ++K)
			{
				const float A = -1.f + 2.f * K / Na;
				if (bAlongX) Rib([A](float Tq) { return FVector2D(A, Tq); }, 36.f, 24.f);
				else Rib([A](float Tq) { return FVector2D(Tq, A); }, 36.f, 24.f);
			}
		}
		else if (Rm.Ceil == 6)
		{
			Rib([](float Tq) { return FVector2D(Tq, Tq); }, 26.f, 18.f);
			Rib([](float Tq) { return FVector2D(Tq, -Tq); }, 26.f, 18.f);
		}
		if (Rv.Num() > 0)
		{
			RD5Turn(Rt); M->CreateMeshSection(Sec, Rv, Rt, Rn, Ru, TArray<FColor>(), TArray<FProcMeshTangent>(), false);
			if (RibMat) M->SetMaterial(Sec, RibMat);
			++Sec;
		}
		++VaultMeshes;
	}
}
