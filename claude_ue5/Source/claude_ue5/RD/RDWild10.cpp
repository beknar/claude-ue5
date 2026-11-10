// The user's list of 2026-11-10 (docs/improvements10.txt), its sixth phase, the wilderness:
//   - "the buildings in the wilderness do not have an interior and there is no way to get inside or climb any stairs on the
//     outside": the wilds' houses (a village's, a lone house, a farmstead's farmhouse) laid as the village houses' open copies with
//     their doors on their hinges (F), a wooden floor set over the ground's highest point under the room, a stone plinth and steps
//     where the ground falls away, their furniture, a lamp and a fire, their plants cleared; the Old Watchtower walked into and
//     climbed: its doorway open, a spiral stair up to a stone floor at its second storey's top;
//   - "the small farm holdings should be noted on the large map": the farmsteads found as places are, on the map (RDWildTown.cpp's
//     TickWildPlaces, FindPlace);
//   - "what can be done to make the town / the wilderness more lively?": travellers on the roads between the towns, camped at night
//     round a fire beside the road; hens loose in a town's square that run from her; the town's watch with lanterns at night.
#include "RD/RDDungeonGenerator.h"
#include "RD/RDWild.h"
#include "RD/RDTown.h"
#include "RD/RDSection.h"
#include "RD/RDCombat.h"
#include "Components/StaticMeshComponent.h"
#include "Components/InstancedStaticMeshComponent.h"
#include "Components/HierarchicalInstancedStaticMeshComponent.h"
#include "Components/PointLightComponent.h"
#include "Components/SkeletalMeshComponent.h"
#include "ProceduralMeshComponent.h"
#include "Engine/StaticMesh.h"
#include "Engine/World.h"
#include "NiagaraFunctionLibrary.h"
#include "NiagaraComponent.h"
#include "NiagaraSystem.h"
#include "Kismet/GameplayStatics.h"

DEFINE_LOG_CATEGORY_STATIC(LogRDWild10, Log, All);

namespace
{
	UStaticMesh* RDW10Cube()
	{
		static TWeakObjectPtr<UStaticMesh> Cube;
		if (!Cube.IsValid()) Cube = LoadObject<UStaticMesh>(nullptr, TEXT("/Engine/BasicShapes/Cube.Cube"));
		return Cube.Get();
	}
	// (a point in a frame: its middle, yaw; local x, y)
	FVector RDW10At(const FVector& O, float Yaw, float X, float Y, float Z) { return O + FRotator(0.f, Yaw, 0.f).RotateVector(FVector(X, Y, 0.f)) + FVector(0, 0, Z); }
	float RDW10AngDiff(float A, float B) { return FMath::Abs(FMath::FindDeltaAngleDegrees(A, B)); }
}

bool ARDWildChunk::IsClear(const FVector& L) const
{
	for (const FClear& Cl : Clears) if (Cl.Contains(L)) return true;
	return false;
}

