// The wilderness's map (the user's spec of 2026-11-03: "the geographical features are a 3d stylized canvas, with the biomes
// and terrain represented by their realistic top down look ... a fog of war that disappears when the player walks into that
// area"): the world's own colours from above with its relief shaded, in 256-pixel tiles at zoom levels from the whole
// continent (level 0, 1.2 km a pixel) to 1.1 m a pixel (level 10), made from FRDWildWorld on worker threads as the map asks
// for them and kept a while (the least recently drawn dropped first); the fog over what she has not seen made for the view
// from the 50 m cells she revealed; the minimap's picture made from the tiles of its level. Fast travel: from the map, to a
// place she has found, not while a monster is after her (the user's choice of 2026-11-03).
#include "RD/RDDungeonGenerator.h"
#include "RD/RDWild.h"
#include "RD/RDWildChunkData.h"
#include "RD/RDSection.h"
#include "RD/RDMonster.h"
#include "RD/RDCombat.h"
#include "RD/RDGameInstance.h"
#include "Engine/Texture2D.h"
#include "Kismet/GameplayStatics.h"
#include "GameFramework/Character.h"
#include "GameFramework/CharacterMovementComponent.h"
#include "Async/Async.h"
#include "HAL/PlatformTime.h"

DEFINE_LOG_CATEGORY_STATIC(LogRDWildMap, Log, All);

struct FRDWMapTileData { FIntVector Key; TArray<FColor> Px; double Ms = 0.0; };
struct FRDWMapStream { TQueue<TSharedPtr<FRDWMapTileData, ESPMode::ThreadSafe>, EQueueMode::Mpsc> Done; };

namespace
{
	constexpr int32 RDWTileN = 256;
	FORCEINLINE float RDWMSmooth(float A, float B, float X) { const float T = FMath::Clamp((X - A) / (B - A), 0.f, 1.f); return T * T * (3.f - 2.f * T); }

	void RDWMakeTile(const FRDWildWorld& W, FRDWMapTileData& D)
	{
		const double T0 = FPlatformTime::Seconds();
		const int32 L = D.Key.X, I = D.Key.Y, J = D.Key.Z, N = RDWTileN, Nb = N + 2;
		const double Span = (W.Xn - W.Xs) / (double)(1 << L), Pm = Span / N;
		const double X1 = W.Xs + (I + 1) * Span, Y0 = W.Yw + J * Span;
		const bool bDetail = Pm < 30.0;
		TArray<float> H; H.SetNumUninitialized(Nb * Nb);
		TArray<FLinearColor> C; C.SetNumUninitialized(N * N);
		TArray<float> Can; Can.SetNumZeroed(N * N);
		TArray<uint8> Wet; Wet.SetNumZeroed(N * N);
		for (int32 R = 0; R < Nb; ++R)
			for (int32 Cc = 0; Cc < Nb; ++Cc)
			{
				const double X = X1 - (R - 0.5) * Pm, Y = Y0 + (Cc - 0.5) * Pm;
				FRDWSample S; W.Sample(X, Y, S, bDetail, (float)Pm);
				H[R * Nb + Cc] = S.WaterKind ? S.Water : S.H;
				if (R >= 1 && Cc >= 1 && R <= N && Cc <= N)
				{
					const int32 K = (R - 1) * N + (Cc - 1);
					C[K] = S.Color; Can[K] = S.Canopy; Wet[K] = S.WaterKind ? (uint8)S.WaterKind : 0;
					if (S.Lava > 0.4f) Wet[K] = 9;
				}
			}
		// the relief shaded from the north-west, more for the coarser levels (the reference's "3d canvas")
		const FVector Light = FVector(-0.55, 0.55, 0.63).GetSafeNormal();
		const float K = FMath::Clamp(1.6f + (float)(Pm / 35.0), 1.6f, 10.f);
		D.Px.SetNumUninitialized(N * N);
		for (int32 R = 0; R < N; ++R)
			for (int32 Cc = 0; Cc < N; ++Cc)
			{
				const int32 A = (R + 1) * Nb + (Cc + 1), Q = R * N + Cc;
				const float Dzde = (H[A + 1] - H[A - 1]) / (float)(2.0 * Pm), Dzdn = (H[A - Nb] - H[A + Nb]) / (float)(2.0 * Pm);
				const FVector Nr = FVector(-K * Dzde, -K * Dzdn, 1.f).GetSafeNormal();
				float Sh = FMath::Clamp((float)FVector::DotProduct(Nr, Light), 0.f, 1.f);
				if (Wet[Q] && Wet[Q] != 9) Sh = 0.78f;
				FLinearColor Col = C[Q] * (0.42f + 0.85f * Sh);
				// forests: darker, grainy with crowns where a pixel is a few metres
				if (Can[Q] > 0.02f)
				{
					const double X = X1 - (R + 0.5) * Pm, Y = Y0 + (Cc + 0.5) * Pm;
					float Gr = 0.5f;
					if (Pm < 10.0)
					{
						const int32 Gx = FMath::FloorToInt(X / 5.0), Gy = FMath::FloorToInt(Y / 5.0);
						const float Fx = (float)(X / 5.0 - Gx) - 0.5f, Fy = (float)(Y / 5.0 - Gy) - 0.5f;
						const float Rr = FMath::Sqrt(Fx * Fx + Fy * Fy);
						Gr = FRDWildWorld::Rand01(Gx, Gy, 7u) < Can[Q] ? (Rr < 0.42f ? 0.15f + 0.6f * (0.5f + Fx * 0.6f - Fy * 0.6f) : 0.9f) : 0.6f;
					}
					else Gr = 0.35f + 0.3f * FRDWildWorld::Rand01(FMath::FloorToInt(X / Pm), FMath::FloorToInt(Y / Pm), 9u);
					Col *= 1.f - Can[Q] * (0.18f + 0.32f * Gr);
				}
				if (Wet[Q] == 9) Col = FLinearColor(0.55f, 0.12f, 0.03f);
				const float Lum = Col.R * 0.3f + Col.G * 0.59f + Col.B * 0.11f;
				Col = FMath::Lerp(Col, FLinearColor(Lum, Lum * 1.02f, Lum * 1.06f), 0.22f);
				D.Px[Q] = Col.ToFColor(true);
			}
		D.Ms = (FPlatformTime::Seconds() - T0) * 1000.0;
	}

