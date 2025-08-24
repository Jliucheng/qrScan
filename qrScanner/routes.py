from flask import Blueprint, jsonify, request
from qrScanner import get_available_cameras, decode_qr_code

scanner = Blueprint('scanner', __name__)


@scanner.route('/cameras')
def get_cameras():
    """获取可用摄像头列表"""
    cameras = get_available_cameras()
    return jsonify({'cameras': cameras})


@scanner.route('/scan', methods=['POST'])
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