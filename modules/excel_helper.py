import fnmatch
import datetime
import os
import xlrd
import collections

import excel_utils
import utils
import customer_parser
import elements


def BuildFromScratch(fromDir=None, files=[], dbBuildingName=None):
    
    if fromDir:
        files = [os.path.join(dirpath, f) for dirpath, dirnames, filenames in os.walk(fromDir) for f in filenames ]
        
    #building_name -> building obj
    buildingOf = collections.defaultdict(lambda: elements.Building())        
    
    for filePath in files: 
        baseName = os.path.basename(filePath)
        ext = os.path.splitext(baseName)[-1]
             
        if ext in customer_parser.SupportedExcelExtentions():            
             
            if utils.config.excelGeneralFilePrefix in baseName:                
                customer_parser.ParseTenantsGeneralData(filePath, buildingOf, dbBuildingName)
            if utils.config.excelPaymentFilePrefix in baseName:
                customer_parser.ParseTenantsPaymentData(filePath, buildingOf, dbBuildingName)
            if utils.config.excelSpecialFilePrefix in baseName:
                customer_parser.ParseTenantSpecialsData(filePath, buildingOf, dbBuildingName) 
                                            
    
    return buildingOf


def ExtractHeaderFromSheet(sheet, header_row):
    headers = [sheet.cell_value(header_row, col).strip() if sheet.cell_type(header_row, col) == 1 
                                            else sheet.cell_value(header_row, col) for col in range(sheet.ncols)]
    return headers

def ExtractApartments(sheet, start, jump=1, header_row=1):
    for row in range(start, sheet.nrows, jump):
        values = [sheet.cell_value(row, col).strip() if sheet.cell_type(row, col) == 1 else sheet.cell_value(row, col) for col in range(sheet.ncols)]
        
        cells = [sheet.cell(row, col)                           
                 for col in range(sheet.ncols)]        
        #this is a dict which represents an excel record - meaning a row. the key is the column name, and the 
        #value is the excel cell object
        excelRecord = customer_parser.ExcelRecord(dict(zip( (excel_utils.TidyCellValue(h) for h in ExtractHeaderFromSheet(sheet, header_row)), 
                        cells ) ))
        
        if excelRecord.eof:
            break        

        if excelRecord.skip:
            continue                                    
        
        yield excelRecord
        
#def TidyField(field):                
    #if isinstance(field, unicode):
        #return field.encode('utf-8')
    #if isinstance(field, float):
        #return str(int(field))
    #return str(field)

def OpenExcelFile(excel):
    try:
        return xlrd.open_workbook(excel)
    except:
        pass