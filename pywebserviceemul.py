import os
import ssl
import socket
import json
import sys
import argparse
from datetime import datetime
import time
import re

debugFlag = False

def writeLog(logFile, logText, addDateTime = True):
	# work log
	if logFile:
		if addDateTime:
			dt = datetime.now()
			logText = '' + dt.isoformat() + ' - ' + logText + '\n'
		else:
			logText = '' + logText + '\n'
		with open(logFile, 'a', encoding='utf-8') as f:
			f.write(logText)
	# debug log in console
	if debugFlag:
		print(logText)

def writeDataLog(dataLogFile, logData):
	# file with query/answers data
	if dataLogFile:
		if os.path.exists(dataLogFile):
			with open(dataLogFile, 'r', encoding='utf-8') as f:
				workData = json.load(f)
		else:
			workData = []
		workData.append(logData)
		with open(dataLogFile, 'w', encoding='utf-8') as f:
			json.dump(workData, f)

def getTemplateString(sourceStr):
	result = sourceStr
	result = result.replace('<curCat>', os.getcwd())
	return result

def createArgumentParser():
	parser = argparse.ArgumentParser()
	parser.add_argument ('-o', '--optionFile', required = False)
	return parser

def valueContainValueCheck(value1, value2):
	if type(value1) == type('string'):
		if value1.upper().find(value2.upper()) >= 0:
			return True
		else:
			return False
	if type(value1) == type(dict()) or type(value1) == type(list()):
		checkResult = valueContainValue(value1, value2)
		if checkResult == True:
			return True
		else:
			return False
	elif type(value1) == type(1) or type(value1) == type(True):
		if value1 == value2:
			return True
		else:
			return False
	return False

# value must be same types
# value must be one of the types: int, bool, str, list, dict
# if value type is int or bool then will check equal
# if value type is str or list or dict then will check contain
def valueContainValue(sourceValue, checkValue):
	if type(sourceValue) != type(checkValue):
		return False
	if type(sourceValue) == type(dict()):
		for key, keyValue in checkValue.items():
			sourceKeyValue = sourceValue.get(key)
			if sourceKeyValue == None:
				return False
			if valueContainValueCheck(sourceKeyValue, keyValue) != True:
				return False
		return True
	elif type(sourceValue) == type([]):
		for keyValue in checkValue:
			result = False
			for sourceKeyValue in sourceValue:
				if valueContainValueCheck(sourceKeyValue, keyValue) == True:
					result = True
					break
			if result == False:
				return False
		return True
	else:
		return valueContainValueCheck(sourceValue, checkValue)
	return False

def loadOptions(optionsFilePath):
	options_file_ = os.getcwd() + '/options.json'
	if optionsFilePath:
		options_file_ = optionsFilePath
	with open(options_file_, 'r', encoding='utf-8') as f:
		optionsData = json.load(f)
	return optionsData

def fillMessageData(messageData):
	# HTTP have data with newline split
	headText = messageData.get('headText', '')
	bodyText = messageData.get('bodyText', '')
	query_lines = headText.split('\n')
	# HTTP firstline is splitted by ' '
	query_line_words = query_lines[1].split()
	messageData['type'] = query_line_words[0]
	messageData['page'] = query_line_words[1]
	messageData['version'] = query_line_words[2]
	messageData['headers'] = dict()
	# process headers
	for i in range(2, len(query_lines)):
		query_line_words = query_lines[i].split(':')
		if len(query_line_words) > 0:
			header_key = query_line_words[0]
			header_key = header_key.replace(' ', '')
			header_key = header_key.replace('\r', '')
			if len(header_key) > 0:
				messageData['headers'][header_key] = query_line_words[1].strip()
	# if json type defined in headers will process it
	headerValue = messageData['headers'].get('Content-Type')
	if headerValue != None and headerValue.upper().find('JSON') >= 0:
		if bodyText.replace('\n', '') != '':
			messageData['body'] = json.loads(bodyText)
			if type(messageData['body']) == type('string'):
				messageData['body'] = json.loads(messageData['body'])
		else:
			messageData['body'] = dict()
		messageData['body_json'] = True
	else:
		messageData['body'] = bodyText
		messageData['body_json'] = False

