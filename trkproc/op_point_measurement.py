import sys, os
import pathlib

import pandas as pd
import numpy as np
## robust z score用
from sklearn.preprocessing import robust_scale
from scipy.stats import norm

dir_path = pathlib.Path(__file__).resolve().parent
sys.path.append(str(dir_path))
import point_measurement

from trkproc import logger

class OpPointMeasurement(point_measurement.PointMeasurement):
    def __init__(self, trk_path, mevent_path, rolling_mean_window=1):
        super().__init__(trk_path, mevent_path, rolling_mean_window)
        self.r_eye_points = ['36', '37', '38', '39', '40', '41']
        self.l_eye_points = ['42', '43', '44', '45', '46', '47']
        ## 口だと閉じてるときに面積計算に失敗する模様
        self.inner_mouth_points = ['60', '61', '62', '63', '64', '65', '66', '67']
        self.outer_mouth_points = ['48', '49', '50', '51', '52', '53', '54', '55', '56', '57', '58', '59']

    ## 目の領域の重心を原点とした瞳(keypoint #68, 69)の座標を計算
    def calc_eye_centre(self):
        try:
            r_eye_df = self.tar_p2p_df.loc[:, self.r_eye_points]
            r_eye_df = r_eye_df.mean(axis='columns')
            r_eye_df = r_eye_df - self.tar_p2p_df['68']

            l_eye_df = self.tar_p2p_df.loc[:, self.l_eye_points]
            l_eye_df = l_eye_df.mean(axis='columns')
            l_eye_df = l_eye_df - self.tar_p2p_df['69']

            eye_centre = r_eye_df + l_eye_df
            eye_centre = eye_centre.unstack(level=2)
            eye_centre.columns = ['eye_x', 'eye_y']
            eye_centre = eye_centre.astype('int64')
        except Exception as e:
            logger.error(self._traceback_parser(e))
            raise Exception(e)
        return eye_centre

    def calc_mouth_shape(self):
        tar_df = self.tar_p2p_df.loc[:, ['36', '45', '27', '48', '54', '51', '57']]

        tar_df['36-27'] = (tar_df['36'] - tar_df['27'])
        tar_df['45-27'] = (tar_df['45'] - tar_df['27'])
        tar_df['36-45'] = (tar_df['36'] - tar_df['45'])
        tar_df['48-36'] = (tar_df['48'] - tar_df['27'])
        tar_df['54-45'] = (tar_df['54'] - tar_df['27'])
        tar_df['51-27'] = (tar_df['51'] - tar_df['27'])
        tar_df['57-27'] = (tar_df['57'] - tar_df['27'])
        tar_df['48-54'] = (tar_df['48'] - tar_df['54'])
        tar_df = tar_df.loc[:, ['36-27', '45-27', '36-45', '48-36', '54-45', '48-54', '51-27', '57-27']] ** 2
        tar_df = tar_df.unstack(level=2)
        tar_df = tar_df.swaplevel(axis=1)
        tar_df = np.sqrt(tar_df['x'] + tar_df['y'])
        tar_df['48-36'] = tar_df['48-36'] / (tar_df['36-27'] * 2)
        tar_df['54-45'] = tar_df['54-45'] / (tar_df['45-27'] * 2)
        tar_df['48-54'] = tar_df['48-54'] / tar_df['36-45']
        tar_df['51-27'] = tar_df['51-27'] / tar_df['36-45']
        tar_df['57-27'] = tar_df['57-27'] / tar_df['36-45']
        return tar_df.loc[:, ['48-36', '54-45', '48-54', '51-27', '57-27']]

    ## 目の領域の面積を計算
    def calc_eye_area(self, sqrt_flg=False):
        r_eye_area = self.calc_area(self.r_eye_points)
        l_eye_area = self.calc_area(self.l_eye_points)
        eye_area = r_eye_area + l_eye_area
        eye_area = eye_area.rename(columns={'area':'eye_area'})
        if sqrt_flg == True:
            eye_area = np.sqrt(eye_area)
        return eye_area

    ## 口の領域の面積を計算
    def calc_mouth_area(self, sqrt_flg=False):
        inner_mouth_area = self.calc_area(self.inner_mouth_points)
        inner_mouth_area = inner_mouth_area.rename(columns={'area':'inner_mouth_area'})
        outer_mouth_area = self.calc_area(self.outer_mouth_points)
        outer_mouth_area = outer_mouth_area.rename(columns={'area':'outer_mouth_area'})
        mouth_area = pd.concat([inner_mouth_area, outer_mouth_area], axis=1)
        if sqrt_flg == True:
            mouth_area = np.sqrt(mouth_area)
        return mouth_area

    def get_pitch(self):
        pitch_df = self.get_point('pitch')
        pitch_df = pitch_df.rename(columns={'pitch_x':'pitch'})
        pitch_df = pitch_df.drop('pitch_y', axis=1)
        return pitch_df

    def get_yaw(self):
        yaw_df = self.get_point('yaw')
        yaw_df = yaw_df.rename(columns={'yaw_x':'yaw'})
        yaw_df = yaw_df.drop('yaw_y', axis=1)
        return yaw_df

    def load_calclist(self, calclist_path):
        try:
            calclist_df = pd.read_csv(calclist_path, dtype={'pointA':str, 'pointB':str, 'func':str}, comment=';')
            calclist_df = calclist_df.fillna({'pointB':'', 'fun':'?'})
            df_list = []
            ## === CSV規則 ===
            ## 1行につきグラフ1本
            for row in calclist_df.itertuples():
