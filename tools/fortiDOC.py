import logging
import os
import json
import time
import sys
import requests

from seleniumrequests import Firefox
from langchain.tools import BaseTool

log = logging.getLogger(__name__)

TMP_FOLDER = 'tmp'
# create tmp folder if not exists
if os.path.exists(TMP_FOLDER) is False:
    os.mkdir(TMP_FOLDER)

TEST_SAMPLE_FILENAME = 'docs_test_sample.json'
TEST_SAMPLE_PATH = os.path.join(TMP_FOLDER, TEST_SAMPLE_FILENAME)


def get_product_id(product: str) -> str:
    """
    Return dynamic product id with product name for the API
    """
    url = "https://docs.fortinet.com/api/products"
    response = requests.get(url)
    if response.status_code != 200:
        log.error(f'Error getting product id for {product}')
        return ""
    _j = json.loads(response.text)
    for p in _j:
        if p["title"].lower() == product.lower():
            return p["id"]


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

    data = {}

    response = driver.request(
        'POST', 'https://app.rfpio.com/rfpserver/content-library/search', json=data, headers={'Authorization': f'Bearer {_token}'})
    driver.close()

    if response.status_code == 403:
        login()
    elif response.status_code != 200:
        log.error(
            f'Error searching for "{query}" with tags {product_tags}, status code {response.status_code}')

    _j = json.loads(response.text)
    _j["term"] = query
    with open(TEST_SAMPLE_PATH, 'w') as f:
        json.dump(_j, f)

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


class SearchTicket(BaseTool):
    """Use SearchTicket to search for previous ticket support."""
    name = "Support Ticket Search"
    description = "Use this more than the normal search if the question is about Fortinet product troobleshooting. The input to this tool should start with the name of the Fortinet Product (no abbreviation) then a comma then the query. For example, `FortiGate,SD-WAN` would be the input if you wanted to search how SD-WAN works on Fortigate."

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
    if len(sys.argv) < 2:
        print("Please provide a query")
        sys.exit(1)

    query = sys.argv[1]
    product_tags = []
    product_version = ""

    results = []
    results = get_reponses(access_token, query, product_tags)
    results = format_response(results)
    output = ""
    # merge results
    for r in results:
        output += r + "\n"
    print(output)
