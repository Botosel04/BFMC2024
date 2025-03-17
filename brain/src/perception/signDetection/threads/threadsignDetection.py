from typing import Tuple
import cv2
from src.templates.threadwithstop import ThreadWithStop
from src.utils.messages.allMessages import (mainCamera, serialCamera, CrosswalkSign, HighwayEntrySign, HighwayExitSign, NoEntryRoadSign, OneWayRoadSign, ParkingSign, PrioritySign, RoundaboutSign, StopSign)
from src.utils.messages.messageHandlerSubscriber import messageHandlerSubscriber
from src.utils.messages.messageHandlerSender import messageHandlerSender
import base64
import numpy as np
from ultralytics import YOLO

class threadsignDetection(ThreadWithStop):
    """This thread handles signDetection.
    Args:
        queueList (dictionary of multiprocessing.queues.Queue): Dictionary of queues where the ID is the type of messages.
        logging (logging object): Made for debugging.
        debugging (bool, optional): A flag for debugging. Defaults to False.
    """

    def __init__(self, queueList, logging, debugging=False):
        self.queuesList = queueList
        self.logging = logging
        self.debugging = debugging
        super(threadsignDetection, self).__init__()

        self.camera = messageHandlerSubscriber(self.queuesList, mainCamera, "lastOnly", True)

        self.frameCount = 0
        self.model = YOLO("src/perception/models/best_ncnn_model")
        #self.model = YOLO("src/perception/models/best.pt")

        self.cross_walk = messageHandlerSender(self.queuesList, CrosswalkSign)
        self.highway_entry = messageHandlerSender(self.queuesList, HighwayEntrySign)
        self.highway_exit = messageHandlerSender(self.queuesList, HighwayExitSign)
        self.no_entry = messageHandlerSender(self.queuesList, NoEntryRoadSign)
        self.one_way = messageHandlerSender(self.queuesList, OneWayRoadSign)
        self.parking = messageHandlerSender(self.queuesList, ParkingSign)
        self.priority = messageHandlerSender(self.queuesList, PrioritySign)
        self.roundabout = messageHandlerSender(self.queuesList, RoundaboutSign)
        self.stop_sign = messageHandlerSender(self.queuesList, StopSign)

    def run(self):
        while self._running:
            if self.camera.isDataInPipe():
                cam = self.camera.receive()
                self.frameCount += 1

                if self.frameCount % 30 != 0:
                    continue

                self.frameCount = 0

                if not cam:
                    continue

                image_data = base64.b64decode(cam)
                img = np.frombuffer(image_data, dtype=np.uint8)
                image = cv2.imdecode(img, cv2.IMREAD_COLOR)

                detect = self.model(image)
                pred = detect.pop()
                #detectProbs = [[pred.names[int(a)], float(b)] for a, b in list(zip(pred.boxes.cls, pred.boxes.conf))]
                #coords = [[[int(a) for a in sign[0:2]], [int(a) for a in sign[2:4]]] for sign in pred.boxes.data]

                '''
                for name, prob, coord in zip(detectProbs, coords):
                    if name == "Crosswalk":
                        self.send'
                '''

                for i in range(len(pred.boxes.cls)):
                    on_right = (pred.boxes.xyxy[i][0] + pred.boxes.xyxy[i][2]) / 2 > pred.orig_shape[0]
                    if int(pred.boxes.cls[i]) == 0 and on_right:
                        self.cross_walk.send("")
                    elif int(pred.boxes.cls[i]) == 1 and on_right:
                        self.highway_entry.send("")
                    elif int(pred.boxes.cls[i]) == 2 and on_right:
                        self.highway_exit.send("")
                    elif int(pred.boxes.cls[i]) == 3:
                        self.no_entry.send("right" if on_right else "left")
                    elif int(pred.boxes.cls[i]) == 4 and on_right:
                        self.one_way.send("")
                    elif int(pred.boxes.cls[i]) == 5 and on_right:
                        self.parking.send("")
                    elif int(pred.boxes.cls[i]) == 6 and on_right:
                        self.priority.send("")
                    elif int(pred.boxes.cls[i]) == 7 and on_right:
                        self.roundabout.send("")
                    elif int(pred.boxes.cls[i]) == 8 and on_right:
                        self.stop_sign.send("")
