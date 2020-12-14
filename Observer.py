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

# Basic (simplistic?) implementation of Observer pattern
#

''' To Use:
- subclass Observable for a thing that chagnes
- subclass Observer for the things that will use those changes

- Observers call Observable's #addObserver to register and #removeObserver to stop

- When the thing (the Observable) changes, #notifyObservers calls all the Observers
'''




class Observer:
    def update(observable, arg):
        '''Called when observed object is modified, from list
        of Observers in object via notifyObservers.
        Observers must first register with Observable.'''
        pass

'''NOTE: NOT Implementing the thread synchronization from
https://python-3-patterns-idioms-test.readthedocs.io/en/latest/Observer.html
for simplicity'''

class Observable:
    def __init__(self):
        self.observers = []
        self.changed = False
    
    def addObserver(self, observer):
        if observer not in self.observers:
            self.observers.append(observer)

    def removeObserver(self, observer):
        self.observers.remove(observer)

    def notifyObservers(self, arg = None):
        try:
            observers = self.observers
            self.changed = False

            for o in observers:
                o.update(arg)
        except Exception as err:
            pass


# an observable chunk of raw data from the serial port, or a file, or ?
class ObservableString(Observable):
    def __init__(self):
        super().__init__()
        self.clear()

    def clear(self):
        self.chunk = b''

    # call to add to the end of the chunk, notifies observers
    def append(self, increment):
        if len(increment) > 0:
            self.chunk = self.chunk + increment

            self.notifyObservers(self.chunk)
            self.clear()

# an Observaable wrapped array
class ObservableFlatArray(Observable):
    def __init__(self):
        super().__init__()
        self.clear()

    def clear(self):
        self.elements = []

    def append(self, newElements):
        if len(newElements) > 0:
            self.elements.extend(newElements)

            self.notifyObservers(self.elements)
            self.clear()

# ObservableArray is 'flat' in that it will be extended with the new elements.
# sometimes you want to append a deep object to the array... 
#
#   use ObservableDeepArray for that
class ObservableDeepArray(Observable):
    def __init__(self):
        super().__init__()
        self.clear()

    def clear(self):
        self.elements = []

    def append(self, newItem):
        if len(newItem) > 0:
            self.elements.append(newItem)

            self.notifyObservers(self.elements)
            self.clear()

# an Observable wrapped dict
class ObservableDict(Observable):
    def __init__(self):
        super().__init__()
        self.clear()

    def clear(self):
        self.dict = {}

    def append(self, newDict):
        if len(newDict) > 0:
            self.dict.update(newDict)

            self.notifyObservers(self.dict)

    def getDict(self):
        return self.dict

    