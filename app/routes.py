from flask import Blueprint, render_template

home = Blueprint('home', __name__)


@home.route('/')
def index():
    """主页面"""
    return render_template('index.html')