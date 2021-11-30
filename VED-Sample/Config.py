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
 

# Global configuration dict object for the app
#
#   can be used as state as well
#
import datetime

# these are the defaults, they can be overwritten
state = {
    # file to read -- 'file://', 's3://' also supported
    'file': 'file:///988_465.csv',

    #
    # Timestamp handling
    #
    'time_col_name': 'Timestamp(ms)',                     # column name to use for time        
    #'timestamp_format': '%Y-%m-%d %H:%M:%S.%f',    # set to parse the time, otherwise, numeric is assumed
    'timestamp_offset': float((datetime.date.today() - datetime.timedelta(days=1)).strftime('%s')),                # if set, added to the timestamp values
    'time_scale': 1.0,                              # units/second -- e.g. 1000.0 means stamps in milliseconds

    # Select a Strategy from MessagePayload.py to define how to format a payload from the record
    'payload_strategy': 'SimpleLabelledPayload',

    # Topic to publish messages, different payload_strategies may need different templates using local vars
    'topic_name': "vt/cvra/{deviceid}/cardata/{timestamp_ms}",

    # throttle of messages per second
    'message_publish_rate': 10.0,

    # what to do at the end of the file... 'stop' or 'repeat'
    'at_end': 'stop',
}
