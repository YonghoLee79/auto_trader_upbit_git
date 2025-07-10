"""
설정 관리 모듈
"""
import os
from dotenv import load_dotenv

# 환경변수 로드
load_dotenv()

# API 설정
ACCESS_KEY = os.getenv("UPBIT_ACCESS_KEY")
SECRET_KEY = os.getenv("UPBIT_SECRET_KEY")
SERVER_URL = "https://api.upbit.com"

# 슬랙 설정
SLACK_WEBHOOK_URL = os.getenv("SLACK_WEBHOOK_URL", "https://hooks.slack.com/services/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")

# 거래 설정
MARKETS = ["KRW-DOGE", "KRW-XRP", "KRW-ADA"]
TRADE_AMOUNT = 5000
FEE_RATE = 0.0005
TAX_RATE = 0.0022
MAX_RATIO = 0.2

# 데이터베이스 설정
DB_NAME = 'trade.db'

# 로그 설정
LOG_FILE = 'trade_log.txt'
LOG_FORMAT = '%(asctime)s | %(levelname)s | %(message)s'

# Flask 설정
FLASK_HOST = '0.0.0.0'
FLASK_PORT = int(os.environ.get('PORT', 9000))
FLASK_DEBUG = True
