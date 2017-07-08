# -*- coding: utf8 -*-  

import time
import os
import datetime
import json
#import simplejson
import sys
import traceback
import collections
import shutil
import uuid
import socket
import fnmatch
import xlrd
import math
import sqlite3
from dateutil.relativedelta import relativedelta

import mail
import sms
import alerters
import bottle
import dates
import decimal

import web_utils
import utils
import excel_helper
import db_helper

#comment
FaIconOf = {
    'building': 'fa fa-building',
    'building_owners': 'fa fa-building owner',
    'building_renters': 'fa fa-building renter',
    'building_defacto': 'fa fa-building defecto',
    'tenant': 'fa fa-male',
    'tenant_owner': 'fa fa-male owner',
    'tenant_renter': 'fa fa-male renter',
    'professional': 'fa fa-suitcase',
    'worker': 'fa fa-users'
}

SpecificBuildingHebrewOf = {
    'building_owners': 'בעלים'.decode('utf-8'),
    'building_renters': 'שוכרים'.decode('utf-8'),
    'building_defacto': 'דיירים'.decode('utf-8')
}

TenantTypeOf = {
    1: 'owner',
    2: 'renter'
}

recepientAlertCodeOf = {
    #both building and tenant type are stored as tenant in the db, as there is no 
    #alerts sent from the building but from the tenants
    'building': 0,
    'tenant': 0,
    'professional': 1,
    'worker': 2 }            

class RequestParameters(object):

    def __init__(self, params):

        self.ignores = [ign.decode('utf-8').strip() for ign in params["ignores"].split(',')]
        self.includes = [ign.decode('utf-8').strip() for ign in params["includes"].split(',')]
        self.noMonths = False

        #if no year, take current
        self.year = int(params["year"]) if params.get("year", None) else datetime.date.today().year
        #if no months, take from begining of year till current
        self.months = params.get("months", "").split(',')        
        if len(self.months) == 1 and self.months[0] == '':
            #will use this as an indication in specific reporters' debtMonths function
            self.noMonths = True
            self.months = ['1-%d' % datetime.date.today().month]

        self.reportingMonths = self._getMonths(params)

        self.threshold = int(params["threshold"]) if params.get("threshold", None) else 0

        self.event = params.get("event", "")

        self.occasional = params.get("occasional", "")

        self.subject = params.get("subject", "")

        self.reportOnlyIfAllInARow = True if params.in_a_row == 'on' else False                                

        self.mode = int(params["execution"])

        self.appertments = [app.strip() for app in params["app"].split(',')]                

        #need that to disable check box in executive report
        self.customerTemplatesDir = params.get("printFormat", '').decode('utf-8')

    def _getMonths(self, params):
        #if any month is of form month/year let the specific reporters layer to handle it
        if any('/' in m for m in self.months):
            return self.months

        reportingMonths = []

        for i in self.months:                
            if i.find('-') >= 0:
                startRange, endRange = i.split('-')
                for m in range(int(startRange.strip()), int(endRange.strip()) + 1):
                    reportingMonths.append(m)
            else: 
                reportingMonths.append(int(i.strip()))

        return reportingMonths

def GetCustomerTemplatesDir():
    return utils.config.ongoingDebtsTemplatesDir    

@bottle.post("/support")
def SupportRequest():
    msg = bottle.request.forms.supportMsg

    my_id = hash(str(uuid.uuid1())) % 1000000
    supportRequestId = my_id

    mail.MailGunMail().send(to=['omerbach@gmail.com'],
                            fromMail = utils.config.maiFromDebts,
                            subject = ('בקשת תמיכה : #%s, מלקוח : %s' % (supportRequestId, utils.config.companyName.encode('utf-8'))).decode('utf-8'),
                            message = msg, 
                            html = False,
                            )


    return {'supportRequestId': supportRequestId}


@bottle.get("/fetchTemplates")
def getTemplates():

    #root = 'web\customer_templates' 
    folders = []
    root = GetCustomerTemplatesDir()
    if root:
        for element in os.listdir(root):
            if os.path.isdir(os.path.join(root,element)):                                                
                try:
                    sms_content = file(os.path.join(root, element, 'sms.htm')).read().decode('utf-16') if 'sms.htm' in os.listdir(os.path.join(root, element)) else  ""
                    mail_content = file(os.path.join(root, element, 'mail.htm')).read().decode('utf-16') if 'mail.htm' in os.listdir(os.path.join(root, element)) else  ""
                    letter_content = file(os.path.join(root, element, 'letter.htm')).read().decode('utf-16') if 'letter.htm' in os.listdir(os.path.join(root, element)) else  ""


                    folders.append({'name': element, 
                                    'path': os.path.join(root, element),
                                    'sms': True if 'sms.htm' in os.listdir(os.path.join(root, element)) else False,
                                    'mail': True if 'mail.htm' in os.listdir(os.path.join(root, element)) else False,
                                    'letter': True if 'letter.htm' in os.listdir(os.path.join(root, element)) or 'mail.htm' in os.listdir(os.path.join(root, element)) else False,
                                    'sms_content': sms_content,
                                    'mail_content': mail_content,
                                    'letter_content': letter_content
                                    })

                except:
                    continue

    return {'templates': folders}    


@bottle.get("/download/<folder_name>/<file_name>")
def download(folder_name, file_name):

    file_name =  file_name.decode('utf-8')
    folder_name =  folder_name.decode('utf-8')

    fileName, fileExtension = os.path.splitext(file_name)

    if os.path.exists(os.path.join(folder_name, file_name)):
        if fileExtension in ['.htm', '.html']:
            #http://stackoverflow.com/questions/19978975/how-to-serve-static-file-with-a-hebrew-name-in-python-bottle
            return bottle.static_file(file_name, root=folder_name, download=True)
        else:
            return bottle.static_file(file_name, root=folder_name)


@bottle.get("/suicide")
def KilleMe():
    os.system('kill.bat')


@bottle.get("/authorize")
def Authorize(): 
    authorized, expiry = utils.Authorize()
    if not authorized:
        errMsg = json.dumps({
            'message': bottle.template('web/templates/errors/error_customer_not_approved', 
                                       date = datetime.date.today().strftime("%d/%m/%Y"),                               
                                       company_name = utils.config.companyName,
                                       company_web_site = utils.config.companyWebSite,
                                       company_logo = utils.config.companyLogo )  ,                                 
            'label': 'לקוח לא שילם דמי מנוי',
            'type': 'error'})

    return {'approved': 'yes'} if  authorized else {'approved': 'no', 'data': errMsg}


def GetTenantsDynamicDataInfoFromDb(tenants_ids):
    dynamic_headers = db_helper.GetTableHeaders('dynamic_extra_tenant_data')
    info_db = sqlite3.connect(utils.DB_INFO)      
    cursor=info_db.cursor()        
    tenantsOf = {}
    
    cursor.execute('''
    SELECT %s       
    FROM dynamic_extra_tenant_data
    WHERE tenant_id IN (%s)
    ''' % (','.join(dynamic_headers), ','.join([str(t) for t in tenants_ids])) )    

    for values in cursor.fetchall():
        dynamic_results = dict(zip(dynamic_headers, values))
        tenantsOf[dynamic_results["tenant_id"]] = dynamic_results
            
    return tenantsOf

def GetTenantsGeneralInfoFromDb(lastUpdatedTenant = 0, buildings = ''):
    info_db = sqlite3.connect(utils.DB_INFO)      
    cursor=info_db.cursor()    

    cursor.execute('''
    SELECT t.tenant_id
         , t.tenant_type
         , t.defacto
         , t.focal_point
         , t.name
         , t.building_id
         , b.name
         , t.apartment_number
         , t.phones
         , t.mails         
    FROM tenants as t, buildings as b
    WHERE t.building_id = b.building_id and t.building_id IN (%s)
    ''' % buildings )    

    #index is used for sorting in the original data base order
    tenantsOf = { tId: {
        'index': index,
        'tenant_id': tId,
        'tenant_type': tType,
        'defacto': defacto,
        'focal_point': focal_point,
        'tenant_name': tName,                        
        'building_id': bId,
        'name': bName,
        'apartment_number': tApartmentNumber,
        'tenant_phones': phones,
        'tenant_mails': mails,
        'tenant_selected': int(lastUpdatedTenant) == int(tId)} 
                  for index, (tId, 
                              tType,
                              defacto,
                              focal_point,
                              tName, 
                              bId, 
                              bName,
                              tApartmentNumber,                       
                              phones,
                              mails) in enumerate(cursor)}
    return tenantsOf

def GetTenantsDebtsInfoFromDb(start_date, end_date, buildings = [], debt_type = 1):
    info_db = sqlite3.connect(utils.DB_INFO)        
    cursor=info_db.cursor()

    cursor.execute('''        
            SELECT 
                t.tenant_id,
                d.description,
                MAX(d.expected) as monthly_payment,
                sum(d.amount) as total_amount,
                GROUP_CONCAT(d.debt_date) as months, 
                GROUP_CONCAT(d.amount) as debts
            FROM tenants as t, debts as d
            WHERE 
                t.building_id IN (%s) AND 
                t.building_id = d.building_id AND 
                t.apartment_number = d.apartment_number AND 
                DATE(d.debt_date) BETWEEN ? AND ? AND 
                d.description = ? AND
                d.expected >= 0 AND
                d.amount >= 0

            GROUP BY t.building_id, d.description, t.apartment_number, t.tenant_id
            ''' % buildings, (start_date, end_date, debt_type))        



    records = []  
    building_debt = 0
    tenantsOf = collections.defaultdict(dict)

    for tId, debt_description, monthly_payment, total_debt, months, debts in cursor:

        debtsOf = {dates.date(m): d for m, d in dict(zip(months.split(','), debts.split(','))).items() 
                   if decimal.Decimal(d) > 0}

        monthDebts = ','.join(debtsOf.values())

        tenant_debt_details = {                            
            'tenant_id': tId,
            'debt_description': debt_description,
            'monthly_payment': monthly_payment,
            'total_debt': total_debt,
            'months': utils.GroupRangeConsecutiveMonths(debtsOf.keys()),
            'n_months': len(debtsOf),
            'debts': monthDebts
        }
        tenantsOf[tId] = tenant_debt_details

    return tenantsOf        

def GetBuildingsGeneralInfoFromDb(lastUpdatedBuilding = 0):
    info_db = sqlite3.connect(utils.DB_INFO)    
    cursor=info_db.cursor()

    cursor.execute('''
        SELECT b.building_id, b.name, b.updated, b.based_on_file, b.nick_name
        FROM buildings as b         
        ''')

    buildingsOf = { bId: {'id': bId, 
                          'name': bName, 
                          'last_updated': updated, 
                          'based_on_file': based_on_file,
                          'nick_name': nick_name,
                          'building_selected': int(lastUpdatedBuilding) == int(bId),
                          'source_files_exist': all(os.path.exists(f) for f in based_on_file.split(',')),
                          'fa_icon': FaIconOf['building']
                          } 
                    for bId, bName, updated, based_on_file, nick_name in cursor }

    return buildingsOf

def DoesBuildingPaymentsDataExist(start_date, end_date, building_id, debt_type):
    info_db = sqlite3.connect(utils.DB_INFO)

    cursor=info_db.cursor()    

    cursor.execute('''
        SELECT count(*)        
        FROM debts as d, buildings as b 
        WHERE DATE(d.debt_date) between ? and ?  and d.building_id=b.building_id and b.building_id = ? and d.expected > 0 and d.description = ?
        GROUP BY b.building_id
        ''', (start_date, end_date, building_id, debt_type))    

    return cursor.fetchone()

