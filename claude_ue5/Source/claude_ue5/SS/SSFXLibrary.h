// starship_level: helpers for the pipeline scripts to fit a pack's Cascade effect to the level. The emitters of a
// particle system cannot be reached from Python (protected), so 800 duplicates a library effect (a ribbon trail) and
// has it tuned here: ribbon width, colour, lifetime and material. Editor only (the changes are saved with the copy).
#pragma once

#include "CoreMinimal.h"
#include "Kismet/BlueprintFunctionLibrary.h"
#include "SSFXLibrary.generated.h"

class UMaterialInterface;
class UParticleSystem;

UCLASS()
class CLAUDE_UE5_API USSFXLibrary : public UBlueprintFunctionLibrary
{
	GENERATED_BODY()

public:
	/** emitters, their materials, type data and modules with the values of their properties (one line each) */
	UFUNCTION(BlueprintCallable, Category = "Starship|FX") static FString DescribeParticleSystem(UParticleSystem* System);
	/** sets, in every emitter of the system: particle size (ribbon width, cm), colour and start alpha (fading to 0 over
	 *  the particle's life), lifetime (s) and, when given, the material. Values <= 0 / null leave that setting alone.
	 *  Returns the number of modules changed. */
	UFUNCTION(BlueprintCallable, Category = "Starship|FX") static int32 TuneParticleSystem(UParticleSystem* System, float Size, FLinearColor Color, float Lifetime, UMaterialInterface* Material);
};
