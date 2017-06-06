'''various dates-related utils'''

import os
import datetime

import dateutil.parser
from dateutil.relativedelta import relativedelta

def months_delta(start, end):
    months = []
    start = date(start)
    end = date(end)
    
    delta = relativedelta(months=+1)
    d = start
    while d <= end:
        months.append(d)
        d += delta
    
    return len(months)

def month_year_iter( start_month, start_year, end_month, end_year ):
    start_month, start_year, end_month, end_year = int(start_month), int(start_year), int(end_month), int(end_year)
    ym_start= 12*start_year + start_month - 1
    ym_end= 12*end_year + end_month
    for ym in xrange( ym_start, ym_end ):
        y, m = divmod( ym, 12 )
        yield y, m+1
        
def date(d):
    if type(d) == datetime.date:
        return d
    try:
        return d.date()
    except:
        return dateutil.parser.parse(d).date()

def datify(candidate, year=datetime.date.today().year):
    d = None
    acceptedFormats = ('%m/%y',  '%m.%y', 
                       #and with yyyy
                       '%m/%Y', '%m.%Y')
    
    for frmt in acceptedFormats:
        try:
            d = datetime.datetime.strptime(candidate, frmt).date()
        except ValueError:
            pass
        
    if d:
        return d
    
    try:
        d = int(candidate)
        if d >= 1 and d<=12:
            return datetime.datetime.strptime('%d/%s' % (d, year), '%m/%Y').date()
    
    except:
        pass
        
TheDate = datetime.date.today()

def range(first, last):
    """an iterator on dates' range"""
    first, last = date(first), date(last)
    while first <= last:
        yield first
        first += datetime.timedelta(days=1)

def isweekend(d):
    return datetime.date.isoweekday(date(d)) in (6,7)

def dates(dl):
    '''return a list of dates, based on the dl:
    if two elements in dl - assume a range of dates excluding weekends,
    otherwise - assume a list of sporadic dates
    if no input: is a list that contains only TheDate
    '''
    if not dl:
        return [TheDate]

    if len(dl) != 2:
        return [date(d) for d in dl]
    return [ d for d in range(
        min(date(dl[0]), date(dl[1])), 
        max(date(dl[0]), date(dl[1]))
        ) if not isweekend(d) ]

def YYYY(d):
    d = date(d)
    return '%04d' % d.year

def MM(d):
    d = date(d)
    return '%02d' % d.month

def DD(d):
    d = date(d)
    return '%02d' % d.day

def YYYYMMDD(d):
    d = date(d)
    return '%04d%02d%02d' % (d.year, d.month, d.day)

if __name__ == '__main__':
    for m in month_year_iter(5, 2013, 3, 2014):
        print m
    print date('2009-11-09')
    print date(date('2009-11-09'))
