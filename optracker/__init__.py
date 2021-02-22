import sys,os
import pathlib

import logging
logger = logging.getLogger(__name__)
logger.setLevel(level=logging.DEBUG)
os.makedirs('C:/ProgramData/BehavioralObservation', exist_ok=True)
log_path = 'C:/ProgramData/BehavioralObservation/optracker.log'
#log_path = os.path.join(os.path.abspath(os.path.dirname(__file__)), '..', 'optracker.log')
handler = logging.FileHandler(log_path)
handler_format = logging.Formatter('%(asctime)s,%(levelname)s,%(filename)s,%(lineno)s,%(funcName)s(),%(message)s')
handler.setFormatter(handler_format)
logger.addHandler(handler)

## face_tracking.pyはimportでなくプロセスからpython face_tracking.pyで呼ぶ仕様
## importして実行すると2回目以降の処理が失敗する(OpenCVのバグ？)ため
