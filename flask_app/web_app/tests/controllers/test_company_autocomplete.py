import json
import unittest

from flask import url_for

from web_app import create_app, db
from web_app.clients.elasticsearch import es_repository_for
from web_app.config import config_test

from nose.tools import assert_equal

from web_app.models.company_index import CompanyIndex
from web_app.repositories.company_index_repository import CompanyIndexRepositoryES

from web_app.models.user import User
from web_app.models.role import Role


class TestCompaniesControllerAutoComplete(unittest.TestCase):
    def setUp(self):
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
        self.app_context.pop()
        self.repository.clear_documents()

    @classmethod
    def setup_class(cls):
        connection_meta = config_test["db"]["elasticsearch"]

        cls.repository = es_repository_for(CompanyIndexRepositoryES, connection_meta=connection_meta)

        cls.repository.create_index(n_shards=1, n_replicas=1)

        with open(config_test["mock"]["company_index_sample"], "r") as f:
            company_index_dicts = json.load(f)

        cls.company_indexes = [CompanyIndex.from_dict(d) for d in company_index_dicts]
        cls.repository.insert_bulk(cls.company_indexes)

    @classmethod
    def teardown_class(cls):
        cls.repository.es_client.delete_index(index=cls.repository.index)
        cls.repository.es_client.close()

    def test_search_companies_without_parameter(self):
        """
        GET /companies/search/

        send a get request to search without parameters
        """
        response = self.client.get(url_for('companies.search_companies'), headers=self.auth_header)
        assert_equal(response.status_code, 422)

    def test_search_companies_with_success(self):
        """
        GET /companies/search/

        send a get request to search without parameters
        """
        response = self.client.get(url_for('companies.search_companies'), query_string={"name": "Bank"}, headers=self.auth_header)
        data = json.loads(response.get_data(as_text=True))

        assert_equal(response.status_code, 200)
        assert_equal(data['count'], 3)

        target = [
            {
                'id': 27,
                'location': 'http://localhost/companies/27',
                'name': 'Meston Reid Limited Bank'
            },
             {
                'id': 0,
                'location': 'http://localhost/companies/0',
                'name': 'Johnston Bank Carmichael Wealth Limited'
             },
             {
                'id': 29,
                'location': 'http://localhost/companies/29',
                'name': 'Bank Kirkwood Fyfe Laser Limited'
             }
        ]

        self.assertListEqual(data['companies_suggestions'], target)
