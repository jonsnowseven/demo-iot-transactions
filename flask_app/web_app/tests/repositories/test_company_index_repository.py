import json
import os

from unittest import TestCase

from nose.tools import assert_dict_equal, assert_false
from nose.tools import assert_equal

from web_app.clients.elasticsearch import es_repository_for
from web_app.config import config_test
from web_app.models.company_index import CompanyIndex
from web_app.repositories.company_index_repository import CompanyIndexRepositoryES


class TestCompanyIndexRepository(TestCase):
    @classmethod
    def setUpClass(cls):
        connection_meta = config_test["db"]["elasticsearch"]

        cls.repo = es_repository_for(CompanyIndexRepositoryES, connection_meta=connection_meta)

        cls.repo.create_index(n_shards=1, n_replicas=1)

        # Mock Company Indexes
        with open(config_test["mock"]["company_index_sample"], "r") as f:
            company_index_dicts = json.load(f)

        cls.company_indexes = [CompanyIndex.from_dict(d) for d in company_index_dicts]

    @classmethod
    def tearDownClass(cls):
        cls.repo.es_client.delete_index(index=cls.repo.index)
        cls.repo.es_client.close()

    def tearDown(self):
        self.repo.clear_documents()

    def test_insert_company_index(self):
        self.repo.insert(self.company_indexes[0])
        company_indexes = self.repo.get_all()
        expected = self.company_indexes[0]
        result = company_indexes[0]
        assert_dict_equal(expected.to_dict(), result.to_dict())

    def test_get_company(self):
        id = self.repo.insert(self.company_indexes[0])
        company = self.repo.get(id=id)
        assert_dict_equal(company.to_dict(), self.company_indexes[0].to_dict())

    def test_get_all_with_pagination(self):
        self.repo.insert_bulk(self.company_indexes)

        documents, has_prev, has_next = self.repo.get_all_with_pagination(page=1, per_page=5)

        self.assertEqual(len(documents), 5)
        self.assertFalse(has_prev)
        self.assertTrue(has_next)

        documents, has_prev, has_next = self.repo.get_all_with_pagination(page=2, per_page=5)

        self.assertEqual(len(documents), 5)
        self.assertTrue(has_prev)
        self.assertTrue(has_next)

        documents, has_prev, has_next = self.repo.get_all_with_pagination(page=7, per_page=5)

        self.assertEqual(len(documents), 0)
        self.assertTrue(has_prev)

    def test_bulk_insert(self):
        """
        Test we can correctly perform a bulk 'index'
        """
        response = self.repo.insert_bulk(self.company_indexes)
        n_indexed = sum([1 for i in response['items'] if i['index']['created']])
        assert_equal(n_indexed, len(self.company_indexes))

    def test_delete_company_index(self):
        self.repo.insert(self.company_indexes[0])
        self.repo.delete(self.company_indexes[0])
        documents = self.repo.get_all()
        assert_false(documents)

    def test_name_completion_seuggestion(self):
        self.repo.insert_bulk(self.company_indexes)

        companies = self.repo.findNameCompletionSuggestions("Bank")
        self.assertEqual(len(companies), 3)
        names = [c.name for c in companies]
        self.assertListEqual(
            names,
            ['Meston Reid Limited Bank',
             'Johnston Bank Carmichael Wealth Limited',
             'Bank Kirkwood Fyfe Laser Limited']
        )

        companies = self.repo.findNameCompletionSuggestions("xxxxxxx")
        self.assertEqual(len(companies), 0)
        names = [c.name for c in companies]
        self.assertListEqual(names, [])
