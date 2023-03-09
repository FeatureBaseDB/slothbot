import os
import sys
import weaviate
import random
import string

import requests
from string import Template

import config

# parse helper
def find_between(s, first, last):
    try:
        start = s.index( first ) + len( first )
        end = s.index( last, start )
        return s[start:end]
    except ValueError:
        return ""

# random strings
def random_string(size=6, chars=string.ascii_letters + string.digits):
	return ''.join(random.choice(chars) for _ in range(size))

###############
# FeatureBase #
###############

def featurebase_tables_schema(table_name=None):
	# get current tables
	if not table_name:
		index_url = "%s/index" % config.featurebase_url
	else:
		index_url = "%s/index/%s" % (config.featurebase_url, table_name)

	try:
		# get the index information
		result = requests.get(index_url)

		# toggle on one or many
		if table_name:
			_result = [result.json()]
		else:
			_result = result.json().get("indexes")

		# table array
		tables = []

		# iterrate on results to build tables, schemas and create sequences
		for table in _result:
			if table.get('name', 'fb_views') != "fb_views":
				# sql endpoint
				query_url = "%s/sql" % config.featurebase_url

				# query to get create table statement
				query = "SHOW CREATE TABLE %s;" % table.get('name')
				
				# run a query
				result = requests.post(
					query_url,
					data=query.encode('utf-8'),
					headers={'Content-Type': 'text/plain'}
				).json()

				# grab the data from the response
				data = result.get('data')[0][0]
				schema = find_between(data, "(", ")")

				# build fields
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

				# prep entry to array
				entry = {
					"name": table.get('name'),
					"fields": fields,
					"create_table_sql": data
				}

				# append to table array
				tables.append(entry)

	except Exception as ex:
		# something went wrong, so return nothing
		tables = None
		print(ex)

	return tables

# build a list of the current tables in a string
def featurebase_tables_string(table_name=None):
	# get the full table list + schema
	tables = featurebase_tables_schema(table_name)
	
	# if there were no tables, or no connection, return
	if not tables:
		return None

	# build a string of the table names with commas
	_table_string = ""
	for table in tables:
		if table.get('name', 'fb_views') != "fb_views":
			_table_string = _table_string + " " + table.get('name') + ","
	
	return _table_string.strip(",").strip(" ")

def featurebase_table_id(document):
	table = document.get("table", None)

	try:
		query = "SELECT max()"
	except:
		pass
	return

# query featurebase by document
# "sql" key in document should have a valid query
def featurebase_query(document):
	# try to run the query
	try:
		query = document.get("sql")

		result = requests.post(
			config.featurebase_url+"/sql",
			data=query.encode('utf-8'),
			headers={'Content-Type': 'text/plain'}
		).json()
		print("=============")
		print(result)
		print("=============")
	except Exception as ex:
		# bad query?
		exc_type, exc_obj, exc_tb = sys.exc_info()
		print("=============")
		print(exc_type, exc_obj, exc_tb)
		print("=============")
		document['explain'] = "(╯°□°)╯︵ ┻━┻"
		document['error'] = "%s: %s" % (exc_tb.tb_lineno, ex)
		document.pop('template_file', None)

		return document

	if result.get('error', ""):
		# featurebase reports and error
		document['explain'] = "Error returned by FeatureBase: %s" % result.get('error')
		document['error'] = result.get('error')
		document['data'] = result.get('data')
		document['template_file'] = "handle_error"

	elif result.get('data', []):
		# got some data back from featurebase
		document['data'] = result.get('data')
		document['schema'] = result.get('schema')
		document['template_file'] = "process_response"
	
	else:
		document['explain'] = "Query was successful, but returned no data."
		document['template_file'] = "eject_document" # forces the document flow to stop
	
	return document

############
# Weaviate #
############

def weaviate_schema(schema="memories"):
	# connect to weaviate and ensure schema exists
	try:
		weaviate_client = weaviate.Client(config.weaviate_url)
		return weaviate_client.schema.get(schema)
	
	except Exception as ex:
		print(ex)
		try:
			# show vector database connection error
			dir_path = os.path.dirname(os.path.realpath(__file__))
			schema_file = os.path.join(dir_path, "schema/%s.json" % schema)
			weaviate_client.schema.create(schema_file)
			return weaviate_client.schema.get(schema)
		except Exception as ex:
			print(ex)
			return {"error": "no schema"}

def weaviate_delete_schema(collection):
	weaviate_client = weaviate.Client(config.weaviate_url)

	if collection == "force_all":
		weaviate_client.schema.delete_all()
	else:
		try:
			weaviate_client.schema.delete_class(collection)
		except Exception as ex:
			print(ex)

	return

# query weaviate for matches
def weaviate_query(concepts, collection, fields):
	# connect to weaviate
	weaviate_client = weaviate.Client(config.weaviate_url)

	nearText = {
	  "concepts": concepts,
	  "moveAwayFrom": {
	  	"concepts": "All rights reserved table of contents next steps copyright",
	  	"force": 2.0
	  }
	  #"distance": distance,
	}

	# fetch result and fields
	result = (
	  weaviate_client.query
	  .get(collection, fields)
	  .with_additional(["certainty", "distance", "id"])
	  .with_near_text(nearText)
	  .do()
	)

	_records = []

	try:
		results = result.get('data').get('Get').get(collection)
		for record in results:
			_records.append(record)

	except Exception as ex:
		print("likely no records for %s" % collection)
		print(ex)

	return _records

# send a document to a class/collection
def weaviate_update(document, collection):
	# connect to weaviate
	weaviate_client = weaviate.Client(config.weaviate_url)

	data_uuid = weaviate_client.data_object.create(document, collection)

	return data_uuid

# delete a document from weaviate
def weaviate_delete_document(uuid, collection):
	try:
		weaviate_client.data_object.delete(uuid, collection)
	except Exception as ex:
		print(ex)

	return

