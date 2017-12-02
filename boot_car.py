#!/usr/bin/env python

import copy
import logging.config

import config as cfg

from car import Dispatcher
from car import VesperController

if __name__ == '__main__':
    # Logging setup
    mylogcfg = copy.deepcopy(cfg.LOGCFG)
    mylogcfg['handlers']['file']['filename'] = 'car_output.log'
    logging.config.dictConfig(mylogcfg)

    log = logging.getLogger('boot_car')

    controller = VesperController()
    dispatcher = Dispatcher(controller)

    log.info('booting car...')
    dispatcher.start()
    dispatcher.stop()
