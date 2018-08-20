def dict_to_object(d):
    obj_type = type('ObjectFromDict', (object,), d)
    return _dict_to_obj(d, obj_type)


def _dict_to_obj(d, obj_type):
    obj = obj_type()
    seqs = tuple, list, set, frozenset
    for attr_name, attr_value in d.items():
        if isinstance(attr_value, dict):
            setattr(obj, attr_name, _dict_to_obj(attr_value, obj_type))
        elif isinstance(attr_value, seqs):
            setattr(obj, attr_name,
                    type(attr_value)(_dict_to_obj(sj, obj_type) if isinstance(sj, dict) else sj for sj in attr_value))
        else:
            setattr(obj, attr_name, attr_value)

    return obj
