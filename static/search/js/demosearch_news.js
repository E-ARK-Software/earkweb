var blobField = 'body';
var titleField = 'url';
var bytesField = 'size';
var typeField = 'url';
var dateField = 'datePublished';
var rows = 10;

$(function() {
  $("#from").datepicker({
    dateFormat: "yy-mm-dd",
    changeYear: true,
    onClose: function( selectedDate ) {
      $( "#to" ).datepicker( "option", "minDate", selectedDate );
    }
  });
  $("#to").datepicker({
    dateFormat: "yy-mm-dd",
    changeYear: true,
    onClose: function( selectedDate ) {
      $( "#from" ).datepicker( "option", "maxDate", selectedDate );
    }
  });
});

function callback(data) {
  //var lilyEndpoint = 'http://localhost:12060/repository/record/';
  var lilyEndpoint = 'http://earkdev.ait.ac.at:12060/repository/record/';
  var lilyNamespace = 'at.ac.ait';
  
  var results = data.response.numFound;
  var resultMessage = results + ' result';
  if (results != 1)
    resultMessage += 's';
  resultMessage += ' found';
  
  var pages = '';
  if (results > rows) {
    for (p = 1; p <= 20 && (p - 1) * rows < results; p++) {
      var start = (p - 1) * rows;
      if (start == data.response.start)
        pages += p + ' ';
      else
        pages += '<a href="javascript:;" onclick="askSolr(' + start + ')">' + p + '</a> ';
    }
  }
  
  var searchResults = '';
  for (doc of data.response.docs) {
    var fileAdress = lilyEndpoint + encodeURIComponent(doc['lily.id']) +
        '/field/n$' + blobField + '/data?ns.n=' + lilyNamespace;
    var title = doc[titleField];
    if (doc.headline)
      title = doc.headline;
    var link = '<a href="' + fileAdress + '">' + title + '</a>';
    var bytes = doc[bytesField];
    var filesize;
    if (bytes < 1024)
      filesize = bytes + ' B';
    else if (bytes < 1024 * 1024)
      filesize = Math.floor(bytes / 1024) + ' kB';
    else
      filesize = Math.floor(bytes / (1024 * 1024)) + ' MB';
    var category='';
    if (doc.category) {
      var categories = doc.category.split(' > ');
      category = categories[categories.length - 1];
    }
    searchResults += '<tr><td>' + link + '</td>' +
        '<td>' + category  + '</td>' +
        '<td>' + (doc.author ? doc.author : '') + '</td>' +
        '<td>' + filesize + '</td></tr>';
  }
  
  resultMessage = '<div class="results">' + resultMessage + '</div>';
  pages = '<div class="results">' + pages + '</div>';
  
  document.getElementById('output').innerHTML = resultMessage +
      pages + '<table>' + searchResults + '</table>';
}

function askSolr(start) {
  //var solrEndpoint = 'http://localhost:8983/solr/collection1/';
  var solrEndpoint = 'http://earkdev.ait.ac.at:8983/solr/news/';
  var queryString = document.forms.find.queryString.value;
  var blobQuery = '';
  if (queryString)
    blobQuery = blobField + ':' + queryString;
  
  var typesQuery = '';
  for (option of document.forms.find.url.options) {
    if (option.selected) {
      if (typesQuery) typesQuery += " ";
      typesQuery += typeField + ':' + option.value;
    }
  }

  var headline = document.forms.find.headline.value;
  var packageQuery = '';
  if (headline) {
    packageQuery += 'headline:"' + headline + '"';
  }
  
  var dateQuery = '';
  var from = document.forms.find.from.value;
  var to = document.forms.find.to.value;
  if (from || to) {
    from = from ? from + 'T00:00:00Z' : '*';
    to = to ? to + 'T23:59:59Z' : '*';
    dateQuery = dateField + ':[' + from + ' TO ' + to + ']';
  }
  
  var query = '';
  if (blobQuery) query = blobQuery;
  if (packageQuery) {
    if (query)
      query += ' AND ' + packageQuery;
    else
      query = packageQuery;
  }
  if (typesQuery) {
    if (query)
      query += ' AND (' + typesQuery + ')';
    else
      query = typesQuery;
  }
  if (dateQuery) {
    if (query)
      query += ' AND ' + dateQuery;
    else
      query = dateQuery;
  }
  
  if (!query) query = '*:*';
  
  var sort = document.forms.find.sort.value;
  var sortParameter = '';
  if (sort) {
    sortParameter = '&sort=' + sort;
  }
  
  var script = document.createElement('script');
  script.src = solrEndpoint + 'select?q=' + encodeURIComponent(query) +
      sortParameter + '&start=' + start + '&rows=' + rows + '&wt=json&json.wrf=callback';
  document.getElementsByTagName('head')[0].appendChild(script);
}
