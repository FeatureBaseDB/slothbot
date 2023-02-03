import os
import weaviate

client = weaviate.Client("http://localhost:8080")

# Empty the Weaviate
client.schema.delete_all()

if not client.schema.contains():
    print("Creating Schema")
    dir_path = os.path.dirname(os.path.realpath(__file__))
    schema_file = os.path.join(dir_path, "weaviate_schema.json")
    client.schema.create(schema_file)
    print("Creating Schema done")



"""
data_obj = {
    "query": "select top(10) * from allyourbase;",
    "explain": "show all the entries in allyourbase"
}

data_uuid = client.data_object.create(
  data_obj, 
  "slothbot",
)
"""