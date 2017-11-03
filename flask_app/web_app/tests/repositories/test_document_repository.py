import json
import logging
from unittest import TestCase

from nose.tools import assert_dict_equal, assert_in
from nose.tools import assert_equal

from web_app.clients.elasticsearch import es_repository_for
from web_app.config import config_test
from web_app.models.document import Document
from web_app.repositories.document_repository import DocumentRepositoryES


class TestDocumentRepository(TestCase):
    @classmethod
    def setUpClass(cls):
        connection_meta = config_test["db"]["elasticsearch"]

        cls.repo = es_repository_for(DocumentRepositoryES, connection_meta=connection_meta)

        cls.repo.create_index(n_shards=1, n_replicas=1)

        json_data = json.loads(open(config_test["mock"]["documents_sample"], "r").read())

        cls.documents = [Document.from_dict(d) for d in json_data]

    @classmethod
    def tearDownClass(cls):
        cls.repo.es_client.delete_index(index=cls.repo.index)
        cls.repo.es_client.close()

    def tearDown(self):
        self.repo.clear_documents()

    def test_create_index(self):
        assert_in(self.repo.index, self.repo.es_client.get_all_indexes())

    def test_insert_document(self):
        id = self.repo.insert(self.documents[0])
        document = self.repo.get(id=id)
        assert_dict_equal(document, self.documents[0].to_dict())

    def test_bulk_insert(self):
        """
        Test we can correctly perform a bulk 'index'
        """
        ids = self.repo.insert_bulk(self.documents)
        n_indexed = len(ids)
        assert_equal(n_indexed, len(self.documents))

    def test_get_document(self):
        """
        Test we can retrieve all documents (ES imposes a limit on the number of documents returned)
        """
        id = self.repo.insert(self.documents[0])
        document = self.repo.get(id=id)
        assert_dict_equal(document, self.documents[0].to_dict())

    def test_get_all_documents(self):
        """
        Test we can retrieve all documents (ES imposes a limit on the number of documents returned)
        """
        self.repo.insert_bulk(self.documents)
        documents = self.repo.get_all()
        assert_equal(len(documents), min(len(self.documents), 10))

    def test_get_all_documents_with_pagination(self):
        """
        Test we can retrieve all documents with pagination
        """
        self.repo.insert_bulk(self.documents)

        documents, has_prev, has_next = self.repo.get_all_with_pagination(page=1, per_page=5)

        self.assertEqual(len(documents), 5)
        self.assertFalse(has_prev)
        self.assertTrue(has_next)

        documents, has_prev, has_next = self.repo.get_all_with_pagination(page=2, per_page=5)

        self.assertEqual(len(documents), 5)
        self.assertTrue(has_prev)
        self.assertTrue(has_next)

        documents, has_prev, has_next = self.repo.get_all_with_pagination(page=3, per_page=5)

        self.assertEqual(len(documents), 2)
        self.assertTrue(has_prev)
        self.assertFalse(has_next)

    def test_get_all_documents_filter_by_document_level(self):
        self.repo.insert_bulk(self.documents)

        filters = {'document_level': 1}
        documents, _, _ = self.repo.get_all_with_pagination(page=1, per_page=10, **filters)
        self.assertEqual(len(documents), 4)

        filters = {'document_level': 2}
        documents, _, _ = self.repo.get_all_with_pagination(page=1, per_page=10, **filters)
        self.assertEqual(len(documents), 10)

    def test_get_all_documents_filter_by_industry(self):
        self.repo.insert_bulk(self.documents)

        filters = {'industry': 'pharmacy'}
        documents, _, _ = self.repo.get_all_with_pagination(page=1, per_page=10, **filters)
        self.assertEqual(len(documents), 2)

    def test_get_all_documents_filter_by_label(self):
        self.repo.insert_bulk(self.documents)

        filters = {'label': 'label 01'}
        documents, _, _ = self.repo.get_all_with_pagination(page=1, per_page=10, **filters)
        self.assertEqual(len(documents), 1)

    def test_get_all_documents_filter_by_workflow_theme(self):
        self.repo.insert_bulk(self.documents)

        filters = {'workflow_theme': 'workflow_theme 01'}
        documents, _, _ = self.repo.get_all_with_pagination(page=1, per_page=10, **filters)
        self.assertEqual(len(documents), 1)

    def test_get_all_documents_filter_by_tags(self):
        self.repo.insert_bulk(self.documents)

        filters = {'tags': ['TAG 01', 'TAG 02']}
        documents, _, _ = self.repo.get_all_with_pagination(page=1, per_page=10, **filters)
        self.assertEqual(len(documents), 4)

    def test_get_all_documents_filter_by_requirement_id(self):
        self.repo.insert_bulk(self.documents)

        filters = {'id': 'commission-delegated-regulation-eu-2017-104/part-ix/article-100'}
        documents, _, _ = self.repo.get_all_with_pagination(page=1, per_page=10, **filters)
        self.assertEqual(len(documents), 1)

    def test_get_all_documents_filter_by_tags_and_document_level(self):
        self.repo.insert_bulk(self.documents)

        filters = {
            'tags': ['TAG 01', 'TAG 02'],
            'document_level': 3
        }
        documents, _, _ = self.repo.get_all_with_pagination(page=1, per_page=10, **filters)
        self.assertEqual(len(documents), 0)

        filters = {
            'tags': ['TAG 01', 'TAG 02'],
            'document_level': 1
        }
        documents, _, _ = self.repo.get_all_with_pagination(page=1, per_page=10, **filters)
        self.assertEqual(len(documents), 1)

    def test_get_documents_by_external_requirement_id_they_are_refering_to(self):
        self.repo.insert_bulk(self.documents)

        filters = {'references.*.external_ref_id': 'commission-delegated-regulation-eu-2017-180/paragraph-1001'}
        requirements, _, _ = self.repo.get_all_with_pagination(page=1, per_page=10, **filters)
        self.assertEqual(len(requirements), 1)

        filters = {'references.*.external_ref_id': 'path/paragraph-does-not-exist'}
        requirements, _, _ = self.repo.get_all_with_pagination(page=1, per_page=10, **filters)
        self.assertEqual(len(requirements), 0)

    def test_search_documents_by_text(self):
        self.repo.insert_bulk(self.documents)

        text = "First evidence to be found"

        documents, _, _ = self.repo.findByText(page=1, per_page=10, text=text)
        self.assertEqual(len(documents), 2)

    def test_serch_documents_by_text_restricted_by_filter(self):
        self.repo.insert_bulk(self.documents)

        text = "First evidence to be found"
        filters = {'document_level': 1}

        documents, _, _ = self.repo.findByText(page=1, per_page=10, text=text, **filters)
        self.assertEqual(len(documents), 1)

    def test_serch_documents_by_name_01(self):
        self.repo.insert_bulk(self.documents)

        name = "BROWN FOX"

        documents, _, _ = self.repo.findByName(page=1, per_page=10, name=name)

        self.assertEqual(len(documents), 2)

    def test_serch_documents_by_name_filters(self):
        self.repo.insert_bulk(self.documents)

        name = "BROWN FOX"
        filters = {'has_text': 100}

        documents, _, _ = self.repo.findByName(page=1, per_page=10, name=name, **filters)

        self.assertEqual(len(documents), 1)

    def test_serch_documents_by_name_02(self):
        self.repo.insert_bulk(self.documents)

        name = "white rabit"

        documents, _, _ = self.repo.findByName(page=1, per_page=10, name=name)

        self.assertEqual(len(documents), 1)

    def test_serch_documents_by_name_03(self):
        self.repo.insert_bulk(self.documents)

        name = "wrong turn"

        documents, _, _ = self.repo.findByName(page=1, per_page=10, name=name)

        self.assertEqual(len(documents), 1)

    def test_serch_documents_by_name(self):
        self.repo.insert_bulk(self.documents)

        name = "THE BROWN FOX"

        documents, _, _ = self.repo.findByName(page=1, per_page=10, name=name)

        self.assertEqual(len(documents), 2)

    def test_delete_document(self):
        id = self.repo.insert(self.documents[0])
        self.repo.delete(id)
        documents, _, _ = self.repo.get_all_with_pagination(page=1, per_page=10)
        self.assertEqual(len(documents), 0)

    def test_update_document(self):
        id = self.repo.insert(self.documents[0])

        for node, data in self.documents[0].traverse():
            data['text'] = ''

        self.repo.update(id=id, document=self.documents[0])

        document = self.repo.get(id)

        self.assertDictEqual(document, self.documents[0].to_dict())



