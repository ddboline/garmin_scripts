#!/bin/bash

sudo apt-get update
sudo apt-get install -y gpsbabel garmin-forerunner-tools xml2
# sudo apt-get install -y python-mpltoolkits.basemap
sudo apt-get install -y python-pandas python-lockfile

#CURDIR=`pwd`
#cd ${HOME}
#git clone https://github.com/ddboline/ddboline_html.git public_html
#cd public_html/
#sh setup_cloud9.sh
#mkdir garmin
#cd $CURDIR

#echo "America/New_York" > timezone
#sudo mv timezone /etc/timezone
#sudo rm /etc/localtime
#sudo ln -sf /usr/share/zoneinfo/posixrules /etc/localtime

./test_cloud9.sh
