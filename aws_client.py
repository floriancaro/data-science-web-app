import os
import boto3
import sys
import streamlit as st
import json

# get your credentials from environment variables -----
aws_id = st.secrets['AWS_KEY']
aws_secret = st.secrets['AWS_KEY_SECRET']
aws_region = st.secrets['AWS_REGION']

client = boto3.client('s3', aws_access_key_id=aws_id,
        aws_secret_access_key=aws_secret, region_name=aws_region)

bucket_name = 'hired-foreigners'

# object_key = 'df_oyatoi_simplified.csv'
object_key = 'publish_wo_katakana.csv'
csv_obj = client.get_object(Bucket=bucket_name, Key=object_key)
body = csv_obj['Body']
csv_string = body.read().decode('utf-8')

json_key = "oyatoi_geojson_simplified.json"
json_content = client.get_object(Bucket=bucket_name, Key=json_key)['Body'].read().decode('utf-8')
# json_content = json.loads(file_content)

# df = pd.read_csv(StringIO(csv_string))
