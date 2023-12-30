import datetime
import json
import os
import unittest
import uuid

from faker import Faker

from api.api import app as restful_api
from models.db_session import global_init, create_session
from models.questions import QuestionGroupAssociation, Question, QuestionType, AnswerRecord, AnswerState
from tools import Settings

fake = Faker()


class TestDatabaseFunctions(unittest.TestCase):
    def test_global_init(self):
        # Test if global_init initializes the session factory without errors
        db_file = ":memory:"  # Use an in-memory database for testing
        global_init(db_file)

    def test_create_session(self):
        # Test if create_session returns a valid session
        db_file = ":memory:"
        global_init(db_file)

        # Ensure create_session doesn't raise an exception
        session = create_session()
        self.assertIsNotNone(session)


class TestQuestionGroupAssociation(unittest.TestCase):
    def setUp(self):
        db_file = ":memory:"
        global_init(db_file, drop_db=True)
        self.session = create_session()

    def tearDown(self):
        # Clean up resources after each test
        self.session.rollback()
        self.session.close()

    def test_association_attributes(self):
        # Test if attributes are set up correctly
        association = QuestionGroupAssociation(question_id=1, group_id='group_1')
        self.assertEqual(association.question_id, 1)
        self.assertEqual(association.group_id, 'group_1')

    def test_association_relationships(self):
        # Test if relationships are set up correctly

        question = Question(text=fake.sentence(),
                            options=json.dumps(fake.words(4)),
                            answer="1",
                            level=1)
        self.session.add(question)
        self.session.commit()

        association = QuestionGroupAssociation(question_id=question.id, group_id='group_1')
        self.session.add(association)
        self.session.commit()

        retrieved_question = self.session.query(Question).filter_by(id=question.id).first()
        self.assertIn(association, retrieved_question.groups)


class TestQuestion(unittest.TestCase):
    def setUp(self):
        db_file = ":memory:"
        global_init(db_file, drop_db=True)
        self.session = create_session()

    def tearDown(self):
        # Clean up resources after each test
        self.session.rollback()
        self.session.close()

    def test_question_attributes(self):
        # Test if attributes are set up correctly
        question = Question(
            text='Sample Question',
            subject='Sample Subject',
            options='["Option 1", "Option 2", "Option 3"]',
            answer='1',
            level=2,
            article_url='http://example.com',
            type='OPEN'
        )
        self.session.add(question)
        self.session.commit()

        question_from_db = self.session.get(Question, question.id)

        self.assertEqual(question.text, question_from_db.text)
        self.assertEqual(question.subject, question_from_db.subject)
        self.assertEqual(question.options, question_from_db.options)
        self.assertEqual(question.answer, question_from_db.answer)
        self.assertEqual(question.level, question_from_db.level)
        self.assertEqual(question.article_url, question_from_db.article_url)
        self.assertEqual(question.type, question_from_db.type)

    def test_question_groups_relationship(self):
        # Test if the relationship with QuestionGroupAssociation is set up correctly
        question = Question(
            text='Sample Question',
            options='["Option 1", "Option 2", "Option 3"]',
            answer='1',
            level=2,
            type='TEST'
        )

        association = QuestionGroupAssociation(group_id='group_1')
        question.groups.append(association)
        self.session.add(question)
        self.session.commit()

        retrieved_question = self.session.query(Question).filter_by(id=question.id).first()
        self.assertIn(association, retrieved_question.groups)


