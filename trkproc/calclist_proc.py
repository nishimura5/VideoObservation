import pathlib
import traceback
import glob

from trkproc import logger

class CalclistList:
    def __init__(self, tar_dir_path, trk_path):
        try:
            trk_path = pathlib.Path(trk_path)
            tar_dir_path = pathlib.Path(tar_dir_path)

            suffix = trk_path.stem.split('_')[-1]
            if suffix == 'body':
                search_code = '*_body.calclist'
            else:
                search_code = '*_face.calclist'
            self.file_list = glob.glob(str(tar_dir_path.joinpath(search_code)))
            logger.debug('file_list={}'.format(self.file_list))
        except Exception as e:
            logger.error(self._traceback_parser(e))
            raise Exception(e)

    def gen_calclist_dict(self):
        try:
            dst_dict = {}
            for file_path in self.file_list:
                with open(file_path, 'r', encoding='UTF-8') as f:
                    comment = f.readline()
                if comment[0:9] != ';comment=':
                    continue
                else:
                    title = comment[9:].strip()
                file_name = pathlib.Path(file_path).name
                logger.debug('dst_dict[{}] = {}'.format(file_name, title))
                dst_dict[file_name] = title
            logger.debug(dst_dict)
        except Exception as e:
            logger.error(self._traceback_parser(e))
            raise Exception(e)
        return dst_dict

    def _traceback_parser(self, e):
        line = traceback.format_tb(e.__traceback__)[0].split(', ')[1]
        return '{},{}'.format(line, e)


