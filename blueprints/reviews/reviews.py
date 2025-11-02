from flask import Blueprint, request, make_response, jsonify
from bson import ObjectId
from decorators import jwt_required, admin_required
import globals

reviewsBP = Blueprint("reviewsBP", __name__)

movies = globals.db.movies

@reviewsBP.route("/home/movies/<string:m_id>/reviews", methods=['GET'])
def showAllReviews(m_id):
    data_to_return = []
    movie = movies.find_one( { "_id" : ObjectId(m_id) }, { "reviews" : 1, "_id" : 0} )
    for review in movie['reviews']:
        review['_id'] = str(review['_id'])
        data_to_return.append(review)
    if not data_to_return:
        return make_response(jsonify( {"error" : "No reviews were found for the Movie ID " + m_id} ), 404)
    return make_response(jsonify(data_to_return), 200)

@reviewsBP.route("/home/movies/<string:m_id>/reviews/<string:r_id>", methods=['GET'])
def showOneReview(m_id, r_id):
    movie = movies.find_one( { "reviews._id" : ObjectId(r_id) }, {
        "_id" : 0, "reviews.$" : 1
    })
    if movie is None:
        return make_response(jsonify({"Error" : "Invalid Movie ID or Review ID"}), 404)
    movie['reviews'][0]['_id'] = str(movie['reviews'][0]['_id'])
    return make_response(jsonify(movie['reviews'][0]), 200)

@reviewsBP.route("/home/movies/<string:m_id>/reviews", methods=['POST'])
@jwt_required
def addReview(m_id):
    if 'rating' in request.form and 'review' in request.form and 'username' in request.form:
        new_review = {
            '_id' : ObjectId(),
            'rating' : request.form['rating'],
            'review' : request.form['review'],
            'username' : request.form['username']
        }
        movies.update_one( { "_id" : ObjectId(m_id) }, {
            "$push" : { "reviews" : new_review}
        })
        new_review_link = "http://localhost:5000/home/movies/" + m_id + "/reviews/" + str(new_review['_id'])
        return make_response(jsonify( {"url" : new_review_link} ), 201)
    else:
        return make_response(jsonify( {"error" : "Missing Form Data"} ), 404)

@reviewsBP.route("/home/movies/<string:m_id>/reviews/<string:r_id>", methods=['PUT'])
@jwt_required
def editReview(m_id, r_id):
    if 'rating' in request.form and 'review' in request.form and 'username' in request.form:
        edited_review = {
            "reviews.$.rating" : request.form['rating'],
            "reviews.$.review" : request.form['review'],
            "reviews.$.username" : request.form['username']
        }
        movies.update_one({
            "reviews._id" : ObjectId(r_id)
        }, {
            "$set" : edited_review
        })
        edited_review_url = "http://localhost:5000/home/movies/" + m_id + "/reviews/" + r_id
        return make_response(jsonify({"url" : edited_review_url}), 200)
    else:
        return make_response(jsonify( {"error" : "Missing Form Data"} ), 404)

@reviewsBP.route("/home/movies/<string:m_id>/reviews/<string:r_id>", methods=['DELETE'])
@jwt_required
@admin_required
def deleteReview(m_id, r_id):
    result = movies.update_one({
        "_id" :     ObjectId(m_id)
    }, {
        "$pull" : {"reviews" : {"_id" : ObjectId(r_id)}}
    })
    if result.modified_count == 1:
        return make_response(jsonify( {"message" : "Review ID " + r_id + " deleted successfully"} ), 200)
    else:
        return make_response(jsonify( {"error" : "Review ID " + r_id + " was not found for Movie ID " + m_id} ), 404)

@reviewsBP.route("/home/movies/reviewed_by/<string:username>", methods=['GET'])
def showMoviesReviewedByUser(username):
    pipeline = [
        { "$match" : { "reviews.username" : username} },
    ]
    data_to_return = []
    for movie in movies.aggregate(pipeline):
        movie['_id'] = str(movie['_id'])
        for review in movie['reviews']:
            review['_id'] = str(review['_id'])
        data_to_return.append(movie)
    if not data_to_return:
        return make_response(jsonify( {"error" : "No reviews were found for the user " + username} ), 404)
    return make_response(jsonify(data_to_return), 200)