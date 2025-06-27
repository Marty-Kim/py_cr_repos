# 웨이브파크 크롤러 프로젝트

웨이브파크 공식 웹사이트에서 이벤트 정보와 세션 정보를 자동으로 수집하는 크롤러 프로젝트입니다.

## 📁 프로젝트 구조

```
py_cr_repos/
├── py_wp_event_crawler.py          # Cloud Run용 이벤트 크롤러
├── py_wp_sessions_crawl.py         # Cloud Run용 세션 크롤러
├── test_event_crawler_local.py     # 로컬 테스트용 이벤트 크롤러
├── test_sessions_crawler_local.py  # 로컬 테스트용 세션 크롤러
├── requirements.txt                # Cloud Run용 라이브러리
├── requirements_local.txt          # 로컬 테스트용 라이브러리
├── Dockerfile                      # Cloud Run 배포용
├── .dockerignore                   # Docker 빌드 제외 파일
├── deploy.sh                       # Cloud Run 배포 스크립트
├── README.md                       # 이 파일
└── crawler.py                      # 기존 크롤러 (참고용)
```

## 🚀 빠른 시작

### 로컬 테스트 (권장)

#### 1. 이벤트 크롤러 테스트
```bash
# 라이브러리 설치
pip install -r requirements_local.txt

# 이벤트 크롤러 실행
python test_event_crawler_local.py
```

#### 2. 세션 크롤러 테스트
```bash
# 세션 크롤러 실행
python test_sessions_crawler_local.py
```

### Cloud Run 배포

#### 1. 이벤트 크롤러 배포
```bash
# 라이브러리 설치
pip install -r requirements.txt

# 배포 스크립트 실행 (PROJECT_ID 수정 필요)
./deploy.sh
```

## 📊 크롤러별 상세 설명

### 1. 이벤트 크롤러 (Event Crawler)

웨이브파크 이벤트 페이지에서 이벤트 정보를 수집합니다.

#### 수집 정보
- 이벤트 ID
- 이벤트 제목
- 이벤트 타입 ([패키지], [이벤트] 등)
- 이벤트 기간
- D-day 정보
- 이벤트 이미지 URL
- 이벤트 상세 페이지 링크
- 크롤링 시간

#### 사용법

**로컬 테스트:**
```bash
python test_event_crawler_local.py
```

**Cloud Run 배포:**
```bash
# Docker 이미지 빌드 및 배포
docker build -t gcr.io/YOUR_PROJECT_ID/wavepark-event-crawler .
docker push gcr.io/YOUR_PROJECT_ID/wavepark-event-crawler
gcloud run deploy wavepark-event-crawler \
  --image gcr.io/YOUR_PROJECT_ID/wavepark-event-crawler \
  --platform managed \
  --region asia-northeast3 \
  --allow-unauthenticated
```

#### 출력 예시
```json
{
  "event_id": "184",
  "title": "보드보관함+공항 Pick-up 이용권 출시",
  "event_type": "[패키지]",
  "date": "25.06.16 ~ 25.07.18",
  "d_day": 23,
  "image_url": "https://www.wavepark.co.kr/Board/boardFile.php?mode=view&key=229488513",
  "event_url": "https://www.wavepark.co.kr/board/event?scolumn=ext2&sorder=+DESC%2C+regdate+DESC&page=1&act=view/detail/184",
  "crawled_at": "2024-01-15T10:30:00.000000"
}
```

### 2. 세션 크롤러 (Session Crawler)

웨이브파크 예약 시스템에서 세션 정보를 수집합니다.

#### 수집 정보
- 세션 시간
- 패키지명 (초급, 중급, 상급, Lv4 레슨, Lv5 레슨)
- Left/Right 섹션 잔여 수량
- Waves 정보
- 레슨 여부
- 펀딩 여부

#### 사용법

**로컬 테스트:**
```bash
python test_sessions_crawler_local.py
```

**Cloud Run 배포:**
```bash
# Docker 이미지 빌드 및 배포
docker build -t gcr.io/YOUR_PROJECT_ID/wavepark-sessions-crawler .
docker push gcr.io/YOUR_PROJECT_ID/wavepark-sessions-crawler
gcloud run deploy wavepark-sessions-crawler \
  --image gcr.io/YOUR_PROJECT_ID/wavepark-sessions-crawler \
  --platform managed \
  --region asia-northeast3 \
  --allow-unauthenticated
```

#### 출력 예시
```json
{
  "2024-01-15": [
    {
      "time": "10:00:00",
      "name": "초급",
      "left": 15,
      "right": 12,
      "isfunding": false,
      "islesson": false,
      "waves": "M4 , T1"
    },
    {
      "time": "11:00:00",
      "name": "Lv4 라인업 레슨",
      "left": 3,
      "right": null,
      "isfunding": false,
      "islesson": true,
      "waves": "M1(E) , M2(E)"
    }
  ]
}
```

## 🔧 설정 및 환경

### 로컬 개발 환경

#### 필요한 라이브러리
```bash
# 로컬 테스트용
pip install -r requirements_local.txt

# Cloud Run 배포용
pip install -r requirements.txt
```

