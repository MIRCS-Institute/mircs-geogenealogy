from django.shortcuts import render, redirect
from django.template import RequestContext
from django.http import HttpResponse, JsonResponse, HttpResponseRedirect
from django.conf import settings
from sqlalchemy.orm import sessionmaker, class_mapper
from sqlalchemy.schema import Index
from sqlalchemy import func, or_
import geoalchemy2.functions as geofunc

import json

import math
import numbers

import website.models as m
from .forms import Uploadfile, AddDatasetKey

import pandas as pd

import os
import uuid

import datetime

import website.table_generator as table_generator

import logging

schema = "mircs"

def home(request):
    """
    Render a view listing all datasets found in the datasets table in the DB
    """

    # Connect to the session
    session = m.get_session()

    # Create a table map to pass to the html file
    tables = session.query(
        m.DATASETS.original_filename,
        m.DATASETS.uuid,
        m.DATASETS.upload_date
    ).all()
    # Close the session
    session.close()
    # Create a context of the table map to pass to the html file
    context = {'tables': tables}
    # Renders the home page
    return render(request, 'home.html', context)


def upload_file(request):
    """
    Render a file upload form
    """

    # Check to make sure it is not a Post request
    if request.method == 'POST':
        return HttpResponseRedirect('test_response')
    else:
        # File upload form
        form = Uploadfile()
    # Render the upload file page
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

            # Convert dates and times to proper datetime format
            df = convert_time_columns(df)

            # Return the columns and the first 10 rows of the file as a JSON object
            columns = df.columns.tolist()
            rows = df[0:10].values.tolist()

            # Get the autopicked datatypes for the columns
            datatypes = table_generator.get_readable_types_from_dataframe(df)
            possible_datatypes = table_generator.type_mappings.values()

            # Convert np.NaN objects to 'null' so rows is JSON serializable
            rows = table_generator.convert_nans(rows)

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
        print len(geospatial_string)
        if len(geospatial_string) > 0:
            geospatial_columns = []
            for col in  geospatial_string.split(','):
                geospatial_columns.append(table_generator.parse_geospatial_column_string(col))

            for c in geospatial_columns:
                # Add geospatial columns to the session
                geo_col = m.GEOSPATIAL_COLUMNS(
                    dataset_uuid=table_uuid,
                    column=c['name'],
                    column_definition=c['column_definition']
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

        # Create a transaction to add to transaction table
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
        if len(geospatial_string) > 0:
            table_generator.to_sql(df, datatypes, table_uuid, schema, geospatial_columns)
        else:
            print df.columns
            table_generator.to_sql(df, datatypes, table_uuid, schema)

        session.close()
        return redirect('/')
    else:
        return None

def get_dataset_columns(request, table):
    # Get a session
    session = m.get_session()
    # Get the object for the table we're working with
    table = getattr(m.Base.classes, table)
    table = session.query(table)
    # Get a DataFrame
    df = pd.read_sql(table.statement, table.session.bind)

    # Convert to a list of strings
    columns = df.columns.tolist()

    session.close()
    return JsonResponse({
        'columns': columns, #Return the list
    })

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
    session.close()
    # Render the view dataset page
    return render(request, 'view_dataset.html', {
        'tablename': file_name
    })
	
def search_dataset(request, table):
    """
    Opens the page that allows the user to search a dataset, and retrieve the input data in post to view it
    """
    if request.method == 'POST':
        # Get session
        session = m.get_session()
        # Get the object for the table we're working with
        table = getattr(m.Base.classes, table)
        table = session.query(table)
        # Get a DataFrame
        df = pd.read_sql(table.statement, table.session.bind)
        # Get the list of columns
        columns = df.columns.tolist()
        # Close the session
        session.close()

        post_data = dict(request.POST) #Retrieve the post data
        queries = []

        # Load the post data into an array of pairs (columns and respective input strings)
        for col in columns: #Check each column in the table
            if col in post_data: #If that column name was returned in the post data, then there is an input for it
                queries.append([col, post_data[col+'_query'][0].encode("ascii")]) #Add the pair

        #Call the page to view the results of the search and pass the queries
        return render(request, 'view_dataset_query.html', { 
            'queries': queries
        })
    else:
        return render(request, 'search_dataset.html')

def get_dataset_query(request, table, queries):
    """
    Uses input data to build a SQL alchemy query and returns the resulting data
    """
    # Get the list of queries
    queries = queries.split("/")[:-1]
    # This list in in the format [col1, query for col1, col2, query for col2, etc...]

    # Get a session
    session = m.get_session()

    # Get the object for the table we're working with
    table = getattr(m.Base.classes, table)

	# Build the query command
    i = 0
    search = "query = session.query(table).filter("
    valid = True
    while i < len(queries) and valid:
        if i != 0: #Add commas between filters
            search += ", "
        logging.warning(str(getattr(table, queries[i]).type))
        if str(getattr(table, queries[i]).type) == 'INTEGER': #Query for integer columns
            if isInt(queries[i+1]): #If input string is a valid integer, add the filter
                search += "getattr(table, queries["+str(i)+"]) == int(queries["+str(i+1)+"])"
            else: # If the input is not valid, the query cannot return any results
                valid = False
        elif str(getattr(table, queries[i]).type) == 'DOUBLE PRECISION': #Query for decimal columns
            if isFloat(queries[i+1]): #If input string is a valid float, add the filter
                search += "getattr(table, queries["+str(i)+"]) == float(queries["+str(i+1)+"])"
            else: # If the input is not valid, the query cannot return any results
                valid = False
        else: # Query for string columns
            search += "getattr(table, queries["+str(i)+"]).ilike(\"%\"+queries["+str(i+1)+"]+\"%\")"
        i += 2 #Items accessed from list in pairs [col1, quer1, col2, quer2, etc...]

    if not valid: #If the query had invalid input, return with a false value
        session.close()
        return JsonResponse({
            'valid': valid
        })

    search += ")"
    # Query the table
    exec(search)

    # Get a DataFrame with the results of the query
    df = pd.read_sql(query.statement, query.session.bind)

    # Convert everything to the correct formats for displaying
    columns = df.columns.tolist()
    rows = table_generator.convert_nans(df.values.tolist())

    session.close()
    return JsonResponse({
        'columns': columns,
        'rows': rows,
        'valid': valid
    })

def isInt(value): #Returns true if the given string can be converted to a valid integer
    try:
        int(value)
        return True
    except ValueError:
        return False

def isFloat(value): #Returns true if the given string can be converted to a valid float
    try:
        float(value)
        return True
    except ValueError:
        return False

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
    # Get the keys from the table being queried
    keys = session.query(
        m.DATASET_KEYS
    ).filter(
        m.DATASET_KEYS.dataset_uuid == table
    ).all()
    session.close
    # Get the user defined joins for the table
    joins = session.query(
        m.DATASET_JOINS
    ).filter(
        or_(
            m.DATASET_JOINS.dataset1_uuid == table,
            m.DATASET_JOINS.dataset2_uuid == table
        )
    ).all()

    # Render the data management page
    return render(request, 'manage_dataset.html', {
        'tablename': file_name,
        'table': table,
        'keys': keys,
        'joins': joins
    })

def append_column(request, table):
    """
    append a new column to a table

    parameters:
    table(str) - uid of the table to add the column too
    """

    # If it is POST append the column
    if request.method == 'POST':
        # Get the POST data
        post_data = dict(request.POST)

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
        datatypes = table_generator.get_readable_types_from_dataframe(df)

        # Get a session
        session = m.get_session()

        # Append the column to the table
        ids = table_generator.insert_column(df, datatypes, table)

        # Create entry in transaction table for appending column
        transaction = m.DATASET_TRANSACTIONS(
            dataset_uuid=table,
            transaction_type=m.transaction_types[3],
            rows_affected=ids,
            affected_row_ids=range(1,ids),
        )
        session.add(transaction)
        session.commit()
        # Close the session
        session.close()

        return redirect('/manage/' + table)
    else:
        # Upload file form (Used for appending)
        form = Uploadfile()
        # Render the append column page
        return render(request, 'append_column.html', {
            'form': form,
            'table': table
        })

def append_dataset(request, table, flush=False):
    """
    Append dataset to existing table

    Parameters:
    table (str) - the name of the table to be displayed. This should be a UUID
    flush (bool) - if True, it truncates the table first (Default: False)
    """
    # If it is POST append the dataset
    if request.method == 'POST':

        df = create_df_from_upload(request)

        # Get a session
        session = m.get_session()
        # Store the table uuid
        table_uuid = table

        # Get the table model
        table = getattr(m.Base.classes, table)

        # Get the current highest row id in the table
        query = session.query(func.max(table.id).label("last_id"))
        idMax = query.one()

        geospatial_columns = table_generator.get_geospatial_columns(table_uuid)
        print geospatial_columns

        if flush:
            table_generator.truncate_table(table)


        if flush:
            table_generator.truncate_table(table)


        # Append the to the table with a batch insert
        table_generator.insert_df(df, table, geospatial_columns)

        # Get the new highest row id in the table
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

        # Close the session
        session.close()

        return redirect('/manage/' + table_uuid)
    else:
        # Upload file form (Used for appending)
        form = Uploadfile()
        # Render the append dataset page
        return render(request, 'append_dataset.html', {
            'form': form,
            'table': table
        })
		
def update_dataset(request, table):
    """
    update  dataset to existing table
	
    Parameters:
    table (str) - the name of the table to be displayed. This should be a UUID
    """
    # If it is POST update the dataset
    if request.method == 'POST':
        df = create_df_from_upload(request)
        key = request.POST.getlist('key')
        table_generator.update_dataset(
            df,
            table,
            key
        )
        return redirect('/manage/' + table)
    else:
        # Upload file form (Used for appending)
        form = Uploadfile()
        # Render the append dataset page
        session = m.get_session()
        # Get all the keys belonging to this dataset
        keys = session.query(m.dataset_keys).filter_by(dataset_uuid=table).all()
        keys = [{
            'index': x.index_name,
            # Makes strings able to be stored in tags' value attr
            'columns': json.dumps(x.dataset_columns).replace('"', '\'')
            } for x in keys]

        return render(request, 'update_dataset.html', {
            'form': form,
            'table': table,
            'keys': keys
        })

def add_dataset_key(request, table):
    """
    Add a key to a dataset
    """
    # If POST add the key
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

        # Redirect to the manage_dataset page
        return redirect('/manage/' + table)
    else:
        # Get the columns in the table and add them to the dropdown in the form
        columns = [str(x).split('.')[1] for x in getattr(m.Base.classes, table).__table__.columns]
        form = AddDatasetKey(zip(columns, columns))
        # Return the form
        return render(request, 'add_dataset_key.html', {'form': form})


def get_dataset_page(request, table, page_number):
    """"
    Get the data for a specific page of a dataset

    Parameters:
    table (str) - The uuid of the table being requested
    page_number (int) - The page being requested

    Returns:
    JsonResponse (str) - A JSON string containing:
                                * median latitude for the current page
                                * median longitude for the current page
                                * pageCount - total number of pages in dataset
                                * rows - a list of rows of data for the current page
                                * columns - a list of columns in the dataset
    """
    # Determines the id range and number of pages needed to display the table
    id_range, page_count = get_pagination_id_range(table, page_number)

    # Get a session
    session = m.get_session()

    # Get the object for the table we're working with
    table = getattr(m.Base.classes, table)

    # Query the table for rows within the correct range
    query = session.query(
        table
    ).filter(
        table.id > id_range[0],
        table.id <= id_range[1]
    )

    # Get a DataFrame with the results of the query
    df = pd.read_sql(query.statement, query.session.bind)

    # Convert everything to the correct formats for displaying
    columns = df.columns.tolist()
    rows = table_generator.convert_nans(df.values.tolist())
    median_lat = df.LATITUDE.median()
    median_lon = df.LONGITUDE.median()

    return JsonResponse({
        'columns': columns,
        'rows': rows,
        'pageCount': page_count,
        'lat': median_lat,
        'lon': median_lon
    })
def get_household_members(request, table, person_id):
    """
    get data on members of the same household_ID

    Parameters:
    table(str) - The uuid of the table being requested
    person_id - the id of the person whoose family information is being requested

    Returns:
    JsonResponse (str) - A JSON string containing:
                                                  *data entries related to the person
    """
    # Get a session
    session = m.get_session()

    # Get the object for the table we're working with
    table_id = table
    table = getattr(m.Base.classes, table)

    # Query the table for family information from row with the correct person_id
    query = session.query(
        table.ID_of_Spouse,
        table.Children_name_ID,
        table.Mothers_ID,
        table.Fathers_ID,
        table.Siblings_IDs
    ).filter(
        table.PERSON_ID == person_id
    )
    #get dataframe of query
    df = pd.read_sql(query.statement, query.session.bind)

    columnList = df.columns.values.tolist()
    spouse_id=""
    child_ids=""
    mom_id=""
    dad_id=""
    sib_ids=""
    #get families id information from the dataframe
    for row in df.itertuples():
        spouse_id = row[columnList.index('ID_of_Spouse')+1]
        child_ids = row[columnList.index('Children_name_ID')+1]
        mom_id = row[columnList.index('Mothers_ID')+1]
        dad_id = row[columnList.index('Fathers_ID')+1]
        sib_ids = row[columnList.index('Siblings_IDs')+1]
    childlist=[]
    if child_ids != None:
        childlist = child_ids.split('; ')
    siblist=[]
    if sib_ids != None:
        siblist = sib_ids.split('; ')
    #query the table for rows corresponding to this person and their family
    query = session.query(
        table
    ).filter(
        or_(
            table.PERSON_ID == person_id,
            table.PERSON_ID == mom_id,
            table.PERSON_ID == dad_id,
            table.PERSON_ID == spouse_id,
            table.PERSON_ID.in_(childlist),
            table.PERSON_ID.in_(siblist)
        )
    )
    df = pd.read_sql(query.statement, query.session.bind)
    #return nescessary data
    return JsonResponse({
        'data':df.to_json(),
        'numEntries': len(df.index)
    })

def get_joined_dataset(request,table,page_number):
    """
    get joined data for specific page of dataset
    Parameters:
    table (str) - The uuid of the table being requested
    page_number (int) - The page being requested
    Returns:
    JsonResponse (str) - A JSON string containing:
                                                  *uuids of databases joined to this one
                                                  *data from those databases joined to entries on the current page
    """
    # Determines the id range and number of pages needed to display the table
    id_range, page_count = get_pagination_id_range(table, page_number)

    # Get a session
    session = m.get_session()

    # Get the object for the table we're working with
    table_id = table
    table = getattr(m.Base.classes, table)

    # Query the table for rows within the correct range
    query = session.query(
        table
    ).filter(
        table.id > id_range[0],
        table.id <= id_range[1]
    )

    # Get a DataFrame with the results of the query
    df = pd.read_sql(query.statement, query.session.bind)

    #query for joins in which the table is the main dataset
    join_query = session.query(
        m.DATASET_JOINS
    ).filter(
        m.DATASET_JOINS.dataset1_uuid == table_id
    )
    #get dataframe of join query
    join_df = pd.read_sql(join_query.statement, join_query.session.bind)
    columnList = join_df.columns.values.tolist()
    joined_results = []
    joined_database_ids = []
    #for every dataset joined to this one
    for row in join_df.itertuples():
        i1_name = row[columnList.index('index1_name')+1]
        d2_id = row[columnList.index('dataset2_uuid')+1]
        joined_database_ids.append(d2_id)
        curr_db = d2_id
        i2_name = row[columnList.index('index2_name')+1]
        #query for the join key from the main table
        d1_key_query = session.query(
            m.DATASET_KEYS
        ).filter(
            m.DATASET_KEYS.dataset_uuid == table_id,
            m.DATASET_KEYS.index_name == i1_name
        )
        d1_key_df = pd.read_sql(d1_key_query.statement, d1_key_query.session.bind)
        for row in d1_key_df.itertuples():
            cols1= row[3]
        #query for the join key from the joined table
        d2_key_query = session.query(
            m.DATASET_KEYS
        ).filter(
            m.DATASET_KEYS.dataset_uuid == d2_id,
            m.DATASET_KEYS.index_name == i2_name
        )
        d2_key_df = pd.read_sql(d2_key_query.statement, d2_key_query.session.bind)
        for row in d2_key_df.itertuples():
            cols2 = row[3]
        col_list = df.columns.tolist()
        #for every entry on th dataset page
        for row in df.itertuples():
            matchString =""
            #build matching parameter
            for x in cols1:
                sql="SELECT data_type FROM information_schema.columns WHERE table_name = '%s' AND column_name ='%s'" % (d2_id, x)
                typeSql = m.engine.execute(sql)
                for k in typeSql:
                    dt = k[0]
                if dt != 'character varying':
                    matchString = "%s \"%s\"=%s AND" % (matchString,cols2[cols2.index(x)],row[col_list.index(x)+1])
                else:
                    matchString = "%s \"%s\"='%s' AND" % (matchString,cols2[cols2.index(x)],row[col_list.index(x)+1])
            matchString = matchString[:len(matchString)-3]
            #retrieve any entry from the joined dataset that corresponds to this entry
            sql_stmt = "SELECT * FROM mircs.\"%s\" WHERE %s" %(d2_id,matchString)
            result = m.engine.execute(sql_stmt)
            #get result of sql query in the form of a dict and append to the final results
            for j in result:
                rowRes = dict(zip(j.keys(), j))
                rowRes['dataset'] = curr_db
                joined_results.append(rowRes)
    return JsonResponse({
        'joined_database_ids':json.dumps(joined_database_ids),
        'main_dataset_key': cols1,
        'joined_dataset_key':cols2,
        'data':json.dumps(joined_results)})


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
    Returns JSON containing a list of table keys that have been added for a
    particular dataset

    Parameters:
    table (str) - The uuid of the table being requested

    Returns:
    JsonResponse({'keys': keys}) (str) - A JSON string containing a list of keys
    """

    # Get the session
    session = m.get_session()
    # Get the keys from the requested table ???
    query = session.query(
        m.DATASET_KEYS
    ).filter(
        m.DATASET_KEYS.dataset_uuid == table
    )
    # Close the session
    session.close()
    # Get the tabley keys
    df = pd.read_sql(query.statement, query.session.bind)

    # Append and return the keys as JSON
    keys = []
    for index, row in df.iterrows():
        keys.append([row['index_name'], row['dataset_columns']])
    return JsonResponse({'keys': keys})


def get_dataset_geojson(request, table, page_number):
    """
    Returns geojson created from the geospatial columns of a given page of a table
    """
    # Get the range of database IDs included in the current page of data as well
    # as the total number of pages
    id_range, page_count = get_pagination_id_range(table, page_number)

    # Get a session
    session = m.get_session()

    t = getattr(m.Base.classes, table)

    # Get geospatial columns
    geo = m.GEOSPATIAL_COLUMNS
    geospatial_columns = session.query(geo.column).filter(geo.dataset_uuid == table).all()
    geo_column_objects = []
    geo_column_names = []
    # Create the geospatial object from the columns
    for col in geospatial_columns:
        geo_column_objects.append(geofunc.ST_AsGeoJSON(getattr(t, col[0])))
        geo_column_names.append(col[0])

    # build up geospatial select functions
    # Note: we're just grabbing the first geospatial column right now. it is explicitly labeled 'geometry'
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

def download_dataset(request, table):
    """
    Download full database table as .csv file
    Parameters:
    table (str) - the name of the table to be displayed. This should be a UUID
    """

    # Get a session
    session = m.get_session()
    # Get the name of the file used to create the csv file being returned
    file_name = str(session.query(
        m.DATASETS.original_filename
    ).filter(
        m.DATASETS.uuid == table
    ).one()[0])  # This returns a list containing a single element(original_filename)
                 # The [0] gets the filename out of the list
    session.close

    db = Session().connection()

    #Create pandas dataframe from table
    df = pd.read_sql("SELECT * FROM " + schema + ".\"" + table + "\"",
                     db, params={'schema': schema, 'table': table})

    #content_type tells browser that file is csv
    response = HttpResponse(content_type='text/csv')
    #Content-Disposition tells browser name of file to be downloaded
    response['Content-Disposition'] = 'attachment; filename = export_%s'%file_name
    #convert dataframe to csv
    df.to_csv(response, index=False)

    return response

def test_response(request):
    """
    Test function for returns
    """
    return HttpResponse('yay')


def convert_time_columns(df, datetime_identifiers=['time', 'date']):
    """
    Find date columns based on name and convert them to pandas datetime64 objects

    Parameters:
    df (pandas.DataFrame) - The dataframe to be converted
    datetime_identifiers (list) - optional. A list of possible datetime column names
                                  NOT case sensitive.

    Retrun:
    df (pandas.DataFrame) - Return the dataframe with datetime columns converted
    """
    for c in df.columns:
        for d in datetime_identifiers:
            if d in c.lower():
                df[c] = pd.to_datetime(df[c])
    return df

def get_pagination_id_range(table, page_number):
    """
    Determine the range of IDs included in a specific page of data. Pages are
    defined as n * settings.DATASET_ITEMS_PER_PAGE to n * (settings.DATASET_ITEMS_PER_PAGE + 1)
    where n is the page_number

    Parameters:
    page_number (int) - The requested page number

    Returns:
    id_range (tuple) - The start and end of the range of database IDs included
                       in the requested page
    page_count (int) - The total number of pages available in the dataset.
                       n / settings.DATASET_ITEMS_PER_PAGE where n is
                       the total number of rows in the dataset
    """
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

def create_df_from_upload(request):
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

    return df

def Session():
    """
    Creates and returns an sqlalchemy session mapped to django orm's models
    this is no longer used meaningfully since the django orm has been fully replaced
    """
    from aldjemy.core import get_engine
    # Get the engine from aldjemy
    engine = get_engine()
    # Create the session with tyhe engine
    _Session = sessionmaker(bind=engine)
    return _Session()