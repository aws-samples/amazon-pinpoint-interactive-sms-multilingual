import json
import os
from unittest import mock
import boto3
import botocore.session
import pytest
from moto import mock_dynamodb
from botocore.stub import Stubber
from receive_sms_messages import app


def pinpoint_sns_event_message(text):
    return {
        "Records": [
            {
                "body": "{\"originationNumber\":\"+15055550100\",\"destinationNumber\":\"+15055550100\",\"messageKeyword\":\"INTERACTIVESMS\",\"messageBody\":\"" + text + "\",\"previousPublishedMessageId\":\"imvr0joif8735it2o3cve1to0q5jni58k7i7sd00\",\"inboundMessageId\":\"e101a83b-4cbd-42a3-8a9b-60d3871f766e\"}"
            }
        ]
    }

def boto3_client_side_effect_pinpoint_send_success(*args, **kwargs):
    if args[0] == 'pinpoint':
        pinpoint = botocore.session.get_session().create_client('pinpoint')
        stubber = Stubber(pinpoint)
        stubber.add_response(
            'send_messages',
            {
                'MessageResponse': {
                    'ApplicationId': 'string',
                    'Result': {
                        '+15055550100': {
                            'StatusCode': 123,
                            'DeliveryStatus': 'SUCCESSFUL'
                        }
                    }
                }
            }
        )
        stubber.activate()
        return pinpoint
    #else:
    #    return boto3.client


