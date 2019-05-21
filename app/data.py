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
from .models import PLANT_DIM, TAG_DIM, SCADA_STG1
from .db import es_dw_session, es_ods_session, es_dw_engine, es_ods_engine, es_dw_conn, es_ods_conn


class Timer():

    def __init__(self):
        self.start_time = 0
        self.duration = 0
        self.job_name = ""

    def start(self, job_name):
        self.start_time = time.time()
        self.job_name = job_name

    def stop(self):
        self.duration = time.time() - self.start_time
        print("Completed {JobName} in {Duration} seconds".format(JobName=self.job_name,Duration=self.duration))


def select_plant_dim():
    plant_dim_resp = es_dw_conn.execute("""
                                        SELECT DISTINCT
                                            pd.plant_id
                                        FROM ES_DW_OWNER.ES_PLANT_DIM pd
                                        WHERE pd.status = 'A'
                                        ORDER BY pd.plant_id
                                       """)
    plant_dim_df = pd.DataFrame(plant_dim_resp.fetchall())
    plant_dim_df.columns = [k.upper() for k in plant_dim_resp.keys()]
    return plant_dim_df


def select_tag_type_vals():
    tag_type_resp = es_dw_conn.execute("""
                                        SELECT DISTINCT
                                            td.plant_id,
                                            td.tag_type
                                        FROM ES_DW_OWNER.ES_TAGS_DIM td
                                       """)
    tag_type_df = pd.DataFrame(tag_type_resp.fetchall())
    tag_type_df.columns = [k.upper() for k in tag_type_resp.keys()]
    tag_type_df = tag_type_df.append({'TAG_TYPE': 'ALL'}, ignore_index=True)
    tag_type_df = tag_type_df.append({'TAG_TYPE': 'NONE'}, ignore_index=True)
    return tag_type_df


def select_tag_dim():
    tag_dim_resp = es_dw_conn.execute("""
                                        SELECT DISTINCT
                                            td.plant_id,
                                            td.tag_name,
                                            td.tag_type
                                        FROM ES_DW_OWNER.ES_TAGS_DIM td
                                       """)
    tag_dim_df = pd.DataFrame(tag_dim_resp.fetchall())
    tag_dim_df.columns = [k.upper() for k in tag_dim_resp.keys()]
    return tag_dim_df


def summ_s1(num_days):
    s1_dm_summ_resp = es_ods_conn.execute("""
                      select
                          td.plant_id,
                          td.tag_type,
                          td.tag_name as "TAG_NAME",
                          TO_CHAR(ts.TIMESTAMPLOCAL, 'YYYY-MM-DD') AS "DAILY_DATE",
                          ROUND(SUM_DAILY_VAL,2) AS "SUM_DAILY_VAL",
                          ROUND(AVG_DAILY_VAL,2) AS "AVG_DAILY_VAL",
                          ROUND(MIN_DAILY_VAL,2) AS "MIN_DAILY_VAL",
                          ROUND(MAX_DAILY_VAL,2) AS "MAX_DAILY_VAL",
                          DAILY_MIN_COUNT
                      from es_dw_owner.es_tags_dim td
                      CROSS JOIN
                      (
                          select (to_date(TO_CHAR(SYSDATE,'DD-MON-YYYY'),'dd-MON-yyyy') - INTERVAL '{nd}' DAY) + rownum -1 TIMESTAMPLOCAL
                          from all_objects
                          where rownum <= to_date(TO_CHAR(SYSDATE,'DD-MON-YYYY'),'dd-MON-yyyy')-(to_date(TO_CHAR(SYSDATE,'DD-MON-YYYY'),'dd-MON-yyyy') - INTERVAL '{nd}' DAY) + 1
                      ) TS
                      LEFT JOIN
                      (
                        SELECT /*+ PARALLEL */
                            PLANT_ID,
                            tagname,
                            DAILY_DATE,
                            SUM(VAL) SUM_DAILY_VAL,
                            AVG(VAL) AVG_DAILY_VAL,
                            MIN(VAL) MIN_DAILY_VAL,
                            MAX(VAL) MAX_DAILY_VAL,
                            COUNT(*) DAILY_MIN_COUNT
                        FROM
                        (
                            SELECT /*+ PARALLEL */
                                plant_id,
                                TAGNAME,
                                TRUNC(timestamplocal) DAILY_DATE,
                                NVL(NULLIF(VALUE, 'NaNQ'),0) VAL
                            FROM es_ods_owner.es_scada_stg1
                            WHERE TRUNC(timestamplocal) >= TO_DATE(TO_CHAR(SYSDATE,'DD-MON-RR'),
                            'DD-MON-RR') - INTERVAL '{nd}' DAY
                            AND TRUNC(timestamplocal) < TO_DATE(TO_CHAR(SYSDATE,'DD-MON-RR'), 'DD-MON-RR')
                        ) a
                        GROUP BY
                            PLANT_ID,
                            TAGNAME,
                            DAILY_DATE
                     ) s1
                     ON s1.plant_id = td.plant_id
                     AND s1.tagname = td.tag_name
                     AND s1.DAILY_DATE = TS.TIMESTAMPLOCAL
                     """.format(nd=num_days))
    s1_dm_summ_df = pd.DataFrame(s1_dm_summ_resp.fetchall())
    s1_dm_summ_df.columns = [k.upper() for k in s1_dm_summ_resp.keys()]
    # Convert date string into DateTime Type?
    s1_dm_summ_df['DAILY_DATE'] = pd.to_datetime(s1_dm_summ_df['DAILY_DATE'], format="%Y-%m-%d")
    # s1_dm_summ_df['MONTHLY_DATE'] = pd.to_datetime(s1_dm_summ_df['MONTHLY_DATE'], format="%Y-%m")
    return s1_dm_summ_df


