#include "SS/SSFXLibrary.h"
#include "Distributions/DistributionFloatConstant.h"
#include "Distributions/DistributionFloatConstantCurve.h"
#include "Distributions/DistributionVectorConstant.h"
#include "Materials/MaterialInterface.h"
#include "Particles/Color/ParticleModuleColor.h"
#include "Particles/Color/ParticleModuleColorOverLife.h"
#include "Particles/Lifetime/ParticleModuleLifetime.h"
#include "Particles/ParticleEmitter.h"
#include "Particles/ParticleLODLevel.h"
#include "Particles/ParticleModule.h"
#include "Particles/ParticleModuleRequired.h"
#include "Particles/ParticleSystem.h"
#include "Particles/Size/ParticleModuleSize.h"
#include "Particles/Spawn/ParticleModuleSpawn.h"
#include "Particles/Spawn/ParticleModuleSpawnPerUnit.h"
#include "Particles/TypeData/ParticleModuleTypeDataBase.h"
#include "Particles/TypeData/ParticleModuleTypeDataRibbon.h"
#include "UObject/UnrealType.h"

static void SSDescribeObject(const UObject* O, const UClass* StopAt, const FString& Indent, FString& Out)
{
	for (TFieldIterator<FProperty> It(O->GetClass()); It; ++It)
	{
		if (It->GetOwnerClass() == StopAt || It->GetOwnerClass() == UObject::StaticClass()) continue;
		FString V;
		It->ExportText_InContainer(0, V, O, O, const_cast<UObject*>(O), PPF_None);
		if (V.Len() > 150) V = V.Left(150) + TEXT("...");
		Out += FString::Printf(TEXT("%s%s = %s\n"), *Indent, *It->GetName(), *V);
	}
}

FString USSFXLibrary::DescribeParticleSystem(UParticleSystem* System)
{
	FString Out;
	if (!System) return Out;
	for (const UParticleEmitter* E : System->Emitters)
	{
		if (!E) continue;
		Out += FString::Printf(TEXT("emitter %s (%s), %d lods\n"), *E->EmitterName.ToString(), *E->GetClass()->GetName(), E->LODLevels.Num());
		const UParticleLODLevel* L = E->LODLevels.Num() > 0 ? E->LODLevels[0] : nullptr;
		if (!L) continue;
		if (const UParticleModuleRequired* Rq = L->RequiredModule)
			Out += FString::Printf(TEXT("  required: material %s, local space %d, duration %.2f, loops %d\n"), Rq->Material ? *Rq->Material->GetPathName() : TEXT("none"), Rq->bUseLocalSpace ? 1 : 0, Rq->EmitterDuration, Rq->EmitterLoops);
		if (L->TypeDataModule)
		{
			Out += FString::Printf(TEXT("  type data %s\n"), *L->TypeDataModule->GetClass()->GetName());
			SSDescribeObject(L->TypeDataModule, UParticleModule::StaticClass(), TEXT("      "), Out);
		}
		TArray<const UParticleModule*> Mods;
		if (L->SpawnModule) Mods.Add(L->SpawnModule);
		for (const UParticleModule* M : L->Modules) if (M) Mods.Add(M);
		for (const UParticleModule* M : Mods)
		{
			Out += FString::Printf(TEXT("  module %s\n"), *M->GetClass()->GetName());
			SSDescribeObject(M, UParticleModule::StaticClass(), TEXT("      "), Out);
			TArray<UObject*> Inner;
			GetObjectsWithOuter(M, Inner, EGetObjectsFlags::None);
			for (const UObject* I : Inner)
			{
				Out += FString::Printf(TEXT("      > %s %s\n"), *I->GetClass()->GetName(), *I->GetName());
				SSDescribeObject(I, UObject::StaticClass(), TEXT("          "), Out);
			}
		}
	}
	return Out;
}