class TestAnswerRecord(unittest.TestCase):
    def setUp(self):
        # Use an in-memory database for testing
        db_file = ":memory:"
        global_init(db_file, drop_db=True)
        self.session = create_session()

    def tearDown(self):
        # Clean up resources after each test
        self.session.rollback()
        self.session.close()

    def test_answer_record_attributes(self):
        # Test if attributes are set up correctly
        question = Question(
            text='Sample Question',
            options='["Option 1", "Option 2", "Option 3"]',
            answer='1',
            level=2,
            type='TEST'
        )
        self.session.add(question)
        self.session.commit()

        answer_record = AnswerRecord(
            question_id=question.id,
            person_id='user_1',
            person_answer='1',
            ask_time=datetime.datetime(2024, 1, 1, 12, 0, 0),
            state=AnswerState.NOT_ANSWERED,
            points=0.5  # Set a non-default value for testing
        )

        self.session.add(answer_record)
        self.session.commit()
        answer_record = self.session.get(AnswerRecord, answer_record.id)

        self.assertEqual(answer_record.question_id, question.id)
        self.assertEqual(answer_record.person_id, 'user_1')
        self.assertEqual(answer_record.person_answer, '1')
        self.assertEqual(answer_record.ask_time, datetime.datetime(2024, 1, 1, 12, 0, 0))
        self.assertEqual(answer_record.state, AnswerState.NOT_ANSWERED)
        self.assertEqual(answer_record.points, 0.5)

    def test_answer_record_relationship(self):
        # Test if the relationship with Question is set up correctly
        question = Question(
            text='Sample Question',
            options='["Option 1", "Option 2", "Option 3"]',
            answer='1',
            level=2,
            type='TEST'
        )
        self.session.add(question)
        self.session.commit()

        answer_record = AnswerRecord(
            question_id=question.id,
            person_id='user_1',
            person_answer='1',
            ask_time=datetime.datetime(2024, 1, 1, 12, 0, 0),
            state=AnswerState.NOT_ANSWERED,
            points=0.5  # Set a non-default value for testing
        )

        self.session.add(answer_record)
        self.session.commit()
        answer_record = self.session.get(AnswerRecord, answer_record.id)

        retrieved_question = self.session.query(Question).filter_by(id=question.id).first()
        self.assertEqual(answer_record.question_id, retrieved_question.id)

    def test_calculate_points_test_type(self):
        # Test calculate_points method for QuestionType.TEST
        question = Question(
            text='Sample Question',
            options='["Option 1", "Option 2", "Option 3"]',
            answer='1',
            level=2,
            type='TEST'
        )
        self.session.add(question)
        self.session.commit()

        answer_record = AnswerRecord(
            question_id=question.id,
            question=question,
            person_id='user_1',
            person_answer='1',
            ask_time=datetime.datetime(2024, 1, 1, 12, 0, 0),
            state=AnswerState.NOT_ANSWERED,
            points=0.5
        )

        answer_record.calculate_points()
        self.assertEqual(answer_record.points, 1)


class TestAnswerResource(unittest.TestCase):
    def setUp(self):
        # Use an in-memory database for testing
        db_file = ":memory:"
        global_init(db_file, drop_db=True)
        self.app = restful_api.test_client()
        self.session = create_session()

    def tearDown(self):
        # Clean up resources after each test
        self.session.rollback()
        self.session.close()

    def test_get_existing_answer(self):
        # Create a test AnswerRecord
        answer = AnswerRecord(
            person_id='user_1',
            question_id=1,
            ask_time=datetime.datetime(2024, 1, 1, 12, 0, 0),
            state=AnswerState.NOT_ANSWERED
        )
        self.session.add(answer)
        self.session.commit()

        # Make the request
        with self.app as client:
            response = client.get(f'/answer/{answer.id}')
            result_json = response.get_json()

            # Assertions
            self.assertEqual(200, response.status_code)
            self.assertEqual(answer.id, result_json['id'])
            self.assertEqual('user_1', result_json['person_id'])
            self.assertEqual(1, result_json['question_id'])
            self.assertEqual(AnswerState.NOT_ANSWERED, AnswerState(result_json['state']))

    def test_get_nonexistent_answer(self):
        # Make the request for a nonexistent answer
        with self.app as client:
            response = client.get('/answer/1042')

            # Assertions
            self.assertEqual(404, response.status_code)


