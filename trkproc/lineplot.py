import sys,os
from decimal import Decimal, ROUND_HALF_UP, ROUND_HALF_EVEN

import pandas as pd
import numpy as np
import matplotlib
## TkAggだとエラーになったのでAggを使用
matplotlib.use("Agg")
from matplotlib import pyplot as plt
from matplotlib.ticker import FuncFormatter, MultipleLocator, IndexLocator
from matplotlib import patches

import trkproc
from trkproc import logger

plt.rcParams['font.size'] = 9
plt.rcParams['font.family'] = 'sans-serif'
plt.rcParams['font.sans-serif'] = ['Yu Gothic']

class LinePlot:
    def __init__(self, fps, graph_size_mm):
        self.data_df = None
        self.fps = fps

        graph_size_inch = (graph_size_mm[0]/25.4, graph_size_mm[1]/25.4)
        self.fig = plt.figure(figsize=graph_size_inch, dpi=300)

        self.rect_list = []

        self.clear_line()

    ## set_plot_data()でtrkデータを入れないと使えないのでインスタンス生成後は必ず呼ぶこと
    def set_plot_data(self, data_df, member_list=None):
        self.data_df = data_df
        if member_list is None:
            self.member_arr = self.data_df.index.get_level_values('name').unique().to_numpy()
        else:
            self.member_arr = np.array(member_list)
        self.__fill()
        self.__make_time_df()
        self.time_arr = self.time_df['time_str'].to_numpy()

    def set_line(self, legend, color, points):
        self.line_list.append({'legend':legend, 'color':color, 'points':points})

    def clear_line(self):
        self.line_list = []

    ## グラフ中に書き込む長方形情報を追加
    ## rect_info_list = [[{'left':xxx, 'right':xxx, 'width':xxx}, ...], [{...}, ...]]
    ## top,bottomはplot_linesで決定
    ## offset rect_info_listの値は動画の開始を0としているがグラフ描画は指定したevent_idの開始時刻を0とするためオフセットが必要
    def set_rect_info(self, rect_info_list, offset):
        logger.info('rect_info_list={} offset={}'.format(rect_info_list, offset))
        try:
            for name in self.member_arr:
                self.rect_list.append([{'left':x['left']-offset, 'right':x['right']-offset, 'width':x['width']} for x in rect_info_list[int(name)]])
        except Exception as e:
            logger.error(e)
            logger.error('name={}'.format(name))
            raise Exception(e)

    ## ylim = (top, btm)
    def plot_lines(self, ylim=None, zero_line=True, tick_interval_sec=30):
        self.gs = self.fig.add_gridspec(self.member_arr.size, 2)
        for i, name in enumerate(self.member_arr):
            try:
                ax = self.fig.add_subplot(self.gs[i, 0])

                if ylim is not None:
                    ax.set_ylim(top=ylim[0], bottom=ylim[1])
                    rect_height = ylim[0] - ylim[1]
                    rect_bottom = ylim[1]
                else:
                    rect_height = 100
                    rect_bottom = 0

                ## 横線
                if zero_line == True:
                    ax.plot([0, self.time_arr.size], [0,0], 'k-', linewidth=0.5)

                ## 長方形
                if len(self.rect_list) > 0:
                    for rect_info in self.rect_list[i]:
                        rectangle = patches.Rectangle((rect_info['left'], rect_bottom), width=rect_info['width'], height=rect_height, fill=True, facecolor='gray', alpha=0.2)
                        ax.add_patch(rectangle)

                ## メインのプロット
                for line in self.line_list:
                    print('%d [%s] %s' % (i, name, line))
                    ax.plot(self.time_arr, self.data_df.loc[pd.IndexSlice[:,name], line['points']].to_numpy(), color=line['color'], linewidth=0.5, label=line['legend'])
            except Exception as e:
                logger.error(e)
                logger.error('self.data_df={}'.format(self.data_df))
#                logger.error('self.time_arr={}'.format(self.time_arr))
                raise Exception(e)

            try:
                ax.set_ylabel(name)
                rounder = lambda x: Decimal(str(x)).quantize(Decimal('0'), rounding=ROUND_HALF_UP)
                x_ticks = np.arange(0, self.time_arr.size+1, self.fps*tick_interval_sec)
                x_ticks = np.fromiter(map(rounder, x_ticks), dtype=np.int)
