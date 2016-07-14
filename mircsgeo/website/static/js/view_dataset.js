$( document ).ready(function() {
  $.getJSON('/get_dataset_page/' + getTableFromURL() + '/0/', function(data) {
    insertDatasetPage(data, 0);
  });
});

function insertDatasetPage(data, selected) {
  var dataTable = $('#dataTable');
  var pagePicker = $('.pagePicker');
  dataTable.empty();
  pagePicker.empty();
  populateDataTable(dataTable, data['columns'], data['rows']);
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
        console.log(current_page);
        console.log(data['pageCount']);
        if(current_page < data['pageCount']) {
          target_page = 1 + current_page;
        } else {
          target_page = current_page;
        }
      }
    }
    $.getJSON('/get_dataset_page/' + getTableFromURL() + '/' + target_page + '/', function(data) {
      insertDatasetPage(data, target_page);
    });
  });
}

function getTableFromURL() {
  var parts = window.location.href.split('/');
  for(var i=0; i<parts.length; i++) {
    if(parts[i] === 'view') {
      return parts[i+1];
    }
  }
  return false;
}

function buildPagePicker(parentElement, pageCount, selected) {
  pageCount = Number(pageCount);
  selected = Number(selected);
  var startEndButtons = 3;
  var buttonsPerSide = 5;
  if(selected < (startEndButtons + buttonsPerSide) || selected > (pageCount - (startEndButtons + buttonsPerSide))) {
    startEndButtons += buttonsPerSide;
  }
  parentElement.append($('<a id="previousPage" class="item">Previous</a>'));
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
