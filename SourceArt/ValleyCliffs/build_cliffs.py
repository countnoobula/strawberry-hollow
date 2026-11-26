"""Generate Strawberry Hollow's moss-fringed creekstone kit. Run with Blender in background."""
import math
import random
import sys
from pathlib import Path
import bpy
import numpy as np
from mathutils import Vector
from mathutils.bvhtree import BVHTree
from math import sin, cos, pi

OUT = Path(__file__).resolve().parent
TEX = OUT / "Textures"
bpy.ops.wm.read_factory_settings(use_empty=True)
scene = bpy.context.scene
scene.unit_settings.system = "METRIC"
scene.unit_settings.scale_length = 1.0
size = 1024
yy, xx = np.mgrid[0:size, 0:size] / size
def noise(seed, nx, ny):
    data = np.random.default_rng(seed).random((ny,nx)).astype("float32")
    x, y = xx*nx, yy*ny
    ix, iy = x.astype(int), y.astype(int)
    tx, ty = x-ix, y-iy
    tx, ty = tx*tx*(3-2*tx), ty*ty*(3-2*ty)
    def val(i,j): return data[(iy+j)%ny,(ix+i)%nx]
    return (val(0,0)*(1-tx)+val(1,0)*tx)*(1-ty)+(val(0,1)*(1-tx)+val(1,1)*tx)*ty

def cushion_heads(seed, nx, ny):
    """A seamless field of uneven, softly joined, rounded moss shoots."""
    rng=np.random.default_rng(seed)
    offsets=rng.uniform(-.36,.36,(ny,nx,2))
    radii=rng.uniform(.40,.64,(ny,nx,2))
    heights=rng.uniform(.66,1.0,(ny,nx))
    x=xx*nx+.42*(noise(seed+1,7,9)-.5)
    y=yy*ny+.46*(noise(seed+2,9,6)-.5)
    ix=np.floor(x).astype(int);iy=np.floor(y).astype(int)
    result=np.zeros_like(x)
    for j in (-1,0,1):
        for i in (-1,0,1):
            cell=((iy+j)%ny,(ix+i)%nx)
            dx=(x-ix-i-.5-offsets[cell][:,:,0])/radii[cell][:,:,0]
            dy=(y-iy-j-.5-offsets[cell][:,:,1])/radii[cell][:,:,1]
            q=dx*dx+dy*dy
            # The small skirt overlaps the adjacent cushion, keeping recesses soft.
            result+=heights[cell]*np.exp(-1.8*q)
    return result

def texture(name, pixels, is_data):
    # Write the exact sRGB swatch bytes. Data maps go through the same writer
    # without a display transform so that the tangent-space midpoint stays at 128.
    import struct
    import zlib
    rgb = np.rint(np.clip(pixels, 0, 1)*255).astype(np.uint8)
    def chunk(kind, data):
        return struct.pack('>I', len(data)) + kind + data + struct.pack('>I', zlib.crc32(kind+data))
    body = b''.join(b'\0'+row.tobytes() for row in rgb[::-1])
    filename = TEX/(name+'.png')
    header = struct.pack('>IIBBBBB', size, size, 8, 2, 0, 0, 0)
    filename.write_bytes(b'\x89PNG\r\n\x1a\n'+chunk(b'IHDR',header)+chunk(b'IDAT',zlib.compress(body,9))+chunk(b'IEND',b''))
    img=bpy.data.images.load(str(filename))
    img.colorspace_settings.name='Non-Color' if is_data else 'sRGB'
    return img

