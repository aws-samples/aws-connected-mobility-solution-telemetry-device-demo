#!/usr/bin/python3

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


import numpy as np
import time


metrics = [
    # jittered time
    { 'name': 'Timestamp(ms)', 'method': np.random.normal, 'params': [5000, 1000]},

    # simulated measures -- SET DESIRED METRICS AND RANDOMIZATION HERE
    { 'name': 'e.t', 'method': np.random.normal, 'params': [18.0, 2.0]},
    { 'name': 'e.h', 'method': np.random.normal, 'params': [35.0, 5.0]},
    { 'name': 'l', 'method': np.random.choice, 'params': [[ {'c':{'o':'AT&T', 'a':[{'i':1704310, 'l':56986, 'c':310, 'n':410}]}},
                                                            {'c':{'o':'AT&T', 'a':[{'i':1707951, 'l':56986, 'c':310, 'n':410}]}},
                                                            {'c':{'o':'AT&T', 'a':[{'i':1704630, 'l':56986, 'c':310, 'n':410}]}} ]] }
]               
separator = "\t"


# shouldn't generally need to modify anything below here
print(separator.join([ f"\"{m['name']}\"" for m in metrics ]))

while True:
    data = [ m['method'](*m['params']) for m in metrics ]
    delay = data[0]/950     # delay by 95% of the generated timestamp to keep ahead of consumer
    print(separator.join([ f"\"{d}\"" for d in data ]), flush=True)

    time.sleep(delay)
