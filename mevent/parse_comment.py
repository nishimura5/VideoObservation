import pathlib
import sys

import pandas as pd

#dir_path = pathlib.Path(__file__).resolve().parent.parent
#sys.path.append(str(dir_path))
from mevent import mevent_editor
from mevent import logger

## comment style
## begin/end + n

class ParseComment:
    def __init__(self):
        pass

    def load(self, tar_path):
        logger.info(tar_path)
        md = mevent_editor.MeventEditor()
        md.load(tar_path)
        self.mevent_df = md.gen_event_df()

    ## event_idの範囲外のrectを削除する
    def select_event_id(self, event_id):
        event_df = self.mevent_df[self.mevent_df['event_id']==event_id]
        begin = event_df['frame'].min()
        end = event_df['frame'].max()
        self.mevent_df = self.mevent_df[self.mevent_df['frame'] > begin]
        self.mevent_df = self.mevent_df[self.mevent_df['frame'] < end]

    def gen_rect_info(self, tar_id, member_num):
        logger.debug('++')
        try:
            rect_info = []

            tar_df = self.mevent_df[self.mevent_df['event_id']==tar_id]
            for i in range(member_num):
                name_df = tar_df[tar_df['comment'].str.contains('{}'.format(i))]
                begin_df = name_df[name_df['comment'].str.contains('begin')]
                end_df = name_df[name_df['comment'].str.contains('end')]
                if len(begin_df) != len(end_df):
                    logger.warning('{}: {} != {}'.format(i, len(begin_df), len(end_df)))
                new_df = pd.concat([begin_df.reset_index(), end_df.reset_index()], axis=1)
                frames = new_df['frame'].to_numpy()
                frames = [{'left':x[0], 'right':x[1], 'width':x[1]-x[0]} if x[1]>x[0] else False for x in frames]

                if False in frames:
                    logger.error(new_df)
                    raise Exception('invalid format of mevent comment')

                rect_info.append(frames)
        except Exception as e:
            logger.error(e)
        logger.debug('--')
        return rect_info

if __name__ == "__main__":
    pass

