import sys
import time
import requests

from bs4 import BeautifulSoup
import nltk

from lib.database import weaviate_schema, weaviate_update
from lib.ai import ai

nltk.download('punkt')
tokenizer = nltk.data.load('tokenizers/punkt/english.pickle')

# weavaite schema
schema = weaviate_schema("docs")

# get the sitemap and load it
sitemap = "https://docs.featurebase.com/sitemap.xml"
result = requests.get(sitemap).text

# parse with BS
soup = BeautifulSoup(result, features="xml")
urls = soup.find_all("loc")

# build list of URLs
_urls = []
for url in urls:
	_urls.append(url.text)

# overwrite the list
urls = _urls

for url in urls:
	if "404" in url:
		continue

	res = requests.get(url)
	html_page = res.content
	soup = BeautifulSoup(html_page, 'html.parser')

	title = soup.find('title').text
	
	print("Indexing: %s" % title)

	text = soup.find("div", {"id": "main-content"})

	words = ""
	previous_words = ""
	for i, entry in enumerate(tokenizer.tokenize(text.text)):
		print(i)
		words = words + " " + entry.replace("\n", " ")

		if (i % 3) == 0:
			# ai_doc = ai("mirror", {"words": words})

			document = {
				"sentence": words,
				"url": url,
				"title": title
			}

			print("==================")
			print(document)

			for x in range(10):
				try:
					print(weaviate_update(document, "Docs"))
					break
				except Exception as ex:
					print("%s - sleeping 10 seconds for retry" % ex)
					time.sleep(10)
			print("==================")
			words = ""

	if words != "":
		# ai_doc = ai("mirror", {"words": words})

		document = {
			"sentence": words,
			"url": url,
			"title": title
		}

		print("==================")
		print(document)

		for x in range(10):
			try:
				print(weaviate_update(document, "Docs"))
				break
			except Exception as ex:
				print("%s - sleeping 10 seconds for retry" % ex)
				time.sleep(10)
		print("==================")

sys.exit()

"""

	splits = text.text.split(" ") # split on spaces

	fulltexts = []
	_fulltext = ""
	for split in splits:
		_fulltext = _fulltext + split + " "

		# if we have a long string and a stop character
		if len(_fulltext) > 208 and (split.endswith(".") or split.endswith('."') or split.endswith("?") or split.endswith("!")):
			fulltexts.append(_fulltext)
			_fulltext = ""
	
	fulltexts.append(_fulltext)
	
	for fulltext in fulltexts:
		document = {
			"url": url,
			"title": title,
			"sentence": fulltext.strip(" ")
		}
		weaviate_update(document, "Docs")
"""