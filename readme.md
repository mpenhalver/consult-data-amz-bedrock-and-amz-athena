
# Consult data with Amazon Bedrock and Amazon Athena

## Pre-Requirements

1. It is recommended to run this sample in a **sandbox account**. The sample has no tests and not all security best practices are implemented.
2. Python v3.12
3. Docker installed
4. [Manage Amazon Bedrock model access](https://docs.aws.amazon.com/bedrock/latest/userguide/model-access.html) based on the models you will use


## Steps-to-start

1. **Create your ECR Repo and push your Docker Image**

    ```bash
        aws ecr create-repository --repository-name poc-app
        aws ecr get-login-password --region <your-region> | docker login --username AWS --password-stdin <your-account-id>.dkr.ecr.<your-region>.amazonaws.com
        docker build -t poc-app --platform linux/amd64 .
        docker tag poc-app:latest <your-account-id>.dkr.ecr.<your-region>.amazonaws.com/poc-app:latest
        docker push <your-account-id>.dkr.ecr.<your-region>.amazonaws.com/poc-app:latest
    ```

2. **Deploy your CloudFormation stack**

    ```bash
        chmod +x deploy.sh
        ./deploy.sh
    ```

3. **Run Glue Crawler**

    Run Glue Crawler to import CSV files and point to S3 poc-table-data

4. **Access your App**
    
    Access your App getting ALB URL that is available in Output section from CloudFormation stack

## Features

### Model Selection
The application now includes a dropdown menu that allows users to select which Amazon Bedrock model to use for:
- Generating SQL queries from natural language questions
- Creating natural language responses from SQL query results

Available models include:
- Claude 3.5 Sonnet (default)
- Claude 3 Haiku
- Claude 3 Opus
- Claude Instant
- Meta Llama 2 (13B and 70B variants)
- Amazon Titan Text

**Note:** Make sure you have enabled access to all the models you want to use in your Amazon Bedrock console. See [Manage Amazon Bedrock model access](https://docs.aws.amazon.com/bedrock/latest/userguide/model-access.html) for more information.

