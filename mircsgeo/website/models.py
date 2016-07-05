from __future__ import unicode_literals

from django.conf import settings

# from django.db import models
from sqlalchemy.ext.automap import automap_base
from sqlalchemy import create_engine, MetaData, Table, Column, Integer, String, Float, DateTime, ForeignKeyConstraint, ForeignKey, Enum, UniqueConstraint, Boolean
from sqlalchemy.orm import sessionmaker
from sqlalchemy.dialects.postgresql import ARRAY

import uuid

import atexit

# Create your models here.

# Get a connection to the database based on the info in settings.py
engine = create_engine(settings.SQLALCHEMY_CONNECT_STRING, echo=False)
# Create a metadata object to attach tables to
m = MetaData(schema=settings.DATABASES['default']['SCHEMA'])

datasets = Table('datasets', m,
    Column('uuid', String, primary_key=True),
    Column('original_filename', String),
    Column('upload_date', DateTime),
)

metadata = Table('metadata', m,
    Column('id', Integer, primary_key=True),
    Column('dataset_uuid', String),
    Column('key', String),
    Column('value', String),
    ForeignKeyConstraint(['dataset_uuid'], [settings.DATABASES['default']['SCHEMA'] + '.datasets.uuid']),
)

transaction_types = ('create', 'add', 'modify', 'add_and_modify', 'remove')
dataset_transactions = Table('dataset_transactions', m,
    Column('id', Integer, primary_key=True),
    Column('dataset_uuid', String),
    Column('transaction_type', Enum(*transaction_types, name='transaction_type'), default=transaction_types[0]),
    Column('rows_affected', Integer),
    Column('affected_row_ids', ARRAY(Integer)),
    ForeignKeyConstraint(['dataset_uuid'], [settings.DATABASES['default']['SCHEMA'] + '.datasets.uuid']),
)

dataset_keys = Table('dataset_keys', m,
    Column('dataset_uuid', String, primary_key=True),
    Column('constraint_name', String, primary_key=True),
    Column('constraint_author', String),
    ForeignKeyConstraint(['dataset_uuid'], [settings.DATABASES['default']['SCHEMA'] + '.datasets.uuid']),
)

dataset_joins = Table('dataset_joins', m,
    Column('dataset1_uuid', String),
    Column('dataset2_uuid', String),
    ForeignKeyConstraint(
        ['dataset1_uuid'],
        [settings.DATABASES['default']['SCHEMA'] + '.datasets.uuid'],
        name='fk_dataset_joins1_datasets_uuid'
    ),
    ForeignKeyConstraint(
        ['dataset2_uuid'],
        [settings.DATABASES['default']['SCHEMA'] + '.datasets.uuid'],
        name='fk_dataset_joins2_datasets_uuid'
    ),
)

# SAVAGE
# Close your eyes
def name_for_collection_relationship(base, local_cls, refered_cls, constraint):
    uid = str(uuid.uuid4()).replace('_', '')
    return refered_cls.__name__.lower() + "_" + uid + "_collection"

# BOILERPLATE
m.create_all(engine)
m.reflect(engine)
Base = automap_base(metadata=m)
Base.prepare(name_for_collection_relationship=name_for_collection_relationship)
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
    Base.prepare(name_for_collection_relationship=name_for_collection_relationship)
    Session = sessionmaker(bind=engine)


# Helper function for querying
def get_session():
    return Session()


def exit_handler():
    Session.close_all()
    print "Bye!"

atexit.register(exit_handler)
