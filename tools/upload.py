import os
import argparse
import time
import datetime

import s3_utils
import hgapi


def Upload():  
    repo = hgapi.hgapi.Repo('.')
    repositoryFiles = repo.hg_command('locate').split()
    #['A', 'R', 'M', 'D', '!'] --> files
    filesPerStatus = repo.hg_status()
    for st, files in filesPerStatus.items():
        for i,f in enumerate(files):
            #norm path as this is the way it is represented at s3
            filesPerStatus[st][i] = f.replace('\\','/')
    
    #don't upload files which are not commited
    for f in repositoryFiles[:]:        
        if any(f in [stFile.replace('\\','/') for stFile in files] for st, files in filesPerStatus.items()):
            print 'skipping %s' % f
            repositoryFiles.remove(f)
         
    s3_utils.UploadFiles('sam-sam', repositoryFiles)
        
if __name__ == '__main__':
    cmdLineParser = argparse.ArgumentParser(description = "update Amazon s3 with changes")    
    cmdLine = cmdLineParser.parse_args()      
    
    Upload()