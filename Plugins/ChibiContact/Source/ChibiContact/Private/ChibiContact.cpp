#include "Modules/ModuleManager.h"
IMPLEMENT_MODULE(FDefaultModuleImpl, ChibiContact)
#if WITH_DEV_AUTOMATION_TESTS
#include "GameFramework/PlayerController.h"
#include "Engine/World.h"
#include "InputKeyEventArgs.h"
#include "HAL/IConsoleManager.h"
// Feed deterministic keyboard events through the normal controller during gym playtests.
static FAutoConsoleCommandWithWorldAndArgs ClimbReviewKey(TEXT("Chibi.ClimbReviewKey"),TEXT("Key and Down/Up for climbing automation"),FConsoleCommandWithWorldAndArgsDelegate::CreateLambda([](const TArray<FString>& Args,UWorld* World){
    if (Args.Num()!=2 || !World || !World->IsGameWorld()) return;
    if (auto* PC=World->GetFirstPlayerController()) PC->InputKey(FInputKeyEventArgs(nullptr,FInputDeviceId::CreateFromInternalId(0),FKey(FName(*Args[0])),Args[1]==TEXT("Down")?IE_Pressed:IE_Released,FPlatformTime::Cycles64()));
}));
#endif
