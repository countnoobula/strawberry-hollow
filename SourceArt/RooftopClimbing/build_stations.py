"""Build both rooftop stations in centimetres. X points into the backing panel."""
import bpy, math, random
from mathutils import Vector
from pathlib import Path

out = Path(__file__).resolve().parent
bpy.ops.wm.read_factory_settings(use_empty=True)
import runpy
route = runpy.run_path(str(out/'wall_route.py'))['WALL_ROUTE']
scene = bpy.context.scene
scene.unit_settings.system = 'METRIC'
scene.unit_settings.scale_length = .01
palette = {}
for name, rgb in {'Basalt': (.105,.18,.25), 'Petrol': (.15,.31,.37), 'Ink': (.035,.075,.10),
                  'Coral': (.98,.23,.13), 'Ochre': (.98,.59,.14), 'Mint': (.20,.77,.66),
                  'Flax': (.82,.59,.31), 'Binding': (.21,.39,.37), 'Steel': (.55,.65,.65)}.items():
    mat = bpy.data.materials.new(name)
    mat.diffuse_color = (*rgb,1)
    palette[name] = mat

def finish(name, mat):
    obj = bpy.context.object
    obj.name = name
    obj.data.materials.append(palette[mat])
    return obj

def box(name, pos, size, mat, radius):
    bpy.ops.mesh.primitive_cube_add(size=1, location=pos)
    obj = finish(name, mat)
    obj.dimensions = size
    bpy.ops.object.transform_apply(location=False, rotation=False, scale=True)
    bevel = obj.modifiers.new('Rounded edges','BEVEL')
    bevel.width, bevel.segments = radius, 3
    obj.modifiers.new('Face normals','WEIGHTED_NORMAL')
    return obj

def sphere(name, pos, size, mat, seed=0):
    bpy.ops.mesh.primitive_ico_sphere_add(subdivisions=2, radius=1, location=pos)
    obj = finish(name,mat)
    rng=random.Random(seed)
    for v in obj.data.vertices:
        v.co *= rng.uniform(.87,1.08)
    obj.scale=size
    obj.rotation_euler.x=rng.uniform(-.40,.40)
    return obj

def rod(name, a, b, radius, mat):
    p,q=Vector(a),Vector(b)
    bpy.ops.mesh.primitive_cylinder_add(vertices=12, radius=radius, depth=(q-p).length, location=(p+q)/2)
    obj=finish(name,mat)
    obj.rotation_euler=(q-p).to_track_quat('Z','Y').to_euler()
    for poly in obj.data.polygons:
        poly.use_smooth=len(poly.vertices)==4

def rope(name,a,b):
    start,end=Vector(a),Vector(b)
    axis=(end-start).normalized()
    normal=Vector((1,0,0))
    tangent=axis.cross(normal)
    length=(end-start).length
    for ply in range(3):
        curve=bpy.data.curves.new(name,'CURVE');curve.dimensions='3D'
        curve.bevel_depth=.95;curve.bevel_resolution=1;curve.resolution_u=1
        spline=curve.splines.new('POLY');steps=math.ceil(length/.9);spline.points.add(steps)
        for n,point in enumerate(spline.points):
            t=n/steps;angle=2*math.pi*(ply/3+t*length/7)
            center=start+axis*(t*length)+.85*(math.cos(angle)*normal+math.sin(angle)*tangent)
            point.co=(*center,1)
        strand=bpy.data.objects.new(name,curve);collection.objects.link(strand)
        strand.data.materials.append(palette['Flax' if ply!=2 else 'Ochre'])
        bpy.context.view_layer.objects.active=strand;strand.select_set(True)
        bpy.ops.object.convert(target='MESH');strand.select_set(False)

for net in (False,True):
    name='SM_RooftopNet' if net else 'SM_RooftopHolds'
    collection=bpy.data.collections.new(name)
    scene.collection.children.link(collection)
    bpy.context.view_layer.active_layer_collection=bpy.context.view_layer.layer_collection.children[name]
    half=60 if net else 140
    height=276
    box('Perimeter chassis',(7,0,height/2),(12,2*half+20,height),'Ink',3)
    count=2 if net else 4
    for i in range(count):
        width=(2*half+12)/count
        box('Modular panel',(2,-half-6+width*(i+.5),height/2),(4,width-.9,height-6),
            ('Petrol' if net else ['Petrol','Basalt'][i%2]),1)
    for sign in (-1,1):
        box('Edge flash',(-.4,sign*(half+7),height/2),(3,2,height-12),'Ochre' if net else 'Mint',.8)
    if net:
        for z in (7,265):
            for y in (-52,52):
                rod('Wall standoff',(1,y,z),(-18,y,z),3.2,'Steel')
            rope('Perimeter rope',(-18,-50,z),(-18,50,z))
        for y in range(-50,51,20):
            rope('Laid vertical rope',(-18,y,7),(-18,y,265))
        for row in range(16):
            z=16+16*row
            rope('Laid foot rope',(-19,-50,z),(-19,50,z))
            for y in range(-50,51,20):
                sphere('Square lashing',(-19,y,z),(2.3,2.6,2.4),'Binding',row)
    else:
        for row, band in enumerate(route):
            for col,(lateral,z) in enumerate(band):
                y=-lateral
                rng=random.Random(row*121+col)
                color=['Ochre','Coral','Mint'][(col+row//2)%3]
                grip=sphere('Route grip %02d-%02d'%(row,col),(-2,y,z),
                    (rng.uniform(4.6,5.7),rng.uniform(5.0,8.4),rng.uniform(3,5.4)),color,row*121+col)
                grip.rotation_euler.x=rng.uniform(-.88,.88)
                sphere('Recessed fixing',(-6.8,y,z),(.55,.85,.85),'Ink',1)
        for i,(y,z) in enumerate(runpy.run_path(str(out/'wall_route.py'))['TOE_CHIPS']):
            sphere('Foot chip',(-1.8,-y,z),(3.7,4.4,2.3),'Basalt' if i%3 else 'Mint',i)
    bpy.ops.object.select_all(action='DESELECT')
    for obj in collection.objects: obj.select_set(True)
    bpy.ops.export_scene.fbx(filepath=str(out/(name+'.fbx')), use_selection=True, axis_forward='-Y',axis_up='Z',
        apply_unit_scale=True,bake_anim=False,add_leaf_bones=False)
    if net:
        for obj in collection.objects: obj.location.y+=250
bpy.ops.wm.save_as_mainfile(filepath=str(out/'RooftopClimbing.blend'))

