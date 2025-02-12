import cv2
import numpy as np
import math

leftpoint = -100
rightpoint = 2000
toppoint = 1000, 10
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

def compute_steering_angle(frame, lines, max_angle=50):
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

    return -(steering_angle*250/30)

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

def get_steer(image):
    canny_image = canny(image)
    cropped_image = region_of_interest(canny_image)
    lines = cv2.HoughLinesP(cropped_image, 2, np.pi / 180, 100, np.array([]), minLineLength=100, maxLineGap=30)
    averaged_lines = average_slope_intercept(image, lines)
    steering_angle = compute_steering_angle(image, averaged_lines)
    smoothed = update_smoothed_angle(steering_angle, alpha=0.2)
    final_angle = apply_deadzone(smoothed, threshold=100)
    return final_angle

