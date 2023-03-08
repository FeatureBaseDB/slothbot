import sys
import requests
from bs4 import BeautifulSoup

from lib.database import weaviate_schema, weaviate_update

# weavaite schema
schema = weaviate_schema("support")

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
	text = soup.find("div", {"id": "main-content"})

	splits = text.text.split(" ") # split on spaces

	fulltexts = []
	_fulltext = ""
	for split in splits:
		_fulltext = _fulltext + split + " "

		# if we have a long string and a stop character
		if len(_fulltext) > 108 and (split.endswith(".") or split.endswith('."') or split.endswith("?") or split.endswith("!")):
			fulltexts.append(_fulltext)
			_fulltext = ""
	
	fulltexts.append(_fulltext)
	
	for fulltext in fulltexts:
		document = {
			"url": url,
			"title": title,
			"sentence": fulltext.strip(" ")
		}
		weaviate_update(document, "Support")