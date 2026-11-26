#pragma once

#include "Kismet/BlueprintFunctionLibrary.h"
#include "ChibiRopeSwing.generated.h"

UCLASS()
class UChibiRopeSwing : public UBlueprintFunctionLibrary
{
    GENERATED_BODY()
public:
    UFUNCTION(BlueprintCallable, Category="Parkour|Swing")
    static void AdvanceRopeSwing(double DeltaSeconds, double Angle, double AngularVelocity,
        double RopeLength, double Input, double PumpAccel, double MaxAngle,
        double& NextAngle, double& NextVelocity);
};