// ================================================================================================ the houses
bool ARDDungeonGenerator::FitWildHouse(ARDWildChunk* C, UStaticMeshComponent* Sm, uint32 Salt)
{
	if (!bWildHouseInsides || !C || !Sm || !Sm->GetStaticMesh()) return false;
	const FRDWildHouse* H = WildHouses.FindByPredicate([&](const FRDWildHouse& X) { return X.Mesh == Sm->GetStaticMesh(); });
	if (!H) return false;
	FRandomStream R((int32)Salt);
	const int32 Before = C->PlaceProps.Num();
	const float Sc = Sm->GetComponentScale().X;
	const float Yaw = Sm->GetComponentRotation().Yaw;
	// (the hermit's hut is a house at 0.6: its door too low for her, its doorways shut by their leaves, no inside)
	const bool bInside = Sc >= 0.75f;
	FTransform T = Sm->GetComponentTransform();
	const FVector2D Mn = H->InMin * Sc, Mx = H->InMax * Sc;
	const FVector Mid0 = T.GetLocation();
	const FVector2D RoomC = (Mn + Mx) * 0.5f, RoomH = (Mx - Mn) * 0.5f;
	// the ground under the room (its highest: the floor over it) and under the whole house (its lowest: the plinth down to it)
	float Gmax = -1e9f, Gmin = 1e9f;
	const FBox Bb = Sm->GetStaticMesh()->GetBoundingBox();
	for (int32 I = 0; I <= 4; ++I)
		for (int32 J = 0; J <= 4; ++J)
		{
			const FVector Pr = RDW10At(Mid0, Yaw, Mn.X + (Mx.X - Mn.X) * I / 4.f, Mn.Y + (Mx.Y - Mn.Y) * J / 4.f, 0.f);
			Gmax = FMath::Max(Gmax, WildGroundZ(Pr));
			const FVector Po = RDW10At(Mid0, Yaw, (Bb.Min.X + (Bb.Max.X - Bb.Min.X) * I / 4.f) * Sc, (Bb.Min.Y + (Bb.Max.Y - Bb.Min.Y) * J / 4.f) * Sc, 0.f);
			Gmin = FMath::Min(Gmin, WildGroundZ(Po));
		}
	if (bInside)
	{
		// (the house on the room's highest ground: the floor over every bit of it, no grass or earth through the boards)
		FVector Loc = Mid0; Loc.Z = Gmax + 2.f;
		Sm->SetWorldLocation(Loc);
		T = Sm->GetComponentTransform();
	}
	const float Base = T.GetLocation().Z;
	const FVector O = FVector(T.GetLocation().X, T.GetLocation().Y, Base);
	ARDWildChunk::FHouse Rec; Rec.C = O; Rec.H = RoomH; Rec.Yaw = Yaw; Rec.FloorZ = Base + 1.f; Rec.Of = Sm->GetStaticMesh()->GetName();
	auto Mesh = [&](UStaticMesh* M, const FTransform& W, bool bCollide, UMaterialInterface* Mat = nullptr) -> UStaticMeshComponent*
	{
		if (!M) return nullptr;
		UStaticMeshComponent* Pc = NewObject<UStaticMeshComponent>(C);
		Pc->SetStaticMesh(M);
		Pc->SetupAttachment(C->Ground);
		Pc->SetWorldTransform(W);
		if (Mat) Pc->SetMaterial(0, Mat);
		if (!bCollide) Pc->SetCollisionEnabled(ECollisionEnabled::NoCollision);
		Pc->RegisterComponent();
		Pc->SetWorldTransform(W);
		C->PlaceProps.Add(Pc);
		return Pc;
	};
	// ---- its doors: each leaf on a pivot at its hinge (the house's frame and scale); outward, the way its wall faces
	for (const FRDWildHouseDoor& D : H->Doors)
	{
		if (!D.Leaf) continue;
		USceneComponent* Pv = NewObject<USceneComponent>(C);
		Pv->SetupAttachment(Sm);
		Pv->SetRelativeLocation(D.Pivot);
		Pv->RegisterComponent();
		UStaticMeshComponent* L = NewObject<UStaticMeshComponent>(C);
		L->SetStaticMesh(D.Leaf);
		L->SetupAttachment(Pv);
		L->RegisterComponent();
		C->PlaceProps.Add(L);
		// (a door the house's data puts on an X wall only: the outward way, the swing, the steps and the back wall are read from it;
		// one on another wall stays shut (PR #43's review))
		if (!bInside || FMath::Abs(D.Pivot.X) < 0.8f * FMath::Max(FMath::Abs(H->InMin.X), FMath::Abs(H->InMax.X))) continue;
		ARDWildChunk::FDoor Dr;
		Dr.Pivot = Pv;
		Dr.At = T.TransformPosition(D.Pivot + FVector(0.f, D.Width * 0.5f, 0.f));
		// (the leaf runs along Y from its hinge, the way its width's sign says (916: interactive.json's leaf_dir in Unreal's axes);
		// open, it swings out of the house: the quarter turn that puts it along its wall's outward way)
		const FVector Ld(0.f, D.Width >= 0.f ? 1.f : -1.f, 0.f), Outw(D.Pivot.X > 0.f ? 1.f : -1.f, 0.f, 0.f);
		Dr.OutYaw = FVector::DotProduct(FRotator(0.f, 90.f, 0.f).RotateVector(Ld), Outw) > 0.f ? 90.f : -90.f;
		Dr.OpenYaw = Dr.OutYaw;
		Dr.Out = T.TransformVectorNoScale(Outw);
		C->Doors.Add(Dr);
		++Rec.Doors;
		// (a step or two before a door where the ground outside lies lower than the sill)
		const float Out = D.Pivot.X > 0.f ? 1.f : -1.f;
		const FVector Fr = T.TransformPosition(FVector(D.Pivot.X + Out * 60.f / Sc, D.Pivot.Y + D.Width * 0.5f, 0.f));
		const float Drop = Base - WildGroundZ(Fr);
		if (Drop > 30.f)
		{
			const int32 N = FMath::Min(FMath::CeilToInt(Drop / 28.f), 6);
			for (int32 K = 0; K < N; ++K)
			{
				const float Top = Base - Drop * K / N;
				const float Depth = 42.f;
				const FVector Lc = FVector(D.Pivot.X * Sc + Out * (Depth * (K + 0.5f) + 8.f), (D.Pivot.Y + D.Width * 0.5f) * Sc, 0.f);
				const FVector W = RDW10At(O, Yaw, Lc.X, Lc.Y, 0.f);
				const float Z0 = WildGroundZ(W) - 20.f;
				Mesh(RDW10Cube(), FTransform(FRotator(0.f, Yaw, 0.f), FVector(W.X, W.Y, (Top + Z0) * 0.5f), FVector(Depth / 100.f, 2.f, FMath::Max(Top - Z0, 5.f) / 100.f)), true, WildPlinthMaterial);
			}
		}
	}
	if (!bInside) { C->Houses.Add(Rec); return true; }
	// ---- the plinth: stone from the floor down to the lowest ground under the house, where the ground falls away
	if (Base - Gmin > 8.f)
	{
		const FVector Bc = (Bb.Min + Bb.Max) * 0.5f * Sc, Be = (Bb.Max - Bb.Min) * Sc;
		const float Z0 = Gmin - 30.f;
		Mesh(RDW10Cube(), FTransform(FRotator(0.f, Yaw, 0.f), RDW10At(O, Yaw, Bc.X, Bc.Y, 0.f) + FVector(0, 0, (Z0 - Base) * 0.5f - 1.f),
			FVector((Be.X - 20.f) / 100.f, (Be.Y - 20.f) / 100.f, (Base - Z0) / 100.f)), true, WildPlinthMaterial);
	}
	// ---- its floor: the dungeon's wooden floor tiles over the room, stretched to fit it
	if (const FRDPiece* Fp = Piece(TEXT("Floor_Wood")))
	{
		UInstancedStaticMeshComponent* Fl = NewObject<UInstancedStaticMeshComponent>(C);
		Fl->SetStaticMesh(Fp->Mesh);
		Fl->SetupAttachment(C->Ground);
		Fl->RegisterComponent();
		const float Ts = FMath::Max((float)Fp->Size.X, 100.f);
		const int32 Nx = FMath::Max(1, FMath::CeilToInt((Mx.X - Mn.X) / Ts)), Ny = FMath::Max(1, FMath::CeilToInt((Mx.Y - Mn.Y) / Ts));
		const float Sx = (Mx.X - Mn.X) / (Nx * Ts), Sy = (Mx.Y - Mn.Y) / (Ny * Ts);
		for (int32 I = 0; I < Nx; ++I)
			for (int32 J = 0; J < Ny; ++J)
			{
				const FVector W = RDW10At(O, Yaw, Mn.X + (I + 0.5f) * Ts * Sx, Mn.Y + (J + 0.5f) * Ts * Sy, 1.f);
				Fl->AddInstance(Fp->Adjust * FTransform(FRotator(0.f, Yaw, 0.f), W, FVector(Sx, Sy, 1.f)), true);
			}
	}
	// ---- its furniture: the dungeon's pieces by name, against its back wall (across from the first door) and round a table
	const float Ds = H->Doors.Num() > 0 && H->Doors[0].Pivot.X < 0.f ? -1.f : 1.f;          // (the door's wall: +X or -X)
	const float Xb = Ds > 0.f ? Mn.X : Mx.X;                                                // (the back wall)
	const float Face = Ds > 0.f ? 0.f : 180.f;                                              // (a piece's front (+X) into the room)
	auto Put = [&](FName Name, float X, float Y, float YawL) -> bool
	{
		const FRDPiece* P = Piece(Name);
		if (!P || !P->Mesh) return false;
		const FVector W = RDW10At(O, Yaw, X, Y, 1.f);
		if (Mesh(P->Mesh, P->Adjust * FTransform(FRotator(0.f, Yaw + YawL, 0.f), W), P->bCollision, P->Material)) { ++Rec.Furniture; return true; }
		return false;
	};
	const float W = Mx.X - Mn.X;
	if (const FRDPiece* Fp = Piece(TEXT("Fireplace")))
	{
		Put(TEXT("Fireplace"), Xb + Ds * (Fp->Size.X * 0.5f + 2.f), RoomC.Y, Face);
		const FVector F = RDW10At(O, Yaw, Xb + Ds * 45.f, RoomC.Y, 22.f);
		if (WildFireFx) UNiagaraFunctionLibrary::SpawnSystemAttached(WildFireFx, C->Ground, NAME_None, F - C->Ground->GetComponentLocation(), FRotator::ZeroRotator, FVector(0.7f), EAttachLocation::KeepRelativeOffset, true, ENCPoolMethod::None);
	}
	float BedY = Mx.Y - 70.f;
	if (const FRDPiece* Bp = Piece(TEXT("Bed")))
	{
		BedY = Mx.Y - Bp->Size.Y * 0.5f - 25.f;
		Put(TEXT("Bed"), Xb + Ds * (Bp->Size.X * 0.5f + 6.f), BedY, Face);
		if (const FRDPiece* Cp = Piece(TEXT("Chest"))) Put(TEXT("Chest"), Xb + Ds * (Bp->Size.X + 14.f + Cp->Size.X * 0.5f), BedY, Face);
	}
	Put(TEXT("TableLong"), Xb + Ds * W * 0.55f, Mn.Y + (Mx.Y - Mn.Y) * 0.32f, 0.f);
	if (const FRDPiece* Tp = Piece(TEXT("TableLong")))
		for (const float Sd : { -1.f, 1.f }) Put(TEXT("Bench"), Xb + Ds * W * 0.55f + Sd * (Tp->Size.X * 0.5f + 30.f), Mn.Y + (Mx.Y - Mn.Y) * 0.32f, 0.f);
	Put(TEXT("Barrel"), Xb + Ds * 45.f, Mn.Y + 45.f, R.FRandRange(0.f, 360.f));
	Put(TEXT("Crate"), Xb + Ds * 45.f, Mn.Y + 125.f, Face);
	Put(TEXT("Wardrobe"), Xb + Ds * W * 0.62f, Mx.Y - 32.f, -90.f);
	// ---- a lamp under its roof (the fire's glow is small)
	{
		UPointLightComponent* Lt = NewObject<UPointLightComponent>(C);
		Lt->SetupAttachment(C->Ground);
		Lt->SetIntensityUnits(ELightUnits::Candelas);
		Lt->SetIntensity(30.f);
		Lt->SetAttenuationRadius(FMath::Max(RoomH.X, RoomH.Y) * 1.6f);
		Lt->SetLightColor(FLinearColor(1.f, 0.72f, 0.45f));
		Lt->SetCastShadows(false);
		Lt->RegisterComponent();
		Lt->SetWorldLocation(RDW10At(O, Yaw, RoomC.X, RoomC.Y, 290.f));
		Rec.bLit = true;
	}
	// ---- its ground kept clear: the plants in it taken out, the near grass to come left out; the place's own props in it (a lone
	// house's fences and hay, a village's carts laid before it) taken away
	const FTransform Gt = C->Ground->GetComponentTransform();
	const FVector Lc = Gt.InverseTransformPosition(RDW10At(O, Yaw, RoomC.X, RoomC.Y, 0.f));
	ARDWildChunk::FClear Cl; Cl.C = FVector2D(Lc.X, Lc.Y); Cl.H = RoomH + FVector2D(40.f, 40.f); Cl.Yaw = Yaw - Gt.Rotator().Yaw;
	C->Clears.Add(Cl);
	const float Rr = FMath::Max(Cl.H.X, Cl.H.Y) * 1.5f;
	const FBox Wb(O - FVector(Rr, Rr, 2000.f), O + FVector(Rr, Rr, 2000.f));
	int32 Gone = 0;
	auto Clean = [&](UHierarchicalInstancedStaticMeshComponent* Hm)
	{
		if (!Hm) return;
		const TArray<int32> Ix = Hm->GetInstancesOverlappingBox(Wb, true);
		TArray<int32> Out;
		for (const int32 I : Ix)
		{
			FTransform It; if (!Hm->GetInstanceTransform(I, It, true)) continue;
			if (C->IsClear(Gt.InverseTransformPosition(It.GetLocation()))) Out.Add(I);
		}
		if (Out.Num() > 0) { Hm->RemoveInstances(Out); Gone += Out.Num(); }
	};
	for (UHierarchicalInstancedStaticMeshComponent* Hm : C->Foliage) Clean(Hm);
	for (UHierarchicalInstancedStaticMeshComponent* Hm : C->NearFoliage) Clean(Hm);
	{
		// (the place's own props laid before this house (indices under Before) within a metre of its room: taken away)
		for (int32 K = FMath::Min(Before, C->PlaceProps.Num()) - 1; K >= 0; --K)
		{
			UStaticMeshComponent* P = C->PlaceProps[K];
			if (!P || P == Sm) continue;
			if (Cl.Contains(Gt.InverseTransformPosition(P->GetComponentLocation()), 110.f)) { P->DestroyComponent(); C->PlaceProps.RemoveAt(K); ++Rec.PropsGone; }
		}
	}
	C->Houses.Add(Rec);
	UE_LOG(LogRDWild10, Verbose, TEXT("RDWILDHOUSE %s at (%.0f, %.0f, %.0f): %d doors, %d furniture, %d plants cleared"), *Rec.Of, O.X, O.Y, O.Z, Rec.Doors, Rec.Furniture, Gone);
	return true;
}

