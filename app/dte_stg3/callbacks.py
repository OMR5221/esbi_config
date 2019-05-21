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

from app.data import *


def register_callbacks(dashapp):

    # DTE Stg3 Dims: PLANT_ID, START_DATE_TIME_LOCAL, Energy_del, energy_rec, dt_hrs_dur,
    # dt_hrs_areg, dt_hrs_batt, rsd_hrs, dt_hrs_equip:

    # Update Table based on dropdowns:
    @dashapp.callback(Output('stg3-rsd-table', 'data'),
                      [
                        Input('stg3-rsd-table', 'pagination_settings'),
                        Input('stg3-plant-id-dropdown', 'value'),
                        Input('stg3-year-month-dropdown', 'value')
                      ])
    def update_rsd_check_table(ps, plant_id, year_month):

        if not stg3_rsd_hrs_df.empty:

            df = stg3_rsd_hrs_df.loc[(stg3_rsd_hrs_df['PLANT_ID'] == plant_id) &
                                    (stg3_rsd_hrs_df['YEAR_MONTH'] == year_month)].copy()

            df['index'] = range(1, len(df) + 1)
            dfp = df.iloc[ps['current_page'] * ps['page_size']: (ps['current_page'] + 1) * ps['page_size']]
            dff = dfp.sort_values(['PLANT_ID', 'YEAR_MONTH', 'DATE'], ascending=[True, True, True], inplace=False)
            return dff.to_dict("rows")

        else:
            df = [{}]
            return df

    # Update Equip Table:
    @dashapp.callback(Output('stg3-equip-table', 'data'),
                      [
                          Input('stg3-equip-table', 'pagination_settings'),
                          Input('stg3-plant-id-dropdown', 'value'),
                          Input('stg3-year-month-dropdown', 'value')
                      ])
    def update_equip_check_table(ps, plant_id, year_month):

        if not equip_check_df.empty:

            df = equip_check_df.loc[(equip_check_df['PLANT_ID'] == plant_id) &
                                    (equip_check_df['DAILY_DATE'] == year_month)].copy()

            #  .loc[row_indexer,col_indexer] = value
            df['index'] = range(1, len(df) + 1)
            dfp = df.iloc[
                ps['current_page'] * ps['page_size']:
                (ps['current_page'] + 1) * ps['page_size']
            ]
            dff = dfp.sort_values(['PLANT_ID','YEAR_MONTH', 'DATE'], ascending=[True, True, True], inplace=False)
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
