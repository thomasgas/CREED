import numpy as np
from solid.utils import translate, rotate, union, forward, right, up, linear_extrude
from solid.utils import cylinder, color, text, multmatrix, cube


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


def grid_plane(grid_unit=12, count=10, line_weight=0.1, plane='xz'):

    # Draws a grid of thin lines in the specified plane.  Helpful for
    # reference during debugging.
    elle = count * grid_unit
    t = union()
    t.set_modifier('background')
    for i in range(-count // 2, count // 2 + 1):
        if 'xz' in plane:
            # xz-plane
            h = up(i * grid_unit)(cube([elle, line_weight, line_weight], center=True))
            v = right(i * grid_unit)(cube([line_weight, line_weight, elle], center=True))
            t.add([h, v])

        # xy plane
        if 'xy' in plane:
            h = forward(i * grid_unit)(cube([elle, line_weight, line_weight], center=True))
            v = right(i * grid_unit)(cube([line_weight, elle, line_weight], center=True))
            t.add([h, v])

        # yz plane
        if 'yz' in plane:
            h = up(i * grid_unit)(cube([line_weight, elle, line_weight], center=True))
            v = forward(i * grid_unit)(cube([line_weight, line_weight, elle], center=True))
            t.add([h, v])
    return t


def rot_arrow(radius, angle_init, angle_end, label, text_flip=False):
    """
    Create curved arrow as 1 degree-step cylinders with a cone at the end ==> arrow
    Add also a label in the middle of the arrox as a text.
    :param radius: radius is in cm
    :param angle_init: in degrees
    :param angle_end: in degrees
    :param label: label to be given to the arrow
    :param text_flip: rotate text by 180 degrees
    :return: arrow

    example:

    arr_curved = color([1, 0, 0])(rot_arrow(8000, az.to('deg').value,0, label='AZ'))
    array.add(arr_curved)

    """
    curved_arrow = union()
    point = cylinder(r1=radius/15, r2=0, h=radius/8)
    point = rotate([0, -90, -90])(point)

    if angle_end > angle_init:
        angles = np.deg2rad(np.arange(angle_init, angle_end, 1))[1:-5]
        x = radius*np.cos(angles)
        y = radius*np.sin(angles)
        point = rotate([0, 0, np.rad2deg(angles[-2])])(point)
    elif angle_end < angle_init:
        angles = np.deg2rad(np.arange(angle_init, angle_end, -1))[:-5]
        x = radius*np.cos(angles)
        y = radius*np.sin(angles)
        point = rotate([0, 0, np.rad2deg(angles[-2]) + 180])(point)

    curved_body = arco(x, y, radius/30)
    point = translate([x[-2], y[-2], 0])(point)
    curved_arrow.add(point)
    curved_arrow.add(curved_body)
    testo = linear_extrude(radius/30)(text(label, size=radius/5))
    index = x.size//3*2
    testo = rotate([0, 0, np.rad2deg(angles[index])])(testo)
    if text_flip:
        testo = rotate([0, 0, 180])(testo)
        testo = translate([0.15*len(label)*x[index], 0.15*len(label)*y[index], 0])(testo)
    testo = translate([1.1*x[index], 1.1*y[index], 0])(testo)
    curved_arrow.add(testo)
    return curved_arrow


def rotation(angle, axis):
    """
    Calculate 4D rotation matrix to rotate things in space.
    Use of multmatrix from solid package.
    :param angle: in degree
    :param axis: 'x', 'y', 'z'
    :return:
    """
    angle = angle*np.pi/180
    c = np.cos(angle)
    s = np.sin(angle)

    if axis == 'x':
        rot_matrix = [[1, 0, 0, 0], [0, c, -s, 0], [0, s, c, 0], [0, 0, 0, 1]]
    if axis == 'y':
        rot_matrix = [[c, 0, s, 0], [0, 1, 0, 0], [-s, 0, c, 0], [0, 0, 0, 1]]
    if axis == 'z':
        rot_matrix = [[c, -s, 0, 0], [s, c, 0, 0], [0, 0, 1, 0], [0, 0, 0, 1]]

    return rot_matrix


def length(a, b):
    """
    calculate length from two tuples
    :param a: either 1D or 2D tuple
    :param b: either 1D or 2D tuple
    :return: euclidean distance
    """
    a = np.array(list(a))
    b = np.array(list(b))
    dist = np.linalg.norm(a-b)
    return dist


def arrow(heigth, tail, label, rotation=(0, 0, 0)):
    """
    Create arrow with rotation. Default is VERTICAL, along Z-axis
    :param heigth: (float) height
    :param tail:    (tuple) position of tail.
    :param rotation: (tuple) rotation along x, y and z axis
    :param label: something converted to string to put as label on axis
    :return: arrow with label
    TODO: add rotation from rotation function and not with the *rotate* in *solid*
    """
    arrow_inst = union()
    arrow_inst.add(cylinder(r=heigth/20, h=heigth))
    arrow_inst.add(translate([0, 0, heigth])(cylinder(r1=heigth/10, r2=0, h=heigth/8)))
    arrow_inst.add(translate([0, 0, heigth*1.2])(rotate([90, -90, 0])(linear_extrude(heigth/40)(text(text=label, size=heigth/5, font="Cantarell:style=Bold")))))
    arrow_inst = rotate(list(rotation))(arrow_inst)
    arrow_inst = translate(list(tail))(arrow_inst)
    return arrow_inst


def ref_arrow_3d(arr_length, origin, label, ref_rotation=(0, 0, 0)):
    """
    Create 3-axis ref frame, with color for x, y, z
    :param arr_length: length of arrow
    :param origin: set origin of arrows. (x, y, z)
    :param ref_rotation: tuple for rotation
    :param label: dictionary of labels for the three axis. {'x': label_x, 'y': label_y, 'z': label_z}
    :return:
    """
    ref_frame = union()
    ref_frame.add(color([1, 0, 0])(arrow(heigth=arr_length, tail=origin, rotation=(0, 90, 0), label=label['x'])))   # x_axis
    ref_frame.add(color([0, 1, 0])(arrow(heigth=arr_length, tail=origin, rotation=(-90, 0, 0), label=label['y'])))  # y_axis
    ref_frame.add(color([0, 0, 1])(arrow(heigth=arr_length, tail=origin, rotation=(0, 0, 0), label=label['z'])))   # z_axis
    ref_frame = rotate(list(ref_rotation))(ref_frame)
    return ref_frame


def ref_arrow_2d(length, origin, label, ref_rotation=(0, 0), inverted = False):
    """
    Create 3-axis ref frame, with color for x,y
    :param length: length of arrow
    :param label. dictionary of labels for the 2 axis: {'x': label_x, 'y': label_y}
    :param origin: set origin of arrows. (x, y)
    :param ref_rotation: tuple for rotation
    :return: arrow with right text rotation.
    """
    ref_frame = union()
    if inverted:
        ref_frame.add(color([1, 0, 0])(arrow(heigth=length, tail=origin, label=label['x'], rotation=(-90, 180, 0))))  # x_axis
        ref_frame.add(color([0, 1, 0])(multmatrix(m=rotation(90, 'x'))(arrow(heigth=length, tail=origin, label=label['y'], rotation=(0, 90, 0)))))  # y_axis
        ref_frame = rotate(list(ref_rotation))(ref_frame)
    else:
        ref_frame.add(color([1, 0, 0])(multmatrix(m=rotation(-90, 'x'))(arrow(heigth=length, tail=origin, label=label['x'], rotation=(0, 90, 0)))))   # x_axis
        ref_frame.add(color([0, 1, 0])(arrow(heigth=length, tail=origin, label=label['y'], rotation=(-90, 0, 0))))  # y_axis
        ref_frame = rotate(list(ref_rotation))(ref_frame)
    return ref_frame