#                logger.debug('{}, {}, {}'.format(row.pointA, row.pointB, row.func))
                ## pointAだけ = 値(roll, pitch, yaw)
                if row.pointB == '':
#                    logger.debug('tar_p2p_df=\n{}'.format(self.tar_p2p_df))
                    tar_df = self.tar_p2p_df[row.pointA].unstack(level=2).loc[:,['x']].rename(columns={'x':row.pointA})
#                    logger.debug('tar_df=\n{}'.format(tar_df))
                    col_name = row.pointA
                elif row.pointB == 'x' or row.pointB == 'y':
                    tar_df = self.tar_p2p_df[row.pointA].unstack(level=2).loc[:,[row.pointB]].rename(columns={row.pointB:row.pointA})
                    col_name = row.pointA
                ## pointAとpointBに同じ値 = 移動量
                elif row.pointA == row.pointB:
                    tar_df = self.calc_diff(row.pointA, 60)
                    col_name = row.pointA+'_diff'
                ## それ以外 = 距離
                else:
                    col_name = '{}-{}'.format(row.pointA, row.pointB)
                    tar_df = self.calc_point2point(row.pointA, row.pointB, new_column_name=col_name)

                ## 先頭が'*' = 倍率
                if row.func[0] == '*':
                    amp = float(row.func[1:])
                    tar_df = tar_df * amp
                ## 先頭が'p' = パーセンタイル
                elif row.func[0] == 'p':
                    tile = int(row.func[1:]) * 0.01
                    logger.debug('percentile={}'.format(tile))
                    new_col_name = '{}_{}ile'.format(col_name, row.func[1:])
                    tar_df = self._normalize_quantile(tar_df, tile, 0.0).rename(columns={col_name:new_col_name})
                    col_name = new_col_name
                elif row.func[0] == 'r':
                    range_code = row.func[1:].split('~')
                    if len(range_code) != 2:
                        raise Exception('invalid range code({})'.format(range_code))
                    min_val = int(range_code[0])
                    max_val = int(range_code[1])
                    logger.debug('range={}~{}'.format(min_val, max_val))
                    new_col_name = '{}_{}'.format(col_name, row.func[1:])
                    tar_df = self._normalize(tar_df, max_val, min_val).rename(columns={col_name:new_col_name})
                    col_name = new_col_name
                else:
                    logger.debug('no func')

                df_list.append({'legend':row.legend, 'df':tar_df, 'color':row.color, 'points':col_name})

#            con_df = pd.DataFrame()
#            con_df['con'] = (df_list[0]['df']['62-66'] + df_list[1]['df']['pitch'] + df_list[2]['df']['diff']) / (-3) + 1.0
#            com_df = pd.DataFrame()
#            com_df['com'] = (df_list[0]['df']['62-66'] + df_list[1]['df']['pitch']) / (2)
##            con_df['con'] = mouth_df[0]
#            con_df['con'] = con_df['con'].where(con_df['con'] < 1, 2)
#            con_df['con'] = con_df['con'].where((con_df['con'] > 1)|(con_df['con'] < 0), 1)
#            con_df['con'] = con_df['con'].where(con_df['con'] > 0, 0)
#
#            df_list.append({'legend':'集中指数', 'df':con_df, 'color':'red', 'points':'con'})
#            df_list.append({'legend':'コミュニケーション指数', 'df':com_df, 'color':'green', 'points':'com'})
#
#            df_list.pop(0)
#            df_list.pop(0)
#            df_list.pop(0)

        except Exception as e:
            logger.error(self._traceback_parser(e))
            raise Exception(e)
        return df_list

    def _robust_z(self, src_s):
        rzs_df = src_s.groupby('name').apply(robust_z)
        rzs_df = rzs_df.reset_index().rename({'level_1':'frame'}, axis=1).set_index(['frame', 'name']).sort_index()
        return rzs_df

    def _normalize_quantile(self, src_s, qmax=1.0, qmin=0.0):
        norm_df = src_s.groupby('name').apply(qnorm, xmax=qmax, xmin=qmin)
        norm_df = norm_df.reset_index().rename({'level_1':'frame'}, axis=1).set_index(['frame', 'name']).sort_index()
        norm_df = norm_df.where(norm_df < 1.0, 1.0)
        return norm_df

    def _normalize(self, src_s, vmax, vmin):
        norm_df = src_s.groupby('name').apply(norm, xmax=vmax, xmin=vmin)
        norm_df = norm_df.reset_index().rename({'level_1':'frame'}, axis=1).set_index(['frame', 'name']).sort_index()
        norm_df = norm_df.where(norm_df < 1.0, 1.0)
        norm_df = norm_df.where(norm_df > 0.0, 0.0)
        return norm_df


def robust_z(x):
    frames_arr = x.reset_index(['frame'])['frame'].values
    coefficient = norm.ppf(0.75)-norm.ppf(0.25)  ## 1.34898
    robust_z_score = robust_scale(x)*coefficient

    frame_df = pd.DataFrame(frames_arr, columns=['frame'])
    rzs_df = pd.DataFrame(robust_z_score)
    rzs_df = pd.concat([frame_df, rzs_df], axis=1).set_index(['frame'])

    return rzs_df

def qnorm(x, xmax, xmin):
    top = x.quantile(xmax).values[0]
    bottom = x.quantile(xmin).values[0]
    if (top-bottom) != 0:
        normed_df = (x - bottom) / (top - bottom)
    else:
        normed_df = (x - bottom)

    return normed_df

def norm(x, xmax, xmin):
    normed_df = (x - xmin) / (xmax - xmin)
    return normed_df

