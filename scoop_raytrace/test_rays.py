# import ray_sets

# rays, N_rays = ray_sets.random_disc(.5, 1000, [0, 0, 0], [0, .707, .707])

# ray_sets.plot_rays(rays[:,:3].numpy(), rays[:,3:].numpy())

import open3d as o3d
import numpy as np

import geometry

meshes, _, _= geometry.get_geometry()
mesh = meshes[3]

# Create scene and add the monkey model.
scene = o3d.t.geometry.RaycastingScene()
# d = o3d.data.MonkeyModel()
# mesh = o3d.t.io.read_triangle_mesh(d.path)
mesh_id = scene.add_triangles(mesh)

# Create a grid of rays covering the bounding box
bb_min = mesh.vertex['positions'].min(dim=0).numpy()
bb_max = mesh.vertex['positions'].max(dim=0).numpy()
x,y = np.linspace(bb_min, bb_max, num=100)[:,:2].T
xv, yv = np.meshgrid(x,y)
orig = np.stack([xv, yv, np.full_like(xv, bb_min[2]-1)], axis=-1).reshape(-1,3)
dest = orig + np.full(orig.shape, (0,0,2+bb_max[2]-bb_min[2]),dtype=np.float32)
rays = np.concatenate([orig, dest-orig], axis=-1).astype(np.float32)

# Compute the ray intersections.
lx = scene.list_intersections(rays)
lx = {k:v.numpy() for k,v in lx.items()}

# Calculate intersection coordinates using the primitive uvs and the mesh
v = mesh.vertex['positions'].numpy()
t = mesh.triangle['indices'].numpy()
tidx = lx['primitive_ids']
uv = lx['primitive_uvs']    
w = 1 - np.sum(uv, axis=1)
c = \
v[t[tidx, 1].flatten(), :] * uv[:, 0][:, None] + \
v[t[tidx, 2].flatten(), :] * uv[:, 1][:, None] + \
v[t[tidx, 0].flatten(), :] * w[:, None]

# Calculate intersection coordinates using ray_ids
# c = rays[lx['ray_ids']][:,:3] + rays[lx['ray_ids']][:,3:]*lx['t_hit'][...,None]

# Visualize the rays and intersections.
lines = o3d.t.geometry.LineSet()
lines.point.positions = np.hstack([orig,dest]).reshape(-1,3)
lines.line.indices = np.arange(lines.point.positions.shape[0]).reshape(-1,2)
lines.line.colors = np.full((lines.line.indices.shape[0],3), (1,0,0))
x = o3d.t.geometry.PointCloud(positions=c)
o3d.visualization.draw([mesh, lines, x], point_size=8)