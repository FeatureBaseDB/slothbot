import weaviate
import config

client = weaviate.Client(
    url="http://localhost:8080",
    additional_headers={
        "X-OpenAI-Api-Key": config.openai_token
    }
)


all_objects = client.data_object.get(class_name="Slothbot")
# print(all_objects)

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

for doc in documents:
	nearText = {
	  "concepts": [doc.get('plain')],
	  "distance": 0.7,
	}
	print("=========================================")
	print("========", doc.get('plain'))
	result = (
	  client.query
	  .get("Slothbot", ["table","plain","sql"])
	  .with_additional(["certainty", "distance"])
	  .with_near_text(nearText)
	  .do()
	)

	for record in result.get('data').get('Get').get('Slothbot'):
		print(record.get('_additional').get('certainty'), "|", record.get('_additional').get('distance'), "|", record.get('table'), "|", record.get('sql'))

documents = [
	{"plain": "what are the planets with the most orders for electronics?"}
]
for doc in documents:
	nearText = {
	  "concepts": [doc.get('plain')],
	  "distance": 0.7,
	  "moveAwayFrom": {
	    "concepts": ["ORDER BY"],
	    "force": 0.45
	  }
	}
	print("=========================================")
	print("========", doc.get('plain'))
	result = (
	  client.query
	  .get("Slothbot", ["table","plain","sql"])
	  .with_additional(["certainty", "distance"])
	  .with_near_text(nearText)
	  .do()
	)

	for record in result.get('data').get('Get').get('Slothbot'):
		print(record.get('_additional').get('certainty'), "|", record.get('_additional').get('distance'), "|", record.get('table'), "|", record.get('sql'))

