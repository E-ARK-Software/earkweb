import string

commands = {
    'summain':
        ["/usr/bin/summain", "-c", "SHA256", "-c", "MD5", "--exclude=Ino,Dev,Uid,Username,Gid,Group,Nlink,Mode", "--output", string.Template("$manifest_file"), string.Template("$package_dir")],
    'untar':
        ["tar", "-xf", string.Template("$tar_file"), "-C", string.Template("$target_dir")],
    'pdftohtml':
        ["pdftohtml", "-c", "-s", "-noframes", string.Template("$pdf_file"), string.Template("$html_file")],
    'pdftopdfa':
        ['gs', '-dPDFA', '-dBATCH', '-dNOPAUSE', '-dUseCIEColor', '-sProcessColorModel=DeviceCMYK', '-sDEVICE=pdfwrite',
         '-sPDFACompatibilityPolicy=1', string.Template('$output_file'), string.Template('$input_file')]
}
