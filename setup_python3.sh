#!/bin/bash

### hack...
export LANG="C.UTF-8"

sudo bash -c "echo deb ssh://ddboline@home.ddboline.net/var/www/html/deb/trusty/python3/devel ./ > /etc/apt/sources.list.d/py2deb.list"
sudo apt-get update
sudo apt-get install -y --force-yes python3-numpy=1.\* python3-matplotlib python3-setuptools \
                                    python3-scipy python3-pytest python3-pytest-cov \
                                    python3-sklearn python3-pandas