	UTexture2D* RDWTexture(int32 W, int32 H, const TArray<FColor>& Px, UObject* Outer)
	{
		UTexture2D* T = UTexture2D::CreateTransient(W, H, PF_B8G8R8A8);
		if (!T) return nullptr;
		T->SRGB = true; T->Filter = TF_Bilinear; T->AddressX = TA_Clamp; T->AddressY = TA_Clamp; T->LODGroup = TEXTUREGROUP_UI;
		void* Data = T->GetPlatformData()->Mips[0].BulkData.Lock(LOCK_READ_WRITE);
		FMemory::Memcpy(Data, Px.GetData(), (SIZE_T)W * H * sizeof(FColor));
		T->GetPlatformData()->Mips[0].BulkData.Unlock();
		T->UpdateResource();
		return T;
	}

	void RDWUpdateTexture(UTexture2D* T, const TArray<FColor>& Px)
	{
		// (a texture already made: its pixels sent again; the region's copy is the render thread's to free)
		const int32 W = T->GetSizeX(), H = T->GetSizeY();
		FColor* Copy = new FColor[(SIZE_T)W * H];
		FMemory::Memcpy(Copy, Px.GetData(), (SIZE_T)W * H * sizeof(FColor));
		FUpdateTextureRegion2D* Rg = new FUpdateTextureRegion2D(0, 0, 0, 0, W, H);
		T->UpdateTextureRegions(0, 1, Rg, W * sizeof(FColor), sizeof(FColor), (uint8*)Copy, [](uint8* Src, const FUpdateTextureRegion2D* R) { delete[] (FColor*)Src; delete R; });
	}
}

int32 ARDDungeonGenerator::WildMapLevelFor(double Mpp) const
{
	if (!Wild.IsValid()) return 0;
	const double Span = Wild->Xn - Wild->Xs;
	return FMath::Clamp(FMath::RoundToInt(FMath::Log2(Span / (RDWTileN * FMath::Max(Mpp, 0.01)))), 0, WildMapMaxLevel);
}

double ARDDungeonGenerator::WildMapTileSpan(int32 L) const
{
	return Wild.IsValid() ? (Wild->Xn - Wild->Xs) / (double)(1 << L) : 1.0;
}

