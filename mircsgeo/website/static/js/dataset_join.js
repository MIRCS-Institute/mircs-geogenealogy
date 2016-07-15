$(document).ready(function(){
  $('select').change(function(){
    var table  = $(this).val();
    var keyField = $(this).attr('data-key');
    $.get('/get_dataset_keys/'+table, function(data){
      $.each(data['keys'], function(key,val){
        var html = "<option value=\""+val[0]+"\">";
        var len = val[1].length
        $.each(val[1], function(index,col){
          if(index == len-1){
            html += col
          } else {
            html += col+", ";
          }
        });
        html+="</option>";
        $('#'+keyField).append(html);
      });
    });
  });
});
