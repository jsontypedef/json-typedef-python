import unittest
import jtd
import json

# We skip these tests because strict_rfc3339 does not tolerate leap seconds.
SKIPPED_TESTS = [
    "timestamp type schema - 1990-12-31T23:59:60Z",
    "timestamp type schema - 1990-12-31T15:59:60-08:00",
]

class TestSchema(unittest.TestCase):
    def test_invalid_schemas(self):
        with open("json-typedef-spec/tests/validation.json") as f:
            test_cases = json.loads(f.read())
            for k, v in test_cases.items():
                with self.subTest(k):
                    if k in SKIPPED_TESTS:
                        self.skipTest("leap seconds in timestamps are not supported")

                    expected = [jtd.ValidationError(
                        instance_path=e["instancePath"],
                        schema_path=e["schemaPath"]
                    ) for e in v["errors"]]

                    schema = jtd.Schema.from_dict(v["schema"])
                    actual = jtd.validate(schema=schema, instance=v["instance"])
                    self.assertEqual(expected, actual)
