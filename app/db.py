import os
from sqlalchemy import create_engine
from sqlalchemy.orm import (scoped_session, sessionmaker)


file_path = os.path.abspath(os.getcwd()) + "\\app.db"

# local db session:
local_engine = create_engine('sqlite:///' + file_path)
local_session = scoped_session(sessionmaker(bind=local_engine))

es_dw_engine = create_engine('oracle://schema_name:password@DB')
es_dw_conn = es_dw_engine.connect()
es_dw_session = scoped_session(sessionmaker(bind=es_dw_engine))

es_ods_engine = create_engine('oracle://schema_name:password@DB')
es_ods_conn = es_ods_engine.connect()
es_ods_session = scoped_session(sessionmaker(bind=es_ods_engine))
