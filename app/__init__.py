import dash
from flask import Flask
from flask.helpers import get_root_path
from flask_login import login_required

from config import Config


# Set up Flask server and register dash apps, extensions and blueprints
def create_app():
    server = Flask(__name__)
    server.config.from_object(Config)

    register_dashapps(server)
    register_extensions(server)
    register_blueprints(server)

    return server


def register_dashapps(app):

    # Split file into layout and callbacks scripts:
    from app.scada_stg1.layout import layout
    from app.scada_stg1.callbacks import register_callbacks

    # Meta tags for viewport responsiveness:
    meta_viewport = {"name": "viewport",
                     "content": "width=device-width, initial-scale=1, shrink-to-fit=no"}


    layout_ess = ['https://cdn.rawgit.com/plotly/dash-app-stylesheets/2d266c578d2a6e8850ebce48fdb52759b2aef506/stylesheet-oil-and-gas.css']
    scada_stg1 = dash.Dash(__name__,
                           server=app,
                           url_base_pathname='/scada_stg1/',
                           assets_folder=get_root_path(__name__) + '/dashboard/assets/',
                           meta_tags=[meta_viewport],
                           external_stylesheets=layout_ess)

    scada_stg1.title = 'Scada Stg1'
    scada_stg1.layout = layout
    register_callbacks(scada_stg1)
    # Use Flask login security:
    # _protect_dashviews(scada_stg1)

    inv_stg2 = dash.Dash(__name__,
                         server=app,
                         url_base_pathname='/inv_stg2/',
                         assets_folder=get_root_path(__name__) + '/dashboard/assets/',
                         meta_tags=[meta_viewport],
                         external_stylesheets=layout_ess)

    inv_stg2.title = 'Inverter Stg2'
    inv_stg2.layout = layout
    register_callbacks(inv_stg2)


    dte_stg3 = dash.Dash(__name__,
                         server=app,
                         url_base_pathname='/dte_stg3/',
                         assets_folder=get_root_path(__name__) + '/dashboard/assets/',
                         meta_tags=[meta_viewport],
                         external_stylesheets=layout_ess)

    dte_stg3.title = 'DownTime Stg3'
    dte_stg3.layout = layout
    register_callbacks(dte_stg3)


    fact_stg4 = dash.Dash(__name__,
                         server=app,
                         url_base_pathname='/fact_stg4/',
                         assets_folder=get_root_path(__name__) + '/dashboard/assets/',
                         meta_tags=[meta_viewport],
                         external_stylesheets=layout_ess)

    fact_stg4.title = 'Fact Stg4'
    fact_stg4.layout = layout
    register_callbacks(fact_stg4)

    # Use Flask login security:
    # _protect_dashviews(inv_stg2)

# Enable login:
def _protect_dashviews(dashapp):

    for view_func in dashapp.server.view_functions:
        if view_func.startswith(dashapp.url_base_pathname):
            dashapp.server.view_functions[view_func] = login_required(dashapp.server.view_functions[view_func])


def register_extensions(server):
    from app.extensions import db
    from app.extensions import login
    from app.extensions import migrate

    db.init_app(server)
    login.init_app(server)
    login.login_view = 'main.login'
    migrate.init_app(server, db)


def register_blueprints(server):
    from app.webapp import server_bp

    server.register_blueprint(server_bp)
