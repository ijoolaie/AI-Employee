#!/usr/bin/env python3
"""Generate the project-original low-poly seated employee base GLB.

Uses only Python's standard library. The mesh has no external model, texture,
font, or image dependency; materials are authored here and embedded in the GLB.
"""
from __future__ import annotations

import argparse
import json
import math
import struct
from pathlib import Path

parser = argparse.ArgumentParser(description=__doc__)
parser.add_argument("--output", type=Path, default=Path("frontend/public/assets/world/employee-base.glb"))
OUT = parser.parse_args().output
OUT.parent.mkdir(parents=True, exist_ok=True)

# Material names are intentionally stable: the runtime recolors only "uniform"
# per employee while keeping skin, hair, shirt and accessories intact.
MATERIALS = [
    ("uniform", (0.25, 0.42, 0.60, 1.0)),
    ("skin", (0.84, 0.62, 0.46, 1.0)),
    ("hair", (0.20, 0.16, 0.15, 1.0)),
    ("shirt", (0.95, 0.92, 0.85, 1.0)),
    ("tie", (0.80, 0.52, 0.24, 1.0)),
    ("badge", (0.97, 0.95, 0.87, 1.0)),
    ("pants", (0.16, 0.22, 0.31, 1.0)),
    ("shoes", (0.08, 0.12, 0.17, 1.0)),
    ("eyes", (0.08, 0.10, 0.12, 1.0)),
    ("blush", (0.82, 0.38, 0.34, 1.0)),
]
MAT = {name: i for i, (name, _) in enumerate(MATERIALS)}

# Shared unit cube, 24 vertices (flat normals), 36 indices.
def make_box():
    faces = [
        ((1, 0, 0), [(0.5,-0.5,-0.5),(0.5,-0.5,0.5),(0.5,0.5,0.5),(0.5,0.5,-0.5)]),
        ((-1, 0, 0), [(-0.5,-0.5,0.5),(-0.5,-0.5,-0.5),(-0.5,0.5,-0.5),(-0.5,0.5,0.5)]),
        ((0, 1, 0), [(-0.5,0.5,-0.5),(0.5,0.5,-0.5),(0.5,0.5,0.5),(-0.5,0.5,0.5)]),
        ((0, -1, 0), [(-0.5,-0.5,0.5),(0.5,-0.5,0.5),(0.5,-0.5,-0.5),(-0.5,-0.5,-0.5)]),
        ((0, 0, 1), [(-0.5,-0.5,0.5),(-0.5,0.5,0.5),(0.5,0.5,0.5),(0.5,-0.5,0.5)]),
        ((0, 0, -1), [(0.5,-0.5,-0.5),(0.5,0.5,-0.5),(-0.5,0.5,-0.5),(-0.5,-0.5,-0.5)]),
    ]
    positions, normals, indices = [], [], []
    for normal, verts in faces:
        # The face corner order above is convenient for the coordinate table;
        # reverse it so the triangle winding agrees with the outward flat normal.
        verts = [verts[0], verts[3], verts[2], verts[1]]
        base = len(positions) // 3
        for v in verts:
            positions.extend(v); normals.extend(normal)
        indices.extend([base, base+1, base+2, base, base+2, base+3])
    return positions, normals, indices

def cross(a,b):
    return (a[1]*b[2]-a[2]*b[1], a[2]*b[0]-a[0]*b[2], a[0]*b[1]-a[1]*b[0])
def dot(a,b): return a[0]*b[0]+a[1]*b[1]+a[2]*b[2]
def sub(a,b): return (a[0]-b[0], a[1]-b[1], a[2]-b[2])

