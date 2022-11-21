USE moviedb;

CREATE TABLE movieinfo_tb(
	id INT AUTO_INCREMENT PRIMARY KEY,
	title VARCHAR(50) NOT NULL,
    production_year INT,
    rel_date DATE,
    countries VARCHAR(50),
    genres VARCHAR(50),
    directors VARCHAR(50),
    sales BIGINT,
    audience INT,
    play INT,
    poster VARCHAR(100),
    grade DECIMAL(4,2),
    actors VARCHAR(300),
    summary VARCHAR(2500),
    reviews VARCHAR(1000)
);
SELECT * FROM movieinfo_tb;
-- UPDATE movieinfo_tb SET directors = '김현호|윤창섭' WHERE id = 1239;

CREATE TABLE country_tb(
	id INT PRIMARY KEY,
    country VARCHAR(10) NOT NULL
);
SELECT * FROM country_tb;

CREATE TABLE genre_tb(
	id INT PRIMARY KEY,
    genre VARCHAR(10) NOT NULL
);
SELECT * FROM genre_tb;

CREATE TABLE director_tb(
	id INT PRIMARY KEY,
    director VARCHAR(30) NOT NULL
);
SELECT * FROM director_tb;

CREATE TABLE actor_tb(
	id INT PRIMARY KEY,
    actor VARCHAR(30) NOT NULL
);
SELECT * FROM actor_tb;


#---------------- 정규화 ----------------

CREATE TABLE movie_tb
AS
SELECT 
	id, 
	title, 
	production_year, 
	rel_date, 
	grade, 
	sales, 
	audience, 
	play, 
	summary, 
	poster
FROM movieinfo_tb;

ALTER TABLE movie_tb MODIFY id INT PRIMARY KEY;

SELECT * FROM movie_tb;

#-------------------

CREATE TABLE movie_country_tb(
	movie_id INT NOT NULL,
    country_id INT,
    CONSTRAINT id PRIMARY KEY(movie_id, country_id),
    FOREIGN KEY(movie_id) REFERENCES movie_tb(id),
    FOREIGN KEY(country_id) REFERENCES country_tb(id)
);

INSERT INTO movie_country_tb
SELECT m.id, c.id
FROM country_tb c, 
	(SELECT id, substring_index(substring_index(countries, ',', n.n), ',', -1) country
	FROM movieinfo_tb CROSS JOIN 
		(SELECT 1 n
			UNION ALL SELECT 2
			UNION ALL SELECT 3
			UNION ALL SELECT 4
			UNION ALL SELECT 5
			UNION ALL SELECT 6
		) n
	WHERE n.n <= 1 + (length(countries) - length(REPLACE(countries, ',', '')))
    ) m
WHERE c.country = m.country;

SELECT * FROM movie_country_tb;

#-------------------

CREATE TABLE movie_genre_tb(
    movie_id INT,
    genre_id INT,
    CONSTRAINT id PRIMARY KEY(movie_id, genre_id),
    FOREIGN KEY(movie_id) REFERENCES movie_tb(id),
    FOREIGN KEY(genre_id) REFERENCES genre_tb(id)
);

SELECT * FROM movie_genre_tb;

INSERT INTO movie_genre_tb
SELECT m.id, g.id
FROM genre_tb g,
	(SELECT id, substring_index(substring_index(genres, ',', n.n), ',', -1) genre
	FROM movieinfo_tb CROSS JOIN
		(SELECT 1 n
			UNION ALL SELECT 2
			UNION ALL SELECT 3
			UNION ALL SELECT 4
			UNION ALL SELECT 5
			UNION ALL SELECT 6
		) n
	WHERE n.n <= 1 + (length(genres) - length(REPLACE(genres, ',', '')))
    ) m
WHERE g.genre = m.genre;

#-------------------

CREATE TABLE movie_director_tb(
    movie_id INT,
    director_id INT,
    CONSTRAINT id PRIMARY KEY(movie_id, director_id),
    FOREIGN KEY(movie_id) REFERENCES movie_tb(id),
    FOREIGN KEY(director_id) REFERENCES director_tb(id)
);

INSERT INTO movie_director_tb
SELECT m.id, d.id
FROM director_tb d,
	(SELECT id, substring_index(substring_index(directors, '|', n.n), '|', -1) director
	FROM movieinfo_tb CROSS JOIN
		(SELECT 1 n
			UNION ALL SELECT 2
			UNION ALL SELECT 3
			UNION ALL SELECT 4
			UNION ALL SELECT 5
			UNION ALL SELECT 6
		) n
	WHERE n.n <= 1 + (length(directors) - length(REPLACE(directors, '|', '')))
    ) m
WHERE d.director = m.director;

SELECT * FROM movie_director_tb;

#-------------------

CREATE TABLE movie_actor_tb(
    movie_id INT,
    actor_id INT,
    CONSTRAINT id PRIMARY KEY(movie_id, actor_id),
    FOREIGN KEY(movie_id) REFERENCES movie_tb(id),
    FOREIGN KEY(actor_id) REFERENCES actor_tb(id)
);

INSERT INTO movie_actor_tb
SELECT m.id, a.id
FROM actor_tb a,
	(SELECT id, substring_index(substring_index(actors, ',', n.n), ',', -1) actor
	FROM movieinfo_tb CROSS JOIN
		(SELECT 1 n
			UNION ALL SELECT 2
			UNION ALL SELECT 3
			UNION ALL SELECT 4
			UNION ALL SELECT 5
			UNION ALL SELECT 6
		) n
	WHERE n.n <= 1 + (length(actors) - length(REPLACE(actors, ',', '')))
    ) m
WHERE a.actor = m.actor;

SELECT * FROM movie_actor_tb;

#-------------------

CREATE TABLE movie_review_tb(
	id INT AUTO_INCREMENT PRIMARY KEY,
    movie_id INT,
    review VARCHAR(300),
    FOREIGN KEY(movie_id) REFERENCES movie_tb(id)
);

INSERT INTO movie_review_tb(movie_id, review)
SELECT id, substring_index(substring_index(reviews, '|', n.n), '|', -1) review
FROM movieinfo_tb CROSS JOIN
	(SELECT 1 n
		UNION ALL SELECT 2
		UNION ALL SELECT 3
		UNION ALL SELECT 4
		UNION ALL SELECT 5
		UNION ALL SELECT 6
	) n
WHERE n.n <= 1 + (length(reviews) - length(REPLACE(reviews, '|', '')))
ORDER BY n.n;

SELECT * FROM movie_review_tb;
