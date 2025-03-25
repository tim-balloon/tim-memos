import matplotlib.pyplot as plt
import numpy as np
from scipy.spatial.transform import Rotation
import open3d as o3d

rng = np.random.default_rng(seed=77777)

# label position vector u, direction vector v, surface normal n
u_ = np.s_[0:3] # ray tensor position
v_ = np.s_[3:] # ray tensor direction

MESH_RES_FACTOR = 1

# -----------------------------------------------------------------------------
# Helpers
# -----------------------------------------------------------------------------
def get_new_direction(start:o3d.core.Tensor, nhat):
    # https://3dkingdoms.com/weekly/weekly.php?a=2
    vhat = start[v_].numpy()
    vhat_new = -2. * np.dot(vhat, nhat) * nhat + vhat
    return vhat_new / np.linalg.norm(vhat_new)


class RayPath(object):
    # an identified list of ray bounces with some properties
    def __init__(self, id):
        self.id = id
        self.rays = []
        self.n_bounces = 0
        self.last_surface_id = o3d.t.geometry.RaycastingScene.INVALID_ID
        self.last_pos = [np.inf, np.inf, np.inf]
        self.color = [0.5, 0.5, 0.5]
        self.lines = []

    def ray_to_line(self, start:o3d.core.Tensor, end:o3d.core.Tensor):
        l = o3d.t.geometry.LineSet(
            np.vstack([start[u_].numpy(), end[u_].numpy()]),
            np.array([[0,1]])
        )
        self.last_pos = end[u_]
        return l

    def append(self, ray_start, ray_end, surf_hit_id):
        self.rays.append(ray_start)
        line = self.ray_to_line(ray_start, ray_end)
        self.lines.append(line) # TODO: refactor to use LineSet properly
        self.n_bounces += 1
        self.last_surface_id = surf_hit_id

    def get_total_length(self):
        return np.sum(self.lengths)

    def apply_color(self, rgb):
        self.color = rgb
        colored_lines = []
        for line in self.lines:
            ls = o3d.t.geometry.LineSet.to_legacy(line)
            ls.paint_uniform_color(rgb)
            colored_lines.append(o3d.t.geometry.LineSet.from_legacy(ls))
        self.lines = colored_lines


# -----------------------------------------------------------------------------
# Meshes
# -----------------------------------------------------------------------------
print('Creating meshes...')
# all units meters, rad
# primary mirror
f = 1.6
r_in = .45 / 2.
r_out = 1
x = np.linspace(r_in, r_out, num=int(500 * MESH_RES_FACTOR))
y = np.zeros_like(x)
z = x**2 / 4. / f
# add a bottom layer to the mirror
t = 0.075
x = np.concatenate([x, x[::-1]])
y = np.concatenate([y, y])
z = np.concatenate([z, z[::-1] - t])
primary_profile_points = np.vstack([x, y, z]).T
pairs = np.arange(0, len(primary_profile_points)+1)
pairs = [p % len(x) for p in pairs]
primary_profile_pairs = np.array(list(zip(pairs[:-1], pairs[1:])))
mirror_profile = o3d.t.geometry.LineSet(primary_profile_points, primary_profile_pairs)
primary = mirror_profile.extrude_rotation(360., [0, 0, 1], resolution=int(500 * MESH_RES_FACTOR))
# color
primary = o3d.t.geometry.TriangleMesh.to_legacy(primary)
primary.paint_uniform_color([0.5, 0.8, 0.5])
primary = o3d.t.geometry.TriangleMesh.from_legacy(primary)

# secondary mirror
r_sec_in = 80e-3 / 2
r_sec_out = 510e-3 / 2
roc = 937.5e-3
t_sec = 52.55e-3
h_sec_vertex = 1.225
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
secondary = o3d.t.geometry.TriangleMesh.to_legacy(secondary)
secondary.paint_uniform_color([0.7, 0.5, 0.7])
secondary = o3d.t.geometry.TriangleMesh.from_legacy(secondary)

