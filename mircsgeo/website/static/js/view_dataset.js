

$( document ).ready(function() {
  var group = null;
  var map = L.map('dataMap');
  //Initiate map and dataset for display to page
  $.getJSON('/get_dataset_page/' + getTableFromURL() + '/0/', function(data) {
    insertDatasetPage(data, 0);
    initMap(map, data);
  });
  //Populate map with json data
  $.getJSON('/get_dataset_geojson/' + getTableFromURL() + '/0/', function(data) {
    group = populateMap(map, data);
  });

  //Create and poplulate dataset for display on page
  function insertDatasetPage(data, selected) {
    //Grab datatable div
    var dataTable = $('#dataTable');
    //pagePicker for pagination of datatable
    var pagePicker = $('.pagePicker');
    dataTable.empty();
    pagePicker.empty();
    //Populate datatab;e with data from columns and rows
    populateDataTable(dataTable, data['columns'], data['rows']);
    //Build page picker from buildPagePicker function
    buildPagePicker(pagePicker, data['pageCount'], selected);
    pagePicker.children('a.item').click(function(event) {
      var link_value = $(this).text();
      var target_page = link_value;
      if(link_value === 'Previous' || link_value === 'Next') {
        var current_page = Number($(this).siblings('a.item.active').text());
        if(link_value === 'Previous') {
          if(current_page > 0) {
            target_page = -1 + current_page;
          } else {
            target_page = current_page;
          }
        } else if(link_value === 'Next') {
          if(current_page < data['pageCount']) {
            target_page = 1 + current_page;
          } else {
            target_page = current_page;
          }
        }
      }
      //Get map points from get request in url
      $.getJSON('/get_dataset_geojson/' + getTableFromURL() + '/' + target_page + '/', function(data) {
        if(group !== null) {
          group.clearLayers();
        }
        group = populateMap(map, data);
      });
      //Get table data from get request in url
      $.getJSON('/get_dataset_page/' + getTableFromURL() + '/' + target_page + '/', function(data) {
        insertDatasetPage(data, target_page);
      });
    });
  }
  //Get table data from the URL
  function getTableFromURL() {
    //Split URL on '/'
    var parts = window.location.href.split('/');
    for(var i=0; i<parts.length; i++) {
      //Find view in url and return
      if(parts[i] === 'view') {
        return parts[i+1];
      }
    }
    return false;
  }

  //Build page picker for pagination.
  function buildPagePicker(parentElement, pageCount, selected) {
    //Number of pages to display
    pageCount = Number(pageCount);
    //Selected page
    selected = Number(selected);
    //Buttons for pagination
    var startEndButtons = 3;
    var buttonsPerSide = 5;
    //Choose how many buttons to display.
    if(selected < (startEndButtons + buttonsPerSide) || selected > (pageCount - (startEndButtons + buttonsPerSide))) {
      startEndButtons += buttonsPerSide;
    }
    //Create link to previous page labelled as Previous
    parentElement.append($('<a id="previousPage" class="item">Previous</a>'));
    //Iterate through buttons and set active page
    for(var i=0; i<=startEndButtons; i++) {
      var linkElement = $('<a class="item">' + i + '</a>');
      if(i === selected) {
        linkElement.addClass('active');
      }
      parentElement.append(linkElement);
    }
    parentElement.append($('<div class="disabled item">...</div>'));
    if(selected >= (startEndButtons + buttonsPerSide) && selected <= (pageCount - (startEndButtons + buttonsPerSide))) {
      for(var i=-1*buttonsPerSide; i<0; i++) {
        var linkElement = $('<a class="item">' + (selected + i) + '</a>');
        if((selected + i) === selected) {
          linkElement.addClass('active');
        }
        parentElement.append(linkElement);
      }
      //Iterate through buttons and set how many to show on each side of the list, depending on how many pages are displayed
      for(var i=0; i<buttonsPerSide; i++) {
        var linkElement = $('<a class="item">' + (selected + i) + '</a>');
        if((selected + i) === selected) {
          linkElement.addClass('active');
        }
        parentElement.append(linkElement);
      }
      parentElement.append($('<div class="disabled item">...</div>'));
    }
    for(var i=-1*startEndButtons; i<=0; i++) {
      var linkElement = $('<a class="item">' + (i + pageCount) + '</a>');
      if((i + pageCount) === selected) {
        linkElement.addClass('active');
      }
      parentElement.append(linkElement);
    }
    parentElement.append('<a id="nextPage" class="item">Next</a>');
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
