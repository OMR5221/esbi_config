import os
basedir = os.path.abspath(os.path.dirname(__file__))


class Config(object):

    file_path = os.path.abspath(os.getcwd()) + "app.db"

    SQLALCHEMY_DATABASE_URI = 'sqlite:///' + file_path

    #SQLALCHEMY_DATABASE_URI = # os.environ.get('DATABASE_URL')
    SQLALCHEMY_TRACK_MODIFICATIONS = True
    # SECRET_KEY = os.environ['SECRET_KEY']
    DEBUG = True
    SQLALCHEMY_ECHO = True


class DevelopmentConfig(Config):
    """
    Test configurations
    """
    DEBUG = True
    SQLALCHEMY_ECHO = True

    """
    SQLALCHEMY_BINDS = {
        'local': 'sqlite:///app/esbi_config_local.db',
        'orx_es_dw': 'oracle://schema_name:password@DBNAME',
        'orx_es_ods': 'oracle://schema_name:password@DBNAME',
        'orx_solar_ods': 'oracle://schema_name:password@DBNAME'
    }
    """


class QAConfig(Config):
    """
    QAConfig configurations
    """
    DEBUG = True
    SQLALCHEMY_ECHO = True

    """
    SQLALCHEMY_BINDS = {
        'local': 'sqlite:///esbi_config_local.db',
        'orx_es_dw': 'oracle://schema_name:password@DBNAME',
        'orx_es_ods': 'oracle://schema_name:password@DBNAME',
        'orx_solar_ods': 'oracle://schema_name:password@DBNAME'
    }
    """


class ProductionConfig(Config):
    """
    Production configurations
    """
    DEBUG = False
    SQLALCHEMY_ECHO = False
    """
    SQLALCHEMY_BINDS = {
        'local': 'sqlite:///esbi_config_local.db',
        'orx_es_dw': 'oracle://schema_name:password@DBNAME',
        'orx_es_ods': 'oracle://schema_name:password@DBNAME',
        'orx_solar_ods': 'oracle://schema_name:password@DBNAME'
    }
    """

app_config = {
    'qa': QAConfig,
    'dev': DevelopmentConfig,
    'prod': ProductionConfig
}
