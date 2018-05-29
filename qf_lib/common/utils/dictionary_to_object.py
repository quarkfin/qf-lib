def dict_to_object(d):
    obj_type = type('ObjectFromDict', (object,), d)
    return _dict_to_obj(d, obj_type)


def _dict_to_obj(d, obj_type):
    obj = obj_type()
    seqs = tuple, list, set, frozenset
    for i, j in d.items():
        if isinstance(j, dict):
            setattr(obj, i, _dict_to_obj(j, obj_type))
        elif isinstance(j, seqs):
            setattr(obj, i,
                    type(j)(_dict_to_obj(sj, obj_type) if isinstance(sj, dict) else sj for sj in j))
        else:
            setattr(obj, i, j)

    return obj
