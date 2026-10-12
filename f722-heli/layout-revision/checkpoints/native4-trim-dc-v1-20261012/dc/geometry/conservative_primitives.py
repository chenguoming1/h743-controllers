"""Disabled primitive-bound proposal using exact native integer coordinates.

No native export, full-board graph or numerical execution. Raw KiCad polygons
remain evidence; this module constructs separate proven bounds from explicitly
bound primitive parameters. Unsupported geometry fails closed.
"""
from fractions import Fraction as F
from math import isqrt

MODEL = "f722-conservative-integer-primitives-proposal/v1"
FULL_BOARD_INTEGRATION_ENABLED = False


def require(value, message):
    if not value:
        raise ValueError(message)


def cross(a, b, c):
    return (b[0] - a[0]) * (c[1] - a[1]) - (b[1] - a[1]) * (c[0] - a[0])


def hull(points):
    points = sorted(set(points))
    require(len(points) >= 3, "Primitive has no guaranteed area at native resolution")
    lower, upper = [], []
    for p in points:
        while len(lower) >= 2 and cross(lower[-2], lower[-1], p) <= 0:
            lower.pop()
        lower.append(p)
    for p in reversed(points):
        while len(upper) >= 2 and cross(upper[-2], upper[-1], p) <= 0:
            upper.pop()
        upper.append(p)
    result = lower[:-1] + upper[:-1]
    require(len(result) >= 3, "Degenerate guaranteed-area primitive")
    return result


def rotate(p, quarters):
    require(type(quarters) is int and 0 <= quarters < 4, "Only exact orthogonal pad transforms are supported")
    x, y = p
    return [(x, y), (-y, x), (-x, -y), (y, -x)][quarters]


def integer_point(point):
    require(len(point) == 2 and all(type(v) is int for v in point), "Exact native integer-IU coordinates required")
    return tuple(point)


def directions(count):
    # Ordered exact rational unit vectors. Adjacent t=k/count samples obey
    # tan(delta/2)=count/(count**2+k*(k+1)) <= 1/count.
    require(type(count) is int and 2 <= count <= 1024, "Bounded rational sampling count required")
    for quarter in range(4):
        for k in range(count):
            denominator = count * count + k * k
            yield rotate((F(count * count - k * k, denominator), F(2 * count * k, denominator)), quarter)


