from flask import Blueprint
from flask import redirect
from flask import render_template
from flask import request
from flask import url_for
from flask_login import current_user
from flask_login import login_required
from flask_login import login_user
from flask_login import logout_user
from werkzeug.urls import url_parse
from sqlalchemy import func
from sqlalchemy.sql import text
import datetime
import json

from app.extensions import db
from app.forms import LoginForm
from app.forms import RegistrationForm
from app.models import User
from app.models import PLANT_DIM, SCADA_STG1
from app.db import es_dw_session, es_ods_session, es_dw_engine, es_ods_engine


server_bp = Blueprint('main', __name__)


@server_bp.route('/')
def index():
    return render_template("index.html", title='Home Page')


@server_bp.route('/login', methods=['GET', 'POST'])
def login():
    if current_user.is_authenticated:
        return redirect(url_for('main.index'))

    form = LoginForm()
    if form.validate_on_submit():
        user = User.query.filter_by(username=form.username.data).first()
        if user is None or not user.check_password(form.password.data):
            error = 'Invalid username or password'
            return render_template('login.html', form=form, error=error)

        login_user(user, remember=form.remember_me.data)
        next_page = request.args.get('next')
        if not next_page or url_parse(next_page).netloc != '':
            next_page = url_for('main.index')
        return redirect(next_page)

    return render_template('login.html', title='Sign In', form=form)


@server_bp.route('/logout')
@login_required
def logout():
    logout_user()

    return redirect(url_for('main.index'))


@server_bp.route('/register', methods=['GET', 'POST'])
def register():
    if current_user.is_authenticated:
        return redirect(url_for('main.index'))

    form = RegistrationForm()
    if form.validate_on_submit():
        user = User(username=form.username.data)
        user.set_password(form.password.data)
        db.session.add(user)
        db.session.commit()

        return redirect(url_for('main.login'))

    return render_template('register.html', title='Register', form=form)


@server_bp.route('/plant_dim')
def plant_dim():
    values = es_dw_session.query(PLANT_DIM).all()
    results = [{ 'plant_code': value.plant_code } for value in values]
    return (json.dumps(results), 200, { 'content_type': 'application/json' })


@server_bp.route('/scada_stg1')
def scada_stg1():
    with es_ods_engine.connect() as es_ods_conn:
        statement = text("""
                         SELECT distinct TRUNC(timestamplocal) timestamplocal, plant_code, tagname,
                         count(*) count
                         FROM ES_ODS_OWNER.ES_SCADA_STG1
                         WHERE TRUNC(timestamplocal) >= TO_DATE('01-OCT-18', 'DD-MON-RR')
                         group by TRUNC(timestamplocal),PLANT_CODE, TAGNAME
                         order by TRUNC(timestamplocal),PLANT_CODE, TAGNAME
                         """)
        values = es_ods_conn.execute(statement)
        results = [{ 'timestamplocal': value.timestamplocal, 'plant_code': value.plant_code, 'tag_name': value.tagname, 'count': value.count } for value in values]
        return (json.dumps(results, default=str), 200, { 'content_type': 'application/json' })
