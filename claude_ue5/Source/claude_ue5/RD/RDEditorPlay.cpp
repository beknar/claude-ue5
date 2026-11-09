// Play in the editor in a window of its own: see RDEditorPlay.h.
#include "RD/RDEditorPlay.h"
#if WITH_EDITOR
#include "Editor.h"
#include "Editor/EditorEngine.h"
#include "Settings/LevelEditorPlaySettings.h"
#include "LevelEditorViewport.h"
#endif

bool URDEditorPlay::PlayInNewWindow(int32 W, int32 H)
{
#if WITH_EDITOR
	if (!GEditor || GEditor->PlayWorld || GEditor->IsPlaySessionRequestQueued()) return false;
	ULevelEditorPlaySettings* PS = DuplicateObject<ULevelEditorPlaySettings>(GetDefault<ULevelEditorPlaySettings>(), GetTransientPackage());
	PS->NewWindowWidth = FMath::Clamp(W, 320, 3840); PS->NewWindowHeight = FMath::Clamp(H, 240, 2160);
	PS->CenterNewWindow = true;
	FRequestPlaySessionParams P;
	P.WorldType = EPlaySessionWorldType::PlayInEditor;
	P.EditorPlaySettings = PS;
	// (no DestinationSlateViewport: the session opens a window of its own at the settings' size)
	GEditor->RequestPlaySession(P);
	return true;
#else
	return false;
#endif
}

int32 URDEditorPlay::SetLevelViewportsRealtime(bool bOn)
{
	int32 N = 0;
#if WITH_EDITOR
	if (!GEditor) return 0;
	for (FLevelEditorViewportClient* C : GEditor->GetLevelViewportClients())
		if (C) { C->SetRealtime(bOn); ++N; }
#endif
	return N;
}
