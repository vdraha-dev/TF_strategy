import logging
import logging.config

import yaml

with open("logging_config.yaml") as f:
    config = yaml.safe_load(f)
    logging.config.dictConfig(config)
