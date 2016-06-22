import numpy as np
import pandas as pd

from sqlalchemy import create_engine, MetaData, Table, Column, Integer, \
                       String, Float, DateTime, ForeignKeyConstraint, ForeignKey,\
                       Enum, UniqueConstraint, Boolean

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


def to_sql(df, datatypes, table_name, schema):
    create_table(df, datatypes, table_name, schema)
    session = m.get_session()
    table = getattr(m.Base.classes, table_name)
    print table
    insert_df(df, table, session)
    session.close()
    return table


def create_table(df, datatypes, table_name, schema):
    datatypes = get_alchemy_types(datatypes)
    columns = [Column('id', Integer, primary_key=True)]
    for i, c in enumerate(df.columns):
        columns.append(
            Column(c, datatypes[i])
        )
    table = Table(table_name, m.m, *columns, schema=schema)
    m.m.create_all(m.engine)
    m.refresh()
    return table


def insert_df(df, table, session):
    print dir(table)
    for row in df.to_dict('records'):
        for c in row:
            if pd.isnull(row[c]):
                row[c] = None
        session.add(
            table(**row)
        )
    session.commit()
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
