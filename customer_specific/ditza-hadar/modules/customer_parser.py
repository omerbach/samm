# -*- coding: utf8 -*-  

# --------------------------------DITZA HADAR REPORTES------------------------------------------------
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

    @property
    def skip(self):
        return False
        # filter out appartments which are not between 50000 to to 5999
        return self.appartment == '*' or (self.appartment < 0 or self.appartment > 999)

    @property
    def eof(self):
        return self.appartment == ''

    def specialYearlyData(self, year, excelCellInfoPerDate, debt_description):

        # regular dates are logged under the first of each month, so log special debts inder the 2nd (this is a hack
        # instead of making excelCellInfoPerDate a dict which is:   desciption->date-> ExcelCellInfo)
        special_date = datetime.datetime.strptime('02/01/%s' % year, '%d/%m/%Y').date()
        cell_info = excelCellInfoPerDate[special_date]

        cell_info.payment_details.actual_payment = 0
        cell_info.payment_details.expected_payment = self.special_debt

        cell_info.payment_details.debt_type = 2
        cell_info.payment_details.debt_description = debt_description

    def monthlyData(self, excelCellInfoPerDate=None):

        # log debts per today
        cell_info = excelCellInfoPerDate[datetime.date.today()]
        cell_info.payment_details.actual_payment = 0
        cell_info.payment_details.expected_payment = self.debt

    @property
    def debt(self):
        return utils.Intify(excel_utils.ExtractCellValueByColumn(self, 'יתרה'))

    @property
    def building(self):
        return excel_utils.ExtractCellValueByColumn(self, 'בנין')

    @property
    def building_code(self):
        return utils.Intify(excel_utils.ExtractCellValueByColumn(self, 'קוד בניין'))

    @property
    def special_payment(self):
        # if payment does not exist, treat as 0 as it is defined integer in the data base
        return utils.Intify(excel_utils.ExtractCellValueByColumn(self, 'נדרש לשלם'))

    @property
    def special_debt(self):
        # if payment does not exist, treat as 0 as it is defined integer in the data base
        return utils.Intify(excel_utils.ExtractCellValueByColumn(self, 'יתרה לתשלום'))

    @property
    def appartment(self):
        try:
            app = excel_utils.ExtractCellValueByColumn(self, 'כרטיס')
            return int(str(int(app))[3:]) - 5000
        except ValueError:
            return app

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
        # probably an integer, therfore could not be splitted, so str it
        except:
            return str(mails)

        return excel_utils.ExtractCellValueByColumn(self, 'דואר אלקטרוני בעלים').split()

    @property
    def renterMails(self):
        mails = excel_utils.ExtractCellValueByColumn(self, 'דואר אלקטרוני שוכרים')
        try:
            return mails.split()
        # probably an integer, therfore could not be splitted, so str it
        except:
            return str(mails)

    @property
    def ownerPhones(self):
        phones = excel_utils.ExtractCellValueByColumn(self, 'טלפון בעלים')
        try:
            return phones.split()
        # probably a phone which was written without a leading zero therefore is treated as a number in the excel
        except:
            return ['0' + str(phones)]

    @property
    def renterPhones(self):
        phones = excel_utils.ExtractCellValueByColumn(self, 'טלפון שוכרים')
        try:
            return phones.split()
        # probably a phone which was written without a leading zero therefore is treated as a number in the excel
        except:
            return ['0' + str(phones)]

    @property
    def isRepresentative(self):
        return False


def SupportedExcelExtentions():
    return ['.xls', '.xlsx']


def GetGeneralSheet(excel_book):
    worksheets = excel_book.sheet_names()
    for worksheet_name in worksheets:
        if worksheet_name.startswith(utils.config.excelGeneralSheetPrefix):
            return excel_book.sheet_by_name(worksheet_name)


def GetPaymentSheet(excel_book):
    worksheets = excel_book.sheet_names()
    for worksheet_name in worksheets:
        if worksheet_name.startswith(utils.config.excelPaymentSheetPrefix):
            return excel_book.sheet_by_name(worksheet_name)


def GetSpecialPaymentSheet(excel_book):
    prefix = utils.config.excelSpecialSheetPrefix
    sheetsOf = {}
    sheets = excel_book.sheet_names()
    # scan and find interesting sheets
    for sheet_name in sheets:

        if prefix in sheet_name:
            sheet = excel_book.sheet_by_name(sheet_name)

            try:
                # if after removing prefix, there are a few digits left besides numbers, then don't take
                # this sheet into account
                year = int(sheet_name.replace(prefix, '').strip())
            except:
                continue

            sheetsOf[year] = sheet

    return sheetsOf if len(sheetsOf) else None


def GetRenter(excelRecord):
    if type(excelRecord.renter) == float or type(excelRecord.renter) == int or len(excelRecord.renter):
        return elements.Person(excelRecord.renter, excelRecord.renterMails, excelRecord.renterPhones)


