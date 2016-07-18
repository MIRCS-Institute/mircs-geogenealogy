from django.shortcuts import render, redirect
from django.template import RequestContext
from django.http import HttpResponse, JsonResponse, HttpResponseRedirect
from django.conf import settings
from sqlalchemy.orm import sessionmaker
from sqlalchemy.schema import Index
from sqlalchemy import func, or_
import geoalchemy2.functions as geofunc

import json

import math

import website.models as m
from .forms import Uploadfile, AddDatasetKey

import pandas as pd

import os
import uuid

import datetime

import website.table_generator as table_generator

schema = "mircs"


def home(request):
    """
    Render a view listing all datasets found in the datasets table in the DB
    """

    db = Session().connection()
    session = m.get_session()
    tables = session.query(
        m.DATASETS.original_filename,
        m.DATASETS.uuid,
        m.DATASETS.upload_date
    ).all()
    session.close()

    context = {'tables': tables}
    return render(request, 'home.html', context)


def upload_file(request):
    """
    Render a file upload form
    """

    if request.method == 'POST':
        return HttpResponseRedirect('test_response')
    else:
        form = Uploadfile()
    return render(request, 'upload_file.html', {'form': form})


def store_file(request):
    """
    Submit the file upload form and return a JSON object containing data from the file
    """

    if request.method == 'POST':
        # Do some stuff
        form = Uploadfile(request.POST, request.FILES)
        if form.is_valid():
            # Store the name of the uploaded file in the session for this request
            request.session['real_filename'] = request.FILES['file_upload'].name
            # Generate a UUID to serve as the temporary filename, store it in the session
            request.session['temp_filename'] = str(uuid.uuid4())
            # Store the file extension in the session
            request.session['filetype'] = os.path.splitext(request.session['real_filename'])[1]

            # Figure out the path to the file location
            absolute_path = os.path.join(
                os.path.dirname(__file__),
                settings.MEDIA_ROOT,
                request.session['temp_filename']
            )

            # Parse the file using the relevant pandas read_* function
            if request.session['filetype'].lower() == '.csv':
                df = pd.read_csv(request.FILES['file_upload'])
            elif request.session['filetype'].lower() == '.xlsx':
                df = pd.read_excel(request.FILES['file_upload'])
            else:
                # TODO: Add a proper error handler for invalid file uploads. Probably inform the user somehow
                raise Exception("invalid file type uploaded: %s" % request.session['filetype'])
            # Store the file as a csv
            df.to_csv(absolute_path, index=False)

            df = convert_time_columns(df)

            # Return the columns and the first 10 rows of the file as a JSON object
            columns = df.columns.tolist()
            rows = df[0:10].values.tolist()

            # Get the autopicked datatypes for the columns
            datatypes = table_generator.get_readable_types_from_dataframe(df)
            possible_datatypes = table_generator.type_mappings.values()

            # Convert np.NaN objects to 'null' so rows is JSON serializable
            rows = convert_nans(rows)

            return JsonResponse({
                'columns': columns,
                'rows': rows,
                'datatypes': datatypes,
                'possibleDatatypes': possible_datatypes
            })
    else:
        return None


