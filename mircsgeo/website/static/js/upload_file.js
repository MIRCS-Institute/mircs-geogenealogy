$( document ).ready(function() {
  $('#fileUploadForm #id_file_upload').change( function() {
    $('.dimmer').dimmer('show', function(){
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

          $('#Geocolumns').click(function( event ) {
            if(!$('#GeospatialCol_name').length){
              //generate the form
              var form = $("<form class='ui form geospatialColumnForm'></form>")
              form.append($("<label for='GeospatialCol_name'> GeoSpatial Column Name: <label/>"));
              var GeospatialCol_name = $("<div class=\"field\"><input type='text' id='GeospatialCol_name' name='name' value='geom'></div>");
              form.append(GeospatialCol_name);


              var lat_col = $( "<select id='lat_col' name='lat_col'></select>");
              var lon_col = $("<select id='lon_col' name='lon_col'></select>");

              $.each(data['columns'],function(key,value){
                lat_col.append($("<option></option>").attr("value",value).text(value));
                lon_col.append($("<option></option>").attr("value",value).text(value));
              });

              form.append($("<label for='lat_col'> Select Latitude</label>"));
              form.append($('<div class=\"field\"></div>').append(lat_col));
              form.append($("<label for='lon_col'> Select Longitude</label>"));
              form.append($('<div class=\"field\"></div>').append(lon_col));

              form.append($("<label for='srid'> SRID: </label>"));
              var srid = $("<div class=\"field\"><input type='text' id='srid' name='srid' value='4326'></input></div>");
              form.append(srid);

              var GeoCol_type = $( "<input></input>",{'type':'hidden', 'id': 'GeoCol_type', 'name': 'type', 'value': 'latlon'});
              form.append(GeoCol_type);

              $(form).appendTo("#geospatialColumnsContainer").hide().fadeIn('slow');
              $('select').dropdown();
            }

          });
        }
      });
      $('.dimmer').dimmer('hide');
    });
    return false;
  });
});