def inv_stg2_daily(num_days):

    inv_stg2_daily_resp = es_ods_conn.execute("""
        SELECT
            plant_id as "PLANT_ID",
            TO_CHAR(TRUNC(TIMESTAMPLOCAL), 'YYYY-MM') AS "YEAR_MONTH",
            TO_CHAR(TRUNC(TIMESTAMPLOCAL), 'YYYY-MM-DD') AS "DATE",
            EXTRACT(HOUR FROM TIMESTAMPLOCAL) AS "HOUR",
            SUM(SITE_POWER) AS "DAILY SITE POWER",
            SUM(ENERGY_DEL_MWH) AS "DAILY ENERGY DELIVERED",
            SUM(ENERGY_REC_MWH) AS "DAILY ENERGY RECEIVED",
            round(SUM(down_time_hrs_areg),3) AS "DOWN_TIME_HRS_AREG",
            round(sum(down_time_hrs_rsd),3) AS "DOWN_TIME_HRS_RSD",
            round(sum(down_time_hrs_prfm),3) AS "DOWN_TIME_HRS_PRFM",
            round(sum(down_time_hrs_equip),3) AS "DOWN_TIME_HRS_EQUIP"
        FROM ES_ODS_OWNER.es_inverter_stg2
        WHERE TRUNC(timestamplocal) >= TO_DATE(TO_CHAR(SYSDATE,
        'DD-MON-RR'), 'DD-MON-RR') - INTERVAL '{nd}' DAY
        AND TRUNC(timestamplocal) < TO_DATE(TO_CHAR(SYSDATE,'DD-MON-RR'), 'DD-MON-RR')
        GROUP BY
            plant_id,
            TO_CHAR(TRUNC(timestamplocal),'YYYY-MM-DD'),
            EXTRACT(HOUR FROM TIMESTAMPLOCAL),
            TO_CHAR(TRUNC(TIMESTAMPLOCAL), 'YYYY-MM')
        ORDER BY plant_id,
        TO_CHAR(TRUNC(TIMESTAMPLOCAL), 'YYYY-MM'),
        TO_CHAR(TRUNC(timestamplocal),'YYYY-MM-DD'),
        EXTRACT(HOUR FROM TIMESTAMPLOCAL)
    """.format(nd=num_days))
    inv_stg2_daily_df = pd.DataFrame(inv_stg2_daily_resp.fetchall())
    inv_stg2_daily_df.columns = [k.upper() for k in inv_stg2_daily_resp.keys()]
    # Convert date string into DateTime Type?
    inv_stg2_daily_df['DATE'] = pd.to_datetime(inv_stg2_daily_df['DATE'], format="%Y-%m-%d")
    return inv_stg2_daily_df


