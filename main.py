import os
import time
import requests
import pandas as pd
import numpy as np
import sqlite3
import jwt
import uuid
import hashlib
import logging
from dotenv import load_dotenv

# ----- 슬랙 알림 함수 -----
SLACK_WEBHOOK_URL = "https://hooks.slack.com/services/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"

def slack_send(text):
    payload = {"text": text}
    try:
        requests.post(SLACK_WEBHOOK_URL, json=payload, timeout=5)
    except Exception as e:
        logging.error(f"슬랙 전송 오류: {str(e)}")

# ----- 로그 설정 -----
logging.basicConfig(
    filename='trade_log.txt',
    level=logging.INFO,
    format='%(asctime)s | %(levelname)s | %(message)s'
)

# ----- 환경 변수 및 기본 설정 -----
load_dotenv()
ACCESS_KEY = os.getenv("UPBIT_ACCESS_KEY")
SECRET_KEY = os.getenv("UPBIT_SECRET_KEY")
SERVER_URL = "https://api.upbit.com"
MARKETS = ["KRW-DOGE", "KRW-XRP", "KRW-ADA"]
TRADE_AMOUNT = 5000
FEE_RATE = 0.0005
TAX_RATE = 0.0022
MAX_RATIO = 0.2

# ----- DB 설정 -----
conn = sqlite3.connect('trade.db', check_same_thread=False)
c = conn.cursor()
c.execute('''CREATE TABLE IF NOT EXISTS trades
             (time TEXT, market TEXT, action TEXT, price REAL, amount REAL, pnl REAL)''')
conn.commit()

def log_trade(time, market, action, price, amount, pnl):
    c.execute("INSERT INTO trades VALUES (?, ?, ?, ?, ?, ?)", (time, market, action, price, amount, pnl))
    conn.commit()

# ----- Rate Limiter -----
class RateLimiter:
    def __init__(self, max_calls, period):
        self.max_calls = max_calls
        self.period = period
        self.calls = []
    def acquire(self):
        now = time.time()
        self.calls = [t for t in self.calls if now - t < self.period]
        if len(self.calls) >= self.max_calls:
            sleep_time = self.period - (now - self.calls[0])
            if sleep_time > 0:
                time.sleep(sleep_time)
            self.calls = [t for t in self.calls if now - t < self.period]
        self.calls.append(time.time())

rate_limiter = RateLimiter(8, 1)  # Upbit 초당 10회 제한, 여유 있게 8회

# ----- 업비트 API 함수 -----
def get_candles(market, unit='days', count=60, retry=3):
    url = f"{SERVER_URL}/v1/candles/{unit}"
    params = {"market": market, "count": count}
    for attempt in range(retry):
        try:
            rate_limiter.acquire()
            res = requests.get(url, params=params, timeout=5)
            res.raise_for_status()
            data = res.json()
            df = pd.DataFrame(data)
            df = df[['candle_date_time_kst', 'opening_price', 'high_price', 'low_price', 'trade_price']]
            df.columns = ['date', 'open', 'high', 'low', 'close']
            df = df.sort_values(by='date')
            df.reset_index(drop=True, inplace=True)
            return df
        except Exception as e:
            if "429" in str(e):
                logging.warning(f"{market} {unit} 캔들: 429 Rate Limit, 2초 대기 후 재시도")
                time.sleep(2)
            else:
                logging.error(f"{market} {unit} 캔들 데이터 수신 오류: {str(e)}")
                slack_send(f"{market} {unit} 캔들 데이터 수신 오류: {str(e)}")
                break
    return pd.DataFrame()

def get_balance(currency):
    url = f"{SERVER_URL}/v1/accounts"
    try:
        rate_limiter.acquire()
        headers = {'Authorization': f'Bearer {jwt.encode({"access_key": ACCESS_KEY, "nonce": str(uuid.uuid4())}, SECRET_KEY, algorithm="HS256")}'}
        response = requests.get(url, headers=headers, timeout=5)
        if response.status_code == 200:
            data = response.json()
            for b in data:
                if b['currency'] == currency:
                    return float(b['balance'])
        return 0
    except Exception as e:
        logging.error(f"잔고 조회 오류: {str(e)}")
        slack_send(f"잔고 조회 오류: {str(e)}")
        return 0

