import base64

import cv2
import numpy as np
from src.templates.threadwithstop import ThreadWithStop
from src.utils.messages.allMessages import (SteerMotor, mainCamera, serialCamera)
from src.utils.messages.messageHandlerSubscriber import messageHandlerSubscriber
from src.utils.messages.messageHandlerSender import messageHandlerSender
from src.perception.laneDetection.lane_detection import get_steer

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
        self.subscribe()
        super(threadlaneDetection, self).__init__()

        self.steer = messageHandlerSender(self.queuesList, SteerMotor)
        self.camera = messageHandlerSubscriber(self.queuesList, serialCamera, "lastOnly", True)

    def run(self):
        while self._running:
            cam = self.camera.receive()

            if cam is not None:
                image_data = base64.b64decode(cam)
                img = np.frombuffer(image_data, dtype=np.uint8)
                image = cv2.imdecode(img, cv2.IMREAD_COLOR)

                steer_angle = get_steer(image)
                steer_angle = steer_angle*2
                if steer_angle > 250:
                    steer_angle = 250
                print(steer_angle)
                self.steer.send(str(int(steer_angle)))

    def subscribe(self):
        """Subscribes to the messages you are interested in"""
        pass