// ================================================================================================ the watchtower climbed
void ARDDungeonGenerator::FitWildTower(ARDWildChunk* C, const FVector& Mid, float Z0, float Hs, float DoorYaw, float KeptYaw)
{
	if (!C) return;
	const FRDPiece* Cp = Piece(TEXT("Town.Collider"));
	const FRDPiece* Sp = Piece(TEXT("Town.Spiral"));
	auto Add = [&](const FRDPiece* P, const FTransform& W, bool bHide)
	{
		if (!P || !P->Mesh) return (UStaticMeshComponent*)nullptr;
		UStaticMeshComponent* M = NewObject<UStaticMeshComponent>(C);
		M->SetStaticMesh(P->Mesh);
		M->SetupAttachment(C->Ground);
		if (bHide) M->SetHiddenInGame(true);
		M->RegisterComponent();
		M->SetWorldTransform(P->Adjust * W);
		C->PlaceProps.Add(M);
		return M;
	};
	// (its collision: 32 hidden boxes round the ring (the town towers' way), the doorway's left open below its lintel)
	constexpr float RMid = 284.f;
	if (Cp)
		for (int32 J = 0; J < 32; ++J)
		{
			const float A = DoorYaw + 5.625f + 11.25f * J;
			const FVector P = Mid + FRotator(0, A, 0).RotateVector(FVector(RMid, 0, 0));
			auto Box = [&](float Za, float Zb)
			{
				if (Zb - Za < 5.f) return;
				Add(Cp, FTransform(FRotator(0, A, 0), FVector(P.X, P.Y, Za), FVector(0.6f, 0.62f, (Zb - Za) / 100.f)), true);
			};
			if (RDW10AngDiff(A, DoorYaw) < 11.25f) { Box(Z0 + 255.f, Z0 + 2.f * Hs); }
			else Box(Z0, Z0 + 2.f * Hs);
			// (the broken third storey: its two quarters left standing (from KeptYaw, 180 degrees) (PR #43's review: walked through, she fell))
			if (KeptYaw > -1e5f && FMath::Fmod(FMath::Fmod(A - KeptYaw, 360.f) + 360.f, 360.f) < 180.f) Box(Z0 + 2.f * Hs, Z0 + 3.f * Hs);
		}
	// (the floor at the doorway: the ground's highest under the ring; the spiral from it to the second storey's top, clockwise from
	// just past the door)
	// (the floor at the doorway's sill: the tower stands on the highest ground under its ring (RDWildPlaces); a stone footing down to
	// the lowest where it falls)
	const float Gf = Z0 + 2.f;
	float Gmin = 1e9f;
	for (int32 K = 0; K < 8; ++K) Gmin = FMath::Min(Gmin, WildGroundZ(Mid + FRotator(0, 45.f * K, 0).RotateVector(FVector(330.f, 0, 0))));
	const float Top = Z0 + 2.f * Hs;
	UMaterialInterface* Stone = nullptr;
	if (const FRDPiece* Fs = Piece(TEXT("Floor_Stone"))) Stone = Fs->Material ? Fs->Material.Get() : (Fs->Mesh ? Fs->Mesh->GetMaterial(0) : nullptr);
	// (a stone disc under the stair: the ground inside levelled)
	auto Sector = [&](UProceduralMeshComponent* Pm, int32 Sec, float R0, float R1, float A0, float A1, float Z, float Th)
	{
		TArray<FVector> V; TArray<int32> Tr; TArray<FVector> N; TArray<FVector2D> Uv;
		const int32 Na = FMath::Max(2, FMath::CeilToInt((A1 - A0) / 7.5f));
		auto Pt = [&](float R, float A, float Zz) { return FVector(Mid.X + R * FMath::Cos(FMath::DegreesToRadians(A)), Mid.Y + R * FMath::Sin(FMath::DegreesToRadians(A)), Zz) - C->Ground->GetComponentLocation(); };
		for (int32 F = 0; F < 2; ++F)
		{
			const float Zz = F == 0 ? Z : Z - Th;
			const int32 B = V.Num();
			for (int32 I = 0; I <= Na; ++I)
			{
				const float A = A0 + (A1 - A0) * I / Na;
				for (const float R : { R0, R1 }) { const FVector P = Pt(R, A, Zz); V.Add(P); N.Add(F == 0 ? FVector::UpVector : -FVector::UpVector); Uv.Add(FVector2D(P.X, P.Y) / 150.f); }
			}
			for (int32 I = 0; I < Na; ++I)
			{
				const int32 A_ = B + I * 2, B_ = A_ + 1, C_ = A_ + 2, D_ = A_ + 3;
				// (the procedural mesh draws a face whose cross(V1 - V0, V2 - V0) points away from the viewer: down for the top)
				if (F == 0) { Tr.Append({ A_, B_, C_, C_, B_, D_ }); } else { Tr.Append({ A_, C_, B_, C_, D_, B_ }); }
			}
		}
		Pm->CreateMeshSection(Sec, V, Tr, N, Uv, {}, {}, true);
		if (Stone) Pm->SetMaterial(Sec, Stone);
	};
	UProceduralMeshComponent* Fl = NewObject<UProceduralMeshComponent>(C);
	Fl->SetupAttachment(C->Ground);
	Fl->bUseComplexAsSimpleCollision = true;
	Fl->RegisterComponent();
	Sector(Fl, 0, 0.f, 300.f, 0.f, 360.f, Gf, 30.f);
	if (Cp && Z0 - Gmin > 8.f)
		if (UStaticMeshComponent* Ft = Add(Cp, FTransform(FRotator(0, DoorYaw, 0), FVector(Mid.X, Mid.Y, Gmin - 30.f), FVector(6.6f, 6.6f, (Z0 + 1.f - (Gmin - 30.f)) / 100.f)), false))
			if (Stone) Ft->SetMaterial(0, Stone);
	// (steps out of the doorway where the ground before it lies lower than the floor (on a slope its edge was too tall a step: 888
	// tower10 stopped her at the door))
	{
		const FVector Dw = FRotator(0, DoorYaw, 0).RotateVector(FVector(1, 0, 0));
		const float Drop = Gf - WildGroundZ(Mid + Dw * 390.f);
		if (Drop > 25.f)
			for (int32 K = 0, N = FMath::Min(FMath::CeilToInt(Drop / 26.f), 8); K < N; ++K)
			{
				const float StepTop = Gf - Drop * K / N, R0 = 330.f + 40.f * K;
				const FVector P = Mid + Dw * (R0 + 20.f);
				const float Zb = WildGroundZ(P) - 25.f;
				if (Cp) if (UStaticMeshComponent* St = Add(Cp, FTransform(FRotator(0, DoorYaw, 0), FVector(P.X, P.Y, Zb), FVector(0.42f, 1.3f, FMath::Max(StepTop - Zb, 5.f) / 100.f)), false))
					if (Stone) St->SetMaterial(0, Stone);
			}
	}
	int32 Pieces_ = 0;
	float Ys = DoorYaw - 22.f;
	if (Sp && Top - Gf > 150.f)
	{
		const float SpZ = FMath::Max((float)Sp->Size.Z, 50.f);
		const int32 Qn = FMath::Max(4, FMath::RoundToInt((Top - Gf) / 100.f));
		const float Qh = (Top - Gf) / Qn, Sa = DoorYaw - 22.f;
		for (int32 K = 0; K < Qn; ++K)
			if (Add(Sp, FTransform(FRotator(0, Sa - 90.f * K, 0), FVector(Mid.X, Mid.Y, Gf + Qh * K), FVector(1.f, 1.f, Qh / SpZ)), false)) ++Pieces_;
		Ys = Sa - 90.f * (Qn - 1);
		// the floor at the top: the ring outside the stairwell all round, and the landing (the quarter past the last step) within
		// it; the stairwell (its last three quarter turns) open for her head; a low wall round the open well
		Sector(Fl, 1, 230.f, 300.f, 0.f, 360.f, Top, 25.f);
		Sector(Fl, 2, 0.f, 230.f, Ys - 180.f, Ys - 90.f, Top, 25.f);
		if (Cp)
			for (float A = Ys - 90.f; A <= Ys + 180.f + 0.1f; A += 15.f)
			{
				const FVector P = Mid + FRotator(0, A + 7.5f, 0).RotateVector(FVector(236.f, 0, 0));
				UStaticMeshComponent* Wl = Add(Cp, FTransform(FRotator(0, A + 7.5f, 0), FVector(P.X, P.Y, Top), FVector(0.16f, 0.64f, 1.f)), false);
				if (Wl && Stone) Wl->SetMaterial(0, Stone);
			}
	}
	WildTowerLines.Add(FString::Printf(TEXT("tower|%.0f|%.0f|%.0f|%.0f|%d|%.0f|%.0f|%.0f"), Mid.X, Mid.Y, Gf, Top, Pieces_, DoorYaw, Ys, KeptYaw));
}

