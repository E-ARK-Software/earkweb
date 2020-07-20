HEADER="\e[34m"
OKGREEN="\e[92m"
FAIL="\e[91m"
ENDC="\e[0m"

function echo_highlight() {
    echo -e "$1$2$ENDC"
}

function echo_highlight_header()
{
    echo -e "$1==========================================================="
    echo -e "$2"
    echo -e "===========================================================$ENDC"
}
