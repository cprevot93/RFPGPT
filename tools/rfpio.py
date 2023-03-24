import logging
import os
import pickle
import json
import time
import sys

from seleniumrequests import Firefox
from langchain.tools import BaseTool
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.firefox.options import Options
from .helpers import http_local_storage as ls

log = logging.getLogger()
TOKEN = ""

TMP_FOLDER = 'tmp'
# create tmp folder if not exists
if os.path.exists(TMP_FOLDER) is False:
    os.mkdir(TMP_FOLDER)

COOKIES_FILENAME = 'rfpio_cookies.pkl'
LOCAL_STORAGE_FILENAME = 'rfpio_local_storage.json'
TEST_SAMPLE_FILENAME = 'rfpio_test_sample.json'

COOKIES_PATH = os.path.join(TMP_FOLDER, COOKIES_FILENAME)
LOCAL_STORAGE_PATH = os.path.join(TMP_FOLDER, LOCAL_STORAGE_FILENAME)
TEST_SAMPLE_PATH = os.path.join(TMP_FOLDER, TEST_SAMPLE_FILENAME)


def login():
    log.info('> Login to RFPio')
    driver = Firefox()  # head browser
    # load cookies, start head
    driver.get(
        "https://app.rfpio.com/#/page/login?companyId=5c588363c51a59041a54cf02")

    wait = WebDriverWait(driver, 60)  # timeout after 60 seconds

    results = wait.until(EC.url_to_be(
        "https://app.rfpio.com/#/my-work?companyId=5c588363c51a59041a54cf02"))
    cookies = driver.get_cookies()
    pickle.dump(cookies, open(COOKIES_PATH, "wb"))

    # save local storage
    storage = ls.LocalStorage(driver)
    with open(LOCAL_STORAGE_PATH, 'w') as f:
        json.dump(storage.items(), f)

    # close head browser
    driver.close()


# get token from local storage when logged in
def get_token() -> str:
    if not os.path.exists(COOKIES_PATH) or not os.path.exists(LOCAL_STORAGE_PATH):
        login()
    else:
        log.info('> Previous session found, loading token')

    with open(LOCAL_STORAGE_PATH, 'r') as f:
        j = json.load(f)
        for key, value in j.items():
            if key != 'userData':
                continue

            j = json.loads(value)
            for key2, value2 in j.items():
                if key2 != 'access_token':
                    continue
                return value2
    return ""


def normalize_product_tags(tags: list) -> list:
    """
    Normalize product tags to match RFPio tags:
    FortiGate
    FortiAP
    FortiNac
    FortiWeb
    FortiManager
    FortiMail
    FortiSIEM
    FortiCNP
    FortiAuthenticator
    FortiMonitor
    FortiSOAR
    FortiSASE
    FortiAnalyzer
    FortiClient
    FortiToken
    FortiDDos
    FortiExtender
    """
    res_list = []
    for t in tags:
        match t.lower():
            case 'fortigate':
                res_list.append('FortiGate')
            case 'fortiap':
                res_list.append('FortiAP')
            case 'fortinac':
                res_list.append('FortiNac')
            case 'fortiweb':
                res_list.append('FortiWeb')
            case 'fortimanager':
                res_list.append('FortiManager')
            case 'fortimail':
                res_list.append('FortiMail')
            case 'fortisiem':
                res_list.append('FortiSIEM')
            case 'forticnp':
                res_list.append('FortiCNP')
            case 'fortiauthenticator':
                res_list.append('FortiAuthenticator')
            case 'fortimonitor':
                res_list.append('FortiMonitor')
            case 'fortisoar':
                res_list.append('FortiSOAR')
            case 'fortisase':
                res_list.append('FortiSASE')
            case 'fortianalyzer':
                res_list.append('FortiAnalyzer')
            case 'forticlient':
                res_list.append('FortiClient')
            case 'fortitoken':
                res_list.append('FortiToken')
            case 'fortiddos':
                res_list.append('FortiDDos')
            case 'fortiextender':
                res_list.append('FortiExtender')
            case '_':
                pass
    return res_list