// ================================================================================================ the doors
ARDWildChunk* ARDDungeonGenerator::WildDoorNear(const FVector& From, float Reach, int32& Index) const
{
	ARDWildChunk* Best = nullptr; float Bd = Reach; Index = -1;
	for (const auto& Kv : WildChunks)
	{
		ARDWildChunk* C = Kv.Value;
		if (!IsValid(C) || !C->bNear) continue;
		for (int32 I = 0; I < C->Doors.Num(); ++I)
		{
			const ARDWildChunk::FDoor& D = C->Doors[I];
			if (!D.Pivot.IsValid()) continue;
			const float Dd = FVector::Dist2D(D.At, From);
			if (Dd < Bd && FMath::Abs(D.At.Z - From.Z) < 220.f) { Bd = Dd; Best = C; Index = I; }
		}
	}
	return Best;
}

FString ARDDungeonGenerator::WildDoorDescribe(const FVector& From) const
{
	if (!bWild || !bWildHouseInsides) return FString();
	int32 I = -1;
	if (const ARDWildChunk* C = WildDoorNear(From, 190.f, I)) return C->Doors[I].Target > 0.5f ? TEXT("close the door") : TEXT("open the door");
	return FString();
}

FString ARDDungeonGenerator::WildDoorInteract(const FVector& From)
{
	if (!bWild || !bWildHouseInsides) return FString();
	int32 I = -1;
	if (ARDWildChunk* C = WildDoorNear(From, 190.f, I))
	{
		ARDWildChunk::FDoor& D = C->Doors[I];
		// (opened, it swings away from her: in from outside, out from inside (888 houses10: swung out at her 1.1 m before it, the leaf
		// shut her out); the way is chosen while it is shut)
		if (D.Target < 0.5f && D.Alpha < 0.05f) D.OpenYaw = FVector::DotProduct(From - D.At, D.Out) > 0.f ? -D.OutYaw : D.OutYaw;
		D.Target = D.Target > 0.5f ? 0.f : 1.f;
		return TEXT("door");
	}
	return FString();
}

