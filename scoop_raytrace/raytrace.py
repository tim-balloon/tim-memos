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
        self.terminated = False

    def ray_to_line(self, start:o3d.core.Tensor, end:o3d.core.Tensor):
        l = o3d.t.geometry.LineSet(
            np.vstack([start[u_].numpy(), end[u_].numpy()]),
            np.array([[0,1]])
        )
        self.last_pos = end[u_]
        return l

    def append(self, ray_start, ray_end, surf_hit_id):
        self.rays.append(ray_end)
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
meshes, mesh_names, absorber_meshes, system_hull = geometry.get_geometry()

print('Creating scene...')
scene = o3d.t.geometry.RaycastingScene()
mesh_ids = [scene.add_triangles(m) for m in meshes]
geom_dict = {mesh_ids[i]: m for i, m in enumerate(meshes)}
mesh_ids = [o3d.t.geometry.RaycastingScene.INVALID_ID] + mesh_ids
mesh_id_to_name = {mesh_ids[i]: mesh_name for i, mesh_name in enumerate(mesh_names)}

print('Creating ray bundles...')
rays, N_rays = ray_sets.angular_sector()
# rays, N_rays = ray_sets.simple_fan([1 - 1e-1, .75, .51 + 1e-2])
# rays, N_rays = ray_sets.random_disc(1, 100, [0, 0, 10], [0, 0, -1])

# store history of each ray
paths = [RayPath(i) for i in range(N_rays)]
for i, path in enumerate(paths):
    path.append(rays[i], rays[i], o3d.t.geometry.RaycastingScene.INVALID_ID)

# if aluminized mylar/aluminum mirrors have reflection coefficients of
# ~.99, any ray is down to ~.6 by 50 bounces
max_consecutive_hits = 3 # indicates a ray may be trapped inside a mesh
N_bounces = 50
i_bounce = 0
print('Tracing rays...')
while i_bounce < N_bounces:
    # build the set of rays to trace
    valid_rays = []
    ray_idx_to_path_idx = []
    for i, path in enumerate(paths):
        if path.terminated:
            continue
        valid_rays.append(path.rays[-1].numpy())
        ray_idx_to_path_idx.append(i)
    if not valid_rays:
        break
    rays = o3d.core.Tensor(valid_rays, dtype=o3d.core.Dtype.Float32)

    ans = scene.cast_rays(rays)

    distance_finite = np.isfinite(ans['t_hit'].numpy())
    miss_mask = np.where(~distance_finite)[0]
    for i in miss_mask:
        paths[ray_idx_to_path_idx[i]].terminated = True
    hit_mask = np.where(distance_finite)[0]
    print(
        f'Bounce {i_bounce} finds {len(hit_mask)} hits ' +
        f'on surfaces {[mesh_id_to_name[ide] for ide in ans["geometry_ids"].numpy()]}'
    )
    for i in hit_mask:
        this_ray = rays[i]
        this_path = paths[ray_idx_to_path_idx[i]]
        mesh_id_hit = ans["geometry_ids"].numpy()[i]
        mesh_hit = geom_dict[mesh_id_hit]
        this_path.color = mesh_hit.vertex.colors[0].numpy()

        # make double-sure units of distance are still 1m
        this_ray[v_] = this_ray[v_] / np.linalg.norm(this_ray[v_].numpy())
        dist = ans['t_hit'][i]
        end = this_ray.clone()
        end[u_] = this_ray[u_] + this_ray[v_] * dist

        # terminate if absorbed
        if mesh_hit in absorber_meshes:
            this_path.append(this_ray, end, mesh_id_hit)
            this_path.terminated = True
            continue

        # check to see if ray has ended up inside mesh:
        # get the projection along triangle surface normal of a vector pointing
        # from triangle's centroid to intersection's position
        # assume outward-facing normal, so a point inside has a negative
        # projection
        v = mesh_hit.vertex['positions'].numpy()
        t = mesh_hit.triangle['indices'].numpy()
        tidx = ans['primitive_ids'].numpy()[i]
        # triangle vertex centroid
        centroid = v[t[tidx]].mean(axis=0)
        # triangle surface normal
        nhat = mesh_hit.triangle.normals[tidx].numpy()
        # projection of intersection position along surface normal
        intersec_vec = end[u_].numpy() - centroid
        proj = np.dot(intersec_vec, nhat)
        # fix errant interior intersections by flipping pos along the normal
        if proj < 0:
            correction_distance = np.max([1e-7, -2 * proj])
            corrected_pos = end[u_].numpy() + nhat * correction_distance
            end[u_] = corrected_pos
            print(
                f'WARNING: ray {i} propagated inside mesh ' +
                f'{mesh_id_to_name[mesh_id_hit]}, flipping pos about mesh ' + 
                f'normal, a correction of {correction_distance} m.'
            )
            # # check your work
            # intersec_vec = corrected_pos - centroid
            # proj = np.dot(intersec_vec, nhat)
            # if proj < 0:
            #     raise RuntimeError(
            #         f'Mesh ray eater fix failed! Fixed ray was {proj} ' +
            #         f'inside mesh {mesh_id_to_name[mesh_id_hit]}!'
            #     )

        # propagate rays that will be continuing on to next surface
        vhat_new = get_new_direction(this_ray, nhat)
        new_ray = np.concatenate([end[u_].numpy(), vhat_new])
        this_path.append(
            this_ray,
            o3d.core.Tensor(
                new_ray,
                dtype=o3d.core.Dtype.Float32
            ),
            mesh_id_hit
        )

        surf_ids, counts = np.unique(this_path.surfaces_hit, return_counts=True)
        if any(counts > max_consecutive_hits):
            print(
                f'WARNING: path {ray_idx_to_path_idx[i]} hit a mesh more ' +
                f'than {max_consecutive_hits} times: ' +
                f'{this_path.surfaces_hit} Terminating.'
            )
            this_path.terminated = True

    i_bounce += 1

