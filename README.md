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
##2. Add geospatial columns
##3. Append data to a dataset
##4. Pick a key
##5. Create a Join
##6. View the datatset
