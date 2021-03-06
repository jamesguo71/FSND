import os
import sys

from flask import Flask, request, abort, jsonify
from flask_sqlalchemy import SQLAlchemy
from flask_cors import CORS
import random

from models import setup_db, Question, Category

QUESTIONS_PER_PAGE = 10


def create_app(test_config=None):
    # create and configure the app
    app = Flask(__name__)
    setup_db(app)

    '''
    @TODO: Set up CORS. Allow '*' for origins. Delete the sample route after
    completing the TODOs
    '''
    CORS(app, resources={r'/*': {'origins': '*'}})

    '''
    @TODO: Use the after_request decorator to set Access-Control-Allow
    '''

    @app.after_request
    def set_access_control(response):
        response.headers.add(
            "Access-Control-Allow-Headers",
            "Content-Type, Authorization, true"
        )
        response.headers.add(
            "Access-Control-Allow-Methods",
            "GET, POST, PATCH, DELETE, OPTIONS"
        )
        return response

    '''
    @TODO:
    Create an endpoint to handle GET requests
    for all available categories.
    '''

    @app.route('/categories')
    def get_categories():
        categories = {}
        for category in Category.query.all():
            categories[category.id] = category.type
        return jsonify({
            'categories': categories
        })

    '''
    @TODO:
    Create an endpoint to handle GET requests for questions,
    including pagination (every 10 questions).
    This endpoint should return a list of questions,
    number of total questions, current category, categories.

    TEST: At this point, when you start the application
    you should see questions and categories generated,
    ten questions per page and pagination at the bottom of the screen for three
    pages. Clicking on the page numbers should update the questions.
    '''

    def paginate(selection):
        page = request.args.get('page', 1, type=int)
        start = (page - 1) * QUESTIONS_PER_PAGE
        end = start + QUESTIONS_PER_PAGE
        return selection[start:end]

    @app.route('/questions', methods=['GET'])
    def get_questions():
        all_questions = Question.query.all()
        paged_questions = [question.format()
                           for question in paginate(all_questions)]
        categories = {cat.id: cat.type for cat in Category.query.all()}
        return jsonify({
            'questions': paged_questions,
            'total_questions': len(all_questions),
            'current_category': None,
            'categories': categories
        })

    '''
    @TODO:
    Create an endpoint to DELETE question using a question ID.

    TEST: When you click the trash icon next to a question, the question will
    be removed.
    This removal will persist in the database and when you refresh the page.
    '''

    @app.route('/questions/<int:question_id>', methods=['DELETE'])
    def delete_question(question_id):
        question = Question.query.filter_by(id=question_id).first_or_404()
        question.delete()

        selection = Question.query.order_by(Question.id).all()
        current_questions = paginate(selection)
        formatted_questions = [question.format()
                               for question in current_questions]
        return jsonify({
            'success': True
        })
        # return jsonify({
        #     'success': True,
        #     'deleted': question_id,
        #     'questions': formatted_questions,
        #     'total_questions': len(Question.query.all())
        # })

    '''
    @TODO:
    Create an endpoint to POST a new question,
    which will require the question and answer text,
    category, and difficulty score.

    TEST: When you submit a question on the "Add" tab,
    the form will clear and the question will appear at the end of the last
    page of the questions list in the "List" tab.
    '''

    '''
    @TODO:
    Create a POST endpoint to get questions based on a search term.
    It should return any questions for whom the search term
    is a substring of the question.

    TEST: Search by any phrase. The questions list will update to include
    only question that include that string within their question.
    Try using the word "title" to start.
    '''

    @app.route('/questions', methods=['POST'])
    def add_or_search_question():
        data = request.get_json()
        if 'searchTerm' in data:
            match_questions = Question.query.filter(
                Question.question.ilike(f"%{data['searchTerm']}%")
            ).all()
            paginated_questions = paginate(match_questions)
            formatted_questions = [question.format()
                                   for question in paginated_questions]
            return jsonify({
                'success': True,
                'questions': formatted_questions,
                'total_questions': Question.query.count(),
                'current_category': [question.category
                                     for question in paginated_questions]
            })
        try:
            question = Question(question=data['question'],
                                answer=data['answer'],
                                category=data['category'],
                                difficulty=data['difficulty'])
            question.insert()
            return jsonify({
                'success': True,
                'created': question.id,
                'total_questions': Question.query.count()
            })
        except Exception as e:
            # print(sys.exc_info())
            # print(e)
            abort(422)

    '''
    @TODO:
    Create a GET endpoint to get questions based on category.

    TEST: In the "List" tab / main screen, clicking on one of the
    categories in the left column will cause only questions of that
    category to be shown.
    '''

    @app.route('/categories/<int:category_id>/questions')
    def get_questions_by_category(category_id):
        category = Category.query.filter_by(id=category_id).first_or_404()
        category_questions = Question.query.filter_by(
            category=category.id
        ).all()
        paginated_questions = paginate(category_questions)
        formatted_questions = [question.format()
                               for question in paginated_questions]
        return jsonify({
            'questions': formatted_questions,
            'total_questions': len(category_questions),
            'current_category': category.type
        })

    '''
    @TODO:
    Create a POST endpoint to get questions to play the quiz.
    This endpoint should take category and previous question parameters
    and return a random questions within the given category,
    if provided, and that is not one of the previous questions.

    TEST: In the "Play" tab, after a user selects "All" or a category,
    one question at a time is displayed, the user is allowed to answer
    and shown whether they were correct or not.
    '''

    @app.route('/quizzes', methods=['POST'])
    def play_quizzes():
        try:
            json_data = request.get_json()
            previous_questions = json_data['previous_questions']
            quiz_category = json_data['quiz_category']
            category_id = quiz_category['id']
        except KeyError:
            print(sys.exc_info())
            abort(422)
        if category_id == 0:
            candidates = Question.query.all()
        else:
            candidates = Question.query.filter_by(category=category_id).all()
        remaining_candidates = [candidate for candidate in candidates
                                if candidate.id not in previous_questions]
        if remaining_candidates:
            chosen_question = random.choice(remaining_candidates)
            formatted_question = chosen_question.format()
        else:
            formatted_question = None
        return jsonify({
            'question': formatted_question
        })

    '''
    @TODO:
    Create error handlers for all expected errors
    including 404 and 422.
    '''

    @app.errorhandler(400)
    def bad_request(error):
        return jsonify({
            'code': 400,
            'error': "Bad Request."
        })

    @app.errorhandler(404)
    def not_found(error):
        return jsonify({
            'code': 404,
            'error': "Not found."
        })

    @app.errorhandler(422)
    def unprocessable(error):
        return jsonify({
            'code': 422,
            'error': 'Unprocessable Request.'
        })

    @app.errorhandler(405)
    def method_not_allowed(error):
        return jsonify({
            'code': 405,
            'error': 'Method not allowed.'
        })

    @app.errorhandler(500)
    def internal_server_error(error):
        return jsonify({
            'code': 500,
            'error': 'Internal Server Error.'
        })

    return app
