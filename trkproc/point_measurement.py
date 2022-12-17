import sys, os
import traceback
import csv

import pandas as pd
import numpy as np

from trkproc import logger

pd.set_option("display.min_rows", 100)

class PointMeasurement:
    def __init__(self, trk_path, mevent_path, rolling_mean_window=1):
        ## Int64にするとstack(dropna=False)で失敗するのでここはfloatで読み込む
        ## read_csvのオプションでインデックス指定するとdtypeが反映されないようなのでset_index()で指定する
        dtyp = {'frame':'int32', 'name':'str', 'code':'str', 'x':'float', 'y':'float'}
        try:
            self.trk_df = pd.read_csv(trk_path, dtype=dtyp).set_index(['frame', 'name', 'code']).sort_index()
            if rolling_mean_window > 1:
                ## pandas 1.1以降でgroupbyの仕様が変わっているみたい
                ## name,codeでgroupbyするとframeが消えるので、
                self.trk_df = self.trk_df.reset_index(['name', 'code'])
                tar_df = self.trk_df.groupby(['name', 'code'], as_index=True).rolling(rolling_mean_window, center=True).mean()
                self.trk_df = tar_df.reset_index().set_index(['frame', 'name', 'code']).sort_index()
#                self.trk_df = pd.DataFrame(tar_df).sort_index().reset_index().set_index(['frame', 'name', 'code'])

            self.trk_df = self.trk_df[~self.trk_df.index.duplicated()]
            self.p2p_df = self.trk_df.stack(dropna=False).unstack(level=2)
            self.tar_p2p_df = self.p2p_df
            self.tar_trk_df = self.trk_df

            self.mevent_list = []
            with open(mevent_path, 'r') as f:
                head_line = f.readline()
                for row in csv.DictReader(f, ['time', 'frame', 'event_id', 'comment']):
                    self.mevent_list.append(row)
                if len(self.mevent_list) < 2:
                    logger.warning("len(self.mevent_list) < 2")
        except Exception as e:
            logger.error(self._traceback_parser(e))
            raise Exception(e)

    ## trkに含まれるnameカラムを取得
    def get_member(self):
        name_list = self.trk_df.index.get_level_values('name').unique().tolist()
        return name_list

    def set_event_id(self, tar_event_id):
        try:
            tar_frame = sorted([int(v['frame']) for v in self.mevent_list if v['event_id']==str(tar_event_id)])
            if len(tar_frame) == 0:
                return False

            min_pos = tar_frame[0]
            max_pos = tar_frame[-1]
            logger.debug('min_pos={} max_pos={}'.format(min_pos, max_pos))
            self.tar_p2p_df = self.p2p_df.loc[pd.IndexSlice[min_pos:max_pos, :], :]
            self.tar_trk_df = self.trk_df.loc[pd.IndexSlice[min_pos:max_pos, :, :], :]

            self.event_comments = [{'frame':v['frame'], 'comment':v['comment']} for v in self.mevent_list if v['event_id']==str(tar_event_id)]
        except Exception as e:
            logger.error(self._traceback_parser(e))
            raise Exception(e)
        return True

    def get_event_comments(self):
        return self.event_comments

    ## 面積を計算
    def calc_area(self, point_list):
        point_next_list = point_list.copy()
        point_next_list.pop(0)
        point_next_list.append(point_list[0])
        area = None
        for point in zip(point_list, point_next_list):
            cp = self._calc_cross_product(point[0], point[1])
            if area is None:
                area = cp
            else:
                area += cp
        area *= 0.5
        area = area.abs()
        return area

    ## 2点間距離を計算
    def calc_point2point(self, point1, point2, new_column_name='distance'):
        try:
            diff_df = (self.tar_p2p_df[point1] - self.tar_p2p_df[point2]) ** 2
            diff_df = diff_df.unstack(level=2)
            dist_df = np.sqrt(diff_df['x'] + diff_df['y'])
            dist_df = dist_df.reset_index().set_index(['frame', 'name'])
            dist_df.columns = [new_column_name]
        except Exception as e:
            logger.error(self._traceback_parser(e))
            raise Exception(e)
        return dist_df

    ## フレーム間の移動量を計算
    def calc_diff(self, point_code, step, suffix='diff'):
        try:
            diff_df = self.tar_trk_df.loc[pd.IndexSlice[:,:,point_code], :]
            diff_df = diff_df.groupby(['name']).diff(step)**2
#            diff_df = pd.DataFrame(np.sqrt(diff_df['x'] + diff_df['y'])).set_index(['frame','name']).drop('code', axis=1)
            diff_df = pd.DataFrame({f'{point_code}_{suffix}':(np.sqrt(diff_df['x'] + diff_df['y']))})
            diff_df = diff_df.reset_index(['code'], drop=True)

        except Exception as e:
            logger.error(self._traceback_parser(e))
            raise Exception(e)
        return diff_df

    def calc_diffdiff(self, point_code, step):
        try:
            diff_df = self.calc_diff(point_code, step, suffix='diffdiff')
            diffdiff_df = diff_df.groupby(['name']).diff(step)
        except Exception as e:
            logger.error(self._traceback_parser(e))
            raise Exception(e)
        return diffdiff_df

    def get_point(self, point_code, new_column_name=None):
        tar_df = self.trk_df.loc[pd.IndexSlice[:,:,point_code],:].reset_index().set_index(['frame','name']).drop('code', axis=1)
        if new_column_name is None:
            tar_df = tar_df.rename(columns={'x':f"{point_code}_x", 'y':f"{point_code}_y"})
        else:
            tar_df = tar_df.rename(columns={'x':f"{new_column_name}_x", 'y':f"{new_column_name}_y"})
        return tar_df

    ## 外積
    def _calc_cross_product(self, point1, point2):
        point1 = self.tar_p2p_df[point1].unstack(level=2)
        point2 = self.tar_p2p_df[point2].unstack(level=2)
        diff_df = point1['x']*point2['y'] - point2['x']*point1['y']
        diff_df = diff_df.reset_index().set_index(['frame', 'name'])
        diff_df.columns = ['area']
        return diff_df

    def _gen_frame_pos_list(self, event_id):
        frame_pos_list = []
        try:
            tar_mevent = []
            for eid in event_id:
                tar_mevent = sorted([int(v['frame']) for v in self.mevent_list if v['event_id']==str(eid)])
                if len(tar_mevent) < 2:
                    continue
                frame_nums = range(tar_mevent[0], tar_mevent[-1])
                frame_pos_list.extend(frame_nums)
        except Exception as e:
            logger.error(self._traceback_parser(e))
            frame_pos_list = []
        return frame_pos_list

    def _traceback_parser(self, e):
        line = traceback.format_tb(e.__traceback__)[0].split(', ')[1]
        return '{},{}'.format(line, e)

## 移動平均
def rolling_mean(tar_df, tar_col, window):
    tar_df = tar_df.groupby(level=1)[tar_col].rolling(window, center=True).mean().reset_index(level=0, drop=True)
    tar_df = pd.DataFrame(tar_df, columns=[tar_col]).sort_index()
    return tar_df

## 平均値が0になるように正規化
def ave_normalize(tar_df, tar_col):
    mean = tar_df.groupby(level=1)[tar_col].mean()
    names = mean.index.values
    for name in names:
        tar_df.loc[pd.IndexSlice[:,name], :] -= mean[name]
    return tar_df


