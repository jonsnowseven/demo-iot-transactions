import json
from unittest import TestCase

from web_app.config import config_test
from web_app.utils.elasticsearch.query_templates import _field_type, with_terms


class TestQueryTemplates(TestCase):

    @classmethod
    def setUpClass(cls):
        cls.mapping = json.loads(open(config_test["mock"]["es_mapping_sample"], "r").read())

    def test_get_mapping_field_type_top_level(self):
        self.assertEqual("text", _field_type('document_name', self.mapping))
        self.assertEqual("nested", _field_type('nodes', self.mapping))

    def test_get_mapping_field_type_nested_level(self):
        self.assertEqual("long", _field_type('nodes.content.document_level', self.mapping))
        self.assertEqual("keyword", _field_type('nodes.content.tags', self.mapping))
        self.assertEqual("text", _field_type('nodes.predecessors', self.mapping))

    def test_build_terms_blocks(self):

        fields = [
            ('nodes.content.document_level', 6),
            ('nodes.content.tags', ["TAG_01", "TAG_02"]),
            ('nodes.content.industry', "finance")
        ]

        blocks = with_terms(fields, self.mapping)

        target = [
            {'terms': {'nodes.content.tags': ['TAG_01', 'TAG_02']}},
            {'term': {'nodes.content.industry.keyword': 'finance'}},
            {'term': {'nodes.content.document_level': 6}}
        ]

        self.assertListEqual(target, blocks)

