

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
  function buildPagePicker(parentElement, pageCount, selected)
  {
    //Number of pages to display
    pageCount = Number(pageCount);
    //Selected page
    selected = Number(selected);

    //-----Build pagination bar-----

	//Settings
	var pad = 4; //The number of page numbers shown between the start/end of the list and the elipses during truncation
	var buttons = 19; //Total number of page number buttons + elipses. Should be an odd number

    //Add 'Previous' Button
    parentElement.append($('<a id="previousPage" class="item">Previous</a>'));

    //Add page numbers
	if(pageCount < buttons) //If all numbers can fit with no truncation (elipses)
	{
		for(var i=0; i<=pageCount; i++)
		{
			var linkElement = $('<a class="item">' + i + '</a>');
			if(i === selected)
			{
				linkElement.addClass('active');
			}
			parentElement.append(linkElement);
		}
	}
	else //If truncation is necessary
	{
		var index = 0; //Current page number
		//b = current button index
		for(var b=0; b < buttons; b++)
		{
			if(b == pad && selected > (buttons-1)/2) //At the place where the first (...) would go, if the selected page is in an appropriate place
			{
				parentElement.append($('<div class="disabled item">...</div>')); //Add elipses
				if(selected >= pageCount-(buttons-pad-pad-1)) //If a second truncation will not be necessary...
				{
					index = pageCount-(buttons-pad-2); //...Set index to count up to the last page
				}
				else
				{
					index = selected-(buttons-pad-pad-3)/2; //Otherwise, set index to center the view around the selected page
				}
			}
			//At the place where the second (...) would go, if this second truncation is necessary to reach the last page
			else if(b == buttons-pad-1 && selected < pageCount-(buttons-1)/2  && index !== pageCount-pad)
			{
				parentElement.append($('<div class="disabled item">...</div>')); //Add the elipses
				index = pageCount-(pad-1); //Set index to count to the final page for the last button
			}
			else //If not truncating, add the button for this page number
			{
				var linkElement = $('<a class="item">' + index + '</a>');
				if(index === selected)
				{
					linkElement.addClass('active');
				}
				parentElement.append(linkElement);
				index += 1;
			}
		}
	}

	//Add 'Next' Button
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
        popupText += "<strong class='coloured'>"+val  + "</strong>: " + feature.properties[val] +"<br/>";
      });
      popupText += "<button class='ui button'>Preeess mee</button>"
      layer.bindPopup(popupText, pOptions);

    }
  }
});
