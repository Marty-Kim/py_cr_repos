@echo off
echo ========================================
echo 웨이브파크 크롤러 로컬 테스트
echo ========================================

echo.
echo 1. 라이브러리 설치 중...
pip install -r requirements_local.txt

echo.
echo 2. 이벤트 크롤러 테스트 시작...
python test_event_crawler_local.py

echo.
echo 3. 세션 크롤러 테스트 시작...
python test_sessions_crawler_local.py

echo.
echo ========================================
echo 모든 테스트가 완료되었습니다!
echo ========================================
echo.
echo 생성된 파일:
echo - wavepark_events_local.json (이벤트 데이터)
echo - wavepark_sessions_local.json (세션 데이터)
echo.
pause 