void ARDDungeonGenerator::TickWildDoors(float Dt)
{
	for (const auto& Kv : WildChunks)
	{
		ARDWildChunk* C = Kv.Value;
		if (!IsValid(C)) continue;
		for (ARDWildChunk::FDoor& D : C->Doors)
		{
			if (FMath::IsNearlyEqual(D.Alpha, D.Target) || !D.Pivot.IsValid()) continue;
			D.Alpha = FMath::FInterpConstantTo(D.Alpha, D.Target, Dt, 1.4f);
			D.Pivot->SetRelativeRotation(FRotator(0.f, D.OpenYaw * D.Alpha, 0.f));
		}
	}
}

TArray<FString> ARDDungeonGenerator::GetWildHouseLines() const
{
	TArray<FString> Out;
	for (const auto& Kv : WildChunks)
	{
		const ARDWildChunk* C = Kv.Value;
		if (!IsValid(C)) continue;
		for (const ARDWildChunk::FHouse& H : C->Houses)
			Out.Add(FString::Printf(TEXT("house|%d|%d|%.0f|%.0f|%.0f|%d|%d|%d|%.0f|%s|%.0f|%.0f|%.1f"), C->Coord.X, C->Coord.Y, H.C.X, H.C.Y, H.C.Z, H.Doors, H.Furniture, H.bLit ? 1 : 0, H.FloorZ, *H.Of, H.H.X, H.H.Y, H.Yaw));
		for (const ARDWildChunk::FDoor& D : C->Doors)
			Out.Add(FString::Printf(TEXT("door|%.0f|%.0f|%.0f|%.2f|%.0f"), D.At.X, D.At.Y, D.At.Z, D.Alpha, D.Target));
	}
	return Out;
}

TArray<FString> ARDDungeonGenerator::GetWildTowerLines() const { return WildTowerLines; }

// ================================================================================================ the travellers on the roads
void ARDTownsfolk::TickRoad(float Dt)
{
	const FVector L = GetActorLocation();
	if (RoadPath.Num() > 0)
	{
		if (Act == 3) { Act = 0; SetProp(NAME_None); }
		FVector D = RoadPath[0] - L; D.Z = 0.f;
		if (D.Size() < 50.f) { RoadPath.RemoveAt(0); return; }
		FVector N = L + D.GetSafeNormal() * FMath::Min(Speed * Dt, D.Size());
		if (Gen) N.Z = Gen->WildGroundZ(N) + 92.f;
		SetActorLocation(N, false);
		const FRotator Want = D.Rotation();
		SetActorRotation(FRotator(0.f, FMath::RInterpConstantTo(GetActorRotation(), Want, Dt, 240.f).Yaw, 0.f));
		SetClip(true);
		return;
	}
	if (!StandWork.IsNone())
	{
		if (UAnimationAsset* Wc = WorkClip(StandWork)) PlayAnim(Wc, 1.f); else SetClip(false);
		SetActorRotation(FRotator(0.f, FMath::RInterpConstantTo(GetActorRotation(), FRotator(0.f, HomeYaw, 0.f), Dt, 180.f).Yaw, 0.f));
		return;
	}
	SetClip(false);
}

void ARDTownsfolk::SetLantern(bool bOn)
{
	if (bOn == bLanternOn) return;
	// (at work it holds its work's prop: no lantern then; off, only the lantern goes (PR #43's review: it took a work prop with it))
	if (bOn && Act == 3) return;
	if (!bOn) { SetProp(NAME_None); return; }          // (SetProp ends the lantern and its light)
	SetProp(TEXT("Lantern"));
	bLanternOn = true;
	if (!PropComp) { bLanternOn = false; return; }
	UPointLightComponent* Lt = NewObject<UPointLightComponent>(this);
	Lt->SetupAttachment(PropComp);
	Lt->SetIntensityUnits(ELightUnits::Candelas);
	Lt->SetIntensity(12.f);
	Lt->SetAttenuationRadius(900.f);
	Lt->SetLightColor(FLinearColor(1.f, 0.66f, 0.35f));
	Lt->SetCastShadows(false);
	Lt->RegisterComponent();
	Lt->SetRelativeLocation(FVector(0, 0, -15.f));
	LanternLight = Lt;
}

