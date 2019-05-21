from flask_login import UserMixin
from werkzeug.security import check_password_hash
from werkzeug.security import generate_password_hash

from app.extensions import db
from app.extensions import login


@login.user_loader
def load_user(id):
    return User.query.get(int(id))


class User(UserMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(64), index=True, unique=True)
    password_hash = db.Column(db.String(128))

    def set_password(self, password):
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.password_hash, password)

    def __repr__(self):
        return '<User {}>'.format(self.username)

# Load imports for Oracle DB:
from .db import local_engine, es_dw_engine, es_ods_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship
from sqlalchemy import (Column, Integer, String, TIMESTAMP, DateTime, Date, types, ForeignKey, Boolean)


# Load ES_DW_OWNER credentials:
es_dw_base = declarative_base()
es_dw_base.metadata.reflect(es_dw_engine)

class PLANT_DIM(es_dw_base):
    __tablename__ = 'es_plant_dim'
    __table_args__ = {'extend_existing': True}

    id = Column(Integer, primary_key=True)

    def __repr__(self):
        return '<ES_PLANT_DIM: {}>'.format(self.plant_code)


class TAG_DIM(es_dw_base):
    __tablename__ = 'es_tags_dim'
    __table_args__ = {'extend_existing': True}

    tag_id = Column(Integer, primary_key=True)

    def __repr__(self):
        return '<ES_TAG_DIM: {}>'.format(self.tagname)


# Load ES_ODS_OWNER credentials:
es_ods_base = declarative_base()
es_ods_base.metadata.reflect(es_ods_engine)

class SCADA_STG1(es_ods_base):
    __tablename__ = 'es_scada_stg1'
    __table_args__ = {'extend_existing': True}

    plant_id = Column(Integer, primary_key=True)
    plant_code = Column(String(10), primary_key=True)
    tagname = Column(String(120), primary_key=True)
    timestamplocal = Column(DateTime, primary_key=True)

    def __repr__(self):
        return '<ES_SCADA_STG1: {}>'.format(self.plant_code)
