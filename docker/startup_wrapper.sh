#!/bin/sh

isPidRunning() {
	pid="$1"
	kill -0 "$pid" >/dev/null 2>&1
	result="$?"
	if [ "$result" != "0" ]
	then
		echo 1
	else
		echo 0	
	fi
}

isPidFileRunning() {
	pid_file="$1"
	if [ -f "$pid_file" ]
	then
		pid="$(cat "$pid_file")"
		echo $(isPidRunning "$pid")
	else
		echo 1
	fi

}

startUwsgi() {
	/usr/sbin/service uwsgi restart
}

uwsgi_pid_file="/var/run/uwsgi/earkweb/pid"

uwsgi_folders="
/run/uwsgi
/run/uwsgi/stats
/run/uwsgi/earkweb
/run/uwsgi/earkweb/develop
/var/log/earkweb
/var/log/uwsgi
/var/log/uwsgi/app
"


# create needed tmp folders and files
for uwsgi_folder in $uwsgi_folders
do
	mkdir -p "$uwsgi_folder"
	chown -R www-data:www-data "$uwsgi_folder"
done

while true
do
	# keep uwsgi running
	if [ "$(isPidFileRunning "$uwsgi_pid_file")" != "0" ]
	then
		startUwsgi
	fi

	sleep 10
done
