var identifier_field = 'package';
var blobField = 'content';
var titleField = 'path';
var labelField = 'eadtitle_t';
var bytesField = 'stream_size';
var typeField = 'content_type';
var rows = 20;

function callback(data) {
  var repo_item_access_endpoint = '/earkweb/access/get-item/';

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
    window.console.log(doc);

    // var fileAdress = repo_item_access_endpoint + doc[identifier_field] + "/" + doc[titleField];
    var fileAdress = repo_item_access_endpoint  +  doc[titleField];

    var archiveDateFormatted = new Date(doc['archivedate']).toLocaleDateString(window.lang+'-'+window.lang, {year:"numeric", month:"short", day:"numeric", hour:"numeric", minute:"numeric"})


    var popupWidth = window.popupWidth != undefined ? window.popupWidth : 900;
    var popupHeight = window.popupHeight != undefined ? window.popupHeight : 500;

    var docInfo = "<span style='font-size:9px'>"+doc[identifier_field]+" (v"+doc['version']+", "+archiveDateFormatted+")</span>";
    var docPath = ( (doc[labelField] != null) ? doc[labelField] : doc[titleField] );
    var link = '<a href="/earkweb/access/'+doc[identifier_field]+'/">'+docInfo+'</a><br><a data-toggle="tooltip" title="' + mimeStr + '" href="' + fileAdress + '?search='+document.forms.find.queryString.value+'" target="_blank" onclick="PopupCenter(this,\'xtf\',\''+popupWidth+'\',\''+popupHeight+'\'); return false;">' + docPath + '</a>';

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
  var solrEndpoint = '/earkweb/solrif/storagecore1/';
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
    packageQuery += " AND " + identifier_field + ':"' + package + '"';
  }

  //if($('#submission_data_only').prop('checked')) {
  //  packageQuery += " AND is_content_data:true";
  //}

  if($('#exclude_migrated_data').prop('checked')) {
    packageQuery += " AND NOT path:*_mig-*";
  }

  var eaddate_from = $('#eaddate_from').val();
  var eaddate_to = $('#eaddate_to').val();
  if(acceptedDateFormat(eaddate_from) || acceptedDateFormat(eaddate_to)) {
    var from = !acceptedDateFormat(eaddate_from) ? "*" : dateStringToUTCString(eaddate_from);
    var to = !acceptedDateFormat(eaddate_to) ? "*" : dateStringToUTCString(eaddate_to);
    packageQuery += " AND eaddate_dt:[" + from  + " TO " + to + "]";
  }

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
  window.console.log("sortParameter: " + sortParameter)

  var script = document.createElement('script');
  script.src = solrEndpoint + 'select?q=' + encodeURIComponent(query) +
      sortParameter + '&start=' + start + '&rows=' + rows + '&wt=json&json.wrf=callback';
  console.log(script.src);
  document.getElementsByTagName('head')[0].appendChild(script);
}
