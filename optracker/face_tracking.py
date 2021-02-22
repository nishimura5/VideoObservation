import sys, os
from argparse import ArgumentParser
import pathlib
import re

import cv2
import pandas as pd

dir_path = pathlib.Path(__file__).resolve().parent
sys.path.append(str(dir_path.parent))
import pyopenpose_to_df
import mevent
import trkproc

from optracker import logger

## 顔ランドマークのトラッキングと頭部姿勢推定
class FaceTracking:
    def __init__(self, src_mov_path, mevent_path, rot, number_people_max, dst_mov_path=None, dst_mov_resize=1.0):
        try:
            logger.info('python:{} (cv2:{})(pandas:{})'.format(sys.version, cv2.__version__, pd.__version__))
            logger.info('src_mov_path={} mevent_path={} rot={} number_people_max={} dst_mov_resize={}'.format(src_mov_path, mevent_path, rot, number_people_max, dst_mov_resize))
            match = re.fullmatch('[ -~]+', src_mov_path)
            if match is None:
                logger.error('パスに無効な文字(全角文字等)が使用されています。')
                raise Exception('パスに無効な文字(全角文字等)が使用されています。')

            self.number_people_max = number_people_max
            self.file_name = os.path.basename(src_mov_path).split('.')[0]
            self.vcm = mevent.VideoCaptureMevent(src_mov_path, mevent_path, rot_ccw=rot)
            width, height, self.fps = self.vcm.get_frame_size_and_fps()
            logger.info('{}x{} fps={}'.format(width, height, self.fps))

            self.out = None
            self.out_img_size = (int(width*dst_mov_resize), int(height*dst_mov_resize))
            logger.info('out_img_size={}'.format(self.out_img_size))
        except Exception as e:
            logger.error(self._traceback_parser(e))
            raise Exception(e)

        try:
            if dst_mov_path is not None:
                fourcc = 'mp4v'
                logger.info('fourcc={} out_img_size={}'.format(fourcc, self.out_img_size))
                logger.info('dst_mov_path={}'.format(dst_mov_path))
                os.makedirs(os.path.dirname(dst_mov_path), exist_ok=True)
                fourcc = cv2.VideoWriter_fourcc(*fourcc)
                self.out = cv2.VideoWriter(dst_mov_path, fourcc, self.fps, self.out_img_size)
        except Exception as e:
            logger.error(self._traceback_parser(e))
            raise Exception(e)
        self.out_mov_resize = dst_mov_resize

        self.dtyp = {'frame':'int32', 'name':'object', 'code':'object', 'x':'Int64', 'y':'Int64'}

    ## トラッキングを開始
    ## high_speed=Trueのとき、体の姿勢推定の精度を下げて計算時間を短縮 → 頭部姿勢推定ができなくなる
    def tracking(self, dst_trk_dir, tar_event_ids, high_speed=False):
        logger.debug('++')
        try:
            dst_trk_dir = pathlib.Path(dst_trk_dir)
            dst_trk_path = dst_trk_dir.joinpath(self.file_name + '.trk')
            frame_pos_list = self.vcm.gen_frame_num_list(event_id=tar_event_ids)

            dst_trk_dir.mkdir(exist_ok=True)
            dst_body_trk_path = dst_trk_dir.joinpath(self.file_name + '_body.trk')

            if len(frame_pos_list) == 0:
                print('empty frame_pos_list.')
                logger.error('empty frame_pos_list.')
                return None

            init_frame_num = frame_pos_list[0] - 1
            if init_frame_num > 0:
                frame = self.vcm.get_frame(init_frame_num)

            opdf = pyopenpose_to_df.OpenposeToDataframe(self.number_people_max, high_speed)
            ## 顔方向推定の矢印の長さ,Noneだと矢印は出ない
            opdf.change_direction_axis_length(new_length=700)
            logger.info("dst_trk_path={} len(frame_pos_list)={} (tar_event_ids={})".format(dst_trk_path, len(frame_pos_list), tar_event_ids))

            for frame_pos in frame_pos_list:
                frame = self.vcm.get_frame(frame_pos)
    #            frame = self.vcm.get_next_frame()
                if frame is None:
                    print('frame is None')
                    logger.error('frame is None')
                    continue
                dst_img = opdf.detect(frame, frame_pos)
                trkproc.put_frame_pos(dst_img, frame_pos, self.out_mov_resize)
                out_img = cv2.resize(dst_img, self.out_img_size)
                cv2.imshow(self.file_name, out_img)
                if self.out is not None:
                    self.out.write(out_img)
                key = cv2.waitKey(1) & 0xFF
                if chr(key) in [' ', 'x']:
                    logger.info('break')
                    key = ''
                    break
            logger.info('last frame_pos={}'.format(frame_pos))

            face_df = opdf.get_face_trk()
            logger.info('dst_trk_path={}'.format(dst_trk_path))
            face_df.to_csv(dst_trk_path)
            body_df = opdf.get_body_trk()
            body_df.to_csv(dst_body_trk_path)
        except Exception as e:
            logger.error(self._traceback_parser(e))
        cv2.destroyAllWindows()
        print('trk_end')
        logger.debug('--')

    def play(self, src_trk_dir, tar_event_ids, wait_ms=1, draw_point_list=None, body_flg=False, eye_blur_flg=False):
        src_trk_dir = pathlib.Path(src_trk_dir)
        frame_pos_list = self.vcm.gen_frame_num_list(event_id=tar_event_ids)
        if draw_point_list is None:
            draw_point_list = [i for i in range(70)]

        src_trk_path = src_trk_dir.joinpath(self.file_name + '.trk')
        if body_flg == True:
            src_trk_path = src_trk_dir.joinpath(self.file_name + '_body.trk')

        if src_trk_path.exists() == False:
            print('trk file not found. (%s)' % (src_trk_path))
            logger.error('trk file not found. (%s)' % (src_trk_path))
            return

        ## Pandasのバグで100万行超えるCSVを読むときはdtypeとindex_colを同時に指定できないらしい
