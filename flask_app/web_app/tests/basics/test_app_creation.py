from nose.tools import assert_true, assert_false

from flask import current_app
from web_app import create_app


class TestAppCreation:

    def setup(self):
        self.app = create_app('testing')
        self.app_context = self.app.app_context()
        self.app_context.push()

    def teardown(self):
        self.app_context.pop()

    @classmethod
    def setup_class(cls):
        pass

    @classmethod
    def teardown_class(cls):
        pass

    def test_app_exists(self):
        assert_false(current_app is None)

    def test_app_is_testing(self):
        assert_true(current_app.config['TESTING'])

