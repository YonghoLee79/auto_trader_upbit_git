"""
웹 애플리케이션 라우트
"""
from flask import jsonify
from config import MARKETS
from trading.upbit_api import get_krw_balance, get_balance, get_candles
from trading.position import position_manager
from utils.database import db_manager
from web.utils import get_trading_status

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
            'trading_active': get_trading_status(),
            'krw_balance': krw_balance,
            'coin_balances': coin_balances,
            'total_value': total_value,
            'positions': position_manager.get_all_positions()
        })
    except Exception as e:
        return jsonify({'error': str(e)}), 500

def get_trades():
    """거래 내역 조회"""
    try:
        trades = db_manager.get_trades()
        return jsonify(trades)
    except Exception as e:
        return jsonify({'error': str(e)}), 500

def get_performance():
    """수익률 통계"""
    try:
        performance = db_manager.get_performance_stats()
        return jsonify(performance)
    except Exception as e:
        return jsonify({'error': str(e)}), 500

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

def start_trading():
    """자동매매 시작"""
    try:
        from web.utils import get_trading_status, set_trading_status, set_trading_thread
        import threading
        from trading.trader import trade_job
        
        if not get_trading_status():
            set_trading_status(True)
            
            def trading_loop():
                """백그라운드 트레이딩 루프"""
                import time
                import logging
                while get_trading_status():
                    try:
                        trade_job()
                        time.sleep(60)  # 1분 대기
                    except Exception as e:
                        logging.error(f"Trading loop error: {e}")
                        time.sleep(10)
            
            thread = threading.Thread(target=trading_loop, daemon=True)
            thread.start()
            set_trading_thread(thread)
            
            return jsonify({'message': '자동매매가 시작되었습니다'})
        else:
            return jsonify({'message': '이미 실행중입니다'}), 400
    except Exception as e:
        return jsonify({'error': str(e)}), 500

def stop_trading():
    """자동매매 중지"""
    try:
        from web.utils import set_trading_status
        
        set_trading_status(False)
        return jsonify({'message': '자동매매가 중지되었습니다'})
    except Exception as e:
        return jsonify({'error': str(e)}), 500
