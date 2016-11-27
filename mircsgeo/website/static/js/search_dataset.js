$( document ).ready(function() {
	$.getJSON('/get_dataset_columns/' + getTableFromURL(), function(data) {
		create_checkboxes(data['columns']); //Get the columns of the current table and use it to create the checkboxes
	});


	function create_checkboxes(columns){ //Add checkboxes to page, one for each dataset column
		var thing = $('#checkboxes');
		for(var i=0; i < columns.length; i++)
		{
			thing.append('<li><div class="ui checkbox">'
						+'<input type="checkbox" name="'+columns[i]+'" onclick="addForm(this);">'
						+'<label>'+columns[i]+'</label>'
						+'</div></li>');
		}
	}

	function getTableFromURL() {
		//Split URL on '/'
		var parts = window.location.href.split('/');
		for(var i=0; i<parts.length; i++) {
			//Find view in url and return
			if(parts[i] === 'search') {
				return parts[i+1];
			}
		}
		return false;
	}

});

function addForm(checkBox) { //Function that runs when a checkbox is clicked
	if (checkBox.checked) { //If the user just checked the box
        var input = document.createElement("input"); //Create a new input element
		input.name = checkBox.name + "_query"; //In post, this data will be located in 'post_data[columnName+"_query"]'
        input.type = "text"; //Text field
        var div = document.createElement("div"); //Create a div to store it in
        div.id = checkBox.name;
        div.innerHTML = "Search for this in " + checkBox.name + ":"; //Label for above the input field
        div.appendChild(input); //Put the input field inside the div
        document.getElementById("inputfields").appendChild(div); //Add it to the html
	} else { //If the user just unchecked the box
		document.getElementById(checkBox.name).remove(); //Remove the input field
	}
}