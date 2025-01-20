import time
from src.templates.threadwithstop import ThreadWithStop
from src.utils.messages.allMessages import (SpeedMotor, mainCamera)
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

    def run(self):
        #while self._running:
        self.speed.send("5")
        print("\n\n\n\nan ajuns aici\n\n\n\n\ns")

    def subscribe(self):
        """Subscribes to the messages you are interested in"""
        pass
