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


class TestDocumentController(unittest.TestCase):

    def setUp(self):
        self.repository.insert_bulk(self.documents)
        self.app = create_app('testing')
        self.app_context = self.app.test_request_context()
        self.app_context.push()
        self.client = self.app.test_client()

        db.create_all()

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

    def test_get_document(self):
        """
        GET /documents/id
        """
        id = self.repository.insert(document=self.documents[0])

        response = self.client.get(url_for('documents.get_document', id=id), headers=self.auth_header)

        data = json.loads(response.get_data(as_text=True))
        self.assertDictEqual(data, self.documents[0].to_dict())

    def test_update_document(self):
        """
        PUT /documents/id
        """
        id = self.repository.insert(document=self.documents[0])

        for node, data in self.documents[0].traverse():
            data['text'] = ''

        serialized = json.dumps(self.documents[0].to_dict())

        response = self.client.put(
            url_for('documents.update_document', id=id),
            data=serialized,
            headers=dict({'content-type': 'application/json'}, **self.auth_header))

        self.assertEqual(response.status_code, 204)

        response = self.client.get(url_for('documents.get_document', id=id), headers=self.auth_header)
        data = json.loads(response.get_data(as_text=True))

        self.assertDictEqual(self.documents[0].to_dict(), data)

    def test_delete_document(self):
        """
        DELETE /documents/id
        """
        id = self.repository.insert(document=self.documents[0])

        response = self.client.get(url_for('documents.get_document', id=id), headers=self.auth_header)
        self.assertEqual(response.status_code, 200)

        response = self.client.delete(url_for('documents.delete_document', id=id), headers=self.auth_header)
        self.assertEqual(response.status_code, 204)

        response = self.client.get(url_for('documents.get_document', id=id), headers=self.auth_header)
        self.assertEqual(response.status_code, 404)

    def test_post_invalid_json(self):
        """
        POST /documents/

        post a request with an invalid json
        """
        serialized = "NOT A VALID JSON"

        response = self.client.post(
            url_for('documents.new_document'),
            data=serialized,
            headers=dict({'content-type': 'application/json'}, **self.auth_header))

        self.assertEqual(response.status_code, 400)

    def test_post_valid_json(self):
        """
        POST /documents/
        """
        new_record = self.documents[-1].to_dict()
        serialized = json.dumps(new_record)

        response = self.client.post(
            url_for('documents.new_document'),
            data=serialized,
            headers=dict({'content-type': 'application/json'}, **self.auth_header))

        data = json.loads(response.get_data(as_text=True))

        self.assertIn('/documents/', response.headers['location'])
        self.assertEqual(response.status_code, 201)
        self.assertEqual(new_record, data)

    def test_get_all_documents(self):
        """
        GET /documents/
        """
        response = self.client.get(url_for('documents.get_documents'), headers=self.auth_header)
        data = json.loads(response.get_data(as_text=True))

        self.assertEqual(response.status_code, 200)
        self.assertEqual(data['count'], self.app.config['RESULTS_PER_PAGE'])
        self.assertEqual(len(data['documents']), self.app.config['RESULTS_PER_PAGE'])
        self.assertEqual(data['documents'][0]['_score'], 1.0)
        self.assertEqual(data['page'], 1)
        self.assertEqual(data['prev'], None)
        self.assertIn('documents/?page=2', data['next'])

        response = self.client.get(url_for('documents.get_documents'), query_string={"page": len(self.documents)}, headers=self.auth_header)
        data = json.loads(response.get_data(as_text=True))

        self.assertEqual(response.status_code, 200)
        self.assertEqual(data['count'], 0)
        self.assertEqual(len(data['documents']), 0)
        self.assertEqual(data['page'], len(self.documents))
        self.assertEqual(data['prev'], None)
        self.assertEqual(data['next'], None)

    def test_search_documents_missing_required_field(self):
        """
        GET /documents/search?text=TEXT
        """
        response = self.client.get(url_for('documents.search_documents'), query_string={}, headers=self.auth_header)

        self.assertEqual(response.status_code, 422)

    def test_search_documents_missing_required_field_02(self):
        """
        GET /documents/search?text=TEXT
        """
        parms = {"document_level": 1}

        response = self.client.get(url_for('documents.search_documents'), query_string=parms, headers=self.auth_header)

        self.assertEqual(response.status_code, 422)

    def test_search_documents_violating_exclusive_or_condition(self):
        """
        GET /documents/search?text=TEXT
        """

        parms = {
            "document_level": 1,
            "text": "First evidence to be found",
            "name": "directive"
        }

        response = self.client.get(url_for('documents.search_documents'), query_string=parms, headers=self.auth_header)
        self.assertEqual(response.status_code, 422)

    def test_search_documents(self):
        """
        GET /documents/search?text=TEXT
        """

        parms = {
            "document_level": 1,
            "text": "First evidence to be found"
        }

        response = self.client.get(url_for('documents.search_documents'), query_string=parms, headers=self.auth_header)
        data = json.loads(response.get_data(as_text=True))

        self.assertEqual(response.status_code, 200)
        self.assertEqual(data['count'], 1)
        self.assertNotEqual(data['documents'][0]['_score'], 1.0)
        self.assertEqual(len(data['documents']), 1)
        self.assertEqual(data['page'], 1)
        self.assertEqual(data['prev'], None)
        self.assertEqual(data['next'], None)
