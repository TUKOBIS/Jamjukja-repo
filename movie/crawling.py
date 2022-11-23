from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.support.select import Select
import requests
from bs4 import BeautifulSoup
import pymysql
from datetime import datetime
import re
import os

# kobis 사이트에서 영화 정보(영화명, 제작국가, 개봉일, 장르, 포스터, 누적매출액, 누적관객수, 상영수) 크롤링
movieinfo = []
def kobis_crawling():
    browser = webdriver.Chrome('/Users/gosuke/Documents/GitHub/Jamjukja-repo/movie/chromedriver')
    browser.implicitly_wait(20)
    browser.get('https://www.kobis.or.kr/kobis/business/stat/boxs/findMonthlyBoxOfficeList.do')

    today = datetime.today()
    current_year = today.year
    last_month = today.month - 1

    # 현재년도부터 지난 10년 동안의 개봉 영화 수집
    for y in range(current_year, current_year+1): # current_year : 원래 current_year 뒤에 -10있었음 ㅅㄱ
        # 연도 입력
        Select(browser.find_element(By.ID, 'sSearchYearFrom')).select_by_value(str(y))
        Select(browser.find_element(By.ID, 'sSearchYearTo')).select_by_value(str(y))

        for m in range(1,13):
            print(y, '년 ', m, '월의 영화 크롤링은', sep='', end=' ')
            # 월 입력
            if m > 6:
                Select(browser.find_element(By.ID, 'sSearchMonthTo')).select_by_index(m-1)
                Select(browser.find_element(By.ID, 'sSearchMonthFrom')).select_by_index(m-1)
            else:
                Select(browser.find_element(By.ID, 'sSearchMonthFrom')).select_by_index(m-1)
                Select(browser.find_element(By.ID, 'sSearchMonthTo')).select_by_index(m-1)
            
            # 검색 버튼 클릭
            browser.find_element(By.CLASS_NAME, 'btn_blue').send_keys(Keys.ENTER)
            # 숨겨진 정보 나타내기 (영화 목록 더보기)
            browser.execute_script("document.querySelector('.rst_sch > div:nth-child(5)').style.display = 'block';")
            soup = BeautifulSoup(browser.page_source, 'html.parser')

            for idx, val in enumerate(soup.select('tbody > tr')):
                # 영화 수집 기준이 되는 관객수(해당 사이트의 영화 목록 정렬 기준)
                a = int(val.select_one('td:nth-child(7)').get_text(strip=True).replace(',', ''))
                # 관객수가 10000명 미만인 영화는 수집 X
                if a < 10000:
                    print(idx+1, '번째에서 관객수 ', a, '명으로 종료', sep='')
                    break

                # 영화명, 개봉일, 누적매출액, 누적관객수, 상영횟수 정보 수집
                title = val.select_one('td:nth-child(2)').get_text(strip=True)
                release_date = val.select_one('td:nth-child(3)').get_text(strip=True)
                # 개봉일 정보가 없는 영화는 수집하지 않기
                if release_date == '':
                    continue
                sales = int(val.select_one('td:nth-child(6)').get_text(strip=True).replace(',', ''))
                audience = int(val.select_one('td:nth-child(8)').get_text(strip=True).replace(',', ''))
                showing = int(val.select_one('td:nth-child(10)').get_text(strip=True).replace(',', ''))

                # 영화의 세부 정보가 있는 팝업 창 띄우기
                if idx+1 <= 10:
                    selector = 'div.rst_sch > div:nth-child(3) tbody tr:nth-child({}) a'.format(idx+1)
                else:
                    selector = 'div.rst_sch > div:nth-child(5) tbody tr:nth-child({}) a'.format(idx-9)
                browser.find_element(By.CSS_SELECTOR, selector).send_keys(Keys.ENTER)
                soup = BeautifulSoup(browser.page_source, 'html.parser')

                # 포스터, 장르, 제작국가 정보 수집
                poster = 'https://www.kobis.or.kr' + soup.select_one('div.ovf > a').get('href')
                info_list = soup.select_one('dl.ovf > dd:nth-of-type(4)').get_text().split('|')
                genre = ''.join(info_list[2].split())  # 공백, 탭, 줄바꿈 제거
                country = ''.join(info_list[-1].split())  # 공백, 탭, 줄바꿈 제거

                # 외부 사이트 크롤링때 영화 일치 여부 판단을 위한 제작년도와 감독 정보 수집
                if soup.select_one('dl.ovf > dt:nth-of-type(6)').get_text() == '제작연도':
                    production_year = int(soup.select_one('dl.ovf > dd:nth-of-type(6)').get_text(strip=True)[:4])
                else:
                    production_year = int(soup.select_one('dl.ovf > dd:nth-of-type(7)').get_text(strip=True)[:4])
                if soup.select_one('div.staffMore div:first-child dd') is not None:
                    director = soup.select_one('div.staffMore div:first-child dd').get_text()
                else:
                    director = ''

                browser.find_element(By.CSS_SELECTOR, 'a.close:nth-of-type(2)').send_keys(Keys.ENTER)
                
                movieinfo.append((title,production_year,release_date,country,genre,director,sales,audience,showing,poster))

            if y == current_year:
                if m == last_month:
                    break

    browser.close()
    os.system('say "완료"')
