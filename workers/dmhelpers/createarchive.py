import requests
import tarfile
import tempfile
import os


class CreateNLPArchive(object):
    """
    Create a tar container from files that should be processed by NLP tools. This is done to avoid additional Solr
    queries if different algorithms/models are to be used.

    The Solr query will have to formed as such that only the desired files are in the JSON result object! This means:
    * no duplicate files
    * no non-text files
    * etc.
    """

    def get_data_from_solr(self, solr_query, archive_name):
        """
        Takes a Solr query and sends every document in the JSON result to a tar file. Takes care of paging the results
        (default: 10 documents per query).

        @param solr_query:      Complete solry query (url to JSON result as string)
        @param archive_name:    Path to where the tar file should be created (string)
        @return:                Path to tar (string)
        """
        # these file types should be stored

        # get JSON result
        result = requests.get(solr_query)
        if result.status_code is not 200:
            result.raise_for_status()   # raises exception when GET request failed

        # tar file
        try:
            archive = tarfile.open(archive_name, 'w')
        except tarfile.TarError, e:
            raise e

        for document in result.json()['response']['docs']:
            self.add_to_archive(document, archive)

        # check if there are more than 10 results (default paging)
        numFound = result.json()['response']['numFound']
        if numFound > 10:
            loop = 1
            rows = 10   # default increment of 10 results
            loops = numFound / rows
            extra = numFound % rows     # number of rows for last query
            start = 0
            while loop < loops:
                loop_query = solr_query + '&start=%d&rows=%d' % (start + rows * loop, rows)
                loop_result = requests.get(loop_query)
                for document in loop_result.json()['response']['docs']:
                    self.add_to_archive(document, archive)
                loop += 1
            end_query = solr_query + '&start=%d&rows=%d' % (start + rows * loop, extra)
            end_result = requests.get(end_query)
            for document in end_result.json()['response']['docs']:
                self.add_to_archive(document, archive)

        # close tar file
        archive.close()
        return archive_name

    def add_to_archive(self, document, archive):
        """
        Takes JSON objects and adds them to a tar file. The filename inside the tar equals 'entry' (with '/' replaced
        by '.').

        @param document:    The document, taken from the Solr query (JSON)
        @param archive:     Path to the tar file, where the document should be stored.
        @return:            
        """
        entry = document['entry'][0].encode('utf-8')
        content = document['content'][0].encode('utf-8')

        tmpfile = tempfile.NamedTemporaryFile(mode='w', delete=False)
        tmpfile.write(content)
        tmpfile.close()
        try:
            archive.add(tmpfile.name, arcname=entry.replace('/', '.'))
        except tarfile.TarError, e:
            raise e
        os.remove(tmpfile.name)


# if __name__ == '__main__':
#     tarcreator = CreateNLPArchive()
#     tarcreator.get_data_from_solr('http://localhost:8983/solr/earkstorage/select?indent=on&q=content_type:%22application/pdf%22%20OR%20content_type:%22text/plain;%20charset=UTF-8%22&rows=31&wt=json', '/home/janrn/test.tar')