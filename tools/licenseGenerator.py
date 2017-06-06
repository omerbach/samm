# -*- coding: utf8 -*-
import time
import datetime
import os
import argparse

import bottle
import utils
import dates

def UpdateLicense(d):
    
    expiry = int(time.mktime(time.strptime('%s 12:27:00' % str(d), utils.dt_pattern)))
    
    authFile = 'web/misc/pgp/auth.txt'
    if not os.path.exists(authFile):
        return
    
    authTxt = file(authFile).read()
    start , end = '5sX2RBAiZT', 'Yl0n'
    
    startPos = authTxt.find(start)
    
    if startPos == -1:
        return
    
    endPos = authTxt.find(end)
    
    if endPos == -1:
        return
    
    currentExpiry = authTxt[startPos + len(start) : endPos]
    newAuth = authTxt.replace(currentExpiry, str(expiry))
        
    with file('web/misc/pgp/auth.txt', 'wb') as fpo:
        fpo.write(newAuth)

if __name__ == '__main__':
        
    cmdLineParser = argparse.ArgumentParser(description=__doc__)
    cmdLineParser.add_argument('-d', '--date')    
    cmdLine = cmdLineParser.parse_args()
    
    d = dates.date(cmdLine.date)        
    UpdateLicense(d)
    
    