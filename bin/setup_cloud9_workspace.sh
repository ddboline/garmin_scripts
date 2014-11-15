#!/bin/bash

sudo echo
SCRIPTDIR="${HOME}/workspace"
#git clone git@github.com:ddboline/ddboline_personal_scripts.git

scp ddboline@ddbolineathome.mooo.com:~/gDrive/backup/chromebook_home_backup_20141029.tar.gz ${SCRIPTDIR}/

sudo apt-get update
#sudo apt-get install -y sendxmpp byobu screen
# sudo apt-get install -y mailutils postfix
sudo apt-get install -y python-pexpect
sudo apt-get install -y ipython
# sudo apt-get install -y libroot-bindings-python-dev libroot-graf2d-postscript-dev
sudo apt-get install -y python-googleapi
sudo apt-get install -y make
# sudo apt-get install -y libboost-python-dev
sudo apt-get install -y cython
sudo apt-get install -y python-matplotlib python-sklearn