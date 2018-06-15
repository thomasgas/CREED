from solid.utils import translate, union
from solid.utils import color, polygon, circle, cylinder
from ctapipe.image import tailcuts_clean
import numpy as np
from solid.utils import multmatrix

from utilities import ref_arrow_2d, rotation

import matplotlib.pyplot as plt

cmap = plt.get_cmap("jet")

tail_cut = {"LSTCam": (8, 16),
            "NectarCam": (7, 14),
            "FlashCam": (7, 14),
            "CHEC": (3, 6)}


def hexagon(center, radius, sides):
    """
    Draw an hexagon based on center and number of sides.
    First point is at (x,y) = (radius, 0)
    :param center: this must bu a tuple with the coordinates x and y
    :param radius: radius of hexagon
    :param sides:
    :return: hexagon

    """
    (center_x, center_y) = center
    points = []
    angles = np.linspace(0., 2.*np.pi, sides+1)
    x = center_x + radius*np.cos(angles)
    y = center_y + radius*np.sin(angles)
    points.extend(np.ndarray.tolist(np.stack((x, y), axis=1)))
    return polygon(points)


def circle_trans(center, radius, height):
    """
    Draw translated circle at *center* and with *radius*
    :param center: tuple (x,y) for the center
    :param radius: radius of pixel element
    :param height: height of camera to be plotted
    :return: the translated circle
    """
    (center_x, center_y) = center
    return translate([center_x, center_y])(cylinder(r=radius, h=height,  segments=8))


def draw_camera(event, itel, subarray, scale_cam=1.0, tail_cut_bool=False):  # ,ref_axis=True):
    """
    Draw camera, either with or without an event. Take info from a simtel file.
    Make camera a list with the second element a boolean which knows if the camera has data after the cleaning.
    :param event: event selected from simtel file.
    :param itel: telescope ID from simtel file. Select only LST IDs for the moment
    :param subarray: subarray info from the simtel file. Needed for the description of the instrument
    :param scale_cam: scale the whole camera to see it better
    :param tail_cut_bool: (bool) decide whether to perform the tailcut
    :return: return camera object to plot on a telescope object
    """
    camera_display = union()

    camera = subarray.tel[itel].camera
    if camera.cam_id == 'LSTCam':
        cam_height = 200
    elif camera.cam_id == 'NectarCam' or camera.cam_id == 'FlashCam':
        cam_height = 120
    print('plotting camera: ', camera.cam_id)

    x_pix_pos = 100 * camera.pix_x.value
    y_pix_pos = 100 * camera.pix_y.value
    side = 1.05*np.sqrt(((x_pix_pos[0] - x_pix_pos[1]) ** 2 + (y_pix_pos[0] - y_pix_pos[1]) ** 2)) / 2

    data_after_cleaning = False

    if tail_cut_bool:
        # Perform tailcut cleaning on image
        pic_th = tail_cut[camera.cam_id][1]
        bound_th = tail_cut[camera.cam_id][1]
        image_cal = event.dl1.tel[itel].image[0]
        max_col = np.max(image_cal)
        mask_tail = tailcuts_clean(camera, image_cal, picture_thresh=pic_th, boundary_thresh=bound_th,
                                   min_number_picture_neighbors=1)

        # set boolean for trigger display on ground
        data_after_cleaning = np.sum(mask_tail) == 0

        for i in range(x_pix_pos.size):
            # camera_display.add((hexagon((x_pix_pos[i],y_pix_pos[i]), side, 6)))
            colore = list(cmap(image_cal[i] * mask_tail[i] / max_col))
            center = (x_pix_pos[i]*scale_cam, y_pix_pos[i]*scale_cam)
            camera_display.add(color(colore)(circle_trans(center=center, radius=side*scale_cam, height=cam_height)))
    else:
        for i in range(x_pix_pos.size):
            # camera_display.add((hexagon((x_pix_pos[i],y_pix_pos[i]), side, 6)))
            colore = [0, 0, 1]
            center = (x_pix_pos[i]*scale_cam, y_pix_pos[i]*scale_cam)
            camera_display.add(color(colore)(circle_trans(center=center, radius=side*scale_cam, height=cam_height)))

    camera_display = camera_display.add(translate([0, 0, cam_height/2])(ref_arrow_2d(400, label={'x': "x_sim", 'y': "y_sim"}, origin=(0, 0))))
    camera_display = multmatrix(m=rotation(180, 'y'))(camera_display)
    camera_display = translate([0, 0, cam_height/2])(camera_display)

    # return also the boolean for the cleaned image
    camera_display_arr = [camera_display, data_after_cleaning]
    return camera_display_arr
