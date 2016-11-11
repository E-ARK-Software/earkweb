echo "Stopping Peripleo ..."
echo eark | sudo -S service peripleo stop
echo "Pause 10 seconds ..."
sleep 10
echo "Starting Peripleo ..."
echo eark | sudo -S service peripleo start
echo "Restarting finished, window can be closed."
