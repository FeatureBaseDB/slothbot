# reference code

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

