import unittest
import jtd
import json

class TestSchema(unittest.TestCase):
    def test_invalid_schemas(self):
        with open("json-typedef-spec/tests/invalid_schemas.json") as f:
            invalid_schemas = json.loads(f.read())
            for k, v in invalid_schemas.items():
                with self.subTest(k):
                    with self.assertRaises(BaseException) as c:
                        schema = jtd.Schema.from_dict(v)
                        schema.validate()

                    self.assertIsInstance(c.exception, (AttributeError, TypeError))
