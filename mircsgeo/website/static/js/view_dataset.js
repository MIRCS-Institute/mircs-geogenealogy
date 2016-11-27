

$( document ).ready(function() {
  var group = null;
  var map = L.map('dataMap');
  //Initiate map and dataset for display to page
  $.getJSON('/get_dataset_page/' + getTableFromURL() + '/0/', function(data) {
    insertDatasetPage(data, 0);
    initMap(map, data);
  });
  //example of getting data from datasets joined with this one
  $.getJSON('/get_joined_dataset/' + getTableFromURL() + '/0/', function(data) {
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
      //example of getting data from datasets joined with this one
      $.getJSON('/get_joined_dataset/' + getTableFromURL() + '/' + target_page + '/', function(data) {
        //window.alert(JSON.stringify(data));
      });
      //Get table data from get request in url
      $.getJSON('/get_dataset_page/' + getTableFromURL() + '/' + target_page + '/', function(data) {
        insertDatasetPage(data, target_page);
      });
    });
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
      fillColor: "#FF2955",
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
  ids=[];
  lefts=[];
  rights=[];
  //Function for displaying popup on map features
  function onEachFeature(feature, layer) {
    id="";
    var pOptions = {
      maxHeight: 400
    };
    if (feature.properties) {
      //Popup some text for each feature. Grabbed from feature.key. Val is the value from the feature
      var popupText = ""
      count = 0;
      left = "";
      right = "";
      $.each(feature.keys, function(key, val){
        if (count == 2 || count == 7 || count == 11 || count == 12){
          popupText += "<font color='purple'><strong>"+ val + "</strong></font>: " + '&nbsp;&nbsp;' + feature.properties[val] +"<br/>";
        }
        if(val==='id'){
            ids.push(feature.properties[val]+"");
        }
        count++;
        left += "<font color='purple' class='label'>" + val + "</font><br/>";
        right += "<font class='values'>"+feature.properties[val] +"</font><br/>";
      });
      left+="<div><input class='ui button blue' type='button' value='view joined data entry' onClick= 'viewJoinedInfo(getTableFromURL())'></div>";
      lefts.push(left);
      rights.push(right);
      id=""
      splited = popupText.split("<br/>");
      for(var l in splited){
        ind = splited[l].search("</strong>");
        if(splited[l].substring(ind-3,ind)===">id"){
          splitedA = splited[l].split("&nbsp;&nbsp;");
          id=splitedA[1];
          //console.log(popupText[popupText.search("<font color='purple'><strong>id</strong></font>: &nbsp;&nbsp;")]);
          popupText += "<div id ='detail'><input id ='in' class='ui button green' type='button' onClick= 'show_modal("+id+")' value='Detail'></div>";
        }
      }
      layer.bindPopup(popupText, pOptions);
    }
  }
});
function show_modal(id){
  myFunction(lefts[ids.indexOf(id.toString())],rights[ids.indexOf(id.toString())]);
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
//function for viewing data on joined entry
function viewJoinedInfo(tabUrl){
  //example of getting data from datasets joined with this one
  $.getJSON('/get_joined_dataset/' + tabUrl + '/0/', function(data) {
    left = "";
    right = "";
    m_cont ="<div class='ui very relaxed grid'>";
    labels = document.getElementsByClassName('label');
    labelB=[];
    for (var k in labels){
      labelB.push(labels[k].textContent);
    }
    values = document.getElementsByClassName('values');
    valuesB=[];
    for (var k in values){
      valuesB.push(values[k].textContent);
    }
    var joined_data = data.data;
    var main_key = data.main_dataset_key;
    var joined_key = data.joined_dataset_key;
    var ds="";
    var pid = "";
    var isPersonProfile = false;
    joined_json = JSON.parse(joined_data);
    for(var i in joined_json){
      for (var j in main_key){
        var match_val = valuesB[labelB.indexOf(main_key[j])];
        if(joined_json[i][main_key[j]].toString() === match_val.toString()){
          m_cont+="<div class='two column row'>";
          left="";
          right="";
          for(var key in joined_json[i]){
            if(key == 'Household_ID'){
              isPersonProfile = true;
              pid = joined_json[i]['PERSON_ID'];
            }
            if(key != 'dataset'){
              left += "<font color='purple' class='label'>" + key + "</font><br/>";
              right += "<font class='values'>"+joined_json[i][key]+"</font><br/>";
            }
            else{
              ds=joined_json[i][key];
            }
          }
          if(isPersonProfile == true){
            right+= "<div><input class='ui button green' type='button' value='view family members' onClick= 'viewHouseholdMembers(\""+ds.toString()+"\",\""+pid.toString()+"\")'></div>";
          }
          left+="<div><input class='ui button blue' type='button' value='view joined data entry' onClick= 'viewJoinedInfo(\""+ds.toString()+"\")'></div>";
          m_cont+="<div class='column'><p>"+left+"</p></div><div class='column'><p>"+right+"</p></div></div>";
        }
      }
    }
    m_cont+="</div>"
    document.getElementById('m_content').innerHTML = m_cont;
    $('.ui.long.modal')
    .modal('refresh');
  });
}

//function for viewing family members of a particular person_id
function viewHouseholdMembers(ds,pid){
  //get data for family members
  $.getJSON('/get_household_members/'+ds+'/'+pid+'/', function(data) {
    var family_data = data.data;
    var numEntries = data.numEntries;
    left = "";
    right = "";
    //define modal content
    m_cont ="<div class='ui accordion'>";
    person_index ="";
    var json_data = JSON.parse(family_data );
    //find data entry associated the person_id
    for(i=0;i<numEntries;i=i+1){
      if(json_data['PERSON_ID'][i]==pid){
        person_index = i;
      }
    }
    sn="";
    gn="";
    spouse_id="";
    mothers_id="";
    children_ids=[];
    fathers_id="";
    sibling_ids=[];
    left = "";
    right = "";
    for(var j in json_data){
      //find information on their relations
      if(j=='Surname'){
        sn=json_data[j][person_index];
      }
      else if(j=='Given_Name'){
        gn=json_data[j][person_index];
      }
      else if(j=='ID_of_Spouse'){
        spouse_id=json_data[j][person_index];
      }
      else if(j=='Children_name_ID' && json_data[j][person_index] !=null ){
        children_ids=json_data[j][person_index].split('; ');
      }
      else if(j=='Mothers_ID'){
        mothers_id=json_data[j][person_index];
      }
      else if(j=='Fathers_ID'){
        fathers_id=json_data[j][person_index];
      }
      else if(j=='Siblings_IDs' && json_data[j][person_index] !=null){
        sibling_ids=json_data[j][person_index].split('; ');
      }
      //add information corresponding to person id to modal
      left += "<font color='purple' class='label'>" + j + "</font><br/>";
      right += "<font class='values'>"+json_data[j][person_index]+"</font><br/>";
    }
    left+="<div><input class='ui button blue' type='button' value='view joined data entry' onClick= 'viewJoinedInfo(\""+ds.toString()+"\")'></div>";
    m_cont+="<div class='active title'><i class='dropdown icon'></i>"+gn+" "+sn+"</div><div class='active content'><div class='ui very relaxed grid'><div class='two column row'><div class='column'><p>"+left+"</p></div><div class='column'><p>"+right+"</p></div></div></div></div>";
    for(i=0;i<numEntries;i=i+1){
      if(i != person_index){
        drop_title="";
        //find this entries relationship to person id
        if(json_data['PERSON_ID'][i]==spouse_id){
          drop_title="their spouse";
        }else if(json_data['PERSON_ID'][i]==mothers_id){
          drop_title="their mother";
        }else if(json_data['PERSON_ID'][i]==fathers_id){
          drop_title="their father";
        }else if($.inArray(json_data['PERSON_ID'][i].toString(), children_ids) > -1){
          drop_title="one of their children";
        }else if($.inArray(json_data['PERSON_ID'][i].toString(), sibling_ids_ids) > -1){
          drop_title="one of their siblings";
        }
        left = "";
        right = "";
        //add their information to modal
        for(var j in json_data){
          left += "<font color='purple' class='label'>" + j + "</font><br/>";
          right += "<font class='values'>"+json_data[j][i]+"</font><br/>";
        }
        left+="<div><input class='ui button blue' type='button' value='view joined data entry' onClick= 'viewJoinedInfo(\""+ds.toString()+"\")'></div>";
        right+= "<div><input class='ui button green' type='button' value='view family members' onClick= 'viewHouseholdMembers(\""+ds.toString()+"\",\""+json_data['PERSON_ID'][i].toString()+"\")'></div>"
        m_cont+="<div class='title'><i class='dropdown icon'></i>"+drop_title+"</div><div class='content'><div class='ui very relaxed grid'><div class='two column row'><div class='column'><p>"+left+"</p></div><div class='column'><p>"+right+"</p></div></div></div></div>";
      }
    }
    m_cont+="</div>"
    //set content of modal
    document.getElementById('m_content').innerHTML = m_cont;
    $('.ui.accordion')
    .accordion({
      onChange: function(){
        $('.ui.long.modal')
        .modal('refresh');
      }
    });
    $('.ui.long.modal')
    .modal('refresh');
  });
}