def get_reponses_head():
    # head browser for testing
    driver = Firefox()
    driver.get("https://app.rfpio.com/")

    # load cookies
    cookies = pickle.load(open(COOKIES_PATH, "rb"))
    for cookie in cookies:
        driver.add_cookie(cookie)
    # load local storage
    storage = ls.LocalStorage(driver)
    with open(LOCAL_STORAGE_PATH, 'r') as f:
        print("> Loading local storage")
        for key, value in json.load(f).items():
            print(key, value)
            storage[key] = value

    driver.get(
        "https://app.rfpio.com/v2/content-library/library?currentTab=LIBRARY&companyId=5c588363c51a59041a54cf02")

    time.sleep(360)

    driver.close()
    exit(0)


def get_reponses(_token: str, query: str, product_tags: list, limit=3, search_only_in_question=False) -> list:
    """
    RFPIO API call
    """
    product_tags = normalize_product_tags(product_tags)
    log.info(f'> Searching for "{query}" with tags {product_tags}')
    options = Options()
    options.add_argument("-headless")
    driver = Firefox(options=options)

    # load cookies
    driver.get("https://app.rfpio.com/")  # required to load cookies
    cookies = pickle.load(open(COOKIES_PATH, "rb"))
    for cookie in cookies:
        driver.add_cookie(cookie)

    fields = ["question", "alternate_questions"] if search_only_in_question else [
        "question", "alternate_questions", "answer"]

    data = {
        "term": query,
        "additionalUIParams": {},
        "additionalQueries": {"content_type": ["ANSWER"], "tags": product_tags},
        "businessUnits": [],
        "lastUpdateFromDate": None,
        "lastUpdateToDate": None,
        "createdFromDate": None,
        "createdToDate": None,
        "lastUsedFromDate": None,
        "lastUsedToDate": None,
        "lastReviewedFromDate": None,
        "lastReviewedToDate": None,
        "deletedFromDate": None,
        "deletedToDate": None,
        "cursor": None,
        "usedCountFrom": "",
        "usedCountTo": "",
        "standardResponse": [],
        "hasAttachments": "",
        "collectionList": [],
        "offset": 0,
        "limit": limit,
        "facet": "true",
        "tagSearchOption": "ANY",
        "collectionSearchOption": "ANY",
        "importFileNameSearchList": [],
        "fileSourceList": [],
        "tagSearch": [],
        "documentTypeSearch": [],
        "excludeTagSearch": [],
        "projectSearch": [],
        "sectionSearch": [],
        "fields": ["question", "alternate_questions"],
        "boostQuerys": [],
        "owners": [],
        "approvers": [],
        "fromDate": None,
        "toDate": None,
        "includeFollowUp": False,
        "viewPending": False,
        "starRating": 0,
        "sortKey": "score desc",
        "editOnly": False,
        "skipQuery": [],
        "reviewFlag": "",
        "hasFlag": "",
        "flagList": [],
        "flagSearchOption": "ANY",
        "contentUsed": "",
        "secondarySearchText": "",
        "updatedByList": [],
        "reviewStatus": "",
        "hasImages": False,
        "score": 0,
        "hasOpenComments": False,
        "commentMention": [],
        "recommendationSearch": False,
        "offlineSearch": False,
        "backUp": False,
        "sourceList": [],
        "filterBusinessUnits": "",
        "languageSearch": [],
        "responseHeaders": [],
        "linkId": "",
        "hasRelatedContent": False,
        "savedSearchId": "",
        "hasAlertText": "",
        "idsList": [],
        "excludeIds": False,
        "partnerSearch": False,
        "maxContentScore": "",
        "minContentScore": "",
        "source": "CONTENT_LIBRARY",
        "alBackUpSearch": False,
        "translatedJobName": [],
        "translatedBy": [],
        "translatedFromLanguage": [],
        "languageReviewers": [],
        "statusFilter": "ACTIVE",
        "reviewFilter": "ALL",
        "reviewersPending": [],
        "reviewersCompleted": [],
        "secondarySearchFields": [],
        "hasLinkedContent": False,
        "relatedTo": [],
        "alReviewers": [],
        "hasOnDemandReview": "",
        "hasDocumentReview": "",
        "deletedByList": [],
        "previousState": "",
        "teamsField": "",
        "facetFields": [],
        "internalCodeSearch": False,
        "additionalMap": {},
        "customFields": {},
        "contentTypeFilterList": ["ANSWER"],
        "filterCount": 4,
        "resultantCount": 0,
        "ansLibUsedTypes": [],
        "createdByList": [],
        "minStarRating": 2,
        "maxStarRating": 5,
        "ownersSearchOption": "ANY",
        "approversSearchOption": "ANY",
        "createdBySearchOption": "ANY",
        "createDateOption": "RANGE",
        "dueDateOption": "RANGE",
        "updateDateOption": "RANGE",
        "lastUsedDateOption": "RANGE",
        "reviewedDateOption": "RANGE",
        "myFavoritesUsers": "",
        "dueDateSkipCount": 0,
        "excludeRetainContent": False,
        "alertTextTerm": ""
    }

    response = driver.request(
        'POST', 'https://app.rfpio.com/rfpserver/content-library/search', json=data, headers={'Authorization': f'Bearer {_token}'})
    driver.close()

    if response.status_code == 403 or response.status_code == 440:
        login()
    elif response.status_code != 200:
        log.error(
            f'Error searching for "{query}" with tags {product_tags}, status code {response.status_code}')

    _j = json.loads(response.text)
    _j["query"] = data
    with open(TEST_SAMPLE_PATH, 'w') as f:
        json.dump(_j, f)

    if _j['totalRecords'] == 0:
        log.info(f'No results found for "{query}" with tags {product_tags}')
        return [""]
    return _j["results"]


