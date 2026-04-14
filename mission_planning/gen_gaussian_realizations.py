
import numpy as np
from scipy import interpolate
import scipy.constants as cst
from src.map_power_spectrum import angular_power_spectrum
from astropy.cosmology import Planck18 as cosmo

def D3_pk_to_D2_pk(z, dnu, nu0):

    dz = (1+z)**2 / nu0 * dnu
    Dc =  cosmo.comoving_distance(z) 
    nu_obs = nu0 / (1+z)
    delta_Dc = ( (cst.c*1e-3) * (1+z) * dnu / cosmo.H(z) / nu_obs)
    pk_3d_to_2d = 1/(Dc**2*delta_Dc)
    k_3d_to_2d  = Dc/2/np.pi
    #full_volume_at_z = 4/3*np.pi*(Dc_max**3-Dc_min**3)
    return  k_3d_to_2d.value , pk_3d_to_2d.value

def D2_pk_to_D3_pk(z, dnu, nu0):

    """
    convert an angular power spectrum to a spherically averaged power spectrum (see e.g., Bethermin et al. 2022)

    Parameters
    ----------
    z : array
        redshift
    dnu : array
        frequency channel width in GHz
    nu0: float
        rest frame frequency in GHz

    Returns
    -------
    cube : ndarray
        Gaussian random field [Jy]
    pk_map : ndarray
        3D power spectrum sampled on FFT grid
    """

    dz = (1+z)**2 / nu0 * dnu
    Dc =  cosmo.comoving_distance(z) 
    nu_obs = nu0 / (1+z)
    delta_Dc = ( (cst.c*1e-3) * (1+z) * dnu / cosmo.H(z) / nu_obs)
    pk_3d_to_2d = 1/(Dc**2*delta_Dc)
    k_3d_to_2d  = Dc/2/np.pi
    #full_volume_at_z = 4/3*np.pi*(Dc_max**3-Dc_min**3)
    return  1/k_3d_to_2d.value , 1/pk_3d_to_2d.value


def gaussian_random_field(k, pk, ny, nx, res, k_cutoff=None, pk_map = None, force = True):

    """
    Create a map of a Gaussian random field, given its angular power spectrum or from a power law with a given index 
        

    Parameters
    ----------
    k: 1d array
        the wavenumbers in rad-1

    pk: 1d array
        the given power spectrum in Jy2/sr

    ny, nx: int
        the size of the map to generate

    res: 
        the resolution of the map in rad

    k_cutoff: float
        the maximum multipol taken into account in the map generation (optional, in rad-1)

    pk_map: 2d array
        map containing the power amplitudes for each k. If provided, not recomputed. 

    force: bool
        set the negative values in the power spectrum map to zero. 

    Returns
    -------
    
    real_space_map: 2d array
        the generated map in real space in Jy/sr

    pk_map: 2d array
        the angular power spectrum map in Jy2/sr
    """

    norm = 1/res

    np.random.seed()

    noise = np.random.normal(loc=0, scale=1, size=(ny,nx))
    dmn1  = np.fft.fft2( noise )

    #Interpolate input power spectrum
    if(pk_map is None):

        aps = angular_power_spectrum(np.zeros((1,1,1)), res)
        aps.give_map_spatial_freq()
        k_map = aps.k_map

        if(k_cutoff is not None): kmax = np.minimum(k_cutoff, k.max())
        else: kmax = np.minimum(k.max(), k_map.max()) 
        
        pk_map = np.zeros(k_map.shape) 
        
        w = np.where((k_map>k.min()) & (k_map<=kmax))
    
        if(not w[0].any()): print("wrong k range")
        else:
            #Power law spectrum
            print("interpolate")
            f = interpolate.interp1d( k, pk,  kind='linear')
            pk_map[w] = f(k_map[w])
            w1 = np.where( pk_map <= 0)
            if(w1[0].shape[0] != 0 and force): pk_map[w1] = 0

    #Fill amn_t
    amn_t = dmn1 * norm * np.sqrt( pk_map )
    
    #Output map
    real_space_map = np.real(np.fft.ifft2( amn_t ))
    
    return real_space_map, pk_map

def gaussian_random_field_3d(k, pk, nx, ny, nz, dx, dy, dz, pk_map = None, k_cutoff= None,force = True):

    """
    Generate a 3D Gaussian random field from a 3D power spectrum.

    Parameters
    ----------
    k : array
        Wavenumbers [Mpc^-1]
    pk : array
        Power spectrum P(k) [Jy^2 / Mpc^3]

    nx, ny, nz : int
        Cube size

    dx, dy, dz : float
        Pixel size [Mpc]

    Returns
    -------
    cube : ndarray
        Gaussian random field [Jy]
    pk_map : ndarray
        3D power spectrum sampled on FFT grid
    """

    # --- white noise cube ---
    noise = np.random.normal(size=(nz, ny, nx))
    noise_fft = np.fft.fftn(noise)

    #Interpolate input power spectrum
    if(pk_map is None):

        # --- Fourier frequencies ---
        kx = np.fft.fftfreq(nx, dx) * 2*np.pi
        ky = np.fft.fftfreq(ny, dy) * 2*np.pi

        if(nz>1):
                kz = np.fft.fftfreq(nz, dz) * 2*np.pi
                kz, ky, kx = np.meshgrid(kz, ky, kx, indexing='ij')
                k_map = np.sqrt(kx**2 + ky**2 + kz**2)
        else: 
                ky, kx = np.meshgrid(ky, kx, indexing='ij')
                k_map = np.sqrt(kx**2 + ky**2)

        if(k_cutoff is not None): kmax = np.minimum(k_cutoff, k.max())
        else: kmax = np.minimum(k.max(), k_map.max()) 
        pk_map = np.zeros(k_map.shape) 
        w = np.where((k_map>k.min()) & (k_map<=kmax))
        if(not w[0].any()): print("wrong k range")
        else:
            f = interpolate.interp1d( k, pk,  kind='linear')
            pk_map[w] = f(k_map[w])
            w1 = np.where( pk_map <= 0)
            if(w1[0].shape[0] != 0 and force): pk_map[w1] = 0
            
        f = interpolate.interp1d(k, pk, bounds_error=False, fill_value=0)
        pk_map = f(k_map)

    # --- voxel volume ---
    Vvox = dx * dy * dz

    # --- apply power spectrum ---
    field_fft = noise_fft * np.sqrt(pk_map / Vvox)

    # --- inverse transform ---
    cube = np.real(np.fft.ifftn(field_fft))

    return cube, pk_map