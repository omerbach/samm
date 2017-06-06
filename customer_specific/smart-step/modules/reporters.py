# -*- coding: utf8 -*-  

#--------------------------------SMART STEP REPORTES------------------------------------------------
import os
import fnmatch
import collections
import datetime
import time
import json
import shutil
import decimal
import copy
from collections import defaultdict

import dates
import xlrd
import requests
import bottle

from alerters import Alerter
import utils
import sms
import mail            


#9: white, 64: None, 65: None, 81: None, 32767: None
COLORS_NON_DEBT = [9, 64, 65, 81, 32767]
COLOR_DEBT = 13
COLOR_STANDING_ORDER = 46

COLOR_PROBLEMATIC_1 = 31
COLOR_PROBLEMATIC_2 = 50
COLOR_PROBLEMATIC_3 = 40
COLOR_PROBLEMATIC_6 = 29

COLOR_LEGAL_WARNING = 10
COLOR_VAAD = 51

PROBLEMATIC_COLORS = [ 
                      COLOR_PROBLEMATIC_2,
                      COLOR_PROBLEMATIC_3,
                      COLOR_PROBLEMATIC_6]

def MonthsToMonthYearFormat(months, year):
            
    formattedMonths = []                
    for i in months: 
        i = str(i)
        if i.find('-') >= 0:
            startRange, endRange = i.split('-')
            
            startDate = dates.datify(i.split('-')[0], year)
            endDate = dates.datify(i.split('-')[1], year)
            #monthYearStart = startRange.split('/')
            #monthYearEnd = endRange.split('/')
            
            #if len(monthYearStart) > 1:
                #startMonth, startYear = monthYearStart
            #else:
                #startMonth, startYear = startRange, year
                
            #if len(monthYearEnd) > 1:
                #endMonth, endYear = monthYearEnd
            #else:
                #endMonth, endYear = endRange, year
            if startDate and endDate:
                for y,m in dates.month_year_iter(startDate.month, startDate.year, endDate.month, endDate.year):
                #for m in range(int(startRange.strip()), int(endRange.strip()) + 1):
                    formattedMonths.append('%s/%s' % (m,y))
        else:     
            d = dates.datify(i, year)
            if d:
            #my = i.split('/')
            #if len(my) > 1:
                #m, y = my
            #else:
                #m, y = i, year
                
                formattedMonths.append(d)
    
    return formattedMonths

def TidyField(field):
    
    if isinstance(field, unicode):
        return field.encode('utf-8')
    if isinstance(field, float):
        return str(int(field))
    return str(field)

def ExtractValue(cell):
    #XL_CELL_TEXT	1	a Unicode string
    val = cell.value.strip() if cell.ctype == 1 else cell.value    
    return val

def ExtractBackground(cell, sheet):
    try:
        xf = sheet.workSheet.book.xf_list[cell.xf_index]
        bgx = xf.background.pattern_colour_index    
    except AttributeError:
        return -1
    
    return bgx
    
class ReportersBase(object):    
    
    def __init__(self, requestParameters, serverInClient, excelPrefix):
        self.excelPrefix = excelPrefix
        self.ignores, self.includes = requestParameters.ignores, requestParameters.includes
        self.groups = collections.defaultdict(# sheet key 
                                    lambda: collections.defaultdict(  # record key
                                        list # list of records (renter + owner)
                                        ))
        self.excelPathOf = {}        
        
        self.excelRoot = utils.config.rootBuildingsDir        
        self.requestParameters = requestParameters
        
        self.serverInClient = serverInClient
        self.broken = False
        
    def getAllBuildings(self):
        buildings = []
        
        for dirpath, dirnames, filenames in os.walk(utils.config.rootBuildingsDir):            
            head, tail = os.path.split(dirpath)           
            
            #can not retreive background color of cells at xlsx files cause xlrd doesn't support that (only for xls)            
            for filename in fnmatch.filter(filenames, '*%s*.xls' % self.excelPrefix ):                    
                excel = os.path.join(dirpath, filename)
                
                excelFile = self.ExcelFile(excel, self.requestParameters)
                
                #no interesting sheet found in the file, continue to next file
                if not excelFile.sheet:                        
                    continue
                
                excelFile.sheet.parseBuildingMetaData()
                
                #when parsing failed we do not know which building this excel represents,                    
                if not excelFile.sheet.buildingDescription:                          
                    continue
              
                buildings.append(excelFile.sheet.buildingDescription)
                            
        return buildings
    

class ExcelSheetBase(object):
    def __init__(self, excel, workSheet, startRow = 2):
        self.excel = excel
        self.startRow = startRow
        self.workSheet = workSheet
        
        
        self.header = [self.workSheet.cell_value(1, col).strip() if self.workSheet.cell_type(1, col) == 1 
                                else self.workSheet.cell_value(1, col) for col in range(self.workSheet.ncols)]
        self.records = []
      
    def validateHeader(self, mandatoryHeaderFields):        
        #note on mandatory and missing fields : could be integers
        missing = self.getMissingHeaders(mandatoryHeaderFields)
        if len(missing):
            if len(missing) == len(mandatoryHeaderFields):
                return bottle.template('web/templates/errors/error_missing_all_headers', 
                                   date = datetime.date.today().strftime("%d/%m/%Y"),
                                   file_name = self.excel,
                                   header = ','.join(self.tidyField(h) for h in self.header),
                                   mandatory_fields = ', '.join(str(mandat) if type(mandat) == int else mandat for mandat in mandatoryHeaderFields),
                                   company_name = utils.config.companyName,
                                   sheet = self.workSheet.name,
                                   missing_fields = ', '.join(str(miss) if type(miss) == int else miss for miss in missing),
                                   company_web_site = utils.config.companyWebSite,
                                   company_logo = utils.config.companyLogo)
            else:
                return bottle.template('web/templates/errors/error_missing_header', 
                                   date = datetime.date.today().strftime("%d/%m/%Y"),
                                   file_name = self.excel,
                                   header = ','.join(self.tidyField(h) for h in self.header),
                                   mandatory_fields = ', '.join(str(mandat) if type(mandat) == int else mandat for mandat in mandatoryHeaderFields),
                                   company_name = utils.config.companyName,
                                   sheet = self.workSheet.name,
                                   missing_fields = ', '.join(str(miss) if type(miss) == int else miss for miss in missing),
                                   company_web_site = utils.config.companyWebSite,
                                   company_logo = utils.config.companyLogo)
            
    
    def parseGeneralData(self):
        try:
            #general stuff at BB1 which is cell (0, 53) -> discovered by xlrd.cellname(0, 53)
            self.generalData = self.workSheet.cell(0, 53).value         
        except:
            self.generalData = ""
        
    def parseBuildingMetaData(self):
        self.description, self.buildingDescription = None, None        
        
        try:            
            self.A1value = self.workSheet.cell(0,1).value
            desc_general_building = self.A1value.strip().split(':')
            self.description, self.buildingDescription = desc_general_building[0].strip().replace(',', ''), desc_general_building[1].strip().replace(',', '')            
            
        except (IndexError, ValueError, AttributeError):
            pass
            
        
    def getMissingHeaders(self, expectedHeader):        
        return [h for h in expectedHeader if h not in self.header]
    
    def tidyField(self, field):                
        if isinstance(field, unicode):
            return field.encode('utf-8')
        if isinstance(field, float):
            return str(int(field))
        return str(field)

    def fetchRecords(self):
            for row in range(self.startRow, self.workSheet.nrows):                
                
                cells = [self.workSheet.cell(row, col)                           
                          for col in range(self.workSheet.ncols)]                
                                
                yield dict(zip( (self.tidyField(h) for h in self.header), 
                                cells ) )

