import json
from unittest import TestCase

from web_app.clients.elasticsearch import es_repository_for
from web_app.config import config_test
from web_app.models.document import Document
from web_app.models.document_utils import flatten
from web_app.repositories.document_repository import DocumentRepositoryES
from web_app.repositories.requirements_repository import RequirementRepositoryES


class TestDocumentRepository(TestCase):
    @classmethod
    def setUpClass(cls):
        connection_meta = config_test["db"]["elasticsearch"]

        cls.repo_doc = es_repository_for(DocumentRepositoryES, connection_meta=connection_meta)
        cls.repo_req = es_repository_for(RequirementRepositoryES, connection_meta=connection_meta)

        cls.repo_doc.create_index(n_shards=1, n_replicas=1)

        json_data = json.loads(open(config_test["mock"]["documents_sample"], "r").read())

        cls.documents = [Document.from_dict(d) for d in json_data]

        cls.flat_requirements = lambda x: flatten([req['requirements'] for req in x])

    @classmethod
    def tearDownClass(cls):
        cls.repo_doc.es_client.delete_index(index=cls.repo_doc.index)
        cls.repo_doc.es_client.close()

    def tearDown(self):
        self.repo_doc.clear_documents()

    def test_get_requirement(self):
        """
        Test that we can get the requirement (node) with 'path_id' = id
        """
        self.repo_doc.insert_bulk(self.documents)

        node, data = next(self.documents[0].traverse())

        requirement = self.repo_req.get(id=data['id'])

        self.assertDictEqual(requirement['_source'], data)

    def test_get_all_requirements(self):
        """
        Test we can retrieve all requirements (ES imposes a limit on the number of documents returned)
        """
        self.repo_doc.insert_bulk(self.documents)

        requirements = self.repo_req.get_all()

        self.assertEqual(len(flatten([x["_source"] for x in requirements])), 20)

        for req in requirements:
            self.assertIn("_id", req)
            self.assertNotIn("document_name", req)
            self.assertNotIn("predecessors", req)

    def test_get_all_requirements_with_pagination(self):
        """
        Test we can retrieve all requirements with pagination
        NOTE: the pagination is currently being done by document since the nodes are nested objects
        inside the document we are ingesting
        """
        self.repo_doc.insert_bulk(self.documents)

        requirements, has_prev, has_next = self.repo_req.get_all_with_pagination(page=1, per_page=5)

        self.assertEqual(len(flatten([x["_source"] for x in requirements])), 10)
        self.assertFalse(has_prev)
        self.assertTrue(has_next)

        requirements, has_prev, has_next = self.repo_req.get_all_with_pagination(page=2, per_page=5)

        self.assertEqual(len(flatten([x["_source"] for x in requirements])), 10)
        self.assertTrue(has_prev)
        self.assertTrue(has_next)

        requirements, has_prev, has_next = self.repo_req.get_all_with_pagination(page=3, per_page=5)

        self.assertEqual(len(flatten([x["_source"] for x in requirements])), 4)
        self.assertTrue(has_prev)
        self.assertFalse(has_next)

    def test_get_all_requirements_filter_by_document_level(self):
        self.repo_doc.insert_bulk(self.documents)

        filters = {'document_level': 1}
        requirements, _, _ = self.repo_req.get_all_with_pagination(page=1, per_page=100, **filters)
        self.assertEqual(len(flatten([x["_source"] for x in requirements])), 5)

        filters = {'document_level': 2}
        requirements, _, _ = self.repo_req.get_all_with_pagination(page=1, per_page=100, **filters)
        self.assertEqual(len(flatten([x["_source"] for x in requirements])), 15)

    def test_get_all_requirements_filter_by_industry(self):
        self.repo_doc.insert_bulk(self.documents)

        filters = {'industry': 'pharmacy'}
        requirements, _, _ = self.repo_req.get_all_with_pagination(page=1, per_page=10, **filters)
        self.assertEqual(len(flatten([x["_source"] for x in requirements])), 3)

    def test_get_all_requirements_filter_by_label(self):
        self.repo_doc.insert_bulk(self.documents)

        filters = {'label': 'label 01'}
        requirements, _, _ = self.repo_req.get_all_with_pagination(page=1, per_page=10, **filters)
        self.assertEqual(len(flatten([x["_source"] for x in requirements])), 2)

    def test_get_all_requirements_filter_by_workflow_theme(self):
        self.repo_doc.insert_bulk(self.documents)

        filters = {'workflow_theme': 'workflow_theme 01'}
        requirements, _, _ = self.repo_req.get_all_with_pagination(page=1, per_page=10, **filters)
        self.assertEqual(len(flatten([x["_source"] for x in requirements])), 1)

    def test_get_all_requirements_filter_by_tags(self):
        self.repo_doc.insert_bulk(self.documents)

        filters = {'tags': ['TAG 01', 'TAG 02']}
        requirements, _, _ = self.repo_req.get_all_with_pagination(page=1, per_page=10, **filters)
        self.assertEqual(len(flatten([x["_source"] for x in requirements])), 5)

    def test_get_all_requirements_filter_by_tags_and_document_level(self):
        self.repo_doc.insert_bulk(self.documents)

        filters = {
            'tags': ['TAG 01', 'TAG 02'],
            'document_level': 3
        }
        requirements, _, _ = self.repo_req.get_all_with_pagination(page=1, per_page=10, **filters)
        self.assertEqual(len(flatten([x["_source"] for x in requirements])), 0)

        filters = {
            'tags': ['TAG 01', 'TAG 02'],
            'document_level': 1
        }
        requirements, _, _ = self.repo_req.get_all_with_pagination(page=1, per_page=10, **filters)
        self.assertEqual(len(flatten([x["_source"] for x in requirements])), 1)

    def test_get_documents_by_external_requirement_id_they_are_refering_to(self):
        self.repo_doc.insert_bulk(self.documents)

        filters = {'references.*.external_ref_id': 'commission-delegated-regulation-eu-2017-180/paragraph-1001'}
        requirements, _, _ = self.repo_req.get_all_with_pagination(page=1, per_page=10, **filters)
        self.assertEqual(len(flatten([x["_source"] for x in requirements])), 2)

        filters = {'references.*.external_ref_id': 'path/paragraph-does-not-exist'}
        requirements, _, _ = self.repo_req.get_all_with_pagination(page=1, per_page=10, **filters)
        self.assertEqual(len(flatten([x["_source"] for x in requirements])), 0)

    def test_search_requirements_by_text(self):
        self.repo_doc.insert_bulk(self.documents)

        text = "First evidence to be found"

        requirements, _, _ = self.repo_req.findByText(page=1, per_page=10, text=text)
        self.assertEqual(len(flatten([x["_source"] for x in requirements])), 3)

    def test_serch_requirements_by_text_restricted_by_filter(self):
        self.repo_doc.insert_bulk(self.documents)

        text = "First evidence to be found"
        filters = {'industry': 'pharmacy'}

        requirements, _, _ = self.repo_req.findByText(page=1, per_page=10, text=text, **filters)
        self.assertEqual(len(flatten([x["_source"] for x in requirements])), 2)

    def test_serch_requirements_by_text_restricted_by_filter_02(self):
        self.repo_doc.insert_bulk(self.documents)

        text = "First evidence to be found"
        filters = {'document_level': 1}

        requirements, _, _ = self.repo_req.findByText(page=1, per_page=10, text=text, **filters)
        self.assertEqual(len(flatten([x["_source"] for x in requirements])), 1)

    def test_update_requirement(self):
        id = self.repo_doc.insert(self.documents[0])

        requirement = next(data for node, data in self.documents[0].traverse() if data['level'] == 6)
        requirement['text'] = "UPDATED TEXT"
        requirement['meta'] = "UPDATED META"

        self.repo_req.update(doc_id=id, requirement=requirement)

        updated_requirement = self.repo_req.get(requirement['id'])
        self.assertDictEqual(updated_requirement['_source'], requirement)

        updated_document = self.repo_doc.get(id)
        self.assertDictEqual(updated_document, self.documents[0].to_dict())



