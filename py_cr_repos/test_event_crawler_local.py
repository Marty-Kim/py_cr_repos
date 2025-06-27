import requests
from bs4 import BeautifulSoup
import re
from datetime import datetime
import time
import json
import os

class WaveParkEventCrawlerLocal:
    def __init__(self):
        self.base_url = "https://www.wavepark.co.kr/board/event"
        self.headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
        }
        self.events = []
    
    def get_page_url(self, page):
        """페이지 URL 생성"""
        return f"{self.base_url}?scolumn=ext2&sorder=+DESC%2C+regdate+DESC&page={page}"
    
    def extract_image_url(self, img_style):
        """CSS background-image에서 이미지 URL 추출"""
        if img_style:
            match = re.search(r"url\('([^']+)'\)", img_style)
            if match:
                img_url = match.group(1)
                if img_url.startswith('/'):
                    return f"https://www.wavepark.co.kr{img_url}"
                return img_url
        return None
    
    def extract_d_day(self, d_day_text):
        """D-day 텍스트에서 숫자 추출"""
        if d_day_text:
            match = re.search(r'D-(\d+)', d_day_text)
            if match:
                return int(match.group(1))
        return None
    
    def parse_event_item(self, li_element):
        """개별 이벤트 항목 파싱"""
        try:
            # 링크 추출
            link_element = li_element.find('a')
            if not link_element:
                return None
            
            event_url = link_element.get('href')
            if event_url.startswith('/'):
                event_url = f"https://www.wavepark.co.kr{event_url}"
            
            # 이미지 추출
            img_div = li_element.find('div', class_='img')
            image_url = None
            if img_div:
                img_style = img_div.get('style', '')
                image_url = self.extract_image_url(img_style)
            
            # 제목 추출
            title_element = li_element.find('h2')
            if not title_element:
                return None
            
            # 제목에서 태그 제거하고 텍스트만 추출
            title_text = title_element.get_text(strip=True)
            
            # 이벤트 타입 추출 ([패키지], [이벤트] 등)
            event_type = ""
            type_span = title_element.find('span', class_=['pkg-c', 'event-c'])
            if type_span:
                event_type = type_span.get_text(strip=True)
                # 제목에서 이벤트 타입 제거
                title_text = title_text.replace(event_type, '').strip()
            
            # D-day 추출
            d_day_element = title_element.find('span', class_='d-day')
            d_day = None
            if d_day_element:
                d_day = self.extract_d_day(d_day_element.get_text(strip=True))
                # 제목에서 D-day 제거
                title_text = title_text.replace(d_day_element.get_text(strip=True), '').strip()
            
            # 날짜 추출
            date_element = li_element.find('p', class_='date')
            date_text = date_element.get_text(strip=True) if date_element else ""
            
            # 이벤트 ID 추출 (URL에서)
            event_id = None
            if event_url:
                match = re.search(r'/detail/(\d+)', event_url)
                if match:
                    event_id = match.group(1)
            
            return {
                'event_id': event_id,
                'title': title_text,
                'event_type': event_type,
                'date': date_text,
                'd_day': d_day,
                'image_url': image_url,
                'event_url': event_url,
                'crawled_at': datetime.now().isoformat()
            }
            
        except Exception as e:
            print(f"이벤트 파싱 중 오류 발생: {e}")
            return None
    
    def crawl_page(self, page):
        """특정 페이지 크롤링"""
        try:
            url = self.get_page_url(page)
            print(f"페이지 {page} 크롤링 중: {url}")
            
            response = requests.get(url, headers=self.headers)
            response.raise_for_status()
            
            soup = BeautifulSoup(response.content, 'html.parser')
            
            # 이벤트 목록 찾기
            event_list = soup.find('ul', class_='event-wrap')
            if not event_list:
                print(f"페이지 {page}에서 이벤트 목록을 찾을 수 없습니다.")
                return []
            
            page_events = []
            event_items = event_list.find_all('li')
            
            for item in event_items:
                event_data = self.parse_event_item(item)
                if event_data:
                    page_events.append(event_data)
            
            print(f"페이지 {page}에서 {len(page_events)}개의 이벤트를 찾았습니다.")
            return page_events
            
        except requests.RequestException as e:
            print(f"페이지 {page} 요청 중 오류 발생: {e}")
            return []
        except Exception as e:
            print(f"페이지 {page} 처리 중 오류 발생: {e}")
            return []
    
    def crawl_all_pages(self, max_pages=10):
        """모든 페이지 크롤링 (최대 10페이지)"""
        all_events = []
        
        for page in range(1, max_pages + 1):
            page_events = self.crawl_page(page)
            
            if not page_events:
                print(f"페이지 {page}에서 이벤트를 찾을 수 없습니다. 크롤링을 종료합니다.")
                break
            
            all_events.extend(page_events)
            
            # 서버 부하 방지를 위한 딜레이
            time.sleep(1)
        
        self.events = all_events
        return all_events
    
    def save_to_json(self, filename="wavepark_events_local.json"):
        """결과를 JSON 파일로 저장"""
        try:
            with open(filename, 'w', encoding='utf-8') as f:
                json.dump(self.events, f, ensure_ascii=False, indent=2)
            print(f"결과가 {filename}에 저장되었습니다.")
        except Exception as e:
            print(f"파일 저장 중 오류 발생: {e}")
    
    def print_summary(self):
        """크롤링 결과 요약 출력"""
        print(f"\n=== 웨이브파크 이벤트 크롤링 결과 ===")
        print(f"총 이벤트 수: {len(self.events)}")
        
        if self.events:
            print("\n=== 첫 5개 이벤트 미리보기 ===")
            for i, event in enumerate(self.events[:5], 1):
                print(f"\n{i}. {event['event_type']} {event['title']}")
                print(f"   날짜: {event['date']}")
                print(f"   D-day: {event['d_day']}")
                print(f"   이미지: {event['image_url']}")
                print(f"   링크: {event['event_url']}")
            
            # 이벤트 타입별 통계
            event_types = {}
            for event in self.events:
                event_type = event.get('event_type', '기타')
                event_types[event_type] = event_types.get(event_type, 0) + 1
            
            print(f"\n=== 이벤트 타입별 통계 ===")
            for event_type, count in event_types.items():
                print(f"  {event_type}: {count}개")

def main():
    """로컬 테스트용 메인 함수"""
    print("웨이브파크 이벤트 크롤러 (로컬 테스트)를 시작합니다...")
    
    # 크롤러 초기화 및 실행
    crawler = WaveParkEventCrawlerLocal()
    
    # 모든 페이지 크롤링
    events = crawler.crawl_all_pages(max_pages=10)
    
    if events:
        # 결과 출력
        crawler.print_summary()
        
        # JSON 파일로 저장
        crawler.save_to_json()
        
        print("\n크롤링이 완료되었습니다!")
    else:
        print("크롤링된 이벤트가 없습니다.")

if __name__ == "__main__":
    main() 