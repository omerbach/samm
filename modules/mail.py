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
#https://github.com/sendgrid/sendgrid-python/blob/master/use_cases/attachment.md

from sendgrid.helpers.mail import ( Mail, Attachment, FileContent, FileName, FileType, Disposition, ContentId )

from sendgrid import SendGridAPIClient
import base64
import utils
 
#will use send grid only for attacments for now
def SendGrid(to, fromMail, subject, mailContent, html, attachments=[], inlineImages=[]):

    success = True
    desc = 'Status: '

    to_emails = [ (emailAddr, emailAddr) for emailAddr in to ]

    message = Mail(
        from_email=fromMail.encode('utf8'),
        to_emails=to_emails,
        subject=subject.encode('utf8'),
        html_content=mailContent.encode('utf8'))

    for file_path in attachments:
        with open(file_path, 'rb') as f:
            data = f.read()
            f.close()
        encoded = base64.b64encode(data).decode()
        attachment = Attachment()
        attachment.file_content = FileContent(encoded)
        attachment.file_type = FileType('application/pdf')
        attachment.file_name = FileName(os.path.basename(file_path))
        attachment.disposition = Disposition('attachment')
        attachment.content_id = ContentId('Example Content ID')
        message.add_attachment(attachment)

    try:
        sg = SendGridAPIClient(utils.config.mailApiKey)
        response = sg.send(message)
        status_code = response.status_code
        desc += str(status_code)

    except Exception as e:
        desc += (str(e))
        success = False

    return success, desc

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

        # always use sendGrid. In the past, we used it only for attachments
        if True:
            sucess, desc = SendGrid(to, fromMail, subject, message, html, attachments, inlineImages)
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
            
        return (sucess, desc)

    
if __name__ == '__main__':
           
    cmdLineParser = argparse.ArgumentParser(description = "Sends mail by demand")
    cmdLineParser.add_argument('-t', '--to', nargs='*')
    cmdLineParser.add_argument('-s', '--subject')
    cmdLineParser.add_argument('-bt', '--body-text')  
    cmdLineParser.add_argument('-ht', '--html', action='store_true')
    cmdLineParser.add_argument('-f', '--files', nargs='*', help='attachments')           
    cmdLineParser.add_argument('-i', '--inline-images', nargs='*', help='images to be embedded')           

    cmdLine = cmdLineParser.parse_args()            
    
    m = MailGunMail()
    m.send(['blblb'], 'omerba@gmail.com', 'yadyad', '<strong>and easy to do anywhere, even with Python</strong>', True)
    #m.send(cmdLine.to, cmdLine.subject, cmdLine.body_text, cmdLine.html, cmdLine.files, cmdLine.inline_images)