kobis_crawling()
len(movieinfo)
movieinfo[0]


# 정해놓은 영화 수집 기간(현재년도 기준 지난 10년) 외의 개봉작들 제거 
def delete_old_movie():
    today = datetime.today()
    current_year = today.year

    for i in movieinfo[:][:]:
        rel_year = int(i[2][:4])
        if rel_year < current_year-10:
            movieinfo.remove(i)
delete_old_movie()

# 확장판, 감독판 제거
def delete_movie_edition():
    for i in movieinfo[:][:]:
        title = i[0]
        if '확장판' in title or '감독판' in title:
            movieinfo.remove(i)
delete_movie_edition()

# 영화 중복 제거
def distinct_movie():
    movieinfo.sort(key = lambda x:x[0])

    i = 0
    while i < len(movieinfo)-1:
        # 영화명, 감독이 같으면 같은 영화로 간주 (영화 통계 수치들이 누적값이므로 첫번째 영화를 제거)
        if movieinfo[i][0] == movieinfo[i+1][0] and movieinfo[i][5] == movieinfo[i+1][5]:
            # 같은 영화인데 개봉일이 다르면 재개봉이라고 간주하고 두번째 영화를 제거
            if movieinfo[i][2] != movieinfo[i+1][2]:
                del movieinfo[i+1]
            else:
                del movieinfo[i]
            i = 0
        i += 1
distinct_movie()
len(movieinfo)


