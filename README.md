# 업비트 자동매매 웹 플랫폼

모바일 적응형 웹 기반 업비트 자동매매 플랫폼입니다.

## 주요 기능

### 🌐 웹 인터페이스
- **모바일 적응형 디자인**: 스마트폰, 태블릿, PC 모든 기기에서 최적화된 UI
- **실시간 대시보드**: 잔고, 포지션, 수익률을 실시간으로 모니터링
- **인터랙티브 차트**: Chart.js를 활용한 가격 차트 분석
- **원클릭 매매 제어**: 웹에서 자동매매 시작/중지 제어

### 📊 트레이딩 기능
- **다중 시그널 전략**: MA, RSI, MACD, 볼린저밴드 조합
- **멀티타임프레임 분석**: 일봉, 시간봉, 5분봉 종합 분석
- **자동 손절/익절**: 2% 손절, 5% 익절 자동 실행
- **포지션 관리**: 실시간 포지션 추적 및 관리

### 💰 리스크 관리
- **자금 관리**: 총 자산의 20% 이내 투자
- **Rate Limiting**: API 호출 제한 준수
- **실질 수익률 계산**: 수수료 및 세금 고려한 정확한 수익률

## 시작하기

### 로컬 실행

```bash
# 의존성 설치
pip install -r requirements.txt

# 환경변수 설정
cp .env.example .env
# .env 파일에 업비트 API 키 입력

# 실행
python main.py
```

웹 브라우저에서 `http://localhost:5000` 접속

### Railway 배포

1. **Railway 계정 생성 및 CLI 설치**
```bash
npm install -g @railway/cli
railway login
```

2. **프로젝트 초기화**
```bash
railway init
```

3. **환경변수 설정**
```bash
railway variables set UPBIT_ACCESS_KEY=your_actual_access_key
railway variables set UPBIT_SECRET_KEY=your_actual_secret_key
railway variables set SLACK_WEBHOOK_URL=your_slack_webhook_url
```

4. **배포**
```bash
railway up
```

## API 엔드포인트

### 상태 조회
- `GET /api/status` - 트레이딩 상태 및 잔고 정보
- `GET /api/trades` - 거래 내역 조회
- `GET /api/performance` - 수익률 통계
- `GET /api/charts/<market>` - 차트 데이터

### 트레이딩 제어
- `POST /api/trading/start` - 자동매매 시작
- `POST /api/trading/stop` - 자동매매 중지

## 모바일 최적화

- **반응형 그리드 레이아웃**: 화면 크기에 따른 자동 배치
- **터치 친화적 UI**: 모바일에서 쉬운 조작
- **최적화된 차트**: 모바일에서도 선명한 차트 표시
- **빠른 로딩**: 효율적인 데이터 로딩으로 빠른 반응속도

## 대상 코인

- DOGE (도지코인)
- XRP (리플)
- ADA (에이다)

## 주의사항

⚠️ **투자 위험 고지**
- 암호화폐 투자는 높은 위험을 수반합니다
- 투자 손실에 대한 책임은 투자자 본인에게 있습니다
- 충분한 테스트 후 소액으로 시작하세요

⚠️ **Railway 배포 시 고려사항**
- 무료 플랜은 매월 제한된 실행 시간이 있습니다
- SQLite 데이터베이스는 재시작 시 초기화될 수 있습니다
- 중요한 데이터는 외부 데이터베이스 사용을 권장합니다

## 기술 스택

- **Backend**: Python, Flask
- **Frontend**: HTML5, CSS3, JavaScript
- **Charts**: Chart.js
- **Database**: SQLite
- **Deployment**: Railway
- **APIs**: Upbit REST API, Slack Webhook

## 라이선스

이 프로젝트는 교육 목적으로 제작되었습니다.