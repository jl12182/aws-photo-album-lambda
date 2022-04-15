import base64
import io
import json
import time
from base64 import decodebytes

import boto3
import requests
from aws_requests_auth.aws_auth import AWSRequestsAuth
from opensearchpy import OpenSearch, RequestsHttpConnection
from requests_aws4auth import AWS4Auth


def lambda_handler(event, context):
    S3_details = event['Records'][0]['s3']
    bucket = event['Records'][0]['s3']['bucket']['name']
    photo = event['Records'][0]['s3']['object']['key']
    timeStamp = time.time()
    s3_client = boto3.client('s3')
    s3_clientobj = s3_client.get_object(Bucket=bucket, Key=photo)
    body = s3_clientobj['Body'].read()
    image = base64.b64decode(body)

    print("image uploaded")

    # response=s3_client.delete_object(Bucket=bucket,Key=photo)
    # response=s3_client.put_object(Bucket=bucket, Body=image, Key=photo,ContentType='image/jpg')

    client = boto3.client('rekognition')
    response = client.detect_labels(Image={'S3Object':{'Bucket':bucket,'Name':photo}}, MaxLabels=10)

    detected_labels = response['Labels']
    print(detected_labels)

    combined_labels=[]
    for label in detected_labels:
        combined_labels.append(label['Name'])


    meta_response = s3_client.head_object(Bucket=bucket,Key=photo)
    custom_labels = meta_response['Metadata']
    combined_labels.append(custom_labels['customlabels'])

    print(combined_labels)

    format={
        'objectKey':photo,
        'bucket':bucket,
        'createdTimeStamp':timeStamp,
        'labels':combined_labels
    }

    host='search-photos-7sgbt5rvbqhxhl6255irtfbfmy.us-east-1.es.amazonaws.com'
    region = 'us-east-1'
    service = 'es'

    # AWS Credentials
    credentials = boto3.Session().get_credentials()
    awsauth = AWS4Auth(credentials.access_key, credentials.secret_key, region, service, session_token=credentials.token)

    opensearch_client = OpenSearch(
        hosts = [{'host': host, 'port': 443}],
        http_auth = ('jl12182', 'August@781'),
        use_ssl = True,
        verify_certs = True,
        connection_class = RequestsHttpConnection
    )

    opensearch_payload=json.dumps(format).encode("utf-8")
    # awsauth = AWSRequestsAuth(aws_access_key='',
    #                   aws_secret_access_key='',
    #                   aws_host=host,
    #                   aws_region='us-east-1',
    #                   aws_service='es')

    # esClient = Elasticsearch(
    #     hosts=[{'host': host, 'port':443}],
    #     use_ssl=True,
    #     http_auth=awsauth,
    #     verify_certs=True,
    #     connection_class=RequestsHttpConnection)


    opensearch_response = opensearch_client.index(index='photos', doc_type='photo', body=format)
    print(opensearch_response)
