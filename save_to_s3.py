#! /usr/bin/env python
# -*- coding: utf-8 -*-

# Copyright 2013. Amazon Web Services, Inc. All Rights Reserved.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

# Import the SDK
import boto
import uuid
import os
import time
import glob

# read aws credentials from file, then stick into global variables...
def read_keys():
    with open('%s/.aws/credentials' % os.getenv('HOME'), 'r') as f:
        for line in f:
            if 'aws_access_key_id' in line:
                aws_access_key_id = line.split('=')[-1].strip()
            if 'aws_secret_access_key' in line:
                aws_secret_access_key = line.split('=')[-1].strip()
    return aws_access_key_id, aws_secret_access_key

AWS_ACCESS_KEY_ID, AWS_SECRET_ACCESS_KEY = read_keys()

def save_to_s3(bname='garmin_scripts_gps_files_ddboline', filelist=[]):
    s3 = boto.connect_s3(aws_access_key_id=AWS_ACCESS_KEY_ID, aws_secret_access_key=AWS_SECRET_ACCESS_KEY)
    bucket = s3.create_bucket(bucket_name=bname)
    list_of_keys = {}
    for k in bucket.list():
        list_of_keys[k.key] = k.etag.replace('"','')
    for fn in filelist:
        kn = fn.split('/')[-1]
        if kn in list_of_keys:
            continue
        with open(fn, 'r') as infile:
            k = boto.s3.key.Key(bucket)
            k.key = kn
            k.set_contents_from_file(infile)
            list_of_keys[k.key] = k.etag.replace('"','')
            print kn, fn, list_of_keys[k.key]
    return list_of_keys

if __name__ == '__main__':
    save_to_s3('garmin_scripts_gps_files_ddboline', glob.glob('run/*/*/*'))
    #print save_to_s3()
