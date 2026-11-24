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


# Long axial fibers and sinuous fissures remain continuous around the trunk's circumference.
line=noise(801,4,4)*.50+noise(803,8,8)*.22
vwarp=yy+.010*np.sin(2*pi*xx)+.037*(line-.4)+.003*np.sin(6*pi*xx+2*pi*yy)
def vfield(freq,offset):
    return np.cos(2*pi*(vwarp*freq+offset+.08*np.sin(2*pi*xx+freq*.11)))
haze=noise(24,7,25); fleck=noise(52,40,155); micro=noise(9,140,410)
broad=vfield(12,.1)
fiss=np.clip((broad-.18)/.82,0,1)**3
secondary=np.clip((vfield(31,.2)-.46)/.54,0,1)**2
fiber=vfield(83,.43)
tone=.49*(haze-.46)+.18*(fleck-.5)+.13*(micro-.5)-.29*fiss-.12*secondary+.026*fiber
base=np.array([.45,.354,.285])+tone[:,:,None]*np.array([.59,.50,.47])
base+=(noise(38,4,9)-.49)[:,:,None]*np.array([.06,.063,.085])
height=.33*broad*-1+.25*(1-secondary)+.2*fleck+.09*micro+.07*fiber
du=(np.roll(height,-1,1)-np.roll(height,1,1))*2.5
dv=(np.roll(height,-1,0)-np.roll(height,1,0))*2.5
normal=np.stack([-du,-dv,np.ones_like(du)],axis=2)
normal=normal/np.linalg.norm(normal,axis=2)[:,:,None]*.5+.5
rough=np.clip(.82+.12*fiss+.04*micro,0,1)
maps=[texture('T_ValleyRootBark_BaseColor',base,False),texture('T_ValleyRootBark_NormalGL',normal,True),texture('T_ValleyRootBark_Roughness',np.repeat(rough[:,:,None],3,axis=2),True)]
bark=bpy.data.materials.new('M_ValleyRootBark');bark.use_nodes=True
bs=bark.node_tree.nodes.get('Principled BSDF')
for i,img in enumerate(maps):
    node=bark.node_tree.nodes.new('ShaderNodeTexImage');node.image=img;node.location=(-600,250-260*i)
    if i==0:bark.node_tree.links.new(node.outputs[0],bs.inputs['Base Color'])
    if i==1:
        nm=bark.node_tree.nodes.new('ShaderNodeNormalMap');nm.inputs['Strength'].default_value=.75
        bark.node_tree.links.new(node.outputs[0],nm.inputs['Color']);bark.node_tree.links.new(nm.outputs[0],bs.inputs['Normal'])
    if i==2:bark.node_tree.links.new(node.outputs[0],bs.inputs['Roughness'])
with bpy.data.libraries.load(str(OUT.parent/'ValleyCliffs'/'ValleyCliffs.blend'),link=False) as (available,new):
    new.materials=['M_ValleyMoss','M_ValleyMossTips']
moss,tips=new.materials
verts=[];faces=[];materials=[];texcoords=[];rng=random.Random(719)
def vert(p):
    verts.append(tuple(p));return len(verts)-1
def face(ids,mat,uv):
    faces.append(tuple(ids));materials.append(mat);texcoords.append(uv)
def surface(x,a,detail=True):
    t=x/5.27
    height=.015+4.035*(1-(math.sqrt(x*x+.46*.46)-.46)/(math.sqrt(5.27**2+.46*.46)-.46))
    height+=.075*(1-t*t)*sin(x*1.2)
    ry=.70+.09*sin(x*1.39+.4)+.14*(abs(t)**2)+.035*cos(x*2.6)
    rz=.46+.21*(1-t*t)+.042*sin(x*1.9+.2)
    center_y=.105*sin(.95*x+.1)+.039*cos(x*2.05)
    q=cos(a);s=sin(a)
    # Mild spiral, folded bark ridges, and a local grain vortex around a weather knot.
    w=a+.105*sin(.85*x+a*.8)+.06*sin(1.82*x+a*2)
    knot=math.exp(-((x+.7)/.85)**2)*math.exp(-((a-2.95)/.60)**2)
    w+=.30*knot*sin(3*(a-2.95))
    folds=.017*sin(18*w+.33*x)+.009*sin(31*w-.21*x)+.015*cos(9*w+.45*x)
    folds*=1-.74*max(s,0)**5
    crawl=(1+folds if detail else 1)
    y=center_y+ry*math.copysign(abs(q)**.79,q)*crawl
    z=height-rz+rz*math.copysign(abs(s)**.74,s)*crawl
    return Vector((x,y,z))
N=152;M=112;rings=[]
for i in range(N+1):
    x=-5.27+10.54*i/N;rings.append([vert(surface(x,j*2*pi/M)) for j in range(M)])
