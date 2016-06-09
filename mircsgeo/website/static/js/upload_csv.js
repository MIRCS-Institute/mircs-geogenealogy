var selected_primary_key_cols = [];

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
      dataType: 'json',
      success: function(data) {
        populateDataTable($('#uploadedDataTable'), data['columns'], data['rows']);
        $('#uploadedDataTable th').mouseover(function() {
          var thClass = $(this).attr('class').split(' ')[0];
          $('.'+thClass).addClass('active');
        });
        $('#uploadedDataTable th').mouseout(function() {
          var thClass = $(this).attr('class').split(' ')[0];
          $('.'+thClass).removeClass('active');
        });
        $('#uploadedDataTable th').click(function() {
          var thClass = $(this).attr('class').split(' ')[0];
          var key = $(this).text();
          var key_index = $.inArray(key, selected_primary_key_cols);

          if(key_index == -1) {
            // This key isn't selected yet
            $('.'+thClass).addClass('selected');
            selected_primary_key_cols.push(key);
          } else {
            // This key was already selected
            $('.'+thClass).removeClass('selected');
            selected_primary_key_cols.splice(key_index, 1);
          }
          console.log(selected_primary_key_cols);
        });
      }
    });
    return false;
  });
})

function populateDataTable(tableElement, columns, rows) {
  tableElement.empty();
  // Iterate columns and create table headers for each
  var headerRow = $('<tr></tr>');
  for(var i=0; i<columns.length; i++) {
    headerRow.append('<th class="col_' + i + '">' + columns[i] + '</th>');
  }
  tableElement.append($('<thead></thead>').append(headerRow));

  var tableBody = $('<tbody></tbody>');
  // Iterate rows of data and create table rows for each
  for(var i=0; i<rows.length; i++) {
    // step through rows of data, convert each to an html table row, append to the table
    tableBody.append(createTableRow(rows[i]));
  }
  tableElement.append(tableBody);
}

function createTableRow(dataRow) {
  var tableRow = $('<tr></tr>');
  for(var i=0; i<dataRow.length; i++) {
    // Create a table element for every cell
    tableRow.append('<td class="col_' + i + '">' + dataRow[i] + '</td>');
  }
  return tableRow;
}
