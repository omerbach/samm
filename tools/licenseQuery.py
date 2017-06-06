# -*- coding: utf8 -*-
import time
import datetime
import os

import bottle
import utils

authorized, expiry = utils.Authorize()

formattedExpiry = time.strftime('%Y-%m-%d', time.localtime(expiry))

if authorized:
    message = bottle.template('web/templates/reports/license_report', 
            date = formattedExpiry,                               
                               company_name = utils.config.companyName,                               
                               expiry = formattedExpiry)
else:
    message = bottle.template('web/templates/errors/error_customer_not_approved', 
            date = datetime.date.today().strftime("%d/%m/%Y"),                               
                               company_name = utils.config.companyName,
                               company_web_site = utils.config.companyWebSite,
                               company_logo = utils.CustomerSignature() )

title = 'license.html'
with file(title, 'wb') as fpo:
    fpo.write(message.encode('utf-8'))
os.startfile(title)