from src.templates.threadwithstop import ThreadWithStop
from src.utils.messages.allMessages import (mainCamera, serialCamera)
from src.utils.messages.messageHandlerSubscriber import messageHandlerSubscriber
from src.utils.messages.messageHandlerSender import messageHandlerSender
from src.perception.ultralytics.models import YOLO
import base64
import numpy as np
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
        self.subscribe()
        super(threadsignDetection, self).__init__()

        self.camera = messageHandlerSubscriber(self.queuesList, mainCamera, "lastOnly", True)

        self.frameCount = 0

        self.model = YOLO("src/perception/models/best_ncnn_model")

    def run(self):
        while self._running:
            if self.camera.isDataInPipe():
                cam = self.camera.receive()
                self.frameCount += 1

                if self.frameCount % 60 != 0:
                    continue

                self.frameCount = 0

                if not cam:
                    continue

                image_data = base64.b64decode(cam)
                img = np.frombuffer(image_data, dtype=np.uint8)

                print(self.model(img))
