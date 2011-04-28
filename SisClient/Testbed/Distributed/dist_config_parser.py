import os
import sys
import ConfigParser

from SisClient.Testbed.TestbedConfig import TestbedClientConfiguration
from SisClient.Testbed.Distributed.dtestbed_config import DistributedDeployment
from SisClient.Testbed.Distributed.dtestbed_config import DistributedTestbedConfig
from SisClient.Testbed.Distributed.dtestbed_config import DistributedTrackerConfiguration

_type_mapping = {
    "sis_url"                   :   "string",
    "upload"                    :   "int",
    "download"                  :   "int",
    "remote_base_directory"     :   "string",
    "leech"                     :   "list,string",
    "seed"                      :   "list,string",
    "ps_mode"                   :   "string",
    "ns_mode"                   :   "string",
    "host"                      :   "string",
    "piece_length"              :   "int",
    "url"                       :   "string",
    "files"                     :   "list,string",
    "exit_on"                   :   "int",
    "seeding_time"              :   "int",
    "ranking_source"            :   "string",
    "waiting_time"              :   "int"
}

_method_mapping = {
    "sis_url"                   :   "set_sis_url",
    "upload"                    :   "set_uprate",
    "download"                  :   "set_downrate",
    "remote_base_directory"     :   "set_base_directory",
    "leech"                     :   "add_file_to_leech",
    "seed"                      :   "add_file_to_seed",
    "ps_mode"                   :   "set_peer_selection_mode",
    "ns_mode"                   :   "set_neighbour_selection_mode",
    "host"                      :   "set_hostname",
    "piece_length"              :   "set_piece_length",
    "url"                       :   "set_url",
    "files"                     :   "add_file",
    "exit_on"                   :   "set_exit_on",
    "seeding_time"              :   "set_seeding_time",
    "ranking_source"            :   "set_ranking_source",
    "waiting_time"              :   "set_waiting_time"
}

#_______________________________________________________________________________
# PUBLIC SECTION

def parse_distributed_configuration(filename):
    '''Processes a file that contains deployment information for a distributed
    testbed instance. By doing so, a DistributedTestbed object will be created,
    which holds the relevant data in slightly edited form so it can be directly
    applied to the the distributed testbed module (resolving mappings, ...).
    
    Parameter:
        filename -- The filename that contains the deployment information
                    for an instance of the distributed testbed.
    
    Return:
        DistributedTestbed object, containing the specified information.
        NoneType, if there was any error while parsing the deployment
        configuration.
    '''
    if not os.access(filename, os.F_OK):
        return None
    
    config_parser = ConfigParser.ConfigParser()
    config_parser.read(filename)
    _check_sections(config_parser)

    dtestbed = DistributedTestbedConfig()
    testb = _section_items_to_dictionary(config_parser, "testbed")
    hosts = _section_items_to_dictionary(config_parser, "hosts")
    files = _section_items_to_dictionary(config_parser, "files")
    
    # check host and file integrity
    for host_key in hosts.keys():
        dtestbed.add_host(host_key, hosts[host_key])
    _check_referenced_files(files)
    for file_key in files.keys():
        dtestbed.add_file(file_key, files[file_key])
    
    locc = _fetch_schemas(config_parser)
    _add_deployments(config_parser, dtestbed, locc, hosts)

    tracker = _build_tracker_configuration(config_parser, "tracker")
    dtestbed.set_tracker(tracker)
    
    # set testbed globals
    dtestbed.set_timeout(int(testb['timeout']))
    if "remove_remote_files" in testb.keys():
        dtestbed.set_remove_remote_files(testb['remove_remote_files'] == "true")
    if "logfile_directory" in testb.keys():
        logfile_directory = testb['logfile_directory']
        if not logfile_directory.endswith(os.path.normcase('/')):
            logfile_directory += os.path.normcase('/')
        dtestbed.set_logfile_directory(logfile_directory)
    # create linearization of events
    dtestbed.set_events(_linearize_events(testb['schedule'], dtestbed))
        
    return dtestbed

#_______________________________________________________________________________
# PRIVATE SECTION

def _check_sections(parser):
    '''Performs a simple check for required sections on a ConfigParser object.
    Throws an AssertionError if the deployment file that was parsed
    using the ConfigParser object before shows any signs of misconfiguration.
    
    Parameter:
        parser -- ConfigParser.ConfigParser object which has parsed a
                  deployment file before.
                  
    Return:
        NoneType
    '''
    to_check = ["tracker", "testbed", "files", "hosts", "deployment", "schema"]
    for section in parser.sections():
        for section_prefix in to_check:
            if str(section).startswith(section_prefix):
                to_check.remove(section_prefix)
    assert len(to_check) == 0
    assert len(parser.items("tracker")) > 0
    assert len(parser.items("testbed")) > 0
    assert len(parser.items("files")) > 0
    assert len(parser.items("hosts")) > 0
                
