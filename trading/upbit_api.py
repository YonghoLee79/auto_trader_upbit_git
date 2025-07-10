"""
업비트 API 관련 함수들
"""
import time
import requests
import pandas as pd
import jwt
import uuid
import hashlib
import logging
from config import ACCESS_KEY, SECRET_KEY, SERVER_URL
from utils.rate_limiter import rate_limiter
from utils.notifications import slack_send

def get_candles(market, unit='days', count=60, retry=3):
    """캔들 데이터 조회"""
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
    """잔고 조회"""
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
    """KRW 잔고 조회"""
    return get_balance('KRW')

def buy_market_order(market, amount):
    """시장가 매수 주문"""
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
    """시장가 매도 주문"""
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
    """코인 보유 여부 확인"""
    coin = market.split('-')[1]
    return get_balance(coin) > 0
