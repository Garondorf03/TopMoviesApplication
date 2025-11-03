from flask import Blueprint, request, make_response, jsonify
from bson import ObjectId
from decorators import jwt_required, admin_required
import globals

platformsBP = Blueprint("platformsBP", __name__)

movies = globals.db.movies
platforms = globals.db.platforms

@platformsBP.route("/home/movies/<string:m_id>/platforms", methods=['GET'])
def showAllPlatforms(m_id):
    data_to_return = []
    platforms_list = platforms.find_one({ "movie_id": ObjectId(m_id) }, { "platforms": 1, "_id": 0 })
    if platforms_list is not None:
        for platform in platforms_list['platforms']:
            data_to_return.append({
                "_id": str(platform['_id']),
                "name": platform['name'],
                "subscription_required": platform['subscription_required']
            })
    if not data_to_return:
        return make_response(jsonify( {"error" : "No platforms were found for the Movie ID " + m_id} ), 404)
    return make_response(jsonify(data_to_return), 200)

@platformsBP.route("/home/movies/<string:m_id>/platforms/<string:p_id>", methods=['GET'])
def showOnePlatform(m_id, p_id):
    movie = platforms.find_one(
        { "movie_id": ObjectId(m_id), "platforms._id": ObjectId(p_id) },
        { "_id": 0, "platforms.$": 1
    })
    if movie is None:
        return make_response(jsonify({"Error": "Invalid Movie ID or Platform ID"}), 404)
    movie['platforms'][0]['_id'] = str(movie['platforms'][0]['_id'])
    return make_response(jsonify(movie['platforms'][0]), 200)

@platformsBP.route("/home/movies/<string:m_id>/platforms", methods=['POST'])
@jwt_required
def addPlatform(m_id):
    if 'name' in request.form and 'subscription_required' in request.form:
        new_platform = {
            '_id': ObjectId(),
            'name': request.form['name'],
            'subscription_required': request.form['subscription_required'].lower()
        }
        platforms.update_one(
            { "movie_id": ObjectId(m_id) },
            { "$push": { "platforms": new_platform } }
        )
        new_platform_link = "http://localhost:5000/home/movies/" + m_id + "/platforms/" + str(new_platform['_id'])
        return make_response(jsonify({"url": new_platform_link}), 201)
    else:
        return make_response(jsonify( {"error" : "Missing Form Data"} ), 404)

@platformsBP.route("/home/movies/<string:m_id>/platforms/<string:p_id>", methods=['PUT'])
@jwt_required
def editPlatform(m_id, p_id):
    if 'name' in request.form and 'subscription_required' in request.form:
        edited_platform = {
            "platforms.$.name": request.form['name'],
            "platforms.$.subscription_required": request.form['subscription_required'].lower()
        }
        platforms.update_one(
            { "platforms._id": ObjectId(p_id) },
            { "$set": edited_platform }
        )
        edited_platform_url = "http://localhost:5000/home/movies/" + m_id + "/platforms/" + p_id
        return make_response(jsonify({"url": edited_platform_url}), 200)
    else:
        return make_response(jsonify( {"error" : "Missing Form Data"} ), 404)

@platformsBP.route("/home/movies/<string:m_id>/platforms/<string:p_id>", methods=['DELETE'])
@jwt_required
@admin_required
def deletePlatform(m_id, p_id):
    result = platforms.update_one(
        { "movie_id": ObjectId(m_id) },
        { "$pull": { "platforms": { "_id": ObjectId(p_id)}}}
    )
    if result.modified_count == 0:
        return make_response(jsonify({"Error": "Movie ID or Platform ID not found"}), 404)
    return make_response(jsonify({"Message": "Platform ID " +  p_id + " deleted successfully"}), 200)
