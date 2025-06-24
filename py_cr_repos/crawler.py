import requests
from bs4 import BeautifulSoup

# 크롤링할 URL 예시
url = 'https://example.com'

response = requests.get(url)
if response.status_code == 200:
    soup = BeautifulSoup(response.text, 'html.parser')
    if soup.title:
        print(soup.title.text)
    else:
        print('타이틀 태그가 없습니다.')
else:
    print(f'크롤링 실패: {response.status_code}') 