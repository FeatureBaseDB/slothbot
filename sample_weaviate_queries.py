import weaviate
import config

from database import weaviate_query

client = weaviate.Client(
    url="http://localhost:8080",
    additional_headers={
        "X-OpenAI-Api-Key": config.openai_token
    }
)


all_objects = client.data_object.get(class_name="History")
print(all_objects)


result = weaviate_query({"concepts": "select all from planets"}, "History", 0.3)
print(result)

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