def make_sphere(segments=8, rings=6):
    positions, normals = [], []
    for r in range(rings + 1):
        theta = math.pi * r / rings
        for s in range(segments + 1):
            phi = 2 * math.pi * s / segments
            p = (math.sin(theta)*math.cos(phi), math.cos(theta), math.sin(theta)*math.sin(phi))
            positions.extend(p); normals.extend(p)
    indices = []
    stride = segments + 1
    for r in range(rings):
        for s in range(segments):
            a = r*stride+s; b = a+stride; c = a+1; d = b+1
            for tri in ((a,b,c),(b,d,c)):
                pa = tuple(positions[3*tri[0]+k] for k in range(3))
                pb = tuple(positions[3*tri[1]+k] for k in range(3))
                pc = tuple(positions[3*tri[2]+k] for k in range(3))
                n = cross(sub(pb,pa), sub(pc,pa))
                center = tuple((pa[k]+pb[k]+pc[k])/3 for k in range(3))
                indices.extend((tri[0],tri[2],tri[1]) if dot(n,center)<0 else tri)
    return positions, normals, indices

binary = bytearray()
buffer_views, accessors = [], []
def align4():
    while len(binary) % 4: binary.append(0)
def pack_floats(values): return struct.pack('<' + 'f'*len(values), *values)
def pack_indices(values): return struct.pack('<' + 'H'*len(values), *values)
def add_view(data, target):
    align4(); offset=len(binary); binary.extend(data); align4()
    view=len(buffer_views); buffer_views.append({"buffer":0,"byteOffset":offset,"byteLength":len(data),"target":target})
    return view
def add_accessor(view, component, count, typ, minv=None, maxv=None):
    a={"bufferView":view,"componentType":component,"count":count,"type":typ}
    if minv is not None: a["min"]=minv
    if maxv is not None: a["max"]=maxv
    accessors.append(a); return len(accessors)-1

