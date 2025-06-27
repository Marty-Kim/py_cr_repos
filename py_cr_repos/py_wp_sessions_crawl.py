import requests
from bs4 import BeautifulSoup
import firebase_admin
from firebase_admin import firestore
from datetime import datetime, timedelta
import json
import os
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

package_infos = [
    {
        "name": "초급",
        "packagecode": "WI3015DB9887B2A7",
        "idx": 13,
        "cate1": "9",
        "cate2": "30",
        "cate3": "0",
        "sectype": "30",
        "price": "80000",
        "thumb": "",
        "subject": "리프자유서핑(초급)",
        "possaleid": "N492525291106G7S4546"
    },
    {
        "name": "중급",
        "packagecode": "WI3015DB98879C47",
        "idx": 14,
        "cate1": "9",
        "cate2": "30",
        "cate3": "0",
        "sectype": "30",
        "price": "80000",
        "thumb": "",
        "subject": "리프자유서핑(중급)",
        "possaleid": "N492525291106G7S4547"
    },
    {
        "name": "상급",
        "packagecode": "WI3015DB988796C8",
        "idx": 15,
        "cate1": "9",
        "cate2": "30",
        "cate3": "0",
        "sectype": "30",
        "price": "80000",
        "thumb": "",
        "subject": "리프자유서핑(상급)",
        "possaleid": "N492525291106G7S4548"
    },
    {
        "name": "Lv4 라인업 레슨",
        "packagecode": "WI7016C431CF3046",
        "idx": 16,
        "cate1": "9",
        "cate2": "30",
        "cate3": "0",
        "sectype": "30",
        "price": "90000",
        "thumb": "",
        "subject": "라인업 레슨 Lv4",
        "possaleid": "N492525291106G7S4549"
    },
    {
        "name": "Lv5 턴기초 레슨",
        "packagecode": "WI7016C431CEDEBD",
        "idx": 17,
        "cate1": "9",
        "cate2": "30",
        "cate3": "0",
        "sectype": "30",
        "price": "90000",
        "thumb": "",
        "subject": "턴기초 레슨 Lv5",
        "possaleid": "N492525291106G7S4550"
    }
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
    }
    # 이후 기간 timetable도 추가 가능
]

def get_valid_waves_mapping(target_date):
    for item in waves_timetable:
        from_dt = datetime.strptime(item["valid_from"], "%Y-%m-%d")
        to_dt = datetime.strptime(item["valid_to"], "%Y-%m-%d")
        if from_dt <= target_date <= to_dt:
            return item["mapping"]
    return {}

# 3. 1차 API 크롤링
def get_session_info(pkg, pickdate):
    url = "https://www.wavepark.co.kr/generalbooking/ajaxDateCheck"
    data = {
        "usercnt": 0,
        "pickdate": pickdate,
        "cate3": pkg["cate3"],
        "cate2": pkg["cate2"],
        "cate1": pkg["cate1"],
        "sectype": pkg["sectype"],
        "code": code,
        "price": pkg["price"],
        "thumb": pkg["thumb"],
        "subject": pkg["subject"],
        "packagecode": pkg["packagecode"],
        "possaleid": pkg["possaleid"],
        "idx": pkg["idx"],
        "dateActive": dateActive,
        "pannelCnt": 1
    }
    headers = {
        "User-Agent": "Mozilla/5.0",
        "Referer": "https://www.wavepark.co.kr/generalbooking/"
    }
    logger.info(f"[1차] {pickdate} {pkg['name']} 요청 payload: {json.dumps(data, ensure_ascii=False)}")
    try:
        response = requests.post(url, data=data, headers=headers)
        logger.info(f"[1차] {pickdate} {pkg['name']} 응답코드: {response.status_code}")
        session_list = []
        if response.status_code == 200:
            try:
                res_json = response.json()
                out_html = res_json.get('outHtml', '')
                soup = BeautifulSoup(out_html, 'html.parser')
                lis = soup.find_all('li', class_='reg_items')
                logger.info(f"[1차] {pickdate} {pkg['name']} 파싱된 세션 개수: {len(lis)}")
                for li in lis:
                    session = {
                        "itemidx": li.get('data-itemidx'),
                        "pickdatetime": li.get('data-pickdatetime'),
                        "picktime": li.get('data-picktime'),
                        "schidx": li.get('data-schidx'),
                        "limit_cnt": li.get('data-limit_cnt')
                    }
                    # 레슨은 remain만 파싱
                    if "레슨" in pkg["name"]:
                        remain_span = li.find('span', class_='remain')
                        if remain_span:
                            remain_text = remain_span.get_text(strip=True)
                            remain = remain_text.split('/')[0].strip()
                            session["remain"] = remain
                        else:
                            session["remain"] = None
                    session_list.append(session)
            except Exception as e:
                logger.error(f"[1차] {pickdate} {pkg['name']} JSON/outHtml 파싱 오류: {e}", exc_info=True)
                logger.error(f"[1차] {pickdate} {pkg['name']} 응답 본문: {response.text[:1000]}")
        else:
            logger.error(f"[1차] {pickdate} {pkg['name']} API 응답코드 비정상: {response.status_code}")
            logger.error(f"[1차] {pickdate} {pkg['name']} 응답 본문: {response.text[:500]}")
        return session_list
    except Exception as e:
        logger.error(f"[1차] {pickdate} {pkg['name']} 요청 예외: {e}", exc_info=True)
        return []

