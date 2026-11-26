#pragma once
#include "CoreMinimal.h"
#include "GameFramework/Actor.h"
#include "ChibiPool.generated.h"

class ACharacter;
class UAnimSequence;
class UAnimationAsset;
class UInstancedStaticMeshComponent;
class UPostProcessComponent;
class USpringArmComponent;

UCLASS()
class AChibiPool : public AActor
{
    GENERATED_BODY()
public:
    AChibiPool();
    virtual void Tick(float Delta) override;
    virtual void EndPlay(const EEndPlayReason::Type Reason) override;
private:
    void EnterWater(ACharacter& Character);
    void BeginSwimming();
    void EndSwimming();
    void LeaveWater();
    void Swim(float Delta, float Height);
    bool TryClimbOut();
    void UpdateCamera(float Delta);
    void EmitRipple(FVector WorldPosition, float Diameter);
    void EmitBubble(FVector WorldPosition);
    void AnimateEffects(float Delta);

    UPROPERTY() TObjectPtr<UInstancedStaticMeshComponent> Rings;
    UPROPERTY() TObjectPtr<UInstancedStaticMeshComponent> Bubbles;
    UPROPERTY() TObjectPtr<UPostProcessComponent> Underwater;
    UPROPERTY() TObjectPtr<UAnimSequence> SwimClip;
    UPROPERTY() TObjectPtr<UAnimSequence> SurfaceClip;
    UPROPERTY() TObjectPtr<UAnimSequence> TreadClip;
    UPROPERTY() TObjectPtr<UAnimationAsset> PriorClip;
    TWeakObjectPtr<ACharacter> Occupant;
    TWeakObjectPtr<UActorComponent> Parkour;
    TWeakObjectPtr<USpringArmComponent> CameraArm;
    FTransform SwimMeshRest;
    bool bSurfaceSwimming = false;
    float SurfaceWeight = 0.f, DiveKickTime = 0.f;
    float SwimPitch = 0.f;
    float CameraOffset = 0.f;
    bool bSwimming = false, bParkourTick = false, bOldOrient = false, bOldLoop = true;
    float OldWalkSpeed = 0, OldFlySpeed = 0, OldClipRate = 1, OldClipTime = 0;
    FName OldState;
    float RippleClock = 0, BubbleClock = 0;
    int Foot = 0;
    struct FEffect { FVector Position; float Size, Age, Life; };
    TArray<FEffect> Ripples, Air;
};
