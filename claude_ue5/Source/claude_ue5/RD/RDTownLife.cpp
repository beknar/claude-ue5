// Brokenspire's life (the user's third list of 2026-11-02, docs/levels/brokenspire.md): "the town should look more lively ...
// have a finite state machine that loops between at least 3 activities for NPCs and have different timers for each NPC so
// that they drift between at least 3 different jobs".
//   - the townsfolk's round of work (ARDTownsfolk): the places of work the plan leaves (ARDSection::TownWorks: a cooking pot,
//     a spit, a garden, a pen, a tavern's seat, a table to serve, the bar, the well, the market's stalls, the smithy, the
//     refugees' camp) gone between in turn, each for a time drawn from the townsperson's own range
//   - who does what (SpawnTownLife): the residents round their homes, the children, the refugees at their camp, the smith, the
//     innkeeper and a server, the tavern's customers, the drunk, the preacher, the town's fool
//   - the farm animals in their pens (ARDTownAnimal) and the spits' meat turned while their cranks are turned
#include "RD/RDDungeonGenerator.h"
#include "RD/RDSection.h"
#include "RD/RDTown.h"
#include "Components/SkeletalMeshComponent.h"
#include "Components/StaticMeshComponent.h"
#include "Animation/AnimSequenceBase.h"
#include "Engine/StaticMesh.h"
#include "Engine/World.h"

DEFINE_LOG_CATEGORY_STATIC(LogRDTownLife, Log, All);

// ================================================================================================ a townsperson's round of work
void ARDTownsfolk::SetJobs(const TArray<int32>& InJobs, float InMin, float InMax)
{
	Jobs = InJobs; JobMin = FMath::Max(3.f, InMin); JobMax = FMath::Max(JobMin + 1.f, InMax);
	JobI = R.RandRange(0, FMath::Max(0, Jobs.Num() - 1)) - 1;
	// (the first job a little later for each: they do not all set off in the same second)
	Act = 0; WorkAt = -1; NextTrip = GetWorld() ? GetWorld()->GetTimeSeconds() + R.FRandRange(0.5f, 6.f) : 0.f;
}

FName ARDTownsfolk::WorkKind() const
{
	return Section && Section->TownWorks.IsValidIndex(WorkAt) ? Section->TownWorks[WorkAt].Kind : NAME_None;
}

UAnimationAsset* ARDTownsfolk::WorkClip(FName Kind) const
{
	if (!Gen || !Gen->Townsfolk.IsValidIndex(Def)) return nullptr;
	const TObjectPtr<UAnimationAsset>* A = Gen->Townsfolk[Def].WorkClips.Find(Kind);
	return A ? A->Get() : nullptr;
}

void ARDTownsfolk::SetProp(FName Prop)
{
	if (PropComp) { PropComp->DestroyComponent(); PropComp = nullptr; }
	if (Prop.IsNone() || !Gen) return;
	const FRDTownProp* P = Gen->TownProps.Find(Prop);
	if (!P || !P->Mesh) return;
	UStaticMeshComponent* C = NewObject<UStaticMeshComponent>(this);
	C->SetStaticMesh(P->Mesh);
	C->SetCollisionEnabled(ECollisionEnabled::NoCollision);
	C->SetCastShadow(false);
	C->SetupAttachment(Body, P->Bone);
	C->SetRelativeTransform(P->Grip);
	C->RegisterComponent();
	PropComp = C;
}

