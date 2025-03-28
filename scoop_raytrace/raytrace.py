import matplotlib.pyplot as plt
import numpy as np

import open3d as o3d

import geometry
import ray_sets

rng = np.random.default_rng(seed=77777)

# label position vector u, direction vector v, surface normal n
u_ = np.s_[0:3] # ray tensor position
v_ = np.s_[3:] # ray tensor direction

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
        self.surfaces_hit = []
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
        self.surfaces_hit.append(surf_hit_id)

    def apply_color(self, rgb):
        self.color = rgb
        colored_lines = []
        for line in self.lines:
            ls = o3d.t.geometry.LineSet.to_legacy(line)
            ls.paint_uniform_color(rgb)
            colored_lines.append(o3d.t.geometry.LineSet.from_legacy(ls))
        self.lines = colored_lines


print('Creating meshes...')
meshes, mesh_names, absorber_meshes = geometry.get_geometry()

print('Creating ray bundles...')
# rays, N_rays = ray_sets.angular_sector()
rays, N_rays = ray_sets.simple_fan([1 - 1e-1, .51 + 1e-1])
# rays, N_rays = ray_sets.random_disc(1, 100, [0, 0, 10], [0, 0, -1])

print('Creating scene...')
scene = o3d.t.geometry.RaycastingScene()
mesh_ids = [scene.add_triangles(m) for m in meshes]
geom_dict = {mesh_ids[i]: m for i, m in enumerate(meshes)}
mesh_ids = [o3d.t.geometry.RaycastingScene.INVALID_ID] + mesh_ids
mesh_id_to_name = {mesh_ids[i]: mesh_name for i, mesh_name in enumerate(mesh_names)}

# store history of each ray
paths = [RayPath(i) for i in range(N_rays)]
for i, ray in enumerate(rays):
    paths[i].append(ray, ray, o3d.t.geometry.RaycastingScene.INVALID_ID)

# if aluminized mylar/aluminum mirrors have reflection coefficients of
# ~.99, any ray is down to ~.6 by 50 bounces
N_bounces = 50
i_bounce = 0
print('Tracing rays...')
while i_bounce <= N_bounces:
    # cast
    ans = scene.cast_rays(rays)
    print(scene.list_intersections(rays))
    # prune rays that terminate at infinity
    hit_mask = np.where(np.isfinite(ans['t_hit'].numpy()))[0]
    print(
        f'Bounce {i_bounce} finds {len(hit_mask)} hits\n' +
        f'on surfaces {[mesh_id_to_name[ide] for ide in ans["geometry_ids"].numpy()]}'
    )
    # compute new ray directions
    new_ray_list = []

    # if i_bounce == 0:
    #     plt.plot(ans['t_hit'].numpy())
    #     plt.show()

    # iterate over all rays that hit a mesh
    for i_hit in hit_mask:
        mesh_id_hit = ans["geometry_ids"].numpy()[i_hit]
        mesh_hit = geom_dict[mesh_id_hit]
        this_ray = rays[i_hit]
        # make double-sure units of distance are 1m
        this_ray[v_] = this_ray[v_] / np.linalg.norm(this_ray[v_].numpy())
        dist = ans['t_hit'][i_hit]
        end = this_ray.clone()
        end[u_] = this_ray[u_] + this_ray[v_] * (dist - 1e-6)
        # check to see ray does not end up inside a mesh
        query_point = o3d.core.Tensor([end[u_].numpy()], dtype=o3d.core.Dtype.Float32)
        signed_dist = scene.compute_signed_distance(query_point).numpy()[0]
        if signed_dist < 0:
            print(ans['primitive_uvs'][i_hit])
            continue
        adjust_step = 1e-6
        maxtries = 5e4
        while (signed_dist < 0) and (maxtries > 0):
            maxtries -= 1
            print(
                f'WARNING: ray {str(this_ray)} found at point ' +
                f'{end[u_].numpy()}, a distance {signed_dist} inside mesh ' +
                f'{mesh_id_to_name[mesh_id_hit]}!\nAdjusting ' +
                f'position by {adjust_step} along ray.'
            )
            # adjust position backward along ray
            dist -= adjust_step
            end[u_] = this_ray[u_] + this_ray[v_] * dist
            new_query_point = o3d.core.Tensor([end[u_].numpy()], dtype=o3d.core.Dtype.Float32)
            signed_dist = scene.compute_signed_distance(new_query_point).numpy()[0]
        if maxtries < 1:
            print('|||||||WARNING: failed to adjust ray outside of mesh. Eating ray.')
            continue

        this_path = paths[i_hit]
        this_path.append(this_ray, end, mesh_id_hit)
        # terminate if required
        if mesh_hit in absorber_meshes:
            this_path.color = mesh_hit.vertex.colors[0].numpy()
            continue
        
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
    surf_id = path.surfaces_hit[-1]
    last_surfaces_hit.append(surf_id)
    # for ezest plotting, only consider rays that entered the forbidden zone
    # if surf_id != mesh_ids[5]:
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
surf_ids = list(surf_ids)
if o3d.t.geometry.RaycastingScene.INVALID_ID in surf_ids:
    surf_ids[surf_ids.index(o3d.t.geometry.RaycastingScene.INVALID_ID)] = -1
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