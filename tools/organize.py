import sys
import os
import argparse
import datetime
import shutil
import time
import dateutil
from collections import defaultdict

import EXIF

import utils
import times
import dates

def GetModifiedTsStr(path):
    return str(GetModifiedTs(path))

def GetModifiedTs(path):
    return datetime.datetime.fromtimestamp(os.path.getmtime(path))

def IsVideo(suffix):   
    return suffix in ['.%s' % vid for vid in ('MP4', 'M2TS', 'MTS', 'MOV', 'AVI', 'WMA', 'MPG')]

def GetMaxDate(folder):
    return max(Retrieve(folder), key=lambda df:df[0])

def Retrieve(folder):
    for f in os.listdir(folder):
        fullPath = os.path.join(folder, f)
        try:
            with open(fullPath, 'rb') as fileObject:             
                #this is the 'date taken' attribute of the image
                tag = "EXIF DateTimeOriginal"                
             
                # get the tags and stop processing the file after reaching a tag (faster processing)
                data = EXIF.process_file(fileObject, details=False, stop_tag=tag)
                                      
                #if file has EXIT data, than it is a picture
                if data:                                                                
                    #not all pictures have the 'date taken' attribute
                    try:
                        #2012:12:18 15:40:52 -> 2012-12-18 15:40:52
                        d,t = str(data[tag]).split()
                        d = d.replace(':', '-')
                        ts = '%s %s' % (d, t)                    
                        yield dateutil.parser.parse(ts), fullPath
                        
                    except KeyError:                                    
                        pass
                else:
                    pass
                
        except IOError as e:
            print "I/O error({0}): {1}".format(e.errno, e.strerror)
            
        
class Picture(object):
    def __init__(self, folder, root, fileName, filePath, dateTimeTaken, suffix):
        self.folder = folder
        self.root = root
        self.fileName = fileName
        self.filePath = filePath
        self.dateTimeTaken = dateTimeTaken
        self.suffix = suffix
        
    @property
    def size(self):
        utils.GetFileSize(self.filePath)
        
def Organize(folders, maxDate):
    #main structure:
    #[PICTURES, VIDEOS, UNKNOWN] [TS] [list of files]    
    filesOf = defaultdict(
        lambda: defaultdict(list))    
                
    utils.Md(cmdLine.target)
    
    #we will organize files which have a time stamp which is bigger 
    dateTimeThreshold, maxFile = GetMaxDate(cmdLine.max_folder) if cmdLine.max_folder  else (datetime.datetime.combine(dates.date(cmdLine.date), times.parse_time(cmdLine.time)), None)
    if cmdLine.max_folder:
        print
        print "last date from '%s'\n was retrieved from '%s'\n and is '%s'" % (cmdLine.max_folder, maxFile, dateTimeThreshold.strftime("%A, %d. %B %Y %I:%M%p"))        
        print
    
    category = None
    ts = None
    
    for folder in folders:        
        for root, dirs, files in os.walk(folder):
            print 'scanning %s' % root
            print 'found %d files' % len(files)
            for f in files:             
                fullPath = os.path.join(root, f)
                suffix = os.path.splitext(fullPath)[1]
                
                with open(fullPath, 'rb') as fileObject:                
                             
                    pic = Picture(folder, root, f, fullPath, ts, suffix)
                    
                    #this is the 'date taken' attribute of the image
                    tag = "EXIF DateTimeOriginal"                
                  
                    # get the tags and stop processing the file after reaching a tag (faster processing)
                    data = EXIF.process_file(fileObject, details=False, stop_tag=tag)
                          
                    #if file has EXIT data, than it is a picture
                    if data:
                        category = 'PICTURES'
                        
                        #not all pictures have the 'date taken' attribute
                        try:
                            
                            ts = str(data[tag]).strip()
                            if ts and ts!='0000:00:00 00:00:00':                                
                                d,t = str(ts).split()
                                d = d.replace(':', '-')
                                ts = '%s %s' % (d, t)
                            else:
                                #use the 'last modified' attribute instead
                                ts = GetModifiedTsStr(fullPath)                                  
                            
                        except (KeyError, ValueError):                        
                            #use the 'last modified' attribute instead
                            ts = GetModifiedTsStr(fullPath)                            
                    
                    else:
                        #no data, could be a video or some other file
                        #use the 'last modified' attribute instead
                        ts = GetModifiedTsStr(fullPath)                
                        
                        if IsVideo(suffix.upper()):
                            category = 'VIDEOS'                    
                        else:
                            category = 'UNKNOWN'
                                    
                    dt = dateutil.parser.parse(ts)
                                        
                    if dt >= dateTimeThreshold:
                        filesOf[category][ts].append(pic)
    
    #now we have the main structure populated, lets dump the files
    for category, filesPerTs in filesOf.items():
        #go over all the pictures (normally should be one per ts)
            for ts, pictures in sorted(filesPerTs.items()):
                #2008-09-26 10:58:03 -> 2008_09_26 10_58_03
                newName = ts.replace('-', '_').replace(':', '_')
                
                root = os.path.join(cmdLine.target, category)
                utils.Md(root)
                
                #more than one picture with this time stamp, copy them to duplicates folder
                if len(pictures) > 1:
                    
                    dupDest = os.path.join(root, 'duplicates', newName)
                    utils.Md(dupDest)
                    
                    with open(os.path.join(dupDest, 'duplicates.tda'), 'wb') as report:
                        report.write('file\tsize\r\n')                        
                        
                        for i, pic in enumerate(pictures):                        
                            src =  pic.filePath
                            dst = os.path.join(dupDest, '%s_%d' %(newName, i+1) + pic.suffix)
                            
                            report.write('%s\t%d\r\n' % (pic.filePath, utils.GetFileSize(pic.filePath)))
                            
                            print '%s -> %s' % (src, dst)                            
                            shutil.copy2(src, dst)
                 
                #copy the largest one
                pic = max(pictures, key=lambda p : p.size)
                src =  pic.filePath
                dst = os.path.join(root, newName + pic.suffix)
                
                print '%s -> %s' % (src, dst)                
                shutil.copy2(src, dst)
                    
if __name__=='__main__':
          
    cmdLineParser = argparse.ArgumentParser(description="Validate we're balanced")    
        
    cmdLineParser.add_argument('-s', '--sources', nargs='+', help='folders to retrieve data from')
    cmdLineParser.add_argument('-d', '--date', default = '1978-11-29', help = 'search files newer than that date. use format YYYY-MM-DD')
    cmdLineParser.add_argument('-t', '--time', default = '09:00:00', help = 'search files newer than that date. use format HH:MM:SS')
    cmdLineParser.add_argument('-ta', '--target', required = 'True', help = 'target folder to organize files')        
    cmdLineParser.add_argument('-mf', '--max-folder', help = 'get the newest file from this folder and organize files which are newer than it')        
    
    
        
    cmdLine = cmdLineParser.parse_args()     
    cmdLine.sources = [utils.Normpath(s) for s in cmdLine.sources]
    cmdLine.target = utils.Normpath(cmdLine.target)
    Organize(cmdLine.sources, cmdLine.date)