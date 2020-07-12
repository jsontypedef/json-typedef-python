import dataclasses
import enum
from typing import Any, Dict, List, Optional

class Form(enum.Enum):
    """
    Represents the "forms" a JSON Typedef schema can take on. The JSON Typedef
    spec restricts valid schemas to only using certain combinations of keywords.
    This enum represents which of those valid combinations a schema is using.
    """

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
    """
    Represents a JSON Typedef schema. To construct an instance of Schema, it's
    recommended you use :func:`from_dict`.

    >>> import jtd
    >>> schema = jtd.Schema.from_dict({ 'elements': { 'type': 'string' }})
    >>> schema.form()
    <Form.ELEMENTS: 5>
    >>> schema.elements.form()
    <Form.TYPE: 3>
    """

    metadata: Optional[Dict[str, Any]]
    """Additional metadata. Does not affect validation."""

    nullable: Optional[bool]
    """Describes data that can be JSON ``null`` (Python ``None``)."""

    definitions: Optional[Dict[str, 'Schema']]
    """A set of definitions that ``ref`` can refer to. Can only appear on root schemas."""

    ref: Optional[str]
    """A reference to a definition."""

    type: Optional[str]
    """Describes data that is a boolean, number, string, or timestamp."""

    enum: Optional[List[str]]
    """Describes data that must be in a predefined list of strings."""

    elements: Optional['Schema']
    """Describes arrays."""

    properties: Optional[Dict[str, 'Schema']]
    """Describes required properties of an object."""

    optional_properties: Optional[Dict[str, 'Schema']]
    """Describes optional properties of an object."""

    additional_properties: Optional[bool]
    """Describes whether there may be properties not in ``properties`` or ``optional_properties``."""

    values: Optional['Schema']
    """Describes the values of an object."""

    discriminator: Optional[str]
    """Specifies the "tag" property of an object, indicating what kind of data it contains."""

    mapping: Optional[Dict[str, 'Schema']]
    """Describes the data, depending on the value of the "tag" property of an object."""

    _KEYWORDS = [
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

    _TYPE_VALUES = [
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

    _VALID_FORMS = [
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
        """
        Instantiate a Schema from a dictionary. The dictionary should only
        contain types produced by ``json.loads``; otherwise, the output is not
        meaningful.

        >>> import jtd
        >>> jtd.Schema.from_dict({ 'elements': { 'type': 'string' }})
        Schema(metadata=None, nullable=None, definitions=None, ref=None, type=None, enum=None, elements=Schema(metadata=None, nullable=None, definitions=None, ref=None, type='string', enum=None, elements=None, properties=None, optional_properties=None, additional_properties=None, values=None, discriminator=None, mapping=None), properties=None, optional_properties=None, additional_properties=None, values=None, discriminator=None, mapping=None)
        """

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
            if k not in cls._KEYWORDS:
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
        """
        Checks whether a schema satisfies the semantic rules of JSON Typedef,
        such as ensuring that all refs have a corresponding definition.

        >>> import jtd
        >>> schema = jtd.Schema.from_dict({ 'ref': 'xxx' })
        >>> schema.validate()
        Traceback (most recent call last):
            ...
        TypeError: ref but no definitions
        """

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

        if self.type is not None and self.type not in self._TYPE_VALUES:
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

        if form_signature not in self._VALID_FORMS:
            raise TypeError("invalid form")

    def form(self) -> Form:
        """
        Determine the form of the schema. Meaningful only if :func:`validate`
        did not throw any exceptions.

        >>> import jtd
        >>> jtd.Schema.from_dict({}).form()
        <Form.EMPTY: 1>
        >>> jtd.Schema.from_dict({ 'enum': ['foo', 'bar' ]}).form()
        <Form.ENUM: 4>
        >>> jtd.Schema.from_dict({ 'elements': {} }).form()
        <Form.ELEMENTS: 5>
        """

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
