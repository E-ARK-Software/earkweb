import httplib
import base64


def write_to_exist(xml, xml_id):
    """
    Takes an XML string and an identifier, creates a record in eXist-db.

    @param xml:     XML as a string
    @param xml_id:  identifier for the eXist-db entry
    @return:        HTML status code (200, 201 if successful)
    """
    con = httplib.HTTP('earkdev.ait.ac.at')
    con.putrequest('PUT', '/exist/apps/eark/nlp/%s' % xml_id)
    con.putheader('Content-Type', 'application/xml')
    clen = len(xml)
    con.putheader('Content-Length', `clen`)
    con.putheader('Authorization', 'Basic %s' % base64.b64encode('nlp-user:earknlp'))   # TODO: set this in settings.py
    con.endheaders()
    con.send(xml)
    errcode, errmsg, headers = con.getreply()
    if errcode in (200, 201):   # HTML OK and Created
        return errcode
    else:
        # f = con.getfile()
        # with open('/home/janrn/tomarfiles/errors/%s.err' % xml_id, 'w') as errfile:
        #     errfile.write(errmsg)
        return errcode