def make_surface(kind):
    broad=noise(15,3,3)
    drift=noise(23,6,7)
    if kind=='Creekstone':
        # Each short ledge dies away inside a continuous field of weathered stone.
        # The broad shoulder on one side catches sunlight above the narrow nick.
        bend=.012*(noise(241,7,6)-.5)+.004*(noise(207,25,21)-.5)
        joint=np.zeros_like(xx)
        shoulder=np.zeros_like(xx)
        for cx,cy,angle,half_length in ((.23,.19,24,.185),(.74,.60,57,.13),(.35,.81,-15,.10)):
            ux=(xx-cx+.5)%1-.5
            uy=(yy-cy+.5)%1-.5
            c,s=cos(math.radians(angle)),sin(math.radians(angle))
            along=ux*c+uy*s
            across=-ux*s+uy*c+bend+.09*np.abs(along)
            fade=np.clip(1-(along/half_length)**2,0,1)**1.5
            joint+=fade*np.exp(-(across/.007)**2)
            rise=np.clip(across/.016,0,1)
            shoulder+=fade*rise*rise*(3-2*rise)*np.exp(-(across/.062)**2)
        grain=noise(217,95,103)-.5
        grit=noise(287,230,241)-.5
        flakes=noise(295,26,31)-.5
        # Mineral variation warms worn faces and cools the deepest cuts.
        mineral=noise(303,10,9)-.5
        light=.50+.40*(broad-.5)+.31*(drift-.5)+.21*flakes+.086*grain+.04*grit
        light+=.060*shoulder-.27*joint
        base=np.array([.344,.335,.316])+light[:,:,None]*np.array([.32,.302,.273])
        base+=mineral[:,:,None]*np.array([.056,.028,-.010])
        height=.006*shoulder-.005*joint+.012*(broad-.5)+.006*(drift-.5)+.0045*flakes+.0010*grain+.00042*grit
        # Central differences downstream expect height expressed in texel units.
        h=height*size/7
        rough=np.clip(.87+.08*joint+.08*flakes+.055*grain,.75,.97)
    else:
        # Broad fern-to-sage color remains legible as the smaller shoots mip out.
        clumps=cushion_heads(513,30,33)
        shoots=cushion_heads(746,82,79)
        light=np.clip(.05+.55*broad+.28*drift+.13*noise(97,12,10),0,1)
        shadow=np.array([.23,.43,.265])
        sage=np.array([.645,.745,.415])
        base=shadow+(sage-shadow)*light[:,:,None]
        nap=.68*clumps+.32*shoots
        base+=(nap-np.mean(nap))[:,:,None]*np.array([.072,.060,.038])
        h=.12*drift+.56*clumps+.122*shoots
        rough=.94-.034*clumps-.012*shoots
    dx=(np.roll(h,-1,1)-np.roll(h,1,1))*3.5
    dy=(np.roll(h,-1,0)-np.roll(h,1,0))*3.5
    normal=np.stack([-dx,-dy,np.ones_like(h)],axis=2)
    normal=normal/np.linalg.norm(normal,axis=2)[:,:,None]*.5+.5
    maps=[texture('T_Valley'+kind+'_BaseColor',base,False),
          texture('T_Valley'+kind+'_NormalGL',normal,True),
          texture('T_Valley'+kind+'_Roughness',np.repeat(rough[:,:,None],3,axis=2),True)]
    mat=bpy.data.materials.new('M_Valley'+kind);mat.use_nodes=True
    nodes=mat.node_tree.nodes;links=mat.node_tree.links
    bs=nodes.get('Principled BSDF')
    mat.diffuse_color=tuple(np.mean(base,axis=(0,1)))+(1,)
    for i,img in enumerate(maps):
        node=nodes.new('ShaderNodeTexImage');node.image=img;node.location=(-640,230-260*i)
        if i==0:links.new(node.outputs['Color'],bs.inputs['Base Color'])
        if i==1:
            nm=nodes.new('ShaderNodeNormalMap');nm.location=(-290,-80);nm.inputs['Strength'].default_value=.73
            links.new(node.outputs['Color'],nm.inputs['Color']);links.new(nm.outputs['Normal'],bs.inputs['Normal'])
        if i==2:links.new(node.outputs['Color'],bs.inputs['Roughness'])
    return mat

rock=make_surface('Creekstone');moss=make_surface('Moss')

def terrain_moss_material():
    # Bend the terrain's color, height and surface channels together, preserving
    # their local registration while giving the rock cushion its own growth.
    u=(xx+.031*(noise(823,4,5)-.5)+.21)%1
    v=(yy+.027*(noise(827,6,4)-.5)+.39)%1
    def terrain_channel(suffix):
        source=OUT.parent/'ValleyGround'/('T_MossGround01_'+suffix+'.png')
        image=bpy.data.images.load(str(source));image.colorspace_settings.name='Non-Color'
        image.scale(size,size)
        pixels=np.empty(size*size*4,np.float32);image.pixels.foreach_get(pixels)
        pixels=pixels.reshape(size,size,4)
        ix=u*size;iy=v*size
        x=ix.astype(int);y=iy.astype(int)
        fx=(ix-x)[:,:,None];fy=(iy-y)[:,:,None]
        rgb=(1-fy)*((1-fx)*pixels[y,x,:3]+fx*pixels[y,(x+1)%size,:3])
        rgb+=fy*((1-fx)*pixels[(y+1)%size,x,:3]+fx*pixels[(y+1)%size,(x+1)%size,:3])
        bpy.data.images.remove(image)
        return rgb
    soil_color=terrain_channel('Color')
    relief=terrain_channel('Height')[:,:,0]
    orm=terrain_channel('ORM')
    lo,hi=np.percentile(relief,[1,99])
    ground_height=np.clip((relief-lo)/(hi-lo),0,1)
    tips=cushion_heads(746,82,79)
    broad=noise(827,5,7)-.5
    color=.86*soil_color+.14*np.array([.38,.47,.14])
    color+=(.018*broad+.014*(tips-tips.mean()))[:,:,None]
    height=np.clip(.07+.81*ground_height+.10*tips+.03*broad,0,1)
    dx=(np.roll(height,-1,1)-np.roll(height,1,1))*7.0
    dy=(np.roll(height,-1,0)-np.roll(height,1,0))*7.0
    n=np.stack((-dx,-dy,np.ones_like(dx)),axis=2)
    normal=n/np.linalg.norm(n,axis=2)[:,:,None]*.5+.5
    # Red occlusion, green roughness, blue relief for Unreal's bump offset.
    packed=np.stack((.38+.62*orm[:,:,0],.17+.80*orm[:,:,1],height),axis=2)
    diffuse=texture('T_ValleyBoulderMoss_BaseColor',color,False)
    normals=texture('T_ValleyBoulderMoss_NormalGL',normal,True)
    surface=texture('T_ValleyBoulderMoss_Surface',packed,True)
    mat=moss.copy();mat.name='M_ValleyBoulderMoss'
    mat.diffuse_color=tuple(color.mean(axis=(0,1)))+(1,)
    tree=mat.node_tree
    for node in list(tree.nodes):
        if node.type!='TEX_IMAGE': continue
        key=node.image.name
        if 'BaseColor' in key:node.image=diffuse
        elif 'NormalGL' in key:node.image=normals
        elif 'Roughness' in key:
            node.image=surface
            separate=tree.nodes.new('ShaderNodeSeparateColor')
            tree.links.new(node.outputs['Color'],separate.inputs['Color'])
            tree.links.new(separate.outputs['Green'],tree.nodes.get('Principled BSDF').inputs['Roughness'])
    return mat

