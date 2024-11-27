#!/bin/bash

# Primeiro, criar o stack
aws cloudformation create-stack --stack-name poc-app-stack --template-body file://poc-app-stack.yaml --capabilities CAPABILITY_IAM

# Esperar o stack ser criado
aws cloudformation wait stack-create-complete --stack-name poc-app-stack

# Account ID
ACCOUNTID=$(aws sts get-caller-identity --query Account --output text)

# Fazer upload dos arquivos
aws s3 cp data/schools.csv s3://$ACCOUNTID-poc-table-data/Schools/
aws s3 cp data/students.csv s3://$ACCOUNTID-poc-table-data/Students/
aws s3 cp data/table_structures.json s3://$ACCOUNTID-poc-config-data/