def daily_outages(s1_df):
    return s1_df.loc[(s1_df['SUM_DAILY_VAL'] == 0), ['PLANT_ID','TAG_NAME','DAILY_DATE',
                                                 'MIN_DAILY_VAL', 'MAX_DAILY_VAL']]


def monthly_outages(s1_df):
    return s1_df.loc[(s1_df['MONTHLY_SUM'] == 0), ['PLANT_ID','TAG_NAME','MONTHLY_DATE',
                                                   'MIN_MONTHLY_VAL', 'MAX_MONTHLY_VAL']]


def daily_missing_recs(s1_df):
    return s1_df.loc[(s1_df['DAILY_MIN_COUNT'] > 0) & (s1_df['DAILY_MIN_COUNT'] < 1440),
                     ['PLANT_ID','TAG_NAME','DAILY_DATE','DAILY_MIN_COUNT']]


def monthly_missing_recs(s1_df):
    return s1_df.loc[(s1_df['MONTHLY_MIN_COUNT'] > 0) & (s1_df['MONTHLY_MIN_COUNT'] < 1440),
                     ['PLANT_ID','TAG_NAME','MONTHLY_DATE','MONTHLY_MIN_COUNT']]

def rsd_check(s2_df):
    # Check that the rsd calcualtion is correction for FREQ sites:
    return s2_df.loc[(s2_df['DOWN_TIME_HRS_RSD'] != (s2_df['DOWN_TIME_HRS_AREG'] - s2_df['DOWN_TIME_HRS_PRFM'])), ['PLANT_ID','DATE','HOUR']]

def equip_check(s2_df):
    # Check that the rsd calcualtion is correction for FREQ sites:
    return s2_df.loc[(s2_df['DOWN_TIME_HRS_EQUIP'] != (s2_df['DOWN_TIME_HRS_AREG'] - (s2_df['DOWN_TIME_HRS_RSD'] + s2_df['DOWN_TIME_HRS_PRFM']))),['PLANT_ID','DATE', 'HOUR']]

def select_min_date(num_days):
    return dt.utcnow().date() - timedelta(days=int(num_days))

### DTE TABLE: ###

