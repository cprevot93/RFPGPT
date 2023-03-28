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
from .ingest_file import search_file

log = logging.getLogger(__name__)


class Milestone(BaseTool):
    """Use Milestone to search for Fortinet product life cycle dates."""
    name = "Milestone"
    description = """
Use this more than the normal search if assistant need to search about dates of a Fortinet product life cycle like launch date, end of support dates, etc.
The input for this tool is the model name. Example: 'FortiGate 100E'
    """

    def __init__(self, *args, **kwargs):
        """Initialize the tool."""
        super().__init__(*args, **kwargs)

    def _run(self, tool_input: str) -> str:
        """Use the tool."""
        # check if input is a string or a dict

        model = ""
        if isinstance(tool_input, str):
            model = tool_input
        else:
            raise Exception("Invalid input")

        search_doc = search_file(model, "fortinet_milestones")
        output = search_doc["answer"]

        return output

    async def _arun(self, query: str) -> str:
        """Use the tool asynchronously."""
        raise NotImplementedError("Milestone does not support async")


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
    parser.add_argument("-q", "--model", help="Query to search for")
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

    _search = search_file(args.model, "fortinet_milestones")
    print("Raw:", _search)
    print(_search["answer"])
    print(_search["source"])
