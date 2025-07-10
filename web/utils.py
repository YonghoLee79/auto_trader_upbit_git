"""
웹 유틸리티 함수들
"""

# 전역 상태 변수들
trading_active = False
trading_thread = None

def set_trading_status(status):
    """트레이딩 상태 설정"""
    global trading_active
    trading_active = status

def get_trading_status():
    """트레이딩 상태 조회"""
    return trading_active

def set_trading_thread(thread):
    """트레이딩 스레드 설정"""
    global trading_thread
    trading_thread = thread

def get_trading_thread():
    """트레이딩 스레드 조회"""
    return trading_thread
