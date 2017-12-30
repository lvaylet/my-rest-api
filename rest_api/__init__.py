# -*- coding: utf-8 -*-

import os

import hammock

# Credentials and Hammock instances
LMS_TOKEN = os.environ['LMS_TOKEN']
LMS = hammock.Hammock('https://talend.talentlms.com/api/v1',
                      auth=(LMS_TOKEN, ''))
