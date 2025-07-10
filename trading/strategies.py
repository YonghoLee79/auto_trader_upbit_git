"""
거래 전략 함수들
"""
import pandas as pd
import numpy as np

def ma_signal(df, window=5):
    """이동평균 시그널"""
    if df.empty or len(df) < window:
        return 0
    ma = df['close'].rolling(window=window).mean()
    if df['close'].iloc[-1] > ma.iloc[-1]:
        return 1
    elif df['close'].iloc[-1] < ma.iloc[-1]:
        return -1
    return 0

def rsi_signal(df, period=14):
    """RSI 시그널"""
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
    """MACD 시그널"""
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
    """볼린저 밴드 시그널"""
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

def get_combined_signals(df_day, df_hour, df_5m):
    """다중 시그널 조합"""
    signals = [
        ma_signal(df_day),
        rsi_signal(df_day),
        macd_signal(df_day),
        bb_signal(df_day),
        ma_signal(df_hour),
        rsi_signal(df_hour),
        ma_signal(df_5m)
    ]
    
    buy_score = signals.count(1)
    sell_score = signals.count(-1)
    
    return buy_score, sell_score