def grid_box(point):
    def bounds(v):
        floor = v.numerator // v.denominator
        return floor, -((-v.numerator) // v.denominator)
    xs, ys = bounds(F(point[0])), bounds(F(point[1]))
    return [(x, y) for x in xs for y in ys]


def sample_count(radius, budget_IU, rounding_bound_IU):
    require(type(budget_IU) is int and budget_IU > rounding_bound_IU, "Budget must exceed proven rounding bound")
    target = F(radius, 2 * (budget_IU - rounding_bound_IU))
    count = max(2, isqrt(target.numerator // target.denominator))
    while count * count < target:
        count += 1
    require(count <= 1024, "Requested bound exceeds bounded prototype sampling")
    return count


def verify_outer_support(polygon, core_vertices, radius):
    """Every CCW face includes core + radius disk, using exact comparisons."""
    require(len(polygon) >= 3 and all(type(x) is int and type(y) is int for x, y in polygon),
            "Nondegenerate integer outer hull required")
    require(list(map(tuple, polygon)) == hull(polygon), "Canonical nondegenerate CCW outer hull required")
    require(core_vertices and all(type(v) in {int, F} for point in core_vertices for v in point),
            "Nonempty exact analytic core required")
    require(type(radius) in {int, F} and radius >= 0, "Exact nonnegative analytic radius required")
    for a, b in zip(polygon, polygon[1:] + polygon[:1]):
        norm2 = (b[0] - a[0])**2 + (b[1] - a[1])**2
        support = min(cross(a, b, p) for p in core_vertices)
        require(support >= 0 and support * support >= radius * radius * norm2,
                "Constructed outer face excludes analytic primitive")


def circle(radius, count):
    radius = F(radius)
    require(radius > 0, "Positive exact native radius required")
    normals = list(directions(count))
    # Each component magnitude decreases. Squared norm therefore cannot grow.
    inner = hull([(int(radius * x), int(radius * y)) for x, y in normals])
    require(all(x*x + y*y <= radius*radius for x, y in inner), "Inner circle vertex exceeds exact radius")
    boxes = []
    for (a, b), (c, d) in zip(normals, normals[1:] + normals[:1]):
        determinant = a*d - b*c
        require(determinant > 0, "Rational normal ordering differs")
        vertex = (radius * (d-b) / determinant, radius * (a-c) / determinant)
        # These four integer corners enclose the exact tangent intersection.
        boxes.extend(grid_box(vertex))
    outer = hull(boxes)
    verify_outer_support(outer, [(0, 0)], radius)
    error = radius / (2 * count * count) + 2
    verify_outer_support(inner, [(0, 0)], max(F(0), radius - error))
    require(all(x*x + y*y <= (radius + error)**2 for x, y in outer),
            "Constructed outer circle exceeds its proved radius-only budget")
    return inner, outer


def packet(kind, inner, outer, radius, count, rounding_bound, budget):
    deficit = F(radius, 2 * count * count) + rounding_bound
    require(deficit <= budget, "Proven approximation bound exceeds declared budget")
    return {"schema": MODEL, "kind": kind, "coordinates": "integer native IU; 1 IU = 0.000001 mm",
            "inner_IU": inner, "outer_IU": outer,
            "circle_samples_per_quadrant": count,
            "maximum_Hausdorff_deficit_IU_bound": [deficit.numerator, deficit.denominator],
            "requested_budget_IU": budget, "contact_epsilon_IU": 0,
            "raw_native_polygons_modified": False, "full_board_integration_enabled": False,
            "electrical_acceptance_claimed": False}


def capsule(start_IU, end_IU, width_IU, budget_IU=10):
    start, end = integer_point(start_IU), integer_point(end_IU)
    require(type(width_IU) is int and width_IU > 0, "Exact native positive width required")
    radius = F(width_IU, 2)
    count = sample_count(radius, budget_IU, 2)
    inner_circle, outer_circle = circle(radius, count)
    inner = hull([(x+a, y+b) for x, y in [start, end] for a, b in inner_circle])
    outer = hull([(x+a, y+b) for x, y in [start, end] for a, b in outer_circle])
    verify_outer_support(outer, [start, end], radius)
    return packet("circle" if start == end else "straight_capsule", inner, outer, radius, count, 2, budget_IU)


def pad(center_IU, size_IU, shape, quarter_turns=0, corner_radius_IU=None, budget_IU=10):
    center = integer_point(center_IU)
    width, height = integer_point(size_IU)
    require(width > 0 and height > 0, "Positive native pad dimensions required")
    require(shape in {"circle", "rectangle", "oval", "roundrect"}, "Unsupported/custom/chamfered pad shape")
    rotate((0, 0), quarter_turns)
    if shape == "circle":
        require(width == height, "Circle pad size differs")
        return capsule(center, center, width, budget_IU)
    if shape == "rectangle":
        radius = F(0)
    elif shape == "oval":
        radius = F(min(width, height), 2)
    else:
        require(type(corner_radius_IU) is int and 0 < 2*corner_radius_IU <= min(width, height),
                "Actual per-layer native roundrect corner radius required")
        radius = F(corner_radius_IU)
    half_x, half_y = F(width, 2)-radius, F(height, 2)-radius
    actual_core = [rotate((sx*half_x, sy*half_y), quarter_turns) for sx in [-1, 1] for sy in [-1, 1]]
    inner_core = [rotate((sx*int(half_x), sy*int(half_y)), quarter_turns) for sx in [-1, 1] for sy in [-1, 1]]
    count = sample_count(radius, budget_IU, 3)
    if radius:
        inner_circle, outer_circle = circle(radius, count)
    else:
        inner_circle = outer_circle = [(0, 0)]
    inner = hull([(center[0]+x+a, center[1]+y+b) for x, y in inner_core for a, b in inner_circle])
    outer_boxes = []
    for x, y in actual_core:
        for a, b in outer_circle:
            outer_boxes.extend(grid_box((center[0]+x+a, center[1]+y+b)))
    outer = hull(outer_boxes)
    verify_outer_support(outer, [(center[0]+x, center[1]+y) for x, y in actual_core], radius)
    return packet(shape, inner, outer, radius, count, 3, budget_IU)


def exact_convex_contact(first, second):
    """Zero-epsilon closed-set contact for small convex integer polygons."""
    require(3 <= len(first) <= 8192 and 3 <= len(second) <= 8192, "Bounded convex polygons required")
    for polygon in [first, second]:
        require(all(type(x) is int and type(y) is int for x, y in polygon), "Integer contact geometry required")
        require(list(map(tuple, polygon)) == hull(polygon), "Canonical exact convex hull required")
        for a, b in zip(polygon, polygon[1:] + polygon[:1]):
            normal = (a[1]-b[1], b[0]-a[0])
            one = [normal[0]*x + normal[1]*y for x, y in first]
            two = [normal[0]*x + normal[1]*y for x, y in second]
            if max(one) < min(two) or max(two) < min(one):
                return False
    return True
