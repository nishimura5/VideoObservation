import datetime

import cv2

txt_font = cv2.FONT_HERSHEY_PLAIN
font_size = 1

#txt_font = cv2.FONT_HERSHEY_SIMPLEX
#font_size = 0.6

## add_time: fpsを入れると換算して一緒に表示
def put_frame_pos(src_img, frame_pos, out_mov_resize=1.0, add_time=None):
    pos = (int(10*out_mov_resize), int(20*out_mov_resize))
    cv2.putText(src_img, '%d'%frame_pos, pos, txt_font, font_size, (0, 0, 0), 3)
    cv2.putText(src_img, '%d'%frame_pos, pos, txt_font, font_size, (255, 255, 255), 1)
    if add_time is not None:
        pos = (int(10*out_mov_resize), int(40*out_mov_resize))
        sec = int(frame_pos / add_time)
        td = datetime.timedelta(seconds=sec)
        cv2.putText(src_img, '%s'%td, pos, txt_font, font_size, (0, 0, 0), 3)
        cv2.putText(src_img, '%s'%td, pos, txt_font, font_size, (255, 255, 255), 1)

def put_name(src_img, name, pos):
    pos = (pos[0]-len(str(name))*12, pos[1])
    cv2.putText(src_img, '%s'%name, pos, txt_font, font_size, (0, 0, 255), 1)