void ARDDungeonGenerator::TickWild10(float Dt, const FVector& Her)
{
	TickWildDoors(Dt);
	TravellerClock += Dt; LanternClock += Dt;
	if (bWild && bWildTravellers && TravellerClock >= 1.f) { TravellerClock = 0.f; TickWildTravellers(Her); }
	if (bNightLanterns && LanternClock >= 2.f) { LanternClock = 0.f; TickNightLanterns(); }
}

namespace
{
	// (the road's nearest point to P (world metres): its segment and how far along it)
	bool RDW10NearestOnRoad(const FRDWildWorld::FRoad& Rd, const FVector2D& P, int32& Seg, float& Dm)
	{
		Seg = -1; Dm = 1e30f;
		for (int32 I = 0; I + 1 < Rd.P.Num(); ++I)
		{
			const FVector2D A = Rd.P[I], B = Rd.P[I + 1], Ab = B - A;
			const float T = FMath::Clamp((float)FVector2D::DotProduct(P - A, Ab) / FMath::Max((float)Ab.SizeSquared(), 1e-3f), 0.f, 1.f);
			const float D = (float)FVector2D::Distance(A + Ab * T, P);
			if (D < Dm) { Dm = D; Seg = I; }
		}
		return Seg >= 0;
	}
}

void ARDDungeonGenerator::TickWildTravellers(const FVector& Her)
{
	if (!IsWildReady()) return;
	const FVector2D Hm(Her.X / 100.0, Her.Y / 100.0);
	const float H = GetTownHour();
	const bool bNight = H >= 21.f || H < 5.5f;
	// (a group far from her goes: its folk and its camp)
	for (int32 G = WildTravellers.Num() - 1; G >= 0; --G)
	{
		FTraveller& T = WildTravellers[G];
		ARDTownsfolk* Lead = T.Folk.Num() > 0 ? T.Folk[0].Get() : nullptr;
		if (!Lead || FVector::Dist2D(Lead->GetActorLocation(), Her) > WildTravellerM * 130.f)
		{
			for (auto& F : T.Folk) if (F.IsValid()) F->Destroy();
			for (auto& B : T.CampBits) if (B.IsValid()) B->DestroyComponent();
			WildTravellers.RemoveAt(G);
		}
	}
	// (each walking group's way along its road topped up ahead; at night it camps beside the road, in the morning it goes on)
	for (FTraveller& T : WildTravellers)
	{
		if (!Wild->Roads.IsValidIndex(T.Road)) continue;
		const FRDWildWorld::FRoad& Rd = Wild->Roads[T.Road];
		if (bNight && !T.bCamped) { CampTravellers(T); continue; }
		if (!bNight && T.bCamped)
		{
			T.bCamped = false;
			for (auto& B : T.CampBits) if (B.IsValid()) B->DestroyComponent();
			T.CampBits.Reset();
			for (auto& F : T.Folk) if (F.IsValid()) { F->SetStandWork(NAME_None, NAME_None); F->Act = 0; }
		}
		if (T.bCamped) continue;
		ARDTownsfolk* Lead = T.Folk.Num() > 0 ? T.Folk[0].Get() : nullptr;
		if (!Lead || Lead->RoadPath.Num() > 3) continue;
		// (the next points of its road; at its end the way back)
		int32 S = T.Seg;
		TArray<FVector2D> Next;
		for (int32 K = 0; K < 8; ++K)
		{
			S += T.Dir;
			if (!Rd.P.IsValidIndex(S)) { T.Dir = -T.Dir; S += 2 * T.Dir; if (!Rd.P.IsValidIndex(S)) break; }
			Next.Add(Rd.P[S]);
		}
		T.Seg = S;
		for (int32 F = 0; F < T.Folk.Num(); ++F)
		{
			ARDTownsfolk* Fk = T.Folk[F].Get();
			if (!Fk) continue;
			// (side by side and a little behind each other, on the road's right)
			for (int32 K = 0; K < Next.Num(); ++K)
			{
				// (from the end of its own way (PR #43's review: from where it stood, a follower's queue doubled back))
				const FVector Ql = Fk->RoadPath.Num() > 0 ? Fk->RoadPath.Last() : Fk->GetActorLocation();
				const FVector2D A = K == 0 ? FVector2D(Ql.X / 100.0, Ql.Y / 100.0) : Next[K - 1];
				const FVector2D Dd = (Next[K] - A).GetSafeNormal(), Rt(-Dd.Y, Dd.X);
				const FVector2D Pm = Next[K] + Rt * (1.2f + 0.9f * F) - Dd * (1.4f * F);
				Fk->RoadPath.Add(FVector(Pm.X * 100.0, Pm.Y * 100.0, 0.0));
			}
		}
	}
	// (new groups up to the most, on a road within reach of her, out of sight along it (150 to 350 m off), never in a town)
	if (WildTravellers.Num() >= WildTravellerGroups || bNight) return;
	for (int32 Ri = 0; Ri < Wild->Roads.Num() && WildTravellers.Num() < WildTravellerGroups; ++Ri)
	{
		const FRDWildWorld::FRoad& Rd = Wild->Roads[Ri];
		if (Rd.P.Num() < 4 || !Rd.Box.ExpandBy(WildTravellerM).IsInside(Hm)) continue;
		if (WildTravellers.ContainsByPredicate([Ri](const FTraveller& T) { return T.Road == Ri; })) continue;
		int32 Seg; float Dm;
		if (!RDW10NearestOnRoad(Rd, Hm, Seg, Dm) || Dm > WildTravellerM) continue;
		const uint32 Seed = HashCombine((uint32)Ri, (uint32)(++WildTravellersMade) * 2654435761u);
		FRandomStream R((int32)Seed);
		const int32 Dir = R.FRand() < 0.5f ? 1 : -1;
		// (out along the road from her nearest point)
		int32 S = Seg; float Along = 0.f;
		const float Want = R.FRandRange(150.f, 350.f);
		while (Rd.P.IsValidIndex(S + Dir) && Along < Want) { Along += (float)FVector2D::Distance(Rd.P[S], Rd.P[S + Dir]); S += Dir; }
		const FVector2D At = Rd.P[S];
		bool bNearTown = false;
		for (const FRDWildTown& Tw : Wild->Towns) if (FVector2D::Distance(Tw.Site, At) < 1300.0) bNearTown = true;
		if (bNearTown || FVector2D::Distance(At, Hm) < 120.0) continue;
		// (its folk: the travelling roles' shared people)
		TArray<int32> Pool;
		for (int32 D = 0; D < Townsfolk.Num(); ++D)
			if (Townsfolk[D].Mesh && Townsfolk[D].Town.IsEmpty() && Townsfolk[D].WorkClips.Contains(TEXT("SitTalk")) && WildTravellerRoles.Contains(FName(*StaticEnum<ERDTownRole>()->GetNameStringByValue((int64)Townsfolk[D].Role)))) Pool.Add(D);
		if (Pool.Num() == 0) return;
		FTraveller T; T.Road = Ri; T.Seg = S; T.Dir = -Dir; T.Seed = Seed;
		const FRDWildTown* To = Wild->Towns.IsValidIndex(T.Dir > 0 ? Rd.To : Rd.From) ? &Wild->Towns[T.Dir > 0 ? Rd.To : Rd.From] : nullptr;
		T.Name = To ? To->Name : FString(TEXT("the next town"));
		const int32 N = R.RandRange(2, 3);
		FActorSpawnParameters Sp; Sp.SpawnCollisionHandlingOverride = ESpawnActorCollisionHandlingMethod::AlwaysSpawn;
		for (int32 K = 0; K < N; ++K)
		{
			const int32 D = Pool[R.RandRange(0, Pool.Num() - 1)];
			FVector P(At.X * 100.0 + R.FRandRange(-150.f, 150.f), At.Y * 100.0 + R.FRandRange(-150.f, 150.f), 0.0);
			P.Z = WildGroundZ(P) + 92.f;
			ARDTownsfolk* F = GetWorld()->SpawnActor<ARDTownsfolk>(ARDTownsfolk::StaticClass(), FTransform(FRotator(0, R.FRandRange(0.f, 360.f), 0), P), Sp);
			if (!F) continue;
			F->Init(this, nullptr, D, P, 0.f, 0.f, HashCombine(Seed, (uint32)K * 7919u));
			F->bRoadWalker = true;
			F->SetTitle(FString::Printf(TEXT("%s on the road to %s"), *F->Title, *T.Name));
			T.Folk.Add(F);
		}
		// (the group at its slowest's pace: they walk together (PR #43's review: a slower one fell further behind at every top-up))
		float Pace = 1e9f; for (auto& F : T.Folk) if (F.IsValid()) Pace = FMath::Min(Pace, F->Speed);
		for (auto& F : T.Folk) if (F.IsValid()) F->Speed = Pace;
		if (T.Folk.Num() > 0) { WildTravellers.Add(T); UE_LOG(LogRDWild10, Log, TEXT("RDTRAVELLERS %d on the road to %s at (%.0f, %.0f) m"), T.Folk.Num(), *T.Name, At.X, At.Y); }
	}
}

