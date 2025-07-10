"""
데이터베이스 관리 유틸리티
"""
import sqlite3
import pandas as pd
import logging
from config import DB_NAME

class DatabaseManager:
    def __init__(self):
        self.db_name = DB_NAME
        self.init_database()
    
    def init_database(self):
        """데이터베이스 초기화"""
        conn = sqlite3.connect(self.db_name, check_same_thread=False)
        c = conn.cursor()
        c.execute('''CREATE TABLE IF NOT EXISTS trades
                     (time TEXT, market TEXT, action TEXT, price REAL, amount REAL, pnl REAL)''')
        conn.commit()
        conn.close()
    
    def log_trade(self, time, market, action, price, amount, pnl):
        """거래 로그 저장"""
        try:
            conn = sqlite3.connect(self.db_name, check_same_thread=False)
            c = conn.cursor()
            c.execute("INSERT INTO trades VALUES (?, ?, ?, ?, ?, ?)", 
                     (time, market, action, price, amount, pnl))
            conn.commit()
            conn.close()
        except Exception as e:
            logging.error(f"거래 로그 저장 오류: {str(e)}")
    
    def get_trades(self, limit=50):
        """거래 내역 조회"""
        try:
            conn = sqlite3.connect(self.db_name)
            query = """
            SELECT time, market, action, price, amount, pnl 
            FROM trades 
            ORDER BY time DESC 
            LIMIT ?
            """
            df = pd.read_sql_query(query, conn, params=[limit])
            conn.close()
            return df.to_dict('records')
        except Exception as e:
            logging.error(f"거래 내역 조회 오류: {str(e)}")
            return []
    
    def get_performance_stats(self):
        """수익률 통계 조회"""
        try:
            conn = sqlite3.connect(self.db_name)
            
            # 마켓별 통계
            market_query = """
            SELECT market, SUM(pnl) as total_pnl, COUNT(*) as trade_count
            FROM trades 
            WHERE action LIKE 'SELL%'
            GROUP BY market
            """
            market_df = pd.read_sql_query(market_query, conn)
            
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
            
            return {
                'by_market': market_df.to_dict('records'),
                'total': total_df.to_dict('records')[0] if not total_df.empty else {}
            }
        except Exception as e:
            logging.error(f"수익률 통계 조회 오류: {str(e)}")
            return {'by_market': [], 'total': {}}

# 전역 데이터베이스 매니저 인스턴스
db_manager = DatabaseManager()