#        trk_df = pd.read_csv(src_trk_path, dtype=self.dtyp, index_col=[0,1,2])
        trk_df = pd.read_csv(src_trk_path, dtype=self.dtyp)
        trk_df = trk_df.set_index(['frame','name','code'])
        frame_pos_list_trk = trk_df.index.get_level_values('frame').unique().to_list()
        frame_pos_list = [i for i in frame_pos_list_trk if i in frame_pos_list]

        init_frame_num = frame_pos_list[0] - 1
        if init_frame_num > 0:
            frame = self.vcm.get_frame(init_frame_num)

        logger.info("src_trk_path={} len(frame_pos_list)={} (tar_event_ids={})".format(src_trk_path, len(frame_pos_list), tar_event_ids))
        for frame_pos in frame_pos_list:
            try:
                ## get_next_frame()の方が高速だがフレームがずれるのでget_frameを使用する。
                frame = self.vcm.get_frame(frame_pos)
                #frame = self.vcm.get_next_frame()
                frame = cv2.resize(frame, self.out_img_size)
                trkproc.put_frame_pos(frame, frame_pos, self.out_mov_resize, add_time=self.fps)
                frame_trk_df = trk_df.loc[frame_pos]
                name_list = frame_trk_df.index.get_level_values('name').unique().to_list()
            except Exception as e:
                logger.error(e)
                raise

            for name in name_list:
                tar_df = trk_df.loc[pd.IndexSlice[frame_pos, name, :], :]
                landmarks = tar_df.values.tolist()

                try:
                    ## モザイク
                    left = int(landmarks[36][0]*self.out_mov_resize)
                    top = int(landmarks[37][1]*self.out_mov_resize)
                    right = int(landmarks[45][0]*self.out_mov_resize)
                    bottom = int(landmarks[33][1]*self.out_mov_resize)
                    frame = self.blur(frame, left, top, right, bottom)
                except:
                    pass

                for label, pos in enumerate(landmarks):
                    if pd.isnull(pos[0]):
                        continue
                    else:
                        pos = (int(pos[0]*self.out_mov_resize), int(pos[1]*self.out_mov_resize))

                    if label == 0:
                        trkproc.put_name(frame, name, pos)
                    elif label == 68 or label == 69:
                        cv2.circle(frame, pos, 4, (30,0,200), -1)
                    elif label in draw_point_list:
                        cv2.circle(frame, pos, 3, (0,244,0), 2)
    #                    cv2.putText(frame, '%d'%label, tuple(pos), cv2.FONT_HERSHEY_PLAIN, 0.5, (0, 244, 0), 1)
                    else:
                        continue

                try:
                    ## 頭部姿勢推定
                    dir_point = tar_df.loc[pd.IndexSlice[frame_pos, name,('30', 'dir_point')], : ].values
                    if dir_point.size < 4:
                        continue
                    if pd.isnull(dir_point[0][0]) == False and pd.isnull(dir_point[1][0]) == False:
                        p1 = (int(dir_point[0][0]*self.out_mov_resize), int(dir_point[0][1]*self.out_mov_resize))
                        p2 = (int(dir_point[1][0]*self.out_mov_resize), int(dir_point[1][1]*self.out_mov_resize))
                        cv2.arrowedLine(frame, p1, p2, (5,00,255), 2)
                except Exception as e:
                    logger.error(e)
                    raise

            cv2.imshow('play', frame)
            if self.out is not None:
                self.out.write(frame)
            key = cv2.waitKey(wait_ms) & 0xFF
            if chr(key) == 'x':
                key = ''
                break

        cv2.destroyAllWindows()
        logger.info('play_end')

    def blur(self, src_img, left, top, right, bottom):
        offset = 30
        rect_img = src_img[top-offset:bottom+offset, left-offset:right+offset, :]
        resize_width = int(rect_img.shape[1]/14)
        resize_height = int(rect_img.shape[0]/14)
        if resize_width == 0 or resize_height == 0:
            return src_img
        resize_img = cv2.resize(rect_img, (resize_width, resize_height))
        mozaik_img = cv2.resize(resize_img, (rect_img.shape[1], rect_img.shape[0]), interpolation = cv2.INTER_NEAREST)
        src_img[top-offset:bottom+offset, left-offset:right+offset, :] = mozaik_img
        return src_img

    def _traceback_parser(self, e):
        line = traceback.format_tb(e.__traceback__)[0].split(', ')[1]
        return '{},{}'.format(line, e)

