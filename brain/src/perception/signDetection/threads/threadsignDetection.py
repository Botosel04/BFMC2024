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

        self.camera = messageHandlerSubscriber(self.queuesList, serialCamera, "lastOnly", True)

        self.frameCount = 0
        self.model = YOLO("src/perception/models/best_ncnn_model")
        #self.model = YOLO("src/perception/models/best.pt")
        self.confList = [0.0, 0.3, 0.7, 0.8, 0.0, 0.5, 0.9, 0.8, 0.3]

        self.events = [messageHandlerSender(self.queuesList, CrosswalkSign), messageHandlerSender(self.queuesList, HighwayEntrySign), messageHandlerSender(self.queuesList, HighwayExitSign), messageHandlerSender(self.queuesList, NoEntryRoadSign), messageHandlerSender(self.queuesList, OneWayRoadSign), messageHandlerSender(self.queuesList, ParkingSign), messageHandlerSender(self.queuesList, PrioritySign), messageHandlerSender(self.queuesList, RoundaboutSign), messageHandlerSender(self.queuesList, StopSign)]

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
                w, h, _ = image.shape

                detect = self.model(image)
                pred = detect.pop()
                detectProbs = [[pred.names[int(a)], int(b), float(c)] for a, b, c in list(zip(pred.boxes.cls, pred.boxes.cls, pred.boxes.conf))]
                coords = [[[int(a) for a in sign[0:2]], [int(a) for a in sign[2:4]]] for sign in pred.boxes.data]

                print(detectProbs)
                '''
                for coord in coords:
                    ss, dj = coord
                    ss = [ss[0]/w, ss[1]/h]
                    dj = [dj[0]/w, dj[1]/h]
                    print(ss, dj)'
                '''
                for prob, box in zip(detectProbs, coords):
                    name, tag, conf = prob
                    on_right = (box[0][0] + box[1][0]) / 2 > pred.orig_shape[0]
                    message = "right" if on_right else "left"
                    if conf >= self.confList[tag]:
                        self.events[tag].send(message)