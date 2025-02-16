import cv2
import numpy as np
import math

## leftpoint = -100
leftpoint = -50
## rightpoint = 2100
rightpoint = 562
## toppoint = 1000, 250
toppoint = 256, 15
smoothed_angle = 0.0

def apply_deadzone(angle, threshold=5):
    if abs(angle) < threshold:
        return 0
    return angle

def update_smoothed_angle(new_angle, alpha=0.2):
    global smoothed_angle
    # Exponential moving average: new_smoothed = alpha * new_angle + (1 - alpha) * old_smoothed
    smoothed_angle = alpha * new_angle + (1 - alpha) * smoothed_angle
    return smoothed_angle

def compute_steering_angle(frame, lines, max_angle=25):
    height, width, _ = frame.shape

    if lines is None or len(lines) == 0:
        return 0

    lane_center = 0
    if len(lines) == 2:
        left_line, right_line = lines
        left_bottom_x = left_line[0] 
        right_bottom_x = right_line[0]  
        lane_center = (left_bottom_x + right_bottom_x) / 2.0
    elif len(lines) == 1:
        line = lines[0]
        x1, y1, x2, y2 = line
        bottom_x = x1 if y1 > y2 else x2
        lane_center = bottom_x

    frame_center = width / 2.0
    error_pixels = lane_center - frame_center

    angle_radian = math.atan(error_pixels / height)
    angle_degree = angle_radian * 180.0 / math.pi

    steering_angle = max(-max_angle, min(max_angle, angle_degree))

    return -(steering_angle*250/25)

def make_coordinates(image, line_parameters):
    slope, intercept = line_parameters
    y1 = image.shape[0]
    y2 = int(y1 * (3 / 5))
    x1 = int((y1 - intercept) / slope)
    x2 = int((y2 - intercept) / slope)

    return np.array([x1, y1, x2, y2])

def average_slope_intercept(lane_image, lines):
    left_fit = []
    right_fit = []

    if lines is None:
        return None

    for line in lines:
        x1, y1, x2, y2 = line.reshape(4)
        parameters = np.polyfit((x1, x2), (y1, y2), 1)
        slope = parameters[0]
        intercept = parameters[1]

        if slope < 0:
            left_fit.append((slope, intercept))
        else:
            right_fit.append((slope, intercept))

    left_line, right_line = None, None

    if left_fit:
        left_fit_average = np.average(left_fit, axis=0)
        left_line = make_coordinates(lane_image, left_fit_average)

    if right_fit:
        right_fit_average = np.average(right_fit, axis=0)
        right_line = make_coordinates(lane_image, right_fit_average)

    lines_to_draw = []
    if left_line is not None:
        lines_to_draw.append(left_line)
    if right_line is not None:
        lines_to_draw.append(right_line)

    return np.array(lines_to_draw) if lines_to_draw else None

def canny(image):
    gray = cv2.cvtColor(image, cv2.COLOR_RGB2GRAY)
    blur = cv2.GaussianBlur(gray, (5, 5), 0)
    canny = cv2.Canny(blur, 150, 300)
    return canny

def region_of_interest(image):
    height = image.shape[0]
    polygons = np.array([[(leftpoint, height), (rightpoint, height), toppoint]])
    mask = np.zeros_like(image)
    cv2.fillPoly(mask, polygons, 255)
    masked_image = cv2.bitwise_and(image, mask)
    return masked_image


