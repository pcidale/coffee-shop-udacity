from flask import Flask, request, jsonify, abort
import json
from flask_cors import CORS

from .database.models import db_drop_and_create_all, setup_db, Drink
from .auth.auth import AuthError, requires_auth

app = Flask(__name__)
setup_db(app)
CORS(app)

'''
@TODO uncomment the following line to initialize the database
!! NOTE THIS WILL DROP ALL RECORDS AND START YOUR DB FROM SCRATCH
!! NOTE THIS MUST BE UNCOMMENTED ON FIRST RUN
'''
db_drop_and_create_all()


# ROUTES
@app.route('/drinks')
def get_drinks_short():
    """
    Public endpoint to get short representation of all drinks in the database
    :return: status code and json containing the list of drinks
    """
    drinks = [drink.short() for drink in Drink.query.all()]
    return jsonify({
        'success': True,
        'drinks': drinks
    }), 200


@app.route('/drinks-detail')
@requires_auth('get:drinks-detail')
def get_drinks_long():
    """
    Reserved endpoint for users with permission 'get:drinks-detail' containing
    long representation of all drinks in the database
    :return: status code and json containing the list of drinks
    """
    drinks = [drink.long() for drink in Drink.query.all()]
    return jsonify({
        'success': True,
        'drinks': drinks
    }), 200


@app.route('/drinks', methods=['POST'])
@requires_auth('post:drinks')
def post_drink():
    """
    Reserved endpoint for users with permission 'post:drinks-detail', allowing
    them to create new drinks in the database
    :return: status code and json containing the newly created drink
    """
    drink = Drink(
        title=request.json['title'],
        recipe=json.dumps(request.json['recipe'])
    )
    drink.insert()
    return jsonify({
        'success': True,
        'drinks': [drink.long()]
    })


@app.route('/drinks/<int:drink_id>', methods=['PATCH'])
@requires_auth('patch:drinks')
def patch_drink(drink_id):
    """
    Reserved endpoint for users with permission 'patch:drinks-detail', allowing
    them to modify a drink in the database
    :param drink_id: drink unique id in the database
    :return: status code and json containing the updated drink
    """
    drink = Drink.query.get(drink_id)
    if drink:
        if 'title' in request.json:
            drink.title = request.json['title']
        if 'recipe' in request.json:
            drink.recipe = json.dumps(request.json['recipe'])
        drink.update()
        return jsonify({
            'success': True,
            'drinks': [drink.long()]
        })
    else:
        abort(404, f'Drink id {drink_id} not found')


@app.route('/drinks/<int:drink_id>', methods=['DELETE'])
@requires_auth('delete:drinks')
def delete_drink(drink_id):
    """
    Reserved endpoint for users with permission 'delete:drinks-detail', allowing
    them to delete drinks in the database
    :param drink_id: drink unique id in the database
    :return: status code and json containing the removed drink id
    """
    drink = Drink.query.get(drink_id)
    if drink:
        drink.delete()
        return jsonify({
            'success': True,
            'delete': drink_id
        })
    else:
        abort(404, f'Drink id {drink_id} not found')


# Error Handling
@app.errorhandler(422)
def unprocessable(error):
    """
    Handler for unprocessable errors
    :param error:
    :return: status code and json with error message
    """
    return jsonify({
        "success": False,
        "error": 422,
        "message": "unprocessable"
    }), 422


@app.errorhandler(404)
def not_found(error):
    """
        Handler for resources not found
        :param error:
        :return: status code and json with error message
        """
    return jsonify({
        "success": False,
        "error": 404,
        "message": "resource not found"
    }), 404


@app.errorhandler(AuthError)
def handle_auth_error(exception):
    """
    Authentication error handler for scoped endpoints
    :param exception: AuthError instance
    :return: response: status code and the error description
    """
    response = jsonify(exception.error)
    response.status_code = exception.status_code
    return response


@app.errorhandler(500)
def internal_server_error(error):
    """
    Handler for internal errors
    :param error:
    :return: status code and json with error message
    """
    return jsonify(
        {
            'success': False,
            'message': 'internal error',
            'error': 500
        }
    ), 500
