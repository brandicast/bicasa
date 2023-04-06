from config_setup import *
import logging
import logging.config


try:
    logging.config.fileConfig(
        fname=config["logging"]["config_file"], disable_existing_loggers=False)
except:
    print("Initialize logging error")


logger = logging.getLogger(__name__)
