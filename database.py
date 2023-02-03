import sys
import weaviate

import requests
from string import Template

import config


# featurebase tables
url = 'http://localhost:10101/sql'

def find_between(s, first, last):
    try:
        start = s.index( first ) + len( first )
        end = s.index( last, start )
        return s[start:end]
    except ValueError:
        return ""

def featurebase_tables(table_name=None):
	# get current tables
	if not table_name:
		index_url='http://localhost:10101/index'
	else:
		index_url='http://localhost:10101/index/%s' % table_name

	try:
		result = requests.get(index_url)

		if table_name:
			_result = [result.json()]
		else:
			_result = result.json().get("indexes")

		tables = []

		for table in _result:
			if table.get('name', 'fb_views') != "fb_views":
				query = "SHOW CREATE TABLE %s;" % table.get('name')
				result = requests.post(
					url,
					data=query.encode('utf-8'),
					headers={'Content-Type': 'text/plain'}
				).json()

				data = result.get('data')[0][0]
				schema = find_between(data, "(", ")")

				fields = []
				for field in schema.split(","):
					field = field.strip(" ")
					field_name = field.split(" ")[0]
					field_type = field.split(" ")[1]
					fields.append(
						{
							"name": field_name,
							"type": field_type
						}
					)

				entry = {
					"name": table.get('name'),
					"fields": fields,
					"create_table_sql": data
				}
				tables.append(entry)

	except Exception as ex:
		print(ex)

	return tables


def featurebase_query(document):
	# try to run the query
	try:
		query = document.get("sql")
		result = requests.post(
			url,
			data=query.encode('utf-8'),
			headers={'Content-Type': 'text/plain'}
		).json()
		print(result)
	except Exception as ex:
		# bad query?
		exc_type, exc_obj, exc_tb = sys.exc_info()
		print(exc_type, exc_obj, exc_tb)
		
		document['explain'] = "(╯°□°)╯︵ ┻━┻"
		document['error'] = "%s: %s" % (exc_tb.tb_lineno, ex)
		document.pop('template_file', None)
		document['is_sql'] = 'False'
		return document

	if result.get('error', ""):
		document['explain'] = "Error returned by FeatureBase: %s" % result.get('error')
		document['error'] = result.get('error')
		document['is_sql'] = 'False'
		document['template_file'] = "handle_error"
	elif result.get('data', []):
		document['data'] = result.get('data')
		if not result.get('data'):
			document['explain'] = "Whatever it is that I did, it's done."
		document['template_file'] = "process_response"
	else:
		print(result)
		document['error'] = "No useful information was returned."
		document['is_sql'] = 'False'
		document['explain'] = "(╯°□°)╯︵ ┻━┻"
		document.pop('template_file', None)
	
	return document


def weaviate_update(document):
	try:
		weaviate_client = weaviate.Client("http://localhost:8080")
		data = {
			"plain": document.content,
			"explain": document.get('answer'),
			"sql": document.get('sql'),
			"epoch": int(time.time()),
			"author": document.author
		}
		print(data)
		data_uuid = weaviate_client.data_object.create(data, "Slothbot")

	except Exception as ex:
		print(ex)
		data_uuid = False

	return data_uuid