def GetBuildingsDebtsInfoFromDb(start_date, end_date, debt_type = 1):
    info_db = sqlite3.connect(utils.DB_INFO)

    cursor=info_db.cursor()

    cursor.execute('''
        SELECT 
        b.building_id,         
        sum(d.amount) as total_debt,         
        (sum(d.expected) - sum(d.amount))*1.0/sum(d.expected)*100 as percent
        FROM debts as d, buildings as b 
        WHERE DATE(d.debt_date) between ? and ?  and d.building_id=b.building_id and d.amount >= 0 and d.expected > 0 AND 
                d.description = ?
        GROUP BY b.building_id
        ''', (start_date, end_date, debt_type))    

    buildingsOf = { bId: {'id': bId,                       
                          'total_debt': total_debt,
                          'percent': percent
                          } 
                    for bId, total_debt, percent  in cursor }

    return buildingsOf


#gets buildings info from the database
@bottle.route('/fetchBuildingsGeneral')
def fetchBuildingsGeneral():
    return GetBuildingsGeneralInfoFromDb()

#gets buildings info from the database
@bottle.route('/fetchBuildingsDebts')
def fetchBuildingsDebts():

    lastUpdatedBuilding = bottle.request.query.updated_building if len(bottle.request.query.updated_building) else 0
    start_date = bottle.request.query.start_date
    end_date = bottle.request.query.end_date    
    debt_type = bottle.request.query.debt_type

    buildingsOf = GetBuildingsGeneralInfoFromDb(lastUpdatedBuilding)
    debtsOf = GetBuildingsDebtsInfoFromDb(start_date, end_date, debt_type)

    for bId, building in buildingsOf.items():        
        building_debt = debtsOf.get(bId, None)

        if building_debt:
            #copy all debts' details to this building
            for k,v in building_debt.items():
                building[k] = v
        #no debts - check if there is pyment data for this oeriod
        else:
            #horray - no debts
            if DoesBuildingPaymentsDataExist(start_date, end_date, bId, debt_type):
                building['percent'] = 100
                building['total_debt'] = 0
            else:
                #this will be an indication that there is no payments\data
                building['percent'] = -1    

    return json.dumps(buildingsOf)        

#gets dashboard data info from the database
@bottle.route('/fetchDashBoardData')
def fetchDashBoardData():

    info_db = sqlite3.connect(utils.DB_INFO)

    cursor=info_db.cursor()

    cursor.execute('''SELECT COUNT(*) FROM buildings''')
    buildings_count, = cursor.fetchone()

    cursor.execute('''SELECT COUNT(*) FROM tenants''')
    tenants_count, = cursor.fetchone()

    cursor.execute('''SELECT COUNT(*) FROM professionals''')
    professionals_count, = cursor.fetchone()

    cursor.execute('''SELECT COUNT(*) FROM service where status = 1 OR status = 2''')
    service_count, = cursor.fetchone()

    return json.dumps({
        'buildings_count': buildings_count,
        'tenants_count': tenants_count,
        'professionals_count': professionals_count,
        'service_count': service_count,
        'company_logo': utils.config.companyLogo,
        'company_web_site': utils.config.companyWebSite
    })


#gets dashboard data info from the database
@bottle.route('/fetchSmsCredit')
def fetchSmsCredit():
    smsProvider = eval('sms.%s()' % utils.config.smsProvider)
    credit = smsProvider.credit()
    return {'credit': credit }

#gets dashboard data info from the database
@bottle.route('/fetchServiceData')
def fetchServiceData():
    buildingObjectPerBuildingId = GetBuildingsGeneralInfoFromDb()

    buildingIds = ','.join([str(b) for b in buildingObjectPerBuildingId])       
    tenantObjectPertenantId = GetTenantsGeneralInfoFromDb(buildings = buildingIds)

    tenantsIdsPerBuildingId = collections.defaultdict(list)
    buildingIdPerTenantId = {}

    for tid, tenant in tenantObjectPertenantId.items():
        bid = tenant['building_id']
        tenantsIdsPerBuildingId[bid].append(tid)
        buildingIdPerTenantId[tid] = bid

    return { 'buildingObjectPerBuildingId': buildingObjectPerBuildingId,
             'tenantObjectPerTenantId': tenantObjectPertenantId,
             'tenantsIdsPerBuildingId': tenantsIdsPerBuildingId,
             'buildingIdPerTenantId': buildingIdPerTenantId }

def GetMultiTypeElements(include_specific_buildings = False, tenants_from_building_id = 0):
    
    info_db = sqlite3.connect(utils.DB_INFO)
    cursor=info_db.cursor()  

    entities = []    

    for entity_type in ['building', 'professional', 'worker'] if not tenants_from_building_id else ['professional', 'worker']:        
        cursor.execute('''
            SELECT %s_id, name
            FROM %ss        
            ''' % (entity_type, entity_type ) )

        for entity_id, entity_name in cursor.fetchall():
            if entity_type == 'building' and include_specific_buildings:
                for suffix in ['owners', 'renters', 'defacto']:
                    specific_building_entity = '%s_%s' % (entity_type, suffix)
                    entities.append({
                        'id': entity_id, 
                        'name': '%s | %s' % (entity_name, SpecificBuildingHebrewOf[specific_building_entity]), 
                        'type': specific_building_entity,
                        'icon': FaIconOf[specific_building_entity]
                    })

            entities.append({
                'id': entity_id, 
                'name': entity_name, 
                'type': entity_type, 
                'icon': FaIconOf[entity_type]
            })                


    if tenants_from_building_id:
        #tenants present as tenant_name | building_name
        cursor.execute('''
	    SELECT t.tenant_id, t.name, t.phones, t.mails, b.name, t.tenant_type
	    FROM tenants as t, buildings as b
	    WHERE t.building_id = b.building_id AND b.building_id = ?''', (tenants_from_building_id,))
    else:
        #tenants present as tenant_name | building_name
        cursor.execute('''
            SELECT t.tenant_id, t.name, t.phones, t.mails, b.name, t.tenant_type
            FROM tenants as t, buildings as b
            WHERE t.building_id = b.building_id
            ''')	

    for tenant_id, tenant_name, tenant_phones, tenant_mails, building_name, tenant_type in cursor.fetchall():
        entities.append({
            'id': tenant_id, 
            'name': '%s | %s | %s | %s' % (tenant_name, tenant_phones, tenant_mails, building_name),
            'type': 'tenant', 
            'icon': FaIconOf['tenant_%s' % TenantTypeOf[tenant_type]]
        })

    return entities

#gets dashboard data info from the database
@bottle.route('/fetchMultiTypeElements')
def fetchMultiTypeElements():
    include_specific_buildings = bottle.request.query.include_specific_buildings    
    return json.dumps({'entities': GetMultiTypeElements(len(include_specific_buildings))}) 

#gets professionals info from the database
@bottle.route('/fetchProfessionals')
def fetchProfessionals():

    lastUpdatedProfessional = bottle.request.query.updated_professional if len(bottle.request.query.updated_professional) else 0

    info_db = sqlite3.connect(utils.DB_INFO)

    cursor=info_db.cursor()

    cursor.execute('''
        SELECT p.professional_id, p.name, p.company_person_id, p.category, p.phones, p.mails, p.address, p.fax, p.comment
        FROM professionals as p        
        ''')    


    professionalOf =  { pId: {
        'professional_id': pId, 
        'name': pName, 
        'company_person_id': pCompanyPersonId, 
        'category': pCategory, 
        'phones': pPhones,
        'mails': pMails,
        'address': pAddress,
        'fax': pFax,
        'comment': pComment,
        'modified_now': int(lastUpdatedProfessional) == int(pId)} for 
                        pId, 
                        pName, 
                        pCompanyPersonId,
                        pCategory, 
                        pPhones, 
                        pMails, 
                        pAddress, 
                        pFax,
                        pComment in cursor}        

    return json.dumps({'professionals': professionalOf})

@bottle.route('/download_file_from_server')
def download_file_from_server():
    download_folder = bottle.request.query.folder
    download_file = bottle.request.query.file     
    path = os.path.join(download_folder, download_file)     

    #download_file = download_file.encode('utf-8')
    #return bottle.static_file(filename=download_file, root='downloads', download=True)    
    return bottle.static_file(download_file.encode('utf-8'), root=download_folder, download=True)

@bottle.route('/get_building_files')
def get_building_files():
    copied_building_files = []
    building_id = bottle.request.query.building_id    

    info_db = sqlite3.connect(utils.DB_INFO)    
    cursor=info_db.cursor()	    
    cursor.execute('''SELECT name, based_on_file FROM buildings WHERE building_id = ?''', (building_id, ))

    res = cursor.fetchone()

    if not res:
        return {'building_files': []}

    building_name, building_files = res
    building_files = building_files.split(',')
    building_files = [b for b in building_files if os.path.exists(b)]

    if not len(building_files):
        return {'building_files': []}

    path_to_buildig_files = 'downloads'
    utils.Md(path_to_buildig_files)
    #tmpFolder = utils.CreateTempFolder(dir='downloads')
    #path_to_buildig_files = os.path.join('downloads', tmpFolder, building_name)
    #path_to_buildig_files = os.path.join('downloads', building_name)
    #utils.Md(path_to_buildig_files)

    for b in building_files:	
        shutil.copy2(b, path_to_buildig_files)
        copied_building_files.append(os.path.basename(b))

    #add id : str(datetime.datetime.now())

    return {'root': 'downloads', 'building_files': copied_building_files}
    #path = os.path.join(download_folder, download_file)        
    #return bottle.static_file(download_file, root=download_folder, download=True)


@bottle.route('/getCompanyInfo')
def getCompanyInfo():      
    return json.dumps({
        'comapnyLogo': utils.config.companyLogo,
        'comapnyName': utils.config.companyName,
        'comapnyWebSite': utils.config.companyWebSite
    })

#gets workers info from the database
@bottle.route('/fetchWorkers')
def fetchWorkers():

    start_date = bottle.request.query.start_date
    end_date = bottle.request.query.end_date    
    lastUpdatedWorker = bottle.request.query.updated_worker if len(bottle.request.query.updated_worker) else 0

    info_db = sqlite3.connect(utils.DB_INFO)

    cursor=info_db.cursor()

    cursor.execute('''
        SELECT w.worker_id, w.name, w.person_id, w.title, w.phones, w.mails, w.address, w.fax, w.comment
        FROM workers as w       
        ''')    


    workerOf =  { wId: {
        'worker_id': wId, 
        'name': wName, 
        'person_id': wPersonId, 
        'title': wTitle, 
        'phones': wPhones,
        'mails': wMails,
        'address': wAddress,
        'fax': wFax,
        'comment': wComment,
        'modified_now': int(lastUpdatedWorker) == int(wId)} for 
                  wId, 
                  wName, 
                  wPersonId,
                  wTitle, 
                  wPhones, 
                  wMails, 
                  wAddress, 
                  wFax,
                  wComment in cursor}        

    return json.dumps({'workers': workerOf})

