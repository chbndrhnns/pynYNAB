# coding=utf-8
import json
import logging
from time import sleep

import requests
from requests.cookies import RequestsCookieJar

from pynYNAB.KeyGenerator import generateuuid
from pynYNAB.schema.Entity import ComplexEncoder
from pynYNAB.utils import rate_limited

LOG = logging.getLogger(__name__)


class NYnabConnectionError(Exception):
    pass


# noinspection PyPep8Naming
class nYnabConnection(object):
    urlCatalog = 'https://app.youneedabudget.com/api/v1/catalog'

    def init_session(self):
        self.session.cookies = RequestsCookieJar()

        self.session.headers['X-YNAB-Device-Id'] = self.id
        #self.session.headers['User-Agent'] = 'python nYNAB API bot - rienafairefr rienafairefr@gmail.com'
        self.session.headers['User-Agent'] = 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/58.0.3029.110 Safari/537.36'

        firstlogin = self.dorequest({"email": self.email, "password": self.password, "remember_me": True,
                                     "device_info": {"id": self.id}}, 'loginUser')
        if firstlogin is None:
            raise NYnabConnectionError('Couldnt connect with the provided email and password')
        self.sessionToken = firstlogin["session_token"]
        self.session.headers['X-Session-Token'] = self.sessionToken
        self.user_id = firstlogin['user']['id']

    def __init__(self, email, password):
        self.email = email
        self.password = password
        self.session = requests.Session()
        self.sessionToken = None
        self.id = str(generateuuid())
        self.lastrequest_elapsed = None

    @rate_limited(maxpersecond=5)
    def dorequest(self, request_dic, opname):
        """
        :param request_dic: a dictionary containing parameters for the request
        :param opname: An API operation name, available are: loginUser,getInitialUserData,logoutUser,createNewBudget,
        freshStartABudget,cloneBudget,deleteTombstonedBudgets,syncCatalogData,syncBudgetData,getInstitutionList,
        getInstitutionLoginFields,getInstitutionAccountList,registerAccountForDirectConnect,
        updateDirectConnectCredentials,poll,createFeedback,runSqlStatement
        :return: the dictionary of the result of the request
        """
        # Available operations :

        def errorout(message):
            LOG.error(message.replace(self.password,'********'))
            raise NYnabConnectionError(message)

        json_request_dict = json.dumps(request_dic, cls=ComplexEncoder, separators=(',', ':'))
        params = {u'operation_name': opname, 'request_data': json_request_dict}
        LOG.debug(('%s  ... %s ' % (opname, params)).replace(self.password,'********'))
        self.session.headers['X-YNAB-Client-Request-Id'] = generateuuid()
        self.session.headers['X-YNAB-Client-App-Version'] = 'v1.16300'
        self.session.headers['Accept'] = 'application/json, text/javascript, */*; q=0.01'
        self.session.headers['Accept-Encoding'] = 'gzip, deflate, br'
        self.session.headers['Origin'] = 'https://app.youneedabudget.com'
        self.session.headers['X-Requested-With'] = 'XMLHttpRequest'
        self.session.headers['Referer'] = 'https://app.youneedabudget.com/e96959a4-c600-409e-81c4-493b76cde50d/accounts/863d0f27-d510-49a0-8985-6df95f62e6bc'
        self.session.headers['Content-Type']='application/x-www-form-urlencoded; charset=UTF-8'

        r = self.session.post(self.urlCatalog, params, verify = "D:\Perso\FiddlerRoot.crt")
        self.lastrequest_elapsed = r.elapsed
        js = r.json()
        if r.status_code == 500:
            raise NYnabConnectionError('Uunrecoverable server error, sorry YNAB')
        if r.status_code != 200:
            LOG.debug('non-200 HTTP code: %s ' % r.text)
        if not 'error' in js:
            errorout('The server returned a json value without an error field')
        if js['error'] is None:
            return js
        error = js['error']
        if 'id' not in error:
            errorout('Error field %s without id returned from the API, %s' % (error, params))
        if error['id'] == 'user_not_found':
            errorout('API error, User Not Found')
        elif error['id'] == 'user_password_invalid':
            errorout('API error, User-Password combination invalid')
        elif error['id'] == 'request_throttled':
            LOG.debug('API Rrequest throttled')
            retryrafter = r.headers['Retry-After']
            LOG.debug('Waiting for %s s' % retryrafter)
            sleep(float(retryrafter))
            return self.dorequest(request_dic, opname)
        else:
            errorout('Unknown API Error \"%s\" \"%s\" was returned from the API when sending request (%s)' % (error['id'], error['message'], params))

