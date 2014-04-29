#!/usr/bin/env python3

# Script for managing Sony QX100 (or Sony QX10, not tested with it yet) from PC.
# Supports AUTHORIZATION (!!!), which allows to use a lot of undocumented commands (such as setStillSize and others).

# Before using this script: manually connect to Wi-Fi; set up IP 10.0.1.1, mask 255.0.0.0 (and if that's not enough - default gateway: 10.0.0.1).
# Note. Password can be taken from a text file in the internal memory of the device, connect it with USB and switch on for accessing this memory.

# This script depends on PyQt4 for displaying liveview. On Ubuntu just run command: apt-get install python3-pyqt4

import sys, json, time
import http.client, urllib.parse
import threading
import base64, hashlib

from PyQt4.QtCore import *
from PyQt4.QtGui import *

lock = threading.Lock()

app = QApplication(sys.argv)
image = QImage()

class ImageDisplay(QLabel):
    def __init__(self):
        QLabel.__init__(self)

    def paintEvent(self, event):
        global lock
        lock.acquire()
        try:
            self.setPixmap(QPixmap.fromImage(image))
        finally:
            lock.release()
        QLabel.paintEvent(self, event)

imgDisplay = ImageDisplay()
imgDisplay.setMinimumSize(640, 480)
imgDisplay.show()

pId = 0
headers = {"Content-type": "text/plain", "Accept": "*/*", "X-Requested-With": "com.sony.playmemories.mobile"}

AUTH_CONST_STRING = "90adc8515a40558968fe8318b5b023fdd48d3828a2dda8905f3b93a3cd8e58dc"
METHODS_TO_ENABLE = "camera/setFlashMode:camera/getFlashMode:camera/getSupportedFlashMode:camera/getAvailableFlashMode:camera/setExposureCompensation:camera/getExposureCompensation:camera/getSupportedExposureCompensation:camera/getAvailableExposureCompensation:camera/setSteadyMode:camera/getSteadyMode:camera/getSupportedSteadyMode:camera/getAvailableSteadyMode:camera/setViewAngle:camera/getViewAngle:camera/getSupportedViewAngle:camera/getAvailableViewAngle:camera/setMovieQuality:camera/getMovieQuality:camera/getSupportedMovieQuality:camera/getAvailableMovieQuality:camera/setFocusMode:camera/getFocusMode:camera/getSupportedFocusMode:camera/getAvailableFocusMode:camera/setStillSize:camera/getStillSize:camera/getSupportedStillSize:camera/getAvailableStillSize:camera/setBeepMode:camera/getBeepMode:camera/getSupportedBeepMode:camera/getAvailableBeepMode:camera/setCameraFunction:camera/getCameraFunction:camera/getSupportedCameraFunction:camera/getAvailableCameraFunction:camera/setLiveviewSize:camera/getLiveviewSize:camera/getSupportedLiveviewSize:camera/getAvailableLiveviewSize:camera/setTouchAFPosition:camera/getTouchAFPosition:camera/cancelTouchAFPosition:camera/setFNumber:camera/getFNumber:camera/getSupportedFNumber:camera/getAvailableFNumber:camera/setShutterSpeed:camera/getShutterSpeed:camera/getSupportedShutterSpeed:camera/getAvailableShutterSpeed:camera/setIsoSpeedRate:camera/getIsoSpeedRate:camera/getSupportedIsoSpeedRate:camera/getAvailableIsoSpeedRate:camera/setExposureMode:camera/getExposureMode:camera/getSupportedExposureMode:camera/getAvailableExposureMode:camera/setWhiteBalance:camera/getWhiteBalance:camera/getSupportedWhiteBalance:camera/getAvailableWhiteBalance:camera/setProgramShift:camera/getSupportedProgramShift:camera/getStorageInformation:camera/startLiveviewWithSize:camera/startIntervalStillRec:camera/stopIntervalStillRec:camera/actFormatStorage:system/setCurrentTime"