void ARDTownsfolk::NextJob(float Now)
{
	if (Jobs.Num() == 0 || !Gen || !Section) { Act = 0; return; }
	const FVector L = GetActorLocation();
	for (int32 K = 1; K <= Jobs.Num(); ++K)
	{
		const int32 J = (JobI + K + Jobs.Num()) % Jobs.Num();
		const int32 W = Jobs[J];
		if (W < 0)
		{
			// (a stroll about its post: its old round of short walks, for a while)
			JobI = J; Act = 4; WorkUntil = Now + R.FRandRange(JobMin, JobMax) * 0.6f; NextTrip = Now;
			KindsDone.Add(TEXT("Stroll")); ++JobsDone;
			return;
		}
		if (!Section->TownWorks.IsValidIndex(W) || !Gen->IsTownWorkFree(W, this)) continue;
		const ARDSection::FTownWork& Tw = Section->TownWorks[W];
		// (a tile path to the walkable tile nearest the place (the place itself may be in a garden's bed or by a stool), then
		// the last steps straight)
		const FIntPoint Tt = Section->WorldToLocal(Tw.At);
		FIntPoint Best = Tt; bool bFound = Section->IsWalkable(Tt);
		for (int32 Rr = 1; Rr <= 3 && !bFound; ++Rr)
		{
			float Bd = MAX_flt;
			for (int32 Dx = -Rr; Dx <= Rr; ++Dx) for (int32 Dy = -Rr; Dy <= Rr; ++Dy)
			{
				if (FMath::Max(FMath::Abs(Dx), FMath::Abs(Dy)) != Rr) continue;
				const FIntPoint Q = Tt + FIntPoint(Dx, Dy);
				if (!Section->IsWalkable(Q)) continue;
				const float D = FVector::Dist2D(Section->LocalToWorld(Q), Tw.At);
				if (D < Bd) { Bd = D; Best = Q; bFound = true; }
			}
		}
		// (and from the walkable tile nearest where it stands: a place of work can be on a blocked tile (the bar's front, by a
		// fire), and a tile path from there found nothing: the server at the bar never reached a table)
		FIntPoint From = Section->WorldToLocal(L);
		bool bFromMoved = false;
		if (!Section->IsWalkable(From))
			for (int32 Rr = 1; Rr <= 3; ++Rr)
			{
				float Bd = MAX_flt; FIntPoint Bq = From;
				for (int32 Dx = -Rr; Dx <= Rr; ++Dx) for (int32 Dy = -Rr; Dy <= Rr; ++Dy)
				{
					const FIntPoint Q = From + FIntPoint(Dx, Dy);
					if (FMath::Max(FMath::Abs(Dx), FMath::Abs(Dy)) != Rr || !Section->IsWalkable(Q)) continue;
					const float D = FVector::Dist2D(Section->LocalToWorld(Q), L);
					if (D < Bd) { Bd = D; Bq = Q; }
				}
				if (Bq != From) { From = Bq; bFromMoved = true; break; }
			}
		TArray<FVector> P;
		if (bFound && From != Best) P = Section->FindPathWorld(Section->LocalToWorld(From), Section->LocalToWorld(Best));
		const bool bNear = FVector::Dist2D(L, Tw.At) < 450.f;
		if (P.Num() < 2 && !bNear) continue;
		if (P.Num() > 160) continue;
		Gen->ClaimTownWork(W, this);
		JobI = J; WorkAt = W; GoFails = 0;
		GlideTo = FVector(Tw.At.X, Tw.At.Y, L.Z);
		if (P.Num() >= 2) { if (!bFromMoved) P.RemoveAt(0); for (FVector& Q : P) Q.Z = L.Z; Path = P; Act = 1; ++Walks; }
		else Act = 2;
		// (on the way to serve, the tray already in its hands)
		if (Tw.Kind == TEXT("CarryIdle")) SetProp(Tw.Prop);
		return;
	}
	// (every place of its round taken: a short stroll, then it looks again)
	Act = 4; WorkUntil = Now + R.FRandRange(5.f, 12.f); NextTrip = Now;
}

void ARDTownsfolk::BeginWork(float Now)
{
	if (!Section || !Section->TownWorks.IsValidIndex(WorkAt)) { Act = 0; return; }
	const ARDSection::FTownWork& Tw = Section->TownWorks[WorkAt];
	const FVector L = GetActorLocation();
	SetActorLocation(FVector(Tw.At.X, Tw.At.Y, L.Z), false);
	SetActorRotation(FRotator(0.f, Tw.Yaw, 0.f));
	Path.Reset();
	UAnimationAsset* A = WorkClip(Tw.Kind);
	if (!A) A = Tw.Kind == TEXT("Talk") || Tw.Kind == TEXT("CarryIdle") ? WorkClip(TEXT("Talk")) : nullptr;
	PlayAnim(A ? A : IdleAnim.Get(), 1.f);
	if (const UAnimSequenceBase* S = Cast<UAnimSequenceBase>(A)) Body->SetPosition(R.FRandRange(0.f, S->GetPlayLength()));
	SetProp(Tw.Prop);
	Act = 3;
	WorkUntil = Now + R.FRandRange(JobMin, JobMax);
	KindsDone.Add(FString::Printf(TEXT("%s@%d"), *Tw.Kind.ToString(), (int32)Tw.Group)); ++JobsDone;
}

void ARDTownsfolk::EndWork()
{
	if (Gen && WorkAt >= 0) Gen->ReleaseTownWork(WorkAt, this);
	WorkAt = -1;
	SetProp(NAME_None);
	Path.Reset();
	Act = 0;
	SetClip(false);
}

