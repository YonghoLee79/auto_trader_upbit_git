"""
업비트 API 연결 테스트 스크립트
"""
import sys
import os
sys.path.insert(0, os.getcwd())

from config import ACCESS_KEY, SECRET_KEY
from trading.upbit_api import get_krw_balance, get_balance
import requests

def test_api_connection():
    """API 연결 테스트"""
    print("=== 업비트 API 연결 테스트 ===")
    print(f"Access Key: {ACCESS_KEY[:10]}..." if ACCESS_KEY else "Access Key: 없음")
    print(f"Secret Key: {SECRET_KEY[:10]}..." if SECRET_KEY else "Secret Key: 없음")
    
    if not ACCESS_KEY or ACCESS_KEY == "test_access_key" or ACCESS_KEY == "your_actual_access_key_here":
        print("❌ 실제 업비트 API 키가 설정되지 않았습니다!")
        print("\n🔧 API 키 설정 방법:")
        print("1. 업비트(upbit.com) 로그인")
        print("2. 마이페이지 > Open API 관리")
        print("3. API 키 발급 (자산조회 권한 필요)")
        print("4. .env 파일에 키 입력")
        return False
    
    # 공개 API 테스트 (인증 불필요)
    try:
        response = requests.get("https://api.upbit.com/v1/market/all", timeout=5)
        if response.status_code == 200:
            print("✅ 공개 API 연결 성공")
        else:
            print(f"❌ 공개 API 연결 실패: {response.status_code}")
    except Exception as e:
        print(f"❌ 공개 API 연결 오류: {e}")
        return False
    
    # 잔고 조회 테스트 (인증 필요)
    print("\n=== 잔고 조회 테스트 ===")
    try:
        krw_balance = get_krw_balance()
        print(f"KRW 잔고: {krw_balance:,.0f} 원")
        
        # 다른 코인 잔고도 확인
        coins = ['BTC', 'ETH', 'DOGE', 'XRP', 'ADA']
        for coin in coins:
            balance = get_balance(coin)
            if balance > 0:
                print(f"  - {coin}: {balance:.8f}")
        
        if krw_balance > 0 or any(get_balance(coin) > 0 for coin in coins):
            print("✅ API 연결 및 잔고 조회 성공!")
            return True
        else:
            print("⚠️ API 연결은 되지만 모든 잔고가 0입니다.")
            return True
    except Exception as e:
        print(f"❌ 잔고 조회 실패: {str(e)}")
        return False

if __name__ == "__main__":
    test_api_connection()
