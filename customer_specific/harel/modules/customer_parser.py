# -*- coding: utf8 -*-  

#--------------------------------HAREL REPORTES------------------------------------------------
import os
import fnmatch
import datetime

import dates
import xlrd
import excel_helper
import excel_utils

import utils
import elements

indexAppartnment = -1

class ExcelRecord(object):
    def __init__(self, record):                    
        self.uncalculated = False
        
        for k, cell in record.items():                        
            setattr(self, k, cell)
        
        #build monthly payment - relevant when monthly payment changes within the year
        self.monthlyColumns = sorted([int(k.split('_')[1]) for k in self.__dict__ if 'תשלום חודשי_' in k])
        
    
    @property
    def skip(self):                    
        return self.appartment == '*'
        
    @property
    def eof(self):  
        global indexAppartnment
        appStart = ( (indexAppartnment+1)%4 == 0)
        return self.appartment == '' and appStart
        
        
    def monthlyData(self, year, excelCellInfoPerDate = None):
                           
        
        #find columns in this sheet which represent months
        allMonths = sorted([k for k in self.__dict__ if dates.datify(k, year)], key= (lambda dateColumn: dates.datify(dateColumn)))                
        
        #build monthly expected payments table
        monthlyExpectedPaymentOf = {}                
        
        #if there are different expected payment throughtout this sheet, then monthlyColumns gets updated
        #ar the c'tor of the excel record
        if len(self.monthlyColumns):
            currExpectedPayment = self.payment
            for m in allMonths:
                if m in self.monthlyColumns:
                    currExpectedPayment = int(getattr(self, 'תשלום חודשי_%d' % m))
                monthlyExpectedPaymentOf[m] = currExpectedPayment            
        else:
            for m in allMonths:
                monthlyExpectedPaymentOf[m] = utils.Intify(self.payment)
       
        #calculate how much was paid during the whole period
        total_paid = sum( utils.Intify(self.monthlyPayment(month))
                     for month in allMonths 
                     if self.monthlyPayment(month) is not None)
                

        for month in allMonths:                        
            
            cell_info = excelCellInfoPerDate[dates.datify(month, year)]
            
            expected_payment = monthlyExpectedPaymentOf[month]
            
            if not total_paid:
                actual_payment = 0
                
            else:
                if total_paid >= expected_payment:
                    actual_payment = expected_payment
                    
                else:
                    actual_payment = total_paid
            
                total_paid -= actual_payment             
                     
            cell_info.payment_details.actual_payment = actual_payment
            cell_info.payment_details.expected_payment = expected_payment            
            
                    
    def monthlyPayment(self, month):
        return excel_utils.ExtractCellValueByColumn(self, str(month))
    
           
    @property
    def payment(self):
        #if payment does not exist, treat as 0 as it is defined integer in the data base
        return utils.Intify(excel_utils.ExtractCellValueByColumn(self, 'סכום לחודש'))

    @property
    def appartment(self):
        app = excel_utils.ExtractCellValueByColumn(self, 'דירה')
        try:
            return int(app)
        except:        
            return app.strip()
    
    @property
    def owner(self):
        return excel_utils.ExtractCellValueByColumn(self, 'שם בעלים')
    
    @property
    def renter(self):
        return excel_utils.ExtractCellValueByColumn(self, 'שם שוכרים')                
    
    @property
    def ownerMails(self):
        mails = excel_utils.ExtractCellValueByColumn(self, 'מייל בעלים')
        try:
            return mails.split()
        #probably an integer, therfore could not be splitted, so str it 
        except:            
            return str(mails)
                    
    
    @property
    def renterMails(self):  
        mails = excel_utils.ExtractCellValueByColumn(self, 'מייל שוכרים')
        try:
            return mails.split()
        #probably an integer, therfore could not be splitted, so str it 
        except:            
            return str(mails)        
        
    
    @property
    def ownerPhones(self):  
        phones = excel_utils.ExtractCellValueByColumn(self, 'טלפון בעלים')
        try:
            return phones.split()
        #probably a phone which was written without a leading zero therefore is treated as a number in the excel
        except:            
            return ['0'+str(phones)]
    
    @property
    def renterPhones(self): 
        phones = excel_utils.ExtractCellValueByColumn(self, 'טלפון שוכרים')
        try:
            return phones.split()
        #probably a phone which was written without a leading zero therefore is treated as a number in the excel
        except:            
            return ['0'+str(phones)]
        
    @property
    def isRepresentative(self):        
        return False                                