class TestAnswerListResource(unittest.TestCase):
    def setUp(self):
        # Use an in-memory database for testing
        db_file = ":memory:"
        global_init(db_file, drop_db=True)
        self.app = restful_api.test_client()
        self.session = create_session()

    def tearDown(self):
        # Drop all tables and close the session
        self.session.rollback()
        self.session.close()

    def test_get_method_with_filtering(self):
        # Create test AnswerRecords
        answer_1 = AnswerRecord(person_id='user_1', question_id=1, ask_time=datetime.datetime(2024, 1, 1, 12, 0, 0),
                                state=AnswerState.NOT_ANSWERED)
        answer_2 = AnswerRecord(person_id='user_2', question_id=2, ask_time=datetime.datetime(2024, 1, 2, 12, 0, 0),
                                state=AnswerState.NOT_ANSWERED)
        self.session.add_all([answer_1, answer_2])
        self.session.commit()

        with self.app as client:
            # Make the request with filtering parameters
            response = client.get('/answer/', json={'person_id': 'user_2'})
            result_json = response.get_json()

            # Assertions
            self.assertEqual(200, response.status_code)
            self.assertEqual(1, len(result_json))
            self.assertEqual('user_2', result_json[0]['person_id'])
            self.assertEqual(2, result_json[0]['question_id'])

    def test_post_method(self):
        with self.app as client:
            # Make the request to add a new answer
            response = client.post('/answer/', json={
                'person_id': 'user_1',
                'question_id': 1,
                'ask_time': '2024-01-01T12:01:00'
            })

            # Assertions
            self.assertEqual(response.status_code, 200)

            # Check if the new answer is in the database
            new_answer = self.session.query(AnswerRecord).filter_by(person_id='user_1', question_id=1).first()
            self.assertIsNotNone(new_answer)
            self.assertEqual(new_answer.state, AnswerState.NOT_ANSWERED)


class TestQuestionResource(unittest.TestCase):
    def setUp(self):
        # Use an in-memory database for testing
        db_file = ":memory:"
        global_init(db_file, drop_db=True)
        self.app = restful_api.test_client()
        self.session = create_session()

    def tearDown(self):
        # Drop all tables and close the session
        self.session.rollback()
        self.session.close()

    def test_get_method(self):
        # Create a test Question
        question = Question(
            text='What is the capital of France?',
            subject='Geography',
            options=json.dumps(['Berlin', 'Paris', 'London', 'Moscow']),
            answer='0',
            level=2,
            article_url='https://example.com/geography',
            type=QuestionType.TEST
        )
        self.session.add(question)
        self.session.commit()

        # Make the request
        with self.app as client:
            response = client.get(f'/question/{question.id}')
            result_json = response.get_json()

            # Assertions
            self.assertEqual(200, response.status_code)
            self.assertEqual('What is the capital of France?', result_json['text'])
            self.assertEqual('Geography', result_json['subject'])

    def test_post_method(self):
        # Make the request to create a new question
        with self.app as client:
            response = client.post('/question/', json={
                'text': 'What is the capital of Germany?',
                'subject': 'Geography',
                'options': ['Berlin', 'Paris', 'London', 'Moscow'],
                'answer': '0',
                'groups': ['group1', 'group2'],
                'level': 3,
                'article_url': 'https://example.com/AAAAAAAAAA',
                'type': 0
            })

            # Assertions
            self.assertEqual(200, response.status_code)

            result_json = response.get_json()
            self.assertEqual('What is the capital of Germany?', result_json['text'])
            self.assertEqual('Geography', result_json['subject'])
            self.assertEqual(['Berlin', 'Paris', 'London', 'Moscow'], result_json['options'])
            self.assertEqual('0', result_json['answer'])
            self.assertEqual([{'group_id': 'group1'}, {'group_id': 'group2'}], result_json['groups'])
            self.assertEqual(3, result_json['level'])
            self.assertEqual('https://example.com/AAAAAAAAAA', result_json['article_url'])
            self.assertEqual(0, result_json['type'])

    def test_delete_method(self):
        # Create a test Question
        question = Question(
            text='What is the capital of Spain?',
            subject='Geography',
            options=json.dumps(['Madrid', 'Barcelona', 'Seville', 'Chelyabinsk']),
            answer='0',
            level=2,
            article_url='https://example.com/geography',
            type=QuestionType.TEST
        )
        self.session.add(question)
        self.session.commit()

        # Make the request to delete the question
        with self.app as client:
            response = client.delete(f'/question/{question.id}')

            # Assertions
            self.assertEqual(response.status_code, 200)

            # Check if the question is deleted
            self.session.close()
            self.session = create_session()
            deleted_question = self.session.get(Question, question.id)
            self.assertIsNone(deleted_question)


