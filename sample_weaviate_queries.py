import weaviate
import config
import pprint

from database import weaviate_query

client = weaviate.Client(
    url="http://localhost:8080",
    additional_headers={
        "X-OpenAI-Api-Key": config.openai_token
    }
)


# all_objects = client.data_object.get(class_name="Intent")
# print(all_objects)

for distance in range(0, 10):
	intents = weaviate_query({"concepts": "planets"}, "Intent", float(distance/10))

	if len(intents) > 3:
		break

pp = pprint.PrettyPrinter(indent=4)
pp.pprint(intents)

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
