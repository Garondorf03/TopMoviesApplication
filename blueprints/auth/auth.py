from flask import Blueprint, request, make_response, jsonify
import jwt
import datetime
import bcrypt
from decorators import jwt_required, admin_required
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

@authBP.route("/home/admin/activity_logs", methods=['GET'])
@admin_required
def showAllActivityLogs():
    page_num, page_size = 1, 10
    if request.args.get('pn'):
        page_num = int(request.args.get('pn'))
    if request.args.get('ps'):
        page_size = int(request.args.get('ps'))
    page_start = (page_size * (page_num - 1))

    data_to_return = []
    for log in activity_logs.find().skip(page_start).limit(page_size):
        log['_id'] = str(log['_id'])
        data_to_return.append(log)
    if not data_to_return:
        return make_response(jsonify( {"error" : "No activity logs were found"} ), 404)
    return make_response(jsonify(data_to_return), 200)
