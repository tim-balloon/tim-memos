import matplotlib.pyplot as plt
import numpy as np
from scipy.spatial.transform import Rotation

import open3d as o3d


def simple_fan(radii):
    # [r_out - 1e-6, r_sec_out + 1e-6]
    # on-axis, sparse
    h = 10
    ray_list = [[0, 0, h, 0, 0, -1]]
    for r in radii:
        ray_list += [[0, r, h, 0, 0, -1]]
        ray_list += [[r, 0, h, 0, 0, -1]]
        ray_list += [[0, -r, h, 0, 0, -1]]
        ray_list += [[-r, 0, h, 0, 0, -1]]
    rays = o3d.core.Tensor(
        ray_list,
        dtype=o3d.core.Dtype.Float32
    )
    N_rays = rays.numpy().shape[0]
    return rays, N_rays


def simple_gaussian():
    # on-axis, Gaussian bundle, dense
    h = 10
    N_rays = 500
    rays = o3d.core.Tensor(
        np.zeros((N_rays, 6)),
        dtype=o3d.core.Dtype.Float32
    )
    xy_coord = np.random.normal(scale=(.35,.35), loc=(0,0), size=(N_rays, 2))
    rays[:,0] = xy_coord[:,0]
    rays[:,1] = xy_coord[:,1]
    rays[:,2] = h
    rays[:,5] = -1
    return rays, N_rays


def random_disc(r_max, N_rays, pos, dir, rng=None):
    if not rng:
        rng = np.random.default_rng(seed=77777)
    # inverse transform sampling
    r = r_max * np.sqrt(rng.uniform(size=N_rays))
    theta = rng.uniform(size=N_rays) * 2. * np.pi
    x = r * np.cos(theta)
    y = r * np.sin(theta)
    z = np.zeros_like(x)
    nhat = [0, 0, 1] # initial normal of the disc of points
    u = np.vstack([x, y, z]).T
    v = np.tile(dir, (N_rays, 1))
    R, _ = Rotation.align_vectors(np.atleast_2d(dir), np.atleast_2d(nhat))
    u = R.apply(u)
    nhat = R.apply(nhat)
    u += pos
    rays = o3d.core.Tensor(
        np.zeros((N_rays, 6)),
        dtype=o3d.core.Dtype.Float32
    )
    rays[:,0] = u[:,0]
    rays[:,1] = u[:,1]
    rays[:,2] = u[:,2]
    rays[:,3] = v[:,0]
    rays[:,4] = v[:,1]
    rays[:,5] = v[:,2]
    return rays, N_rays


def random_omnidirectional():
    earth_limb_angle = (-20. + np.linspace(0, 6, num=2001, endpoint=True)) * np.pi / 180.
    ray_z = 10
    ray_ys = ray_z * np.tan(earth_limb_angle)
    ray_xs = np.linspace(-4, 4, num=2001, endpoint=True)
    XX, YY = np.meshgrid(ray_xs, ray_ys)
    xflat = XX.flatten()
    yflat = YY.flatten()
    rng = np.random.default_rng(seed=77777)
    v = rng.normal(size=(len(xflat), 3))
    vhat = v / np.linalg.norm(v)
    assert(len(xflat) == len(yflat))
    N_rays = vhat.shape[0]
    rays = o3d.core.Tensor(
        np.zeros((N_rays, 6)),
        dtype=o3d.core.Dtype.Float32
    )
    rays[:,0] = xflat
    rays[:,1] = yflat
    rays[:,2] = ray_z
    rays[:,3:] = vhat
    return rays, N_rays


def angular_sector():
    # focused range of angles
    # set up a grid of origin points in relevant angular ranges
    # the nominal lowest el is +20, and Earth limb may become important by +6.
    # launch rays from a relative angle below the assembly
    earth_limb_angle = (-20. + np.linspace(0, .1, num=1, endpoint=True)) * np.pi / 180.
    ray_z = 10
    ray_ys = ray_z * np.tan(earth_limb_angle)
    ray_xs = np.linspace(-10, 10, num=20, endpoint=True)
    XX, YY = np.meshgrid(ray_xs, ray_ys)
    xflat = XX.flatten()
    yflat = YY.flatten()
    ray_bundle_origin = np.vstack([xflat, yflat, np.ones_like(xflat) * ray_z]).T
    aimpoint = np.array([0, 0, 0]).T
    v_aim = aimpoint - ray_bundle_origin
    v_aim /= np.atleast_2d(np.linalg.norm(v_aim, axis=1)).T

    # shoot a bundle of rays, each rotated by a small amount relative to the main
    # aim vector
    theta_half_angle = np.pi/4
    phi_half_angle = np.pi/4
    N_bundle_side = 100
    thetas = np.linspace(-theta_half_angle, theta_half_angle, num=N_bundle_side)
    phis = np.linspace(-phi_half_angle, phi_half_angle, num=N_bundle_side)
    # rays_per_origin = 100
    ray_list = []
    for i in range(len(xflat)):
        print(f'{(i+1) / len(xflat):.2f}', end='\r')
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
    return rays, N_rays


def plot_rays(u, v):
    # u is a (N,3)-shape position vector
    # v is a (N,3)-shape orientation vector
    if u.shape[0] > 100:
        alpha = 0.3
    else:
        alpha = 1
    fig, ax = plt.subplots(subplot_kw={'projection':'3d'})
    ax.quiver(
        u[:,0],
        u[:,1],
        u[:,2],
        v[:,0],
        v[:,1],
        v[:,2],
        alpha=alpha
    )
    ax.scatter(
        u[:,0],
        u[:,1],
        u[:,2],
        alpha=alpha
    )
    ax.scatter(0,0,0)
    ax.set_aspect('equal')
    ax.set_xlabel('x')
    ax.set_ylabel('y')
    ax.set_zlabel('z')
    plt.show()
    return fig, ax