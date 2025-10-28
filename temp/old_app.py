from flask import Flask, request, jsonify, make_response
from pymongo import MongoClient
from bson import ObjectId
import jwt
import datetime
from functools import wraps
import bcrypt

app = Flask(__name__)
app.config['SECRET_KEY'] = 'zelda'

client = MongoClient("mongodb://127.0.0.1:27017")
db = client.movieApp
movies = db.movies
users = db.users
blacklist = db.blacklist

def jwt_required(func):
    @wraps(func)
    def jwt_required_wrapper(*args, **kwargs):
        token = None
        if 'x-access-token' in request.headers:
            token = request.headers['x-access-token']
        if not token:
            return make_response(jsonify({'message' : 'Token is missing'}), 401)
        try:
            data = jwt.decode(token, app.config['SECRET_KEY'], algorithms='HS256')
        except:
            return make_response(jsonify({'message' : 'Token is invalid'}), 401)
        bl_token = blacklist.find_one({"token":token})
        if bl_token is not None:
            return make_response(jsonify({'message' : 'Token has been cancelled'}), 401)
        return func(*args, **kwargs)
    return jwt_required_wrapper

def admin_required(func):
    @wraps(func)
    def admin_required_wrapper(*args, **kwargs):
        token = request.headers['x-access-token']
        data = jwt.decode(token, app.config['SECRET_KEY'], algorithms="HS256")
        if data["admin"]:
            return func(*args, **kwargs)
        else:
            return make_response(jsonify({'message' : 'Admin access required'}), 401 )
    return admin_required_wrapper

@app.route("/home/movies", methods=['GET'])
def showAllMovies():
    page_num, page_size = 1, 10
    if request.args.get('pn'):
        page_num = int(request.args.get('pn'))
    if request.args.get('ps'):
        page_size = int(request.args.get('ps'))
    page_start = (page_size * (page_num - 1))

    data_to_return = []
    for movie in movies.find().skip(page_start).limit(page_size):
        movie['_id'] = str(movie['_id'])
        for review in movie['reviews']:
            review['_id'] = str(review['_id'])
        data_to_return.append(movie)

    return make_response(jsonify(data_to_return), 200)

@app.route("/home/movies/<string:id>", methods=["GET"])
def showOneMovie(id):
    movie = movies.find_one( { '_id' : ObjectId(id) })
    if movie is not None:
        movie['_id'] = str(movie['_id'])
        for review in movie['reviews']:
            review['_id'] = str(review['_id'])
        return make_response(jsonify(movie), 200)
    else:
        return make_response(jsonify( {"error" : "Movie ID " + id + " was not found"} ), 404)

@app.route("/home/movies", methods=['POST'])
@jwt_required
def addNewMovie():
    if 'Director' in request.form and 'Genre' in request.form and 'IMDB_Rating' in request.form and 'Released_Year' in request.form and 'Runtime' in request.form and 'Series_Title' in request.form:
        newMovie = {
            "Director" : request.form['Director'],
            "Genre" : request.form['Genre'],
            "IMDB_Rating" : request.form['IMDB_Rating'],
            "Released_Year" : request.form['Released_Year'],
            "Runtime" : request.form['Runtime'],
            "Series_Title" : request.form['Series_Title'],
            "reviews" : []
        }
        new_movie_id = movies.insert_one(newMovie)
        new_movie_link = "http://localhost:5000/home/movies/" + str(new_movie_id.inserted_id)
        return make_response(jsonify( {"url" : new_movie_link} ), 201)
    else:
        return make_response(jsonify( {"error" : "Missing Form Data"} ), 404)

