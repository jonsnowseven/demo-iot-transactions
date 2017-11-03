import json
import pandas as pd

from flask import url_for
from nose.tools import assert_in
from unittest import TestCase

from web_app import create_app, db
from web_app.clients.elasticsearch import es_repository_for
from web_app.clients.postgresql import psql_repository_for
from web_app.config import config_test

from nose.tools import assert_dict_equal
from nose.tools import assert_not_in, assert_list_equal, assert_equal, raises

from web_app.models.company import Company
from web_app.models.document import Document

from web_app.models.user import User
from web_app.models.role import Role

from web_app.repositories.company_repository import CompanyRepositoryPSQL
from web_app.repositories.document_repository import DocumentRepositoryES


class TestCompaniesControllers(TestCase):

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

    @classmethod
    def setUpClass(cls):

        #  Setup some mock companies
        df_mock_companies = pd.read_json(config_test['mock']['companies-sample'], orient='records')
        df_mock_companies = df_mock_companies.where((pd.notnull(df_mock_companies)), None)

        cls.companies = [
            Company.from_json(row.to_dict())
            for (index, row) in df_mock_companies.iterrows()
        ]

        cls.repository = psql_repository_for(CompanyRepositoryPSQL, connection_meta=config_test['db']['postgresql'])

        cls.repository.drop_table()
        cls.repository.create_table()

        for company in cls.companies:
            company.id = cls.repository.insert(company)

        cls.repository.commit()

        #  Setup some mock documents
        connection_meta = config_test["db"]["elasticsearch"]

        cls.repo_doc = es_repository_for(DocumentRepositoryES, connection_meta=connection_meta)
        cls.repo_doc.create_index(n_shards=1, n_replicas=1)

        json_data = json.loads(open(config_test["mock"]["documents_sample"], "r").read())
        cls.documents = [Document.from_dict(d) for d in json_data]
        cls.repo_doc.insert_bulk(cls.documents)

    @classmethod
    def tearDownClass(cls):
        cls.repository.clear_table()
        cls.repository.commit()
        cls.repo_doc.es_client.delete_index(index=cls.repo_doc.index)
        cls.repo_doc.es_client.close()

    def test_get_all_companies(self):
        """
        GET /companies/
        """
        response = self.client.get(url_for('companies.get_companies'), headers=self.auth_header)
        data = json.loads(response.get_data(as_text=True))

        assert_equal(response.status_code, 200)
        assert_equal(data['count'], self.app.config['RESULTS_PER_PAGE'])
        assert_equal(len(data['companies']), self.app.config['RESULTS_PER_PAGE'])
        assert_equal(data['page'], 1)
        assert_equal(data['prev'], None)
        assert_in('companies/?page=2', data['next'])

    def test_get_company_01(self):
        """
        GET /companies/id
        """
        response = self.client.get(url_for('companies.get_company', id=1), headers=self.auth_header)
        data = json.loads(response.get_data(as_text=True))

        assert_equal(response.status_code, 200)
        assert_equal(data['id'], 1)

    @raises(ValueError)
    def test_get_company_02(self):
        """
        GET /companies/id
        """
        response = self.client.get(url_for('companies.get_company', id='o'), headers=self.auth_header)

    def test_get_company_03(self):
        """
        GET /companies/id
        """
        response = self.client.get(url_for('companies.get_company', id=10000), headers=self.auth_header)
        assert_equal(response.status_code, 404)

    def test_post_company_invalid_content_type(self):
        """
        POST /companies/

        post a request with an invalid 'content-type'
        """
        new_record = self.companies[-1]
        serialized = json.dumps(new_record.to_json())

        headers = dict({'content-type': 'application/xml'}, **self.auth_header)

        response = self.client.post(url_for('companies.new_company'), data=serialized, headers=headers)
        assert_equal(response.status_code, 400)

    def test_post_company_not_valid_json(self):
        """
        POST /companies/

        post a request with an invalid json
        """
        serialized = "NOT A VALID JSON"
        headers = dict({'content-type': 'application/json'}, **self.auth_header)
        response = self.client.post(url_for('companies.new_company'), data=serialized, headers=headers)
        assert_equal(response.status_code, 400)

    def test_post_company_valid_json_with_invalid_data(self):
        """
        POST /companies/

        post a request with a syntactically valid JSON but failing in the model validator
        """
        serialized = json.dumps({})
        headers = dict({'content-type': 'application/json'}, **self.auth_header)
        response = self.client.post(url_for('companies.new_company'), data=serialized, headers=headers)
        assert_equal(response.status_code, 405)

    def test_post_company_valid_json(self):
        """
        POST /companies/

        post a correct request
        """
        new_record = self.companies[-1].to_json()
        serialized = json.dumps(new_record)

        headers = dict({'content-type': 'application/json'}, **self.auth_header)

        response = self.client.post(url_for('companies.new_company'), data=serialized, headers=headers)

        data = json.loads(response.get_data(as_text=True))

        new_record['id'] = data['id']

        assert_in('/companies/' + str(data['id']), response.headers['location'])
        assert_equal(response.status_code, 201)
        assert_dict_equal(new_record, data)

    def test_update_company_valid_json(self):
        """
        PUT /companies/

        update a record by sending a well formed request
        """
        response = self.client.get(url_for('companies.get_company', id=10), headers=self.auth_header)
        data = json.loads(response.get_data(as_text=True))
        data['name'] = 'UPDATED NAME'

        headers = dict({'content-type': 'application/json'}, **self.auth_header)
        serialized = json.dumps(data)

        response = self.client.put(url_for('companies.update_company', id=10), data=serialized, headers=headers)

        assert_equal(response.status_code, 204)

        response = self.client.get(url_for('companies.get_company', id=10), headers=self.auth_header)
        data = json.loads(response.get_data(as_text=True))

        assert_equal(data['name'], 'UPDATED NAME')

    def test_delete_company(self):
        """
        DELETE /companies/id

        send a delete request to eliminate a record for the given 'id'
        """
        new_record = self.companies[-1]
        serialized = json.dumps(new_record.to_json())
        headers = dict({'content-type': 'application/json'}, **self.auth_header)
        response = self.client.post(url_for('companies.new_company'), data=serialized, headers=headers)
        data = json.loads(response.get_data(as_text=True))

        response = self.client.delete(url_for('companies.delete_company', id=data['id']), headers=self.auth_header)

        assert_equal(response.status_code, 204)

    def test_delete_company_unknown_id(self):
        """
        DELETE /companies/id

        send a delete request to eliminate a record for a non existing 'id'
        """
        response = self.client.delete(url_for('companies.delete_company', id=100000), headers=self.auth_header)
        assert_equal(response.status_code, 204)

    def test_companies_requirements_matching_process_non_existent_id(self):
        """
        GET /companies/id/requirements (Unknown ID)
        """
        response = self.client.get(url_for('companies.get_company_requirements', id=100000), headers=self.auth_header)
        assert_equal(response.status_code, 404)

    def test_companies_requirements_matching_process_01(self):
        """
        GET /companies/id/requirements (Known ID)
        """

        response = self.client.get(url_for('companies.get_company_requirements', id=self.companies[1].id), headers=self.auth_header)
        assert_equal(response.status_code, 200)
        data = json.loads(response.get_data(as_text=True))
        self.assertEqual(data['number_documents'], 2)

        response = self.client.get(url_for('companies.get_company_requirements', id=self.companies[3].id), headers=self.auth_header)
        assert_equal(response.status_code, 200)
        data = json.loads(response.get_data(as_text=True))
        self.assertEqual(data['number_documents'], 2)

        response = self.client.get(url_for('companies.get_company_requirements', id=self.companies[3].id), headers=self.auth_header)
        assert_equal(response.status_code, 200)
        data = json.loads(response.get_data(as_text=True))
        self.assertEqual(data['number_documents'], 2)

    def test_companies_requirements_matching_process_02(self):
        """
        GET /companies/id/requirements (Known ID) 02
        """

        response = self.client.get(url_for('companies.get_company_requirements', id=self.companies[2].id), headers=self.auth_header)
        assert_equal(response.status_code, 200)
        data = json.loads(response.get_data(as_text=True))
        self.assertEqual(data['number_documents'], 3)

        response = self.client.get(url_for('companies.get_company_requirements', id=self.companies[9].id), headers=self.auth_header)
        assert_equal(response.status_code, 200)
        data = json.loads(response.get_data(as_text=True))
        self.assertEqual(data['number_documents'], 3)