@bottle.post('/deletePreventions')
def deletePreventions():
    f = bottle.request.forms
    prevention_ids = json.loads(f.prevention_ids)
    delete_status = int(f.delete_status)

    info_db = sqlite3.connect(utils.DB_INFO)
    with info_db as connection:
        cursor = connection.cursor()

        cursor.execute('''
        DELETE FROM prevention where prevention_id in (%s)
        ''' % ','.join(str(b) for b in prevention_ids ) )

    # delete service requests from the same prevention id
    if delete_status:
        with info_db as connection:
            cursor = connection.cursor()

            cursor.execute('''
                    DELETE FROM service where prevention_id in (%s)
                    ''' % ','.join(str(b) for b in prevention_ids))


@bottle.route('/fetchDistinctPreventionNames')
def fetchDistinctPreventionNames():

    info_db = sqlite3.connect(utils.DB_INFO)
    with info_db as connection:
        cursor = connection.cursor()
        cursor.execute('select distinct description, category from prevention order by description asc')

        distinct_names = [{'description': d, 'category': c} for d, c in cursor]

    return json.dumps(distinct_names)

#gets service requests info from the database
@bottle.route('/fetchPreventions')
def fetchPreventions():

    building_id = bottle.request.query.building_id
    professional_id = bottle.request.query.professional_id
    prevention_description = bottle.request.query.description

    lastUpdatedPrevention = bottle.request.query.updated_prevention_id if len(bottle.request.query.updated_prevention_id) else 0

    limit = bottle.request.query.limit

    if len(limit):
        limit = int(limit)
    else:
        limit = 0

    info_db = sqlite3.connect(utils.DB_INFO)

    cursor = info_db.cursor()

    # https://stackoverflow.com/questions/25469981/python-sqlite3-build-where-part-with-dynamic-placeholders
    # dirty and ugly hack
    parameters, query_ext = [-1], []

    query = '''         
        SELECT 
        r.prevention_id, 
        r.building_id, 
        r.description, 
        r.category, 
        r.worker_id, 
        r.professional_id, 
        r.months, 
        r.cost, 
        r.comment,
        b.name as building_name,
        w.name as worker_name,
        p.name as professional_name,
        (SELECT count(*) FROM service as q WHERE q.prevention_id = r.prevention_id) AS linked_services
        FROM prevention as r
        LEFT JOIN buildings as b ON r.building_id = b.building_id
        LEFT JOIN workers as w ON r.worker_id = w.worker_id
        LEFT JOIN professionals as p ON r.professional_id = p.professional_id
        WHERE prevention_id > ?
        '''

    if len(building_id):
        query_ext.append('r.building_id = ?')
        parameters += [building_id]

    if len(professional_id):
        query_ext.append('r.professional_id = ?')
        parameters += [professional_id]

    if len(prevention_description):
        query_ext.append('r.description = ?')
        parameters += [prevention_description]

    extra = ' AND '.join(query_ext)
    if len(extra):
        extra = ' AND ' + extra

    extra += " ORDER BY r.description ASC"

    cursor.execute('SELECT COUNT(*) FROM prevention as r WHERE prevention_id > ? %s' % extra, parameters)
    res = cursor.fetchone()
    if res:
        maximum_records, = res
    else:
        maximum_records = 0

    #now for the main query
    if limit:
        extra += " LIMIT %d" % limit

    query += extra

    cursor.execute(query, parameters)

    preventionOf =  { pId: {
        'prevention_id': pId,
        'building_id': pBuildingId,
        'description': pDescription,
        'category': pCategory,
        'worker_id': pWorkerId,
        'professional_id': pProfessionalId,
        'months': months,
        'cost': cost,
        'comment': pComment,
        'prevention_selected': int(lastUpdatedPrevention) == int(pId),
        'january': '1' in months.split(','),
        'february': '2' in months.split(','),
        'march': '3' in months.split(','),
        'april': '4' in months.split(','),
        'may': '5' in months.split(','),
        'june': '6' in months.split(','),
        'july': '7' in months.split(','),
        'august': '8' in months.split(','),
        'september': '9' in months.split(','),
        'october': '10' in months.split(','),
        'november': '11' in months.split(','),
        'december': '12' in months.split(','),
        'building_name': building_name,
        'worker_name': worker_name,
        'professional_name': professional_name,
        'linked_services': linked_services
        } for
                   pId,
                   pBuildingId,
                   pDescription,
                   pCategory,
                   pWorkerId,
                   pProfessionalId,
                   months,
                   cost,
                   pComment,
                   building_name,
                   worker_name,
                   professional_name,
                   linked_services in cursor}

    return {'preventions': preventionOf, 'maximum_records': maximum_records}


@bottle.post('/copyPayment') 
def copyPayment():
    f = bottle.request.forms        
    payment_details = json.loads(f.payment_details)
    return addPaymentToDb(payment_details)

@bottle.post('/deletePayments') 
def deletePayments():
    f = bottle.request.forms    
    payment_ids = json.loads(f.payment_ids)

    info_db = sqlite3.connect(utils.DB_INFO)
    with info_db as connection:
        cursor=connection.cursor()        

        cursor.execute('''
        DELETE FROM payments where payment_id in (%s)
        ''' % ','.join(str(b) for b in payment_ids ) )    

@bottle.post('/addNewPayment') 
def addNewPayment():
    f = bottle.request.forms    
    payment_details = json.loads(f.payment_details)     
    return addPaymentToDb(payment_details)
         
def addPaymentToDb(payment_details):
    
    amount = 0 if payment_details.get("amount", "") == "" else utils.Intify(payment_details["amount"])
    quantity = 1 if payment_details.get("quantity", "") == "" else utils.Intify(payment_details["quantity"])
    payment_ids = []
    
    info_db = sqlite3.connect(utils.DB_INFO)    
    with info_db as connection:
        cursor=connection.cursor() 
        #update existing
        if payment_details.get("edit", False):
            cursor.execute('''
            UPDATE payments            
            SET status = ?, tenant_id = ?, 
            building_id = ?, acceptance_date = ?, amount = ?, payment_type = ?, worker_id = ?,
            receipt = ?, tenant_cheque_identifier = ?, payment_approval = ?, tenant_cheque_date = ?, tenant_bank_account = ?, tenant_bank_branch = ?,
            company_bank_account = ?, company_bank_branch = ?, deposit_date = ?, comment = ?, external_folder = ?
            WHERE payment_id = ?
            ''', (payment_details.get("status", ""), 
                  payment_details.get("tenant_id", ""), 
                  payment_details.get("building_id", ""), 
                  payment_details.get("acceptance_date", ""), 
                  payment_details.get("amount", ""), 
                  payment_details.get("payment_type", ""), 
                  payment_details.get("worker_id", ""), 
                  payment_details.get("receipt", ""), 
                  payment_details.get("tenant_cheque_identifier", ""), 
                  payment_details.get("payment_approval", ""),                   
                  payment_details.get("tenant_cheque_date", ""), 
                  payment_details.get("tenant_bank_account", ""), 
                  payment_details.get("tenant_bank_branch", ""), 
                  payment_details.get("company_bank_account", ""), 
                  payment_details.get("company_bank_branch", ""), 
                  payment_details.get("deposit_date", ""), 
                  payment_details.get("comment", ""), 
                  payment_details.get("external_folder", ""),
                  payment_details.get("payment_id", "")
                  ) )  

            payment_id = payment_details.get("payment_id", "")
            payment_ids.append(payment_id)
        
        #insert new
        else:  
            tenant_cheque_identifier = payment_details.get("tenant_cheque_identifier", "")
            tenant_cheque_date = payment_details.get("tenant_cheque_date", "")
            
            for i in range(quantity):                
                cursor.execute('''
                INSERT INTO payments 
                (status, tenant_id, 
                building_id, acceptance_date, amount, payment_type, worker_id,
                receipt, tenant_cheque_identifier, payment_approval, tenant_cheque_date, tenant_bank_account, tenant_bank_branch,
                company_bank_account, company_bank_branch, deposit_date, comment, external_folder) 
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                ''', (payment_details.get("status", ""), 
                      payment_details.get("tenant_id", ""), 
                      payment_details.get("building_id", ""), 
                      payment_details.get("acceptance_date", ""), 
                      payment_details.get("amount", ""), 
                      payment_details.get("payment_type", ""), 
                      payment_details.get("worker_id", ""), 
                      payment_details.get("receipt", ""), 
                      '%d' % (int(tenant_cheque_identifier) + i) if len(tenant_cheque_identifier) else "", 
                      payment_details.get("payment_approval", ""),
                      '%s' % (dates.date(tenant_cheque_date) + relativedelta(months=i)) if len(tenant_cheque_date) else "",                                        
                      payment_details.get("tenant_bank_account", ""), 
                      payment_details.get("tenant_bank_branch", ""), 
                      payment_details.get("company_bank_account", ""), 
                      payment_details.get("company_bank_branch", ""), 
                      payment_details.get("deposit_date", ""), 
                      payment_details.get("comment", ""), 
                      payment_details.get("external_folder", "")
                      ) )                     
                
                payment_id = cursor.lastrowid
                payment_ids.append(payment_id)

    return {'payment_ids': payment_ids}

#gets service requests info from the database
@bottle.route('/fetchPayments')
def fetchPayments():
    
    building_id = bottle.request.query.building_id
    tenant_id = bottle.request.query.tenant_id    
    status = bottle.request.query.status    
    payment_approval = bottle.request.query.payment_approval        
    limit = bottle.request.query.limit        

    start_date = bottle.request.query.start_date
    end_date = bottle.request.query.end_date  
    lastUpdatedPaymentRequests = json.loads(bottle.request.query.updated_payment_ids) if len(bottle.request.query.updated_payment_ids) else []
    
    

    if len(limit):
        limit = int(limit)
    else:
        limit = 0        

    info_db = sqlite3.connect(utils.DB_INFO)

    cursor=info_db.cursor()
    #https://stackoverflow.com/questions/25469981/python-sqlite3-build-where-part-with-dynamic-placeholders
    parameters  = [start_date, end_date]
    query = '''         
        SELECT p.payment_id, 
        p.status, 
        p.payment_type,
        p.receipt,
        DATE(p.tenant_cheque_date),
        p.amount,
        p.tenant_bank_account,
        p.tenant_bank_branch,        
        p.tenant_cheque_identifier,
        p.payment_approval,
        p.building_id, 
        p.tenant_id, 
        b.name as building_name,
        t.name as tenant_name,
        t.apartment_number,
        DATE(p.acceptance_date),
        DATE(p.deposit_date),        
        p.worker_id,
        w.name as worker_name,
        p.company_bank_account,
        p.company_bank_branch,        
        p.comment,
        p.external_folder        
        FROM payments as p
        LEFT JOIN buildings as b ON p.building_id = b.building_id
	LEFT JOIN tenants as t ON p.tenant_id = t.tenant_id
	LEFT JOIN workers as w ON p.worker_id = w.worker_id	
        WHERE DATE(p.tenant_cheque_date) between ? AND ? 
        '''

    query_ext = ''

    if len(status) and int(status):
        query_ext += " AND p.status = ?"
        parameters += [status]
        
    if len(payment_approval):
        query_ext += " AND p.payment_approval = ?"
        parameters += [payment_approval]

    if len(building_id):
        query_ext += " AND p.building_id = ?"
        parameters += [building_id]    

    if len(tenant_id):
        query_ext += " AND p.tenant_id = ?"
        parameters += [tenant_id]                    

    query_ext += " ORDER BY p.acceptance_date DESC"        

    cursor.execute('SELECT COUNT(*) FROM payments as p WHERE DATE(p.tenant_cheque_date) between ? AND ? %s' % query_ext, parameters)
    res = cursor.fetchone()
    if res:
        maximum_records, = res
    else:
        maximum_records = 0    

    #now for the main query
    if limit:
        query_ext += " LIMIT %d" % limit    

    query += query_ext      
    cursor.execute(query, parameters)                
        
    paymentOf =  { pId: {
        'payment_id': pId,         
        'status': status, 
        'payment_type': payment_type,
        'receipt': receipt,
        'tenant_cheque_date': tenant_cheque_date,
        'amount': amount,
        'tenant_bank_account': tenant_bank_account,
        'tenant_bank_branch': tenant_bank_branch,        
        'tenant_cheque_identifier': tenant_cheque_identifier,        
        'payment_approval': payment_approval,                
        'building_id': building_id,
        'payment_selected': pId in lastUpdatedPaymentRequests,
        'tenant_id': tenant_id,
        'building_name': building_name,
        'tenant_name': tenant_name,
        'apartment_number': apartment_number,
        'acceptance_date': acceptance_date,
        'deposit_date': deposit_date,
        'worker_id': worker_id,
        'worker_name': worker_name,
        'company_bank_account': company_bank_account,
        'company_bank_branch': company_bank_branch,        
        'comment': comment,
        'external_folder': external_folder
        } for pId, 
                status, 
                payment_type,
                receipt,
                tenant_cheque_date,
                amount,
                tenant_bank_account,
                tenant_bank_branch,                
                tenant_cheque_identifier,
                payment_approval,
                building_id, 
                tenant_id, 
                building_name,
                tenant_name,
                apartment_number,
                acceptance_date,
                deposit_date,        
                worker_id,
                worker_name,
                company_bank_account,
                company_bank_branch,                
                comment,
                external_folder  in cursor }        


    return {'payment_requests': paymentOf, 'maximum_records': maximum_records}


