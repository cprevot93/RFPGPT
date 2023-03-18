import logging
import os
import pickle
import json
import time

import requests
from seleniumrequests import Firefox
# from seleniumrequests import Chrome
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.firefox.options import Options
import local_storage as ls

log = logging.getLogger(__name__)
TOKEN = ""
COOKIES_FILE = 'cookies.pkl'
LOCAL_STORAGE_FILE = 'local_storage.json'


def get_reponses(s: requests.Session):
    url = 'https://app.rfpio.com/rfpserver/ext/v1/content-lib/search?companyId=5c588363c51a59041a54cf02'
    json = {
        'limit': 50,
        'metadata': True
    }
    cursor = None
    while True:
        response = s.post(url, json=json)
        response.raise_for_status()
        payload = response.json()
        yield from payload.get('results', {})
        new_cursor = payload.get('nextCursorMark')
        if new_cursor == cursor:
            log.info('Duplicate cursor, quitting...')
            break
        cursor = new_cursor
        if cursor:
            log.debug(f'Cursor is now {cursor}')
            json.update({
                'cursor': cursor
            })
        else:
            break


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
    pickle.dump(cookies, open(COOKIES_FILE, "wb"))

    # save local storage
    storage = ls.LocalStorage(driver)
    with open(LOCAL_STORAGE_FILE, 'w') as f:
        json.dump(storage.items(), f)

    # close head browser
    driver.close()


def get_token() -> str:
    if not os.path.exists(COOKIES_FILE) or not os.path.exists(LOCAL_STORAGE_FILE):
        login()
    else:
        log.info('> Token found')

    with open(LOCAL_STORAGE_FILE, 'r') as f:
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


def head():
    driver = Firefox()
    driver.get("https://app.rfpio.com/")

    # load cookies
    cookies = pickle.load(open("cookies.pkl", "rb"))
    for cookie in cookies:
        driver.add_cookie(cookie)
    # load local storage
    storage = ls.LocalStorage(driver)
    with open('local_storage.json', 'r') as f:
        print("local storage")
        for key, value in json.load(f).items():
            print(key, value)
            storage[key] = value

    driver.get(
        "https://app.rfpio.com/v2/content-library/library?currentTab=LIBRARY&companyId=5c588363c51a59041a54cf02")

    time.sleep(1200)

    # print("res:", res)

    driver.close()
    exit(0)

    count = 0
    answer_records = []

    for answer in get_reponses(s):
        answer_id = answer.get('id')
        log.debug(f'Found answer {answer_id}')
        answer_records.append({
            'id': answer_id,
            'company_id': answer.get('companyId'),
            'question': answer.get('question'),
            'tags': ' / '.join(answer.get('tags', [])),
            'used_count': answer.get('numUsed'),
            'content_score': answer.get('contentScore'),
            'star_rating': answer.get('starRating'),
            'updated_date': answer.get('updateDate'),
            'updated_by': answer.get('updateBy'),
            'status': answer.get('status'),
            'last_used_date': answer.get('lastUsedDate'),
            'reviewed': answer.get('reviewed'),
            'needs_review': answer.get('needReview'),
            'review_flag': answer.get('reviewFlag'),
            'review_status': answer.get('reviewStatus')
        })
        count += 1
        if len(answer_records) > 99:
            log.info(f'Found {count} answers so far')

    log.info(f'Found {count} total')


def headless():
    options = Options()
    options.add_argument("-headless")
    driver = Firefox(options=options)

    driver.get("https://app.rfpio.com/")

    # load cookies
    cookies = pickle.load(open("cookies.pkl", "rb"))
    for cookie in cookies:
        driver.add_cookie(cookie)

    query = {
        "term": "Flow mode",
        "additionalUIParams": {},
        "additionalQueries": {},
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
        "limit": 25,
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
        "fields": [],
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
        "contentTypeFilterList": [
            "ANSWER",
            "DOCUMENT"
        ],
        "filterCount": 1,
        "resultantCount": 0,
        "ansLibUsedTypes": [],
        "createdByList": [],
        "minStarRating": 0,
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
        'POST', 'https://app.rfpio.com/rfpserver/content-library/search', json=query, headers={'Authorization': f'Bearer {access_token}'})
    _j = json.loads(response.text)
    print(json.dumps(_j, indent=4, sort_keys=True))

    driver.close()


if __name__ == '__main__':
    access_token = get_token()
    head()
