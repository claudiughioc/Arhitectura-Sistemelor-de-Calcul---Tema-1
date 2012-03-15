"""
	ASC TEMA 1
"""

import threading
import manager, sensor

DEBUG = True
DEFAULT_MIN_VALUE = 0

class Node(threading.Thread):
    """
        Class representing a sensor node. Each node has a unique identifier and a list of 
        sensors (Sensor objects) of different types. The nodes are clustered and they have a reference
        to the cluster head node (ClusterHead object). The node is a Thread that waits for aggregation
        requests from the Manager or other nodes or cluster head nodes. For testing purposes, each
        node must communicate with the Manager notifying it about its actions.
    """
    tuplu = []

    def __init__(self, nodeID, sensors, manager):
        threading.Thread.__init__(self)
        self.nodeID = nodeID

        self.sensors = {};
        for sensor in sensors:
            self.sensors[sensor.sensorType] = sensor
        self.clusterHead = None
        self.manager = manager

    def init_values(self):
        self.parentIsManager = False
        self.responseReceived = False
        self.parentIsCluster = False
        self.reqReceived = False
        self.die = False
        self.tuplu = ()
        self.reqClusters = {}
        self.sensor_type = None
        
        
    def getNodeID(self):
        return self.nodeID

    def getSensors(self):
        return self.sensors.values()

    def setClusterHead(self, clusterHead):
        self.clusterHead = clusterHead

    def getClusterHead(self):
        return self.clusterHead

    def receiveResponseFromCluster(self, tuplu):
        self.tuplu = tuplu
        self.responseReceived = True

    def requestClusterToNode(self, parent, sensor_type):
        self.parent = parent
        self.sensor_type = sensor_type
        self.parentIsCluster = True
        self.reqReceived = True

    def replyToCluster(self):
        sensor = self.sensors[self.sensor_type]
        value = sensor.getValue()
        print self.name + " intorc " + str(value) + "\n"
        self.parent.receiveResponseFromNode(value)
        self.manager.notify_resp_node2cluster(self, self.parent, self.sensor_type)

    def replyToManager(self):
        if (self.getClusterHead in self.reqClusters):
                sensor = self.sensors[self.sensor_type]
                minim = sensor.getValue()
                maxim = minim
                if minim < self.tuplu[0]:
                        self.tuplu[0] = minim
                if maxim > self.tuplu[1]:
                        self.tuplu[1] = maxim
        print self.name + " intorc la manager" + str(self.tuplu) + "\n"
        self.manager.submitResponse(self, self.tuplu)
   
    def forwardToCluster(self):
        print self.name + " forward to " + str(self.reqClusters)
        self.clusterHead.requestNodeToCluster(self, self.reqClusters, self.sensor_type)
        self.manager.notify_req_node2cluster(self, self.clusterHead, self.sensor_type)
        
    def run(self):
        self.manager.registerNode(self)
        self.init_values()
        self.name = "Thread " + str(self.nodeID)
        while (1):
                if (self.reqReceived == True):
                        if self.parentIsManager == True:
                                self.forwardToCluster()
                                while self.responseReceived == False:
                                        continue
                                self.replyToManager()
                                self.parentIsManager = False
                        if self.parentIsCluster == True:
                                self.replyToCluster() 
                                self.parentIsCluster = False
                        self.init_values()
                        self.manager.nextPhase()
                if (self.die == True):
                        break
                continue
        print "Exit thread " + str(self.nodeID) + "\n"

    def getAggregatedData(self, clusters, sensor_type):
            if (sensor_type != None):
                    print "\n" + self.name + "primeste cerere de la manager\n"
                    self.reqClusters = clusters
                    self.sensor_type = sensor_type
                    self.parentIsManager = True
                    self.reqReceived = True
            else:
                    self.die = True