@app.route("/home/movies/<string:id>", methods=['PUT'])
@jwt_required
def editMovie(id):
    if 'Director' in request.form and 'Genre' in request.form and 'IMDB_Rating' in request.form and 'Released_Year' in request.form and 'Runtime' in request.form and 'Series_Title' in request.form:
        result = movies.update_one( { '_id' : ObjectId(id) }, {
            "$set" : {
                "Director" : request.form['Director'],
                "Genre" : request.form['Genre'],
                "IMDB_Rating" : request.form['IMDB_Rating'],
                "Released_Year" : request.form['Released_Year'],
                "Runtime" : request.form['Runtime'],
                "Series_Title" : request.form['Series_Title']
            }
        })
        if result.matched_count == 1:
            edited_movie_link = "http://localhost:5000/home/movies/" + id
            return make_response(jsonify( {"url" : edited_movie_link} ), 200)
        else:
            return make_response(jsonify( {"error" : "Invalid Movie ID"} ), 404)
    else:
        return make_response(jsonify( {"error" : "Missing Form Data"} ), 404)

@app.route("/home/movies/<string:id>", methods=['DELETE'])
@jwt_required
@admin_required
def deleteMovie(id):
    result = movies.delete_one( { "_id" : ObjectId(id) } )
    if result.deleted_count == 1:
        return make_response(jsonify( {} ), 200)
    else:
        return make_response(jsonify( {"error" : "Movie ID " + id + " was not found"} ), 404)

@app.route("/home/movies/<string:id>/reviews", methods=['GET'])
def showAllReviews(id):
    data_to_return = []
    movie = movies.find_one( { "_id" : ObjectId(id) }, { "reviews" : 1, "_id" : 0} )
    for review in movie['reviews']:
        review['_id'] = str(review['_id'])
        data_to_return.append(review)
    return make_response(jsonify(data_to_return), 200)

@app.route("/home/movies/<string:id>/reviews/<string:id2>", methods=['GET'])
def showOneReview(id, id2):
    movie = movies.find_one( { "reviews._id" : ObjectId(id2) }, {
        "_id" : 0, "reviews.$" : 1
    })
    if movie is None:
        return make_response(jsonify({"Error" : "Invalid Movie ID or Review ID"}), 404)
    movie['reviews'][0]['_id'] = str(movie['reviews'][0]['_id'])
    return make_response(jsonify(movie['reviews'][0]), 200)

@app.route("/home/movies/<string:id>/reviews", methods=['POST'])
@jwt_required
def addReview(id):
    new_review = {
        '_id' : ObjectId(),
        'rating' : request.form['rating'],
        'review' : request.form['review'],
        'username' : request.form['username']
    }
    movies.update_one( { "_id" : ObjectId(id) }, {
        "$push" : { "reviews" : new_review}
    })
    new_review_link = "http://localhost:5000/home/movies/" + id + "/reviews/" + str(new_review['_id'])
    return make_response(jsonify( {"url" : new_review_link} ), 201)

@app.route("/home/movies/<string:id>/reviews/<string:id2>", methods=['PUT'])
@jwt_required
def editReview(id, id2):
    edited_review = {
        "reviews.$.rating" : request.form['rating'],
        "reviews.$.review" : request.form['review'],
        "reviews.$.username" : request.form['username']
    }
    movies.update_one({
        "reviews._id" : ObjectId(id2)
    }, {
        "$set" : edited_review
    })
    edited_review_url = "http://localhost:5000/home/movies/" + id + "/reviews/" + id2
    return make_response(jsonify({"url" : edited_review_url}), 200)

@app.route("/home/movies/<string:id>/reviews/<string:id2>", methods=['DELETE'])
@jwt_required
@admin_required
def deleteReview(id, id2):
    movies.update_one({
        "_id" :     ObjectId(id)
    }, {
        "$pull" : {"reviews" : {"_id" : ObjectId(id2)}}
    })
    return make_response(jsonify({}), 200)


@app.route("/home/login", methods=['GET'])
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
                }, app.config['SECRET_KEY'], algorithm='HS256')
                return make_response(jsonify({'token' : token}), 200)
            else:
                return make_response(jsonify({'message' : 'Incorrect password'}), 401)
        else:
            return make_response(jsonify({'message' : 'User not found'}), 401)
    return make_response(jsonify({'message' : 'Authentication required'}), 401)

@app.route("/home/logout", methods=['GET'])
@jwt_required
def logout():
    token = request.headers['x-access-token']
    blacklist.insert_one({"token":token})
    return make_response(jsonify({'message' : 'Logout successful'}), 200 )

if __name__ == "__main__":
    app.run(debug=True)