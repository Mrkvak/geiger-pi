#!/bin/bash
mkdir -p /run/geiger/img
SECONDARY_Y_SCALE=3
for sched in h d w m y; do
	rrdtool graph "/run/geiger/img/geiger-${sched}.png" \
		--start -1${sched} \
		-w 1280 \
		-h 360 \
		--vertical-label=CPM \
		--right-axis-label=PeakCPM \
		--right-axis=${SECONDARY_Y_SCALE}:0 \
		--font=LEGEND:8:monospace \
		"DEF:cpm=/var/lib/geiger/geiger.rrd:CPM:AVERAGE" \
		"DEF:peak_cpm=/var/lib/geiger/geiger.rrd:PeakCPM:AVERAGE" \
		"COMMENT:------------------------------------------------------------------------------------------\n" \
		"COMMENT:       \t\t\tCurrent   \t Minimum \t Maximum \t Average\n" \
		"COMMENT:------------------------------------------------------------------------------------------\n" \
		"LINE2:cpm#0000FF:CPM    \t" \
		"GPRINT:cpm:LAST: %7.0lf \t" \
		"GPRINT:cpm:MIN: %7.0lf \t" \
		"GPRINT:cpm:MAX: %7.0lf \t" \
		"GPRINT:cpm:AVERAGE: %7.0lf\n" \
		"CDEF:peak_cpm_scaled=peak_cpm,${SECONDARY_Y_SCALE},/" \
		"LINE1:peak_cpm_scaled#00FF00:PeakCPM\t" \
		"GPRINT:peak_cpm:LAST: %7.0lf \t" \
		"GPRINT:peak_cpm:MIN: %7.0lf \t" \
		"GPRINT:peak_cpm:MAX: %7.0lf \t" \
		"GPRINT:peak_cpm:AVERAGE: %7.0lf\n" \
		"COMMENT:PeakCPM is highest CPS value in a minute multiplied by 60\n"
done
