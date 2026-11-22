// The list of 2026-11-16's fourteenth phase (docs/improvements14.txt items 21, 22): the signs on the roads laid where she goes (the
// world's FRDWildSign, RDWildRoads14.cpp: a post and one or two painted arms, each naming a place and how far), and the tests' hooks
// for the roads and their signs.
#include "RD/RDDungeonGenerator.h"
#include "RD/RDWild.h"
#include "Components/StaticMeshComponent.h"
#include "Components/TextRenderComponent.h"
#include "Engine/StaticMesh.h"
#include "Kismet/GameplayStatics.h"

DEFINE_LOG_CATEGORY_STATIC(LogRDSigns14, Log, All);

namespace
{
	const TCHAR* RDS14Post = TEXT("/Game/Village_Collection/Props/SM_WoodDirectionPlaque/Meshes/FBX/SM_WoodDirectionPlaque_Base_SM_WoodDirectionPlaque_Base.SM_WoodDirectionPlaque_Base_SM_WoodDirectionPlaque_Base");
	const TCHAR* RDS14Arm = TEXT("/Game/Village_Collection/Props/SM_WoodDirectionPlaque/Meshes/FBX/SM_WoodDirectionPlaque_Up_SM_WoodDirectionPlaque_Up.SM_WoodDirectionPlaque_Up_SM_WoodDirectionPlaque_Up");
	// (the arm's mesh, measured: 3.4 cm thick across X, from 2 to 61.3 cm along +Y off the post, 173 to 188 cm up; laid 1.7 times as long
	// and 1.8 times as tall, its middle 185 cm up for the upper arm, 32 cm lower for the second)
	constexpr float RDS14ArmSY = 1.7f, RDS14ArmSZ = 1.8f, RDS14ArmMidY = 31.65f * RDS14ArmSY, RDS14ArmMidZ = 180.65f * RDS14ArmSZ, RDS14ArmTop = 185.f, RDS14ArmGap = 32.f;
}

AActor* ARDDungeonGenerator::SpawnWildSign14(int32 K)
{
	if (!IsWildReady() || !Wild->Signs.IsValidIndex(K)) return nullptr;
	const FRDWildWorld::FRDWildSign& S = Wild->Signs[K];
	// (arm A along the post's +Y, arm B back along the road: turned half round)
	TArray<FSignArm14> Arms;
	Arms.Add(FSignArm14{ S.A, S.Am, 0.f });
	if (!S.B.IsEmpty()) Arms.Add(FSignArm14{ S.B, S.Bm, 180.f });
	return SpawnSignPost14(S.At, S.Yaw, Arms, FString::Printf(TEXT("sign14:%d"), K));
}

