# -*- coding: utf8 -*-  

#--------------------------------BATIM-YAFIM REPORTES------------------------------------------------
import os
import fnmatch
import datetime

import dates
import xlrd
import excel_helper
import excel_utils
import sqlite3

import utils
import elements
        
class ExcelRecord(object):
    def __init__(self, record):                    
        self.uncalculated = False
        
        for k, cell in record.items():                        
            setattr(self, k, cell)
        
        #build monthly payment - relevant when monthly payment changes within the year
        self.monthlyColumns = sorted([int(k.split('_')[1]) for k in self.__dict__ if 'ת.חודשי_' in k])
        
    
    @property
    def skip(self):                    
        return self.appartment == '*'
        
    @property
    def eof(self):                    
        return self.appartment == ''    
        
        
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
                if int(m) in self.monthlyColumns:
                    currExpectedPayment = utils.Intify(excel_utils.ExtractCellValueByColumn(self, 'ת.חודשי_%d' % int(m)))                    
                monthlyExpectedPaymentOf[m] = currExpectedPayment            
        else:
            for m in allMonths:
                monthlyExpectedPaymentOf[m] = utils.Intify(self.payment)
               

        for month in allMonths:                        
            
            cell_info = excelCellInfoPerDate[dates.datify(month, year)]
            
            expected_payment = monthlyExpectedPaymentOf[month]
            actual_payment = utils.Intify(self.monthlyPayment(month))            
                     
            cell_info.payment_details.actual_payment = actual_payment
            cell_info.payment_details.expected_payment = expected_payment            
            
                    
    def monthlyPayment(self, month):
        return excel_utils.ExtractCellValueByColumn(self, str(month))
    
           
    @property
    def payment(self):
        #if payment does not exist, treat as 0 as it is defined integer in the data base
        return utils.Intify(excel_utils.ExtractCellValueByColumn(self, 'ת.חודשי'))        

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
    def tenant(self):
        return excel_utils.ExtractCellValueByColumn(self, 'שם דיירים') 
    
    @property
    def ownerMails(self):
        mails = excel_utils.ExtractCellValueByColumn(self, 'דואר אלקטרוני בעלים')
        try:
            return mails.split()
        #probably an integer, therfore could not be splitted, so str it 
        except:            
            return str(mails)
            
        return excel_utils.ExtractCellValueByColumn(self, 'דואר אלקטרוני בעלים').split()
    
    @property
    def tenantMails(self):  
        mails = excel_utils.ExtractCellValueByColumn(self, 'דואר אלקטרוני דיירים')
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
    def tenantPhones(self): 
        phones = excel_utils.ExtractCellValueByColumn(self, 'טלפון דיירים')
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
                    
            sheetsOf[year] = sheet
                
    return sheetsOf if len(sheetsOf) else None
    
    
def GetTenant(excelRecord):
    if type(excelRecord.tenant) == int or len(excelRecord.tenant):
        return elements.Person(excelRecord.tenant, excelRecord.tenantMails, excelRecord.tenantPhones)

def GetOwner(excelRecord):
    if type(excelRecord.owner) == int or len(excelRecord.owner):
        return elements.Person(excelRecord.owner, excelRecord.ownerMails, excelRecord.ownerPhones)
    
    
def ParseTenantsGeneralData(excel, buildingOf, dbBuildingName):        
    book = excel_helper.OpenExcelFile(excel)
    if not book:
        return    
    building_name = os.path.splitext(os.path.basename(excel).replace(utils.config.excelGeneralFilePrefix, '').strip())[0].strip()
    
    building = buildingOf[building_name]
    building.based_on_files.add(excel)
    building.building_name = building_name
    
    sheet = GetGeneralSheet(book)
    
    if not sheet:
        return                    
    
    #go over all excel rows, each represents an apartment
    for excelRecord in excel_helper.ExtractApartments(sheet, 2):
        
        apartment_number = excelRecord.appartment
        
        app = building.apartmentOf[apartment_number]
        
        app.apartment_number = apartment_number
        app.recent_payment = excelRecord.payment
        
        tenant = GetTenant(excelRecord)
        owner = GetOwner(excelRecord)
        
        if tenant or owner:
            #no owner, only tenant, so tenant is owner
            if not owner:
                app.owner = tenant
                app.owner.defacto = True
            else:
                #there is an owner
                app.owner = owner
                #if there is a tenant than he is the renter otherwise there is only an owner
                if tenant:
                    app.renter = tenant
                    app.renter.defacto = True
                else:
                    app.owner.defacto = True
                
        #if no details for renter and owner store an empty person as owner
        else:
            app.owner = elements.Person()
            app.owner.defacto = True

        info_db = sqlite3.connect(utils.DB_INFO)      
        cursor=info_db.cursor()    
        cursor.execute('''SELECT excel_header, field_type, template_name from fields''')
        for excel_header, field_type, template_name in cursor.fetchall():
            app.dynamicData[template_name] = excel_utils.ResolveDynamicFieldValue(excelRecord, excel_header, field_type)
        

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
        #go over all excel rows, each represents an apartment
        for excelRecord in excel_helper.ExtractApartments(sheet, 2):
            
            apartment_number = excelRecord.appartment
            app = building.apartmentOf[apartment_number]                        
            
            excelRecord.monthlyData(year, app.excelCellInfoPerDate)            
                    

def ParseTenantSpecialsData(excel, buildingOf, dbBuildingName):
    return
