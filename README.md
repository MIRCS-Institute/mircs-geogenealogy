# mircs-geogenealogy

MIRCS Institute is a nonprofit devoted to the renewal of civil society. It is currently engaging a number of projects in public history, research, and education. The project is to have a publicly accessible web application - basically “Facebook for dead people”, which would serve as a prototype for future development of a robust, scalable, online platform. The developed project will allow a user to browse through the map, populated with historic data with the ability to click on the historic profiles to view more information as well as log in to add more information to the data.

#Dependencies
##System
The system based dependencies needed to run the program are:

1. PostgreSQL
2. PostGIS
3. Python

## Python
The Python libraries used in the program  are:

1. django
2. pandas
3. Jinja2
4. sqlalchemy
5. Aldjemy
6. geoalchemy2
7. psycopg2
8. xlrd

#Starting the Server
1. Navigate to mircsgeo/manage.py
2. Run the command `python manage.py runserver 0.0.0.0:8080`

#Current Functionality
##1. Upload a file (CSV or Excel)
1. Click "Upload File"
2. On the new page, click "Choose file"
3. Select the Excel or CSV to upload
4. Wait for the page to load a preview of the data
5. If dataset contains GeoSpatial data, Click "Add GeoSpatial Columns" and select the Longitude and Latitude columns
6. Scroll to the bottom of the page
7. Click "Submit"

##2. Update data to a dataset
1. On the home page click "Edit" for the dataset to which you want to update data
2. Select the "Update Data" option from the dropdown
3. On the new page, click "Choose file"
4. Select the Excel or CSV to upload
5. Wait for the page to load a preview of the data
6. Create a unique key by which to update, or select 'Import key' to choose a pre-existing one
6. Scroll to the bottom of the page
7. Click "Submit"

##3. Create a key
1. On the home page Click "Edit" for the dataset to which you want to create a key
2. Select the "Add Data Key For Join" option from the dropdown
3. 3. On the new page, select all columns for the key using the dropdown
4. Click "Submit"

##4. Create a Join
1. On the home page click "Edit" for the dataset to which you want to join data
2. Select the "Join Data" option from the dropdown
3. Select the joining dataset
4. Select the main dataset key
5. Select the joining dataset key
6. Click "Submit"

##5. Upload an Image
1. On the home page click "Edit" for the dataset to which you want to upload an image
2. Select the "Add File to an Element" option from the dropdown
3. Select search/filter criteria
4. Search for specific dataset entry
5. Select requested table entry
6. Click 'Upload File'
7. Select the image to upload.

##6. View the datatset
1. On the home page click "View" for the dataset to view a map and the table of data
2. Select a marker or table entry to expand entry information.
3. If joins have been made with the dataset, related entries can be viewed after expanding a specific entry.
4. If files have been uploaded to an entry, they can be downloaded after expanding a specific entry.

##7. Download dataset
1. On the home page click "Download" to download a csv of the dataset including id numbers

#Database
##ERD
![Alt text] (https://github.com/alexetnunes/mircs-geogenealogy/blob/master/db-erd.png)
