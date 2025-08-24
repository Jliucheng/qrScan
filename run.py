from flask import Flask, g

from app.routes import home
from qrScanner.routes import scanner
from report.routes import report
from db import init_db

_initialize = False

app = Flask(__name__)


@app.before_request
def before_request():
    global _initialize
    if not _initialize:
        initialize()
        _initialize = True

def initialize():
    with app.app_context():
        init_db()


@app.teardown_appcontext
def close_connection(exception):
    """关闭数据库连接"""
    db = getattr(g, '_database', None)
    if db is not None:
        db.close()
    if exception is not None:
        app.logger.error(exception)


app.register_blueprint(
    home,
    url_prefix='/',
    static_folder='static',  # 可选的静态文件配置
    template_folder='templates'
)

app.register_blueprint(
    scanner,
    url_prefix='/',
    static_folder='static',  # 可选的静态文件配置
    template_folder='templates'
)

app.register_blueprint(
    report,
    url_prefix='/',
    static_folder='static',  # 可选的静态文件配置
    template_folder='templates'
)


if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5000)