def create_table(request):
    """
    Submit the primary key / datatype picking page and create a database table
    from the file that was uploaded by the store_file view
    """

    if request.method == 'POST':
        # Get the POST data
        post_data = dict(request.POST)
        # Get teh primary key from the posted data
        datatypes = post_data['datatypes'][0].split(',')

        # Get an sqlalchemy session automap'ed to the database
        session = m.get_session()

        # Generate a UUID to use as the table name, use replace to remove dashes
        table_uuid = str(uuid.uuid4()).replace("-", "")

        # Parse the string returned from the form
        geospatial_string = post_data['geospatial_columns'][0]
        geospatial_columns = []
        for column in geospatial_string.split(','):
            c = {}
            for field in column.split('&'):
                field = field.split('=')
                c[field[0]] = field[1]

            geospatial_columns.append(c)

            geo_col = m.GEOSPATIAL_COLUMNS(
                dataset_uuid=table_uuid,
                column=c['name']
            )
            session.add(geo_col)


        # Figure out the path to the file that was originally uploaded
        absolute_path = os.path.join(
            os.path.dirname(__file__),
            settings.MEDIA_ROOT,
            request.session['temp_filename']  # Use the filepath stored in the session
                                              # from when the user originally uploaded
                                              # the file
        )
        # Use pandas to read the uploaded file as a CSV
        df = pd.read_csv(absolute_path)
        df = convert_time_columns(df)
        # Replace spaces with underscores in the column names to be used in the db table
        df.columns = [x.replace(" ", "_") for x in df.columns]


        # Create a new dataset to be added
        dataset = m.DATASETS(
            uuid=table_uuid,
            original_filename=request.session['real_filename'],
            upload_date=datetime.datetime.now(),
        )
        # create a new transaction to be added
        ids = [int(i) for i in (df.index + 1).tolist()]

        transaction = m.DATASET_TRANSACTIONS(
            dataset_uuid=table_uuid,
            transaction_type=m.transaction_types[0],
            rows_affected=len(ids),
            affected_row_ids=ids,
        )


        # Add the dataset and transaction to the session and commit the session
        # to the database
        session.add(dataset)
        session.add(transaction)
        session.commit()

        # Generate a database table based on the data found in the CSV file
        table_generator.to_sql(df, datatypes, table_uuid, schema, geospatial_columns)

        session.close()
        return redirect('/')
    else:
        return None


def view_dataset(request, table):
    """
    Return a page drawing the requested dataset using an html table

    Parameters:
    table (str) - the name of the table to be displayed. This should be a UUID
    """
    # Get a session
    session = m.get_session()
    # Get the name of the file used to create the table being queried
    file_name = str(session.query(
        m.DATASETS.original_filename
    ).filter(
        m.DATASETS.uuid == table
    ).one()[0])  # This returns a list containing a single element(original_filename)
                 # The [0] gets the filename out of the list
    session.close

    db = Session().connection()
    # Get the first 100 rows of data out of the database for the requested dataset
    df = pd.read_sql("SELECT * FROM " + schema + ".\"" + table + "\" LIMIT 100",
                     db, params={'schema': schema, 'table': table})
    columns = df.columns.tolist()
    rows = convert_nans(df.values.tolist())

    return render(request, 'view_dataset.html', {
        'dataset': rows,
        'columns': columns,
        'tablename': file_name,
    })


def manage_dataset(request, table):
    """
    Return a page for managing table data

    Parameters:
    table (str) - the name of the table to be displayed. This should be a UUID
    tablename (str) - original filename of uploaded table
    """

    # Get a session
    session = m.get_session()
    # Get the name of the file used to create the table being queried
    file_name = str(session.query(
        m.DATASETS.original_filename
    ).filter(
        m.DATASETS.uuid == table
    ).one()[0])  # This returns a list containing a single element(original_filename)
                 # The [0] gets the filename out of the list

    keys = session.query(
        m.DATASET_KEYS
    ).filter(
        m.DATASET_KEYS.dataset_uuid == table
    ).all()
    session.close

    joins = session.query(
        m.DATASET_JOINS
    ).filter(
        or_(
            m.DATASET_JOINS.dataset1_uuid == table,
            m.DATASET_JOINS.dataset2_uuid == table
        )
    ).all()

    return render(request, 'manage_dataset.html', {
        'tablename': file_name,
        'table': table,
        'keys': keys,
        'joins': joins
    })