for i in range(N):
    for j in range(M):
        k=(j+1)%M
        ids=(rings[i][j],rings[i][k],rings[i+1][k],rings[i+1][j])
        u0=i/N*5.8;u1=(i+1)/N*5.8;v0=j/M*2.3;v1=(j+1)/M*2.3
        face(ids,0,[(u0,v0),(u0,v1),(u1,v1),(u1,v0)])
for i in (0,N):
    ids=rings[i][::-1] if i==0 else rings[i]
    face(ids,0,[(verts[k][1]*.65,verts[k][2]*.65) for k in ids])
def thread(center, width, count, mat,seed):
    points=[Vector(v) for v in center];rows=[]
    for i,p in enumerate(points):
        tangent=(points[min(i+1,len(points)-1)]-points[max(0,i-1)]).normalized()
        ref=Vector((0,0,1)) if abs(tangent.z)<.88 else Vector((1,0,0))
        across=tangent.cross(ref).normalized()
        normal=tangent.cross(across).normalized()
        row=[];rs=width[i]
        for j in range(count):
            a=2*pi*j/count
            r=rs*(1+.09*sin(a*5+.06*i+seed)+.06*cos(3*a-.035*i))
            row.append(vert(p+r*(across*cos(a)+normal*sin(a))))
        rows.append(row)
    for i in range(len(rows)-1):
        for j in range(count):
            k=(j+1)%count
            ids=(rows[i][j],rows[i][k],rows[i+1][k],rows[i+1][j])
            face(ids,mat,[(i*.06,j/count*.52),(i*.06,(j+1)/count*.52),((i+1)*.06,(j+1)/count*.52),((i+1)*.06,j/count*.52)])
    face(rows[0][::-1],mat,[(0,0)]*count);face(rows[-1],mat,[(.5,.5)]*count)
# Subordinate root flutes hug the structural arch rather than drawing uniform bands over it.
for j in range(13):
    a0=(j+.4)*2*pi/13
    if .64<a0<2.48:continue
    pts=[];r=[]
    for i in range(85):
        t=i/84;x=-5.24+10.45*t;a=a0+.24*sin(x*.7+j)+.09*cos(x*1.6-j)
        p=surface(x,a)
        rr=.058+.043*(.5+.5*sin(x*1.8+j))+.072*abs(2*t-1)**1.4
        p.y-=rr*.60*cos(a);p.z-=rr*.59*sin(a)
        pts.append(p);r.append(rr*(.26+.74*min(1,t*10,(1-t)*10)))
    thread(pts,r,10,0,j)
# Crown quilt overlaps bark along individually eroded edges and drapes lower at each shoulder.
def crown(x,t):
    left=.68+.22*sin(1.7*x)+.12*cos(3.7*x)-.13*max(0,sin(5.4*x))**4
    right=2.60+.22*sin(1.3*x+.7)+.14*cos(3.4*x)+.12*max(0,cos(6*x))**4
    a=left+(right-left)*t;p=surface(x,a)
    cushion=.026+.052*(max(0,4*t*(1-t)))**.6+.012*sin(x*4.3+a*3)
    p.y+=cushion*cos(a);p.z+=cushion*sin(a)
    return p
rows=[]
for i in range(N+1):
    x=-5.25+10.50*i/N
    rows.append([vert(crown(x,j/28)) for j in range(29)])
for i in range(N):
    for j in range(28):
        ids=(rows[i][j],rows[i][j+1],rows[i+1][j+1],rows[i+1][j])
        face(ids,1,[(i/15,j/18),(i/15,(j+1)/18),((i+1)/15,(j+1)/18),((i+1)/15,j/18)])
for j in (0,28):
    lower=[]
    for i in range(N+1):
        p=Vector(verts[rows[i][j]]);p.z-=.04;p.y+=(.015 if j==28 else -.015);lower.append(vert(p))
    for i in range(N):
        face((lower[i],rows[i][j],rows[i+1][j],lower[i+1]),1,[(i/15,0),(i/15,.06),((i+1)/15,.06),((i+1)/15,0)])
# Uneven cushion tufts, concentrated at clump boundaries.
for _ in range(2700):
    x=rng.uniform(-5.22,5.22)
    t=rng.random()
    if rng.random()>.56+.38*sin(x*3.7+t*7):continue
    p=crown(x,t)
    for k in range(rng.randint(3,7)):
        root=p+Vector((rng.uniform(-.026,.026),rng.uniform(-.021,.021),0))
        a=rng.uniform(0,2*pi);length=rng.uniform(.017,.055)
        tip=root+Vector((length*.66*cos(a),length*.66*sin(a),length))
        mid=root.lerp(tip,.45)+Vector((0,0,length*.2))
        e=Vector((-sin(a),cos(a),0))*length*.17
        ids=[vert(k) for k in (root,mid-e,mid+Vector((0,0,length*.1)),mid+e,tip)]
        for tr in ((0,2,1),(0,3,2),(1,2,4),(2,3,4)):
            face([ids[k] for k in tr],2,[(0,0),(1,.4),(.5,1)])
