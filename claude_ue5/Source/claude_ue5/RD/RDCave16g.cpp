// The user's list of 2026-11-22 (docs/improvements16.txt; the plan docs/improvements16_plan.md), its fifteenth phase: rewards that
// last. Fossils, a set per region (found in its caves): a full set (amber with an insect may stand in for one) traded at a temple
// for hit points or mana for good, or an Angel Token, as the collectibles are. Ancient tablets teaching a recipe (recipe items:
// the recipe they teach is locked until read) or a spell (tomes). Cave paintings on a set's walls: studied, they mark the region's
// other caves (the landmark towers' squares whose land is the region's, within 42 km) and the lairs and ruins round them on the
// wilds' map, once she is back in the wilds (the cave level has no wilds). An Angel Token from a cave's last boss.
#include "RD/RDDungeonGenerator.h"
#include "RD/RDSection.h"
#include "RD/RDCombat.h"
#include "RD/RDGameInstance.h"
#include "RD/RDWild.h"
#include "RD/RDMistward.h"
#include "Components/DecalComponent.h"
#include "Engine/World.h"
DEFINE_LOG_CATEGORY_STATIC(LogRDCave16g, Log, All);

// ================================================================================================ the cave painting
// ("<i>_<j>": a landmark tower's square, as the cave's key names it)
static bool RDCave16CellOf(const FString& Cell, int32& I, int32& J)
{
	FString A, B;
	if (!Cell.Split(TEXT("_"), &A, &B) || !A.IsNumeric() || !B.IsNumeric()) return false;
	I = FCString::Atoi(*A); J = FCString::Atoi(*B);
	return true;
}

