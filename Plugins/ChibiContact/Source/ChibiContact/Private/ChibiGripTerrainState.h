#pragma once

#include "CoreMinimal.h"

class UPrimitiveComponent;

struct FChibiTerrainHand
{
    TWeakObjectPtr<UPrimitiveComponent> Support;
    FVector LocalPoint = FVector::ZeroVector;
    FVector LocalNormal = FVector::UpVector;
    FVector LocalTangent = FVector::RightVector;
    FVector Point = FVector::ZeroVector;
    FVector Normal = FVector::UpVector;
    FVector Tangent = FVector::RightVector;
    float Weight = 0.f;
    bool bLocked = false;
};

struct FChibiTerrainState
{
    FChibiTerrainHand Hands[2];
    FVector PreviousPosition = FVector::ZeroVector;
    FName LastState;
    float WallTravel = 0.f;
    bool bInitialized = false;
};
