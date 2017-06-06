import os
import time
import utils
import requests
import alerters
import sms

import hgapi
import datetime
from collections import defaultdict
import configuration


t = str(datetime.datetime.now().time().replace(microsecond=0))
d = str(datetime.date.today())

clients = defaultdict(list)

repo = hgapi.hgapi.Repo('.')
customersRepositoryFiles = [f.replace('\\','/') for f in repo.hg_command('locate').split() if 'customer_specific' in f]

for f in customersRepositoryFiles:
    if 'debt.ini' in f:        
        c = configuration.Config(f)        
        smsProvider = eval('sms.%s(c)' % c.smsProvider)        
        clients[c.clientIdentifier].append(smsProvider.credit())
    if 'auth.txt' in f:
        expiry = utils.GetLicenseExpiration(f)
        clients[c.clientIdentifier].append(time.strftime('%Y-%m-%d', time.localtime(expiry)))        
         

message = alerters.Alerter.GetTemplateContent('web/templates/reports/customers_report.html',
                                              {'d': d,
                                               't': t,
                                               'clients': clients})  

response = requests.post(url="https://api.mailgun.net/v2/%s/messages" % utils.config.mailDomain,
                auth=("api", utils.config.mailApiKey),
                data={
                        "from" : 'sam@sam.sam',
                        "to" : 'omerbach@gmail.com',
                        "subject" : '%s - customers status report' % d,
                        "html" : message
                    }
                )

print response