UTexture2D* ARDDungeonGenerator::WildMapTile(int32 L, int32 I, int32 J, bool bAsk)
{
	if (!IsWildReady() || I < 0 || J < 0 || I >= (1 << L) || J >= (1 << L)) return nullptr;
	const FIntVector Key(L, I, J);
	if (TObjectPtr<UTexture2D>* T = WildMapTex.Find(Key)) { WildMapUsed.Add(Key, FPlatformTime::Seconds()); return *T; }
	if (bAsk && !WildMapPending.Contains(Key) && WildMapPending.Num() < WildMapMaxInFlight)
	{
		if (!WildMapStream.IsValid()) WildMapStream = MakeShared<FRDWMapStream, ESPMode::ThreadSafe>();
		WildMapPending.Add(Key);
		TSharedPtr<FRDWildWorld, ESPMode::ThreadSafe> W = Wild;
		TSharedPtr<FRDWMapStream, ESPMode::ThreadSafe> St = WildMapStream;
		TSharedPtr<FRDWMapTileData, ESPMode::ThreadSafe> D = MakeShared<FRDWMapTileData, ESPMode::ThreadSafe>(); D->Key = Key;
		Async(EAsyncExecution::ThreadPool, [W, St, D]() { RDWMakeTile(*W, *D); St->Done.Enqueue(D); });
	}
	return nullptr;
}

void ARDDungeonGenerator::TickWildMap(float Dt)
{
	if (!WildMapStream.IsValid()) return;
	const double T0 = FPlatformTime::Seconds();
	TSharedPtr<FRDWMapTileData, ESPMode::ThreadSafe> D;
	while (WildMapStream->Done.Dequeue(D))
	{
		WildMapPending.Remove(D->Key);
		if (UTexture2D* T = RDWTexture(RDWTileN, RDWTileN, D->Px, this)) { WildMapTex.Add(D->Key, T); WildMapUsed.Add(D->Key, T0); }
		if (D->Key.X == WildMiniLevel) WildMapCpu.Add(D->Key, MoveTemp(D->Px));
		WildMapTileMs = WildMapTileMs <= 0.0 ? D->Ms : FMath::Lerp(WildMapTileMs, D->Ms, 0.1);
		++WildMapTilesMade;
		if ((FPlatformTime::Seconds() - T0) * 1000.0 > 3.0) break;
	}
	// the least recently drawn tiles go past the limit (never the continent's first levels)
	if (WildMapTex.Num() > WildMapMaxTiles)
	{
		TArray<TPair<double, FIntVector>> Ages;
		for (const auto& Kv : WildMapUsed) if (Kv.Key.X > 2) Ages.Add({ Kv.Value, Kv.Key });
		Ages.Sort([](const TPair<double, FIntVector>& A, const TPair<double, FIntVector>& B) { return A.Key < B.Key; });
		for (int32 K = 0; K < Ages.Num() && WildMapTex.Num() > WildMapMaxTiles * 9 / 10; ++K)
		{
			WildMapTex.Remove(Ages[K].Value); WildMapUsed.Remove(Ages[K].Value); WildMapCpu.Remove(Ages[K].Value);
		}
	}
	if (WildMapCpu.Num() > 64)
	{
		TArray<FIntVector> Keys; WildMapCpu.GetKeys(Keys);
		for (const FIntVector& K : Keys) if (!WildMapTex.Contains(K)) WildMapCpu.Remove(K);
	}
}

// ------------------------------------------------------------------------------------------------ the fog over the view
float ARDDungeonGenerator::WildRevealedShare(double Xm, double Ym, double Radius) const
{
	// (fine: the cells round the point; coarse: how much of the 1.6 km block is revealed)
	if (Radius < 120.0)
	{
		int32 N = 0;
		for (int32 K = 0; K < 5; ++K)
		{
			static const double Ox[5] = { 0, 0.5, -0.5, 0.5, -0.5 }, Oy[5] = { 0, 0.5, 0.5, -0.5, -0.5 };
			if (IsWildRevealed(Xm + Ox[K] * Radius, Ym + Oy[K] * Radius)) ++N;
		}
		return N / 5.f;
	}
	const int32 I = FMath::FloorToInt(Xm / 1600.0), J = FMath::FloorToInt(Ym / 1600.0);
	const int32* C = WildRevealCount.Find(FIntPoint(I, J));
	return C ? FMath::Clamp(*C / 200.f, 0.f, 1.f) : 0.f;
}