# Slender hanging sprigs join the moss rim to weathered bark.
for j in range(25):
    x=rng.uniform(-4.8,4.8);t=0 if rng.random()<.45 else 1
    start=crown(x,t);length=rng.uniform(.10,.38);direction=1 if t==0 else -1
    pts=[start+Vector((.033*sin(i*.7+j),direction*.02*sin(pi*i/7),-length*i/7)) for i in range(8)]
    thread(pts,[.013*(1-i/10) for i in range(8)],5,1,j)
    for i in (2,4,6):
        p=pts[i];vx=.046 if i%4==0 else -.046
        points=[p,p+Vector((vx*.52,-.012,-.025)),p+Vector((vx*1.4,0,-.068)),p+Vector((vx*.6,.012,-.044))]
        face([vert(k) for k in points],2,[(0,0),(0,1),(1,1),(1,0)])
name='SM_Valley_MossRootArch'
# Match the existing placed arch pivot and extents, preserving both bank approaches.
bounds=[(-5.2854,5.2796),(-.9268,1.0394),(-.7642,4.18)]
spans=[(min(p[i] for p in verts),max(p[i] for p in verts)) for i in range(3)]
def matched(p):
    return tuple(bounds[i][0]+(p[i]-spans[i][0])*(bounds[i][1]-bounds[i][0])/(spans[i][1]-spans[i][0]) for i in range(3))
verts=[matched(p) for p in verts]
mesh=bpy.data.meshes.new(name);mesh.from_pydata(verts,[],faces)
for mat in [bark,moss,tips]:mesh.materials.append(mat)
mesh.update();uv=mesh.uv_layers.new(name='SurfaceUV')
for poly,m,uvs in zip(mesh.polygons,materials,texcoords):
    poly.material_index=m;poly.use_smooth=m!=2
    for idx,pt in zip(poly.loop_indices,uvs):uv.data[idx].uv=pt
obj=bpy.data.objects.new(name,mesh);scene.collection.objects.link(obj)
obj.select_set(True);bpy.context.view_layer.objects.active=obj
bpy.ops.export_scene.fbx(filepath=str(OUT/(name+'.fbx')),use_selection=True,object_types={'MESH'},axis_forward='-Y',axis_up='Z',apply_unit_scale=True,apply_scale_options='FBX_SCALE_NONE',bake_anim=False,add_leaf_bones=False,mesh_smooth_type='FACE',path_mode='RELATIVE')
# A dedicated smooth triangle shell supplies accurate complex collision underneath and
# over the crown without thousands of tiny moss-shoot collision faces.
cv=[];cf=[]
for i in range(81):
    x=-5.27+10.54*i/80
    for j in range(52):
        a=j*2*pi/52;p=surface(x,a,False)
        if .6<a<2.65:p.z+=.072*max(0,sin(a))
        cv.append(matched(p))
for i in range(80):
    for j in range(52):
        k=(j+1)%52
        cf.append((i*52+j,i*52+k,(i+1)*52+k,(i+1)*52+j))
cf.append(tuple(reversed(range(52))))
cf.append(tuple(range(80*52,81*52)))
collision_mesh=bpy.data.meshes.new('RootWalkShell');collision_mesh.from_pydata(cv,[],cf);collision_mesh.update()
cu=collision_mesh.uv_layers.new(name='SurfaceUV')
for loop in collision_mesh.loops:
    v=cv[loop.vertex_index];cu.data[loop.index].uv=(v[0],v[1])
collision=bpy.data.objects.new('SM_Valley_RootWalkShell',collision_mesh);scene.collection.objects.link(collision)
obj.select_set(False);collision.select_set(True);bpy.context.view_layer.objects.active=collision
bpy.ops.export_scene.fbx(filepath=str(OUT/'SM_Valley_RootWalkShell.fbx'),use_selection=True,object_types={'MESH'},axis_forward='-Y',axis_up='Z',apply_unit_scale=True,apply_scale_options='FBX_SCALE_NONE',bake_anim=False,add_leaf_bones=False,mesh_smooth_type='FACE',path_mode='RELATIVE')
collision.hide_render=True;collision.hide_set(True);collision.hide_viewport=True
obj.select_set(True);bpy.context.view_layer.objects.active=obj
print('ROOT',list(obj.dimensions),len(faces))
bpy.context.preferences.filepaths.save_version=0;bpy.ops.file.pack_all()
bpy.ops.wm.save_as_mainfile(filepath=str(OUT/'ValleyRoot.blend'))