# 4. 2차 API (레슨 아닌 경우만)
def get_section_limitsqty(s, pannelCnt=1):
    url = "https://www.wavepark.co.kr/generalbooking/ajaxSectionCheck"
    data = {
        "limit_cnt": s["limit_cnt"],
        "schidx": s["schidx"],
        "picktime": s["picktime"],
        "pickdatetime": s["pickdatetime"],
        "itemidx": s["itemidx"],
        "pannelCnt": pannelCnt
    }
    headers = {
        "User-Agent": "Mozilla/5.0",
        "Referer": "https://www.wavepark.co.kr/generalbooking/"
    }
    logger.info(f"[2차] schidx={s['schidx']} 요청 payload: {json.dumps(data, ensure_ascii=False)}")
    try:
        response = requests.post(url, data=data, headers=headers)
        logger.info(f"[2차] schidx={s['schidx']} 응답코드: {response.status_code}")
        if response.status_code != 200:
            logger.warning(f"[2차] schidx={s['schidx']} 응답코드 비정상: {response.status_code}")
            logger.warning(f"[2차] schidx={s['schidx']} 응답 본문: {response.text[:500]}")
            return {"left": None, "right": None}
        try:
            res_json = response.json()
            out_html = res_json.get('outHtml', '')
            soup = BeautifulSoup(out_html, 'html.parser')
            left_input = soup.find('input', {'id': 'area101'})
            right_input = soup.find('input', {'id': 'area201'})
            result = {
                "left": left_input.get('data-limitsqty') if left_input else None,
                "right": right_input.get('data-limitsqty') if right_input else None
            }
            logger.info(f"[2차] schidx={s['schidx']} limitsqty: {result}")
            return result
        except Exception as e:
            logger.error(f"[2차] schidx={s['schidx']} JSON/outHtml 파싱 오류: {e}", exc_info=True)
            logger.error(f"[2차] schidx={s['schidx']} 응답 본문: {response.text[:500]}")
            return {"left": None, "right": None}
    except Exception as e:
        logger.error(f"[2차] schidx={s['schidx']} 요청 예외: {e}", exc_info=True)
        return {"left": None, "right": None}

# 5. 세션 가공 및 waves 매핑
def process_sessions(raw_sessions, date_str):
    target_date = datetime.strptime(date_str, "%Y-%m-%d")
    waves_map = get_valid_waves_mapping(target_date)
    sessions = []
    for s in raw_sessions:
        name = s["name"]
        # Lv4/Lv5 레슨 시간 고정
        if "Lv4" in name:
            time = "11:00:00"
            islesson = True
        elif "Lv5" in name:
            time = "13:00:00"
            islesson = True
        else:
            time = s.get("picktime")
            islesson = False
        # waves 자동 적용 (time만)
        waves = ""
        if time in waves_map:
            waves = waves_map[time]
        session_obj = {
            "time": time,
            "name": name,
            "left": s.get("left"),
            "right": s.get("right"),
            "isfunding": s.get("isfunding", False),
            "islesson": islesson,
            "waves": waves
        }
        sessions.append(session_obj)
    # 시간 오름차순 정렬
    sessions.sort(key=lambda x: x["time"])
    return sessions

# 6. Firestore 병합 저장 (지난 세션/None 세션 제외)
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
        if key in session_map:
            session_map[key]['left'] = ns.get('left')
            session_map[key]['right'] = ns.get('right')
            session_map[key]['name'] = ns.get('name')
            session_map[key]['waves'] = ns.get('waves')
            session_map[key]['isfunding'] = ns.get('isfunding')
        else:
            session_map[key] = ns

    merged_sessions = sorted(
        session_map.values(),
        key=lambda x: x['time']
    )
    doc_ref.set({'sessions': merged_sessions})
    logger.info(f"[저장] {date_str} 세션 {len(merged_sessions)}개(병합) 저장 완료")

# 7. 메인 루프
def main(request):
    if not firebase_admin._apps:
        firebase_admin.initialize_app(options={
            'projectId': os.environ.get('GOOGLE_CLOUD_PROJECT', 'wavepark-d71a3')
        })
    db = firestore.client()
    start_date = datetime.today()
    for day in range(0, 14):
        pickdate = (start_date + timedelta(days=day)).strftime('%Y-%m-%d')
        logger.info(f"=== {pickdate} 전체 패키지 크롤링 시작 ===")
        raw_sessions = []
        for pkg in package_infos:
            logger.info(f"[START] {pickdate} {pkg['name']} ({pkg['packagecode']}) 크롤링 시작")
            sessions = get_session_info(pkg, pickdate)
            for s in sessions:
                # 레슨: left만, 시간 고정
                if "레슨" in pkg["name"]:
                    s["name"] = pkg["name"]
                    s["left"] = int(s.get("remain") or 0)
                    s["right"] = None
                else:
                    limitsqty = get_section_limitsqty(s)
                    s["name"] = pkg["name"]
                    s["left"] = int(limitsqty.get("left") or 0)
                    s["right"] = int(limitsqty.get("right") or 0)
                raw_sessions.append({
                    "picktime": s.get("picktime"),  # 원본 picktime 유지
                    "name": s["name"],
                    "left": s.get("left"),
                    "right": s.get("right"),
                    "isfunding": False,  # 추후 확장
                    "islesson": "레슨" in pkg["name"],
                    "waves": ""         # process_sessions에서 자동 매핑
                })
        processed_sessions = process_sessions(raw_sessions, pickdate)
        save_to_firestore(db, pickdate, processed_sessions)
        logger.info(f"=== {pickdate} 전체 패키지 크롤링 및 저장 완료 ===")
    logger.info("=== 전체 기간 크롤링 및 저장 완료 ===")
    return "OK"

if __name__ == '__main__':
    main(None)
