$(document).ready(function() {
  $('#fileUploadForm #id_file_upload').change( function() {
    $('.dimmer').dimmer('show', function(){
      //Get form data
      var formData = new FormData($('#fileUploadForm')[0]);
      console.log(formData);
      $.ajax({
        url: '/store_file',
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
            data['rows']
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

          $('[name="ignored_cols"]').change(function(event) {
            var num_ign = $('[name="ignored_cols"]').val().length;

            var conf_range = []; // Gengerate confidence range
            for (var i = 1; i < data['columns'].length - num_ign; i++)
              conf_range.push(i);
            var num_ucols = $('[name="num_ucols"]');
            num_ucols.html('');
            conf_range.forEach(function(el) {
              num_ucols.append("<option>" + el + "</option>");
            });
            num_ucols.dropdown('set selected', conf_range[(conf_range.length / 2) - num_ign]);
          });

          var ign_cols = $('[name="ignored_cols"]');
          data['columns'].forEach(function(el) {
            ign_cols.append("<option>" + el + "</option>");
          });

          var conf_range = []; // Gengerate confidence range
          for (var i = 1; i < data['columns'].length; i++)
            conf_range.push(i);

          var num_ucols = $('[name="num_ucols"]');
          conf_range.forEach(function(el) {
            num_ucols.append("<option>" + el + "</option>");
          });

          ign_cols.dropdown();
          num_ucols.dropdown('set selected', conf_range[conf_range.length / 2]);

        }
      });
      $('.dimmer').dimmer('hide');
    });
    return false;
  });
});
