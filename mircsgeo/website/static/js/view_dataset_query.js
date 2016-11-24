

$( document ).ready(function() {
  var group = null;
  var map = L.map('dataMap');

  //Initiate map and dataset for display to page
  $.getJSON('/get_dataset_query/' + getTableFromURL() + '/' + column + '/' + query + '/', function(data) {
	insertDatasetPage(data, 0);
    initMap(map, data);
  });
  //Populate map with json data
  $.getJSON('/get_query_geojson/' + getTableFromURL() + '/' + column + '/' + query + '/', function(data) {
    group = populateMap(map, data);
  });

  //Create and poplulate dataset for display on page
  function insertDatasetPage(data, selected) {
    //Grab datatable div
    var dataTable = $('#dataTable');
    dataTable.empty();
    //Populate datatable with data from columns and rows
    populateDataTable(dataTable, data['columns'], data['rows']);
  }
  //Get table data from the URL
  function getTableFromURL() {
    //Split URL on '/'
    var parts = window.location.href.split('/');
    for(var i=0; i<parts.length; i++) {
      //Find search in url and return
      if(parts[i] === 'search') {
        return parts[i+1];
      }
    }
    return false;
  }
  
  //Initialize map
  function initMap(map, data) {
    // .setView([data['lat'], data['lon']], 13)
    //Set to a default view of lat and lon
    var map = map.setView([data['lat'], data['lon']], 13);
    //Use openstreetmap tile layer
    L.tileLayer('http://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png', {
      attribution: '&copy; <a href="http://www.openstreetmap.org/copyright">OpenStreetMap</a>',
      maxZoom: 20}).addTo(map);
    return map;
  }
  //Add data to map
  function populateMap(map, data) {
    //Set up marker display settings
    var geojsonMarkerOptions = {
      radius: 8,
      fillColor: "#FF9639",
      color: "#000",
      weight: 1,
      opacity: 1,
      fillOpacity: 0.8
    };
    //Add each point to map
    var group = L.geoJson(data,{
      onEachFeature: onEachFeature,
      pointToLayer: function (feature, latlng) {
          return L.circleMarker(latlng, geojsonMarkerOptions);
    }}).addTo(map);
    map.fitBounds(group.getBounds());
    return group;
  }
  //Function for displaying popup on map features
  function onEachFeature(feature, layer) {
    var pOptions = {
      maxHeight: 80
    };
    if (feature.properties) {
      //Popup some text for each feature. Grabbed from feature.key. Val is the value from the feature
      var popupText = "";
      $.each(feature.keys, function(key, val){
        popupText += "<strong>"+val  + "</strong>: " + feature.properties[val] +"<br/>";
      });
      layer.bindPopup(popupText, pOptions);

    }
  }
});