if __name__ == "__main__":
    try:
        argparser = ArgumentParser()
        argparser.add_argument('--mode', type=str)
        argparser.add_argument('--mov', type=str)
        argparser.add_argument('--trk', type=str)
        argparser.add_argument('-o', '--dst_mov_path', type=str)
        argparser.add_argument('-m', '--mevent', type=str)
        argparser.add_argument('-r', '--rot', type=int)
        argparser.add_argument('-e', '--event_id', type=int)
        argparser.add_argument('-p', '--people', type=int)
        argparser.add_argument('-s', '--resize', type=float)
        args = argparser.parse_args()

        mov_path = args.mov
        if not os.path.exists(mov_path):
            logger.warning('mov not found {}'.format(mov_path))
        mevent_path = args.mevent
        if not os.path.exists(mevent_path):
            logger.warning('mevent not found {}'.format(mevent_path))

        dst_mov_path = args.dst_mov_path

        trk_dir = args.trk

        rot = args.rot
        event_id = args.event_id
        number_people_max = args.people
        dst_mov_resize = args.resize

        ft = FaceTracking(mov_path, mevent_path, rot, number_people_max, dst_mov_path, dst_mov_resize)
        if args.mode == 'track':
            ft.tracking(trk_dir, [event_id])
        elif args.mode == 'face_play':
            ft.play(trk_dir, [event_id])
        elif args.mode == 'body_play':
            ft.play(trk_dir, [event_id], body_flg=True)
    except Exception as e:
        logger.error(e)
