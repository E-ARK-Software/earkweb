import os,sys
import json
from earkcore.utils.fileutils import remove_protocol
import mimetypes

mimetypes.add_type('text/plain','.log')

def path_to_dict(path, strip_path_part=None):
    import sys
    reload(sys)
    sys.setdefaultencoding('utf8')
    d = {'text': os.path.basename(unicode(path).encode('utf-8'))}
    if os.path.isdir(unicode(path).encode('utf-8')):
        d['icon'] = "glyphicon glyphicon-folder-close"
        d['children'] = [path_to_dict(os.path.join(unicode(path).encode('utf-8'),x), strip_path_part) for x in os.listdir(unicode(path).encode('utf-8'))]
        path_metadata = path if strip_path_part is None else path.replace(strip_path_part, "")
        d['data'] = {"path": unicode(path_metadata).encode('utf-8')}
    else:
        d['icon'] = "glyphicon glyphicon-file"
        path_metadata = path if strip_path_part is None else path.replace(strip_path_part, "")
        d['data'] = {"path": unicode(path_metadata).encode('utf-8'), "mimetype": get_mime_type(path)}

    return d

def fsize(file_path, wd=None):
    fp = remove_protocol(file_path)
    path = fp if wd is None else os.path.join(wd,fp)
    return int(os.path.getsize(path))


def get_mime_type(path):
    type, subtype = mimetypes.guess_type(path)
    return type

def main():
    print json.dumps(path_to_dict('.'), indent=4, sort_keys=False)

if __name__ == "__main__":
    main()
