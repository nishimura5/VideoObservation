import datetime
import time

import cv2

txt_font = cv2.FONT_HERSHEY_PLAIN
font_size = 1

#txt_font = cv2.FONT_HERSHEY_SIMPLEX
#font_size = 0.6

## add_time: fpsを入れると換算して一緒に表示
def put_frame_pos(src_img, frame_pos, out_mov_resize=1.0, add_time=None):
    pos = (int(10*out_mov_resize), int(10*out_mov_resize + 10))
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

def draw_body_bone(src_img, landmarks, out_mov_resize):
    points = []
    for landmark in landmarks:
        points.append((int(landmark[0] * out_mov_resize), int(landmark[1] * out_mov_resize)))

    put_line(src_img, points, 0, 1)
    put_line(src_img, points, 0, 15)
    put_line(src_img, points, 15, 17)
    put_line(src_img, points, 0, 16)
    put_line(src_img, points, 16, 18)

    put_line(src_img, points, 1, 2)
    put_line(src_img, points, 2, 3)
    put_line(src_img, points, 3, 4)
    put_line(src_img, points, 1, 5)
    put_line(src_img, points, 5, 6)
    put_line(src_img, points, 6, 7)

    put_line(src_img, points, 8, 9)
    put_line(src_img, points, 8, 12)
    put_line(src_img, points, 8, 1)

    put_line(src_img, points, 23, 22)
    put_line(src_img, points, 22, 11)
    put_line(src_img, points, 11, 10)
    put_line(src_img, points, 10, 9)
    put_line(src_img, points, 11, 24)

    put_line(src_img, points, 20, 19)
    put_line(src_img, points, 19, 14)
    put_line(src_img, points, 14, 13)
    put_line(src_img, points, 13, 12)
    put_line(src_img, points, 14, 21)

def draw_face_bone(src_img, landmarks, out_mov_resize):
    points = []
    for landmark in landmarks:
        points.append((int(landmark[0] * out_mov_resize), int(landmark[1] * out_mov_resize)))

    put_line(src_img, points, 17, 18)
    put_line(src_img, points, 18, 19)
    put_line(src_img, points, 19, 20)
    put_line(src_img, points, 20, 21)
    put_line(src_img, points, 22, 23)
    put_line(src_img, points, 23, 24)
    put_line(src_img, points, 24, 25)
    put_line(src_img, points, 25, 26)

    put_line(src_img, points, 36, 37)
    put_line(src_img, points, 37, 38)
    put_line(src_img, points, 38, 39)
    put_line(src_img, points, 39, 40)
    put_line(src_img, points, 40, 41)
    put_line(src_img, points, 41, 36)

    put_line(src_img, points, 42, 43)
    put_line(src_img, points, 43, 44)
    put_line(src_img, points, 44, 45)
    put_line(src_img, points, 45, 46)
    put_line(src_img, points, 46, 47)
    put_line(src_img, points, 47, 42)

    put_line(src_img, points, 27, 28)
    put_line(src_img, points, 28, 29)
    put_line(src_img, points, 29, 30)

    put_line(src_img, points, 31, 32)
    put_line(src_img, points, 32, 33)
    put_line(src_img, points, 33, 34)
    put_line(src_img, points, 34, 35)

    put_line(src_img, points, 48, 49)
    put_line(src_img, points, 49, 50)
    put_line(src_img, points, 50, 51)
    put_line(src_img, points, 51, 52)
    put_line(src_img, points, 52, 53)
    put_line(src_img, points, 53, 54)
    put_line(src_img, points, 54, 55)
    put_line(src_img, points, 55, 56)
    put_line(src_img, points, 56, 57)
    put_line(src_img, points, 57, 58)
    put_line(src_img, points, 58, 59)
    put_line(src_img, points, 59, 48)

    put_line(src_img, points, 60, 61)
    put_line(src_img, points, 61, 62)
    put_line(src_img, points, 62, 63)
    put_line(src_img, points, 63, 64)
    put_line(src_img, points, 64, 65)
    put_line(src_img, points, 65, 66)
    put_line(src_img, points, 66, 67)
    put_line(src_img, points, 67, 60)

def put_line(src_img, points, a, b):
    if (points[a][0]==0 and points[a][1]==0) or (points[b][0]==0 and points[b][1]==0):
        return
    cv2.line(src_img, points[a], points[b], (250, 250, 250), 1, lineType=cv2.LINE_AA)