void ARDSection::CavePaintingSet16()
{
	CavePaintings16.Reset();
	if (!Generator || !Generator->PaintingDecal16) return;
	// (one set in some, by a hash of its seed (the plan's streams untouched))
	if ((float)(HashCombine((uint32)Seed, 0xA1A716u) % 10000u) / 10000.f >= Generator->PaintingShare16) return;
	UWorld* W = GetWorld();
	if (!W) return;
	TArray<int32> Rooms16;
	for (int32 I = 0; I < CavePlaced16.Num(); ++I) if (CavePlaced16[I].Kit >= 0 && Rooms[I].Kind != ERDRoomKind::Junction && CaveRoomTiles16.IsValidIndex(I) && CaveRoomTiles16[I].Num() > 0) Rooms16.Add(I);
	if (Rooms16.Num() == 0) return;
	const uint32 H = HashCombine((uint32)Seed, 0x9A17u);
	const float S = Generator->TileSize;
	FCollisionQueryParams Q(SCENE_QUERY_STAT(RDCave16Paint), true);
	// (a flat stretch of wall: the kit's rock is lumpy, and a picture laid across its knobs read as a red smear (the first test's
	// picture). Round each room from its middle at two heights; a hit is kept only where a grid of eight traces round it, 1.4 m by
	// 1 m on its plane, all meet rock facing the same way (within 35 degrees) and within 18 cm of its plane)
	for (int32 Ri = 0; Ri < Rooms16.Num(); ++Ri)
	{
		const int32 RI = Rooms16[(H + Ri) % (uint32)Rooms16.Num()];
		for (const float Up : { 160.f, 210.f })
		{
			const FVector Mid = GetActorLocation() + FVector((CavePlaced16[RI].At.X + 0.5f) * S, (CavePlaced16[RI].At.Y + 0.5f) * S, CavePlaced16[RI].Z + Up);
			for (int32 K = 0; K < 24; ++K)
			{
				const float Yaw = (float)((H >> 8) % 360u) + K * 15.f;
				const FVector Way = FRotator(0.f, Yaw, 0.f).Vector();
				FHitResult Hh;
				if (!W->LineTraceSingleByChannel(Hh, Mid, Mid + Way * 3500.f, ECC_Visibility, Q)) continue;
				const FVector Nw = Hh.ImpactNormal;
				if (FMath::Abs(Nw.Z) > 0.3f || FVector::DotProduct(Nw, -Way) < 0.6f || Hh.Distance < 250.f) continue;
				const FVector Tg = FVector::CrossProduct(Nw, FVector::UpVector).GetSafeNormal(), Ug = FVector::CrossProduct(Tg, Nw).GetSafeNormal();
				FVector Avg = Nw; bool bFlat = true;
				for (int32 A = -1; A <= 1 && bFlat; ++A)
					for (int32 B = -1; B <= 1 && bFlat; ++B)
					{
						if (A == 0 && B == 0) continue;
						const FVector O = Hh.ImpactPoint + Tg * (70.f * A) + Ug * (50.f * B) + Nw * 80.f;
						FHitResult Hg;
						if (!W->LineTraceSingleByChannel(Hg, O, O - Nw * 160.f, ECC_Visibility, Q)) { bFlat = false; break; }
						if (FVector::DotProduct(Hg.ImpactNormal, Nw) < 0.82f || FMath::Abs(FVector::DotProduct(Hg.ImpactPoint - Hh.ImpactPoint, Nw)) > 18.f) { bFlat = false; break; }
						Avg += Hg.ImpactNormal;
					}
				if (!bFlat) continue;
				// (4 m clear of every door, container and anvil of the set (PR #122's review: a chest under it shared F's reach))
				{
					bool bDoor = false; int32 Ix = -1;
					FindNearestInteractive(Hh.ImpactPoint, 400.f, bDoor, Ix);
					if (Ix >= 0) continue;
					bool bAnvil = false;
					for (const FVector& A : GetAnvilPoints()) bAnvil |= FVector::Dist2D(A, Hh.ImpactPoint) < 400.f;
					if (bAnvil) continue;
				}
				Avg = FVector(Avg.X, Avg.Y, 0.f).GetSafeNormal();
				FCavePainting16 P; P.At = Hh.ImpactPoint; P.Normal = Avg;
				if (bBuildInteractive && W->IsGameWorld())
				{
					UDecalComponent* D = NewObject<UDecalComponent>(this);
					D->SetDecalMaterial(Generator->PaintingDecal16);
					D->DecalSize = FVector(45.f, 100.f, 100.f);          // (its depth either side of the wall, then the picture's half-size across)
					D->SetupAttachment(RootComponent);
					// (a decal's picture has its top toward its -Y: laid with its Z up the figures lay on their sides, with its +Y up they stood
					// on their heads (the sun drawn at the top left showed at the bottom right in the test's close pictures))
					D->SetRelativeTransform(FTransform(FRotationMatrix::MakeFromXY(-Avg, -FVector::UpVector).Rotator(), Hh.ImpactPoint - GetActorLocation()));
					D->RegisterComponent();
					CaveComps16.Add(D);
				}
				CavePaintings16.Add(P);
				UE_LOG(LogRDCave16g, Log, TEXT("RDCAVE16 (%d,%d): a cave painting in room %d at (%.0f, %.0f, %.0f), the wall flat over 1.4 x 1 m"), Coord.X, Coord.Y, RI, P.At.X, P.At.Y, P.At.Z);
				return;
			}
		}
	}
	UE_LOG(LogRDCave16g, Log, TEXT("RDCAVE16 (%d,%d): no flat wall for a cave painting"), Coord.X, Coord.Y);
}

bool ARDDungeonGenerator::PaintingNear16(const FVector& From, float Reach, FVector* OutAt) const
{
	if (!bCave16) return false;
	for (const TPair<FIntPoint, TObjectPtr<ARDSection>>& Kv : Sections)
	{
		const ARDSection* S = Kv.Value;
		if (!IsValid(S)) continue;
		for (const ARDSection::FCavePainting16& P : S->CavePaintings16)
			if (FVector::Dist2D(P.At, From) < Reach && FMath::Abs(P.At.Z - From.Z) < 250.f) { if (OutAt) *OutAt = P.At; return true; }
	}
	return false;
}

