from solid.utils import translate, union
from solid.utils import color, polygon, circle, cylinder
from ctapipe.image import tailcuts_clean
import numpy as np


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


def circle_trans(center, radius):
    """
    Draw translated circle at *center* and with *radius*
    :param center: tuple (x,y) for the center
    :param radius:
    :return: the translated circle
    """
    (center_x, center_y) = center
    return translate([center_x, center_y])(cylinder(r=radius, h=200,  segments=10))


def draw_camera(event, itel, subarray, scale_cam = 1.0, flip=False, tail_cut_bool=False):  # ,ref_axis=True):
    """
    Draw camera, either with or without an event. Take info from a simtel file.
    :param event: event selected from simtel file.
    :param itel: telescope ID from simtel file. Select only LST IDs for the moment
    :param subarray: subarray info from the simtel file. Needed for the description of the instrument
    :param scale: scale the whole camera to see it better
    :param tail_cut_bool: (bool) decide whether to perform the tailcut
    :return: return camera object to plot on a telescope object
    """
    camera_display = union()

    camera = subarray.tel[itel].camera
    x_pix_pos = 100 * camera.pix_x.value
    y_pix_pos = 100 * camera.pix_y.value

    side = 1.05*np.sqrt(((x_pix_pos[0] - x_pix_pos[1]) ** 2 + (y_pix_pos[0] - y_pix_pos[1]) ** 2)) / 2

    if flip:
        x_pix_pos, y_pix_pos = y_pix_pos, x_pix_pos

    if tail_cut_bool:
        # Perform tailcut cleaning on image

        pic_th = tail_cut[camera.cam_id][1]
        bound_th = tail_cut[camera.cam_id][1]
        image_cal = event.dl1.tel[itel].image[0]
        max_col = np.max(image_cal)
        mask_tail = tailcuts_clean(camera, image_cal, picture_thresh=pic_th, boundary_thresh=bound_th,
                                   min_number_picture_neighbors=1)

        for i in range(x_pix_pos.size):
            # camera_display.add((hexagon((x_pix_pos[i],y_pix_pos[i]), side, 6)))
            colore = list(cmap(image_cal[i] * mask_tail[i] / max_col))
            center = (x_pix_pos[i]*scale_cam, y_pix_pos[i]*scale_cam)
            camera_display.add(color(colore)(circle_trans(center, side*scale_cam)))
    else:
        for i in range(x_pix_pos.size):
            # camera_display.add((hexagon((x_pix_pos[i],y_pix_pos[i]), side, 6)))
            colore = [0, 0, 1]
            center = (x_pix_pos[i]*scale_cam, y_pix_pos[i]*scale_cam)
            camera_display.add(color(colore)(circle_trans(center, side*scale_cam)))

    # point_ref_frame = {'scale': side, 'origin': (np.max(x_pix_pos), np.max(y_pix_pos),0)}

    # if ref_axis:
    #    camera_display.add(ref_arrow_3d(point_ref_frame['scale'] * 10, point_ref_frame['origin']))

    return camera_display
