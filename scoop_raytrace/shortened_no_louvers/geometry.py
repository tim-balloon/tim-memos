import numpy as np

import open3d as o3d


# sometimes useful to downsample primary/secondary meshes for faster debugging
MESH_RES_FACTOR = 1

# primary
f = 1.6
r_in = .45 / 2.
r_out = 1
# secondary
r_sec_in = 80e-3 / 2
r_sec_out = 510e-3 / 2
roc = 937.5e-3
t_sec = 52.55e-3
h_sec_vertex = 1.225
# scoop main body
min_el = 20. * np.pi / 180.
dh = -1.5 # shorten the scoop?
h = 2. * r_out / np.arctan(min_el) + dh
scoop_back = 0
scoop_front = h
r_scoop = 1.1 # octagon circumradius
# scoop roof louvers
corrugation_angle = 27.6 * np.pi / 180. # scoop exclusion angle
corrugation_height = (3. / 12.) * .3048 # radial space taken up by louvers
corrugation_thickness = (.5 / 12.) * .3048 # assume 0.5" thick foamular board

# -----------------------------------------------------------------------------
# Meshes
# -----------------------------------------------------------------------------
def get_geometry():
    # all units meters, rad
    # primary mirror
    x = np.linspace(r_in, r_out, num=int(500 * MESH_RES_FACTOR))
    y = np.zeros_like(x)
    z = x**2 / 4. / f
    # add a bottom layer to the mirror
    t = 0.075
    x = np.concatenate([x, x[::-1]])
    y = np.concatenate([y, y])
    z = np.concatenate([z, z[::-1] - t])
    primary_profile_points = np.vstack([x, y, z]).T
    pairs = np.arange(0, len(primary_profile_points)+1)[::-1] # for proper normals
    pairs = [p % len(x) for p in pairs]
    primary_profile_pairs = np.array(list(zip(pairs[:-1], pairs[1:])))
    mirror_profile = o3d.t.geometry.LineSet(primary_profile_points, primary_profile_pairs)
    primary = mirror_profile.extrude_rotation(360., [0, 0, 1], resolution=int(500 * MESH_RES_FACTOR))
    # color
    primary.compute_vertex_normals()
    primary.compute_triangle_normals()
    primary = o3d.t.geometry.TriangleMesh.to_legacy(primary)
    primary.paint_uniform_color([0.5, 0.8, 0.5])
    primary.orient_triangles()
    primary = o3d.t.geometry.TriangleMesh.from_legacy(primary)

    # secondary mirror
    x_sec = np.linspace(r_sec_in, r_sec_out, num=int(500 * MESH_RES_FACTOR))
    y_sec = np.zeros_like(x_sec)
    z_sec = (x_sec ** 2) / (roc + np.sqrt(roc ** 2 + 1.263498 * x_sec ** 2)) # spec'd in sec CAD
    x_sec = np.concatenate([x_sec, x_sec[::-1]])
    y_sec = np.concatenate([y_sec, y_sec])
    z_sec = np.concatenate([z_sec, np.ones_like(z_sec) * z_sec.min() + t_sec])
    secondary_profile_points = np.vstack([x_sec, y_sec, z_sec]).T
    pairs = np.arange(0, len(secondary_profile_points)+1)
    pairs = [p % len(x) for p in pairs]
    secondary_profile_pairs = np.array(list(zip(pairs[:-1], pairs[1:])))
    sec_mirror_profile = o3d.t.geometry.LineSet(secondary_profile_points, secondary_profile_pairs)
    secondary = sec_mirror_profile.extrude_rotation(360., [0, 0, 1], resolution=int(500 * MESH_RES_FACTOR))
    secondary.translate([0, 0, h_sec_vertex])
    # color
    secondary.compute_vertex_normals()
    secondary.compute_triangle_normals()
    secondary = o3d.t.geometry.TriangleMesh.to_legacy(secondary)
    secondary.paint_uniform_color([0.3, 0.3, 0.8])
    secondary.orient_triangles()
    secondary = o3d.t.geometry.TriangleMesh.from_legacy(secondary)

    # scoop
    # let the scoop be a thin shell, to remain manifold
    print(f'scoop len: {h}')

    # some useful octagon properties
    # https://mathworld.wolfram.com/RegularOctagon.html
    scoop_thickness = (1. / 12.) * .3048
    a_scoop = 2. * r_scoop / np.sqrt(4. + 2. * np.sqrt(2.)) # octagon side length
    inradius = 0.5 * (1. + np.sqrt(2.)) * a_scoop # octagon normal height
    side_halfangle = np.arctan(a_scoop / (2. * inradius))
    midpoint_x = inradius * np.cos(2. * side_halfangle)
    midpoint_y = inradius * np.sin(2. * side_halfangle)
    vertex_y = r_scoop * np.sin(side_halfangle)

    scoop_inside = o3d.t.geometry.TriangleMesh.create_cylinder(radius=r_scoop, height=h+1e-3, resolution=8, split=1)
    scoop_outside = o3d.t.geometry.TriangleMesh.create_cylinder(radius=r_scoop+scoop_thickness, height=h, resolution=8, split=1)
    scoop = scoop_outside.boolean_difference(scoop_inside)
    scoop.translate([0, 0, h/2])
    scoop = o3d.t.geometry.TriangleMesh.to_legacy(scoop)
    R = scoop.get_rotation_matrix_from_axis_angle([0, 0, (np.pi / 180.) * (360. / 16.)])
    scoop.rotate(R)
    scoop = o3d.t.geometry.TriangleMesh.from_legacy(scoop)
    # rear shield, for sim purposes only
    # rear_shield = scoop.clone()
    # rear_shield = rear_shield.clip_plane(point=[0,0,scoop_front-1e-6], normal=[0,0,-1])
    # rear_shield = rear_shield.clip_plane(point=[0,0,scoop_front/2], normal=[0,0,1])
    h_shield = h / 4
    rear_shield_inside = o3d.t.geometry.TriangleMesh.create_cylinder(radius=r_scoop, height=h_shield+1e-3, resolution=8, split=1)
    rear_shield_outside = o3d.t.geometry.TriangleMesh.create_cylinder(radius=r_scoop+scoop_thickness, height=h_shield, resolution=8, split=1)
    rear_shield = rear_shield_outside.boolean_difference(rear_shield_inside)
    rear_shield.translate([0, 0, -h_shield/2 + .18])
    rear_shield.compute_vertex_normals()
    rear_shield.compute_triangle_normals()
    rear_shield = o3d.t.geometry.TriangleMesh.to_legacy(rear_shield)
    rear_shield.rotate(R)
    rear_shield.paint_uniform_color([0.3, 0.3, 0.3])
    rear_shield.orient_triangles()
    rear_shield = o3d.t.geometry.TriangleMesh.from_legacy(rear_shield)

    # clip off the front and back faces of the scoop
    # clip off an angled portion of the scoop
    scoop_angle = (np.pi / 2.) - min_el
    y_proj = np.sin(scoop_angle)
    z_proj = np.cos(scoop_angle)
    scoop_clip_nhat = [0, y_proj, z_proj]
    scoop_clip_nhat /= np.linalg.norm(scoop_clip_nhat)
    scoop_clip_nhat *= -1
    scoop = scoop.clip_plane(point=[0,-r_scoop,h+1.2-dh], normal=scoop_clip_nhat)
    # clip off the top to prepare for louvers
    # scoop = scoop.clip_plane(point=[0, vertex_y, 0], normal=[0, -1, 0])

    # color
    scoop.compute_vertex_normals()
    scoop.compute_triangle_normals()
    scoop = o3d.t.geometry.TriangleMesh.to_legacy(scoop)
    scoop.paint_uniform_color([0.7, 0.7, 0.9])
    scoop.orient_triangles()
    scoop = o3d.t.geometry.TriangleMesh.from_legacy(scoop)

    # create louvers for top panels
    # corrugation unit cell: bladed rectangular prism
    #  ___________
    # |__________/
    #
    corrugation_base = corrugation_height / np.tan(corrugation_angle)
    louver_length = h_sec_vertex # along boresight
    corrugation_width = a_scoop * 1.2
    N_vanes = np.round(louver_length / (corrugation_base)).astype(int)
    # proto-louver
    corrugation_l = np.sqrt(corrugation_height**2 + corrugation_base**2)
    pts = np.array([
        [0, 0, 0],
        [0, 0, corrugation_l],
        [0, corrugation_thickness, corrugation_l + 2. * corrugation_thickness],
        [0, corrugation_thickness, corrugation_l],
        [0, corrugation_thickness, 0],
    ])
    pairs = np.array([[0,4], [4,3], [3,2], [2,1], [1,0]]) # order dictates normals
    louver_lineset = o3d.t.geometry.LineSet(pts, pairs)
    louver = louver_lineset.extrude_linear([1, 0, 0], corrugation_width) # fudge some extra length to cover corners on top
    louver.compute_vertex_normals()
    louver.compute_triangle_normals()
    louver = o3d.t.geometry.TriangleMesh.to_legacy(louver)
    R = louver.get_rotation_matrix_from_axis_angle([-corrugation_angle, 0, 0])
    louver.rotate(R)
    louver.paint_uniform_color([0.9, 0.3, 0.9])
    louver.orient_triangles()
    louver = o3d.t.geometry.TriangleMesh.from_legacy(louver)

    # positioning
    louvers = []

    louver_top = louver.clone()
    louver_top.translate([-corrugation_width/2, inradius, .15])
    louver_top = o3d.t.geometry.TriangleMesh.to_legacy(louver_top)
    R = louver_top.get_rotation_matrix_from_axis_angle([0, 0, np.pi])
    louver_top.rotate(R)
    louver_top = o3d.t.geometry.TriangleMesh.from_legacy(louver_top)

    louver_port = louver.clone()
    louver_port.translate([-corrugation_width/2 + midpoint_x, midpoint_y, .15])
    louver_port = o3d.t.geometry.TriangleMesh.to_legacy(louver_port)
    R = louver_port.get_rotation_matrix_from_axis_angle([0, 0, np.pi - (np.pi / 180.) * (360. / 8.)])
    louver_port.rotate(R)
    louver_port = o3d.t.geometry.TriangleMesh.from_legacy(louver_port)

    louver_star = louver.clone()
    louver_star.translate([-corrugation_width/2 - midpoint_x, midpoint_y, .15])
    louver_star = o3d.t.geometry.TriangleMesh.to_legacy(louver_star)
    R = louver_star.get_rotation_matrix_from_axis_angle([0, 0, np.pi + (np.pi / 180.) * (360. / 8.)])
    louver_star.rotate(R)
    louver_star = o3d.t.geometry.TriangleMesh.from_legacy(louver_star)

    for i in range(N_vanes):
        for lv in [louver_top, louver_port, louver_star]:
            louver_new = lv.clone()
            louver_new.translate([0, 0, i * corrugation_base])
            louvers.append(louver_new)

    # create a central baffle
    # h_snoot = .18
    # snoot = o3d.t.geometry.TriangleMesh.create_cylinder(radius=r_in, height=h_snoot, resolution=50, split=1)
    # snoot.translate([0, 0, h_snoot/2])
    # snoot_front = h_snoot
    # snoot_back = 0
    # snoot = snoot.clip_plane(point=[0,0,snoot_front-1e-6], normal=[0,0,-1])
    # snoot = snoot.clip_plane(point=[0,0,snoot_back+1e-6], normal=[0,0,1])
    # # color
    # snoot = o3d.t.geometry.TriangleMesh.to_legacy(snoot)
    # snoot.paint_uniform_color([0.8, 0.7, 0.3])
    # snoot = o3d.t.geometry.TriangleMesh.from_legacy(snoot)

    # a catcher disc: every ray that makes it to this plane is considered naughty, and a no-no
    cryostat_window = o3d.t.geometry.TriangleMesh.create_cylinder(radius=r_in, height=0.05, resolution=50, split=1)
    cryostat_window.translate([0, 0, -0.3])
    # color
    cryostat_window = o3d.t.geometry.TriangleMesh.to_legacy(cryostat_window)
    cryostat_window.paint_uniform_color([0.9, 0.0, 0.0])
    cryostat_window = o3d.t.geometry.TriangleMesh.from_legacy(cryostat_window)

    # prepare meshes for rendering and calculation
    meshes = [scoop, rear_shield, primary, secondary, cryostat_window]# + louvers
    [m.compute_vertex_normals() for m in meshes]
    [m.compute_triangle_normals() for m in meshes]

    absorber_meshes = [cryostat_window, primary, rear_shield]

    print('Computing convex hull for incoming rad membership...')
    system_hull = scoop.compute_convex_hull().boolean_union(primary.compute_convex_hull())
    system_hull = system_hull.compute_convex_hull()
    system_hull = o3d.t.geometry.TriangleMesh.from_legacy(
        system_hull.to_legacy(),
        vertex_dtype=o3d.core.float32,
        triangle_dtype=o3d.core.int32
    )

    mesh_names = [
        'inf',
        'scoop',
        'rear_shield',
        'primary',
        'secondary',
        'cryostat_window'
    ]# + [f'louvers{i}' for i in range(len(louvers))]

    # for i, mesh in enumerate(meshes):
        # print('vmanifold?', mesh_names[i], o3d.t.geometry.TriangleMesh.to_legacy(mesh).is_self_intersecting())
    # for i, mesh in enumerate(meshes):
        # print('emanifold?', mesh_names[i], o3d.t.geometry.TriangleMesh.to_legacy(mesh).is_edge_manifold())
    # for i, mesh in enumerate(meshes):
    #     print('orientable?', mesh_names[i], o3d.t.geometry.TriangleMesh.to_legacy(mesh).is_orientable())
    # for i, mesh in enumerate(meshes):
    #     print('watertight?', mesh_names[i], o3d.t.geometry.TriangleMesh.to_legacy(mesh).is_watertight())
    # for i, mesh in enumerate(meshes):
    #     print('self-intersecting?', mesh_names[i], o3d.t.geometry.TriangleMesh.to_legacy(mesh).is_self_intersecting())

    return meshes, mesh_names, absorber_meshes, system_hull