@mock_dynamodb
@mock.patch.dict(os.environ, {'TABLE': 'MESSAGING_TABLE'})
@mock.patch.dict(os.environ, {'APP': 'abc123'})
def test_lambda_handler():
    boto3.setup_default_session()
    client = boto3.client('dynamodb', region_name='us-west-2')
    client.create_table(
        TableName='MESSAGING_TABLE',
        KeySchema=[
            {'AttributeName': 'pk', 'KeyType': 'HASH'}
        ],
        AttributeDefinitions=[
            {'AttributeName': 'pk', 'AttributeType': 'S'}
        ],
        BillingMode='PAY_PER_REQUEST'
    )
    client.put_item(
        TableName='MESSAGING_TABLE',
        Item={
            "conversation_status": {"S": "NONE"},
            "chat_list": {"L": []},
            "opted_out": {"BOOL": False},
            "last_name": {"S": "Stiles"},
            "dob": {"S": "01/01/2000"},
            "first_name": {"S": "John"},
            "locale": {"S": "en"},
            "Language": {"S": "EN"},
            "physical_address": {"S": "NO ADDRESS ON FILE"},
            "pk": {"S": "15055550100"}
        }
    )
    with mock.patch('boto3.client',
                    mock.MagicMock(side_effect=boto3_client_side_effect_pinpoint_send_success)):
        app.lambda_handler(pinpoint_sns_event_message('Hello?'), None)
    response = client.get_item(
        TableName='MESSAGING_TABLE',
        Key={'pk': {'S': '15055550100'}},
    )
    assert response['Item']['conversation_status']['S'] == 'NONE'
    with mock.patch('boto3.client',
                    mock.MagicMock(side_effect=boto3_client_side_effect_pinpoint_send_success)):
        app.lambda_handler(pinpoint_sns_event_message('NO'), None)
    response = client.get_item(
        TableName='MESSAGING_TABLE',
        Key={'pk': {'S': '15055550100'}},
    )
    assert response['Item']['conversation_status']['S'] == 'DECLINED_ADDRESS_UPDATE'
    with mock.patch('boto3.client',
                    mock.MagicMock(side_effect=boto3_client_side_effect_pinpoint_send_success)):
        app.lambda_handler(pinpoint_sns_event_message('UPDATE'), None)
    response = client.get_item(
        TableName='MESSAGING_TABLE',
        Key={'pk': {'S': '15055550100'}},
    )
    assert response['Item']['conversation_status']['S'] == 'WAITING_FOR_VERIFICATION_FIRST_TIME'
    with mock.patch('boto3.client',
                    mock.MagicMock(side_effect=boto3_client_side_effect_pinpoint_send_success)):
        app.lambda_handler(pinpoint_sns_event_message('01/01/1111'), None)
    response = client.get_item(
        TableName='MESSAGING_TABLE',
        Key={'pk': {'S': '15055550100'}},
    )
    assert response['Item']['conversation_status']['S'] == 'FAILED_IDENTITY_VERIFICATION'
    with mock.patch('boto3.client',
                    mock.MagicMock(side_effect=boto3_client_side_effect_pinpoint_send_success)):
        app.lambda_handler(pinpoint_sns_event_message('UPDATE'), None)
    response = client.get_item(
        TableName='MESSAGING_TABLE',
        Key={'pk': {'S': '15055550100'}},
    )
    assert response['Item']['conversation_status']['S'] == 'WAITING_FOR_VERIFICATION_FIRST_TIME'
    with mock.patch('boto3.client',
                    mock.MagicMock(side_effect=boto3_client_side_effect_pinpoint_send_success)):
        app.lambda_handler(pinpoint_sns_event_message('01/01/2000'), None)
    response = client.get_item(
        TableName='MESSAGING_TABLE',
        Key={'pk': {'S': '15055550100'}},
    )
    assert response['Item']['conversation_status']['S'] == 'WAITING_FOR_ADDRESS_CHANGE_ANSWER'
    with mock.patch('boto3.client',
                    mock.MagicMock(side_effect=boto3_client_side_effect_pinpoint_send_success)):
        app.lambda_handler(pinpoint_sns_event_message('NO'), None)
    response = client.get_item(
        TableName='MESSAGING_TABLE',
        Key={'pk': {'S': '15055550100'}},
    )
    assert response['Item']['conversation_status']['S'] == 'WAITING_FOR_ADDRESS'
    with mock.patch('boto3.client',
                    mock.MagicMock(side_effect=boto3_client_side_effect_pinpoint_send_success)):
        app.lambda_handler(pinpoint_sns_event_message('123 ABC AVE'), None)
    response = client.get_item(
        TableName='MESSAGING_TABLE',
        Key={'pk': {'S': '15055550100'}},
    )
    assert response['Item']['conversation_status']['S'] == 'WAITING_FOR_ADDRESS_CONFIRMATION'
    with mock.patch('boto3.client',
                    mock.MagicMock(side_effect=boto3_client_side_effect_pinpoint_send_success)):
        app.lambda_handler(pinpoint_sns_event_message('NO'), None)
    response = client.get_item(
        TableName='MESSAGING_TABLE',
        Key={'pk': {'S': '15055550100'}},
    )
    assert response['Item']['conversation_status']['S'] == 'WAITING_FOR_ADDRESS'
    with mock.patch('boto3.client',
                    mock.MagicMock(side_effect=boto3_client_side_effect_pinpoint_send_success)):
        app.lambda_handler(pinpoint_sns_event_message('123 ABC AVE'), None)
    response = client.get_item(
        TableName='MESSAGING_TABLE',
        Key={'pk': {'S': '15055550100'}},
    )
    assert response['Item']['conversation_status']['S'] == 'WAITING_FOR_ADDRESS_CONFIRMATION'
    with mock.patch('boto3.client',
                    mock.MagicMock(side_effect=boto3_client_side_effect_pinpoint_send_success)):
        app.lambda_handler(pinpoint_sns_event_message('YES'), None)
    response = client.get_item(
        TableName='MESSAGING_TABLE',
        Key={'pk': {'S': '15055550100'}},
    )
    assert response['Item']['conversation_status']['S'] == 'ADDRESS_UPDATED'
    with mock.patch('boto3.client',
                    mock.MagicMock(side_effect=boto3_client_side_effect_pinpoint_send_success)):
        app.lambda_handler(pinpoint_sns_event_message('UPDATE'), None)
    response = client.get_item(
        TableName='MESSAGING_TABLE',
        Key={'pk': {'S': '15055550100'}},
    )
    assert response['Item']['conversation_status']['S'] == 'WAITING_FOR_VERIFICATION_FIRST_TIME'
    with mock.patch('boto3.client',
                    mock.MagicMock(side_effect=boto3_client_side_effect_pinpoint_send_success)):
        app.lambda_handler(pinpoint_sns_event_message('01/01/2000'), None)
    response = client.get_item(
        TableName='MESSAGING_TABLE',
        Key={'pk': {'S': '15055550100'}},
    )
    assert response['Item']['conversation_status']['S'] == 'WAITING_FOR_ADDRESS_CHANGE_ANSWER'
    with mock.patch('boto3.client',
                    mock.MagicMock(side_effect=boto3_client_side_effect_pinpoint_send_success)):
        app.lambda_handler(pinpoint_sns_event_message('YES'), None)
    response = client.get_item(
        TableName='MESSAGING_TABLE',
        Key={'pk': {'S': '15055550100'}},
    )
    assert response['Item']['conversation_status']['S'] == 'ADDRESS_CONFIRMED'
    with mock.patch('boto3.client',
                    mock.MagicMock(side_effect=boto3_client_side_effect_pinpoint_send_success)):
        app.lambda_handler(pinpoint_sns_event_message('STOP'), None)
    response = client.get_item(
        TableName='MESSAGING_TABLE',
        Key={'pk': {'S': '15055550100'}},
    )
    assert response['Item']['conversation_status']['S'] == 'OPTED_OUT'
    with mock.patch('boto3.client',
                    mock.MagicMock(side_effect=boto3_client_side_effect_pinpoint_send_success)):
        app.lambda_handler(pinpoint_sns_event_message('OPT OUT TEST'), None)
    response = client.get_item(
        TableName='MESSAGING_TABLE',
        Key={'pk': {'S': '15055550100'}},
    )
    assert response['Item']['conversation_status']['S'] == 'OPTED_OUT'


