import json
import math
import dateutil.parser
import datetime
import time
import os
import logging
import boto3
import requests
import urllib.parse
from aws_requests_auth.aws_auth import AWSRequestsAuth
from opensearchpy import OpenSearch, RequestsHttpConnection
import random

logger = logging.getLogger()
logger.setLevel(logging.INFO)

headers = { "Content-Type": "application/json" }
region = 'us-west-2'

def get_labels(query):
    lex = boto3.client('lex-runtime')
    response = lex.post_text(
        botName='PhotoQuery',
        botAlias='dev',
        userId='root',
        inputText=query
    )


    labels = []
    if 'slots' not in response:
        print("No photo collection for query {}".format(query))
    else:
        print ("slot: ",response['slots'])
        slot_val = response['slots']
        for key,value in slot_val.items():
            if value!=None:
                labels.append(value)
    return labels


def get_photo_path(keys):
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


    resp = []
    for key in keys:
        if (key is not None) and key != '':
            searchData = opensearch_client.search({"query": {"match": {"labels": key}}})
            resp.append(searchData)
    # print(resp)

    output = []
    for r in resp:
        if 'hits' in r:
            for val in r['hits']['hits']:
                key = val['_source']['objectKey']
                if key not in output:
                    output.append('s3://csgyb2/'+key)
    # print (output)
    return output

def lambda_handler(event, context):
    # q1 = event["queryStringParameters"]["q"]
    # labels = get_labels(q1)
    logger.info("event is ****************************")
    logger.info(event)

    q1 = event["queryStringParameters"]["q"]

    labels = get_labels(q1)
    print(labels)

    img_paths = []
    if len(labels) != 0:
        img_paths = get_photo_path(labels)

    response_body = {
            'imagePaths':img_paths,
            'userQuery':q1,
            'labels': labels,}

    if not img_paths:
        return{
            'statusCode':200,
            'headers':
                {
                    "Access-Control-Allow-Origin":"*",
                    "Access-Control-Allow-Headers":"Content-Type",
                    "Access-Control-Allow-Methods":"OPTIONS,GET"
                },
            #'body': json.dumps('No Results found')
            'body':json.dumps(response_body),
        }
    else:

        return{
            'statusCode': 200,
            'headers':
                {
                    "Access-Control-Allow-Origin":"*",
                    "Access-Control-Allow-Headers":"Content-Type",
                    "Access-Control-Allow-Methods":"OPTIONS,GET"
                },
            'body':json.dumps(response_body),
            'isBase64Encoded': False
        }