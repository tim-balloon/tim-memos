import matplotlib.pyplot as plt
import numpy as np
import pickle

from ray_sets import RayPath

query_surface = 'cryostat_window'

with open('paths.pickle', 'rb') as f:
    paths = pickle.load(f)
with open('azs.pickle', 'rb') as f:
    aa = pickle.load(f)
with open('els.pickle', 'rb') as f:
    ee = pickle.load(f)
with open('results_incident.pickle', 'rb') as f:
    results_incident = pickle.load(f)
with open('results_problem.pickle', 'rb') as f:
    results_problem = pickle.load(f)
N_rays = len(paths)


fig, ax = plt.subplots(ncols=2, nrows=2)
ax = ax.flatten()
im = ax[0].pcolormesh(
    aa * 180. / np.pi,
    ee * 180. / np.pi,
    results_incident / N_rays,
    cmap='bone'
)
plt.colorbar(im, ax=ax[0])
im = ax[1].pcolormesh(
    aa * 180. / np.pi,
    ee * 180. / np.pi,
    (results_problem / results_incident),
    vmax=0.1,
    cmap='turbo'
)
plt.colorbar(im, ax=ax[1])
im = ax[2].pcolormesh(
    aa * 180. / np.pi,
    ee * 180. / np.pi,
    np.log10(results_incident / N_rays),
    cmap='bone'
)
plt.colorbar(im, ax=ax[2])
im = ax[3].pcolormesh(
    aa * 180. / np.pi,
    ee * 180. / np.pi,
    np.log10(results_problem / results_incident),
    cmap='turbo'
)
plt.colorbar(im, ax=ax[3])
[a.axhline(-20, linestyle='--', color='silver', label='Relative Horizon @ Min. El.') for a in ax]
[a.scatter(90, 0, s=50, alpha=0.5, marker='o', color='silver', label='Boresight') for a in ax]
ax[0].legend(loc='lower left')
[ax[i].set_title(s) for i,s in enumerate(['Incident Fraction', 'Problematic Hit Fraction'] * 2)]
# [a.set_aspect('equal') for a in ax]
[a.set_xlabel('Az') for a in ax]
[a.set_ylabel('El') for a in ax]
fig.suptitle(query_surface)
fig.tight_layout()
plt.show()

