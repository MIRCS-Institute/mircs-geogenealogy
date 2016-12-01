import numpy as np
import pandas as pd
import datetime, time
from django.conf import settings

from sqlalchemy import create_engine, MetaData, Table, Column, Integer, \
                       String, Float, DateTime, ForeignKeyConstraint, ForeignKey,\
                       Enum, UniqueConstraint, Boolean, func, and_
from geoalchemy2 import Geometry
from types import StringType

import uuid
import os

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
    table_name (str) - The name tusable_colshe table will be given
    schema (str) - The schema the table will be created into
    geospatial_columns(list) - A list of geospatial columns of the type returned
                               by get_geospatial_columns()

    Returns:
    table - The SQLAlchemy table object that was generated
    """
    #replace parantheses in column names with their html numbers
    #might have to do this for every entry in dataframe but haven't
    #come across case where that was needed
    df.columns = df.columns.str.replace('(','&#40')
    df.columns = df.columns.str.replace(')','&#41')

    create_table(df, datatypes, table_name, schema, geospatial_columns)
    print geospatial_columns
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
        print i
        print c
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

def insert_columns(columns, table):
    """
    Adds columns to a dataset.

    Arguments:
    columns (dict) - all the columns to be added {name: type}
    table (str) - the uuid of the dataset

    Returns:
    Nothing
    """
    columns = {k.replace('(','&#40'): v for (k, v) in columns.iteritems()}
    columns = {k.replace(')','&#41'): v for (k, v) in columns.iteritems()}

    for col, dtype in columns.iteritems():
        add_column_to_table(table, col, dtype)
        print col, dtype



def insert_column(df, datatypes, table):
    """
    add a new column to the table

    Arguments:
    df - the data added to the table. should have columns to match with and the new columnList
    datatypes - list of python datatypes of the columns
    table - the uid of the table to add the column to_csv

    returns:
    max id of rows affected
    """
    #prepare variables
    df.columns = df.columns.str.replace('(','&#40')
    df.columns = df.columns.str.replace(')','&#41')
    df.columns = df.columns.str.replace(' ', '_')
    columnList = df.columns.values.tolist()
    newCol = columnList[len(columnList)-1]
    columnList = columnList[:len(columnList)]
    table = getattr(m.Base.classes, table)

    #add the column
    add_column_to_table(table.__name__,newCol,datatypes[len(datatypes)-1])

    rows = convert_nans(df.values.tolist())

    sql = "SELECT column_name, data_type FROM information_schema.columns WHERE table_name = '%s' AND (" % table.__name__
    for col in columnList:
        sql = "%scolumn_name = '%s' OR " % (sql, col)
    # Remove the last OR and spaces and end the parantheses
    sql = "%s);" % sql[:-4]
    col_types = m.engine.execute(sql).fetchall();
    col_types = dict((x, y) for x, y in col_types)

    #for every row in the dataframe
    for row in rows:
        matchString=""
        #get the parameters to match on
        for col in columnList:
            dt = col_types[col]
            if row[columnList.index(col)] == 'null' or row[columnList.index(col)] == 'NaT':
                matchString = "%s \"%s\"=%s AND" % (matchString,col,row[columnList.index(col)])
            elif dt == 'character varying' or dt == 'timestamp without time zone':
                matchString = "%s \"%s\"='%s' AND" % (matchString,col,row[columnList.index(col)])
            else:
                matchString = "%s \"%s\"=%s AND" % (matchString,col,row[columnList.index(col)])

        #add the entry for the new row based on the matchstring
        matchString = matchString[:len(matchString)-3]
        dt = col_types[col]
        if dt == 'character varying' or dt == 'timestamp without time zone':
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
    df.columns = df.columns.str.replace('(','&#40')
    df.columns = df.columns.str.replace(')','&#41')
    columnList = df.columns.values.tolist()
    datatypes = get_readable_types_from_dataframe(df)
    for col in columnList:
        print col
        #sql="SELECT EXISTS(SELECT column_name FROM information_schema.columns WHERE table_name='%s' and column_name='%s')" % (table.__name__,col)
        res = m.engine.execute("SELECT EXISTS(SELECT column_name FROM information_schema.columns WHERE table_name=%s and column_name=%s)",(table.__name__,col))
        for k in res:
            if k[0] != True:
                add_column_to_table(table,col,datatypes[len(datatypes)-1])
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
def add_column_to_table(table, column_name, py_datatype):
    psql_types = {
        'integer': "integer",
        'float': "decimal",
        'datetime': "DateTime",
        'string': "text"
    }
    sql = "ALTER TABLE mircs.\"%s\" ADD COLUMN \"%s\" %s" % (table, column_name, psql_types[py_datatype])
    m.engine.execute(sql)
    m.refresh()
    print getattr(m.Base.classes, table).__dict__

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


def get_readable_types_from_dataframe(df, return_dict=False):
    """
    Get human readable datatypes for the columns in a pandas.DataFrame. This is
    used to help the user verify that the system is auto-generating the correct
    database column types

    Parameters:
    df (pandas.DataFrame) - The DataFrame the human readable datatype list will
                            be generated from.
    return_dict (bool) - If a dict should be returned instead of a list

    Returns:
    readable_types (mixed) - a list or dict of human readable datatypes. Dict
                             key is the column name
    """

    readable_types = {} if return_dict else []
    for i, d in enumerate(df.dtypes):
        if return_dict:
            readable_types[df.columns[i]] = convert_type(d)
        else:
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

def update_dataset(df, table, key):
    """
    Takes a dataframe of changes to be made to the data and updates the proper
    rows using a given confidence value.

    Parameters:
    df (pandas.DataFrame) - The dataframe with the proper row values
    table (str) - The name of the table that being updated
    key (list) -   The names of the columns that make up the key

    Returns:
    bool - If the update was successful or not
    """
    df = convert_nans(df)
    num_col = len(df.columns) # Gets the numbers of columns
    orm = getattr(m.Base.classes, table) # Gets the mapper for the table
    session = m.get_session()
    new_rows = df.copy()[df.index == -1]
    for index, row in df.iterrows():
        ands = [] # List of AND statements

        for i in range(len(key)):
            col = key[i].replace(' ', '_')
            ands.append(getattr(orm, col) == getattr(row, col))

        try:
            for col in row.to_dict():
                if str(row[col]).lower() == 'nat':
                    row[col] = None
            res = session.query(orm).filter(and_(*ands)).update(row.to_dict())
        except:
            return False
        finally:
            session.close()

        if res == 0:
            list_dict = new_rows.T.to_dict().values()
            list_dict.append(row)
            new_rows = pd.DataFrame(list_dict)
    session.close()
    geospatial_columns = get_geospatial_columns(table)
    insert_df(new_rows, orm, geospatial_columns)
    return True


def truncate_table(table):
    """
    Truncates the table. Legacy function, but could be useful down the road.

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


