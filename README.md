# Multi-Lingual Interactive SMS For Medicaid Unwinding

An interactive multi-lingual interactive text messaging workflow for updating member information for Medicaid unwinding.

## Architecture

![Overall Architecture Diagram](./docs/arch-overview.png "Overall Architecture Diagram")

## Workflow

1. Administrator or automated process loads contacts into Amazon DynamoDB Contact table
2. User contacts are automatically imported into Amazon Pinpoint segments (via DynamoDB Streams to the `ProcessDDBStream` function)
3. Administrator initiates initial text message broadcast via Amazon Pinpoint Journey, sending to the users within the segments
   1. After the initial text message is sent the Journey workflow triggers the `MarkConversationInitiated` Lambda function to update the Contact Table to mark the contact as having been sent the initial engagement text.
4. Users respond to the text message, which Pinpoint sends to the `ReceiveSMSMessages` Lambda function via SNS and SQS.
5. The Lambda functions queries the DynamoDB contact information and the analyses the user's text to update the database and send a reply text via Pinpoint.
6. Steps 4 and 5 repeat until the conversation reaches a terminal state.

Reporting is accomplished via Amazon QuickSight accessing data in DynamoDB via the DynamoDB/Athena connector.

## Security

See [CONTRIBUTING](CONTRIBUTING.md#security-issue-notifications) for more information.

## License

This library is licensed under the MIT-0 License. See the [LICENSE](LICENSE) file.