def _fetch_schemas(parser):
    '''Iterates through all sections of the parsed configuration file and
    fetches those sections that begin with "schema". If such a section
    is found, it will be dispatched to a builder method which uses the
    information in the section to construct a TestbedClientConfiguration
    object that is used to parameterize multiple clients in a distributed
    testbed setup.
    
    Parameter:
        parser -- ConfigParser.ConfigParser object which has parsed a
                  deployment file before.
                  
    Return:
        List of TestbedClientConfiguration objects. The list can be empty.
    '''
    locc = {}
    for section in parser.sections():
        if str(section).startswith("schema"):
            locc[section] = _build_schema_configuration(parser, section)
    return locc

def _add_deployments(parser, dtestbed, locc, hosts):
    '''Iterates through all sections of the parsed configuration file and
    fetches those sections that begin with "deployment". If such a section
    is found, it will be dispatched to a builder method which uses the
    information in the section to construct a DistributedDeployment
    object which is used to specify a the deployment of a specific client
    schema on multiple remote host machines.
    
    Parameters:
        parser   -- ConfigParser.ConfigParser object which has parsed a
                    deployment file before.
        dtestbed -- DistributedTestbedConfig object
        locc     -- List of TestbedClientConfiguration objects
        hosts    -- Dictionary that contains all specified hosts. Keys are
                    represented by the abbreviated form of the hostname, values
                    contain the full hostname.
                    
    Return:
        NoneType
    '''
    for section in parser.sections():
        if str(section).startswith("deployment"):
            dpl = _build_deployment_configuration(parser, section, locc, hosts)
            dtestbed.add_deployment(section, dpl)

def _build_tracker_configuration(parser, section):
    '''Fetches the tracker configuration section and constructs a
    parameterized DistributedTrackerConfiguration object from the information
    given by that section. key-value-pairs of that section are resolved using
    the method and type mapping functionality provided by this module. See
    _set_class_attributes_from_section for further information.
    
    Parameters:
        parser  -- ConfigParser.ConfigParser object which has parsed a
                   deployment file before.
        section -- String value that represents the name of the tracker section.
        
    Return:
        DistributedTrackerConfiguration object which holds the information
        that was specified in the tracker section of the deployment file.
    '''
    tracker = DistributedTrackerConfiguration()
    _set_class_attributes_from_section(tracker, parser, section)
    return tracker

def _section_items_to_dictionary(parser, section):
    '''Helper method that fetches all key-value pairs of a given section and
    stores them in a dictionary. Please note that this function does not check
    if the specified actually exists. This check will be performed beforehand
    (see _check_sections function of this module).
    
    Parameters:
        parser  -- ConfigParser.ConfigParser object that was used to parse
                   a deployment file before.
        section -- String value which represents the name of the section
                   for which the dictionary shall be built.
                   
    Return:
        A dictionary that contains the key-value-pairs that were directly
        read from the specified section. The dictionary can be empty, if the
        section does not provide any key-value-pairs.
    '''
    tmpd = {}
    for name, value in parser.items(section):
        tmpd[name] = value
    return tmpd

def _convert(name, value):
    '''Helper method which is used to convert to the correct type of an
    configuration attribute. The nature of this function is very simplistic.
    It looks up the desired data type in the global _type_mapping dictionary
    by the given name parameter, converts the value according to the
    found type mapping and returns it to the caller. Please note that
    no conversion takes place if the resolved type mapping is string, since
    the passed value argument is already represented by a string.
    
    Parameters:
        name  -- String value which represents the key of a type mapping that
                 corresponds to the desired type for the given value parameter.
        value -- String representation of a value that shall be converted
                 to its appropriate data type.
                 
    Return:
        The converted value (in its appropriate representation). NoneType,
        if the type mapping is not correct, e.g. if the desired data type
        can not be determined.
    '''
    global _type_mapping
    
    data_type = _type_mapping[name]
    converted_value = None
    if data_type == "int":
        converted_value = int(value)
    if data_type == "string":
        converted_value = value
    if data_type == "list,string":
        converted_value = [value for value in value.split(" ")]
    return converted_value

def _build_schema_configuration(parser, section):
    '''Constructs a TestbedClientConfiguration object from a given schema
    section of the deployment file. This object will be used later on to
    parameterize the clients for a specific deployment.
    
    Parameters:
        parser  -- ConfigParser.ConfigParser object that was used to parse
                   a deployment file before.
        section -- String value that represents the name of a concrete
                   schema section of the deployment file.
                   
    Return:
        TestbedClientConfiguration object which holds the information
        associated with the given client configuration schema.
    '''
    cc = TestbedClientConfiguration(-1)
    _set_class_attributes_from_section(cc, parser, section)
    return cc

