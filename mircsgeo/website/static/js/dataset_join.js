//Dataset joins
$(document).ready(function(){
  $('select').change(function(){
    var table  = $(this).val();
    var keyField = $(this).attr('data-key');
    //Get keys for dataset
    $.get('/get_dataset_keys/'+table, function(data){
      //For each key in dataset create options for select box
      $.each(data['keys'], function(key,val){
        //Create opening to html option tag
        var html = "<option value=\""+val[0]+"\">";
        var len = val[1].length
        //Check index and either col or col+", " from length of key value
        $.each(val[1], function(index,col){
          if(index == len-1){
            html += col
          } else {
            html += col+", ";
          }
        });
        //Append closing option tag to html
        html+="</option>";
        //Append html to keyfield
        $('#'+keyField).append(html);
      });
    });
  });
});
