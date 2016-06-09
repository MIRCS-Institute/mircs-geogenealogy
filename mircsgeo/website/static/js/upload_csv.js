$( document ).ready(function() {
  $('#csvUploadForm #submitButton').click( function() {
    var formData = new FormData($('#csvUploadForm')[0]);
    // var formData =  $('#csvUploadForm').serialize();
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
        console.log(data);
      }
    });
    return false;
  });
})
