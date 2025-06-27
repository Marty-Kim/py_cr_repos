#!/bin/bash

# 웨이브파크 이벤트 크롤러 Cloud Run 배포 스크립트

# 환경 변수 설정 (실행 전 수정 필요)
PROJECT_ID="your-project-id"
REGION="asia-northeast3"
SERVICE_NAME="wavepark-event-crawler"
IMAGE_NAME="gcr.io/$PROJECT_ID/$SERVICE_NAME"

echo "=== 웨이브파크 이벤트 크롤러 배포 시작 ==="

# 1. 프로젝트 설정 확인
echo "프로젝트 ID: $PROJECT_ID"
gcloud config set project $PROJECT_ID

# 2. Docker 이미지 빌드
echo "Docker 이미지 빌드 중..."
docker build -t $IMAGE_NAME .

# 3. Google Container Registry에 푸시
echo "이미지를 Container Registry에 푸시 중..."
docker push $IMAGE_NAME

# 4. Cloud Run에 배포
echo "Cloud Run에 배포 중..."
gcloud run deploy $SERVICE_NAME \
  --image $IMAGE_NAME \
  --platform managed \
  --region $REGION \
  --allow-unauthenticated \
  --memory 512Mi \
  --timeout 300 \
  --max-instances 1

# 5. 배포 완료 확인
echo "배포 완료!"
echo "서비스 URL: $(gcloud run services describe $SERVICE_NAME --region=$REGION --format='value(status.url)')"

echo "=== 배포 완료 ===" 