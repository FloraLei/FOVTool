import numpy as np

class DummyLP:
    lane_width = 6.0
    line_width = 0.15
    lateral_offset = 0.0
    curvature_r = 700.0
    left_lines = 9
    right_lines = 10
    length = 1000.0
    color_outer = "#FFFFFF"
    color_inner = "#FFCC00"

lp = DummyLP()
y_start = -lp.length / 2.0
y_end = lp.length / 2.0
num_points = max(20, int(abs(y_end - y_start) / 2))
ys = np.linspace(y_start, y_end, num_points)

def get_xs(x_base):
    c = 1.0 / (2.0 * lp.curvature_r) if lp.curvature_r != 0.0 else 0.0
    return x_base + c * ys ** 2

# Let's print the min/max of xs for a few base x values:
print("y_start:", y_start, "y_end:", y_end)
print("c:", 1.0 / (2.0 * lp.curvature_r))

# Outermost left:
x_left_most = lp.lateral_offset - lp.left_lines * lp.lane_width
xs_left = get_xs(x_left_most)
print(f"Left outermost (x_base={x_left_most}): min_x={np.min(xs_left):.2f}, max_x={np.max(xs_left):.2f}")

# Left dividers:
for idx in range(1, lp.left_lines):
    x_base = lp.lateral_offset - idx * lp.lane_width
    xs = get_xs(x_base)
    print(f"Left divider {idx} (x_base={x_base}): min_x={np.min(xs):.2f}, max_x={np.max(xs):.2f}, mid_x (y=0)={xs[len(ys)//2]:.2f}")

# Center divider:
xs_center = get_xs(lp.lateral_offset)
print(f"Center divider (x_base=0.0): min_x={np.min(xs_center):.2f}, max_x={np.max(xs_center):.2f}, mid_x (y=0)={xs_center[len(ys)//2]:.2f}")

# Right dividers:
for idx in range(1, lp.right_lines):
    x_base = lp.lateral_offset + idx * lp.lane_width
    xs = get_xs(x_base)
    print(f"Right divider {idx} (x_base={x_base}): min_x={np.min(xs):.2f}, max_x={np.max(xs):.2f}, mid_x (y=0)={xs[len(ys)//2]:.2f}")

# Outermost right:
x_right_most = lp.lateral_offset + lp.right_lines * lp.lane_width
xs_right = get_xs(x_right_most)
print(f"Right outermost (x_base={x_right_most}): min_x={np.min(xs_right):.2f}, max_x={np.max(xs_right):.2f}")