#### 환경 변수 (로컬 테스트)
```bash
# Firebase 사용 시 (선택사항)
export GOOGLE_APPLICATION_CREDENTIALS="path/to/service-account-key.json"
export GOOGLE_CLOUD_PROJECT="your-project-id"
```

### Cloud Run 환경

#### 환경 변수
- `GOOGLE_CLOUD_PROJECT`: Google Cloud 프로젝트 ID

#### 리소스 설정
- 메모리: 512Mi
- 타임아웃: 300초
- 최대 인스턴스: 1

## 📅 정기 실행 설정

### Cloud Scheduler 설정

#### 이벤트 크롤러 (매일 오전 9시)
```bash
gcloud scheduler jobs create http wavepark-event-crawler-job \
  --schedule="0 9 * * *" \
  --uri="YOUR_EVENT_CRAWLER_URL" \
  --http-method=POST \
  --location=asia-northeast3
```

#### 세션 크롤러 (매시간)
```bash
gcloud scheduler jobs create http wavepark-sessions-crawler-job \
  --schedule="0 * * * *" \
  --uri="YOUR_SESSIONS_CRAWLER_URL" \
  --http-method=POST \
  --location=asia-northeast3
```

## 📊 데이터베이스 구조 (Firestore)

### events 컬렉션
```json
{
  "event_id": "184",
  "title": "보드보관함+공항 Pick-up 이용권 출시",
  "event_type": "[패키지]",
  "date": "25.06.16 ~ 25.07.18",
  "d_day": 23,
  "image_url": "https://www.wavepark.co.kr/Board/boardFile.php?mode=view&key=229488513",
  "event_url": "https://www.wavepark.co.kr/board/event?scolumn=ext2&sorder=+DESC%2C+regdate+DESC&page=1&act=view/detail/184",
  "crawled_at": "2024-01-15T10:30:00.000000"
}
```

### daily_sessions 컬렉션
```json
{
  "sessions": [
    {
      "time": "10:00:00",
      "name": "초급",
      "left": 15,
      "right": 12,
      "isfunding": false,
      "islesson": false,
      "waves": "M4 , T1"
    }
  ]
}
```

### crawling_meta 컬렉션
```json
{
  "last_crawled": "2024-01-15T10:30:00.000000",
  "total_events": 25,
  "status": "success"
}
```

## 🛠️ 개발 및 테스트

### 로컬 테스트 시나리오

1. **이벤트 크롤러 테스트**
   ```bash
   python test_event_crawler_local.py
   ```
   - 최대 10페이지까지 크롤링
   - JSON 파일로 결과 저장
   - 콘솔에 요약 정보 출력

2. **세션 크롤러 테스트**
   ```bash
   python test_sessions_crawler_local.py
   ```
   - 3일치 세션 정보 크롤링 (테스트용)
   - JSON 파일로 결과 저장
   - 콘솔에 요약 정보 출력

### 디버깅

#### 로그 확인
- 로컬: 콘솔 출력
- Cloud Run: Google Cloud Console > Cloud Run > 로그

#### 오류 처리
- 네트워크 오류: 자동 재시도 없음 (수동 재실행 필요)
- 파싱 오류: 개별 항목 스킵 후 계속 진행
- API 오류: 응답 코드 및 본문 로깅

## ⚠️ 주의사항

### 크롤링 정책
- 서버 부하 방지를 위해 페이지 간 1초 딜레이 적용
- 웹사이트 이용약관 준수
- 과도한 요청 방지

### 데이터 정확성
- 웹사이트 구조 변경 시 크롤러 수정 필요
- API 응답 형식 변경 시 파싱 로직 업데이트 필요
- 정기적인 데이터 검증 권장

### 리소스 관리
- Cloud Run 메모리 제한 고려
- 배치 처리로 효율적인 데이터 저장
- 불필요한 데이터 정리

## 📈 모니터링

### Cloud Run 모니터링
- 로그 확인: `gcloud logs tail --service=wavepark-event-crawler`
- 메트릭 확인: Google Cloud Console > Cloud Run > 메트릭

### Firestore 모니터링
- 데이터 확인: Google Cloud Console > Firestore
- 크롤링 메타데이터: `crawling_meta` 컬렉션

### Cloud Scheduler 모니터링
- 작업 상태: Google Cloud Console > Cloud Scheduler
- 실행 히스토리: 각 작업의 실행 로그

## 🔄 업데이트 및 유지보수

### 정기 업데이트
- 패키지 정보 업데이트 (세션 크롤러)
- Waves timetable 업데이트
- 새로운 이벤트 타입 추가

### 버전 관리
- 코드 변경 시 버전 태그 추가
- 배포 전 로컬 테스트 필수
- 롤백 계획 수립

## 📞 지원 및 문의

### 문제 해결
1. 로컬 테스트로 기본 기능 확인
2. Cloud Run 로그 확인
3. Firestore 데이터 검증
4. 네트워크 연결 상태 확인

### 개선 제안
- 새로운 크롤링 대상 추가
- 성능 최적화
- 모니터링 기능 강화

## 📄 라이선스

이 프로젝트는 교육 및 개인 사용 목적으로 제작되었습니다. 