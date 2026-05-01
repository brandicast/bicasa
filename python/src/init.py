from config_reader import *
import logging
import logging.config


try:
    logging_conf_path = str(BASE_DIR / config["logging"]["config_file"])
    logging.config.fileConfig(
        fname=logging_conf_path, disable_existing_loggers=False)
except:
    print("Initialize logging error")


logger = logging.getLogger(__name__)
