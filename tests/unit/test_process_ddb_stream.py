import json
import os
from unittest import mock
import boto3
import botocore.session
import pytest
from moto import mock_dynamodb
from botocore.stub import Stubber
from process_ddb_stream import app


def dynamodb_stream_event_message_insert():
    return {
        "Records": [
            {
                "eventName": "INSERT",
                "dynamodb": {
                    "Keys": {
                        "pk": {"S": "15055550100"}
                    },
                    "NewImage": {
                        "pk": {"S": "15055550100"},
                        "first_name": {"S": "John"},
                        "Language": {"S": "EN"},
                        "last_name": {"S": "Stiles"},
                        "opted_out": {"BOOL": True},
                        "dob": {"S": "01/01/2000"}
                    }
                }
            }
        ]
    }

def dynamodb_stream_event_message_remove():
    return {
        "Records": [
            {
                "eventName": "REMOVE",
                "dynamodb": {
                    "Keys": {
                        "pk": {"S": "15055550100"}
                    },
                    "NewImage": {
                        "pk": {"S": "15055550100"},
                        "first_name": {"S": "John"},
                        "Language": {"S": "EN"},
                        "last_name": {"S": "Stiles"},
                        "opted_out": {"BOOL": True},
                        "dob": {"S": "01/01/2000"}
                    }
                }
            }
        ]
    }

def boto3_client_side_effect_pinpoint_send_success(*args, **kwargs):
    if args[0] == 'pinpoint':
        pinpoint = botocore.session.get_session().create_client('pinpoint')
        stubber = Stubber(pinpoint)
        stubber.add_response(
            'update_endpoint',
            {
                'MessageBody': {
                    'Message': 'string',
                    'RequestID': 'string'
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
def test_lambda_handler_insert():
    boto3.setup_default_session()
    mock.MagicMock(name='mock_verifier')
    with mock.patch('boto3.client',
                    mock.MagicMock(side_effect=boto3_client_side_effect_pinpoint_send_success)):
        ret = app.lambda_handler(dynamodb_stream_event_message_insert(), None)
    assert ret is True

@mock_dynamodb
@mock.patch.dict(os.environ, {'TABLE': 'MESSAGING_TABLE'})
@mock.patch.dict(os.environ, {'APP': 'abc123'})
def test_lambda_handler_remove():
    boto3.setup_default_session()
    mock.MagicMock(name='mock_verifier')
    with mock.patch('boto3.client',
                    mock.MagicMock(side_effect=boto3_client_side_effect_pinpoint_send_success)):
        ret = app.lambda_handler(dynamodb_stream_event_message_remove(), None)
    assert ret is None



