# Control url loads of different apps:

import dash_core_components as dcc
import dash_html_components as html
from dash.dependencies import Input, Output

import dash
from flask import Flask
from flask_login import login_required

from app import create_app

server = create_app()

'''
external_stylesheets = ['https://cdn.rawgit.com/plotly/dash-app-stylesheets/2d266c578d2a6e8850ebce48fdb52759b2aef506/stylesheet-oil-and-gas.css']
# external_stylesheets = ['https://codepen.io/chriddyp/pen/bWLwgP.css']
dashapp = dash.Dash(name=__name__, server=server,
                    external_stylesheets=external_stylesheets)
dashapp.config.suppress_callback_exceptions = True
# protect_dashviews(dashapp)
'''