# scoop
min_el = 20 * np.pi / 180.
dh = -1 # shorten the scoop?
h = 2. * r_out / np.arctan(min_el) + dh
scoop_back = 0
scoop_front = h
print(f'scoop len: {h}')
r_scoop = 1.1
scoop = o3d.t.geometry.TriangleMesh.create_cylinder(radius=r_scoop, height=h, resolution=8, split=4)
scoop.translate([0, 0, h/2])
scoop = o3d.t.geometry.TriangleMesh.to_legacy(scoop)
R = scoop.get_rotation_matrix_from_axis_angle([0, 0, (np.pi / 180.) * (360. / 16.)])
scoop.rotate(R)
scoop = o3d.t.geometry.TriangleMesh.from_legacy(scoop)
# clip off the front and back faces of the scoop
scoop = scoop.clip_plane(point=[0,0,scoop_front-1e-6], normal=[0,0,-1])
scoop = scoop.clip_plane(point=[0,0,scoop_back+1e-6], normal=[0,0,1])
# clip off an angled portion of the scoop
scoop_angle = (np.pi / 2.) - min_el
y_proj = np.sin(scoop_angle)
z_proj = np.cos(scoop_angle)
scoop_clip_nhat = [0, y_proj, z_proj]
scoop_clip_nhat /= np.linalg.norm(scoop_clip_nhat)
scoop_clip_nhat *= -1
scoop = scoop.clip_plane(point=[0,-r_scoop,h+1.2-dh], normal=scoop_clip_nhat)
# color
scoop = o3d.t.geometry.TriangleMesh.to_legacy(scoop)
scoop.paint_uniform_color([0.7, 0.7, 0.9])
scoop = o3d.t.geometry.TriangleMesh.from_legacy(scoop)

# a catcher disc: every ray that makes it to this plane is considered naughty, and a no-no
cryostat_window = o3d.t.geometry.TriangleMesh.create_cylinder(radius=r_in, height=0.1, resolution=50, split=1)
cryostat_window.translate([0, 0, -0.3])
# color
cryostat_window = o3d.t.geometry.TriangleMesh.to_legacy(cryostat_window)
cryostat_window.paint_uniform_color([1.0, 0.0, 0.0])
cryostat_window = o3d.t.geometry.TriangleMesh.from_legacy(cryostat_window)

# prepare meshes for rendering and calculation
meshes = [scoop, primary, secondary, cryostat_window]
[m.compute_vertex_normals() for m in meshes]
[m.compute_triangle_normals() for m in meshes]

# convert to legacy to flip some normals
meshes = [o3d.t.geometry.TriangleMesh.to_legacy(m) for m in meshes]
scoop, primary, secondary, cryostat_window = meshes
for i in range(len(scoop.triangles)):
    scoop.triangles[i] = scoop.triangles[i][::-1]
for i in range(len(primary.triangles)):
    primary.triangles[i] = primary.triangles[i][::-1]
# convert back to tensor representation to do ray tracing
meshes = [o3d.t.geometry.TriangleMesh.from_legacy(m) for m in meshes]
scoop, primary, secondary, cryostat_window = meshes

# -----------------------------------------------------------------------------
# Ray tracing
# -----------------------------------------------------------------------------
print('Creating ray bundles...')
scene = o3d.t.geometry.RaycastingScene()
mesh_ids = [scene.add_triangles(m) for m in meshes]
geom_dict = {mesh_ids[i]: m for i, m in enumerate(meshes)}
mesh_ids = [-1] + mesh_ids # support for a numbered surface at inf
mesh_names = ['inf', 'scoop', 'primary', 'secondary', 'cryostat_window']
mesh_id_to_name = {mesh_ids[i]: mesh_name for i, mesh_name in enumerate(mesh_names)}
absorber_meshes = [cryostat_window, ]

# on-axis, sparse
# r_ray = 0.999
# h = 10
# rays = o3d.core.Tensor([
#         [0, 0, h, 0, 0, -1],
#         [0, r_ray, h, 0, 0, -1],
#         [r_ray, 0, h, 0, 0, -1],
#         [0, -r_ray, h, 0, 0, -1],
#         [-r_ray, 0, h, 0, 0, -1],
#     ],
#     dtype=o3d.core.Dtype.Float32
# )
# N_rays = rays.numpy().shape[0]

