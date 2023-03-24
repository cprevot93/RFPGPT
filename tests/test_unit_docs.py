from unittest import TestCase

import json
import os
from ..tools.fortiDOC import _construct_url, _construct_collection_name


class FortiDocsUnitTestCase(TestCase):
    """
    Unit tests for fortiDocs tool system
    """

    def test_construct_url(self):
        """ Create a url """
        samples = {}
        with open("tests/samples/docs_query.json", "r") as f:
            samples = json.load(f)['results']

        result = _construct_url(samples)
        self.assertEqual(
            result, "https://docs.fortinet.com/document/fortiweb/6.3.0/cli-reference/257614/waf-ftp-protection-profile")

    def test_construct_collection_name(self):
        """ Create a collection name """

        pass
