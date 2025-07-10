"""
Flask 웹 애플리케이션 메인 파일
"""
import os
import sys
import logging

# 현재 디렉토리를 Python 경로에 추가
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from flask import Flask, render_template
from config import FLASK_HOST, FLASK_PORT, FLASK_DEBUG, LOG_FILE, LOG_FORMAT
from web import routes

# 로그 설정
logging.basicConfig(
    filename=LOG_FILE,
    level=logging.INFO,
    format=LOG_FORMAT
)

# Flask 앱 생성
app = Flask(__name__)

# 메인 페이지
@app.route('/')
def index():
    return render_template('test.html')

# 테스트 페이지
@app.route('/test')
def test():
    return render_template('test.html')

# 풀 버전 페이지
@app.route('/full')
def full():
    return render_template('index.html')

# API 라우트 등록
@app.route('/api/status')
def api_status():
    return routes.get_status()

@app.route('/api/trades')
def api_trades():
    return routes.get_trades()

@app.route('/api/performance')
def api_performance():
    return routes.get_performance()

@app.route('/api/charts/<market>')
def api_charts(market):
    return routes.get_chart_data(market)

@app.route('/api/trading/start', methods=['POST'])
def api_start_trading():
    return routes.start_trading()

@app.route('/api/trading/stop', methods=['POST'])
def api_stop_trading():
    return routes.stop_trading()

if __name__ == "__main__":
    app.run(host=FLASK_HOST, port=FLASK_PORT, debug=FLASK_DEBUG)
