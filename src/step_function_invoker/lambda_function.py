import json
import boto3
import uuid

sfn_client = boto3.client("stepfunctions")


def lambda_handler(event, context):
    transactionId = str(uuid.uuid1())

    response = sfn_client.start_execution(
        stateMachineArn="arn:aws:states:ap-southeast-1:283031858316:stateMachine:TranscribeStateMachine",
        name=transactionId,
        input=json.dumps(event),
    )
