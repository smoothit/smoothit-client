import unittest
import logging

from SisClient.Utils.serialize import serialize

class SerializationTest(unittest.TestCase):
    def setUp(self):
        pass
    
    def tearDown(self):
        pass
    
    def suite(self):
        suite = unittest.TestSuite()
        suite.addTest(SerializationTest(""))
        
    def testSerializeSimpleDict(self):
        test_against = "<map name=\"parent\">\n\t<key name=\"status\">3</key>\n\t<key name=\"intern_list\">\n\t\t<list name=\"intern_list\">\n\t\t\t<item>3</item>\n\t\t\t<item>4</item>\n\t\t\t<item>5</item>\n\t\t</list>\n\t</key>\n\t<key name=\"string_value\">value</key>\n</map>"
        test_dict = {
                    'status'    :   3,
                    'intern_list'   : [3,4,5],
                    'string_value'  :   'value'
                    }
        xml_string = serialize(test_dict)
        self.assertEquals(test_against, xml_string, "xml string was: "+xml_string)
        
    def testSerializeNestedLists(self):
        test_against = "<list name=\"parent\">\n\t<item>1</item>\n\t<item>2</item>\n\t<item>\n\t\t<list name=\"0\">\n\t\t\t<item>3</item>\n\t\t\t<item>4</item>\n\t\t</list>\n\t</item>\n</list>"
        test_list = [1, 2, [3, 4]]
        xml_string = serialize(test_list)
        self.assertEquals(test_against, xml_string, "XML string was "+xml_string)
        
    def testSerializeNestedDicts(self):
        test_against = "<map name=\"parent\">\n\t<key name=\"some_dict\">\n\t\t<map name=\"some_dict\">\n\t\t\t<key name=\"sub_value\">2</key>\n\t\t</map>\n\t</key>\n\t<key name=\"some_value\">3</key>\n\t<key name=\"some_another_dict\">\n\t\t<map name=\"some_another_dict\">\n\t\t\t<key name=\"sub_value2\">6</key>\n\t\t\t<key name=\"sub_value1\">5</key>\n\t\t</map>\n\t</key>\n</map>"
        test_dict = {'some_value'   :   3,
                     'some_dict'    :   {
                                         'sub_value'    :   2
                                         },
                    'some_another_dict'  :  {
                                             'sub_value1'   : 5,
                                             'sub_value2'   : 6
                                             }}
        xml_string = serialize(test_dict)
        self.assertEquals(test_against, xml_string, "xml string was: "+xml_string)
        
    def testQuoteList(self):
        test_against = "<list name=\"parent\">\n\t<item>&gt;</item>\n\t<item>&lt;</item>\n</list>"
        test_list = ['>', '<']
        xml_string = serialize(test_list)
        self.assertEquals(test_against, xml_string, "xml string was: "+xml_string)
        
if __name__ == "__main__":
    logging.disable(logging.DEBUG)
    logging.disable(logging.INFO)
    unittest.main()