bool ARDTownsfolk::TickWork(float Now, float Dt)
{
	if (Jobs.Num() == 0 || bWentHome) return false;
	switch (Act)
	{
	case 3:
		if (Now >= WorkUntil) { EndWork(); NextJob(Now); }
		return true;
	case 1:
		// (its way was blocked: on to the next place of its round (tried again, the same place held the innkeeper for good))
		if (Path.Num() == 0 && Now >= NextTrip)
		{
			EndWork();
			NextJob(Now);
		}
		return true;
	case 4:
		// (strolling: the old round below until its time is up)
		if (Now >= WorkUntil) { Act = 0; NextJob(Now); return true; }
		return false;
	default:
		if (Now >= NextTrip) NextJob(Now);
		return true;
	}
}

FString ARDTownsfolk::GetWorkState() const
{
	const float Now = GetWorld() ? GetWorld()->GetTimeSeconds() : 0.f;
	TArray<FString> Kd = KindsDone.Array(); Kd.Sort();
	TArray<FString> Js; for (const int32 J : Jobs) Js.Add(FString::FromInt(J));
	static const TCHAR* States[] = { TEXT("none"), TEXT("going"), TEXT("gliding"), TEXT("working"), TEXT("strolling") };
	return FString::Printf(TEXT("%s|%d|%s|%.1f|%d|%s|%s|%.1f|%.1f"), States[FMath::Min<int32>(Act, 4)], WorkAt, *WorkKind().ToString(), FMath::Max(0.f, WorkUntil - Now), JobsDone,
		*FString::Join(Kd, TEXT(",")), *FString::Join(Js, TEXT(",")), JobMin, JobMax);
}

FString ARDTownsfolk::GetClipName() const
{
	return CurAnim ? CurAnim->GetName() : FString();
}

// ================================================================================================ the animals
ARDTownAnimal::ARDTownAnimal()
{
	PrimaryActorTick.bCanEverTick = true;
	Root = CreateDefaultSubobject<USceneComponent>(TEXT("Root"));
	RootComponent = Root;
	Body = CreateDefaultSubobject<USkeletalMeshComponent>(TEXT("Body"));
	Body->SetupAttachment(Root);
	Body->SetCollisionEnabled(ECollisionEnabled::NoCollision);
	Body->SetAnimationMode(EAnimationMode::AnimationSingleNode);
	Body->VisibilityBasedAnimTickOption = EVisibilityBasedAnimTickOption::OnlyTickPoseWhenRendered;
	Body->bEnableUpdateRateOptimizations = true;
}

void ARDTownAnimal::Init(ARDDungeonGenerator* InGenerator, int32 InDef, int32 InPen, const FVector& InPenAt, const FVector2D& InPenHalf, uint32 InSeed)
{
	Gen = InGenerator; Def = InDef; Pen = InPen; PenAt = InPenAt; PenHalf = InPenHalf;
	R.Initialize((int32)InSeed);
	if (!Gen || !Gen->TownAnimals.IsValidIndex(Def)) return;
	const FRDTownAnimalDef& D = Gen->TownAnimals[Def];
	Body->SetSkeletalMeshAsset(D.Mesh);
	Body->SetRelativeRotation(FRotator(0, D.MeshYaw, 0));
	Body->SetRelativeScale3D(FVector(D.Scale));
	Speed = FMath::Max(D.WalkSpeed, 5.f);
	SetState(R.RandRange(0, 1), GetWorld()->GetTimeSeconds());
	if (const UAnimSequenceBase* S = Cast<UAnimSequenceBase>(Body->AnimationData.AnimToPlay)) Body->SetPosition(R.FRandRange(0.f, S->GetPlayLength()));
}

void ARDTownAnimal::SetState(int32 S, float Now)
{
	if (!Gen || !Gen->TownAnimals.IsValidIndex(Def)) return;
	const FRDTownAnimalDef& D = Gen->TownAnimals[Def];
	State = S; ++Changes;
	UAnimationAsset* A = S == 1 && D.Graze ? D.Graze.Get() : S == 2 && D.Walk ? D.Walk.Get() : D.Idle.Get();
	if (A) Body->PlayAnimation(A, true);
	Body->SetPlayRate(1.f);
	if (S == 2)
	{
		// (somewhere else in the pen, kept its body's half length from the fence)
		const FVector2D H = (PenHalf - FVector2D(D.HalfSize.X, D.HalfSize.X)).ComponentMax(FVector2D(5.f, 5.f));
		To = PenAt + FVector(R.FRandRange(-H.X, H.X), R.FRandRange(-H.Y, H.Y), 0.f);
		Until = Now + 20.f;
	}
	else Until = Now + (S == 1 ? R.FRandRange(4.f, 11.f) : R.FRandRange(3.f, 8.f));
}

