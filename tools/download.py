import os
import argparse
import time
import datetime

import boto
from boto.s3.key import Key

import s3_utils


def Download(customerName = None):
    
    s3_utils.DownloadFiles('sam-sam', customerName)

if __name__ == '__main__':
    cmdLineParser = argparse.ArgumentParser(description = "update Amazon s3 with changes")    
    cmdLineParser.add_argument('-c', '--customer')    
    cmdLine = cmdLineParser.parse_args()      
    
    Download(cmdLine.customer)