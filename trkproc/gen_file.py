import sys,os
import traceback
import pathlib

import pandas as pd

dir_path = pathlib.Path(__file__).resolve().parent
sys.path.append(str(dir_path))
import op_point_measurement
import lineplot

from trkproc import logger

class GenFile:
    def __init__(self, trk_path, mevent_path, rolling_mean_window):
        logger.info('trk_path={} mevent_path={} rolling_mean_window={}'.format(trk_path, mevent_path, rolling_mean_window))
        self.rolling_mean_window = rolling_mean_window
        self.mevent_path = pathlib.Path(mevent_path)
        self.fpm = op_point_measurement.OpPointMeasurement(trk_path, str(mevent_path), rolling_mean_window)
        self.lp = None
        self.rect_info_list = []

    def load_calclist(self, calclist_path):
        logger.info('calclist_path={}'.format(calclist_path))
        try:
            self.df_list = self.fpm.load_calclist(calclist_path)
            name_list = [x['df'].index.get_level_values('name').unique().tolist() for x in self.df_list]
            logger.debug('name_list={}'.format(name_list))
            return 'ok'
        except Exception as e:
            logger.error(e)
            return 'ng'

    def set_tar_event_id(self, event_id):
        try:
            self.event_id = event_id
            ok = self.fpm.set_event_id(event_id)
            event_comment = self.fpm.get_event_comments()
            self.min_pos = int(event_comment[0]['frame'])
            if ok == False:
                logger.error('load failed (no event_id)')
                raise Exception('load failed (no event_id)')
        except Exception as e:
            logger.error(self._traceback_parser(e))
            raise Exception(e)

    def set_param(self, graph_width, graph_height, x_tick, ylim_min, ylim_max):
        logger.info('graph_width={} graph_height={} x_tick={} ylim_min={} ylim_max={}'.format(graph_width, graph_height, x_tick, ylim_min, ylim_max))
        try:
            ## グラフに表示したくないmemberはdrawをOFFにする
            self.member_list = [{'member':m, 'draw':'ON'} for m in self.fpm.get_member()]
            logger.info('member_list={}'.format(self.member_list))

            self.graph_width = graph_width
            self.graph_height = graph_height
            self.x_tick = x_tick

            if '' in [ylim_min, ylim_max]:
                self.ylim = None
            else:
                self.ylim = [float(ylim_max), float(ylim_min)]
        except Exception as e:
            logger.error(self._traceback_parser(e))
            raise Exception(e)

    def set_fps(self, fps):
        logger.info('fps={}'.format(fps))
        self.fps = fps

    def set_rect_info(self, rect_info_list):
        logger.info('rect_info_list={}'.format(rect_info_list))
        self.rect_info_list = rect_info_list

    def before_save_proc(self, ext):
        tardir = self.mevent_path.parent.parent.joinpath('graph')
        tardir.mkdir(exist_ok=True)
        org_file_name = (self.mevent_path.name).split('.')[0]
        event_comment = self.fpm.get_event_comments()
        file_name = '{}_{}_{}_{}'.format(org_file_name, event_comment[0]['comment'], self.event_id, self.rolling_mean_window)
        dst_path = tardir.joinpath(file_name+'.'+ext)
        logger.info('{}_path={}'.format(ext, str(dst_path)))
        return dst_path

    def save_png(self):
        try:
            png_path = self.before_save_proc('png')
            op_df = pd.concat([x['df'] for x in self.df_list], axis=1)

            if self.lp is None:
                self.lp = lineplot.LinePlot(self.fps, (self.graph_width, self.graph_height))

            draw_member = [m['member'] for m in self.member_list if m['draw']=='ON']
            self.lp.set_plot_data(op_df, draw_member)

#            offset = self.min_pos
#            self.lp.set_rect_info(self.rect_info_list, offset)

            self.lp.clear_line()
            for legend,color,points in [(x['legend'],x['color'],x['points']) for x in self.df_list]:
                self.lp.set_line(legend, color, points)
            self.lp.plot_lines(ylim=self.ylim, tick_interval_sec=self.x_tick)
            self.lp.plot_violins(ylim=self.ylim)
            self.lp.write(png_path)
        except Exception as e:
            logger.error(self._traceback_parser(e))
#            logger.error('self.df_list\n{}'.format(self.df_list))
            return 'ng'
        return 'ok'

    def save_csv(self):
        try:
            csv_path = self.before_save_proc('csv')
            op_df = pd.concat([x['df'] for x in self.df_list], axis=1)

            op_df['sec'] = op_df.index.get_level_values('frame') / self.fps
            op_df.to_csv(csv_path)
        except Exception as e:
            logger.error(self._traceback_parser(e))

    def get_graph_path(self):
        graph_dir = self.mevent_path.parent.parent.joinpath('graph')
        graph_dir.mkdir(exist_ok=True)
        return graph_dir

    def _traceback_parser(self, e):
        line = traceback.format_tb(e.__traceback__)[0].split(', ')[1]
        return '{},{}'.format(line, e)

if __name__ == "__main__":
    pass