def strip_html_tags_and_url(text: str) -> str:
    """Remove html tags from a string"""
    import re
    tags = re.compile(r'<.*?>|For more information:')
    links = re.compile(
        r'\(?https?:\/{2}[\d\w-]+(\.[\d\w-]+)*(?:(?:\/[^\s/]*))*\)?')
    clean_text = re.sub(tags, ' ', text)
    clean_text = re.sub(links, ' ', clean_text)
    return re.sub(' +', ' ', clean_text).strip()


def format_response(results: list) -> list[str]:
    """
    Format the response into raw text
    """
    res = []
    for i, r in enumerate(results):
        for j, a in enumerate(r['answers']):
            key = f"{a['key']}." if a['key'] != 'Response' else ""
            if a['type'] == 'RICH_TEXT':
                answer = strip_html_tags_and_url(a['value'])
            else:
                answer = a['value']
            answer = f"Question: {strip_html_tags_and_url(r['question'])}\nResponse: {key} {answer}"
            res.append(answer)
    return res


class RFPIO(BaseTool):
    """Use RFPio to search for answers for Fortinet product."""
    name = "RFPio Search"
    description = "Use this in addition to the normal search if the question pertains to in-depth Fortinet product functionalities. Inputs of this tool should start with Fortinet product name (no abbreviation) followed by a comma then the query. Query MUST be in english. For example, `FortiGate,SD-WAN routing` would be the input if you wanted to search for SD-WAN on Fortigate."

    def __init__(self, *args, **kwargs):
        """Initialize the tool."""
        super().__init__(*args, **kwargs)

    def _run(self, query: str) -> str:
        """Use the tool."""
        access_token = get_token()

        product, terms = query.split(",")
        product_tags = [product.strip()]

        results = get_reponses(access_token, terms.strip(), product_tags)
        results = format_response(results)

        output = ""
        # merge results
        for r in results:
            output += r + "\n"

        return output

    async def _arun(self, query: str) -> str:
        """Use the tool asynchronously."""
        raise NotImplementedError("RFPio does not support async")


if __name__ == '__main__':
    access_token = get_token()

    if len(sys.argv) < 2:
        print("Please provide a query")
        sys.exit(1)

    query = sys.argv[1]
    product_tags = []

    if query == "test":
        get_reponses_head()

    if query == "clean":
        print(strip_html_tags_and_url(sys.argv[2]))
        exit(0)

    results = []
    if os.path.exists(TEST_SAMPLE_PATH):
        with open(TEST_SAMPLE_PATH, 'r') as f:
            _j = json.load(f)
            if 'term' in _j and _j['term'] == query:
                results = _j['results']
    if results == []:
        results = get_reponses(access_token, query, product_tags)

    results = format_response(results)
    output = ""
    # merge results
    for r in results:
        output += r + "\n"
    print(output)