class DebtsPercentageReporter(ReportersBase):  
        
    def __init__(self, requestParameters, serverInClient):
        super(DebtsPercentageReporter, self).__init__(requestParameters, serverInClient, utils.config.excelPaymentFilePrefix)
        
    def build(self, helper=None, helperFields=None, historydata=None):        
        includes, ignores = self.includes, self.ignores
        
        for dirpath, dirnames, filenames in os.walk(utils.config.rootBuildingsDir):            
            head, tail = os.path.split(dirpath)
           
            def showError():
                return utils.SSE_MSG(
                            message = errMessage,
                            label = 'בעיה בסריקת הקובץ :%s ' % 
                            excelFile.excel.encode('utf-8') + 
                            ('   <button class="ignore" type="button" id="%s">התעלם מבניין זה</button> ' % building.encode('utf-8')) if building else '',
                            progress = 0,
                            msgType = 'error'
                        )
            
            def handleError():
                if self.serverInClient:
                    os.startfile(excelFile.excel)
                else:
                    utils.Md('errors')                                        
                    shutil.copy2(excelFile.excel, 'errors')
    
            #if includes is empty, split by ',' will generate an array of one empty string
            def noIncludes():
                return len(includes)==1 and not len(includes[0])
            
            #if no includes defined, then treat the dir as included
            def inIncludes():
                return  noIncludes() or building in includes
            
            def notInIgnores():
                return building not in ignores                       
                                    
            #can not retreive background color of cells at xlsx files cause xlrd doesn't support that (only for xls)            
            for filename in fnmatch.filter(filenames, '*%s*.xls' % self.excelPrefix ):                    
                excel = os.path.join(dirpath, filename)
                
                excelFile = self.ExcelFile(excel, self.requestParameters)
                
                if self.broken:
                    break
                
                #no interesting sheet found in the file, continue to next file
                if not excelFile.sheet:
                    continue                                                    
                
                building = None    
                excelFile.sheet.parseBuildingMetaData()                                
                
                #when parsing failed we do not know which building this excel represents,
                #when there is no includes we'll show this error
                if not excelFile.sheet.buildingDescription :
                    if noIncludes():
                        
                        errMessage =  bottle.template('web/templates/errors/error_building_format', 
                               date = datetime.date.today().strftime("%d/%m/%Y"),
                               file_name = excelFile.sheet.excel,
                               company_name = utils.config.companyName,
                               sheet = excelFile.sheet.workSheet.name,
                               A1_value = getattr(excelFile.sheet, 'A1value', ""),
                               company_web_site = utils.config.companyWebSite,
                               company_logo = utils.config.companyLogo)
                        yield showError()
                        yield handleError()                                                                
                        self.broken = True
                        break
                    else:
                        continue
                    
                #got here, we know which building this file represents                
                building = excelFile.sheet.buildingDescription                    
                
                if notInIgnores() and inIncludes():                                               
                    
                    yield utils.SSE_MSG(
                        message = utils.Html(['בונה נתוני גבייה של בניין: %s, מקובץ : %s' % 
                                              ('<b>%s</b>' % building.encode('utf-8'), 
                                               '<b>%s</b>' % utils.Normpath(excelFile.excel).encode('utf-8')) ], True),
                        label = 'קולט נתונים...')
                    
                    errMessage = excelFile.sheet.validateHeader(excelFile.sheet.MandatoryFields)
                
                    if errMessage:
                        yield showError()
                        yield handleError()                                                                
                        self.broken = True
                        break

                    expectedPaid, totalDebt = 0, 0                                                
                    for record in excelFile.sheet.fetchRecords():
            
                        if self.broken:
                            break
                                    
                        rec = self.ExcelFile.ExcelSheet.ExcelRecord(record, excelFile.sheet)
                        
                        if rec.skip:
                            continue
                                            
                        if rec.eof:
                            break
                                                                                                                
                        if self.broken:
                            break
                                                                                                                                         
                                                        
                        rec.source = utils.Normpath(excel).replace('/', '*')
                        rec.building = building
                        rec.year = self.requestParameters.year
                        
                        rec.monthsInDebt = rec.debtMonths(None if excelFile.requestParameters.noMonths else MonthsToMonthYearFormat(excelFile.requestParameters.reportingMonths, rec.year), 
                                                          excelFile.requestParameters.reportOnlyIfAllInARow)
                        
                        rec.months = '?' if rec.uncalculated else \
                        ','.join(['%s-%s' % (str(p[0]), str(p[-1])) if len(p) > 1 else str(p[0]) for p in 
                                               utils.MonthsConsecutivify(rec.monthsInDebt) ])                                                                                                    
                                                                                                   
                        if not rec.uncalculated:
                            expectedPaid += len([k for k in rec.__dict__  if dates.datify(k)]) * rec.payment
                            totalDebt += rec.debt
                    
                    actualPaid = expectedPaid - totalDebt
                    percentage = '%.2f' % (float(actualPaid) / float(expectedPaid) * 100) if expectedPaid else 0
                    self.groups[building] = (percentage, 
                                            utils.Normpath(excel).replace('/', '*'),
                                            self.requestParameters.year,
                                            'עד - %s' % datetime.date.today().strftime("%m/%Y"),
                                            utils.Commafy(actualPaid),
                                            utils.Commafy(expectedPaid)                                                
                                            )
                            
                        
    def prepareExecutiveReport(self, requestParameters):                
        
        return Alerter.coverage(self.groups, requestParameters)
        
    
    class ExcelFile(object):      
        
        def __init__(self, excel, requestParameters):
            self.excel = excel
            self.requestParameters = requestParameters
            self.workbook = xlrd.open_workbook(excel, formatting_info=True)
            sh = self._getSheet(requestParameters.year)
            #sometimes there is no sheet and this is fine (for example, user selected a year which not in the excel file)
            self.sheet = self.ExcelSheet(excel, sh) if sh else None
        
        def _getSheet(self, requestedYear):
            worksheet = None
            #find specific sheet
            worksheets = self.workbook.sheet_names()                                                
            
            for worksheet_name in worksheets:
                if str(requestedYear) in worksheet_name and worksheet_name.startswith(utils.config.excelPaymentSheetPrefix):
                    return self.workbook.sheet_by_name(worksheet_name)
           
                        
        class ExcelSheet(ExcelSheetBase):
            MandatoryFields = [u"דירה", 
                               u"תשלום חודשי",
                               u"חוב נצבר",
                               u'טלפון בעלים', 
                               u'מייל בעלים', 
                               u'טלפון דיירים', 
                               u'מייל דיירים', 
                               u'שם בעלים', 
                               u'שם דיירים']
            
            def __init__(self, excel, workSheet):
                super(DebtsPercentageReporter.ExcelFile.ExcelSheet, self).__init__(excel, workSheet)
                        
            class ExcelRecord(object):
                def __init__(self, record, sheet):
                    self.sheet = sheet
                    self.uncalculated = False
                    
                    for k, cell in record.items():                        
                        setattr(self, k, cell)                                            
                
                    #diiferent states per row which translated into a row highlight in the css
                    self.fishy = False
                    self.problematic = False
                    self.multiple_partial = False
                    self.vaad = False
                    self.legal = False
                    
                @property
                def debt(self):                    
                    return '?' if self.uncalculated else sum(d for d in self.monthsInDebt.values())
                
                @property
                def previosDebtValue(self):
                    cell = getattr(self, 'חוב נצבר', None)
                    if not cell:
                        return 0
                    
                    previousDebt = TidyField(ExtractValue(cell))                   
                    
                    if len(previousDebt):
                        try:
                            return int(previousDebt.strip())
                        except:
                            return 0
                        
                    return 0
                    
                @property
                def previousDebt(self):
                    if self.uncalculated:
                        return '?'
                    
                    previousDebtBackGround = ExtractBackground(getattr(self, 'חוב נצבר'), self.sheet)                    
                    
                    #if color is a debt color, return its value
                    if previousDebtBackGround == COLOR_DEBT:
                        return self.previosDebtValue if self.previosDebtValue > 0 else 0
                    
                    #color is not a debt color, no matter what is written it is not a debt
                    else:
                        return 0
                
                @property
                def skip(self):                    
                    return self.appartment == '*'
                    
                @property
                def eof(self):                    
                    return self.appartment == ''
                
                @property
                def appartment(self):
                    cell = getattr(self, 'דירה')
                    app = TidyField(ExtractValue(cell))
                                                            
                    try:                       
                        return int(app)
                    except ValueError:
                        return app
                                
                
                @property
                def payment(self):
                    cell = getattr(self, 'תשלום חודשי')
                    payment = TidyField(ExtractValue(cell))
                                        
                    try:
                        return int(payment)
                    except ValueError:                
                        return payment
        
                #this is the most problematic method
                def debtMonths(self, reportingMonths, reportOnlyIfAllInARow):
                   
                    debts = {}
                    multiple_partial = False
                    fishy = False
                    monthlyDebtOf = {}
                    
                    #months can be partial (when company takes ownership of the building in the middle of the year for example)                    
                    allMonths = sorted([k for k in self.__dict__ if dates.datify(k, self.year)], key= (lambda dateColumn: dates.datify(dateColumn)))
                    
                    if not reportingMonths:                       
                        reportingMonths = [dates.datify(m) for m in allMonths if dates.datify(m) <= datetime.date.today() ]
                        
                    previousDebtBackGround = ExtractBackground(getattr(self, 'חוב נצבר'), self.sheet)
                    
                    previousDebtValue = self.previosDebtValue
                    
                    #if at least one cell has a problematic color set, than mark the whole row as problematic
                    problematic = any(self.getCellBackGround(str(month)) in PROBLEMATIC_COLORS for month in allMonths) or \
                        previousDebtBackGround in PROBLEMATIC_COLORS
                    
                    #if at least one cell has a vaad color set, than mark the whole row as special problematic
                    problematic2 = any(self.getCellBackGround(str(month)) == COLOR_PROBLEMATIC_1 for month in allMonths) or \
                        previousDebtBackGround == COLOR_PROBLEMATIC_1
                    
                    #if at least one cell has a vaad color set, than mark the whole row as vaad
                    vaad = any(self.getCellBackGround(str(month)) == COLOR_VAAD for month in allMonths) or \
                        previousDebtBackGround == COLOR_VAAD
                    
                    #if at least one cell has a vaad color set, than mark the whole row as vaad
                    legal = any(self.getCellBackGround(str(month)) == COLOR_LEGAL_WARNING for month in allMonths) or \
                        previousDebtBackGround == COLOR_LEGAL_WARNING
                                        
                    #a cell which has an amount at least as the fix payment and still marked as debt where 
                    #the previous debt cell is marked as not in debt, then this is fishy
                    fishy = any(self.getCellBackGround(str(month)) == COLOR_DEBT and 
                                utils.Intify(self.monthlyPayment(month)) >= self.payment and 
                                previousDebtBackGround in COLORS_NON_DEBT
                                for month in allMonths)
                                        
                        
                    #calculate how much was paid during the year, treat COLOR_STANDING_ORDER cells as fully paid
                    totalPaid = sum(max( utils.Intify(self.monthlyPayment(month)), 
                                         self.payment if self.getCellBackGround(str(month)) == COLOR_STANDING_ORDER else 0 )
                                    for month in allMonths)
                    
                    #deduct past debt if this was paid during the year
                    totalPaid = totalPaid - (previousDebtValue if previousDebtBackGround != COLOR_DEBT else 0)
                    
                    #calculate expected payments for the year
                    expectedPayments = len(allMonths)*self.payment                                                            
                        
                    partialPayment = totalPaid % self.payment if self.payment else 0
                    
                    if self.payment:
                        if totalPaid / self.payment >= len(allMonths):
                            partialPayment = 0
                    
                    partialPaymentsCounter = 0
                                        
                    for month in allMonths:
                        formattedMonth = dates.datify(month)
                        
                        if self.getCellBackGround(str(month)) == COLOR_DEBT:
                            #partial if has a √ sign or a number
                            if self.monthlyPayment(month) == '√':
                                monthlyDebtOf[formattedMonth] = self.payment - partialPayment
                                partialPaymentsCounter += 1
                                
                            elif utils.Intify(self.monthlyPayment(month)):
                                if utils.Intify(self.monthlyPayment(month)) < self.payment:
                                    monthlyDebtOf[formattedMonth] = self.payment - partialPayment
                                    partialPaymentsCounter += 1
                                else:
                                    monthlyDebtOf[formattedMonth] = self.payment
                                
                            else:
                                monthlyDebtOf[formattedMonth] = self.payment
                                
                        #color standing order are fully paid, therefore are not debts
                        elif self.getCellBackGround(str(month)) != COLOR_STANDING_ORDER:
                            #this indicates the month was paid for
                            if self.monthlyPayment(month) == '√':
                                continue
                            #this indicates that the cell is not empty or has a number in it --> therefore this month was paid for
                            if utils.Intify(self.monthlyPayment(month)):
                                continue
                            
                            #empty cell or has a text in it therefore a debt
                            monthlyDebtOf[formattedMonth] = self.payment                                                            
                        
                    totalDebts = sum(monthlyDebtOf.values())	                    
                      
                    #can not relate partial debt to a specific month where previous debt was covered during the year
                    #dono how to deal with multiple partials debts
                    if (partialPayment and previousDebtValue and previousDebtBackGround != COLOR_DEBT) or partialPaymentsCounter > 1:
                        multiple_partial = True
                    
                    
                    if expectedPayments != totalDebts + totalPaid:
                        if totalDebts == 0:
                            if totalDebts + totalPaid < expectedPayments:
                                fishy = True
                                
                        else:
                            if expectedPayments > totalDebts + totalPaid:
                                multiple_partial = True
                                                                    
                    if legal:
                        self.legal = True
                        self.uncalculated = True
                        
                    elif problematic:
                        self.problematic = True 
                        self.uncalculated = True 
                        
                    elif problematic2:
                        self.problematic2 = True 
                        self.uncalculated = True
                        
                    elif fishy:
                        self.fishy = True
                        self.uncalculated = True
                        
                    elif multiple_partial:
                        self.multiple_partial = True
                        self.uncalculated = True                                                
                    elif vaad:
                        self.vaad = True
                        self.uncalculated = True
                   
                    debts = {month:debt for month, debt in monthlyDebtOf.items() 
                             if month in reportingMonths }
                    
                    #for month, debt in monthlyDebtOf.items():
                        #if reportingMonths:
                    
                    #if self.uncalculated:
                        #debts =  {'?': '?'}                        
                        
                    if reportOnlyIfAllInARow:
                        return debts if all(m in debts.keys() for m in reportingMonths) else {}                    
                    
                    return debts
                
                         
                def getCellBackGround(self, key):
                    cell = getattr(self, key)
                    return ExtractBackground(cell, self.sheet)
                
                
                def monthlyPayment(self, month):
                    cell = getattr(self, str(month))
                    return TidyField(ExtractValue(cell))                    


