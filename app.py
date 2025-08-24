from flask import Flask, render_template, request, jsonify
import cv2
import numpy as np
import base64
import threading
import time
import re

app = Flask(__name__)

# 存储扫描结果的全局变量
scanned_data = []
scanned_data_lock = threading.Lock()


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

            # 添加到全局扫描结果列表（如果尚未存在）
            with scanned_data_lock:
                if not any(d['data'] == data for d in scanned_data):
                    scanned_data.append({
                        'type': qr_type,
                        'data': data,
                        'time': time.strftime("%Y-%m-%d %H:%M:%S")
                    })

        return results
    except Exception as e:
        print(f"解码错误: {e}")
        return []


@app.route('/')
def index():
    """主页面"""
    return render_template('index.html')


@app.route('/cameras')
def get_cameras():
    """获取可用摄像头列表"""
    cameras = get_available_cameras()
    return jsonify({'cameras': cameras})


@app.route('/scan', methods=['POST'])
def scan_qr():
    """处理二维码扫描请求"""
    try:
        data = request.get_json()
        if not data or 'image' not in data:
            return jsonify({'error': '没有图像数据'}), 400

        results = decode_qr_code(data['image'])
        return jsonify({'results': results})
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@app.route('/history')
def get_history():
    """获取扫描历史"""
    with scanned_data_lock:
        return jsonify({'history': scanned_data})


@app.route('/clear', methods=['POST'])
def clear_history():
    """清空扫描历史"""
    with scanned_data_lock:
        scanned_data.clear()
    return jsonify({'status': 'cleared'})


if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5000)