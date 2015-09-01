import requests

SERVER_PROTOCOL_PREFIX = 'http://'
SERVER_NAME = '81.189.135.189/dm-hdfs-storage'
SERVER_HDFS = SERVER_PROTOCOL_PREFIX + SERVER_NAME + '/hsink/fileresource'
FILE_RESOURCE = SERVER_HDFS + '/files/{0}'

def upload(aip_path):
    if aip_path is not None:
        hdfs_path = None
        with open(aip_path, 'r') as f:
            filename = aip_path.rpartition('/')[2]
            r = requests.put(FILE_RESOURCE.format(filename), data=f)
            if r.status_code == 201:
                hdfs_path = r.headers['location'].rpartition('/files/')[2]
            else:
                hdfs_path = None

def main():
    aip_path = "/var/data/earkweb/storage/2d93fe6b-2c92-4a5d-a033-48d0709826b3_00001.tar"
    upload(aip_path)

if __name__ == "__main__":
    main()
