import numpy as np
import pandas as pd

from sqlalchemy import create_engine, MetaData, Table, Column, Integer, \
                       String, Float, DateTime, ForeignKeyConstraint, ForeignKey,\
                       Enum, UniqueConstraint, Boolean
from geoalchemy2 import Geometry

import website.models as m

type_mappings = {
    'int': 'integer',
    'float': 'float',
    'datetime': 'datetime',
    'object': 'string'
}

alchemy_types = {
    'integer': Integer,
    'float': Float,
    'datetime': DateTime,
    'string': String
}


def to_sql(df, datatypes, table_name, schema, geospatial_columns=None):
    create_table(df, datatypes, table_name, schema, geospatial_columns)
    session = m.get_session()
    table = getattr(m.Base.classes, table_name)
    insert_df(df, table, session, geospatial_columns)
    session.close()
    return table


def create_table(df, datatypes, table_name, schema, geospatial_columns=None):
    datatypes = get_alchemy_types(datatypes)
    columns = [Column('id', Integer, primary_key=True)]
    for i, c in enumerate(df.columns):
        columns.append(
            Column(c, datatypes[i])
        )
    if geospatial_columns is not None:
        for c in geospatial_columns:
            if c['type'] == 'latlon':
                columns.append(
                    Column(c['name'], Geometry('POINT', srid=c['srid']))
                )
    table = Table(table_name, m.m, *columns, schema=schema)
    m.m.create_all(m.engine)
    m.refresh()
    return table


def insert_df(df, table, session, geospatial_columns=None):
    insert_dict = df.to_dict('records')
    for row in insert_dict:
        for c in row:
            if pd.isnull(row[c]):
                row[c] = None
        if geospatial_columns is not None:
            for c in geospatial_columns:
                row[c['name']] = 'SRID=%s;POINT(%s %s)' % (c['srid'], row[c['lat_col']], row[c['lon_col']])
    m.engine.execute(
        table.__table__.insert(),
        insert_dict
    )
    return


def get_alchemy_types(mapped_types):
    rt = []
    for t in mapped_types:
        rt.append(alchemy_types[t])
    return rt


def get_readable_types_from_dataframe(df):
    readable_types = []
    for d in df.dtypes:
        readable_types.append(convert_type(d))
    return readable_types


def convert_type(dtype):
    d = str(dtype)
    for t in type_mappings:
        if t in d:
            return type_mappings[t]
    return None
