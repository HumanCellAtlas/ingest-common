from unittest import TestCase

from ingest.importer.json_to_ingest import JsonToIngest
import ingest.utils.token_util as token_util


class TestJsonToIngest(TestCase):

    def setUp(self):
        pass

    def test_submit(self):
        json_to_ingest = JsonToIngest()
        json_to_ingest.submit(token_util.get_token(), "example.json")