#gets alerts info from the database
@bottle.route('/fetchTemplates_new')
def fetchTemplates_new():
    templates = []
    lastUpdatedTemplateId = bottle.request.query.updated_template if len(bottle.request.query.updated_template) else 0        
    
    info_db = sqlite3.connect(utils.DB_INFO)    
    cursor=info_db.cursor()    
    cursor.execute("SELECT t.template_id, t.template_name, t.comment FROM templates as t")

    templates = [
        { 
            'template_id': tId, 
            'name': tName, 
            'comment': tComment,            
            'sms_content': open(os.path.join('templates', tName, 'sms.htm')).read() if os.path.exists(os.path.join('templates', tName, 'sms.htm')) else "",
            'mail_content': open(os.path.join('templates', tName, 'mail.htm')).read() if os.path.exists(os.path.join('templates', tName, 'mail.htm')) else "",
            'mail_subject': open(os.path.join('templates', tName, 'mailSubject.htm')).read() if os.path.exists(os.path.join('templates', tName, 'mailSubject.htm')) else "",
            'letter_content': open(os.path.join('templates', tName, 'letter.htm')).read() if os.path.exists(os.path.join('templates', tName, 'letter.htm')) else "",
            'modified_now': int(lastUpdatedTemplateId) == int(tId),
            'path': ""
        } 
        for tId, tName, tComment
        in cursor]                         
    
    return {'templates': templates}

@bottle.post('/copyTemplate')
def copyTemplate():
    utils.Md('templates')
    f = bottle.request.forms    
    template_details = json.loads(f.template_details) 
    template_name = template_details["name"]
    comment = template_details["comment"]
    template_path = os.path.join('templates', template_name)
    
    template_copy = utils.GenerateDirCopy('templates', template_name, ' - עותק'.decode('utf-8'))

    template_copied_path = os.path.join('templates', template_copy)
    shutil.copytree(template_path, template_copied_path)
    
    #now update db    
    info_db = sqlite3.connect(utils.DB_INFO)    
    with info_db as connection:
        cursor=connection.cursor()     
        cursor.execute('''
        INSERT INTO templates (template_name, comment) 
        VALUES (?, ?)
        ''', ( template_copy, comment ) )  

    template_id = cursor.lastrowid
    return {'template_id': template_id}
    
@bottle.post('/addNewTemplate')
def addNewTemplate():
    f = bottle.request.forms    
    template_details = json.loads(f.template_details)
    
    sms_content = f.sms_content
    mail_content = f.mail_content
    mail_subject = f.mail_subject
    letter_content = f.letter_content
       
    #first of all update files at hard disk level
    template_name = template_details.get("name", "")
 
    utils.Md('templates')
    template_path = os.path.join('templates', template_name)
    utils.Md(template_path)
    
    with open(os.path.join(template_path, 'sms.htm'), 'wb') as smsFp:
        smsFp.write(sms_content.encode('utf-8'))
        
    with open(os.path.join(template_path, 'mail.htm'), 'wb') as mailFp:
            mailFp.write(mail_content.encode('utf-8'))
            
    with open(os.path.join(template_path, 'mailSubject.htm'), 'wb') as mailSubjectFp:
                mailSubjectFp.write(mail_subject.encode('utf-8'))    
            
    with open(os.path.join(template_path, 'letter.htm'), 'wb') as letterFp:
            letterFp.write(letter_content.encode('utf-8'))    


    #now update db    
    info_db = sqlite3.connect(utils.DB_INFO)    
    with info_db as connection:
        cursor=connection.cursor() 

        if template_details.get("edit", False):
            cursor.execute('''
            UPDATE templates 
            SET template_name = ?, comment = ?
            WHERE template_id = ?
            ''', (template_details.get("name", ""), 
                  template_details.get("comment", ""),
                  template_details.get("template_id", "") ) ) 

            template_id = template_details.get("template_id", "")

        else:

            cursor.execute('''
            INSERT INTO templates (template_name, comment) 
            VALUES (?, ?)
            ''', ( template_details.get("name", ""), 
                  template_details.get("comment", "") ) )  

            template_id = cursor.lastrowid


    return {'template_id': template_id}

@bottle.post('/deleteTemplate') 
def deleteTemplate():
    f = bottle.request.forms    
    template_id = f.template_id

    info_db = sqlite3.connect(utils.DB_INFO)    
    with info_db as connection:
        cursor=connection.cursor()        

        cursor.execute('''
        DELETE FROM templates where template_id = ?
        ''', (template_id, ))
        
#gets fields info from the database
@bottle.route('/fetchFields')
def fetchFields():
    
    lastUpdatedField = bottle.request.query.updated_field if len(bottle.request.query.updated_field) else 0

    info_db = sqlite3.connect(utils.DB_INFO)

    cursor=info_db.cursor()

    cursor.execute('''
        SELECT f.field_id, f.excel_header, f.field_type, f.template_name, f.comment
        FROM fields as f     
        ''')    


    fieldOf =  { fId: {
        'field_id': fId, 
        'excel_header': fHeader, 
        'field_type': fType, 
        'template_name': fTemplate,         
        'comment': fComment,
        'modified_now': int(lastUpdatedField) == int(fId)} for 
                  fId, 
                  fHeader, 
                  fType,
                  fTemplate, 
                  fComment in cursor}        

    return json.dumps({'fields': fieldOf})

@bottle.post('/addNewField')
def addNewField():
    f = bottle.request.forms    
    field_details = json.loads(f.field)


    info_db = sqlite3.connect(utils.DB_INFO)    
    with info_db as connection:
        cursor=connection.cursor() 

        if field_details.get("edit", False):
            cursor.execute('''
            UPDATE fields 
            SET excel_header = ?, field_type = ?, template_name = ?, comment = ?
            WHERE field_id = ?
            ''', (field_details.get("excel_header", ""), 
                  field_details.get("field_type", ""), 
                  field_details.get("template_name", ""), 
                  field_details.get("comment", ""),
                  field_details.get("field_id", "") ) ) 

            field_id = field_details.get("field_id", "")

        else:

            cursor.execute('''
            INSERT INTO fields (excel_header, field_type, template_name, comment) 
            VALUES (?, ?, ?, ?)
            ''', (field_details.get("excel_header", ""), 
                  field_details.get("field_type", ""), 
                  field_details.get("template_name", ""), 
                  field_details.get("comment", "") ) )  

            field_id = cursor.lastrowid


    return {'field_id': field_id}

@bottle.post('/deleteField') 
def deleteField():
    f = bottle.request.forms    
    field_id = f.field_id

    info_db = sqlite3.connect(utils.DB_INFO)    
    with info_db as connection:
        cursor=connection.cursor()        

        cursor.execute('''
        DELETE FROM fields where field_id = ?
        ''', (field_id, ))
        
#gets service requests info from the database
@bottle.route('/fetchServiceRequests')
def fetchServiceRequests():

    building_id = bottle.request.query.building_id
    tenant_id = bottle.request.query.tenant_id
    professional_id = bottle.request.query.professional_id    
    status = bottle.request.query.status
    service_type = bottle.request.query.service_type

    start_date = bottle.request.query.start_date
    end_date = bottle.request.query.end_date  
    lastUpdatedServiceRequest = bottle.request.query.updated_service_request_id if len(bottle.request.query.updated_service_request_id) else 0        

    limit = bottle.request.query.limit

    if len(limit):
        limit = int(limit)
    else:
        limit = 0        

    info_db = sqlite3.connect(utils.DB_INFO)

    cursor=info_db.cursor()
    #https://stackoverflow.com/questions/25469981/python-sqlite3-build-where-part-with-dynamic-placeholders
    parameters  = [start_date, end_date]
    query = '''         
        SELECT s.service_id, 
        s.description, 
        s.category, 
        s.building_id, 
        s.tenant_id, 
        s.worker_id, 
        s.professional_id, 
        s.prevention_id,
        s.status, 
        s.start_date, 
        s.end_date, 
        s.cost, 
        s.comment,
        s.reminders,
        b.name as building_name,
        t.name as tenant_name,
        w.name as worker_name,
        p.name as professional_name        
        FROM service as s
        LEFT JOIN buildings as b ON s.building_id = b.building_id
	LEFT JOIN tenants as t ON s.tenant_id = t.tenant_id
	LEFT JOIN workers as w ON s.worker_id = w.worker_id
	LEFT JOIN professionals as p ON s.professional_id = p.professional_id
        WHERE DATE(s.start_date) between ? AND ? 
        '''

    query_ext = ''

    if len(status) and int(status):
        if int(status) == 4:
            #pull only service requests which are opened/in progress
            status = 3
            statuses = utils.DecimalBreakDown(status)
            question_marks = ['?' for s in statuses]
            query_ext += " AND s.status in (%s)" % ','.join(question_marks)
            for st in statuses:
                parameters += [st]

            query_ext += "AND DATE(s.start_date) < ?"
            parameters += [datetime.datetime.now().date() - datetime.timedelta(days=utils.config.service_sla)]

    if len(service_type) and int(service_type):
        if int(service_type) == 1:
            query_ext += " AND s.prevention_id = 0"

        if int(service_type) == 2:
            query_ext += " AND s.prevention_id > 0"

    if len(building_id):
        query_ext += " AND s.building_id = ?"
        parameters += [building_id]    

    if len(tenant_id):
        query_ext += " AND s.tenant_id = ?"
        parameters += [tenant_id]        
    if len(professional_id):
        query_ext += " AND s.professional_id = ?"
        parameters += [professional_id]            

    query_ext += " ORDER BY s.start_date DESC"        

    cursor.execute('SELECT COUNT(*) FROM service as s WHERE DATE(s.start_date) between ? AND ? %s' % query_ext, parameters)
    res = cursor.fetchone()
    if res:
        maximum_records, = res
    else:
        maximum_records = 0    

    #now for the main query
    if limit:
        query_ext += " LIMIT %d" % limit    


    query += query_ext

    cursor.execute(query, parameters)

    serviceOf =  { sId: {
        'service_id': sId, 
        'description': sDescription,         
        'category': sCategory, 
        'building_id': sBuildingId, 
        'tenant_id': sTenantId,
        'worker_id': sWorkerId,
        'professional_id': sProfessionalId,
        'prevention_id': sPrevention_id,
        'status': sStatus,
        'start_date': sStartDate,
        'end_date': sEndDate,
        'cost': sCost,
        'comment': sComment,
        'reminders': sReminders,
        'service_selected': int(lastUpdatedServiceRequest) == int(sId),
        'must_attend': (dates.date(sStartDate) + datetime.timedelta(days=utils.config.service_sla)) < datetime.datetime.now().date() and (int(sStatus) == 1 or int(sStatus) == 2),
        'building_name': building_name,
        'tenant_name': tenant_name,
        'worker_name': worker_name,
        'professional_name': professional_name,
        } for
                   sId,
                   sDescription,                    
                   sCategory,
                   sBuildingId, 
                   sTenantId, 
                   sWorkerId, 
                   sProfessionalId,
                   sPrevention_id,
                   sStatus,
                   sStartDate,
                   sEndDate,                   
                   sCost,
                   sComment,
                   sReminders,
                   building_name,
                   tenant_name,
                   worker_name,
                   professional_name in cursor}        


    return {'service_requests': serviceOf, 'maximum_records': maximum_records}


