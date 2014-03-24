#!/usr/bin/env python3

# Before using this script: manually connect to Wi-Fi; setup IP 10.0.1.1, mask 255.0.0.0 (and if that's not enough - default gateway: 10.0.0.1)
# Password of MY device: rjo1Tvr4

import sys, json
import http.client, urllib.parse
import base64, hashlib

conn = None
pId = 0
headers = {"Content-type": "text/plain", "Accept": "*/*", "X-Requested-With": "com.sony.playmemories.mobile"}

AUTH_CONST_STRING = "90adc8515a40558968fe8318b5b023fdd48d3828a2dda8905f3b93a3cd8e58dc"
METHODS_TO_ENABLE = "camera/setFlashMode:camera/getFlashMode:camera/getSupportedFlashMode:camera/getAvailableFlashMode:camera/setExposureCompensation:camera/getExposureCompensation:camera/getSupportedExposureCompensation:camera/getAvailableExposureCompensation:camera/setSteadyMode:camera/getSteadyMode:camera/getSupportedSteadyMode:camera/getAvailableSteadyMode:camera/setViewAngle:camera/getViewAngle:camera/getSupportedViewAngle:camera/getAvailableViewAngle:camera/setMovieQuality:camera/getMovieQuality:camera/getSupportedMovieQuality:camera/getAvailableMovieQuality:camera/setFocusMode:camera/getFocusMode:camera/getSupportedFocusMode:camera/getAvailableFocusMode:camera/setStillSize:camera/getStillSize:camera/getSupportedStillSize:camera/getAvailableStillSize:camera/setBeepMode:camera/getBeepMode:camera/getSupportedBeepMode:camera/getAvailableBeepMode:camera/setCameraFunction:camera/getCameraFunction:camera/getSupportedCameraFunction:camera/getAvailableCameraFunction:camera/setLiveviewSize:camera/getLiveviewSize:camera/getSupportedLiveviewSize:camera/getAvailableLiveviewSize:camera/setTouchAFPosition:camera/getTouchAFPosition:camera/cancelTouchAFPosition:camera/setFNumber:camera/getFNumber:camera/getSupportedFNumber:camera/getAvailableFNumber:camera/setShutterSpeed:camera/getShutterSpeed:camera/getSupportedShutterSpeed:camera/getAvailableShutterSpeed:camera/setIsoSpeedRate:camera/getIsoSpeedRate:camera/getSupportedIsoSpeedRate:camera/getAvailableIsoSpeedRate:camera/setExposureMode:camera/getExposureMode:camera/getSupportedExposureMode:camera/getAvailableExposureMode:camera/setWhiteBalance:camera/getWhiteBalance:camera/getSupportedWhiteBalance:camera/getAvailableWhiteBalance:camera/setProgramShift:camera/getSupportedProgramShift:camera/getStorageInformation:camera/startLiveviewWithSize:camera/startIntervalStillRec:camera/stopIntervalStillRec:camera/actFormatStorage:system/setCurrentTime"

def postRequest(target, req):
    global conn
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
    if data["id"] != pId:
        print("FATAL ERROR: Response id does not match")
        return {}
    print(data, end = "\n\n")
    return data

def exitWithError(message):
    global conn
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

def symb5(c):
    s = str(c)
    while len(s) < 5:
        s = "0" + s
    return s

def liveviewFromUrl(url):
    host, port, address, img_name = parseUrl(url)
    conn3 = http.client.HTTPConnection(host, port)
    conn3.request("GET", address)
    response = conn3.getresponse()
    if response.status == 200:
        buf = b''
        c = 0
        while not response.closed:
            nextPart = response.read(1024)
            jpegStart = nextPart.find(b'\xFF\xD8\xFF')
            jpegEnd = nextPart.find(b'\xFF\xD9')
            if jpegEnd != -1:
                c += 1
                buf += nextPart[:jpegEnd + 2]
                with open("live_" + symb5(c) + ".jpg", "wb") as liveImg:
                    liveImg.write(buf)
            if jpegStart != -1:
                buf = nextPart[jpegStart:]
            else:
                buf += nextPart

if __name__ == "__main__":
    #target = "/sony/camera"
    #target = "/sony/system"
    #target = "/sony/accessControl"

    #req = {"method": "getVersions", "params": [], "id": 1}
    #req = {"method": "getApplicationInfo", "params": [], "id": 2, "version": "1.0"}
    #req = {"method": "getEvent", "params": [False], "id": 3, "version": "1.0"}        # (!!!) get method list
    #req = {"method": "getEvent", "params": [True], "id": 4, "version": "1.0"}
    #req = {"method": "getMethodTypes", "params": ["1.0"], "id": 8, "version": "1.0"}
    #req = {"method": "getFocusMode", "params": [], "id": 9, "version": "1.0"}

    conn = http.client.HTTPConnection("10.0.0.1", 10000)

    resp = postRequest("camera", {"method": "getVersions", "params": []})
    if resp["result"][0][0] != "1.0":
        exitWithError("Unsupported version")

    resp = postRequest("accessControl", {"method": "actEnableMethods", "params": [{"methods": "", "developerName": "", "developerID": "", "sg": ""}], "version": "1.0"})
    dg = resp["result"][0]["dg"]

    h = hashlib.sha256()
    h.update(bytes(AUTH_CONST_STRING + dg, "UTF-8"))
    sg = base64.b64encode(h.digest()).decode("UTF-8")

    resp = postRequest("accessControl", {"method": "actEnableMethods", "params": [{"methods": METHODS_TO_ENABLE, "developerName": "Sony Corporation", "developerID": "7DED695E-75AC-4ea9-8A85-E5F8CA0AF2F3", "sg": sg}], "version": "1.0"})

    #resp = postRequest("camera", {"method": "getStillSize", "params": [], "version": "1.0"})
    #resp = postRequest("camera", {"method": "getSupportedStillSize", "params": [], "version": "1.0"})
    #resp = postRequest("camera", {"method": "getAvailableStillSize", "params": [], "version": "1.0"})

    #resp = postRequest("camera", {"method": "setStillSize", "params": ["20M", "3:2"], "version": "1.0"})

    resp = postRequest("camera", {"method": "stopLiveview", "params": [], "version": "1.0"})

    resp = postRequest("camera", {"method": "startLiveview", "params": [], "version": "1.0"})
    liveviewFromUrl(resp["result"][0])

    resp = postRequest("camera", {"method": "actTakePicture", "params": [], "version": "1.0"})
    downloadImage(resp["result"][0][0])

    conn.close()
