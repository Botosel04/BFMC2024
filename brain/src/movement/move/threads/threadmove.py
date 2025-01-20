import base64
import time

import cv2
import numpy as np
from src.templates.threadwithstop import ThreadWithStop
from src.utils.messages.allMessages import (DrivingMode, SpeedMotor, mainCamera, serialCamera)
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
        self.driving_mode = messageHandlerSubscriber(self.queuesList, DrivingMode, "lastOnly", True)
        self.camera = messageHandlerSubscriber(self.queuesList, serialCamera, "lastOnly", True)

        self.driveState = True

    def run(self):
        while self._running:
            drv = self.driving_mode.receive()
            cam = self.camera.receive()
            if drv is not None:
                if drv == "auto":
                    self.speed.send("50")
                    print("a")
            if cam is not None:
                image_data = base64.b64decode(cam)
                img = np.frombuffer(image_data, dtype=np.uint8)
                image = cv2.imdecode(img, cv2.IMREAD_COLOR)
                nrPix = self.countRedPixels(image)
                height, width, channels = image.shape
                MP = height*width
                if nrPix > MP/3 and self.driveState:
                    self.speed.send("0")
                    self.driveState = False
                elif not nrPix > MP/3 and self.driveState == False:
                    self.speed.send("50")
                    self.driveState = True
                    


    def countRedPixels(self, image):
        hsv = cv2.cvtColor(image, cv2.COLOR_BGR2HSV)
        lower_red = np.array([160,140,50]) 
        upper_red = np.array([180,255,255])

        imgThreshHigh = cv2.inRange(hsv, lower_red, upper_red)
        nr_pix = np.sum(imgThreshHigh == 255)
        return nr_pix

    def subscribe(self):
        """Subscribes to the messages you are interested in"""
        pass
