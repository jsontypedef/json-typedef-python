import dataclasses
import strict_rfc3339
from typing import Any, List, Optional

from .schema import Form, Schema

@dataclasses.dataclass
class ValidationError:
    instance_path: List[str]
    schema_path: List[str]

@dataclasses.dataclass
class ValidationOptions:
    max_depth: int = 0
    max_errors: int = 0

def validate(**kwargs) -> List[ValidationError]:
    state = _ValidationState(
        config=kwargs.get('opts', ValidationOptions()),
        root_schema=kwargs['schema'],
        instance_tokens=[],
        schema_tokens=[[]],
        errors=[],
    )

    _validate_with_state(state, kwargs['schema'], kwargs['instance'], None)
    return state.errors

@dataclasses.dataclass
class _ValidationState:
    config: ValidationOptions
    root_schema: Schema
    instance_tokens: List[str]
    schema_tokens: List[List[str]]
    errors: List[ValidationError]

    def push_instance_token(self, token):
        self.instance_tokens.append(token)

    def pop_instance_token(self):
        self.instance_tokens.pop()

    def push_schema_token(self, token):
        self.schema_tokens[-1].append(token)

    def pop_schema_token(self):
        self.schema_tokens[-1].pop()

    def push_error(self):
        self.errors.append(ValidationError(
            instance_path=self.instance_tokens.copy(),
            schema_path=self.schema_tokens[-1].copy(),
        ))

def _validate_with_state(state: _ValidationState, schema: Schema, instance: Any, parent_tag: Optional[str]):
    if schema.nullable and instance is None:
        return

    form = schema.form()
    if form == form.REF:
        state.schema_tokens.append(["definitions", schema.ref])
        _validate_with_state(state, state.root_schema.definitions[schema.ref], instance, None)
        state.schema_tokens.pop()
    elif form == form.TYPE:
        state.push_schema_token("type")

        if schema.type == "boolean":
            if type(instance) is not bool:
                state.push_error()
        elif schema.type == "float32" or schema.type == "float64":
            if type(instance) not in [int, float]:
                state.push_error()
        elif schema.type == "int8":
            _validate_int(state, -128, 127, instance)
        elif schema.type == "uint8":
            _validate_int(state, 0, 255, instance)
        elif schema.type == "int16":
            _validate_int(state, -32768, 32767, instance)
        elif schema.type == "uint16":
            _validate_int(state, 0, 65535, instance)
        elif schema.type == "int32":
            _validate_int(state, -2147483648, 2147483647, instance)
        elif schema.type == "uint32":
            _validate_int(state, 0, 4294967295, instance)
        elif schema.type == "string":
            if type(instance) is not str:
                state.push_error()
        elif type(instance) is not str or not strict_rfc3339.validate_rfc3339(instance):
                state.push_error()

        state.pop_schema_token()
    elif form == form.ENUM:
        state.push_schema_token("enum")
        if instance not in schema.enum:
            state.push_error()
        state.pop_schema_token()
    elif form == form.ELEMENTS:
        state.push_schema_token("elements")
        if type(instance) is list:
            for i, v in enumerate(instance):
                state.push_instance_token(str(i))
                _validate_with_state(state, schema.elements, v, None)
                state.pop_instance_token()
        else:
            state.push_error()
        state.pop_schema_token()
    elif form == form.PROPERTIES:
        if type(instance) is dict:
            state.push_schema_token("properties")
            for k, v in (schema.properties or {}).items():
                state.push_schema_token(k)
                if k in instance:
                    state.push_instance_token(k)
                    _validate_with_state(state, v, instance[k], None)
                    state.pop_instance_token()
                else:
                    state.push_error()
                state.pop_schema_token()
            state.pop_schema_token()

            state.push_schema_token("optionalProperties")
            for k, v in (schema.optional_properties or {}).items():
                state.push_schema_token(k)
                if k in instance:
                    state.push_instance_token(k)
                    _validate_with_state(state, v, instance[k], None)
                    state.pop_instance_token()
                state.pop_schema_token()
            state.pop_schema_token()

            if not schema.additional_properties:
                for k in instance:
                    in_props = k in (schema.properties or {})
                    in_opt_props = k in (schema.optional_properties or {})

                    if not in_props and not in_opt_props and k != parent_tag:
                        state.push_instance_token(k)
                        state.push_error()
                        state.pop_instance_token()
        elif schema.properties is not None:
            state.push_schema_token("properties")
            state.push_error()
            state.pop_schema_token()
        else:
            state.push_schema_token("optionalProperties")
            state.push_error()
            state.pop_schema_token()
    elif form == form.VALUES:
        state.push_schema_token("values")
        if type(instance) is dict:
            for k, v in instance.items():
                state.push_instance_token(k)
                _validate_with_state(state, schema.values, v, None)
                state.pop_instance_token()
        else:
            state.push_error()
        state.pop_schema_token()
    elif form == form.DISCRIMINATOR:
        if type(instance) is dict:
            if schema.discriminator in instance:
                if type(instance[schema.discriminator]) is str:
                    if instance[schema.discriminator] in schema.mapping:
                        sub_schema = schema.mapping[instance[schema.discriminator]]
                        parent_tag = schema.discriminator

                        state.push_schema_token("mapping")
                        state.push_schema_token(instance[schema.discriminator])
                        _validate_with_state(state, sub_schema, instance, parent_tag)
                        state.pop_schema_token()
                        state.pop_schema_token()
                    else:
                        state.push_schema_token("mapping")
                        state.push_instance_token(schema.discriminator)
                        state.push_error()
                        state.pop_instance_token()
                        state.pop_schema_token()
                else:
                    state.push_schema_token("discriminator")
                    state.push_instance_token(schema.discriminator)
                    state.push_error()
                    state.pop_instance_token()
                    state.pop_schema_token()
            else:
                state.push_schema_token("discriminator")
                state.push_error()
                state.pop_schema_token()
        else:
            state.push_schema_token("discriminator")
            state.push_error()
            state.pop_schema_token

def _validate_int(state: _ValidationState, min: int, max: int, instance: Any):
    if type(instance) not in [int, float]:
        state.push_error()
        return

    if int(instance) != instance or instance < min or instance > max:
        state.push_error()
