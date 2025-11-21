from astroplan import Observer, FixedTarget, Constraint, AltitudeConstraint
from astroplan import is_observable, is_always_observable, observability_table
from astroplan.plots import plot_altitude, plot_finder_image

from astropy.coordinates import Angle, SkyCoord, EarthLocation, get_body
from astropy.time import Time
import astropy.units as u

import matplotlib.pyplot as plt
import numpy as np


EL_MIN = 20
EL_MAX = 52
DAZ_MIN = 90
DAZ_MAX = 225

LDB = (-77.861 * u.deg, 167.061 * u.deg)
FLOAT_ALT = 37000 * u.m

def wrap360(ang):
    return ((ang + 360.) % 360.)


class SunRelativeAzConstraint(Constraint):
    '''
    Constrain an asymmetrical sun-relative azimuth pointing of the boresight to
    target.
    These angles are the angles that the boresight must point away from the sun
    in order to maintain the instrument and electronics in the shade of the
    sunshade. As always, azimuth is measured +clockwise from the reference
    point, in this case the sun azimuth. The range is [0, 360] deg.
    '''
    def __init__(self, min=None, max=None):
        '''
        min : `~astropy.units.Quantity` or `None` (optional)
            Minimum acceptable azimuth angle between sun and boresight. `None`
            indicates no limit.
        max : `~astropy.units.Quantity` or `None` (optional)
            Maximum acceptable azimuth angle between sun and boresight. `None`
            indicates no limit.
        '''
        self.min = min if min is not None else 0*u.deg
        self.max = max if max is not None else 360*u.deg


    def compute_constraint(self, times, observer, targets):
        # targets = get_skycoord(targets)
        sun_body = get_body('sun', times, location=observer.location)
        sun = SkyCoord(ra=sun_body.ra, dec=sun_body.dec, obstime=times,
                       location=observer.location)
        sun_altaz = sun.transform_to('altaz')

        # Calculate separation between boresight and sun
        # Targets are automatically converted to SkyCoord objects
        # by __call__ before compute_constraint is called.

        try:
            n_targets = len(targets)
        except TypeError as e:
            targets = SkyCoord([targets,])
            n_targets = len(targets)
        try:
            n_times = len(times)
        except TypeError as e:
            # times = [times,]
            n_times = len(times)

        delta_az = np.atleast_2d(np.empty((n_targets, n_times)) * u.deg)
        for i, target in enumerate(targets):
            target_with_loc = SkyCoord(ra=target.ra, dec=target.dec, obstime=times, location=observer.location)
            target_altaz = target_with_loc.transform_to('altaz')
            delta_az[i,:] = wrap360(target_altaz.az.deg - sun_altaz.az.deg) * u.deg # time axis
        # print(n_targets, n_times, delta_az.shape, delta_az)

        if self.min is None and self.max is not None:
            mask = self.max >= delta_az
        elif self.max is None and self.min is not None:
            mask = self.min <= delta_az
        elif self.min is not None and self.max is not None:
            mask = ((self.min <= delta_az) &
                    (delta_az <= self.max))
        else:
            raise ValueError("No max and/or min specified in "
                             "SunRelativeAzConstraint.")
        return mask


def get_observer(launch_lat, launch_lon, float_alt, times):
    '''Generate an observer object with lat/lon that change over time like a balloon.'''
    t = (times - times[0]).to(u.hr)
    ldb = (launch_lat, launch_lon)
    # ground track:
    # Salter Test Flight Universal completed ~1 circuit in 11 days, 6 hr, 57 min.
    # Average the longitudinal velocity. Really, ballons have a spatial velocity,
    # so this constant lat assumption is an oversimplification.
    dlon_dt = -(360 * u.deg / (11 * u.day + 6 * u.hr + 57 * u.min)).to(u.deg / u.hr)
    lon = ldb[1] + dlon_dt * t
    lon = wrap360(lon.to(u.deg).value) * u.deg
    # add a little lat wobble, eyeballed from STFU flight track
    lat = 0 * u.deg + np.ones_like(lon.value) * ldb[0] + .2 * u.deg * np.sin(lon.to(u.rad) * 15)
    observer = Observer(longitude=lon, latitude=lat, elevation=float_alt, name="TIM")
    return observer


