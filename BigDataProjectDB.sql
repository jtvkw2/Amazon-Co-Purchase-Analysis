DROP TABLE product_reviews;
DROP TABLE review;
DROP TABLE product_categories;
DROP TABLE category;
DROP TABLE similar_products;
DROP TABLE product;

CREATE TABLE product(
	ID INT PRIMARY KEY,
	ASIN CHAR(10) not null UNIQUE,
	title VARCHAR(100),
	group_name VARCHAR(5) not null,
	salesrank INT,
	avg_review_rating INT
);

CREATE TABLE similar_products(
	product_id INT,
	similar_ASIN CHAR(10),
	CONSTRAINT pk_similar PRIMARY KEY (product_id, similar_ASIN),
	CONSTRAINT fk_similar_productid FOREIGN KEY (product_id) REFERENCES product(ID),
	CONSTRAINT fk_similar_productASIN FOREIGN KEY (similar_ASIN) REFERENCES product(ASIN)
);

CREATE TABLE category(
	category_id INT PRIMARY KEY,
	name VARCHAR(20),
	head_category_id INT
);

CREATE TABLE product_categories(
	product_id INT,
	category_id INT,
	CONSTRAINT pk_product_categories PRIMARY KEY (product_id, category_id),
	CONSTRAINT fk_category_productid FOREIGN KEY (product_id) REFERENCES product(ID),
	CONSTRAINT fk_category_categoryid FOREIGN KEY (category_id) REFERENCES category(category_id)
);

CREATE TABLE review(
	review_id SERIAL PRIMARY KEY,
	date DATE,
	customer_id VARCHAR(20),
	rating INT,
	votes INT,
	helpful INT
);

CREATE TABLE product_reviews(
	product_id INT,
	review_id INT,
	CONSTRAINT pk_product_reviews PRIMARY KEY (product_id, review_id),
	CONSTRAINT fk_review_productid FOREIGN KEY (product_id) REFERENCES product(ID),
	CONSTRAINT fk_review_reviewid FOREIGN KEY (review_id) REFERENCES review(review_id)
);