# on-axis, Gaussian bundle, dense
# N_rays = 500
# rays = o3d.core.Tensor(
#     np.zeros((N_rays, 6)),
#     dtype=o3d.core.Dtype.Float32
# )
# xy_coord = np.random.normal(scale=(.35,.35), loc=(0,0), size=(N_rays, 2))
# rays[:,0] = xy_coord[:,0]
# rays[:,1] = xy_coord[:,1]
# rays[:,2] = h
# rays[:,5] = -1

# off-axis grid
# assumptions:
# - 120 kft alt
# - earth limb angle ~6.5deg down from horizon
# jaguirre did some calcs to come up with ~6m scoop
# earth_limb_angle = np.linspace(-6.5, -10, num=51, endpoint=True) * np.pi / 180.
# ray_z = 10
# ray_ys = ray_z * np.tan(earth_limb_angle)
# ray_xs = np.linspace(-4, 4, num=51, endpoint=True)
# XX, YY = np.meshgrid(ray_xs, ray_ys)
# xflat = XX.flatten()
# yflat = YY.flatten()
# ray_bundle_origin = np.vstack([xflat, yflat, np.ones_like(xflat) * ray_z]).T
# aimpoint = np.array([0, 0, 0])
# vhat = aimpoint - ray_bundle_origin
# vhat /= np.linalg.norm(vhat)
# assert(len(xflat) == len(yflat))
# N_rays = vhat.shape[0]
# rays = o3d.core.Tensor(
#     np.zeros((N_rays, 6)),
#     dtype=o3d.core.Dtype.Float32
# )
# rays[:,0] = xflat
# rays[:,1] = yflat
# rays[:,2] = ray_z
# rays[:,3:] = vhat

# # random direction
# earth_limb_angle = (-20. + np.linspace(0, 6, num=2001, endpoint=True)) * np.pi / 180.
# ray_z = 10
# ray_ys = ray_z * np.tan(earth_limb_angle)
# ray_xs = np.linspace(-4, 4, num=2001, endpoint=True)
# XX, YY = np.meshgrid(ray_xs, ray_ys)
# xflat = XX.flatten()
# yflat = YY.flatten()
# ray_bundle_origin = np.vstack([xflat, yflat, np.ones_like(xflat) * ray_z]).T
# aimpoint = np.array([0, 0, 0])
# rng = np.random.default_rng(seed=77777)
# v = rng.normal(size=(len(xflat), 3))
# vhat = v / np.linalg.norm(v)
# assert(len(xflat) == len(yflat))
# N_rays = vhat.shape[0]
# rays = o3d.core.Tensor(
#     np.zeros((N_rays, 6)),
#     dtype=o3d.core.Dtype.Float32
# )
# rays[:,0] = xflat
# rays[:,1] = yflat
# rays[:,2] = ray_z
# rays[:,3:] = vhat

# focused range of angles
# set up a grid of origin points in relevant angular ranges
# the nominal lowest el is +20, and Earth limb may become important by +6.
# launch rays from a relative angle below the assembly
earth_limb_angle = (-20. + np.linspace(0, .1, num=1, endpoint=True)) * np.pi / 180.
ray_z = 10
ray_ys = ray_z * np.tan(earth_limb_angle)
ray_xs = np.linspace(-10, 10, num=40, endpoint=True)
XX, YY = np.meshgrid(ray_xs, ray_ys)
xflat = XX.flatten()
yflat = YY.flatten()
ray_bundle_origin = np.vstack([xflat, yflat, np.ones_like(xflat) * ray_z]).T
aimpoint = np.array([0, 0, 0]).T
v_aim = aimpoint - ray_bundle_origin
v_aim /= np.atleast_2d(np.linalg.norm(v_aim, axis=1)).T

# fig, ax = plt.subplots(subplot_kw={'projection':'3d'})
# ax.quiver(
#     ray_bundle_origin[:,0],
#     ray_bundle_origin[:,1],
#     ray_bundle_origin[:,2],
#     v_aim[:,0],
#     v_aim[:,1],
#     v_aim[:,2],
# )
# ax.scatter(0,0,0)
# ax.set_aspect('equal')
# ax.set_xlabel('x')
# ax.set_title('Unperturbed ray aimings')
# plt.show()