bool ARDDungeonGenerator::PaintingFirst16(const FVector& From, float Reach, float OtherD) const
{
	// (PR #122's review: weighed against piles alone, a chest under the painting answered its F only from its reach's far edge)
	FVector At;
	if (!PaintingNear16(From, Reach, &At)) return false;
	const float Dp = FVector::Dist2D(At, From);
	if (Dp >= OtherD) return false;
	for (const ARDLootPile* P : LootPiles)
		if (IsValid(P) && FVector::Dist2D(P->GetActorLocation(), From) < Dp) return false;
	FVector An;
	if (FindNearestAnvil(From, Dp, An)) return false;
	if (!StationDescribe(From, Dp).IsEmpty()) return false;
	return true;
}

FString ARDDungeonGenerator::StudyPainting16(const FVector& From, float Reach)
{
	if (!PaintingNear16(From, Reach)) return FString();
	URDGameInstance* GI = URDGameInstance::Of(this);
	const FString Key = GI && !GI->CaveKey15.IsEmpty() ? GI->CaveKey15 : FString(TEXT("cave"));
	const int32 Rg = CaveRegion16();
	const FString Region = CaveRegions16.IsValidIndex(Rg) ? CaveRegions16[Rg].Name.ToString() : FString();
	const FString Entry = Key + TEXT("|") + Region;
	// (a cave entered with no tower's cell in its key (a test's or the package's run: "cave:go", "cave") or no region known shows her
	// nothing to find (PR #122's review: such a key parsed as Brokenspire's square))
	FString CellS; int32 Ci = 0, Cj = 0;
	const bool bCell = Key.Split(TEXT(":"), nullptr, &CellS) && RDCave16CellOf(CellS, Ci, Cj);
	const bool bMarks = bCell && !Region.IsEmpty();
	const bool bNew = GI && bMarks && !GI->Paintings16.Contains(Entry);
	if (GI && bMarks) GI->Paintings16.AddUnique(Entry);
	if (PlayerCombat)
		PlayerCombat->ShowMessage(!bMarks ? FString(TEXT("Hunters and a stag in red ochre: the old people knew these caves"))
			: !bNew ? FString(TEXT("You know this painting: its caves are on your map"))
			: FString::Printf(TEXT("You study the painting: it shows the %s lands' caves and their hidden places (on your map once you are back in the wilds)"), *Region));
	UE_LOG(LogRDCave16g, Log, TEXT("RDCAVE16 painting studied: %s (%s)"), *Entry, bNew ? TEXT("new") : TEXT("known"));
	return TEXT("painting");
}

TArray<FString> ARDDungeonGenerator::GetPaintings16() const
{
	TArray<FString> Out;
	if (const URDGameInstance* GI = URDGameInstance::Of(this))
	{
		for (const FString& P : GI->Paintings16) Out.Add(TEXT("studied|") + P + (GI->PaintingsApplied16.Contains(P) ? TEXT("|applied") : TEXT("|waiting")));
		for (const FIntPoint& C : GI->KnownCaves16)
		{
			FVector2D S; const bool bAt = bWild && Wild && WildTowerSite13(C.X, C.Y, S);
			Out.Add(FString::Printf(TEXT("cave|%d|%d|%.0f|%.0f|%s"), C.X, C.Y, bAt ? S.X : 0.0, bAt ? S.Y : 0.0, bAt ? *Wild->BiomeName(Wild->BiomeAt(S.X, S.Y)) : TEXT("")));
		}
	}
	for (const TPair<FIntPoint, TObjectPtr<ARDSection>>& Kv : Sections)
		if (const ARDSection* S = Kv.Value; IsValid(S))
			for (const ARDSection::FCavePainting16& P : S->CavePaintings16) Out.Add(FString::Printf(TEXT("painting|%d|%d|%.0f|%.0f|%.0f|%.3f|%.3f|%.3f"), Kv.Key.X, Kv.Key.Y, P.At.X, P.At.Y, P.At.Z, P.Normal.X, P.Normal.Y, P.Normal.Z));
	return Out;
}

