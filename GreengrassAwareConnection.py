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

# GreengrassAwareConnection.py
#
#   class to connect to IoT core or gg based on discovery.
# methods to publish to topic, subscribe, shadow, etc.
#
#   Based on v 1 of the Python SKD
#

import json
import logging
import os
import time
import uuid

from AWSIoTPythonSDK.core.greengrass.discovery.providers import DiscoveryInfoProvider
from AWSIoTPythonSDK.core.protocol.connection.cores import ProgressiveBackOffCore
from AWSIoTPythonSDK.exception.AWSIoTExceptions import DiscoveryFailure, DiscoveryInvalidRequestException, publishQueueFullException
from AWSIoTPythonSDK.core.protocol.paho.client import MQTT_ERR_SUCCESS
from AWSIoTPythonSDK.exception.AWSIoTExceptions import publishError

from AWSIoTPythonSDK.MQTTLib import *


class Obj(object):
    pass

class GreengrassAwareConnection:
    def __init__(self, host, rootCA, cert, key, thingName, stateChangeQueue = None, config={}):
        self.logger = logging.getLogger("GreengrassAwareConnection")
        self.logger.setLevel(logging.DEBUG)
        streamHandler = logging.StreamHandler()
        formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
        streamHandler.setFormatter(formatter)
        self.logger.addHandler(streamHandler)
        
        self.config = config
        self.max_discovery_retries = self.config.get('MAX_DISCOVERY_RETRIES', 10)
        self.group_ca_path = self.config.get('GROUP_CA_PATH', "./groupCA/")
        self.offline_queue_depth = self.config.get('OFFLINE_QUEUE_DEPTH', 10)

        self.host = host
        self.rootCA = rootCA
        self.cert = cert
        self.key = key
        self.thingName = thingName

        self.stateChangeQueue = stateChangeQueue

        self.backOffCore = ProgressiveBackOffCore()

        self.discovered = False
        self.discoverBroker()

        self.connected = False
        self.connect()

        self.shadowConnected = False
        self.connectShadow()

        self.published_ids = []

    def hasDiscovered(self):
        return self.discovered


    def discoverBroker(self):
        if self.hasDiscovered():
            return

        # Discover GGCs
        discoveryInfoProvider = DiscoveryInfoProvider()
        discoveryInfoProvider.configureEndpoint(self.host)
        discoveryInfoProvider.configureCredentials(self.rootCA, self.cert, self.key)
        discoveryInfoProvider.configureTimeout(10)  # 10 sec

        retryCount = self.max_discovery_retries
        self.groupCA = None
        coreInfo = None

        while retryCount != 0:
            try:
                discoveryInfo = discoveryInfoProvider.discover(self.thingName)
                caList = discoveryInfo.getAllCas()
                coreList = discoveryInfo.getAllCores()

                # We only pick the first ca and core info
                groupId, ca = caList[0]
                self.coreInfo = coreList[0]
                self.logger.info("Discovered GGC: %s from Group: %s" % (self.coreInfo.coreThingArn, groupId))

                self.groupCA = self.group_ca_path + groupId + "_CA_" + str(uuid.uuid4()) + ".crt"
                if not os.path.exists(self.group_ca_path):
                    os.makedirs(self.group_ca_path)
                groupCAFile = open(self.groupCA, "w")
                groupCAFile.write(ca)
                groupCAFile.close()

                self.discovered = True
                break
            except DiscoveryFailure as e:
                # device is not configured for greengrass, revert to IoT Core
                cl = Obj()
                cl.host = self.host
                cl.port = 8883

                self.coreInfo = Obj()
                self.coreInfo.connectivityInfoList = [cl]
                break
            except DiscoveryInvalidRequestException as e:
                print("Invalid discovery request detected!")
                print("Type: %s" % str(type(e)))
                print("Error message: %s" % e.message)
                print("Stopping...")
                break
            except BaseException as e:
                print("Error in discovery!")
                print("Type: %s" % str(type(e)))
                # print("Error message: %s" % e.message)
                retryCount -= 1
                print("\n%d/%d retries left\n" % (retryCount, self.MAX_DISCOVERY_RETRIES))
                print("Backing off...\n")
                self.backOffCore.backOff()


    def isConnected(self):
        return self.connected

    def _getCA(self):
        return self.groupCA if self.hasDiscovered() else self.rootCA

    def onOnline(self):
        print("online callback")

    def onOffline(self):
        print("offline callback")

    def connect(self):
        if self.isConnected():
            return

        self.client = AWSIoTMQTTClient(self.thingName)
        self.client.configureCredentials(self._getCA(), self.key, self.cert)

        for connectivityInfo in self.coreInfo.connectivityInfoList:
            currentHost = connectivityInfo.host
            currentPort = connectivityInfo.port
            self.logger.info("Trying to connect to core at %s:%d" % (currentHost, currentPort))
            self.client.configureEndpoint(currentHost, currentPort)
            try:
                self.client.configureAutoReconnectBackoffTime(1, 128, 20)
                self.client.configureOfflinePublishQueueing(10)
                self.client.configureDrainingFrequency(50)
                self.client.configureMQTTOperationTimeout(10)

                self.client.onOnline = self.onOnline
                self.client.onOffline = self.onOffline

                self.client.connect()
                self.connected = True

                self.currentHost = currentHost
                self.currentPort = currentPort
                break
            except BaseException as e:
                self.logger.warn("Error in Connect: Type: %s" % str(type(e)))

    def disconnect(self):
        if not self.isConnected():
            return

        if self.shadowConnected:
            self.disconnectShadow()

        self.client.disconnect()
        self.connected = False

    def pubAck(self, mid):
        print(f"puback: {mid}")
        self.published_ids.remove(mid)

    def publicationIsBlocked(self):
        # return self.pubIsQueued
        return False

    def publishMessageOnTopic(self, message, topic, qos=0):
        if not self.isConnected():
            raise ConnectionError()

        result = MQTT_ERR_SUCCESS
        did_publish = False
        try:
            result = self.client.publishAsync(topic, message, qos, self.pubAck)
            did_publish = True

            # may be QUEUED or has ID
            self.published_ids.append(int(result))

        except ValueError as e:
            print(f"message queued - {result}")
        except publishError as e:
            print(f"Publish Error: {e.message}")
        except publishQueueFullException as e:
            print(f"Publish Full Exception: {e.message}")
        except Exception as e:
            print(f"Another Exception: {type(e)}")

        return did_publish

    def isShadowConnected(self):
        return self.shadowConnected

    def deltaHandler(self, payload, responseStatus, token):
        print("got a delta message " + payload)
        payloadDict = json.loads(payload)
        state = payloadDict['state']

        try:
            self.stateChangeQueue.append(state)
        except Exception as e:
            pass

    def shadowUpdate_callback(self, payload, responseStatus, token):
        if responseStatus != 'accepted':
            print(f"\n Update Status: {responseStatus}")
            print(json.dumps(payload))
            print("\n")

    def shadowDelete_callback(self, payload, responseStatus, token):
        print("shadow deleted")
        # print(json.dumps({'payload': payload, 'responseStatus': responseStatus, 'token':token}))


    def connectShadow(self):
        if not self.isConnected():
            self.logger.warn("connect regula client first to get host and port")
            raise ConnectionError

        self.shadowClient = AWSIoTMQTTShadowClient(self.thingName)
        self.shadowClient.configureEndpoint(self.currentHost, self.currentPort)
        self.shadowClient.configureCredentials(self._getCA(), self.key, self.cert)

        # AWSIoTMQTTShadowClient configuration
        self.shadowClient.configureAutoReconnectBackoffTime(1, 32, 20)
        self.shadowClient.configureConnectDisconnectTimeout(10)  # 10 sec
        self.shadowClient.configureMQTTOperationTimeout(5)  # 5 sec

        self.shadowClient._AWSIoTMQTTClient.configureOfflinePublishQueueing(self.offline_queue_depth, DROP_OLDEST)

        self.shadowClient.connect()

        # Create a deviceShadow with persistent subscription
        self.deviceShadowHandler = self.shadowClient.createShadowHandlerWithName(self.thingName, True)

        self.deviceShadowHandler.shadowRegisterDeltaCallback(self.deltaHandler)

        self.shadowConnected = True

    def disconnectShadow(self):
        if not self.shadowConnected:
            return

        self.shadowClient.disconnect()
        self.shadowConnected = False


    def updateShadow(self, update):
        if not self.isShadowConnected():
            raise ConnectionError

        state = {'state': {
                    'reported': update
        }}
        try:
            self.deviceShadowHandler.shadowUpdate(json.dumps(state), self.shadowUpdate_callback, 10)
        except Exception as e:
            print("Exception updating shadow")



    def deleteShadow(self):
        if not self.isShadowConnected():
            raise ConnectionError

        self.deviceShadowHandler.shadowDelete(self.shadowDelete_callback, 15)
