from solid import scad_render_to_file
from solid.utils import translate, rotate, union, intersection, hole, multmatrix, difference, linear_extrude
from solid.utils import cylinder, color, polygon, circle, sphere, cube, text, arc
import numpy as np

from ctapipe.io import event_source
from ctapipe.calib.camera.dl0 import CameraDL0Reducer
from ctapipe.calib.camera.dl1 import CameraDL1Calibrator
from ctapipe.calib.camera.r1 import HESSIOR1Calibrator
from ctapipe.io import EventSeeker
from ctapipe.coordinates import HorizonFrame, TiltedGroundFrame, GroundFrame, NominalFrame, CameraFrame, TelescopeFrame

import astropy.units as u

from camera_event import draw_camera
from utilities import ref_arrow_3d, grid_plane, ref_arrow_2d, rot_arrow

from telescope_structure import telescope


def load_calibrate():
    # LOAD AND CALIBRATE
    allowed_tels = [279, 280, 281, 282, 283, 284, 286, 287, 289, 297, 298, 299,
                    300, 301, 302, 303, 304, 305, 306, 307, 308, 315, 316, 317,
                    318, 319, 320, 321, 322, 323, 324, 325, 326, 327, 328, 329,
                    330, 331, 332, 333, 334, 335, 336, 337, 338, 345, 346, 347,
                    348, 349, 350, 375, 376, 377, 378, 379, 380, 393, 400, 402,
                    403, 404, 405, 406, 408, 410, 411, 412, 413, 414, 415, 416,
                    417]

    source = event_source("/home/thomas/Programs/astro/CTAPIPE_DAN/gamma_20deg_180deg_run10651___cta-prod3-merged_desert-2150m-Paranal-subarray-3.simtel-dst0.gz")
    # source = event_source("/home/thomas/Programs/astro/Alice/gamma_20deg_180deg_run1___cta-prod3-demo-2147m-LaPalma-baseline.simtel.gz")
    # source = event_source(
    #    "/home/thomas/Programs/astro/CTAPIPE_DAN/gamma_20deg_180deg_run10651___cta-prod3-merged_desert-2150m-Paranal-subarray-3.simtel-dst0.gz",
    #    allowed_tels=allowed_tels)

    seeker = EventSeeker(source)
    # event_number = 8 # used for GCT-only data
    # event_number = 5   # 3 LST triggered
    # event_number = 1   # MST triggered
    event_number = 26   # 4 LST triggered, with overlap
    # event_number = 9

    event = seeker[event_number]

    source.r1 = HESSIOR1Calibrator()
    source.dl0 = CameraDL0Reducer()
    source.dl1 = CameraDL1Calibrator()
    source.r1.calibrate(event)
    source.dl0.reduce(event)
    source.dl1.calibrate(event)
    return event


def telescope_camera_event(event):
    """
    Plot telescope + camera + event on it (if needed). Loop over all the telescopes with data in an event.
    The function create:
        - camera display with event visualization and arrows
        - telescope frame
        - position every telescope on its right position on ground

    :param event: event selected from simtel file
    :return: return the array to be rendered
    """
    itel = list(event.r0.tels_with_data)
    print("id_telescopes:", itel)
    subinfo = event.inst.subarray
    sub_arr_trig = event.inst.subarray.select_subarray('sub_trig', itel).to_table()

    x_tel_trig = sub_arr_trig['tel_pos_x'].to('cm').value
    y_tel_trig = sub_arr_trig['tel_pos_y'].to('cm').value
    z_tel_trig = sub_arr_trig['tel_pos_z'].to('cm').value

    label_tel = sub_arr_trig['tel_id']
    tel_names = sub_arr_trig['tel_description']

    point_dir = {'alt': event.mcheader.run_array_direction[1].to('deg'), 'az': event.mcheader.run_array_direction[0].to('deg')}

    array = union()
    itel = [3]

    sub_arr_trig.add_index('tel_id')

    for tel_id in itel:
        index = sub_arr_trig.loc_indices[tel_id]
        if subinfo.tel[tel_id].camera.cam_id in ['FlashCam']:
            continue
        print('-------------------------')
        print("tel_id processed: ", tel_id)
        tel_name = tel_names[index]
        camera_display = draw_camera(event=event, itel=tel_id, subarray=subinfo, scale_cam=1.6, tail_cut_bool=True)  #, ref_axis=True)
        origin = (x_tel_trig[index], y_tel_trig[index], z_tel_trig[index])
        tel_struct = telescope(tel_description=tel_name, camera_display_bool=camera_display, pointing=point_dir, origin=origin, tel_num=label_tel[index], ref_camera=True, ref_tel=False, sim_to_real = True)
        array.add(tel_struct)
    array.add(grid_plane())

    return array


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


def mc_details(event):
    """
    append MC details to array. Now only:
        - MC impact point on ground
    :param event:
    :return:
    """
    # add MC core x and y
    cross = text(text="+", size=5000)
    cross = cross + translate([1000, 1000, 0])(text(text="MC", size=1000))
    cross = color([1, 0, 0])(linear_extrude(200)(cross))
    cross = translate([event.mc.core_x.to('cm').value, event.mc.core_y.to('cm').value, 0])(cross)
    return cross


def main():
    """
    Main function to
    - load and calibrate the event from simtel file
    - pass the selected event to create array:
        - camera + event
        - telescope structure
        - tel id (w/o data_after_cleaning: Red (Y) or Green (N))
    - add MC cross on ground
    - add ground ref frame
    :return: the full array plus the MC cross on ground and reference frame + grid for xy-plane
    """
    array = union()
    event = load_calibrate()
    # array.add(telescope_camera_event(event=event))
    array.add(tilted_grid(event=event, tel_pos=False, zen_az_arrows=True))
    array.add(ground_grid(event=event, tel_pos=False))
    array = array + mc_details(event=event)
    file_out = 'basic_geometry.scad'
    scad_render_to_file(array, file_out)


if __name__ == '__main__':
    main()