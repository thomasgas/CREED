import sys
from solid import scad_render_to_file
from solid.utils import translate, rotate, union, intersection, hole, multmatrix, difference, linear_extrude
from solid.utils import cylinder, color, polygon, circle, sphere, cube, text, arc
import numpy as np

from ctapipe.io import event_source
from ctapipe.calib import CameraCalibrator

from camera_event import draw_camera
from utilities import ref_arrow_3d, grid_plane, ref_arrow_2d, rot_arrow

from telescope_structure import telescope
import copy


def load_calibrate(filename):
    # LOAD AND CALIBRATE

    # pwd = "/home/thomas/Programs/astro/CTAPIPE_DAN/"
    # filename = 'gamma_20deg_0deg_run100___cta-prod3-lapalma3-2147m-LaPalma_cone10.simtel.gz'
    # filename = 'gamma_20deg_0deg_run100___cta-prod3_desert-2150m-Paranal-merged.simtel.gz'
    # filename = 'gamma_20deg_0deg_run118___cta-prod3_desert-2150m-Paranal-merged_cone10.simtel.gz'
    # filename = 'gamma_20deg_180deg_run11___cta-prod3_desert-2150m-Paranal-merged_cone10.simtel.gz'

    # layout = np.loadtxt(pwd+'CTA.prod3Sb.3HB9-FG.lis', usecols=0, dtype=int)
    if "Paranal" in filename:
        layout = [4, 5, 6, 11]
        print("PARANAL WITH {0}".format(layout))
    elif "palma" in filename:
        layout = [5, 6, 7, 8]
        print("LAPALMA WITH {0}".format(layout))

    print("Layout telescopes IDs:".format(layout))

    # layout = [279, 280, 281, 282, 283, 284, 286, 287, 289, 297, 298, 299,
    #           300, 301, 302, 303, 304, 305, 306, 307, 308, 315, 316, 317,
    #           318, 319, 320, 321, 322, 323, 324, 325, 326, 327, 328, 329,
    #           330, 331, 332, 333, 334, 335, 336, 337, 338, 345, 346, 347,
    #           348, 349, 350, 375, 376, 377, 378, 379, 380, 393, 400, 402,
    #           403, 404, 405, 406, 408, 410, 411, 412, 413, 414, 415, 416,
    #           417]

    layout = set(layout)

    source = event_source(filename)
    source.max_events = 50
    source.allowed_tels = layout
    events = [copy.deepcopy(event) for event in source]

    cal = CameraCalibrator(None, None, r1_product='HESSIOR1Calibrator', extractor_product='NeighbourPeakIntegrator')
    for event in events:
        cal.calibrate(event)

    # Find "big" event (piece of code from T.V. notebook ...thanks :D )
    events_amplitude = []
    for event in events:
        event_amplitude = 0
        for tel_id in event.r0.tels_with_data:
            if event.dl1.tel[tel_id].image is not None:
                event_amplitude += event.dl1.tel[tel_id].image[0].sum()
        events_amplitude.append(event_amplitude)
    events_amplitude = np.array(events_amplitude)

    mm = events_amplitude.argmax()
    print("event: {0}".format(mm))
    event = events[mm]

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

    point_dir = {'alt': event.mcheader.run_array_direction[1].to('deg'),
                 'az': event.mcheader.run_array_direction[0].to('deg')}

    # create union object for the array
    array = union()

    sub_arr_trig.add_index('tel_id')

    for tel_id in itel:
        index = sub_arr_trig.loc_indices[tel_id]
        if subinfo.tel[tel_id].camera.cam_id in ['CHEC']:
            continue
        print('-------------------------')
        print("tel_id processed: ", tel_id)

        # get telescope name
        tel_name = tel_names[index]

        # add camera (tail_cut_bool=True means that the plotted image is cleaned)
        camera_display = draw_camera(event=event, itel=tel_id,
                                     subarray=subinfo, scale_cam=1.6,
                                     tail_cut_bool=True)

        origin = (x_tel_trig[index], y_tel_trig[index], z_tel_trig[index])
        tel_struct = telescope(tel_description=tel_name,
                               camera_display_bool=camera_display,
                               pointing=point_dir,
                               origin=origin,
                               tel_num=label_tel[index],
                               ref_camera=True,
                               ref_tel=False,
                               sim_to_real=True)
        array.add(tel_struct)

    #array.add(grid_plane())

    return array


def mc_details(event):
    """
    append MC details to array. Now only:
        - MC impact point on ground
    :param event:
    :return:
    """
    # add MC core x and y as a cross
    cross = text(text="+", size=5000)
    cross = cross + translate([1000, 1000, 0])(text(text="MC", size=1000))
    cross = color([1, 0, 0])(linear_extrude(200)(cross))
    cross = translate([event.mc.core_x.to('cm').value, event.mc.core_y.to('cm').value, 0])(cross)
    return cross


def main(filename):
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
    event = load_calibrate(filename)
    array.add(telescope_camera_event(event=event))
    array = array + mc_details(event=event)

    # dimension, origin and label of reference arrow
    ref_arr = ref_arrow_3d(2000,
                           origin=(1000, 1000, 0),
                           label={'x': "x_gnd = NORTH", 'y': "y_gnd = WEST", 'z': "z_gnd"})

    array = array + ref_arr

    if "Paranal" in filename:
        site = "Paranal"
    elif "palma" in filename:
        site = "LaPalma"
    else:
        site = "nosite"

    file_out = 'basic_geometry_4LST_' + site + '.scad'
    scad_render_to_file(array, file_out)


if __name__ == '__main__':
    filename = sys.argv[1]
    main(filename)
