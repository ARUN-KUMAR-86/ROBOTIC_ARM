#!/usr/bin/env python3
"""
Procedural STL Mesh Generator for Auron 6-DOF Industrial Robot
Generates clean binary STL meshes for each robot link matching the visual reference:
- Flared metallic/white base pedestal
- Circular gear-like joint housings with turbine/spoke faceplates
- Sleek white arm shells
- Articulated wrist assemblies
- Industrial two-finger gripper
"""

import math
import os
import struct
import numpy as np

def write_stl(filename, triangles):
    """Write triangles (list of 3x3 float tuples/arrays) to a binary STL file."""
    os.makedirs(os.path.dirname(filename), exist_ok=True)
    with open(filename, 'wb') as f:
        # 80-byte header
        header = b'Auron Robotics Procedural STL Mesh'[:80].ljust(80, b'\0')
        f.write(header)
        # Number of triangles
        f.write(struct.pack('<I', len(triangles)))
        for tri in triangles:
            p1, p2, p3 = tri[0], tri[1], tri[2]
            # Compute normal vector
            v1 = np.array(p2) - np.array(p1)
            v2 = np.array(p3) - np.array(p1)
            normal = np.cross(v1, v2)
            norm = np.linalg.norm(normal)
            if norm > 1e-9:
                normal = normal / norm
            else:
                normal = np.array([0.0, 0.0, 1.0])
            # Normal (3 floats), vertices (9 floats), attribute byte count (uint16)
            f.write(struct.pack('<3f9fH',
                                normal[0], normal[1], normal[2],
                                p1[0], p1[1], p1[2],
                                p2[0], p2[1], p2[2],
                                p3[0], p3[1], p3[2],
                                0))
    print(f"Generated {filename} ({len(triangles)} facets)")

def create_cylinder(r1, r2, h, n_segments=36, z_offset=0.0):
    """Create cylinder/cone with top & bottom caps."""
    triangles = []
    angles = [2 * math.pi * i / n_segments for i in range(n_segments)]
    
    # Vertices
    bot_v = [[r1 * math.cos(a), r1 * math.sin(a), z_offset] for a in angles]
    top_v = [[r2 * math.cos(a), r2 * math.sin(a), z_offset + h] for a in angles]
    bot_center = [0.0, 0.0, z_offset]
    top_center = [0.0, 0.0, z_offset + h]
    
    for i in range(n_segments):
        nxt = (i + 1) % n_segments
        # Bottom cap (clockwise when looking from below)
        triangles.append([bot_center, bot_v[nxt], bot_v[i]])
        # Top cap (counter-clockwise when looking from above)
        triangles.append([top_center, top_v[i], top_v[nxt]])
        # Sides
        triangles.append([bot_v[i], bot_v[nxt], top_v[nxt]])
        triangles.append([bot_v[i], top_v[nxt], top_v[i]])
        
    return triangles

def create_torus(r_major, r_minor, n_major=36, n_minor=16, z_offset=0.0):
    """Create torus."""
    triangles = []
    phi = [2 * math.pi * i / n_major for i in range(n_major)]
    theta = [2 * math.pi * j / n_minor for j in range(n_minor)]
    
    grid = []
    for p in phi:
        ring = []
        for t in theta:
            x = (r_major + r_minor * math.cos(t)) * math.cos(p)
            y = (r_major + r_minor * math.cos(t)) * math.sin(p)
            z = r_minor * math.sin(t) + z_offset
            ring.append([x, y, z])
        grid.append(ring)
        
    for i in range(n_major):
        ni = (i + 1) % n_major
        for j in range(n_minor):
            nj = (j + 1) % n_minor
            p00 = grid[i][j]
            p10 = grid[ni][j]
            p01 = grid[i][nj]
            p11 = grid[ni][nj]
            triangles.append([p00, p10, p11])
            triangles.append([p00, p11, p01])
    return triangles

def create_flared_pedestal(r_base=0.18, r_top=0.10, height=0.12, n_rings=16, n_segments=36):
    """Create the signature flared pedestal base from the reference image."""
    triangles = []
    ring_z = [height * (i / n_rings) for i in range(n_rings + 1)]
    # Exponential / smooth flare curve
    ring_r = [r_top + (r_base - r_top) * math.pow(1.0 - (z / height), 2.5) for z in ring_z]
    
    angles = [2 * math.pi * j / n_segments for j in range(n_segments)]
    
    layers = []
    for r, z in zip(ring_r, ring_z):
        layer = [[r * math.cos(a), r * math.sin(a), z] for a in angles]
        layers.append(layer)
        
    # Bottom cap
    bot_center = [0.0, 0.0, 0.0]
    for j in range(n_segments):
        nj = (j + 1) % n_segments
        triangles.append([bot_center, layers[0][nj], layers[0][j]])
        
    # Top cap
    top_center = [0.0, 0.0, height]
    for j in range(n_segments):
        nj = (j + 1) % n_segments
        triangles.append([top_center, layers[-1][j], layers[-1][nj]])
        
    # Sides between rings
    for i in range(n_rings):
        for j in range(n_segments):
            nj = (j + 1) % n_segments
            p00 = layers[i][j]
            p10 = layers[i + 1][j]
            p01 = layers[i][nj]
            p11 = layers[i + 1][nj]
            triangles.append([p00, p01, p11])
            triangles.append([p00, p11, p10])
            
    return triangles

