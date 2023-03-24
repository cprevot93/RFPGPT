import logging
import os
import json
import sys
import requests
import re
import urllib.parse
from bs4 import BeautifulSoup as bs, Tag, NavigableString
from typing import Any, Dict, List, Optional, Tuple, Union

from langchain.tools import BaseTool
from .context_tool import ContextTool
from .ingest_file import search_file

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


def _get_product_id(product_name: str) -> str:
    """
    Return dynamic product id with product name for the API
    """
    if not os.path.exists(API_PRODUCT_LIST_PATH):
        response = requests.get(API_PRODUCT_LIST_URL, timeout=10)
        if response.status_code != 200:
            log.error('Error getting product id for %s', product_name)
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
        if obj["slug"].lower() == product_name.lower():
            return obj["id"]
    return ""


def _get_query(query: str, product_tag: str) -> list:
    log.info(
        f'> Searching "{query}" for product {product_tag} on docs.fortinet.com')

    product_id = "" if product_tag == "" else _get_product_id(product_tag)
    url = f"https://docs.fortinet.com/search2?q={urllib.parse.quote(query)}"
    if product_id != "":
        url += f"&product={product_id}"

    log.debug(f'URL search: %s', url)

    response = None
    try:
        response = requests.get(url, timeout=10)
        _j = json.loads(response.text)
    except Exception as excep:
        log.error(f'ERROR fetching {url}: {excep.args}')
        if response and response.text:
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


def format_response(main_content: Union[Tag, NavigableString]) -> str:
    """
    Format the response into raw text
    """
    # replace all <li> with '-'
    for li in main_content.find_all('li'):
        li.replace_with(f"- {li.get_text()}")
    # replace all <pre> with a new line
    for pre in main_content.find_all('pre'):
        pre.replace_with(f"\n{pre.get_text()}")
    text = main_content.get_text()
    # remove multiple spaces
    clean_space_text = re.sub(' +', ' ', text).strip()
    # remove multiple new lines
    clean_newline_text = re.sub('\n+', '\n', clean_space_text).strip()
    # remove newline after a list item
    clean_newline_text = re.sub('- \n', '- ', clean_newline_text).strip()
    return clean_newline_text


def _extract_content(html: str) -> Union[Tag, NavigableString]:
    """
    Extract the main content from the html
    """
    if html is None:
        raise Exception('No html')

    soup = bs(html, 'html.parser')
    main_content = soup.find('div', id='mc-main-content')

    if main_content is None:
        raise Exception('No main content found')

    return main_content


def _construct_collection_name(product_tag: str, product_version: str) -> str:
    """
    Construct the collection name for the product and version
    """
    return f"docs_{product_tag}_{product_version}"


def searchDB(query: str, product_tag: str, product_version: str) -> str:
    """
    Search query in the database document
    """
    collection_name = _construct_collection_name(product_tag, product_version)


def scrap_docs(query: str, product_tag: str, raw=False) -> str:
    """
    Return the first result for the query
    """
    results = _get_query(query, product_tag)
    content = ""
    if len(results) == 0:
        return content

    try:
        url = _construct_url(results[0])  # get the first result
        html = requests.get(url, timeout=10)
        soup = _extract_content(html.text)
        if raw:
            content = str(soup)
        else:
            content = format_response(soup)
    except Exception:
        log.error('Unknown error while fetching result: ', exc_info=True)

    return content


CONTEXT_PROMPT = "CONTEXT:You must ask the human about {context}. Reply with schema #2."


class FortiDocs(BaseTool):
    """Use FortiDOC to search in Fortinet Docs database."""
    name = "Fortinet DOCS search"
    description = """
Use this more than the normal search if you need to search about a feature in a Fortinet product or Fortinet product configuration.
The input should start with the name of the product followed by a comma, the product current firmware version a comma finished by the query.
The query MUST be in English. For example, `FortiGate,7.2.4,SD-WAN overview` would be the input if you want to search of a SD-WAN documentation on Fortigate in firmware version 7.2.4.
If you don't know the product name, you must input 0. If you don't know the firmware version, you must input 0. Exemple: `FortiWeb,0,Security features` or `0,7.2.4,IPsec VPN`"""

    def __init__(self, *args, **kwargs):
        """Initialize the tool."""
        super().__init__(*args, **kwargs)

    def _run(self, tool_input: str) -> str:
        """Use the tool."""
        # check if input is a string or a dict

        if isinstance(tool_input, str):
            product_tag, firmware_version, query = tool_input.split(",")
        elif isinstance(tool_input, dict):  # I don't know why but the input can a dict sometimes
            query = tool_input.get('query', '')
            firmware_version = tool_input.get('firmware_version', '')
            product_tag = tool_input.get('product_tag', '')
        else:
            raise Exception("Invalid input")

        if product_tag == "0":
            return CONTEXT_PROMPT.format(context="the product name")
        if firmware_version == "0":
            return CONTEXT_PROMPT.format(context="the firmware version")

        output = scrap_docs(query.strip(), product_tag.strip())

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
    parser.add_argument("-p", "--product", help="Fortinet product to search for")
    parser.add_argument("-r", "--raw", action='store_true', help="Don't format the response")
    parser.add_argument("-v", "--verbose", action='store_true', help="Verbose mode")
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
        first = scrap_docs(args.query, product, args.raw)
        print(first)
        # results = format_response(results)