void ARDDungeonGenerator::CampTravellers(FTraveller& T)
{
	ARDTownsfolk* Lead = T.Folk.Num() > 0 ? T.Folk[0].Get() : nullptr;
	if (!Lead || !Wild->Roads.IsValidIndex(T.Road)) return;
	T.bCamped = true;
	// (its camp 7 m off the road's side, where the leader is: a fire on its stones, logs round it to sit on, the fire's light)
	const FRDWildWorld::FRoad& Rd = Wild->Roads[T.Road];
	const FVector L = Lead->GetActorLocation();
	const int32 S = FMath::Clamp(T.Seg, 0, Rd.P.Num() - 2);
	const FVector2D Dd = (Rd.P[S + 1] - Rd.P[S]).GetSafeNormal(), Rt(-Dd.Y, Dd.X);
	// (the side of the road with no field and no water (a camp in a bean field had the crop through its fire); else on its verge)
	FVector2D Side = Rt * 7.0; bool bSide = false;
	for (const float Sg : { 1.f, -1.f })
	{
		FRDWSample Q; Wild->Sample(L.X / 100.0 + Rt.X * 7.0 * Sg, L.Y / 100.0 + Rt.Y * 7.0 * Sg, Q, false);
		if (Q.Field < 0.3f && Q.WaterKind == 0 && Q.Road < 0.15f) { Side = Rt * (7.0 * Sg); bSide = true; break; }
	}
	if (!bSide) Side = Rt * 3.5;
	FVector Fire(L.X + Side.X * 100.0, L.Y + Side.Y * 100.0, 0.0);
	Fire.Z = WildGroundZ(Fire);
	T.Camp = Fire;
	ARDWildChunk* C = nullptr;
	{
		const FIntPoint Ck(FMath::FloorToInt(Fire.X / 100.0 / WildChunkM), FMath::FloorToInt(Fire.Y / 100.0 / WildChunkM));
		if (const TObjectPtr<ARDWildChunk>* Cp = WildChunks.Find(Ck)) C = Cp->Get();
	}
	USceneComponent* Att = C ? (USceneComponent*)C->Ground : nullptr;
	auto PutAt = [&](const FString& Prefix, const FVector& At, float Yaw, float Sink) -> UStaticMeshComponent*
	{
		TArray<UStaticMesh*> Ms; WildPiecesOf(Prefix, Ms);
		if (Ms.Num() == 0 || !Att) return nullptr;
		UStaticMesh* M = Ms[FMath::Abs((int32)T.Seed) % Ms.Num()];
		const float* Ks = WildPieceScale.Find(FName(*M->GetName()));
		const float Sc = Ks ? *Ks : 1.f;
		UStaticMeshComponent* Sm = NewObject<UStaticMeshComponent>(C);
		Sm->SetStaticMesh(M);
		Sm->SetupAttachment(Att);
		Sm->RegisterComponent();
		Sm->SetWorldTransform(FTransform(FRotator(0.f, Yaw, 0.f), FVector(At.X, At.Y, WildGroundZ(At) - Sink * Sc), FVector(Sc)));
		T.CampBits.Add(Sm);
		return Sm;
	};
	if (UStaticMeshComponent* F = PutAt(TEXT("campfire"), Fire, 0.f, 2.f))
	{
		if (WildFireFx) T.CampBits.Add(UNiagaraFunctionLibrary::SpawnSystemAttached(WildFireFx, F, NAME_None, FVector(0, 0, 25.f), FRotator::ZeroRotator, EAttachLocation::KeepRelativeOffset, true));
		UPointLightComponent* Lt = NewObject<UPointLightComponent>(C);
		Lt->SetupAttachment(F);
		Lt->SetIntensityUnits(ELightUnits::Candelas);
		Lt->SetIntensity(40.f);
		Lt->SetAttenuationRadius(1400.f);
		Lt->SetLightColor(FLinearColor(1.f, 0.55f, 0.22f));
		Lt->SetCastShadows(true);
		Lt->RegisterComponent();
		Lt->SetRelativeLocation(FVector(0, 0, 60.f));
		T.CampBits.Add(Lt);
	}
	// (each sits on a log round the fire, facing it)
	for (int32 K = 0; K < T.Folk.Num(); ++K)
	{
		ARDTownsfolk* Fk = T.Folk[K].Get();
		if (!Fk) continue;
		const float A = 360.f * K / T.Folk.Num() + 20.f;
		const FVector Seat = Fire + FRotator(0.f, A, 0.f).RotateVector(FVector(210.f, 0.f, 0.f));
		PutAt(TEXT("log"), Fire + FRotator(0.f, A, 0.f).RotateVector(FVector(250.f, 0.f, 0.f)), A + 90.f, 3.f);
		Fk->RoadPath.Reset();
		Fk->RoadPath.Add(FVector(Seat.X, Seat.Y, 0.0));
		Fk->SetStandWork(TEXT("SitTalk"), NAME_None);
		Fk->HomeYaw = A + 180.f;
	}
	UE_LOG(LogRDWild10, Log, TEXT("RDTRAVELLERS camped at (%.0f, %.0f, %.0f) on the road to %s"), Fire.X, Fire.Y, Fire.Z, *T.Name);
}