def get_krw_balance():
    return get_balance('KRW')

def buy_market_order(market, amount):
    url = f"{SERVER_URL}/v1/orders"
    query = {
        'market': market,
        'side': 'bid',
        'price': str(amount),
        'ord_type': 'price'
    }
    try:
        rate_limiter.acquire()
        query_string = '&'.join([f"{k}={v}" for k, v in query.items()])
        query_hash = hashlib.sha512(query_string.encode()).hexdigest()
        payload = {
            'access_key': ACCESS_KEY,
            'nonce': str(uuid.uuid4()),
            'query_hash': query_hash,
            'query_hash_alg': 'SHA512',
        }
        jwt_token = jwt.encode(payload, SECRET_KEY, algorithm='HS256')
        headers = {'Authorization': f'Bearer {jwt_token}'}
        response = requests.post(url, data=query, headers=headers, timeout=5)
        if response.status_code == 201:
            msg = f"{market} 매수 성공: {response.json().get('uuid')}"
            logging.info(msg)
            slack_send(msg)
            return response.json()
        else:
            msg = f"{market} 매수 실패: {response.status_code}, {response.text}"
            logging.error(msg)
            slack_send(msg)
            return None
    except Exception as e:
        msg = f"{market} 매수 요청시 예외 발생: {str(e)}"
        logging.error(msg)
        slack_send(msg)
        return None

def sell_market_order(market):
    url = f"{SERVER_URL}/v1/orders"
    coin = market.split('-')[1]
    balance = get_balance(coin)
    if balance <= 0:
        msg = f"{coin} 잔고 없음"
        logging.warning(msg)
        slack_send(msg)
        return None
    query = {
        'market': market,
        'side': 'ask',
        'volume': str(balance),
        'ord_type': 'market'
    }
    try:
        rate_limiter.acquire()
        query_string = '&'.join([f"{k}={v}" for k, v in query.items()])
        query_hash = hashlib.sha512(query_string.encode()).hexdigest()
        payload = {
            'access_key': ACCESS_KEY,
            'nonce': str(uuid.uuid4()),
            'query_hash': query_hash,
            'query_hash_alg': 'SHA512',
        }
        jwt_token = jwt.encode(payload, SECRET_KEY, algorithm='HS256')
        headers = {'Authorization': f'Bearer {jwt_token}'}
        response = requests.post(url, data=query, headers=headers, timeout=5)
        if response.status_code == 201:
            msg = f"{market} 매도 성공: {response.json().get('uuid')}"
            logging.info(msg)
            slack_send(msg)
            return response.json()
        else:
            msg = f"{market} 매도 실패: {response.status_code}, {response.text}"
            logging.error(msg)
            slack_send(msg)
            return None
    except Exception as e:
        msg = f"{market} 매도 요청시 예외 발생: {str(e)}"
        logging.error(msg)
        slack_send(msg)
        return None

def has_coin(market):
    coin = market.split('-')[1]
    return get_balance(coin) > 0

# ----- 전략 함수 (시그널 정밀화, 멀티타임프레임) -----
def ma_signal(df, window=5):
    if df.empty or len(df) < window:
        return 0
    ma = df['close'].rolling(window=window).mean()
    if df['close'].iloc[-1] > ma.iloc[-1]:
        return 1
    elif df['close'].iloc[-1] < ma.iloc[-1]:
        return -1
    return 0

def rsi_signal(df, period=14):
    if df.empty or len(df) < period + 1:
        return 0
    delta = df['close'].diff()
    gain = (delta.where(delta > 0, 0)).rolling(window=period).mean()
    loss = (-delta.where(delta < 0, 0)).rolling(window=period).mean()
    rs = gain / loss
    rsi = 100 - (100 / (1 + rs))
    if pd.isna(rsi.iloc[-1]):
        return 0
    if rsi.iloc[-1] < 30:
        return 1
    elif rsi.iloc[-1] > 70:
        return -1
    return 0

