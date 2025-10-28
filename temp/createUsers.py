from pymongo import MongoClient
import bcrypt

client = MongoClient("mongodb://127.0.0.1:27017")
db = client.movieApp
users = db.users

user_list = [
    {
        "name" : "Mason Murphy",
        "username" : "mason03",
        "password" : b"mason_m",
        "email" : "mason@mancity.net",
        "admin" : True
    },
    {
        "name" : "Ami Morrow",
        "username" : "ami04",
        "password" : b"ami_m",
        "email" : "ami@makeup.net",
        "admin" : False
    },
    {
        "name" : "Harrison Gordon",
        "username" : "harrison03",
        "password" : b"harrison_g",
        "email" : "harrison@music.net",
        "admin" : False
    }
]

for new_user in user_list:
    new_user["password"] = bcrypt.hashpw(new_user["password"], bcrypt.gensalt())
    users.insert_one(new_user)