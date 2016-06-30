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
        });
      }
    });
    return false;
  });
})
