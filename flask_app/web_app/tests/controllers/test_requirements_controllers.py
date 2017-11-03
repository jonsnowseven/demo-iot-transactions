import json
import logging
import unittest

from flask import url_for

from web_app import create_app, db
from web_app.clients.elasticsearch import es_repository_for
from web_app.config import config_test
from web_app.models.document import Document
from web_app.repositories.document_repository import DocumentRepositoryES

from web_app.models.user import User
from web_app.models.role import Role


class TestRequirementController(unittest.TestCase):

    def setUp(self):
        self.app = create_app('testing')
        self.app_context = self.app.test_request_context()
        self.app_context.push()
        self.client = self.app.test_client()

        user = User(
            username='john',
            password='catz'
        )

        db.session.add(user)

        login_data = json.dumps({'username': 'john', 'password': 'catz'})
        response = self.client.post('/auth', data=login_data, headers={'content-type':'application/json'})

        body = json.loads(response.data.decode('utf-8'))
        auth_token = body['access_token']
        self.auth_header = {'Authorization': 'JWT {}'.format(auth_token)}

    def tearDown(self):
        db.session.remove()
        db.drop_all()
        self.repository.clear_documents()
        self.app_context.pop()

    @classmethod
    def setUpClass(cls):
        connection_meta = config_test["db"]["elasticsearch"]

        cls.repository = es_repository_for(DocumentRepositoryES, connection_meta=connection_meta)
        cls.repository.create_index(n_shards=1, n_replicas=1)

        json_data = json.loads(open(config_test["mock"]["documents_sample"], "r").read())
        cls.documents = [Document.from_dict(d) for d in json_data]

    @classmethod
    def tearDownClass(cls):
        cls.repository.es_client.delete_index(index=cls.repository.index)
        cls.repository.es_client.close()

    def test_get_requirement(self):
        """
        GET /requirements/
        """
        _ = self.repository.insert(document=self.documents[0])

        requirement = next(d for n, d in self.documents[0].traverse() if d['level'] == 6)
        req_id = requirement['id'].replace('/', '_')

        response = self.client.get(url_for('requirements.get_requirement', id=req_id), headers=self.auth_header)

        self.assertEqual(response.status_code, 200)

        data = json.loads(response.get_data(as_text=True))
        self.assertDictEqual(data['_source'], requirement)

    def test_update_requirement(self):
        """
        PUT /requirements/id
        """
        id = self.repository.insert(document=self.documents[0])

        requirement = next(d for n, d in self.documents[0].traverse() if d['level'] == 6)

        req_id = requirement['id'].replace('/', '_')

        requirement['text'] = 'NEW TEXT'
        requirement['meta'] = 'NEW META'

        serialized = json.dumps(requirement)

        response = self.client.put(
            url_for('requirements.update_requirement', id=req_id),
            data=serialized,
            headers=dict({'content-type': 'application/json'}, **self.auth_header))

        self.assertEqual(response.status_code, 204)

        response = self.client.get(url_for('requirements.get_requirement', id=req_id), headers=self.auth_header)

        data = json.loads(response.get_data(as_text=True))

        self.assertDictEqual(requirement, data['_source'])

    def test_get_all_documents(self):
        """
        GET /requirements/
        """
        self.repository.insert_bulk(self.documents)

        response = self.client.get(url_for('requirements.get_requirements'), headers=self.auth_header)
        data = json.loads(response.get_data(as_text=True))

        self.assertEqual(response.status_code, 200)
        self.assertEqual(data['number_documents'], self.app.config['RESULTS_PER_PAGE'])
        self.assertEqual(len(data['requirements_by_document']), self.app.config['RESULTS_PER_PAGE'])
        self.assertEqual(data['page'], 1)
        self.assertEqual(data['prev'], None)
        self.assertIn('requirements/?page=2', data['next'])

        response = self.client.get(url_for('requirements.get_requirements'), query_string={"page": len(self.documents)}, headers=self.auth_header)
        data = json.loads(response.get_data(as_text=True))

        self.assertEqual(response.status_code, 200)
        self.assertEqual(data['number_documents'], 0)
        self.assertEqual(data['number_requirements'], 0)
        self.assertEqual(len(data['requirements_by_document']), 0)
        self.assertEqual(data['page'], len(self.documents))
        self.assertEqual(data['prev'], None)
        self.assertEqual(data['next'], None)

    def test_search_requirements_missing_required_field(self):
        """
        GET /requirements/search?text=TEXT
        """
        response = self.client.get(url_for('requirements.search_requirements'), query_string={}, headers=self.auth_header)

        self.assertEqual(response.status_code, 422)

    def test_search_requirements_missing_required_field_02(self):
        """
        GET /requirements/search?text=TEXT
        """
        parms = {"document_level": 1}

        response = self.client.get(url_for('requirements.search_requirements'), query_string=parms, headers=self.auth_header)

        self.assertEqual(response.status_code, 422)

    def test_search_requirements(self):
        """
        GET /requirements/search?text=TEXT
        """
        self.repository.insert_bulk(self.documents)

        parms = {
            "document_level": 1,
            "text": "First evidence to be found"
        }

        response = self.client.get(url_for('requirements.search_requirements'), query_string=parms, headers=self.auth_header)
        data = json.loads(response.get_data(as_text=True))

        self.assertEqual(response.status_code, 200)
        self.assertEqual(data['number_documents'], 1)
        self.assertEqual(data['number_requirements'], 1)
        self.assertEqual(len(data['requirements_by_document']), 1)
        self.assertEqual(data['page'], 1)
        self.assertEqual(data['prev'], None)
        self.assertEqual(data['next'], None)

    def test_search_requirements_02(self):
        """
        GET /requirements/search?text=TEXT
        """
        self.repository.insert_bulk(self.documents)

        parms = {
            "industry": "pharmacy",
            "text": "First evidence to be found"
        }

        response = self.client.get(url_for('requirements.search_requirements'), query_string=parms, headers=self.auth_header)
        data = json.loads(response.get_data(as_text=True))

        self.assertEqual(response.status_code, 200)
        self.assertEqual(data['number_documents'], 1)
        self.assertEqual(data['number_requirements'], 2)
        self.assertEqual(len(data['requirements_by_document']), 1)
        self.assertEqual(data['page'], 1)
        self.assertEqual(data['prev'], None)
        self.assertEqual(data['next'], None)

