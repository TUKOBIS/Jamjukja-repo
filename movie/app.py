from flask import Flask, render_template, redirect, url_for, request, send_file
from io import BytesIO
import pymysql
import pandas as pd
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import datetime as dt
import platform
import json

app = Flask(__name__)


# 시각화 한글 인코딩
if platform.system() == 'Windows':
    matplotlib.rc('font', family='Malgun Gothic')
elif platform.system() == 'Darwin': # Mac
    matplotlib.rc('font', family='AppleGothic')
else: # Linux
    matplotlib.rc('font', family='NanumGothic')

# 그래프에 마이너스 표시가 되도록 변경
plt.rcParams['axes.unicode_minus'] = False


@app.route('/')
def index():
    try:
        conn = pymysql.connect(user='root', passwd='1234', db='moviedb')
    except:
        return redirect(url_for('_except', err = 'DB 연결 실패'))
    else:
        try:
            movie = pd.read_sql("SELECT * FROM movie_tb ORDER BY sales DESC LIMIT 30", con=conn)
            movie = movie.to_dict('records')

            return render_template('index.html',
                movie = movie,
            )
        except Exception as e:
            return redirect(url_for('_except', err=e))
        finally:
            conn.close()


@app.route('/result', methods=['GET'])
def result():
    try:
        conn = pymysql.connect(user='root', passwd='1234', db='moviedb')
    except:
        return redirect(url_for('_except', err = 'DB 연결 실패'))
    else:
        try:
            # 검색한 영화의 정보
            title = request.args.get('title')
            movie = pd.read_sql("SELECT * FROM movie_tb WHERE title LIKE '%{}%'".format(title), con = conn)
            movie = movie.to_dict('records')[0]

            # 배우, 나라, 감독, 장르, 리뷰
            actor = pd.read_sql("SELECT a.actor FROM movie_actor_tb m JOIN actor_tb a on a.id=m.movie_id WHERE m.movie_id = {} LIMIT 1".format(movie.get('id')), con = conn)
            if len(actor) > 0:
                actor = actor.to_dict('records')[0]
            else:
                actor = {"actor":"알 수 없음"}
            country = pd.read_sql("SELECT c.country FROM movie_country_tb m JOIN country_tb c on c.id = m.movie_id WHERE movie_id = {} LIMIT 1".format(movie.get('id')), con = conn)
            if len(country) > 0:
                country = country.to_dict('records')[0]
            else:
                country = {"country":"알 수 없음"}
            director = pd.read_sql("SELECT d.director FROM movie_director_tb m JOIN director_tb d on d.id = m.movie_id WHERE movie_id = {} LIMIT 1".format(movie.get('id')), con = conn)
            if len(director) > 0:
                director = director.to_dict('records')[0]
            else:
                director = {"director":"알 수 없음"}
            genre = pd.read_sql("SELECT g.genre FROM movie_genre_tb m JOIN genre_tb g on g.id = m.movie_id WHERE movie_id = {} LIMIT 1".format(movie.get('id')), con = conn)
            if len(genre) > 0:
                genre = genre.to_dict('records')[0]
            else:
                genre = {"genre":"알 수 없음"}
            review = pd.read_sql("SELECT m.review FROM movie_review_tb m WHERE movie_id = {}".format(movie.get('id')), con = conn)

            return render_template('result.html',
                movie = movie,
                actor = actor,
                country = country,
                director = director,
                genre = genre,
                review = review,
            )
        except Exception as e:
            return redirect(url_for('_except', err = e))
        finally:
            conn.close()

@app.route('/except/')
def _except():
    err = request.args.get('err')
    return render_template('except.html', err = err)


# 코로나에 의한 영화 매출 동향
@app.route('/graph1/')
def graph1():
    try:
        conn = pymysql.connect(user='root', passwd='1234', db='moviedb')

        sql = """
        SELECT rel_date, sales
        FROM movie_tb
        """
        df = pd.read_sql(sql, con = conn)
        df['rel_date'] = pd.to_datetime(df['rel_date']).dt.year
        stats = df.groupby('rel_date').mean()

        # 시각화
        fig = plt.figure()
        ax = fig.add_subplot()
        ax.plot(stats.index, stats['sales'], label='평균 매출액 (단위: 100억)')
        ax.set_xticks(stats.index)
        ax.set_xlabel('연도',size = 12)
        ax.set_ylabel('평균 매출액',size = 12)
        ax.legend()
        img = BytesIO()
        plt.savefig(img, format='png')
        img.seek(0)

        return send_file(img, mimetype='image/png')
    except Exception as e:
        print('예외가 발생했습니다.', e)
    finally:
        conn.close()