# Get range of data:
def dte_daily(num_days):
    dte_data_resp = es_ods_conn.execute("""
					  SELECT mq.plant_code,
							 mq.plant_id,
							 mq.energy_del_mwh  AS "energy_delivered_mwh",
							 mq.energy_rec_mwh  AS "energy_received_mwh",
							 mq.downtime_hrs_inv  AS "downtime_hrs_inv",
							 mq.downtime_hrs_areg,
							 mq.downtime_hrs_rsd,
							 mq.downtime_hrs_equip,
							 mq.downtime_hrs_duration,
							 mq.down_time_hrs_battery,
							 mq.state_of_charge,
							 mq.start_date_time_local,
							 to_timestamp(to_char( (mq.start_date_time_local + 1/24) - 1/1440, 'DD-MON-RR HH24-MI-SS'),'DD-MON-RR HH24-MI-SS') AS "end_date_time_local",
							 es_ods_owner.es_battery_pkg.local_to_gmt(pi_input_date => TRUNC(mq.start_date_time_local, 'HH'),
																	  pi_timezone   => timezone )                   AS "start_date_time_utc",
							(es_ods_owner.es_battery_pkg.local_to_gmt(pi_input_date => TRUNC(mq.start_date_time_local, 'HH'),
																	  pi_timezone   => timezone ) + 1/24) - 1/1440  AS "end_date_time_utc",
							dd.rsd_type_id,
							dd.rsd_hrs,
							dd.event_id
					  FROM (SELECT eis.plant_id ,
								   pd.plant_code,
								   timezone,
								   TO_TIMESTAMP( (TRUNC(TIMESTAMPLOCAL) || ' ' ||  EXTRACT(HOUR FROM timestamplocal)||'-00-00'), 'DD-MON-RR HH24-MI-SS' ) start_date_time_local,
								   --TRUNC(timestamplocal, 'HH')        
								   SUM(energy_del_mwh)                energy_del_mwh,
								   SUM(energy_rec_mwh)                energy_rec_mwh,
								   SUM(down_time_hrs_inverter)        downtime_hrs_inv,
								   SUM(down_time_hrs_battery)         down_time_hrs_battery,
								   SUM(down_time_hrs_areg)            downtime_hrs_areg,
								   SUM(down_time_hrs_rsd)             downtime_hrs_rsd,
								   SUM(down_time_hrs_equip)           downtime_hrs_equip,
								   SUM(downtime_hours)                downtime_hrs_duration,
								   SUM(state_of_charge_avg)           state_of_charge
							FROM   es_ods_owner.es_inverter_stg2 eis
							JOIN   es_dw_owner.es_plant_dim      pd
							ON     eis.plant_id    = pd.plant_id
							WHERE TRUNC(timestamplocal) >= TO_DATE(TO_CHAR(SYSDATE,'DD-MON-RR'), 'DD-MON-RR') - INTERVAL '{nd}' DAY
							AND TRUNC(timestamplocal) < TO_DATE(TO_CHAR(SYSDATE,'DD-MON-RR'), 'DD-MON-RR')
							GROUP BY TO_TIMESTAMP( (TRUNC(TIMESTAMPLOCAL) || ' ' ||  EXTRACT(HOUR FROM timestamplocal)||'-00-00'), 'DD-MON-RR HH24-MI-SS' ),
										   eis.plant_id,
										   pd.plant_code,
										   timezone
					  ) MQ
					  left JOIN ES_ODS_OWNER.ES_DTE_DATA dd
						on dd.plant_id = mq.plant_id
						and TRUNC( mq.start_date_time_local ) = trunc(dd.start_date_time_local)
						and TO_CHAR(mq.energy_del_mwh) = TO_CHAR(dd.energy_delivered_mwh)
						and TO_CHAR(mq.energy_rec_mwh) = TO_CHAR(dd.energy_received_mwh)
						and mq.state_of_charge = dd.state_of_charge
					  WHERE( mq.downtime_hrs_equip > 0
					  OR     mq.downtime_hrs_rsd   > 0
					  OR  mq.downtime_hrs_duration > 0)
                     """.format(nd=num_days))
    dte_data_df = pd.DataFrame(dte_data_resp.fetchall())
    dte_data_df.columns = [k.upper() for k in dte_data_resp.keys()]
    # Convert date string into DateTime Type?
    # dte_data_df['DAILY_DATE'] = pd.to_datetime(dte_data_df['DAILY_DATE'], format="%Y-%m-%d")
    # s1_dm_summ_df['MONTHLY_DATE'] = pd.to_datetime(s1_dm_summ_df['MONTHLY_DATE'], format="%Y-%m")
    return dte_data_df


##################

t = Timer()
t.start("plant_dim")
plant_dim_df = select_plant_dim()
t.stop()

t.start("tags_dim")
tags_dim_df = select_tag_dim()
t.stop()

t.start("tag_type")
tag_types_df = select_tag_type_vals()
t.stop()

t.start("scada_stg1")
s1_dm_df = summ_s1(30)
t.stop()

t.start("inv_stg2")
s2_inv_df = inv_stg2_daily(30)
t.stop()

t.start("outages")
daily_outages_df = daily_outages(s1_dm_df)
t.stop()

t.start("missing_recs")
daily_counts_df = daily_missing_recs(s1_dm_df)
t.stop()

t.start("rsd_check")
rsd_check_df = rsd_check(s2_inv_df)
t.stop()

t.start("equip_check")
equip_check_df = equip_check(s2_inv_df)
t.stop()

t.start("dte_data")
min_date = dte_daily(30)
t.stop()

t.start("min_date")
min_date = select_min_date(30)
t.stop()

today_date = dt.now()
