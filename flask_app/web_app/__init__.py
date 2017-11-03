from flask import Flask
from flasgger import Swagger


swagger = Swagger()


from web_app.config import profiles
from web_app.controllers.streams import streams as streams_blueprint


def create_app(config_name):
    """
    Application Factory function

    Creates a Flask application passing a configuration profile:
    e.g. 'development' | 'testing' | 'production'
    """

    app = Flask(__name__)

    app.config.from_object(profiles[config_name])

    #  register blueprints
    app.register_blueprint(streams_blueprint)

    swagger.init_app(app)

    profiles[config_name].init_app(app)

    return app

