import sys, os
import time
import pathlib

import cv2
import numpy as np
import pandas as pd

CUDA_PATH = 'C:\\Program Files\\NVIDIA GPU Computing Toolkit\\CUDA\\v11.5\\bin;'
## dll用
dir_path = pathlib.Path(__file__).resolve().parent
bin_path = dir_path.joinpath('bin')
os.environ['PATH'] = str(dir_path) + ';' + str(bin_path) + ';' + CUDA_PATH

sys.path.append(str(bin_path))
os.add_dll_directory(str(bin_path))
if os.path.exists(CUDA_PATH) == True:
    os.add_dll_directory(CUDA_PATH)

import pyopenpose as op
import direction_estimation
import trkproc

from optracker import logger

## Openposeの結果をDataFrameとして取得するためのクラス
## high_speed=Falseのときは頭部姿勢推定もする
class OpenposeToDataframe:
    def __init__(self, number_people_max=1, high_speed=False, calc_iris=False):
        models_path = dir_path.joinpath('models')
        self.opWrapper = op.WrapperPython()
        self.params = {}
        self.number_people_max = number_people_max
        self.params['model_folder'] = str(models_path)

        self.face_keys = [str(i) for i in range(70)]
        self.body_keys = [str(i) for i in range(25)]

        self.params['face'] = True
        self.params['number_people_max'] = number_people_max
        self.people_list = [i for i in range(self.number_people_max)]

        ## 高速化するときにいじるパラメータ
        self.high_speed = high_speed
        if self.high_speed == True:
            logger.warning('high_speed mode.')
            self.params['face_net_resolution'] = '320x320'
            self.params['net_resolution'] = '-1x32'
            self.params['render_pose'] = 1
        else:
            self.params['net_resolution'] = '-1x160'

        ## 瞳位置を再計算(計算時間がかかる)
        self.calc_iris = calc_iris
        if self.high_speed == False and self.calc_iris == True:
            logger.warning('calc_iris mode.')

        self.opWrapper.configure(self.params)

        self.face_trk = {}
        self.body_trk = {}
        self.face_dir = {}
        self.opWrapper.start()
        self.prev_points_0 = None

        ## 頭部姿勢推定結果を描画するための線の長さ
        self.direction_axis_length = 500
        logger.info(self.params)

    def detect(self, src_img, frame_pos):
        if isinstance(src_img, (np.ndarray)) == False:
            raise TypeError('src_img={}'.format(type(src_img)))
        self.frame_pos = frame_pos
        datum = op.Datum()
        if datum is None:
            logger.warning('datum is None.')
            return src_img
        datum.cvInputData = src_img
        self.opWrapper.emplaceAndPop(op.VectorDatum([datum]))

        f_keypoints = datum.faceKeypoints
        b_keypoints = datum.poseKeypoints
        dst_img = datum.cvOutputData

        if self.high_speed == False:
            self.fdir = direction_estimation.DirectionEstimation(dst_img, self.direction_axis_length)
            self.people_list = [i for i in range(self.number_people_max)]

        ## 検出結果が(0, 0)のデータを除外
#        f_keypoints = np.delete(f_keypoints, np.where(f_keypoints==0.0)[0], axis=0)
#        b_keypoints = np.delete(b_keypoints, np.where(b_keypoints==0.0)[0], axis=0)

        ## 何も検出していなかったら以降の処理は実行しない
        if f_keypoints is None or b_keypoints is None:
            logger.warning('no object(None)')
            return src_img
        if len(f_keypoints.shape) == 0 and len(b_keypoints.shape) == 0:
            logger.warning('no object(0)')
            return src_img

        ## 顔と体keypointsのnan埋め
        self.f_keypoints = self.__fill(f_keypoints, 70)
        self.b_keypoints = self.__fill(b_keypoints, 25)

        ## 鼻の点でインデックスを揃える
