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
        populatePrimaryKeyPicker($('#primary_key'), data['columns']);
        $('select.dropdown').dropdown();
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
        });
      }
    });
    return false;
  });
})

function populatePrimaryKeyPicker(selectElement, columns) {
  selectElement.empty();
  selectElement.append('<option value="">Select Primary Key Columns...</option>');
  $.each(columns, function(k,v){
    selectElement.append('<option value="'+v+'">'+v+'</option>');
  });
}

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
