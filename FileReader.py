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

# FileReader
#

import boto3
from pathlib import Path

from Config import state

class FileReader():
    def __init__(self, fileURI = None, local_dir = "/tmp", record_separator=",", quote_records=False):
        super().__init__()
        self.file = None

        self.local_dir = local_dir
        self.record_separator = record_separator
        self.quote_records = quote_records

        self._setLocalFile(None)
        self.useFileURI(fileURI)


    def __del__(self):
        self.close()

    def useFileURI(self, fileURI):
        if self.getFileURI() == fileURI:
            return

        if self.isOpen():
            self.close()
        self.cols = []
        self.fileURI = fileURI
        self.open()
        

    def getFileURI(self):
        uri = None
        try:
            uri = self.fileURI
        except Exception as e:
            pass
        finally:
            return uri

    def isOpen(self):
        return (self.file is not None)

    def _getLocalFilePath(self, key):
        return "/".join([self.local_dir, key])
        
    def _setLocalFile(self, filename):
        self.localFile = filename

    def _fetchFromS3(self, bucket, key):
        s3 = boto3.client('s3')

        localFile = self._getLocalFilePath(key)
        result = s3.download_file(bucket, key, localFile)

        self.localFile = localFile        

    def _fetchFileFromURI(self):
        try:
            handlers = { 's3:': self._fetchFromS3 }
            src = self.fileURI.split("/")

            protocol = src[0]

            bucket = src[2]
            key = "/".join(src[3:])

            # check local cache before downloading
            localFile = self._getLocalFilePath(key)
            if Path(localFile).is_file():
                self._setLocalFile(localFile)
            else:
                handlers[protocol](bucket, key)
        except Exception as err:
            pass
        
    def open(self):
        try:
            if self.localFile == None:
                self._fetchFileFromURI()

            self.file = open(self.localFile, 'r')
            header = self.file.readline().rstrip()
            self.cols = header.split(self.record_separator)
            if self.quote_records:
                self.cols = [ c.strip('"') for c in self.cols ]
        except Exception as err:
            print(f'error opening {self.localFile}: {err}')

    def close(self):
        if self.isOpen():
            self.file.close()
            self.file = None
            self.localFile = None

    def _makeSample(self, lineCSV):
        sample = {}
        line = lineCSV.split(self.record_separator)
        if self.quote_records:
            line = [ c.strip('"') for c in line ]
        for i in range(0, len(self.cols)):
            sample[self.cols[i]] = line[i] 

        return sample

    def getSample(self):
        readbuffer = {}
        try:
            readbuffer = self._makeSample(self.file.readline().rstrip())
        except IndexError as ie:
            print("End of File Reached...")
            self.close()
            if state['at_end'] == 'repeat':
                self.open()
        except Exception as e:
            print("Exception while reading from file")

        return readbuffer
