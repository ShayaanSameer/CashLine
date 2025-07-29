from pymongo.mongo_client import MongoClient
from pymongo.server_api import ServerApi

from mongodb_operations import mongoDBClient

client = mongoDBClient(uri)

try:
    collection = client.getCollectionEndpoint('users').find()

    print(list(collection))

    # # Query for a movie that has the title 'Back to the Future'
    # query = { "title": "Back to the Future" }
    # movie = movies.find_one(query)

    # print(movie)

except Exception as e:
    raise Exception("Unable to find the document due to the following error: ", e)

