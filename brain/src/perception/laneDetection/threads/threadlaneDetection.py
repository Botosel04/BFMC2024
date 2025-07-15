import base64

import cv2
import numpy as np
from src.templates.threadwithstop import ThreadWithStop
from src.utils.messages.allMessages import (Pedestrian, laneDetectionSteering, mainCamera, serialCamera, processedCamera, LineInFront)
from src.utils.messages.messageHandlerSubscriber import messageHandlerSubscriber
from src.utils.messages.messageHandlerSender import messageHandlerSender
from src.perception.laneDetection.lane_detection import getSteer

class threadlaneDetection(ThreadWithStop):
    """This thread handles laneDetection.
    Args:
        queueList (dictionary of multiprocessing.queues.Queue): Dictionary of queues where the ID is the type of messages.
        logging (logging object): Made for debugging.
        debugging (bool, optional): A flag for debugging. Defaults to False.
    """

    def __init__(self, queueList, logging, debugging=False):
        self.queuesList = queueList
        self.logging = logging
        self.debugging = debugging
        self.processedCamera = messageHandlerSender(self.queuesList, processedCamera)
        self.subscribe()
        super(threadlaneDetection, self).__init__()

        self.steer = messageHandlerSender(self.queuesList, laneDetectionSteering)
        self.lineInFront = messageHandlerSender(self.queuesList, LineInFront)
        self.camera = messageHandlerSubscriber(self.queuesList, serialCamera, "lastOnly", True)
        self.pedestrian = messageHandlerSender(self.queuesList, Pedestrian)
        
        self.last_angle = 0.0
        self.frameCount = 0

        self.wid = 512

        self.lastLine = False
        self.lastPedestrian = False

        self.lane_roi = [[170, 200], [int(self.wid*0.3), int(self.wid*0.7)]]
        self.pedestrian_roi = [[180, 205], [int(self.wid*0.3), int(self.wid*0.7)]]

        self.roisize = (200 - 170) * (int(self.wid*0.7) - int(self.wid*0.3))

    def run(self):
        while self._running:
            cam = self.camera.receive()

            if cam is not None:
                image_data = base64.b64decode(cam)
                img = np.frombuffer(image_data, dtype=np.uint8)
                image = cv2.imdecode(img, cv2.IMREAD_COLOR)

                #transversal lane detection
                cropped_lane = image[self.lane_roi[0][0]:self.lane_roi[0][1], self.lane_roi[1][0]:self.lane_roi[1][1]]
                self.whiteForLine = self.countWhitePixels(cropped_lane)
                if self.whiteForLine > self.roisize * 0.1:
                    if not self.lastLine:
                        self.lineInFront.send(True)
                        self.lastLine = True
                elif self.lastLine:
                    self.lineInFront.send(False)
                    self.lastLine = False


                #pedestrain detection
                cropped_pedestrian = image[self.pedestrian_roi[0][0]:self.pedestrian_roi[0][1], self.pedestrian_roi[1][0]:self.pedestrian_roi[1][1]]
                pink_count = self.countPinkPixels(cropped_pedestrian)
                if pink_count > 10:
                    if not self.lastPedestrian:
                        self.pedestrian.send(True)
                        self.lastPedestrian = True
                elif self.lastPedestrian:
                    self.pedestrian.send(False)
                    self.lastPedestrian = False

                steer_angle, processed_image, no_of_lines = getSteer(image)

                steer_angle = -steer_angle * 20/3
                if steer_angle > 250:
                    steer_angle = 250
                elif steer_angle < -250:
                    steer_angle = -250
                
                
                if processed_image is not None:
                    _, processed_image_jpg = cv2.imencode(".jpg", processed_image)
                    processed_image_bytes = base64.b64encode(processed_image_jpg).decode("utf-8")
                    self.processedCamera.send(processed_image_bytes)

                

                self.frameCount += 2
                if self.frameCount % 15 == 0:
                    print(steer_angle)
                    print("No. of lines: ", no_of_lines)
                    self.frameCount = 0

                if abs(steer_angle - self.last_angle) > 15:
                    self.steer.send(str(int(steer_angle)))
                    self.last_angle = steer_angle

    def countWhitePixels(self, image):
        #hsv = cv2.cvtColor(image, cv2.COLOR_BGR2HSV)
        lower_red = np.array([220,220,220]) 
        upper_red = np.array([255,255,255])

        imgThreshHigh = cv2.inRange(image, lower_red, upper_red)
        nr_pix = np.sum(imgThreshHigh == 255)
        return nr_pix
    
    def countPinkPixels(self, image):
        lower_pink = np.array([120, 100, 180])  # B, G, R
        upper_pink = np.array([180, 160, 255])

        imgThreshHigh = cv2.inRange(image, lower_pink, upper_pink)
        nr_pix = np.sum(imgThreshHigh == 255)
        return nr_pix



    def subscribe(self):
        """Subscribes to the messages you are interested in"""
        pass
