import string

commands = {
    'summain':
        ["/usr/bin/summain", "-c", "SHA256", "-c", "MD5", "--exclude=Ino,Dev,Uid,Username,Gid,Group,Nlink,Mode", "--output", string.Template("$manifest_file"), string.Template("$package_dir")]
}