def create_circular_joint_housing(radius=0.11, width=0.10, n_teeth=16, n_segments=48):
    """
    Create the signature circular actuator housing with gear rim, bevel, and outer hub.
    Joint axis along Y.
    """
    triangles = []
    # Cylinder along Y axis: from -width/2 to +width/2
    y_half = width / 2.0
    angles = [2 * math.pi * i / n_segments for i in range(n_segments)]
    
    # Outer profile with gear notches
    profile_r = []
    for i, a in enumerate(angles):
        # Tooth variation
        tooth = 0.006 * math.cos(n_teeth * a)
        profile_r.append(radius + tooth)
        
    # Left face (Y = -y_half)
    # Right face (Y = +y_half)
    left_v = [[r * math.cos(a), -y_half, r * math.sin(a)] for a, r in zip(angles, profile_r)]
    right_v = [[r * math.cos(a), y_half, r * math.sin(a)] for a, r in zip(angles, profile_r)]
    
    # Side cylindrical faces
    for i in range(n_segments):
        ni = (i + 1) % n_segments
        triangles.append([left_v[i], right_v[i], right_v[ni]])
        triangles.append([left_v[i], right_v[ni], left_v[ni]])
        
    # Left face cap (with central hole/recess for turbine faceplate)
    r_inner = radius * 0.70
    left_in = [[r_inner * math.cos(a), -y_half, r_inner * math.sin(a)] for a in angles]
    right_in = [[r_inner * math.cos(a), y_half, r_inner * math.sin(a)] for a in angles]
    left_cen = [0.0, -y_half, 0.0]
    right_cen = [0.0, y_half, 0.0]
    
    for i in range(n_segments):
        ni = (i + 1) % n_segments
        # Outer rim plate
        triangles.append([left_v[i], left_v[ni], left_in[ni]])
        triangles.append([left_v[i], left_in[ni], left_in[i]])
        triangles.append([right_v[i], right_in[ni], right_v[ni]])
        triangles.append([right_v[i], right_in[i], right_in[ni]])
        
    # Center caps
    for i in range(n_segments):
        ni = (i + 1) % n_segments
        triangles.append([left_cen, left_in[i], left_in[ni]])
        triangles.append([right_cen, right_in[ni], right_in[i]])
        
    return triangles

def create_turbine_faceplate(radius=0.075, depth=0.015, n_blades=8, n_segments=32):
    """
    Create the signature cyan turbine / spiral shutter circular plate seen in the reference image.
    Oriented in X-Z plane, extruding slightly in Y.
    """
    triangles = []
    angles = [2 * math.pi * i / n_segments for i in range(n_segments)]
    r_hub = radius * 0.25
    
    # Spiral angled blades
    center = [0.0, depth, 0.0]
    cen_base = [0.0, 0.0, 0.0]
    
    outer_v = [[radius * math.cos(a), 0.0, radius * math.sin(a)] for a in angles]
    inner_v = [[r_hub * math.cos(a), depth * 0.8, r_hub * math.sin(a)] for a in angles]
    
    # Conical hub face
    for i in range(n_segments):
        ni = (i + 1) % n_segments
        triangles.append([cen_base, outer_v[ni], outer_v[i]])
        # Slanted turbine surface
        triangles.append([inner_v[i], outer_v[i], outer_v[ni]])
        triangles.append([inner_v[i], outer_v[ni], inner_v[ni]])
        # Center cone
        triangles.append([center, inner_v[i], inner_v[ni]])
        
    return triangles

def create_arm_tube(r_bot=0.065, r_top=0.055, length=0.38, n_segments=36):
    """Sleek arm tube along Z axis."""
    return create_cylinder(r_bot, r_top, length, n_segments=n_segments, z_offset=0.0)

def create_box(dx, dy, dz, center=(0.0, 0.0, 0.0)):
    """Create axis-aligned box."""
    cx, cy, cz = center
    hx, hy, hz = dx / 2.0, dy / 2.0, dz / 2.0
    v = [
        [cx - hx, cy - hy, cz - hz], # 0
        [cx + hx, cy - hy, cz - hz], # 1
        [cx + hx, cy + hy, cz - hz], # 2
        [cx - hx, cy + hy, cz - hz], # 3
        [cx - hx, cy - hy, cz + hz], # 4
        [cx + hx, cy - hy, cz + hz], # 5
        [cx + hx, cy + hy, cz + hz], # 6
        [cx - hx, cy + hy, cz + hz], # 7
    ]
    # 6 faces * 2 = 12 triangles
    triangles = [
        # Bottom (-Z)
        [v[0], v[2], v[1]], [v[0], v[3], v[2]],
        # Top (+Z)
        [v[4], v[5], v[6]], [v[4], v[6], v[7]],
        # Front (-Y)
        [v[0], v[1], v[5]], [v[0], v[5], v[4]],
        # Back (+Y)
        [v[2], v[3], v[7]], [v[2], v[7], v[6]],
        # Left (-X)
        [v[0], v[4], v[7]], [v[0], v[7], v[3]],
        # Right (+X)
        [v[1], v[2], v[6]], [v[1], v[6], v[5]],
    ]
    return triangles

