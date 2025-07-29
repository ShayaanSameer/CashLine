from pymongo.mongo_client import MongoClient
from pymongo.server_api import ServerApi

class mongoDBClient:
    def __init__(self, uri):
        self.uri = uri
        self.client = MongoClient(self.uri, server_api=ServerApi('1'))

    def getCollectionEndpoint(self, name):
        return self.client.get_database("sample_mflix").get_collection(name)
    
    def __del__(self):
        self.client.close()