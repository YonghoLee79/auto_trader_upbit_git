"""
포지션 관리 모듈
"""
from config import FEE_RATE, TAX_RATE

class PositionManager:
    def __init__(self):
        self.positions = {}  # market: {'entry': 매입가, 'amount': 수량}
    
    def add_position(self, market, entry_price, amount):
        """포지션 추가"""
        self.positions[market] = {
            'entry': entry_price,
            'amount': amount
        }
    
    def remove_position(self, market):
        """포지션 제거"""
        if market in self.positions:
            self.positions.pop(market)
    
    def get_position(self, market):
        """포지션 조회"""
        return self.positions.get(market)
    
    def check_position(self, market, current_price):
        """손절/익절 확인"""
        pos = self.positions.get(market)
        if not pos:
            return None
        
        entry = pos['entry']
        change = (current_price - entry) / entry
        
        if change >= 0.05:  # 5% 익절
            return "tp"
        elif change <= -0.02:  # 2% 손절
            return "sl"
        return None
    
    def calc_real_profit(self, buy_price, sell_price):
        """실질 수익률 계산 (수수료 및 세금 포함)"""
        gross = (sell_price - buy_price) / buy_price
        net = gross - (FEE_RATE * 2) - (gross * TAX_RATE if gross > 0 else 0)
        return net
    
    def get_all_positions(self):
        """모든 포지션 반환"""
        return self.positions

# 전역 포지션 매니저 인스턴스
position_manager = PositionManager()