def getAnswerItem(queryItem, options):
	# get filter values
	find_format = queryItem['version']
	find_type = queryItem['type']
	find_page = queryItem['page']
	find_headers = queryItem['headers']
	find_body = queryItem['body']
	# filter
	answerItem = None
	
	for curAnswer in options['answers']:
		# full equal flag
		flagFullEqual = True
		
		# check format
		if curAnswer['filter_format'] == '':
			flagFullEqual = False
		elif find_format.upper().find(curAnswer['filter_format'].upper()) < 0 and re.fullmatch(curAnswer['filter_format'].upper(), find_format.upper()) == None:
			continue
		# check query type
		if curAnswer['filter_type'] == '':
			flagFullEqual = False
		elif find_type.upper() != curAnswer['filter_type'].upper() and re.fullmatch(curAnswer['filter_type'].upper(), find_type.upper()) == None:
			continue
		# check page / resource
		if curAnswer['filter_page'] == '':
			flagFullEqual = False
		elif find_page.upper() != curAnswer['filter_page'].upper() and re.fullmatch(curAnswer['filter_page'].upper(), find_page.upper()) == None:
			continue
		# check headers
		if len(curAnswer['filter_headers']) == 0:
			flagFullEqual = False
		else:
			allHeaders = True
			for headerKey, headerValue in curAnswer['filter_headers'].items():
				if len(headerValue) == 0:
					flagFullEqual = False
				else:
					findHeaderValue = find_headers.get(headerKey)
					if findHeaderValue == None:
						allHeaders = False
						break
					elif findHeaderValue.upper().find(headerValue.upper()) < 0:
						allHeaders = False
						break
			if not allHeaders:
				continue
		# check body text
		if len(curAnswer['filter_body']) == 0:
			flagFullEqual = False
		else:
			if queryItem['body_json']:
				allBody = True
				for bodyKey, bodyValue in curAnswer['filter_body'].items():
					if len(bodyValue) == 0:
						flagFullEqual = False
					else:
						
						findBodyValue = find_body.get(bodyKey)
						if findBodyValue == None:
							allBody = False
							break
						if valueContainValue(bodyValue, findBodyValue) != True:
							allBody = False
							break
				if not allBody:
					continue
			elif find_body.upper().find(curAnswer['filter_body'].upper()) < 0:
				continue
		# if we here - we find answer item
		if flagFullEqual:
			# answer with full equal filter
			answerItem = curAnswer
			break
		else:
			# here we finded answer with not full equal filter
			# we save this answer
			# we will find another answer with full equal
			answerItem = curAnswer
	# we not found answer - get first answer
	if answerItem == None:
		answerItem = options['answers'][0]
	return answerItem

def getAnswerText(queryItem, answerItem, getQueryInfo = False):
	# make answer text from answer item
	result = ''
	result = result + answerItem['format'] + '/' + answerItem['version'] + ' ' + answerItem['code'] + ' ' + answerItem['comment']
	result = result + '\n' + answerItem['headers']
	result = result + '\n\n' + answerItem['body']
	# make query info and replace it in answer texr
	queryInfo = ''
	if getQueryInfo:
		queryInfo = queryInfo + '(' + queryItem['type'] + ' ' + queryItem['page'] + ' ' + queryItem['version']
		for headerKey in queryItem['headers'].keys():
			queryInfo = queryInfo + '\n' + headerKey + ': ' + queryItem['headers'][headerKey]
		queryInfo = queryInfo + '\n\n' + json.dumps(queryItem['body']) + ')'
	result = result.replace('<queryInfo>', queryInfo)
	#
	return result

