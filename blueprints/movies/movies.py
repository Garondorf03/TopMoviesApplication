from flask import Blueprint, request, make_response, jsonify
from bson import ObjectId
from decorators import jwt_required, admin_required
import globals, random

moviesBP = Blueprint("moviesBP", __name__)

movies = globals.db.movies
platforms = globals.db.platforms

locations = {
    "Los Angeles": [34.00, -118.50, 34.10, -118.20],
    "New York": [40.70, -74.10, 40.80, -73.90],
    "London": [51.48, -0.15, 51.55, 0.00],
    "Tokyo": [35.65, 139.70, 35.75, 139.85],
    "Paris": [48.85, 2.25, 48.90, 2.40],
    "Sydney": [-34.00, 151.10, -33.85, 151.25],
    "Berlin": [52.50, 13.30, 52.55, 13.45],
    "Toronto": [43.65, -79.45, 43.70, -79.35],
    "Chicago": [41.85, -87.70, 41.90, -87.60],
    "Rome": [41.88, 12.45, 41.92, 12.55],
    "Hong Kong": [22.25, 114.10, 22.35, 114.20],
    "Dubai": [25.20, 55.25, 25.30, 55.35],
    "San Francisco": [37.70, -122.50, 37.80, -122.40],
    "Vancouver": [49.25, -123.15, 49.30, -123.10]
}

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
    if not data_to_return:
        return make_response(jsonify( {"error" : "No movies were found"} ), 404)
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
    if ('Director' in request.form and 'Genre' in request.form and 'IMDB_Rating' in request.form and
            'Released_Year' in request.form and 'Runtime' in request.form and 'Series_Title' in request.form):
        location_filmed = random.choice(list(locations.keys()))
        coordinates = locations[location_filmed]
        rand_lat = coordinates[0] + ((coordinates[2] - coordinates[0]) * random.random())
        rand_lng = coordinates[1] + ((coordinates[3] - coordinates[1]) * random.random())
        new_movie = {
            "Director" : request.form['Director'],
            "Genre" : request.form['Genre'],
            "IMDB_Rating" : float(request.form['IMDB_Rating']),
            "Released_Year" : int(request.form['Released_Year']),
            "Runtime" : request.form['Runtime'],
            "Series_Title" : request.form['Series_Title'],
            "Filming_Location": location_filmed,
            "location": {
                "type": "Point",
                "coordinates": [rand_lng, rand_lat]
            },
            "reviews" : []
        }
        movie_result = movies.insert_one(new_movie)
        new_movie_id = movie_result.inserted_id
        new_platform_doc = {
            "movie_id": new_movie_id,
            "platforms": []
        }
        platforms.insert_one(new_platform_doc)
        new_movie_link = "http://localhost:5000/home/movies/" + str(new_movie_id)
        return make_response(jsonify( {"url" : new_movie_link} ), 201)
    else:
        return make_response(jsonify( {"error" : "Missing Form Data"} ), 404)

@moviesBP.route("/home/movies/<string:m_id>", methods=['PUT'])
@jwt_required
def editMovie(m_id):
    if ('Director' in request.form and 'Genre' in request.form and 'IMDB_Rating' in request.form and
            'Released_Year' in request.form and 'Runtime' in request.form and 'Series_Title' in request.form):
        result = movies.update_one( { '_id' : ObjectId(m_id) }, {
            "$set" : {
                "Director" : request.form['Director'],
                "Genre" : request.form['Genre'],
                "IMDB_Rating" : float(request.form['IMDB_Rating']),
                "Released_Year" : int(request.form['Released_Year']),
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
        platforms.delete_one({"movie_id": ObjectId(m_id)})
        return make_response(jsonify( {"message" : "Movie ID " + m_id + " deleted successfully"} ), 200)
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

@moviesBP.route("/home/movies/genre_avg_rating", methods=['GET'])
def showGenresAvgRating():
    pipeline = [
        {
            "$group": { "_id": "$Genre", "average_rating": { "$avg": "$IMDB_Rating" }, "count": { "$sum": 1 } } # also count number of movies in that genre
        },
        {
            "$sort": { "average_rating": -1 }  # sort descending by average rating
        }
    ]
    data_to_return = []
    for genre in movies.aggregate(pipeline):
        data_to_return.append({
            "genre": genre["_id"],
            "average_rating": round(genre["average_rating"], 2),
            "number_of_movies": genre["count"]
        })
    if not data_to_return:
        return make_response(jsonify( {"error" : "No data found"} ), 404)
    return make_response(jsonify(data_to_return), 200)

@moviesBP.route("/home/movies/<string:m_id>/filmed_nearby", methods=['GET'])
def showNearbyFilmedMovies(m_id):
    movie = movies.find_one({"_id": ObjectId(m_id)})
    if not movie or "location" not in movie:
        return make_response(jsonify({"error": "Movie ID " + m_id + " was not found or it has no location"}), 404)
    pipeline = [
        {
            "$geoNear": {
                "near": movie["location"],
                "distanceField": "distance",
                "minDistance": 1,
                "maxDistance": 50000,
                "spherical": True
            }
        },
        {"$project": {"Series_Title": 1, "Filming_Location": 1, "distance": 1}},
        {"$limit": 5}
    ]
    nearby = list(movies.aggregate(pipeline))
    for movie_document in nearby:
        movie_document["_id"] = str(movie_document["_id"])
        movie_document["distance_km"] = round(movie_document["distance"] / 1000, 2)
    if not nearby:
        return make_response(jsonify({"error": "No movies were found filmed nearby"}), 404)
    return make_response(jsonify(nearby), 200)