void ARDDungeonGenerator::ApplyPaintings16()
{
	// (in the wilds, once a second: a painting studied in a cave marks the region's caves (the towers' squares within 7 of the painted
	// cave's whose land is the region's) and the lairs and ruins within 3 km of each; once each)
	URDGameInstance* GI = URDGameInstance::Of(this);
	if (!GI || !bWild || !IsWildReady() || GI->Paintings16.Num() == GI->PaintingsApplied16.Num()) return;
	for (const FString& Entry : GI->Paintings16)
	{
		if (GI->PaintingsApplied16.Contains(Entry)) continue;
		GI->PaintingsApplied16.Add(Entry);
		FString Key, Region; Entry.Split(TEXT("|"), &Key, &Region);
		FString Cell; int32 Ci = 0, Cj = 0;
		const FRDCaveRegion16* Rg = CaveRegions16.FindByPredicate([&Region](const FRDCaveRegion16& R) { return R.Name.ToString() == Region; });
		// (no tower's cell or no region known: nothing to mark (PR #122's review))
		if (!Key.Split(TEXT(":"), nullptr, &Cell) || !RDCave16CellOf(Cell, Ci, Cj) || !Rg) { UE_LOG(LogRDCave16g, Log, TEXT("RDCAVE16 painting %s: no cell or region, nothing marked"), *Entry); continue; }
		int32 Caves = 0, Secrets = 0;
		// (the region's caves round the painted one: the towers' squares within 7 whose land is the region's, the nearest twelve (near
		// Brokenspire the open lands' were 53: a map full of caves says nothing))
		FVector2D Here(0.0, 0.0); const bool bHere = WildTowerSite13(Ci, Cj, Here);
		TArray<TPair<double, FIntPoint>> Found;
		for (int32 I = Ci - 7; I <= Ci + 7; ++I)
			for (int32 J = Cj - 7; J <= Cj + 7; ++J)
			{
				FVector2D S;
				if ((I == Ci && J == Cj) || !WildTowerSite13(I, J, S)) continue;
				if (!Rg->Biomes.Contains(Wild->BiomeName(Wild->BiomeAt(S.X, S.Y)))) continue;
				Found.Add(TPair<double, FIntPoint>(bHere ? FVector2D::Distance(S, Here) : (double)(FMath::Square(I - Ci) + FMath::Square(J - Cj)), FIntPoint(I, J)));
			}
		Found.Sort([](const TPair<double, FIntPoint>& A, const TPair<double, FIntPoint>& B) { return A.Key < B.Key; });
		if (Found.Num() > PaintingCaves16) Found.SetNum(PaintingCaves16);
		for (const TPair<double, FIntPoint>& F : Found)
		{
			FVector2D S; WildTowerSite13(F.Value.X, F.Value.Y, S);
			if (!GI->KnownCaves16.Contains(F.Value)) { GI->KnownCaves16.Add(F.Value); ++Caves; }
			// (its secrets: the lairs and ruins within 3 km)
			TArray<FRDWildPlace> Ps;
			const FIntPoint P0 = Wild->PlaceCellOf(S.X - 3000.0, S.Y - 3000.0), P1 = Wild->PlaceCellOf(S.X + 3000.0, S.Y + 3000.0);
			for (int32 A = P0.X; A <= P1.X; ++A) for (int32 B = P0.Y; B <= P1.Y; ++B) Wild->PlacesIn(FIntPoint(A, B), Ps);
			for (const FRDWildPlace& P : Ps)
			{
				// (the captain's quest places (QuestIdBase on) are listed as ruins: they are no painting's secret (PR #122's review))
				if (P.Town >= 0 || P.Id >= FRDWildWorld::QuestIdBase || (P.Kind != TEXT("lair") && P.Kind != TEXT("ruins")) || FVector2D::Distance(P.At, S) > 3000.0) continue;
				if (WildFound.Contains(P.Id) || WildMarked15.Contains(P.Id)) continue;
				WildMarked15.Add(P.Id); GI->WildMarked15.AddUnique(P.Id); PaintingMarked16.Add(P.Id); ++Secrets;
			}
		}
		WildMarkedCacheFor15 = -1;
		PaintedApplied16 += Caves;
		if (PlayerCombat && (Caves > 0 || Secrets > 0)) PlayerCombat->ShowMessage(FString::Printf(TEXT("From the cave painting you studied: %d caves and %d hidden places marked on your map"), Caves, Secrets));
		UE_LOG(LogRDCave16g, Log, TEXT("RDCAVE16 painting %s applied: %d caves, %d secrets"), *Entry, Caves, Secrets);
	}
	WildAutosave(TEXT("found"));
}