if __name__ == '__main__':
	# read arg
	parser = createArgumentParser()
	namespace = parser.parse_args()
	# load options
	options = loadOptions(namespace.optionFile)
	# set debug flag
	debugFlag = options.get('debug', False)
	# def log file
	logFilePath = getTemplateString(options.get('logFile', ''))
	# def data log file
	dataLogFile = getTemplateString(options.get('dataLogFile', ''))
	# def SSL filekey.key
	key_key = getTemplateString(options.get('standard_key_key', ''))
	# def SSL filekey.crt
	key_crt = getTemplateString(options.get('standard_key_crt', ''))
	# def server adress
	server_addr = getTemplateString(options.get('standard_server', ''))
	if server_addr == '' or server_addr == 0:
		server_addr = '127.0.0.1'
		writeLog(logFilePath, 'server adress not defined: will use 127.0.0.1')
	# def server port
	server_port = options.get('standard_port', 0)
	if server_port == '' or server_port == 0:
		server_addr = 443
		writeLog(logFilePath, 'server port not defined: will use 443')
	# create socket
	if options.get('usessl', False) == True:
		sock = ssl.wrap_socket(socket.socket(), key_key, key_crt, True)
		ssl_text = '(use SSL: yes)'
	else:
		sock = socket.socket()
		ssl_text = '(use SSL: no)'
	# bind
	sock.bind((server_addr, server_port))
	# determine the processing queue
	sock.listen(1)
	# wait for connections
	print('Emul started, waiting for connections (close app: Cntrl + Break/Pause)' + ssl_text)
	writeLog(logFilePath, '----------------------------------------------------------------------', False)
	writeLog(logFilePath, 'Emul started, waiting for connections (close app: Cntrl + Break/Pause)' + ssl_text)
	# processing loop
	while True:
		# get next message
		try:
			conn, addr = sock.accept()
			conn.setblocking(0)
		except ssl.SSLError as error_obj:
			writeLog(logFilePath, 'Connect try: ' + str(error_obj))
			continue
		curConnectData = dict()
		curConnectData['addr'] = str(addr)
		# log
		writeLog(logFilePath, '------------------------------', False)
		writeLog(logFilePath, 'connected:' + str(addr))
		# read data
		query_head = ''
		query_head_found = False
		query_body = ''
		data = True
		while data:
			try:
				time.sleep(1)
				data = conn.recv(1024)
			except socket.error:
				break
			try:
				sdata = data.decode()
			except:
				sdata = data.decode('latin-1')
			lines = sdata.split('\n')
			curLine = ''
			for ls in lines:
				if not query_head_found and (ls == '\r' or ls == ''):
					query_head = curLine
					curLine = ''
					query_head_found = True
				else:
					curLine = curLine + '\n' + ls
			if query_head_found:
				query_body = query_body + curLine
			else:
				query_head = query_head + curLine
		writeLog(logFilePath, 'HEAD: ' + query_head)
		writeLog(logFilePath, 'BODY: ' + query_body)
		curConnectData['headText'] = query_head
		curConnectData['bodyText'] = query_body
		#
		if query_head == '':
			writeLog(logFilePath, 'ERROR: HEAD tag is empty')
			conn.close()
			continue
		# parse query text to data
		fillMessageData(curConnectData)
		# end processing
		itFin = False
		if curConnectData['body_json'] != True and curConnectData['body'].strip().replace('\n', '').upper() == 'FIN':
			itFin = True
		elif isinstance(curConnectData['body'], dict):
			idValue = curConnectData['body'].get('id')
			if idValue != None and idValue.upper() == 'FIN':
				itFin = True
		if itFin:
			query_answer_text = 'HTTP/1.1 200 OK \n Content-Type: application/json \n\n { "ok": true }'
			conn.send(query_answer_text.encode())
			conn.close()
			writeLog(logFilePath, 'Received exit command')
			break
		# get answer item
		answerItem = getAnswerItem(curConnectData, options)
		# get answer text
		query_answer_text = getAnswerText(curConnectData, answerItem, options['debug'])
		writeLog(logFilePath, 'ANSWER:' + answerItem.get('query_desc'))
		writeLog(logFilePath, query_answer_text)
		# send answer
		conn.send(query_answer_text.encode())
		# close connection
		conn.close()
		# add data log info
		for key, value in answerItem.items():
			curConnectData[key] = value
		writeDataLog(dataLogFile, curConnectData)
		# wait for next

	conn.close()
	print('Emul stopped')
	writeLog(logFilePath, 'Emul stopped')