# -*- coding: utf8 -*-  

import argparse
import requests
import HTMLParser

import utils
    
class BaseSmS(object):    
    def __init__(self, sendUrl, balanceUrl):        
        #for now our sms providers use the same link for send and credit request , but this could change 
        self.sendUrl = sendUrl
        self.balanceUrl = balanceUrl        
    
    
class SmartSmS(BaseSmS):
    def __init__(self):                  
        super(SmartSmS, self).__init__( "http://smartsms.co.il/member/http_sms_api.php", "http://smartsms.co.il/member/http_sms_api.php")
        
    def credit(self):
        try:
            from BeautifulSoup import BeautifulSoup
            
            phone, message = '03111111', 'dummy msg'
            to = ''.join(c for c in phone if c.isdigit())
            #replace 0 with international prefix
            to = "972"+ to[1:]        
            
            response = requests.post(url=self.sendUrl,                                
                    data={                    
                        "UN": utils.config.smsUser,
                        "P": utils.config.smsPassword,
                        "SA": utils.config.companyPhone,
                        "DA": '9723111111',
                        #get rid of bom
                        "M": message[1:] if message.startswith(u'\ufeff') else message                 
                        }
                    )                           
            
            #http://stackoverflow.com/questions/2474971/from-escaped-html-to-regular-html-python
            #convert a string with HTML entity codes (e.g. &lt; &amp;) to a normal string (e.g. < &)
            #http://docs.python.org/2/library/xml.sax.utils.html#xml.sax.saxutils.unescape
            
            h= HTMLParser.HTMLParser()
            unescapedData = h.unescape(response.text)
    
            soup = BeautifulSoup(unescapedData)
            credit = soup.find('credit').getText()
            return int(credit)
        except:
            return 0
            
    def send(self, sorcePhone, destPhone, message):        
        to = ''.join(c for c in destPhone if c.isdigit())
        
        return 50000
    
        die()
        
        #replace 0 with international prefix
        to = "972"+ to[1:]        
        
        response = requests.post(url=self.sendUrl,                                
                data={                    
                    "UN": utils.config.smsUser,
                    "P": utils.config.smsPassword,
                    "SA": sorcePhone,
                    "DA": to,
                    #get rid of bom
                    "M": message[1:] if message.startswith(u'\ufeff') else message                 
                    }
                )
        
        assert 'credit' in response.text, response.text
        return response                

class MicroPay(BaseSmS):
    def __init__(self):                  
        super(MicroPay, self).__init__( "http://www.micropay.co.il/ExtApi/ScheduleSms.php", "http://www.micropay.co.il/ExtApi/ScheduleSms.php")
        
    def credit(self):
        
        #return 50000
    
        #die()
                
        
        response = requests.get(url=self.balanceUrl,                                
                params={ 
                    "uid": 3395,                    
                    "un": utils.config.smsUser,
                    "type": "sms",                    
                    "get": 1,
                    "act": "credit"                    
                    }
                )
                
        try:
            balance = int(response.text)  
        except:
            balance = 0
        
        return balance
            
    def send(self, sorcePhone, destPhone, message):        
        to = ''.join(c for c in destPhone if c.isdigit())
        fromPhone = ''.join(c for c in sorcePhone if c.isdigit())
        return 50000
    
        die()
                
        
        response = requests.post(url=self.sendUrl,                                
                data={ 
                    "uid": 3395,                    
                    "un": utils.config.smsUser,
                    "msglong": message,
                    "charset": "utf-8",
                    "post": 2,
                    "from": fromPhone,
                    "list": to
                    }
                )
                
        assert 'OK' in response.text, response.text
        return response                

class Ofrix(BaseSmS):
    def __init__(self):                  
        super(Ofrix, self).__init__( "http://api.inforu.co.il/SendMessageXml.ashx", "http://api.inforu.co.il/WebTools/GetUserQuota.ashx")
        
    def credit(self):
        try:
            from lxml import etree
            
            response = requests.post(url=self.balanceUrl,                                
                    data={                    
                        "UserName": utils.config.smsUser,
                        "Password": utils.config.smsPassword                    
                        }
                    )
            
            doc = etree.fromstring(response.text)
            status = doc.findall('Status')
            data = doc.findall('Data')
            
            assert len(status) == 1
            assert len(data) == 1
            
            assert int(status[0].text) == 1
            return int(float(data[0].text))
        
        except:
            return 0
            
    def send(self, sorcePhone, destPhone, message): 
        from lxml import etree
        
        to = ''.join(c for c in destPhone if c.isdigit())
        fromPhone = ''.join(c for c in sorcePhone if c.isdigit())        

        return 50000
    
        die()
               
        root = etree.Element('Inforu')
        user = etree.Element('User')       
        userName = etree.Element('Username')
        userName.text = utils.config.smsUser
        password = etree.Element('Password')
        password.text = utils.config.smsPassword
        user.append(userName)
        user.append(password)
        root.append(user)
        
        content = etree.Element('Content', Type="sms")
        msg = etree.Element('Message')
        msg.text = message
        content.append(msg)
        root.append(content)
        
        recipients = etree.Element('Recipients')
        phoneNumber = etree.Element('PhoneNumber')
        phoneNumber.text = to
        recipients.append(phoneNumber)
        root.append(recipients)
        
        settings = etree.Element('Settings')
        senderNumber = etree.Element('SenderNumber')
        senderNumber.text = fromPhone
        settings.append(senderNumber)
        root.append(settings)
        
        xmlMessage = etree.tostring(root, pretty_print=True)                
        
        response = requests.post(url=self.sendUrl, data={"InforuXML": xmlMessage} )
        
        doc = etree.fromstring(response.text)        
        status = doc.findall('Status')                
        assert len(status) == 1        
        
        assert int(status[0].text) == 1       
    
        return 5000

        
if __name__ == '__main__':   
    
    cmdLineParser = argparse.ArgumentParser(description = "Sends sms by demand")
    cmdLineParser.add_argument('-t', '--to', nargs='*')   
    cmdLineParser.add_argument('-m', '--message', default='testing123')    
    cmdLine = cmdLineParser.parse_args()            
    
    
    s = SmartSmS()
    for phone in cmdLine.to:
        s.send(phone, cmdLine.message)
