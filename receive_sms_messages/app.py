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
    pinpoint = boto3.client('pinpoint')
    dynamodb = boto3.resource('dynamodb')
    table = dynamodb.Table(environ['TABLE'])
    message = json.loads(event['Records'][0]['body'])
    new_status, response_msg = parse_message(message, table)
    if response_msg is not False:
        send_response(new_status, response_msg, message, pinpoint, table)


def send_response(status, response_msg, original_msg, pinpoint, table):
    logger.debug('Outgoing Message: ' + response_msg)
    to_number = original_msg['originationNumber']
    from_number = original_msg['destinationNumber']
    response = pinpoint.send_messages(
        ApplicationId=os.environ['APP'],
        MessageRequest={
            'Addresses': {
                to_number: {
                    'ChannelType': 'SMS'
                }
            },
            'MessageConfiguration': {
                'SMSMessage': {
                    'Body': response_msg,
                    'MessageType': 'TRANSACTIONAL',
                    'OriginationNumber': from_number
                }
            }
        }
    )
    if response['MessageResponse']['Result'][original_msg['originationNumber']]['DeliveryStatus'] == 'SUCCESSFUL':
    #if True:
        if status == False:
            table.update_item(
                Key={
                    'pk': original_msg['originationNumber'].replace('+', '')
                },
                UpdateExpression='SET chat_list = list_append(chat_list, :new_msg)',
                ExpressionAttributeValues={
                    ':new_msg': [
                        f"{datetime.datetime.now().replace(microsecond=0).isoformat()} <INCOMING> " +
                        original_msg['messageBody'],
                        f"{datetime.datetime.now().replace(microsecond=0).isoformat()} <OUTGOING> " + response_msg
                    ]
                },
                ReturnValues='ALL_NEW',
            )
        else:
            table.update_item(
                Key={
                    'pk': original_msg['originationNumber'].replace('+', '')
                },
                UpdateExpression='SET conversation_status = :conversation_status, chat_list = list_append(chat_list, :new_msg)',
                ExpressionAttributeValues={
                    ':conversation_status': status,
                    ':new_msg': [
                        f"{datetime.datetime.now().replace(microsecond=0).isoformat()} <INCOMING> " +
                        original_msg['messageBody'],
                        f"{datetime.datetime.now().replace(microsecond=0).isoformat()} <OUTGOING> " + response_msg
                    ]
                },
                ReturnValues='ALL_NEW',
            )


def customize(text, record):
    template = text.replace('%FIRST_NAME%', record['first_name'])
    template = template.replace('%LAST_NAME%', record['last_name'])
    template = template.replace('%PHYSICAL_ADDRESS%', record['physical_address'])
    if 'physical_address_new' in record:
        template = template.replace('%PHYSICAL_ADDRESS_NEW%', record['physical_address_new'])
    if 'message_body' in record:
        template = template.replace('%MESSAGE_BODY%', record['message_body'])
    return template


def parse_message(message, table):
    response = table.query(
        KeyConditionExpression=Key('pk').eq(
            message['originationNumber'].replace('+', ''))
    )['Items'][0]
    logger.debug('Incoming Message: ' + message['messageBody'])
    lang[response['Language'].lower()].install()
    if response['opted_out']:
        # Note that this means we don't capture messages from someone who has opted out as well.
        return False, False
    conversation_status = response.get('conversation_status', 'NONE')
    # This is a list of the "terminal" conversation statuses, so prompting the beginning of the process again.
    if conversation_status in ['NONE', 'WAITING_ON_INITIAL_RESPONSE', 'DECLINED_ADDRESS_UPDATE', 'FAILED_IDENTITY_VERIFICATION', 'ADDRESS_CONFIRMED', 'ADDRESS_UPDATED']:
        if message['messageBody'].upper() == 'YES' or message['messageBody'].upper() == 'UPDATE':
            new_status = 'WAITING_FOR_VERIFICATION_FIRST_TIME'
            response_msg = customize(_('VERIFY_ADDRESS_PROMPT'), response)
        elif message['messageBody'].upper() == 'NO':
            new_status = 'DECLINED_ADDRESS_UPDATE'
            response_msg = customize(_('VERIFY_ADDRESS_PROMPT_DECLINED'), response)
        elif message['messageBody'].upper() == 'STOP':
            table.update_item(
                Key={
                    'pk': message['originationNumber'].replace('+', '')
                },
                UpdateExpression='SET opted_out = :opted_out',
                ExpressionAttributeValues={
                    ':opted_out': True
                },
                ReturnValues='ALL_NEW',
            )
            new_status = 'OPTED_OUT'
            response_msg = customize(_('OPTED_OUT'), response)
        else:
            new_status = False
            response_msg = customize(_('INVALID_RESPONSE'), response)
    elif conversation_status == 'WAITING_FOR_VERIFICATION_FIRST_TIME' or conversation_status == 'WAITING_FOR_VERIFICATION':
        dob_regex = r".*(?P<dob>\d{2}/\d{2}/\d{4}).*"
        dob_matches = re.match(dob_regex, message['messageBody'])
        if dob_matches:
            msg_dob = dob_matches.group('dob')
            if msg_dob == response['dob']:
                new_status = 'WAITING_FOR_ADDRESS_CHANGE_ANSWER'
                response_msg = ''
                if conversation_status == 'WAITING_FOR_VERIFICATION_FIRST_TIME':
                    response_msg = customize(_('IDENTITY_VERIFIED'), response) + "\n\n"
                response_msg += customize(_('ADDRESS_CHANGE_PROMPT'), response)
            else:
                new_status = 'FAILED_IDENTITY_VERIFICATION'
                response_msg = customize(_('FAILED_IDENTITY_VERIFICATION'), response)
    elif conversation_status == 'WAITING_FOR_ADDRESS_CHANGE_ANSWER':
        if message['messageBody'].upper() == 'YES':
            new_status = 'ADDRESS_CONFIRMED'
            response_msg = customize(_('ADDRESS_CONFIRMED'), response)
        elif message['messageBody'].upper() == 'NO':
            new_status = 'WAITING_FOR_ADDRESS'
            response_msg = customize(_('PROMPT_FOR_ADDRESS'), response)
    elif conversation_status == 'WAITING_FOR_ADDRESS':
        table.update_item(
            Key={
                'pk': message['originationNumber'].replace('+', '')
            },
            UpdateExpression='SET physical_address_new = :physical_address_new',
            ExpressionAttributeValues={
                ':physical_address_new': message['messageBody']
            },
            ReturnValues='ALL_NEW',
        )
        new_status = 'WAITING_FOR_ADDRESS_CONFIRMATION'
        response['message_body'] = message['messageBody']
        response_msg = customize(_('CONFIRM_ADDRESS_PROMPT'), response)
    elif conversation_status == 'WAITING_FOR_ADDRESS_CONFIRMATION':
        if message['messageBody'].upper() == 'YES':
            table.update_item(
                Key={
                    'pk': message['originationNumber'].replace('+', '')
                },
                UpdateExpression='SET physical_address = :physical_address REMOVE new_physical_address',
                ExpressionAttributeValues={
                    ':physical_address': response['physical_address_new']
                },
                ReturnValues='ALL_NEW',
            )
            new_status = 'ADDRESS_UPDATED'
            response_msg = customize(_('ADDRESS_UPDATED'), response)
        elif message['messageBody'].upper() == 'NO':
            new_status = 'WAITING_FOR_ADDRESS'
            response_msg = customize(_('REPROMPT_FOR_ADDRESS'), response)
    return new_status, response_msg
