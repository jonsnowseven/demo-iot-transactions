import logging
import os
import sys
import yaml


from web_app.utils.swagger import template


basedir = os.path.abspath(os.path.dirname(__file__))

_ROOT = os.path.abspath(os.path.dirname(__file__))

logging.basicConfig(
    stream=sys.stdout, level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)


def get_data(path):
    return os.path.join(_ROOT, path)


properties_path_dev = 'resources/properties/config.yaml'

with open(os.path.join(get_data(properties_path_dev))) as config_file:
    config = yaml.load(config_file)



class Config:
    SECRET_KEY = os.environ.get('SECRET_KEY') or 'hard to guess string'
    RESULTS_PER_PAGE = os.environ.get('RESULTS_PER_PAGE') or 10
    POSTGRESQL = config['db']['postgresql']
    ELASTICSEARCH = config['db']['elasticsearch']
    SQLALCHEMY_DATABASE_URI = config['db']['sqlalchemy']
    SQLALCHEMY_COMMIT_ON_TEARDOWN = True
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    SWAGGER = template


    @staticmethod
    def init_app(app):
        pass


class DevelopmentConfig(Config):
    DEBUG = True


class TestingConfig(Config):
    TESTING = True
    POSTGRESQL = config['db']['postgresql']
    ELASTICSEARCH = config['db']['elasticsearch']
    SQLALCHEMY_DATABASE_URI = config['db']['sqlalchemy']


class ProductionConfig(Config):
    PRODUCTION = True


profiles = {
    'development': DevelopmentConfig,
    'testing': TestingConfig,
    'production': ProductionConfig,
    'default': DevelopmentConfig
}
