# Control url loads of different apps:

import dash_core_components as dcc
import dash_html_components as html
from dash.dependencies import Input, Output

import dash
from flask import Flask
from flask_login import login_required

from app import dashapp
from apps import scada_stg1


dashapp.layout = html.Div([
    dcc.Location(id='url', refresh=False),
    html.Div(id='page-content')
])


@dashapp.callback(Output('page-content', 'children'),
            [Input('url', 'pathname')])
def display_page(pathname):

    if pathname == '/apps/scada_stg1':
        return scada_stg1.layout
    elif pathname == '/apps/inv_stg2':
        return inv_stg2.layout
    else:
        return '404'

if __name__ == '__main__':
    dashapp.run_server(debug=True)
