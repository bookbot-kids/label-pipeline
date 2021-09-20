{
  "Comment": "Invoke Transcribe Lambda function after 10 minutes.",
  "StartAt": "WaitState",
  "States": {
    "WaitState": {
      "Type": "Wait",
      "Seconds": 120,
      "Next": "Transcribe"
    },
    "Transcribe": {
      "Type": "Task",
      "Resource": "arn:aws:lambda:ap-southeast-1:283031858316:function:my-s3-function",
      "End": true
    }
  }
}