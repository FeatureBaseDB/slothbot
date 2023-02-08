from database import weaviate_update

def loadMessages():
	with open("out.json") as outfile:
		for line in outfile:
			document = json.loads(line)
			data_uuid = weaviate_update(document, "BotDev")