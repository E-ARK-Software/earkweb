import logging

import config.params

def init(name):
    logger = logging.getLogger(name)

    if not logger.handlers:
        logging.basicConfig(filename=config.params.root_dir+'/sip-to-aip-converter.log', level=logging.DEBUG, format='%(asctime)s - %(levelname)s - %(module)s - %(message)s')
        handler = logging.StreamHandler()
        logger.setLevel(logging.DEBUG)
        logger.addHandler(handler)

    return logger

