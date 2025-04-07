import matplotlib.pyplot as plt
import numpy as np
import pickle

import open3d as o3d

import geometry
import ray_sets
from ray_sets import RayPath

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


print('Creating meshes...')
meshes, mesh_names, absorber_meshes, system_hull = geometry.get_geometry()
hull_scene = o3d.t.geometry.RaycastingScene()
hull_scene.add_triangles(system_hull)

auld_meshes = meshes

print('Creating scene...')
scene = o3d.t.geometry.RaycastingScene()
mesh_ids = [scene.add_triangles(m) for m in meshes]
geom_dict = {mesh_ids[i]: m for i, m in enumerate(meshes)}
mesh_ids = [o3d.t.geometry.RaycastingScene.INVALID_ID] + mesh_ids
mesh_id_to_name = {mesh_ids[i]: mesh_name for i, mesh_name in enumerate(mesh_names)}

print('Creating ray bundles...')
# construct sample points on a 10 m sphere: note that trial density is greater
# near poles, but this is just efficiency/angular sampling accuracy
az_pts = np.arange(-45, 0, 1) * np.pi / 180. + np.pi/2
el_pts = np.arange(-45, 90, 1) * np.pi / 180.
aa, ee = np.meshgrid(az_pts, el_pts)
results_incident = np.zeros_like(aa)
results_problem = np.zeros_like(aa)
end_idx = len(aa.flatten())
idx = 0
try:
    for ia, az in enumerate(az_pts):
        for ie, el in enumerate(el_pts):
            idx += 1
            x = 10. * np.cos(az)
            y = 10. * np.sin(el)
            z = 10. * np.sin(az)
            nhat = np.array([-x, -y, -z])
            nhat /= np.linalg.norm(nhat)
            rays, N_rays = ray_sets.random_disc(3, 3, [x, y, z], nhat)
            # fig, ax = ray_sets.plot_rays(rays[:,:3].numpy(), rays[:,3:].numpy())
            # ax.set_xlim([-10, 10])
            # ax.set_ylim([-10, 10])
            # ax.set_zlim([-10, 10])
            # ax.set_aspect('equal')
            # plt.show()

            # store history of each ray
            paths = [RayPath(i) for i in range(N_rays)]
            for i, path in enumerate(paths):
                path.append(rays[i], rays[i], o3d.t.geometry.RaycastingScene.INVALID_ID)

            # if aluminized mylar/aluminum mirrors have reflection coefficients of
            # ~.99, any ray is down to ~.6 by 50 bounces (e.g. terahertz, solar)
            # if radiation is earth glow and rays hit mylarized side of mli, r~0.7,
            # so down to ~0.34 by 3 bounces 
            max_consecutive_hits = 10 # indicates a ray may be trapped inside a mesh
            N_bounces = 3
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
                # print(
                #     f'Bounce {i_bounce} finds {len(hit_mask)} hits ' +
                #     f'on surfaces {[mesh_id_to_name[ide] for ide in ans["geometry_ids"].numpy()]}'
                # )
                for i in hit_mask:
                    this_ray = rays[i]
                    this_path = paths[ray_idx_to_path_idx[i]]
                    mesh_id_hit = ans["geometry_ids"].numpy()[i]
                    mesh_hit = geom_dict[mesh_id_hit]
                    this_path.color = mesh_hit.vertex.colors[0].numpy()

                    # make double-sure units of distance are still 1m
                    # this_ray[v_] = this_ray[v_] / np.linalg.norm(this_ray[v_].numpy())
                    dist = ans['t_hit'][i]
                    end = this_ray.clone()
                    end[u_] = this_ray[u_] + this_ray[v_] * dist

                    # check to see if path has entered hull of interest -
                    # whichever rays hit a forbidden surface afterward are
                    # problematic
                    if not this_path.incident:
                        query_point = o3d.core.Tensor([end[u_].numpy()], dtype=o3d.core.Dtype.Float32)
                        if hull_scene.compute_signed_distance(query_point) < 0:
                            this_path.incident = True

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
                        # print(
                        #     f'WARNING: ray {i} propagated inside mesh ' +
                        #     f'{mesh_id_to_name[mesh_id_hit]}, flipping pos about mesh ' + 
                        #     f'normal, a correction of {correction_distance} m.'
                        # )
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
                        # print(
                        #     f'WARNING: path {ray_idx_to_path_idx[i]} hit a mesh more ' +
                        #     f'than {max_consecutive_hits} times: ' +
                        #     f'{this_path.surfaces_hit} Terminating.'
                        # )
                        this_path.terminated = True

                i_bounce += 1

            print(f'Simulation terminated after {i_bounce} bounces.')

            # -----------------------------------------------------------------------------
            # Rendering + statistics
            # -----------------------------------------------------------------------------
            print('Measuring results...')
            print(f'progress: {idx/end_idx:.2f}')
            query_surface = 'cryostat_window'
            last_surfaces_hit = []
            geom = []
            N_incident = 0 # number of rays that entered the structure
            N_cryo = 0
            N_primary = 0
            for path in paths:
                surf_id = path.surfaces_hit[-1]
                last_surfaces_hit.append(surf_id)
                # for ezest plotting, only consider rays that entered the forbidden zone
                # if surf_id != mesh_ids[5]:
                #     continue
                if mesh_id_to_name[surf_id] == query_surface:
                    N_cryo += 1
                if path.incident:
                    N_incident += 1
                # unwind all paths into lines
                # path.apply_color(path.color)
                # linesets = []
                # for l in path.lines:
                #     linesets.append(o3d.t.geometry.LineSet.to_legacy(l))
                # geom += linesets

            results_incident[ie][ia] = N_incident
            results_problem[ie][ia] = N_cryo

            # # add in the triad for reference
            # # coordinate system triad
            # triad = o3d.geometry.TriangleMesh.create_coordinate_frame(size=.5, origin=[0,0,0])
            # triad = o3d.t.geometry.TriangleMesh.from_legacy(triad)
            # triad.compute_vertex_normals()
            # auld_meshes += [triad,]

            # # convert back to legacy to render
            # plot_meshes = [o3d.t.geometry.TriangleMesh.to_legacy(m) for m in auld_meshes]
            # geom += plot_meshes
            # o3d.visualization.draw_geometries(geom, mesh_show_wireframe=False)
except KeyboardInterrupt as e:
    print(e)

with open('paths.pickle', 'wb') as f:
    pickle.dump(paths, f)
with open('azs.pickle', 'wb') as f:
    pickle.dump(aa, f)
with open('els.pickle', 'wb') as f:
    pickle.dump(ee, f)
with open('results_incident.pickle', 'wb') as f:
    pickle.dump(results_incident, f)
with open('results_problem.pickle', 'wb') as f:
    pickle.dump(results_problem, f)