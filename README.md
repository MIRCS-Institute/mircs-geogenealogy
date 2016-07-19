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
2. Run the command `python manage.py runserver 0.0.0.0:8000`

#Current Functionality
##1. Upload a file (CSV or Excel)
1. Click "Upload File"
2. On the new page, click "Choose..."
3. Select the Excel or CSV to upload
4. Wait for the page to load a preview of the data
5. Click "Add GeoSpatial Columns"
6. Select the Longitude and Latitude columns
7. Scroll to the bottom of the page
8. Click "Submit"

##2. Append data to a dataset


##3. Pick a key


##4. Create a Join


##5. View the datatset
1. On the home page Click "View" for the dataset to view a map and the table of data