class OngoingDebtsReporter(ReportersBase):  
        
    def __init__(self, requestParameters, serverInClient):
        super(OngoingDebtsReporter, self).__init__(requestParameters, serverInClient, utils.config.excelPaymentFilePrefix)
        
    def build(self, helper=None, helperFields=None, historydata=None):
    
        includes, ignores = self.includes, self.ignores
        
        for dirpath, dirnames, filenames in os.walk(utils.config.rootBuildingsDir):            
            head, tail = os.path.split(dirpath)
           
            def showError():
                return utils.SSE_MSG(
                            message = errMessage,
                            label = 'בעיה בסריקת הקובץ :%s ' % 
                            excelFile.excel.encode('utf-8') + 
                            ('   <button class="ignore" type="button" id="%s">התעלם מבניין זה</button> ' % building.encode('utf-8')) if building else '',
                            progress = 0,
                            msgType = 'error'
                        )
            
            def handleError():
                if self.serverInClient:
                    os.startfile(excelFile.excel)
                else:
                    utils.Md('errors')                                        
                    shutil.copy2(excelFile.excel, 'errors')
    
            #if includes is empty, split by ',' will generate an array of one empty string
            def noIncludes():
                return len(includes)==1 and not len(includes[0])
            
            #if no includes defined, then treat the dir as included
            def inIncludes():
                return  noIncludes() or building in includes
            
            def notInIgnores():
                return building not in ignores                       
                                    
            #can not retreive background color of cells at xlsx files cause xlrd doesn't support that (only for xls)            
            for filename in fnmatch.filter(filenames, '*%s*.xls' % self.excelPrefix ):                    
                excel = os.path.join(dirpath, filename)
                
                excelFile = self.ExcelFile(excel, self.requestParameters)
                
                if self.broken:
                    break
                
                #no interesting sheet found in the file, continue to next file
                if not excelFile.sheet:
                    continue                                                    
                
                building = None    
                excelFile.sheet.parseBuildingMetaData()
                excelFile.sheet.parseGeneralData()
                
                #when parsing failed we do not know which building this excel represents,
                #when there is no includes we'll show this error
                if not excelFile.sheet.buildingDescription :
                    if noIncludes():
                        
                        errMessage =  bottle.template('web/templates/errors/error_building_format', 
                               date = datetime.date.today().strftime("%d/%m/%Y"),
                               file_name = excelFile.sheet.excel,
                               company_name = utils.config.companyName,
                               sheet = excelFile.sheet.workSheet.name,
                               A1_value = getattr(excelFile.sheet, 'A1value', ""),
                               company_web_site = utils.config.companyWebSite,
                               company_logo = utils.config.companyLogo)
                        yield showError()
                        yield handleError()                                                                
                        self.broken = True
                        break
                    else:
                        continue
                    
                #got here, we know which building this file represents                
                building = excelFile.sheet.buildingDescription
                general = excelFile.sheet.generalData
                
                if notInIgnores() and inIncludes():                                               
                    
                    yield utils.SSE_MSG(
                        message = utils.Html(['בונה נתוני גבייה של בניין: %s, מקובץ : %s' % 
                                              ('<b>%s</b>' % building.encode('utf-8'), 
                                               '<b>%s</b>' % utils.Normpath(excelFile.excel).encode('utf-8')) ], True),
                        label = 'קולט נתונים...')
                    
                    errMessage = excelFile.sheet.validateHeader(excelFile.sheet.MandatoryFields)
                
                    if errMessage:
                        yield showError()
                        yield handleError()                                                                
                        self.broken = True
                        break
                    
                    
                    tenantsHistory = defaultdict(# (appartment, name)
                                lambda: defaultdict(  # (date, time, formatTemplate)
                                    list # (alert, alertFile)
                                    ))
                                        
                    buildingHistory = utils.TidyFileName(building)
                    execType = Alerter.getExecutionDesc(self.requestParameters.mode)                        
                    #organize history per this building, per this executionMode                        
                    for d in sorted(historydata[buildingHistory]):
                        for t in historydata[buildingHistory][d]:
                            for formatTemplate in historydata[buildingHistory][d][t][execType]:
                                for appartment in historydata[buildingHistory][d][t][execType][formatTemplate]:
                                    for name in historydata[buildingHistory][d][t][execType][formatTemplate][appartment]:
                                        for alert in historydata[buildingHistory][d][t][execType][formatTemplate][appartment][name]:
                                            for alertDestination in historydata[buildingHistory][d][t][execType][formatTemplate][appartment][name][alert]:
                                                alertFile = historydata[buildingHistory][d][t][execType][formatTemplate][appartment][name][alert][alertDestination]
                                                tenantsHistory[(TidyField(appartment), TidyField(name))][(d, t, formatTemplate)].append((alert, alertFile))
                                                    
                    for i,record in enumerate(excelFile.sheet.fetchRecords()):
            
                        if self.broken:
                            break
                                    
                        rec = self.ExcelFile.ExcelSheet.ExcelRecord(record, excelFile.sheet)
                                                
                        if rec.skip:
                            continue
                                            
                        if rec.eof:
                            break
                                                                                                                
                        if self.broken:
                            break
                                                                                                                                         
                                                        
                        rec.source = utils.Normpath(excel).replace('/', '*')
                        rec.building = building
                        rec.general = general
                        rec.year = self.requestParameters.year                                               
                            
                        rec.monthsInDebt = rec.debtMonths(None if excelFile.requestParameters.noMonths else MonthsToMonthYearFormat(excelFile.requestParameters.reportingMonths, rec.year), 
                                                          excelFile.requestParameters.reportOnlyIfAllInARow)
                        
                        rec.months = '?' if rec.uncalculated else \
                        ','.join(['%s-%s' % (str(p[0]), str(p[-1])) if len(p) > 1 else str(p[0]) for p in 
                                               utils.MonthsConsecutivify(rec.monthsInDebt) ])                                                                                                    
                        
                        #if rec.owner is empty, that means that the owner lives at the appartment and its details 
                        #are in the renter columns, otherwise there is a renter and an owner
                        
                        #only one record for this app, an owner one, fetch details from the renter column                        
                        if not len(rec.owner): 
                            ownerRecord = copy.copy(rec)
                            ownerRecord.isRenter = False
                            ownerRecord.isDefacto = True
                            ownerRecord.name = ownerRecord.renter
                            ownerRecord.mails = ownerRecord.renterMails
                            ownerRecord.phones = ownerRecord.renterPhones
                            
                            ownerRecord.historyAlerts = tenantsHistory.get( (utils.TidyFileName(TidyField(ownerRecord.appartment)), 
                                                                             utils.TidyFileName(TidyField(ownerRecord.name))), [])
                            
                            self.groups[excelFile.sheet.buildingDescription][i].append(ownerRecord)
                            
                        else:                                
                            renterRecord = copy.copy(rec)
                            renterRecord.isRenter = True
                            renterRecord.isDefacto = True
                            renterRecord.name = renterRecord.renter
                            renterRecord.mails = renterRecord.renterMails
                            renterRecord.phones = renterRecord.renterPhones
                            
                            renterRecord.historyAlerts = tenantsHistory.get( (utils.TidyFileName(TidyField(renterRecord.appartment)), 
                                                                              utils.TidyFileName(TidyField(renterRecord.name))), [])
                            
                            self.groups[excelFile.sheet.buildingDescription][i].append(renterRecord)
                            
                            ownerRecord = copy.copy(rec)
                            ownerRecord.isRenter = False
                            ownerRecord.isDefacto = False
                            ownerRecord.name = ownerRecord.owner
                            ownerRecord.mails = ownerRecord.ownerMails
                            ownerRecord.phones = ownerRecord.ownerPhones
                            
                            ownerRecord.historyAlerts = tenantsHistory.get( (utils.TidyFileName(TidyField(ownerRecord.appartment)), 
                                                                             utils.TidyFileName(TidyField(ownerRecord.name))), [])
                            
                            self.groups[excelFile.sheet.buildingDescription][i].append(ownerRecord)
                            
                        
    def prepareExecutiveReport(self, requestParameters):
        
        tenants = [t for building, recordsOf in sorted(self.groups.items())
                   for appartment, appTenantsOwners in sorted(recordsOf.items()) for t in appTenantsOwners
                   if t.uncalculated or ((int(t.debt) > 0 and int(t.debt) >= requestParameters.threshold) or t.previousDebt)]        
        
        buildingsNum = len(set(t.building for t in tenants))
        total = utils.Commafy(sum(int(t.debt) for t in tenants if not t.uncalculated))        
        columns_toolTips = zip(['כללי', 'שם', 'תשלום חודשי', 'חוב קודם', 'חוב נוכחי', 'סה"כ חוב',  'שנת דיווח', 'חודשים'], ['general', 'name', 'payment','previous_debt', 'debt', 'total_debt', 'year', 'months'])
        values_classes = [('general', 'general'), ('name', 'name'), ('payment', 'payment'), ('previousDebt', 'previousDebt'), ('debt', 'debt'), ('totalDebt', 'totalDebt'), ('year', 'year'), ('months', 'months')]
        
        return Alerter.report(requestParameters, tenants, buildingsNum, columns_toolTips, values_classes, total)    
        
    
    class ExcelFile(object):      
        
        def __init__(self, excel, requestParameters):
            self.excel = excel
            self.requestParameters = requestParameters            
            self.workbook = xlrd.open_workbook(excel, formatting_info=True)
            sh = self._getSheet(requestParameters.year)
            #sometimes there is no sheet and this is fine (for example, user selected a year which not in the excel file)
            self.sheet = self.ExcelSheet(excel, sh) if sh else None
        
        def _getSheet(self, requestedYear):
            worksheet = None
            #find specific sheet
            worksheets = self.workbook.sheet_names()                                                
            
            for worksheet_name in worksheets:
                if str(requestedYear) in worksheet_name and worksheet_name.startswith(utils.config.excelPaymentSheetPrefix):
                    return self.workbook.sheet_by_name(worksheet_name)
           
                        
        class ExcelSheet(ExcelSheetBase):
            MandatoryFields = [u"דירה", 
                               u"תשלום חודשי",                               
                               u'טלפון בעלים', 
                               u'מייל בעלים', 
                               u'טלפון דיירים', 
                               u'מייל דיירים', 
                               u'שם בעלים', 
                               u'שם דיירים']
            
            def __init__(self, excel, workSheet):
                super(OngoingDebtsReporter.ExcelFile.ExcelSheet, self).__init__(excel, workSheet)
                        
            class ExcelRecord(object):
                def __init__(self, record, sheet):                    
                    self.sheet = sheet
                    self.uncalculated = False
                    
                    for k, cell in record.items():       
                        setattr(self, k, cell) 
                        
                    #diiferent states per row which translated into a row highlight in the css
                    self.fishy = False
                    self.problematic = False
                    self.multiple_partial = False
                    self.vaad = False
                    self.legal = False
                
                @property
                def skip(self):                    
                    return self.appartment == '*'
                    
                @property
                def eof(self):                    
                    return self.appartment == ''
                
                @property
                def appartment(self):
                    cell = getattr(self, 'דירה')
                    app = TidyField(ExtractValue(cell))
                                                            
                    try:                       
                        return int(app)
                    except ValueError:
                        return app
                
                @property
                def owner(self):
                    cell = getattr(self, 'שם בעלים')
                    return TidyField(ExtractValue(cell))
                
                @property
                def renter(self):
                    cell = getattr(self, 'שם דיירים')
                    return TidyField(ExtractValue(cell))
                
                @property
                def payment(self):
                    cell = getattr(self, 'תשלום חודשי')
                    payment = TidyField(ExtractValue(cell))
                                        
                    try:
                        return int(payment)
                    except ValueError:                
                        return payment
        
                @property
                def ownerMails(self):                    
                    cell = getattr(self, 'מייל בעלים')                    
                    ownerMails = TidyField(ExtractValue(cell)).split()                                        
                    return ownerMails
                
                @property
                def renterMails(self):               
                    cell = getattr(self, 'מייל דיירים')
                    renterMails = TidyField(ExtractValue(cell)).split()
                    return renterMails
                
                @property
                def ownerPhones(self):                    
                    cell = getattr(self, 'טלפון בעלים')
                    ownerPhones = TidyField(ExtractValue(cell)).split()                                        
                    return ownerPhones
                
                @property
                def renterPhones(self):               
                    cell = getattr(self, 'טלפון דיירים')
                    renterPhones = TidyField(ExtractValue(cell)).split()
                    return renterPhones

                @property
                def debt(self):                    
                    return '?' if self.uncalculated else sum(d for d in self.monthsInDebt.values())
                
                @property
                def previosDebtValue(self):
                    cell = getattr(self, 'חוב נצבר', None)
                    if not cell:
                        return 0
                    
                    previousDebt = TidyField(ExtractValue(cell))                   
                    
                    if len(previousDebt):
                        try:
                            return int(previousDebt.strip())
                        except:
                            return 0
                        
                    return 0
                    
                @property
                def previousDebt(self):
                    if self.uncalculated:
                        return '?'
                    
                    pdCell = getattr(self, 'חוב נצבר', None)
                    if not pdCell:
                        return 0
                    
                    previousDebtBackGround = ExtractBackground(getattr(self, 'חוב נצבר'), self.sheet)                    
                    
                    #if color is a debt color, return its value
                    if previousDebtBackGround == COLOR_DEBT:
                        return self.previosDebtValue if self.previosDebtValue > 0 else 0
                    
                    #color is not a debt color, no matter what is written it is not a debt
                    else:
                        return 0
                    
                @property
                def totalDebt(self):
                    if self.uncalculated:
                        return '?'
                    
                    else:
                        return self.debt + self.previousDebt                                        
                      
                #this is the most problematic method
                def debtMonths(self, reportingMonths, reportOnlyIfAllInARow):
                   
                    debts = {}
                    multiple_partial = False
                    fishy = False
                    monthlyDebtOf = {}
                    
                    #months can be partial (when company takes ownership of the building in the middle of the year for example)                    
                    allMonths = sorted([k for k in self.__dict__ if dates.datify(k, self.year)], key= (lambda dateColumn: dates.datify(dateColumn)))
                    
                    if not reportingMonths:                       
                        reportingMonths = [dates.datify(m) for m in allMonths if dates.datify(m) <= datetime.date.today() ]
                        
                    previousDebtBackGround = ExtractBackground(getattr(self, 'חוב נצבר'), self.sheet)
                    
                    previousDebtValue = self.previosDebtValue
                    
                    #if at least one cell has a problematic color set, than mark the whole row as problematic
                    problematic = any(self.getCellBackGround(str(month)) in PROBLEMATIC_COLORS for month in allMonths) or \
                        previousDebtBackGround in PROBLEMATIC_COLORS
                    
                    #if at least one cell has a vaad color set, than mark the whole row as special problematic
                    problematic2 = any(self.getCellBackGround(str(month)) == COLOR_PROBLEMATIC_1 for month in allMonths) or \
                        previousDebtBackGround == COLOR_PROBLEMATIC_1
                    
                    #if at least one cell has a vaad color set, than mark the whole row as vaad
                    vaad = any(self.getCellBackGround(str(month)) == COLOR_VAAD for month in allMonths) or \
                        previousDebtBackGround == COLOR_VAAD
                    
                    #if at least one cell has a vaad color set, than mark the whole row as vaad
                    legal = any(self.getCellBackGround(str(month)) == COLOR_LEGAL_WARNING for month in allMonths) or \
                        previousDebtBackGround == COLOR_LEGAL_WARNING
                                        
                    #a cell which has an amount at least as the fix payment and still marked as debt where 
                    #the previous debt cell is marked as not in debt, then this is fishy
                    fishy = any(self.getCellBackGround(str(month)) == COLOR_DEBT and 
                                utils.Intify(self.monthlyPayment(month)) >= self.payment and 
                                previousDebtBackGround in COLORS_NON_DEBT
                                for month in allMonths)
                                        
                        
                    #calculate how much was paid during the year, treat COLOR_STANDING_ORDER cells as fully paid
                    totalPaid = sum(max( utils.Intify(self.monthlyPayment(month)), 
                                         self.payment if self.getCellBackGround(str(month)) == COLOR_STANDING_ORDER else 0 )
                                    for month in allMonths)
                    
                    #deduct past debt if this was paid during the year
                    totalPaid = totalPaid - (previousDebtValue if previousDebtBackGround != COLOR_DEBT else 0)
                    
                    #calculate expected payments for the year
                    expectedPayments = len(allMonths)*self.payment                                                            
                        
                    partialPayment = totalPaid % self.payment if self.payment else 0
                    
                    if self.payment:
                        if totalPaid / self.payment >= len(allMonths):
                            partialPayment = 0
                    
                    partialPaymentsCounter = 0
                                        
                    for month in allMonths:
                        formattedMonth = dates.datify(month)
                        
                        if self.getCellBackGround(str(month)) == COLOR_DEBT:
                            #partial if has a √ sign or a number
                            if self.monthlyPayment(month) == '√':
                                monthlyDebtOf[formattedMonth] = self.payment - partialPayment
                                partialPaymentsCounter += 1
                                
                            elif utils.Intify(self.monthlyPayment(month)):
                                if utils.Intify(self.monthlyPayment(month)) < self.payment:
                                    monthlyDebtOf[formattedMonth] = self.payment - partialPayment
                                    partialPaymentsCounter += 1
                                else:
                                    monthlyDebtOf[formattedMonth] = self.payment
                                
                            else:
                                monthlyDebtOf[formattedMonth] = self.payment
                                
                        #color standing order are fully paid, therefore are not debts
                        elif self.getCellBackGround(str(month)) != COLOR_STANDING_ORDER:
                            #this indicates the month was paid for
                            if self.monthlyPayment(month) == '√':
                                continue
                            #this indicates that the cell is not empty or has a number in it --> therefore this month was paid for
                            if utils.Intify(self.monthlyPayment(month)):
                                continue
                            
                            #empty cell or has a text in it therefore a debt
                            monthlyDebtOf[formattedMonth] = self.payment                                                            
                        
                    totalDebts = sum(monthlyDebtOf.values())	                    
                      
                    #can not relate partial debt to a specific month where previous debt was covered during the year
                    #dono how to deal with multiple partials debts
                    if (partialPayment and previousDebtValue and previousDebtBackGround != COLOR_DEBT) or partialPaymentsCounter > 1:
                        multiple_partial = True
                    
                    
                    if expectedPayments != totalDebts + totalPaid:
                        if totalDebts == 0:
                            if totalDebts + totalPaid < expectedPayments:
                                fishy = True
                                
                        else:
                            if expectedPayments > totalDebts + totalPaid:
                                multiple_partial = True
                                                                    
                    if legal:
                        self.legal = True
                        self.uncalculated = True
                        
                    elif problematic:
                        self.problematic = True 
                        self.uncalculated = True 
                        
                    elif problematic2:
                        self.problematic2 = True 
                        self.uncalculated = True
                        
                    elif fishy:
                        self.fishy = True
                        self.uncalculated = True
                        
                    elif multiple_partial:
                        self.multiple_partial = True
                        self.uncalculated = True                                                
                    elif vaad:
                        self.vaad = True
                        self.uncalculated = True
                   
                    debts = {month:debt for month, debt in monthlyDebtOf.items() 
                             if month in reportingMonths }
                    
                    #for month, debt in monthlyDebtOf.items():
                        #if reportingMonths:
                    
                    #if self.uncalculated:
                        #debts =  {'?': '?'}                        
                        
                    if reportOnlyIfAllInARow:
                        return debts if all(m in debts.keys() for m in reportingMonths) else {}                    
                    
                    return debts
                                            
                def getCellBackGround(self, key):
                    cell = getattr(self, key)
                    return ExtractBackground(cell, self.sheet)
                
                
                def monthlyPayment(self, month):
                    cell = getattr(self, str(month))
                    return TidyField(ExtractValue(cell))                    
                
                

