function myFunction(a, b) {
  document.getElementById('m_content').innerHTML = "<div class='ui two column very relaxed grid'><div class='column'><p>"+a+"</p></div><div class='column'><p>"+b+"</p></div></div>";
  $('.ui.long.modal')
  .modal('show')
  ;
}
