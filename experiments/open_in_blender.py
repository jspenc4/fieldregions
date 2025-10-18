#!/usr/bin/env python3
"""
Open OBJ file in Blender with proper setup.

Usage: python3 open_in_blender.py <obj_file>
"""

import sys
import subprocess
from pathlib import Path

# Blender Python script to run
blender_script = """
import bpy
import sys

# Get the OBJ file path from argv
obj_file = sys.argv[-1]

# Delete default objects
bpy.ops.object.select_all(action='SELECT')
bpy.ops.object.delete()

# Import OBJ (Blender 4.x uses wm.obj_import)
try:
    bpy.ops.wm.obj_import(filepath=obj_file)
except AttributeError:
    # Fallback for older Blender versions
    bpy.ops.import_scene.obj(filepath=obj_file)

# Select imported object
bpy.ops.object.select_all(action='SELECT')

# Frame view
for area in bpy.context.screen.areas:
    if area.type == 'VIEW_3D':
        for region in area.regions:
            if region.type == 'WINDOW':
                override = {'area': area, 'region': region}
                bpy.ops.view3d.view_all(override)
                break

# Set shading to solid
for area in bpy.context.screen.areas:
    if area.type == 'VIEW_3D':
        for space in area.spaces:
            if space.type == 'VIEW_3D':
                space.shading.type = 'SOLID'

print("\\n" + "="*60)
print("Mesh loaded and framed!")
print("="*60)
"""

def main():
    if len(sys.argv) < 2:
        print("Usage: python3 open_in_blender.py <obj_file>")
        sys.exit(1)

    obj_file = Path(sys.argv[1]).absolute()

    if not obj_file.exists():
        print(f"ERROR: File not found: {obj_file}")
        sys.exit(1)

    print(f"Opening {obj_file} in Blender...")

    # Write temp script
    script_path = Path("/tmp/blender_setup.py")
    script_path.write_text(blender_script)

    # Launch Blender with script
    blender_path = "/Applications/Blender.app/Contents/MacOS/Blender"
    subprocess.run([blender_path, "--python", str(script_path), "--", str(obj_file)])

if __name__ == "__main__":
    main()
