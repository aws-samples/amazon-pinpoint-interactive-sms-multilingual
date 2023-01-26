import json
import os
from unittest import mock
import boto3
import botocore.session
import pytest
from moto import mock_dynamodb
from botocore.stub import Stubber
from mark_conversation_initiated import app


def pinpoint_event_message():
    return {
        "Endpoints": {
            "pn_15055550100": {
                "Address": "15055550100",
                "User": {
                    "UserId": "pn_15055550100",
                    "UserAttributes": {
                        "Language": ["en"],
                        "FirstName": ["John"],
                        "PhysicalAddress": ["NO ADDRESS ON FILE"],
                        "LastName": ["Stiles"]
                    }
                }
            }
        }
    }


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
    app.lambda_handler(pinpoint_event_message(), None)
    response = client.get_item(
        TableName='MESSAGING_TABLE',
        Key={'pk': {'S': '15055550100'}},
    )
    assert response['Item']['conversation_status'][
               'S'] == 'WAITING_ON_INITIAL_RESPONSE'