@bottle.route('/guessProfessionalCategory')
def guessProfessionalCategory():

    guesses = []
    info_db = sqlite3.connect(utils.DB_INFO)
    cursor=info_db.cursor()

    user_input = bottle.request.query.name

    query = """
    SELECT DISTINCT category 
    FROM professionals
    WHERE category like '%%%s%%'""" % user_input

    cursor.execute(query)
    guesses = list( {'id': category, 'name': category} for (category,) in cursor.fetchall())    

    return json.dumps(guesses)


@bottle.route('/guessServiceCategory')
def guessServiceCategory():

    guesses = []
    info_db = sqlite3.connect(utils.DB_INFO)
    cursor=info_db.cursor()

    user_input = bottle.request.query.name

    query = """
    SELECT DISTINCT category 
    FROM service
    WHERE category like '%%%s%%'""" % user_input

    cursor.execute(query)
    guesses = list( {'id': category, 'name': category} for (category,) in cursor.fetchall())    
    
    return json.dumps(guesses)

@bottle.route('/guessBuildingNickName')
def guessBuildingNickName():

    guesses = []
    info_db = sqlite3.connect(utils.DB_INFO)
    cursor=info_db.cursor()

    user_input = bottle.request.query.name

    query = """
    SELECT DISTINCT nick_name 
    FROM buildings
    WHERE nick_name like '%%%s%%'""" % user_input

    cursor.execute(query)
    guesses = list( {'id': nick_name, 'name': nick_name} for (nick_name,) in cursor.fetchall())    
    
    return json.dumps(guesses)

#get a list of professional names by the user input
@bottle.route('/guessProfessional')
def guessProfessional():

    guesses = []
    info_db = sqlite3.connect(utils.DB_INFO)
    cursor=info_db.cursor()

    user_input = bottle.request.query.name

    query = """
    SELECT DISTINCT p.professional_id, p.name 
    FROM professionals as p
    WHERE p.name like '%%%s%%'""" % user_input

    cursor.execute(query)
    guesses = list( {'id': professionalId, 'name': professionalName} for professionalId, professionalName in cursor.fetchall())    

    return json.dumps(guesses)

#get a list of building names by the user input
@bottle.route('/guessBuilding')
def GuessBuilding():

    guesses = []
    info_db = sqlite3.connect(utils.DB_INFO)
    cursor=info_db.cursor()

    user_input = bottle.request.query.name

    query = """
    SELECT DISTINCT b.building_id, b.name 
    FROM buildings as b
    WHERE b.name like '%%%s%%'""" % user_input

    cursor.execute(query)
    guesses = list( {'id': buildingId, 'name': buildingName} for buildingId, buildingName in cursor.fetchall())

    return json.dumps(guesses)

#get a list of prevention names by the user input
@bottle.route('/guessPrevention')
def guessPrevention():

    guesses = []
    info_db = sqlite3.connect(utils.DB_INFO)
    cursor=info_db.cursor()

    user_input = bottle.request.query.name

    query = """
        SELECT DISTINCT description 
        FROM prevention
        WHERE description like '%%%s%%'""" % user_input

    cursor.execute(query)
    guesses = list({'id': description, 'name': description} for (description,) in cursor.fetchall())

    return json.dumps(guesses)

@bottle.route('/guessMultiElement')
def guessMultiElement():
    entities = GetMultiTypeElements()
    user_input = bottle.request.query.name    
    guesses = [ent for ent in entities if user_input in ent["name"]]
    return json.dumps(guesses)


#get a list of tenants names by the user input
@bottle.route('/guessTenant')
def GuessTenant():
    guesses = []

    user_input = bottle.request.query.name
    building_id = bottle.request.query.building_id

    #https://stackoverflow.com/questions/25469981/python-sqlite3-build-where-part-with-dynamic-placeholders
    parameters  = []
    query = '''
    SELECT DISTINCT t.tenant_id, t.name
    FROM tenants as t
    WHERE t.name like '%%%s%%'
    ''' % user_input

    if len(building_id):
        query += " AND t.building_id = ?"
        parameters += [building_id] 

    info_db = sqlite3.connect(utils.DB_INFO)
    cursor=info_db.cursor()    
    cursor.execute(query, parameters)

    guesses = list( {'id': tenantId, 'name': tenantName} for tenantId, tenantName in cursor.fetchall())

    return json.dumps(guesses)

#get a list of tenants names by the user input
@bottle.route('/guessDestination')
def guessDestination():
    guesses = []

    user_input = bottle.request.query.name
    building_id = bottle.request.query.building_id
    tenant_id = bottle.request.query.tenant_id

    #https://stackoverflow.com/questions/25469981/python-sqlite3-build-where-part-with-dynamic-placeholders
    parameters  = []
    query = '''
    SELECT DISTINCT a.destination
    FROM alerts as a
    WHERE a.destination like '%%%s%%'
    ''' % user_input

    if len(building_id):
        query += " AND a.building_id = ?"
        parameters += [building_id] 

    if len(tenant_id):
        query += " AND a.tenant_id = ?"
        parameters += [tenant_id]     

    info_db = sqlite3.connect(utils.DB_INFO)
    cursor=info_db.cursor()    
    cursor.execute(query, parameters)

    guesses = list( {'id': destination, 'name': destination} for (destination,) in cursor.fetchall())

    return json.dumps(guesses)

#get a list of tenants names by the user input
@bottle.route('/guessAlertByColumn')
def guessDestination():
    guesses = []

    user_input = bottle.request.query.name
    column = bottle.request.query.column
    
    #https://stackoverflow.com/questions/25469981/python-sqlite3-build-where-part-with-dynamic-placeholders    
    parameters  = []
    query = '''
    SELECT DISTINCT %s
    FROM alerts
    WHERE %s like '%%%s%%'
    ''' % (column, column, user_input)        

    info_db = sqlite3.connect(utils.DB_INFO)
    cursor=info_db.cursor()    
    cursor.execute(query, parameters)
    
    guesses = list( name for name, in cursor.fetchall() )

    return json.dumps(guesses)

#get a list of tenants names by the user input
@bottle.route('/guessBankAccount')
def guessBankAccount():
    guesses = []
    
    user_input = bottle.request.query.name
    
    query = """
    SELECT DISTINCT p.company_bank_name
    FROM payments as p
    WHERE p.company_bank_name like '%%%s%%'""" % user_input    

    info_db = sqlite3.connect(utils.DB_INFO)
    cursor=info_db.cursor()    
    cursor.execute(query)
    
    guesses = list( name for name, in cursor.fetchall())        
    return json.dumps(guesses)

#get a list of tenants names by the user input
@bottle.route('/guessPaymentApproval')
def guessPaymentApproval():
    guesses = []
    
    user_input = bottle.request.query.name
    
    query = """
    SELECT DISTINCT p.payment_approval
    FROM payments as p
    WHERE p.payment_approval like '%%%s%%'""" % user_input    

    info_db = sqlite3.connect(utils.DB_INFO)
    cursor=info_db.cursor()    
    cursor.execute(query)
    
    guesses = list( name for name, in cursor.fetchall())        
    return json.dumps(guesses)


#gets alerts info from the database
@bottle.route('/fetchAlerts')
def fetchAlerts():
    alerts = []

    building_name = bottle.request.query.buildingName
    recepient_name = bottle.request.query.recepientName
    source = bottle.request.query.source
    destination = bottle.request.query.destination

    start_date = bottle.request.query.start_date
    end_date = bottle.request.query.end_date
    limit = bottle.request.query.limit

    if len(limit):
        limit = int(limit)
    else:
        limit = 0

    info_db = sqlite3.connect(utils.DB_INFO)    
    cursor=info_db.cursor()        

    #https://stackoverflow.com/questions/25469981/python-sqlite3-build-where-part-with-dynamic-placeholders
    parameters  = [start_date, end_date]
    query = '''
    SELECT a.alert_id
         , a.recepient_type
         , a.recepient_name
         , a.building_name
         , a.path_to_file
         , a.alert_type
         , a.meta_data
         , a.destination
         , a.source
         , a.updated
         , a. external_folder
    FROM alerts as a
    WHERE DATE(a.updated) between ? AND ?    
    '''

    query_ext = ''

    if len(building_name):
        query_ext += " AND a.building_name = ?"
        parameters += [building_name]

    if len(recepient_name):
        query_ext += " AND a.recepient_name = ?"
        parameters += [recepient_name]

    if len(source):
        query_ext += " AND a.source = ?"
        parameters += [source]

    if len(destination):
        query_ext += " AND a.destination = ?"
        parameters += [destination]          

    query_ext += " ORDER BY a.updated DESC"           

    cursor.execute('SELECT COUNT(*) FROM alerts as a WHERE DATE(a.updated) between ? AND ? %s' % query_ext, parameters)    
    res = cursor.fetchone()
    if res:
        maximum_records, = res
    else:
        maximum_records = 0    

    #now for the main query
    if limit:
        query_ext += " LIMIT %d" % limit    

    query += query_ext
    cursor.execute(query, parameters)

    alerts = [
        { 
            'alert_id': aId, 
            'recepient_type': rType, 
            'recepient_name': rName, 
            'building_name': bName, 
            'path_to_file': alertPathToFile,
            'alert_type': aType,
            'meta_data': alertMetaData,
            'destination': aDestination,
            'source': aSource,        
            'updated': alertTimeStamp,
            'external_folder':  external_folder,            
            'alert_data': open(alertPathToFile).read() if os.path.exists(alertPathToFile) else "%s does not exist" % alertPathToFile,
            'alert_selected': False
        } 
        for aId, rType, rName, bName, alertPathToFile, aType, alertMetaData, aDestination, aSource, alertTimeStamp, external_folder
        in cursor]                         

    return {'alerts': alerts, 'maximum_records': maximum_records}

