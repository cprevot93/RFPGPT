from unittest import TestCase

import json
import os
from tools.fortiDOC import _construct_url, _construct_collection_name


class FortiDocsUnitTestCase(TestCase):
    """
    Unit tests for fortiDocs tool system
    """

    def test_construct_url(self):
        """ Create a url """
        sample_1 = {}
        sample_2 = {}
        sample_3 = {}

        with open("tests/samples/docs_query.json", "r") as f:
            samples_json = json.load(f)

        sample_1 = samples_json['results'][0]
        sample_2 = samples_json['results'][1]
        sample_3 = samples_json['results'][10]

        # sample 1

        self.assertEqual(
            _construct_url(sample_1), "https://docs.fortinet.com/document/fortiweb/7.2.1/cli-reference/257614/waf-ftp-protection-profile")
        self.assertEqual(
            _construct_url(sample_1, "6.3.0"), "https://docs.fortinet.com/document/fortiweb/6.3.0/cli-reference/257614/waf-ftp-protection-profile")
        self.assertEqual(
            _construct_url(sample_1, "7.0.3"), "https://docs.fortinet.com/document/fortiweb/7.0.3/cli-reference/257614/waf-ftp-protection-profile")
        self.assertEqual(
            _construct_url(sample_1, "6.3.0"), "https://docs.fortinet.com/document/fortiweb/6.3.0/cli-reference/257614/waf-ftp-protection-profile")

        # sample 2
        self.assertEqual(
            _construct_url(sample_2), "https://docs.fortinet.com/document/fortiadc/7.2.0/handbook/909/configuring-a-waf-profile")
        self.assertEqual(
            _construct_url(sample_2, "7.1.1"), "https://docs.fortinet.com/document/fortiadc/7.1.1/handbook/909/configuring-a-waf-profile")
        self.assertEqual(
            _construct_url(sample_2, "7.0.3"), "https://docs.fortinet.com/document/fortiadc/7.0.3/handbook/909/configuring-a-waf-profile")
        self.assertEqual(
            _construct_url(sample_2, "6.2.6"), "https://docs.fortinet.com/document/fortiadc/6.2.6/handbook/909/configuring-a-waf-profile")

        # sample 3
        self.assertEqual(
            _construct_url(sample_3), "https://docs.fortinet.com/document/fortigate/7.2.4/cli-reference/33848/waf")
        self.assertEqual(
            _construct_url(sample_3, "6.4.9"), "https://docs.fortinet.com/document/fortigate/6.4.9/cli-reference/17848/waf")
        self.assertEqual(
            _construct_url(sample_3, "7.0.1"), "https://docs.fortinet.com/document/fortigate/7.0.1/cli-reference/31848/waf")
        self.assertEqual(
            _construct_url(sample_3, "6.2.10"), "https://docs.fortinet.com/document/fortigate/6.2.10/cli-reference/17848/waf")

    def test_construct_collection_name(self):
        """ Create a collection name """
        samples = [
            {
                "product_tag": "fortiweb",
                "product_version": "7-2-1",
                "expected": "docs_fortiweb_7-2-1"
            },
            {
                "product_tag": "fortigate",
                "product_version": "7-0-9",
                "expected": "docs_fortigate_7-0-9"
            },
            {
                "product_tag": "fortios",
                "product_version": "6-4-9",
                "expected": "docs_fortios_6-4-9"
            },
            {
                "product_tag": "fortios",
                "product_version": "6-4-9",
                "expected": "docs_fortios_6-4-9"
            },
            {
                "product_tag": "fortisandbox",
                "product_version": "6-4-9",
                "expected": "docs_fortisandbox_6-4-9"
            },
            {
                "product_tag": "fortianalyzer",
                "product_version": "6-4-9",
                "expected": "docs_fortianalyzer_6-4-9"
            },
            {
                "product_tag": "fortimanager",
                "product_version": "6-4-9",
                "expected": "docs_fortimanager_6-4-9"
            },
            {
                "product_tag": "fortiap",
                "product_version": "6-4-9",
                "expected": "docs_fortiap_6-4-9"
            },
            {
                "product_tag": "fortiasic",
                "product_version": "6-4-9",
                "expected": "docs_fortiasic_6-4-9"
            },
            {
                "product_tag": "forticloud",
                "product_version": "6-4-9",
                "expected": "docs_forticloud_6-4-9"
            },
            {
                "product_tag": "fortiportal",
                "product_version": "6-4-9",
                "expected": "docs_fortiportal_6-4-9"
            },
            {
                "product_tag": "fortiswitch",
                "product_version": "6-4-9",
                "expected": "docs_fortiswitch_6-4-9"
            },
            {
                "product_tag": "fortiextender",
                "product_version": "6-4-9",
                "expected": "docs_fortiextender_6-4-9"
            }
        ]
        for test in samples:
            self.assertEqual(
                _construct_collection_name(test["product_tag"], test["product_version"]), test["expected"])