class SpecialDebtsReporter(ReportersBase):  
        
    def __init__(self, requestParameters, serverInClient):
        super(SpecialDebtsReporter, self).__init__(requestParameters, serverInClient, utils.config.excelSpecialFilePrefix) 
                    
    def build(self, helper=None, helperFields=None, historydata=None):
    
        errMessage = None
        includes, ignores = self.includes, self.ignores
        
        for dirpath, dirnames, filenames in os.walk(utils.config.rootBuildingsDir):            
            head, tail = os.path.split(dirpath)
            
            def showError():
                return utils.SSE_MSG(
                            message = errMessage,
                            label = 'בעיה בסריקת הקובץ :%s ' % 
                            excelFile.excel.encode('utf-8') + 
                            ('   <button class="ignore" type="button" id="%s">התעלם מבניין זה</button> ' % building.encode('utf-8')) if building else '',
                            progress = 0,
                            msgType = 'error'
                        )
            
            def handleError():
                if self.serverInClient:
                    os.startfile(excelFile.excel)
                else:
                    utils.Md('errors')                                        
                    shutil.copy2(excelFile.excel, 'errors')
    
                    return utils.SSE_MSG_DOWNLOAD(os.path.basename(excelFile.excel).encode('utf-8'), 'errors')
            #if includes is empty, split by ',' will generate an array of one empty string
            def noIncludes():
                return len(includes)==1 and not len(includes[0])
            
            #if no includes defined, then treat the dir as included
            def inIncludes():
                return  noIncludes() or building in includes
            
            def notInIgnores():
                return building not in ignores                       
                        
            for extension in ('*.xls', '*.xlsx'):
                for filename in fnmatch.filter(filenames, '%s*%s' % (self.excelPrefix, extension)):                    
                    excel = os.path.join(dirpath, filename)                    
                    excelFile = self.ExcelFile(excel, self.requestParameters)
                    
                    if self.broken:
                        break
                    
                    #no interesting sheet found in the file, continue to next file
                    if not excelFile.sheet:
                        continue
                    
                    building = None
                    excelFile.sheet.parseBuildingMetaData()
                    excelFile.sheet.parseGeneralData()
                    
                    #when parsing failed we do not know which building this excel represents,
                    #when there is no includes we'll show this error
                    if not excelFile.sheet.buildingDescription :
                        if noIncludes():
                            errMessage =  bottle.template('web/templates/errors/error_building_format', 
                                   date = datetime.date.today().strftime("%d/%m/%Y"),
                                   file_name = excelFile.sheet.excel,
                                   company_name = utils.config.companyName,
                                   sheet = excelFile.sheet.workSheet.name,
                                   A1_value = getattr(excelFile.sheet, 'A1value', ""),
                                   company_web_site = utils.config.companyWebSite,
                                   company_logo = utils.config.companyLogo)
                            yield showError()
                            yield handleError()                                                                
                            self.broken = True
                            break
                        else:
                            continue
                        
                    #got here, we know which building this file represents                
                    building = excelFile.sheet.buildingDescription                    
                    general = excelFile.sheet.generalData
                    
                    if notInIgnores() and inIncludes():
                                
                        yield utils.SSE_MSG(
                            message = utils.Html(['בונה נתוני גבייה מיוחדת של בניין: %s, מקובץ : %s' % 
                                                  ('<b>%s</b>' % building.encode('utf-8'), 
                                                   '<b>%s</b>' % utils.Normpath(excelFile.excel).encode('utf-8')) ], True),
                            label = 'קולט נתונים...')                        
                        
                        errMessage = excelFile.sheet.validateHeader(excelFile.sheet.MandatoryFields)
                    
                        if errMessage:
                            yield showError()
                            yield handleError()                                                                
                            self.broken = True
                            break
                        
                        buildingHelper = helper.get(excelFile.sheet.buildingDescription, None)
                        
                        if not buildingHelper:                                        
                            errMessage = bottle.template('web/templates/errors/error_missing_building', 
                                date = datetime.date.today().strftime("%d/%m/%Y"),
                                building = building,
                                file_name = excelFile.excel,
                                company_name = utils.config.companyName,
                                sheet = excelFile.sheet.workSheet.name,                                        
                                company_web_site = utils.config.companyWebSite,
                                company_logo = utils.config.companyLogo)
                            
                            yield showError()
                            yield handleError()
                            self.broken = True
                            break
                            
                        for i,record in enumerate(excelFile.sheet.fetchRecords()):
                
                            if self.broken:
                                break                                                                  
                            
                            rec = self.ExcelFile.ExcelSheet.ExcelRecord(record, excelFile.requestParameters.destination, excelFile.sheet)
                            
                            if rec.eof:
                                break
                            
                            if rec.skip:
                                continue
                            
                            tenant = buildingHelper.get(rec.appartment, None)
                                
                            if not tenant:
                                errMessage = bottle.template('web/templates/errors/error_missing_tenant', 
                                   date = datetime.date.today().strftime("%d/%m/%Y"),
                                   file_name = excelFile.excel,
                                   sheet = excelFile.sheet.workSheet.name,
                                   tenant_app = rec.appartment,
                                   company_name = utils.config.companyName,
                                   company_web_site = utils.config.companyWebSite,
                                   company_logo = utils.config.companyLogo)
                                yield showError()
                                yield handleError()
                                self.broken = True
                                break
                                                                      
                            rec.source = utils.Normpath(excel).replace('/', '*')
                            rec.building = building
                            rec.general = general
                            rec.description = excelFile.sheet.description
                            rec.year = self.requestParameters.year
                            
                                                         
                            for fieldName in helperFields:                                    
                                fieldValue = getattr(helper[excelFile.sheet.buildingDescription][rec.appartment], fieldName, "")
                                setattr(rec, fieldName, fieldValue)
                                                        
                            self.groups[excelFile.sheet.buildingDescription][excelFile.sheet.description][i] = rec                
                            
    def prepareExecutiveReport(self, requestParameters):                
        
        tenants = [t for building, appatmentOf in sorted(self.groups.items())
                   for description, recordsOf in sorted(appatmentOf.items())
                   for appartment, t in sorted(recordsOf.items())
                   if int(t.debt) > 0 and int(t.debt) >= requestParameters.threshold]
        
        buildingsNum = len(set(t.building for t in tenants))
        total = utils.Commafy(sum(int(t.debt) for t in tenants))        
        columns_toolTips = zip(['כללי', 'גבייה מיוחדת', 'שם בעלים', 'חוב', 'שנה'], ['general', 'description', 'name', 'debt', 'year'])
        values_classes = [('general', 'general'), ('description', 'description'), ('owner', 'name'), ('debt', 'debt'), ('year', 'year')]                
        
        return Alerter.report(requestParameters, tenants, buildingsNum, columns_toolTips, values_classes, total)    
        
    
    class ExcelFile(object):      
        
        def __init__(self, excel, requestParameters):
            self.excel = excel
            self.requestParameters = requestParameters
            self.workbook = xlrd.open_workbook(excel, formatting_info=True)
            sh = self._getSheet(requestParameters.year)
            #sometimes there is no sheet and this is fine (for example, user selected a year which is just no in the excel file)
            self.sheet = self.ExcelSheet(excel, sh) if sh else None
        
        def _getSheet(self, requestedYear):
            worksheet = None
            #find specific sheet
            worksheets = self.workbook.sheet_names()                                                
            
            for worksheet_name in worksheets:
                if str(requestedYear) in worksheet_name and worksheet_name.startswith(utils.config.excelSpecialSheetPrefix):
                    return self.workbook.sheet_by_name(worksheet_name)                
        
        class ExcelSheet(ExcelSheetBase):
            MandatoryFields = [u"דירה", u"יתרה לתשלום"]
            
            def __init__(self, excel, workSheet):
                super(SpecialDebtsReporter.ExcelFile.ExcelSheet, self).__init__(excel, workSheet)                                        
                                
            
            class ExcelRecord(object):
                def __init__(self, record, destination, sheet):
                    self.destination = destination
                    self.sheet = sheet
                    
                    for k, v in record.items():                        
                        setattr(self, k, v)                                            
                
                @property
                def debt(self):
                    return getattr(self, 'יתרה לתשלום')
                                
                
                @property
                def skip(self):                    
                    return False
                    
                @property
                def eof(self):                    
                    return self.appartment == ''
                
                @property
                def appartment(self):
                    try:
                        app = getattr(self, 'דירה')
                        return int(app)
                    except ValueError:
                        return app
                
                @property
                def name(self):
                    return getattr(self, 'שם', "")                
                
                @property
                def owner(self):
                    return getattr(self, 'שם בעלים')
                
                @property
                def renter(self):
                    return getattr(self, 'שם שוכרים')
                
                @property
                def mails(self):
                    
                    if self.destination == Alerter.DESTINATION_ALL:
                        return getattr(self, 'דואר אלקטרוני שוכרים').split() + getattr(self, 'דואר אלקטרוני בעלים').split()
                    
                    elif self.destination == Alerter.DESTINATION_RENTAL:
                        return getattr(self, 'דואר אלקטרוני שוכרים').split()
                    
                    elif self.destination == Alerter.DESTINATION_OWNER:
                        return getattr(self, 'דואר אלקטרוני בעלים').split()
                    
                    elif self.destination == Alerter.DESTINATION_DE_FACTO:
                        if len(self.renter):
                            return getattr(self, 'דואר אלקטרוני שוכרים').split()
                        else:
                            return getattr(self, 'דואר אלקטרוני בעלים').split()
                    
                
                @property
                def phones(self):
                    if self.destination == Alerter.DESTINATION_ALL:
                        return getattr(self, 'טלפון שוכרים').split() + getattr(self, 'טלפון בעלים').split()
                    
                    elif self.destination == Alerter.DESTINATION_RENTAL:
                        return getattr(self, 'טלפון שוכרים').split()
                    
                    elif self.destination == Alerter.DESTINATION_OWNER:
                        return getattr(self, 'טלפון בעלים').split()
                    
                    elif self.destination == Alerter.DESTINATION_DE_FACTO:
                        if len(self.renter):
                            return getattr(self, 'טלפון שוכרים').split()
                        else:
                            return getattr(self, 'טלפון בעלים').split()
                

