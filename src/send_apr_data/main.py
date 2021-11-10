#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Fri Jul 30 18:25:13 2021

@author: klaus
"""
from prettytable import PrettyTable
import os

from google.cloud import storage
storage_client = storage.Client()
BUCKET_NAME=os.getenv('DATA_BUCKET')

BASE_PATH="/tmp/"
RECIEVER_EMAIL="xxx@yyy.de"
Contracts={
        "Yearn-crvDUSD":"0x30FCf7c6cDfC46eC237783D94Fc78553E79d4E9C",
        "Yearn-crvUSDN":"0x3B96d491f067912D18563d56858Ba7d6EC67a6fa",
        "Yearn-crvBBTC":"0x8fA3A9ecd9EFb07A8CE90A6eb014CF3c0E3B32Ef",
        "Yearn-crvOBTC":"0xe9Dc63083c464d6EDcCFf23444fF3CFc6886f6FB",

        "CURVE-crvDUSD":"0x8038C01A0390a8c547446a0b2c18fc9aEFEcc10c",
        "CURVE-crvUSDN":"0x0f9cb53Ebe405d49A0bbdBD291A65Ff571bC83e1",        

        "CURVE-crvOBTC":"0xd81dA8D904b52208541Bade1bD6595D8a251F8dd",
        "CURVE-crvBBTC":"0x071c661B4DeefB59E2a3DdB20Db036821eeE8F4b",
        
        "Yearn-crvUSDP":"0xC4dAf3b5e2A9e93861c3FBDd25f1e943B8D87417",
        "CURVE-crvUSDP":"0x42d7025938bEc20B69cBae5A77421082407f053A",
        
        "Yearn-crvEURS":"0x25212Df29073FfFA7A67399AcEfC2dd75a831A1A",
        "CURVE-crvEURS":"0x0Ce6a5fF5217e38315f87032CF90686C96627CAA",
        
        "Yearn-USDC":"0x5f18C75AbDAe578b483E5F43f12a39cF75b973a9",
        
        "Yearn-crvPBTC":"0x3c5DF3077BcF800640B5DAE8c91106575a4826E6",
        "CURVE-crvPBTC":"0x7F55DDe206dbAD629C080068923b36fe9D6bDBeF",
        
        "Yearn-crvTBTC":"0x23D3D0f1c697247d5e0a9efB37d8b0ED0C464f7f",
        "CURVE-crvTBTC":"0xC25099792E9349C7DD09759744ea681C7de2cb66",
        
        "Yearn-crvMIM":"0x2DfB14E32e2F8156ec15a2c21c3A6c053af52Be8",
        "CURVE-crvMIM":"0x5a6A4D54456819380173272A5E8E9B9904BdF41B",
        }

def download_blob(bucket_name, source_blob_name, destination_file_name):
    """Downloads a blob from the bucket."""
    # bucket_name = "your-bucket-name"
    # source_blob_name = "storage-object-name"
    # destination_file_name = "local/path/to/file"

    bucket = storage_client.bucket(bucket_name)
    blobs = storage_client.list_blobs(bucket_name)
    for blob in blobs:
        print(blob.name)
        if (blob.name == source_blob_name):
            # Construct a client side representation of a blob.
            # Note `Bucket.blob` differs from `Bucket.get_blob` as it doesn't retrieve
            # any content from Google Cloud Storage. As we don't need additional data,
            # using `Bucket.blob` is preferred here.
            blob = bucket.blob(source_blob_name)
            blob.download_to_filename(destination_file_name)
        
            print(
                "Blob {} downloaded to {}.".format(
                    source_blob_name, destination_file_name
                )
            )
          

def calc_apr(row_new,row_old,index):
    dy=float(row_new.split(",")[2+2*index])-float(row_old.split(",")[2+2*index])
    dt=int(row_new.split(",")[0])-int(row_old.split(",")[0]) 
    apr=round(dy/dt*3600*24*365*100,1)
    return apr

def get_row_with_age(data,age):
    t_now=int(data[-1].split(",")[0])
    for k in range(len(data)-1):
        print(data[-(1+k)])
        if (t_now - int(data[-(1+k)].split(",")[0]) > age):
            return data[-(1+k)].split("\n")[0]
    print("no row with age of ",age,"found")
    return data[1].split("\n")[0]

from datetime import datetime
def create_timestamp_diff(row_new,row_old):
    return datetime.utcfromtimestamp(int(row_old.split(",")[0])).strftime('%d.%m.%Y')+"-"+datetime.utcfromtimestamp(int(row_new.split(",")[0])).strftime('%d.%m.%Y')

def create_timestamp_diff_short(row_new,row_old):
    return datetime.utcfromtimestamp(int(row_old.split(",")[0])).strftime('%d.%m')+"-"+datetime.utcfromtimestamp(int(row_new.split(",")[0])).strftime('%d.%m')

    
def get_last_apr():
    file='history_apy.csv'  
    download_blob(BUCKET_NAME, file, BASE_PATH+file)
    apy_data=dict()
    with open(BASE_PATH+file, 'r') as f:
        data=f.readlines()  
    for n in range(int((len(data[-1].split(","))-1)/2)):
        name=data[-1].split(",")[1+2*n]
        #if not ("CURVE" in name):
        if not ("USDC" in name):
                total_row=data[1].split("\n")[0]
                last_row=data[-1].split("\n")[0]
                month_row=get_row_with_age(data,3600*24*365/12*3)
                bi_week_row=get_row_with_age(data,3600*24*365/12*1)
                week_row=get_row_with_age(data,3600*24*7)
                
                apr_total=calc_apr(last_row,total_row,n)
                time_total=create_timestamp_diff(last_row,total_row)   
                
                apr_month=calc_apr(last_row,month_row,n)
                time_month=create_timestamp_diff_short(last_row,month_row)
                
                apr_week=calc_apr(last_row,week_row,n)
                time_week=create_timestamp_diff_short(last_row,week_row)
                
                apr_biweek=calc_apr(last_row,bi_week_row,n) 
                time_biweek=create_timestamp_diff_short(last_row,bi_week_row)
                
                apy_data["Time-period"]=[time_week,time_biweek,time_month,time_total]
                apy_data[name]=[apr_week,apr_biweek,apr_month,apr_total]
    print(apy_data)
    apy_data_final=dict()
    apy_data_final["Time-period"]=[time_week,time_biweek,time_month,time_total]
    for key in apy_data.keys():
        if ("Yearn" in key):
            yearn_apy=apy_data[key]
            curve_key="CURVE-crv"+key.split("crv")[1]        
            curve_apy=apy_data.get(curve_key,[0,0,0,0])
            apy_data_final[key]=list()
            for k in range(len(yearn_apy)):
                combined_apy=round(((yearn_apy[k]/100+1)*(curve_apy[k]/100+1)-1)*100,1)
                apy_data_final[key].append(combined_apy)
    print(apy_data_final)
    return apy_data_final
    
def prepare_email(data):   
    
    table = PrettyTable()
    headline=["Pool","Weekly[%] ","Monthly[%]", "Tri-Monthly[%]", "Total-APR[%"]    
    table.field_names = headline
    #fill table
    for pool in data:
        row=[pool]+data[pool] 
        table.add_row(row)
    print(table.get_string())
    return table.get_string()
    
def send_email(data):
    from email.mime.text import MIMEText
    from email.mime.multipart import MIMEMultipart
    import smtplib, ssl
    port = 587  # For starttls
    smtp_server = "smtp.gmail.com"
    sender_email = os.getenv('EMAIL_USER')
    password=os.getenv('EMAIL_PWD')
    receiver_email = [RECIEVER_EMAIL]
    
    table=prepare_email(data)
    context = ssl.create_default_context()
    with smtplib.SMTP(smtp_server, port) as server:    
        server.starttls(context=context)    
        server.login(sender_email, password)    
        for reciever in receiver_email:
                message = MIMEMultipart("alternative")
                message["Subject"] = "My Crypto update"
                message["From"] = sender_email        
                text=table
                part1 = MIMEText(text, "plain")
                message.attach(part1)
                message["To"] = reciever
                server.sendmail(message["From"], message["To"], message.as_string())

def send_apr_data(request):    
    last_apr=get_last_apr()
    send_email(last_apr)
    
