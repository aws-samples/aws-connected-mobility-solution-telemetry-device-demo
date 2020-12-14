# Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
# SPDX-License-Identifier: MIT-0
#
# Permission is hereby granted, free of charge, to any person obtaining a copy of this
# software and associated documentation files (the "Software"), to deal in the Software
# without restriction, including without limitation the rights to use, copy, modify,
# merge, publish, distribute, sublicense, and/or sell copies of the Software, and to
# permit persons to whom the Software is furnished to do so.
#
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR IMPLIED,
# INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY, FITNESS FOR A
# PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE AUTHORS OR COPYRIGHT
# HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER LIABILITY, WHETHER IN AN ACTION
# OF CONTRACT, TORT OR OTHERWISE, ARISING FROM, OUT OF OR IN CONNECTION WITH THE
# SOFTWARE OR THE USE OR OTHER DEALINGS IN THE SOFTWARE.

# MessagePayload
#
#   Takes dict of keys/vals and makes a formatted payload message.
# Implemented as factory pattern that allows for variations in message formatting.
#

from abc import ABC, abstractmethod

class MessagePayload(ABC):
    # pass array of keys to remove from message BEFORE or AFTER formatting
    # allows for subclasses to use data and then remove it
    #
    #   Typically, the caller will only supply preDropKeys if any and 
    # subclasses would set the postDropKeys as needed.
    #
    def __init__(self, d, config={'preDropKeys':[], 'postDropKeys':[]}) -> None:
        self.payload = {}
        self.preDropKeys = config.get('preDropKeys', [])
        self.preDropKeys.append('')
        self.postDropKeys = config.get('postDropKeys', [])
        self._prepare_message(d)

    def _prepare_message(self, d):
        [ d.pop(k) for k in (set(self.preDropKeys) & set(d.keys())) ]
        self.payload = d.copy()
        self.make_message(d)
        [ self.payload.pop(k) for k in (set(self.postDropKeys) & set(self.payload.keys())) ]
    
    def message(self, formatter=None):
        return self.payload if formatter == None else formatter(self.payload)

    @abstractmethod
    def make_message(self, d):
        raise NotImplementedError("MessagePayload must be subclassed with an implementation of #prepare_message")

# SimpleLabelled Strategy just returns the dict
#   the dict is assumed to be structured with 'key': value
# so no changes.
class SimpleLabelledPayload(MessagePayload):
    def make_message(self, d):
        # self.payload = d.copy()
        pass

# DynamicLabelledPayload takes apart the dict and builds the payload
#   the dict is of the format 'name': metric, 'value': reading
# and will be reformatted to 'metric': reading
#
class DynamicLabelledPayload(MessagePayload):
    def __init__(self, d, config={'metricKey':'status', 'readingKey':'value', 'value_transform_function': float}) -> None:
        self.metricKey = config.get('metricKey', 'status')
        self.readingKey = config.get('readingKey', 'value')
        self.transform = config.get('value_transform_function', float)

        pdk = config.get('postDropKeys', [])
        pdk.extend([self.metricKey, self.readingKey])
        config['postDropKeys'] = pdk

        super().__init__(d, config)

    def make_message(self, d):
        try:
            self.payload[d[self.metricKey]] = self.transform(d[self.readingKey])
        except Exception as e:
            print("key or value didn't exist")

# UntimedDynamicLabelledPayload removes the timestamp from the payload
#   
class UntimedDynamicLabelledPayload(DynamicLabelledPayload):
    def __init__(self, d, config={'metricKey':'status', 'readingKey':'value', 'time_col_name': 'timestamp'}) -> None:
        self.time_col_name = config.get('time_col_name', 'timestamp')
        pdk = config.get('postDropKeys', [])
        pdk.extend([self.time_col_name])
        config['postDropKeys'] = pdk

        super().__init__(d, config)