boulder_moss=terrain_moss_material()
tipmat=bpy.data.materials.new("M_ValleyMossTips")
tipmat.diffuse_color=(.36,.54,.18,1);tipmat.use_nodes=True
b=tipmat.node_tree.nodes.get("Principled BSDF")
b.inputs['Base Color'].default_value=tipmat.diffuse_color
b.inputs['Roughness'].default_value=.91

BOUNDS={
    'SM_Valley_MossCliffShelf':((-2.2512128,-1.0856807,-.2568510),(2.5189342,.9940718,1.4482089)),
    'SM_Valley_MossPromontory':((-1.4448421,-1.1433696,-.1963560),(1.4316597,1.1786081,1.1225617)),
    'SM_Valley_MossCreekBoulder':((-.5093056,-.3984329,-.1053338),(.5789441,.4471750,.6134803)),
}

def create(name,w,depth,h,seed,rounded,fringe,creeping=False,shape=None):
    creeping=creeping or shape is not None
    cliff=name in ('SM_Valley_MossCliffShelf','SM_Valley_MossPromontory')
    sculpted_moss=creeping or cliff
    rng=random.Random(seed);ph=[rng.random()*2*pi for _ in range(9)]
    n=336 if creeping else 112
    verts=[];faces=[];indices=[];faceuv=[]
    def ring(rad,zf,mode):
        rr=[]
        for i in range(n):
            th=i*2*pi/n; c,s=cos(th),sin(th)
            wob=1+.049*sin(3*th+ph[0])+.028*cos(5*th+ph[1])+.019*sin(9*th+ph[2])
            x=math.copysign(abs(c)**rounded,c)*w*.5
            y=math.copysign(abs(s)**rounded,s)*depth*.5
            top=.95+.052*cos(2*th+ph[3])+.031*sin(5*th+ph[4])+.017*sin(11*th+ph[1])
            relief=.013*sin(14*th+zf*2.3+ph[6])+.010*sin(7*th+zf*2+ph[5])
            r=rad*wob*(1+relief)
            if mode=='rim': r+=.018*sin(19*th+ph[5])+.014*sin(31*th)
            z=zf*top*h
            if mode=='rim':
                z-=fringe*h*(.17+.39*(.5+.5*sin(5*th+ph[0]))+.19*(.5+.5*cos(9*th+ph[7]))+.25*(.5+.5*sin(21*th))**5)
            x=x*r+.023*w*sin(th*3+ph[3])*rad+.034*w*zf
            y=y*r+.032*depth*cos(2*th+ph[2])*rad
            rr.append(len(verts));verts.append((x,y,z))
        return rr
    def poly(idx,mi,uv):
        faces.append(tuple(idx));indices.append(mi);faceuv.append(uv)
    def planar(ids):
        return [(verts[i][0]*.84,verts[i][1]*.84) for i in ids]
    def side(btm,top,mi):
        for i in range(n):
            j=(i+1)%n
            ids=(btm[i],btm[j],top[j],top[i])
            x0=i/n*pi*(w+depth)*.5; x1=(i+1)/n*pi*(w+depth)*.5
            poly(ids,mi,[(x0,verts[ids[0]][2]),(x1,verts[ids[1]][2]),(x1,verts[ids[2]][2]),(x0,verts[ids[3]][2])])
    layers=[(.72,-.18),(.94,.06),(1.00,.22),(.993,.37),(.977,.39),(.994,.41),(1.009,.51),(.985,.57),(.979,.58),(.996,.6),(.969,.74),(.945,.86),(.83,.95)]
    if creeping:
        # Replace the layered sides with a single continuous, weathered body.
        # The crown and high lip retain their seats beneath the original moss.
        heights=np.linspace(-.18,.95,26)
        key_z=[-.18,.025,.24,.52,.70,.86,.95]
        key_r=[.72,.91,.985,.99,.974,.945,.83]
        layers=[(np.interp(z,key_z,key_r),z) for z in heights]
    rings=[ring(r,z,'rock') for r,z in layers]
    def smooth(a,b,x):
        t=max(0,min(1,(x-a)/(b-a)))
        return t*t*(3-2*t)
    if creeping:
        planes=[(-.69,.68,.20,.377),(.20,.94,.15,.388),
                (.78,.32,.78,.694),(-.15,.80,-.68,.213),(.91,-.18,-.37,.552)]
        if shape=='wedge':
            planes=[(-.73,.52,.32,.35),(.21,.92,-.32,.36),
                    (.71,.51,.67,.61),(.84,-.50,-.22,.439)]
        elif shape=='bluff':
            planes=[(-.88,.37,.33,.516),(-.55,.79,-.22,.345),
                    (.90,.29,.32,.487),(.33,-.86,-.35,.342)]
        elif shape=='step':
            planes=[(.22,.94,-.20,.374),(-.79,.50,.37,.41),
                    (.88,.38,.10,.576),(.65,-.55,-.50,.46)]
        for ring_ids,(_,zf) in zip(rings,layers):
            for idx in ring_ids:
                x,y,z=verts[idx]
                th=math.atan2(y/depth,x/w)
                # One broad, off-center shoulder projects past the moss skirt.
                # Its crown slopes across the stone rather than forming a ledge
                # at one common elevation around the boulder.
                heading=max(0,cos(th-.30))
                shoulder_top=.56+.14*sin(th+.11)
                lobe=.225*heading**3*smooth(-.14,.18,zf)*(1-smooth(shoulder_top-.16,shoulder_top+.17,zf))
                if shape=='wedge':
                    lobe=.10*max(0,cos(th-.85))**2*smooth(-.1,.15,zf)*(1-smooth(.37,.77,zf))
                elif shape=='bluff':
                    lobe=.18*max(0,cos(th-2.81))**2*smooth(-.08,.38,zf)*(1-smooth(.51,.88,zf))
                elif shape=='step':
                    # The step occupies one flank and fades at both ends.
                    flank=max(0,cos(th-.49))**2
                    ledge_top=.27+.10*sin(th+.23)
                    lobe=.24*flank*smooth(-.14,.10,zf)*(1-smooth(ledge_top,ledge_top+.15,zf))
                axis=Vector((x,y)).normalized()
                x+=axis.x*lobe;y+=axis.y*lobe
                radius=math.hypot(x,y)
                ux,uy=x/radius,y/radius
                for nx,ny,nz,distance in planes:
                    facing=nx*ux+ny*uy
                    if facing<=0: continue
                    limit=(distance-nz*z)/facing
                    # A narrow, rounded arris connects broad flat fracture faces.
                    bevel=max(.012-abs(radius-limit),0)
                    cut=min(radius,limit)-bevel*bevel/.048
                    radius+=(cut-radius)*(1-smooth(.61,.87,zf))
                verts[idx]=(ux*radius,uy*radius,z)
    poly(rings[0][::-1],0,planar(rings[0][::-1]))
    for lo,hi in zip(rings,rings[1:]):side(lo,hi,0)
    inset=ring(.50,.80,'rock')
    for i in range(n):
        j=(i+1)%n
        ids=(rings[-1][i],rings[-1][j],inset[j],inset[i]);poly(ids,0,planar(ids))
    poly(inset,0,planar(inset))
    # One continuous padded skin: neighboring tufts fuse at their bases, with
    # the largest pillows turning over the stone edge and shadowing the face.
    first_moss=len(verts)
    stone_surface=BVHTree.FromPolygons(verts,faces)
    n=112
    pads=[]
    for row in range(4):
        count=max(3,round((1-row*.27)*(.64*w+.36*depth)*7))
        for i in range(count):
            angle=2*pi*(i+rng.uniform(-.26,.26))/count+row*.49
            radius=(.96-row*.25)+rng.uniform(-.045,.045)
            pads.append((radius*cos(angle),radius*sin(angle),
                         rng.uniform(.11,.23)*2.8/w,rng.uniform(.15,.32)*2.25/depth,
                         rng.uniform(.048,.115)))
    def pillows(px,py):
        lobe=0
        for cx,cy,rx,ry,lift in pads:
            q=((px-cx)/rx)**2+((py-cy)/ry)**2
            if q<3:
                lobe+=lift*math.exp(-1.9*q)*(1-q/3)**2
        return min(.16,lobe)

    def moss_ring(rad,level,edge,roundness):
        ids=[]
        for i in range(n):
            th=2*pi*i/n
            c,s=cos(th),sin(th)
            swell=pillows(rad*c,rad*s)
            # Different rhythms at the bottom lip and along the crown avoid a
            # regular fringe; the underside tucks back into the existing rock.
            hanging=.50+.27*sin(5*th+ph[0])+.16*cos(8*th+ph[7])+.07*sin(14*th+ph[2])
            zf=level-edge*fringe*hanging+roundness*swell
            top=.95+.052*cos(2*th+ph[3])+.031*sin(5*th+ph[4])+.017*sin(11*th+ph[1])
            wob=1+.049*sin(3*th+ph[0])+.028*cos(5*th+ph[1])+.019*sin(9*th+ph[2])
            side_shape=.012*sin(8*th+ph[4])+.009*cos(13*th+ph[6])
            radius=rad*(wob+edge*(side_shape+.36*swell))
            x=w*.5*math.copysign(abs(c)**rounded,c)*radius+.023*w*sin(3*th+ph[3])*rad+.034*w*zf
            y=depth*.5*math.copysign(abs(s)**rounded,s)*radius+.032*depth*cos(2*th+ph[2])*rad
            z=h*(zf*(1+(top-1)*min(1,rad*1.3)))
            ids.append(len(verts));verts.append((x,y,z))
        return ids

    skin=[(.925,.816,1,0),(.969,.801,1,.02),(.994,.817,.99,.14),
          (1.000,.841,.93,.32),(.996,.868,.78,.50),(.990,.892,.59,.65),
          (.980,.913,.38,.79),(.962,.931,.19,.91)]
    if sculpted_moss:
        # Extra loops allow the moss to follow the narrow ledges in the stone.
        interpolated=[]
        for a,b in zip(skin,skin[1:]):
            for step in range(5):
                interpolated.append(tuple(x+(y-x)*step/5 for x,y in zip(a,b)))
        skin=interpolated+[skin[-1]]
    shoulder=len(skin)
    for j in range(39):
        t=j/39
        skin.append((.94*(1-t),.947+.035*sin(t*pi*.75),0,1))
    crown_faces=[]
    moss_rings=[]
    moss_rim_face_start=len(faces)
    last=None
    for radius,level,edge,roundness in skin:
        current=moss_ring(radius,level,edge,roundness)
        moss_rings.append(current)
        if radius==.980: upper_surface=current[0]
        if last:
            for i in range(n):
                j=(i+1)%n
                ids=(last[i],last[j],current[j],current[i])
                poly(ids,1,planar(ids))
                if .10<radius<.91: crown_faces.append(ids)
        last=current
    center=len(verts);verts.append((.034*w,0,h*.976))
    for i in range(n):
        ids=(last[i],last[(i+1)%n],center);poly(ids,1,planar(ids))

    # Occasional round-tipped three-leaf moss shoots, tucked into the cushions.
    first_shoot_face=len(faces)
    for _ in range(round(8+w*depth*5)):
        quad=rng.choice(crown_faces)
        a,b,c,d=(Vector(verts[i]) for i in quad)
        along=rng.random()
        p=a.lerp(b,along).lerp(d.lerp(c,along),rng.random())
        turn=rng.uniform(0,2*pi)
        for k in range(3):
            ang=turn+k*2*pi/3
            length=rng.uniform(.015,.033)*min(1.0,h+.25)
            forward=Vector((cos(ang),sin(ang),0))*length
            across=Vector((-sin(ang),cos(ang),0))*length*.24
            up=Vector((0,0,length))
            start=len(verts)
            verts.extend(tuple(pt) for pt in [p,p+.36*forward+across+.55*up,
                p+.72*forward+.76*across+.88*up,p+.79*forward+.95*up,
                p+.72*forward-.76*across+.88*up,p+.36*forward-across+.55*up,
                p+.42*forward+.67*up])
            for i in range(6):
                ids=(start+(i+1)%6,start+i,start+6);poly(ids,2,planar(ids))

    # Only reshape the new moss to respect the original placement envelope.
    # All original stone vertices, the pivot, local axes and scale are retained.
    lo,hi=BOUNDS['SM_Valley_MossCreekBoulder' if creeping else name]
    xyz=np.array(verts[first_moss:])
    for axis in range(3):
        if axis==2:
            z0=h*.74
            above=xyz[:,2]>z0
            xyz[above,2]=z0+(xyz[above,2]-z0)*(hi[2]-z0)/(xyz[:,2].max()-z0)
        else:
            stone_axis=[v[axis] for v in verts[:first_moss]]
            low=xyz[:,axis].min()
            high=xyz[:,axis].max()
            if min(stone_axis)<=lo[axis]+1e-6: low=min(low,lo[axis])
            if max(stone_axis)>=hi[axis]-1e-6: high=max(high,hi[axis])
            xyz[:,axis]=lo[axis]+(xyz[:,axis]-low)*(hi[axis]-lo[axis])/(high-low)
    verts[first_moss:]=[tuple(v) for v in xyz]
    # Clear the high points of the stone lip without changing any rock vertices.
    # A small, smooth transition prevents thin exposed slivers at glancing angles.
    for i in range(upper_surface,len(verts)):
        x,y,z=verts[i]
        hit=stone_surface.ray_cast((x,y,hi[2]+1),(0,0,-1))[0]
        if hit is not None:
            floor=hit.z+.013*h
            blend=max(.019*h-abs(z-floor),0)
            verts[i]=(x,y,min(hi[2],max(floor,z)+blend*blend/(.076*h)))
    if sculpted_moss:
        # Long lobes grow directly out of the same continuous cushion. Their
        # taper and subtle sideways drift differ around the stone. The prominent
        # lobe faces local +Y in Blender, corresponding to the creek approach.
        tongues=[(91,.34,.195,.07),(56,.21,.108,-.03),(-72,.29,.214,-.12),
                 (-151,.19,.17,.08),(153,.15,.108,-.07)]
        if shape=='wedge':
            tongues=[(124,.46,.18,-.10),(39,.24,.082,.03),(-72,.37,.154,.06)]
        elif shape=='bluff':
            tongues=[(72,.26,.22,.13),(101,.16,.087,.05),(167,.43,.14,-.09),
                     (-115,.23,.17,.12)]
        elif shape=='step':
            tongues=[(48,.36,.151,-.09),(79,.16,.105,.03),(-178,.42,.129,.06),
                     (-60,.21,.18,-.12)]
        elif name=='SM_Valley_MossCliffShelf':
            tongues=[(69,.19,.43,.08),(106,.24,.29,-.05),(-55,.20,.36,.07),(-126,.24,.48,-.07)]
        elif name=='SM_Valley_MossPromontory':
            tongues=[(24,.27,.24,-.06),(88,.29,.36,.11),(-78,.21,.34,-.09),(-154,.18,.20,.07)]
        pad_scale=h/.56 if cliff else 1.
        ray_radius=max(w,depth)+1 if cliff else 2.
        for ring_number,ring_ids in enumerate(moss_rings[:shoulder]):
            level=ring_number/5
            t=min(1,max(0,(level-.8)/6.2))
            profile=1-t*t*(3-2*t)
            for i,idx in enumerate(ring_ids):
                a=2*pi*i/n
                pull=0
                for bearing,width,length,drift in tongues:
                    target=math.radians(bearing)+drift*profile
                    delta=math.atan2(sin(a-target),cos(a-target))
                    q=abs(delta)/width
                    if q<1:
                        pull=max(pull,length*(1-q*q)**1.75)
                x,y,z=verts[idx]
                direction=Vector((x,y,0)).normalized()
                new_z=z-profile*pull
                origin=direction*ray_radius+Vector((0,0,new_z))
                contact=stone_surface.ray_cast(origin,-direction)[0]
                if contact is None or contact.dot(direction)<=0: continue
                edge_padding=pad_scale*np.interp(level,[0,1,2,3,4,5,6,7],
                    [-.003,.006,.011,.015,.019,.019,.014,.010])
                surface_radius=math.hypot(contact.x,contact.y)
                # Keep the original cap's outward fullness where the creep
                # attaches. Conform progressively to the face further down.
                influence=min(1,pull*profile/.12)
                radius=(1-influence)*math.hypot(x,y)+influence*(surface_radius+edge_padding)
                protected=max(radius,surface_radius+edge_padding)
                correction=1-min(1,max(0,(level-4.5)/2.5))
                radius=radius+(protected-radius)*correction
                # The lower skin follows freshly cut faces and stays seated at
                # its foot. Gradually release this constraint into the crown.
                limit=surface_radius+max(0,edge_padding)+.009
                radius+=(min(radius,limit)-radius)*(1-smooth(3.6,6.2,level))
                verts[idx]=(direction.x*radius,direction.y*radius,new_z)
        # Roll the top into the flank over a hand-width band. A cubic section
        # matches the existing flank and crown tangents at both ends; the
        # lowest turn, which establishes the tongue lengths, stays in place.
        flank=14
        crown=shoulder+8
        moss_face_ids=[f for f,material in zip(faces,indices) if material==1]
        old_skin=BVHTree.FromPolygons(verts,moss_face_ids)
        correction=np.zeros((crown-flank+1,n))
        directions={}
        for i in range(n):
            band=[moss_rings[row][i] for row in range(flank,crown+1)]
            path=[Vector(verts[idx]) for idx in band]
            arc=np.r_[0.,np.cumsum([(b-a).length for a,b in zip(path,path[1:])])]
            a,b=path[0],path[-1]
            incoming=(a-Vector(verts[moss_rings[flank-3][i]])).normalized()
            outgoing=(Vector(verts[moss_rings[crown+2][i]])-b).normalized()
            arm=(b-a).length*.57
            control_a=a+arm*incoming
            control_b=b-arm*outgoing
            for k,(idx,distance) in enumerate(zip(band[1:-1],arc[1:-1]),1):
                t=float(distance/arc[-1]);s=1-t
                p=s*s*s*a+3*s*s*t*control_a+3*s*t*t*control_b+t*t*t*b
                # Add softness outside the original stone envelope rather than
                # shaving the corner through the high point of the rock.
                bulge=(sin(pi*t)**2)*.028*pad_scale
                outward=Vector((p.x,p.y,0)).normalized()
                p+=bulge*(outward+Vector((0,0,.85)))
                verts[idx]=tuple(p)
                direction=(outward*(1-t)+Vector((0,0,t))).normalized()
                directions[idx]=direction
                hit=stone_surface.ray_cast(p+direction,-direction,2)[0]
                if hit is not None:
                    correction[k,i]=max(0,.009*pad_scale-(p-hit).dot(direction))
        # Carry clearance into the adjacent samples so an angular stone
        # shoulder cannot poke through the continuous fillet or flatten it.
        for _ in range(8):
            blurred=(np.roll(correction,1,axis=1)+np.roll(correction,-1,axis=1)+
                     np.roll(correction,1,axis=0)+np.roll(correction,-1,axis=0))*.25
            correction=np.maximum(correction,blurred)
            correction[[0,-1]]=0
        for k in range(1,crown-flank):
            for i,idx in enumerate(moss_rings[flank+k]):
                verts[idx]=tuple(Vector(verts[idx])+float(correction[k,i])*directions[idx])
        new_skin=BVHTree.FromPolygons(verts,moss_face_ids)
        # Move each original seven-vertex leaf rigidly with its rooting point.
        for root in range(center+1,len(verts),7):
            x,y,_=verts[root]
            origin=(x,y,hi[2]+1)
            old=old_skin.ray_cast(origin,(0,0,-1))[0]
            new=new_skin.ray_cast(origin,(0,0,-1))[0]
            if old is None or new is None: continue
            dz=new.z-old.z
            for idx in range(root,root+7):
                x,y,z=verts[idx];verts[idx]=(x,y,z+dz)
    # Unfold the turned lip into the same UV island as its crown. Each spoke
    # spends exactly as much UV distance as it travels over the finished mesh.
    # A horizontal top projection alone collapses the nap on vertical surfaces.
    anchor=moss_rings[shoulder]
    rim_uv={}
    for i,idx in enumerate(anchor):
        # The superellipse's smooth outward normal avoids UV folds where two
        # adjacent sculpted lobes curve back toward one another.
        th=2*pi*i/n
        c,s=cos(th),sin(th)
        outward=Vector((math.copysign(abs(c)**(2-rounded),c)/w,
                        math.copysign(abs(s)**(2-rounded),s)/depth)).normalized()
        uv=Vector((verts[idx][0],verts[idx][1]))*.84
        rim_uv[idx]=tuple(uv)
        previous=Vector(verts[idx])
        for ring_indices in reversed(moss_rings[:shoulder]):
            idx=ring_indices[i]
            point=Vector(verts[idx])
            uv+=outward*((point-previous).length*.84)
            rim_uv[idx]=tuple(uv)
            previous=point
    for face in range(moss_rim_face_start,moss_rim_face_start+shoulder*n):
        faceuv[face]=[rim_uv[idx] for idx in faces[face]]
    if sculpted_moss:
        # Use the original planted markers to preserve each cluster's position,
        # orientation and scale on the finished moss.
        guides=[(Vector(verts[j]),Vector(verts[j+3])) for j in range(center+1,len(verts),7)]
        del verts[center+1:]
        del faces[first_shoot_face:],indices[first_shoot_face:],faceuv[first_shoot_face:]
        up=Vector((0,0,1))
        segments=10
        for leaf,(base,tip) in enumerate(guides):
            reach=tip-base
            forward=Vector((reach.x,reach.y,0)).normalized()
            across=up.cross(forward)
            length=max(reach.length,.01)*1.28
            hit=new_skin.ray_cast((base.x,base.y,hi[2]+1),(0,0,-1))[0]
            if hit is not None: base.z=hit.z
            base-=up*(length*.09)
            root=len(verts);verts.append(tuple(base))
            previous=[]
            # Sweep a plump oval section up an arch, rolling the lip gently
            # down. A shallow transverse cup makes the side rims catch light.
            lean=.09*sin(leaf*2.4)
            for t in (.09,.22,.39,.57,.73,.86,.95,.985):
                arc=sin(pi*t)
                mid=base+length*(forward*t+across*(lean*t*t)+up*(.63*t+.34*arc))
                tangent=(forward+2*lean*t*across+up*(.63+.34*pi*cos(pi*t))).normalized()
                normal=tangent.cross(across).normalized()
                lateral=normal.cross(tangent)
                profile=arc**.54*(.55+.76*t)
                ring=[]
                for k in range(segments):
                    angle=2*pi*k/segments
                    side=cos(angle)
                    point=mid+length*profile*(.325*side*lateral+(.095*sin(angle)+.059*side*side)*normal)
                    ring.append(len(verts));verts.append(tuple(point))
                for k in range(segments):
                    j=(k+1)%segments
                    ids=(previous[k],previous[j],ring[j],ring[k]) if previous else (root,ring[j],ring[k])
                    poly(ids,2,planar(ids))
                previous=ring
            end=len(verts);verts.append(tuple(base+length*(forward+lean*across+.63*up)))
            for k in range(segments):
                ids=(previous[k],previous[(k+1)%segments],end);poly(ids,2,planar(ids))

    # Shape the complete skin and stone together, so the crown, turned-over
    # rim and individual shoots all keep their contact with the underlying rock.
    if shape=='wedge':
        verts=[(1.27*x,y*(.88+.12*x),z*(.73+.51*x)+.020*x) for x,y,z in verts]
    elif shape=='bluff':
        verts=[(.87*x-.21*z,1.025*y+.085*z,1.19*z) for x,y,z in verts]
    elif shape=='step':
        verts=[(1.11*x,.91*y,z*(.90-.12*x)+.027*y) for x,y,z in verts]
    mesh=bpy.data.meshes.new(name);mesh.from_pydata(verts,[],faces);mesh.materials.append(rock);mesh.materials.append(boulder_moss if creeping else moss);mesh.materials.append(tipmat)
    mesh.update();uv=mesh.uv_layers.new(name='SurfaceUV')
    for poly_,mi,coords in zip(mesh.polygons,indices,faceuv):
        poly_.material_index=mi;poly_.use_smooth=sculpted_moss or mi!=2
        for idx,xy in zip(poly_.loop_indices,coords):uv.data[idx].uv=xy
    obj=bpy.data.objects.new(name,mesh);scene.collection.objects.link(obj)
    for ob in bpy.context.selected_objects:ob.select_set(False)
    obj.select_set(True);bpy.context.view_layer.objects.active=obj
    if sculpted_moss:
        # Relax the crown and visible drape together with the crown interior
        # pinned to its world-scale UVs. A few short darts at the tucked lower
        # lip relieve the longest tongues without cutting through the shoulder.
        fixed={v for ring_ids in moss_rings[shoulder+8:] for v in ring_ids}
        fixed.add(center)
        for p in mesh.polygons:
            p.select=p.material_index==1
            if p.select:
                for vid,lid in zip(p.vertices,p.loop_indices):
                    if vid in fixed:
                        uv.data[lid].uv=(verts[vid][0]*.84,verts[vid][1]*.84)
                        uv.data[lid].pin_uv=True
        darts={frozenset((moss_rings[row][i],moss_rings[row+1][i]))
               for i in (5,53,76,103) for row in range(11)}
        for edge in mesh.edges:
            if frozenset(edge.vertices) in darts: edge.use_seam=True
        bpy.context.tool_settings.mesh_select_mode=(False,False,True)
        bpy.ops.object.mode_set(mode='EDIT')
        bpy.ops.uv.unwrap(method='CONFORMAL',correct_aspect=False,margin=0)
        bpy.ops.uv.unwrap(method='MINIMUM_STRETCH',iterations=20,correct_aspect=False,margin=0)
        bpy.ops.object.mode_set(mode='OBJECT')
    export_mesh=(cliff if '--cliffs-only' in sys.argv else
                 creeping if '--creek-boulders-only' in sys.argv else
                 shape is not None if '--creek-set-only' in sys.argv else
                 name=='SM_Valley_CreepingMossBoulder' if '--variant-only' in sys.argv else True)
    if export_mesh:
        bpy.ops.export_scene.fbx(filepath=str(OUT/(name+'.fbx')),use_selection=True,object_types={'MESH'},axis_forward='-Y',axis_up='Z',apply_unit_scale=True,apply_scale_options='FBX_SCALE_NONE',bake_anim=False,add_leaf_bones=False,mesh_smooth_type='FACE',path_mode='RELATIVE')
    if cliff or name=='SM_Valley_MossCreekBoulder':
        # Existing FBX slot names are a reimport contract. Match the assigned
        # Unreal material override when presenting the original rock in Blender.
        mesh.materials[1]=boulder_moss
    print(name,'dimensions',tuple(round(v,3) for v in obj.dimensions),'polys',len(mesh.polygons),flush=True)
    return obj