def postRequest(conn, target, req):
    global pId
    pId += 1
    req["id"] = pId
    print("REQUEST  [%s]: " % target, end = "")
    print(req)
    conn.request("POST", "/sony/" + target, json.dumps(req), headers)
    response = conn.getresponse()
    print("RESPONSE [%s]: " % target, end = "")
    #print(response.status, response.reason)
    data = json.loads(response.read().decode("UTF-8"))
    print(data)
    if data["id"] != pId:
        print("FATAL ERROR: Response id does not match")
        return {}
    if "error" in data:
        print("WARNING: Response contains error code: %d; error message: [%s]" % tuple(data["error"]))
    print("")
    return data

def exitWithError(conn, message):
    print("ERROR: %s" % message)
    conn.close()
    sys.exit(1)

def parseUrl(url):
    parsedUrl = urllib.parse.urlparse(url)
    return parsedUrl.hostname, parsedUrl.port, parsedUrl.path + "?" + parsedUrl.query, parsedUrl.path[1:]

def downloadImage(url):
    host, port, address, img_name = parseUrl(url)
    conn2 = http.client.HTTPConnection(host, port)
    conn2.request("GET", address)
    response = conn2.getresponse()
    if response.status == 200:
        with open(img_name, "wb") as img:
            img.write(response.read())
    else:
        print("ERROR: Could not download picture, error = [%d %s]" % (response.status, response.reason))

#def symb5(c):
#    s = str(c)
#    while len(s) < 5:
#        s = "0" + s
#    return s

def liveviewFromUrl(url):
    global image
    global lock
    host, port, address, img_name = parseUrl(url)
    conn3 = http.client.HTTPConnection(host, port)
    conn3.request("GET", address)
    response = conn3.getresponse()
    #flow = open("liveview", "wb")
    if response.status == 200:
        buf = b''
        c = 0
        while not response.closed:
            nextPart = response.read(1024)
            #flow.write(nextPart)
            #flow.flush()

            # TODO: It would be better to use description from the documentation (page 51) for parsing liveview stream
            jpegStart = nextPart.find(b'\xFF\xD8\xFF')
            jpegEnd = nextPart.find(b'\xFF\xD9')
            if jpegEnd != -1:
                c += 1
                buf += nextPart[:jpegEnd + 2]
                #with open("live_" + symb5(c) + ".jpg", "wb") as liveImg:
                #    liveImg.write(buf)
                lock.acquire()
                try:
                    image.loadFromData(buf)
                finally:
                    lock.release()
            if jpegStart != -1:
                buf = nextPart[jpegStart:]
            else:
                buf += nextPart

