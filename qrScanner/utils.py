import os
os.environ['OPENCV_LOG_LEVEL'] = 'OFF'  # 在导入 cv2 之前设置

import cv2
import numpy as np
import base64
import re
from db import save_to_database

cv2.setLogLevel(0)  # 0 = SILENT, 1 = ERROR, 2 = WARN, 3 = INFO, 4 = DEBUG

def get_available_cameras():
    """获取可用的摄像头列表"""
    cameras = []
    # 测试前10个摄像头索引
    for i in range(10):
        cap = cv2.VideoCapture(i)
        if cap.isOpened():
            cameras.append(i)
            cap.release()
    return cameras


def decode_qr_code(image_data):
    """使用OpenCV解码二维码图像"""
    try:
        # 将base64图像数据转换为OpenCV图像格式
        image_data = image_data.split(',')[1]  # 移除数据URL前缀
        nparr = np.frombuffer(base64.b64decode(image_data), np.uint8)
        img = cv2.imdecode(nparr, cv2.IMREAD_COLOR)

        # 使用OpenCV的QRCodeDetector
        qr_decoder = cv2.QRCodeDetector()

        # 检测并解码二维码
        data, points, _ = qr_decoder.detectAndDecode(img)

        results = []
        if data and len(data) > 0:
            # 计算二维码的位置
            if points is not None:
                points = points[0].astype(int)
                x, y, w, h = cv2.boundingRect(points)
            else:
                x, y, w, h = 0, 0, 0, 0

            # 尝试确定二维码类型
            qr_type = "QRCODE"
            if data.startswith("http://") or data.startswith("https://"):
                qr_type = "URL"
            elif re.match(r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$', data):
                qr_type = "EMAIL"
            elif re.match(r'^[A-Za-z]{2}\d{9}[A-Za-z]{2}$', data):
                qr_type = "TRACKING"

            results.append({
                'type': qr_type,
                'data': data,
                'position': [x, y, w, h]
            })

            # 保存到数据库
            save_to_database(qr_type, data)

        return results
    except Exception as e:
        print(f"解码错误: {e}")
        return []