# shoot a bundle of rays, each rotated by a small amount relative to the main
# aim vector
theta_half_angle = np.pi/4
phi_half_angle = np.pi/4
N_bundle_side = 50
thetas = np.linspace(-theta_half_angle, theta_half_angle, num=N_bundle_side)
phis = np.linspace(-phi_half_angle, phi_half_angle, num=N_bundle_side)
# rays_per_origin = 100
ray_list = []
for i in range(len(xflat)):
    print(f'{(i+1) / len(xflat):.2f}', end='\r')
    # current angle of the aim vector
    theta = np.arctan2(v_aim[i,1], v_aim[i,0])
    phi = np.arccos(v_aim[i,2])
    # thetas = rng.uniform(-theta_half_angle, theta_half_angle, rays_per_origin)
    # phis = rng.uniform(-phi_half_angle, phi_half_angle, rays_per_origin)
    ddtheta, ddphi = np.meshgrid(thetas, phis)
    dtheta = ddtheta.flatten()
    dphi = ddphi.flatten()
    rots = Rotation.from_euler('YXZ', np.vstack([dtheta, dphi, np.zeros_like(dphi)]).T)
    for rot in rots:
        v_aim_new = rot.apply(v_aim[i,:])
        # add the bundle of rays to the total list
        this_ray = [xflat[i], yflat[i], ray_z, v_aim_new[0], v_aim_new[1], v_aim_new[2]]
        ray_list.append(this_ray)

rays = o3d.core.Tensor(
    ray_list,
    dtype=o3d.core.Dtype.Float32
)
N_rays = rays.numpy().shape[0]

# fig, ax = plt.subplots(subplot_kw={'projection':'3d'})
# rnp = rays.numpy()
# ax.quiver(
#     rnp[:,0],
#     rnp[:,1],
#     rnp[:,2],
#     rnp[:,3],
#     rnp[:,4],
#     rnp[:,5],
# )
# ax.scatter(0,0,0)
# ax.set_aspect('equal')
# ax.set_xlabel('x')
# ax.set_title('Ray bundles')
# plt.show()

# store history of each ray
paths = [RayPath(i) for i in range(N_rays)]

# if aluminized mylar/aluminum mirrors have reflection coefficients of
# ~.99, any ray is down to ~.6 by 50 bounces
N_bounces = 50
i_bounce = 0
print('Tracing rays...')
while i_bounce <= N_bounces:
    # cast
    ans = scene.cast_rays(rays)
    # prune rays that terminate at infinity
    hit_mask = np.where(np.isfinite(ans['t_hit'].numpy()))[0]
    print(f'Bounce {i_bounce} finds {len(ans["geometry_ids"].numpy())} hits, {len(hit_mask)} valid, on surfaces {ans["geometry_ids"].numpy()}')
    # compute new ray directions
    new_ray_list = []
    # iterate over all rays that hit a mesh
    for i_hit in hit_mask:
        mesh_id_hit = ans["geometry_ids"].numpy()[i_hit]
        mesh_hit = geom_dict[mesh_id_hit]

        this_ray = rays[i_hit]
        # log progress in ray's path
        dist = ans['t_hit'][i_hit]
        # HACK: FIXME: rays go inside surfaces sometimes.
        # They may propagate inside and come out randomly...should do closest
        # point to mesh or something, perturb back outside along surface normal to fix.
        # this is a close approximation, a few um is pretty good
        ray_fudge = (1 - 1e-5)
        dist *= ray_fudge
        end = this_ray.clone()
        end[u_] = this_ray[u_] + this_ray[v_] * dist
        # ensure ray didn't go inside mesh and bounce around
        # query_point = o3d.core.Tensor([end[u_].numpy()], dtype=o3d.core.Dtype.Float32)
        # close = scene.compute_closest_points(query_point)
        # close_coord = close['points'].numpy()[0] + this_ray[v_].numpy() * -1e-6
        # correction_mag = np.linalg.norm(close_coord - end[u_].numpy())
        # end[u_] = close_coord

        this_path = paths[i_hit]
        this_path.append(this_ray, end, mesh_id_hit)
        # terminate if required
        if mesh_hit in absorber_meshes:
            this_path.color = mesh_hit.vertex.colors[0].numpy()
            continue
        # if correction_mag > 1e-6:
        #     print(f'WARNING: mesh intersection correction larger than 1 um: {correction_mag}, terminating ray')
        #     continue

        # propagate rays to next surface:
        # get mesh triangle surface normal
        nhat = ans['primitive_normals'][i_hit].numpy()
        vhat_new = get_new_direction(this_ray, nhat)
        # advance the ray position
        pos_new = this_ray[u_] + this_ray[v_] * dist
        new_ray = np.concatenate([pos_new.numpy(), vhat_new])
        new_ray_list.append(list(new_ray))

    # create the new ray bundle
    rays = o3d.core.Tensor(new_ray_list, dtype=o3d.core.Dtype.Float32)

    i_bounce += 1

    # Terminate if necessary
    if not new_ray_list:
        print(f'All rays have been terminated after {i_bounce} bounces.')
        break