def add_geometry(geometry):
    positions,normals,indices=geometry
    pmin=[min(positions[i::3]) for i in range(3)]
    pmax=[max(positions[i::3]) for i in range(3)]
    pv=add_view(pack_floats(positions),34962)
    nv=add_view(pack_floats(normals),34962)
    iv=add_view(pack_indices(indices),34963)
    pa=add_accessor(pv,5126,len(positions)//3,"VEC3",pmin,pmax)
    na=add_accessor(nv,5126,len(normals)//3,"VEC3")
    ia=add_accessor(iv,5123,len(indices),"SCALAR",[min(indices)],[max(indices)])
    return {"POSITION":pa,"NORMAL":na},ia

box_attrs, box_indices = add_geometry(make_box())
sphere_attrs, sphere_indices = add_geometry(make_sphere())
materials=[]
for name,color in MATERIALS:
    materials.append({"name":name,"pbrMetallicRoughness":{"baseColorFactor":list(color),"metallicFactor":0.0,"roughnessFactor":0.82},"doubleSided":False})
meshes=[]; mesh_lookup={}
for shape, attrs, indices_accessor in [('box',box_attrs,box_indices),('sphere',sphere_attrs,sphere_indices)]:
    for name,_ in MATERIALS:
        mesh_lookup[(shape,name)]=len(meshes)
        meshes.append({"name":f"{shape}-{name}","primitives":[{"attributes":attrs,"indices":indices_accessor,"material":MAT[name],"mode":4}]})

nodes=[]
def node(name,shape,material,translation,scale,rotation=None):
    n={"name":name,"mesh":mesh_lookup[(shape,material)],"translation":list(translation),"scale":list(scale)}
    if rotation is not None: n["rotation"]=list(rotation)
    nodes.append(n)
def quat_z(angle): return [0,0,math.sin(angle/2),math.cos(angle/2)]

# Seated body, feet forward (+Z), with a warm face and simple, readable workwear.
node("Jacket torso","sphere","uniform",(0,1.02,0.00),(0.34,0.39,0.19))
node("Left shoulder","sphere","uniform",(-0.25,1.25,0.00),(0.21,0.18,0.17))
node("Right shoulder","sphere","uniform",(0.25,1.25,0.00),(0.21,0.18,0.17))
node("Neck","sphere","skin",(0,1.40,0.015),(0.09,0.12,0.085))
node("Head","sphere","skin",(0,1.68,0.00),(0.235,0.275,0.205))
node("Left ear","sphere","skin",(-0.228,1.66,0),(0.045,0.065,0.035))
node("Right ear","sphere","skin",(0.228,1.66,0),(0.045,0.065,0.035))
node("Hair cap","sphere","hair",(0,1.875,-0.035),(0.245,0.12,0.21))
node("Hair fringe","sphere","hair",(0,1.80,0.145),(0.20,0.065,0.065))
node("Left sideburn","sphere","hair",(-0.205,1.73,0.015),(0.055,0.13,0.055))
node("Right sideburn","sphere","hair",(0.205,1.73,0.015),(0.055,0.13,0.055))
for side,label in [(-1,"Left"),(1,"Right")]:
    node(label+" eye","sphere","eyes",(side*0.087,1.695,0.188),(0.027,0.034,0.018))
    node(label+" brow","box","hair",(side*0.087,1.755,0.184),(0.075,0.018,0.02),quat_z(-0.05*side))
    node(label+" cheek","sphere","blush",(side*0.15,1.61,0.166),(0.045,0.027,0.018))
node("Nose","sphere","skin",(0,1.635,0.205),(0.032,0.046,0.032))
node("Mouth","box","eyes",(0,1.555,0.196),(0.072,0.012,0.016))
node("Left collar","box","shirt",(-0.065,1.335,0.155),(0.105,0.10,0.035),quat_z(-0.15))
node("Right collar","box","shirt",(0.065,1.335,0.155),(0.105,0.10,0.035),quat_z(0.15))
node("Tie","box","tie",(0,1.17,0.176),(0.045,0.22,0.025))
node("Lanyard","box","tie",(0,1.30,0.17),(0.018,0.10,0.02))
node("Employee badge","box","badge",(0.205,1.08,0.165),(0.095,0.12,0.025))
node("Badge mark","box","tie",(0.205,1.09,0.181),(0.055,0.018,0.008))
node("Belt","box","shoes",(0,0.75,0.00),(0.31,0.065,0.19))
for side,label in [(-1,"Left"),(1,"Right")]:
    node(label+" upper arm","box","uniform",(side*0.355,1.15,0.005),(0.14,0.33,0.14),quat_z(side*0.16))
    node(label+" forearm","box","skin",(side*0.36,0.91,0.16),(0.105,0.27,0.105),quat_z(side*0.08))
    node(label+" hand","sphere","skin",(side*0.36,0.765,0.25),(0.07,0.06,0.075))
    node(label+" trouser leg","box","pants",(side*0.135,0.46,0.02),(0.135,0.39,0.15),quat_z(-side*0.04))
    node(label+" shoe","box","shoes",(side*0.135,0.19,0.105),(0.17,0.11,0.24))

gltf={
  "asset":{"version":"2.0","generator":"AI-Employee original World employee asset generator","extras":{"provenance":"Original low-poly character geometry generated from scripts/world_assets/generate_employee_base_glb.py; no third-party model, texture, image or font source."}},
  "scene":0,"scenes":[{"name":"World Employee","nodes":list(range(len(nodes)))}],
  "nodes":nodes,"meshes":meshes,"materials":materials,
  "buffers":[{"byteLength":len(binary)}],"bufferViews":buffer_views,"accessors":accessors
}
def js_numbers(value):
    if isinstance(value, float) and value.is_integer():
        return int(value)
    if isinstance(value, list):
        return [js_numbers(v) for v in value]
    if isinstance(value, dict):
        return {k: js_numbers(v) for k, v in value.items()}
    return value
json_chunk=json.dumps(js_numbers(gltf),separators=(',',':'),ensure_ascii=False).encode('utf-8')
while len(json_chunk)%4: json_chunk+=b' '
while len(binary)%4: binary.append(0)
total=12+8+len(json_chunk)+8+len(binary)
with OUT.open('wb') as f:
    f.write(struct.pack('<4sII',b'glTF',2,total))
    f.write(struct.pack('<I4s',len(json_chunk),b'JSON')); f.write(json_chunk)
    f.write(struct.pack('<I4s',len(binary),b'BIN\x00')); f.write(binary)
print(f'generated={OUT} bytes={OUT.stat().st_size} nodes={len(nodes)} meshes={len(meshes)} materials={len(materials)}')