FString ARDDungeonGenerator::DebugPaintingNear16(float Xm, float Ym)
{
	URDGameInstance* GI = URDGameInstance::Of(this);
	FVector2D S; double D = 0.0;
	if (!GI || !bWild || !IsWildReady() || !NearestTowerSite15(FVector2D(Xm, Ym), 3, S, D)) return FString();
	const FString Biome = Wild->BiomeName(Wild->BiomeAt(S.X, S.Y));
	const FRDCaveRegion16* Rg = CaveRegions16.FindByPredicate([&Biome](const FRDCaveRegion16& R) { return R.Biomes.Contains(Biome); });
	if (!Rg) return FString();
	const FString Entry = FString::Printf(TEXT("cave:%d_%d|%s"), FMath::FloorToInt(S.X / WildLandmarkCellM), FMath::FloorToInt(S.Y / WildLandmarkCellM), *Rg->Name.ToString());
	GI->Paintings16.AddUnique(Entry);
	return Entry + TEXT("|") + Biome;
}

int32 ARDDungeonGenerator::ForgetPaintingMarks16()
{
	URDGameInstance* GI = URDGameInstance::Of(this);
	const int32 N = PaintingMarked16.Num();
	for (const int32 Id : PaintingMarked16) { WildMarked15.Remove(Id); if (GI) GI->WildMarked15.Remove(Id); }
	PaintingMarked16.Reset(); WildMarkedCacheFor15 = -1;
	return N;
}

void ARDDungeonGenerator::DrawKnownCaves16(TFunctionRef<void(const FVector2D&)> Draw) const
{
	const URDGameInstance* GI = URDGameInstance::Of(this);
	if (!GI || !bWild) return;
	for (const FIntPoint& C : GI->KnownCaves16) { FVector2D S; if (WildTowerSite13(C.X, C.Y, S)) Draw(S); }
}

// ================================================================================================ the fossil sets
TArray<FString> ARDDungeonGenerator::GetFossilLines16() const
{
	// ("fossil|<region>|<1: whole>|<a>,<b>,<c>" for each set she carries a part of)
	TArray<FString> Out;
	if (!PlayerCombat) return Out;
	for (const FString& L : FossilSets16)
	{
		TArray<FString> F; L.ParseIntoArray(F, TEXT("|"), false);
		if (F.Num() < 2) continue;
		int32 Have = 0, Missing = 0;
		for (int32 K = 1; K < F.Num(); ++K) { if (PlayerCombat->GetItemCount(FName(*F[K])) > 0) ++Have; else ++Missing; }
		if (Have == 0) continue;
		const bool bWhole = Missing == 0 || (Missing == 1 && !FossilAmber16.IsNone() && PlayerCombat->GetItemCount(FossilAmber16) > 0);
		Out.Add(FString::Printf(TEXT("fossil|%s|%d|%d of %d"), *F[0], bWhole ? 1 : 0, Have, F.Num() - 1));
	}
	return Out;
}

