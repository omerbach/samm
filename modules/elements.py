import collections

class ExcelCellInfo(object):
    def __init__(self):
        self.payment_details = Payment()
        self.comment = ""
        self.raw = None
        
class Payment(object):
    def __init__(self):
        self.expected_payment = 0
        self.actual_payment = 0        
        
    @property
    def debt(self):        
        return self.expected_payment - self.actual_payment
    
class Apartment(object):
    def __init__(self):
        self.apartment_number = ""        
        self.recent_payment = 0                          
        self.excelCellInfoPerDate = collections.defaultdict(lambda: ExcelCellInfo()) #date-> ExcelCellInfo obj        
        self.renter = None
        self.owner = None
        #field_name -> field_value
        self.dynamicData = {}        
        
class Building(object):
    def __init__(self):
        self.building_name = ""
        self.based_on_files = set()
        #apartment_number -> app obj
        self.apartmentOf = collections.defaultdict(lambda: Apartment())
        
class Person(object):
    def __init__(self, name="", mails=[], phones=[]):
        self.name = name
        self.mails = mails
        self.phones = phones        
    