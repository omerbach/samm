import sqlite3
import os
import signal

import utils
def Kill():
   
    theProcess = utils.GetSamProcess()
    if theProcess:
        try:
            print 'killing process %d' % theProcess
            os.kill(theProcess, signal.SIGBREAK)
        #unknow process Id
        except WindowsError:
            pass
        
if __name__ == '__main__':
    Kill()