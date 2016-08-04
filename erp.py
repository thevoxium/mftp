import requests
from os import environ as env
from bs4 import BeautifulSoup as bs
import sys
import re
import settings

ERP_HOMEPAGE_URL = 'http://erp.iitkgp.ernet.in/IIT_ERP3/welcome.jsp'
ERP_LOGIN_URL = 'http://erp.iitkgp.ernet.in/SSOAdministration/auth.htm'
ERP_SECRET_QUESTION_URL = 'http://erp.iitkgp.ernet.in/SSOAdministration/getSecurityQues.htm'
ERP_CDC_MODULE_URL = 'https://erp.iitkgp.ernet.in/IIT_ERP3/menulist.htm?module_id=26'
ERP_TPSTUDENT_URL = 'http://erp.iitkgp.ernet.in/TrainingPlacementSSO/TPStudent.jsp'


req_args = {
    'timeout': 20,
    'headers': {
        'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_11_1) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/46.0.2490.86 Safari/537.36',
        'Referer': 'https://erp.iitkgp.ernet.in/SSOAdministration/login.htm?sessionToken=595794DC220159D1CBD10DB69832EF7E.worker3&requestedUrl=https://erp.iitkgp.ernet.in/IIT_ERP2/welcome.jsp',
    },
    'verify': False
}


def erp_login(func):

    def wrapped_func(*args, **kwargs):

        print "Started erp_login!"

        s = requests.Session()

        r = s.get(ERP_HOMEPAGE_URL, **req_args)
        soup = bs(r.text, 'html.parser')

        print "Length of the fetched HTML: " + str(len(str(r.text)))
        # print str(r.text)
        if soup.find(id='sessionToken'):
            sessionToken = soup.find(id='sessionToken').attrs['value']
        else:
            raise Exception("Could not get the sessionToken!")

        r = s.post(ERP_SECRET_QUESTION_URL, data={'user_id': env['ERP_USERNAME']},
                   **req_args)
        secret_question = r.text
        secret_answer = None
        for i in xrange(1, 4):
            print env['ERP_Q%d' % i]
            if env['ERP_Q%d' % i] == secret_question:
                secret_answer = env['ERP_A%d' % i]
                break

        if secret_answer is None:
            print 'No secret question matched:', secret_question
            sys.exit(1)

        login_details = {
            'user_id': env['ERP_USERNAME'],
            'password': env['ERP_PASSWORD'],
            'answer': secret_answer,
            'sessionToken': sessionToken,
            'requestedUrl': 'https://erp.iitkgp.ernet.in/IIT_ERP2/welcome.jsp',
        }


        r = s.post(ERP_LOGIN_URL, data=login_details,
                   **req_args)
        ssoToken = re.search(r'\?ssoToken=(.+)$',
                             r.history[1].headers['Location']).group(1) 

        func(session=s, sessionData={'ssoToken': ssoToken,
                                     'sessionToken': sessionToken},
             *args, **kwargs)
        print "ERP Login completed!"

    return wrapped_func


def tnp_login(func):

    @erp_login
    def wrapped_func(session, sessionData, *args, **kwargs):

        ssoToken = sessionData['ssoToken']
        session.post(ERP_TPSTUDENT_URL,  # headers=headers,
                     data=dict(ssoToken=ssoToken, menu_id=11, module_id=26),
                     **req_args)
        func(session=session, sessionData=sessionData, *args, **kwargs)

        print "TNP Login completed!"

    return wrapped_func
