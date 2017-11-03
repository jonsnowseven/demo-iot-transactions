import unittest

from flask import json
from flask import url_for

from web_app import create_app, db
from web_app.models.user import User
from web_app.models.role import Role


class UserModelTestCase(unittest.TestCase):
    def setUp(self):
        self.app = create_app('testing')
        self.app_context = self.app.test_request_context()
        self.app_context.push()
        self.client = self.app.test_client()
        self.secured_endpoint = 'companies.secured'
        db.create_all()

    def tearDown(self):
        db.session.remove()
        db.drop_all()
        self.app_context.pop()

    def test_jwt_token_locks_secured_endpoint(self):
        """If no known user is detected, the app should return a 401 Unauthorized"""
        response = self.client.get(url_for(self.secured_endpoint))
        self.assertEqual(response.status_code, 401)

    def test_jwt_authenticates_known_user(self):
        """If a user is known, a token should be allowed and the request granted"""
        user = User(
            username='john',
            password='catz'
        )
        db.session.add(user)
        login_data = json.dumps({'username': user.username, 'password': 'catz'})
        response = self.client.post('/auth', data=login_data, headers={'content-type': 'application/json'})
        self.assertEqual(response.status_code, 200)

    def test_jwt_refuses_unknown_user(self):
        login_data = json.dumps({'username': 'UNKNOWN USER', 'password': 'UNKNOWN'})
        response = self.client.post('/auth', data=login_data, headers={'content-type': 'application/json'})
        self.assertEqual(response.status_code, 401)

    def test_jwt_allows_authorized_user_secured_endpoint(self):
        """If the user is authenticated, he should be allowed access to secured endpoints"""
        user = User(
            username='john',
            password='catz'
        )
        db.session.add(user)
        login_data = json.dumps({'username': user.username, 'password': 'catz'})
        response = self.client.post('/auth', data=login_data, headers={'content-type':'application/json'})

        body = json.loads(response.data)
        auth_token = body['access_token']
        headers = {'Authorization': 'JWT {}'.format(auth_token)}

        response = self.client.get(url_for(self.secured_endpoint), headers=headers)
        self.assertEqual(response.status_code, 200)

