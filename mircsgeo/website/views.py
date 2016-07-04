from django.shortcuts import render, redirect
from django.template import RequestContext
from django.http import HttpResponse, JsonResponse, HttpResponseRedirect
from django.conf import settings
from sqlalchemy.orm import sessionmaker
from sqlalchemy import func

import math

import website.models as m
from .forms import Uploadfile

import pandas as pd

import os
import uuid

import datetime
import folium

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

        # Generate a UUID to use as the table name, use replace to remove dashes
        table_uuid = str(uuid.uuid4()).replace("-", "")

        # Get an sqlalchemy session automap'ed to the database
        session = m.get_session()
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
        """columns = df.columns.tolist()
        rows = df.values.tolist()
        rows = convert_nans(rows)"""

        """
        Add the dataset and transaction to the session and commit the session
        to the database
        """
        session.add(dataset)
        session.add(transaction)
        session.commit()

        # Generate a database table based on the data found in the CSV file
        table_generator.to_sql(df, datatypes, table_uuid, schema=schema)

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

    #Save north end coordinates
    NORTHEND_COORDINATES = (44.6701, -63.6108)

    # create empty map zoomed in on North end Halifax
    map = folium.Map(location=NORTHEND_COORDINATES, zoom_start=10)

    # add a marker for every record in the filtered data, use a clustered view
    if 'LATITUDE' in df and 'LONGITUDE' in df:
        for each in df[0:100].iterrows():
            map.simple_marker(
                location = [each[1]['LATITUDE'],each[1]['LONGITUDE']])


    map.save(os.path.dirname(os.path.abspath(__file__)) + '/static/maps/map-'+table+'.html')
    return render(request, 'view_dataset.html', {
        'dataset': rows,
        'columns': columns,
        'tablename': file_name,
        'map' : '/static/maps/map-'+table+'.html'
    })


def manage_dataset(request, table):
    return 'lols'


def get_dataset_page(request, table, page_number):
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

    return JsonResponse({
        'columns': columns,
        'rows': rows,
        'pageCount': page_count
    })


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
            if pd.isnull(e):
                row[i] = 'null'
    return rows


def Session():
    from aldjemy.core import get_engine
    engine = get_engine()
    _Session = sessionmaker(bind=engine)
    return _Session()
