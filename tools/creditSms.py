# -*- coding: utf8 -*-  
import datetime
import utils
import os

import sms
import utils
import alerters

smsProvider = eval('sms.%s()' % utils.config.smsProvider)
credit = smsProvider.credit()
t = str(datetime.datetime.now().time().replace(microsecond=0))
d = str(datetime.date.today())

message = alerters.Alerter.GetTemplateContent('web/templates/reports/sms_report.html',
                                              {'d': d,
                                               't': t,
                                               'sms_credit': utils.Commafy(credit),
                                               'sms_password': utils.config.smsPassword,
                                               'sms_mail': utils.config.smsMail,
                                               'sms_web_site': utils.config.smsWebSite(),
                                               'company_logo': utils.CustomerSignature()})

title = 'יתרת_סמסים'.decode('utf-8') + '.html'
with file(title, 'wb') as fpo:
    fpo.write(message.encode('utf-8'))
os.startfile(title)

