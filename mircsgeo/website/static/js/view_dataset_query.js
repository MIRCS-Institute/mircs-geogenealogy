var currentRow = -1; //Gets updated when a row is clicked on
$( document ).ready(function() {
	
	$('#fileUploadForm #id_file_upload').change( function() {
		$('.dimmer').dimmer('show', function(){
		  //Get form data
		  var formData = new FormData($('#fileUploadForm')[0]);
		  console.log(formData);
		  $.ajax({
			url: '/upload_image/' + getTableFromURL() + '/' + currentRow + '/',
			type: 'POST',
			data: formData,
			async: false,
			cache: false,
			contentType: false,
			processData: false,
			dataType: 'image/png',
			success: function(data) {
				if(data['result'] === true)
					alert("File successfully added!");
				else
					alert("Upload failed...");
			}
		  });
		  $('.dimmer').dimmer('hide');
		});
		return false;
	});
	
	var group = null;
  
	var req = getTableFromURL();
	for(var i=0; i < queries.length; i++)
	{
		req += '/' + queries[i][0] + '/' + queries[i][1];
	}
	req += '/';

	//Initiate dataset for display to page
	$.getJSON('/get_dataset_query/' + req, function(data) {
		if(data['valid']){
			if(data['rows'].length > 0)
				insertDatasetPage(data, 0);
			else
				noResults();
		}
		else
			noResults();
	});

	//Create and poplulate dataset for display on page
	function insertDatasetPage(data, selected) {
		//Grab datatable div
		var dataTable = $('#dataTable');
		dataTable.empty();
		//Populate datatable with data from columns and rows
		populateDataTable(dataTable, data['columns'], data['rows']);
	}
  
	//If the query had no results
	function noResults(){
		var div = document.createElement("div");
        div.innerHTML = "No results.";
		document.getElementById("dataTable").appendChild(div);
	}
	

});

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

//Called from createTable, opens modal for clicking on a row
function clickRow(dataRowString)
{
	var dataRow = dataRowString.split(",");
	currentRow = dataRow[0];
	$.getJSON('/get_dataset_columns/' + getTableFromURL(), function(data) {
		viewRowModal(dataRow, data['columns']);
	});
}

function showRowModal(left, right){
	createModal(left, right);
}

function createModal(a, b) {
	document.getElementById('m_content').innerHTML = "<div class='ui two column very relaxed grid'><div class='column'><p>"+a+"</p></div><div class='column'><p>"+b+"</p></div></div>";
	$('.ui.long.modal').modal('show');
}