def macd_signal(df, fast=12, slow=26, signal=9):
    if df.empty or len(df) < slow + signal:
        return 0
    ema_fast = df['close'].ewm(span=fast, adjust=False).mean()
    ema_slow = df['close'].ewm(span=slow, adjust=False).mean()
    macd = ema_fast - ema_slow
    macd_signal_line = macd.ewm(span=signal, adjust=False).mean()
    if macd.iloc[-2] < macd_signal_line.iloc[-2] and macd.iloc[-1] > macd_signal_line.iloc[-1]:
        return 1
    elif macd.iloc[-2] > macd_signal_line.iloc[-2] and macd.iloc[-1] < macd_signal_line.iloc[-1]:
        return -1
    return 0

def bb_signal(df, window=20, num_std=2):
    if df.empty or len(df) < window:
        return 0
    ma = df['close'].rolling(window=window).mean()
    std = df['close'].rolling(window=window).std()
    upper = ma + (num_std * std)
    lower = ma - (num_std * std)
    close = df['close'].iloc[-1]
    if close < lower.iloc[-1]:
        return 1
    elif close > upper.iloc[-1]:
        return -1
    return 0

# ----- 포지션 관리(손절/익절) -----
positions = {}  # market: {'entry': 매입가, 'amount': 수량}

def check_position(market, cur_price):
    pos = positions.get(market)
    if not pos:
        return None
    entry = pos['entry']
    change = (cur_price - entry) / entry
    if change >= 0.05:
        return "tp"
    elif change <= -0.02:
        return "sl"
    return None

def calc_real_profit(buy_price, sell_price):
    gross = (sell_price - buy_price) / buy_price
    net = gross - (FEE_RATE*2) - (gross * TAX_RATE if gross > 0 else 0)
    return net

# ----- 메인 트레이딩 루프 -----
def trade_job():
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
            sigs = [
                ma_signal(df_day),
                rsi_signal(df_day),
                macd_signal(df_day),
                bb_signal(df_day),
                ma_signal(df_hour),
                rsi_signal(df_hour),
                ma_signal(df_5m)
            ]
            buy_score = sigs.count(1)
            sell_score = sigs.count(-1)
            cur_price = df_day['close'].iloc[-1]
            # 익절/손절 자동 매도
            pos_check = check_position(market, cur_price)
            if pos_check in ["tp", "sl"]:
                resp = sell_market_order(market)
                if resp and market in positions:
                    entry = positions[market]['entry']
                    amount = positions[market]['amount']
                    profit = calc_real_profit(entry, cur_price)
                    log_trade(time.strftime("%Y-%m-%d %H:%M:%S"), market, "SELL-"+pos_check, cur_price, amount, profit)
                    slack_send(f"[{market}] {pos_check} 매도, 실질수익률 {profit*100:.2f}%")
                    positions.pop(market)
                continue
            # 매도 신호 완화: 2개 이상 -1 시그널
            if sell_score >= 2 and has_coin(market):
                resp = sell_market_order(market)
                logging.info(f"{market}: 시그널 합 {sell_score}로 매도 시도")
                slack_send(f"{market}: 시그널 합 {sell_score}로 매도 시도")
                if resp and market in positions:
                    entry = positions[market]['entry']
                    amount = positions[market]['amount']
                    profit = calc_real_profit(entry, cur_price)
                    log_trade(time.strftime("%Y-%m-%d %H:%M:%S"), market, "SELL", cur_price, amount, profit)
                    slack_send(f"[{market}] 다중시그널 매도, 실질수익률 {profit*100:.2f}%")
                    positions.pop(market)
                continue
            # 매수: 2개 이상 +1 시그널
            if buy_score >= 2 and not has_coin(market) and krw_balance >= TRADE_AMOUNT and TRADE_AMOUNT <= max_trade:
                resp = buy_market_order(market, TRADE_AMOUNT)
                if resp and 'price' in resp:
                    price = float(resp['price'])
                    positions[market] = {'entry': price, 'amount': TRADE_AMOUNT / price}
                    log_trade(time.strftime("%Y-%m-%d %H:%M:%S"), market, "BUY", price, positions[market]['amount'], 0)
                    slack_send(f"[{market}] 다중시그널 매수, 매입가 {price}")
                continue
            logging.info(f"{market}: 대기 (시그널합계: {buy_score}, {sell_score})")
        # 시장 급변동 감지 (각 코인 2개 캔들만 요청)
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

if __name__ == "__main__":
    while True:
        trade_job()
        time.sleep(60)
        