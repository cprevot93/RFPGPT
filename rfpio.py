import logging
import os
import pickle
import json
import time

import requests
from selenium import webdriver
# from seleniumrequests import Chrome
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.keys import Keys

log = logging.getLogger(__name__)
TOKEN = ""


def get_reponses(s: requests.Session):
    url = 'https://app.rfpio.com/rfpserver/ext/v1/content-lib/search'
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
    log.info('Login to RFPio...')

    driver = webdriver.Chrome()
    driver.get(
        "https://app.rfpio.com/#/page/login?companyId=5c588363c51a59041a54cf02")

    wait = WebDriverWait(driver, 60)  # timeout after 60 seconds

    results = wait.until(EC.url_to_be(
        "https://app.rfpio.com/#/my-work?companyId=5c588363c51a59041a54cf02"))
    # cookies = driver.get_cookies()
    # pickle.dump(cookies, open("cookies.pkl", "wb"))

    # get the local storage
    # localStorage = driver.execute_script("return window.localStorage;")
    # userData = json.loads(localStorage["userData"])
    # TOKEN = userData.get("access_token")

    driver.get(
        "https://app.rfpio.com/v2/content-library/library?currentTab=LIBRARY&companyId=5c588363c51a59041a54cf02")

    results = wait.until(EC.element_to_be_clickable((By.ID, 'search_text')))
    input = driver.find_element(By.ID, "search_text")
    input.send_keys('Flow mode' + Keys.ENTER)

    time.sleep(10)

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


if __name__ == '__main__':
    login()