void ARDTownAnimal::Tick(float Dt)
{
	Super::Tick(Dt);
	if (!Gen) return;
	const float Now = GetWorld()->GetTimeSeconds();
	const FVector L = GetActorLocation();
	if (State == 2)
	{
		FVector D = To - L; D.Z = 0.f;
		if (D.Size() < 8.f || Now >= Until) { SetState(R.FRand() < 0.6f ? 1 : 0, Now); return; }
		const FRotator Want = D.Rotation();
		SetActorRotation(FRotator(0.f, FMath::RInterpConstantTo(GetActorRotation(), Want, Dt, 120.f).Yaw, 0.f));
		// (it walks the way it faces once it has nearly turned)
		if (FMath::Abs(FMath::FindDeltaAngleDegrees(GetActorRotation().Yaw, Want.Yaw)) < 35.f)
			SetActorLocation(L + GetActorForwardVector() * FMath::Min(Speed * Dt, D.Size()), false);
		return;
	}
	if (Now >= Until) SetState(R.FRand() < 0.45f ? 2 : State == 1 ? 0 : 1, Now);
}

// ================================================================================================ the generator's side
bool ARDDungeonGenerator::IsTownWorkFree(int32 Work, const ARDTownsfolk* T) const
{
	if (!TownWorkBy.IsValidIndex(Work)) return true;
	const ARDTownsfolk* By = TownWorkBy[Work].Get();
	return !By || By == T;
}

bool ARDDungeonGenerator::ClaimTownWork(int32 Work, ARDTownsfolk* T)
{
	if (Work < 0) return false;
	if (TownWorkBy.Num() <= Work) TownWorkBy.SetNum(Work + 1);
	if (!IsTownWorkFree(Work, T)) return false;
	TownWorkBy[Work] = T;
	return true;
}

void ARDDungeonGenerator::ReleaseTownWork(int32 Work, const ARDTownsfolk* T)
{
	if (TownWorkBy.IsValidIndex(Work) && TownWorkBy[Work].Get() == T) TownWorkBy[Work] = nullptr;
}

void ARDDungeonGenerator::SpawnTownAnimals()
{
	for (ARDTownAnimal* A : TownAnimalActors) if (IsValid(A)) A->Destroy();
	TownAnimalActors.Reset();
	const ARDSection* S = GetSection(FIntPoint::ZeroValue);
	if (!S) return;
	FActorSpawnParameters Sp; Sp.SpawnCollisionHandlingOverride = ESpawnActorCollisionHandlingMethod::AlwaysSpawn;
	for (int32 P = 0; P < S->TownPens.Num(); ++P)
	{
		const ARDSection::FTownPen& Pn = S->TownPens[P];
		if (!TownAnimals.IsValidIndex(Pn.Animal) || !TownAnimals[Pn.Animal].Mesh) continue;
		const FRDTownAnimalDef& D = TownAnimals[Pn.Animal];
		FRandomStream R((int32)HashCombine((uint32)StartSeed, (uint32)P * 2654435761u));
		const int32 Count = R.RandRange(FMath::Min(D.PenMin, D.PenMax), FMath::Max(D.PenMin, D.PenMax));
		const FVector2D H = (Pn.Half - FVector2D(D.HalfSize.X, D.HalfSize.X)).ComponentMax(FVector2D(5.f, 5.f));
		for (int32 K = 0; K < Count; ++K)
		{
			const FVector At(Pn.At.X + R.FRandRange(-H.X, H.X), Pn.At.Y + R.FRandRange(-H.Y, H.Y), S->GetActorLocation().Z);
			ARDTownAnimal* A = GetWorld()->SpawnActor<ARDTownAnimal>(ARDTownAnimal::StaticClass(), FTransform(FRotator(0, R.FRandRange(0.f, 360.f), 0), At), Sp);
			if (!A) continue;
			A->Init(this, Pn.Animal, P, FVector(Pn.At.X, Pn.At.Y, At.Z), Pn.Half, R.RandHelper(0x7fffffff));
			TownAnimalActors.Add(A);
		}
	}
	UE_LOG(LogRDTownLife, Log, TEXT("RDTOWN %d animals in %d pens"), TownAnimalActors.Num(), S->TownPens.Num());
}

