// The user's list of 2026-11-07 (docs/improvements8.txt) on the towns: the barracks' training dummies and targets react when
// her blow or her bolt meets them (rocked away from her, a swing that dies away, the weapon's hit sound, the blow's number).
// Only where the generator has bTown; the dungeons have no dummies.
#include "RD/RDSection.h"
#include "RD/RDDungeonGenerator.h"
#include "Components/StaticMeshComponent.h"
#include "Engine/StaticMesh.h"
#include "Engine/World.h"

void ARDSection::AddTownDummy(FName Kind, const FRDPiece* P, const FTransform& T, float Lift)
{
	if (!P || !P->Mesh) return;
	// (the pivot at its foot, turned as the piece is; the mesh on it as the piece places it)
	const FTransform Foot(T.GetRotation(), T.GetLocation() + FVector(0, 0, Lift), FVector::OneVector);
	USceneComponent* Pv = AddPivot(RootComponent, Foot.GetRelativeTransform(GetActorTransform()));
	UStaticMeshComponent* M = AddMesh(Pv, P->Mesh, P->Adjust * FTransform(FQuat::Identity, FVector::ZeroVector, T.GetScale3D()), P->bCollision);
	if (M && P->Material) for (int32 Sl = 0; Sl < P->Mesh->GetStaticMaterials().Num(); ++Sl) M->SetMaterial(Sl, P->Material);
	FTownDummy D;
	D.Pivot = Pv; D.Mesh = M; D.Kind = Kind; D.At = Foot.GetLocation(); D.Rest = Pv->GetComponentQuat();
	const FVector Sz = FVector(P->Size) * T.GetScale3D();
	D.Radius = FMath::Clamp(0.5f * FMath::Max(Sz.X, Sz.Y), 25.f, 70.f);
	D.Height = FMath::Max(Sz.Z, 100.f);
	TownDummies.Add(D);
}

void ARDSection::HitTownDummy(int32 I, const FVector& From, float Strength)
{
	if (!TownDummies.IsValidIndex(I) || !GetWorld()) return;
	FTownDummy& D = TownDummies[I];
	// (tipped away from where the blow came from: about the level line across that way)
	FVector Away = (D.At - From) * FVector(1, 1, 0);
	if (!Away.Normalize()) Away = FVector(1, 0, 0);
	D.Axis = FVector::CrossProduct(FVector::UpVector, Away).GetSafeNormal();
	// (a blow on a dummy still swinging adds to it, up to 22 degrees)
	const float Now = GetWorld()->GetTimeSeconds();
	const float Left = D.Amp * FMath::Exp(-2.6f * FMath::Max(0.f, Now - D.HitAt));
	D.Amp = FMath::Min(22.f, Left * 0.5f + 13.f * FMath::Clamp(Strength, 0.2f, 1.5f));
	D.HitAt = Now; ++D.Hits;
}

void ARDSection::TickTownDummies(float Now)
{
	for (FTownDummy& D : TownDummies)
	{
		USceneComponent* Pv = D.Pivot.Get();
		if (!Pv || D.Amp <= 0.f) continue;
		const float T = Now - D.HitAt;
		const float Env = FMath::Exp(-2.6f * T);
		if (Env * D.Amp < 0.05f) { Pv->SetWorldRotation(D.Rest); D.Amp = 0.f; continue; }
		// (a stiff post: out first, back past its rest, about 1.7 swings a second)
		const float Ang = D.Amp * Env * FMath::Sin(T * 2.f * PI * 1.7f);
		Pv->SetWorldRotation(FQuat(D.Axis, FMath::DegreesToRadians(Ang)) * D.Rest);
	}
}

int32 ARDSection::TownDummyOf(const UPrimitiveComponent* C) const
{
	if (C) for (int32 I = 0; I < TownDummies.Num(); ++I) if (TownDummies[I].Mesh.Get() == C) return I;
	return -1;
}

TArray<FString> ARDSection::GetTownDummyLines() const
{
	TArray<FString> Out;
	const float Now = GetWorld() ? GetWorld()->GetTimeSeconds() : 0.f;
	for (int32 I = 0; I < TownDummies.Num(); ++I)
	{
		const FTownDummy& D = TownDummies[I];
		// (kind|x|y|z|hits|its lean now from upright, degrees|radius|height)
		const USceneComponent* Pv = D.Pivot.Get();
		const float Lean = Pv ? FMath::RadiansToDegrees(FMath::Acos(FMath::Clamp(FVector::DotProduct(Pv->GetUpVector(), D.Rest.GetUpVector()), -1.f, 1.f))) : -1.f;
		Out.Add(FString::Printf(TEXT("%s|%.0f|%.0f|%.0f|%d|%.2f|%.0f|%.0f"), *D.Kind.ToString(), D.At.X, D.At.Y, D.At.Z, D.Hits, Lean, D.Radius, D.Height));
	}
	return Out;
}

int32 ARDDungeonGenerator::HitTownDummiesInArc(const FVector& L, const FVector& Fw, float Reach, float MinCos, float Strength, FName Sound, float Dmg)
{
	if (!bTown) return 0;
	int32 N = 0;
	for (const auto& Kv : Sections)
	{
		ARDSection* S = Kv.Value;
		if (!S) continue;
		for (int32 I = 0; I < S->TownDummies.Num(); ++I)
		{
			const ARDSection::FTownDummy& D = S->TownDummies[I];
			const FVector Dv = (D.At - L) * FVector(1, 1, 0);
			const float Dist = Dv.Size() - D.Radius;
			if (Dist > Reach || L.Z < D.At.Z - 120.f || L.Z > D.At.Z + D.Height + 120.f) continue;
			if (Dist > 40.f && FVector::DotProduct(Dv.GetSafeNormal(), Fw) < MinCos) continue;
			S->HitTownDummy(I, L, Strength);
			const FVector Top = D.At + FVector(0, 0, D.Height * 0.8f);
			if (!Sound.IsNone()) PlaySoundAt(Sound, Top);
			if (Dmg > 0.f) AddHitText(Top, Dmg, false);
			++N; ++TownDummyHits;
		}
	}
	return N;
}

bool ARDDungeonGenerator::HitTownDummyByComponent(const UPrimitiveComponent* C, const FVector& From, float Strength, FName Sound, float Dmg)
{
	if (!bTown || !C) return false;
	ARDSection* S = Cast<ARDSection>(C->GetOwner());
	const int32 I = S ? S->TownDummyOf(C) : -1;
	if (I < 0) return false;
	S->HitTownDummy(I, From, Strength);
	const ARDSection::FTownDummy& D = S->TownDummies[I];
	const FVector Top = D.At + FVector(0, 0, D.Height * 0.8f);
	if (!Sound.IsNone()) PlaySoundAt(Sound, Top);
	if (Dmg > 0.f) AddHitText(Top, Dmg, false);
	++TownDummyHits;
	return true;
}

TArray<FString> ARDDungeonGenerator::GetTownDummyLines() const
{
	TArray<FString> Out;
	for (const auto& Kv : Sections) if (Kv.Value) Out.Append(Kv.Value->GetTownDummyLines());
	return Out;
}
