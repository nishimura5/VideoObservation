import os
import sys
import logging

import numpy as np
import pandas as pd

if 'optracker' in sys.modules.keys():
    logger = logging.getLogger('optracker')
else:
    logger = logging.getLogger(__name__)

def dict_to_df(tar_dict, use_p=True):
    logger.info('len(tar_dict.values())={}'.format(len(tar_dict.values())))
    try:
        tar_df = pd.DataFrame(tar_dict).T.rename(columns={0:'x', 1:'y', 2:'p'})
        tar_df.index.names = ['frame', 'name', 'code']
        tar_df = tar_df.astype({'x':'Int64' ,'y':'Int64'})
        if use_p == False:
            tar_df = tar_df.drop('p', axis=1)
    except Exception as e:
        logger.error(e)
        tar_df = None
    return tar_df

## ぜんぶnanのdataframeを生成
def gen_blank_df(frame_pos_list, name_list, code_list, col_num=2):
    cols = [np.nan for i in range(col_num)]

    if frame_pos_list is not None and code_list is not None:
        tar_dict = {(f,n,c):cols for f in frame_pos_list for n in name_list for c in code_list}
        names = ['frame', 'name', 'code']
    elif frame_pos_list is not None and code_list is None:
        tar_dict = {(f,n):cols for f in frame_pos_list for n in name_list}
        names = ['frame', 'name']
    else:
        tar_dict = {(n,c):cols for n in name_list for c in code_list}
        names = ['name', 'code']

    m_index = pd.MultiIndex.from_tuples(tar_dict.keys(), names=names)
    blank_df= pd.DataFrame(list(tar_dict.values()), index=m_index)
    return blank_df

def concat(tar_trk_path, add_df):
    if os.path.exists(tar_trk_path):
        dtyp = {'frame':'int32', 'name':'object', 'code':'object', 'x':'Int64', 'y':'Int64'}
        trk_df = pd.read_csv(tar_trk_path, dtype=dtyp).set_index(['frame', 'name', 'code'])
        new_df = pd.concat([trk_df, add_df]).sort_index()
        new_df.to_csv(tar_trk_path)
    else:
        add_df.to_csv(tar_trk_path)

