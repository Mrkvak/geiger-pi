#!/bin/sh
echo "Status: 200" 
echo "Content-Type: application/json" 
echo
DATA=
while [ "$DATA" = "" ]; do
	DATA=$(tail -n 1 /run/geiger/geiger.csv)
	if [ $(echo "$DATA" | grep -o , |wc -l) -lt 3 ]; then
		sleep 0.1
		DATA=
		continue
	fi
done
LASTUPD=$(echo "$DATA"|cut -d , -f 1)
CPS_CURRENT=$(echo "$DATA"|cut -d , -f 3)
CPM_1MAVG=$(echo "$DATA"|cut -d , -f 4)
echo "{\"lastUpdate\": \"$LASTUPD\", \"currentCPS\": $CPS_CURRENT, \"avgCPM1min\": $CPM_1MAVG}"
