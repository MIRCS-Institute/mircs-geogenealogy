$( document ).ready(function() {
  $('#csvUploadForm #id_csv_file').change( function() {
    var formData = new FormData($('#csvUploadForm')[0]);
    console.log(formData);
    $.ajax({
      url: 'store_csv',
      type: 'POST',
      data: formData,
      async: false,
      cache: false,
      contentType: false,
      processData: false,
      success: function(data) {
        populateDataTable($('#uploadedDataTable'), data['columns'], data['rows'])
      }
    });
    return false;
  });
})

function populateDataTable(tableElement, columns, rows) {
  // Iterate columns and create table headers for each
  var headerRow = $('<tr></tr>');
  for(var i=0; i<columns.length; i++) {
    headerRow.append('<th>' + columns[i] + '</th>');
  }
  tableElement.append(headerRow);

  // Iterate rows of data and create table rows for each
  for(var i=0; i<rows.length; i++) {
    // step through rows of data, convert each to an html table row, append to the table
    tableElement.append(createTableRow(rows[i]));
  }
}

function createTableRow(dataRow) {
  var tableRow = $('<tr></tr>');
  for(var i=0; i<dataRow.length; i++) {
    // Create a table element for every cell
    tableRow.append('<td>' + dataRow[i] + '</td>');
  }
  return tableRow;
}