def append_dataset(request, table):
    """
    Append dataset to existing table

    Parameters:
    table (str) - the name of the table to be displayed. This should be a UUID
    """
    if request.method == 'POST':
        # Get the POST data
        post_data = dict(request.POST)
        # Get teh primary key from the posted data
        datatypes = post_data['datatypes'][0].split(',')

        # Figure out the path to the file that was originally uploaded
        absolute_path = os.path.join(
            os.path.dirname(__file__),
            settings.MEDIA_ROOT,
            request.session['temp_filename']  # Use the filepath stored in the session
                                              # from when the user originally uploaded
                                              # the file
        )
        # Use pandas to read the uploaded file as a CSV
        df = pd.read_csv(absolute_path)
        df = convert_time_columns(df)
        # Replace spaces with underscores in the column names to be used in the db table
        df.columns = [x.replace(" ", "_") for x in df.columns]

        # Get a session
        session = m.get_session()
        table_uuid = table
        table = getattr(m.Base.classes, table)
        query = session.query(func.max(table.id).label("last_id"))
        idMax = query.one()
        result = table_generator.insert_df(df, table, session)
        newIdMax = query.one()

        # Create entry in transaction table for append
        transaction = m.DATASET_TRANSACTIONS(
            dataset_uuid=table_uuid,
            transaction_type=m.transaction_types[1],
            rows_affected=len(df.index),
            affected_row_ids=range(idMax[0]+1, newIdMax[0]+1),
        )
        session.add(transaction)
        session.commit()

        session.close()
        return redirect('/manage/'+table_uuid)
    else:
        form = Uploadfile()
        return render(request, 'append_dataset.html', {
            'form': form,
            'table': table
        })

def add_dataset_key(request, table):
    if request.method == 'POST':
        # Get the POST parameter
        post_data = dict(request.POST)
        dataset_columns = post_data['dataset_columns']

        # Get the table
        t = getattr(m.Base.classes, table)

        # Get the column objects for each selected column in the POST parameter
        column_objects = []
        for col in dataset_columns:
            column_objects.append(getattr(t.__table__.columns, col))

        # Build up a standard name for the index
        index_name = '%s_' % table
        for col in dataset_columns:
            index_name += '%s_' % col
        index_name += 'idx'

        # Create an sqlalchemy Index object
        index = Index(index_name, *column_objects)
        index.create(m.engine)

        # Create an entry in dataset_keys
        session = m.get_session()
        dataset_key = m.DATASET_KEYS(
            dataset_uuid=table,
            index_name=index_name,
            dataset_columns=dataset_columns
        )
        session.add(dataset_key)
        session.commit()
        session.close()

        # This will eventually redirect to the manage_dataset page
        return redirect('/manage/'+table)
    else:
        columns = [str(x).split('.')[1] for x in getattr(m.Base.classes, table).__table__.columns]
        form = AddDatasetKey(zip(columns, columns))
        return render(request, 'add_dataset_key.html', {'form': form})


def get_dataset_page(request, table, page_number):
    id_range, page_count = get_pagination_id_range(table, page_number)

    # Get a session
    session = m.get_session()

    # Get the object for the table we're working with
    table = getattr(m.Base.classes, table)


    query = session.query(
        table
    ).filter(
        table.id > id_range[0],
        table.id <= id_range[1]
    )

    # Get a DataFrame with the results of the query
    df = pd.read_sql(query.statement, query.session.bind)

    columns = df.columns.tolist()
    rows = df.values.tolist()
    rows = convert_nans(rows)
    median_lat = df.LATITUDE.median()
    median_lon = df.LONGITUDE.median()

    return JsonResponse({
        'columns': columns,
        'rows': rows,
        'pageCount': page_count,
        'lat': median_lat,
        'lon': median_lon
    })


def join_datasets(request, table):
    """
    Join Datsets
    """
    # If the method is post write the join to the datbase
    if request.method == "POST":
        # Get the POST data
        post_data = dict(request.POST)

        # Get the sqlalchemy sesssion and create the dataset_join object
        session = m.get_session()
        dataset_join = m.DATASET_JOINS(
            dataset1_uuid=post_data['main_dataset'][0],
            index1_name=post_data['main_key'][0],
            dataset2_uuid=post_data['joining_dataset'][0],
            index2_name=post_data['joining_key'][0]
        )
        # Commit the object to the database
        session.add(dataset_join)
        session.commit()
        session.close()
        # Return to the tables dataset manage page
        return redirect('/manage/'+table)
    else:
        # If the Request is GET, get the datasets
        session = m.get_session()
        tables = session.query(
            m.DATASETS.original_filename,
            m.DATASETS.uuid,
            m.DATASETS.upload_date
        ).all()

        # Get the table datasets keys
        keys = session.query(
            m.DATASET_KEYS
        ).filter(
            m.DATASET_KEYS.dataset_uuid == table
        )
        session.close()

        # Return to the manage/join page
        context = {'tables': tables, 'main':table, 'keys': keys}
        return render(request, 'join_datasets.html', context)


