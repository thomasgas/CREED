from solid.utils import translate, rotate, union, intersection, hole, multmatrix, difference, linear_extrude
from solid.utils import cylinder, color, polygon, circle, sphere, cube, text
from utilities import ref_arrow_3d
from utilities import ref_arrow_2d
from utilities import length
from utilities import rotation
import numpy as np

import astropy.units as u

def arco(x, y, radius):
    """
    Create curve from set of point. Each point is connected with a cylinder
    The curve must be 2D, because I want to perform only rotations along one axis.
    Connect P(x[i],y[i]) and P(x[i+1], y[y+1])
    :param x: np.array with the x points
    :param y: np.array with the "heights"
    :param radius: dimension cylinder
    :return: curve
    """
    # x = list(x)
    # y = list(y)
    arco_sum = union()
    for i in range(x.size - 1):
        begin = (x[i], y[i])
        end = (x[i + 1], y[i + 1])
        angle = np.rad2deg(np.arctan((y[i] - y[i+1])/(x[i] - x[i+1])))

        heigth = length(end, begin)
        new_cylinder = multmatrix(m=rotation(90, 'y'))(cylinder(h=heigth, r=radius))
        new_cylinder = multmatrix(m=rotation(angle, 'z'))(new_cylinder)
        new_cylinder = translate(list(begin))(new_cylinder)
        arco_sum.add(new_cylinder)
    return arco_sum


def struct_spider(height, radius_square_low, radius_square_top):
    """
    Create structure for MST and SST camera with one mirror (FOR THE MOMENT).
    :param height: height between mirror plane and camera plane
    :param radius_square_low: radius in the lower part (mirror plane)
    :param radius_square_top: radius in the upper part (camera plane)
    :return: 4 spider and camera structure
    TODO: how to create 2-mirror telescope structure?
    """
    structure = union()
    sides = 4
    delta_angles = 360./sides

    incl_angle = 90-np.rad2deg(np.arctan(height/(radius_square_low-radius_square_top)))

    spider = cylinder(h=height, r=20)
    spider = multmatrix(m=rotation(incl_angle, 'y'))(spider)
    spider = translate([-radius_square_low+25, 0, 110])(spider)

    for i in range(sides):
        structure = multmatrix(m=rotation(delta_angles, 'z'))(structure)
        structure.add(spider)
    structure = multmatrix(m=rotation(45, 'z'))(structure)
    return structure


def mirror_plane_creator(tel_type, radius):
    """
    Create a fake mirror plane and hole at center
    :param tel_type: select mirror plane type: 'LST', 'MST'
    :param radius: radius of the mirror plane. (e.g.: LST is 11,50 m == 23/2 m)
    :return: mirror_plane with
    """
    if tel_type == 'LST':
        mirror_plane = difference()
        mirror_plane.add(color([1, 0, 0])(sphere(radius)))
        mirror_plane.add(translate([0, 0, 1.6 * radius])(color([0, 0, 1, 0.7])(sphere(radius * 2))))
        cal_box = color([1, 0, 0])(translate([0, 0, -radius])(cylinder(r=radius/6, h=radius*2)))
        mirror_plane.add(cal_box)
    elif tel_type == 'MST':
        # first create a big sphere (to have a big curvature radius), then cut a hole for the calbox
        spheres = difference()
        spheres.add(color([1, 0, 0])(sphere(3*radius)))
        spheres.add(color([0, 0, 1, 0.6])(sphere(3*radius*0.96)))
        cal_box = color([1, 0, 0])(translate([0, 0, -3*radius])(cylinder(r=radius/6, h=radius*2)))
        spheres.add(cal_box)

        # then select only one part of the full sphere
        mirror_plane = intersection()
        mirror_plane.add(spheres)
        sel_region = translate([0, 0, -3*radius])(cylinder(r=radius, h=radius))
        mirror_plane.add(sel_region)

        # finally translate everything at zero
        mirror_plane = translate([0, 0, 3*radius])(mirror_plane)
    return mirror_plane


