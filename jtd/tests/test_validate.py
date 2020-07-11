import unittest
import jtd
import json

# We skip these tests because strict_rfc3339 does not tolerate leap seconds.
SKIPPED_TESTS = [
    "timestamp type schema - 1990-12-31T23:59:60Z",
    "timestamp type schema - 1990-12-31T15:59:60-08:00",
]

class TestSchema(unittest.TestCase):
    def test_max_depth(self):
        schema = jtd.Schema.from_dict({
            'definitions': { 'loop': { 'ref': 'loop' }},
            'ref': 'loop'
        })

        with self.assertRaises(jtd.MaxDepthExceededError):
            options = jtd.ValidationOptions(max_depth=32)
            jtd.validate(schema=schema, instance=None, options=options)

    def test_max_errors(self):
        schema = jtd.Schema.from_dict({ 'elements': { 'type': 'string' }})
        instance = [None, None, None, None, None]
        options = jtd.ValidationOptions(max_errors=3)
        errors = jtd.validate(schema=schema, instance=instance, options=options)

        self.assertEqual(3, len(errors))

    def test_validation(self):
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
