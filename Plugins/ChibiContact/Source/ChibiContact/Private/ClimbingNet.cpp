#include "ClimbingNet.h"

namespace { constexpr double Step=1./90.; }

FVector2D FClimbingNet::Grid(const FVector& P)
{
    const double Z=FMath::Clamp(P.Z,7.,265.);
    const double Row=Z<16 ? (Z-7)/9 : Z>256 ? 16+(Z-256)/9 : 1+(Z-16)/16;
    return FVector2D(FMath::Clamp((P.Y+50)/20,0.,5.),Row);
}
FVector FClimbingNet::IdleOffset(const FVector& P)
{
    const double U=FMath::Clamp(P.Y/50.,-1.,1.);
    const double V=FMath::Clamp((P.Z-136)/129.,-1.,1.);
    return FVector(-3*(1-U*U)-2*(1-V*V),0,-5*(1-U*U)-2*(1-V*V));
}
void FClimbingNet::Initialize()
{
    Links.Reset(); TimeBank=0;
    for(int R=0;R<Rows;++R) for(int C=0;C<Cols;++C){
        const int I=R*Cols+C;
        Rest[I]=FVector(-19,-50+20*C,R==0?7:R==Rows-1?265:16+(R-1)*16);
        Previous[I]=Position[I]=Rest[I]+IdleOffset(Rest[I]);
        Force[I]=FVector::ZeroVector;
        Pinned[I]=(C==0 || C==Cols-1) && (R==0 || R==Rows-1);
        auto Link=[&](int J,double Slack,double Stiffness){
            Links.Add({I,J,(Rest[I]-Rest[J]).Size()*Slack,Stiffness});
        };
        if(C) Link(I-1,1.035,.93);
        if(R) Link(I-Cols,1.02,.93);
        if(R && C) Link(I-Cols-1,1.025,.12);
        if(R && C+1<Cols) Link(I-Cols+1,1.025,.12);
    }
    for(int I=0;I<180;++I) Substep();
}
void FClimbingNet::Load(const FVector& P,const FVector& Acceleration)
{
    auto G=Grid(P);
    int X=FMath::Min(FMath::FloorToInt(G.X),Cols-2),Y=FMath::Min(FMath::FloorToInt(G.Y),Rows-2);
    for(int B=0;B<2;++B) for(int A=0;A<2;++A){
        const double Weight=(A?G.X-X:1-(G.X-X))*(B?G.Y-Y:1-(G.Y-Y));
        Force[(Y+B)*Cols+X+A]+=Weight*Acceleration;
    }
}
void FClimbingNet::Substep()
{
    for(int I=0;I<Count;++I){
        if(Pinned[I]) continue;
        FVector V=(Position[I]-Previous[I])*.979;
        Previous[I]=Position[I];
        // Weak bending recovery around the hanging shape prevents persistent folds.
        FVector Acc=FVector(0,0,-280)+Force[I]+(Rest[I]+IdleOffset(Rest[I])-Position[I])*14;
        Position[I]+=V+Acc*(Step*Step);
    }
    for(int Pass=0;Pass<8;++Pass){
        for(const FLink& L:Links){
            FVector D=Position[L.B]-Position[L.A];
            double Len=D.Size();
            if(Len<=L.Length) continue; // A slack strand transmits tension only.
            double WA=Pinned[L.A]?0:1, WB=Pinned[L.B]?0:1;
            if(WA+WB==0) continue;
            FVector Correction=D*(L.Stiffness*(Len-L.Length)/(Len*(WA+WB)));
            Position[L.A]+=WA*Correction; Position[L.B]-=WB*Correction;
        }
        for(int I=0;I<Count;++I) if(!Pinned[I]){
            Position[I].X=FMath::Min(Position[I].X,-4.);
            Position[I].Z=FMath::Max(Position[I].Z,3.);
        }
    }
}
bool FClimbingNet::Advance(double Delta)
{
    TimeBank+=FMath::Min(Delta,.1);
    bool Changed=false;
    while(TimeBank>=Step){Substep();TimeBank-=Step;Changed=true;}
    for(auto& F:Force) F=FVector::ZeroVector;
    return Changed;
}
FVector FClimbingNet::Offset(const FVector& P) const
{
    auto G=Grid(P);
    int X=FMath::Min(FMath::FloorToInt(G.X),Cols-2),Y=FMath::Min(FMath::FloorToInt(G.Y),Rows-2);
    auto At=[&](int I){return Position[I]-Rest[I];};
    int I=Y*Cols+X;
    return FMath::Lerp(FMath::Lerp(At(I),At(I+1),G.X-X),
        FMath::Lerp(At(I+Cols),At(I+Cols+1),G.X-X),G.Y-Y);
}
