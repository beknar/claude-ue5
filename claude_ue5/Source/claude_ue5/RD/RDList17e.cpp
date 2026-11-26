// The user's list of 2026-11-26 (docs/improvements17.txt; the plan docs/improvements17_plan.md), its seventh phase: the windows from outside.
//   "For this new mode, the windows show a solid or glowing texture depicting the inside of that room."
//   - Under Closed Structures every window of a closed building has a pane in its frame facing the street: a picture of a room of that
//     building's kind and look (a home of the medieval towns, the holy, forge and mage cities, Heaven's; a tavern, a smithy, a store...), the
//     game's own rooms photographed from inside their windows (884 rooms17) and imported by 949 rooms. A building whose kind has no picture
//     takes its kind's medieval one, then a home's.
//   - It glows at night while the building's lights burn (the town's rule: someone awake inside), and is dim by day: one instanced component a
//     picture, the glow a per-instance value (M_B17_Pane: the picture times the day's or the night's strength).
#include "RD/RDDungeonGenerator.h"
#include "RD/RDSection.h"
#include "RD/RDTown.h"
#include "Components/InstancedStaticMeshComponent.h"
#include "Engine/StaticMesh.h"
#include "HAL/IConsoleManager.h"
#include "Components/PointLightComponent.h"
DEFINE_LOG_CATEGORY_STATIC(LogRDList17e, Log, All);

namespace
{
	TAutoConsoleVariable<int32> CVarRDPanes17(TEXT("rd.Panes17"), 1, TEXT("Closed Structures' windows: pictures of their rooms (1) or none (0)"));
}

FName ARDDungeonGenerator::RoomKey17(const ARDSection* S, int32 BI)
{
	// ("<kind>" for the medieval towns' looks, "<kind>_holy|forge|mage|modern" for the cities' own; the kind's name without spaces)
	if (!S || !S->TownBlds.IsValidIndex(BI)) return NAME_None;
	const ARDSection::FTownBld& B = S->TownBlds[BI];
	FString K = RDTownKindName(B.Kind).Replace(TEXT(" "), TEXT("")).Replace(TEXT("'"), TEXT(""));
	const TCHAR* Grp = B.Style == 4 ? TEXT("_holy") : B.Style == 5 ? TEXT("_forge") : B.Style == 6 ? TEXT("_mage") : B.Style >= 7 ? TEXT("_modern") : TEXT("");
	return FName(*(K + Grp));
}

UMaterialInterface* ARDDungeonGenerator::RoomPaneFor17(const ARDSection* S, int32 BI, FName* Used) const
{
	const FName K = RoomKey17(S, BI);
	FString Base = K.ToString(); int32 Us = -1;
	if (Base.FindChar(TEXT('_'), Us)) Base = Base.Left(Us);
	const bool bModern = K.ToString().EndsWith(TEXT("_modern"));
	for (const FName& Try : { K, FName(*Base), FName(bModern ? TEXT("home_modern") : TEXT("home")), FName(TEXT("home")) })
		if (const TObjectPtr<UMaterialInterface>* M = RoomPanes17.Find(Try); M && *M) { if (Used) *Used = Try; return *M; }
	return nullptr;
}

