# -*- coding: utf8 -*-  

#--------------------------------Idan Shani REPORTES------------------------------------------------
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
        
        
    def specialYearlyData(self, year, excelCellInfoPerDate, debt_description): 
        
        #regular dates are logged under the first of each month, so log special debts inder the 2nd (this is a hack
        #instead of making excelCellInfoPerDate a dict which is:   desciption->date-> ExcelCellInfo)
        special_date = datetime.datetime.strptime('02/01/%s' % year, '%d/%m/%Y').date()        
        special_date = utils.FindFirstNonUsedDate(excelCellInfoPerDate, special_date)
        
        cell_info = excelCellInfoPerDate[special_date]
        
        expected_payment = self.special_payment
        actual_payment = expected_payment - self.special_debt
                 
        cell_info.payment_details.actual_payment = actual_payment
        cell_info.payment_details.expected_payment = self.special_payment
        
        cell_info.payment_details.debt_type = 2
        cell_info.payment_details.debt_description = debt_description
        
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
               

        for month in allMonths:                        
            
            cell_info = excelCellInfoPerDate[dates.datify(month, year)]
            
            expected_payment = monthlyExpectedPaymentOf[month]
            actual_payment = expected_payment if self.paid else utils.Intify(self.monthlyPayment(month))            
                     
            cell_info.payment_details.actual_payment = actual_payment
            cell_info.payment_details.expected_payment = expected_payment
            
                    
    def monthlyPayment(self, month):
        return excel_utils.ExtractCellValueByColumn(self, str(month))
    
           
    @property
    def payment(self):
        #if payment does not exist, treat as 0 as it is defined integer in the data base
        return utils.Intify(excel_utils.ExtractCellValueByColumn(self, 'תשלום חודשי'))
    
    @property
    def special_payment(self):
        #if payment does not exist, treat as 0 as it is defined integer in the data base
        return utils.Intify(excel_utils.ExtractCellValueByColumn(self, 'נדרש לשלם'))
    
    @property
    def special_debt(self):
        #if payment does not exist, treat as 0 as it is defined integer in the data base
        return utils.Intify(excel_utils.ExtractCellValueByColumn(self, 'יתרה לתשלום'))
    
    
    @property
    def appartment(self):
        app = excel_utils.ExtractCellValueByColumn(self, 'דירה')
        try:
            return int(app)
        except:        
            return app.strip()
    
    @property
    def paid(self):
        paid = excel_utils.ExtractCellValueByColumn(self, 'תשלום בהוראת קבע')
        if type(paid) == int or type(paid) == float or len(paid):
            return True
    
    @property
    def owner(self):
        return excel_utils.ExtractCellValueByColumn(self, 'שם בעלים')
    
    @property
    def renter(self):
        return excel_utils.ExtractCellValueByColumn(self, 'שם שוכרים')                
    
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
    def renterMails(self):               
        mails = excel_utils.ExtractCellValueByColumn(self, 'דואר אלקטרוני שוכרים')
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
            return sheet
    
    
def GetPaymentSheets(excel_book, prefix):
    sheetsOf = {}
    sheets = excel_book.sheet_names()
    #scan and find interesting sheets
    for sheet_name in sheets:
        
        if prefix in sheet_name:
            sheet = excel_book.sheet_by_name(sheet_name)
            
            try:
                #if after removing prefix, there are a few digits left besides numbers, then don't take 
                #this sheet into account
                year = int(sheet_name.replace(prefix, '').strip())
            except:
                continue                        
            
            
            sheetsOf[year] = sheet
                
    return sheetsOf if len(sheetsOf) else None
    
    
def GetRenter(excelRecord):
    if type(excelRecord.renter) == int or len(excelRecord.renter):
        return elements.Person(excelRecord.renter, excelRecord.renterMails, excelRecord.renterPhones)

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
        app.renter = GetRenter(excelRecord)
        app.owner = GetOwner(excelRecord)
        
        #could be that no renter or owner details exist
        if app.renter or app.owner:
            if app.renter:
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
    sheetsOf = GetPaymentSheets(book, utils.config.excelPaymentSheetPrefix)
    
    if not sheetsOf:
        return                    
    
    for (year, sheet) in sheetsOf.items():    
        #go over all excel rows, each represents an apartment
        for excelRecord in excel_helper.ExtractApartments(sheet, 2):
            
            apartment_number = excelRecord.appartment
            app = building.apartmentOf[apartment_number]                        
            
            excelRecord.monthlyData(year, app.excelCellInfoPerDate)            
                    

def ParseTenantSpecialsData(excel, buildingOf, dbBuildingName):    
    book = excel_helper.OpenExcelFile(excel)
    building_name, debt_description = "", ""
    
    if not book:
        return
    building_name_debt_description = os.path.splitext(os.path.basename(excel).replace(utils.config.excelSpecialFilePrefix, '').strip())[0].strip()
    
    try:
        building_name, debt_description = building_name_debt_description.rsplit('-', 1)
    except:
        pass
    
    building_name = building_name.strip()
    debt_description = debt_description.strip()        
    
    building = buildingOf[building_name]
    building.based_on_files.add(excel)
    building.building_name = building_name

    #dict year->sheet
    sheetsOf = GetPaymentSheets(book, utils.config.excelSpecialSheetPrefix)
    
    if not sheetsOf:
        return                    
    
    for (year, sheet) in sheetsOf.items():    
        #go over all excel rows, each represents an apartment
        for excelRecord in excel_helper.ExtractApartments(sheet, 2):
            
            apartment_number = excelRecord.appartment
            app = building.apartmentOf[apartment_number]
            
            app.apartment_number = apartment_number            
            
            excelRecord.specialYearlyData(year, app.excelCellInfoPerDate, debt_description)    

