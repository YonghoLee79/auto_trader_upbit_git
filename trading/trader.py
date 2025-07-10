"""
메인 트레이딩 로직
"""
import time
import logging
from config import MARKETS, TRADE_AMOUNT, MAX_RATIO
from trading.upbit_api import get_candles, get_krw_balance, buy_market_order, sell_market_order, has_coin
from trading.strategies import get_combined_signals
from trading.position import position_manager
from utils.database import db_manager
from utils.notifications import slack_send

def trade_job():
    """메인 트레이딩 작업"""
    try:
        krw_balance = get_krw_balance()
        logging.info(f"KRW 잔고: {krw_balance}")
        slack_send(f"KRW 잔고: {krw_balance}")
        max_trade = krw_balance * MAX_RATIO
        
        # 모든 캔들 데이터 미리 받아놓기(중복호출 방지)
        candle_cache = {}
        for market in MARKETS:
            candle_cache[market] = {
                "days": get_candles(market, 'days', 60),
                "hour": get_candles(market, 'minutes/60', 60),
                "min5": get_candles(market, 'minutes/5', 60)
            }
            time.sleep(0.2)
        
        for market in MARKETS:
            df_day = candle_cache[market]["days"]
            df_hour = candle_cache[market]["hour"]
            df_5m = candle_cache[market]["min5"]
            
            if df_day.empty or df_hour.empty or df_5m.empty:
                continue
            
            # 시그널 계산
            buy_score, sell_score = get_combined_signals(df_day, df_hour, df_5m)
            cur_price = df_day['close'].iloc[-1]
            
            # 익절/손절 자동 매도
            pos_check = position_manager.check_position(market, cur_price)
            if pos_check in ["tp", "sl"]:
                resp = sell_market_order(market)
                if resp:
                    pos = position_manager.get_position(market)
                    if pos:
                        entry = pos['entry']
                        amount = pos['amount']
                        profit = position_manager.calc_real_profit(entry, cur_price)
                        db_manager.log_trade(
                            time.strftime("%Y-%m-%d %H:%M:%S"), 
                            market, 
                            f"SELL-{pos_check}", 
                            cur_price, 
                            amount, 
                            profit
                        )
                        slack_send(f"[{market}] {pos_check} 매도, 실질수익률 {profit*100:.2f}%")
                        position_manager.remove_position(market)
                continue
            
            # 매도 신호: 2개 이상 -1 시그널
            if sell_score >= 2 and has_coin(market):
                resp = sell_market_order(market)
                logging.info(f"{market}: 시그널 합 {sell_score}로 매도 시도")
                slack_send(f"{market}: 시그널 합 {sell_score}로 매도 시도")
                if resp:
                    pos = position_manager.get_position(market)
                    if pos:
                        entry = pos['entry']
                        amount = pos['amount']
                        profit = position_manager.calc_real_profit(entry, cur_price)
                        db_manager.log_trade(
                            time.strftime("%Y-%m-%d %H:%M:%S"), 
                            market, 
                            "SELL", 
                            cur_price, 
                            amount, 
                            profit
                        )
                        slack_send(f"[{market}] 다중시그널 매도, 실질수익률 {profit*100:.2f}%")
                        position_manager.remove_position(market)
                continue
            
            # 매수: 2개 이상 +1 시그널
            if (buy_score >= 2 and not has_coin(market) and 
                krw_balance >= TRADE_AMOUNT and TRADE_AMOUNT <= max_trade):
                resp = buy_market_order(market, TRADE_AMOUNT)
                if resp and 'price' in resp:
                    price = float(resp['price'])
                    amount = TRADE_AMOUNT / price
                    position_manager.add_position(market, price, amount)
                    db_manager.log_trade(
                        time.strftime("%Y-%m-%d %H:%M:%S"), 
                        market, 
                        "BUY", 
                        price, 
                        amount, 
                        0
                    )
                    slack_send(f"[{market}] 다중시그널 매수, 매입가 {price}")
                continue
            
            logging.info(f"{market}: 대기 (시그널합계: {buy_score}, {sell_score})")
        
        # 시장 급변동 감지
        for market in MARKETS:
            df = get_candles(market, 'days', 2)
            time.sleep(0.1)
            if len(df) < 2:
                continue
            change = (df['close'].iloc[-1] - df['close'].iloc[-2]) / df['close'].iloc[-2]
            if abs(change) > 0.07:
                slack_send(f"[이벤트] {market} 단기 급변동 {change*100:.2f}% 발생!")
                
    except Exception as e:
        logging.error(f"trade_job 예외 발생: {str(e)}")
        slack_send(f"trade_job 예외 발생: {str(e)}")

def trading_loop():
    """백그라운드 트레이딩 루프"""
    while True:
        try:
            trade_job()
            time.sleep(60)  # 1분 대기
        except Exception as e:
            logging.error(f"Trading loop error: {e}")
            time.sleep(10)
