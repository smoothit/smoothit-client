from SisClient.Testbed.Reporting.analyzer import *
from Conditions import *
from SisClient.Testbed.Utils import plotter

# this is a test module that can be dynamically loaded into the testbed.
# every test function that you specify, has to start with the prefix "test".
# furthermore, a test function consumes a TestbedConfiguration object which
# is used to parameterize a concrete testbed situation.

# !!! this module serves as an example for your own tests !!!

def test_with_two_clients(conf):
    conf.set_base_directory("test_with_two_clients")
    conf.set_test_name("Test with two clients, file size 2.3 MB")
    conf.set_timeout(200)
    
    conf.add_file(1, "BaseLib/Test/testdata.txt")
    
    tracker = conf.add_tracker()
    
    client1 = conf.add_client(1)
    client1.set_port(10000)
    client1.set_uprate(32)
    client1.set_downrate(32)
    client1.add_file_to_leech(1)
    client1.set_logfile("test_with_two_clients/client1.log")
    
    client2 = conf.add_client(2)
    client2.set_port(10002)
    client2.set_uprate(32)
    client2.set_downrate(32)
    client2.add_file_to_seed(1)
    client2.set_logfile("test_with_two_clients/client2.log")
    
    conf.add_condition(IsLeechingCondition(1))
    conf.add_condition(IsSeedingCondition(1))
    conf.add_condition(IsSeedingCondition(2))
    
    conf.register_processor(plot_progress_for_clients)
    
def plot_progress_for_clients(datafile):
    if not os.path.isfile(datafile):
        return
    
    datafileHandle = open(datafile, 'r')
    datafileLines = datafileHandle.readlines()
    datafileHandle.close()
    
    data = []
    timeMin = 0
    timeMax = 0
    clients = {}
    for line in datafileLines:
        tokens = line.split("\t")
        ts = float(tokens[1])
        if ts > timeMax:
            timeMax = ts
        if ts < timeMin or timeMin == 0:
            timeMin = ts
        if int(tokens[0]) not in clients.keys():
            clients[int(tokens[0])] = []

    for line in datafileLines:
        tokens = line.split("\t")
        normalizedTime = float(tokens[1]) - timeMin
        clients[int(tokens[0])].append("%i %i" % (normalizedTime, int(tokens[3])))
    
    for i in xrange(len(clients)):
        tmpout = open('tmpfile%i.out' % (i+1), 'w')
        for line in clients[i+1]:
            print line
            tmpout.write(line + "\n")
        tmpout.close()
        
        plot = plotter.Plotter(".", "tmpfile%i.out" % (i+1), "progress_for_client%i" % (i+1),
                               "progress_for_client%i_gp"% (i+1), xlabel="time in s",
                               ylabel="progress in %")
        plot.addPlot(title="client %i" % (i+1), style="lines")
        plot.commitPlot()
        
        os.unlink('tmpfile%i.out' % (i+1))