#        points_0 = self.b_keypoints[:, 0, :2].tolist()
        ## 首の点でインデックスを揃える
        points_0 = self.b_keypoints[:, 1, :2].tolist()

        ## 初回
        if self.prev_points_0 is None:
            self.prev_points_0 = points_0

        if self.number_people_max > 1:
            for i, prev_point in enumerate(self.prev_points_0):
                nearest_idx = self.__get_nearest_idx(prev_point, points_0, distance_thresh=10)
                if nearest_idx is not None:
                    points_0[i], points_0[nearest_idx] = points_0[nearest_idx], points_0[i]
                    self.people_list[i], self.people_list[nearest_idx] = self.people_list[nearest_idx], self.people_list[i]

            for name in range(self.number_people_max):
                if np.isnan(self.prev_points_0[name][0]) == False:
                    self.prev_points_0[name] = points_0[name]
        else:
            self.prev_points_0[0] = points_0[0]

        for name, person in enumerate(self.people_list):
            pf_keypoints = self.f_keypoints[person, :]
            pb_keypoints = None
            if self.high_speed == False:
                pb_keypoints = self.b_keypoints[person, :]

            if self.high_speed == False and pb_keypoints.size > 2:
                body_trk = self.__make_trk_row(pb_keypoints, name, self.body_keys)
                self.body_trk.update(body_trk)

            if pf_keypoints.size > 2:
                face_trk = self.__make_trk_row(pf_keypoints, name, self.face_keys)

                ## 頭部姿勢推定
                face_trk = self.__direction_and_iris(src_img, name, face_trk, person, pb_keypoints, pf_keypoints)

                self.face_trk.update(face_trk)
        return dst_img

    def get_face_trk(self, use_p=False, clear_trk=True):
        face_df = trkproc.dict_to_df(self.face_trk, use_p)
        if face_df is None:
            logger.error('face_df is None')

        if clear_trk == True:
            self.face_trk = {}
        return face_df

    def get_body_trk(self, use_p=False, clear_trk=True):
        if self.high_speed == True:
            logger.warning('can\'t get body_trk in high speed mode.')
            return None

        body_df = trkproc.dict_to_df(self.body_trk, use_p)
        if body_df is None:
            logger.error('body_df is None')

        if clear_trk == True:
            self.body_trk = {}
        return body_df

    def change_direction_axis_length(self, new_length):
        self.direction_axis_length = new_length
        logger.info('direction_axis_length=%s' % (new_length))

    def __fill(self, src_keypoints, code_num):
        if self.high_speed == True:
            return src_keypoints

        idx = pd.MultiIndex.from_product([range(s) for s in src_keypoints.shape], names=['name', 'code', 'val'])
        ## 一旦DataFrame化
        keypoints_df = pd.DataFrame({'A': src_keypoints.flatten()}, index=idx) ['A'].unstack(level=2)
        ## 検出できてないところをnanで埋めるためのDataFrameを生成
        fill_df = trkproc.gen_blank_df(None, range(self.number_people_max), range(code_num), col_num=3)
        fill_df.loc[pd.IndexSlice[:,:],:] = keypoints_df.loc[pd.IndexSlice[:,:],:]
        ## 一旦DataFrame化したものをarrayに戻す
        return fill_df.values.reshape(self.number_people_max,code_num,3)

    def __make_trk_row(self, src_keypoints, name, keys):
        keypoints = src_keypoints.reshape(-1,3)
        keypoints[:, :2] = keypoints[:, :2].astype('int16')
        trk = {(self.frame_pos, name, k):v for k,v in zip(keys, keypoints)}
        return trk

    def __get_nearest_idx(self, prev_point, now_points, distance_thresh=200):
        distance_list = {i:None for i in range(len(prev_point))}
        for i, tar_point in enumerate(now_points):
            if np.isnan(tar_point[0]) or np.isnan(prev_point[0]):
                distance_list[i] = 100000
            else:
                distance = np.sqrt((tar_point[0] - prev_point[0])**2 + (tar_point[1] - prev_point[1])**2)
                distance_list[i] = distance
        sorted_distance_list = sorted(distance_list.items(), key=lambda x:x[1])
        if sorted_distance_list[0][1] < distance_thresh:
            return sorted_distance_list[0][0]
        else:
            return None

    def __direction_and_iris(self, src_img, idx, face_trk, person, pb_keypoints, pf_keypoints):
        if self.high_speed == True:
            return face_trk

        if self.b_keypoints.shape[0] <= person:
            return face_trk
        roll, pitch, yaw, direction_x, direction_y = self.fdir.calc_direction(pb_keypoints, pf_keypoints)
        if np.isnan(roll) == False:
            roll = int(roll)
            pitch = int(pitch)
            yaw = int(yaw)
            direction_x = int(direction_x)
            direction_y = int(direction_y)
        face_trk[(self.frame_pos, idx, 'roll')] = roll
        face_trk[(self.frame_pos, idx, 'pitch')] = pitch
        face_trk[(self.frame_pos, idx, 'yaw')] = yaw
        face_trk[(self.frame_pos, idx, 'dir_point')] = (direction_x, direction_y, 0)
        if self.calc_iris == True:
            r_eye, l_eye = self.fdir.iris(src_img, pf_keypoints)
            if r_eye is not None:
                face_trk[(frame_pos, idx, '68')] = r_eye
                face_trk[(frame_pos, idx, '69')] = l_eye
        return face_trk

