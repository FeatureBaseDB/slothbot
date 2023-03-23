import time
import sys
import PyPDF2
from lib.ai import ai
from lib.database import weaviate_schema, weaviate_update

import nltk

nltk.download('punkt')
tokenizer = nltk.data.load('tokenizers/punkt/english.pickle')

# weavaite schema
schema = weaviate_schema("quantum")

# creating a pdf file object
pdfFileObj = open('quantum.pdf', 'rb')
    
# creating a pdf reader object 
pdfReader = PyPDF2.PdfReader(pdfFileObj)
    
# printing number of pages in pdf file 
num_pages = len(pdfReader.pages)

# creating a page object
for page in range(0,num_pages):
	pageObj = pdfReader.pages[page]

	words = ""
	for i, entry in enumerate(tokenizer.tokenize(pageObj.extract_text())):
		words = words + " " + entry.replace("\n", " ")
		if (i % 3) == 0:
			ai_doc = ai("chat_cleanup", {"words": words})
			time.sleep(2)
			document = {
				"filename": "quantum.pdf",
				"gpt_fragment": ai_doc.get('answer'),
				"fragment": ai_doc.get('words')
			}
			try:
				print(weaviate_update(document, "Quantum"))
			except:
				time.sleep(10)
			print("==================")
			print(document)
			words = ""

# closing the pdf file object 
pdfFileObj.close() 

"""
	for fulltext in fulltexts:

		weaviate_update(document, "Docs")
"""
