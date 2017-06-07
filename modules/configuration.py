from ConfigParser import SafeConfigParser
import codecs

#testing
class Config(object):
    def __init__(self, configFile):
        self.parser = SafeConfigParser()
        # Open the file with the correct encoding
        #config.ini file is encoded with utf-8 with bom (saved by notepad) so use utf_8_sig for SafeConfigParser to ignore it
        with codecs.open(configFile, 'r', encoding='utf_8_sig') as f:
            self.parser.readfp(f)        

    def __str__(self):
        pass
    #helloe leoolsl sod osd
    #[file_system]
    @property
    def rootBuildingsDir(self):
        return self.parser.get('file_system', 'root_buildings_dir')
        
    @property
    def ongoingDebtsTemplatesDir(self):
        return self.parser.get('file_system', 'ongoing_debts_templates_dir')
    
    @property
    def specialDebtsTemplatesDir(self):
        return self.parser.get('file_system', 'special_debts_templates_dir')
    
    @property
    def generalMessagesTemplatesDir (self):
        return self.parser.get('file_system', 'general_messages_templates_dir')
    
    @property
    def eventsMessagesTemplatesDir (self):
        return self.parser.get('file_system', 'events_handling_templates_dir')
    
    @property
    def occasionalMessagesTemplatesDir (self):
        return self.parser.get('file_system', 'occasional_messaging_templates_dir')
    
    @property
    def historyDir (self):
        return self.parser.get('file_system', 'history_dir')
        

    #[excel]
    
    @property
    def excelPaymentFilePrefix(self):
        return self.parser.get('excel', 'excel_payment_file_prefix')
    
    @property
    def excelSpecialFilePrefix(self):
        return self.parser.get('excel', 'excel_special_file_prefix')
    
    @property
    def excelGeneralFilePrefix(self):
        return self.parser.get('excel', 'excel_general_file_prefix')
    
    @property
    def excelPaymentSheetPrefix(self):
        return self.parser.get('excel', 'excel_payment_sheet_prefix')
    
    @property
    def excelSpecialSheetPrefix(self):
        return self.parser.get('excel', 'excel_special_sheet_prefix')
    
    @property
    def excelGeneralSheetPrefix(self):
        return self.parser.get('excel', 'excel_general_sheet_prefix')
    
    #[company]
    
    @property
    def companyName(self):
        return self.parser.get('company', 'company_name')
    
    @property
    def companyLogo(self):
        return self.parser.get('company', 'company_logo')
    
    @property
    def companyWebSite(self):
        return self.parser.get('company', 'company_web_site')
    
    @property
    def companyPhone(self):
        return self.parser.get('company', 'company_phone')
    
    @property
    def companyMail(self):
        return self.parser.get('company', 'company_mail')
    
    @property
    def companyMailDebts(self):
        return self.parser.get('company', 'company_mail_debts')
    
    @property
    def companyFax(self):
        return self.parser.get('company', 'company_fax')
    
    @property
    def companyAddress(self):
        return self.parser.get('company', 'company_address')
    
    def companyPersonalSignature(self):
        return self.parser.get('company', 'company_signature')
    
    #[authentication]
    
    @property
    def clientIdentifier(self):
        return self.parser.get('authentication', 'identifier')
    
    #[alerts]        
    
    @property
    def smsProvider(self):
        return self.parser.get('alerts', 'sms_provider')
    
    def smsWebSite(self):
        return self.parser.get('alerts', 'sms_web_site')
    
    @property
    def smsMail(self):
        return self.parser.get('alerts', 'sms_mail')
    
    @property
    def smsUser(self):
        return self.parser.get('alerts', 'sms_user')
    
    @property
    def smsPassword(self):
        return self.parser.get('alerts', 'sms_password')
    
    @property
    def mailDomain(self):
        return self.parser.get('alerts', 'mail_domain')
    
    @property
    def mailApiKey(self):
        return self.parser.get('alerts', 'mail_api_key')
    
    @property
    def maiFromDebts(self):
        return self.parser.get('alerts', 'mail_from_debts')
    
    @property
    def mailFromSpecial (self):
        return self.parser.get('alerts', 'mail_from_special')
    
    @property
    def mailFromGeneral (self):
        return self.parser.get('alerts', 'mail_from_general')
    