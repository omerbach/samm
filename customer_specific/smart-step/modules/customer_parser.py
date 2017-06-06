# -*- coding: utf8 -*-  

#--------------------------------SMART-STEP REPORTES------------------------------------------------
import os
import fnmatch
import datetime

import dates
import xlrd
import excel_helper
import excel_utils

import utils
import elements
        
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
        return utils.Intify(excel_utils.ExtractCellValueByColumn(self, 'תשלום חודשי'))
        
    
        #payment = getattr(self, 'תשלום חודשי', '').decode('utf-8')
        
        ##payment can also be empty or text (indicating this is not  debt) hence it is not always an integer
        #try:
            #return int(payment)
        #except ValueError:                
            #return payment

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
        #return getattr(self, 'שם בעלים', '').decode('utf-8')
    
    @property
    def tenant(self):
        return excel_utils.ExtractCellValueByColumn(self, 'שם דיירים')        
        #return getattr(self, 'שם דיירים', '').decode('utf-8')
    
    @property
    def ownerMails(self):
        return excel_utils.ExtractCellValueByColumn(self, 'מייל בעלים').split()
        #return getattr(self, 'מייל בעלים', '').decode('utf-8').split()
    
    @property
    def tenantMails(self):
        return excel_utils.ExtractCellValueByColumn(self, 'מייל דיירים').split()
        #return getattr(self, 'מייל דיירים', '').decode('utf-8').split()
    
    @property
    def ownerPhones(self): 
        return excel_utils.ExtractCellValueByColumn(self, 'טלפון בעלים').split()
        #return getattr(self, 'טלפון בעלים', '').decode('utf-8').split()
    
    @property
    def tenantPhones(self): 
        return excel_utils.ExtractCellValueByColumn(self, 'טלפון דיירים').split()
        #return getattr(self, 'טלפון דיירים', '').decode('utf-8').split()
        
    @property
    def isRepresentative(self):        
        return False                                

def SupportedExcelExtentions():
    #smart step only uses xls suffix as this is the only supported type by xlrd that can 
    #read the cell colors
    return ['.xls']

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
    
    
def GetTenant(excelRecord):
    if len(excelRecord.tenant):
        return elements.Person(excelRecord.tenant, excelRecord.tenantMails, excelRecord.tenantPhones)

def GetOwner(excelRecord):
    if len(excelRecord.owner):
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