# 네이버에서 영화 정보(평점, 출연 배우, 줄거리, 리뷰) 크롤링
# movieinfo_copy = movieinfo[:]
# len(movieinfo_copy)
# movieinfo_copy[0]
def naver_movie_crawling():
    headers = {'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/107.0.0.0 Safari/537.36'}

    for i in range(len(movieinfo)):
        search = movieinfo[i][0]
        search = search.replace('%', '%25')
        search = search.replace('#', '%23')
        search = search.replace('&', '%26')
        search = re.sub('\(|\)|3D', '', search)

        production_year = movieinfo[i][1]
        director = movieinfo[i][5]
        
        try:
            url = 'https://movie.naver.com/movie/search/result.naver?section=movie&query=' + search
            resp = requests.get(url, headers = headers)
            resp.raise_for_status() # 요청/응답 코드가 200이 아니면 예외 발생
        
            # 영화 검색 결과 유무 판단
            if 'search_list_1' in resp.text:
                soup = BeautifulSoup(resp.text, 'html.parser')

                result = None
                # 영화 결과가 하나면 일치 여부 검증 할 필요 X
                if len(soup.select('ul.search_list_1 > li')) == 1:
                    result = soup.select_one('dl')
                else:
                    # 검색 결과가 두 페이지가 이상이면 영화 3페이지까지 읽기
                    search_list = soup.select('ul.search_list_1 > li')
                    if len(soup.select('div.pagenavigation td')) >= 2:
                        for j in range(2,4):
                            url = 'https://movie.naver.com/movie/search/result.naver?section=movie&query=' + search + '&page={}'.format(j)
                            resp = requests.get(url, headers = headers)
                            soup2 = BeautifulSoup(resp.text, 'html.parser')
                            search_list += soup2.select('ul.search_list_1 > li')

                    for j in search_list:
                        # 영화 일치 여부 판단 기준 (제작년도, 감독)
                        search_production_year = j.select('dd.etc')[0].get_text().split('|')[-1]
                        search_director = j.select('dd.etc')[1].get_text().split('|')[0]
                        
                        # 검색하고자 한 영화가 맞는지 판단
                        if search_production_year.isnumeric() and '감독' in search_director:
                            search_production_year = int(search_production_year)
                            search_director = search_director.replace('감독 : ', '')

                            # 기준 1) 제작년도 1년 차이까지는 kobis와 naver의 데이터 차이이므로 같은 영화로 간주
                            is_same_year = abs(production_year - search_production_year) <= 1

                            # 기준 2) 감독 정보가 없는 영화는 제작년도로만 판단
                            # 기준 3) 감독이 2명 이상일 경우, 한 명이라도 같으면 같은 영화로 간주
                            # 기준 4) 영어 이름의 표기 차이가 있을 수 있으므로 단어 일치 개수로 판단
                            if director != '':
                                # 네이버 결과 형식에 맞춰서 데이터 가공 (공백 제거는 정규식 에러 방지)
                                director = ''.join(re.findall('[ㄱ-힣|]', director))
                                is_same_director = any(len(re.findall('[{}+]'.format(d), search_director)) >= int(len(d)*0.7) for d in director.split('|'))
                            else:
                                is_same_director = True

                            # 제작년도는 같은데 감독이 다를 경우, 감독의 다른 이름도 찾아보기
                            if is_same_year and not is_same_director:
                                # 감독 정보 페이지
                                url = 'https://movie.naver.com' + j.select('dd.etc')[1].select_one('a:first-child').get('href')
                                resp = requests.get(url, headers = headers)
                                soup = BeautifulSoup(resp.text, 'html.parser')

                                if soup.find('img', alt='다른이름') is not None:
                                    search_director2 = soup.find('img', alt='다른이름').find_next('td').get_text(strip=True)
                                    is_same_director = any(len(re.findall('[{}+]'.format(d), search_director2)) >= int(len(d)*0.7) for d in director.split('|'))
                                        
                            # 제작년도와 감독이 같으면 같은 영화로 간주
                            if is_same_year and is_same_director:
                                result = j.select_one('dl')
                                break
                
                grade = None
                actor = ''
                summary = ''
                review = ''
                # 영화 결과가 올바른 경우에만 평점, 출연 배우, 줄거리, 리뷰 가져오기
                if result is None:
                    print(search, movieinfo[i][1:6], '영화 결과가 일치하지 않습니다.')
                else:
                    # 평점
                    if result.select_one('dd.point > em.num') is not None:
                        grade = float(result.select_one('dd.point > em.num').get_text())

                    # 출연 배우
                    if len(result.select('dd.etc')[1].get_text().split('|')) >= 2:
                        actor = result.select('dd.etc')[1].get_text().split('|')[1]
                        actor = actor.replace('출연 :', '').replace(', ', ',').strip()
                    else:
                        if '출연' in result.select('dd.etc')[1].get_text():
                            actor = result.select('dd.etc')[1].get_text()
                            actor = actor.replace('출연 :', '').replace(', ', ',').strip()

                    # 영화 상세 정보 페이지
                    url = 'https://movie.naver.com' + result.select_one('dt > a').get('href')
                    resp = requests.get(url, headers = headers)
                    soup = BeautifulSoup(resp.text, 'html.parser')

                    # 줄거리
                    if soup.select_one('div.story_area > p') is not None:
                        summary = soup.select_one('div.story_area > p').get_text(strip=True)

                    # 리뷰
                    if len(soup.select('div.score_reple')) > 0:
                        review = []
                        for j in soup.select('div.score_reple > p'):
                            review.append(j.get_text(strip=True))
                        review = '|'.join(review)

            else:
                print(search, movieinfo[i][1:6], '검색 결과가 없습니다.')

        finally:
            movieinfo[i] = movieinfo[i] + (grade, actor, summary, review)

    os.system('say "완료"')
naver_movie_crawling()
movieinfo[0]


# 인덱스 테이블을(나라, 장르, 감독, 배우)을 위한 배열 생성
countries = []
genres = []
directors = []
actors = []
def create_index_table():
    global countries, genres, directors, actors
    
    for i in movieinfo:
        country, genre, director = i[3:6]
        actor = i[11]
        
        countries += country.split(',')
        genres += genre.split(',')
        directors += director.split('|')
        actors += actor.split(',')
            
    countries = list(set(countries))
    genres = list(set(genres))
    directors = list(set(directors))
    actors = list(set(actors))
create_index_table()


# 크롤링으로 모은 데이터들 DB에 삽입
def sql_insert():
    print("checkcheckehcke")
    connect = pymysql.connect(user='root', passwd='Koh716sk*', db='moviedb')
    cursor = connect.cursor()

    query = "insert into movieinfo_tb(title, production_year, rel_date, countries, genres, directors, sales, audience, play, poster, grade, actors, summary, reviews) values (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)"
    cursor.executemany(query, movieinfo)

    cursor.executemany("insert into country_tb values (%s, %s)", [(i+1, c) for i, c in enumerate(countries)])
    cursor.executemany('insert into genre_tb values (%s, %s) ', [(i+1, g) for i, g in enumerate(genres)])
    cursor.executemany('insert into director_tb values (%s, %s) ', [(i, d) for i, d in enumerate(directors)])
    cursor.executemany('insert into actor_tb values (%s, %s)', [(i, a) for i, a in enumerate(actors)])

    connect.commit()
    connect.close()
sql_insert()