# -----------------------------------------------------------------------------
# Rendering + statistics
# -----------------------------------------------------------------------------
print('Creating render...')
last_surfaces_hit = []
geom = []
for path in paths:
    # for ez plotting, relabel rays that terminated at infinity
    if path.last_surface_id == o3d.t.geometry.RaycastingScene.INVALID_ID:
        surf_id = -1
    else:
        surf_id = path.last_surface_id
    last_surfaces_hit.append(surf_id)
    # for ezest plotting, only consider rays that entered the forbidden zone
    # if surf_id != mesh_ids[-1]:
    #     continue
    # unwind all paths into lines and paint
    # BUG: FIXME: some line segments are grey. why?
    path.apply_color(path.color)
    linesets = []
    for l in path.lines:
        linesets.append(o3d.t.geometry.LineSet.to_legacy(l))
    geom += linesets

# add in the triad for reference
# coordinate system triad
triad = o3d.geometry.TriangleMesh.create_coordinate_frame(size=.5, origin=[0,0,0])
triad = o3d.t.geometry.TriangleMesh.from_legacy(triad)
triad.compute_vertex_normals()
meshes += [triad,]

# identify surfaces
# TODO: render text near each surface to label them

# convert back to legacy to render
meshes = [o3d.t.geometry.TriangleMesh.to_legacy(m) for m in meshes]
geom += meshes
o3d.visualization.draw_geometries(geom, mesh_show_wireframe=False)

# plot statistics

# fraction of counts per last hit surface
fig, ax = plt.subplots()
surf_ids, counts = np.unique(last_surfaces_hit, return_counts=True)
ax.bar(surf_ids, counts / N_rays)
# ax.set_yscale('log')
ax.set_xticks(surf_ids)
ax.set_xticklabels([mesh_id_to_name[id] for id in surf_ids])
ax.set_title('Ray Fates')
ax.set_xlabel('ID of Last Surface')
ax.set_ylabel('Fraction of Total Casted Rays')
plt.show()

# ray counts per last hit surface
fig, ax = plt.subplots()
ax.bar(surf_ids, counts)
# ax.set_yscale('log')
ax.set_xticks(surf_ids)
ax.set_xticklabels([mesh_id_to_name[id] for id in surf_ids])
ax.set_title('Ray Fates')
ax.set_xlabel('ID of Last Surface')
ax.set_ylabel('Hit Counts')
plt.show()

# # fraction of rays with >1 bounce per last hit surface
# last_surfaces_hit = []
# dangerous_paths = 0 # path has >= 1 bounce and last hit surface is not scoop or secondary
# for path in paths:
#     if path.n_bounces >= 1:
#         dangerous_paths += 1
#         if path.last_surface_id == o3d.t.geometry.RaycastingScene.INVALID_ID:
#             last_surfaces_hit.append(-1)
#         else:
#             last_surfaces_hit.append(path.last_surface_id)
# fig, ax = plt.subplots()
# surf_ids, counts = np.unique(last_surfaces_hit, return_counts=True)
# ax.bar(surf_ids, counts / dangerous_paths)
# ax.set_xticks(surf_ids)
# ax.set_xticklabels([mesh_id_to_name[id] for id in surf_ids])
# ax.set_title('Ray Fates:\nFraction of Rays not Rejected By Scoop')
# ax.set_xlabel('ID of Last Surface')
# ax.set_ylabel('Fraction of Rays')
# plt.show()