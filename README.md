# pywebserviceemul
Script for check algorithms for working with web services

#### EN [RU](READMEru.md)

## Why use

In the event that your software interacts with web services that affect the company's business processes, it becomes necessary to test the maximum possible number of interaction scenarios, both successful and problematic. Web service providers do not always provide a testbed with a wide variation of interaction scenarios, so you can use this emulator to test your interaction algorithms with web services.

## How to use

To use it, you need to prepare the settings file in JSON format and specify the path to this file with an argument (first or with the code '-o', '--optionFile') when running the script.

For example:
```` command
python pywebserviceemul.py options.json
````

## How it works

The script begins to listen to the specified address and port, accepting requests, processing them according to the HTTP protocol, and sends one of the prepared answers in response (socket). You can use SSL.

The minimum set of operations for interacting with a web service can be fully tested using scripts based on emulating the corresponding reaction to requests of a certain content, while emulating both successful cases and error situations.

## How to set it up

All settings fit into a single JSON file. If the settings file is not specified, or is specified as a file name without a full path, the script will look for the settings file by the specified name or default name (options.json) in the current directory.

#### Example settings file: [options.json](options.json)

In the response array, the first should always be the data block about the response to all obscure requests.

The remaining request/response options may be unlimited. The algorithm allows you to filter the current request by type (protocol), method, resource on the server (page), headers and content of the request body.

In this case, the search will search for an answer with a complete match of the request data, but if it does not find it, it will offer the most suitable answer. In the case when no answer is suitable, the algorithm uses the first answer from the array of answers.

## What is necessary for work

Python 3.7.3 or higher, as well as all the libraries at the beginning of the script.

Also, if desired, you can compile an executable file. For example for win:
```` command
pyinstaller pywebserviceemul.py --onefile --noconsole
````

## What you should not forget

The script itself is not sufficiently covered by tests, so it may contain errors.