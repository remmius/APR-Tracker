#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Fri Jul 30 18:25:13 2021

@author: klaus
"""
import csv
import time
#etherscan-python
from etherscan import Etherscan
import os
eth = Etherscan(os.getenv('ETHERSCAN-API-KEY'))

#web3
from web3 import Web3
w3 = Web3(Web3.HTTPProvider(os.getenv('WEB3_HTTP_PROVIDER')))

from google.cloud import storage
storage_client = storage.Client()
BUCKET_NAME=os.getenv('DATA_BUCKET')

BASE_PATH="/tmp/"

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

def upload_blob(bucket_name, source_file_name, destination_blob_name):
    """Uploads a file to the bucket."""
    # The ID of your GCS bucket
    # bucket_name = "your-bucket-name"
    # The path to your file to upload
    # source_file_name = "local/path/to/file"
    # The ID of your GCS object
    # destination_blob_name = "storage-object-name"

    bucket = storage_client.bucket(bucket_name)
    blob = bucket.blob(destination_blob_name)

    blob.upload_from_filename(source_file_name)

    print(
        "File {} uploaded to {}.".format(
            source_file_name, destination_blob_name
        )
    )
        
def get_shareprice(contract_add,abi):
    contract = w3.eth.contract(contract_add, abi=abi)

    if "pricePerShare" in abi:
        shareprice=contract.functions.pricePerShare().call()/10**18
    if "get_virtual_price" in abi:
    #print(contract_add)
        shareprice=contract.functions.get_virtual_price().call()/10**18
    return shareprice     

def get_ABI(contract_add):
    file=str(contract_add)+".json"
    try:
        download_blob(BUCKET_NAME, file, BASE_PATH+file)
        f=open(BASE_PATH+file,"r")
        abi=f.read()
    except IOError:
        abi=eth.get_contract_abi(contract_add)
        with open(BASE_PATH+file, 'x') as f:
            f.write(abi)
        upload_blob(BUCKET_NAME, BASE_PATH+file, file)
    return abi

def update_file():
    csv_row=list()
    csv_row.append(int(time.time()))
    for contract_name in Contracts.keys():  
        contract_add=Contracts[contract_name]
        abi=get_ABI(contract_add)
        csv_row.append(contract_name)
        csv_row.append(get_shareprice(contract_add,abi))
        
    file='history_apy.csv'    
    with open(BASE_PATH+file, 'a') as f:
        writer = csv.writer(f)
        writer.writerow(csv_row)
    upload_blob(BUCKET_NAME, BASE_PATH+file, file)
    upload_blob(BUCKET_NAME, BASE_PATH+file, 'history_apy_backup.csv')

def updated_required(freq_s=3600*24):
    try:
        file='history_apy.csv'  
        download_blob(BUCKET_NAME, file, BASE_PATH+file)
        with open(BASE_PATH+file, 'r') as f:
            data=f.readlines()
            if(int(time.time())-int(data[-1].split(",")[0]) > freq_s):
                return True
        print("No update required")
        return False
    except:
        return True

def get_apr_data(request):    
    if(updated_required(3600)):
        update_file()
