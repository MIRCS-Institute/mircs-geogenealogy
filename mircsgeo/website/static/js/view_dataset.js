$( document ).ready(function() {
  $.getJSON('/get_dataset_page/' + getTableFromURL() + '/0/', function(data) {
    populateDataTable($('#dataTable'), data['columns'], data['rows']);
    console.log(data);
  });
});

function getTableFromURL() {
  var parts = window.location.href.split('/');
  for(var i=0; i<parts.length; i++) {
    if(parts[i] === 'view') {
      return parts[i+1]
    }
  }
  return false;
}
