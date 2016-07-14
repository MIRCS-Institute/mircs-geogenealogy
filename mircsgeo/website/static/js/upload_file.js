$( document ).ready(function() {

  $('#fileUploadForm #id_file_upload').change( function() {
    var formData = new FormData($('#fileUploadForm')[0]);
    console.log(formData);
    $.ajax({
      url: 'store_file',
      type: 'POST',
      data: formData,
      async: false,
      cache: false,
      contentType: false,
      processData: false,
      dataType: 'json',
      success: function(data) {
        var dataTable = $('#uploadedDataTable');
        populateDataTable(
          dataTable,
          data['columns'],
          data['rows'],
          data['datatypes'],
          data['possibleDatatypes']
        );
        $('#primaryKeyPicker').show();
        // Add an event handler to get the entered datatypes from the table and
        // append them to the form before submission
        $('#primaryKeyPicker').find( "#fileUploadForm" ).submit(function( event ) {
          var datatypes = dataTable.find('.ui.dropdown').dropdown('get value');
          var input = $('<input>').attr({'type':'hidden','name':'datatypes'}).val(datatypes);
          $(this).append(input);

          var geospatial_columns = $("#geospatialColumnsContainer").find('.geospatialColumnForm');
          geospatial_col_return = [];
          for(var i=0; i<geospatial_columns.length; i++) {
            geospatial_col_return.push($(geospatial_columns[i]).serialize());
          }
          var input = $('<input>').attr({'type':'hidden','name':'geospatial_columns'}).val(geospatial_col_return);
          $(this).append(input);
        });

        $('#Geocolumns').click(function(event ){
          //generate the form
          var form = $("<form class='ui form geospatialColumnForm'></form>")
          form.append($("<label for='GeospatialCol_name'> GeoSpatial Column Name: <label/>"));
          var GeospatialCol_name = $("<input type='text' id='GeospatialCol_name' name='name' value='geom'>");
          form.append(GeospatialCol_name);


          var lat_col = $( "<select id='lat_col' name='lat_col'></select>");
          var lon_col = $("<select id='lon_col' name='lon_col'></select>");

          $.each(data['columns'],function(key,value){
            lat_col.append($("<option></option>").attr("value",value).text(value));
            lon_col.append($("<option></option>").attr("value",value).text(value));
          });

          form.append($("<label for='lat_col'> Select Latitude</label>"));
          form.append(lat_col);
          form.append($("<label for='lon_col'> Select Longitude</label>"));
          form.append(lon_col);

          form.append($("<label for='srid'> SRID: </label>"));
          var srid = $("<input type='text' id='srid' name='srid' value='4326'></input>");
          form.append(srid);

          var GeoCol_type = $( "<input></input>",{'type':'hidden', 'id': 'GeoCol_type', 'name': 'type', 'value': 'latlon'});
          form.append(GeoCol_type);

          $("#geospatialColumnsContainer").append(form);

        });
      }
    });
    return false;
  });
})

function populateDataTable(tableElement, columns, rows, datatypes, possibleDatatypes) {
  console.log(datatypes);
  console.log(possibleDatatypes);
  tableElement.empty();
  // Iterate columns and create table headers for each
  var headerRow = $('<tr></tr>');
  for(var i=0; i<columns.length; i++) {
    headerRow.append('<th class="col_' + i + '">' + columns[i] + '</th>');
  }
  tableElement.append($('<thead></thead>').append(headerRow));

  // Iterate the datatypes and create table headers for each
  var headerRow = $('<tr id="datatypes"></tr>');
  for(var i=0; i<datatypes.length; i++) {
    var datatypePicker = createDatatypePicker(datatypes[i], possibleDatatypes);
    var header = $('<th class="col_' + i + '"></th>').append(datatypePicker);
    headerRow.append(header);
  }
  tableElement.append($('<thead></thead>').append(headerRow));
  $('.ui.dropdown').dropdown();

  var tableBody = $('<tbody></tbody>');
  // Iterate rows of data and create table rows for each
  for(var i=0; i<rows.length; i++) {
    // step through rows of data, convert each to an html table row, append to the table
    tableBody.append(createTableRow(rows[i]));
  }
  tableElement.append(tableBody);
}

function createDatatypePicker(currentDatatype, possibleDatatypes) {
  var pickerDiv = $('<div class="ui selection dropdown"></div>')
                    .append('<input type="hidden" value="' + currentDatatype + '">')
                    .append('<div class="text">' + currentDatatype + '</div>');

  var menu = $('<div class="menu"></div>');

  for(var i=0; i<possibleDatatypes.length; i++) {
    menu.append('<div class="item" data-value="' + possibleDatatypes[i]
                      +'">' + possibleDatatypes[i] + '</div>');
  }
  return pickerDiv.append(menu);
}

function createTableRow(dataRow) {
  var tableRow = $('<tr></tr>');
  for(var i=0; i<dataRow.length; i++) {
    // Create a table element for every cell
    tableRow.append('<td class="col_' + i + '">' + dataRow[i] + '</td>');
  }
  return tableRow;
}
