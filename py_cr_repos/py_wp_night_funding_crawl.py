import requests
from bs4 import BeautifulSoup
import firebase_admin
from firebase_admin import firestore
from datetime import datetime, timedelta
import json
import os
import logging
import copy

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

MAX_SESSION_DATE_COUNT = 21

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

    
    # 25 / 7  중순 ~ 25 / 8월 말
    {
        "idx": 28856,
        "isFunding": False,
        "available_date": [
            "2025-07-13", "2025-08-03",
            "2025-08-17"
        ],
        "session_name": "나이트 초급 2시간",
        "minimum_funding_rate": 0,
        "maximun_count": 60
    },
    {
        "idx": 28855,
        "isFunding": False,
        "available_date": [
            "2025-07-12", "2025-07-27",
            "2025-08-02", "2025-08-09", "2025-08-15", "2025-08-16"
        ],
        "session_name": "나이트 중급 2시간",
        "minimum_funding_rate": 0,
        "maximun_count": 60
    },
    {
        "idx": 28854,
        "isFunding": False,
        "available_date": [
            "2025-07-26"
        ],
        "session_name": "나이트 상급 2시간",
        "minimum_funding_rate": 0,
        "maximun_count": 60
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

code = "241511957"
dateActive = "1"

# 2. Waves timetable (valid 기간별로 추가)
waves_timetable = [
    {
        "valid_from": "2025-06-01",
        "valid_to": "2025-07-04",
        "mapping": {
            "10:00:00": "M4 , T1",
            "11:00:00": "M1(E) , M2(E)",
            "12:00:00": "M3 , M4",
            "13:00:00": "M1 , M2",
            "14:00:00": "M4",
            "15:00:00": "M2 , M3",
            "16:00:00": "T1 , T2",
            "17:00:00": "M2 , M3 , M4"
        }
    },
    {
        "valid_from": "2025-07-05",
        "valid_to": "2025-07-25",
        "mapping": {
            "09:00:00": "M4,M4(L)",
            "10:00:00": "T1,T2",
            "11:00:00": "M1(easy),M2(easy)",
            "12:00:00": "M4",
            "13:00:00": "M1,M2",
            "14:00:00": "M2,M3,M4",
            "15:00:00": "M1,M2,M3",
            "16:00:00": "M3,M4",
            "17:00:00": "M2,M3",
            "18:00:00": "M4,T1",
            "19:00:00": "T1,T2"
        }
    },
    {
        "valid_from": "2025-07-26",
        "valid_to": "2025-08-17",
        "mapping": {
             "09:00:00": "M4,M4(L)",
            "10:00:00": "T1,T2",
            "11:00:00": "M1(easy),M2(easy)",
            "12:00:00": "M4",
            "13:00:00": "M1,M2",
            "14:00:00": "M2,M3,M4",
            "15:00:00": "M1,M2,M3(easy)",
            "16:00:00": "M3,M4",
            "17:00:00": "M2,M3",
            "18:00:00": "M4,T1",
            "19:00:00": "T1,T2"
        }
    },
    {
        "valid_from": "2025-08-18",
        "valid_to": "2025-08-30",
        "mapping": {
            "09:00:00": "M4(L)",
            "10:00:00": "M4,T1",
            "11:00:00": "M1(easy),M2(easy)",
            "12:00:00": "M3,M4",
            "13:00:00": "M1,M2",
            "14:00:00": "M2,M3,M4",
            "15:00:00": "M1,M2,M3",
            "16:00:00": "M4",
            "17:00:00": "M2,M3",
            "18:00:00": "M4,T1",
            "19:00:00": "M2,M3,M4"
        }
    },
    
    
    # 이후 기간 timetable도 추가 가능
]

def get_valid_waves_mapping(target_date):
    for item in waves_timetable:
        from_dt = datetime.strptime(item["valid_from"], "%Y-%m-%d")
        to_dt = datetime.strptime(item["valid_to"], "%Y-%m-%d")
        if from_dt <= target_date <= to_dt:
            return item["mapping"]
    return {}

# 나이트 펀딩 세션 크롤링 함수
def get_night_funding_sessions(night_pkg, pickdate):
    """나이트 펀딩 세션 정보 가져오기"""
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
        return night_sessions
    except Exception as e:
        logger.error(f"[나이트] {pickdate} {night_pkg['session_name']} 요청 예외: {e}", exc_info=True)
        return []

# 세션 가공 및 waves 매핑
def process_sessions(raw_sessions, date_str):
    target_date = datetime.strptime(date_str, "%Y-%m-%d")
    waves_map = get_valid_waves_mapping(target_date)
    
    processed_sessions = []
    for s in raw_sessions:
        time = s.get("time")
        
        if time is None:
            logger.warning(f"[필터] time이 None인 세션 제외: {s}")
            continue

        if time in waves_map:
            s['waves'] = waves_map[time]
        
        processed_sessions.append(s)

    processed_sessions.sort(key=lambda x: x["time"] if x["time"] is not None else "99:99:99")
    return processed_sessions

# Firestore 병합 저장 (지난 세션/None 세션 제외)
def save_to_firestore(db, date_str, new_sessions):
    doc_ref = db.collection('daily_sessions').document(date_str)
    doc = doc_ref.get()
    if doc.exists:
        existing_sessions = doc.to_dict().get('sessions', [])
    else:
        existing_sessions = []
    session_map = {(s['time'], s['name']): s for s in existing_sessions if s.get('time') is not None}

    now = datetime.now()
    target_date = datetime.strptime(date_str, "%Y-%m-%d")

    for ns in new_sessions:
        ns_time = ns.get('time')
        # 1. time이 None이면 제외
        if ns_time is None:
            logger.info(f"[필터] time이 None인 세션 제외: {ns}")
            continue
        # 2. 이미 지난 시간 세션 제외
        session_dt = datetime.strptime(f"{date_str} {ns_time}", "%Y-%m-%d %H:%M:%S")
        if session_dt < now:
            logger.info(f"[필터] 이미 지난 시간 세션 제외: {ns}")
            continue

        key = (ns['time'], ns['name'])
        session_map[key] = ns

    merged_sessions = sorted(
        session_map.values(),
        key=lambda x: x['time']
    )
    doc_ref.set({'sessions': merged_sessions})
    logger.info(f"[저장] {date_str} 세션 {len(merged_sessions)}개(병합) 저장 완료")

# 펀딩 세션 별도 저장
def save_funding_sessions_to_firestore(db, date_str, new_sessions):
    """펀딩 세션만 'funding_sessions' 컬렉션에 저장"""
    funding_sessions_to_save = [s for s in new_sessions if s.get('isfunding')]
    
    if not funding_sessions_to_save:
        logger.info(f"[펀딩 저장] {date_str} 에 저장할 펀딩 세션이 없습니다.")
        return

    doc_ref = db.collection('funding_sessions').document(date_str)
    doc = doc_ref.get()
    if doc.exists:
        existing_sessions = doc.to_dict().get('sessions', [])
    else:
        existing_sessions = []
    
    session_map = {(s['time'], s['name']): s for s in existing_sessions if s.get('time') is not None}

    now = datetime.now()

    for ns in funding_sessions_to_save:
        ns_time = ns.get('time')
        if ns_time is None:
            logger.info(f"[펀딩 필터] time이 None인 펀딩 세션 제외: {ns}")
            continue
            
        session_dt = datetime.strptime(f"{date_str} {ns_time}", "%Y-%m-%d %H:%M:%S")
        if session_dt < now:
            logger.info(f"[펀딩 필터] 이미 지난 시간 펀딩 세션 제외: {ns}")
            continue

        key = (ns['time'], ns['name'])
        session_map[key] = ns

    merged_sessions = sorted(
        session_map.values(),
        key=lambda x: x['time']
    )
    doc_ref.set({'sessions': merged_sessions})
    logger.info(f"[펀딩 저장] {date_str} 펀딩 세션 {len(merged_sessions)}개(병합) 저장 완료")


# 메인 루프
def main(request):
    if not firebase_admin._apps:
        firebase_admin.initialize_app(options={
            'projectId': os.environ.get('GOOGLE_CLOUD_PROJECT', 'wavepark-d71a3')
        })
    db = firestore.client()
    start_date = datetime.today()
    for day in range(0, MAX_SESSION_DATE_COUNT):
        pickdate = (start_date + timedelta(days=day)).strftime('%Y-%m-%d')
        logger.info(f"=== {pickdate} 나이트/펀딩 세션 크롤링 시작 ===")
        raw_sessions = []
        
        # 펀딩 비율 동적 설정
        date_obj = datetime.strptime(pickdate, "%Y-%m-%d")
        weekday = date_obj.weekday()
        min_rate = 40 if weekday >= 5 else 30 # 토,일 40%, 평일 30%
        
        # deepcopy를 사용하여 원본 BASE_NIGHT_PACKAGE_INFOS가 변경되지 않도록 함
        night_package_infos_today = copy.deepcopy(BASE_NIGHT_PACKAGE_INFOS)
        
        for pkg in night_package_infos_today:
            if pkg.get("isFunding"):
                pkg['minimum_funding_rate'] = min_rate

        for night_pkg in night_package_infos_today:
            if pickdate in night_pkg["available_date"]:
                logger.info(f"[START] {pickdate} {night_pkg['session_name']} 나이트 펀딩 크롤링 시작")
                night_sessions = get_night_funding_sessions(night_pkg, pickdate)
                raw_sessions.extend(night_sessions)
        
        if not raw_sessions:
            logger.info(f"=== {pickdate} 에 해당하는 나이트/펀딩 세션이 없습니다. ===")
            continue

        processed_sessions = process_sessions(raw_sessions, pickdate)
        save_to_firestore(db, pickdate, processed_sessions)
        save_funding_sessions_to_firestore(db, pickdate, processed_sessions)
        logger.info(f"=== {pickdate} 나이트/펀딩 세션 크롤링 및 저장 완료 ===")
    logger.info("=== 전체 기간 나이트/펀딩 크롤링 및 저장 완료 ===")
    return "OK"

if __name__ == '__main__':
    main(None)