#gets buildings info from the database
@bottle.route('/fetchDebtTypes')
def fetchDebtTypes():
    info_db = sqlite3.connect(utils.DB_INFO)    
    with info_db as connection:
        cursor=connection.cursor()            
        cursor.execute('''SELECT distinct description FROM debts''')        
    
    res = {'debt_types': [desc for desc, in cursor.fetchall()]}    
    return res
    
#gets buildings info from the database
@bottle.route('/fetchTenantsDebts')
def fetchTenantsDebts():

    lastUpdatedTenant = bottle.request.query.updated_tenant if len(bottle.request.query.updated_tenant) else 0    
    start_date = bottle.request.query.start_date
    end_date = bottle.request.query.end_date 
    months_delta = dates.months_delta(start_date, end_date)
    
    show_only_debts = bottle.request.query.show_only_debts
    show_only_consecutive_debts = bottle.request.query.show_only_consecutive_debts
    debt_type = bottle.request.query.debt_type
    minimal_debt = utils.Intify(bottle.request.query.minimal_debt)

    buildings = ','.join([str(b) for b in json.loads(bottle.request.query.element_id)])        

    tenantsOf = GetTenantsGeneralInfoFromDb(lastUpdatedTenant, buildings)
    debtsOf = GetTenantsDebtsInfoFromDb(start_date, end_date, buildings, debt_type)
    dynamicTenantDataOf = GetTenantsDynamicDataInfoFromDb(tenantsOf.keys())

    for tId, tenant in tenantsOf.items():
        tenant_debt = debtsOf.get(tId, None)
        if tenant_debt:        
            #copy all debts' details to this building
            for k,v in tenant_debt.items():
                tenant[k] = v
        
        dynamic_data = dynamicTenantDataOf.get(tId, None)
        if dynamic_data:
            for k,v in dynamic_data.items():
                tenant[k] = v        
    if show_only_debts == 'true':
        tenantsOf = {k: tenantsOf[k] 
                     for k,v in debtsOf.items() 
                     if v['total_debt'] and v['total_debt'] >= minimal_debt} 
        
    if show_only_consecutive_debts == 'true':
        tenantsOf = {k: tenantsOf[k] 
                     for k,v in debtsOf.items() 
                     if months_delta and v['n_months'] == months_delta}    


    return json.dumps(tenantsOf)        


@bottle.route('/increaseServiceReminders') 
def increaseServiceReminders():
    increaseServiceRemindersDb(bottle.request.query.service_request_id)    

def increaseServiceRemindersDb(service_request_id):    

    info_db = sqlite3.connect(utils.DB_INFO)    
    with info_db as connection:
        cursor=connection.cursor()        

        cursor.execute('''
        UPDATE service SET reminders = reminders + 1 WHERE service_id = ?
        ''', (service_request_id, ))   

#gets buildings info from the database
@bottle.route('/sendGroupSms')
def sendGroupSms():
    d = bottle.request.query

    recepients = json.loads(d.recepients)
    smsBody = d.sms_body
    worker_id = d.worker_id
    building_name = d.building_name

    info_db = sqlite3.connect(utils.DB_INFO)

    source = db_helper.GetSourceAlertsInfo('worker', worker_id)
    #source has no phone, do not send
    if not source["phone"]:
        return

    for recepient in recepients:
        #each recepient is a string of "type-id" where type can be building, tenant, professional or worker
        recepient_type, recepient_id = recepient.split('-')

        for ad in db_helper.GetDestinationAlertsInfo(recepient_type, recepient_id, building_name):
            name = ad["name"] 
            building = ad["building"]
            phones = ad["phones"]
            emails = ad["emails"]
            element_type = ad["type"]

            for phone in phones:                
                sendAlert(smsBody, SmsCreditMessage(smsBody), 0, phone, building, name, element_type, source["phone"])            

#gets buildings info from the database
@bottle.post('/deleteBuildings')
def deleteBuildings():
    f = bottle.request.forms    
    building_ids = json.loads(f.building_ids)

    info_db = sqlite3.connect(utils.DB_INFO)
    with info_db as connection:
        cursor=connection.cursor()        
        for tableName in ['buildings', 'tenants', 'service']:            

            cursor.execute('''
            DELETE FROM %s where building_id in (%s)
            ''' % (tableName, ','.join(str(b) for b in building_ids)) )

#gets buildings info from the database
@bottle.post('/resendAlertsFromHistory') 
def resendAlertsFromHistory():
    f = bottle.request.forms    
    alert_ids = json.loads(f.alert_ids)

    info_db = sqlite3.connect(utils.DB_INFO)
    with info_db as connection:
        cursor=connection.cursor()        

        cursor.execute('''
        SELECT recepient_type, recepient_name, building_name, path_to_file, alert_type, meta_data, destination, source FROM alerts 
        WHERE alert_id in (%s)
        ''' % ','.join(str(b) for b in alert_ids ) )        

        for recepientType, recepientName, buildingName, pathToFile, alertType, alertMeta, alertDestination, source in cursor.fetchall():
            alertData = file(pathToFile).read().decode('utf-8')
            sendAlert(alertData, alertMeta, alertType, alertDestination, buildingName, recepientName, recepientType, source)


#gets buildings info from the database
@bottle.route('/sendGroupMail')
def sendGroupMail():    
    d = bottle.request.query    
    recepients = json.loads(d.recepients)
    attachments = json.loads(d.attachments)
    uploaded_folder = d.uploaded_folder

    #prepare attachment folder
    if len(uploaded_folder):
        attachments = [attach["name"] for attach in attachments]
        for dirpath, dirnames, filenames in os.walk(uploaded_folder):
            for f in filenames:
                if f not in attachments:
                    os.remove(os.path.join(uploaded_folder, f))



    mailBody = d.mail_body

    mailSubject = d.mail_subject
    worker_id = d.worker_id
    building_name = d.building_name

    info_db = sqlite3.connect(utils.DB_INFO)

    source = db_helper.GetSourceAlertsInfo('worker', worker_id)
    #source has no phone, do not send
    if not source["email"]:
        return

    for recepient in recepients:
        #each recepient is a string of "type-id" where type can be building, tenant, professional or worker
        recepient_type, recepient_id = recepient.split('-')

        for ad in db_helper.GetDestinationAlertsInfo(recepient_type, recepient_id, building_name):
            name = ad["name"] 
            building = ad["building"]
            phones = ad["phones"]
            emails = ad["emails"]
            element_type = ad["type"]

            for email in emails:                   
                sendAlert(mailBody,
                          mailSubject, 
                          1, 
                          email, 
                          building, 
                          name, 
                          element_type, 
                          source["email"], 
                          uploaded_folder)

#this is the main screen
@bottle.route('/main')
def main():    
    return bottle.static_file('index.html', '.')

@bottle.post('/deleteServiceRequests')
def deleteServiceRequests():

    f = bottle.request.forms    
    service_ids = json.loads(f.service_ids)
    prevention_ids = json.loads(f.prevention_ids)
    delete_status = int(f.delete_status)

    info_db = sqlite3.connect(utils.DB_INFO)

    # delete service requests
    with info_db as connection:
        cursor = connection.cursor()

        cursor.execute('''
        DELETE FROM service where service_id in (%s)
        ''' % ','.join(str(b) for b in service_ids))

    # delete service requests from the same prevention id
    if delete_status:
        with info_db as connection:
            cursor = connection.cursor()

            cursor.execute('''
                DELETE FROM service where prevention_id in (%s)
                ''' % ','.join(str(b) for b in prevention_ids))

@bottle.post('/sendServiceReminders') 
def sendServiceReminders():
    f = bottle.request.forms    
    service_ids = json.loads(f.service_ids)
    worker_id = f.worker_id
    alert = 'sms'
    
    source = db_helper.GetSourceAlertsInfo('worker', worker_id)
    source_phone = source["phone"]    
    
    #source has no phone, do not send
    if not source_phone:
        return
    
    #take the first phone
    source_phone = source_phone.split(',')[0]
    
    info_db = sqlite3.connect(utils.DB_INFO)
    with info_db as connection:
        cursor=connection.cursor()        

        cursor.execute('''
        SELECT s.service_id, s.description ,s.status, b.name as building_name, p.name as professional_name, p.phones as professional_phones, t.name as tenant_name, w.name as worker_name, t.phones as tenant_phones, p.phones as professional_phones
	FROM service as s 
	LEFT JOIN buildings as b ON s.building_id = b.building_id
	LEFT JOIN tenants as t ON s.tenant_id = t.tenant_id
	LEFT JOIN workers as w ON s.worker_id = w.worker_id
	LEFT JOIN professionals as p ON s.professional_id = p.professional_id
	WHERE service_id in (%s)
        ''' % ','.join(str(b) for b in service_ids ) )

        for service_id, service_description, service_status, building_name, professional_name, professional_phones, tenant_name, worker_name, tenant_phones, professional_phones in cursor.fetchall():	    
            content = resolveAlertTemplate(f.path, 
                                           alert,
                                           {
                                               'service_request_description': service_description if service_description else "",
                                               'service_request_id': service_id,
                                               'building': building_name if building_name else "",
                                               'professional_name': professional_name if professional_name else "",
                                               'worker_name': worker_name if worker_name else "",
                                               'tenant_name': tenant_name if tenant_name else "",
                                               'tenant_phones': tenant_phones	                                    
                                               },
                                           file(os.path.join(f.path, alert + '.htm')).read())

            content = content["content"]
            for phone in professional_phones.split(', '):                
                sendAlert(content, SmsCreditMessage(content), 0, phone, building_name, professional_name, 1, source_phone)
                increaseServiceRemindersDb(service_id)
                
@bottle.post('/deleteProfessional') 
def deleteProfessional():
    f = bottle.request.forms    
    professional_id = f.professional_id

    info_db = sqlite3.connect(utils.DB_INFO)    
    with info_db as connection:
        cursor=connection.cursor()        

        cursor.execute('''
        DELETE FROM professionals where professional_id = ?
        ''', (professional_id, ))


@bottle.post('/deleteAlertsFromHistory')  
def deleteAlertsFromHistory():
    f = bottle.request.forms    
    alert_ids = json.loads(f.alert_ids)

    info_db = sqlite3.connect(utils.DB_INFO)
    with info_db as connection:
        cursor=connection.cursor()        

        cursor.execute('''
        DELETE FROM alerts where alert_id in (%s)
        ''' % ','.join(str(b) for b in alert_ids ) )       


@bottle.post('/deleteWorker') 
def deleteWorker():
    f = bottle.request.forms    
    worker_id = f.worker_id

    info_db = sqlite3.connect(utils.DB_INFO)    
    with info_db as connection:
        cursor=connection.cursor()        

        cursor.execute('''
        DELETE FROM workers where worker_id = ?
        ''', (worker_id, ))