class TestQuestionsListResource(unittest.TestCase):
    def setUp(self):
        # Use an in-memory database for testing
        db_file = ":memory:"
        global_init(db_file, drop_db=True)
        self.app = restful_api.test_client()
        self.session = create_session()

    def tearDown(self):
        # Drop all tables and close the session
        self.session.rollback()
        self.session.close()

    def test_get_method_with_search(self):
        # Create test Questions
        question_1 = Question(
            text='What is the capital of France?',
            subject='Geography',
            options=json.dumps(['Berlin', 'Paris', 'London']),
            answer='Paris',
            level=2,
            article_url='https://example.com/geography',
            type=QuestionType.TEST
        )
        question_2 = Question(
            text='What is the capital of Germany?',
            subject='Geography',
            options=json.dumps(['Berlin', 'Paris', 'London']),
            answer='Berlin',
            level=2,
            article_url='https://example.com/geography',
            type=QuestionType.TEST
        )
        self.session.add_all([question_1, question_2])
        self.session.commit()

        # Make the request with a search string
        with self.app as client:
            response = client.get('/question/', json={"search_string": "Germany", "column_to_order": "text",
                                                      "descending": False})
            result_json = response.get_json()

            # Assertions
            self.assertEqual(response.status_code, 200)
            self.assertEqual(1, len(result_json))
            self.assertEqual(result_json[0]['text'], 'What is the capital of Germany?')

    def test_get_method_without_search(self):
        # Create test Questions
        question_1 = Question(
            text='What is the capital of France?',
            subject='Geography',
            options=json.dumps(['Berlin', 'Paris', 'London']),
            answer='Paris',
            level=2,
            article_url='https://example.com/geography',
            type=QuestionType.TEST
        )
        question_2 = Question(
            text='What is the capital of Germany?',
            subject='Geography',
            options=json.dumps(['Berlin', 'Paris', 'London']),
            answer='Berlin',
            level=2,
            article_url='https://example.com/geography',
            type=QuestionType.TEST
        )
        self.session.add_all([question_1, question_2])
        self.session.commit()

        # Make the request without a search string
        with self.app as client:
            response = client.get('/question/', json={"search_string": "", "column_to_order": "",
                                                      "descending": False})
            result_json = response.get_json()

            # Assertions
            print()
            self.assertEqual(response.status_code, 200)
            self.assertEqual(2, len(result_json))

    def test_post_method(self):
        # Make the request to create a new question
        with self.app as client:
            response = client.post('/question/', json={
                'text': 'What is the capital of Spain?',
                'subject': 'Geography',
                'options': ['Madrid', 'Barcelona', 'Seville'],
                'answer': '0',
                'groups': ['group1'],
                'level': 2,
                'article_url': 'https://example.com/',
                'type': 0
            })

            # Assertions
            self.assertEqual(200, response.status_code)
            result_json = response.get_json()
            self.assertEqual('What is the capital of Spain?', result_json['text'])
            self.assertEqual('Geography', result_json['subject'])


class TestSettingsResource(unittest.TestCase):

    def setUp(self):
        """
        Some pretty weird stuff going on here, but let me explain. I create unique files just so that the singleton
        object is safe and calm. Yeah, I delete the file using os stuff but who cares, right? <3
        """

        default_settings = {
            "time_period": datetime.timedelta(seconds=30),
            "from_time": datetime.time(0),
            "to_time": datetime.time(23, 59),
            "week_days": [d for d in range(7)],
        }
        self.settings_file = str(uuid.uuid4())
        Settings().setup(self.settings_file, default_settings)
        self.client = restful_api.test_client()

    def tearDown(self) -> None:
        """
        What are you looking at? Yes, I delete the file just like that. It's safe, trust me.
        Don't let your trust issues be involved in it. Let them, when I accidentally delete files with all the code.
        """

        os.remove(self.settings_file)

    def test_get_settings(self):
        response = self.client.get('/settings/')

        # Assertions
        default_settings = {
            "time_period": datetime.timedelta(seconds=30).total_seconds(),
            "from_time": datetime.time(0).isoformat(),
            "to_time": datetime.time(23, 59).isoformat(),
            "week_days": [d for d in range(7)],
        }
        self.assertEqual(200, response.status_code)
        self.assertEqual(default_settings, response.json)

    def test_update_settings(self):
        new_settings = {
            'time_period': datetime.timedelta(seconds=3600).total_seconds(),
            'from_time': datetime.time(9, 0).isoformat(),
            'to_time': datetime.time(18, 0).isoformat(),
            'week_days': [1, 2, 3]
        }

        response = self.client.post('/settings/', json=new_settings)

        # Assertions
        self.assertEqual(200, response.status_code)
        self.assertEqual(new_settings, response.json)


if __name__ == '__main__':
    unittest.main()