UTexture2D* ARDDungeonGenerator::WildFog(const FVector2D& Mid, double Mpp, const FVector2D& SizePx, FVector2D& OutUV0, FVector2D& OutUV1)
{
	// (the view's half extents in metres: X north (the rows, up), Y east (the columns))
	const double Vhx = SizePx.Y * Mpp * 0.5, Vhy = SizePx.X * Mpp * 0.5;
	auto UVs = [&]()
	{
		const double Bx = WildFogFor.X, By = WildFogFor.Y, Bhx = WildFogFor.Z, Bhy = WildFogFor.W;
		OutUV0 = FVector2D((Mid.Y - Vhy - (By - Bhy)) / (2.0 * Bhy), ((Bx + Bhx) - (Mid.X + Vhx)) / (2.0 * Bhx));
		OutUV1 = FVector2D((Mid.Y + Vhy - (By - Bhy)) / (2.0 * Bhy), ((Bx + Bhx) - (Mid.X - Vhx)) / (2.0 * Bhx));
	};
	// (made over twice the view each way and kept while the view stays inside it at about its scale: made for the view's
	// own middle and scale, it was made again in every frame the map was dragged or zoomed: 65k texels of noise each)
	if (WildFogTex && WildFogVersion == WildRevealVersion && WildFogMpp > 0.0 && Mpp / WildFogMpp > 0.75 && Mpp / WildFogMpp < 1.5
		&& Mid.X - Vhx >= WildFogFor.X - WildFogFor.Z && Mid.X + Vhx <= WildFogFor.X + WildFogFor.Z
		&& Mid.Y - Vhy >= WildFogFor.Y - WildFogFor.W && Mid.Y + Vhy <= WildFogFor.Y + WildFogFor.W)
	{
		UVs(); return WildFogTex;
	}
	const int32 Fw = 384, Fh = FMath::Clamp(FMath::RoundToInt(384.0 * SizePx.Y / FMath::Max(SizePx.X, 1.0)), 48, 384);
	const double Bhx = Vhx * 2.0, Bhy = Vhy * 2.0;
	TArray<FColor> Px; Px.SetNumUninitialized(Fw * Fh);
	const double Tx = 2.0 * Bhy / Fw, Ty = 2.0 * Bhx / Fh;     // (a texel in metres)
	for (int32 R = 0; R < Fh; ++R)
		for (int32 C = 0; C < Fw; ++C)
		{
			const double X = Mid.X + (Fh * 0.5 - (R + 0.5)) * Ty, Y = Mid.Y + ((C + 0.5) - Fw * 0.5) * Tx;
			const float Sh = WildRevealedShare(X, Y, FMath::Max(Tx, Ty));
			// (parchment-grey clouds fixed to the world, thinning where she has been)
			// (clouds at the view's own scale and a finer one, so they read at every zoom)
			const double Sc = FMath::Max(Tx, 50.0) * 40.0;
			const float Cl = FMath::Clamp(0.5f + 0.45f * FRDWildWorld::Fbm(X, Y, 1.0 / Sc, 4, 911u) + 0.2f * FRDWildWorld::Fbm(X, Y, 4.0 / Sc, 2, 913u), 0.f, 1.f);
			const float A = 1.f - RDWMSmooth(0.05f, 0.7f, Sh);
			const FLinearColor Col = FMath::Lerp(FLinearColor(0.26f, 0.24f, 0.20f), FLinearColor(0.52f, 0.48f, 0.40f), Cl);
			FColor Fc = Col.ToFColor(true); Fc.A = (uint8)FMath::Clamp(A * 238.f, 0.f, 255.f);
			Px[R * Fw + C] = Fc;
		}
	if (!WildFogTex || WildFogTex->GetSizeX() != Fw || WildFogTex->GetSizeY() != Fh) WildFogTex = RDWTexture(Fw, Fh, Px, this);
	else RDWUpdateTexture(WildFogTex, Px);
	WildFogFor = FVector4(Mid.X, Mid.Y, Bhx, Bhy); WildFogMpp = Mpp; WildFogVersion = WildRevealVersion; ++WildFogBuilds;
	UVs();
	return WildFogTex;
}