def SupportedExcelExtentions():
    return ['.xls', '.xlsx']

def GetGeneralSheet(excel_book):
    sheetsOf = {}    
    sheets = excel_book.sheet_names()
    #scan and find interesting sheets
    for sheet_name in sheets:                
        if utils.config.excelGeneralSheetPrefix in sheet_name:
            sheet = excel_book.sheet_by_name(sheet_name)
            try:
                #if after removing prefix, there are a few digits left besides numbers, then don't take 
                #this sheet into account
                year = int(sheet_name.replace(utils.config.excelGeneralSheetPrefix, '').strip())
            except:
                continue
            
            
            
            #don't take future years into account
            if year <= datetime.date.today().year:
                sheetsOf[year] = sheet
            
    #build tenants personal details, based on the newest year
    return sheetsOf[max(sheetsOf)] if len(sheetsOf) else None
    
    
def GetPaymentSheets(excel_book):
    sheetsOf = {}
    sheets = excel_book.sheet_names()
    #scan and find interesting sheets
    for sheet_name in sheets:
        
        if utils.config.excelPaymentSheetPrefix in sheet_name:
            sheet = excel_book.sheet_by_name(sheet_name)
            
            try:
                #if after removing prefix, there are a few digits left besides numbers, then don't take 
                #this sheet into account
                year = int(sheet_name.replace(utils.config.excelPaymentSheetPrefix, '').strip())
            except:
                continue                        
            
            #don't take future years into account
            if year <= datetime.date.today().year:
                sheetsOf[year] = sheet
                
    return sheetsOf if len(sheetsOf) else None
    
    
def GetRenter(excelRecord):
    if type(excelRecord.renter) == int or len(excelRecord.renter):
        return elements.Person(excelRecord.renter, excelRecord.renterMails, excelRecord.renterPhones)

def GetOwner(excelRecord):
    if type(excelRecord.owner) == int or len(excelRecord.owner):
        return elements.Person(excelRecord.owner, excelRecord.ownerMails, excelRecord.ownerPhones)
    
    
