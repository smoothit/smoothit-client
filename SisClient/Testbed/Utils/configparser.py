import os
import sys

__author__ = "Markus Guenther"

class LinewiseConfigParser:
    """
    This class provides a very simple parsing mechanism for parsing
    simple configuration files. The parser operates linewise and checks
    the first token of every line against a dict containing all rules
    of your grammar. If there is a matching rule, the associated callback
    function gets the tokenized line passed as a function parameter.
    
    Simple example:
    Assume you have a simple configuration file like
    RunTest <TEST_NAME>
    RunTestsuite <TEST_SUITE_NAME>
    and you want to parse it with using the LinewiseConfigParser. You'll have
    to provide the following code:
    
    mapping = { 'RunTest',      callback_for_run_test,
                'RunTestsuite', callback_for_run_testsuite}
    config = LinewiseConfigParser(configurationFile, mapping, callback_parsing_finished)
    
    callback_for_run_test is a function in your code that gets called in order
    to evaluate the line completely. callback_parsing_finished is a function
    that gets called when the parser parsed the whole file, so you can run
    integrality checks or the like on the parsed data.
    """
    def __init__(self, file, mapping, callback=None):
        self._file = file
        self._mapping = mapping
        self._callback = callback

    def parse(self):
        skip_lines_beginning_with = ["#", "\n"]
        
        if not os.path.isfile(self._file):
            print "The configuration file does not exist or is not readable"
            sys.exit()
            
        fileHandle = open(self._file, 'r')
        fileLines = fileHandle.readlines()
        
        failed = False
        for fileLine in fileLines:
            if fileLine[0] in skip_lines_beginning_with: 
                continue
            tokens = fileLine.split(" ")
            
            if tokens[0] in self._mapping:
                self._mapping[tokens[0]](tokens)
            else:
                print "There is no rule specified for the token %s" % tokens[0]
                failed = True
                
        if failed:
            sys.exit()
            
        # we parsed everything, so call the specified callback handler
        if self._callback is not None:
            self._callback()