#                logger.debug('{}'.format(x_ticks))
#                for n in x_ticks:
#                    logger.debug('{}'.format(self.time_arr[n]))

                ax.set_xticks(x_ticks)
                ax.xaxis.set_major_formatter(FuncFormatter(lambda x, pos: "{}".format(self.time_arr[x][3:8])))
                ax.xaxis.grid(which='major', color='dimgray', linestyle='dashed', linewidth=0.3)

                ## 補助線
                ml_minor = IndexLocator(base=self.fps*tick_interval_sec, offset=int(self.fps*tick_interval_sec*0.5))
                ax.xaxis.set_minor_locator(ml_minor)
                ax.xaxis.grid(which='minor', color='dimgray', linestyle='dashed', linewidth=0.2)

#                if i < self.member_arr.size-1:
#                    ax.tick_params(labelbottom=False, bottom=False)
                if i == 0:
                    ax.legend()
            except Exception as e:
                logger.error(e)
                logger.error('{}, {}'.format(self.fps, tick_interval_sec))
                raise Exception(e)

    def write(self, tar_path):
        logger.info('tar_path={}'.format(tar_path))
        try:
            plt.tight_layout()
            plt.savefig(tar_path)
            plt.clf()
        except Exception as e:
            logger.error(e)
            logger.error(self.line_list)
            print(self.time_arr)
            print(self.data_df)

    ## ylim = (top, btm)
    def plot_violins(self, ylim=None):
        self.gs = self.fig.add_gridspec(self.member_arr.size, 2)
        logger.info('self.line_list={}'.format(self.line_list))
        try:
            for i, name in enumerate(self.member_arr):
                ax = self.fig.add_subplot(self.gs[i, 1])
                datas = [self.data_df.loc[pd.IndexSlice[:,name], p['points']].dropna().to_numpy() for p in self.line_list]
                labels = [p['legend'] for p in self.line_list]
                vparts = ax.violinplot(datas, showmeans=True, showextrema=True, showmedians=True)
                ax.set_xticks(range(1,len(labels)+1))
                ax.set_xticklabels(labels)

                for partname in ('cbars', 'cmins', 'cmaxes', 'cmeans', 'cmedians'):
                    vpart = vparts[partname]
                    if partname == 'cmeans':
                        vpart.set_edgecolor('#ee3333')  #平均値は赤線
                    elif partname == 'cmedians':
                        vpart.set_edgecolor('#3333ee')  #中央値は青線
                    else:
                        vpart.set_edgecolor('#333333')
                    vpart.set_linewidth(0.5)

                colors = [p['color'] for p in self.line_list]
                for vpart, color in zip(vparts['bodies'], colors):
                    vpart.set_facecolor(color)
                    vpart.set_edgecolor(color)
                    vpart.set_linewidth(0.5)

                if ylim is not None:
                    ax.set_ylim(top=ylim[0], bottom=ylim[1])
        except Exception as e:
            logger.error(e)
            logger.error(datas)
            raise Exception(e)


    ## frame番号を時刻(secとtimedeltaとstring)に変換したカラムを生成
    def __make_time_df(self):
        time_df = pd.DataFrame()
        time_df['frame'] = self.data_df.reset_index()['frame'].unique()
        time_df['sec'] = time_df['frame'] / self.fps
        time_df['time'] = pd.to_timedelta(time_df['sec'], unit='sec')
        time_df['time_str'] = time_df['time'].astype('str')
        time_df['time_str'] = time_df['time_str'].apply(lambda x: x.split(' ')[-1])
        self.time_df = time_df.set_index(['frame'])

    def __fill(self):
        try:
            frame_arr = self.data_df.index.get_level_values('frame').unique().to_numpy()
            dummy_df = trkproc.gen_blank_df(frame_arr[:], self.member_arr, None, col_num=len(self.data_df.columns))
            dummy_df = dummy_df.rename(columns={i:v for i,v in enumerate(self.data_df.columns)})

            dummy_df.loc[pd.IndexSlice[:,:],:] = self.data_df.loc[pd.IndexSlice[:,:],:]
            self.data_df = dummy_df
        except Exception as e:
            print(e)
            print(self.data_df)
            print(dummy_df)

    def close(self):
        plt.close()

if __name__ == "__main__":
    pass

