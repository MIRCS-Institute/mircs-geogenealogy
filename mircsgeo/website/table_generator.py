import numpy as np
import pandas as pd

from sqlalchemy import create_engine, MetaData, Table, Column, Integer, \
                       String, Float, DateTime, ForeignKeyConstraint, ForeignKey,\
                       Enum, UniqueConstraint, Boolean

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
