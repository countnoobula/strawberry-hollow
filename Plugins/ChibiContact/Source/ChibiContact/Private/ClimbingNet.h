#pragma once
#include "CoreMinimal.h"

// A particle at every lashing, plus the two perimeter ropes.
struct FClimbingNet
{
    static constexpr int Cols=6, Rows=18, Count=Cols*Rows;
    struct FLink {int A,B; double Length,Stiffness;};
    FVector Rest[Count], Position[Count], Previous[Count], Force[Count];
    bool Pinned[Count];
    TArray<FLink> Links;
    double TimeBank=0;

    static FVector2D Grid(const FVector& P);
    static FVector IdleOffset(const FVector& P);
    void Initialize();
    void Load(const FVector& RestContact,const FVector& Acceleration);
    bool Advance(double Delta);
    FVector Offset(const FVector& RestContact) const;
private:
    void Substep();
};
