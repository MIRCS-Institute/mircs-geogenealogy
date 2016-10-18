import numpy as np
import pandas as pd

from sqlalchemy import create_engine, MetaData, Table, Column, Integer, \
                       String, Float, DateTime, ForeignKeyConstraint, ForeignKey,\
                       Enum, UniqueConstraint, Boolean, func
from geoalchemy2 import Geometry
from types import StringType

import website.models as m

# Pandas to human readable mapping
type_mappings = {
    'int': 'integer',
    'float': 'float',
    'datetime': 'datetime',
    'object': 'string'
}

# Human readable to alchemy mapping
alchemy_types = {
    'integer': Integer,
    'float': Float,
    'datetime': DateTime,
    'string': String
}


def to_sql(df, datatypes, table_name, schema, geospatial_columns=None):
    """
    Create a database table based on a DataFrame and load it with data

    Parameters:
    df (pandas.DataFrame) - The DataFrame the table will be generated based on.
                            The data found in this DataFrame will be loaded into the table
    datatypes (list) - A list of SQLAlchemy column datatypes
    table_name (str) - The name the table will be given
    schema (str) - The schema the table will be created into
    geospatial_columns(list) - A list of geospatial columns of the type returned
                               by get_geospatial_columns()

    Returns:
    table - The SQLAlchemy table object that was generated
    """
    create_table(df, datatypes, table_name, schema, geospatial_columns)
    table = getattr(m.Base.classes, table_name)
    insert_df(df, table, geospatial_columns)
    return table


def create_table(df, datatypes, table_name, schema, geospatial_columns=None):
    """
    Create a database table based on a DataFrame

    Parameters:
    df (pandas.DataFrame) - The dataframe the table will be generated for
    datatypes (list) - A list of SQLAlchemy column datatypes
    table_name (str) - The name the table will be given
    schema (str) - The schema the table will be created into
    geospatial_columns (list) - A list of geospatial columns of the type returned
                                from get_geospatial_columns()

    Returns:
    table - The generated SQLAlchemy table object
    """
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
def insert_column(df,datatypes, table):
    """
    add a new column to the table

    Arguments:
    df - the data added to the table. should have columns to match with and the new columnList
    datatypes - list of python datatypes of the columns
    table - the uid of the table to add the column to_csv

    returns:
    max id of rows affected
    """
    #define conversion between python types and psql types
    psql_types = {
        'integer': 'integer',
        'float': 'decimal',
        'datetime': 'DateTime',
        'string': 'text'
    }
    #prepare variables
    columnList = df.columns.values.tolist()
    newCol = columnList[len(columnList)-1]
    columnList = columnList[:len(columnList)-1]
    table = getattr(m.Base.classes, table)

    #add the column
    sql = "ALTER TABLE mircs.\"%s\" ADD COLUMN \"%s\" %s" % (table.__name__,newCol, psql_types[datatypes[len(datatypes)-1]])
    m.engine.execute(sql)

    #for every row in the dataframe
    for row in df.itertuples():
        matchString=""

        #get the parameters to match on
        for col in columnList:
            sql="SELECT data_type FROM information_schema.columns WHERE table_name = '%s' AND column_name ='%s'" % (table.__name__,col)
            typeSql = m.engine.execute(sql)
            for k in typeSql:
                dt = k[0]
            if dt == 'character varying':
                matchString = "%s \"%s\"='%s' AND" % (matchString,col,row[columnList.index(col)+1])
            else:
                matchString = "%s \"%s\"=%s AND" % (matchString,col,row[columnList.index(col)+1])

        #add the entry for the new row based on the matchstring
        matchString = matchString[:len(matchString)-3]
        sql="SELECT data_type FROM information_schema.columns WHERE table_name = '%s' AND column_name ='%s'" % (table.__name__,col)
        typeSql = m.engine.execute(sql)
        for k in typeSql:
            dt = k[0]
        if dt == 'character varying':
            sql = "UPDATE mircs.\"%s\" SET \"%s\"='%s' WHERE %s" % (table.__name__,newCol,row[len(row)-1],matchString)
        else:
            sql = "UPDATE mircs.\"%s\" SET \"%s\"=%s WHERE %s" % (table.__name__,newCol,row[len(row)-1],matchString)
        m.engine.execute(sql)

    #get return value i.e. max id of rows affected (used fr transaction table entry)
    sql = "SELECT MAX(id) FROM mircs.\"%s\"" % (table.__name__,)
    res = m.engine.execute(sql)
    for k in res:
        ret = k[0]
    return ret

