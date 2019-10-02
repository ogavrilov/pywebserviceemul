import os
import ssl
import socket
import json
import subprocess
import time

def loadTestPlan(testPlanFilePath):
    with open(testPlanFilePath, 'r', encoding='utf-8') as f:
        testPlan = json.load(f)
    return testPlan


def doTest(testItem):
    # set default result
    result = dict()
    result['result'] = False
    result['message'] = ''
    # prepare options.json
    with open('options.json', 'r', encoding='utf-8') as f:
        optionsData = json.load(f)
    if testItem.get('useSSL', False):
        optionsData['usessl'] = True
        optionsData['standard_key_key'] = '<curCat>/server.key'
        optionsData['standard_key_crt'] = '<curCat>/server.crt'
    else:
        optionsData['usessl'] = False
        optionsData['standard_key_key'] = ''
        optionsData['standard_key_crt'] = ''
    optionsData['dataLogFile'] = '<curCat>/datalog.json'
    optionsData['log_file'] = '<curCat>/log.log'
    with open('options.json', 'w', encoding='utf-8') as f:
        json.dump(optionsData, f)
    try:
        # start pywebserviceemul
        emulProcess = subprocess.Popen(['python', '../pywebserviceemul.py', '-o', os.getcwd() + '/options.json'])
        # send test item query
        conn = socket.socket()
        if testItem.get('useSSL', False):
            wSock = ssl.wrap_socket(conn, ssl_version=ssl.PROTOCOL_TLS)
        else:
            wSock = conn
        wSock.connect((testItem['standard_server'], testItem['standard_port']))
        queryText = '' + testItem['method'] + ' ' + testItem['page'] + ' ' + testItem['format']
        queryText += '\r\n'
        for curHeaderKey, curHeaderValue in testItem['headers'].items():
            queryText += curHeaderKey + ': ' + curHeaderValue + '\r'
        queryText += '\n\n'
        queryText += json.dumps(testItem['body'])
        wSock.send(queryText.encode())
        time.sleep(1)
        sdata = ''
        data = True
        while data:
            try:
                data = wSock.recv(1024)
            except socket.error:
                break
            sdata += data.decode()
        wSock.close()
        if sdata.find(testItem['answerText']) >= 0:
            result['result'] = True
        # stop pywebserviceemul
        emulProcess.kill()
    except Exception as errorObj:
        result['message'] = str(errorObj)
    #
    return result


testPlanData = loadTestPlan('testPlan.json')
for testItem in testPlanData:
    testResult = doTest(testItem)
    testResultText = '' + testItem['title'] + ' '
    if testResult['result']:
        testResultText = testResultText + 'passed'
    else:
        testResultText = testResultText + 'failed with message: ' + testResult['message']
    testResultText = testResultText
    print(testResultText)
