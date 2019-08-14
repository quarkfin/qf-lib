#     Copyright 2016-present CERN – European Organization for Nuclear Research
#
#     Licensed under the Apache License, Version 2.0 (the "License");
#     you may not use this file except in compliance with the License.
#     You may obtain a copy of the License at
#
#         http://www.apache.org/licenses/LICENSE-2.0
#
#     Unless required by applicable law or agreed to in writing, software
#     distributed under the License is distributed on an "AS IS" BASIS,
#     WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
#     See the License for the specific language governing permissions and
#     limitations under the License.

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