def ParseTenantsGeneralData(excel, buildingOf, dbBuildingName):    
    print excel
    book = excel_helper.OpenExcelFile(excel)
    if not book:
        return    
    building_name = os.path.splitext(os.path.basename(excel).replace(utils.config.excelGeneralFilePrefix, '').strip())[0].strip()
    print building_name
    building = buildingOf[building_name]
    building.based_on_files.add(excel)
    building.building_name = building_name
    
    sheet = GetGeneralSheet(book)
    
    if not sheet:
        return                    
    
    global indexAppartnment
    indexAppartnment = -1
    renter_mails = []
    owner_mails = []
    renter_phones = []
    owner_phones = []
    renter_name = ""
    owner_name = ""
    payment = 0
    apartment_number = ""
    
    #go over all excel rows, each represents an apartment
    for i, excelRecord in enumerate(excel_helper.ExtractApartments(sheet, 2)):
        indexAppartnment += 1
        
        appStart = ( indexAppartnment%4 == 0)
        
        if appStart and indexAppartnment:
            #time to insert
            apt_num = utils.Intify(apartment_number) if utils.Intify(apartment_number) else apartment_number
            app = building.apartmentOf[apt_num]
            app.apartment_number = apt_num
            
            app.recent_payment = payment
            if type(renter_name) == int or len(renter_name):
                app.renter = elements.Person(renter_name, renter_mails, renter_phones )
            else:
                app.renter = None
                
            if type(owner_name) == int or len(owner_name):
                app.owner = elements.Person(owner_name, owner_mails, owner_phones )
            else:
                app.owner = None
                
            if app.renter:
                app.renter.defacto = True
            else:
                app.owner.defacto = True            
                        
            
            #initialize
            renter_mails = []
            owner_mails = []
            renter_phones = []
            owner_phones = []
            renter_name = ""
            owner_name = ""
            payment = 0
            apartment_number = ""
                
        if indexAppartnment % 4 == 0:            
            apartment_number = excelRecord.appartment            
            renter_name = excelRecord.renter
            owner_name = excelRecord.owner
            payment = excelRecord.payment
            
        if len(excelRecord.renterMails):
            renter_mails.append(','.join(excelRecord.renterMails))
        if len(excelRecord.ownerMails):
            owner_mails.append(','.join(excelRecord.ownerMails))
        if len(excelRecord.renterPhones):
            renter_phones.append(','.join(excelRecord.renterPhones))
        if len(excelRecord.ownerPhones):        
            owner_phones.append(','.join(excelRecord.ownerPhones))
    
        #app.apartment_number = apartment_number
        #app.recent_payment = excelRecord.payment
        #app.renter = GetRenter(excelRecord)
        #app.owner = GetOwner(excelRecord)
        
        #could be that no renter or owner details exist
        #if app.renter or app.owner:
            #if app.renter:
                #app.renter.defacto = True
            #else:
                #app.owner.defacto = True
        
        ##if no details for renter and owner store an empty person as owner
        #else:
            #app.owner = elements.Person()
            #app.owner.defacto = True
     
    #insert last appartment       
    if (indexAppartnment + 1) % 4 == 0:
        #time to insert
        apt_num = utils.Intify(apartment_number) if utils.Intify(apartment_number) else apartment_number
        app = building.apartmentOf[apt_num]
        app.apartment_number = apt_num
        
        app.recent_payment = payment
        if type(renter_name) == int or len(renter_name):
            app.renter = elements.Person(renter_name, renter_mails, renter_phones )
        else:
            app.renter = None
            
        if type(owner_name) == int or len(owner_name):
            app.owner = elements.Person(owner_name, owner_mails, owner_phones )
        else:
            app.owner = None
            
        if app.renter:
            app.renter.defacto = True
        else:
            app.owner.defacto = True     

def ParseTenantsPaymentData(excel, buildingOf, dbBuildingName):
        
    book = excel_helper.OpenExcelFile(excel)
    if not book:
        return
    building_name = os.path.splitext(os.path.basename(excel).replace(utils.config.excelPaymentFilePrefix, '').strip())[0].strip()
    
    building = buildingOf[building_name]
    building.based_on_files.add(excel)
    building.building_name = building_name    

    #dict year->sheet
    sheetsOf = GetPaymentSheets(book)
    
    if not sheetsOf:
        return                    
    
    for (year, sheet) in sheetsOf.items():   
        global indexAppartnment
        indexAppartnment = -1
        apartment_number = ""
        
        #go over all excel rows, each represents an apartment
        for excelRecord in excel_helper.ExtractApartments(sheet, 2):
            
            indexAppartnment += 1
                    
            appStart = ( indexAppartnment%4 == 0)
            
            if appStart and indexAppartnment:
                #time to insert  
                apt_num = utils.Intify(apartment_number) if utils.Intify(apartment_number) else apartment_number
                app = building.apartmentOf[apt_num]
                app.apartment_number = apt_num                
                recordToKeep.monthlyData(year, app.excelCellInfoPerDate)                                                
            if appStart:
                apartment_number = excelRecord.appartment
                recordToKeep = excelRecord
                
        #insert last appartment       
    if (indexAppartnment + 1) % 4 == 0:
            #time to insert  
            apt_num = utils.Intify(apartment_number) if utils.Intify(apartment_number) else apartment_number
            app = building.apartmentOf[apt_num]
            app.apartment_number = apt_num                
            recordToKeep.monthlyData(year, app.excelCellInfoPerDate)        
            
                    

def ParseTenantSpecialsData(excel, buildingOf, dbBuildingName):
    return