def add_resource(table, row_id, resource):
    """
    Adds a resource to a row of a dataset so links and files can be linked to
    dataset rows. When dealing with a file, the file is saved in resources folder
    located in the media folder

    Parameters:
    table (str) - the name of the table
    row_id (int) - the id of the row_id
    resource (mixed) - file to save or str

    Return:
    (bool) - True if resource was added
    """
    Resource = m.Base.classes.resources
    session = m.get_session()
    table_orm = getattr(m.Base.classes, table)
    count = len((session.query(table_orm).filter(table_orm.id == row_id)).all())
    if count == 1:

        resource_orm = Resource()
        resource_orm.dataset_uuid = table
        resource_orm.row_id = row_id
        if type(resource) is str:
            resource_orm.location = resource
        elif type(resource) is file:
            resource_name = os.path.basename(resource.name)
            resource_dir = os.path.join(
                os.path.dirname(__file__),
                settings.MEDIA_ROOT,
                'resources'
            )
            try:
                if not os.path.isdir(resource_dir):
                    os.mkdir(resource_dir)
                ext = os.path.splitext(resource_name)[1]
                file_name = '%s.%s' % (uuid.uuid4(), ext)
                full_path = os.path.join(
                    resource_dir,
                    file_name
                )
                new_file = open(full_path, 'w')
                new_file.write(resource.read())
                new_file.close()
                resource_orm.location = full_path
                resource_orm.file_name = resource_name
            except:
                print "Except!"
                raise
                session.close()
                return False

        session.add(resource_orm)
        session.commit()
        session.close()
        return True
    session.close()
    return False



def convert_nans(rows):
    """
    Convert np.NaN objects to 'null' so rows is JSON serializable

    Parameters:
    rows (list) - list of rows
    """
    for row in rows:
        for i, e in enumerate(row):
            try:
                if pd.isnull(e):
                    row[i] = 'null'
            except TypeError as err:
                row[i] = str(e)
    return rows