AActor* ARDDungeonGenerator::SpawnSignPost14(const FVector2D& AtM, float PostYaw, const TArray<FSignArm14>& Arms, const FString& Tag)
{
	// (a post and its painted arms, each turned about the post by its own yaw (its +Y along the way it points), stacked down from the top:
	// the roads' signs and the list of 2026-11-20's sixteenth phase's crossroads posts alike)
	if (!IsWildReady() || Arms.Num() == 0) return nullptr;
	// (loaded once; missing, never asked again (PR #92's review: every sign near her asked every half second))
	if (bSignMeshMissing14) return nullptr;
	if (!SignPost14) SignPost14 = LoadObject<UStaticMesh>(nullptr, RDS14Post);
	if (!SignArm14) SignArm14 = LoadObject<UStaticMesh>(nullptr, RDS14Arm);
	if (!SignCube14) SignCube14 = LoadObject<UStaticMesh>(nullptr, TEXT("/Engine/BasicShapes/Cube.Cube"));
	UStaticMesh* Post = SignPost14; UStaticMesh* Arm = SignArm14;
	if (!Post || !Arm) { UE_LOG(LogRDSigns14, Error, TEXT("RDSIGN the sign's meshes are missing (%s): no signs are laid"), RDS14Post); bSignMeshMissing14 = true; return nullptr; }
	FActorSpawnParameters Sp; Sp.SpawnCollisionHandlingOverride = ESpawnActorCollisionHandlingMethod::AlwaysSpawn;
	AActor* A = GetWorld()->SpawnActor<AActor>(AActor::StaticClass(), FTransform::Identity, Sp);
	if (!A) return nullptr;
	USceneComponent* Root = NewObject<USceneComponent>(A, TEXT("Root"));
	A->SetRootComponent(Root); Root->RegisterComponent();
	const float Z = Wild->ToZ(Wild->Height(AtM.X, AtM.Y));
	A->SetActorTransform(FTransform(FRotator(0.f, PostYaw, 0.f), FVector(AtM.X * 100.0, AtM.Y * 100.0, Z - 6.f)));
	A->Tags.Add(TEXT("RDWildSign14"));
	A->Tags.Add(*Tag);
	UStaticMeshComponent* Pc = NewObject<UStaticMeshComponent>(A);
	Pc->SetStaticMesh(Post); Pc->SetupAttachment(Root); Pc->RegisterComponent();
	for (int32 I = 0; I < Arms.Num(); ++I)
	{
		const FSignArm14& Am = Arms[I];
		const float Zc = RDS14ArmTop - I * RDS14ArmGap;
		const FRotator Turn(0.f, Am.Yaw, 0.f);
		UStaticMeshComponent* Ac = NewObject<UStaticMeshComponent>(A);
		Ac->SetStaticMesh(Arm); Ac->SetupAttachment(Root);
		Ac->SetRelativeTransform(FTransform(Turn, FVector(0.f, 0.f, Zc - RDS14ArmMidZ), FVector(1.f, RDS14ArmSY, RDS14ArmSZ)));
		Ac->SetCollisionEnabled(ECollisionEnabled::NoCollision);
		Ac->RegisterComponent();
		// (a core inside the arm between its two faces' words: the arm turned half round let the far face's words show through it,
		// mirrored over the near face's (the first pictures); 2 cm thick, 85 x 22 cm, inside the arm's 3.4 x 101 x 27 cm)
		if (UStaticMesh* Cube = SignCube14)
		{
			UStaticMeshComponent* Cc = NewObject<UStaticMeshComponent>(A);
			Cc->SetStaticMesh(Cube); Cc->SetupAttachment(Root);
			Cc->SetRelativeTransform(FTransform(Turn, Turn.RotateVector(FVector(0.f, RDS14ArmMidY, 0.f)) + FVector(0.f, 0.f, Zc), FVector(0.02f, 0.85f, 0.22f)));
			if (UMaterialInterface* Mw = Ac->GetMaterial(0)) Cc->SetMaterial(0, Mw);
			Cc->SetCollisionEnabled(ECollisionEnabled::NoCollision);
			Cc->SetCastShadow(false);
			Cc->RegisterComponent();
		}
		// (painted on both faces: the place's name over its distance, fitted to the arm's face, 90 x 22 cm)
		const FString Text = FString::Printf(TEXT("%s\n%s"), *Am.Name, *FRDWildWorld::SignDistText(Am.M));
		for (int32 Side = -1; Side <= 1; Side += 2)
		{
			UTextRenderComponent* Tx = NewObject<UTextRenderComponent>(A);
			Tx->SetupAttachment(Root);
			Tx->SetText(FText::FromString(Text));
			Tx->SetHorizontalAlignment(EHTA_Center);
			Tx->SetVerticalAlignment(EVRTA_TextCenter);
			Tx->SetWorldSize(10.f);
			const FVector Ls = Tx->GetTextLocalSize();
			Tx->SetWorldSize(10.f * FMath::Min(90.f / FMath::Max(Ls.Y, 1.f), 22.f / FMath::Max(Ls.Z, 1.f)));
			Tx->SetTextRenderColor(FColor(236, 222, 186));          // (cream paint: dark letters on the plaque's dark wood could not be read)
			Tx->SetCollisionEnabled(ECollisionEnabled::NoCollision);
			Tx->ComponentTags.Add(TEXT("SignText14"));
			// (a text faces its +X: the +X face's text turned with the arm, the -X face's half round more)
			Tx->SetRelativeTransform(FTransform(FRotator(0.f, Am.Yaw + (Side > 0 ? 0.f : 180.f), 0.f), Turn.RotateVector(FVector(Side * 2.1f, RDS14ArmMidY, 0.f)) + FVector(0.f, 0.f, Zc)));
			Tx->RegisterComponent();
		}
	}
	return A;
}

void ARDDungeonGenerator::TickWildSigns14()
{
	if (!IsWildReady() || !bWildSigns14 || !GetWorld()) return;
	const float Now = GetWorld()->GetTimeSeconds();
	if (Now < NextSignTick14) return;
	NextSignTick14 = Now + 0.5f;
	const APawn* Pw = UGameplayStatics::GetPlayerPawn(this, 0);
	if (!Pw) return;
	const FVector2D Hm(Pw->GetActorLocation().X / 100.0, Pw->GetActorLocation().Y / 100.0);
	// (laid within 300 m, kept to 380 m: walking along a sign's edge lays it once)
	TArray<int32> Keep; Wild->SignsNear(Hm, WildSignShowM14 + 80.f, Keep);
	const TSet<int32> KeepSet(Keep);
	for (auto It = WildSignActors14.CreateIterator(); It; ++It)
		if (!KeepSet.Contains(It.Key()) || !It.Value().IsValid()) { if (It.Value().IsValid()) It.Value()->Destroy(); It.RemoveCurrent(); }
	TArray<int32> Near; Wild->SignsNear(Hm, WildSignShowM14, Near);
	int32 Made = 0;
	for (const int32 K : Near)
	{
		if (WildSignActors14.Contains(K) || Made >= 4) continue;          // (four a look at most: a cross of roads holds several)
		if (AActor* A = SpawnWildSign14(K)) { WildSignActors14.Add(K, A); ++Made; }
	}
}

