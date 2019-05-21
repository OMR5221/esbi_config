from datetime import datetime as dt
from datetime import timedelta
import time

import dash
import dash_core_components as dcc
import dash_html_components as html
import dash_table
import dash_daq as daq
import pandas as pd
import plotly.graph_objs as go
from dash.dependencies import (Input, Output, Event, State)
from flask import Flask
from flask_login import login_required
from sqlalchemy import func
from sqlalchemy.sql import text
import json
import copy

# from server import server
from app.data import *


def register_callbacks(dashapp):

    # Update tags available for selection based on selected plant_id:
    @dashapp.callback(Output('tagnames-dropdown', 'options'),
                        [
                            Input('plant-id-dropdown', 'value')
                        ])
    def update_tags_dropdown(plant_id):
        df = tags_dim_df.loc[tags_dim_df['PLANT_ID'] == plant_id, ['TAG_NAME']]
        return [{'label': tagname, 'value': tagname} for tagname in df['TAG_NAME']]


    # Update Table based on dropdowns:
    @dashapp.callback(Output('outages-table', 'data'),
                      [
                        Input('outages-table', 'pagination_settings'),
                        Input('plant-id-dropdown', 'value'),
                        Input('daily-date-pick', 'start_date'),
                        Input('daily-date-pick', 'end_date')
                      ])
    def update_outages_table(ps, plant_id, start_date, end_date):

        if start_date is not None:
            start_date = dt.strptime(start_date, '%Y-%m-%d')
            start_date_string = start_date.strftime('%Y-%m-%d')

        if end_date is not None:
            end_date = dt.strptime(end_date, '%Y-%m-%d')
            end_date_string = end_date.strftime('%Y-%m-%d')

        if not daily_outages_df.empty:

            df = daily_outages_df.loc[(daily_outages_df['PLANT_ID'] == plant_id) &
                                        (daily_outages_df['DAILY_DATE'] >= start_date) &
                                        (daily_outages_df['DAILY_DATE'] <= end_date)].copy()

            df[' index'] = range(1, len(df) + 1)
            dfp = df.iloc[
                ps['current_page']*ps['page_size']:
                (ps['current_page'] + 1)*ps['page_size']
            ]
            dff = dfp.sort_values(['PLANT_ID', 'DAILY_DATE', 'TAG_NAME'], ascending=[True, True, True], inplace=False)
            return dff.to_dict("rows")

        else:
            df = [{}]
            return df


    # Update MISSSING RECS Table:
    @dashapp.callback(Output('missing-recs-table', 'data'),
                      [
                          Input('missing-recs-table', 'pagination_settings'),
                          Input('plant-id-dropdown', 'value'),
                          Input('daily-date-pick', 'start_date'),
                          Input('daily-date-pick', 'end_date')
                      ])
    def update_counts_tag_table(ps, plant_id, start_date, end_date):

        if start_date is not None:
            start_date = dt.strptime(start_date, '%Y-%m-%d')
            start_date_string = start_date.strftime('%Y-%m-%d')
            
        if end_date is not None:
            end_date = dt.strptime(end_date, '%Y-%m-%d')
            end_date_string = end_date.strftime('%Y-%m-%d')

            
        if not daily_counts_df.empty:
            df = daily_counts_df.loc[(daily_counts_df['PLANT_ID'] == plant_id) &
                                    (daily_outages_df['DAILY_DATE'] >= start_date) &
                                    (daily_outages_df['DAILY_DATE'] <= end_date)].copy()
                                    
            #  .loc[row_indexer,col_indexer] = value
            df[' index'] = range(1, len(df) + 1)
            dfp = df.iloc[
                ps['current_page']*ps['page_size']:
                (ps['current_page'] + 1)*ps['page_size']
            ]
            dff = dfp.sort_values(['PLANT_ID','TAG_NAME'], ascending=[True, True], inplace=False)
            return dff.to_dict("rows")

        else:
            dff = [{}]
            return dff


    # Update graph based on dropdowns:
    @dashapp.callback(Output('plant-graph', 'figure'),
                      [
                          Input('plant-id-dropdown', 'value'),
                          Input('daily-date-pick', 'start_date'),
                          Input('daily-date-pick', 'end_date'),
                          Input('tagnames-dropdown', 'value')
                      ])
    def tag_outlier_graph(plant_id, start_date, end_date, tag_name):

        if start_date is not None:
            start_date = dt.strptime(start_date, '%Y-%m-%d')
            start_date_string = start_date.strftime('%Y-%m-%d')

        if end_date is not None:
            end_date = dt.strptime(end_date, '%Y-%m-%d')
            end_date_string = end_date.strftime('%Y-%m-%d')

        if tag_name:

            df = s1_dm_df.loc[(s1_dm_df['PLANT_ID'] == plant_id) &
                              (s1_dm_df['TAG_NAME'] == str(tag_name)) &
                              (s1_dm_df['DAILY_DATE'] >= start_date) &
                              (s1_dm_df['DAILY_DATE'] <= end_date),
                              ['PLANT_ID', 'TAG_NAME','DAILY_DATE', 'AVG_DAILY_VAL']]

            df = df.sort_values('DAILY_DATE')

            return {
                'data': [
                    go.Scatter(
                        x = df[df['TAG_NAME'] == i]['DAILY_DATE'],
                        y = df[df['TAG_NAME'] == i]['AVG_DAILY_VAL'],
                        text = df[df['TAG_NAME'] == i]['TAG_NAME'],
                        mode = 'lines+markers',
                        opacity = 0.7,
                        marker = {
                            'size': 10,
                            'line': {'width': 0.5, 'color': 'white'}
                            },
                        name = str(i)
                    ) for i in df['TAG_NAME'].unique()
                ],
                'layout': go.Layout(
                    xaxis={'title': 'Day'},
                    yaxis={'title': 'Avg Value'},
                    margin={'l': 60, 'b': 40, 't': 10, 'r': 10},
                    legend=dict(
                        x=-.1,
                        y=1.2,
                        traceorder='normal',
                        orientation='h',
                        font=dict(
                            family='sans-serif',
                            size=9,
                            color='#000'
                        ),
                        bgcolor='#FFFFFF',
                        bordercolor='#FFFFFF',
                        borderwidth=0
                    ),
                    hovermode='closest'
                )
            }
