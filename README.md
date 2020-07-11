# jtd: JSON Validation for Python

[![PyPI](https://img.shields.io/pypi/v/jtd)](https://pypi.org/project/jtd)

> This package implements JSON Typedef *validation* for JavaScript and
> TypeScript. If you're trying to do JSON Typedef *code generation*, see
> ["Generating TypeScript from JSON Typedef Schemas"][jtd-ts-codegen] in the
> JSON Typedef docs.

`jtd` is a Python implementation of [JSON Type Definition][jtd], a schema
language for JSON. `jtd` primarily gives you two things:

1. Validating input data against JSON Typedef schemas.
2. A Python representation of JSON Typedef schemas.

With this package, you can add JSON Typedef-powered validation to your
application, or you can build your own tooling on top of JSON Type Definition.

## Installation

You can install this package with `pip`:

```bash
pip install jtd
```

## Documentation

Detailed API documentation is available online at:

https://jtd.readthedocs.io

For more high-level documentation about JSON Typedef in general, or JSON Typedef
in combination with Python in particular, see:

* [The JSON Typedef Website][jtd]
* ["Validating JSON in Python with JSON Typedef"][jtd-py-validation]
* ["Generating Python from JSON Typedef Schemas"][jtd-py-codegen]

## Basic Usage

> For a more detailed tutorial and guidance on how to integrate `jtd` in your
> application, see ["Validating JSON in JavaScript with JSON
> Typedef"][jtd-py-validation] in the JSON Typedef docs.

Here's an example of how you can use this package to validate JSON data against
a JSON Typedef schema:

```python
import jtd

schema = jtd.Schema.from_dict({
    'properties': {
        'name': { 'type': 'string' },
        'age': { 'type': 'uint32' },
        'phones': {
            'elements': {
                'type': 'string'
            }
        }
    }
})

# jtd.validate returns an array of validation errors. If there were no problems
# with the input, it returns an empty array.

# Outputs: []
print(jtd.validate(schema=schema, instance={
  'name': 'John Doe',
  'age': 43,
  'phones': ['+44 1234567', '+44 2345678'],
}))

# This next input has three problems with it:
#
# 1. It's missing "name", which is a required property.
# 2. "age" is a string, but it should be an integer.
# 3. "phones[1]" is a number, but it should be a string.
#
# Each of those errors corresponds to one of the errors returned by validate.

# Outputs:
#
# [
#   ValidationError(
#     instance_path=[], schema_path=['properties', 'name']
#   ),
#   ValidationError(
#     instance_path=['age'], schema_path=['properties', 'age', 'type']
#   ),
#   ValidationError(
#     instance_path=['phones', '1'], schema_path=['properties', 'phones', 'elements', 'type']
#   ),
# ]
print(jtd.validate(schema=schema, instance={
  'age': "43",
  'phones': ["+44 1234567", 442345678],
}))
```

## Advanced Usage: Limiting Errors Returned

By default, `jtd.validate` returns every error it finds. If you just care about
whether there are any errors at all, or if you can't show more than some number
of errors, then you can get better performance out of `jtd.validate` using the
`max_errors` option.

For example, taking the same example from before, but limiting it to 1 error, we
get:

```python
# Outputs:
#
# [ValidationError(instance_path=[], schema_path=['properties', 'name'])]
options = jtd.ValidationOptions(max_errors=1)
print(jtd.validate(schema=schema, options=options, instance={
  'age': '43',
  'phones': ['+44 1234567', 442345678],
}))
```

## Advanced Usage: Handling Untrusted Schemas

If you want to run `jtd` against a schema that you don't trust, then you should:

1. Ensure the schema is well-formed, using the `validate()` method on
   `jtd.Schema`. That will check things like making sure all `ref`s have
   corresponding definitions.

2. Call `jtd.validate` with the `max_depth` option. JSON Typedef lets you write
   recursive schemas -- if you're evaluating against untrusted schemas, you
   might go into an infinite loop when evaluating against a malicious input,
   such as this one:

   ```json
   {
     "ref": "loop",
     "definitions": {
       "loop": {
         "ref": "loop"
       }
     }
   }
   ```

   The `max_depth` option tells `jtd.validate` how many `ref`s to follow
   recursively before giving up and throwing `jtd.MaxDepthExceededError`.

Here's an example of how you can use `jtd` to evaluate data against an untrusted
schema:

```python
import jtd

# validate_untrusted returns true if `data` satisfies `schema`, and false if it
# does not. Throws an error if `schema` is invalid, or if validation goes in an
# infinite loop.
def validate_untrusted(schema, data):
    schema.validate()

    # You should tune maxDepth to be high enough that most legitimate schemas
    # evaluate without errors, but low enough that an attacker cannot cause a
    # denial of service attack.
    options = jtd.ValidationOptions(max_depth=32)
    return len(jtd.validate(schema=schema, instance=data, options=options)) == 0
}

# Returns true
validate_untrusted(jtd.Schema.from_dict({ 'type': 'string' }), 'foo')

# Returns false
validate_untrusted(jtd.Schema.from_dict({ 'type': 'string' }), None)

# Throws "invalid schema"
validate_untrusted(jtd.Schema.from_dict({ 'type': 'nonsense' }), 'foo')

# Throws an instance of jtd.MaxDepthExceededError
validate_untrusted({
  "ref": "loop",
  "definitions": {
    "loop": {
      "ref": "loop"
    }
  }
}, None)
```

[jtd]: https://jsontypedef.com
[jtd-py-codegen]: https://jsontypedef.com/docs/python/code-generation
[jtd-py-validation]: https://jsontypedef.com/docs/python/validation