def create_gripper_jaw():
    """
    Create angular industrial gripper finger jaw matching reference.
    Base mount, angled tapering finger, and high-friction inner grip tooth.
    """
    triangles = []
    # Base block
    triangles += create_box(0.025, 0.02, 0.03, center=(0.0, 0.0, 0.015))
    # Angled finger body
    triangles += create_box(0.018, 0.014, 0.05, center=(0.005, 0.0, 0.05))
    # Grip tooth pad
    triangles += create_box(0.006, 0.012, 0.03, center=(0.014, 0.0, 0.055))
    return triangles

def main():
    base_dir = "/home/arun/auron_robot_ws/src/auron_robot_description/meshes"
    
    # 1. Base meshes
    print("Generating base meshes...")
    base_tris = create_flared_pedestal(r_base=0.18, r_top=0.10, height=0.12)
    write_stl(os.path.join(base_dir, "base", "base_pedestal.stl"), base_tris)
    
    base_ring_tris = create_cylinder(0.185, 0.185, 0.012, n_segments=36, z_offset=0.0)
    write_stl(os.path.join(base_dir, "base", "base_accent_ring.stl"), base_ring_tris)
    
    # Base turret
    turret_tris = create_cylinder(0.095, 0.09, 0.08, n_segments=36, z_offset=0.0)
    write_stl(os.path.join(base_dir, "base", "base_turret.stl"), turret_tris)
    
    # 2. Shoulder meshes
    print("Generating shoulder meshes...")
    sh_housing = create_circular_joint_housing(radius=0.11, width=0.12, n_teeth=16)
    write_stl(os.path.join(base_dir, "shoulder", "shoulder_housing.stl"), sh_housing)
    
    sh_turbine = create_turbine_faceplate(radius=0.075, depth=0.012)
    write_stl(os.path.join(base_dir, "shoulder", "shoulder_turbine.stl"), sh_turbine)
    
    # 3. Upper arm meshes
    print("Generating upper arm meshes...")
    ua_body = create_arm_tube(r_bot=0.065, r_top=0.055, length=0.36)
    write_stl(os.path.join(base_dir, "upper_arm", "upper_arm_body.stl"), ua_body)
    
    ua_collar = create_torus(r_major=0.062, r_minor=0.008, n_major=36, n_minor=12)
    write_stl(os.path.join(base_dir, "upper_arm", "upper_arm_ring.stl"), ua_collar)
    
    # 4. Elbow meshes
    print("Generating elbow meshes...")
    el_housing = create_circular_joint_housing(radius=0.095, width=0.10, n_teeth=14)
    write_stl(os.path.join(base_dir, "elbow", "elbow_housing.stl"), el_housing)
    
    el_turbine = create_turbine_faceplate(radius=0.065, depth=0.010)
    write_stl(os.path.join(base_dir, "elbow", "elbow_turbine.stl"), el_turbine)
    
    # 5. Forearm meshes
    print("Generating forearm meshes...")
    fa_body = create_arm_tube(r_bot=0.052, r_top=0.042, length=0.32)
    write_stl(os.path.join(base_dir, "forearm", "forearm_body.stl"), fa_body)
    
    # 6. Wrist meshes
    print("Generating wrist meshes...")
    w1_tris = create_cylinder(0.045, 0.042, 0.06, n_segments=32, z_offset=0.0)
    write_stl(os.path.join(base_dir, "wrist", "wrist_1.stl"), w1_tris)
    
    w2_tris = create_circular_joint_housing(radius=0.048, width=0.065, n_teeth=10)
    write_stl(os.path.join(base_dir, "wrist", "wrist_2.stl"), w2_tris)
    
    w3_flange = create_cylinder(0.042, 0.042, 0.025, n_segments=32, z_offset=0.0)
    write_stl(os.path.join(base_dir, "wrist", "wrist_3_flange.stl"), w3_flange)
    
    # 7. Gripper meshes
    print("Generating gripper meshes...")
    gp_base = []
    # Main mounting block
    gp_base += create_box(0.08, 0.06, 0.035, center=(0.0, 0.0, 0.0175))
    # Actuator center cylinder
    gp_base += create_cylinder(0.022, 0.022, 0.04, n_segments=24, z_offset=0.01)
    write_stl(os.path.join(base_dir, "gripper", "gripper_base.stl"), gp_base)
    
    finger_tris = create_gripper_jaw()
    write_stl(os.path.join(base_dir, "gripper", "gripper_finger.stl"), finger_tris)
    
    print("All STL meshes successfully generated!")

if __name__ == '__main__':
    main()
