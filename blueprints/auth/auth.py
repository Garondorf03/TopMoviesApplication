from flask import Blueprint, request, make_response, jsonify
import jwt
import datetime
import bcrypt
from decorators import jwt_required
import globals

authBP = Blueprint("authBP", __name__)

blacklist = globals.db.blacklist
users = globals.db.users
activity_logs = globals.db.activity_logs

@authBP.route("/home/register", methods=['POST'])
def register():
    if 'name' in request.form and 'username' in request.form and 'password' in request.form and 'email' in request.form:
        if not users.find_one({"username": request.form["username"]}):
            pw_bytes = bytes(request.form["password"], "UTF-8")
            hashed_pw = bcrypt.hashpw(pw_bytes, bcrypt.gensalt())
            new_user = {
                "name": request.form.get("name"),
                "username": request.form["username"],
                "password": hashed_pw,
                "email": request.form["email"],
                "admin": False
            }
            users.insert_one(new_user)
            activity_logs.insert_one({
                'user': request.form["username"],
                'action': "new user registered",
                'timestamp': datetime.datetime.utcnow()
            })
            return make_response(jsonify({"message": "User " + request.form["username"] + " registered successfully"}), 201)
        else:
            return make_response(jsonify({"error": "Username " + request.form["username"] + " already exists"}), 409)
    else:
        return make_response(jsonify({"error": "Missing Form Data"}), 400)

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
                activity_logs.insert_one({
                    'user': auth.username,
                    'action': "user login",
                    'timestamp': datetime.datetime.utcnow()
                })
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
    activity_logs.insert_one({
        'token': token,
        'action': "user logout",
        'timestamp': datetime.datetime.utcnow()
    })
    return make_response(jsonify({'message' : 'Logout successful'}), 200 )