# Cenipili
##########################################################################
def compute_vanishing_point_angle(frame, lines):
    """
    Computes the steering angle (in degrees) using the vanishing point method.
    If both lane lines are detected, it computes their intersection (vanishing point)
    and then computes the angle between the vertical line (from bottom center of frame)
    and the line connecting bottom center to the vanishing point.
    
    If only one line is detected, it falls back to a simpler method.
    """
    height, width, _ = frame.shape

    # Fallback if no line is detected.
    if lines is None or len(lines) == 0:
        return 0

    # When two lane lines are detected, compute their intersection.
    if len(lines) >= 2:
        # Assume the first two lines are the left and right lanes.
        # (You might want to refine how you choose these.)
        left_line = lines[0]
        right_line = lines[1]

        # Fit each line to y = m*x + b using its endpoints.
        # For left_line: (x1, y1, x2, y2)
        m1, b1 = np.polyfit([left_line[0], left_line[2]], [left_line[1], left_line[3]], 1)
        m2, b2 = np.polyfit([right_line[0], right_line[2]], [right_line[1], right_line[3]], 1)

        # To find the intersection:
        # m1*x + b1 = m2*x + b2  ->  x = (b2 - b1) / (m1 - m2)
        if (m1 - m2) == 0:
            # Parallel lines; fallback to simple method.
            return simple_steering_angle(frame, lines)
        x_intersect = (b2 - b1) / (m1 - m2)
        y_intersect = m1 * x_intersect + b1

        # The vanishing point is (x_intersect, y_intersect)
        # Bottom center of frame (assumed car's current heading) is:
        bottom_center = (width / 2, height)

        # Compute offsets from bottom center to the vanishing point:
        dx = x_intersect - bottom_center[0]
        dy = bottom_center[1] - y_intersect  # note: y decreases as we go up

        # Compute angle using arctan: a positive angle means steering right, negative means left.
        angle_rad = np.arctan2(dx, dy)
        angle_deg = np.degrees(angle_rad)
        return angle_deg

    else:
        # If only one line is detected, fallback to a simpler method.
        return simple_steering_angle(frame, lines)


def simple_steering_angle(frame, lines, max_angle=30):
    """
    Fallback method: when only one lane line is detected, use its bottom position relative to
    the image center to compute an angle.
    """
    height, width, _ = frame.shape
    line = lines[0]
    x1, y1, x2, y2 = line
    bottom_x = x1 if y1 > y2 else x2
    lane_center = bottom_x
    frame_center = width / 2.0
    error_pixels = lane_center - frame_center
    normalized_error = error_pixels / (width / 2.0)
    steering_angle = normalized_error * max_angle
    return steering_angle
#####################################################################################
def display_lines(image, lines):
    line_image = np.zeros_like(image)
    if lines is not None:
        for line in lines:
            # Skip if line is None
            if line is None:
                continue
            try:
                # Ensure line is a numpy array
                line = np.array(line)
                # Check if we have exactly four elements
                if line.size != 4:
                    print("Skipping line due to unexpected shape:", line)
                    continue
                # Convert to integers
                x1, y1, x2, y2 = map(int, line.flatten())
                # Draw the line
                cv2.line(line_image, (x1, y1), (x2, y2), (0, 0, 255), 10)
            except Exception as e:
                print("Error drawing line:", line, e)
                continue
    return line_image

def get_steer(image):
    canny_image = canny(image)
    cropped_image = region_of_interest(canny_image)
    ## lines = cv2.HoughLinesP(cropped_image, 2, np.pi / 180, 300, np.array([]), minLineLength=100, maxLineGap=30)
    #lines = cv2.HoughLinesP(cropped_image, 2, np.pi / 180, 100, np.array([]), minLineLength=50, maxLineGap=30)
    lines = cv2.HoughLinesP(cropped_image, 2.3, np.pi / 180, 120, np.array([]), minLineLength=50, maxLineGap=30)
    averaged_lines = average_slope_intercept(image, lines)
    steering_angle = compute_steering_angle(image, averaged_lines)
    smoothed = update_smoothed_angle(steering_angle, alpha=0.2)
    ## final_angle = apply_deadzone(smoothed, threshold=3)
    final_angle = apply_deadzone(smoothed, threshold=30)
    # TODO: remove this during competition
    line_image = display_lines(image, averaged_lines)
    combo_image = cv2.addWeighted(image, 0.8, line_image, 1, 1)

    return final_angle, combo_image