class GeneralMessagingReporters(ReportersBase):  
        
    InfoFields = []
    
    def __init__(self, requestParameters, serverInClient):
        super(GeneralMessagingReporters, self).__init__(requestParameters, serverInClient, utils.config.excelPaymentFilePrefix)
        
    def build(self, helper=None, helperFields=None, historydata=None):
    
        includes, ignores = self.includes, self.ignores
        
        for dirpath, dirnames, filenames in os.walk(utils.config.rootBuildingsDir):            
            head, tail = os.path.split(dirpath)
           
            def showError():
                return utils.SSE_MSG(
                            message = errMessage,
                            label = 'בעיה בסריקת הקובץ :%s ' % 
                            excelFile.excel.encode('utf-8') + 
                            ('   <button class="ignore" type="button" id="%s">התעלם מבניין זה</button> ' % building.encode('utf-8')) if building else '',
                            progress = 0,
                            msgType = 'error'
                        )
            
            def handleError():
                if self.serverInClient:
                    os.startfile(excelFile.excel)
                else:
                    utils.Md('errors')                                        
                    shutil.copy2(excelFile.excel, 'errors')
    
            #if includes is empty, split by ',' will generate an array of one empty string
            def noIncludes():
                return len(includes)==1 and not len(includes[0])
            
            #if no includes defined, then treat the dir as included
            def inIncludes():
                return  noIncludes() or building in includes
            
            def notInIgnores():
                return building not in ignores                       
                                    
            #can not retreive background color of cells at xlsx files cause xlrd doesn't support that (only for xls)            
            for filename in fnmatch.filter(filenames, '*%s*.xls' % self.excelPrefix ):                    
                excel = os.path.join(dirpath, filename)
                
                excelFile = self.ExcelFile(excel, self.requestParameters)
                
                if self.broken:
                    break
                
                #no interesting sheet found in the file, continue to next file
                if not excelFile.sheet:
                    continue                                                    
                
                building = None    
                excelFile.sheet.parseBuildingMetaData()
                excelFile.sheet.parseGeneralData()
                
                #when parsing failed we do not know which building this excel represents,
                #when there is no includes we'll show this error
                if not excelFile.sheet.buildingDescription :
                    if noIncludes():
                        
                        errMessage =  bottle.template('web/templates/errors/error_building_format', 
                               date = datetime.date.today().strftime("%d/%m/%Y"),
                               file_name = excelFile.sheet.excel,
                               company_name = utils.config.companyName,
                               sheet = excelFile.sheet.workSheet.name,
                               A1_value = getattr(excelFile.sheet, 'A1value', ""),
                               company_web_site = utils.config.companyWebSite,
                               company_logo = utils.config.companyLogo)
                        yield showError()
                        yield handleError()                                                                
                        self.broken = True
                        break
                    else:
                        continue
                    
                #got here, we know which building this file represents                
                building = excelFile.sheet.buildingDescription                    
                general = excelFile.sheet.generalData
                
                if notInIgnores() and inIncludes():                                               
                    
                    yield utils.SSE_MSG(
                            message = utils.Html(['בונה נתוני דיירים של בניין: %s, מקובץ : %s' % 
                                                  ('<b>%s</b>' % building.encode('utf-8'), 
                                                   '<b>%s</b>' % utils.Normpath(excelFile.excel).encode('utf-8')) ], True),
                            label = 'קולט נתונים...')
                    
                    errMessage = excelFile.sheet.validateHeader(excelFile.sheet.MandatoryFields)
                
                    if errMessage:
                        yield showError()
                        yield handleError()                                                                
                        self.broken = True
                        break
                    
                    
                    tenantsHistory = defaultdict(# (appartment, name)
                                lambda: defaultdict(  # (date, time, formatTemplate)
                                    list # (alert, alertFile)
                                    ))
                                        
                    buildingHistory = utils.TidyFileName(building)
                    execType = Alerter.getExecutionDesc(self.requestParameters.mode)                       
                    #organize history per this building, per this executionMode                        
                    for d in sorted(historydata[buildingHistory]):
                        for t in historydata[buildingHistory][d]:
                            for formatTemplate in historydata[buildingHistory][d][t][execType]:
                                for appartment in historydata[buildingHistory][d][t][execType][formatTemplate]:
                                    for name in historydata[buildingHistory][d][t][execType][formatTemplate][appartment]:
                                        for alert in historydata[buildingHistory][d][t][execType][formatTemplate][appartment][name]:
                                            for alertDestination in historydata[buildingHistory][d][t][execType][formatTemplate][appartment][name][alert]:
                                                alertFile = historydata[buildingHistory][d][t][execType][formatTemplate][appartment][name][alert][alertDestination]
                                                tenantsHistory[(TidyField(appartment), TidyField(name))][(d, t, formatTemplate)].append((alert, alertFile))
                                                    
                    for i,record in enumerate(excelFile.sheet.fetchRecords()):
            
                        if self.broken:
                            break
                                    
                        rec = self.ExcelFile.ExcelSheet.ExcelRecord(record, excelFile.sheet)
                        
                        if rec.skip:
                            continue
                                            
                        if rec.eof:
                            break
                                                                                                                
                        if self.broken:
                            break
                                                                                                                                         
                                                        
                        rec.source = utils.Normpath(excel).replace('/', '*')
                        rec.building = building
                        rec.general = general
                        rec.year = self.requestParameters.year                                                
                        
                        #if rec.owner is empty, that means that the owner lives at the appartment and its details 
                        #are in the renter columns, otherwise there is a renter and an owner
                        
                        #only one record for this app, an owner one, fetch details from the renter column
                        if not len(rec.owner): 
                            ownerRecord = copy.copy(rec)
                            ownerRecord.isRenter = False
                            ownerRecord.isDefacto = True
                            ownerRecord.name = ownerRecord.renter
                            ownerRecord.mails = ownerRecord.renterMails
                            ownerRecord.phones = ownerRecord.renterPhones
                            
                            ownerRecord.historyAlerts = tenantsHistory.get( (utils.TidyFileName(TidyField(ownerRecord.appartment)), 
                                                                             utils.TidyFileName(TidyField(ownerRecord.name))), [])
                            
                            self.groups[excelFile.sheet.buildingDescription][i].append(ownerRecord)
                            
                        else:                                
                            renterRecord = copy.copy(rec)
                            renterRecord.isRenter = True
                            renterRecord.isDefacto = True
                            renterRecord.name = renterRecord.renter
                            renterRecord.mails = renterRecord.renterMails
                            renterRecord.phones = renterRecord.renterPhones
                            
                            renterRecord.historyAlerts = tenantsHistory.get( (utils.TidyFileName(TidyField(renterRecord.appartment)), 
                                                                              utils.TidyFileName(TidyField(renterRecord.name))), [])
                            
                            self.groups[excelFile.sheet.buildingDescription][i].append(renterRecord)
                            
                            ownerRecord = copy.copy(rec)
                            ownerRecord.isRenter = False
                            ownerRecord.isDefacto = False
                            ownerRecord.name = ownerRecord.owner
                            ownerRecord.mails = ownerRecord.ownerMails
                            ownerRecord.phones = ownerRecord.ownerPhones
                            
                            ownerRecord.historyAlerts = tenantsHistory.get( (utils.TidyFileName(TidyField(ownerRecord.appartment)), 
                                                                             utils.TidyFileName(TidyField(ownerRecord.name))), [])
                            
                            self.groups[excelFile.sheet.buildingDescription][i].append(ownerRecord)
                            
                        
    def prepareExecutiveReport(self, requestParameters):
        
        tenants = [t for building, recordsOf in sorted(self.groups.items())
                   for appartment, appTenantsOwners in sorted(recordsOf.items()) for t in appTenantsOwners]
        buildingsNum = len(set(t.building for t in tenants))        
        columns_toolTips = zip(['כללי', 'שם', 'תשלום חודשי'], ['general', 'name', 'payment'])
        values_classes = [('general', 'general'), ('name', 'name'), ('payment', 'payment')]
        
        return Alerter.report(requestParameters, tenants, buildingsNum, columns_toolTips, values_classes)
        
    
    class ExcelFile(object):      
        
        def __init__(self, excel, requestParameters):
            self.excel = excel
            self.requestParameters = requestParameters
            self.workbook = xlrd.open_workbook(excel, formatting_info=True)
            sh = self._getSheet(requestParameters.year)
            #sometimes there is no sheet and this is fine (for example, user selected a year which not in the excel file)
            self.sheet = self.ExcelSheet(excel, sh) if sh else None
        
        def _getSheet(self, requestedYear):
            worksheet = None
            #find specific sheet
            worksheets = self.workbook.sheet_names()                                                
            
            for worksheet_name in worksheets:
                if str(requestedYear) in worksheet_name and worksheet_name.startswith(utils.config.excelPaymentSheetPrefix):
                    return self.workbook.sheet_by_name(worksheet_name)
           
                        
        class ExcelSheet(ExcelSheetBase):
            MandatoryFields = [u"דירה", 
                               u"תשלום חודשי",
                               u"חוב נצבר",
                               u'טלפון בעלים', 
                               u'מייל בעלים', 
                               u'טלפון דיירים', 
                               u'מייל דיירים', 
                               u'שם בעלים', 
                               u'שם דיירים']
            
            def __init__(self, excel, workSheet):
                super(GeneralMessagingReporters.ExcelFile.ExcelSheet, self).__init__(excel, workSheet)
                        
            class ExcelRecord(object):
                def __init__(self, record, sheet):                    
                    self.sheet = sheet
                    
                    for k, cell in record.items():       
                        setattr(self, k, cell)                                            
                
                @property
                def skip(self):                    
                    return self.appartment == '*'
                    
                @property
                def eof(self):                    
                    return self.appartment == ''
                
                @property
                def appartment(self):
                    cell = getattr(self, 'דירה')
                    app = TidyField(ExtractValue(cell))
                                                            
                    try:                       
                        return int(app)
                    except ValueError:
                        return app
                
                @property
                def owner(self):
                    cell = getattr(self, 'שם בעלים')
                    return TidyField(ExtractValue(cell))
                
                @property
                def renter(self):
                    cell = getattr(self, 'שם דיירים')
                    return TidyField(ExtractValue(cell))
                
                @property
                def payment(self):
                    cell = getattr(self, 'תשלום חודשי')
                    payment = TidyField(ExtractValue(cell))
                                        
                    try:
                        return int(payment)
                    except ValueError:                
                        return payment
        
                @property
                def ownerMails(self):                    
                    cell = getattr(self, 'מייל בעלים')                    
                    ownerMails = TidyField(ExtractValue(cell)).split()                                        
                    return ownerMails
                
                @property
                def renterMails(self):               
                    cell = getattr(self, 'מייל דיירים')
                    renterMails = TidyField(ExtractValue(cell)).split()
                    return renterMails
                
                @property
                def ownerPhones(self):                    
                    cell = getattr(self, 'טלפון בעלים')
                    ownerPhones = TidyField(ExtractValue(cell)).split()                                        
                    return ownerPhones
                
                @property
                def renterPhones(self):               
                    cell = getattr(self, 'טלפון דיירים')
                    renterPhones = TidyField(ExtractValue(cell)).split()
                    return renterPhones

                @property
                def debt(self):                    
                    return sum(d for d in self.monthsInDebt.values())
                
                @property
                def previosDebtValue(self):
                    cell = getattr(self, 'חוב נצבר', None)
                    if not cell:
                        return 0
                    
                    previousDebt = TidyField(ExtractValue(cell))                   
                    
                    if len(previousDebt):
                        try:
                            return int(previousDebt.strip())
                        except:
                            return 0
                        
                    return 0                                
                         
                def getCellBackGround(self, key):
                    cell = getattr(self, key)
                    return ExtractBackground(cell, self.sheet)
                
                
                def monthlyPayment(self, month):
                    cell = getattr(self, str(month))
                    return TidyField(ExtractValue(cell))

