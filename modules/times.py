import datetime

import dateutil.parser

import config

def delta(t1, t2):
    "fills the irritatingly missing datetime.time - datetime.time"
    assert type(t1) == datetime.time, type(t1)
    assert type(t2) == datetime.time, type(t2)
    return datetime.datetime.combine(config.DATE, t1) - datetime.datetime.combine(config.DATE, t2)

def add(t, d):
    "fills the irritatingly missing datetime.time + datetime.timedelta"
    assert type(t) == datetime.time
    assert type(d) == datetime.timedelta
    return (datetime.datetime.combine(config.DATE, t) + d).time()

def parse_time(t):
    return dateutil.parser.parse(t).time()
        
        
def minutes(first, last, jump=1, back=False):
    'yield hh:mm:ss strings of all minutes between start and end (exclusive)'
    first, last = dateutil.parser.parse(first), dateutil.parser.parse(last)
    first = first.replace(microsecond=0)
    
    if back:
        while first < last:            
            yield ':'.join(str(last).split()[1].split(':')[0:3])
            last += datetime.timedelta(minutes=-jump)
    
    else :
        while first < last:            
            yield ':'.join(str(first).split()[1].split(':')[0:3])
            first += datetime.timedelta(minutes=jump)
            
def seconds(first, last, back=False):
    'yield hh:mm:ss strings of all seconds between start and end (exclusive)'
    first, last = dateutil.parser.parse(first), dateutil.parser.parse(last)
    first = first.replace(microsecond=0)
    
    if back:
        while first < last:            
            yield ':'.join(str(last).split()[1].split(':')[0:3])
            last += datetime.timedelta(seconds=-1)
    
    else :
        while first < last:            
            yield ':'.join(str(first).split()[1].split(':')[0:3])
            first += datetime.timedelta(seconds=1)
        
        
def nminutes(first, last):
    'returns the number of minutes between start and end '    
    hours, seconds = divmod(delta(last , first).total_seconds(), 3600)
    minutes, _ = divmod(seconds, 60)
    
    return int(hours) * 60 + int(minutes)

def nmilliseconds(first, last):
    'returns the number of minutes between start and end '    
    #Only days, seconds and microseconds are stored internally in delta object
    return nmilliseconds_from_delta(last -first)

def nmicroseconds(first, last):
    'returns the number of minutes between start and end '    
    #Only days, seconds and microseconds are stored internally in delta object
    return nmicroseconds_from_delta(last -first)

def nmilliseconds_from_delta(delta):
    'returns the number of milliseconds from a delta object '
    #Only days, seconds and microseconds are stored internally in delta object
    return ((delta.days * 24 * 60 * 60 + delta.seconds) * 1000 + delta.microseconds / 1000)

def nmicroseconds_from_delta(delta):    
    'returns the number of microseconds from a delta object '
    #Only days, seconds and microseconds are stored internally in delta object
    return ((delta.days * 24 * 60 * 60 + delta.seconds) * 1000000 + delta.microseconds )

#returns a datetime object representation of the fix time format (as in SendingTime - tag 52 : '20120202-07:10:37.081' )
def tidyFixTimeStamp(ts):
    return datetime.datetime.strptime(ts, "%Y%m%d-%H:%M:%S.%f")

#returns a datetime object representation of the toot time format (as in trader log : '07:10:37.034')
def tidyTootTimeStamp(ts,date=datetime.date.today()):
    return datetime.datetime.strptime(str(date) + ' ' + ts, "%Y-%m-%d %H:%M:%S.%f")

def hhmmss(s):
    "return an int hhmmss of a time-of-day string"
    if s[1] == ':':  # for formats such as 8:06:17 (SAS dumps, for example)
        s = '0' + s
    s = "".join(d for d in s if d.isdigit())[:6]
    if len(s) < 6:
        s += '0' * (6 - len(s))
    r = int(s)
    assert 0 <= r < 240000, s
    return r




def hhmmssrrrr(s):
    "return an int hhmmssrrrr of a time-of-day string"
    s = "".join(d for d in s if d.isdigit())[:10]
    r = int(s)
    if 0 <= r <= 2400:
        return r * 1000000
    if 10000 <= r <= 235959:
        return r * 10000
    if 74000000 <= r <= 173000000:
        return r * 10
    if 740000000 <= r <= 1730000000:
        return r
    assert False, s



def nseconds(hhmmss):
    hh, mm, ss = hhmmss // 10000, (hhmmss // 100) % 100, hhmmss % 100
    return (hh * 60 + mm) * 60 + ss

def time_from_nseconds(s):
    hh = s // 3600
    mm = (s - hh * 3600) // 60
    ss = s - hh * 3600 - mm * 60
    return datetime.time(hour=hh, minute=mm, second=ss)



def time_from_hhmm(hhmm):
    "convert an int of the form hhmm to a datetime.time object"
    if hhmm is None:
        return None
    hh, mm = hhmm // 100, hhmm % 100
    return datetime.time(hour=hh, minute=mm)

def time_from_hhmmss(hhmmss):
    "convert an int of the form hhmmss to a datetime.time object"
    if hhmmss is None:
        return None
    hh, mm, ss = hhmmss // 10000, (hhmmss // 100) % 100, hhmmss % 100
    return datetime.time(hour=hh, minute=mm, second=ss)


def time_from_hhmmssmmm(hhmmssmmm):
    "convert an int of the form hhmmssmmm to a datetime.time object"
    if hhmmssmmm is None:
        return None
    hh, mm, ss, mmm = hhmmssmmm // 10000000, (hhmmssmmm // 100000) % 100, (hhmmssmmm // 1000) % 100, hhmmssmmm % 1000
    return datetime.time(hour=hh, minute=mm, second=ss, microsecond=mmm*1000)

def time_from_hhmmssrrrr(hhmmssrrrr):
    "convert an int of the form hhmmssrrrr to a datetime.time object"
    if hhmmssrrrr is None:
        return None
    hh, mm, ss, rrrr = hhmmssrrrr // 100000000, (hhmmssrrrr // 1000000) % 100, (hhmmssrrrr // 10000) % 100, hhmmssrrrr % 10000
    return datetime.time(hour=hh, minute=mm, second=ss, microsecond=rrrr*100)

def time_from_int(n):
    if 0 <= n <= 2400:
        return time_from_hhmm(n)
    if 10000 <= n <= 235959:
        return time_from_hhmmss(n)
    if 74000000 <= n <= 173000000:
        return time_from_hhmmssmmm(n)
    if 740000000 <= n <= 1730000000:
        return time_from_hhmmssrrrr(n)

def time_from_qpc(qpc):
    if qpc <= 0:
        return datetime.time(0, 0, 0)

    microseconds = (1000000 * (qpc - config.QPC0) + config.QPF / 2) / config.QPF
    assert 0 <= microseconds < 1000000 * 24 * 3600
    seconds = microseconds // 1000000
    minutes = seconds // 60
    hours = minutes // 60
    return datetime.time(hour=hours, minute=minutes % 60, second=seconds % 60, microsecond=microseconds % 1000000)


def time_to_hhmmssrrrr(t):
    "convert a datetime.time object to an int"
    return ((t.hour * 100 + t.minute) * 100 + t.second) * 10000 + t.microsecond // 100


def datetime_from_hhmmssrrrr(hhmmssrrrr):
    return datetime.datetime.combine(config.DATE, time_from_hhmmssrrrr(hhmmssrrrr))

def HH(t):    
    return '%02d' % t.hour

def MM(t):    
    return '%02d' % t.minute

