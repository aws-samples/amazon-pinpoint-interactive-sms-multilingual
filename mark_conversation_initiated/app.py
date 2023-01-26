# Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
# SPDX-License-Identifier: MIT-0
import json
import os
import re
from os import environ
import datetime
import boto3
import simplejson as json
from boto3.dynamodb.conditions import Key
from loguru import logger
import gettext


def load_languages():
    locales_path = os.path.join(os.path.dirname(os.path.realpath(__file__)), 'locales')
    lang_dict = {}
    for lang_dir in next(os.walk(locales_path))[1]:
        lang_dict[lang_dir.lower()] = gettext.translation('base', localedir=locales_path, languages=[lang_dir.lower()])
    return lang_dict


lang = load_languages()


def lambda_handler(event, context):
    logger.debug('Event: ' + json.dumps(event))
    dynamodb = boto3.resource('dynamodb')
    table = dynamodb.Table(environ['TABLE'])
    for endpoint_id, endpoint in event['Endpoints'].items():
        lang[endpoint['User']['UserAttributes']['Language'][0].lower()].install()
        table.update_item(
            Key={
                'pk': endpoint['Address'].replace('+', '')
            },
            UpdateExpression='SET conversation_status = :conversation_status, chat_list = list_append(chat_list, :new_msg)',
            ExpressionAttributeValues={
                ':conversation_status': 'WAITING_ON_INITIAL_RESPONSE',
                ':new_msg': [
                    f"{datetime.datetime.now().replace(microsecond=0).isoformat()} <OUTGOING> " + customize(_('GREETING_IMPORTANT_MESSAGE'), endpoint)
                ]
            },
            ReturnValues='ALL_NEW',
        )

def customize(text, endpoint):
    template = text.replace('%FIRST_NAME%', endpoint['User']['UserAttributes']['FirstName'][0])
    template = template.replace('%LAST_NAME%', endpoint['User']['UserAttributes']['LastName'][0])
    return template