def GetOwner(excelRecord):
    if type(excelRecord.owner) == float or type(excelRecord.owner) == int or len(excelRecord.owner):
        return elements.Person(excelRecord.owner, excelRecord.ownerMails, excelRecord.ownerPhones)


def GetBuildingCodeDict():
    excel = os.path.join(utils.config.rootBuildingsDir, utils.config.excelGeneralFilePrefix + '.xls')
    assert os.path.exists(excel)
    codesOf = {}

    book = excel_helper.OpenExcelFile(excel)
    if not book:
        return

    sheet = GetGeneralSheet(book)

    if not sheet:
        return

        # go over all excel rows, each represents an apartment
    for excelRecord in excel_helper.ExtractApartments(sheet, 1, 1, 0):
        codesOf[excelRecord.building_code] = excelRecord.building

    return codesOf


def ParseTenantsGeneralData(excel, buildingOf, dbBuildingName):
    book = excel_helper.OpenExcelFile(excel)
    if not book:
        return

    sheet = GetGeneralSheet(book)

    if not sheet:
        return

        # go over all excel rows, each represents an apartment
    for excelRecord in excel_helper.ExtractApartments(sheet, 1, 1, 0):

        building_name = excelRecord.building

        # if there is a specific building to update
        if not dbBuildingName or dbBuildingName == building_name:

            building = buildingOf[building_name]
            building.based_on_files.add(excel)
            building.building_name = building_name

            apartment_number = excelRecord.appartment
            app = building.apartmentOf[apartment_number]

            app.apartment_number = apartment_number

            app.renter = GetRenter(excelRecord)
            app.owner = GetOwner(excelRecord)

            # could be that no renter or owner details exist
            if app.renter or app.owner:
                if app.renter:
                    app.renter.defacto = True
                else:
                    app.owner.defacto = True

            # if no details for renter and owner store an empty person as owner
            else:
                app.owner = elements.Person()
                app.owner.defacto = True


def ParseTenantsPaymentData(excel, buildingOf, dbBuildingName):
    # get a dict of building code -> building name
    codesOf = GetBuildingCodeDict()

    book = excel_helper.OpenExcelFile(excel)
    if not book:
        return

    sheet = GetPaymentSheet(book)

    if not sheet:
        return

        # first building starts here
    start_row = 14

    while True:
        skip_building = False
        # column 10 = K, thats where the building code supposed to be
        building_code_cell = sheet.cell_value(start_row, 10)

        # no more buiuldings, finish everything
        if not len(building_code_cell):
            break
        # extract building code
        building_code = utils.Intify(building_code_cell.split('חובות דיירים'.decode('utf-8'))[-1].strip())

        if building_code:
            try:
                # take building name from the dict extracted from the general tenants sheet
                building_name = codesOf[building_code]
                print building_code, building_name
                # retrieve building object
                building = buildingOf[building_name]
                building.based_on_files.add(excel)
                building.building_name = building_name
            except KeyError:
                skip_building = True

        # if for some reason there is no code, iterate the rows but don't update building tenants
        else:
            skip_building = True

        # tenants data starts 2 rows after the header
        start_row += 2
        for num_tenants, excelRecord in enumerate(excel_helper.ExtractApartments(sheet, start_row + 2, 2, start_row)):
            if skip_building:
                continue

            apartment_number = excelRecord.appartment
            app = building.apartmentOf[apartment_number]
            excelRecord.monthlyData(app.excelCellInfoPerDate)

            # set pointer to the last tenant in the table
        start_row += (num_tenants + 1) * 2
        # set pointer to the next building
        start_row += 5


def ParseTenantSpecialsData(excel, buildingOf, dbBuildingName):
    book = excel_helper.OpenExcelFile(excel)
    building_name, debt_description = "", ""

    if not book:
        return
    building_name_debt_description = \
    os.path.splitext(os.path.basename(excel).replace(utils.config.excelSpecialFilePrefix, '').strip())[0].strip()

    try:
        building_name, debt_description = building_name_debt_description.rsplit('-', 1)
        print building_name, debt_description
    except:
        pass

    building_name = building_name.strip()
    debt_description = debt_description.strip()

    building = buildingOf[building_name]
    building.based_on_files.add(excel)
    building.building_name = building_name

    sheetsOf = GetSpecialPaymentSheet(book)

    if not sheetsOf:
        return

    for (year, sheet) in sheetsOf.items():
        # go over all excel rows, each represents an apartment
        for excelRecord in excel_helper.ExtractApartments(sheet, 2):
            apartment_number = excelRecord.appartment
            app = building.apartmentOf[apartment_number]

            app.apartment_number = apartment_number

            excelRecord.specialYearlyData(year, app.excelCellInfoPerDate, debt_description)    


