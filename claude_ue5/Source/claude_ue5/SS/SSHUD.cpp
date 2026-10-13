#include "SS/SSHUD.h"
#include "SS/SSArena.h"
#include "SS/SSFighter.h"
#include "SS/SSPlayerController.h"
#include "SS/SSTarget.h"
#include "Engine/Canvas.h"
#include "Engine/Engine.h"
#include "Engine/Font.h"

static const FLinearColor SSGreen(0.45f, 1.f, 0.62f, 1.f);
static const FLinearColor SSAmber(1.f, 0.78f, 0.25f, 1.f);
static const FLinearColor SSRed(1.f, 0.32f, 0.25f, 1.f);
static const FLinearColor SSInk(0.86f, 0.93f, 1.f, 1.f);

static FLinearColor SSFade(const FLinearColor& C, float A) { return FLinearColor(C.R, C.G, C.B, C.A * A); }

void ASSHUD::Ring(const FVector2D& C, float Radius, const FLinearColor& Col, float Thickness, int32 Sides)
{
	FVector2D P = C + FVector2D(Radius, 0.f);
	for (int32 I = 1; I <= Sides; ++I)
	{
		const float A = 2.f * PI * I / Sides;
		const FVector2D Q = C + FVector2D(FMath::Cos(A), FMath::Sin(A)) * Radius;
		DrawLine(P.X, P.Y, Q.X, Q.Y, Col, Thickness);
		P = Q;
	}
}

void ASSHUD::Bracket(const FVector2D& C, float Half, const FLinearColor& Col, float Thickness)
{
	const float K = Half * 0.38f;
	for (int32 Sx = -1; Sx <= 1; Sx += 2)
		for (int32 Sy = -1; Sy <= 1; Sy += 2)
		{
			const FVector2D P = C + FVector2D(Sx * Half, Sy * Half);
			DrawLine(P.X, P.Y, P.X - Sx * K, P.Y, Col, Thickness);
			DrawLine(P.X, P.Y, P.X, P.Y - Sy * K, Col, Thickness);
		}
}

void ASSHUD::Bar(float X, float Y, float W, float H, float Fraction, const FLinearColor& Col, const FString& Label, const FString& Value)
{
	const float Sc = Canvas->ClipY / 1080.f;
	UFont* Small = GEngine->GetSmallFont();
	DrawRect(FLinearColor(0.02f, 0.04f, 0.06f, 0.55f), X - 3.f * Sc, Y - 3.f * Sc, W + 6.f * Sc, H + 6.f * Sc);
	DrawRect(SSFade(Col, 0.22f), X, Y, W, H);
	DrawRect(Col, X, Y, W * FMath::Clamp(Fraction, 0.f, 1.f), H);
	DrawText(Label, SSInk, X, Y - 20.f * Sc, Small, Sc * 1.05f);
	float Tw, Th; GetTextSize(Value, Tw, Th, Small, Sc * 1.05f);
	DrawText(Value, SSInk, X + W - Tw, Y - 20.f * Sc, Small, Sc * 1.05f);
}