void ARDDungeonGenerator::DropWildSigns14()
{
	for (auto& Kv : WildSignActors14) if (Kv.Value.IsValid()) Kv.Value->Destroy();
	WildSignActors14.Reset();
	NextSignTick14 = -1.f;
}

TArray<FString> ARDDungeonGenerator::GetWildSigns14(FVector At, float RadiusM) const
{
	TArray<FString> Out;
	if (!IsWildReady()) return Out;
	TArray<int32> Near; Wild->SignsNear(FVector2D(At.X / 100.0, At.Y / 100.0), RadiusM, Near);
	for (const int32 K : Near)
	{
		const FRDWildWorld::FRDWildSign& S = Wild->Signs[K];
		Out.Add(FString::Printf(TEXT("%d|%d|%.1f|%.1f|%.1f|%s|%.0f|%s|%.0f|%d"), K, S.Kind, S.At.X, S.At.Y, S.Yaw, *S.A, S.Am, *S.B, S.Bm, S.Road));
	}
	return Out;
}

TArray<FString> ARDDungeonGenerator::GetWildSignActors14() const
{
	// (each laid sign: its index, where it stands (cm), and its arms' painted texts, read from the text components themselves)
	TArray<FString> Out;
	for (const auto& Kv : WildSignActors14)
	{
		const AActor* A = Kv.Value.Get();
		if (!A) continue;
		TArray<UTextRenderComponent*> Tx; A->GetComponents<UTextRenderComponent>(Tx);
		TArray<UStaticMeshComponent*> Ms; A->GetComponents<UStaticMeshComponent>(Ms);
		FString Texts;
		for (const UTextRenderComponent* T : Tx) Texts += T->Text.ToString().Replace(TEXT("\n"), TEXT(" / ")) + TEXT(";");
		const FVector L = A->GetActorLocation();
		Out.Add(FString::Printf(TEXT("%d|%.0f|%.0f|%.0f|%d|%d|%s"), Kv.Key, L.X, L.Y, L.Z, Ms.Num(), Tx.Num(), *Texts));
	}
	return Out;
}

TArray<FVector> ARDDungeonGenerator::GetWildRoadPoints14(int32 Road) const
{
	TArray<FVector> Out;
	if (!IsWildReady() || !Wild->Roads.IsValidIndex(Road)) return Out;
	const FRDWildWorld::FRoad& R = Wild->Roads[Road];
	for (int32 I = 0; I < R.P.Num(); ++I) Out.Add(FVector(R.P[I].X, R.P[I].Y, R.Z.IsValidIndex(I) ? R.Z[I] : 0.f));
	return Out;
}

FString ARDDungeonGenerator::GetWildRoadInfo14(int32 Road) const
{
	// (major: from|to; minor: its place, kind and id, what its far end leads to and how far past it, the road it joins, its parent
	// village's id; both: length (m) and points)
	if (!IsWildReady() || !Wild->Roads.IsValidIndex(Road)) return FString();
	const FRDWildWorld::FRoad& R = Wild->Roads[Road];
	const double L = Wild->RoadLength(Road);
	if (!R.bTrack)
		return FString::Printf(TEXT("major|%s|%s|%.0f|%d"), Wild->Towns.IsValidIndex(R.From) ? *Wild->Towns[R.From].Name : TEXT(""), Wild->Towns.IsValidIndex(R.To) ? *Wild->Towns[R.To].Name : TEXT(""), L, R.P.Num());
	return FString::Printf(TEXT("minor|%s|%s|%d|%s|%.0f|%d|%d|%.0f|%d"), *R.Dest, *R.DestKind, R.DestId, *R.Up, R.UpM, R.Join, R.ParentVillage, L, R.P.Num());
}

int32 ARDDungeonGenerator::FindWildRoadTo14(int32 PlaceId) const
{
	if (!IsWildReady()) return -1;
	// (the last made: a village cut off from the major roads has a second way, joined on to the roads that reach one)
	for (int32 I = Wild->Roads.Num() - 1; I >= 0; --I) if (Wild->Roads[I].bMinor && Wild->Roads[I].DestId == PlaceId) return I;
	return -1;
}

FString ARDDungeonGenerator::GetWildMinorStats14() const
{
	if (!IsWildReady()) return FString();
	int32 Major = 0, Minor = 0;
	for (const FRDWildWorld::FRoad& R : Wild->Roads) { if (R.bTrack) ++Minor; else ++Major; }
	return FString::Printf(TEXT("%s|major %d|minor %d|signs %d|init %.2f s"), *Wild->MinorStats, Major, Minor, Wild->Signs.Num(), Wild->InitSeconds);
}
