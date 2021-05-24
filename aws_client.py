import os
import boto3
import sys

if sys.version_info[0] < 3:
    from StringIO import StringIO # Python 2.x
else:
    from io import StringIO # Python 3.x

# get your credentials from environment variables
aws_id = st.secrets['AWS_KEY']
aws_secret = st.secrets['AWS_KEY_SECRET']
aws_region = st.secrets['AWS_REGION']

client = boto3.client('s3', aws_access_key_id=aws_id,
        aws_secret_access_key=aws_secret, region_name=aws_region)

bucket_name = 'hired-foreigners'

object_key = 'df_oyatoi_simplified.csv'
csv_obj = client.get_object(Bucket=bucket_name, Key=object_key)
body = csv_obj['Body']
csv_string = body.read().decode('utf-8')

# df = pd.read_csv(StringIO(csv_string))