def get_dataset_keys(request, table):
    """
    Get Table Keys
    """
    session = m.get_session()
    query = session.query(
        m.DATASET_KEYS
    ).filter(
        m.DATASET_KEYS.dataset_uuid == table
    )
    session.close()
    df = pd.read_sql(query.statement,query.session.bind)
    keys = []
    for index, row in df.iterrows():
        keys.append([row['index_name'], row['dataset_columns']])
    return JsonResponse({'keys':keys})


def get_dataset_geojson(request, table, page_number):
    id_range, page_count = get_pagination_id_range(table, page_number)

    # Get a session
    session = m.get_session()

    t = getattr(m.Base.classes, table)

    # Get geospatial columns
    geo = m.GEOSPATIAL_COLUMNS
    geospatial_columns = session.query(geo.column).filter(geo.dataset_uuid == table).all()
    geo_column_objects = []
    geo_column_names = []
    for col in geospatial_columns:
        geo_column_objects.append(geofunc.ST_AsGeoJSON(getattr(t, col[0])))
        geo_column_names.append(col[0])

    # build up geospatial select functions
    # Note: we're just grabbing the first geospatial column right now
    #       a picker for geo columns might be desirable someday
    geojson = session.query(t, geo_column_objects[0].label('geometry')).filter(
        t.id > id_range[0],
        t.id <= id_range[1]
    )
    # Get a DataFrame with the results of the query
    data = pd.read_sql(geojson.statement, geojson.session.bind)
    geo_column_names.append('geometry')

    # Build some properly formatted geojson to pass into leaflet
    geojson = []
    for i, r in data.iterrows():
        # Geometry and properties are both required for a 'Feature' object.
        geometry = r['geometry']
        properties = r.drop(geo_column_names).to_dict()
        geojson.append({
            'type': 'Feature',
            'properties': properties,
            'geometry': json.loads(geometry),
            'keys': sorted(properties.keys())
        })
    return JsonResponse(geojson, safe=False)




def test_response(request):
    return HttpResponse('yay')


def convert_time_columns(df, datetime_identifiers=['time', 'date']):
    # Find and convert time and date columns based on name
    for c in df.columns:
        for d in datetime_identifiers:
            if d in c.lower():
                df[c] = pd.to_datetime(df[c])
    return df


def convert_nans(rows):
    # Convert np.NaN objects to 'null' so rows is JSON serializable
    for row in rows:
        for i, e in enumerate(row):
            try:
                if pd.isnull(e):
                    row[i] = 'null'
            except TypeError as err:
                row[i] = str(e)
    return rows


def get_pagination_id_range(table, page_number):
    # Get a session
    session = m.get_session()

    # Get the object for the table we're working with
    table = getattr(m.Base.classes, table)

    # Figure out how many rows are in the dataset and calculate the number of pages
    dataset_count = session.query(
        func.count(table.id)
    ).one()[0]
    page_count = int(math.ceil(dataset_count / settings.DATASET_ITEMS_PER_PAGE))

    # Calculate the id range covered by the current page
    id_range = (
        int(page_number) * settings.DATASET_ITEMS_PER_PAGE,
        (int(page_number) + 1) * settings.DATASET_ITEMS_PER_PAGE
    )
    session.close()

    return id_range, page_count

def Session():
    from aldjemy.core import get_engine
    engine = get_engine()
    _Session = sessionmaker(bind=engine)
    return _Session()