void ARDDungeonGenerator::SpawnTownSpits()
{
	for (USceneComponent* C : TownSpitTurners) if (IsValid(C)) C->DestroyComponent(true);
	TownSpitTurners.Reset(); TownSpitCrank.Reset();
	const ARDSection* S = GetSection(FIntPoint::ZeroValue);
	if (!S) return;
	for (int32 I = 0; I < S->TownSpits.Num(); ++I)
	{
		const FVector4 Sp = S->TownSpits[I];
		// (a pivot along the rod's way, turned about its own X; the rod a thin charred cylinder 2 m long, the meat on it)
		USceneComponent* Pv = NewObject<USceneComponent>(this);
		Pv->SetupAttachment(GetRootComponent());
		Pv->SetMobility(EComponentMobility::Movable);
		Pv->RegisterComponent();
		Pv->SetWorldLocationAndRotation(FVector(Sp.X, Sp.Y, Sp.Z), FRotator(0.f, Sp.W, 0.f));
		if (TownSpitRod)
		{
			UStaticMeshComponent* Rd = NewObject<UStaticMeshComponent>(this);
			Rd->SetStaticMesh(TownSpitRod);
			if (TownSpitRodMaterial) Rd->SetMaterial(0, TownSpitRodMaterial);
			Rd->SetCollisionEnabled(ECollisionEnabled::NoCollision);
			Rd->SetupAttachment(Pv);
			// (the engine's cylinder: 100 cm along its Z round its middle, 100 across)
			Rd->SetRelativeTransform(FTransform(FRotator(90.f, 0.f, 0.f), FVector::ZeroVector, FVector(0.045f, 0.045f, 2.1f)));
			Rd->RegisterComponent();
		}
		if (TownSpitMeat)
			for (int32 K = -1; K <= 1; K += 2)
			{
				UStaticMeshComponent* Mt = NewObject<UStaticMeshComponent>(this);
				Mt->SetStaticMesh(TownSpitMeat);
				Mt->SetCollisionEnabled(ECollisionEnabled::NoCollision);
				Mt->SetupAttachment(Pv);
				const FBox Bx = TownSpitMeat->GetBoundingBox();
				Mt->SetRelativeTransform(FTransform(FRotator(0.f, 90.f, 0.f), FVector(K * 28.f, 0.f, 0.f) - FRotator(0.f, 90.f, 0.f).RotateVector(Bx.GetCenter())));
				Mt->RegisterComponent();
			}
		TownSpitTurners.Add(Pv);
		int32 Crank = -1;
		for (int32 W = 0; W < S->TownWorks.Num(); ++W) if (S->TownWorks[W].Kind == TEXT("Crank") && S->TownWorks[W].Thing == I) { Crank = W; break; }
		TownSpitCrank.Add(Crank);
	}
}

void ARDDungeonGenerator::TickTownLife(float Dt)
{
	// (a spit turns while someone turns its crank: a turn every two seconds, as the Crank clip's hand goes round)
	for (int32 I = 0; I < TownSpitTurners.Num(); ++I)
	{
		USceneComponent* Pv = TownSpitTurners[I];
		if (!IsValid(Pv) || !TownSpitCrank.IsValidIndex(I)) continue;
		const int32 W = TownSpitCrank[I];
		const ARDTownsfolk* By = TownWorkBy.IsValidIndex(W) ? TownWorkBy[W].Get() : nullptr;
		if (!By || !By->IsAtWork() || By->GetWorkAt() != W) continue;
		Pv->AddLocalRotation(FRotator(0.f, 0.f, 180.f * Dt));
	}
}

