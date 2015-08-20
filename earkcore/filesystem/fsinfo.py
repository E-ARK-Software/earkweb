import os,sys
import json

def path_to_dict(path):
    d = {'text': os.path.basename(path)}
    if os.path.isdir(path):
        d['icon'] = "glyphicon glyphicon-folder-close"
        d['children'] = [path_to_dict(os.path.join(path,x)) for x in os.listdir(path)]
    else:
        d['icon'] = "glyphicon glyphicon-file"
    return d

def main():
    print json.dumps(path_to_dict('.'), indent=4, sort_keys=False)

if __name__ == "__main__":
    main()