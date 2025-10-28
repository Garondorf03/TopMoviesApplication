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

@reviewsBP.route("/home/movies/<string:m_id>/reviews/<string:r_id>", methods=['PUT'])
@jwt_required
def editReview(m_id, r_id):
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

@reviewsBP.route("/home/movies/<string:m_id>/reviews/<string:r_id>", methods=['DELETE'])
@jwt_required
@admin_required
def deleteReview(m_id, r_id):
    movies.update_one({
        "_id" :     ObjectId(m_id)
    }, {
        "$pull" : {"reviews" : {"_id" : ObjectId(r_id)}}
    })
    return make_response(jsonify({}), 200)