$(document).ready(function() {

  $('select').dropdown()

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

          var key_cols = $('[name="key"]');
          data['columns'].forEach(function(el) {
            key_cols.append("<option value=\"" + el.replace(' ', '_') + "\">" + el + "</option>");
          });

          key_cols.change(function(e) {
            var key = key_cols.val();
            console.log(key);
            if (key == null)
              $('[type="submit"]').prop('disabled', true);
            else
              $('[type="submit"]').prop('disabled', false);
          });
          key_cols.dropdown();
        }
      });
      $('.dimmer').dimmer('hide');
    });
    return false;
  });

  $('#import').click(function() {
    $('.ui.modal.import').modal('show');
  });

  $('#submit_import').click(function() {
    columns = $('#key').val();
    columns = columns.replace(/\'/g, '"');
    columns = JSON.parse(columns);
    $('#unique_key').dropdown('clear');
    $('#unique_key').dropdown('set selected', columns);

    $('.ui.modal.import').modal('hide');
  });

  $('#save').click(function() {
    var href = window.location.href;
    href = href.split('/');
    uuid = href[href.length - 1]
    var getCookie = function(name) {
      var cookieValue = null;
      if (document.cookie && document.cookie != '') {
        var cookies = document.cookie.split(';');
        for (var i = 0; i < cookies.length; i++) {
          var cookie = jQuery.trim(cookies[i]);
          // Does this cookie string begin with the name we want?
          if (cookie.substring(0, name.length + 1) == (name + '=')) {
            cookieValue = decodeURIComponent(cookie.substring(name.length + 1));
            break;
          }
        }
      }
      return cookieValue;
    }
    var csrftoken = getCookie('csrftoken');
    $.ajaxSetup({
      beforeSend: function(xhr, settings) {
        xhr.setRequestHeader(
          "X-CSRFToken",
          getCookie('csrftoken')
        );
      }
    });
    $.post('/add_dataset_key/' + uuid + '/', {'dataset_columns': $('#unique_key').val()});
  });
});
