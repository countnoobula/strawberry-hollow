"""Generate Strawberry Hollow's moss-fringed creekstone kit. Run with Blender in background."""
import math
import random
from pathlib import Path
import bpy
import numpy as np
from mathutils import Vector
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

def texture(name, pixels, is_data):
    image = bpy.data.images.new(name, width=size, height=size, alpha=False)
    image.colorspace_settings.name = "Non-Color" if is_data else "sRGB"
    color = np.clip(pixels,0,1).astype('float32')
    if not is_data:
        color = np.where(color < .04045,color/12.92,((color+.055)/1.055)**2.4)
    rgba = np.empty((size,size,4),dtype='float32')
    rgba[:,:,:3] = color
    rgba[:,:,3] = 1
    image.pixels.foreach_set(rgba.ravel())
    image.filepath_raw = str(TEX/(name+'.png'))
    image.file_format='PNG'
    image.save()
    # Textures on disk are the source of truth for FBX and packed blend.
    bpy.data.images.remove(image)
    img=bpy.data.images.load(str(TEX/(name+'.png')))
    img.colorspace_settings.name='Non-Color' if is_data else 'sRGB'
    return img

def make_surface(kind):
    n0=noise(15,4,4); n1=noise(23,12,12); n2=noise(36,38,38)
    n3=noise(45,100,100); n4=noise(46,230,230); micro=noise(48,420,420)
    if kind=='Creekstone':
        # Warm grey-violet sandstone with softly eroded bedding and sparse mineral grains.
        phase=2*pi*(yy*6+.31*np.sin(2*pi*xx)+1.12*(n0-.5)+.28*(n1-.5))
        seam=np.clip((np.cos(phase)-.78)/.22,0,1)**2
        fleck=np.clip((n4+n3*.23-.80)*4,0,1)
        mottled=(.28*n0+.26*n1+.22*n2+.11*n3+.08*n4+.05*micro)
        d=((mottled-.49)*.53 + .019*np.sin(phase)-.073*seam+.045*fleck)
        base=np.array([.57,.515,.48])+d[:,:,None]*np.array([.98,.93,.89])
        base[:,:,:]+= (n0-.5)[:,:,None]*np.array([.054,-.017,.044])
        h=.46*n2+.24*n3+.14*n4+.06*micro-.18*seam+.08*fleck
        rough=.80+.10*n2
    else:
        # Mixed green growth, fine golden cushions and darker creases between the moss heads.
        heads=noise(93,80,80)*.58+n4*.29+micro*.13
        pockets=np.clip((.40-heads)*4.7,0,1)
        ridge=(.39*n0+.25*n1+.16*n2+.20*heads)
        col=np.clip((ridge-.19)*1.45,0,1)
        base=np.array([.23,.295,.135])+(np.array([.43,.43,.16])[None,None,:]*col[:,:,None])
        base+=(heads-.5)[:,:,None]*np.array([.20,.18,.075])
        base-=pockets[:,:,None]*np.array([.091,.071,.03])
        h=.37*n1+.28*n2+.34*heads-.14*pockets
        rough=.88+.09*n2
    hn=(np.roll(h,-1,1)-np.roll(h,1,1))*1.7
    vn=(np.roll(h,-1,0)-np.roll(h,1,0))*1.7
    normal=np.stack([-hn,-vn,np.ones_like(h)],axis=2)
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
tipmat.diffuse_color=(.23,.30,.075,1);tipmat.use_nodes=True
b=tipmat.node_tree.nodes.get("Principled BSDF")
b.inputs['Base Color'].default_value=tipmat.diffuse_color
b.inputs['Roughness'].default_value=.91

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
    # Drape moss tightly onto the actual rim profile, giving it some thickness at the overhang.
    top=ring(.975,.875,'rim')
    inn=ring(.931,.882,'rim');side(inn,top,1)
    last=top
    crowns=[]
    for rad,zf in [(.980,.903),(.961,.926),(.930,.949),(.86,.974),(.74,.986),(.56,.999),(.33,1.006),(.12,1.01)]:
        nxt=ring(rad,zf,'plain' if rad<.94 else 'rim')
        for i in range(n):
            j=(i+1)%n;ids=(last[i],last[j],nxt[j],nxt[i])
            if rad>.94:
                x0=i/n*pi*(w+depth)*.5; x1=(i+1)/n*pi*(w+depth)*.5
                poly(ids,1,[(x0,verts[ids[0]][2]),(x1,verts[ids[1]][2]),(x1,verts[ids[2]][2]),(x0,verts[ids[3]][2])])
            else:poly(ids,1,planar(ids))
            if rad>.33: crowns.append(ids)
        last=nxt
    poly(last,1,planar(last))
    # Fine clustered shoots break the moss silhouette, with real geometry and two-sided folded leaves.
    for _ in range(int(w*depth*58)):
        patch=rng.choice(crowns);a,b,c,d=(Vector(verts[i]) for i in patch)
        t=rng.random();r=rng.random();p=a.lerp(b,t).lerp(d.lerp(c,t),r)
        for k in range(rng.randint(3,7)):
            root=p+Vector((rng.uniform(-.014,.014),rng.uniform(-.014,.014),0))
            length=rng.uniform(.012,.042);th=rng.uniform(0,2*pi)
            wing=Vector((-sin(th),cos(th),0))*length*.15
            end=root+Vector((cos(th)*length*.58,sin(th)*length*.58,length*rng.uniform(.63,1.25)))
            mid=root.lerp(end,.45)+Vector((0,0,length*.18))
            ids=[]
            for pt in (root,mid-wing,mid+Vector((0,0,length*.09)),mid+wing,end):
                ids.append(len(verts));verts.append(tuple(pt))
            for i,j,k in ((0,2,1),(0,3,2),(1,2,4),(2,3,4)):
                tri=tuple(ids[a] for a in (i,j,k));poly(tri,2,planar(tri))
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
