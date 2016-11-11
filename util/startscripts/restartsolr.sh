echo "Stopping solr ..."
echo eark | sudo -S service solr stop
echo "Pause 10 seconds ..."
sleep 10
echo "Starting solr ..."
echo eark | sudo -S service solr start
echo "Restarting finished, window can be closed."
