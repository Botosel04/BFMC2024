import base64
import time

import cv2
import numpy as np
from src.templates.threadwithstop import ThreadWithStop
from src.utils.messages.allMessages import (DrivingMode, SpeedMotor, SteerMotor, laneDetectionSteering)
from src.utils.messages.messageHandlerSubscriber import messageHandlerSubscriber
from src.utils.messages.messageHandlerSender import messageHandlerSender
class threadmove(ThreadWithStop):
    """This thread handles move.
    Args:
        queueList (dictionary of multiprocessing.queues.Queue): Dictionary of queues where the ID is the type of messages.
        logging (logging object): Made for debugging.
        debugging (bool, optional): A flag for debugging. Defaults to False.
    """

    def __init__(self, queueList, logging, debugging=False):
        self.queuesList = queueList
        self.logging = logging
        self.debugging = debugging
        self.subscribe()
        super(threadmove, self).__init__()

        self.speed = messageHandlerSender(self.queuesList, SpeedMotor)
        self.steer = messageHandlerSender(self.queuesList, SteerMotor)
        self.driving_mode = messageHandlerSubscriber(self.queuesList, DrivingMode, "lastOnly", True)
        self.lane_detection_steering = messageHandlerSubscriber(self.queuesList, laneDetectionSteering, "lastOnly", True)

        self.driveMode = "stop"
        self.driveState = True

        self.citySpeed = [200, 400]
        self.highwaySpeed = [400, 600]

    def run(self):
        while self._running:
            drv = self.driving_mode.receive()
            if drv is not None:
                if drv == "auto":
                    self.speed.send("500")
                    self.driveMode = drv
                    print("Driving mode set to auto")
                elif drv in ["manual", "legacy", "stop"]:
                    self.speed.send("0")
                    self.steer.send("0")
                    self.driveMode = drv
                    print("Driving mode changed from auto")

            steer_angle = self.lane_detection_steering.receive()
            if steer_angle:
                self.steer.send(steer_angle)

    def countWhitePixels(self, image):
        hsv = cv2.cvtColor(image, cv2.COLOR_BGR2HSV)
        lower_red = np.array([200,200,200]) 
        upper_red = np.array([255,255,255])

        imgThreshHigh = cv2.inRange(hsv, lower_red, upper_red)
        nr_pix = np.sum(imgThreshHigh == 255)
        return nr_pix

    def subscribe(self):
        """Subscribes to the messages you are interested in"""
        pass
