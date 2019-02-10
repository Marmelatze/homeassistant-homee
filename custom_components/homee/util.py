

def get_attr_by_type(node, type):
    for attr in node.attributes:
        if attr.type == type:
            return attr
    return None


def get_attr_type(attr):
    """get attribute name by its type"""
    from pyhomee.const import ATTRIBUTE_TYPES_LOOKUP
    return ATTRIBUTE_TYPES_LOOKUP.get(attr.type, ATTRIBUTE_TYPES_LOOKUP[0])
