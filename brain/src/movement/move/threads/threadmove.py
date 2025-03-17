import base64
import time

import cv2
import numpy as np
from src.templates.threadwithstop import ThreadWithStop
from src.utils.messages.allMessages import (DrivingMode, SpeedMotor, SteerMotor, laneDetectionSteering, LineInFront)
from src.utils.messages.allMessages import (StopSign, PrioritySign, HighwayEntrySign, HighwayExitSign, ParkingSign, CrosswalkSign, NoEntryRoadSign, OneWayRoadSign, RoundaboutSign)
from src.utils.messages.messageHandlerSubscriber import messageHandlerSubscriber
from src.utils.messages.messageHandlerSender import messageHandlerSender
class threadmove(ThreadWithStop):
    """This thread handles move.
    Args:
        queueList (dictionary of multiprocessing.queues.Queue): Dictionary of queues where the ID is the type of messages.
        logging (logging object): Made for debugging.
        debugging (bool, optional): A flag for debugging. Defaults to False.
    """

    NORMAL_SPEED = "200"
    HIGHWAY_SPEED = "400"

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
        self.line_in_front = messageHandlerSubscriber(self.queuesList, LineInFront, "lastOnly", True)
        self.highway_enter = messageHandlerSubscriber(self.queuesList, HighwayEntrySign, "lastOnly", True)
        self.highway_exit = messageHandlerSubscriber(self.queuesList, HighwayExitSign, "lastOnly", True)


        self.stop_sign = messageHandlerSubscriber(self.queuesList, StopSign, "lastOnly", True)
        self.cross_walk_sign = messageHandlerSubscriber(self.queuesList, CrosswalkSign, "lastOnly", True)


        self.driveMode = "stop"
        self.driveState = True

        self.citySpeed = [200, 400]
        self.highwaySpeed = [400, 600]

        self.sawStop = False
        self.passingStop = False

        self.onHighway = False
        self.intersection = 'none'
        

        self.currentSpeed = threadmove.NORMAL_SPEED

    def run(self):
        while self._running:
            drv = self.driving_mode.receive()
            if drv is not None:
                if drv == "auto":
                    print("Driving mode set to auto")
                    self.speed.send("100")
                    self.driveMode = drv
                elif drv in ["manual", "legacy", "stop"]:
                    self.speed.send("0")
                    self.steer.send("0")
                    self.driveMode = drv
                    print("Driving mode changed from auto")
            if self.driveMode == 'auto':
                steer_angle = self.lane_detection_steering.receive()
                if steer_angle:
                    self.steer.send(steer_angle)

                targetSpeed = self.currentSpeed
                highwayEnter = self.highway_enter.receive()
                highwayExit = self.highway_exit.receive()
                if not self.onHighway and highwayEnter:
                    self.onHighway = True
                    targetSpeed = threadmove.HIGHWAY_SPEED
                if self.onHighway and highwayExit:
                    self.onHighway = False
                    targetSpeed = threadmove.NORMAL_SPEED
                lineInFront = self.line_in_front.receive()
                stopSign = self.stop_sign.receive()

                if stopSign:
                    if not self.passingStop:
                        print("SAW STOP")
                        self.sawStop = True

                if lineInFront is not None:
                    if lineInFront and self.sawStop:
                        print("STOPPING")
                        targetSpeed = "0"
                        self.sawStop = False
                        time.sleep(1)
                        self.passingStop = True
                    if not lineInFront and self.passingStop:
                        self.passingStop = False

                if self.currentSpeed !
                self.speed.send(self.currentSpeed)


    def subscribe(self):
        """Subscribes to the messages you are interested in"""
        pass

