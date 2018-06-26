#!/usr/bin/env python


import json
import logging
import requests
from requests import Request, Session

global triagelog


class TriageError(Exception):
    """Base exception class for all Triage related errors
    Exception is explicitly raised when an unknown Triage error"""


class TriageStateError(TriageError):
    """Exception is raised when the session is not in a valid state for the method"""
    pass


class TriageClientError(TriageError):
    """Exception is raised when Triage box or an intermediate proxy responds with HTTP 4xx status code"""
    pass


class TriageAuthError(TriageClientError):
    """Exception is raised when Triage box or a transparent proxy responds with HTTP 401 code"""
    pass


class TriageServerError(TriageError):
    """Exception is raised when Triage box or an intermediate proxy responds with 5xx status code"""
    pass


class TriageFailureError(TriageError):
    """Exception is raised when Triage box returns failure result to last request"""
    pass


class TriageSession:
    """Class maintaining Triage connectivity through API."""

    apiver = '1.0.0'  # API version implemented/required
    debug = False

    def __init__(self, host, email, apikey, ssl=True, uag='Python CoFense Triage Client'):
        """
        Set ssl to False if you like to connect using plain HTTP (Triage must not redirect to HTTPS),
        Set uag to a desired User-Agent header value.
        """

        if not isinstance(ssl, bool): raise TypeError(__name__ + u': ssl parameter must be True or False')
        if not isinstance(uag, str): raise TypeError(__name__ + u': uag parameter must be a string')

        # ------- Private class instance attributes -------
        self._triagehost = host  # Hostname of an Triage box to connect to
        self._usessl = ssl  # Use SSL encryption for Triage communication
        self._userag = uag  # User-Agent string to use in HTTP headers
        self._email = email  # Email address of user with API key
        self._apikey = apikey  # API key of user accessing Triage

        self._headers = {'Accept': 'application/vnd.ve.v1.0+json',
                         'VE-API-Version': TriageSession.apiver,
                         'user-agent': self._userag,
                         'Authorization': 'Token token={0}:{1}'.format(self._email, self._apikey)}

    def _reqsend(self, prep, host=''):
        """Sends prepared request.
        Used by all other methods.
        Returns raw response.
        """

        triagelog.info(u'------- Sending {0} request to host {1} -------'.format(prep.method,
                                                                                 host))

        s = Session()

        resp = s.send(prep, verify=False)
        triagelog.debug(u'server response: {0}'.format(resp.text))

        if resp.status_code == 401:
            triagelog.error(u'Could not authenticate to Triage box {0}.'.format(host))
            raise TriageAuthError(__name__ + u': Could not authenticate to Triage box {0}.'.format(host))

        if resp.status_code != 200:
            desc = __name__ + u': Triage box {0} returned HTTP error {1}.'.format(self._triagehost,
                                                                                  resp.status_code)
            triagelog.error(desc)
            if 400 <= resp.status_code < 500:
                raise TriageClientError(desc)
            elif 500 <= resp.status_code < 600:
                raise TriageServerError(desc)
            else:
                raise TriageError(desc)

        return resp

    def _parse(self, src):
        """Parses source text as json entity.
        Returns result of parser(src).
        Raises TriageError if resp is not json, or json does not contain the values expected by parser.
        """

        triagelog.info(u'------- Parsing {0}-byte server response -------'.format(len(src)))
        triagelog.debug(u'text to parse = "{0}"'.format(src))

        try:
            res = json.loads(src)
        except ValueError as e:
            triagelog.error(u'Triage box {0} did not return a valid json output.'.format(self._triagehost))
            raise TriageError(
                __name__ + u': Triage box {0} did not return a valid json output.'.format(self._triagehost))

        triagelog.debug(u'json data = "{0}"'.format(res))

        return res

    # ===== Public class methods =====
    def reports(self, match_priority=None, category_id=None, start_date=None,
                tags=None, end_date=None, page=None, per_page=None, report_id=None):
        """Searches all Triage reports.

        tags (list) - One or more tags of processed reports to filter on.
        page (int) - The page number for the results.
        per_page (int) - The number of results rendered per page. The maximum value is 50 results per page.
        start_date (str) - The start date and time of the query. The default is six days ago.
        end_date (str) - The end date and time of the query. The default is the current time.
        report_id (int) - The Numeric ID of a Triage report.
        category_id (int) - The category ID (1-5) for processed reports.
        match_priority (int) - The highest match priority based on rule hits for the report.
        """

        triagelog.info(u'------- Opening new session to server {0} with user {1} -------'.format(self._triagehost,
                                                                                      self._email))

        if not isinstance(self._email, str):
            raise TypeError(__name__ + u': email parameter must be a string')
        if not isinstance(self._apikey, str):
            raise TypeError(__name__ + u': apikey parameter must be a string')
        if tags and not isinstance(tags, list):
            raise TypeError(__name__ + u': tags parameter must be a list of strings')
        if page and not isinstance(page, int):
            raise TypeError(__name__ + u': page parameter must be an integer')
        if per_page and not isinstance(per_page, int):
            raise TypeError(__name__ + u': per_page parameter must be an integer')
        if start_date and not isinstance(start_date, str):
            raise TypeError(__name__ + u': start_date parameter must be a string')
        if end_date and not isinstance(end_date, str):
            raise TypeError(__name__ + u': end_date parameter must be a string')
        if report_id and not isinstance(report_id, int):
            raise TypeError(__name__ + u': report_id parameter must be an integer')
        if category_id and not isinstance(category_id, int):
            raise TypeError(__name__ + u': caterory_id parameter must be an integer')
        if match_priority and not isinstance(match_priority, int):
            raise TypeError(__name__ + u': match_priority parameter must be an integer')

        params = []

        if tags: params.append("tags=" + ",".join(tags))
        if page: params.append("page=" + str(page))
        if per_page: params.append("per_page=" + str(per_page))
        if start_date: params.append("start_date=" + start_date)
        if end_date: params.append("end_date=" + end_date)
        if match_priority: params.append("match_priority=" + str(match_priority))
        if category_id: params.append("category_id=" + str(category_id))

        if report_id:
            url = 'http{0}://{1}/api/public/v1/reports/{2}'.format(('s' if self._usessl else ''),
                                                                   self._triagehost,
                                                                   report_id)
        elif params:
            url = 'http{0}://{1}/api/public/v1/reports?{2}'.format(('s' if self._usessl else ''),
                                                                   self._triagehost,
                                                                   '&'.join(params))
        else:
            url = 'http{0}://{1}/api/public/v1/reports'.format(('s' if self._usessl else ''),
                                                               self._triagehost)

        headers = self._headers.copy()
        headers.update({'Content-Type': 'application/json'})

        triagelog.debug(u'url = "{0}", headers = "{1}"'.format(url, headers))

        req = Request('GET', url, headers=headers)
        prep = req.prepare()
        resp = self._reqsend(prep, self._triagehost)

        return self._parse(resp.text)

    def processed_reports(self, match_priority=None, category_id=None, start_date=None,
                          tags=None, end_date=None, page=None, per_page=None):
        """Searches all Triage reports.

        tags (list) - One or more tags of processed reports to filter on.
        page (int) - The page number for the results.
        per_page (int) - The number of results rendered per page. The maximum value is 50 results per page.
        start_date (str) - The start date and time of the query. The default is six days ago.
        end_date (str) - The end date and time of the query. The default is the current time.
        category_id (int) - The category ID (1-5) for processed reports.
        match_priority (int) - The highest match priority based on rule hits for the report.
        """

        triagelog.info(u'------- Opening new session to server {0} with user {1} -------'.format(self._triagehost,
                                                                                      self._email))

        if not isinstance(self._email, str):
            raise TypeError(__name__ + u': email parameter must be a string')
        if not isinstance(self._apikey, str):
            raise TypeError(__name__ + u': apikey parameter must be a string')
        if tags and not isinstance(tags, list):
            raise TypeError(__name__ + u': tags parameter must be a list of strings')
        if page and not isinstance(page, int):
            raise TypeError(__name__ + u': page parameter must be an integer')
        if per_page and not isinstance(per_page, int):
            raise TypeError(__name__ + u': per_page parameter must be an integer')
        if start_date and not isinstance(start_date, str):
            raise TypeError(__name__ + u': start_date parameter must be a string')
        if end_date and not isinstance(end_date, str):
            raise TypeError(__name__ + u': end_date parameter must be a string')
        if category_id and not isinstance(category_id, int):
            raise TypeError(__name__ + u': caterory_id parameter must be an integer')
        if match_priority and not isinstance(match_priority, int):
            raise TypeError(__name__ + u': match_priority parameter must be an integer')

        params = []

        if tags: params.append("tags=" + ",".join(tags))
        if page: params.append("page=" + str(page))
        if per_page: params.append("per_page=" + str(per_page))
        if start_date: params.append("start_date=" + start_date)
        if end_date: params.append("end_date=" + end_date)
        if category_id: params.append("category_id=" + str(category_id))
        if match_priority: params.append("match_priority=" + str(match_priority))

        if params:
            url = 'http{0}://{1}/api/public/v1/processed_reports?{2}'.format(('s' if self._usessl else ''),
                                                                             self._triagehost,
                                                                             '&'.join(params))
        else:
            url = 'http{0}://{1}/api/public/v1/processed_reports'.format(('s' if self._usessl else ''),
                                                                         self._triagehost)

        headers = self._headers.copy()
        headers.update({'Content-Type': 'application/json'})

        triagelog.debug(u'url = "{0}", headers = "{1}"'.format(url, headers))

        req = Request('GET', url, headers=headers)
        prep = req.prepare()
        resp = self._reqsend(prep, self._triagehost)

        return self._parse(resp.text)

    def inbox_reports(self, match_priority=None, start_date=None,
                      end_date=None, page=None, per_page=None):
        """Searches current Triage inbox for new email reports.

        page (int) - The page number for the results.
        per_page (int) - The number of results rendered per page. The maximum value is 50 results per page.
        start_date (str) - The start date and time of the query. The default is six days ago.
        end_date (str) - The end date and time of the query. The default is the current time.
        match_priority (int) - The highest match priority based on rule hits for the report.
        """

        triagelog.info(u'------- Opening new session to server {0} with user {1} -------'.format(self._triagehost,
                                                                                      self._email))

        if not isinstance(self._email, str):
            raise TypeError(__name__ + u': email parameter must be a string')
        if not isinstance(self._apikey, str):
            raise TypeError(__name__ + u': apikey parameter must be a string')
        if page and not isinstance(page, int):
            raise TypeError(__name__ + u': page parameter must be an integer')
        if per_page and not isinstance(per_page, int):
            raise TypeError(__name__ + u': per_page parameter must be an integer')
        if start_date and not isinstance(start_date, str):
            raise TypeError(__name__ + u': start_date parameter must be a string')
        if end_date and not isinstance(end_date, str):
            raise TypeError(__name__ + u': end_date parameter must be a string')
        if match_priority and not isinstance(match_priority, int):
            raise TypeError(__name__ + u': match_priority parameter must be an integer')

        params = []

        if page: params.append("page=" + str(page))
        if per_page: params.append("per_page=" + str(per_page))
        if start_date: params.append("start_date=" + start_date)
        if end_date: params.append("end_date=" + end_date)
        if match_priority: params.append("match_priority=" + str(match_priority))

        if params:
            url = 'http{0}://{1}/api/public/v1/inbox_reports?{2}'.format(('s' if self._usessl else ''),
                                                                         self._triagehost,
                                                                         '&'.join(params))
        else:
            url = 'http{0}://{1}/api/public/v1/inbox_reports'.format(('s' if self._usessl else ''),
                                                                     self._triagehost)

        headers = self._headers.copy()
        headers.update({'Content-Type': 'application/json'})

        triagelog.debug(u'url = "{0}", headers = "{1}"'.format(url, headers))

        req = Request('GET', url, headers=headers)
        prep = req.prepare()
        resp = self._reqsend(prep, self._triagehost)

        return self._parse(resp.text)

    def attachment(self, attachment_id, mime_type):
        """Downloads attachment from a phishing email based on attachment ID.

        attachment_id (int) - The numeric ID associated with the attachment.
        mime_type (str) - mime type of the attachment.

        """

        triagelog.info(u'------- Opening new session to server {0} with user {1} -------'.format(self._triagehost,
                                                                                      self._email))

        if not isinstance(self._email, str):
            raise TypeError(__name__ + u': email parameter must be a string')
        if not isinstance(self._apikey, str):
            raise TypeError(__name__ + u': apikey parameter must be a string')
        if not isinstance(mime_type, str):
            raise TypeError(__name__ + u': mime_type parameter must be a string')
        if not isinstance(attachment_id, int):
            raise TypeError(__name__ + u': attachment_id parameter must be an integer')

        url = 'http{0}://{1}/api/public/v1/attachment/{2}'.format(('s' if self._usessl else ''),
                                                                  self._triagehost,
                                                                  str(attachment_id))

        headers = self._headers.copy()
        headers.update({'Content-Type': mime_type})

        triagelog.debug(u'url = "{0}", headers = "{1}"'.format(url, headers))

        req = Request('GET', url, headers=headers)
        prep = req.prepare()
        resp = self._reqsend(prep, self._triagehost)

        return resp.content

    def integration_search(self, sha256=None, md5=None, searchurl=None):
        """Fetches integration results based on hash (MD5/SHA256) or URL.

        md5 (str) - md5 hash of the file being searched.
        url (str) - url being searched. DO NOT SUBMIT IF PII IN THE URL!!!
        sha256 (str) - sha256 hash of the file being searched.

        """

        params = []

        if searchurl:
            params.append("searchurl=" + searchurl)
        if md5:
            params.append("md5=" + md5)
        if sha256:
            params.append("sha256=" + sha256)

        triagelog.info(u'------- User {0} searching integrations for {1} -------'.format(self._email,
                                                                                         params))

        if not isinstance(self._email, str):
            raise TypeError(__name__ + u': email parameter must be a string')
        if not isinstance(self._apikey, str):
            raise TypeError(__name__ + u': apikey parameter must be a string')
        if md5 and not isinstance(md5, str):
            raise TypeError(__name__ + u': md5 parameter must be a string')
        if searchurl and not isinstance(searchurl, str):
            raise TypeError(__name__ + u': searchurl parameter must be a string')
        if md5 and not isinstance(md5, str):
            raise TypeError(__name__ + u': sha256 parameter must be a string')

        if [sha256, md5, searchurl].count(None) == 3:
            raise ValueError(__name__ + u'Triage.integration_search takes exactly 1 argument. You gave none.')

        url = 'http{0}://{1}/api/public/v1/integration_search?{2}'.format(('s' if self._usessl else ''),
                                                                          self._triagehost,
                                                                          "&".join(params))

        headers = self._headers.copy()
        headers.update({'Content-Type': 'application/json'})

        triagelog.debug(u'url = "{0}", headers = "{1}"'.format(url,
                                                               headers))

        req = Request('GET', url, headers=headers)
        prep = req.prepare()
        resp = self._reqsend(prep, self._triagehost)

        return self._parse(resp.text)

    def clusters(self, match_priority=None, start_date=None,
                 end_date=None, page=None, per_page=None, tags=None):
        """Searches current Triage inbox for new email reports.

        tags (list) - One or more tags of processed reports to filter on.
        page (int) - The page number for the results.
        per_page (integer) - The number of results rendered per page. The maximum value is 50 results per page.
        start_date (str) - The start date and time of the query. The default is six days ago.
        end_date (str) - The end date and time of the query. The default is the current time.
        match_priority (int) - The highest match priority based on rule hits for the report.
        """

        triagelog.info(u'------- Opening new session to server {0} with user {1} -------'.format(self._triagehost,
                                                                                      self._email))

        if not isinstance(self._email, str):
            raise TypeError(__name__ + u': email parameter must be a string')
        if not isinstance(self._apikey, str):
            raise TypeError(__name__ + u': apikey parameter must be a string')
        if tags and not isinstance(tags, str):
            raise TypeError(__name__ + u': tags parameter must be a string')
        if page and not isinstance(page, int):
            raise TypeError(__name__ + u': page parameter must be an integer')
        if per_page and not isinstance(per_page, int):
            raise TypeError(__name__ + u': per_page parameter must be an integer')
        if start_date and not isinstance(start_date, str):
            raise TypeError(__name__ + u': start_date parameter must be a string')
        if end_date and not isinstance(end_date, str):
            raise TypeError(__name__ + u': end_date parameter must be a string')
        if match_priority and not isinstance(match_priority, int):
            raise TypeError(__name__ + u': match_priority parameter must be an integer')

        params = []

        if tags: params.append("tags=" + tags)
        if page: params.append("page=" + str(page))
        if per_page: params.append("per_page=" + str(per_page))
        if start_date: params.append("start_date=" + start_date)
        if end_date: params.append("end_date=" + end_date)
        if match_priority: params.append("match_priority=" + str(match_priority))

        if params:
            url = 'http{0}://{1}/api/public/v1/clusters?{2}'.format(('s' if self._usessl else ''),
                                                                    self._triagehost,
                                                                    '&'.join(params))
        else:
            url = 'http{0}://{1}/api/public/v1/clusters'.format(('s' if self._usessl else ''),
                                                                self._triagehost)

        headers = self._headers.copy()
        headers.update({'Content-Type': 'application/json'})

        triagelog.debug(u'url = "{0}", headers = "{1}"'.format(url, headers))

        req = Request('GET', url, headers=headers)
        prep = req.prepare()
        resp = self._reqsend(prep, self._triagehost)

        return self._parse(resp.text)


# Disable SSL security warning
try:
    requests.packages.urllib3.disable_warnings()
except AttributeError:
    pass
# Define logger
triagelog = logging.getLogger(__name__)
