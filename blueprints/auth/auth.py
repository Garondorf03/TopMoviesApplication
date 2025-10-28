from flask import Blueprint, request, make_response, jsonify
import jwt
import datetime
import bcrypt
from decorators import jwt_required, admin_required
import globals

authBP = Blueprint("authBP", __name__)

blacklist = globals.db.blacklist
users = globals.db.users

@authBP.route("/home/login", methods=['GET'])
def login():
    auth = request.authorization
    if auth:
        user = users.find_one({'username' : auth.username})
        if user is not None:
            if bcrypt.checkpw(bytes(auth.password, 'UTF-8'), user['password']):
                token = jwt.encode({
                    'user' : auth.username,
                    'admin' : user['admin'],
                    'exp' : datetime.datetime.now(datetime.UTC) + datetime.timedelta(minutes = 30)
                }, globals.secretKey, algorithm='HS256')
                return make_response(jsonify({'token' : token}), 200)
            else:
                return make_response(jsonify({'message' : 'Incorrect password'}), 401)
        else:
            return make_response(jsonify({'message' : 'User not found'}), 401)
    return make_response(jsonify({'message' : 'Authentication required'}), 401)

@authBP.route("/home/logout", methods=['GET'])
@jwt_required
def logout():
    token = request.headers['x-access-token']
    blacklist.insert_one({"token":token})
    return make_response(jsonify({'message' : 'Logout successful'}), 200 )