$( document ).ready(function() {
  $('#csv_upload_form').submit( function() {
    console.log("HERE");
    var formData = new FormData($(this)[0]);
    console.log(formData);
    $.post( 'upload_csv', formData, function(data) {
        console.log(data);
      },
      'json' // I expect a JSON response
    );
    return false;
  });
})
