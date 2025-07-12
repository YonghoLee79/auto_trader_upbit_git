<<<<<<< HEAD
=======
import sys
import os
import time
import logging
from dotenv import load_dotenv
from utils.database import get_db_connection, create_trades_table
from trading.trader import trade_job

# 프로젝트 루트 디렉토리를 Python 경로에 추가
sys.path.append(os.path.join(os.path.dirname(__file__), 'auto_trader_upbit_git'))

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

if __name__ == "__main__":
    main()
>>>>>>> origin/main