void ARDDungeonGenerator::SpawnTownLife()
{
	ARDSection* S = GetSection(FIntPoint::ZeroValue);
	if (!S) return;
	TownWorkBy.Reset(); TownWorkBy.SetNum(S->TownWorks.Num());
	const TArray<ARDSection::FTownWork>& Wk = S->TownWorks;
	FRandomStream R((int32)HashCombine((uint32)StartSeed, 0x11FEu));
	// (the nearest place of a group to a point, not already in a list, within a reach)
	auto Nearest = [&](const FVector& From, TFunctionRef<bool(const ARDSection::FTownWork&)> Pass, const TArray<int32>& Not, float Max) -> int32
	{
		int32 Best = -1; float Bd = Max;
		for (int32 I = 0; I < Wk.Num(); ++I)
		{
			if (Not.Contains(I) || !Pass(Wk[I])) continue;
			const float D = FVector::Dist2D(Wk[I].At, From);
			if (D < Bd) { Bd = D; Best = I; }
		}
		return Best;
	};
	auto Group = [](uint8 G) { return [G](const ARDSection::FTownWork& W) { return W.Group == G; }; };
	auto Shuffle = [&](TArray<int32>& A) { for (int32 I = A.Num() - 1; I > 0; --I) A.Swap(I, R.RandRange(0, I)); };
	// (each townsperson's own range: its least time at a place from TownWorkSeconds' range, its most 1.6 to 2.6 times that)
	auto Give = [&](ARDTownsfolk* T, const TArray<int32>& Jobs)
	{
		if (Jobs.Num() == 0) return;
		const float Mn = R.FRandRange(TownWorkSeconds.X, FMath::Max(TownWorkSeconds.X, TownWorkSeconds.Y * 0.6f));
		T->SetJobs(Jobs, Mn, Mn * R.FRandRange(1.6f, 2.6f));
	};
	TArray<int32> Taverns;
	for (int32 B = 0; B < S->TownBlds.Num(); ++B) if (S->TownBlds[B].Kind == TK_Tavern) Taverns.Add(B);
	int32 Given = 0;
	for (ARDTownsfolk* T : TownPeople)
	{
		if (!IsValid(T)) continue;
		const FVector P = T->Post;
		TArray<int32> J;
		auto Add = [&](int32 I) { if (I >= 0 && !J.Contains(I)) J.Add(I); };
		switch (T->TownRole)
		{
		case ERDTownRole::Townsfolk:
		{
			if (!T->IsResident()) break;
			// (its own home's garden, pen, fire first; then the nearest of each kind it lacks, and a chat at the well or the
			// market; a stroll; at least three kinds of work)
			const int32 H = T->GetHomeBuilding();
			for (int32 I = 0; I < Wk.Num(); ++I) if (Wk[I].Bld == H && H >= 0) Add(I);
			auto Has = [&](uint8 G) { return J.ContainsByPredicate([&](int32 I) { return Wk[I].Group == G; }); };
			if (!Has(TW_Garden)) Add(Nearest(P, Group(TW_Garden), J, 6000.f));
			if (!Has(TW_Pen)) Add(Nearest(P, Group(TW_Pen), J, 6000.f));
			if (!Has(TW_Pot) && !Has(TW_Spit)) Add(Nearest(P, [](const ARDSection::FTownWork& W) { return W.Group == TW_Pot || W.Group == TW_Spit; }, J, 6000.f));
			Add(Nearest(P, Group(TW_Chat), J, 9000.f));
			Shuffle(J);
			J.Add(-1);
			break;
		}
		case ERDTownRole::Child:
			Add(Nearest(P, Group(TW_Pen), J, 8000.f)); Add(Nearest(P, Group(TW_Chat), J, 9000.f)); J.Add(-1); Shuffle(J);
			break;
		case ERDTownRole::Refugee:
			for (int32 I = 0; I < Wk.Num(); ++I) if (Wk[I].Group == TW_Camp) Add(I);
			Shuffle(J); J.Add(-1);
			break;
		case ERDTownRole::Smith:
			for (int32 I = 0; I < Wk.Num(); ++I) if (Wk[I].Group == TW_Smithy && Wk[I].Bld == T->GetHomeBuilding()) Add(I);
			break;
		case ERDTownRole::Innkeeper:
		{
			const int32 B = T->GetHomeBuilding();
			Add(Nearest(P, [B](const ARDSection::FTownWork& W) { return W.Bld == B && W.Group == TW_Bar && W.Kind == TEXT("CarryIdle"); }, J, 1e9f));
			for (int32 I = 0; I < Wk.Num(); ++I) if (Wk[I].Bld == B && Wk[I].Group == TW_Serve) { Add(I); Add(Nearest(P, [B](const ARDSection::FTownWork& W) { return W.Bld == B && W.Group == TW_Bar && W.Kind == TEXT("CarryIdle"); }, J, 1e9f)); }
			Add(Nearest(P, [B](const ARDSection::FTownWork& W) { return W.Bld == B && W.Group == TW_Bar && W.Kind == TEXT("Talk"); }, J, 1e9f));
			break;
		}
		case ERDTownRole::Drunk:
			Add(Nearest(P, Group(TW_Seat), J, 4000.f)); Add(Nearest(P, Group(TW_Bar), J, 4000.f)); J.Add(-1);
			break;
		case ERDTownRole::Preacher: case ERDTownRole::Idiot:
			Add(Nearest(P, Group(TW_Chat), J, 9000.f)); { TArray<int32> J2 = J; Add(Nearest(P, Group(TW_Chat), J2, 12000.f)); } J.Add(-1);
			if (T->TownRole == ERDTownRole::Idiot) Add(Nearest(P, Group(TW_Pen), J, 12000.f));
			break;
		default: break;
		}
		// (three kinds of work at least in every round (the user's): the nearest place of a kind it has not got, however far,
		// chatting first, then a pen, a garden, a pot, a spit)
		if (J.Num() > 0)
		{
			auto Kinds = [&]()
			{
				TSet<FString> K;
				for (const int32 I : J) K.Add(I < 0 ? FString(TEXT("stroll")) : FString::Printf(TEXT("%s@%d"), *Wk[I].Kind.ToString(), (int32)Wk[I].Group));
				return K;
			};
			for (const uint8 Gp : { (uint8)TW_Chat, (uint8)TW_Pen, (uint8)TW_Garden, (uint8)TW_Pot, (uint8)TW_Spit })
			{
				if (Kinds().Num() >= 3) break;
				if (J.ContainsByPredicate([&](int32 I) { return I >= 0 && Wk[I].Group == Gp; })) continue;
				Add(Nearest(P, Group(Gp), J, 1e9f));
			}
		}
		if (J.Num() > 0) { Give(T, J); ++Given; }
	}
	// the tavern's customers and a server (the third list: "taverns with customers in them being served by villagers"): a
	// grown townsperson's body for each, a share of the seats; each customer between two seats and the bar, the server between
	// the bar and the tables
	TArray<int32> Adults;
	for (int32 I = 0; I < Townsfolk.Num(); ++I)
		if (Townsfolk[I].Mesh && Townsfolk[I].Role == ERDTownRole::Townsfolk && Townsfolk[I].Scale >= 0.95f && Townsfolk[I].WorkClips.Contains(TEXT("SitDrink"))) Adults.Add(I);
	int32 Customers = 0, Servers = 0;
	FActorSpawnParameters Spp; Spp.SpawnCollisionHandlingOverride = ESpawnActorCollisionHandlingMethod::AlwaysSpawn;
	auto SpawnAt = [&](int32 DefI, const FVector& At, float Yaw, int32 Bld, uint32 Seed) -> ARDTownsfolk*
	{
		const FVector P = FVector(At.X, At.Y, S->GetActorLocation().Z + 92.f);
		ARDTownsfolk* T = GetWorld()->SpawnActor<ARDTownsfolk>(ARDTownsfolk::StaticClass(), FTransform(FRotator(0, Yaw, 0), P), Spp);
		if (!T) return nullptr;
		T->Init(this, S, DefI, P, Yaw, 250.f, Seed);
		T->SetHome(Bld, P, false);
		TownPeople.Add(T);
		return T;
	};
	if (Adults.Num() > 0)
		for (const int32 B : Taverns)
		{
			TArray<int32> Seats, Serve, BarTalk;
			for (int32 I = 0; I < Wk.Num(); ++I)
			{
				if (Wk[I].Bld != B) continue;
				if (Wk[I].Group == TW_Seat) Seats.Add(I);
				if (Wk[I].Group == TW_Serve) Serve.Add(I);
				if (Wk[I].Group == TW_Bar && Wk[I].Kind == TEXT("Talk")) BarTalk.Add(I);
			}
			const int32 Nc = FMath::Clamp(FMath::RoundToInt(Seats.Num() * TownPatronShare), FMath::Min(2, Seats.Num()), Seats.Num());
			for (int32 K = 0; K < Nc; ++K)
			{
				const int32 First = Seats[K], Other = Seats[(K + Nc) % Seats.Num()];
				ARDTownsfolk* T = SpawnAt(Adults[(K + B) % Adults.Num()], Wk[First].At, Wk[First].Yaw, B, HashCombine((uint32)StartSeed, (uint32)(0xC057u + K * 131u + B * 7u)));
				if (!T) continue;
				TArray<int32> J = { First };
				if (BarTalk.Num()) J.Add(BarTalk[K % BarTalk.Num()]);
				if (Other != First) J.Add(Other);
				J.Add(Seats[(K + 1) % Seats.Num()]);
				TArray<int32> Uniq; for (const int32 I : J) Uniq.AddUnique(I);
				const float Mn = R.FRandRange(TownWorkSeconds.X * 1.5f, TownWorkSeconds.Y);
				T->SetJobs(Uniq, Mn, Mn * R.FRandRange(1.6f, 2.4f));
				// (seated at its first seat from the start)
				T->JobI = -1;
				++Customers;
			}
			if (Serve.Num() >= 3)
			{
				int32 Tk = -1;
				for (int32 I = 0; I < Wk.Num(); ++I) if (Wk[I].Bld == B && Wk[I].Group == TW_Bar && Wk[I].Kind == TEXT("CarryIdle")) { Tk = I; break; }
				const FVector At = Tk >= 0 ? Wk[Tk].At : Wk[Serve[0]].At;
				ARDTownsfolk* T = SpawnAt(Adults[(B + 3) % Adults.Num()], At + FVector(60.f, 60.f, 0.f), 0.f, B, HashCombine((uint32)StartSeed, (uint32)(0x5E4Fu + B)));
				if (T)
				{
					TArray<int32> J;
					for (int32 Q = Serve.Num() - 1; Q >= 0; --Q) { J.Add(Serve[Q]); if (Tk >= 0) J.Add(Tk); }
					if (BarTalk.Num()) J.Add(BarTalk.Last());
					const float Mn = R.FRandRange(TownWorkSeconds.X * 0.5f, TownWorkSeconds.X);
					T->SetJobs(J, Mn, Mn * R.FRandRange(1.5f, 2.2f));
					++Servers;
				}
			}
		}
	UE_LOG(LogRDTownLife, Log, TEXT("RDTOWN life: %d places of work, %d townspeople given a round, %d customers, %d servers"), Wk.Num(), Given, Customers, Servers);
	SpawnTownAnimals();
	SpawnTownSpits();
}

