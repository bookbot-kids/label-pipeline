"""
Copyright 2022 [PT BOOKBOT INDONESIA](https://bookbot.id/)

Licensed under the Apache License, Version 2.0 (the "License");
you may not use this file except in compliance with the License.
You may obtain a copy of the License at

    http://www.apache.org/licenses/LICENSE-2.0

Unless required by applicable law or agreed to in writing, software
distributed under the License is distributed on an "AS IS" BASIS,
WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
See the License for the specific language governing permissions and
limitations under the License.
"""

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
