import sys
import os
import time
import logging
from dotenv import load_dotenv
from utils.database import get_db_connection, create_trades_table
from trading.trader import trade_job

<<<<<<< HEAD:main_backup.py
# ----- 슬랙 알림 함수 -----
SLACK_WEBHOOK_URL = os.getenv("SLACK_WEBHOOK_URL", "https://hooks.slack.com/services/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")
=======
# 프로젝트 루트 디렉토리를 Python 경로에 추가
sys.path.append(os.path.join(os.path.dirname(__file__), 'auto_trader_upbit_git'))
>>>>>>> 19e2b78 (커밋 메시지를 여기에 작성하세요):main.py

# 로깅 설정
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# 환경 변수 로드
load_dotenv()

def main():
    conn = None
    try:
        logger.info("프로그램 시작")
        conn = get_db_connection()
        create_trades_table(conn)
        
        while True:
            try:
                logger.info("거래 작업 시작")
                trade_job(conn)
            except Exception as e:
                logger.error(f"거래 중 오류 발생: {e}")
            
            logger.info("60초 대기")
            time.sleep(60)
    
    except KeyboardInterrupt:
        logger.info("사용자에 의해 프로그램 종료")
    except Exception as e:
        logger.critical(f"예기치 못한 오류 발생: {e}")
    finally:
        if conn:
            conn.close()
        logger.info("프로그램 종료")

# ----- Flask 웹 애플리케이션 -----
from flask import Flask, render_template, jsonify, request, redirect, url_for
import threading
from datetime import datetime, timedelta

app = Flask(__name__)

# 트레이딩 상태 관리
trading_active = False
trading_thread = None

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/api/status')
def get_status():
    """현재 트레이딩 상태 및 잔고 정보"""
    try:
        krw_balance = get_krw_balance()
        coin_balances = {}
        total_value = krw_balance
        
        for market in MARKETS:
            coin = market.split('-')[1]
            balance = get_balance(coin)
            if balance > 0:
                # 현재 가격으로 KRW 환산
                df = get_candles(market, 'days', 1)
                if not df.empty:
                    price = df['close'].iloc[-1]
                    value = balance * price
                    coin_balances[coin] = {
                        'balance': balance,
                        'value': value,
                        'price': price
                    }
                    total_value += value
        
        return jsonify({
            'trading_active': trading_active,
            'krw_balance': krw_balance,
            'coin_balances': coin_balances,
            'total_value': total_value,
            'positions': positions
        })
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/trades')
def get_trades():
    """거래 내역 조회"""
    try:
        conn = sqlite3.connect('trade.db')
        query = """
        SELECT time, market, action, price, amount, pnl 
        FROM trades 
        ORDER BY time DESC 
        LIMIT 50
        """
        df = pd.read_sql_query(query, conn)
        conn.close()
        
        trades = df.to_dict('records')
        return jsonify(trades)
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/performance')
def get_performance():
    """수익률 통계"""
    try:
        conn = sqlite3.connect('trade.db')
        query = """
        SELECT market, SUM(pnl) as total_pnl, COUNT(*) as trade_count
        FROM trades 
        WHERE action LIKE 'SELL%'
        GROUP BY market
        """
        df = pd.read_sql_query(query, conn)
        
        # 전체 통계
        total_query = """
        SELECT SUM(pnl) as total_profit, 
               COUNT(*) as total_trades,
               AVG(pnl) as avg_profit
        FROM trades 
        WHERE action LIKE 'SELL%'
        """
        total_df = pd.read_sql_query(total_query, conn)
        conn.close()
        
        return jsonify({
            'by_market': df.to_dict('records'),
            'total': total_df.to_dict('records')[0] if not total_df.empty else {}
        })
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/charts/<market>')
def get_chart_data(market):
    """차트 데이터"""
    try:
        df = get_candles(market, 'days', 30)
        if df.empty:
            return jsonify({'error': '데이터 없음'}), 404
        
        chart_data = []
        for _, row in df.iterrows():
            chart_data.append({
                'time': row['date'],
                'open': row['open'],
                'high': row['high'],
                'low': row['low'],
                'close': row['close']
            })
        
        return jsonify(chart_data)
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/trading/start', methods=['POST'])
def start_trading():
    """자동매매 시작"""
    global trading_active, trading_thread
    
    if not trading_active:
        trading_active = True
        trading_thread = threading.Thread(target=trading_loop, daemon=True)
        trading_thread.start()
        return jsonify({'message': '자동매매가 시작되었습니다'})
    else:
        return jsonify({'message': '이미 실행중입니다'}), 400

@app.route('/api/trading/stop', methods=['POST'])
def stop_trading():
    """자동매매 중지"""
    global trading_active
    trading_active = False
    return jsonify({'message': '자동매매가 중지되었습니다'})

def trading_loop():
    """백그라운드 트레이딩 루프"""
    while trading_active:
        try:
            trade_job()
            time.sleep(60)  # 1분 대기
        except Exception as e:
            logging.error(f"Trading loop error: {e}")
            time.sleep(10)

if __name__ == "__main__":
<<<<<<< HEAD:main_backup.py
    app.run(host='0.0.0.0', port=int(os.environ.get('PORT', 5000)), debug=False)
        
=======
    main()
>>>>>>> 19e2b78 (커밋 메시지를 여기에 작성하세요):main.py
