# -*- coding: utf8 -*-  

import sqlite3
import datetime

import utils
import excel_utils
import elements

TENANT_OWNER = 1
TENANT_RENTER = 2

def GetBuildingDataBaseId(building):
    building_db_id = 0
    info_db = sqlite3.connect(utils.DB_INFO)

    #check if building exists by name kk
    with info_db as connection:
        cursor=connection.cursor()
        cursor.execute('''
        SELECT building_id from buildings where name = ?
        ''', ((building.building_name),) )

        res = cursor.fetchone()
        if res:
            building_db_id, = res

    return building_db_id
#eerer
def UpdateExistingBuilding(building, building_db_id):

    info_db = sqlite3.connect(utils.DB_INFO)
    with info_db as connection:
        cursor=connection.cursor()

        cursor.execute('''
        UPDATE buildings 
        SET name = ?, based_on_file = ?, updated = ?
        WHERE building_id = ?
        ''', (building.building_name, ','.join(building.based_on_files), datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S"), building_db_id) )

def GetApartmentTenantsDataBaseIdByType(app, building_db_id):
    info_db = sqlite3.connect(utils.DB_INFO)

    #check if tenants exist by apartment (could be maximum 2: renter and owner
    with info_db as connection:
        cursor=connection.cursor()

        cursor.execute('''
        SELECT tenant_type, tenant_id FROM tenants WHERE apartment_number = ? AND building_id = ?
        ''', (app.apartment_number, building_db_id ) )

        return {tenant_type: tenant_id for (tenant_type, tenant_id) in cursor.fetchall()}

def UpdateExistingTenants(app, building_db_id, tenantIdOf):

    tenantsToUpdate = 0
    if app.renter:
        tenantsToUpdate += 1
    if app.owner:
        tenantsToUpdate += 1

    #could be no tenants data to update at all, only debts
    if tenantsToUpdate:
        #same tenants number, update type to type
        if tenantsToUpdate == len(tenantIdOf):
            #found 1 tenant in the excel
            if tenantsToUpdate == 1:
                #renter in excel
                if app.renter:
                    #renter in datbase
                    if tenantIdOf.get(TENANT_RENTER, None):
                        UpdateExistingTenant(app, app.renter, tenantIdOf[TENANT_RENTER])
                    #owner in datbase
                    else:
                        UpdateExistingTenant(app, app.renter, tenantIdOf[TENANT_OWNER])

                    #renter in database, insert a blank owner record
                    InsertNewTenant(building_db_id, app, elements.Person(), TENANT_OWNER)

                #owner in excel
                elif app.owner:
                    #renter in datbase
                    if tenantIdOf.get(TENANT_RENTER, None):
                        UpdateExistingTenant(app, app.owner, tenantIdOf[TENANT_RENTER])
                    #owner in datbase
                    else:
                        UpdateExistingTenant(app, app.owner, tenantIdOf[TENANT_OWNER])


            #when there is 2 then it is easy, one per renter, one per owner
            else:
                UpdateExistingTenant(app, app.owner, tenantIdOf[TENANT_OWNER])
                UpdateExistingTenant(app, app.renter, tenantIdOf[TENANT_RENTER])

        #owner and renter in database, only one tenant found in excel
        elif tenantsToUpdate < len(tenantIdOf):
            #update owner and delete renter
            if app.owner:
                DeleteTenant(tenantIdOf[TENANT_RENTER])
                UpdateExistingTenant(app, app.owner, tenantIdOf[TENANT_OWNER])
            else:
                #if there is only a renter this is probably a bug, in this case update owner as an empty person
                UpdateExistingTenant(app, elements.Person(), tenantIdOf[TENANT_OWNER])
                UpdateExistingTenant(app, app.renter, tenantIdOf[TENANT_RENTER])


        #owner in database, owner and renter to update, so update owner and add renter
        elif tenantsToUpdate > len(tenantIdOf):
            UpdateExistingTenant(app, app.owner, tenantIdOf[TENANT_OWNER])
            InsertNewTenant(building_db_id, app, app.renter, TENANT_RENTER)

    UpdateDebts(app, building_db_id)

def ClearBuildingDebts(building_db_id):
    info_db = sqlite3.connect(utils.DB_INFO)
    with info_db as connection:
        cursor=connection.cursor()
        cursor.execute('DELETE FROM debts WHERE building_id = ?', (building_db_id, ) )

def UpdateDebts(app, building_db_id):

    default_desc = 'מיסי ועד'.decode('utf-8')
    debts = []
    for d, excelCellInfo in app.excelCellInfoPerDate.items():
        debts.append((
                building_db_id,
                app.apartment_number,
                d,
                excelCellInfo.payment_details.debt,
                excelCellInfo.payment_details.expected_payment,
                getattr(excelCellInfo.payment_details, 'debt_type', 1),
                getattr(excelCellInfo.payment_details, 'debt_description', default_desc)
            ))


    if len(debts):

        info_db = sqlite3.connect(utils.DB_INFO)
        with info_db as connection:
            cursor=connection.cursor()

            #insert current ones
            cursor.executemany('''
            INSERT INTO debts (building_id, apartment_number, debt_date, amount, expected, debt_type, description) 
            VALUES (?, ?, ?, ?, ?, ?, ?)
            ''', debts )


def UpdateOptOuts(phones):

    if len(phones):
        info_db = sqlite3.connect(utils.DB_INFO)
        with info_db as connection:
            cursor = connection.cursor()

            cursor.execute('DELETE FROM sms_opt_outs')

            # insert current ones
            cursor.executemany('''
            INSERT INTO sms_opt_outs (mobile) 
            VALUES (?)
            ''', [(p,) for p in phones])

def UpdateExistingTenant(app, person, tenant_db_id):

    info_db = sqlite3.connect(utils.DB_INFO)

    defacto = False
    if hasattr(person, 'defacto'):
        defacto = person.defacto

    focal_point = False
    if hasattr(person, 'focal_point'):
        focal_point = person.focal_point

    with info_db as connection:
        cursor=connection.cursor()

        cursor.execute('''
        UPDATE tenants 
        SET name = ?, mails = ?, phones = ?, defacto = ?, focal_point = ?
        WHERE tenant_id = ?
        ''', (person.name, ', '.join(person.mails), ', '.join(person.phones), defacto, focal_point, tenant_db_id) )

        if len(app.dynamicData):

            app.dynamicData['tenant_id'] = tenant_db_id

            for field_name, field_value in app.dynamicData.items():
                cursor.execute('''
                INSERT INTO dynamic_extra_tenant_data (%s)
                VALUES (%s)
                ''' % (','.join(app.dynamicData), ','.join(['?' for i in app.dynamicData]) ), app.dynamicData.values())





def InsertNewTenants(building_db_id, app):
    #a renter with no owner, a case which should not be. In this case enter a blank owner
    if app.renter:
        InsertNewTenant(building_db_id, app, app.renter, TENANT_RENTER)
        if not app.owner:
            InsertNewTenant(building_db_id, app, elements.Person(), TENANT_OWNER)

    if app.owner:
        InsertNewTenant(building_db_id, app, app.owner, TENANT_OWNER)

    UpdateDebts(app, building_db_id)

def InsertNewTenant(building_db_id, app, person, tenant_type):
    info_db = sqlite3.connect(utils.DB_INFO)

    defacto = False
    if hasattr(person, 'defacto'):
        defacto = person.defacto

    focal_point = False
    if hasattr(person, 'focal_point'):
        focal_point = person.focal_point

    with info_db as connection:
        cursor=connection.cursor()

        cursor.execute('''
        INSERT INTO tenants (building_id, apartment_number, tenant_type, defacto, focal_point, name, phones, mails) VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        ''', (building_db_id, app.apartment_number, tenant_type, defacto, focal_point, person.name, ', '.join(person.phones), ', '.join(person.mails))
              )



def DeleteTenant(tenant_db_id):
    info_db = sqlite3.connect(utils.DB_INFO)
    with info_db as connection:
        cursor=connection.cursor()

        cursor.execute('''
        DELETE FROM tenants WHERE tenant_id = ?
        ''', (tenant_db_id, ))

def InsertNewBuilding(building):
    info_db = sqlite3.connect(utils.DB_INFO)

    with info_db as connection:
        cursor=connection.cursor()

        cursor.execute('''
        INSERT INTO buildings (name, based_on_file) VALUES (?, ?)
        ''', (building.building_name, ','.join(building.based_on_files) ) )

        building_id = cursor.lastrowid

    return building_id


def UpdateDataBase(data):

    optOutPhones = []

    #building_name -> building obj
    for building_name, building in data.items():

        building_db_id = GetBuildingDataBaseId(building)
        new_building = building_db_id == 0

        #new building, add building and apartment tenants
        if new_building:
            building_db_id = InsertNewBuilding(building)

        #clear existing debts each time
        #in the other tables, there is a unique id which is used across the product, for example a tenant id is used in
        #service requests, so when reading the excel again, we do not delete a tenant but updating the details on the same
        #id, but in debts, there is no unique id and more over, we want to delete the old debts and inserting the new ones
        ClearBuildingDebts(building_db_id)

        for apartment_number, app in building.apartmentOf.items():
            print 'renter: ', app.renter.phones if app.renter else []
            print 'owner: ',app.owner.phones if app.owner else []
            tmp =   app.renter.phones if app.renter else [] + app.owner.phones if app.owner else []
            print 'combined: ', tmp
            optOutPhones += [''.join(c for c in t if c.isdigit()) for t in tmp]

            u1 = [u'050-2020151']
            u2 = [u'052-2510072']
            d = u1 + u2
            #print d
            #die()

            #new building, add building and apartment tenants
            if new_building:
                InsertNewTenants(building_db_id, app)

            else:
                #assuming apartments are not deleted, but can only be added
                #check if tenants exist by apartment (could be maximum 2: renter and owner)
                tenantIdOf = GetApartmentTenantsDataBaseIdByType(app, building_db_id)

                #an existing building which has this apartment
                if len(tenantIdOf):
                    UpdateExistingTenants(app, building_db_id, tenantIdOf)

                #appartment does not exist for this building, add tenants
                else:
                    InsertNewTenants(building_db_id, app)

        if not new_building:
            UpdateExistingBuilding(building, building_db_id)

        print building_db_id, building_name, datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        print '****************************************************'
        print
        print

    print len(optOutPhones), optOutPhones
    UpdateOptOuts(optOutPhones)

def GetProfessionalAlertsInfo(professional_id):
    info_db = sqlite3.connect(utils.DB_INFO)
    with info_db as connection:
        cursor=connection.cursor()
        cursor.execute('''
        SELECT p.name, p.phones, p.mails		
        FROM professionals as p
        WHERE p.professional_id = ?
        ''', (professional_id,) )

        return [{
                'recepient_name': professional_name,
                'recepient_phones': professional_phones,
                'recepient_emails': professional_mails,
                'recepient_type': 1,
                'recepient_building': "" }  for  professional_name, professional_phones, professional_mails in cursor.fetchall()]

def GetWorkerAlertsInfo(worker_id):
    info_db = sqlite3.connect(utils.DB_INFO)
    with info_db as connection:
        cursor=connection.cursor()
        cursor.execute('''
        SELECT w.name, w.phones, w.mails		
        FROM workers as w
        WHERE w.worker_id = ?
        ''', (worker_id,) )

        return [{
                'recepient_name': worker_name,
                'recepient_phones': worker_phones,
                'recepient_emails': worker_mails,
                'recepient_type': 2,
                'recepient_building': "" }  for  worker_name, worker_phones, worker_mails in cursor.fetchall()]

#source is usualy a worker
#anyhow this function should return a single email and a single phone
def GetSourceAlertsInfo(element_type, element_id):

    source_phone = None
    source_email = None

    if element_type == 'tenant':
        alertsData = GetBuildingTenantsAlertsInfo(element_id, None)
    elif element_type == 'worker':
        alertsData = GetWorkerAlertsInfo(element_id)
    elif element_type == 'professional':
        alertsData = GetProfessionalAlertsInfo(element_id)
    else:
        assert False, 'unsupported source type'

    assert len(alertsData) == 1
    alertsData = alertsData[0]

    source_phones = alertsData["recepient_phones"].split(', ')
    source_phones = [] if len(source_phones) == 1 and source_phones[0] == '' else source_phones
    source_emails = alertsData["recepient_emails"].split(', ')
    source_emails = [] if len(source_emails) == 1 and source_emails[0] == '' else source_emails

    #if source has multiple phones, get the first cell phone
    #if no cell phone, just get the first one (a source cell phone can be not valid....)
    if len(source_phones):
        if len(source_phones) == 1:
            source_phone = source_phones[0]
        else:
            for p in source_phones:
                if p.startswith('05'):
                    source_phone = p
                    break
        #no cell phone, just pick the first one
        if not source_phone:
            source_phone = source_phones[0]

    #if source has multiple emails, just pick the first one
    if len(source_emails):
        source_email = source_emails[0]

    return {'phone': source_phone, 'email': source_email}

def _resolve_phones(phones):
    phones = phones.split(', ')
    phones = [] if len(phones) == 1 and phones[0] == '' else phones
    phones = [''.join(c for c in phone if c.isdigit()) for phone in phones]
    phones = [phone for phone in phones if phone.startswith('05') and len(phone) == 10]
    return phones

#destination can be building, tenant, professional and worker
#destination should return a building also to be logged in alerts data base
#anyhow this function should return a list of objects,
#each one has the following properties: name, building, phones(only valid cell phones), mails and type
def GetDestinationAlertsInfo(element_type, element_id, building_name=""):

    if element_type == 'building':
        alertsData = GetBuildingTenantsAlertsInfo(None, element_id)
        #when destination is a building we send per each tenant so store the alert as tenant type
        element_type = 0
    elif element_type == 'building_owners':
        alertsData = GetBuildingTenantsAlertsInfo(None, element_id, 1)
        #when destination is a building we send per each tenant so store the alert as tenant type
        element_type = 0
    elif element_type == 'building_renters':
        alertsData = GetBuildingTenantsAlertsInfo(None, element_id, 2)
        #when destination is a building we send per each tenant so store the alert as tenant type
        element_type = 0
    elif element_type == 'building_defacto':
        alertsData = GetBuildingTenantsAlertsInfo(None, element_id, 0, True)
        #when destination is a building we send per each tenant so store the alert as tenant type
        element_type = 0
    elif element_type == 'tenant':
        alertsData = GetBuildingTenantsAlertsInfo(element_id, None)
        element_type = 0
    elif element_type == 'worker':
        alertsData = GetWorkerAlertsInfo(element_id)
        element_type = 2
    elif element_type == 'professional':
        alertsData = GetProfessionalAlertsInfo(element_id)
        element_type = 1
    else:
        assert False, 'unsupported alert destination type'

    for ad in alertsData:
        dest_phones = _resolve_phones(ad["recepient_phones"])
        dest_emails = ad["recepient_emails"].split(', ')
        dest_emails = [] if len(dest_emails) == 1 and dest_emails[0] == '' else dest_emails
        dest_name = ad["recepient_name"]
        #if the element has a building use it, else use the supplied one
        dest_building = ad["recepient_building"] if len(ad["recepient_building"]) else building_name
        dest_type = ad["recepient_type"]

        yield {
            "name": dest_name,
            "building": dest_building,
            "phones": dest_phones,
            "emails": dest_emails,
            "type": dest_type
        }


def GetBuildingTenantsAlertsInfo(tenant_id, building_id, tenant_type=None, defacto=None):

    assert building_id or tenant_id

    info_db = sqlite3.connect(utils.DB_INFO)
    parameters  = []
    query ='''
        SELECT t.name, t.phones, t.mails, b.name, t.tenant_type		
        FROM tenants as t, buildings as b
        WHERE b.building_id = t.building_id
        '''

    if tenant_id:
        query += " AND t.tenant_id = ?"
        parameters.append(tenant_id)

    if building_id:
            query += " AND b.building_id = ?"
            parameters.append(building_id)

    if tenant_type:
        query += " AND t.tenant_type = ?"
        parameters.append(tenant_type)

    if defacto:
        query += " AND t.defacto = ?"
        parameters.append(defacto)


    with info_db as connection:
        cursor=connection.cursor()
        cursor.execute(query, parameters)

        return [{
            'recepient_name': tenant_name,
            'recepient_phones': tenant_phones,
            'recepient_emails': tenant_mails,
            'recepient_type': 4 if tenant_type == 1 else 5,
            'recepient_building': building_name }  for  tenant_name, tenant_phones, tenant_mails, building_name, tenant_type in cursor.fetchall()]

def GetElementDestinations(entity_type, entity_id, entity_destination):
    info_db = sqlite3.connect(utils.DB_INFO)
    emails = []
    with info_db as connection:
        cursor=connection.cursor()

        cursor.execute('''
                SELECT %s		
                FROM %ss
                WHERE %s_id = ?
                ''' % (entity_destination, entity_type, entity_type), (entity_id,))

        for tenant_emails, in cursor.fetchall():
            emails_parsed = tenant_emails.split(', ')
            if len(emails_parsed) == 1 and emails_parsed[0] == '':
                continue

            emails.extend(tenant_emails.split(', '))

    return list(set(emails))


def PrepareDataBases():

    info_db = sqlite3.connect(utils.DB_INFO)

    with info_db as connection:
        cursor = connection.cursor()

        cursor.execute('''
        CREATE TABLE IF NOT EXISTS alerts (
         alert_id INTEGER PRIMARY KEY,
         recepient_type INTEGER NOT NULL, -- 0 tenant, 1 professional, 2 worker, 3 other
         recepient_name TEXT NOT NULL,
         building_name TEXT NOT NULL,
         path_to_file TEXT NOT NULL,
         alert_type INTEGER NOT NULL, -- 0 sms, 1 mail, 2 letter         
         meta_data TEXT NOT NULL,
         destination TEXT NOT NULL,
         source TEXT NOT NULL, -- phone, mail or empty string in a case of a letter
         updated DATETIME DEFAULT (datetime('now','localtime')),
         external_folder TEXT DEFAULT NULL
        )''')

        cursor.execute('''
        CREATE TABLE IF NOT EXISTS buildings (
         building_id INTEGER PRIMARY KEY,
         name TEXT NOT NULL,
         nick_name TEXT DEFAULT NULL,
         updated DATETIME DEFAULT (datetime('now','localtime')),
         based_on_file TEXT NOT NULL
        )''')

        cursor.execute('''
        CREATE TABLE IF NOT EXISTS debts (
         building_id INTEGER NOT NULL,
         apartment_number TEXT NOT NULL,
         debt_date DATE NOT NULL,
         amount INTEGER DEFAULT 0,
         expected INTEGER DEFAULT 0,
         debt_type INTEGER DEFAULT 1, -- 0 unknown, 1 ongoing, 2 special
         description TEXT DEFAULT NULL -- relevant for special debt cases                  
        )''')

        cursor.execute('''
        CREATE TABLE IF NOT EXISTS fields (
         field_id INTEGER PRIMARY KEY,
         excel_header TEXT NOT NULL,    
         field_type INTEGER DEFAULT 1, -- 1 general, 2 debt
         template_name TEXT DEFAULT NULL,
         comment TEXT DEFAULT NULL        
         )''')

        declareColumns = []
        cursor.execute('''SELECT template_name, field_type from fields''')
        for template_name, field_type in cursor.fetchall():
            declareColumns.append(',%s %s DEFAULT NULL' % (template_name, {1: 'TEXT', 2: 'INTEGER'}[field_type]))

        cursor.execute('''DROP TABLE IF EXISTS dynamic_extra_tenant_data''')
        cursor.execute('''
        CREATE TABLE dynamic_extra_tenant_data (
        tenant_id INTEGER NOT NULL        
        %s        
        )''' % ''.join(declareColumns))

        cursor.execute('''
        CREATE TABLE IF NOT EXISTS payments (
         payment_id INTEGER PRIMARY KEY,
         status INTEGER DEFAULT 1, -- 1 received, 2 deposit, 3 in_the_bank
         tenant_id INTEGER DEFAULT NULL,         
         building_id INTEGER DEFAULT NULL,
         acceptance_date DATE DEFAULT NULL,
         amount INTEGER DEFAULT 0,                  
         payment_type INTEGER DEFAULT 1, -- 1 cheque, 2 cash, 3 transfer
         worker_id INTEGER DEFAULT NULL,
         receipt TEXT DEFAULT NULL,
         tenant_cheque_identifier TEXT DEFAULT NULL,
         payment_approval TEXT DEFAULT NULL,         
         tenant_cheque_date DATE DEFAULT NULL,                  
         tenant_bank_account TEXT DEFAULT NULL,
         tenant_bank_branch TEXT DEFAULT NULL,         
         company_bank_account TEXT DEFAULT NULL,
         company_bank_branch TEXT DEFAULT NULL,                           
         deposit_date DATE DEFAULT NULL,         
         comment TEXT DEFAULT NULL,
         external_folder TEXT DEFAULT NULL
         )''')

        cursor.execute('''
        CREATE TABLE IF NOT EXISTS prevention (
         prevention_id INTEGER PRIMARY KEY,
         building_id INTEGER NOT NULL,
         description TEXT NOT NULL,         
         category TEXT DEFAULT NULL,
         worker_id INTEGER DEFAULT NULL,
         professional_id INTEGER DEFAULT NULL,
         months TEXT NOT NULL, -- comma separated 1,2,3-12,
         cost INTEGER DEFAULT 0,
         comment TEXT DEFAULT NULL
         )''')

        cursor.execute('''
        CREATE TABLE IF NOT EXISTS professionals (
         professional_id INTEGER PRIMARY KEY,
         name TEXT NOT NULL,
         fax TEXT DEFAULT NULL,
         category TEXT DEFAULT NULL,
         address TEXT DEFAULT NULL,
         phones TEXT DEFAULT NULL, -- comma separated
         mails TEXT DEFAULT NULL, -- comma separated
         company_person_id TEXT DEFAULT NULL,
         comment TEXT DEFAULT NULL 
         )''')

        cursor.execute('''
        CREATE TABLE IF NOT EXISTS service (
         service_id INTEGER PRIMARY KEY,
         description TEXT NOT NULL,         
         category TEXT DEFAULT NULL,
         building_id INTEGER DEFAULT NULL,
         tenant_id INTEGER DEFAULT NULL,
         worker_id INTEGER DEFAULT NULL,
         professional_id INTEGER DEFAULT NULL,
         status INTEGER DEFAULT 1, -- 1 new, 2 in_progress, 3 done
         start_date DATETIME DEFAULT (datetime('now','localtime')),
         end_date DATETIME DEFAULT NULL,
         cost INTEGER DEFAULT 0,
         comment TEXT DEFAULT NULL,
         reminders INTEGER DEFAULT 0,
         prevention_id INTEGER DEFAULT 0
         )''')

        cursor.execute('''
        CREATE TABLE IF NOT EXISTS templates (
         template_id INTEGER PRIMARY KEY,
         template_name TEXT DEFAULT NULL,
         updated DATETIME DEFAULT (datetime('now','localtime')),         
         comment TEXT DEFAULT NULL        
         )''')

        cursor.execute('''
        CREATE TABLE IF NOT EXISTS tenants (
         tenant_id INTEGER PRIMARY KEY,
         building_id INTEGER NOT NULL,
         apartment_number TEXT NOT NULL,
         tenant_type INTEGER DEFAULT 1, -- 0 unknown, 1 owner, 2 renter
         defacto INTEGER DEFAULT 1, -- 0 false, 1 true
         focal_point TEXT DEFAULT NULL,
         name TEXT NOT NULL,
         phones TEXT DEFAULT NULL, -- comma separated
         mails TEXT DEFAULT NULL -- comma separated
        )''')

        cursor.execute('''
        CREATE TABLE IF NOT EXISTS workers (
         worker_id INTEGER PRIMARY KEY,
         name TEXT NOT NULL,         
         fax TEXT DEFAULT NULL,
         title TEXT DEFAULT NULL,
         address TEXT DEFAULT NULL,
         phones TEXT DEFAULT NULL, -- comma separated
         mails TEXT DEFAULT NULL, -- comma separated
         person_id TEXT DEFAULT NULL,
         comment TEXT DEFAULT NULL         
         )''')

        cursor.execute('''
                CREATE TABLE IF NOT EXISTS sms_opt_outs (
                 mobile TEXT,
                 updated DATETIME DEFAULT (datetime('now','localtime'))     
                 )''')


def GetTableHeaders(db_table):
    names = []
    info_db = sqlite3.connect(utils.DB_INFO)
    #check if building exists by name
    with info_db as connection:
        cursor=connection.cursor()
        cursor.execute('''select * from %s''' % db_table)
        names = list(map(lambda x: x[0], cursor.description))

    return names
