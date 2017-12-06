import Queue
import threading

import sys
sys.path.append('../')

import config as cfg

from common import AvgItem
from common import Controller
from common import bounded
from dispatcher import Dispatcher


class VesperController(Controller):
    VAL_AVG_FPS = 'FPS.avg'
    VAL_FRAME_RATE = 'Frame Rate'
    VAL_T_0 = 'T_o'
    VAL_M_0 = 'M_o'

    DRONE_NAME = 'drone'

    QUEUE_TIMEOUT = 1.0

    def __init__(self):
        Controller.__init__(self)
        self.running = threading.Event()

        self.avg_fps = AvgItem(cfg.EWMA_ALPHA)

        self.metrics = {}

        self.values = {}
        self.values[self.VAL_T_0] = cfg.T_o
        self.values[self.VAL_M_0] = cfg.M_o
        self.values[self.VAL_AVG_FPS] = 0.0

        self.connected = set()
        self.values['connected'] = self.connected

        self.pipeline = 0

        return

    def throughput_constraint(self):
        """Returns throughput constraint."""
        return self.values[self.VAL_T_0]

    def makespan_constraint(self):
        """Returns makespan constraint."""
        return self.values[self.VAL_M_0]

    def start(self):
        """Starts controller thread."""
        self.running.set()
        Controller.start(self)
        return

    def stop(self):
        """Stops controller thread."""
        self.log().info('stopping controller')
        self.running.clear()
        return

    def run(self):
        """Controller thread target."""
        self.log().info('running controller')

        while self.running.is_set():
            try:
                name = self.dispatcher.tokens.get(True, self.QUEUE_TIMEOUT)
            except Queue.Empty:
                continue

            # TODO: Determine if device is usable
            # If not, schedule probe
            if True:
                # Schedule probe
                self.dispatcher.probe(name, self.pipeline)
                continue

            while True:
                # TODO: queue timeout
                timestamp, image = self.dispatcher.imagebuf.get()
                now = time.time()

                if (now - timestamp) > self.makespan_constraint():
                    # Image has expired
                    self.log().debug('image expired')
                    continue
                else:
                    break

            # TODO: Schedule job...


        self.log().info('controller finished')
        return

    def loop(self):
        """Controller action loop."""
        self.log().info('controller loop')

        if self.DRONE_NAME in self.connected:
            # Adjust frame rate
            avg_fps = self.values[self.VAL_AVG_FPS]
            t0 = self.values[self.VAL_T_0]
            ratio = float(t0)/avg_fps

            rate = bounded(t0*ratio, 0.8 * t0, 1.2 * t0)
            self.set_frame_rate(t0 * ratio)

        return

    def logon(self, name):
        """Handles device logon."""
        Controller.logon(self, name)
        self.connected.add(name)

        if name == self.DRONE_NAME:
            self.set_frame_rate(self.values[self.VAL_T_0])

        else:
            self.send_pipeline(name, self.pipeline)

        return

    def logoff(self, name):
        """Handles device logoff."""
        Controller.logoff(self, name)
        self.connected.discard(name)
        return

    def put_metrics(self, metrics):
        """Process system metrics."""
        self.metrics = metrics

        if Dispatcher.ITEM_FPS in metrics:
            fps = metrics[Dispatcher.ITEM_FPS]
            self.avg_fps.add(fps)
            self.values[self.VAL_AVG_FPS] = self.avg_fps.pull()

        self.log().debug('values: %s', self.values)
        return

    def get_values(self):
        """Retrieves controller's data."""
        return self.values

    def set_frame_rate(self, rate):
        """Sets frame rate."""
        params = [
            ('frame_rate', rate),
            ('camera', True)
        ]
        self.send_params(self.DRONE_NAME, params)

        self.values[self.VAL_FRAME_RATE] = rate
        return

    def send_pipeline(self, name, pipeline):
        """Configures device pipeline."""
        params = [
            ('pipeline', pipeline)
        ]

        self.send_params(name, params)
        return
