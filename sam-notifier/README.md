# SAM Notifier (sam-notifier)

This project contains source code and supporting files for a serverless application that you can deploy with the SAM CLI. It includes the following files and folders:

- functions - Code for the application's Lambda functions to respond to CIS AWS Foundations Benchmark CloudWatch Alarms.
- statemachines - Definition for the state machine that orchestrates the notification workflow.
- template.yaml - A template that defines the application's AWS resources.

This application creates a AWS Step Functions workflow coupled with event-driven approach using Amazon EventBridge to respond to CIS AWS Foundations Benchmark CloudWatch Alarms provisioned via the [CIS-alarms-cfn.yml](https://github.com/rewindio/aws-security-hub-CIS-metrics/blob/main/CIS-alarms-cfn.yml) CloudFormation template. The event detail information is saved in a Amazon DynamoDB table, as well as supplied to a Jira Cloud issue.

The application uses several AWS resources, including Step Functions state machines, Lambda functions and an EventBridge rule. These resources are defined in the `template.yaml` file in this project. You can update the template to add AWS resources through the same deployment process that updates your application code.

## Deploy the sample application

The Serverless Application Model Command Line Interface (SAM CLI) is an extension of the AWS CLI that adds functionality for building and testing Lambda applications. It uses Docker to run your functions in an Amazon Linux environment that matches Lambda.

To use the SAM CLI, you need the following tools:

* SAM CLI - [Install the SAM CLI](https://docs.aws.amazon.com/serverless-application-model/latest/developerguide/serverless-sam-cli-install.html)
* [Python 3 installed](https://www.python.org/downloads/)
* Docker - [Install Docker community edition](https://hub.docker.com/search/?type=edition&offering=community)

To build and deploy your application for the first time, run the following in your shell:

```bash
sam build --use-container
sam deploy --guided
```

The first command will build the source of your application. The second command will package and deploy your application to AWS, with a series of prompts:

* **Stack Name**: The name of the stack to deploy to CloudFormation. This should be unique to your account and region, and a good starting point would be something matching your project name.
* **AWS Region**: The AWS region you want to deploy your app to.
* **Parameter LogGroupName**: Name of the CloudWatch Logs log group used CloudTrail
* **Jira Url**: Jira REST API URL (ex. https://<org-name>.atlassian.net/rest/api/2)
* **Jira Project Key**: Jira project key
* **Jira Auth Token**: Jira Basic Auth token [Atlassian Developer - Basic auth for REST APIs](https://developer.atlassian.com/cloud/jira/platform/basic-auth-for-rest-apis/)
* **Confirm changes before deploy**: If set to yes, any change sets will be shown to you before execution for manual review. If set to no, the AWS SAM CLI will automatically deploy application changes.
* **Allow SAM CLI IAM role creation**: Many AWS SAM templates, including this example, create AWS IAM roles required for the AWS Lambda function(s) included to access AWS services. By default, these are scoped down to minimum required permissions. To deploy an AWS CloudFormation stack which creates or modifies IAM roles, the `CAPABILITY_IAM` value for `capabilities` must be provided. If permission isn't provided through this prompt, to deploy this example you must explicitly pass `--capabilities CAPABILITY_IAM` to the `sam deploy` command.
* **Save arguments to samconfig.toml**: If set to yes, your choices will be saved to a configuration file inside the project, so that in the future you can just re-run `sam deploy` without parameters to deploy changes to your application.

## Use the SAM CLI to build locally

Build the Lambda functions in your application with the `sam build --use-container` command.

```bash
sam-notifier$ sam build --use-container
```

The SAM CLI installs dependencies defined in `functions/*/requirements.txt`, creates a deployment package, and saves it in the `.aws-sam/build` folder.

## Cleanup

To delete the sample application that you created, use the AWS CLI. Assuming you used your project name for the stack name, you can run the following:

```bash
aws cloudformation delete-stack --stack-name sam-notifier
```
