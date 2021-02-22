import sys,os
import importlib
not_installed_modules = []
loader = importlib.find_loader('cv2')
if loader is None:
    not_installed_modules.append('cv2')
loader = importlib.find_loader('pandas')
if loader is None:
    not_installed_modules.append('pandas')
if len(not_installed_modules) > 0:
    raise ModuleNotFoundError('{}'.format(', '.join(not_installed_modules)))

import logging
logger = logging.getLogger(__name__)
logger.setLevel(level=logging.DEBUG)
os.makedirs('C:/ProgramData/BehavioralObservation', exist_ok=True)
log_path = 'C:/ProgramData/BehavioralObservation/mevent.log'
#log_path = os.path.join(os.path.abspath(os.path.dirname(__file__)), '..', 'mevent.log')
handler = logging.FileHandler(log_path)
handler_format = logging.Formatter('%(asctime)s,%(levelname)s,%(filename)s,%(lineno)s,%(funcName)s(),%(message)s')
handler.setFormatter(handler_format)
logger.addHandler(handler)

from mevent.mevent_editor import *
from mevent.vcap_mevent import *
from mevent.file_proc import *
from mevent.parse_comment import *