// ------------------------------------------------------------------------------------------------ the minimap's picture
UTexture2D* ARDDungeonGenerator::WildMini(const FVector2D& At)
{
	const double Now = FPlatformTime::Seconds();
	if (WildMiniTex && Now - WildMiniTime < 0.2 && FVector2D::Distance(At, WildMiniFor) < 3.0) return WildMiniTex;
	const int32 N = 256, L = WildMiniLevel;
	const double Rm = WildMiniRadiusM, Tm = 2.0 * Rm / N;
	const double Span = WildMapTileSpan(L), Pm = Span / RDWTileN;
	TArray<FColor> Px; Px.SetNumUninitialized(N * N);
	for (int32 R = 0; R < N; ++R)
		for (int32 C = 0; C < N; ++C)
		{
			const double Dx = (N * 0.5 - (R + 0.5)) * Tm, Dy = ((C + 0.5) - N * 0.5) * Tm;
			const double X = At.X + Dx, Y = At.Y + Dy;
			const double Rr = FMath::Sqrt(Dx * Dx + Dy * Dy) / Rm;
			FColor Out(14, 16, 14, 0);
			if (Rr < 1.0)
			{
				const int32 Ti = FMath::FloorToInt((X - Wild->Xs) / Span), Tj = FMath::FloorToInt((Y - Wild->Yw) / Span);
				const FIntVector K(L, Ti, Tj);
				if (const TArray<FColor>* T = WildMapCpu.Find(K))
				{
					const int32 Pr = FMath::Clamp(FMath::FloorToInt((Wild->Xs + (Ti + 1) * Span - X) / Pm), 0, RDWTileN - 1);
					const int32 Pc = FMath::Clamp(FMath::FloorToInt((Y - (Wild->Yw + Tj * Span)) / Pm), 0, RDWTileN - 1);
					Out = (*T)[Pr * RDWTileN + Pc];
				}
				else { WildMapTile(L, Ti, Tj, true); Out = FColor(26, 28, 24); }
				if (!IsWildRevealed(X, Y)) Out = FColor(150, 144, 128);
				Out.A = (uint8)(255.f * FMath::Clamp((1.f - (float)Rr) / 0.12f, 0.f, 1.f));
			}
			Px[R * N + C] = Out;
		}
	if (!WildMiniTex) WildMiniTex = RDWTexture(N, N, Px, this);
	else RDWUpdateTexture(WildMiniTex, Px);
	WildMiniTime = Now; WildMiniFor = At;
	return WildMiniTex;
}

// ------------------------------------------------------------------------------------------------ the places she knows
void ARDDungeonGenerator::WildKnownPlaces(TArray<FRDWildPlace>& Out) const
{
	Out.Reset();
	if (!IsWildReady()) return;
	for (int32 Ti = 0; Ti < Wild->Towns.Num(); ++Ti)
	{
		const FRDWildTown& T = Wild->Towns[Ti];
		FRDWildPlace P; P.Id = FRDWildWorld::TownIdBase + Ti; P.Kind = T.Kind == TEXT("city") ? TEXT("city") : TEXT("town"); P.Name = T.Name; P.At = T.Site; P.H = T.H; P.Town = Ti;
		Out.Add(P);
	}
	for (const int32 Id : WildFound)
	{
		if (Id >= FRDWildWorld::TownIdBase) continue;
		FRDWildPlace P;
		if (Wild->FindPlace(Id, P)) Out.Add(P);
	}
}

bool ARDDungeonGenerator::IsWildCombat() const
{
	const APawn* Her = UGameplayStatics::GetPlayerPawn(this, 0);
	if (!Her) return false;
	const float D2 = FMath::Square(CombatMusicDistance);
	for (const ARDMonster* M : GetMonsters())
		if (M && !M->IsDead() && !M->IsAlly() && M->IsAggro() && FVector::DistSquared(M->GetActorLocation(), Her->GetActorLocation()) < D2) return true;
	return false;
}

// ------------------------------------------------------------------------------------------------ the map's keys
void ARDDungeonGenerator::OpenWildMap()
{
	if (const APawn* P = UGameplayStatics::GetPlayerPawn(this, 0)) WildMapCenter = FVector2D(P->GetActorLocation().X / 100.0, P->GetActorLocation().Y / 100.0);
	WildMapMpp = WildMapOpenMpp;
}