def insert_df(df, table, geospatial_columns=None):
    """
    Load a DataFrame into an autogenerated database table

    Arguments:
    table - The SQLAlchemy table object into which data will be loaded
    geospatial_columns (list) - A list of geospatial columns found in the dataset.
                                Should be of the form returned by get_geospatial_columns()

    Returns:
    Nothing
    """
    insert_dict = df.to_dict('records')
    for row in insert_dict:
        for c in row:
            if pd.isnull(row[c]):
                row[c] = None
        if geospatial_columns is not None:
            for c in geospatial_columns:
                row[c['name']] = 'SRID=%s;POINT(%s %s)' % (c['srid'], row[c['lon_col']], row[c['lat_col']])

    m.engine.execute(
        table.__table__.insert(),
        insert_dict
    )
    return


def get_geospatial_columns(table_uuid):
    """
    Get a list of geospatial column definitions from the geospatial_columnns table
    for a given table

    Parameters:
    table_uuid (str) - The uuid of an autogenerated database table

    Retruns:
    columns (list) - A list of geospatial column definitions where each element
                     is of the type returned by parse_geospatial_column_string()
    """
    session = m.get_session()
    res = session.query(m.GEOSPATIAL_COLUMNS.column_definition).filter(
        m.GEOSPATIAL_COLUMNS.dataset_uuid == table_uuid
    )
    columns = []
    for col in res:
        columns.append(parse_geospatial_column_string(col[0]))
    session.close()
    return columns


def parse_geospatial_column_string(geospatial_column_string):
    """
    Convert a geospatial column definition String into a dictionary to be used
    by the database generation functions.

    Parameters:
    geospatial_column_string (str) - A string defining a geospatial column.
                                     probably either returned from the upload_file page
                                     or pulled from the column_definition column of the
                                     geospatial_columns table.
        example: name=geom&lat_col=LATITUDE&lon_col=LONGITUDE&srid=4326&type=latlon

    Returns:
    geospatial_column (dict) - A dictionary containing all the information foud in the defintion string
    """
    # For each geospatial column, create a dictionary using fields as keys to store values
    for column in geospatial_column_string.split(','):
        # Create the dictionary
        geospatial_column = {'column_definition': column}

        for field in column.split('&'):
            field = field.split('=')
            # "exampleone=7&exampletwo=8" -> {"exampleone":7, "exampletwo":8}
            geospatial_column[field[0]] = field[1]

        # Append the dictionary to geospatial_columns (for the to_sql function)
    return geospatial_column


def get_alchemy_types(mapped_types):
    """
    Get SQLAlchemy column datatype objects from a list of human readable datatypes.
    This converts a verified list human readable types from the frontend to objects
    for database generation on the backend

    Parameters:
    mapped_types (list) -  a list of human readable datatypes like those generated
                           by get_readable_types_from_dataframe().

    Returns:
    rt (list) - A list of SQLAlchemy column datatype objects
    """
    rt = []
    for t in mapped_types:
        rt.append(alchemy_types[t])
    return rt


def get_readable_types_from_dataframe(df):
    """
    Get human readable datatypes for the columns in a pandas.DataFrame. This is
    used to help the user verify that the system is auto-generating the correct
    database column types

    Parameters:
    df (pandas.DataFrame) - The DataFrame the human readable datatype list will
                            be generated from.

    Returns:
    readable_types (list) - a list of human readable datatypes
    """
    readable_types = []
    for d in df.dtypes:
        readable_types.append(convert_type(d))
    return readable_types


def convert_type(dtype):
    """
    Convert a pandas dtype to a human readable database type.

    Parameters:
    dtype - a dtype from the column of a pandas.Dataframe or a pandas.Series

    Returns:
    type_mapping (str) - the human readable equivalent of the dtype
    """
    d = str(dtype)
    for t in type_mappings:
        if t in d:
            return type_mappings[t]
    return None

def truncate_table(table):
    """
    Truncates the table.

    Parameters:
    table_name (str) - the name of the table to truncate
    """

    session = m.get_session()

    max_id_query = session.query(func.max(table.id).label("last_id")).one()[0]
    min_id_query = session.query(func.min(table.id).label("first_id")).one()[0]
    row_count = session.query(func.count(table.id)).one()[0]

    session.execute("DELETE FROM mircs.\"%s\" WHERE id >= 0" % table.__name__) # Delete all rows
    session.execute("ALTER SEQUENCE mircs.\"%s_id_seq\" RESTART WITH 1" % table.__name__) # Reset the id
    session.commit()



    transaction = m.DATASET_TRANSACTIONS( # Makes a transaction
        dataset_uuid=table.__name__,
        transaction_type=m.transaction_types[4],
        rows_affected=row_count,
        affected_row_ids=range(min_id_query, max_id_query),
    )

    session.add(transaction)
    session.commit()
    session.close()
