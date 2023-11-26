import logging

formatter = logging.Formatter(fmt='%(asctime)s - %(name)s - %(levelname)s - %(message)s', datefmt='%Y-%m-%d %H:%M:%S')

handler = logging.StreamHandler()
handler.setFormatter(formatter)

logger = logging.getLogger("pyvalor")
logger.setLevel(logging.DEBUG)
logger.addHandler(handler)