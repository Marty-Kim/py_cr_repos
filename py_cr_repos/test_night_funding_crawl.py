import requests
from bs4 import BeautifulSoup
from datetime import datetime
import json
import logging
import copy

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

BASE_NIGHT_PACKAGE_INFOS = [
    {
        "idx": 27926,
        "isFunding": True,
        "available_date": [
            "2025-07-03", "2025-07-06",
            "2025-07-09", "2025-07-12", "2025-07-22", "2025-07-24"
        ],
        "session_name": "펀딩 초급 2시간",
        "minimum_funding_rate": 40,
        "maximun_count": 60
    },
    {
        "idx": 27925,
        "isFunding": True,
        "available_date": [
            "2025-07-02", "2025-07-07",
            "2025-07-11", "2025-07-13", "2025-07-21", "2025-07-23"
        ],
        "session_name": "펀딩 중급 2시간",
        "minimum_funding_rate": 40,
        "maximun_count": 60
    },
    {
        "idx": 27924,
        "isFunding": True,
        "available_date": [
            "2025-07-05", "2025-07-08",
            "2025-07-10", "2025-07-25"
        ],
        "session_name": "펀딩 상급 2시간",
        "minimum_funding_rate": 40,
        "maximun_count": 40
    },
    # 25 / 7  중순 ~ 25 / 8월 말  Funding
    {
        "idx": 27926,
        "isFunding": True,
        "available_date": [
            "2025-07-26", "2025-07-29",
            "2025-07-31", "2025-08-02",
            "2025-08-06", "2025-08-08",
            "2025-08-11", "2025-08-14"
        ],
        "session_name": "펀딩 초급 2시간",
        "minimum_funding_rate": 0,
        "maximun_count": 60
    },
    {
        "idx": 27925,
        "isFunding": True,
        "available_date": [
            "2025-07-28", "2025-07-29",
            "2025-07-30", "2025-07-31",
            "2025-08-03", "2025-08-05",
            "2025-08-06", "2025-08-07",
            "2025-08-10", "2025-08-12",
            "2025-08-14", "2025-08-17"
        ],
        "session_name": "펀딩 중급 2시간",
        "minimum_funding_rate": 0,
        "maximun_count": 60
    },
    {   
        "idx": 27924,
        "isFunding": True,
        "available_date": [
            "2025-07-27", "2025-08-01",
            "2025-08-04", "2025-08-05",
            "2025-08-07", "2025-08-09",
            "2025-08-13", "2025-08-15",
            "2025-08-16"
        ],
        "session_name": "펀딩 상급 2시간",
        "minimum_funding_rate": 0,
        "maximun_count": 60
    },
]

