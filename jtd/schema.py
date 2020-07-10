import dataclasses
import enum
from typing import Any, Dict, List, Optional

class Form(enum.Enum):
    EMPTY = enum.auto()
    REF = enum.auto()
    TYPE = enum.auto()
    ENUM = enum.auto()
    ELEMENTS = enum.auto()
    PROPERTIES = enum.auto()
    VALUES = enum.auto()
    DISCRIMINATOR = enum.auto()

@dataclasses.dataclass
class Schema:
    metadata: Optional[Dict[str, Any]]
    nullable: Optional[bool]
    definitions: Optional[Dict[str, 'Schema']]
    ref: Optional[str]
    type: Optional[str]
    enum: Optional[List[str]]
    elements: Optional['Schema']
    properties: Optional[Dict[str, 'Schema']]
    optional_properties: Optional[Dict[str, 'Schema']]
    additional_properties: Optional[bool]
    values: Optional['Schema']
    discriminator: Optional[str]
    mapping: Optional[Dict[str, 'Schema']]

    KEYWORDS = [
        "metadata",
        "nullable",
        "definitions",
        "ref",
        "type",
        "enum",
        "elements",
        "properties",
        "optionalProperties",
        "additionalProperties",
        "values",
        "discriminator",
        "mapping",
    ]

    TYPE_VALUES = [
        'boolean',
        'int8',
        'uint8',
        'int16',
        'uint16',
        'int32',
        'uint32',
        'float32',
        'float64',
        'string',
        'timestamp',
    ]

    VALID_FORMS = [
        # Empty form
        [False, False, False, False, False, False, False, False, False, False],
        # Ref form
        [True, False, False, False, False, False, False, False, False, False],
        # Type form
        [False, True, False, False, False, False, False, False, False, False],
        # Enum form
        [False, False, True, False, False, False, False, False, False, False],
        # Elements form
        [False, False, False, True, False, False, False, False, False, False],
        # Properties form -- properties or optional properties or both, and
        # never additional properties on its own
        [False, False, False, False, True, False, False, False, False, False],
        [False, False, False, False, False, True, False, False, False, False],
        [False, False, False, False, True, True, False, False, False, False],
        [False, False, False, False, True, False, True, False, False, False],
        [False, False, False, False, False, True, True, False, False, False],
        [False, False, False, False, True, True, True, False, False, False],
        # Values form
        [False, False, False, False, False, False, False, True, False, False],
        # Discriminator form
        [False, False, False, False, False, False, False, False, True, True],
    ]

    @classmethod
    def from_dict(cls, dict: Dict[str, Any]) -> 'Schema':
        definitions = None
        if "definitions" in dict:
            definitions = { k: cls.from_dict(v) for k, v in dict["definitions"].items() }

        elements = None
        if "elements" in dict:
            elements = cls.from_dict(dict["elements"])

        properties = None
        if "properties" in dict:
            properties = { k: cls.from_dict(v) for k, v in dict["properties"].items() }

        optional_properties = None
        if "optionalProperties" in dict:
            optional_properties = { k: cls.from_dict(v) for k, v in dict["optionalProperties"].items() }

        values = None
        if "values" in dict:
            values = cls.from_dict(dict["values"])

        mapping = None
        if "mapping" in dict:
            mapping = { k: cls.from_dict(v) for k, v in dict["mapping"].items() }

        for k in dict.keys():
            if k not in cls.KEYWORDS:
                raise AttributeError("illegal keyword")

        return Schema(
            metadata=dict.get("metadata"),
            nullable=dict.get("nullable"),
            definitions=definitions,
            ref=dict.get("ref"),
            type=dict.get("type"),
            enum=dict.get("enum"),
            elements=elements,
            properties=properties,
            optional_properties=optional_properties,
            additional_properties=dict.get("additionalProperties"),
            values=values,
            discriminator=dict.get("discriminator"),
            mapping=mapping,
        )

    def validate(self, root=None):
        if root is None:
            root = self

        if self.definitions is not None:
            if self is not root:
                raise TypeError("non-root definitions")

            for v in self.definitions.values():
                v.validate(root)

        if self.nullable is not None and type(self.nullable) is not bool:
            raise TypeError("nullable not bool")

        if self.ref is not None:
            if type(self.ref) is not str:
                raise TypeError("ref not string")

            if type(root.definitions) is not dict:
                raise TypeError("ref but no definitions")

            if self.ref not in root.definitions:
                raise TypeError("ref to non-existent definition")

        if self.type is not None and self.type not in self.TYPE_VALUES:
            raise TypeError("type not valid string value")

        if self.enum is not None:
            if type(self.enum) is not list:
                raise TypeError("enum not list")

            if len(self.enum) == 0:
                raise TypeError("enum is empty")

            for v in self.enum:
                if type(v) is not str:
                    raise TypeError("enum not list of strings")

            if len(self.enum) != len(set(self.enum)):
                raise TypeError("enum contains duplicates")

        if self.elements is not None:
            self.elements.validate(root)

        if self.properties is not None:
            for v in self.properties.values():
                v.validate(root)

        if self.optional_properties is not None:
            for v in self.optional_properties.values():
                v.validate(root)

        if self.properties is not None and self.optional_properties is not None:
            if set(self.properties).intersection(self.optional_properties):
                raise TypeError("properties shares keys with optional_properties")

        if self.additional_properties is not None:
            if type(self.additional_properties) is not str:
                raise TypeError("additional_properties not string")

        if self.values is not None:
            self.values.validate(root)

        if self.discriminator is not None:
            if type(self.discriminator) is not str:
                raise TypeError("discriminator not string")

        if self.mapping is not None:
            for v in self.mapping.values():
                v.validate(root)

                if v.nullable:
                    raise TypeError("mapping value is nullable")

                if v.form() != Form.PROPERTIES:
                    raise TypeError("mapping value not of properties form")

                if self.discriminator in (v.properties or {}):
                    raise TypeError("mapping properties redefines discriminator")

                if self.discriminator in (v.optional_properties or {}):
                    raise TypeError("mapping optional_properties redefines discriminator")

        form_signature = [
            self.ref is not None,
            self.type is not None,
            self.enum is not None,
            self.elements is not None,
            self.properties is not None,
            self.optional_properties is not None,
            self.additional_properties is not None,
            self.values is not None,
            self.discriminator is not None,
            self.mapping is not None,
        ]

        if form_signature not in self.VALID_FORMS:
            raise TypeError("invalid form")

    def form(self) -> Form:
        if self.ref is not None:
            return Form.REF
        if self.type is not None:
            return Form.TYPE
        if self.enum is not None:
            return Form.ENUM
        if self.elements is not None:
            return Form.ELEMENTS
        if self.properties is not None or self.optional_properties is not None:
            return Form.PROPERTIES
        if self.values is not None:
            return Form.VALUES
        if self.discriminator is not None:
            return Form.DISCRIMINATOR
        return Form.EMPTY
