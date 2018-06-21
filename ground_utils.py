from solid.utils import translate, rotate, union
from solid.utils import cylinder, color, sphere
import numpy as np
from ctapipe.coordinates import HorizonFrame, TiltedGroundFrame, GroundFrame, NominalFrame, CameraFrame, TelescopeFrame

import astropy.units as u

from utilities import ref_arrow_3d, grid_plane, ref_arrow_2d, rot_arrow

def tilted_grid(event, tel_pos=False, zen_az_arrows=False):
    """
    Return the telescopes positions in the TiltedGroundFrame and plot them according to azimuth and zenith of simulation
    :param event: event selected from simtel
    :param tel_pos: (bool) If True, plot the telescopes as spheres
    :param zen_az_arrows: plot curved arrows for ZEN and AZ in titled ref frame
    :return:
    """
    alt = event.mcheader.run_array_direction[1]
    az = event.mcheader.run_array_direction[0]

    array_pointing = HorizonFrame(alt=alt, az=az)
    ground_coordinates = GroundFrame(x=event.inst.subarray.tel_coords.x,
                                     y=event.inst.subarray.tel_coords.y,
                                     z=event.inst.subarray.tel_coords.z,  # *0+15.0*u.m,
                                     pointing_direction=array_pointing)

    tilted = ground_coordinates.transform_to("TiltedGroundFrame")

    grid_unit = 20000  # in centimeters
    tilted_system = union()


    # ADD TELESCOPES AS SPHERES
    if tel_pos:
        # for i in range(tilted.x.size):
        for i in range(50):
            coords = [100*tilted.x[i].value, 100*tilted.y[i].value]
            position = translate(coords)(color([1, 0, 0])(sphere(r=800)))
            tilted_system.add(position)

    # add GRID
    grid_tilted = grid_plane(grid_unit=grid_unit,
                             count=2*int(100*np.max(np.abs(ground_coordinates.x.value))/grid_unit),
                             line_weight=200,
                             plane='xy')

    grid_tilted = color([1, 0, 0, 0.5])(grid_tilted)
    grid_tilted = grid_tilted + ref_arrow_2d(8000, label={'x': "x_tilted", 'y': "y_tilted"}, origin=(0, 0))

    tilted_system = rotate([0, 90-alt.to('deg').value, az.to('deg').value])(tilted_system)
    tilted_system.add(grid_tilted)

    arr_curved_az = color([1, 1, 0])(rot_arrow(8000, az.to('deg').value, 0, label='AZ'))
    tilted_system.add(arr_curved_az)
    arr_curved_alt = color([1, 0, 1])(rot_arrow(8000, 0, 90-alt.to('deg').value, label='ZEN'))
    arr_curved_alt = rotate([90, 0, 0])(arr_curved_alt)
    tilted_system.add(arr_curved_alt)

    return tilted_system


def ground_grid(event, tel_pos=False):
    """
    Return the telescopes positions in the GroundFrame and plot on ground
    :param event: input event selected from simtel
    :param tel_pos: (bool) if True, plot the telescopes as spheres
    :return:
    """
    alt = event.mcheader.run_array_direction[1]
    az = event.mcheader.run_array_direction[0]
    array_pointing = HorizonFrame(alt=alt, az=az)

    ground_coordinates = GroundFrame(x=event.inst.subarray.tel_coords.x,
                                     y=event.inst.subarray.tel_coords.y,
                                     z=event.inst.subarray.tel_coords.z,
                                     pointing_direction=array_pointing)

    grid_unit = 20000  # in centimeters

    ground_system = union()
    if tel_pos:
        # for i in range(ground_coordinates.x.size):
        for i in range(50):
            coords = [100*ground_coordinates.x[i].value, 100*ground_coordinates.y[i].value, 100*ground_coordinates.z[i].value]
            position = translate(coords)(color([0, 0, 1])(sphere(r=800)))
            ground_system.add(position)

    grid = grid_plane(grid_unit=grid_unit,
                      count=2 * int(100 * np.max(np.abs(ground_coordinates.x.value)) / grid_unit),
                      line_weight=200,
                      plane='xy')

    grid = color([0, 0, 1, 0.5])(grid)
    ground_system.add(grid)

    # SYSTEM + ARROW
    ref_arr = ref_arrow_3d(8000, origin=(1000, 1000, 0), label={'x': "x_gnd = NORTH", 'y': "y_gnd = WEST", 'z': "z_gnd"})
    ground_system = ground_system + ref_arr
    return ground_system

