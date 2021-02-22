import sys, os
import math
import cv2
import numpy as np

from optracker import logger

class DirectionEstimation:
    def __init__(self, src_img, axis_length=None):
        img_shape = src_img.shape
        self.src_img = src_img
        self.model_points = np.array([
            (0.0, 0.0, 0.0),          # 0  nose
            ( 45.7, 46.2, -33.6),     # 36 right eye
            (-45.7, 46.2, -33.6),     # 45 left eye
            ( 72.85, 10.3, -112.1),   # 17 right ear
            (-72.85, 10.3, -112.1),   # 18 left ear
            ( 22.8, -47.5, -14.8),    # 48 right mouth
            (-22.8, -47.5, -14.8),    # 54 left mouth
            ])

        ## axis_length == None のときは矢印を描画しない
        self.draw_axis = True
        if axis_length is None:
            self.draw_axis = False
            self.axis = np.array([0.0, 0.0, 100])
        else:
            self.axis = np.array([0.0, 0.0, axis_length])

        self.dist_coeffs = np.zeros((4,1)) # Assuming no lens distortion

        self.r_eye_points = [36, 37, 38, 39, 40, 41]
        self.l_eye_points = [42, 43, 44, 45, 46, 47]

        self.ERR_VALUE = np.nan

    def calc_direction(self, b_points, f_points):
        ## 頭部姿勢推定に必要な点(目、鼻、口)が検出されているか
        points = np.array([b_points[0][0], f_points[30][0], f_points[36][0], f_points[45][0], f_points[48][0], f_points[54][0]])
        if np.any(np.isnan(points)):
            logger.debug('np.isnan(points)')
            return self.ERR_VALUE, self.ERR_VALUE, self.ERR_VALUE,self.ERR_VALUE, self.ERR_VALUE
        if np.any(points <= 0):
            logger.debug('np.any(points <= 0)')
            return self.ERR_VALUE, self.ERR_VALUE, self.ERR_VALUE,self.ERR_VALUE, self.ERR_VALUE

        ## 右耳隠れの場合は右目で代用
        if b_points[17][2] < 0.2 and b_points[18][2] >= 0.2:
            b_points[17] = f_points[36]
        ## 左耳隠れの場合は左目で代用
        elif b_points[18][2] < 0.2 and b_points[17][2] >= 0.2:
            b_points[18] = f_points[45]

        center = (b_points[0][0], b_points[0][1])
        focal_length = center[1]
        camera_matrix = np.array(
                             [[focal_length, 0, center[0]],
                             [0, focal_length, center[1]],
                             [0, 0, 1]], dtype = "double"
                             )
        img_points = np.array([
            f_points[30][:2],
            f_points[36][:2],
            f_points[45][:2],
            b_points[17][:2],
            b_points[18][:2],
            f_points[48][:2],
            f_points[54][:2],
            ])
        ok, rotation_vec, translation_vec = cv2.solvePnP(
                self.model_points,
                img_points,
                camera_matrix,
                self.dist_coeffs,
                flags=cv2.SOLVEPNP_UPNP)
