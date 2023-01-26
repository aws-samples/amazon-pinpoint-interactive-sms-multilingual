# Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
# SPDX-License-Identifier: MIT-0
import json
import os
from os import environ

import boto3
import simplejson as json
from boto3.dynamodb.conditions import Key
from loguru import logger


def lambda_handler(event, context):
    logger.debug('Event: ' + json.dumps(event))
    pinpoint = boto3.client('pinpoint')
    record = event['Records'][0]
    if record['eventName'] == 'REMOVE':
        return
    new_image = record['dynamodb']['NewImage']
    opt_out = 'NONE'
    if 'physical_address' not in new_image:
        new_image['physical_address'] = {'S': 'NO ADDRESS ON FILE'}
    if 'locale' not in new_image:
        new_image['locale'] = {'S': 'en'}
    if 'opted_out' in new_image and new_image['opted_out']['BOOL']:
        opt_out = 'ALL'
    pinpoint.update_endpoint(
        ApplicationId=os.environ['APP'],
        EndpointId=f"pn_{new_image['pk']['S']}",
        EndpointRequest={
            'ChannelType': 'SMS',
            'Address': new_image['pk']['S'],
            'OptOut': opt_out,
            'Demographic': {
                'Locale': new_image['locale']['S']
            },
            'User': {
                'UserAttributes': {
                    'FirstName': [new_image['first_name']['S']],
                    'LastName': [new_image['last_name']['S']],
                    'PhysicalAddress': [new_image['physical_address']['S']],
                    'Language': [new_image['locale']['S']]
                },
                'UserId': f"pn_{new_image['pk']['S']}"
            }
        }
    )
    return True
