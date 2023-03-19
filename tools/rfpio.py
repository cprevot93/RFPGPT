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

log = logging.getLogger(__name__)
TOKEN = ""

TMP_FOLDER = 'tmp'
COOKIES_FILENAME = 'cookies.pkl'
LOCAL_STORAGE_FILENAME = 'local_storage.json'
TEST_SAMPLE_FILENAME = 'test_sample.json'

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


def get_reponses(_token: str, query: str, product_tags: list) -> list:
    log.info(f'> Searching for "{query}" with tags {product_tags}')
    options = Options()
    options.add_argument("-headless")
    driver = Firefox(options=options)

    driver.get("https://app.rfpio.com/")

    # load cookies
    cookies = pickle.load(open(COOKIES_PATH, "rb"))
    for cookie in cookies:
        driver.add_cookie(cookie)

    limit = 5  # number of results

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
    if response.status_code != 200:
        log.error(
            f'Error searching for "{query}" with tags {product_tags}, status code {response.status_code}')
    driver.close()

    _j = json.loads(response.text)
    _j["term"] = query
    with open(TEST_SAMPLE_PATH, 'w') as f:
        json.dump(_j, f)

    return _j["results"]


def strip_html_tags(text: str) -> str:
    """Remove html tags from a string"""
    import re
    clean = re.compile('<.*?>')
    return re.sub(clean, '', text)


def format_response(results: list) -> list[str]:
    res = []
    for r in results:
        for a in r['answers']:
            if a['type'] == 'RICH_TEXT':
                answer = strip_html_tags(a['value'])
            else:
                answer = a['value']
            answer = a['key'] + ': ' + answer
            res.append(answer)
    return res


class RFPIO(BaseTool):
    """Use RFPio to search for answers."""
    name = "RFPio Search"
    description = "Use this more than the normal search if the question is about Fortinet products. The input to this tool should start with the name of the Fortinet Product (no abbreviation) then a comma then the query. For example, `FortiGate,SD-WAN` would be the input if you wanted to search how SD-WAN works on Fortigate."

    def __init__(self, *args, **kwargs):
        """Initialize the tool."""
        super().__init__(*args, **kwargs)

    def _run(self, query: str) -> str:
        """Use the tool."""
        access_token = get_token()

        product, terms = query.split(",")
        product_tags = [product]

        results = get_reponses(access_token, terms, product_tags)
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