class ClusterHead(threading.Thread):
    """
        Class representing a sensor node which acts as a cluster head. In addition to its unique identifier and a list of 
        sensors (Sensor objects) of different types, it also keeps the list of nodes(including itself) in its cluster.
        The node is a Thread that waits for aggregation requests from the Manager or other cluster head nodes. For testing purposes, 
        each cluster head must communicate with the Manager notifying it about its actions.
    """

    def __init__(self, nodeID, sensors, manager):
        threading.Thread.__init__(self)
        self.nodeID = nodeID
        self.sensors = {};

        for sensor in sensors:
            self.sensors[sensor.sensorType] = sensor
        self.clusterNodes = None
        self.manager = manager

    def init_values(self):
        self.parentIsManager = False
        self.parentIsCluster = False
        self.parentIsNode = False
        self.reqReceived = False
        self.die = False

        self.sensor_type = None
        self.responses = 0
        self.reqClusters = {};
        self.destNodes = {};
        self.destClusters = {};
        self.results = [];
        self.value = None
        self.tuples = []
        self.responseLock = threading.Lock()

    def getNodeID(self):
        return self.nodeID

    def getSensors(self):
        return self.sensors.values()

    def getClusterNodes(self):
        return self.clusterNodes

    def setClusterNodes(self, clusterNodes):
        self.clusterNodes = clusterNodes

    def getClusterHead(self):
        return self

    def receiveResponseFromNode(self, result):
        self.responseLock.acquire()
        self.results.append(result)
        self.responses += 1
        self.responseLock.release()

    def receiveResponseFromCluster(self, tuplu):
        self.responseLock.acquire()
        self.tuples.append(tuplu)
        self.responses += 1
        self.responseLock.release()

    def requestNodeToCluster(self, parent, reqClusters, sensor_type):
        self.parent = parent      
        self.reqClusters = reqClusters
        self.sensor_type = sensor_type
        self.parentIsNode = True
        self.reqReceived = True

    def requestClusterToCluster(self, parent, sensor_type):
        self.parent = parent      
        self.parentIsCluster = True;
        self.sensor_type = sensor_type
        self.reqReceived = True

    def forwardRequestToClusters(self):
        self.destClusters = self.reqClusters;
        if (self in self.reqClusters):
                self.destClusters.remove(self)
        print self.name + " la clustere " + str(self.destClusters) + "\n"

        if self.destClusters:
                for cluster in self.destClusters:
                        #apeleaza functia de request pt respectivul cluster
                        cluster.requestClusterToCluster(self, self.sensor_type)
                        self.manager.notify_req_cluster2cluster(self, cluster, self.sensor_type)
        

    def forwardRequestToNodes(self, managerNode):
            self.destNodes = self.getClusterNodes()
            if self in self.destNodes:
                self.destNodes.remove(self)
            if managerNode != None:
                self.destNodes.remove(managerNode)
            print self.name + " dau la nodurile mele " + str(self.destNodes)
            for node in self.destNodes:
                #apeleaza functia de request pt node
                node.requestClusterToNode(self, self.sensor_type)
                self.manager.notify_req_cluster2node(self, node, self.sensor_type)

    # Calculate the final results per Cluster Head
    def aggregateResults(self):
        """
        properSensor = self.sensors[self.sensor_type]
        if (self.parentIsCluster == True):
                minim = properSensor.getValue();
                print self.name + " intoarce sil sil " + str(minim) + "\n"
        else:   
                if (self in self.reqClusters):
                        minim = properSensor.getValue();
                        print self.name + " intoarce sil sil " + str(minim) + "\n"
                else:   minim = DEFAULT_MIN_VALUE
                        """
        minim = DEFAULT_MIN_VALUE
        maxim = minim
        for result in self.results:
                if minim == DEFAULT_MIN_VALUE:
                        minim = result
                if maxim == DEFAULT_MIN_VALUE:
                        maxim = result
                if result > maxim:
                        maxim = result
                if result < minim:
                        minim = result
        for tuplu in self.tuples:
                if minim == DEFAULT_MIN_VALUE:
                        minim = tuplu[0]
                if maxim == DEFAULT_MIN_VALUE:
                        maxim = tuplu[1]
                if tuplu[0] < minim:
                        minim = tuplu[0]
                if tuplu[1] > maxim:
                        maxim = tuplu[1]
        self.value = (minim, maxim)


    def forwardResponse(self):
        print self.name + " intorc " + str(self.value) + "\n"
        if self.parentIsCluster:
                self.parent.receiveResponseFromCluster(self.value)
                self.manager.notify_resp_cluster2cluster(self, self.parent, self.sensor_type)
                self.parentIsCluster = False
        if self.parentIsManager:
                self.manager.submitResponse(self, self.value)
                self.parentIsManager = False
        if self.parentIsNode:
                self.parent.receiveResponseFromCluster(self.value)
                self.manager.notify_resp_cluster2node(self, self.parent, self.sensor_type)
                self.parentIsNode = False



    def run(self):
        self.manager.registerClusterHead(self)
        self.init_values()
        self.name = "Clustera " + str(self.nodeID)
        while (1):
                if self.reqReceived == True:
                        # Decide how to forward to own nodes
                        if self in self.reqClusters:
                                if self.parentIsNode == True:
                                        self.forwardRequestToNodes(self.parent)
                                if self.parentIsManager == True:
                                        self.forwardRequestToNodes(None)

                        if self.parentIsCluster == True:
                                self.forwardRequestToNodes(None)

                        if (self.parentIsCluster == False):
                                self.forwardRequestToClusters()

                        #wait for all the nodes and clusters to respond
                        leng =  len(self.destNodes) + len(self.destClusters)
                        while (self.responses < leng):
                                continue
                        self.aggregateResults()
                        self.forwardResponse()
                        self.init_values()
                        self.manager.nextPhase()
                if (self.die == True):
                        break
                continue

        print "Exit thread " + str(self.nodeID) + "\n"

    def getAggregatedData(self, clusters, sensor_type):
            if (sensor_type != None):
                    print "\n" + self.name + " primesc cerere de la manager\n"
                    self.reqClusters = clusters
                    self.sensor_type = sensor_type
                    self.parentIsManager = True
                    self.reqReceived = True
            else:
                    self.die = True