void ARDDungeonGenerator::TickPanes17(float Dt)
{
	ARDSection* S = GetSection(FIntPoint::ZeroValue);
	const bool bOn = CVarRDPanes17.GetValueOnGameThread() != 0;
	if (Panes17For.Get() && Panes17For.Get() == S && bOn != bPanes17Shown)
	{
		// (rd.Panes17 0 hides the panes made, 1 shows them: the tests' with and without)
		bPanes17Shown = bOn;
		for (const TWeakObjectPtr<UInstancedStaticMeshComponent>& W : Panes17) if (UInstancedStaticMeshComponent* C = W.Get()) C->SetVisibility(bOn);
	}
	if (!S || S->IsBuilding() || !S->BldClosed17 || !BuildingPaneMesh17 || !bOn)
	{
		if (Panes17For.Get() && Panes17For.Get() != S) { Panes17.Reset(); PaneBld17.Reset(); PaneKeys17.Reset(); Panes17For = nullptr; }
		return;
	}
	// ---- made once a town: a pane at each window of each closed building, its picture its kind's
	if (Panes17For.Get() != S)
	{
		Panes17For = S; Panes17.Reset(); PaneBld17.Reset(); PaneKeys17.Reset(); Panes17Made = 0; bPanes17Shown = true;
		TMap<UMaterialInterface*, UInstancedStaticMeshComponent*> ByMat;
		for (const ARDSection::FTownWin16& Wn : S->TownWindows16)
		{
			if (!S->HasRecord17(Wn.Bld)) continue;
			FName Used;
			UMaterialInterface* M = RoomPaneFor17(S, Wn.Bld, &Used);
			if (!M) continue;
			UInstancedStaticMeshComponent*& H = ByMat.FindOrAdd(M);
			if (!H)
			{
				H = NewObject<UInstancedStaticMeshComponent>(S);
				H->SetStaticMesh(BuildingPaneMesh17); H->SetMaterial(0, M);
				H->NumCustomDataFloats = 1;
				H->SetMobility(EComponentMobility::Static); H->SetCollisionProfileName(TEXT("NoCollision")); H->SetCastShadow(false);
				H->SetCullDistances(6000, 8000);
				H->SetupAttachment(S->GetRootComponent());
				H->ComponentTags.Add(TEXT("RDPane17"));
				H->RegisterComponent(); S->AddInstanceComponent(H);
				Panes17.Add(H);
			}
			// (facing the street, its width along the wall, a few centimetres out in the frame)
			const FVector Out = Wn.Out.GetSafeNormal2D();
			const FTransform T(FRotationMatrix::MakeFromZX(Out, FVector(Out.Y, -Out.X, 0.f)).Rotator(), Wn.At + Out * BuildingPaneOut17, FVector(BuildingPaneSize17.X / 100.f, BuildingPaneSize17.Y / 100.f, 1.f));
			const int32 I = H->AddInstance(T, true);
			PaneBld17.Add({ H, I, Wn.Bld });
			PaneKeys17.Add(Used);
			++Panes17Made;
		}
		Panes17Lit = -1.f;
		UE_LOG(LogRDList17e, Log, TEXT("RDPANES17 %d panes in %d pictures"), Panes17Made, ByMat.Num());
	}
	// ---- a pane glows at night while its building's lights burn, twice a second
	Panes17T -= Dt;
	if (Panes17T > 0.f) return;
	Panes17T = 0.5f;
	const float H = GetTownHour();
	const bool bNight = bDayNight && (H >= 19.f || H < 6.5f);
	int32 Lit = 0;
	TSet<UInstancedStaticMeshComponent*> Dirty;
	for (const FPane17& P : PaneBld17)
	{
		UInstancedStaticMeshComponent* C = P.C.Get();
		if (!C) continue;
		const bool* L = TownBldLit.Find(P.Bld);
		const float G = bNight && L && *L ? 1.f : 0.f;
		if (G > 0.f) ++Lit;
		if (C->PerInstanceSMCustomData.IsValidIndex(P.I) && C->PerInstanceSMCustomData[P.I] == G) continue;
		C->SetCustomDataValue(P.I, 0, G, false); Dirty.Add(C);
	}
	for (UInstancedStaticMeshComponent* C : Dirty) C->MarkRenderStateDirty();
	Panes17Glowing = Lit;
}

bool ARDDungeonGenerator::CaptureRoom17(FVector At, FRotator Rot, FVector LightAt, float Intensity, const FString& Dir, const FString& File)
{
	// (884 rooms17: a room's picture from inside its window, a warm fill light over its middle for the picture only (rooms without a lamp
	// of their own came out black))
	UPointLightComponent* L = NewObject<UPointLightComponent>(this);
	L->SetMobility(EComponentMobility::Movable); L->SetIntensityUnits(ELightUnits::Candelas);
	L->SetIntensity(Intensity); L->SetAttenuationRadius(1800.f); L->SetLightColor(FLinearColor(1.f, 0.78f, 0.55f)); L->SetCastShadows(false);
	L->RegisterComponent(); L->SetWorldLocation(LightAt);
	const bool bOk = CaptureView24(At, Rot, 75.f, 512, 512, Dir, File);
	L->DestroyComponent();
	return bOk;
}

TArray<FString> ARDDungeonGenerator::GetPanes17() const
{
	// (tests: "<building>|<x>|<y>|<z>|<glow>|<picture key>" a pane)
	TArray<FString> Out;
	for (int32 K = 0; K < PaneBld17.Num(); ++K)
	{
		const FPane17& P = PaneBld17[K];
		const UInstancedStaticMeshComponent* C = P.C.Get();
		if (!C) continue;
		FTransform T; C->GetInstanceTransform(P.I, T, true);
		const float G = C->PerInstanceSMCustomData.IsValidIndex(P.I) ? C->PerInstanceSMCustomData[P.I] : -1.f;
		Out.Add(FString::Printf(TEXT("%d|%.0f|%.0f|%.0f|%.0f|%s"), P.Bld, T.GetLocation().X, T.GetLocation().Y, T.GetLocation().Z, G, PaneKeys17.IsValidIndex(K) ? *PaneKeys17[K].ToString() : TEXT("-")));
	}
	return Out;
}
