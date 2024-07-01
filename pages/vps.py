#import streamlit as st
#import boto3
#import pandas as pd
#from io import StringIO
#
### we first need the aws connection -- NINA
#
## Initialize S3 client
#s3 = boto3.client('s3')
#
## Define the bucket name and object key
#bucket_name = 'aloftdata'
#object_key = 'bejab_vpts_20240101.csv'  # Replace with your actual file name
#
## Fetch the object from S3
#obj = s3.get_object(Bucket=bucket_name, Key=object_key)
#data = obj['Body'].read().decode('utf-8')
#
## Load data into a DataFrame
#df = pd.read_csv(StringIO(data))
#
## Display data in Streamlit
#st.write("### VisAviS Aloft data test")
#st.write(df)
