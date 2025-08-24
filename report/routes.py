from db import get_db
from flask import Blueprint, jsonify

report = Blueprint('report', __name__)


@report.route('/history')
def get_history():
    """获取扫描历史"""
    try:
        db = get_db()
        cursor = db.cursor()

        # 获取最近的100条记录
        cursor.execute(
            "SELECT qr_type, qr_data, scan_time_local FROM scan_history ORDER BY scan_time_local DESC LIMIT 100"
        )
        history = cursor.fetchall()

        # 转换为字典列表
        history_list = [
            {
                'type': row['qr_type'],
                'data': row['qr_data'],
                'time': row['scan_time_local']
            }
            for row in history
        ]

        return jsonify({'history': history_list})
    except Exception as e:
        print(f"获取历史记录错误: {e}")
        return jsonify({'history': []})


@report.route('/clear', methods=['POST'])
def clear_history():
    """清空扫描历史"""
    try:
        db = get_db()
        cursor = db.cursor()
        cursor.execute("DELETE FROM scan_history")
        db.commit()
        return jsonify({'status': 'cleared', 'message': '历史记录已清空'})
    except Exception as e:
        print(f"清空历史记录错误: {e}")
        return jsonify({'status': 'error', 'message': str(e)}), 500


@report.route('/export', methods=['GET'])
def export_history():
    """导出扫描历史为CSV文件"""
    try:
        db = get_db()
        cursor = db.cursor()

        # 获取所有记录
        cursor.execute(
            "SELECT qr_type, qr_data, scan_time_local FROM scan_history ORDER BY scan_time_local DESC"
        )
        history = cursor.fetchall()

        # 生成CSV内容
        csv_content = "类型,内容,扫描时间\n"
        for row in history:
            # 转义CSV中的特殊字符
            data = str(row['qr_data']).replace('"', '""')
            csv_content += f'"{row["qr_type"]}","{data}","{row["scan_time_local"]}"\n'

        return csv_content, 200, {
            'Content-Type': 'text/csv',
            'Content-Disposition': 'attachment; filename=qr_scan_history.csv'
        }
    except Exception as e:
        print(f"导出历史记录错误: {e}")
        return jsonify({'status': 'error', 'message': str(e)}), 500
