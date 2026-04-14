import numpy as np
import scipy.constants as c
import astropy.units as u
import os
from astropy.visualization import quantity_support
quantity_support()


def rebin(x, y, x_new):
    '''
    Assign values from the old array to the new, weighted by their overlap with
    the new bins.
    '''
    y_new = np.zeros_like(x_new).value * y.unit
    for i, (l_new, r_new) in enumerate(zip(x_new[:-1], x_new[1:])):
        for j, (l, r) in enumerate(zip(x[:-1], x[1:])):
            rightest_left = max(l_new, l)
            leftest_right = min(r_new, r)
            overlap_distance = leftest_right - rightest_left
            if overlap_distance <= 0:
                continue
            dx_new = r_new - l_new
            weight = overlap_distance / dx_new
            y_new[i] += (y[j] * weight)
    if len(y_new) > 1:
        y_new[-1] = y_new[-2]
    return x_new, y_new

def TIM_NEI_model(which='SW', path='/home/evanmayer/github/tim-inst_modl/Spectral_loading_model/'):
    '''
    TIM fiducial spectral loading model. Load NEIs for each channel from
    Jianyang (Frank) Fu's model:
    https://github.com/tim-balloon/tim-inst_modl/blob/master/Spectral_loading_model/Spectral_loading.ipynb,
    Output is NEI, so needs to be divided by sqrt(t_int) to yield Jy/sr.

    Parameters
    ----------
    which : str (optional)
        Specify whether to load the short-wave (SW) or long-wave (LW) module's
        noise.
    path : str (optional)
        Specify the directory containing the NEI model output data.

    Returns
    -------
    freq_module : astropy.Quantity
        Frequency axis, as read from the NEI model file, in Hz
    nei : astropy.quantity
        NEI numbers for each frequency, in Jy s^(1/2) / sr
    '''
    fname = os.path.join(path, f'TIM_{which}_loading.tsv')
    lambda_micron, nep, nei = np.genfromtxt(
        fname,
        skip_header=0,
        dtype=float,
        delimiter='\t',
        unpack=True
    )
    # add units and flip order: cube spectral axis ordered by increasing frequency
    lambda_micron *= u.micron
    nep = nep[::-1] * u.W / (u.Hz ** 0.5)
    nei = nei[::-1] * (u.Jy / u.sr) * (u.s ** 0.5)
    freq_module = (c.c*u.m/u.s / lambda_micron[::-1]).to(u.Hz)
    return freq_module, nei

def beam_solid_angle(D, nus):
    lambds = (c.c / nus).to(u.um)
    thetas = (1.2 * lambds / D).decompose() * u.rad
    omegas = ((np.pi / 4 / np.log(2)) * thetas ** 2).to(u.sr)
    return omegas

#------------------------------#

import pandas as pd
from astropy.stats import gaussian_fwhm_to_sigma
from specutils import Spectrum1D
from specutils.manipulation import FluxConservingResampler
      
def set_TIM_noise(frequencies, telescope_diameter=2, path='src/'):
    """
    rebin the TIM noise model to given frequencies

    Parameters
    ----------
    frequencies: 1d array
        EM frequency list to rebin Frank's noise model to
    telescope_diameter: float
        the telescope diameter in meters
    path: str
        the path to the two tsv files containing the NEI model. 

    Returns
    -------
    """

    #------------------------------------------------------------
    #The High Frequency (HF) arrays will measure the higher frequency part of the frequency band 
    noise_model_HF = pd.read_csv(path+'TIM_SW_loading.tsv', sep='\t')
    #The Low Freauency (LF) arrays will measure the lower frequencies
    noise_model_LF = pd.read_csv(path+'TIM_LW_loading.tsv', sep='\t')
    lambda_HF = noise_model_HF["# Wavelength[um]"]*1e3 #nm
    nu_HF = c.c/(lambda_HF*1e-9)/1e9 #GHz
    nHF = noise_model_HF["NEI[Jy/sr s^1/2]"]
    lambda_LF = noise_model_LF["# Wavelength[um]"]*1e3 #nm
    nu_LF = c.c/(lambda_LF*1e-9)/1e9 #GHz
    nLF = noise_model_LF["NEI[Jy/sr s^1/2]"]
    #Combine the LF and HF arrays into 1 array. 
    freqs = np.concatenate((nu_LF[::-1], nu_HF[::-1])) * u.GHz
    noise = np.concatenate((nLF[::-1], nHF[::-1])) * u.Jy / u.sr 
    fwhm = (1.22 * c.c * u.m/u.s / (freqs.to(u.Hz) * telescope_diameter * u.m)).to(u.rad, equivalencies=u.dimensionless_angles())
    Omega_beam = (2 * np.pi * (fwhm * gaussian_fwhm_to_sigma)**2).to(u.sr)
    NEFD = noise * Omega_beam

    #------------------------------------------------------------
    fwhm =  (1.22 * c.c * u.m/u.s / (frequencies.to(u.Hz) * telescope_diameter * u.m)).to(u.rad, equivalencies=u.dimensionless_angles())
    Omega_beam_resampled  = (2*np.pi*(fwhm * gaussian_fwhm_to_sigma)**2).to(u.sr)
    spec = Spectrum1D(spectral_axis=freqs, flux=NEFD)
    fluxc_resample = FluxConservingResampler()
    sed_in_tim = fluxc_resample(spec, frequencies) 
    model = sed_in_tim.flux
    model /= Omega_beam_resampled
    #------------------------------------------------------------
    
    return frequencies, model*u.s**(1/2)