void ASSHUD::DrawHUD()
{
	Super::DrawHUD();
	LastBrackets = 0; bLastLeadMark = false;
	if (!Canvas) return;
	const ASSFighter* F = Cast<ASSFighter>(GetOwningPawn());
	if (!F) return;
	const ASSPlayerController* PC = Cast<ASSPlayerController>(GetOwningPlayerController());
	const ASSArena* Arena = F->GetArena();
	const float Sc = Canvas->ClipY / 1080.f, CX = Canvas->ClipX, CY = Canvas->ClipY;
	const float Now = GetWorld()->GetTimeSeconds();
	UFont* Small = GEngine->GetSmallFont();
	UFont* Medium = GEngine->GetMediumFont();
	const FVector L = F->GetActorLocation(), Fw = F->GetActorForwardVector();
	const bool bPad = PC && PC->IsUsingGamepad();
	auto Proj = [&](const FVector& W, FVector2D& S) { const FVector P = Canvas->Project(W); S = FVector2D(P.X, P.Y); return P.Z > 0.f; };
	auto Centered = [&](const FString& T, const FLinearColor& Col, float Y, UFont* Font, float Scale, bool bBox)
	{
		float Tw, Th; GetTextSize(T, Tw, Th, Font, Scale);
		const float X = (CX - Tw) * 0.5f;
		if (bBox) DrawRect(FLinearColor(0.02f, 0.03f, 0.05f, 0.6f * Col.A), X - 16.f * Sc, Y - 7.f * Sc, Tw + 32.f * Sc, Th + 14.f * Sc);
		DrawText(T, Col, X, Y, Font, Scale);
	};

	if (F->IsDestroyed())
	{
		Centered(TEXT("FIGHTER DESTROYED"), SSRed, CY * 0.42f, Medium, Sc * 2.2f, true);
		Centered(TEXT("a new one is launched from the start point"), SSInk, CY * 0.42f + 58.f * Sc, Small, Sc * 1.3f, false);
	}
	else
	{
		// ---- targets: brackets on the drones ahead, the locked one in amber with its range, hull and lead mark
		const ASSTarget* Locked = F->GetLockedTarget();
		if (Arena)
			for (const ASSTarget* T : Arena->AllTargets())
			{
				if (!T || !T->IsAlive() || (T->Kind != ESSTargetKind::Drone && T != Locked)) continue;
				const float Dist = FVector::Dist(T->GetActorLocation(), L);
				FVector2D S;
				if (Dist > 700000.f || !Proj(T->GetActorLocation(), S) || S.X < 0.f || S.X > CX || S.Y < 0.f || S.Y > CY) continue;
				// (bracket size: the target's apparent size, at least a readable minimum)
				FVector2D Edge; Proj(T->GetActorLocation() + F->GetActorUpVector() * T->GetRadius(), Edge);
				const float Half = FMath::Clamp((Edge - S).Size() * 1.25f, 14.f * Sc, 220.f * Sc);
				const bool bLock = T == Locked;
				const FLinearColor Col = bLock ? SSAmber : SSFade(SSRed, 0.85f);
				Bracket(S, Half, Col, (bLock ? 2.5f : 1.6f) * Sc);
				++LastBrackets;
				const FString D = FString::Printf(TEXT("%.0f m"), Dist / 100.f);
				DrawText(D, Col, S.X + Half + 6.f * Sc, S.Y - 8.f * Sc, Small, Sc);
				if (bLock)
				{
					const FString N = T->Kind == ESSTargetKind::Drone ? (T->TypeName.IsNone() ? FString(TEXT("DRONE")) : T->TypeName.ToString().ToUpper()) : T->Kind == ESSTargetKind::Container ? FString(TEXT("CONTAINER")) : FString(TEXT("ASTEROID"));
					float Tw, Th; GetTextSize(N, Tw, Th, Small, Sc * 1.05f);
					DrawText(N, Col, S.X - Tw * 0.5f, S.Y - Half - 22.f * Sc, Small, Sc * 1.05f);
					const float Bw = FMath::Max(Half * 2.f, 46.f * Sc);
					DrawRect(SSFade(Col, 0.25f), S.X - Bw * 0.5f, S.Y + Half + 6.f * Sc, Bw, 4.f * Sc);
					DrawRect(Col, S.X - Bw * 0.5f, S.Y + Half + 6.f * Sc, Bw * FMath::Clamp(T->Health / FMath::Max(T->MaxHealth, 1.f), 0.f, 1.f), 4.f * Sc);
				}
			}
		if (Locked)
		{
			FVector2D S;
			if (Proj(F->GetLeadPoint(), S) && S.X > 0.f && S.X < CX && S.Y > 0.f && S.Y < CY)
			{
				// shoot here: where the target will be when the bolts arrive
				Ring(S, 11.f * Sc, SSAmber, 2.f * Sc, 16);
				DrawLine(S.X - 4.f * Sc, S.Y, S.X + 4.f * Sc, S.Y, SSAmber, 2.f * Sc);
				DrawLine(S.X, S.Y - 4.f * Sc, S.X, S.Y + 4.f * Sc, SSAmber, 2.f * Sc);
				bLastLeadMark = true;
			}
			FVector2D Ts;
			const bool bFront = Proj(Locked->GetActorLocation(), Ts);
			if (!bFront || Ts.X < 0.f || Ts.X > CX || Ts.Y < 0.f || Ts.Y > CY)
			{
				// off screen: an arrow at the edge of the view toward it
				const FVector V = F->GetActorTransform().InverseTransformVectorNoScale(Locked->GetActorLocation() - L);
				const FVector2D D = FVector2D(V.Y, -V.Z).GetSafeNormal();
				const FVector2D P = FVector2D(CX, CY) * 0.5f + D * (CY * 0.42f), Rt(-D.Y, D.X);
				DrawLine(P.X, P.Y, P.X - D.X * 26.f * Sc + Rt.X * 13.f * Sc, P.Y - D.Y * 26.f * Sc + Rt.Y * 13.f * Sc, SSAmber, 3.f * Sc);
				DrawLine(P.X, P.Y, P.X - D.X * 26.f * Sc - Rt.X * 13.f * Sc, P.Y - D.Y * 26.f * Sc - Rt.Y * 13.f * Sc, SSAmber, 3.f * Sc);
			}
		}

		// ---- the nose (where the cannons fire) and the aim point the nose is chasing
		FVector2D Nose;
		if (Proj(L + Fw * F->Convergence, Nose))
		{
			const float G = 7.f * Sc, E = 20.f * Sc;
			for (int32 K = 0; K < 4; ++K)
			{
				const FVector2D D(K == 0 ? 1.f : K == 1 ? -1.f : 0.f, K == 2 ? 1.f : K == 3 ? -1.f : 0.f);
				DrawLine(Nose.X + D.X * G, Nose.Y + D.Y * G, Nose.X + D.X * E, Nose.Y + D.Y * E, SSGreen, 2.f * Sc);
			}
			DrawRect(SSGreen, Nose.X - 1.5f * Sc, Nose.Y - 1.5f * Sc, 3.f * Sc, 3.f * Sc);
			FVector2D AimS;
			if (F->GetAim().Size() > 0.25f && Proj(L + F->GetAimDirection() * F->Convergence, AimS))
			{
				Ring(AimS, 15.f * Sc, SSFade(SSInk, 0.9f), 2.f * Sc, 20);
				DrawLine(Nose.X, Nose.Y, AimS.X, AimS.Y, SSFade(SSInk, 0.28f), 1.5f * Sc);
			}
		}
	}

	// ---- scope: what is around the fighter (ahead in the middle, dead astern at the rim)
	{
		const FVector2D C(430.f * Sc, CY - 112.f * Sc);       // (beside the speed bars: the fighter itself fills the bottom middle)
		const float Rr = 86.f * Sc;
		DrawRect(FLinearColor(0.02f, 0.04f, 0.06f, 0.45f), C.X - Rr - 8.f * Sc, C.Y - Rr - 8.f * Sc, (Rr + 8.f * Sc) * 2.f, (Rr + 8.f * Sc) * 2.f);
		Ring(C, Rr, SSFade(SSGreen, 0.55f), 1.5f * Sc, 32);
		Ring(C, Rr * 0.5f, SSFade(SSGreen, 0.3f), 1.f * Sc, 24);
		DrawLine(C.X - Rr, C.Y, C.X + Rr, C.Y, SSFade(SSGreen, 0.18f), 1.f);
		DrawLine(C.X, C.Y - Rr, C.X, C.Y + Rr, SSFade(SSGreen, 0.18f), 1.f);
		const FTransform Tr = F->GetActorTransform();
		auto Blip = [&](const FVector& W, const FLinearColor& Col, float Size)
		{
			const FVector V = Tr.InverseTransformVectorNoScale(W - L).GetSafeNormal();
			const float A = FMath::Acos(FMath::Clamp((float)V.X, -1.f, 1.f)) / PI;
			const FVector2D D = FVector2D(V.Y, -V.Z).GetSafeNormal();
			const FVector2D P = C + D * (A * Rr);
			DrawRect(Col, P.X - Size * 0.5f, P.Y - Size * 0.5f, Size, Size);
		};
		if (Arena)
		{
			const ASSTarget* Locked = F->GetLockedTarget();
			for (const ASSTarget* T : Arena->AllTargets())
			{
				if (!T || !T->IsAlive()) continue;
				const float Dist = FVector::Dist(T->GetActorLocation(), L);
				if (T == Locked) Blip(T->GetActorLocation(), SSAmber, 7.f * Sc);
				else if (T->Kind == ESSTargetKind::Drone) Blip(T->GetActorLocation(), SSRed, 5.f * Sc);
				else if (Dist < 90000.f) Blip(T->GetActorLocation(), FLinearColor(0.6f, 0.62f, 0.66f, 0.7f), 3.f * Sc);
			}
			// the middle of the arena (the station): the way home
			Blip(Arena->GetActorLocation(), FLinearColor(0.4f, 0.75f, 1.f, 1.f), 7.f * Sc);
		}
	}

	// ---- flight: speed and throttle (bottom left); hull and weapons (bottom right)
	{
		const float X = 46.f * Sc, W = 250.f * Sc, H = 12.f * Sc;
		const float Speed = F->GetSpeed();
		Bar(X, CY - 118.f * Sc, W, H, Speed / FMath::Max(F->BoostSpeed, 1.f), F->IsBoosting() ? SSAmber : SSGreen, F->IsBoosting() ? TEXT("SPEED  AFTERBURNER") : TEXT("SPEED"), FString::Printf(TEXT("%.0f m/s"), Speed / 100.f));
		Bar(X, CY - 68.f * Sc, W, H, F->GetThrottle(), FLinearColor(0.4f, 0.75f, 1.f, 1.f), TEXT("THROTTLE"), FString::Printf(TEXT("%.0f %%"), F->GetThrottle() * 100.f));
		const float X2 = CX - 46.f * Sc - W;
		const float Hull = F->GetHull() / FMath::Max(F->MaxHull, 1.f);
		Bar(X2, CY - 118.f * Sc, W, H, Hull, Hull > 0.5f ? SSGreen : Hull > 0.25f ? SSAmber : SSRed, TEXT("HULL"), FString::Printf(TEXT("%.0f %%"), Hull * 100.f));
		// missiles: one pip a rail, hollow while it reloads
		const int32 Rails = F->MissileRails.Num(), Ready = F->GetMissilesReady();
		DrawText(TEXT("MISSILES"), SSInk, X2, CY - 88.f * Sc, Small, Sc * 1.05f);
		for (int32 I = 0; I < Rails; ++I)
		{
			const float Px = X2 + 96.f * Sc + I * 24.f * Sc, Py = CY - 86.f * Sc;
			if (I < Ready) DrawRect(SSAmber, Px, Py, 16.f * Sc, 12.f * Sc);
			else { DrawRect(SSFade(SSAmber, 0.22f), Px, Py, 16.f * Sc, 12.f * Sc); }
		}
		if (Ready < Rails) DrawText(FString::Printf(TEXT("reload %.1f s"), F->GetMissileReloadLeft()), SSFade(SSInk, 0.75f), X2 + 96.f * Sc + Rails * 24.f * Sc + 6.f * Sc, CY - 88.f * Sc, Small, Sc);
		DrawText(FString::Printf(TEXT("CANNONS   %d fired   %d hits"), F->ShotsFired, F->ShotsHit), SSFade(SSInk, 0.8f), X2, CY - 62.f * Sc, Small, Sc * 1.05f);
	}

	// ---- score (top left)
	if (Arena)
	{
		DrawText(FString::Printf(TEXT("SCORE  %d"), Arena->Score), SSInk, 46.f * Sc, 36.f * Sc, Medium, Sc * 1.5f);
		DrawText(FString::Printf(TEXT("drones %d destroyed, %d flying      asteroids %d destroyed, %d left      containers %d"), Arena->DronesDestroyed, Arena->CountTargets(ESSTargetKind::Drone),
			Arena->AsteroidsDestroyed, Arena->CountTargets(ESSTargetKind::Asteroid), Arena->ContainersDestroyed), SSFade(SSInk, 0.8f), 48.f * Sc, 74.f * Sc, Small, Sc * 1.05f);
	}

	// ---- warnings (top middle)
	if (!F->IsDestroyed())
	{
		const float Blink = 0.6f + 0.4f * FMath::Sin(Now * 9.f);
		if (F->IsReturning()) Centered(TEXT("OUTSIDE THE COMBAT AREA  -  TURNING BACK"), SSFade(SSRed, Blink), 96.f * Sc, Medium, Sc * 1.5f, true);
		else if (Arena && Arena->DistanceToEdge(L) < Arena->WarnMargin)
			Centered(FString::Printf(TEXT("EDGE OF THE COMBAT AREA IN %.0f m"), FMath::Max(0.f, Arena->DistanceToEdge(L)) / 100.f), SSFade(SSAmber, Blink), 96.f * Sc, Medium, Sc * 1.4f, true);
		else if (F->GetHull() < F->MaxHull * 0.3f) Centered(TEXT("HULL CRITICAL"), SSFade(SSRed, Blink), 96.f * Sc, Medium, Sc * 1.4f, true);
	}

	if (PC && Now < PC->MouseNoteUntil) Centered(FString::Printf(TEXT("MOUSE SENSITIVITY  x %.2f"), PC->MouseScale), SSInk, 140.f * Sc, Medium, Sc * 1.2f, true);

	// ---- controls (the first seconds, or H)
	const bool bHelp = (PC && PC->bShowHelp) || Now < HelpSeconds;
	if (bHelp)
	{
		const float A = (PC && PC->bShowHelp) ? 1.f : FMath::Clamp((HelpSeconds - Now) / 1.5f, 0.f, 1.f);
		static const TCHAR* Keys[] = { TEXT("W / S              throttle up / down"), TEXT("A / D              roll left / right"), TEXT("Mouse              point the nose      [ / ]  sensitivity"),
			TEXT("Left button / Space    cannons"), TEXT("Right button / Ctrl    missile (homes on the locked target)"), TEXT("Shift              afterburner"),
			TEXT("Tab                next target"), TEXT("Mouse wheel        camera distance"), TEXT("I  invert pitch    R  restart    H  help    Esc  quit") };
		static const TCHAR* Pad[] = { TEXT("Left stick up / down       throttle"), TEXT("Left stick left / right    roll"), TEXT("Right stick                point the nose"),
			TEXT("RT                         cannons"), TEXT("LT / RB                    missile (homes on the locked target)"), TEXT("A / left stick click       afterburner"),
			TEXT("Y                          next target"), TEXT("D-pad up / down            camera distance"), TEXT("View  restart     Menu  this help") };
		const TCHAR** Lines = bPad ? Pad : Keys;
		const float X = 46.f * Sc, Y0 = 120.f * Sc, Lh = 22.f * Sc;
		DrawRect(FLinearColor(0.02f, 0.03f, 0.05f, 0.55f * A), X - 12.f * Sc, Y0 - 10.f * Sc, 470.f * Sc, Lh * 10.f + 22.f * Sc);
		DrawText(bPad ? TEXT("XBOX CONTROLLER") : TEXT("KEYBOARD AND MOUSE"), SSFade(SSGreen, A), X, Y0, Small, Sc * 1.1f);
		for (int32 I = 0; I < 9; ++I) DrawText(Lines[I], SSFade(SSInk, A), X, Y0 + Lh * (I + 1.2f), Small, Sc * 1.05f);
	}
}

// ---------------------------------------------------------------------------------------------------------------------

ASSGameMode::ASSGameMode()
{
	DefaultPawnClass = nullptr;             // the fighter stands in the level and possesses itself
	PlayerControllerClass = ASSPlayerController::StaticClass();
	HUDClass = ASSHUD::StaticClass();
}
