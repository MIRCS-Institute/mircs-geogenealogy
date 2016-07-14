$(document).ready(function(){
  $('select').change(function(){
    var table  = $(this).val()
    $.get('/get_dataset_keys/'+table, function(data){
      console.log(data);
    });
  });
});