def communicationThread():
    #target = "/sony/camera"
    #target = "/sony/system"
    #target = "/sony/accessControl"

    #req = {"method": "getVersions", "params": [], "id": 1}
    #req = {"method": "getApplicationInfo", "params": [], "id": 2, "version": "1.0"}
    #req = {"method": "getEvent", "params": [False], "id": 3, "version": "1.0"}        # (!!!) get method list
    #req = {"method": "getEvent", "params": [True], "id": 4, "version": "1.0"}
    #req = {"method": "getMethodTypes", "params": ["1.0"], "id": 8, "version": "1.0"}

    conn = http.client.HTTPConnection("10.0.0.1", 10000)

    resp = postRequest(conn, "camera", {"method": "getVersions", "params": []})
    if resp["result"][0][0] != "1.0":
        exitWithError(conn, "Unsupported version")

    resp = postRequest(conn, "accessControl", {"method": "actEnableMethods", "params": [{"methods": "", "developerName": "", "developerID": "", "sg": ""}], "version": "1.0"})
    dg = resp["result"][0]["dg"]

    h = hashlib.sha256()
    h.update(bytes(AUTH_CONST_STRING + dg, "UTF-8"))
    sg = base64.b64encode(h.digest()).decode("UTF-8")

    resp = postRequest(conn, "accessControl", {"method": "actEnableMethods", "params": [{"methods": METHODS_TO_ENABLE, "developerName": "Sony Corporation", "developerID": "7DED695E-75AC-4ea9-8A85-E5F8CA0AF2F3", "sg": sg}], "version": "1.0"})

    resp = postRequest(conn, "system", {"method": "getMethodTypes", "params": ["1.0"], "version": "1.0"})
    resp = postRequest(conn, "accessControl", {"method": "getMethodTypes", "params": ["1.0"], "version": "1.0"})

    resp = postRequest(conn, "camera", {"method": "getStillSize", "params": [], "version": "1.0"})
    #resp = postRequest(conn, "camera", {"method": "getSupportedStillSize", "params": [], "version": "1.0"})
    #resp = postRequest(conn, "camera", {"method": "getAvailableStillSize", "params": [], "version": "1.0"})

    #resp = postRequest(conn, "camera", {"method": "setStillSize", "params": ["20M", "3:2"], "version": "1.0"})

    resp = postRequest(conn, "camera", {"method": "setFocusMode", "params": ["AF-S"], "version": "1.0"})
    resp = postRequest(conn, "camera", {"method": "getFocusMode", "params": [], "version": "1.0"})

    resp = postRequest(conn, "camera", {"method": "stopLiveview", "params": [], "version": "1.0"})

    resp = postRequest(conn, "camera", {"method": "setPostviewImageSize", "params": ["Original"], "version": "1.0"})
    while "error" in resp:
        resp = postRequest(conn, "camera", {"method": "setPostviewImageSize", "params": ["Original"], "version": "1.0"})
    resp = postRequest(conn, "camera", {"method": "getPostviewImageSize", "params": [], "version": "1.0"})

    resp = postRequest(conn, "camera", {"method": "actTakePicture", "params": [], "version": "1.0"})
    downloadImage(resp["result"][0][0])

    resp = postRequest(conn, "camera", {"method": "setPostviewImageSize", "params": ["2M"], "version": "1.0"})
    while "error" in resp:
        resp = postRequest(conn, "camera", {"method": "setPostviewImageSize", "params": ["2M"], "version": "1.0"})
    resp = postRequest(conn, "camera", {"method": "getPostviewImageSize", "params": [], "version": "1.0"})

    resp = postRequest(conn, "camera", {"method": "actTakePicture", "params": [], "version": "1.0"})
    downloadImage(resp["result"][0][0])

    resp = postRequest(conn, "camera", {"method": "setPostviewImageSize", "params": ["Original"], "version": "1.0"})
    while "error" in resp:
        resp = postRequest(conn, "camera", {"method": "setPostviewImageSize", "params": ["Original"], "version": "1.0"})
    resp = postRequest(conn, "camera", {"method": "getPostviewImageSize", "params": [], "version": "1.0"})

    resp = postRequest(conn, "camera", {"method": "actTakePicture", "params": [], "version": "1.0"})
    downloadImage(resp["result"][0][0])

    resp = postRequest(conn, "camera", {"method": "getAvailableFocusMode", "params": [], "version": "1.0"})

    resp = postRequest(conn, "camera", {"method": "getSupportedFocusMode", "params": [], "version": "1.0"})

    resp = postRequest(conn, "camera", {"method": "getTouchAFPosition", "params": [], "version": "1.0"})

    resp = postRequest(conn, "camera", {"method": "getSupportedFNumber", "params": [], "version": "1.0"})

    #resp = postRequest(conn, "camera", {"method": "setFocusMode", "params": ["MF"], "version": "1.0"})
    #resp = postRequest(conn, "camera", {"method": "getFocusMode", "params": [], "version": "1.0"})

    resp = postRequest(conn, "camera", {"method": "getEvent", "params": [False], "version": "1.0"})

    resp = postRequest(conn, "camera", {"method": "startLiveview", "params": [], "version": "1.0"})
    liveview = threading.Thread(target = liveviewFromUrl, args = (resp["result"][0],))
    liveview.start()

    resp = postRequest(conn, "camera", {"method": "actZoom", "params": ["in", "start"], "version": "1.0"})
    time.sleep(2)
    resp = postRequest(conn, "camera", {"method": "actZoom", "params": ["in", "stop"], "version": "1.0"})

    time.sleep(3)

    resp = postRequest(conn, "camera", {"method": "actZoom", "params": ["out", "start"], "version": "1.0"})
    time.sleep(2.5)
    resp = postRequest(conn, "camera", {"method": "actZoom", "params": ["out", "stop"], "version": "1.0"})

    conn.close()

if __name__ == "__main__":
    communication = threading.Thread(target = communicationThread)
    communication.start()

    sys.exit(app.exec_())
