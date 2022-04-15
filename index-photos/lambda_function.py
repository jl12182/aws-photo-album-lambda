import json
import boto3
from aws_requests_auth.aws_auth import AWSRequestsAuth
import time
from opensearchpy import OpenSearch, RequestsHttpConnection
import requests
import io
import base64
from base64 import decodestring

def lambda_handler(event, context):
    S3_details=event['Records'][0]['s3']
    bucket=event['Records'][0]['s3']['bucket']['name']
    photo=event['Records'][0]['s3']['object']['key']
    timeStamp=time.time()
    s3_client = boto3.client('s3')
    s3_clientobj = s3_client.get_object(Bucket=bucket, Key=photo)

    body=s3_clientobj['Body'].read()
    image = base64.b64decode(body)

    print("image uploaded")
    client=boto3.client('rekognition')
    response = client.detect_labels(Image={'S3Object':{'Bucket':bucket,'Name':photo}},
        MaxLabels=10)

    labels=response['Labels']
    custom_labels=[]
    for label in labels:
        custom_labels.append(label['Name'])
    meta_response = s3_client.head_object(Bucket=bucket, Key=photo)
    meta_labels = meta_response['Metadata'].get('customlabels')
    if meta_labels:
        meta_labels = meta_labels.split(', ')
        for meta_label in meta_labels:
            custom_labels.insert(0, meta_label)

    format={
        'objectKey':photo,
        'bucket':bucket,
        'createdTimeStamp':timeStamp,
        'labels':custom_labels
    }
    print(format)
    host='search-photos2-xgutg37tb5atub6h6tkcoku6he.us-west-2.es.amazonaws.com'
    region = 'us-west-2'
    service = 'es'

    opensearch_client = OpenSearch(
        hosts = [{'host': host, 'port': 443}],
        http_auth = ('hc3086', 'Ch@9706!'),
        use_ssl = True,
        verify_certs = True,
        connection_class = RequestsHttpConnection
    )

    temp=opensearch_client.index(index='photos', doc_type='photo', body=format)
    print("temp is")
    print(temp)