TArray<FString> ARDDungeonGenerator::GetTownLifeLines() const
{
	TArray<FString> Out;
	const ARDSection* S = GetSection(FIntPoint::ZeroValue);
	if (!S) return Out;
	for (int32 I = 0; I < S->TownWorks.Num(); ++I)
	{
		const ARDSection::FTownWork& W = S->TownWorks[I];
		const ARDTownsfolk* By = TownWorkBy.IsValidIndex(I) ? TownWorkBy[I].Get() : nullptr;
		Out.Add(FString::Printf(TEXT("work|%d|%s|%d|%.0f|%.0f|%d|%d"), I, *W.Kind.ToString(), (int32)W.Group, W.At.X, W.At.Y, By ? TownPeople.IndexOfByKey(By) : -1, By && By->IsAtWork() && By->GetWorkAt() == I ? 1 : 0));
	}
	for (int32 I = 0; I < TownPeople.Num(); ++I)
	{
		const ARDTownsfolk* T = TownPeople[I];
		if (!IsValid(T) || T->GetJobs().Num() == 0) continue;
		const UEnum* E = StaticEnum<ERDTownRole>();
		const FVector L = T->GetActorLocation();
		Out.Add(FString::Printf(TEXT("folk|%d|%s|%s|%.0f|%.0f|%s"), I, E ? *E->GetNameStringByValue((int64)T->TownRole) : TEXT("?"), *T->GetWorkState(), L.X, L.Y, *T->GetClipName()));
	}
	for (int32 I = 0; I < TownAnimalActors.Num(); ++I)
	{
		const ARDTownAnimal* A = TownAnimalActors[I];
		if (!IsValid(A)) continue;
		const FVector L = A->GetActorLocation();
		Out.Add(FString::Printf(TEXT("animal|%d|%s|%.0f|%.0f|%.0f|%d|%d|%d"), I, TownAnimals.IsValidIndex(A->Def) ? *TownAnimals[A->Def].Name.ToString() : TEXT("?"), L.X, L.Y, L.Z, A->Pen, A->GetState(), A->GetChanges()));
	}
	for (int32 I = 0; I < TownSpitTurners.Num(); ++I)
	{
		const USceneComponent* Pv = TownSpitTurners[I];
		Out.Add(FString::Printf(TEXT("spit|%d|%.1f|%d"), I, IsValid(Pv) ? Pv->GetRelativeRotation().Roll : 0.f, TownSpitCrank.IsValidIndex(I) ? TownSpitCrank[I] : -1));
	}
	return Out;
}