def observability(names:list, ras:list, decs:list, observer:Observer, times, plot=True):
    assert len(ras) == len(decs)
    targets = []
    for i in range(len(ras)):
        coord = SkyCoord(
            ras[i],
            decs[i],
            frame='icrs',
            obstime=times,
            location=observer.location
        )
        targets.append(FixedTarget(coord, names[i]))

    constraints = [
        AltitudeConstraint(EL_MIN * u.deg, EL_MAX * u.deg),
        SunRelativeAzConstraint(min=DAZ_MIN * u.deg, max=DAZ_MAX * u.deg)
    ]

    table = observability_table(constraints, observer, targets, times)

    if plot:
        # https://astroplan.readthedocs.io/en/latest/tutorials/constraints.html
        for j, target in enumerate(targets):
            observability_grid = np.zeros((len(constraints), len(times)))
            for i, constraint in enumerate(constraints):
                # Evaluate each constraint
                observability_grid[i, :] = constraint(
                    observer,
                    target,
                    times=times,
                    grid_times_targets=True
                )

            # Create plot showing observability of the target:
            extent = [-0.5, -0.5+len(times), -0.5, len(constraints) - 0.5]

            fig, ax = plt.subplots(figsize=(10,4))
            ax.imshow(observability_grid, extent=extent, cmap='bone_r', vmin=0, vmax=1, origin='lower')

            ax.set_yticks(range(0, len(constraints)))
            ax.set_yticklabels([c.__class__.__name__ for c in constraints])

            ax.set_xticks(range(len(times)))
            ax.set_xticklabels([t.datetime.strftime("%H:%M") for t in times])

            ax.set_xticks(np.arange(extent[0], extent[1]), minor=True)
            ax.set_yticks(np.arange(extent[2], extent[3]), minor=True)

            ax.grid(which='minor', color='w', linestyle='-', linewidth=1)
            ax.tick_params(axis='x', which='minor', bottom='off')
            plt.setp(ax.get_xticklabels(), rotation=30, ha='right')

            ax.tick_params(axis='y', which='minor', left='off')
            ax.set_xlabel('Time on {0} (UTC)'.format(times[0].datetime.date()))
            fig.subplots_adjust(left=0.25, right=0.9, top=0.9, bottom=0.1)
            ax.set_title(f'{target.name}: {table["fraction of time observable"][j] * (times[-1] - times[0]).to(u.hr):.2f}' + 
                         '\nBlack = Observable')
            fig.tight_layout()
        plt.show()
    print(table)

    return coord, table


def time_vs_altitude(observer, target, times):
    fig, ax = plt.subplots(figsize=(12,4))
    plot_altitude(target, observer, times, ax=ax, style_kwargs=dict(color='k'))
    ax.axhline(EL_MIN, color='limegreen')
    ax.axhline(EL_MAX, color='limegreen')
    ax.axhspan(EL_MIN, EL_MAX, color='limegreen', alpha=0.3)
    ax.set_title(target.name)
    ax.grid(True)
    fig.tight_layout()
    plt.show()
    return fig, ax


def ground_track(observer, times):
    this_lon = observer.longitude
    this_lat = observer.latitude
    t = (times - times[0]).to(u.hr)
    fig, ax = plt.subplots(figsize=(4, 4), subplot_kw=dict(projection='polar'))
    mappable = ax.scatter(this_lon.to(u.rad), this_lat, c=range(len(this_lon)))
    ax.set_rmin(-90)
    ax.set_rmax(-70)
    # ax.set_rticks(np.arange(-90, -70, 5))
    ax.set_theta_offset(np.pi / 2)
    ax.set_theta_direction(-1)
    ax.set_thetamin(0)
    ax.set_thetamax(360)
    ax.grid(True)
    ax.set_title(f'Looking Down:\nGround Track: {(t[-1] - t[0]).to(u.day).value:.1f} days')
    fig.colorbar(mappable, ax=ax, label='Time Since Launch (hr)')
    fig.tight_layout()
    plt.show()
    return fig, ax


if __name__ == '__main__':
    launch_location = EarthLocation(lat=LDB[0], lon=LDB[1], height=FLOAT_ALT)
    launch_time = Time('2026-12-25 00:00:00', scale='utc', location=launch_location)
    
    step_hr = 1.0 * u.hr
    my_duration = 24 * u.hr
    timespan = np.arange(0, my_duration.value + step_hr.value, step_hr.value) * u.hr
    times = launch_time + timespan

    tim = get_observer(
        launch_location.lat,
        launch_location.lon,
        launch_location.height,
        times
    )

    foo = SkyCoord.from_name('RCW 38')
    coord = SkyCoord(foo.ra, foo.dec, obstime=times, location=tim.location)
    my_label = 'RCW 38'

    foo1 = SkyCoord.from_name('RCW 36')
    coord1 = SkyCoord(foo1.ra, foo1.dec, obstime=times, location=tim.location)
    my_label1 = 'RCW 37'

    _, table = observability([my_label, my_label1], [coord.ra, coord1.ra,], [coord.dec, coord1.dec,], tim, times, plot=False)