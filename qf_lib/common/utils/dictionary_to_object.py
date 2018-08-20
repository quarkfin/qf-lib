class JsonToObjectConverter(object):
    @classmethod
    def dict_to_object(cls, dictionary):
        obj_type = type('ObjectFromDict', (object,), dictionary)
        obj = obj_type()
        for attr_name, attr_value in dictionary.items():
            setattr(obj, attr_name, cls._to_obj_if_necessary(attr_value))

        return obj

    @classmethod
    def sequence_to_obj(cls, sequence):
        result = (cls._to_obj_if_necessary(elem) for elem in sequence)
        return result

    @classmethod
    def _to_obj_if_necessary(cls, value):
        import collections

        if isinstance(value, collections.Mapping):
            result = cls.dict_to_object(value)
        elif isinstance(value, collections.Sequence) and not isinstance(value, str):
            result = cls.sequence_to_obj(value)
        else:
            result = value

        return result