bool ARDDungeonGenerator::ForceWildTravellers()
{
	// (a test's: the groups dropped and made again with her as their reach)
	for (FTraveller& T : WildTravellers)
	{
		for (auto& F : T.Folk) if (F.IsValid()) F->Destroy();
		for (auto& B : T.CampBits) if (B.IsValid()) B->DestroyComponent();
	}
	WildTravellers.Reset();
	const APawn* P = UGameplayStatics::GetPlayerPawn(this, 0);
	if (!P) return false;
	TickWildTravellers(P->GetActorLocation());
	return WildTravellers.Num() > 0;
}

TArray<FString> ARDDungeonGenerator::GetWildTravellerLines() const
{
	TArray<FString> Out;
	for (int32 G = 0; G < WildTravellers.Num(); ++G)
	{
		const FTraveller& T = WildTravellers[G];
		const ARDTownsfolk* L = T.Folk.Num() > 0 ? T.Folk[0].Get() : nullptr;
		if (!L) continue;
		int32 Walking = 0; for (const auto& F : T.Folk) if (F.IsValid() && F->RoadPath.Num() > 0) ++Walking;
		const FVector P = L->GetActorLocation();
		Out.Add(FString::Printf(TEXT("group|%d|%.0f|%.0f|%.0f|%d|%d|%d|%d|%s|%.0f|%.0f|%.0f|%d"), G, P.X, P.Y, P.Z, T.Folk.Num(), T.bCamped ? 1 : 0, Walking, T.Road, *T.Name, T.Camp.X, T.Camp.Y, T.Camp.Z, T.CampBits.Num()));
		for (const auto& F : T.Folk)
			if (const ARDTownsfolk* Fk = F.Get())
			{
				const FVector Q = Fk->GetActorLocation();
				Out.Add(FString::Printf(TEXT("folk|%d|%s|%.0f|%.0f|%.0f|%s|%s"), G, *Fk->Title, Q.X, Q.Y, Q.Z, *Fk->GetClipName(), *Fk->GetRoleName()));
			}
	}
	return Out;
}

// ================================================================================================ the town's hens and its watch
void ARDDungeonGenerator::SpawnTownHens()
{
	ARDSection* S = GetSection(FIntPoint::ZeroValue);
	const int32 Def = TownAnimals.IndexOfByPredicate([](const FRDTownAnimalDef& D) { return D.Name == TEXT("Chicken") && D.Mesh; });
	if (TownHens <= 0 || !S || Def < 0 || TownPlan == 5) return;          // (Heaven: no farm animals (heaven.md))
	FVector Sq = FVector::ZeroVector;
	if (!GetTownPlace(TEXT("square"), Sq)) return;
	// (each on a free tile of the open ground within 24 m of the square, its round that tile's middle and 1.2 m round it: nothing in
	// its way (a tile something stands on is blocked))
	TArray<FIntPoint> Free;
	const FIntPoint T0 = S->WorldToLocal(Sq);
	for (int32 Dx = -8; Dx <= 8; ++Dx)
		for (int32 Dy = -8; Dy <= 8; ++Dy)
		{
			const FIntPoint T = T0 + FIntPoint(Dx, Dy);
			if (S->IsWalkable(T) && S->RoomAtLocal(T) == S->RoomAtLocal(T0) && S->TownLiftAt(FVector2D(S->LocalToWorld(T))) == 0.f) Free.Add(T);
		}
	if (Free.Num() == 0) return;
	FRandomStream R((int32)HashCombine((uint32)StartSeed, 0x4E45u));
	FActorSpawnParameters Sp; Sp.SpawnCollisionHandlingOverride = ESpawnActorCollisionHandlingMethod::AlwaysSpawn;
	int32 Made = 0;
	for (int32 K = 0; K < TownHens; ++K)
	{
		const FIntPoint T = Free[R.RandRange(0, Free.Num() - 1)];
		FVector At = S->LocalToWorld(T); At.Z = S->GetActorLocation().Z;
		ARDTownAnimal* A = GetWorld()->SpawnActor<ARDTownAnimal>(ARDTownAnimal::StaticClass(), FTransform(FRotator(0, R.FRandRange(0.f, 360.f), 0), At), Sp);
		if (!A) continue;
		A->bLoose = true;
		A->Init(this, Def, -1, At, FVector2D(120.f, 120.f) + FVector2D(TownAnimals[Def].HalfSize.X), HashCombine((uint32)StartSeed, (uint32)K * 2654435761u));
		TownAnimalActors.Add(A);
		++Made;
	}
	UE_LOG(LogRDWild10, Log, TEXT("RDTOWN %d hens loose about the square"), Made);
}

TArray<FString> ARDDungeonGenerator::GetTownHenLines() const
{
	TArray<FString> Out;
	for (const ARDTownAnimal* A : TownAnimalActors)
		if (IsValid(A) && A->bLoose)
		{
			const FVector L = A->GetActorLocation();
			Out.Add(FString::Printf(TEXT("hen|%.0f|%.0f|%.0f|%d|%d"), L.X, L.Y, L.Z, A->GetState(), A->GetFlees()));
		}
	return Out;
}

void ARDDungeonGenerator::TickNightLanterns()
{
	const float H = GetTownHour();
	const bool bNight = H >= 20.f || H < 6.f;
	for (ARDTownsfolk* T : TownPeople)
		if (IsValid(T) && (T->TownRole == ERDTownRole::Militia || T->TownRole == ERDTownRole::Guard))
			T->SetLantern(bNight && !T->IsSleeping());
}
