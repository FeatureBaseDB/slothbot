# Slothbot: An Analytics Bot for Discord
Slothbot is an analytics bot written for Discord. It is written in Python and uses OpenAI, Weaviate and FeatureBase.

## Use
Slothbot can be used to discuss various analytical data sets, including scientific data and data related to machine learning applications. With it, you can ask questions of data like how many website visits your site got yesterday. 

It is capable of writing SQL, creating tables, querying tables, creating graphs, and answering questions about a given data set.

## How it Works
Slothbot uses the following software/libraries:

- GPT-3 via OpenAI calls
- FeatureBase
- Weaviate
- Discord
- Plotly
- PrettyTables

## Setup
You'll need some Python packages installed.

```pip3 install -r requirements.txt```

### FeatureBase

### Weaviate
To start Weaviate ensure you have Docker.

Change into the scripts directory:

```docker compose up```


### Discord

### AI Endpoint Handler