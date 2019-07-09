# -*- coding: utf8 -*-  

import os
import argparse
import requests

#https://github.com/sendgrid/sendgrid-python
#https://github.com/sendgrid/sendgrid-python
#https://github.com/sendgrid/sendgrid-python/blob/master/use_cases/attachment.md
#https://github.com/sendgrid/sendgrid-python/blob/master/use_cases/README.md
#https://github.com/sendgrid/sendgrid-python/blob/master/use_cases/send_a_single_email_to_multiple_recipients.md
#https://stackoverflow.com/questions/40656019/python-sendgrid-send-email-with-pdf-attachment-file

from sendgrid.helpers.mail import Mail
from sendgrid import SendGridAPIClient

import utils
 
#will use send grid only for attacments for now
def SendGrid(to, fromMail, subject, mailContent, html, attachments=[], inlineImages=[]):

    status_code = 400

    try:
        sg = SendGridAPIClient(utils.config.mailApiKey)
        response = sg.send(message)
        status_code = response.status_code
    except Exception as e:
        print(str(e))

    return status_code
        
class MailGunMail(object):
   
    def _prepareFiles(self, attachments, inlines): 
        #attachment is the key specified by mailGun, can not use a multi dict in requests (see https://github.com/kennethreitz/requests/issues/367)
        #so mailGun excepts attachment[1],attachment[2] etc..
        attachmentsDict =  dict(zip(["attachment[%d]" % (i+1) for i in range(len(attachments))],
                        [open(attachment) for attachment in attachments])) if attachments else {}
        
        inlinesDict = dict(zip(["inline[%d]" % (i+1) for i in range(len(inlines))],
                        [open(inline) for inline in inlines])) if inlines else {}
        
        final = attachmentsDict.copy()
        final.update(inlinesDict)
                
        return final

    def send(self, to, fromMail, subject, message, html, attachments=[], inlineImages=[]):

        return
        assert not isinstance(to, basestring), 'sendMail expects a list not a string, please correct'

        if len(attachments):
            response = SendGrid(to, fromMail, subject, message, html, attachments, inlineImages)
        else:
            return
            me = fromMail
            recepients = ';'.join(to)
            
            response = requests.post(url="https://api.mailgun.net/v2/%s/messages" % utils.config.mailDomain,
                    auth=("api", utils.config.mailApiKey),
                    data={
                            "from" : me,
                            "to" : recepients,
                            "subject" : subject,
                            "html" if html else "text" : message
                        }
                    )
            
        return response

    
if __name__ == '__main__':
           
    cmdLineParser = argparse.ArgumentParser(description = "Sends mail by demand")
    cmdLineParser.add_argument('-t', '--to', nargs='*')
    cmdLineParser.add_argument('-s', '--subject')
    cmdLineParser.add_argument('-bt', '--body-text')  
    cmdLineParser.add_argument('-ht', '--html', action='store_true')
    cmdLineParser.add_argument('-f', '--files', nargs='*', help='attachments')           
    cmdLineParser.add_argument('-i', '--inline-images', nargs='*', help='images to be embedded')           
    cmdLineParser.add_argument('-p', '--providers', nargs='*', default = MailProvidersList)     
        
    cmdLine = cmdLineParser.parse_args()            
    
    m = MailGunMail()
    m.send(cmdLine.to, cmdLine.subject, cmdLine.body_text, cmdLine.html, cmdLine.files, cmdLine.inline_images)
