import weaviate
import config
import pprint

from database import weaviate_query

client = weaviate.Client(
    url=config.weaviate_url,
    additional_headers={
        "X-OpenAI-Api-Key": config.openai_token
    }
)
query = input("enter query: ")

#all_objects = client.data_object.get(class_name="FeatureBase")
#print(all_objects)
#import sys
#sys.exit()

schema = client.schema.get()
for classe in schema.get('classes'):
	print(classe.get('class'))

document = {"plain": query}
collection = "FeatureBase"
fields = ["author", "plain", "explain", "sql", "table"]
records = weaviate_query(document, collection, fields)

pp = pprint.PrettyPrinter(indent=2)
pp.pprint(records)

"""
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
	{"plain": "select from planets"}
]
for doc in documents:
	nearText = {
	  "concepts": [doc.get('plain')],
	  "distance": 0.2,
	}
	print("=========================================")
	print("========", doc.get('plain'))
	result = (
	  client.query
	  .get("Slothbot", ["plain"])
	  .with_additional(["certainty", "distance", "id"])
	  .with_near_text(nearText)
	  .do()
	)

	for record in result.get('data').get('Get').get('Slothbot'):
		print(record.get('_additional').get('certainty'), "|", record.get('_additional').get('distance'), "|", record.get('table'), "|", record.get('sql'))

"""
