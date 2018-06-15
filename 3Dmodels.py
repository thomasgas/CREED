from solid import scad_render_to_file
from solid.utils import translate, rotate, union, intersection, hole, multmatrix, difference
from solid.utils import cylinder, color, polygon, circle, sphere, cube, text
import numpy as np

from ctapipe.io import event_source
from ctapipe.calib.camera.dl0 import CameraDL0Reducer
from ctapipe.calib.camera.dl1 import CameraDL1Calibrator
from ctapipe.calib.camera.r1 import HESSIOR1Calibrator
from ctapipe.io import EventSeeker
#from ctapipe.coordinates import HorizonFrame

import astropy.units as u

from camera_event import draw_camera
from utilities import ref_arrow_3d

from telescope_structure import telescope
from telescope_structure import mirror_plane_creator


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

    # source = event_source(
    #    "/home/thomas/Programs/astro/CTAPIPE_DAN/gamma_20deg_180deg_run10651___cta-prod3-merged_desert-2150m-Paranal-subarray-3.simtel-dst0.gz",
    #    allowed_tels=allowed_tels)

    seeker = EventSeeker(source)
    # event_number = 8 # used for GCT-only data
    # event_number = 5   # 3 LST triggered
    # event_number = 1   # MST triggered
    event_number = 26   # 4 LST triggered, with overlap

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
    :return: return
    """
    itel = list(event.r0.tels_with_data)
    subinfo = event.inst.subarray
    sub_arr_trig = event.inst.subarray.select_subarray('sub_trig', itel).to_table()

    x_tel_trig = sub_arr_trig['tel_pos_x'].to('cm').value
    y_tel_trig = sub_arr_trig['tel_pos_y'].to('cm').value
    z_tel_trig = sub_arr_trig['tel_pos_z'].to('cm').value

    label_tel = sub_arr_trig['tel_id']
    tel_names = sub_arr_trig['tel_type']

    point_dir = {'alt': event.mcheader.run_array_direction[1].to('deg'), 'az': event.mcheader.run_array_direction[0].to('deg')}

    array = union()
    index = 0
    itel = [7]

    sub_arr_trig.add_index('tel_id')

    for tel_id in itel:
        index = sub_arr_trig.loc_indices[tel_id]
        if subinfo.tel[tel_id].camera.cam_id == 'FlashCam':
            continue
        print('-------------------------')
        print("tel_id processed: ", tel_id)
        tel_name = tel_names[index]
        camera_display = draw_camera(event=event, itel=tel_id, subarray=subinfo, scale_cam=1.6, tail_cut_bool=True)  #, ref_axis=True)
        origin = (x_tel_trig[index], y_tel_trig[index], z_tel_trig[index])
        tel_struct = telescope(tel_name=tel_name, camera_display_bool=camera_display, pointing=point_dir, origin=origin, tel_num=label_tel[index], ref_camera=True, ref_tel=False, sim_to_real = True)

        array.add(tel_struct)
    return array


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
    :return: the full array
    """
    # select LST telescope with ID=5.
    # event, itel, subinfo = load_calibrate(2)
    event = load_calibrate()
    array = telescope_camera_event(event=event)

    # add MC core x and y
    cross = color([1, 0, 0])(text(text="+", size=1000))
    cross = cross + color([1, 0, 0])(translate([800, 0, 0])(text(text="MC", size=500)))
    array = array + translate([event.mc.core_x.to('cm').value, event.mc.core_y.to('cm').value, 0])(cross)

    # # add ref_frame
    ref_arr = ref_arrow_3d(1000, origin=(1000, 1000, 0), label={'x': "x_gnd = EAST", 'y': "y_gnd = NORTH", 'z': "z_gnd"})
    array = array + ref_arr

    file_out = 'basic_geometry.scad'
    scad_render_to_file(array, file_out)
    # scad_render_to_file(camera_display, file_out)


if __name__ == '__main__':
    main()
