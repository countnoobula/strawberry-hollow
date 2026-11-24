"""Generate Strawberry Hollow's moss-fringed creekstone kit. Run with Blender in background."""
import math
import random
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
        # Gentle lilac-grey shadows warm toward sandstone. Broad, curved bedding
        # has soft borders. The smoothed stone silhouette supplies deeper creases.
        phase=2*pi*(yy*2+.16*np.sin(2*pi*xx)+.50*(broad-.5))
        band=(.5+.5*np.cos(phase))**5
        light=np.clip(.24+.35*broad+.35*drift+.06*np.sin(phase)-.09*band,0,1)
        base=np.array([.44,.42,.48])+(np.array([.72,.69,.65])-np.array([.44,.42,.48]))*light[:,:,None]
        h=.23*broad+.18*drift-.055*band
        rough=.78+.07*drift
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

def create(name,w,depth,h,seed,rounded,fringe):
    rng=random.Random(seed);ph=[rng.random()*2*pi for _ in range(9)]
    n=112;verts=[];faces=[];indices=[];faceuv=[]
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
    rings=[ring(r,z,'rock') for r,z in layers]
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
    lo,hi=BOUNDS[name]
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
    # Unfold the turned lip into the same UV island as its crown. Each spoke
    # spends exactly as much UV distance as it travels over the finished mesh.
    # A horizontal top projection alone collapses the nap on vertical surfaces.
    shoulder=8
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
    mesh=bpy.data.meshes.new(name);mesh.from_pydata(verts,[],faces);mesh.materials.append(rock);mesh.materials.append(moss);mesh.materials.append(tipmat)
    mesh.update();uv=mesh.uv_layers.new(name='SurfaceUV')
    for poly_,mi,coords in zip(mesh.polygons,indices,faceuv):
        poly_.material_index=mi;poly_.use_smooth=mi!=2
        for idx,xy in zip(poly_.loop_indices,coords):uv.data[idx].uv=xy
    obj=bpy.data.objects.new(name,mesh);scene.collection.objects.link(obj)
    for ob in bpy.context.selected_objects:ob.select_set(False)
    obj.select_set(True);bpy.context.view_layer.objects.active=obj
    bpy.ops.export_scene.fbx(filepath=str(OUT/(name+'.fbx')),use_selection=True,object_types={'MESH'},axis_forward='-Y',axis_up='Z',apply_unit_scale=True,apply_scale_options='FBX_SCALE_NONE',bake_anim=False,add_leaf_bones=False,mesh_smooth_type='FACE',path_mode='RELATIVE')
    print(name,'dimensions',tuple(round(v,3) for v in obj.dimensions),'polys',len(mesh.polygons),flush=True)
    return obj

shelf=create('SM_Valley_MossCliffShelf',4.70,2.00,1.38,153,.70,.23)
point=create('SM_Valley_MossPromontory',2.8,2.25,1.05,490,.82,.21)
stone=create('SM_Valley_MossCreekBoulder',1.03,.83,.56,212,.88,.31)
shelf.location=(-2.5,0,0);point.location=(2,0,0);stone.location=(.4,-1.8,0)
bpy.context.preferences.filepaths.save_version=0
bpy.ops.file.pack_all()
bpy.ops.wm.save_as_mainfile(filepath=str(OUT/'ValleyCliffs.blend'))
