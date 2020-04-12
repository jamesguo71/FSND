import os
import unittest
import json
from flask_sqlalchemy import SQLAlchemy

from flaskr import create_app
from models import setup_db, Question, Category


class TriviaTestCase(unittest.TestCase):
    """This class represents the trivia test case"""

    def setUp(self):
        """Define test variables and initialize app."""
        self.app = create_app()
        self.client = self.app.test_client
        self.database_name = "trivia_test"
        self.database_path = "postgres://{}/{}".format(
            'localhost:5432',
            self.database_name
        )
        setup_db(self.app, self.database_path)

        # binds the app to the current context
        with self.app.app_context():
            self.db = SQLAlchemy()
            self.db.init_app(self.app)
            # create all tables
            self.db.create_all()

    def tearDown(self):
        """Executed after reach test"""
        pass

    """
    TODO
    Write at least one test for each test for successful operation
    and for expected errors.
    """

    def test_get_all_categories(self):
        res = self.client().get('/categories')
        json_res = json.loads(res.data)

        self.assertTrue(json_res['categories'])
        # self.assertTrue(len(json_res['categories']))

    def test_405_on_delete_all_categories(self):
        res = self.client().delete('/categories')
        json_res = json.loads(res.data)

        self.assertEqual(json_res['error'], 'Method not allowed.')

    def test_get_all_questions(self):
        res = self.client().get('/questions')
        json_res = json.loads(res.data)

        self.assertTrue(len(json_res['questions']))
        self.assertIsNone(json_res['current_category'])

    def test_405_on_delete_all_questions(self):
        res = self.client().delete('/questions')
        json_res = json.loads(res.data)

        self.assertEqual(json_res['error'], 'Method not allowed.')

    def test_delete_and_add_back_question(self):
        question_res = self.client().get('/categories/2/questions')
        questions_json = json.loads(question_res.data)
        some_question = questions_json['questions'][-1]
        some_question_id = questions_json['questions'][-1]['id']
        res = self.client().delete(f'/questions/{some_question_id}')
        json_res = json.loads(res.data)

        self.assertEqual(json_res['success'], True)

        add_res = self.client().post('/questions', json=some_question)
        add_res_json = json.loads(add_res.data)
        self.assertEqual(add_res_json['success'], True)

    def test_404_if_delete_question_not_exist(self):
        res = self.client().delete('/questions/10000')
        json_res = json.loads(res.data)

        self.assertEqual(json_res['code'], 404)

    def test_add_question(self):
        res = self.client().post('/questions', json={
            'question': 'Greatest Singer of All Time',
            'answer': 'Eminem',
            'category': 5,
            'difficulty': 4
        })
        json_res = json.loads(res.data)

        self.assertEqual(json_res['success'], True)

    def test_422_if_data_incomplete(self):
        res = self.client().post('/questions', json={
            'question': 'Greatest Singer of All Time',
            'category': 1,
            'difficulty': 4
        })
        json_res = json.loads(res.data)

        self.assertEqual(json_res['code'], 422)

    def test_search_term(self):
        res = self.client().post('/questions', json={'searchTerm': 'singer'})
        json_res = json.loads(res.data)

        self.assertEqual(json_res['success'], True)
        self.assertGreater(len(json_res['questions']), 0)

    def test_on_non_existing_search_question_term(self):
        res = self.client().post('/questions', json={
            'searchTerm': 'flkadskfsasfjkdafkas'})
        json_res = json.loads(res.data)

        self.assertEqual(len(json_res['questions']), 0)

    def test_get_questions_by_category(self):
        res = self.client().get('/categories/1/questions')
        json_res = json.loads(res.data)

        self.assertEqual(json_res['current_category'], 'Science')
        self.assertTrue(len(json_res['questions']))

    def test_404_if_category_not_exist(self):
        res = self.client().get('/categories/100000/questions')
        json_res = json.loads(res.data)

        self.assertEqual(json_res['code'], 404)

    def test_play_quizzes_all(self):
        res = self.client().post('/quizzes', json={
            'previous_questions': [],
            'quiz_category': {'type': '', 'id': 0}
        })
        json_res = json.loads(res.data)

        self.assertTrue(json_res['question'])

    def test_play_science_quizzes(self):
        res = self.client().post('/quizzes', json={
            'previous_questions': [],
            'quiz_category': {
                'type': 'Science',
                'id': 1
            }
        })
        json_res = json.loads(res.data)

        self.assertTrue(len(json_res['question']))

    def test_play_science_quizzes_no_remaining_question(self):
        res = self.client().post('/quizzes', json={
            'previous_questions': [20, 21, 22],
            'quiz_category':
                {'type': 'Science', 'id': 1}
        })
        json_res = json.loads(res.data)

        self.assertIsNone(json_res['question'])

    def test_422_play_quizzes_invalid_json_input(self):
        res = self.client().post('/quizzes', json={
            'quiz_category': {
                'type': 'Science',
                'id': 1
            }
        })
        json_res = json.loads(res.data)

        self.assertEqual(json_res['code'], 422)


# Make the tests conveniently executable
if __name__ == "__main__":
    unittest.main()
