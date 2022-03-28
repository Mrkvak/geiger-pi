#!/bin/bash
sudo apt install rrdtool python3-rrdtool

sudo mkdir -p /usr/local/sbin
sudo mkdir -p /usr/local/lib/cgi-bin

sudo cp geiger-graph.sh /usr/local/sbin
sudo cp geiger.py /usr/local/sbin
sudo cp getcpm.cgi /usr/local/lib/cgi-bin

sudo cp conf/geiger-cron.conf /etc/cron.d/
sudo cp conf/geiger.service /etc/systemd/system

sudo cp -r html /var/html/geiger


sudo systemctl daemon-reload
sudo systemctl enable geiger.service
sudo systemctl start geiger.service