@bottle.post('/addNewProfessional') 
def addNewProfessional():
    f = bottle.request.forms    
    professional_details = json.loads(f.professional)

    info_db = sqlite3.connect(utils.DB_INFO)    
    with info_db as connection:
        cursor=connection.cursor() 

        if professional_details.get("edit", False):
            cursor.execute('''
            UPDATE professionals 
            SET name = ?, category = ?, mails = ?, phones = ?, fax = ?, address = ?, comment = ?, company_person_id = ?
            WHERE professional_id = ?
            ''', (professional_details.get("name", ""), 
                  professional_details.get("category", ""), 
                  professional_details.get("mails", ""), 
                  professional_details.get("phones", ""), 
                  professional_details.get("fax", ""), 
                  professional_details.get("address", ""), 
                  professional_details.get("comment", ""), 
                  professional_details.get("company_person_id", ""),
                  professional_details.get("professional_id", "") ) )                    

            professional_id = professional_details.get("professional_id", "")

        else:

            cursor.execute('''
            INSERT INTO professionals (name, category, mails, phones, fax, address, comment, company_person_id) 
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            ''', (professional_details.get("name", ""), 
                  professional_details.get("category", ""), 
                  professional_details.get("mails", ""), 
                  professional_details.get("phones", ""), 
                  professional_details.get("fax", ""), 
                  professional_details.get("address", ""), 
                  professional_details.get("comment", ""), 
                  professional_details.get("company_person_id", "") ) )                    

            professional_id = cursor.lastrowid

    return {'professional_id': professional_id}


@bottle.post('/addNewServiceRequest') 
def addNewServiceRequest():
    f = bottle.request.forms    
    service_request_details = json.loads(f.service_request)

    building_id = 0 if service_request_details.get("building_id", "") == "" else service_request_details["building_id"]
    tenant_id = 0 if service_request_details.get("tenant_id", "") == "" else service_request_details["tenant_id"]
    worker_id = 0 if service_request_details.get("worker_id", "") == "" else service_request_details["worker_id"]
    professional_id = 0 if service_request_details.get("professional_id", "") == "" else service_request_details["professional_id"]
    cost = 0 if service_request_details.get("cost", "") == "" else service_request_details["cost"]

    info_db = sqlite3.connect(utils.DB_INFO)
    with info_db as connection:
        cursor=connection.cursor() 

        if service_request_details.get("edit", False):
            cursor.execute('''
            UPDATE service 
            SET description = ?, category = ?, building_id = ?, tenant_id = ?, worker_id = ?, professional_id = ?, status = ?, start_date = ?, end_date = ?, cost = ?, comment = ?
            WHERE service_id = ?
            ''', (service_request_details.get("description", ""), 
                  service_request_details.get("category", ""), 
                  building_id, 
                  tenant_id, 
                  worker_id, 
                  professional_id,                   
                  service_request_details.get("status", ""),
                  service_request_details.get("start_date", ""),
                  service_request_details.get("end_date", ""),
                  service_request_details.get("cost", ""),
                  service_request_details.get("comment", ""),
                  service_request_details.get("service_id", "") ) )  

            service_request_id = service_request_details.get("service_id", "")

        else:

            cursor.execute('''
            INSERT INTO service (description, category, building_id, tenant_id, worker_id, professional_id, cost, comment) 
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            ''', (service_request_details.get("description", ""), 
                  service_request_details.get("category", ""), 
                  service_request_details.get("building_id", ""), 
                  service_request_details.get("tenant_id", ""), 
                  service_request_details.get("worker_id", ""), 
                  service_request_details.get("professional_id", ""), 
                  service_request_details.get("cost", ""), 
                  service_request_details.get("comment", "")
                  ) )


            service_request_id = cursor.lastrowid

    return {'service_request_id': service_request_id}


def bulkServiceRequests(prevention_details, months_list):

    # create service requests for five years in the future
    current_year = datetime.datetime.now().year
    service_dates = [
        datetime.datetime.strptime('%s-%s 08:00:00' % (current_year + i, m), '%Y-%m %H:%M:%S') for m in months_list
        for i in range(6)
        if datetime.datetime.now() < datetime.datetime.strptime('%s-%s 08:00:00' % (current_year + i, m),
                                                                '%Y-%m %H:%M:%S')
    ]

    service_requests = []
    description = 0 if prevention_details.get("description", "") == "" else prevention_details["description"]
    category = "" if prevention_details.get("category", "") == "" else prevention_details["category"]
    building_id = 0 if prevention_details.get("building_id", "") == "" else prevention_details["building_id"]
    tenant_id = 0 if prevention_details.get("tenant_id", "") == "" else prevention_details["tenant_id"]
    worker_id = 0 if prevention_details.get("worker_id", "") == "" else prevention_details["worker_id"]
    professional_id = 0 if prevention_details.get("professional_id", "") == "" else prevention_details[
        "professional_id"]
    prevention_id = 0 if prevention_details.get("prevention_id", "") == "" else prevention_details[
        "prevention_id"]
    cost = 0 if prevention_details.get("cost", "") == "" else prevention_details["cost"]
    comment = 0 if prevention_details.get("comment", "") == "" else prevention_details["comment"]

    # insert new ones now
    for d in service_dates:
        service_requests.append((
            description,
            category,
            building_id,
            tenant_id,
            worker_id,
            professional_id,
            prevention_id,
            cost,
            comment,
            d
        ))

    info_db = sqlite3.connect(utils.DB_INFO)
    with info_db as connection:
        cursor = connection.cursor()

        #first delete all the future ones
        cursor.execute('''
        DELETE FROM service where prevention_id = ? AND DATE(start_date) > ?
        ''', (prevention_id, datetime.datetime.now().date()))

        # insert new ones
        cursor.executemany('''
                    INSERT INTO service (description, category, building_id, tenant_id, worker_id, professional_id, prevention_id, cost, comment, start_date) 
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                    ''', service_requests)

    return {'service_request_id': 3}

@bottle.post('/bulkPreventions')
def bulkPreventions():
    f = bottle.request.forms
    preventions = json.loads(f.preventions)
    target_building = f.target_building

    info_db = sqlite3.connect(utils.DB_INFO)

    # create service requests per each prevention
    for prevention_details in preventions:
        prevention_details["months"] = '1,2,3,4,5,6,7,8,9,10,11,12'
        with info_db as connection:
            cursor = connection.cursor()
            prevention_details["building_id"] = target_building
            cursor.execute('''
            INSERT INTO prevention (description, category, building_id, worker_id, professional_id, months, cost, comment) 
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            ''', (prevention_details.get("description", ""),
                  prevention_details.get("category", ""),
                  prevention_details.get("building_id", ""),
                  prevention_details.get("worker_id", ""),
                  prevention_details.get("professional_id", ""),
                  prevention_details.get("months", ""),
                  prevention_details.get("cost", ""),
                  prevention_details.get("comment", "")
                  ))

            prevention_details["prevention_id"] = cursor.lastrowid

    for prevention_details in preventions:
        # create necessary service requests
        bulkServiceRequests(prevention_details, prevention_details["months"].split(','))


@bottle.post('/addNewPrevention')
def addNewPrevention():
    f = bottle.request.forms
    prevention_details = json.loads(f.prevention)

    building_id = 0 if prevention_details.get("building_id", "") == "" else prevention_details["building_id"]
    worker_id = 0 if prevention_details.get("worker_id", "") == "" else prevention_details["worker_id"]
    professional_id = 0 if prevention_details.get("professional_id", "") == "" else prevention_details["professional_id"]
    cost = 0 if prevention_details.get("cost", "") == "" else prevention_details["cost"]

    months_list = []
    if prevention_details["january"]:
        months_list.append('1')
    if prevention_details["february"]:
        months_list.append('2')
    if prevention_details["march"]:
        months_list.append('3')
    if prevention_details["april"]:
        months_list.append('4')
    if prevention_details["may"]:
        months_list.append('5')
    if prevention_details["june"]:
        months_list.append('6')
    if prevention_details["july"]:
        months_list.append('7')
    if prevention_details["august"]:
        months_list.append('8')
    if prevention_details["september"]:
        months_list.append('9')
    if prevention_details["october"]:
        months_list.append('10')
    if prevention_details["november"]:
        months_list.append('11')
    if prevention_details["december"]:
        months_list.append('12')

    months = ",".join(months_list)

    info_db = sqlite3.connect(utils.DB_INFO)
    with info_db as connection:
        cursor = connection.cursor()

        #edit mode
        if prevention_details.get("edit", False):
            cursor.execute('''
            UPDATE prevention 
            SET description = ?, category = ?, building_id = ?, worker_id = ?, professional_id = ?, months = ?, cost = ?, comment = ?
            WHERE prevention_id = ?
            ''', (prevention_details.get("description", ""),
                  prevention_details.get("category", ""),
                  building_id,
                  worker_id,
                  professional_id,
                  months,
                  prevention_details.get("cost", ""),
                  prevention_details.get("comment", ""),
                  prevention_details.get("prevention_id", "") ) )

            prevention_id = prevention_details.get("prevention_id", "")

        else:

            cursor.execute('''
            INSERT INTO prevention (description, category, building_id, worker_id, professional_id, months, cost, comment) 
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            ''', (prevention_details.get("description", ""),
                  prevention_details.get("category", ""),
                  prevention_details.get("building_id", ""),
                  prevention_details.get("worker_id", ""),
                  prevention_details.get("professional_id", ""),
                  months,
                  prevention_details.get("cost", ""),
                  prevention_details.get("comment", "")
                  ))


            prevention_id = cursor.lastrowid


    prevention_details["prevention_id"] = prevention_id
    bulkServiceRequests(prevention_details, months_list)

    return {'prevention_id': prevention_id}

@bottle.post('/addNewWorker') 
def addNewWorker():
    f = bottle.request.forms    
    worker_details = json.loads(f.worker)


    info_db = sqlite3.connect(utils.DB_INFO)    
    with info_db as connection:
        cursor=connection.cursor() 

        if worker_details.get("edit", False):
            cursor.execute('''
            UPDATE workers 
            SET name = ?, title = ?, mails = ?, phones = ?, fax = ?, address = ?, comment = ?, person_id = ?
            WHERE worker_id = ?
            ''', (worker_details.get("name", ""), 
                  worker_details.get("title", ""), 
                  worker_details.get("mails", ""), 
                  worker_details.get("phones", ""), 
                  worker_details.get("fax", ""), 
                  worker_details.get("address", ""), 
                  worker_details.get("comment", ""), 
                  worker_details.get("person_id", ""),
                  worker_details.get("worker_id", "") ) ) 

            worker_id = worker_details.get("worker_id", "")

        else:

            cursor.execute('''
            INSERT INTO workers (name, title, mails, phones, fax, address, comment, person_id) 
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            ''', (worker_details.get("name", ""), 
                  worker_details.get("title", ""), 
                  worker_details.get("mails", ""), 
                  worker_details.get("phones", ""), 
                  worker_details.get("fax", ""), 
                  worker_details.get("address", ""), 
                  worker_details.get("comment", ""), 
                  worker_details.get("person_id", "") ) )  

            worker_id = cursor.lastrowid


    return {'worker_id': worker_id}

@bottle.post('/addNewBuilding') 
def addNewBuilding():
    f = bottle.request.forms    
    building_details = json.loads(f.building)

    info_db = sqlite3.connect(utils.DB_INFO)    
    with info_db as connection:
        cursor=connection.cursor() 

        cursor.execute('''
            UPDATE buildings 
            SET nick_name = ?
            WHERE building_id = ?
            ''', (building_details.get("nick_name", ""),  building_details.get("id", "") ) ) 

        building_id = building_details.get("id", "")

    return {'id': building_id}