class EventsHandlingReporters(ReportersBase):  
        
    InfoFields = []
    
    def __init__(self, requestParameters, serverInClient):
        super(EventsHandlingReporters, self).__init__(requestParameters, serverInClient, utils.config.excelPaymentFilePrefix)
        
    def build(self, helper=None, helperFields=None, historydata=None):
    
        includes, ignores = self.includes, self.ignores
        
        for dirpath, dirnames, filenames in os.walk(utils.config.rootBuildingsDir):            
            head, tail = os.path.split(dirpath)
           
            def showError():
                return utils.SSE_MSG(
                            message = errMessage,
                            label = 'בעיה בסריקת הקובץ :%s ' % 
                            excelFile.excel.encode('utf-8') + 
                            ('   <button class="ignore" type="button" id="%s">התעלם מבניין זה</button> ' % building.encode('utf-8')) if building else '',
                            progress = 0,
                            msgType = 'error'
                        )
            
            def handleError():
                if self.serverInClient:
                    os.startfile(excelFile.excel)
                else:
                    utils.Md('errors')                                        
                    shutil.copy2(excelFile.excel, 'errors')
    
            #if includes is empty, split by ',' will generate an array of one empty string
            def noIncludes():
                return len(includes)==1 and not len(includes[0])
            
            #if no includes defined, then treat the dir as included
            def inIncludes():
                return  noIncludes() or building in includes
            
            def notInIgnores():
                return building not in ignores                       
                                    
            #can not retreive background color of cells at xlsx files cause xlrd doesn't support that (only for xls)            
            for filename in fnmatch.filter(filenames, '*%s*.xls' % self.excelPrefix ):                    
                excel = os.path.join(dirpath, filename)
                
                excelFile = self.ExcelFile(excel, self.requestParameters)
                
                if self.broken:
                    break
                
                #no interesting sheet found in the file, continue to next file
                if not excelFile.sheet:
                    continue                                                    
                
                building = None    
                excelFile.sheet.parseBuildingMetaData()
                excelFile.sheet.parseGeneralData()
                
                #when parsing failed we do not know which building this excel represents,
                #when there is no includes we'll show this error
                if not excelFile.sheet.buildingDescription :
                    if noIncludes():
                        
                        errMessage =  bottle.template('web/templates/errors/error_building_format', 
                               date = datetime.date.today().strftime("%d/%m/%Y"),
                               file_name = excelFile.sheet.excel,
                               company_name = utils.config.companyName,
                               sheet = excelFile.sheet.workSheet.name,
                               A1_value = getattr(excelFile.sheet, 'A1value', ""),
                               company_web_site = utils.config.companyWebSite,
                               company_logo = utils.config.companyLogo)
                        yield showError()
                        yield handleError()                                                                
                        self.broken = True
                        break
                    else:
                        continue
                    
                #got here, we know which building this file represents                
                building = excelFile.sheet.buildingDescription                    
                general = excelFile.sheet.generalData
                
                if notInIgnores() and inIncludes():                                               
                    
                    yield utils.SSE_MSG(
                            message = utils.Html(['בונה נתוני דיירים של בניין: %s, מקובץ : %s' % 
                                                  ('<b>%s</b>' % building.encode('utf-8'), 
                                                   '<b>%s</b>' % utils.Normpath(excelFile.excel).encode('utf-8')) ], True),
                            label = 'קולט נתונים...')
                    
                    errMessage = excelFile.sheet.validateHeader(excelFile.sheet.MandatoryFields)
                
                    if errMessage:
                        yield showError()
                        yield handleError()                                                                
                        self.broken = True
                        break
                    
                    
                    tenantsHistory = defaultdict(# (appartment, name)
                                lambda: defaultdict(  # (date, time, formatTemplate)
                                    list # (alert, alertFile)
                                    ))
                                        
                    buildingHistory = utils.TidyFileName(building)
                    execType = Alerter.getExecutionDesc(self.requestParameters.mode)                       
                    #organize history per this building, per this executionMode                        
                    for d in sorted(historydata[buildingHistory]):
                        for t in historydata[buildingHistory][d]:
                            for formatTemplate in historydata[buildingHistory][d][t][execType]:
                                for appartment in historydata[buildingHistory][d][t][execType][formatTemplate]:
                                    for name in historydata[buildingHistory][d][t][execType][formatTemplate][appartment]:
                                        for alert in historydata[buildingHistory][d][t][execType][formatTemplate][appartment][name]:
                                            for alertDestination in historydata[buildingHistory][d][t][execType][formatTemplate][appartment][name][alert]:
                                                alertFile = historydata[buildingHistory][d][t][execType][formatTemplate][appartment][name][alert][alertDestination]
                                                tenantsHistory[(TidyField(appartment), TidyField(name))][(d, t, formatTemplate)].append((alert, alertFile))
                                                    
                    for i,record in enumerate(excelFile.sheet.fetchRecords()):
            
                        if self.broken:
                            break
                                    
                        rec = self.ExcelFile.ExcelSheet.ExcelRecord(record, excelFile.sheet)
                        
                        if rec.skip:
                            continue
                                            
                        if rec.eof:
                            break
                                                                                                                
                        if self.broken:
                            break
                                                                                                                                         
                                                        
                        rec.source = utils.Normpath(excel).replace('/', '*')
                        rec.building = building
                        rec.general = general
                        rec.event = self.requestParameters.event
                        rec.year = self.requestParameters.year                                                
                        
                        #if rec.owner is empty, that means that the owner lives at the appartment and its details 
                        #are in the renter columns, otherwise there is a renter and an owner
                        
                        #only one record for this app, an owner one, fetch details from the renter column
                        if not len(rec.owner): 
                            ownerRecord = copy.copy(rec)
                            ownerRecord.isRenter = False
                            ownerRecord.isDefacto = True
                            ownerRecord.name = ownerRecord.renter
                            ownerRecord.mails = ownerRecord.renterMails
                            ownerRecord.phones = ownerRecord.renterPhones
                            
                            ownerRecord.historyAlerts = tenantsHistory.get( (utils.TidyFileName(TidyField(ownerRecord.appartment)), 
                                                                             utils.TidyFileName(TidyField(ownerRecord.name))), [])
                            
                            self.groups[excelFile.sheet.buildingDescription][i].append(ownerRecord)
                            
                        else:                                
                            renterRecord = copy.copy(rec)
                            renterRecord.isRenter = True
                            renterRecord.isDefacto = True
                            renterRecord.name = renterRecord.renter
                            renterRecord.mails = renterRecord.renterMails
                            renterRecord.phones = renterRecord.renterPhones
                            
                            renterRecord.historyAlerts = tenantsHistory.get( (utils.TidyFileName(TidyField(renterRecord.appartment)), 
                                                                              utils.TidyFileName(TidyField(renterRecord.name))), [])
                            
                            self.groups[excelFile.sheet.buildingDescription][i].append(renterRecord)
                            
                            ownerRecord = copy.copy(rec)
                            ownerRecord.isRenter = False
                            ownerRecord.isDefacto = False
                            ownerRecord.name = ownerRecord.owner
                            ownerRecord.mails = ownerRecord.ownerMails
                            ownerRecord.phones = ownerRecord.ownerPhones
                            
                            ownerRecord.historyAlerts = tenantsHistory.get( (utils.TidyFileName(TidyField(ownerRecord.appartment)), 
                                                                             utils.TidyFileName(TidyField(ownerRecord.name))), [])
                            
                            self.groups[excelFile.sheet.buildingDescription][i].append(ownerRecord)
                            
                        
    def prepareExecutiveReport(self, requestParameters):
        
        tenants = [t for building, recordsOf in sorted(self.groups.items())
                   for appartment, appTenantsOwners in sorted(recordsOf.items()) for t in appTenantsOwners]
        buildingsNum = len(set(t.building for t in tenants))        
        columns_toolTips = zip(['כללי', 'שם', 'תשלום חודשי', 'אירוע'], ['general', 'name', 'payment', 'event'])
        values_classes = [('general', 'general'), ('name', 'name'), ('payment', 'payment'), ('event', 'event')]
        
        return Alerter.report(requestParameters, tenants, buildingsNum, columns_toolTips, values_classes)
        
    
    class ExcelFile(object):      
        
        def __init__(self, excel, requestParameters):
            self.excel = excel
            self.requestParameters = requestParameters
            self.workbook = xlrd.open_workbook(excel, formatting_info=True)
            sh = self._getSheet(requestParameters.year)
            #sometimes there is no sheet and this is fine (for example, user selected a year which not in the excel file)
            self.sheet = self.ExcelSheet(excel, sh) if sh else None
        
        def _getSheet(self, requestedYear):
            worksheet = None
            #find specific sheet
            worksheets = self.workbook.sheet_names()                                                
            
            for worksheet_name in worksheets:
                if str(requestedYear) in worksheet_name and worksheet_name.startswith(utils.config.excelPaymentSheetPrefix):
                    return self.workbook.sheet_by_name(worksheet_name)
           
                        
        class ExcelSheet(ExcelSheetBase):
            MandatoryFields = [u"דירה", 
                               u"תשלום חודשי",
                               u"חוב נצבר",
                               u'טלפון בעלים', 
                               u'מייל בעלים', 
                               u'טלפון דיירים', 
                               u'מייל דיירים', 
                               u'שם בעלים', 
                               u'שם דיירים']
            
            def __init__(self, excel, workSheet):
                super(EventsHandlingReporters.ExcelFile.ExcelSheet, self).__init__(excel, workSheet)
                        
            class ExcelRecord(object):
                def __init__(self, record, sheet):                    
                    self.sheet = sheet
                    
                    for k, cell in record.items():       
                        setattr(self, k, cell)                                            
                
                @property
                def skip(self):                    
                    return self.appartment == '*'
                    
                @property
                def eof(self):                    
                    return self.appartment == ''
                
                @property
                def appartment(self):
                    cell = getattr(self, 'דירה')
                    app = TidyField(ExtractValue(cell))
                                                            
                    try:                       
                        return int(app)
                    except ValueError:
                        return app
                
                @property
                def owner(self):
                    cell = getattr(self, 'שם בעלים')
                    return TidyField(ExtractValue(cell))
                
                @property
                def renter(self):
                    cell = getattr(self, 'שם דיירים')
                    return TidyField(ExtractValue(cell))
                
                @property
                def payment(self):
                    cell = getattr(self, 'תשלום חודשי')
                    payment = TidyField(ExtractValue(cell))
                                        
                    try:
                        return int(payment)
                    except ValueError:                
                        return payment
        
                @property
                def ownerMails(self):                    
                    cell = getattr(self, 'מייל בעלים')                    
                    ownerMails = TidyField(ExtractValue(cell)).split()                                        
                    return ownerMails
                
                @property
                def renterMails(self):               
                    cell = getattr(self, 'מייל דיירים')
                    renterMails = TidyField(ExtractValue(cell)).split()
                    return renterMails
                
                @property
                def ownerPhones(self):                    
                    cell = getattr(self, 'טלפון בעלים')
                    ownerPhones = TidyField(ExtractValue(cell)).split()                                        
                    return ownerPhones
                
                @property
                def renterPhones(self):               
                    cell = getattr(self, 'טלפון דיירים')
                    renterPhones = TidyField(ExtractValue(cell)).split()
                    return renterPhones

                @property
                def debt(self):                    
                    return sum(d for d in self.monthsInDebt.values())
                
                @property
                def previosDebtValue(self):
                    cell = getattr(self, 'חוב נצבר', None)
                    if not cell:
                        return 0
                    
                    previousDebt = TidyField(ExtractValue(cell))                   
                    
                    if len(previousDebt):
                        try:
                            return int(previousDebt.strip())
                        except:
                            return 0
                        
                    return 0                                
                         
                def getCellBackGround(self, key):
                    cell = getattr(self, key)
                    return ExtractBackground(cell, self.sheet)
                
                
                def monthlyPayment(self, month):
                    cell = getattr(self, str(month))
                    return TidyField(ExtractValue(cell))