print(f'Simulation terminated after {i_bounce} bounces.')

# -----------------------------------------------------------------------------
# Rendering + statistics
# -----------------------------------------------------------------------------
print('Creating render...')
hull_scene = o3d.t.geometry.RaycastingScene()
hull_scene.add_triangles(system_hull)
last_surfaces_hit = []
geom = []
N_incident = 0 # number of rays that entered the structure
for path in paths:
    surf_id = path.surfaces_hit[-1]
    last_surfaces_hit.append(surf_id)
    # for ezest plotting, only consider rays that entered the forbidden zone
    # if surf_id != mesh_ids[5]:
    #     continue
    for ray in path.rays:
        query_point = o3d.core.Tensor([ray[u_].numpy()], dtype=o3d.core.Dtype.Float32)
        if hull_scene.compute_signed_distance(query_point) < 0:
            N_incident += 1
            break
    # unwind all paths into lines
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

# convert back to legacy to render
meshes = [o3d.t.geometry.TriangleMesh.to_legacy(m) for m in meshes]
geom += meshes
o3d.visualization.draw_geometries(geom, mesh_show_wireframe=False)

# plot statistics

o3d.visualization.draw_geometries([o3d.t.geometry.TriangleMesh.to_legacy(system_hull)], mesh_show_wireframe=True)

# fraction of counts per last hit surface
fig, ax = plt.subplots()
surf_ids, counts = np.unique(last_surfaces_hit, return_counts=True)
surf_ids = list(surf_ids)

xticklabels = []
for i, id in enumerate(surf_ids):
    label = mesh_id_to_name[id]
    xticklabels.append(label)
    if id == o3d.t.geometry.RaycastingScene.INVALID_ID:
        surf_ids[i] = -1

ax.bar(surf_ids, counts / N_rays)
# ax.set_yscale('log')
ax.set_xticks(surf_ids)
ax.set_xticklabels(xticklabels)
ax.set_title('Ray Fates')
ax.set_xlabel('ID of Last Surface')
ax.set_ylabel('Fraction of Total Casted Rays')
plt.show()

# ray counts per last hit surface
fig, ax = plt.subplots()
ax.bar(surf_ids, counts)
# ax.set_yscale('log')
ax.set_xticks(surf_ids)
ax.set_xticklabels(xticklabels)
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