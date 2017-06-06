import os
import mail
import datetime
import boto
from boto.s3.key import Key

aws_access_key_id, aws_secret_access_key = 'AKIAJDM6P2WHBAVLVU3A', 'WzT0prfnfuV2DQV4CkG1kWAfdcOLtkN9l3d3n+YK'


def GetFileModified(file_path):
    t = os.path.getmtime(file_path)            
    return datetime.datetime.fromtimestamp(t).replace(microsecond=0)

def GetKeyModified(key):
    
    dt = boto.utils.parse_ts(key.last_modified)
    if 'GMT' in str(key.last_modified):             
        dt = dt + datetime.timedelta(seconds = 3*60*60)
    
    return dt
    
def UploadFiles(bucket, files):
    s3 = boto.connect_s3(aws_access_key_id, aws_secret_access_key)    
    b = s3.get_bucket(bucket)
    
    for s3Key in files:
            upload = False
            k = b.get_key(s3Key)
            
            if not k:
                k = Key(b)
                k.key = s3Key
                upload = True
            else:
                s3_dt = GetKeyModified(k)
                local_dt = GetFileModified(s3Key)
                
            #upload only if local file has a timestamp newer than that in s3 storage
                if local_dt > s3_dt:
                    upload = True                
            
            #update only if local file has a timestamp older than that in s3 storage
            if upload:
                print 'uploading %s' % k            
                k.set_contents_from_filename(s3Key)
    

def DownloadFiles(bucketName, customer_name):
    s3 = boto.connect_s3(aws_access_key_id, aws_secret_access_key)    
    bucket = s3.get_bucket(bucketName)    
    
    #download specific files for client
    customerName = GetCustomerName(customer_name)
    
    files = []
    
    for ck, filePath in GetCustomersKeys(bucket, customerName):        
        if Download(filePath, ck):
            files.append(ck.name)
        
    for ck, filePath in GetRootKeys(bucket):        
        if Download(filePath, ck):
            files.append(ck.name)
            
    if len(files):
        
        mail.MailGunMail().send(to=['omerbach@gmail.com'], 
                                        fromMail = 'sam@sam.sam',
                                        subject = '%s - customers download report - %s' % (customerName, str(datetime.date.today())),
                                        message = '\n'.join(files), 
                                        html = False
                                        )        
        
def Download(filePath, ck): 
    download = False        
    foldersTree = os.path.dirname(filePath)

    #makedirs is angry when the folder already exists
    if foldersTree and not os.path.exists(foldersTree):
        os.makedirs(foldersTree)
        download = True
        
    elif not os.path.exists(filePath):
        download = True
       
    #file exists, lets check if it is older than that in s3 
    else:
        s3_dt = GetKeyModified(ck)
        local_dt = GetFileModified(filePath)                        
    
        #update only if local file has a timestamp older than that in s3 storage
        if s3_dt > local_dt:
            download = True
         
    if download:   
        print 'downloading %s --> %s' % (ck, filePath)
        ck.get_contents_to_filename(filePath)
        
    return download
        
        
#download general files        
def GetRootKeys(bucket):
    b = bucket
    
    for key in (k for k in b.list() if k.size and 'customer_specific' not in k.name ):
        yield key, key.name
            
#download specific files for customer        
def GetCustomersKeys(bucket, customer_name):
    b = bucket    
    
    if customer_name:
        for customerKey in (k for k in b.list(prefix='customer_specific/%s' % customer_name) if k.size ):
            yield customerKey, customerKey.name.replace('customer_specific/%s/' % customer_name, '')    

def GetCustomerName(customerName=None):
    from ConfigParser import SafeConfigParser
    import codecs
    
    if customerName:
        return customerName
    
    parser = SafeConfigParser()
    
    # Open the file with the correct encoding
    #config.ini file is encoded with utf-8 with bom (saved by notepad) so use utf_8_sig for SafeConfigParser to ignore it
    if os.path.exists('debt.ini'):
        with codecs.open('debt.ini', 'r', encoding='utf_8_sig') as f:
            parser.readfp(f) 

            customerName = parser.get('authentication', 'identifier')
            return customerName
            
    else:
        return
