from __future__ import unicode_literals

from django.conf import settings

# from django.db import models
from sqlalchemy.ext.automap import automap_base
from sqlalchemy import create_engine, MetaData, Table, Column, Integer, String, Float, DateTime, ForeignKeyConstraint, ForeignKey, Enum, UniqueConstraint, Boolean
from sqlalchemy.orm import sessionmaker
from sqlalchemy.dialects.postgresql import ARRAY

import atexit

# Create your models here.

# Get a connection to the database based on the info in settings.py
engine = create_engine(settings.SQLALCHEMY_CONNECT_STRING, echo=False)
# Create a metadata object to attach tables to
m = MetaData(schema=settings.DATABASES['default']['SCHEMA'])

datasets = Table('datasets', m,
    Column('id', Integer, primary_key=True),
    Column('original_filename', String),
    Column('table_name', String),
    Column('upload_date', DateTime),
    schema=settings.DATABASES['default']['SCHEMA'],
)

metadata = Table('metadata', m,
    Column('id', Integer, primary_key=True),
    Column('dataset_id', Integer),
    Column('key', String),
    Column('value', String),
    ForeignKeyConstraint(['dataset_id'], [settings.DATABASES['default']['SCHEMA'] + '.datasets.id']),
    schema=settings.DATABASES['default']['SCHEMA'],
)

transaction_types = ('add', 'modify', 'add_and_modify', 'remove')
dataset_transactions = Table('dataset_transactions', m,
    Column('id', Integer, primary_key=True),
    Column('dataset_id', Integer),
    Column('transaction_type', Enum(*transaction_types, name='transaction_type'), default=transaction_types[0]),
    Column('rows_affected', Integer),
    Column('affected_row_ids', ARRAY(Integer)),
    ForeignKeyConstraint(['dataset_id'], [settings.DATABASES['default']['SCHEMA'] + '.datasets.id']),
    schema=settings.DATABASES['default']['SCHEMA'],
)

# BOILERPLATE
m.create_all(engine)
m.reflect(engine)
Base = automap_base(metadata=m)
Base.prepare()
Session = sessionmaker(bind=engine)

# Expose the tables that were just created
DATASETS = Base.classes.datasets
METADATA = Base.classes.metadata
DATASET_TRANSACTIONS = Base.classes.dataset_transactions


def refresh():
    global m
    global Base
    global Session
    global engine
    m.reflect(engine)
    Base = automap_base(metadata=m)
    Base.prepare()
    Session = sessionmaker(bind=engine)


# Helper function for querying
def get_session():
    return Session()


def exit_handler():
    Session.close_all()
    print "Bye!"

atexit.register(exit_handler)
