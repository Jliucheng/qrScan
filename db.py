from flask import g
import sqlite3
import os
from datetime import datetime


if os.getenv("env") == "dev":
    from config.config_dev import *
else:
    from config.config_prod import *


def get_db():
    """获取数据库连接"""
    db = getattr(g, '_database', None)
    if db is None:
        # 确保目录存在
        os.makedirs(os.path.dirname(DATABASE) if os.path.dirname(DATABASE) else '.', exist_ok=True)
        db = g._database = sqlite3.connect(DATABASE)
        db.row_factory = sqlite3.Row
    return db


def init_db():
    """初始化数据库 - 修复版本"""
    print("正在初始化数据库...")
    try:
        db = get_db()
        cursor = db.cursor()

        # 检查表是否已存在
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='scan_history'")
        table_exists = cursor.fetchone()

        if not table_exists:
            print("创建扫描记录表...")
            # 创建扫描记录表
            cursor.execute('''
                           CREATE TABLE scan_history
                           (
                               id        INTEGER PRIMARY KEY AUTOINCREMENT,
                               qr_type   TEXT NOT NULL,
                               qr_data   TEXT NOT NULL,
                               scan_time_utc TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                               scan_time_local TIMESTAMP DEFAULT (datetime('now', 'localtime'))
                           )
                           ''')

            # 创建索引以提高查询性能
            print("创建索引...")
            cursor.execute('CREATE INDEX idx_scan_time ON scan_history(scan_time_local)')
            cursor.execute('CREATE INDEX idx_qr_data ON scan_history(qr_data)')

            db.commit()
            print("数据库初始化成功")
        else:
            print("数据库表已存在，跳过初始化")

    except Exception as e:
        print(f"数据库初始化失败: {e}")
        # 尝试重新连接并重试
        try:
            if 'db' in locals():
                db.close()
            # 删除可能损坏的数据库文件
            if os.path.exists(DATABASE):
                os.remove(DATABASE)
            # 重新初始化
            init_db()
        except Exception as inner_e:
            print(f"重试初始化也失败: {inner_e}")

def save_to_database(qr_type, qr_data):
    """将扫描结果保存到数据库"""
    try:
        db = get_db()
        cursor = db.cursor()
        print(qr_data)

        # 检查是否已存在相同数据
        cursor.execute(
            "SELECT id FROM scan_history WHERE qr_data = ? ORDER BY scan_time_local DESC LIMIT 1",
            (qr_data,)
        )
        existing = cursor.fetchone()

        # 如果不存在或最近一次扫描是在5分钟前，则插入新记录
        if not existing or should_insert_again(qr_data):
            cursor.execute(
                "INSERT INTO scan_history (qr_type, qr_data) VALUES (?, ?)",
                (qr_type, qr_data)
            )
            db.commit()
    except Exception as e:
        print(f"数据库保存错误: {e}")


def should_insert_again(qr_data):
    """检查是否应该再次插入相同的二维码数据（避免频繁插入相同数据）"""
    try:
        db = get_db()
        cursor = db.cursor()

        cursor.execute(
            "SELECT scan_time_local FROM scan_history WHERE qr_data = ? ORDER BY scan_time_local DESC LIMIT 1",
            (qr_data,)
        )
        result = cursor.fetchone()

        if result:
            last_scan_time = datetime.strptime(result['scan_time_local'], '%Y-%m-%d %H:%M:%S')
            time_diff = datetime.now() - last_scan_time
            # 如果上次扫描是在5分钟前，则允许再次插入
            return time_diff.total_seconds() > 300  # 5分钟
        return True
    except Exception as e:
        print(f"检查重复数据错误: {e}")
        return True

