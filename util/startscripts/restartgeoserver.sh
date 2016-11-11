echo "Stopping Geoserver ..."
echo eark | sudo -S service geoserver stop
echo "Pause 10 seconds ..."
sleep 10
echo "Starting Geoserver ..."
echo eark | sudo -S service geoserver start
echo "Restarting finished, window can be closed."
