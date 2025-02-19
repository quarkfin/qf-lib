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
from typing import Optional, Dict


class Element:
    def __init__(self, name, value: Optional = None):
        self.name = name
        self.value = value

    def setValue(self, value):
        self.value = value

    def appendValue(self, value):
        if self.value is None:
            self.value = [value]
        else:
            self.value.append(value)

    def getElementAsFloat(self):
        return float(self.value)

    def getElementAsDatetime(self):
        return self.value

    def getElementAsString(self):
        return str(self.value)

    def __eq__(self, other):
        return self.name == other.name and self.value == other.value

    def __hash__(self):
        return hash(self.name, self.value)


class Request:
    def __init__(self, elements: Optional[Dict] = None):
        self.elements = elements if elements is not None else {}

    def getElement(self, name):
        if name not in self.elements:
            new_element = Element(name)
            self.elements[name] = new_element

        return self.elements[name]

    def set(self, name, value):
        element = self.getElement(name)
        element.setValue(value)

    def __eq__(self, other):
        return self.elements == other.elements
