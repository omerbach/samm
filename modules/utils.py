# -*- coding: utf8 -*-  
import os
import sys
import mail
import datetime
import tempfile
from configuration import Config
import codecs
import time
import pprint
import json
import html2text
import time
from collections import defaultdict
from operator import itemgetter
from itertools import groupby
import sqlite3
import dates

dt_pattern = '%Y-%m-%d %H:%M:%S'
configFile = 'debt.ini'
cacheFile = 'config.cache'

DB_INFO = 'sam_excel_db.sqlite3'

TENANT_TYPE_OWNER = 1
TENANT_TYPE_RENTER = 2

def CreateTempFile(prefix="tmp", suffix=".html", dir='.'):   
    fd, filename = tempfile.mkstemp(prefix=prefix, suffix=suffix, dir=dir)
    #don't want to use the fd, close it. will use the filename to open the file
    os.close(fd)
    return filename

def CreateTempFolder(prefix="tmp", suffix="", dir='.'):   
    tmpFolder = CreateTempFile(prefix=prefix, suffix=suffix, dir=dir)
    os.remove(tmpFolder)
    return tmpFolder    

config = Config(configFile)

def SetCache(r):      
    with open(cacheFile, "w") as fp:
        pprint.pprint(r, stream=fp)
        

def GetFileSize(path):
    return os.stat(path).st_size

def GetCache():
    if not os.path.exists(cacheFile):
        r = {}
        SetCache(r)
        return r
    
    return eval(open(cacheFile).read())
        
#an os walk that can filter dir names
def MyWalk(top_dir, includes, ignores):
    for dirpath, dirnames, filenames in os.walk(top_dir):
        
        #if includes is empty, split by ',' will generate an array of one empty string
        def noIncludes():
            return len(includes)==1 and not len(includes[0])
        
        #if no includes defined, then treat the dir as included
        def inIncludes():
            return  noIncludes() or dn in includes
        
        def notInIgnores():
            return dn not in ignores
               
        dirnames[:] = [ 
            dn for dn in dirnames 
            if  notInIgnores() and inIncludes()]
        
        yield dirpath, dirnames, filenames

#if text is a list, dump line by line seperated by <p>,else dump as is
def Html(text, paragraphify=False):
    
    return """
    <html>
      <head>
        <meta charset="utf-8">
      </head>
      <body dir="rtl" style="font-size:20px;">                        
        <p>%s</p>                
        %s
        <a href="%s" target="_blank">
          <img src ="%s" id="logo" ALIGN=RIGHT  />
        </a>                    
      </body>
    <html>""" % (
                  datetime.date.today().strftime("%d/%m/%Y"),
                  ''.join('<p>%s</p>'% line for line in text) if paragraphify else ''.join(text), 
                  config.companyWebSite.decode('utf-8').encode(),
                  config.companyLogo.decode('utf-8').encode()                
              )

    
def SSE_MSG(message, label=None, msgType="info", direction="rtl", downloadFile=None, downloadFolder=None, progress=None):
    
    body = {'type': msgType,
            'direction': direction,
            'message': message,
            'label': label,            
            'downloadFile': downloadFile,
            'downloadFolder': downloadFolder,
            'progress' : progress
            }
    
    return  "retry: 0\ndata: %s\n\n" % json.dumps(body)

def SSE_MSG_DOWNLOAD(downloadFile, downloadFolder):    
    return  "retry: 0\nevent: download\ndata: %s\n\n" % json.dumps({'downloadFile': downloadFile, 'downloadFolder': downloadFolder})

def Monthify(month):
    try:
        month = int(month)
    except:
        return month.encode('utf-8')
    
    return {1: 'ינואר', 
            2: 'פברואר',
            3: 'מרץ',
            4: 'אפריל',
            5: 'מאי',
            6: 'יוני',
            7: 'יולי',
            8: 'אוגוסט',
            9: 'ספטמבר',
            10: 'אוקטובר',
            11: 'נובמבר',
            12: 'דצמבר'}[month]

def HtmlToTxt(content):
    return html2text.html2text(content).replace('&nbsp_place_holder;', ' ').strip()
    
def HebrewMonths(months):
    months = months.split(',')
    #no months
    if len(months) == 1 and months[0] == '':
        return ''
    
    if len(months) == 1 and '-' not in months[0]:        
        hebrewMonth = Monthify(months[0])
        return 'חודש %s' % hebrewMonth
        
    return 'חודשים : %s' % ','.join(str(m) for m in months)

def CustomerSignature():
    return '<a href="%s" target="_blank"><img id="mainLogo" src="%s" align="RIGHT"></a>' % (config.companyWebSite, config.companyLogo)

def CompanySignature():
    return '<img id="mainLogo" src="%s">' % config.companyPersonalSignature()


def Md(d):   
    
    #remove fishy characters for folders
    for forbidden in ["?", '"', "<", ">", "*", "|", "\n"]:
        d = d.replace(forbidden, '')    
            
    r = Normpath(os.path.join(d))
    if not os.path.exists(r):
        os.makedirs(r)
    
    return r
    