void ARDDungeonGenerator::TickWildMapInput(APlayerController* PC, float Dt)
{
	if (!PC || !IsWildReady()) return;
	auto Down = [&](const FKey& K) { return PC->IsInputKeyDown(K) ? 1.f : 0.f; };
	auto Hit = [&](const FKey& K) { return PC->WasInputKeyJustPressed(K); };
	// zoom: the wheel, + and -, the right stick; about the view's middle
	float Z = 0.f;
	if (Hit(EKeys::MouseScrollUp) || Hit(EKeys::Add) || Hit(EKeys::Equals)) Z -= 1.f;
	if (Hit(EKeys::MouseScrollDown) || Hit(EKeys::Subtract) || Hit(EKeys::Hyphen)) Z += 1.f;
	Z += (Down(EKeys::Gamepad_RightY) != 0.f ? -PC->GetInputAnalogKeyState(EKeys::Gamepad_RightY) * Dt * 3.f : 0.f);
	if (Z != 0.f) WildMapMpp = FMath::Clamp(WildMapMpp * FMath::Pow(1.3, (double)Z), WildMapMinMpp, WildMapMaxMpp);
	// pan: the arrows / D-pad / left stick, a left-mouse drag
	const float Nn = Down(EKeys::Up) + Down(EKeys::Gamepad_DPad_Up) - Down(EKeys::Down) - Down(EKeys::Gamepad_DPad_Down) + PC->GetInputAnalogKeyState(EKeys::Gamepad_LeftY);
	const float Ee = Down(EKeys::Right) + Down(EKeys::Gamepad_DPad_Right) - Down(EKeys::Left) - Down(EKeys::Gamepad_DPad_Left) + PC->GetInputAnalogKeyState(EKeys::Gamepad_LeftX);
	WildMapCenter += FVector2D(FMath::Clamp(Nn, -1.f, 1.f), FMath::Clamp(Ee, -1.f, 1.f)) * (WildMapMpp * 600.0 * Dt);
	float Mx, My;
	if (PC->IsInputKeyDown(EKeys::LeftMouseButton) && PC->GetMousePosition(Mx, My))
	{
		// (the map moves with the pointer: right is east (+Y), down is south (-X))
		if (bWildDrag) WildMapCenter += FVector2D((My - WildDragFrom.Y) * WildMapMpp, -(Mx - WildDragFrom.X) * WildMapMpp);
		WildDragFrom = FVector2D(Mx, My); bWildDrag = true;
	}
	else bWildDrag = false;
	WildMapCenter.X = FMath::Clamp(WildMapCenter.X, Wild->Xs, Wild->Xn); WildMapCenter.Y = FMath::Clamp(WildMapCenter.Y, Wild->Yw, Wild->Ye);
	// C (the right stick pressed): back over her
	if (Hit(EKeys::C) || Hit(EKeys::Gamepad_RightThumbstick)) OpenWildMap();
	// travel to the place under the view's middle (F, Enter, the pad's A)
	if (WildMapHover >= 0 && (Hit(EKeys::F) || Hit(EKeys::Enter) || Hit(EKeys::Gamepad_FaceButton_Bottom))) WildFastTravel(WildMapHover);
}

