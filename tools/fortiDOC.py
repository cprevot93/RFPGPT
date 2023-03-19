import logging
import os
import json
import sys
import requests
from bs4 import BeautifulSoup as bs

from langchain.tools import BaseTool

log = logging.getLogger(__name__)

TMP_FOLDER = 'tmp'
# create tmp folder if not exists
if os.path.exists(TMP_FOLDER) is False:
    os.mkdir(TMP_FOLDER)

TEST_SAMPLE_FILENAME = 'docs_test_sample.json'
TEST_SAMPLE_PATH = os.path.join(TMP_FOLDER, TEST_SAMPLE_FILENAME)

API_PRODUCT_LIST_URL = 'https://docs.fortinet.com/api/products'
API_PRODUCT_LIST_FILENAME = 'docs_api_product_list.json'
API_PRODUCT_LIST_PATH = os.path.join(TMP_FOLDER, API_PRODUCT_LIST_FILENAME)


def _get_product_id(product: str) -> str:
    """
    Return dynamic product id with product name for the API
    """
    if not os.path.exists(API_PRODUCT_LIST_PATH):
        response = requests.get(API_PRODUCT_LIST_URL)
        if response.status_code != 200:
            log.error(f'Error getting product id for {product}')
            return ""
        _j = json.loads(response.text)

        # save product list to file
        with open(API_PRODUCT_LIST_PATH, 'w') as f:
            json.dump(_j, f)
    else:
        # load product list from file
        with open(API_PRODUCT_LIST_PATH, 'r') as f:
            _j = json.load(f)

    for index, obj in _j.items():
        if obj["slug"].lower() == product.lower():
            return obj["id"]
    return ""


def _get_query(query: str, product_tag: str) -> list:
    log.info(
        f'> Searching "{query}" for product {product_tag} on docs.fortinet.com')

    product_id = "" if product_tag == "" else _get_product_id(product_tag)
    url = f"https://docs.fortinet.com/search2?q={query}"
    if product_id != "":
        url += f"&product={product_id}"

    log.debug(f'URL search: {url}')
    try:
        response = requests.get(url)
        _j = json.loads(response.text)
    except Exception as e:
        log.error(f'Error: {e.args}')
        if response.text:
            print(response.text)
        return []

    res = {
        "query": query,
        "product_tag": product_tag,
        "results": _j
    }
    with open(TEST_SAMPLE_PATH, 'w') as f:
        json.dump(res, f)

    return _j


def _construct_url(result: dict) -> str:
    """
    Construct the URL for the result
    """
    result = result['content']
    # get the more recent version

    def versiontuple(v: str):
        return tuple(map(int, (v.split("."))))

    most_recent_version = result['versions'][0]
    for _v in result['versions']:
        if versiontuple(_v['version']['version']) > versiontuple(most_recent_version['version']['version']):
            most_recent_version = _v

    return f"https://docs.fortinet.com/document/{result['product']['slug']}/{most_recent_version['version']['version']}/{most_recent_version['document']['slug']}/{most_recent_version['page']['permanent_id']}/{most_recent_version['page']['slug']}"


def _extract_content(html: str) -> str:
    """
    Extract the main content from the html
    """
    if html is None:
        raise Exception('No html')

    soup = bs(html, 'html.parser')
    main_content = soup.find('div', id='mc-main-content')

    if main_content is None:
        raise Exception('No main content found')

    # replace <li> with '- '

    return main_content.get_text()


def get_first_result(query: str, product_tag: str) -> str:
    """
    Return the first result for the query
    """
    results = _get_query(query, product_tag)
    if len(results) == 0:
        return ""

    try:
        url = _construct_url(results[0])
        content = requests.get(url)
        return _extract_content(content.text)
    except Exception as e:
        log.error(f'Error: {e.args}')


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


class FortiDOC(BaseTool):
    """Use FortiDOC to search in Fortinet Docs database."""
    name = "Fortinet DOCS search"
    description = "Use this more than the normal search if you need to search about a feature in a Fortinet product or if the question is about Fortinet product configuration. \
The input to this tool should start with the name of the Fortinet Product (no abbreviation) then a comma then the query. For example, `FortiGate,SD-WAN` would be the input if you wanted to search how SD-WAN works on Fortigate."

    def __init__(self, *args, **kwargs):
        """Initialize the tool."""
        super().__init__(*args, **kwargs)

    def _run(self, query: str) -> str:
        """Use the tool."""
        access_token = get_token()

        product, terms = query.split(",")
        product_tags = [product]

        results = _get_query(access_token, terms, product_tags)
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

    # arvg parsing with argparse
    import argparse
    parser = argparse.ArgumentParser(
        prog='FortiDOC',
        description='Search in Fortinet Docs database',
    )
    parser.add_argument("-q", "--query", help="Query to search for")
    parser.add_argument("-p", "--product",
                        help="Fortinet product to search for")
    parser.add_argument("-v", "--verbose",
                        action='store_true', help="Verbose mode")
    args = parser.parse_args()

    if args.verbose:
        logging.basicConfig(level=logging.DEBUG)
    else:
        logging.basicConfig(level=logging.INFO)

    product = ""
    if args.product:
        product = args.product

    if not args.query:
        # return product id
        print(_get_product_id(product))
    else:
        first = get_first_result(args.query, product)
        print(first)
        # results = format_response(results)
