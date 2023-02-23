# reference code

		# refactor
		# run until we get SQL, or an explaination/answer
		if document.get('is_sql', False) != False:
			document = featurebase_query(document)

			if document.get('data', []) != []:
				table_name = document.get('table')
				table = featurebase_tables(table_name)[0]

				_field_names = []
				for field in table.get('fields'):
					_field_names.append(field.get('name'))

				pretty_table = PrettyTable()
				pretty_table.field_names = _field_names

				for entry in document.get('data'):
					pretty_table.add_row(entry)

				table_string = "```\n%s\n```" % pretty_table
				await channel.send(document.get('explain'))
				await channel.send(document.get('sql'))
				await channel.send(table_string)

			else:
				await channel.send("It goes without saying, we have to be here.")
				await channel.send(document.get('explain'))


		# printing
		thetoken = config.print_token
		thebody = {
			"file_name": filename,
			"url": url
		}
		headers = {'Authorization': "Bearer %s" % thetoken}

		response = requests.get("https://api.printify.com/v1/catalog/blueprints/1151.json", headers=headers)
		# print(response.text)
		response = requests.get("https://api.printify.com/v1/shops.json", headers=headers)
		# print(response.text)

		response = requests.get("https://api.printify.com/v1/catalog/blueprints/1151/print_providers.json", data=json.dumps(thebody), headers=headers)

		response = requests.post("https://api.printify.com/v1/uploads/images.json", data=json.dumps(thebody), headers=headers)
		theid = json.loads(response.text).get('id')
		
		response = requests.get("https://api.printify.com/v1/catalog/blueprints/1151/print_providers/59/variants.json", data=json.dumps(thebody), headers=headers)
		

		thebody = {
			"title": "Product",
			"description": "Good product",
			"blueprint_id": 1151,
			"print_provider_id": 59,
			"variants": [
				{
					"id": 96176,
					"title": "11oz / Black",
					"options": {
						"size": "11oz",
						"color": "Black"
					},
					"placeholders": [
						{
							"position": "front",
							"height": 1211,
							"width": 2538
						}
					]
				}
			],
			"print_areas": [
				{
					"variant_ids": [96176],
					"placeholders": [
						{
							"position": "front",
							"images": [
								{
									"id": "%s" % theid,
									"x": 0.5, 
									"y": 0.5,
									"scale": 1,
									"angle": 0
								}
							]
						}
					]
				}
			]
		}

		response = requests.post("https://api.printify.com/v1/shops/7321641/products.json", data=json.dumps(thebody), headers=headers)
		

answer_dict = ai("sql", document)

document = {**document, **answer_dict}

# not working
data_uuid = weaviate_update(document)

# got a SQL query back
if document.get("is_sql", False) and document.get("is_sql").lower() == "true":
	try:
		query = document.get("sql")
		result = requests.post(url, data=query.encode('utf-8'), headers={'Content-Type': 'text/plain'}).json()
	except Exception as bullshit:
		# bad sql
		exc_type, exc_obj, exc_tb = sys.exc_info()
		await message.channel.send("(╯°□°)╯︵ ┻━┻")
		await message.channel.send("%s: %s" % (exc_tb.tb_lineno, bullshit))

	# got an answer from featurebase
	if result.get('error', ""):
		document.setdefault("error", result.get('error', ""))
		answer_dict = ai("sql_feedback", document)
		document = {**document, **answer_dict}

		try:
			query = document.get("sql")
			result = requests.post(url, data=query.encode('utf-8'), headers={'Content-Type': 'text/plain'}).json()
		except Exception as bullshit:
			# bad sql
			exc_type, exc_obj, exc_tb = sys.exc_info()
			await message.channel.send("(╯°□°)╯︵ ┻━┻")
			await message.channel.send("%s: %s" % (exc_tb.tb_lineno, bullshit))


	elif result.get('data', []):
		print(result.get('data'))
		answer_dict = ai("response", document)


		for bits in _result["data"]:
			try:
				# await message.channel.send(bits)
				pass
			except Exception as bullshit:
				exc_type, exc_obj, exc_tb = sys.exc_info()
				await message.channel.send("%s: %s" % (exc_tb.tb_lineno, bullshit))
		await message.channel.send(ai("response", document={"query": message.content,"result": _result['data'], "user": message.author.name, "sql": query}))

	else:
		await message.channel.send(result)
else:
	if document.get("explain") != "":
		await message.channel.send(document.get("explain"))

	else:
		answer = "Unfortunately, when I thought about this I have nothing to say."
		await message.channel.send(answer)

