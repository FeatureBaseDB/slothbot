import os
import json
import sys
import time
import random
import weaviate

from database import featurebase_tables, featurebase_query
from database import weaviate_update

# fb_tables = featurebase_tables()
fb_tables = featurebase_tables("planets")
tables = []
print("%s tables availabe via FeatureBase." % len(fb_tables))

for table in fb_tables:
	print(table)


# connect to weaviate and ensure schema exists
try:
	weaviate_client = weaviate.Client("http://localhost:8080")

	# reset weaviate
	# weaviate_client.schema.delete_all()

	# make schema if not avaialble
	if not weaviate_client.schema.contains():
		dir_path = os.path.dirname(os.path.realpath(__file__))
		schema_file = os.path.join(dir_path, "weaviate_schema.json")
		weaviate_client.schema.create(schema_file)
	
	print("Connected to Weaviate instance.")

except Exception as ex:
	# show vector database connection error
	print("Can't connect to a Weaviate instance.")
	print(ex)

documents = [
{"table": "planets", "plain": "select from planets", "explain": "Running SELECT * FROM planets;", "sql": "SELECT * FROM planets"},
{"table": "users", "plain": "select name, age from users", "explain": "Running SELECT name, age FROM users;", "sql": "SELECT name, age FROM users"},
{"table": "orders", "plain": "select sum(price) from orders", "explain": "Running SELECT SUM(price) FROM orders;", "sql": "SELECT SUM(price) FROM orders"},
{"table": "categories", "plain": "select id, name from categories order by name", "explain": "Running SELECT id, name FROM categories ORDER BY name;", "sql": "SELECT id, name FROM categories ORDER BY name"},
{"table": "customers", "plain": "select count(*) from customers where city = 'New York'", "explain": "Running SELECT COUNT(*) FROM customers WHERE city = 'New York';", "sql": "SELECT COUNT(*) FROM customers WHERE city = 'New York'"},
{"table": "contacts", "plain": "select max(phone) from contacts", "explain": "Running SELECT MAX(phone) FROM contacts;", "sql": "SELECT MAX(phone) FROM contacts"},
{"table": "planets", "plain": "insert into planets", "explain": "Running INSERT INTO planets;", "sql": "INSERT INTO planets"},
{"table": "users", "plain": "insert into users (name, age) values ('John', 25)", "explain": "Running INSERT INTO users (name, age) VALUES ('John', 25);", "sql": "INSERT INTO users (name, age) VALUES ('John', 25)"},
{"table": "orders", "plain": "insert into orders (customer_id, product, price) values (1, 'laptop', 1000)", "explain": "Running INSERT INTO orders (customer_id, product, price) VALUES (1, 'laptop', 1000);", "sql": "INSERT INTO orders (customer_id, product, price) VALUES (1, 'laptop', 1000)"},
{"table": "categories", "plain": "insert into categories (name, description) values ('electronics', 'electronics products')", "explain": "Running INSERT INTO categories (name, description) VALUES ('electronics', 'electronics products');", "sql": "INSERT INTO categories (name, description) VALUES ('electronics', 'electronics products')"},
{"table": "customers", "plain": "insert into customers (name, city) values ('John Doe', 'New York')", "explain": "Running INSERT INTO customers (name, city) VALUES ('John Doe', 'New York');", "sql": "INSERT INTO customers (name, city) VALUES ('John Doe', 'New York')"},
{"table": "contacts", "plain": "insert into contacts (name, phone) values ('Jane Doe', '+1 212-555-1234')", "explain": "Running INSERT INTO contacts (name, phone) VALUES ('Jane Doe', '+1 212-555-1234');", "sql": "INSERT INTO contacts (name, phone) VALUES ('Jane Doe', '+1 212-555-1234')"}
]


from random_word import RandomWords
r = RandomWords()

weaviate_client = weaviate.Client("http://localhost:8080")
for doc in documents:

	data_uuid = weaviate_client.data_object.create(
	  doc, 
	  "Slothbot",
	)