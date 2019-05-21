import dash_core_components as dcc
import dash_html_components as html

from datetime import datetime as dt
from datetime import timedelta
import time

from app.data import *


PAGE_SIZE = 5

layout = dict(
    autosize=True,
    height=500,
    font=dict(color="#191A1A"),
    titlefont=dict(color="#191A1A", size='14'),
    margin=dict(
        l=35,
        r=35,
        b=35,
        t=45
    ),
    hovermode="closest",
    plot_bgcolor='#fffcfc',
    paper_bgcolor='#fffcfc',
    legend=dict(font=dict(size=10), orientation='h')
)

# Creating layouts for datatable
layout_right = copy.deepcopy(layout)
layout_right['height'] = 300
layout_right['margin-top'] = '20'
layout_right['font-size'] = '12'


layout_left = copy.deepcopy(layout)
layout_left['height'] = 300
layout_left['margin-top'] = '20'
layout_left['font-size'] = '12'


## LAYOUT SETTINGS:
layout = html.Div([

    # Title - Row
    html.Div(
        [
            html.H1(
                'ESBI Process Monitor',
                style={'font-family': 'Helvetica',
                       "margin-top": "25",
                       "margin-bottom": "0"},
                className='eight columns',
            ),
            html.Img(
                src="http://logo.png",
                className='two columns',
                style={
                    'height': '9%',
                    'width': '9%',
                    'float': 'right',
                    'position': 'relative',
                    'padding-top': 10,
                    'padding-right': 0
                },
            ),
            html.P(
                'A dashboard to review the data processing of the ESBI application.',
                style={'font-family': 'Helvetica',
                       "font-size": "120%",
                       "width": "80%"},
                className='eight columns',
            ),
        ],
        className='row'
    ),


    # Selectors
    html.Div(
        [

            # Create a DIV to organize the filters:
            html.Div([
                html.Label('Plant ID:'),
                dcc.Dropdown(
                    id = 'plant-id-dropdown',
                    options = [{ 'label': plant_id, 'value': plant_id } for plant_id in plant_dim_df['PLANT_ID']],
                    value = plant_dim_df['PLANT_ID'][0]
                    ),
                ],
                className='two columns',
                style={ 'margin-top': '10',
                        'margin-bottom': '10',
                        'font-family': 'Helvetica',
                        "font-size": "95%"}
            ),

            # Allow user to select a range of dates:
            html.Div([
                html.Label('Date Range:'),
                dcc.DatePickerRange(
                    id='daily-date-pick',
                    min_date_allowed=min_date,
                    max_date_allowed=today_date,
                    initial_visible_month=today_date,
                    start_date = (today_date.date() - timedelta(days=14)),
                    end_date = today_date.date() - timedelta(days=1)
                ),
                # Show selected dates:
                html.Div(id='daily-date-pick-start-text'),
                html.Div(id='daily-date-pick-end-text'),
            ],
            className='four columns',
            style={ 'margin-top': '10',
                    'margin-bottom': '10',
                    'font-family': 'Helvetica',
                    "font-size": "95%"}
            ),


            html.Div([
                html.Label('Tag Names:'),
                dcc.Dropdown(
                    id = 'tagnames-dropdown',
                    # options=[{ 'label': tagname, 'value': tagname } for tagname in ],
                    value = [tag for tag in tags_dim_df.loc[tags_dim_df['PLANT_ID'] == plant_dim_df['PLANT_ID'][0], ['TAG_NAME']]],
                    multi = False
                ),
            ],
            className='four columns',
            style={ 'margin-top': '10',
                    'margin-bottom': '10',
                    'font-family': 'Helvetica',
                    "font-size": "95%"}
            )
        ],
        className='row'
    ),

    # TABLES:
    html.Div(
    [
        html.Div([
            dash_table.DataTable(
                    id='outages-table',
                    columns = [{"name": i, "id": i, "deletable": False}
                                for i in daily_outages_df.columns],

                    sorting=False,
                    # sorting_type='single',
                    # sorting_settings=[],

                    filtering='be',

                    row_selectable="multi",
                    selected_rows=[],
                    pagination_settings={
                        'current_page': 0,
                        'page_size': PAGE_SIZE
                    },
                    pagination_mode='be'
                )
            ],
            className='six columns',
            style=layout_left
        ),

        html.Div([
            ## tags not coming into SCADA STG1:
            dash_table.DataTable(
                    id='missing-recs-table',
                    columns = [{"name": i, "id": i, "deletable": False} 
                                for i in daily_counts_df.columns],

                    sorting=False,
                    # sorting_type='single',
                    # sorting_settings=[],

                    filtering='be',

                    row_selectable="multi",
                    selected_rows=[],
                    pagination_settings={
                        'current_page': 0,
                        'page_size': PAGE_SIZE
                    },
                    pagination_mode='be'
                )
            ],
            className='six columns',
            style=layout_right
        ),
    ],
    className='row'
    ),

    html.Div([
        html.Div(
            [
                html.Div(id='container'),
                html.Div(daq.Gauge(id='empty'), style={'display': 'none'})
            ], className="twelve columns"
        ),
    ],
    className='row'
    ),


    # Graph
    html.Div(
        [
            html.Div(
                [
                    dcc.Graph(id='plant-graph',
                              animate=False,
                              style={'margin-top': '20'})
                ], className = "twelve columns"
            ),
        ],
        className="row"
    ),

], className='ten columns offset-by-one')

