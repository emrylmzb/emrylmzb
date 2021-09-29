from time import time
from twisted.internet import task
from scrapy.utils.signal import send_catch_log


class ClockSignal(object):
    def __init__(self, interval=1.0):
        self.ts = time()
        self.loop = task.LoopingCall(self.callback)
        self.loop.start(interval)

    def __call__(self, interval):
        self.loop.stop()
        self.loop.start(interval)

    def __del__(self):
        self.loop.stop()
        return super(ClockSignal, self).__del__()

    def callback(self):
        now = time()
        delta = round(now - self.ts)
        send_catch_log(self, self, delta=delta)
        self.ts = now

clock_signal = ClockSignal()
