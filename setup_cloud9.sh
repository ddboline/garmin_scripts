#!/bin/bash

sudo bash -c "echo deb ssh://ddboline@ddbolineathome.mooo.com/var/www/html/deb/trusty/devel ./ > /etc/apt/sources.list.d/py2deb.list"
sudo apt-get update
sudo apt-get install -y --force-yes python-numpy=1.\* python-matplotlib python-scipy python-nose \
                                    python-sklearn python-coverage python-setuptools python-dev
