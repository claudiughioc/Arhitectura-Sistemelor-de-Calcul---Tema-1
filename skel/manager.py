"""
	ASC TEMA 1
"""

import threading, random, copy
from sensor import *
from node import *

DEBUG = True
#DEBUG = False

class Manager:

    nThreads = {}   # associates threads and node IDs
    chThreads = {}  # associates threads and cluster head IDs
    nodes = []      # all the nodes (including cluster heads) in the network
    clusters = []   # list of clusters - each cluster consists of a list of nodes, including its CH
    recvResults = {} # the results received from the interrogated nodes during a phase (key - nodeID, value - result)
    
    def __init__(self, seed = 0):
        """
            @param seed: the seed for its pseudo-random generator
        """
        self.randGen = random.Random()
        self.seed = seed
        self.randGen.seed(seed)
        self.respLock = threading.Lock()
        self.registerNodeLock = threading.Lock()
        self.registerCHLock = threading.Lock()
        self.printLock = threading.Lock()

    def __initVar(self):
        """
            Initialize variables used in tests
        """
        self.nThreads = {}
        self.chThreads = {}
        self.recvResults = {}
 
    def generateSensors(self, numSensors):
        """ Randomly generates sensor data. 
            @param numSensors: the number of sensors
            @return:  a list of Sensor objects 
        """
        sensors = []
        for i in range(numSensors):
            sensor = Sensor(self.randGen.random()) #randomly generate the sensors' seeds
            sensors.append(sensor)
        return sensors

    def generateNodes(self, sensors, firstID, clusterHeadID):
        """
            Creates nodes based on a list of sensors.
            @param sensors: a list of sensors that will be assigned to nodes
            @param firstID: the nodes' identifiers are based on this parameter
            @param clusterHeadID: the index(in the list of nodes of the generated cluster) of the node 
            that is Cluster Head for the generated nodes
            @return: a list of Node objects
        """
      
        # create clusterHead node 
        chID = clusterHeadID+firstID 
        clusterHead = ClusterHead(nodeID = chID, sensors = [sensors[clusterHeadID]], manager = self)
        
        # create nodes and associate them to the CH
        nodes = [] 
        for i in range(len(sensors)):
            if i != clusterHeadID:
                node = Node (nodeID = i + firstID, sensors = [sensors[i]], manager = self)
                node.setClusterHead(clusterHead)
                nodes.append(node)
            else: nodes.append(clusterHead)
        
        clusterHead.setClusterNodes([x for x in nodes])# if x!=clusterHead])
        
        return nodes


    def generateCluster(self, numNodes, clusterHeadID, firstID):
        """
            Creates a cluster of sensor nodes.
            @param numNodes: the number of nodes per cluster
            @param clusterHeadID: the index(in the list of nodes of the generated cluster) of the node 
            that is Cluster Head
            @param firstID: the nodes' identifiers are based on this parameter
            @return: a list of Node objects
        """
        sensors = self.generateSensors(numNodes)
        nodes = self.generateNodes(sensors, firstID, clusterHeadID)
        return nodes


    def generateOverlay(self, numClusters, maxNodesPerCluster):
        """
            Randomly generates an overlay.
            @param numClusters: number of clusters
            @param maxNodesPerCluster: maximum number of nodes in each cluster
            @return: a list of clusters, each cluster being represented by a list of Node objects
        """
        #generate number of nodes per cluster
        nodesCluster = []
        for i in range(numClusters):
            nodesCluster.append(self.randGen.randint(2, maxNodesPerCluster))        
             
        # create and assign nodes into clusters
        # randomly choose the clusterHead nodes
        numNodes = 0
        self.clusters = []
        self.nodes = []
        for i in range(numClusters):
            nodes = self.generateCluster(nodesCluster[i], 
                            self.randGen.randint(0, nodesCluster[i]-1), 
                            numNodes)
            numNodes = numNodes + nodesCluster[i]
            self.clusters.append(nodes)
            self.nodes.extend(nodes)

        return (self.clusters, self.nodes)
    
    def runTest(self, tester, phases):
        """
            @param phases: a list of lists of requests. A request contains the interrogated node id, 
            a list of cluster heads and the aggregated data type (e.g. temperature) 
            For example: [ [[x1,[ch1,ch2],temp], [y1,[ch3,ch4]]], [[x2,[ch3,ch1],temp]]]
        """
        if DEBUG:
                print "Intru in manager.runTest\n"
        self.tester = tester
        
        #reinitialize test related variables
        self.__initVar()

        self.waitPhase = threading.Semaphore()

        #start nodes
        for node in self.nodes:
            node.start()

        for i in range(len(phases)):
            if DEBUG:
                print "PHASE", i
                for req in phases[i]:
                    print req[0], req[0].getClusterHead()
                    print req[1]
            
            # inform sensors
            for n in self.nodes:
                for s in n.getSensors():
                    s.nextPhase()
            
            # send requests and wait for all the responses
            requests = phases[i]
            self.recvResults = {}
            self.numResponses = 0
                
            for req in requests:
                req[0].getAggregatedData(req[1], req[2])

            activatedThreads = 0
            for req in requests:
                for cluster in req[1]:
                    activatedThreads += len(cluster.getClusterNodes())
                if req[0].getClusterHead() not in req[1]:
                    activatedThreads += 1
                    if req[0].getClusterHead() != req[0]:
                        activatedThreads += 1

            # wait for results
            while self.numResponses < len(requests): 
                continue
            if DEBUG:
                    print "Am primit toate rezultatele de la noduri\n"

            # verify results
            errorString = ""
            testResults =   self.getCorrectResults(self.clusters, requests) 
            results = self.recvResults 
            if len(results) == len(testResults):
                for node in results.keys():
                    if type(results[node]) == type(testResults[node]):
                        if results[node] == testResults[node]:
                            continue
                        else:
                            errorString = "Incorrect results (%f,%f) instead of (%f,%f)" % (results[node][0],
                                                        results[node][1], testResults[node][0], testResults[node][1])
                            break
                    else: 
                        errorString = "Invalid data structure type for results, it must be 'tuple' not %s" % type(results[node])
                        break
            else: errorString = "Incorrect number of aggregation results in phase %d %d!=%d"%(i,len(results), len(testResults)) 
          
            if len(errorString) > 0:
                self.tester.error(errorString)

            for i in range(activatedThreads):
                self.waitPhase.acquire()

        for node in self.nodes:
            node.getAggregatedData(None, None)

        for node in self.nodes:
            node.join()
   
    def nextPhase(self):
        """ Used by the Node objects to inform about the completion of an aggregation phase """
        self.waitPhase.release()

    def submitResponse(self, node, results):
        """
            Receives a list of aggregation results from a queried node and appends it to the
            other results received during the current aggregation phase
            @param node: the node queried by the Manager during the current test phase
            @param results: a tuple with MIN and MAX aggregates for the requested list of clusters
            @return: nothing
        """
        self.respLock.acquire()
        self.recvResults[node.getNodeID()] = results
        self.numResponses += 1 
        if DEBUG:
            print "[Manager] received %d responses" % (self.numResponses)
        self.respLock.release()
    
    def getCorrectResults(self, clusters, requests): 
        """
        @param clusters: the list of lists of nodes representing clusters
        @param requests: list of tuples (interrogated_node, list_requests, sensor_type), interrogated_nodes being the node
                that received a request from the Manager and list_requests the list of cluster head IDs 
        @return: a dictionary of tuples (min, max), where min and max are the MIN and MAX aggregate results for a list of clusters
        """
        results = {}
        for req in requests:
            minValue = float("inf")
            maxValue = float("-inf")
            for cluster in req[1]:
                nodes = cluster.getClusterNodes()
                for node in nodes:
                    for sensor in node.getSensors():
                        if sensor.getType() == req[2]:
                            value = sensor.getValue()
                            break
                    if value < minValue: minValue = value
                    if value > maxValue: 
                        maxValue = value
            
            results[req[0].getNodeID()] = (minValue, maxValue)
        return results

    def registerNode(self, node):
        """
            Registers a node's thread. Called by the nodes.
            @param node: a Node object
            @return: nothing
        """
        t = threading.current_thread()
        errorString = "" 
        self.registerNodeLock.acquire()
        if t in self.nThreads:
            errorString = "Thread " + str(t) + " is already running for node " + str(nThreads[t].getNodeID())
        elif node in self.nThreads.values():
            errorString = "Node " + str(nThreads[t].getNodeID()) + " already has a running thread: " + str(t)
        else: 
            self.nThreads[t] = node

        self.registerNodeLock.release()

        if len(errorString):    
            self.tester.error("Error registering node:\n"+errorString)

        if DEBUG:
            self.printLock.acquire()
            print "Registered node", node.getNodeID(), node
            self.printLock.release()

    def registerClusterHead(self, node):
        """
            Registers a cluster head node's threads. Called by the cluster head nodes.
            @param node: a ClusterHead object
            @return: nothing
        """
        t = threading.current_thread()
        errorString = ""
        
        self.registerCHLock.acquire() 
        if t in self.chThreads:
            errorString += "\nThread " + str(t) + " is already running for cluster head node " + str(chThreads[t].getNodeID())
        elif node in self.chThreads.values():
            errorString += "\nCluster Head " + str(ch[t].getNodeID()) + " already has a running thread: " + str(t)
        else: 
            self.chThreads[t] = node

        self.registerCHLock.release() 

        if len(errorString):    
            self.tester.error("Error registering cluster head node:"+errorString)

        if DEBUG:
            self.printLock.acquire()
            print "Registered cluster head", node.getNodeID(), node
            self.printLock.release()
                
    def notify_req_node2cluster(self, node, cluster, sensorType):
        """
            A node notifies the Manager about a request sent to a cluster head. This method checks the validity
            of the nodes and request.
            @param node: a Node object (source)
            @param cluster: a ClusterHead object (destination)
            @param sensorType: the type of sensor used in the aggregation, as defined in Sensor.SENSOR_TYPES
            @return: nothing 
        """
        errorString = ""
        self.registerNodeLock.acquire() 
        t = threading.current_thread()
        if self.nThreads[t] != node:
            errorString += "\n Node " + str(node.getNodeID()) + " is not registered"
        self.registerNodeLock.release()

        self.registerCHLock.acquire() 
        if cluster not in self.chThreads.values():
            errorString += "\n Cluster Head " + str(cluster.getNodeID()) + " is not registered" + str(cluster.currentThread())
        self.registerCHLock.release() 

        if cluster.getNodeID() == node.getNodeID():
            errorString += "\n The Node and the cluster head node have the same ID: " + str(cluster.getNodeID())

        if len(errorString):
            self.tester.error("Error registering request:"+errorString)
        else:
            pass

        if DEBUG:
            self.printLock.acquire()
            print "Node2Cluster request", node, cluster, sensorType
            self.printLock.release()
        
    def notify_req_cluster2cluster(self, cluster, other, sensorType):
        """
            A cluster head node notifies the Manager about a request sent to another cluster head. This method checks the validity
            of the nodes and request.
            @param cluster: a ClusterHead object (source)
            @param other: a ClusterHead object (destination)
            @param sensorType: the type of sensor used in the aggregation, as defined in Sensor.SENSOR_TYPES
            @return: nothing 
        """
        errorString = "" 
        self.registerCHLock.acquire() 
        t = threading.current_thread()
        if self.chThreads[t] != cluster:
            errorString += "\n Cluster Head " + str(cluster.getNodeID()) + " is not registered"
        if other not in self.chThreads.values():
            errorString += "\n Cluster Head " + str(other.getNodeID()) + " is not registered"
        self.registerCHLock.release() 
        if cluster.getNodeID() == other.getNodeID():
            errorString += "\n Cluster Heads have the same ID: " + str(cluster.getNodeID())
        if len(errorString):
            self.tester.error("Error registering request:" + errorString)
        else: 
            pass

        if DEBUG:
            self.printLock.acquire()
            print "Cluster2Cluster request", cluster, other, sensorType
            self.printLock.release()
             
    def notify_req_cluster2node(self, cluster, node, sensorType):
        """
            A cluster head node notifies the Manager about a request sent to a node. This method checks the validity
            of the nodes and request.
            @param cluster: a ClusterHead object (source)
            @param node: a Node object (destination)
            @param sensorType: the type of sensor used in the aggregation, as defined in Sensor.SENSOR_TYPES
            @return: nothing 
        """
        errorString = "" 
        self.registerCHLock.acquire() 
        t = threading.current_thread()
        if self.chThreads[t] != cluster:
            errorString += "\n Aici0 Cluster Head " + str(cluster.getNodeID()) + " is not registered"
        self.registerCHLock.release() 
        
        self.registerNodeLock.acquire() 
        if node not in self.nThreads.values():
            errorString += "\n Node " + str(node.getNodeID()) + " is not registered"
        self.registerNodeLock.release() 
        
        if cluster.getNodeID() == node.getNodeID():
            errorString += "\n The node and the cluster head node have the same ID: "
        
        if len(errorString):
            self.tester.error("Error registering request:" + errorString)
        else:
            pass

        if DEBUG:
            self.printLock.acquire()
            print "Cluster2Node request", cluster, node, sensorType
            self.printLock.release()
 
    def notify_resp_node2cluster(self, node, cluster, resp):
        """
            A node notifies the Manager about a response sent to a cluster head node. This method checks the validity
            of the nodes and response.
            @param node: a Node object (source)
            @param cluster: a ClusterHead object (destination)
            @param resp: the response
            @return: nothing 
        """
        errorString = "" 
        self.registerNodeLock.acquire() 
        t = threading.current_thread()
        if self.nThreads[t] != node:
            errorString += "\n Node " + str(node.getNodeID()) + " is not registered"
        self.registerNodeLock.release() 
        
        self.registerCHLock.acquire() 
        if cluster not in self.chThreads.values():
            errorString += "\n Cluster Head " + str(cluster.getNodeID()) + " is not registered"
        self.registerCHLock.release() 
        
        if cluster.getNodeID() == node.getNodeID():
            errorString += "\n The node and the cluster head node have the same ID: " + str(cluster.getNodeID())
        
        if len(errorString):
            self.tester.error("Error registering response:" + errorString)
        else:
            pass

        if DEBUG:
            self.printLock.acquire()
            print "Node2Cluster response", node, cluster, resp
            self.printLock.release()
        
    def notify_resp_cluster2cluster(self, cluster, other, resp):
        """
            A cluster head node notifies the Manager about a response sent to another cluster head node. This method checks the validity
            of the nodes and response.
            @param cluster: a ClusterHead object (source)
            @param other: a ClusterHead object (destination)
            @param resp: the response
            @return: nothing 
        """
        errorString = "" 
        
        self.registerCHLock.acquire() 
        t = threading.current_thread()
        if self.chThreads[t] != cluster:
            errorString += "\n Cluster Head " + str(cluster.getNodeID()) + " is not registered"
        
        if other not in self.chThreads.values():
            errorString += "\n Cluster Head " + str(other.getNodeID()) + " is not registered"
        self.registerCHLock.release() 
        
        if cluster.getNodeID() == other.getNodeID():
            errorString += "\n The cluster head nodes have the same ID: " + str(cluster.getNodeID())
        
        if len(errorString):
            self.tester.error("Error registering response:" + errorString)
        else:
            pass

        if DEBUG:
            self.printLock.acquire()
            print "Cluster2Cluster response", cluster, other, resp
            self.printLock.release()
    
    def notify_resp_cluster2node(self, cluster, node, resp):
        """
            A cluster head node notifies the Manager about a response sent to a node. This method checks the validity
            of the nodes and response.
            @param cluster: a ClusterHead object (source)
            @param node: a Node object (destination)
            @param resp: the response
            @return: nothing 
        """
        errorString = "" 
        self.registerCHLock.acquire() 
        t = threading.current_thread()
        if self.chThreads[t] != cluster:
            errorString += "\n Cluster Head " + str(cluster.getNodeID()) + " is not registered"
        self.registerCHLock.release() 
        
        self.registerNodeLock.acquire() 
        if node not in self.nThreads.values():
            errorString += "\n Node " + str(node.getNodeID()) + " is not registered"
        self.registerNodeLock.release() 
        
        if cluster.getNodeID() == node.getNodeID():
            errorString += "\n The cluster head node and the node have the same ID: " + str(cluster.getNodeID())
        if len(errorString):
            self.tester.error("x1 Error registering response:" + errorString)
        else:
            pass

        if DEBUG:
            self.printLock.acquire()
            print "Cluster2Node response", cluster, node, resp
            self.printLock.release()

    def printMsg(self, msg):
        """ Called by the threads to print a message """
        self.printLock.acquire()
        print msg
        self.printLock.release()
            
        