def get_night_funding_sessions(night_pkg, pickdate):
    print(f"[DEBUG] get_night_funding_sessions 진입: {night_pkg['session_name']} {pickdate}")
    url = "https://www.wavepark.co.kr/packagebooking/reserv_pannel"
    data = {
        "idx": night_pkg["idx"],
        "pickdate": pickdate
    }
    headers = {
        "User-Agent": "Mozilla/5.0",
        "Referer": "https://www.wavepark.co.kr/packagebooking/"
    }
    logger.info(f"[나이트] {pickdate} {night_pkg['session_name']} 요청 payload: {json.dumps(data, ensure_ascii=False)}")
    try:
        response = requests.post(url, data=data, headers=headers)
        logger.info(f"[나이트] {pickdate} {night_pkg['session_name']} 응답코드: {response.status_code}")
        night_sessions = []
        if response.status_code == 200:
            try:
                res_json = response.json()
                out_html = res_json.get('outHtml', '')
                logger.info(f"[나이트] {pickdate} {night_pkg['session_name']} outHtml 길이: {len(out_html)}")
                
                soup = BeautifulSoup(out_html, 'html.parser')
                
                # 세션 시간 정보 찾기
                time_spans = soup.find_all('span', class_='time')
                remain_spans = soup.find_all('span', class_='remain')
                
                logger.info(f"[나이트] {pickdate} {night_pkg['session_name']} time_spans 개수: {len(time_spans)}")
                logger.info(f"[나이트] {pickdate} {night_pkg['session_name']} remain_spans 개수: {len(remain_spans)}")
                
                # HTML 내용 일부 로깅
                if len(out_html) > 0:
                    logger.info(f"[나이트] {pickdate} {night_pkg['session_name']} HTML 일부: {out_html[:500]}...")
                
                logger.info(f"[나이트] {pickdate} {night_pkg['session_name']} 파싱된 세션 개수: {len(time_spans)}")
                
                for i, time_span in enumerate(time_spans):
                    if i < len(remain_spans):
                        time_text = time_span.get_text(strip=True)
                        remain_text = remain_spans[i].get_text(strip=True)
                        
                        logger.info(f"[나이트] {pickdate} {night_pkg['session_name']} 세션 {i+1}: time='{time_text}', remain='{remain_text}'")
                        
                        # 시간 파싱 (예: "22:00 ~ 00:00" -> "22:00:00")
                        time_parts = time_text.split('~')[0].strip()
                        if len(time_parts) == 5:  # "22:00" 형식
                            session_time = time_parts + ":00"
                        else:
                            session_time = time_parts
                        
                        # 잔여 수량 파싱 (예: "21/40" -> 21)
                        remain_parts = remain_text.split('/')
                        if len(remain_parts) >= 1:
                            remain_count = remain_parts[0].strip()
                            try:
                                remain_count = int(remain_count)
                            except ValueError:
                                remain_count = 0
                        else:
                            remain_count = 0
                        
                        # left 값 계산 (minimum_funding_rate|maximun_count)
                        left_value = f"{night_pkg['minimum_funding_rate']}|{night_pkg['maximun_count']}"
                        
                        # 펀딩 성공률 계산
                        funding_rate_percent = 0
                        if night_pkg["maximun_count"] > 0:
                            funding_rate_percent = round((remain_count / night_pkg["maximun_count"]) * 100)

                        night_session = {
                            "time": session_time,
                            "name": night_pkg["session_name"],
                            "left": left_value,
                            "right": remain_count,
                            "isfunding": night_pkg["isFunding"],
                            "isNight": not night_pkg["isFunding"],
                            "islesson": False,
                            "waves": "",
                            "fundingRatePercent": funding_rate_percent
                        }
                        night_sessions.append(night_session)
                        logger.info(f"[나이트] {pickdate} {night_pkg['session_name']} 세션 {i+1} 생성: {night_session}")
                        
            except Exception as e:
                logger.error(f"[나이트] {pickdate} {night_pkg['session_name']} JSON/outHtml 파싱 오류: {e}", exc_info=True)
                logger.error(f"[나이트] {pickdate} {night_pkg['session_name']} 응답 본문: {response.text[:1000]}")
        else:
            logger.error(f"[나이트] {pickdate} {night_pkg['session_name']} API 응답코드 비정상: {response.status_code}")
            logger.error(f"[나이트] {pickdate} {night_pkg['session_name']} 응답 본문: {response.text[:500]}")
        
        logger.info(f"[나이트] {pickdate} {night_pkg['session_name']} 최종 세션 수: {len(night_sessions)}")
        print(f"[DEBUG] get_night_funding_sessions 반환: {night_sessions}")
        return night_sessions
    except Exception as e:
        logger.error(f"[나이트] {pickdate} {night_pkg['session_name']} 요청 예외: {e}", exc_info=True)
        print(f"[DEBUG] get_night_funding_sessions 예외: {e}")
        return []

def process_sessions(raw_sessions, date_str):
    print(f"[DEBUG] process_sessions 진입: {len(raw_sessions)}개")
    processed_sessions = []
    for s in raw_sessions:
        time = s.get("time")
        if time is None:
            logger.warning(f"[필터] time이 None인 세션 제외: {s}")
            continue
        processed_sessions.append(s)
    processed_sessions.sort(key=lambda x: x["time"] if x["time"] is not None else "99:99:99")
    print(f"[DEBUG] process_sessions 반환: {len(processed_sessions)}개")
    return processed_sessions

if __name__ == "__main__":
    print("[DEBUG] __main__ 진입")
    now = datetime.today()
    today_str = now.strftime('%Y-%m-%d')
    print(f"[DEBUG] 오늘 날짜: {today_str}")
    print(f"[DEBUG] BASE_NIGHT_PACKAGE_INFOS 전체: {len(BASE_NIGHT_PACKAGE_INFOS)}개")
    for pkg in BASE_NIGHT_PACKAGE_INFOS:
        print(f"[DEBUG] {pkg['session_name']} available_date: {pkg['available_date']}")
    # 오늘 날짜에 해당하는 펀딩 세션만 추출
    test_pkgs = [pkg for pkg in BASE_NIGHT_PACKAGE_INFOS if pkg["isFunding"] and today_str in pkg["available_date"]]
    print(f"[DEBUG] 오늘 펀딩 세션 패키지 수: {len(test_pkgs)}")
    all_sessions = []
    for pkg in test_pkgs:
        print(f"\n[크롤링 시작] {pkg['session_name']} ({pkg['idx']})")
        sessions = get_night_funding_sessions(pkg, today_str)
        print(f"크롤링 결과: {sessions}")
        all_sessions.extend(sessions)
    print("\n[가공 결과]")
    processed = process_sessions(all_sessions, today_str)
    for s in processed:
        print(s) 