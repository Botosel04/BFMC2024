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

        self.driveMode = "stop"
        self.driveState = True

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
                    self.speed.send(self.currentSpeed)
                    self.speed.send(self.currentSpeed)
                    self.driveMode = drv
                elif drv in ["manual", "legacy", "stop"]:
                    self.speed.send("0")
                    self.speed.send("0")
                    self.steer.send("0")
                    self.steer.send("0")
                    self.driveMode = drv
                    print("Driving mode changed from auto")
            
            if self.driveMode == 'manual':
                self.speed.send('100')
                self.speed.send('100')
                self.steer.send('-170')
                self.steer.send('-170')
                time.sleep(7)
                self.steer.send('0')
                self.steer.send('0')
                self.speed.send('0')
                self.speed.send('0')
                self.driveMode = 'stop'

            if self.driveMode == 'auto':
                steer_angle = self.lane_detection_steering.receive()
                if steer_angle:
                    self.steer.send(steer_angle)

                targetSpeed = self.currentSpeed

                highwayEnter = False
                highwayExit = False
                if self.highway_enter.isDataInPipe():
                    highwayEnter = self.highway_enter.receive()
                if self.highway_exit.isDataInPipe():
                    highwayExit = self.highway_exit.receive()
                if not self.onHighway and highwayEnter:
                    print("ENTERED HIGHWAY")
                    self.onHighway = True
                    targetSpeed = threadmove.HIGHWAY_SPEED
                if self.onHighway and highwayExit:
                    print("EXITED HIGHWAY")
                    self.onHighway = False
                    targetSpeed = threadmove.NORMAL_SPEED
                
                

                if self.stop_sign.isDataInPipe():
                    stopSign = self.stop_sign.receive()
                    if stopSign:
                        if not self.passingStop:
                            print("SAW STOP")
                            self.sawStop = True

                if self.line_in_front.isDataInPipe():
                    lineInFront = self.line_in_front.receive()
                    if lineInFront is not None:
                        if lineInFront and self.sawStop:
                            print("STOPPING")
                            self.speed.send("0")
                            self.speed.send("0")
                            self.sawStop = False
                            time.sleep(3)
                            self.speed.send(self.currentSpeed)
                            self.speed.send(self.currentSpeed)
                            self.passingStop = True
                        if not lineInFront and self.passingStop:
                            print("LEFT STOP")
                            self.passingStop = False

                if self.currentSpeed != targetSpeed:
                    print("CHANGED SPEED")
                    self.currentSpeed = targetSpeed
                    self.speed.send(self.currentSpeed)
                    self.speed.send(self.currentSpeed)

    def subscribe(self):
        """Subscribes to the messages you are interested in"""
        self.driving_mode = messageHandlerSubscriber(self.queuesList, DrivingMode, "lastOnly", True)
        self.lane_detection_steering = messageHandlerSubscriber(self.queuesList, laneDetectionSteering, "lastOnly", True)
        self.line_in_front = messageHandlerSubscriber(self.queuesList, LineInFront, "lastOnly", True)
        self.highway_enter = messageHandlerSubscriber(self.queuesList, HighwayEntrySign, "lastOnly", True)
        self.highway_exit = messageHandlerSubscriber(self.queuesList, HighwayExitSign, "lastOnly", True)
        self.stop_sign = messageHandlerSubscriber(self.queuesList, StopSign, "lastOnly", True)
        self.cross_walk_sign = messageHandlerSubscriber(self.queuesList, CrosswalkSign, "lastOnly", True)


