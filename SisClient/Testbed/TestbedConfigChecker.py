import os

'''This module defines methods that check if a TestbedConfiguration
   is consistent.
'''

__author__ = "Markus Guenther"

class TestbedConfigurationChecker:
    '''Provides static methods that check a TestbedConfiguration for
       consistency.
    '''
    def __init__(self):
        pass
    
    def is_consistent(conf):
        '''Runs some consistency checks on a given TestbedConfiguration.
           Returns the tuple (is_consistent, errors, warnings), where
           is_consistent is a boolean value that indicates the success
           of this method, and errors and warnings refer to lists of
           strings that represent error messages resp. warnings.
        '''
        warnings = []
        errors = []
        files = {}
        
        for file in conf.get_files():
            files[file.get_id()] = False
            if not os.path.isfile(file.get_absolute_path_to_file()):
                errors.append("File %i at %s does not exist." %
                              (file.get_id(), file.get_absolute_path_to_file()))
        
        for client in conf.get_clients():
            if len(client.get_seeding_list()) == 0 and \
               len(client.get_leeching_list()) == 0:
                errors.append("Client %i has no role assigned to it." % client.get_id())
            
            def correct_file_references(list, probe_list):
                for elem in list:
                    if not elem in probe_list:
                        return False
                    files[elem] = True
                return True
            
            probe_files = [file_id for file_id in files.keys()]
            
            if not correct_file_references(client.get_seeding_list(), probe_files) or \
               not correct_file_references(client.get_leeching_list(), probe_files):
                errors.append("Wrong file references for client %i." % client.get_id())
        
            unused_files = [elem for elem in files.values() if elem is False]
            if len(unused_files) > 0:
                 warnings.append("The configuration stores the specification of " + \
                                 "a file that will not be distributed in the " + \
                                 "Testbed.")
                
            return len(errors) == 0, errors, warnings
        
    is_consistent = staticmethod(is_consistent)