"""
슬랙 알림 유틸리티
"""
import requests
import logging
from config import SLACK_WEBHOOK_URL

def slack_send(text):
    """슬랙으로 메시지 전송"""
    payload = {"text": text}
    try:
        requests.post(SLACK_WEBHOOK_URL, json=payload, timeout=5)
    except Exception as e:
        logging.error(f"슬랙 전송 오류: {str(e)}")
