# -*- coding: utf8 -*-  

import os
import argparse
import requests

#https://github.com/sendgrid/sendgrid-python
import sendgrid

import utils
 
#will use send grid only for attacments for now
def SendGrid(to, fromMail, subject, mailContent, html, attachments=[], inlineImages=[]):  
    #to be called from a data base
    sg = sendgrid.SendGridClient('#####', '#####')
    message = sendgrid.Mail()
    message.add_to(to)
    message.set_subject(subject)    
    message.set_html(mailContent)            
    message.set_from(fromMail)    
    
    for attach in attachments:                
        attach = attach.replace('\\', '/')            
        message.add_attachment(os.path.basename(attach), 
                               attach)            
    return    
    status, msg = sg.send(message)
    return msg
        
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
                        
        assert not isinstance(to, basestring), 'sendMail expects a list not a string, please correct'
        return
        
        die()
        
        if len(attachments):
            response = SendGrid(to, fromMail, subject, message, html, attachments, inlineImages)
        else:
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