int32 USSFXLibrary::TuneParticleSystem(UParticleSystem* System, float Size, FLinearColor Color, float Lifetime, UMaterialInterface* Material)
{
	int32 Changed = 0;
#if WITH_EDITOR
	if (!System) return 0;
	System->Modify();
	auto ConstF = [](UObject* Outer, float V) { UDistributionFloatConstant* D = NewObject<UDistributionFloatConstant>(Outer); D->Constant = V; return D; };
	auto ConstV = [](UObject* Outer, const FVector& V) { UDistributionVectorConstant* D = NewObject<UDistributionVectorConstant>(Outer); D->Constant = V; return D; };
	auto Fade = [](UObject* Outer, float A)
	{
		UDistributionFloatConstantCurve* D = NewObject<UDistributionFloatConstantCurve>(Outer);
		D->ConstantCurve.AddPoint(0.f, A); D->ConstantCurve.AddPoint(0.6f, A * 0.55f); D->ConstantCurve.AddPoint(1.f, 0.f);
		return D;
	};
	const FVector Rgb(Color.R, Color.G, Color.B);
	for (UParticleEmitter* E : System->Emitters)
	{
		if (!E) continue;
		for (UParticleLODLevel* L : E->LODLevels)
		{
			if (!L) continue;
			if (Material && L->RequiredModule) { L->RequiredModule->Modify(); L->RequiredModule->Material = Material; ++Changed; }
			// one camera-facing sheet, a few segments between particles: plenty for a contrail, a fraction of the memory
			if (UParticleModuleTypeDataRibbon* Rb = Cast<UParticleModuleTypeDataRibbon>(L->TypeDataModule)) { Rb->Modify(); Rb->SheetsPerTrail = 1; Rb->MaxTessellationBetweenParticles = 6; ++Changed; }
			for (UParticleModule* M : L->Modules)
			{
				if (!M) continue;
				if (UParticleModuleSize* S = Cast<UParticleModuleSize>(M))
				{
					if (Size > 0.f) { S->Modify(); S->StartSize.Distribution = ConstV(S, FVector(Size)); S->StartSize.Initialize(); ++Changed; }
				}
				else if (UParticleModuleLifetime* Lt = Cast<UParticleModuleLifetime>(M))
				{
					if (Lifetime > 0.f) { Lt->Modify(); Lt->Lifetime.Distribution = ConstF(Lt, Lifetime); Lt->Lifetime.Initialize(); ++Changed; }
				}
				else if (UParticleModuleColorOverLife* Co = Cast<UParticleModuleColorOverLife>(M))
				{
					if (Color.A > 0.f)
					{
						Co->Modify();
						Co->ColorOverLife.Distribution = ConstV(Co, Rgb); Co->ColorOverLife.Initialize();
						Co->AlphaOverLife.Distribution = Fade(Co, Color.A); Co->AlphaOverLife.Initialize();
						++Changed;
					}
				}
				else if (UParticleModuleColor* Cm = Cast<UParticleModuleColor>(M))
				{
					if (Color.A > 0.f)
					{
						Cm->Modify();
						Cm->StartColor.Distribution = ConstV(Cm, Rgb); Cm->StartColor.Initialize();
						Cm->StartAlpha.Distribution = ConstF(Cm, Color.A); Cm->StartAlpha.Initialize();
						++Changed;
					}
				}
			}
		}
	}
	System->PostEditChange();
	System->MarkPackageDirty();
#endif
	return Changed;
}

int32 USSFXLibrary::SetSpawnPerUnit(UParticleSystem* System, float UnitScalar, bool bSpawnInitialParticle)
{
	int32 Changed = 0;
#if WITH_EDITOR
	if (!System) return 0;
	System->Modify();
	for (UParticleEmitter* E : System->Emitters)
	{
		if (!E) continue;
		for (UParticleLODLevel* L : E->LODLevels)
		{
			if (!L) continue;
			if (UParticleModuleTypeDataRibbon* Rb = Cast<UParticleModuleTypeDataRibbon>(L->TypeDataModule)) { Rb->Modify(); Rb->bSpawnInitialParticle = bSpawnInitialParticle; ++Changed; }
			for (UParticleModule* M : L->Modules)
				if (UParticleModuleSpawnPerUnit* Su = Cast<UParticleModuleSpawnPerUnit>(M))
					if (UnitScalar > 0.f) { Su->Modify(); Su->UnitScalar = UnitScalar; ++Changed; }
		}
	}
	System->PostEditChange();
	System->MarkPackageDirty();
#endif
	return Changed;
}