bool ARDDungeonGenerator::TownFossilTrade16(const FString& Arg)
{
	URDGameInstance* GI = URDGameInstance::Of(this);
	FString Region, What;
	if (!GI || !PlayerCombat || !Arg.Split(TEXT("|"), &Region, &What)) return false;
	const FString* L = FossilSets16.FindByPredicate([&Region](const FString& S) { return S.StartsWith(Region + TEXT("|")); });
	if (!L) return false;
	TArray<FString> F; L->ParseIntoArray(F, TEXT("|"), false);
	TArray<FName> Take; int32 Missing = 0;
	for (int32 K = 1; K < F.Num(); ++K) { const FName It(*F[K]); if (PlayerCombat->GetItemCount(It) > 0) Take.Add(It); else ++Missing; }
	const bool bAmber = Missing == 1 && !FossilAmber16.IsNone() && PlayerCombat->GetItemCount(FossilAmber16) > 0;
	if (Missing > 1 || (Missing == 1 && !bAmber)) { SetTownNote(TEXT("The priest wants the whole set (amber may stand in for one piece)")); return false; }
	if (What == TEXT("mana") && PlayerMaxMana <= 0.f) { SetTownNote(TEXT("You have no mana to raise")); return false; }
	if (What != TEXT("hp") && What != TEXT("mana") && What != TEXT("token")) return false;
	for (const FName& It : Take) PlayerCombat->RemoveItem(It, 1);
	if (bAmber) PlayerCombat->RemoveItem(FossilAmber16, 1);
	if (What == TEXT("hp")) { GI->LastingHealth15 += FossilGain16; PlayerCombat->RefreshMaxima(); SetTownNote(FString::Printf(TEXT("The priest takes the %s fossils: your hit points' top rises by %d"), *Region, FossilGain16)); }
	else if (What == TEXT("mana")) { GI->LastingMana15 += FossilGain16; PlayerCombat->RefreshMaxima(); SetTownNote(FString::Printf(TEXT("The priest takes the %s fossils: your mana's top rises by %d"), *Region, FossilGain16)); }
	else if (!AngelTokenItem.IsNone()) { PlayerCombat->AddItem(AngelTokenItem, 1); SetTownNote(FString::Printf(TEXT("The priest takes the %s fossils and gives you an %s"), *Region, *AngelTokenItem.ToString())); }
	TownCount(TEXT("fossil_trades"));
	return true;
}

void ARDDungeonGenerator::AddFossilTrades16(TFunctionRef<void(const FString& Act, const FString& Label, const FString& Tag, const FString& Detail, bool bOn, const FString& Arg)> Add) const
{
	for (const FString& L : GetFossilLines16())
	{
		TArray<FString> F; L.ParseIntoArray(F, TEXT("|"), false);
		if (F.Num() < 4) continue;
		const bool bOn = F[2] == TEXT("1");
		Add(TEXT("fossil16"), FString::Printf(TEXT("Offer the %s fossils: %d hit points for good"), *F[1], FossilGain16), F[3], TEXT("A region's set of fossils (amber may stand in for one piece)"), bOn, F[1] + TEXT("|hp"));
		if (PlayerMaxMana > 0.f) Add(TEXT("fossil16"), FString::Printf(TEXT("Offer the %s fossils: %d mana for good"), *F[1], FossilGain16), F[3], TEXT("A region's set of fossils (amber may stand in for one piece)"), bOn, F[1] + TEXT("|mana"));
		if (!AngelTokenItem.IsNone()) Add(TEXT("fossil16"), FString::Printf(TEXT("Offer the %s fossils: an %s"), *F[1], *AngelTokenItem.ToString()), F[3], TEXT("A token for a rank of one of your secondary abilities"), bOn, F[1] + TEXT("|token"));
	}
}

// ================================================================================================ the ancient tablets
FName ARDDungeonGenerator::CaveTablet16(FIntPoint Section, int32 Index) const
{
	// (one of the caves' tablets (recipe items and the tomes' copies named "Ancient Tablet..."), a recipe she knows left out)
	FRandomStream R((int32)HashCombine(HashCombine((uint32)SessionSeed ^ 0x7AB16u, GetTypeHash(Section)), GetTypeHash(Index * 7907 + 11)));
	if (R.FRand() >= TabletShare16) return NAME_None;
	TArray<FName> Pool;
	for (const FRDItemDef& It : Items)
	{
		if (!CaveItems16.Contains(It.Name) || !It.Name.ToString().StartsWith(TEXT("Ancient Tablet"))) continue;
		if (It.Kind == ERDItemKind::Recipe && (!bRecipes14 || KnowsRecipe14(It.Teaches))) continue;
		Pool.Add(It.Name);
	}
	return Pool.Num() > 0 ? Pool[R.RandRange(0, Pool.Num() - 1)] : NAME_None;
}
