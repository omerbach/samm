# -*- coding: utf8 -*-  
import os
import fnmatch
import collections
import datetime
import time
import json
import shutil

import xlrd
import requests
import bottle

import utils
import sms
import mail  
    
class Alerter(object):
    
    WORKING_MODE_ONGOING_DEBTS_COLLECTION = 0
    WORKING_MODE_GENERAL_MAILING = 1
    WORKING_MODE_SPECIAL_DEBTS_COLLECTION = 2
    WORKING_MODE_HISTORY = 3
    WORKING_MODE_DEBTS_PERCENTAGE = 4
    WORKING_MODE_EVENTS = 5
    WORKING_MODE_OCCASIONAL_MESSAGE = 6
    
    @staticmethod
    def getExecutionDesc(executionMode):
        
        #.decode('utf-8') 
        if executionMode == Alerter.WORKING_MODE_ONGOING_DEBTS_COLLECTION:
            return u'איתור חובות'
                           
        elif executionMode == Alerter.WORKING_MODE_SPECIAL_DEBTS_COLLECTION:
            return u'גבייה מיוחדת'
            
        elif executionMode == Alerter.WORKING_MODE_GENERAL_MAILING:
            return u'דיוור כללי'
        
        elif executionMode == Alerter.WORKING_MODE_HISTORY:
            return u'היסטורית התראות'
        
        elif executionMode == Alerter.WORKING_MODE_DEBTS_PERCENTAGE:
            return u'אחוזי גביה'
        
        elif executionMode == Alerter.WORKING_MODE_EVENTS:
            return u'טיפול באירועים'
        
        elif executionMode == Alerter.WORKING_MODE_OCCASIONAL_MESSAGE:
            return u'הודעה מזדמנת'
        
        
            
        
    @staticmethod
    def coverage(coverageOf, requestParameters):                
                
        return Alerter.GetTemplateContent('web/templates/reports/coverage_report.html', None,
        {
            #general fields
            'date': datetime.date.today().strftime("%d/%m/%Y"),                                                                                             
            'company_name': utils.config.companyName,
            'company_mail': utils.config.companyMail,
            'company_mail_debts': utils.config.companyMailDebts,
            'company_web_site': utils.config.companyWebSite,                                                       
            'company_phone': utils.config.companyPhone,
            'company_fax': utils.config.companyFax,
            'company_address': utils.config.companyAddress,
            'current_month': int(datetime.datetime.now().month),
            'current_year': int(datetime.datetime.now().year),
            #specific fields            
            'executionType': Alerter.getExecutionDesc(requestParameters.mode),
            'coverageOf': coverageOf,
            #special fields (with !)
            'company_logo': utils.CustomerSignature()
        })
    
    @staticmethod
    def report(requestParameters, tenants, buildingNum, columns_toolTips = [], values_classes = [], total = None):                
        
        return Alerter.GetTemplateContent('web/templates/reports/executive_report.html', None, 
        {
            #general fields
            'date': datetime.date.today().strftime("%d/%m/%Y"),                                                                                             
            'company_name': utils.config.companyName,
            'company_mail': utils.config.companyMail,
            'company_mail_debts': utils.config.companyMailDebts,
            'company_web_site': utils.config.companyWebSite,                                                       
            'company_phone': utils.config.companyPhone,
            'company_fax': utils.config.companyFax,
            'company_address': utils.config.companyAddress,
            'current_month': int(datetime.datetime.now().month),
            'current_year': int(datetime.datetime.now().year),
            #specific fields
            'customerTemplatesDir': requestParameters.customerTemplatesDir,            
            'executionType': Alerter.getExecutionDesc(requestParameters.mode),
            'tenants': tenants,
            'buildingsNumber': buildingNum,
            'tenantsNumber': len(tenants),
            'year': requestParameters.year,
            'months': utils.HebrewMonths(','.join([str(month) for month in requestParameters.reportingMonths])),
            'total': total,
            'columns_toolTips': columns_toolTips, 
            'values_classes': values_classes,
            'formats': requestParameters.formats,
            #special fields (with !)
            'company_logo': utils.CustomerSignature(),
            #functions
            'Number': int,
            'Commafy': utils.Commafy,
            'UnCommafy': utils.UnCommafy,
            'Monthify': utils.Monthify
        })
        
    @staticmethod
    def PrintingDialog(billboardsOf, lettersOf):
        
        letters = [letter 
                           for hasOtherAlerts, keyToletterPerApp in sorted(lettersOf.items())
                           for key, letterPerApp in sorted(keyToletterPerApp.items())
                           for (app, name), letter in sorted(letterPerApp.items())]
        
        letters2 = [letter 
                           for hasOtherAlerts, keyToletterPerApp in sorted(lettersOf.items())
                           for key, letterPerApp in sorted(keyToletterPerApp.items())
                           for (app, name), letter in sorted(letterPerApp.items()) if not hasOtherAlerts]
        
        if letters:            
            newLetters = ['<hr class="no_print">%s<span class="page-break"></span>' % letter for letter in letters[:-1]]
            newLetters.append('<hr class="no_print">%s' % letters[-1])
            letters = ''.join(newLetters)
            
        if letters2:            
            newLetters2 = ['<hr class="no_print">%s<span class="page-break"></span>' % letter for letter in letters2[:-1]]
            newLetters2.append('<hr class="no_print">%s' % letters2[-1])
            letters2 = ''.join(newLetters2)
                
        return bottle.template('web/templates/reports/print_report', 
                               date = datetime.date.today().strftime("%d/%m/%Y"),
                               billboardsOf = billboardsOf,
                               lettersOf = lettersOf,
                               letters = letters,
                               lettersOfTenantsWithNoAlerts = letters2)
    
    @staticmethod
    def GetTemplateContent(templatePath, templateStr, kwargs):        
        if templatePath:            
            fp = None
            #microsoft word html templates are sometimes encoded with utf-16
            #remove all carridge returns, we do not need them and they sometimes fuck it up
            try:
                fp = open(templatePath).read().decode("utf-8").replace("\r\n", " ")
            except UnicodeDecodeError:
                try:
                    fp = open(templatePath).read().decode("utf-16").replace("\r\n", " ")
                except UnicodeDecodeError:
                    pass
            
            msg = bottle.template(fp,
                                  kwargs)
            return msg
        if templateStr:
            msg = bottle.template(templateStr,
                                kwargs)            
            return msg            


                
        
        
    #this is static cause it used out of Alerter object context upon toolTip requests
    @staticmethod
    def FormatAlertTemplate(path,   
                            templateStr,
                            description = '', 
                            building = '', 
                            name = '', 
                            appartment = '', 
                            months = '', 
                            year = int(datetime.datetime.now().year), 
                            payment = 0,                             
                            debt = 0,
                            previousDebt = 0,
                            totalDebt = 0,
                            mails = [], 
                            phones = [],
                            comment = "",
                            general = "",
                            event = "",
                            occasional = "",
                            subject = "",
                            monthsCount = "",
                            
                            tenant_name = "",
                            tenant_phones = "",
                            professional_name = "",
                            worker_name = "",
                            service_request_id = "",
                            service_request_description = "",
                            parking_debt = 0,
                            previous_debt_2012 = 0,
                            special = 0):
        
        if not path and not templateStr:            
            return ''                
        
        alertTemplateContent = Alerter.GetTemplateContent(path, templateStr,
                                                   {
                                                       #general fields
                                                       'date': datetime.date.today().strftime("%d/%m/%Y"),                                                                                             
                                                       'company_name': utils.config.companyName,
                                                       'company_mail': utils.config.companyMail,
                                                       'company_mail_debts': utils.config.companyMailDebts,
                                                       'company_web_site': utils.config.companyWebSite,                                                       
                                                       'company_phone': utils.config.companyPhone,
                                                       'company_fax': utils.config.companyFax,
                                                       'company_address': utils.config.companyAddress,
                                                       'previous_month': '%02d' % 12 if int(datetime.datetime.now().month) ==  1 else int(datetime.datetime.now().month) - 1,
                                                       'current_month': '%02d' % int(datetime.datetime.now().month),
                                                       'next_month': '%02d' % 1 if int(datetime.datetime.now().month) ==  12 else int(datetime.datetime.now().month) + 1,
                                                       'previous_year': int(datetime.datetime.now().year) - 1,                                                                            
                                                       'current_year': int(datetime.datetime.now().year),
                                                       'next_year': int(datetime.datetime.now().year) + 1,                                                       
                                                       #specific fields
                                                       'comment': comment,
                                                       'general': general,
                                                       'event': event,
                                                       'message': occasional,
                                                       'subject': subject,
                                                       'description': description,
                                                       'building': building,
                                                       'name': name,
                                                       #in case appartment is str in hebrew
                                                       'appartment': appartment.encode('utf-8'),
                                                       'months': utils.HebrewMonths(months),
                                                       'year': int(year),
                                                       'phones': ', '.join(phones),
                                                       'mails': ', '.join(mails),
                                                       'payment0': payment,
                                                       'payment': utils.Commafy(payment),
                                                       'payment2': utils.Commafy(payment * 2),
                                                       'payment3': utils.Commafy(payment * 3),
                                                       'payment4': utils.Commafy(payment * 4),
                                                       'payment5': utils.Commafy(payment * 5),
                                                       'payment6': utils.Commafy(payment * 6),
                                                       'payment7': utils.Commafy(payment * 7),
                                                       'payment8': utils.Commafy(payment * 8),
                                                       'payment9': utils.Commafy(payment * 9),
                                                       'payment10': utils.Commafy(payment * 10),
                                                       'payment11': utils.Commafy(payment * 11),
                                                       'payment12': utils.Commafy(payment * 12),
                                                       'debt': utils.Commafy(debt),
                                                       'previous_debt': utils.Commafy(previousDebt),
                                                       'total_debt': utils.Commafy(totalDebt),
                                                       'months_count': monthsCount,
                                                       #special fields (with !)
                                                       'company_logo': utils.CustomerSignature(),
                                                       'personal_signature' : utils.CompanySignature(),
                                                       #functions
                                                       'Number': int,
                                                       'Commafy': utils.Commafy,
                                                       'UnCommafy': utils.UnCommafy,
                                                       'Monthify': utils.Monthify,
                                                       'tenant_name': tenant_name,
                                                       'tenant_phones': tenant_phones,
                                                       'professional_name': professional_name,
                                                       'worker_name': worker_name,
                                                       'service_request_id': service_request_id,
                                                       'service_request_description': service_request_description,
                                                       'parking_debt': parking_debt,
                                                       'previous_debt_2012': previous_debt_2012,
                                                       'special': utils.Commafy(special)
                                                   })
                
        return alertTemplateContent    
    
    @staticmethod
    def FormatBillboardTemplate(customerTemplatesDir, 
                                description = '',
                                building = '',                                 
                                year = int(datetime.datetime.now().year),
                                tenants = []):                
        
        template = 'billboard.htm'
       
        debtsTenantsTableTemplate = 'web/tenants_tables/debts_tenants_table.html'
        paymentsTenantsTableTemplate = 'web/tenants_tables/payments_tenants_table.html'
        generalTenantsTableTemplate = 'web/tenants_tables/general_tenants_table.html'
        
        debtsTenantsTable = Alerter.GetTemplateContent(debtsTenantsTableTemplate, None, {'tenants': tenants}) if os.path.exists(debtsTenantsTableTemplate) else None
        paymentsTenantsTable = Alerter.GetTemplateContent(paymentsTenantsTableTemplate, None, {'tenants': tenants}) if os.path.exists(paymentsTenantsTableTemplate) else None
        generalTenantsTable = Alerter.GetTemplateContent(generalTenantsTableTemplate, None, {'tenants': tenants}) if os.path.exists(generalTenantsTableTemplate) else None
        
        
        billBoardMessage = Alerter.GetTemplateContent(os.path.join(customerTemplatesDir, template), None,
                                                   {
                                                       #general fields
                                                       'date': datetime.date.today().strftime("%d/%m/%Y"),                                                                                             
                                                       'company_name': utils.config.companyName,
                                                       'company_mail': utils.config.companyMail,
                                                       'company_mail_debts': utils.config.companyMailDebts,
                                                       'company_web_site': utils.config.companyWebSite,                                                       
                                                       'company_phone': utils.config.companyPhone,
                                                       'company_fax': utils.config.companyFax,
                                                       'company_address': utils.config.companyAddress,
                                                       'previous_month': '%02d' % 12 if int(datetime.datetime.now().month) ==  1 else int(datetime.datetime.now().month) - 1,
                                                       'current_month': '%02d' % int(datetime.datetime.now().month),
                                                       'next_month': '%02d' % 1 if int(datetime.datetime.now().month) ==  12 else int(datetime.datetime.now().month) + 1,
                                                       'previous_year': int(datetime.datetime.now().year) - 1,                                                                            
                                                       'current_year': int(datetime.datetime.now().year),
                                                       'next_year': int(datetime.datetime.now().year) + 1,
                                                       #specific fields
                                                       'description': description,
                                                       'building': building,                                                                                                              
                                                       'year': year,
                                                       #special fields (with !)
                                                       'company_logo': utils.CustomerSignature(),
                                                       'debts_tenants_table': debtsTenantsTable,
                                                       'payments_tenants_table': paymentsTenantsTable,
                                                       'general_tenants_table': generalTenantsTable,
                                                       #functions
                                                       'Commafy': utils.Commafy,
                                                       'UnCommafy': utils.UnCommafy,
                                                       'Monthify': utils.Monthify
                                                   })                
        return billBoardMessage
    
    
    @staticmethod
    def BillboardAlert(executionType, customerTemplatesDir, description, building, year, tenants):    
        billboardMessage = Alerter.FormatBillboardTemplate(customerTemplatesDir, description, building, year, tenants)
        return billboardMessage
        #for now, do not dump alerts for billboards
        #return Alerter.DumpBuildingAlert(dumpFolder, billboardMessage, building, 'שלט', description)
        
    @staticmethod
    def SmsAlert(sorcePhone, destPhone, smsMessage):                        
        smsProvider = eval('sms.%s()' % utils.config.smsProvider)        
        smsProvider.send(sorcePhone, destPhone, smsMessage)

    @staticmethod
    def MailAlert(sorceMail, mailAddress, mailBodyMessage, mailSubject, external_folder):
        attachments = []
        
        #important for send grid add attachment func which expects an str and not an unicode,
        #could be a problem when the path to new_sam is with non ascii characters, but we'll 
        #deal with that later
        external_folder = str(external_folder)
        
        if len(external_folder):
            attachments = [os.path.join(external_folder, attach) for attach in os.listdir(external_folder)]        
         
        mail.MailGunMail().send(to=[mailAddress], 
                                            fromMail = sorceMail,
                                            subject=mailSubject,
                                            message=mailBodyMessage, 
                                            html=True,
                                            attachments = attachments
                                            )          
         
         
                    
    @staticmethod
    def LetterAlert(executionType, customerTemplatesDir, letterMessage, building, appartment, description):
        return letterMessage        
    
    @staticmethod
    def DumpBuildingAlert(dumpFolder, msg, building, alert, description):
        
        historyFolder = utils.config.historyDir
        utils.Md(historyFolder)
    
        if len(description):
            fileName = '%s_%s_%s' % (alert.decode('utf-8'), building, description)
        else:
            fileName = '%s_%s' % (alert.decode('utf-8'), building)   
            
        f = utils.TidyFileName(fileName) + '.html.7z'        
        
        alerts = ('%sים' % alert).decode('utf-8')
        allAlertsDir = os.path.join(dumpFolder, alerts)
        alertsPerbuildingDir = os.path.join(allAlertsDir, building)
        
        for alertDestination in [alertsPerbuildingDir]:                        
            alertDestination = utils.Md(alertDestination)                        
            
            with gzip.open(os.path.join(historyFolder, alertDestination, f.decode('utf-8')), 'wb') as fpo:                                
                fpo.write(msg.encode('utf-8'))
                
        return msg
    
    @staticmethod
    def DumpTenantAlert(executionType, customerTemplatesDir, msg, building, appartment, name, alertDestination, alert, description):
        
        historyFolder = utils.config.historyDir                
        fileName = '%s.html' % alert
                
        now = datetime.datetime.now()
        curr_date = now.strftime("%Y-%m-%d")
        curr_time = now.strftime("%H-%M")
        
        dumpDir = os.path.join(utils.config.historyDir, building)        
        dumpDir = utils.Md(dumpDir)        
          
        fileName = os.path.join('%s^%s^%s^%s^%s^%s^%s^%s^%s.html' % (building, 
                                                             curr_date, 
                                                             curr_time, 
                                                             Alerter.getExecutionDesc(executionType), 
                                                             os.path.basename(customerTemplatesDir), 
                                                             appartment,
                                                             name[:35] if len(name) > 35 else name,
                                                             alert, 
                                                             alertDestination)).replace('\n', '')
        
        filePath = os.path.join(dumpDir, utils.TidyFileName(fileName))
        
        #filepath above 260 causes trouble
        if len(filePath) < 260:            
            with file(filePath, 'wb') as fpo:                                
                fpo.write(msg.encode('utf-8'))        
        
        return msg
        
    def tidyField(self, field):                
        if isinstance(field, unicode):
            return field.encode('utf-8')
        if isinstance(field, float):
            return str(int(field))
        return str(field)


if __name__ == '__main__':    
    pass