def Rm(fn):
    "remove a file, if exists"
    if fn and os.path.exists(fn):
        os.remove(fn)
        
def Normpath(path):
    "Return full-path, with fwd slashes"
    return os.path.abspath(path).replace('\\','/')

def TidyFileName(filename):
    
    for forbidden in ["/", "\\", "?", '"', ":", "<", ">", "*", "|", "\n"]:
        filename = filename.replace(forbidden, '')
    
    return filename

def UnStylify(html):
    styleStart = html.find('<style>')
    styleEnd = html.find('</style>')
    if styleStart > 0 and styleEnd > 0:
        end = len(html)
        newContent = html[:styleStart] + html[styleEnd + len('</style>'):]
        html = newContent
    
    return html
        
def UnCommafy(s):    
    try:
        return int(s.replace(',', ''))
    except:
        return 0

def Intify(s):
    try: 
        return int(s)                
    except ValueError:
        return 0
    
def RepresentsInt(s):
    try: 
        return int(s)                
    except ValueError:
        return 10000000
    
def Commafy(n):
    try:
        n = int(n)
    except:
        return n
    
    "Return a comma-fied string of a number"
    s = str(abs(int(n)))
    r = []
    for i, c in enumerate(reversed(s)):
        if i and (not (i % 3)):
            r.insert(0, ',')
        r.insert(0, c)
    if n < 0:
        r.insert(0, '-')
    if n % 1:
        r.extend(str(abs(n) - abs(int(n))).lstrip('0'))
    return ''.join(r)



class HistoryReporter():  
        
    def __init__(self, requestParameters, serverInClient):        
        self.ignores, self.includes = requestParameters.ignores, requestParameters.includes
        self.broken = False
        
        Md(config.historyDir)
        
        self.groups = defaultdict(  # Building
        lambda: defaultdict(  # date
         lambda: defaultdict(  # time
          lambda: defaultdict(  # executionType
           lambda: defaultdict(  # format
            lambda: defaultdict(  # appartment
            lambda: defaultdict(  # name
             lambda: defaultdict(  # alert
                lambda: defaultdict(  # alertDestination
                 str  # file
                 )))))))))
        
        self.requestParameters = requestParameters
        
    
    def getAllBuildings(self):        
        return os.listdir(config.historyDir)
        
    def build(self, helper=None, helperFields=None, historydata=None):
        
        if len(self.requestParameters.appertments)==1 and not len(self.requestParameters.appertments[0]):
            appartments = []
        else:
            appartments = self.requestParameters.appertments
            
        for building in os.listdir(config.historyDir):            
                        
            includeBuildings = not (len(self.includes) == 1 and self.includes[0] == '')
            
            if includeBuildings and building not in [TidyFileName(b) for b in self.includes]:
                continue
            
            if building in [TidyFileName(b) for b in self.ignores]:
                continue
            
            for alertFile in os.listdir(os.path.join(config.historyDir, building)):
                
                yield SSE_MSG(
                            message = Html(['מחלץ נתונים היסטוריים של בניין: %s, מקובץ : %s' % 
                                                  ('<b>%s</b>' % building.encode('utf-8'), 
                                                   '<b>%s</b>' % Normpath(os.path.join(config.historyDir, building, alertFile)).encode('utf-8')) ], True),
                            label = 'קולט נתונים...')
                
                building, curr_date, curr_time, executionType, customerTemplatesDir, appartment, name, alert, alertDestination =  os.path.splitext(alertFile)[0].split('^')
                curr_time = curr_time.replace('-', ':')         
                
                if alert in ['sms', 'mail', 'letter']:
                    toCheck = appartment.encode('utf-8') if isinstance(appartment, unicode) else appartment
                    if not len(appartments) or toCheck in appartments:
                        self.groups[building][curr_date][curr_time][executionType][customerTemplatesDir][appartment][name][alert][alertDestination] = os.path.join(config.historyDir, building, alertFile)
                            
    def prepareExecutiveReport(self, requestParameters):
        tuples = []            
            
        for building in sorted(self.groups):
            for d in sorted(self.groups[building], key=(lambda l: (dates.date(l) ) ), reverse=True):
                for t in sorted(self.groups[building][d], key=(lambda l: (time.strptime(l, '%H:%M') ) ), reverse=True):
                    for execType in sorted(self.groups[building][d][t]):
                        for formatTemplate in sorted(self.groups[building][d][t][execType]):
                            for appartment in sorted(self.groups[building][d][t][execType][formatTemplate], key=(lambda l: (RepresentsInt(l)) )):
                                for name in sorted(self.groups[building][d][t][execType][formatTemplate][appartment], key=(lambda l: (RepresentsInt(l)) )):
                                    for alert in sorted(self.groups[building][d][t][execType][formatTemplate][appartment][name]):
                                        for alertDestination in sorted(self.groups[building][d][t][execType][formatTemplate][appartment][name][alert]):
                                            alertFile = self.groups[building][d][t][execType][formatTemplate][appartment][name][alert][alertDestination]
                                                                                    
                                            tuples.append( ('%s---%s---%s---%s---%s---%s---%s' % (building, 
                                                             d, 
                                                             t, 
                                                             execType, 
                                                             formatTemplate, 
                                                             appartment,
                                                             name
                                                             ), alert, file(alertFile).read()) )
                    
            
        return Alerter.GetTemplateContent('web/templates/reports/history_report.html', 
        {            
            'title_file': tuples
        })
        
    
    