@bottle.post('/exportHtmlTableToPdf') 
def exportHtmlTableToPdf():
    
    f = bottle.request.forms    
    
    records = json.loads(f.records)    
    headers = json.loads(f.headers)

    content = alerters.Alerter.GetTemplateContent('web/customer_templates/service_requests.html', None, {'records': records, 'headers': headers })
    out = 'out.pdf' 

    html = (utils.CreateTempFile(prefix="tmp", suffix=".html", dir='.')).encode('utf-8')
    pdf = (utils.CreateTempFile(prefix="tmp", suffix=".pdf", dir='.')).encode('utf-8')

    with open(html, "wb") as fpo:
        fpo.write(content.encode('utf-8')) 

    with open('convert.bat', "wb") as fpo:
        fpo.write('wkhtmltopdf %s %s' % (html, pdf))

    os.system('convert.bat')
    if os.path.exists(out):
        os.remove(out)

    os.rename(pdf, out)
    os.remove(html)
    
    utils.Md('downloads')
    shutil.copy2(out, 'downloads')
    return {'file_name': 'downloads/%s' % out}    

@bottle.post('/exportHtmlToPdf') 
def exportHtmlToPdf():
    f = bottle.request.forms            
    alert_ids = json.loads(f.alert_ids)
    content = ""
    info_db = sqlite3.connect(utils.DB_INFO)
    with info_db as connection:
        cursor=connection.cursor()        

        cursor.execute('''
        SELECT recepient_type, recepient_name, building_name, path_to_file, alert_type, meta_data, destination, source FROM alerts 
        WHERE alert_id in (%s)
        ''' % ','.join(str(b) for b in alert_ids ) )        

        for recepientType, recepientName, buildingName, pathToFile, alertType, alertMeta, alertDestination, source in cursor.fetchall():
            alertData = file(pathToFile).read().decode('utf-8')
            content = content + alertData            

    content = '<style type="text/css" media="screen,print">.sam_alert { display: block; clear: both; page-break-after: always;} .sam_alert:last-child {page-break-after: auto;}</style>' + content
    out = 'out.pdf' 

    html = (utils.CreateTempFile(prefix="tmp", suffix=".html", dir='.')).encode('utf-8')
    pdf = (utils.CreateTempFile(prefix="tmp", suffix=".pdf", dir='.')).encode('utf-8')

    #will change later on to utf-8
    with open(html, "wb") as fpo:
        fpo.write(content.encode('utf-16')) 

    with open('convert.bat', "wb") as fpo:
        fpo.write('wkhtmltopdf %s %s' % (html, pdf))

    os.system('convert.bat')
    if os.path.exists(out):
        os.remove(out)

    os.rename(pdf, out)
    os.remove(html)  

    utils.Md('downloads')
    shutil.copy2(out, 'downloads')
    return {'file_name': 'downloads/%s' % out}    



@bottle.post('/updateBuilding') 
def updateBuilding():
    f = bottle.request.forms
    building_id = bottle.request.forms.element_id

    assert building_id, 'no building id'

    info_db = sqlite3.connect(utils.DB_INFO)        

    #fetch file name
    connection = info_db.cursor()
    connection.execute('''SELECT based_on_file, name FROM buildings WHERE building_id = ?''', (building_id,))        

    res = connection.fetchone()
    if res:
        building_file, dbBuildingName = res

    #this building has no source file, so no where to update it from
    if not building_file:
        #return 0 which is not a valid id
        building_id = 0

    else:   
        #return a list of Tenants
        db_data = excel_helper.BuildFromScratch(files=building_file.split(','), dbBuildingName = dbBuildingName)        
        db_helper.UpdateDataBase(db_data)                       

    return {'new_building_id': building_id}


def GetTemplateContent(path, templateStr, templateFile, fields ):

    if path and templateFile:
        path = os.path.join(path, templateFile)

    fields["path"] = path if path and os.path.exists(path) else None
    fields["templateStr"] = templateStr if templateStr else None

    return alerters.Alerter.FormatAlertTemplate(**fields)      
    #return alerters.Alerter.FormatAlertTemplate(path if os.path.exists(path) else None,
                                                                #appartment = fields.get('apartment', ''),
                                                                #totalDebt = fields.get('total_debt', 0),
                                                                #months = fields.get('months', ''),
                                                                #building = fields.get('name', '')) 


def GetTemplateByAlertType(alert):
    if alert == 'sms':
        return 'sms.htm'

    elif alert == 'mail':
        return 'mail.htm'

    #later to check file existense
    elif alert == 'letter':
        return 'mail.htm'

def SmsCreditMessage(content):
    smsCredits = math.ceil( len(content) / 67.0 ) if len(content) > 70 else 1 if len(content) > 0 else 0
    meta = ('מספר תווים בהודעה זו : %d (סך של %d  סמסים)' % (len(content), smsCredits)).decode('utf-8')    
    return meta

def resolveAlertTemplate(path, alert, details, template_content, subject=None):
    meta = ""
    templateFile = GetTemplateByAlertType(alert)

    content = GetTemplateContent(None, template_content, None, details)        

    if alert == "mail":
        meta = GetTemplateContent(None, subject, None, details)        

    if alert == "sms":
        content = utils.HtmlToTxt(content)        
        meta = SmsCreditMessage(content)

    if alert == "letter":
        meta = 'מכתב'.decode('utf-8')

    return {'content': content, 'meta': meta}    

@bottle.get("/parseAlertTemplate")
def parseAlertTemplate():
    params = bottle.request.query
    details = json.loads(params.details)
    return resolveAlertTemplate(params.path, params.alert, details, params.content, params.mail_subject)

@bottle.get("/getServiceReminderData")
def getServiceReminderData():     
    params = bottle.request.query
    tenants_from_building_id = params.tenants_from_building_id
    tenants_from_building_id = int(tenants_from_building_id) if len(tenants_from_building_id) else 0

    service_data = resolveAlertTemplate(params.path, params.alert, json.loads(params.details), file(os.path.join(params.path, params.alert + '.htm').replace('\\', '/')).read())
    entities = GetMultiTypeElements(True, tenants_from_building_id)
    service_data["entities"] = entities

    return service_data

def sendAlert(alertContent, alertMetaData, alertType, alertDestination, buildingName, recepientName, recepientType, source, external_folder=""):

    if alertType == 0:
        alerters.Alerter.SmsAlert(source, alertDestination, alertContent) 
        print 'send sms'
    if alertType == 1:
        alerters.Alerter.MailAlert(source, alertDestination, alertContent, alertMetaData, external_folder)
        print 'send mail'        
    if alertType == 2:
        print 'send letter'
        alertContent = '<div class="sam_alert">' + alertContent
        alertContent = alertContent + '<br/><br/><br/><br/><br/><br/><br/><br/><br/><br/><br/><br/></div>'

    storeAlertToHistory(alertContent, alertMetaData, alertType, alertDestination, buildingName, recepientName, recepientType, source, external_folder)

def storeAlertToHistory(alertContent, alertMetaData, alertType, alertDestination, buildingName, recepientName, recepientType, source, external_folder=""):
    utils.Md(utils.config.historyDir)
    tmpFile = utils.CreateTempFile(dir=utils.config.historyDir)

    with open(tmpFile, "wb") as fpo:
        fpo.write(alertContent.encode('utf-8'))

    info_db = sqlite3.connect(utils.DB_INFO)    
    with info_db as connection:
        cursor=connection.cursor()

        cursor.execute('''
        INSERT INTO alerts (recepient_name, building_name, recepient_type, path_to_file, alert_type, meta_data, destination, source, external_folder) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
        ''', (recepientName, buildingName, recepientType, tmpFile, alertType, alertMetaData, alertDestination, source, external_folder))    


@bottle.post("/upload")
def do_upload():    
    uploaded = []
    uploaded_folder = bottle.request.forms.uploaded_folder

    utils.Md('attachments')

    tmpFolder = utils.CreateTempFolder(dir='attachments') if not len(uploaded_folder) else os.path.join('attachments', uploaded_folder)       
    tmpFolder = tmpFolder.encode('utf-8')
    utils.Md(tmpFolder)

    for data in bottle.request.files.dict["data"]:            
        if data and data.file:  

            raw_in_bytes = data.file.read() # This is dangerous for big files
            bytes_size = len(raw_in_bytes)                        

            killobytes_size = 1 if bytes_size <= 1024 else  int(math.ceil(bytes_size/1024.0))

            filename = data.filename

            with open(os.path.join(tmpFolder, filename).decode('utf-8'),'wb') as open_file:
                open_file.write(raw_in_bytes)  

            uploaded.append( {'size': killobytes_size,
                              'name': filename
                              } )

    return json.dumps(
        {
            'files': uploaded,
            'folder': tmpFolder
        })

#sends a single alert per tenant based on a template file
@bottle.get("/sendTemplateAlert")
def sendTemplateAlert(): 
    alertsTypeOf = {
        'sms': 0,
        'mail': 1,
        'letter': 2
    }

    params = bottle.request.query     
    tenant_details = json.loads(params.details)
    alert = params.alert
    subject = params.subject
    worker_id = params.worker_id
    tenant_id = params.tenant_id
    tenant_type = int(params.tenant_type)
    template_content = params.template_content        
    tenant_phones = params.tenant_phones
    tenant_mails = params.tenant_mails

    resolved = resolveAlertTemplate(params.path, alert, tenant_details, template_content)        
    fileContent, metaData = resolved["content"], resolved["meta"] 

    #nothing to send
    if not fileContent:
        return    

    source = db_helper.GetSourceAlertsInfo('worker', worker_id)
    dest = [d for d in db_helper.GetDestinationAlertsInfo('tenant', tenant_id)]

    assert len(dest) == 1
    dest = dest[0]
    
    #override phones and mails with details from GUI
    dest['phones'] = db_helper._resolve_phones(tenant_phones)
    dest_emails = tenant_mails.split(', ')        
    dest['emails'] = [] if len(dest_emails) == 1 and dest_emails[0] == '' else dest_emails    

    if alert == 'sms':
        #if source or destination is missing a phone, do not send
        if not len(dest["phones"]) or not source["phone"]:
            return
        destinations = dest["phones"]
        source = source["phone"]

    elif alert == 'mail':
        if not len(dest["emails"]) or not source["email"]:
            return
        
        metaData = GetTemplateContent(None, subject, None, tenant_details)
        
        destinations = dest["emails"]
        source = source["email"]

    elif alert == 'letter':        
        destinations = [dest["building"]]
        source = ""

    if tenant_type == 1:        
        recepient_type = 4
    elif tenant_type == 2:        
        recepient_type = 5
    else:
        recepient_type = 3

    for destination in destinations:
        sendAlert(fileContent, metaData, alertsTypeOf[alert], destination, dest["building"], dest["name"], recepient_type, source)


if __name__ == '__main__':

    #enabling bottle to receive large messages
    #http://stackoverflow.com/questions/16865997/python-bottle-module-causes-error-413-request-entity-too-large

    bottle.BaseRequest.MEMFILE_MAX = 1024 * 1024     
    utils.UpdateSamProcess(os.getpid())        
    db_helper.PrepareDataBases()
    print 'start: %s' % datetime.datetime.now()
    db_data = excel_helper.BuildFromScratch(fromDir = utils.config.rootBuildingsDir)
    db_helper.UpdateDataBase(db_data)
    print 'end: %s' % datetime.datetime.now() 

    bottle.run(port=3389, host='0.0.0.0', server='paste')
