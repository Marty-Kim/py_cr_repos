# Python 3.9 이미지 사용
FROM python:3.9-slim

# 작업 디렉토리 설정
WORKDIR /app

# 필요한 시스템 패키지 설치
RUN apt-get update && apt-get install -y \
    gcc \
    && rm -rf /var/lib/apt/lists/*

# Python 의존성 파일 복사 및 설치
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# 애플리케이션 코드 복사
COPY py_wp_event_crawler.py .

# 포트 설정 (Cloud Run에서 자동으로 설정됨)
ENV PORT=8080

# 애플리케이션 실행
CMD ["python", "py_wp_event_crawler.py"] 