// ------------------------------------------------------------------------------------------------ fast travel
bool ARDDungeonGenerator::WildFastTravel(int32 PlaceId)
{
	WildTravelRefusal.Reset();
	if (!IsWildReady()) { WildTravelRefusal = TEXT("not ready"); return false; }
	FRDWildPlace P;
	if (!Wild->FindPlace(PlaceId, P)) { WildTravelRefusal = TEXT("no such place"); return false; }
	if (!WildFound.Contains(PlaceId)) { WildTravelRefusal = FString::Printf(TEXT("You have not found %s yet"), *P.Name); if (PlayerCombat) PlayerCombat->ShowMessage(WildTravelRefusal); return false; }
	if (IsWildCombat()) { WildTravelRefusal = TEXT("You cannot travel while enemies are near"); if (PlayerCombat) PlayerCombat->ShowMessage(WildTravelRefusal); return false; }
	APawn* Her = UGameplayStatics::GetPlayerPawn(this, 0);
	if (!Her) return false;
	const FVector2D From(Her->GetActorLocation().X / 100.0, Her->GetActorLocation().Y / 100.0);
	const double Km = FVector2D::Distance(From, P.At) / 1000.0;
	WildAutosave(TEXT("before travel"));
	if (bMapOpen) SetMapOpen(false);
	CloseTownPanel();
	// (the journey's hours: she walks about 5 km an hour)
	if (bDayNight && Km > 0.5)
	{
		float H = TownHour + (float)(Km / 5.0); int32 Days = 0;
		while (H >= 24.f) { H -= 24.f; ++Days; }
		TownHour = H; TownDay += Days;
		if (URDGameInstance* GI = URDGameInstance::Of(this)) { GI->TownHour = TownHour; GI->TownDay = TownDay; }
		ApplyDayNight();
	}
	// her things lying where she fell stay in the world they are in: dropped chunks take nothing of hers (piles are actors of
	// their own); the chunks round the place are made now
	WildDropAll();
	FVector2D To = P.At;
	if (P.Town >= 0)
	{
		// a town: loaded now, she comes in just inside its gate
		if (WildTownIdx != P.Town || !GetSection(FIntPoint::ZeroValue)) LoadWildTown(P.Town, true);
		if (const ARDSection* S = GetSection(FIntPoint::ZeroValue); S && !S->TownGateOut.IsNearlyZero())
			To = FVector2D((S->TownGate.X - S->TownGateOut.X * 500.0) / 100.0, (S->TownGate.Y - S->TownGateOut.Y * 500.0) / 100.0);
	}
	else
	{
		// another place: a stand clear of its props, toward where she came from
		const FVector2D Dir = (From - P.At).GetSafeNormal();
		To = P.At + (Dir.IsNearlyZero() ? FVector2D(-1, 0) : Dir) * 28.0;
		if (WildTownIdx >= 0 && Wild->Towns.IsValidIndex(WildTownIdx) && FVector2D::Distance(To, Wild->Towns[WildTownIdx].Site) > WildTownDropM) UnloadWildTown();
	}
	WildPutHer(To.X, To.Y);
	if (P.Town >= 0 && GetSection(FIntPoint::ZeroValue))
	{
		// (inside the walls: the ground there is the town's floor)
		Her->SetActorLocation(FVector(To.X * 100.0, To.Y * 100.0, 120.0), false, nullptr, ETeleportType::TeleportPhysics);
	}
	if (ACharacter* Ch = Cast<ACharacter>(Her)) Ch->GetCharacterMovement()->StopMovementImmediately();
	++WildTravels; WildLastTravel = P.Name;
	if (PlayerCombat) PlayerCombat->ShowMessage(FString::Printf(TEXT("%s (%.0f km, %.1f hours on the road)"), *P.Name, Km, Km / 5.0));
	UE_LOG(LogRDWildMap, Log, TEXT("RDWILD travelled to %s (%.1f km)"), *P.Name, Km);
	WildAutosave(TEXT("after travel"));
	return true;
}

bool ARDDungeonGenerator::WildTravelToTown(const FString& Key)
{
	// (the packaged game's test of a wilderness town: found, then the map's own fast travel: loaded, she just inside its gate)
	WildTravelRefusal.Reset();
	if (!IsWildReady()) { WildTravelRefusal = TEXT("not ready"); return false; }
	const FString Want = Key.Replace(TEXT(" "), TEXT("")).ToLower();
	for (int32 Ti = 0; Ti < Wild->Towns.Num(); ++Ti)
		if (Wild->Towns[Ti].Name.Replace(TEXT(" "), TEXT("")).ToLower() == Want)
		{
			const int32 Id = FRDWildWorld::TownIdBase + Ti;
			WildFound.Add(Id);
			return WildFastTravel(Id);
		}
	WildTravelRefusal = FString::Printf(TEXT("no town named %s"), *Key);
	return false;
}

FString ARDDungeonGenerator::GetWildMapState() const
{
	return FString::Printf(TEXT("%.0f|%.0f|%.2f|%d|%d|%d|%.1f|%d|%s|%d|%s|%s"), WildMapCenter.X, WildMapCenter.Y, WildMapMpp, WildMapLevelFor(WildMapMpp), WildMapTex.Num(), WildMapPending.Num(),
		WildMapTileMs, WildMapHover, *WildMapHoverName, WildMapTilesMade, *WildTravelRefusal, *WildLastTravel);
}

void ARDDungeonGenerator::SetWildMapView(float Xm, float Ym, float Mpp)
{
	WildMapCenter = FVector2D(Xm, Ym); WildMapMpp = FMath::Clamp((double)Mpp, WildMapMinMpp, WildMapMaxMpp);
}
