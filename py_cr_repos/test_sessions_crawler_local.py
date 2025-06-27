import requests
from bs4 import BeautifulSoup
from datetime import datetime, timedelta
import json
import os
import time

# 패키지 정보
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

# Waves timetable (valid 기간별로 추가)
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
]

def get_valid_waves_mapping(target_date):
    """날짜에 따른 waves 매핑 반환"""
    for item in waves_timetable:
        from_dt = datetime.strptime(item["valid_from"], "%Y-%m-%d")
        to_dt = datetime.strptime(item["valid_to"], "%Y-%m-%d")
        if from_dt <= target_date <= to_dt:
            return item["mapping"]
    return {}

def get_session_info(pkg, pickdate):
    """1차 API 크롤링 - 세션 정보 가져오기"""
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
    print(f"[1차] {pickdate} {pkg['name']} 요청 중...")
    try:
        response = requests.post(url, data=data, headers=headers)
        print(f"[1차] {pickdate} {pkg['name']} 응답코드: {response.status_code}")
        session_list = []
        if response.status_code == 200:
            try:
                res_json = response.json()
                out_html = res_json.get('outHtml', '')
                soup = BeautifulSoup(out_html, 'html.parser')
                lis = soup.find_all('li', class_='reg_items')
                print(f"[1차] {pickdate} {pkg['name']} 파싱된 세션 개수: {len(lis)}")
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
                print(f"[1차] {pickdate} {pkg['name']} JSON/outHtml 파싱 오류: {e}")
                print(f"[1차] {pickdate} {pkg['name']} 응답 본문: {response.text[:500]}")
        else:
            print(f"[1차] {pickdate} {pkg['name']} API 응답코드 비정상: {response.status_code}")
        return session_list
    except Exception as e:
        print(f"[1차] {pickdate} {pkg['name']} 요청 예외: {e}")
        return []

def get_section_limitsqty(s, pannelCnt=1):
    """2차 API - 섹션별 잔여 수량 확인 (레슨 아닌 경우만)"""
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
    print(f"[2차] schidx={s['schidx']} 요청 중...")
    try:
        response = requests.post(url, data=data, headers=headers)
        print(f"[2차] schidx={s['schidx']} 응답코드: {response.status_code}")
        if response.status_code != 200:
            print(f"[2차] schidx={s['schidx']} 응답코드 비정상: {response.status_code}")
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
            print(f"[2차] schidx={s['schidx']} limitsqty: {result}")
            return result
        except Exception as e:
            print(f"[2차] schidx={s['schidx']} JSON/outHtml 파싱 오류: {e}")
            return {"left": None, "right": None}
    except Exception as e:
        print(f"[2차] schidx={s['schidx']} 요청 예외: {e}")
        return {"left": None, "right": None}

def process_sessions(raw_sessions, date_str):
    """세션 가공 및 waves 매핑"""
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

def save_to_json(sessions_by_date, filename="wavepark_sessions_local.json"):
    """결과를 JSON 파일로 저장"""
    try:
        with open(filename, 'w', encoding='utf-8') as f:
            json.dump(sessions_by_date, f, ensure_ascii=False, indent=2)
        print(f"결과가 {filename}에 저장되었습니다.")
    except Exception as e:
        print(f"파일 저장 중 오류 발생: {e}")

def print_summary(sessions_by_date):
    """크롤링 결과 요약 출력"""
    print(f"\n=== 웨이브파크 세션 크롤링 결과 ===")
    print(f"총 날짜 수: {len(sessions_by_date)}")
    
    total_sessions = 0
    for date_str, sessions in sessions_by_date.items():
        print(f"\n=== {date_str} ===")
        print(f"세션 수: {len(sessions)}")
        total_sessions += len(sessions)
        
        # 첫 3개 세션만 출력
        for i, session in enumerate(sessions[:3], 1):
            print(f"  {i}. {session['time']} - {session['name']}")
            print(f"     Left: {session['left']}, Right: {session['right']}")
            print(f"     Waves: {session['waves']}")
            print(f"     레슨: {'예' if session['islesson'] else '아니오'}")
        
        if len(sessions) > 3:
            print(f"  ... 외 {len(sessions) - 3}개 세션")
    
    print(f"\n총 세션 수: {total_sessions}")

def main():
    """로컬 테스트용 메인 함수"""
    print("웨이브파크 세션 크롤러 (로컬 테스트)를 시작합니다...")
    
    start_date = datetime.today()
    sessions_by_date = {}
    
    # 14일치 크롤링 (테스트용으로는 3일만)
    for day in range(0, 3):
        pickdate = (start_date + timedelta(days=day)).strftime('%Y-%m-%d')
        print(f"\n=== {pickdate} 전체 패키지 크롤링 시작 ===")
        
        raw_sessions = []
        for pkg in package_infos:
            print(f"[START] {pickdate} {pkg['name']} ({pkg['packagecode']}) 크롤링 시작")
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
            
            # 서버 부하 방지를 위한 딜레이
            time.sleep(1)
        
        processed_sessions = process_sessions(raw_sessions, pickdate)
        sessions_by_date[pickdate] = processed_sessions
        print(f"=== {pickdate} 전체 패키지 크롤링 및 저장 완료 ===")
    
    if sessions_by_date:
        # 결과 출력
        print_summary(sessions_by_date)
        
        # JSON 파일로 저장
        save_to_json(sessions_by_date)
        
        print("\n크롤링이 완료되었습니다!")
    else:
        print("크롤링된 세션이 없습니다.")

if __name__ == '__main__':
    main() 