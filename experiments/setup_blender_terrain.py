#!/usr/bin/env python3
"""
Blender setup script for terrain visualization.

Usage in Blender:
1. Open Blender
2. Load your OBJ file (File > Import > Wavefront (.obj))
3. Open Scripting tab
4. Load this script
5. Run it

Or from command line:
blender --python setup_blender_terrain.py
"""

import bpy
import math

def setup_terrain_visualization():
    """Set up lighting, materials, and camera for terrain visualization."""

    # Clear existing lights
    bpy.ops.object.select_all(action='DESELECT')
    bpy.ops.object.select_by_type(type='LIGHT')
    bpy.ops.object.delete()

    # Add Sun light at low angle for dramatic shadows
    bpy.ops.object.light_add(type='SUN', location=(0, 0, 10))
    sun = bpy.context.active_object
    sun.name = "Main_Sun"
    sun.data.energy = 3.0
    sun.rotation_euler = (math.radians(60), 0, math.radians(45))

    # Add fill light from opposite side (softer)
    bpy.ops.object.light_add(type='SUN', location=(0, 0, 10))
    fill = bpy.context.active_object
    fill.name = "Fill_Light"
    fill.data.energy = 1.0
    fill.rotation_euler = (math.radians(120), 0, math.radians(-135))

    # Set up world lighting (ambient)
    bpy.context.scene.world.use_nodes = True
    world_nodes = bpy.context.scene.world.node_tree.nodes
    world_nodes["Background"].inputs[0].default_value = (0.05, 0.05, 0.05, 1)  # Dark gray background
    world_nodes["Background"].inputs[1].default_value = 0.5  # Strength

    # Find the mesh object (assumes it's the largest mesh)
    mesh_obj = None
    max_verts = 0
    for obj in bpy.data.objects:
        if obj.type == 'MESH':
            vert_count = len(obj.data.vertices)
            if vert_count > max_verts:
                max_verts = vert_count
                mesh_obj = obj

    if not mesh_obj:
        print("ERROR: No mesh found in scene!")
        return

    print(f"Setting up material for: {mesh_obj.name}")

    # Create material with elevation-based coloring
    mat = bpy.data.materials.new(name="Terrain_Material")
    mat.use_nodes = True
    nodes = mat.node_tree.nodes
    links = mat.node_tree.links

    # Clear default nodes
    nodes.clear()

    # Add nodes for elevation-based coloring
    node_output = nodes.new(type='ShaderNodeOutputMaterial')
    node_output.location = (400, 0)

    node_bsdf = nodes.new(type='ShaderNodeBsdfPrincipled')
    node_bsdf.location = (0, 0)
    node_bsdf.inputs['Roughness'].default_value = 0.8

    # Add coordinate and separate XYZ to get Z (height)
    node_coord = nodes.new(type='ShaderNodeTexCoord')
    node_coord.location = (-800, 0)

    node_separate = nodes.new(type='ShaderNodeSeparateXYZ')
    node_separate.location = (-600, 0)

    # ColorRamp for elevation coloring
    node_ramp = nodes.new(type='ShaderNodeValToRGB')
    node_ramp.location = (-400, 0)

    # Set up color ramp (low=purple/blue, mid=green, high=yellow/white)
    ramp = node_ramp.color_ramp
    ramp.elements[0].position = 0.0
    ramp.elements[0].color = (0.1, 0.0, 0.3, 1)  # Deep purple (valleys)
    ramp.elements[1].position = 0.3
    ramp.elements[1].color = (0.0, 0.3, 0.7, 1)  # Blue

    # Add more elements
    ramp.elements.new(0.5)
    ramp.elements[2].color = (0.0, 0.7, 0.3, 1)  # Green (mid)

    ramp.elements.new(0.7)
    ramp.elements[3].color = (0.9, 0.7, 0.2, 1)  # Yellow

    ramp.elements.new(1.0)
    ramp.elements[4].color = (1.0, 0.95, 0.9, 1)  # White (peaks)

    # Link nodes
    links.new(node_coord.outputs['Object'], node_separate.inputs['Vector'])
    links.new(node_separate.outputs['Z'], node_ramp.inputs['Fac'])
    links.new(node_ramp.outputs['Color'], node_bsdf.inputs['Base Color'])
    links.new(node_bsdf.outputs['BSDF'], node_output.inputs['Surface'])

    # Assign material to mesh
    if mesh_obj.data.materials:
        mesh_obj.data.materials[0] = mat
    else:
        mesh_obj.data.materials.append(mat)

    # Set up viewport shading
    for area in bpy.context.screen.areas:
        if area.type == 'VIEW_3D':
            for space in area.spaces:
                if space.type == 'VIEW_3D':
                    space.shading.type = 'SOLID'
                    space.shading.light = 'MATCAP'
                    space.shading.studio_light = 'metal_carpaint.exr'
                    space.shading.show_cavity = True
                    space.shading.cavity_type = 'BOTH'
                    space.shading.cavity_ridge_factor = 1.0
                    space.shading.cavity_valley_factor = 1.0

    # Frame the object in view
    bpy.ops.object.select_all(action='DESELECT')
    mesh_obj.select_set(True)
    bpy.context.view_layer.objects.active = mesh_obj

    # Switch to rendered view for final output
    bpy.context.scene.render.engine = 'CYCLES'
    bpy.context.scene.cycles.samples = 128

    print("✓ Terrain visualization setup complete!")
    print("\nTips:")
    print("  - Press Z > Solid to see matcap shading with cavity")
    print("  - Press Z > Rendered to see elevation colors")
    print("  - Numpad 7 for top view, Numpad 1 for front view")
    print("  - Shift+Middle Mouse to pan, scroll to zoom")
    print("  - Select camera and press Ctrl+Alt+Numpad 0 to align camera to view")

if __name__ == "__main__":
    setup_terrain_visualization()
