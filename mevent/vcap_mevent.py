import sys,os
import csv
import datetime
import pathlib

import cv2

class VideoCaptureMevent(cv2.VideoCapture):
    __VERSION__ = '1.0.1'
    def __init__(self, mov_path, mevent_path, rot_ccw=0):
        mevent_path = pathlib.Path(mevent_path)
        if os.path.exists(mov_path) == False:
            raise FileNotFoundError('mov_path:%s'%mov_path)
        if mevent_path.exists() == False:
            self.__gen_mevent_file(mov_path, mevent_path)

        super().__init__(mov_path)
        self.mevent_list = []
        with mevent_path.open('r', encoding='UTF-8') as f:
            f.readline()
            for row in csv.DictReader(f, ['time', 'frame', 'event_id', 'comment']):
                self.mevent_list.append(row)
        rot_code = {0:None, 90:cv2.ROTATE_90_COUNTERCLOCKWISE, 270:cv2.ROTATE_90_CLOCKWISE}
        self.rot = rot_code[rot_ccw]
        self.max_frame_pos = self.get(cv2.CAP_PROP_FRAME_COUNT)

    def show_mevent(self):
        for v in self.mevent_list:
            print(v)

    def gen_frame_num_list(self, event_id):
        frame_num_list = []
        try:
            tar_mevent = []
            for eid in event_id:
                tar_mevent = sorted([int(v['frame']) for v in self.mevent_list if v['event_id']==str(eid)])
                if len(tar_mevent) < 2:
                    continue
                if tar_mevent[-1] > self.max_frame_pos:
                    tar_mevent[-1] = int(self.max_frame_pos)
                frame_nums = range(tar_mevent[0], tar_mevent[-1])
                frame_num_list.extend(frame_nums)
        except Exception as e:
            print('exception in vcap_mevent.py')
            print(e)
            frame_num_list = []
        return frame_num_list

    def get_frame_size_and_fps(self):
        if self.rot == cv2.ROTATE_90_COUNTERCLOCKWISE or self.rot == cv2.ROTATE_90_CLOCKWISE:
            height = int(self.get(cv2.CAP_PROP_FRAME_WIDTH))
            width = int(self.get(cv2.CAP_PROP_FRAME_HEIGHT))
        else:
            width = int(self.get(cv2.CAP_PROP_FRAME_WIDTH))
            height = int(self.get(cv2.CAP_PROP_FRAME_HEIGHT))
        fps = self.get(cv2.CAP_PROP_FPS)
        return width, height, fps

    def get_frame(self, frame_pos):
        self.set(cv2.CAP_PROP_POS_FRAMES, frame_pos)
        ok, frame = self.read()
        if self.rot is not None:
            frame = cv2.rotate(frame, self.rot)
        return frame

    def get_next_frame(self):
        ok, frame = self.read()
        if self.rot is not None:
            frame = cv2.rotate(frame, self.rot)
        return frame

    def terminate(self):
        self.release()

    def __gen_mevent_file(self, mov_path, mevent_path):
        cap = cv2.VideoCapture(str(mov_path))
        fps = cap.get(cv2.CAP_PROP_FPS)
        max_frame_pos = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
        max_time = datetime.timedelta(seconds=int(max_frame_pos/fps))
        cap.release()
        mevent_content = """#fps={:.2f}
time,frame,event_id,comment
0:00:00,0,0,auto generated
{},{},0,auto generated""".format(fps, max_time, max_frame_pos)
        mevent_path.parent.mkdir(parents=True, exist_ok=True)
        with mevent_path.open('w') as f:
            f.write(mevent_content)

if __name__ == "__main__":
    pass
