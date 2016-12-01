function createModal(a, b,id,table) {
  document.getElementById('m_content').innerHTML = "<div class='ui two column very relaxed grid'><div class='column'><p>"+a+"</p></div><div class='column'><p>"+b+"</p></div><div/><div class='ui divider'><div/>";

  $.getJSON('/get_connected_resources/'+id+'/'+table ,function(data){
      //console.log(JSON.stringify(data));
      files = data['file_names'];
      var fileString = "<h3 class ='ui header'>files connected to this entry</h3>";
      for(var i in files){
        if(files[i] == null){
          fileString = fileString + "NULL ENTRY<br/>"
          continue;
        }
        location_list = files[i].split('/');
        //console.log(location_list);
        fileString= fileString + "<a href='/download_file/"+location_list[location_list.length-1]+"' download>"+location_list[location_list.length-1]+"</a><br/>";
      }
      document.getElementById('files').innerHTML = fileString + '<br/>';
  });


  $('.ui.long.modal').modal('show');
}
