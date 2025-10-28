from pymongo import MongoClient

secretKey = 'zelda'

client = MongoClient("mongodb://127.0.0.1:27017")
db = client.movieApp