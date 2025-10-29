from flask import Blueprint, request, make_response, jsonify
from bson import ObjectId
from decorators import jwt_required, admin_required
import globals

moviesBP = Blueprint("moviesBP", __name__)

movies = globals.db.movies

@moviesBP.route("/home/movies", methods=['GET'])
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

@moviesBP.route("/home/movies/<string:m_id>", methods=["GET"])
def showOneMovie(m_id):
    movie = movies.find_one( { '_id' : ObjectId(m_id) })
    if movie is not None:
        movie['_id'] = str(movie['_id'])
        for review in movie['reviews']:
            review['_id'] = str(review['_id'])
        return make_response(jsonify(movie), 200)
    else:
        return make_response(jsonify( {"error" : "Movie ID " + m_id + " was not found"} ), 404)

@moviesBP.route("/home/movies", methods=['POST'])
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

@moviesBP.route("/home/movies/<string:m_id>", methods=['PUT'])
@jwt_required
def editMovie(m_id):
    if 'Director' in request.form and 'Genre' in request.form and 'IMDB_Rating' in request.form and 'Released_Year' in request.form and 'Runtime' in request.form and 'Series_Title' in request.form:
        result = movies.update_one( { '_id' : ObjectId(m_id) }, {
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
            edited_movie_link = "http://localhost:5000/home/movies/" + m_id
            return make_response(jsonify( {"url" : edited_movie_link} ), 200)
        else:
            return make_response(jsonify( {"error" : "Invalid Movie ID"} ), 404)
    else:
        return make_response(jsonify( {"error" : "Missing Form Data"} ), 404)

@moviesBP.route("/home/movies/<string:m_id>", methods=['DELETE'])
@jwt_required
@admin_required
def deleteMovie(m_id):
    result = movies.delete_one( { "_id" : ObjectId(m_id) } )
    if result.deleted_count == 1:
        return make_response(jsonify( {} ), 200)
    else:
        return make_response(jsonify( {"error" : "Movie ID " + m_id + " was not found"} ), 404)

@moviesBP.route("/home/movies/title/<string:title>", methods=['GET'])
def showMoviesByTitle(title):
    pipeline = [
        { "$match" : { "Series_Title" : title} },
    ]
    data_to_return = []
    for movie in movies.aggregate(pipeline):
        movie['_id'] = str(movie['_id'])
        for review in movie['reviews']:
            review['_id'] = str(review['_id'])
        data_to_return.append(movie)
    if not data_to_return:
        return make_response(jsonify( {"error" : "No movies were found for the title " + title} ), 404)
    return make_response(jsonify(data_to_return), 200)

@moviesBP.route("/home/movies/director/<string:director>", methods=['GET'])
def showMoviesByDirector(director):
    pipeline = [
        { "$match" : { "Director" : director} },
    ]
    data_to_return = []
    for movie in movies.aggregate(pipeline):
        movie['_id'] = str(movie['_id'])
        for review in movie['reviews']:
            review['_id'] = str(review['_id'])
        data_to_return.append(movie)
    if not data_to_return:
        return make_response(jsonify( {"error" : "No movies were found for the director " + director} ), 404)
    return make_response(jsonify(data_to_return), 200)

@moviesBP.route("/home/movies/genre/<string:genre>", methods=['GET'])
def showMoviesByGenre(genre):
    pipeline = [
        { "$match" : { "Genre" : genre} },
    ]
    data_to_return = []
    for movie in movies.aggregate(pipeline):
        movie['_id'] = str(movie['_id'])
        for review in movie['reviews']:
            review['_id'] = str(review['_id'])
        data_to_return.append(movie)
    if not data_to_return:
        return make_response(jsonify( {"error" : "No movies were found for the genre " + genre} ), 404)
    return make_response(jsonify(data_to_return), 200)

@moviesBP.route("/home/movies/minrating/<float:minrating>", methods=['GET'])
def showMoviesAboveMinRating(minrating):
    pipeline = [
        { "$match" : { "IMDB_Rating" : { "$gte" : minrating} } },
    ]
    data_to_return = []
    for movie in movies.aggregate(pipeline):
        movie['_id'] = str(movie['_id'])
        for review in movie['reviews']:
            review['_id'] = str(review['_id'])
        data_to_return.append(movie)
    if not data_to_return:
        return make_response(jsonify( {"error" : "No movies were found with a rating more than or equal to " + str(minrating)} ), 404)
    return make_response(jsonify(data_to_return), 200)

@moviesBP.route("/home/movies/released/<int:year>", methods=['GET'])
def showMoviesByReleaseYear(year):
    pipeline = [
        { "$match" : { "Released_Year" : year} },
    ]
    data_to_return = []
    for movie in movies.aggregate(pipeline):
        movie['_id'] = str(movie['_id'])
        for review in movie['reviews']:
            review['_id'] = str(review['_id'])
        data_to_return.append(movie)
    if not data_to_return:
        return make_response(jsonify( {"error" : "No movies were found for the year " + str(year)} ), 404)
    return make_response(jsonify(data_to_return), 200)

@moviesBP.route("/home/movies/released_between/<int:lower_year>/<int:higher_year>", methods=['GET'])
def showMoviesReleasedBetweenYears(lower_year, higher_year):
    pipeline = [
        { "$match" : { "Released_Year" : { "$gte" : lower_year, "$lte" : higher_year} } },
    ]
    data_to_return = []
    for movie in movies.aggregate(pipeline):
        movie['_id'] = str(movie['_id'])
        for review in movie['reviews']:
            review['_id'] = str(review['_id'])
        data_to_return.append(movie)
    if not data_to_return:
        return make_response(jsonify( {"error" : "No movies were found between the years " + str(lower_year) + " and " + str(higher_year)} ), 404)
    return make_response(jsonify(data_to_return), 200)
