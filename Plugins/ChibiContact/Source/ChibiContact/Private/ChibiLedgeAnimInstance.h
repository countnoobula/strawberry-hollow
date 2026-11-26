#pragma once

#include "Animation/AnimInstance.h"
#include "ChibiLedgeAnimInstance.generated.h"

/** Post-process layer for the ordinary ledge hang and pull-up on Chibi's mesh. */
UCLASS(Transient, Blueprintable)
class UChibiLedgeAnimInstance : public UAnimInstance
{
    GENERATED_BODY()

public:
    UPROPERTY(Transient) TObjectPtr<UAnimSequence> SurfaceStroke;
    UPROPERTY(Transient) TObjectPtr<UAnimSequence> TreadWater;
    float SurfaceStrokeWeight = 0.f;
private:
    virtual FAnimInstanceProxy* CreateAnimInstanceProxy() override;
    virtual void DestroyAnimInstanceProxy(FAnimInstanceProxy* Proxy) override;
};
