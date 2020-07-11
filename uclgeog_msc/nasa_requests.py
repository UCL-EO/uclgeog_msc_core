import requests
from pathlib import Path
from uclgeog_msc.cylog import cylog

__author__ = "P Lewis"
__copyright__ = "Copyright 2018 P Lewis"
__license__ = "GPLv3"
__email__ = "p.lewis@ucl.ac.uk"

'''
acts like request, but for NASA Earthdata URLs, it adds in your
username and password.
'''

def get(url):
    r1 = None
    r2 = None
    try:
        with requests.Session() as session:
            # get password-authorised url
            session.auth = cylog().login()
            r1 = session.request('get',url)
            # this gets the url with codes for login etc.
            if r1.url:
                r2 = session.get(r1.url)
                return(r2)
    except:
        for r in (r1,r2):
            if r:
                r.ok = False
                return r
    return(None)

def test(url = 'https://e4ftl01.cr.usgs.gov/MOTA/MCD15A3H.006/2018.09.30/'):
    '''
    Run a test that the credentials work

    Returns True if works,False if not.

    '''

    # grab the HTML information
    html = get(url).text
    # test a few lines of the html
    return html[:20] == '<!DOCTYPE HTML PUBLI'