def _set_class_attributes_from_section(instance, parser, section):
    '''This function is used to automatically set member variables of a
    class instance, given a method mapping. This mapping maps keys (from a
    section) to a class method, so that the values associated with those keys
    can be used to alter member variables of a given object. The method does
    the appropriate conversion to the correct data type. It uses Python's
    reflection capabilities to resolve class method names.
    
    The function will terminate the execution of the script in case of:
    * There is no appropriate key specified by the method mapping.
    * The method name given by the method mapping does not exist for the
      given instance.
      
    Parameters:
        instance -- Instance of a non-specified class whose member variables
                    shall be set using a method name mapping and the data
                    read from the given section.
        parser   -- ConfigParser.ConfigParser object that was used to parse
                    a deployment file before.
        section  -- String representation of the section whose key-value-pairs
                    shall be used to parameterize the given class instance.
                    
    Return:
        NoneType
    '''
    global _method_mapping
    
    for name, value in parser.items(section):
        if name not in _method_mapping.keys():
            print >>sys.stderr, "Key %s not specified in method mapping" % name
            sys.exit(1)
        method_name_as_string = _method_mapping[name]
        if method_name_as_string not in dir(instance):
            print >>sys.stderr, "Method name unknown for given instance"
            sys.exit(1)
        converted_value = _convert(name, value)
        if isinstance(converted_value, list):
            for list_item in converted_value:
                getattr(instance, method_name_as_string)(list_item)
        else:
            getattr(instance, method_name_as_string)(converted_value)

def _build_deployment_configuration(parser, section, locc, hosts):
    '''Reads the relevant information from a given deployment section of the
    parsed configuration file and uses this information to construct a
    DistributedDeployment object. Returns the newly created object.
    
    The function will terminate the execution of the script in case of:
    * The deployment information references a host that was not specified.
    * The deployment information references a client schema that was not
      specified.
    * If one or more of the attributes in (hosts, schema, remote_base_directory)
      is missing for the given section.
      
    Parameters:
        parser  -- ConfigParser.ConfigParser object that was used to parse
                   a deployment file before.
        section -- String value which represents the section of a concrete
                   deployment.
        locc    -- List of TestbedClientConfiguration objects.
        hosts   -- Dictionary that contains all specified hosts. Keys are
                   represented by the abbreviated form of the hostname, values
                   contain the full hostname.
        
    Return:
        DeploymentConfiguration object which stores the necessary data.
    '''
    try:
        hostlist = map(lambda x: x.strip(), parser.get(section, "hosts").split(','))
        schema = parser.get(section, "schema")
        remote_base_dir = parser.get(section, "remote_base_directory")

        for hostname in hostlist:
            if hostname not in hosts.keys():
                print >>sys.stderr, "Deployment configuration references a " + \
                                    "non-valid host."
                sys.exit(1)
                                
        if schema not in locc.keys():
            print >>sys.stderr, "Deployment configuration references a " + \
                                "non-valid client schema."
            sys.exit(1)
                                
        # resolve host names for deployment
        hostlist = map(lambda x: hosts[x], hostlist)
        deploy = DistributedDeployment(locc[schema], hostlist, remote_base_dir)
        
    except ConfigParser.NoOptionError:
        print >>sys.stderr, "Deployment configuration is not well-defined"
        sys.exit(1)
        
    return deploy

def _check_referenced_files(files):
    '''This method ensures that every references file is accessible from the
    current scripts working directory context. If there is at least one file
    that is inaccessible or does not exist, the script will terminate its
    execution since the provided configuration is not consistent.
    
    Parameters:
        files -- List of string values, each representing a file that
                 shall be distributed in the testbed and must exist
                 on the local machine.
                 
    Return:
        NoneType
    '''
    for file in files.values():
        if not os.access(file, os.F_OK):
            print >>sys.stderr, "Referenced file %s is missing." % str(file)
            sys.exit(1)
            
def _linearize_events(schedule_file, dtestbed):
    '''Reads the birth information (for clients) from an external schedule file.
    The deployment configuration file references the schedule file.
    
    The function will terminate the execution of the script in case of:
    * The schedule file is inaccessible or does not exist.
    * The schedule file is not well-formed.
    * The schedule file references a non-valid deployment name.
 
    Parameters:
        schedule_file -- String value which represents the filename of the
                         schedule.
        dtestbed      -- DistributedTestbedConfig object.

    Return:
        A list which represents a time-based sorted sequence of birth events
        for the distributed testbed. Such an event is described by the 3-tuple:
        (event_time, client_number, deployment_name)
        
   '''
    if not os.access(schedule_file, os.F_OK):
        print >>sys.stderr, "Referenced schedule file %s is not readable." % str(schedule_file)
        sys.exit(1)
    
    events = []
    handle = open(schedule_file, 'r')
    cspecs = handle.readlines()
    client_no = 0
    for cspec in cspecs:
        # split the line into tokens and erase whitespaces before/after a token
        cspec_tokens = map(lambda x: x.strip(), cspec.split(' '))
        if len(cspec_tokens) != 2:
            print >>sys.stderr, "Schedule file is not well-defined at line %i: %s" \
                % (client_no+1, cspec)
            sys.exit(1)
        if cspec_tokens[1] not in dtestbed.get_deployments().keys():
            print >>sys.stderr, "Schedule file references a non-valid deployment " + \
                                "at line %i: %s" % (client_no+1, cspec)
            sys.exit(1)
        events.append((int(cspec_tokens[0]), client_no, cspec_tokens[1]))
        client_no += 1
    # linearize (sort) events
    events.sort(lambda x,y: cmp(x[0], y[0]))
    return events