class OccasionalMessageReporters(ReportersBase):  
        
    InfoFields = []
    
    def __init__(self, requestParameters, serverInClient):
        super(OccasionalMessageReporters, self).__init__(requestParameters, serverInClient, utils.config.excelPaymentFilePrefix)
        
    def build(self, helper=None, helperFields=None, historydata=None):
    
        includes, ignores = self.includes, self.ignores
        
        for dirpath, dirnames, filenames in os.walk(utils.config.rootBuildingsDir):            
            head, tail = os.path.split(dirpath)
           
            def showError():
                return utils.SSE_MSG(
                            message = errMessage,
                            label = 'בעיה בסריקת הקובץ :%s ' % 
                            excelFile.excel.encode('utf-8') + 
                            ('   <button class="ignore" type="button" id="%s">התעלם מבניין זה</button> ' % building.encode('utf-8')) if building else '',
                            progress = 0,
                            msgType = 'error'
                        )
            
            def handleError():
                if self.serverInClient:
                    os.startfile(excelFile.excel)
                else:
                    utils.Md('errors')                                        
                    shutil.copy2(excelFile.excel, 'errors')
    
            #if includes is empty, split by ',' will generate an array of one empty string
            def noIncludes():
                return len(includes)==1 and not len(includes[0])
            
            #if no includes defined, then treat the dir as included
            def inIncludes():
                return  noIncludes() or building in includes
            
            def notInIgnores():
                return building not in ignores                       
                                    
            #can not retreive background color of cells at xlsx files cause xlrd doesn't support that (only for xls)            
            for filename in fnmatch.filter(filenames, '*%s*.xls' % self.excelPrefix ):                    
                excel = os.path.join(dirpath, filename)
                
                excelFile = self.ExcelFile(excel, self.requestParameters)
                
                if self.broken:
                    break
                
                #no interesting sheet found in the file, continue to next file
                if not excelFile.sheet:
                    continue                                                    
                
                building = None    
                excelFile.sheet.parseBuildingMetaData()
                excelFile.sheet.parseGeneralData()
                
                #when parsing failed we do not know which building this excel represents,
                #when there is no includes we'll show this error
                if not excelFile.sheet.buildingDescription :
                    if noIncludes():
                        
                        errMessage =  bottle.template('web/templates/errors/error_building_format', 
                               date = datetime.date.today().strftime("%d/%m/%Y"),
                               file_name = excelFile.sheet.excel,
                               company_name = utils.config.companyName,
                               sheet = excelFile.sheet.workSheet.name,
                               A1_value = getattr(excelFile.sheet, 'A1value', ""),
                               company_web_site = utils.config.companyWebSite,
                               company_logo = utils.config.companyLogo)
                        yield showError()
                        yield handleError()                                                                
                        self.broken = True
                        break
                    else:
                        continue
                    
                #got here, we know which building this file represents                
                building = excelFile.sheet.buildingDescription                    
                general = excelFile.sheet.generalData
                
                if notInIgnores() and inIncludes():                                               
                    
                    yield utils.SSE_MSG(
                            message = utils.Html(['בונה נתוני דיירים של בניין: %s, מקובץ : %s' % 
                                                  ('<b>%s</b>' % building.encode('utf-8'), 
                                                   '<b>%s</b>' % utils.Normpath(excelFile.excel).encode('utf-8')) ], True),
                            label = 'קולט נתונים...')
                    
                    errMessage = excelFile.sheet.validateHeader(excelFile.sheet.MandatoryFields)
                
                    if errMessage:
                        yield showError()
                        yield handleError()                                                                
                        self.broken = True
                        break
                    
                    
                    tenantsHistory = defaultdict(# (appartment, name)
                                lambda: defaultdict(  # (date, time, formatTemplate)
                                    list # (alert, alertFile)
                                    ))
                                        
                    buildingHistory = utils.TidyFileName(building)
                    execType = Alerter.getExecutionDesc(self.requestParameters.mode)                       
                    #organize history per this building, per this executionMode                        
                    for d in sorted(historydata[buildingHistory]):
                        for t in historydata[buildingHistory][d]:
                            for formatTemplate in historydata[buildingHistory][d][t][execType]:
                                for appartment in historydata[buildingHistory][d][t][execType][formatTemplate]:
                                    for name in historydata[buildingHistory][d][t][execType][formatTemplate][appartment]:
                                        for alert in historydata[buildingHistory][d][t][execType][formatTemplate][appartment][name]:
                                            for alertDestination in historydata[buildingHistory][d][t][execType][formatTemplate][appartment][name][alert]:
                                                alertFile = historydata[buildingHistory][d][t][execType][formatTemplate][appartment][name][alert][alertDestination]
                                                tenantsHistory[(TidyField(appartment), TidyField(name))][(d, t, formatTemplate)].append((alert, alertFile))
                                                    
                    for i,record in enumerate(excelFile.sheet.fetchRecords()):
            
                        if self.broken:
                            break
                                    
                        rec = self.ExcelFile.ExcelSheet.ExcelRecord(record, excelFile.sheet)
                        
                        if rec.skip:
                            continue
                                            
                        if rec.eof:
                            break
                                                                                                                
                        if self.broken:
                            break
                                                                                                                                         
                                                        
                        rec.source = utils.Normpath(excel).replace('/', '*')
                        rec.building = building
                        rec.general = general
                        rec.occasional = self.requestParameters.occasional
                        rec.subject = self.requestParameters.subject
                        rec.year = self.requestParameters.year                                                
                        
                        #if rec.owner is empty, that means that the owner lives at the appartment and its details 
                        #are in the renter columns, otherwise there is a renter and an owner
                        
                        #only one record for this app, an owner one, fetch details from the renter column
                        if not len(rec.owner): 
                            ownerRecord = copy.copy(rec)
                            ownerRecord.isRenter = False
                            ownerRecord.isDefacto = True
                            ownerRecord.name = ownerRecord.renter
                            ownerRecord.mails = ownerRecord.renterMails
                            ownerRecord.phones = ownerRecord.renterPhones
                            
                            ownerRecord.historyAlerts = tenantsHistory.get( (utils.TidyFileName(TidyField(ownerRecord.appartment)), 
                                                                             utils.TidyFileName(TidyField(ownerRecord.name))), [])
                            
                            self.groups[excelFile.sheet.buildingDescription][i].append(ownerRecord)
                            
                        else:                                
                            renterRecord = copy.copy(rec)
                            renterRecord.isRenter = True
                            renterRecord.isDefacto = True
                            renterRecord.name = renterRecord.renter
                            renterRecord.mails = renterRecord.renterMails
                            renterRecord.phones = renterRecord.renterPhones
                            
                            renterRecord.historyAlerts = tenantsHistory.get( (utils.TidyFileName(TidyField(renterRecord.appartment)), 
                                                                              utils.TidyFileName(TidyField(renterRecord.name))), [])
                            
                            self.groups[excelFile.sheet.buildingDescription][i].append(renterRecord)
                            
                            ownerRecord = copy.copy(rec)
                            ownerRecord.isRenter = False
                            ownerRecord.isDefacto = False
                            ownerRecord.name = ownerRecord.owner
                            ownerRecord.mails = ownerRecord.ownerMails
                            ownerRecord.phones = ownerRecord.ownerPhones
                            
                            ownerRecord.historyAlerts = tenantsHistory.get( (utils.TidyFileName(TidyField(ownerRecord.appartment)), 
                                                                             utils.TidyFileName(TidyField(ownerRecord.name))), [])
                            
                            self.groups[excelFile.sheet.buildingDescription][i].append(ownerRecord)
                            
                        
    def prepareExecutiveReport(self, requestParameters):
        
        tenants = [t for building, recordsOf in sorted(self.groups.items())
                   for appartment, appTenantsOwners in sorted(recordsOf.items()) for t in appTenantsOwners]
        buildingsNum = len(set(t.building for t in tenants))        
        columns_toolTips = zip(['כללי', 'שם', 'תשלום חודשי','נושא מייל', 'הודעה'], ['general', 'name', 'payment', 'subject', 'occasional'])
        values_classes = [('general', 'general'), ('name', 'name'), ('payment', 'payment'), ('subject', 'subject'), ('occasional', 'occasional')]
        
        return Alerter.report(requestParameters, tenants, buildingsNum, columns_toolTips, values_classes)
        
    
    class ExcelFile(object):      
        
        def __init__(self, excel, requestParameters):
            self.excel = excel
            self.requestParameters = requestParameters
            self.workbook = xlrd.open_workbook(excel, formatting_info=True)
            sh = self._getSheet(requestParameters.year)
            #sometimes there is no sheet and this is fine (for example, user selected a year which not in the excel file)
            self.sheet = self.ExcelSheet(excel, sh) if sh else None
        
        def _getSheet(self, requestedYear):
            worksheet = None
            #find specific sheet
            worksheets = self.workbook.sheet_names()                                                
            
            for worksheet_name in worksheets:
                if str(requestedYear) in worksheet_name and worksheet_name.startswith(utils.config.excelPaymentSheetPrefix):
                    return self.workbook.sheet_by_name(worksheet_name)
           
                        
        class ExcelSheet(ExcelSheetBase):
            MandatoryFields = [u"דירה", 
                               u"תשלום חודשי",
                               u"חוב נצבר",
                               u'טלפון בעלים', 
                               u'מייל בעלים', 
                               u'טלפון דיירים', 
                               u'מייל דיירים', 
                               u'שם בעלים', 
                               u'שם דיירים']
            
            def __init__(self, excel, workSheet):
                super(OccasionalMessageReporters.ExcelFile.ExcelSheet, self).__init__(excel, workSheet)
                        
            class ExcelRecord(object):
                def __init__(self, record, sheet):                    
                    self.sheet = sheet
                    
                    for k, cell in record.items():       
                        setattr(self, k, cell)                                            
                
                @property
                def skip(self):                    
                    return self.appartment == '*'
                    
                @property
                def eof(self):                    
                    return self.appartment == ''
                
                @property
                def appartment(self):
                    cell = getattr(self, 'דירה')
                    app = TidyField(ExtractValue(cell))
                                                            
                    try:                       
                        return int(app)
                    except ValueError:
                        return app
                
                @property
                def owner(self):
                    cell = getattr(self, 'שם בעלים')
                    return TidyField(ExtractValue(cell))
                
                @property
                def renter(self):
                    cell = getattr(self, 'שם דיירים')
                    return TidyField(ExtractValue(cell))
                
                @property
                def payment(self):
                    cell = getattr(self, 'תשלום חודשי')
                    payment = TidyField(ExtractValue(cell))
                                        
                    try:
                        return int(payment)
                    except ValueError:                
                        return payment
        
                @property
                def ownerMails(self):                    
                    cell = getattr(self, 'מייל בעלים')                    
                    ownerMails = TidyField(ExtractValue(cell)).split()                                        
                    return ownerMails
                
                @property
                def renterMails(self):               
                    cell = getattr(self, 'מייל דיירים')
                    renterMails = TidyField(ExtractValue(cell)).split()
                    return renterMails
                
                @property
                def ownerPhones(self):                    
                    cell = getattr(self, 'טלפון בעלים')
                    ownerPhones = TidyField(ExtractValue(cell)).split()                                        
                    return ownerPhones
                
                @property
                def renterPhones(self):               
                    cell = getattr(self, 'טלפון דיירים')
                    renterPhones = TidyField(ExtractValue(cell)).split()
                    return renterPhones

                @property
                def debt(self):                    
                    return sum(d for d in self.monthsInDebt.values())
                
                @property
                def previosDebtValue(self):
                    cell = getattr(self, 'חוב נצבר', None)
                    if not cell:
                        return 0
                    
                    previousDebt = TidyField(ExtractValue(cell))                   
                    
                    if len(previousDebt):
                        try:
                            return int(previousDebt.strip())
                        except:
                            return 0
                        
                    return 0                                
                         
                def getCellBackGround(self, key):
                    cell = getattr(self, key)
                    return ExtractBackground(cell, self.sheet)
    
    
    def monthlyPayment(self, month):
        cell = getattr(self, str(month))
        return TidyField(ExtractValue(cell))