def telescope(tel_name, camera_display_bool, pointing, origin, tel_num='0', ref_camera=False, ref_tel=False):
    """
    Create telescope. Implemented only 'LST' by now. Everything is somehow in centimeters.
    :param tel_name: string for telescope type. 'LST', 'MST', ecc.
    :param camera_display_bool: input from camera_event.py loaded another event
    :param pointing: dictionary for pointing directions in degrees above horizon, {'alt': val, 'az': val}
    :param origin: (x, y, z) position of the telescope
    :param tel_num: (int) Telescope ID to be plotted with the telescope
    :param ref_camera: (bool) create ref frame on camera
    :param ref_tel: (bool) create ref frame at the center of the telescope...TODO: needed?
    :return: geometry for the telescope.

    TODO: create real substructure for telescope?
    """

    # unpack camera_display values
    bool_trig = camera_display_bool[1]
    if bool_trig:
        color_trig = [1, 0, 0]
    else:
        color_trig = [0, 1, 0]

    camera_display = camera_display_bool[0]

    telescope_struct = union()

    if tel_name == 'LST':
        # create mirror plane
        mirror_plane = mirror_plane_creator(tel_type=tel_name, radius=1150)

        # define arch
        arch = union()
        x_arco = np.linspace(-2200/2, 2200/2, 50)
        y_arco = 4/2300*x_arco**2
        arch_struct = color([1, 0, 0])(arco(x_arco, y_arco, 30))
        arch.add(arch_struct)
        arch = multmatrix(m=rotation(-90, 'x'))(arch)
        arch = translate([0, 0, np.max(y_arco) - 200])(arch)

        # append camera to arch
        cam_struct = cube([400, 400, 190], center=True)
        camera_display = multmatrix(m=rotation(-90, 'z'))(camera_display)
        camera_display = translate([0, 0, -100])(camera_display)
        camera_display = multmatrix(m=rotation(180, 'x'))(camera_display)
        cam_struct = cam_struct + camera_display

        # check for arrows in reference frame
        if ref_camera:
            cam_struct = cam_struct + ref_arrow_2d(500, label={'x': "x_cam", 'y': "y_cam"}, origin=(0, 0), inverted=True)
        arch.add(cam_struct)

        # put together arch and mirror plane
        telescope_struct.add(arch)
        telescope_struct.add(mirror_plane)
        telescope_struct = translate([0, 0, 450])(telescope_struct)
        telescope_struct = multmatrix(m=rotation(-90, 'z'))(telescope_struct)

    elif tel_name == 'MST':
        radius = 600
        height = 1800
        ratio_cam = 2
        mirror_plane = mirror_plane_creator(tel_type=tel_name, radius=radius)
        telescope_struct.add(mirror_plane)

        # add the long spiders to the structure
        structure = struct_spider(height, radius, radius/ratio_cam)

        # create camera structure with ref arrow and overplot the event
        side_cam = 2 * (radius/ratio_cam) / np.sqrt(2)
        camera_frame = cube([side_cam, side_cam, 100], center=True)

        camera_display = multmatrix(m=rotation(-90, 'z'))(camera_display)
        camera_display = translate([0, 0, -60])(camera_display)
        camera_display = multmatrix(m=rotation(180, 'x'))(camera_display)
        camera_frame = camera_frame + camera_display

        # check for arrows in reference frame
        if ref_camera:
            camera_frame = camera_frame + ref_arrow_2d(400, label={'x': "x_cam", 'y': "y_cam"}, origin=(0, 0), inverted=True)

        # rotate camera in order to have x and y in the correct position (y pointing up and x pointing right)
        camera_frame = multmatrix(m=rotation(-90, 'z'))(camera_frame)
        # raise to same level as mirror plane
        camera_frame = translate([0, 0, 110])(camera_frame)

        # raise to top of telescope - some in order to look nicer
        camera_frame = translate([0, 0, height - 30])(camera_frame)
        structure = structure + camera_frame

        # add structure, camera frame and camera on the telescope structure
        telescope_struct.add(structure)
        telescope_struct = translate([0, 0, -150])(telescope_struct)

    # rotate to pointing. First move in ALTITUDE and then in AZIMUTH
    zen = 90 - pointing['alt'].value
    az = pointing['az'].value
    telescope_struct = multmatrix(m=rotation(-zen, 'x'))(telescope_struct)
    telescope_struct = multmatrix(m=rotation(-az, 'z'))(telescope_struct)

    # ADD TELESCOPE ID
    print(tel_num, tel_name)
    tel_number = color(color_trig)(linear_extrude(100)(text(text=str(tel_num), size=10000, spacing=0.1)))
    telescope_struct = translate(list(origin))(telescope_struct)
    telescope_struct = telescope_struct + translate((origin[0]+700, origin[1]+700, 0))(tel_number)


    return telescope_struct