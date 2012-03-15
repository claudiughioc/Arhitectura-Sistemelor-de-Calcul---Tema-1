"""
	ASC TEMA 1
"""

from manager import *
import sensor
import random
import sys

DEBUG = False

class Tester:
    """ Class containing the tests, each test uses a Manager instance 
        and randomly generates the  aggregation requests """
   
    def __init__(self):
        self.failed = False 
        self.currentTest = 0

    def simpleTest(self, testIndex, seed, numClusters, maxNodesPerCluster, numSteps,
                        numReqRange, numValReqRange):

        manager = Manager()
        (clusters, nodes) =  manager.generateOverlay(numClusters, maxNodesPerCluster)
        
        numNodes = len(nodes)

        rand = random.Random()
        rand.seed(seed)

        phases = []
        for step in range(numSteps):

            sensorType = SENSOR_TYPES["TEMP"]
            phase = []
            numRequests = rand.choice(numReqRange) 
            asked = [] #list of nodes communicating with the Manager
            totalReqCH = [] # all the clusters chosen for the aggregation
            
            # randomly choose the nodes which communicate with the Manager in the current phase
            for i in range(numRequests):

                nodeID = rand.randint(0, numNodes-1)
                node = nodes[nodeID]
                while node in asked:
                    nodeID = rand.randint(0, numNodes-1)
                    node = nodes[nodeID]
                asked.append(node)
    
                numReqVal = rand.choice(numValReqRange) # number of aggregation requests (clusters)
       
                # randomly choose the queried clusters 
                reqCH = [] # list of clusters chosen for the aggregation
                for i in range(numReqVal):
                    ch = asked[0] # must enter while
                    while ch in asked or ch in totalReqCH:
                        cl_index = rand.randint(0, numClusters - 1)
                        ch = clusters[cl_index][0].getClusterHead()
                    asked.extend(ch.getClusterNodes())
                    reqCH.append(ch)
                    totalReqCH.append(ch)

                totalReqCH.append(node.getClusterHead())
                asked.extend(node.getClusterHead().getClusterNodes())
            
                phase.append([nodes[nodeID], reqCH, sensorType])

            if DEBUG:
                print "asked", asked
                print "total", totalReqCH
            
            phases.append(phase) 
        
        self.failed = False
        self.currentTest = testIndex
        self.__startTestMessage(); 
        
        manager.runTest(self,phases) 
        
        if self.failed:
            print "Failed, exiting Tester..."
            sys.exit()
        else: print "Passed"

    def complexTest(self, testIndex, seed, numClusters, maxNodesPerCluster, numSteps,
                        numReqRange, numValReqRange, minSensorsPerNode, maxSensorsPerNode, doublePhase = 0):

        manager = Manager()
        (clusters, nodes) =  manager.generateOverlay(numClusters, maxNodesPerCluster, minSensorsPerNode, maxSensorsPerNode)
        
        numNodes = len(nodes)

        rand = random.Random()
        rand.seed(seed)

        phases = []
        for step in range(numSteps):

            phase = []
            numRequests = rand.choice(numReqRange) 
            asked = [] #list of nodes communicating with the Manager
            totalReqCH = [] # all the clusters chosen for the aggregation
            
            # randomly choose the nodes which communicate with the Manager in the current phase
            for i in range(numRequests):
                sensorType = rand.randint(0, maxSensorsPerNode - 1)
                nodeID = rand.randint(0, numNodes-1)
                node = nodes[nodeID]
                while node in asked:
                    nodeID = rand.randint(0, numNodes-1)
                    node = nodes[nodeID]
                asked.append(node)
    
                numReqVal = rand.choice(numValReqRange) # number of aggregation requests (clusters)
       
                # randomly choose the queried clusters 
                reqCH = [] # list of clusters chosen for the aggregation
                for i in range(numReqVal):
                    ch = asked[0] # must enter while
                    while ch in asked or ch in totalReqCH:
                        cl_index = rand.randint(0, numClusters - 1)
                        ch = clusters[cl_index][0].getClusterHead()
                    asked.extend(ch.getClusterNodes())
                    reqCH.append(ch)
                    totalReqCH.append(ch)

                totalReqCH.append(node.getClusterHead())
                asked.extend(node.getClusterHead().getClusterNodes())
            
                phase.append([nodes[nodeID], reqCH, sensorType])

            if DEBUG:
                print "asked", asked
                print "total", totalReqCH
            
            phases.append(phase)
            if doublePhase: phases.append(phase)
        
        self.failed = False
        self.currentTest = testIndex
        self.__startTestMessage(); 
        
        manager.runTest(self,phases) 
        
        if self.failed:
            print "Failed, exiting Tester..."
            sys.exit()
        else: print "Passed"
        
    def test1(self):
        
        numClusters = 10
        maxNodesPerCluster = 10
        numSteps = 3
        numReqRange = range(1,5)
        numValReqRange = range(1,3)
        seed = 1
        testIndex = 1
        dr = random.Random()
        dr.seed(seed)
        delays = [random.uniform(0,0.05) for i in range(100)]
        sensor.setDelayRange(delays)
        self.simpleTest(testIndex, seed, numClusters, maxNodesPerCluster, 
                    numSteps, numReqRange, numValReqRange) 

    def test2(self):
        numClusters = 20
        maxNodesPerCluster = 25
        numSteps = 5
        numReqRange = range(1,5)
        numValReqRange = range(1,5)
        seed = 3
        testIndex = 2
        self.simpleTest(testIndex, seed, numClusters, maxNodesPerCluster, 
                    numSteps, numReqRange, numValReqRange) 

    def test3(self):
        #multiple sensors
        numClusters = 20
        maxNodesPerCluster = 25
        numSteps = 5
        numReqRange = range(1,5)
        numValReqRange = range(1,5)
        seed = 5
        testIndex = 3
        minSensorsPerNode = 2
        maxSensorsPerNode = 3
        delays = [random.uniform(0.01, 0.05) for i in range(5)]
        sensor.setDelayRange(delays)
        self.complexTest(testIndex, seed, numClusters, maxNodesPerCluster, 
                    numSteps, numReqRange, numValReqRange, minSensorsPerNode, maxSensorsPerNode)
    def test4(self):
        #multiple sensors
        numClusters = 60
        maxNodesPerCluster = 5
        numSteps = 5
        numReqRange = range(5,10)
        numValReqRange = range(3,5)
        seed = 7
        testIndex = 4
        minSensorsPerNode = 1
        maxSensorsPerNode = 5
        delays = [random.uniform(0.01, 0.05) for i in range(5)]
        sensor.setDelayRange(delays)
        self.complexTest(testIndex, seed, numClusters, maxNodesPerCluster, 
                    numSteps, numReqRange, numValReqRange, minSensorsPerNode, maxSensorsPerNode, 1)

    def error(self, errorString):
        """
            Method used by the Manager during the tests each time an incorrect behaviour or an error is detected.
            The test has failed if this method was called at least once.
            @type errorString: str
            @param errorString: the error message
            @return: nothing
        """
        print "[TEST %d] %s" % (self.currentTest, errorString)
        self.failed = True

    
    def __startTestMessage(self):
        print "------------ TEST %d ----------- " % self.currentTest
    
if __name__ == "__main__":
    t = Tester()
    t.test1()
    t.test2()
    t.test3()
    t.test4()