@app.route('/stats1/')
def stats1():
    return render_template("stats1.html")


# 여름에 공포 영화 수요가 진짜 많은지
@app.route('/graph2/')
def graph2():
    try:
        conn = pymysql.connect(user='root', passwd='1234', db='moviedb')

        sql = """
        SELECT m.rel_date, m.audience
        FROM movie_tb m JOIN movie_genre_tb g
        ON m.id = g.movie_id
        WHERE g.genre_id IN (8,16)
        """
        df = pd.read_sql(sql, con = conn)
        df['rel_date'] = pd.to_datetime(df['rel_date']).dt.quarter
        stats = df.groupby('rel_date').mean()
        
        # 시각화
        fig = plt.figure()
        ax = fig.add_subplot()
        ax.plot(stats.index, stats['audience'], label='평균 관객수 (단위: 100만명)')
        ax.set_xticks(stats.index)
        ax.set_xticklabels(['겨울', '봄', '여름', '가을'])
        ax.set_ylabel('평균 관객수',size = 12)
        ax.legend()
        img = BytesIO()
        fig.savefig(img, format='png')
        img.seek(0)

        return send_file(img, mimetype='image/png')
    except Exception as e:
        print('예외가 발생했습니다.', e)
    finally:
        conn.close()

@app.route('/stats2/')
def stats2():
    return render_template("stats2.html")


# 평점과 매출액의 관계
@app.route('/graph3/')
def graph3():
    try:
        conn = pymysql.connect(user='root', passwd='1234', db='moviedb')

        sql = """
        SELECT grade, sales
        FROM movie_tb
        """
        df = pd.read_sql(sql, con = conn)
        df = df[~df['grade'].isna()]
        df['grade'] = ((df['grade']*100)//100).astype('int')

        # 3점 미만과 10점은 영화 빈도가 매우 낮아 평균 매출 값이 통계적으로 무의미하다고 판단이 되어 산정하지 않음
        df.groupby('grade', as_index=False).count()
        df = df[(df['grade'] >= 3) & (df['grade'] <= 9)]

        stats = df.groupby('grade').mean()

        # 시각화
        fig = plt.figure()
        ax = fig.add_subplot()
        ax.plot(stats.index, stats['sales'], label='평균 매출액 (단위: 100억)')
        ax.set_xticks(stats.index)
        ax.set_xlabel('평점',size = 12)
        ax.set_ylabel('평균 매출액',size = 12)
        ax.legend()
        img = BytesIO()
        fig.savefig(img, format='png')
        img.seek(0)

        return send_file(img, mimetype='image/png')
    except Exception as e:
        print('예외가 발생했습니다.', e)
    finally:
        conn.close()

@app.route('/stats3/')
def stats3():
    return render_template("stats3.html")


# 상영횟수와 매출액의 관계
@app.route('/graph4/')
def graph4():
    try:
        conn = pymysql.connect(user='root', passwd='1234', db='moviedb')

        sql = """
        SELECT play, sales
        FROM movie_tb
        """
        df = pd.read_sql(sql, con = conn)

        # 기초통계량 확인해서 범위 묶기
        df['play'].describe()
        df['play'] = (df['play']//5000)*5000

        # 빈도가 매우 낮아 평균 매출 값이 통계적으로 무의미하다고 판단이 되는 범위는 제거
        df.groupby('play', as_index=False).count()
        df = df[df['play'] < 50000]
        stats = df.groupby('play').mean()

        # 시각화
        fig = plt.figure()
        ax = fig.subplots()
        ax.plot(stats.index, stats['sales'], label = '평균 매출액 (단위: 100억)')
        ax.set_xlabel('상영 횟수', size = 12)
        ax.set_ylabel('평균 매출액', size = 12)
        # ax.axes.yaxis.set_visible(False)
        ax.legend()
        img4 = BytesIO()
        fig.savefig(img4, format='png', dpi=100)
        img4.seek(0)

        return send_file(img4, mimetype='image/png')
    except Exception as e:
        print('예외가 발생했습니다.', e)
    finally:
        conn.close()

@app.route('/stats4/')
def stats4():
    return render_template("stats4.html")


if __name__ == '__main__':
    app.run(port=5001, debug=True)