from alerters import Alerter


def GetLicenseExpiration(authFile = None):    
    seventies = int(time.mktime(time.strptime('1970-01-01 12:27:00', dt_pattern)))
    
    authFile = authFile if authFile else 'web/misc/pgp/auth.txt'
    if not os.path.exists(authFile):
        return seventies
    
    authTxt = file(authFile).read()
    start , end = '5sX2RBAiZT', 'Yl0n'
    
    startPos = authTxt.find(start)
    
    if startPos == -1:
        return seventies
    
    endPos = authTxt.find(end)
    
    if endPos == -1:
        return seventies
    
    try:
        return int(authTxt[startPos + len(start) : endPos])
    except:
        return seventies

def Authorize():
    expiry = GetLicenseExpiration()    
    return int(time.time()) < GetLicenseExpiration(), expiry

"""
returns a list of lists with consecutive elements. 
[1,2,3,4,5,20,6,7,8,9,10,11,12,16,21,22,87] - > [[1, 2, 3, 4, 5], [20], [6, 7, 8, 9, 10, 11, 12], [16], [21, 22], [87]]
"""
def Consecutivify(data):    
    result = []
    for k, g in groupby(enumerate(data), lambda (i,x):i-x):
        result.append(map(itemgetter(1), g))
    return result

""" 
returns a list of lists with consecutive dates. 
['1/13', '7/13', '2/13', '3/13', '4/14',  '12/13', '10/13', '11/13', '1/14', '2/14'] - > 
[ ['1/13', '2/13', '3/13', '4/13'], ['7/13'], ['10/13', '11/13', '12/13', '1/14', '2/14'] ]
"""
def MonthsConsecutivify(months): 
        
    def month_number(d):        
        m, y = d.month, d.year
        return int(y)*12 + int(m)
    
    return [[date.strftime('%m/%y') for _, date in run]
     for _, run in groupby(enumerate(sorted(months, key=month_number)),
                           key=lambda (i, date): (i - month_number(date)))]

def GroupRangeConsecutiveMonths(months):
    return ', '.join(['%s-%s' % (str(p[0]), str(p[-1])) if len(p) > 1 else str(p[0]) for p in 
            MonthsConsecutivify(months)])    
    

def GetSamProcess():
    rowId = 1
        
    try:
        with sqlite3.connect('setting.sqlite3') as db:
            c = db.cursor()
            c.execute("""SELECT theProcess FROM connections WHERE rowId=?""", (rowId, ))
            res = c.fetchone()
            if res:
                theProcess, = res
                return theProcess                
                
    #no such table
    except sqlite3.OperationalError:
        pass

def UpdateSamProcess(pid):
    try:
        with sqlite3.connect('setting.sqlite3') as db:
            db.execute("""CREATE TABLE IF NOT EXISTS connections (
            rowId INTEGER NOT NULL,
            theProcess INTEGER NOT NULL,            
            PRIMARY KEY (rowId)
        
        
            )""")
            
            rowId = 1
            db.execute('REPLACE INTO connections(rowId, theProcess) VALUES(?, ?)', [rowId, pid])
                
    except:
        pass
    
def GenerateDirCopy(template_path, template_name, copy_suffix):    
    #copied dir path
    copyid_base = Normpath(os.path.join(template_path, template_name + copy_suffix))    
    
    if not os.path.exists(copyid_base):
        return template_name + copy_suffix
            
    #find the next copied index
    else:        
        match = '%s%s(' % (template_name, copy_suffix)
        max_copied_index = 0
                
        current_dirs = [x[0] for x in os.walk(u'templates')]        
        for d in current_dirs:  
                        
            dir_name = os.path.basename(d)
            
            start = dir_name.find(match)
            if dir_name.startswith(match):                
                copy_number = int(dir_name[len(match):-1])
                max_copied_index = max([max_copied_index, copy_number])
                
        return '%s%d)' % (match, max_copied_index + 1)
    
def FindFirstNonUsedDate(date_dict, start_date):
    while 1:
        if not date_dict.get(start_date, None):
            break
        else:
            start_date += datetime.timedelta(days=1)
    
    return start_date

#4 -> '101' -> (1,3)
def DecimalBreakDown(num):      
    num = int(num)    
    enms  = reversed(list(str(bin(num))[2:]))
    indexes = [i+1 for i, x in enumerate(enms) if int(x)]
    return indexes