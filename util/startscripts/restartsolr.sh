echo "Stopping solr ..."
echo repo | sudo -S service solr stop
echo "Pause 10 seconds ..."
sleep 10
echo "Starting solr ..."
echo repo | sudo -S service solr start
echo "Restarting finished, window can be closed."
