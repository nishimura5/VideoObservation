import sys,os
import traceback
import datetime
import re
import shutil
import pathlib
import random
import string

import pandas as pd

from mevent import logger

class MeventEditor:
    dtypes = {'time':str, 'frame':int, 'event_id':int, 'comment':str}
    def __init__(self, fps=0):
        logger.info('python:{} (pandas:{})'.format(sys.version, pd.__version__))
        logger.info('fps={}'.format(fps))

        self.time_col = []
        self.frame_col = []
        self.event_id_col = []
        self.comment_col = []
        self.clear()
        self.fps = fps

    ## C#向けのAPI
    def update_mevent_file(self, mevent_datas, mevent_path):
        self.clear()
        self.update_event_by_mevent_datas(mevent_datas)
        if len(self.time_col) == 0:
            logger.warning('data is empty.')
            return
        self.save(mevent_path)

    def update_event_by_mevent_datas(self, mevent_datas):
        try:
            for mevent in mevent_datas:
                try:
                    t = mevent.Time.encode('utf-8').decode('utf-8')
                    c = mevent.Comment.encode('utf-8').decode('utf-8')
                except Exception as e:
                    logger.error(self._traceback_parser(e))
                    raise Exception(e)

                delta = self.cvt_str_to_time(mevent.Time)
                frame = int(delta.total_seconds()*self.fps)
                self.time_col.append(delta)
                self.frame_col.append(frame)
                self.event_id_col.append(mevent.EventId)
                self.comment_col.append(mevent.Comment)
        except Exception as e:
            logger.error(self._traceback_parser(e))
            raise Exception(e)

    def clear(self):
        self.time_col.clear()
        self.frame_col.clear()
        self.event_id_col.clear()
        self.comment_col.clear()

    def add_event_by_time(self, time_str, event_id, comment="-"):
        time_match = re.search('(\d{1,2}):(\d{1,2}):(\d{1,2}).*', time_str)
        if time_match is None:
            logger.warning('invalid time field format time_str={}'.format(time_str))
            time_str = ''
        else:
            time_str = time_match.group()

        delta = self.cvt_str_to_time(time_str)
        self.time_col.append(delta)
        self.frame_col.append(int(delta.total_seconds()*self.fps))
        self.event_id_col.append(event_id)
        if comment == '':
            comment = '--'
        self.comment_col.append(comment)

    def get_event_row(self, idx):
        return [str(self.time_col[idx])[:9], self.frame_col[idx], self.event_id_col[idx], self.comment_col[idx]]

    def get_event_list(self):
        dst_list = [self.get_event_row(idx) for idx in range(len(self.time_col))]
        logger.debug('dst_list={}'.format(dst_list))
        return dst_list

    def get_id_list(self):
        event_id_list = set(tuple(self.event_id_col))
        return list(event_id_list)

    def load(self, mevent_path, fps=0, total_ms=0):
        try:
            self.clear()
            if os.path.exists(mevent_path) == False:
                logger.warning('mevent file not found (mevent_path={})'.format(mevent_path))
                src_path = pathlib.Path(mevent_path)
                self._gen_mevent_file(src_path, fps, total_ms)

            with open(mevent_path, 'r', encoding='UTF-8') as f:
                content = f.read()
            m = re.search(r'^#fps=\d.*', content)
            if m is not None:
                self.fps = float(m.group().split('=')[1])
                logger.debug('fps={}'.format(self.fps))
            else:
                logger.warning('#fps=xxx not found')

            src_df = pd.read_csv(mevent_path, comment='#', dtype=self.dtypes)
            ## commentが空欄なら--で埋める
            src_df['comment'].fillna('--', inplace=True)
            self.time_col.extend([self.cvt_frame_pos_to_time(f) if t=='' else self.cvt_str_to_time(t) for f,t in zip(src_df['frame'].values, src_df['time'].values)])
            self.frame_col.extend(src_df['frame'].values.tolist())
            self.event_id_col.extend(src_df['event_id'].values.tolist())
            self.comment_col.extend(src_df['comment'].values.tolist())
        except Exception as e:
            logger.error(self._traceback_parser(e))
            raise Exception(e)
        return self.fps

    def randomname(self, n):
       randlst = [random.choice(string.ascii_letters + string.digits) for i in range(n)]
       return ''.join(randlst)

    ## parse_comment.pyで使用
    def gen_event_df(self):
        try:
            mevent_df = pd.DataFrame({'time':self.time_col, 'frame':self.frame_col, 'event_id':self.event_id_col, 'comment':self.comment_col})
            mevent_df = mevent_df.sort_values('time')
            mevent_df['time'] = mevent_df['time'].apply(
                    lambda x: f'{x.components.hours:02d}:{x.components.minutes:02d}:{x.components.seconds:02d}.{x.components.milliseconds:1d}'
                  if not pd.isnull(x) else ''
            )
            mevent_df = mevent_df.set_index('time')
            logger.debug('mevent_df.size={}'.format(mevent_df.size))
        except Exception as e:
            logger.error(self._traceback_parser(e))
            raise Exception(e)
        return mevent_df

    def save(self, dst_path):
        try:
            dst_path = pathlib.Path(dst_path)
            current_path = dst_path.parent.joinpath(self.randomname(10))
            logger.info('{} {}'.format(str(dst_path), str(current_path)))

            mevent_df = self.gen_event_df()

            with open(str(current_path), 'w', encoding='UTF-8') as f:
                f.write('#fps={:.2f}\n'.format(self.fps))
            mevent_df.to_csv(str(current_path), mode='a')

            shutil.move(str(current_path), str(dst_path))

        except Exception as e:
            logger.error(self._traceback_parser(e))
            raise Exception(e)

    def edit(self, pos, event_id, comment):
        num = self.frame_col.index(pos)
        self.event_id_col[num] = event_id
        self.comment_col[num] = comment

    def remove(self, pos):
        num = self.frame_col.index(pos)
        self.time_col.pop(num)
        self.frame_col.pop(num)
        self.event_id_col.pop(num)
        self.comment_col.pop(num)

    def cvt_frame_pos_to_time(self, frame_pos):
        msec = frame_pos / self.fps * 1000000
        frame_pos_time = datetime.timedelta(microseconds=msec)
        return frame_pos_time

    def cvt_str_to_time(self, src_time_str):
        try:
            if '.' in src_time_str:
                src_t = datetime.datetime.strptime(src_time_str, "%H:%M:%S.%f")
                dst_dt = datetime.timedelta(hours=src_t.hour, minutes=src_t.minute, seconds=src_t.second, microseconds=src_t.microsecond)
            else:
                src_t = datetime.datetime.strptime(src_time_str, "%H:%M:%S")
                dst_dt = datetime.timedelta(hours=src_t.hour, minutes=src_t.minute, seconds=src_t.second)
        except Exception as e:
            logger.error(self._traceback_parser(e))
            logger.error('src_time_str={}'.format(src_time_str))
            dst_dt = ''
        return dst_dt

    def set_fps(self, fps):
        self.fps = fps

    def _gen_mevent_file(self, mevent_path, fps, total_ms):
        logger.debug('fps={} total_ms={}'.format(fps, total_ms))
        if fps > 0:
            total_frame = int(total_ms / fps)
        else:
            total_frame = 0
        max_time = datetime.timedelta(seconds=int(total_ms / 1000))
        mevent_content = """#fps={:.2f}
time,frame,event_id,comment
0:00:00,0,0,auto generated
{},{},0,auto generated""".format(fps, max_time, total_frame)
        mevent_path.parent.mkdir(parents=True, exist_ok=True)
        with mevent_path.open('w') as f:
            f.write(mevent_content)

    def _traceback_parser(self, e):
        try:
            tb = traceback.format_tb(e.__traceback__)
            line = tb[0].split(', ')[1]
#            line = tb
        except Exception as e:
            logger.error(e)
        return '{},{}'.format(line, e)

if __name__ == "__main__":
    pass

