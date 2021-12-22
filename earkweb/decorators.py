#!/usr/bin/env python
# -*- coding: utf-8 -*-
import json
import os

from eatb.utils.datetime import ts_date

from config.configuration import config_path_work
from functools import wraps

import logging


def requires_parameters(*required_params):
    """
    Decorator function to check if required parameters are available in the context object
    :param required_params: parameters tuple
    :raises: RuntimeError if required parameter is not available
    """
    assert isinstance(required_params, tuple)

    def check_parameter(func):
        def func_wrapper(self, input):
            missing_params = []
            if isinstance(input, dict) or (isinstance(input, str) and input.startswith("{")):
                for param in required_params:
                    if param not in input:
                        missing_params.append(param)
                if len(missing_params) > 0:
                    raise ValueError("Missing parameters: %s" % ", ".join(missing_params))
            return func(self, input)
        return func_wrapper
    return check_parameter


def get_task_logger(func, ip_dir):
    """
    Task logger (creates log file in information package directory)
    """
    logfile = os.path.join(ip_dir, "processing.log")
    if not os.path.exists(logfile):
        logging.shutdown()

    logger = logging.getLogger("%s_%s" % (ip_dir, func.__name__))

    extra = {'task_name': func.__name__}
    if len(logger.handlers) == 0:
        # Log to output file based on the function name

        hdlr = logging.FileHandler(logfile)
        formatter = logging.Formatter('%(asctime)s %(task_name)s %(levelname)s %(message)s')
        hdlr.setFormatter(formatter)
        logger.addHandler(hdlr)
        logger.setLevel(logging.INFO)
    logger = logging.LoggerAdapter(logger, extra)
    return logger


def task_logger(f):
    @wraps(f)
    def wrapper(*args, **kwds):
        task = args[0]
        task_input = args[1]
        if isinstance(task_input, str):
            context = json.loads(task_input)
        else:
            context = task_input
        uid = context["uid"]
        ip_dir = os.path.join(config_path_work, uid)
        log_dir = ip_dir
        if not os.path.exists(log_dir):
            os.makedirs(log_dir, exist_ok=True)
        task_log = get_task_logger(f, ip_dir)
        kwds["task_log"] = task_log
        try:
            task_log.info("============ Task %s ============" % task.name)
            input_params = context
            for param, value in input_params.items():
                task_log.debug("Input parameter '%s': %s" % (param, value))
            result = f(*args, **kwds)
            result_params = json.loads(result)
            for param, value in result_params.items():
                task_log.debug("Output parameter '%s': %s" % (param, value))
        except Exception as ex:
            task_log.error("Exception {0}".format(ex))
            raise ex
        return result
    return wrapper