#                flags=cv2.SOLVEPNP_ITERATIVE)
        if ok == False:
            logger.info('solvePnp() failed')
            return self.ERR_VALUE, self.ERR_VALUE, self.ERR_VALUE,self.ERR_VALUE, self.ERR_VALUE

        reproject_dst, jacob = cv2.projectPoints(
                self.axis,
                rotation_vec,
                translation_vec,
                camera_matrix,
                self.dist_coeffs
                )

        if np.isnan(reproject_dst[0][0][0]) or np.isnan(reproject_dst[0][0][1]):
            logger.info('projectPoints() failed')
            return self.ERR_VALUE, self.ERR_VALUE, self.ERR_VALUE, self.ERR_VALUE, self.ERR_VALUE

        p1 = (int(img_points[0][0]), int(img_points[0][1]))
        p2 = (int(reproject_dst[0][0][0]), int(reproject_dst[0][0][1]))
        if self.draw_axis == True:
            cv2.arrowedLine(self.src_img, p1, p2, (255,0,0), 2)
            cv2.circle(self.src_img, tuple(f_points[30][:2]), 6, (10, 240, 20), -1)
            cv2.circle(self.src_img, tuple(f_points[36][:2]), 6, (10, 240, 20), -1) ## 右目
            cv2.circle(self.src_img, tuple(f_points[45][:2]), 6, (10, 240, 20), -1) ## 左目
            cv2.circle(self.src_img, tuple(b_points[17][:2]), 6, (10, 240, 20), -1) ## 右耳
            cv2.circle(self.src_img, tuple(b_points[18][:2]), 6, (10, 240, 20), -1) ## 左耳
            cv2.circle(self.src_img, tuple(f_points[48][:2]), 6, (10, 240, 20), -1) ## 右口角
            cv2.circle(self.src_img, tuple(f_points[54][:2]), 6, (10, 240, 20), -1) ## 左口角

        ## ロドリゲスの回転公式
        ret_R, jacob = cv2.Rodrigues(rotation_vec)
        proj_matrix = np.hstack((ret_R, translation_vec))
        euler_angles = cv2.decomposeProjectionMatrix(proj_matrix)[6]

        pitch, yaw, roll = [math.radians(i) for i in euler_angles]
        roll = -math.degrees(math.asin(math.sin(roll)))
        pitch = math.degrees(math.asin(math.sin(pitch)))
        yaw = math.degrees(math.asin(math.sin(yaw)))

        return roll, pitch, yaw, p2[0], p2[1]

    def iris(self, src_img, f_points):
        r_centroid = self.__detect_iris(src_img, f_points, self.r_eye_points)
        l_centroid = self.__detect_iris(src_img, f_points, self.l_eye_points)
        if r_centroid is None or l_centroid is None:
            return None, None

        cv2.circle(self.src_img, tuple(r_centroid), 2, (0,0,244), -1)
        cv2.circle(self.src_img, tuple(l_centroid), 2, (0,0,244), -1)
        return [*r_centroid, 1.0], [*l_centroid, 1.0]

    def __detect_iris(self, src_img, f_points, keypoints):
        gray_img = cv2.cvtColor(src_img, cv2.COLOR_BGR2GRAY)
        mask_img = np.zeros_like(gray_img)
        contours = np.array([f_points[i][:2] for i in keypoints]).astype('int')
        cv2.fillConvexPoly(mask_img, points=contours, color=255)
        dst_img = cv2.bitwise_and(gray_img, mask_img)
        hist = cv2.calcHist([dst_img], [0], None, [256], [0, 256]).astype('int').reshape(-1)
        ## ヒストグラムにおいて3ピクセル以上存在する明るさを閾値として採用
        hist = {k:v for k,v in enumerate(hist) if v > 2}
        white_thresh = np.max(list(hist.keys()))
        if white_thresh == 0:
            return None

        ## 閾値が255になるよう正規化
        gray_img = (dst_img.astype('float') / white_thresh * 255).astype(np.int16)
        gray_img = np.clip(gray_img, 0, 255).astype(np.uint8)

#        cv2.imshow('eye', gray_img)

        white_mask = np.full_like(mask_img, 255)
        dst_img = np.where(mask_img==255, gray_img, white_mask)
        cv2.polylines(dst_img, [contours], True, (255), thickness=3)
        ok, bin_img = cv2.threshold(dst_img, 127, 255, cv2.THRESH_OTSU)
        bin_img = cv2.bitwise_not(bin_img)
        nlabels, labels, stats, centroids = cv2.connectedComponentsWithStats(bin_img, 4, cv2.CV_16U)

        if nlabels > 1:
            sorted_stats_idx = np.argsort(stats[:, 4])
            centroid = centroids[sorted_stats_idx[-2]].astype(int)
        else:
            centroid = None
        return centroid

