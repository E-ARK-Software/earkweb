var identifier_field = 'package';
var blobField = 'content';
var titleField = 'path';
var labelField = 'eadtitle_t';
var bytesField = 'stream_size';
var typeField = 'content_type';
var rows = 20;

function callback(data) {
  var repo_item_access_endpoint = 'http://'+django_service_ip+':'+django_service_port+'/earkweb/earkcore/access_aip_item/';

  //var lilyNamespace = 'org.eu.eark';
  
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
        pages += '<a href="#" onclick="askSolr(' + start + ')">' + p + '</a> ';
    }
  }
  
  var searchResults = '';
  for (doc of data.response.docs) {
    // strip off extended mime type information string (following ';') if it exists
    var mimeStr = doc[typeField][0];

    var mime = mimeStr.toString().replace(/;.*/g, '');
    var fileAdress = repo_item_access_endpoint + doc[identifier_field] + "/" + mime + "/" + doc[titleField]; // encodeURIComponent(doc['lily.id']) + '/field/n$' + blobField + '/data?ns.n=' + lilyNamespace;

    var displaytitle = (doc[labelField] != null) ? doc[labelField] : doc[titleField];

    var link = '<a data-toggle="tooltip" title="' + mimeStr + '" href="' + fileAdress + '" target="_blank">' + displaytitle + '</a>';
    var bytes = doc[bytesField];
    var filesize;
    if (bytes < 1024)
      filesize = bytes + ' B';
    else if (bytes < 1024 * 1024)
      filesize = Math.floor(bytes / 1024) + ' kB';
    else
      filesize = Math.floor(bytes / (1024 * 1024)) + ' MB';
    searchResults += '<tr><td>' + link + '</td><td>' + filesize + '</td></tr>';
  }
  
  resultMessage = '<div class="results">' + resultMessage + '</div>';
  pages = '<div class="results">' + pages + '</div>';
  
  document.getElementById('output').innerHTML = resultMessage +
      pages + '<table>' + searchResults + '</table>';
}

function askSolr(start) {
  //var solrEndpoint = 'http://'+local_solr_server_ip+':'+local_solr_port+'/solr/earkstorage/';
  var solrEndpoint = 'http://'+django_service_ip+':'+django_service_port+'/earkweb/earkcore/solrif/earkstorage/';
  window.console.log("solr endpoint: " + solrEndpoint)
  var queryString = document.forms.find.queryString.value;

  var blobQuery = '';
  if (queryString)
    blobQuery = blobField + ':' + queryString;
  
  var contentTypesQuery = '';
  for (i = 0; i < document.forms.find.contentTypes.options.length; i++) {
    option = document.forms.find.contentTypes.options[i];
    if (option.selected) {
      if (contentTypesQuery) contentTypesQuery += " ";
      contentTypesQuery += typeField + ':' + option.value + '*';
    }
  }

  var package = document.forms.find.package.value;
  var packageQuery = '*:*';
  if (package) {
    stripped_package_identifier = package.replace("urn:uuid:", "")
    window.console.log(stripped_package_identifier);
    packageQuery += " AND " + identifier_field + ':*' + stripped_package_identifier + '*';
  }

  if($('#submission_data_only').prop('checked')) {
    packageQuery += " AND path:*/representations/*/data/*";
  }

  if($('#exclude_migrated_data').prop('checked')) {
    packageQuery += " AND NOT path:*_mig-*";
  }
  var eadtitle = $('#eadtitle').val();
  if (typeof eadtitle !== 'undefined' && eadtitle !== null && eadtitle != '') {
    packageQuery += " AND eadtitle_s:*" + eadtitle + "*";
  }

  var eadtitle = $('#eadtitle').val();
  if (typeof eadtitle !== 'undefined' && eadtitle !== null && eadtitle != '') {
    packageQuery += " AND eadtitle_s:*" + eadtitle + "*";
  }

  var eaddate_from = $('#eaddate_from').val();
  var eaddate_to = $('#eaddate_to').val();
  if(acceptedDateFormat(eaddate_from) || acceptedDateFormat(eaddate_to)) {
    var from = !acceptedDateFormat(eaddate_from) ? "*" : dateStringToUTCString(eaddate_from);
    var to = !acceptedDateFormat(eaddate_to) ? "*" : dateStringToUTCString(eaddate_to);
    packageQuery += " AND eaddate_dt:[" + from  + " TO " + to + "]";
  }

//  if($('#institution_address').val() != "") {
//    packageQuery += " AND institutionaddress:*"+$('#institution_address').val()+"*";
//  }
//  if($('#institutionname').val() != "") {
//    packageQuery += " AND institutionname:*"+$('#institutionname').val()+"*";
//  }
//
//  if($('#yob_from').val() != "" && $('#yob_to').val() != "") {
//    var yob_from_full = $('#yob_from').val() + "0000";
//    var yob_to_full = $('#yob_to').val() + "1231";
//    packageQuery += " AND patientbirthdate:["+yob_from_full+" TO "+yob_to_full+"]";
//  }
  
  var query = '';
  if (blobQuery) query = blobQuery;
  if (packageQuery) {
    if (query)
      query += ' AND ' + packageQuery;
    else
      query = packageQuery;
  }
  if (contentTypesQuery) {
    if (query)
      query += ' AND (' + contentTypesQuery + ')';
    else
      query = contentTypesQuery;
  }
  
  if (!query) query = '*:*';
  
  var sort = document.forms.find.sort.value;
  var sortParameter = '';
  if (sort) {
    sortParameter = '&sort=' + sort;
  }

  window.console.log("query: " + query)
  
  var script = document.createElement('script');
  script.src = solrEndpoint + 'select?q=' + encodeURIComponent(query) +
      sortParameter + '&start=' + start + '&rows=' + rows + '&wt=json&json.wrf=callback';

  document.getElementsByTagName('head')[0].appendChild(script);
}