shelf=create('SM_Valley_MossCliffShelf',4.70,2.00,1.38,153,.70,.23)
point=create('SM_Valley_MossPromontory',2.8,2.25,1.05,490,.82,.21)
stone=create('SM_Valley_MossCreekBoulder',1.03,.83,.56,212,.88,.31)
creeper=create('SM_Valley_CreepingMossBoulder',1.03,.83,.56,212,.88,.31,creeping=True)
creeper.location=(-1.15,-1.8,0);creeper.rotation_euler.z=math.pi
for tag,shape,seed,roundness,fringe,x in [
        ('LowWedge','wedge',399,.79,.27,-2.10),
        ('OffsetBluff','bluff',749,.61,.23,-.27),
        ('SteppedFlank','step',589,.75,.25,1.55)]:
    obj=create('SM_Valley_CreekBoulder_'+tag,1.03,.83,.56,seed,roundness,fringe,shape=shape)
    obj.location=(x,-3.48,0)
    obj.rotation_euler.z=math.pi
shelf.location=(-2.5,0,0);point.location=(2,0,0);stone.location=(.4,-1.8,0)
bpy.context.preferences.filepaths.save_version=0
bpy.ops.file.pack_all()
bpy.ops.wm.save_as_mainfile(filepath=str(OUT/'ValleyCliffs.blend'))
