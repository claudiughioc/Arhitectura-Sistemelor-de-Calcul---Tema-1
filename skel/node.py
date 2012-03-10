"""
	ASC TEMA 1
"""

import threading
import manager, sensor

DEBUG = True

class Node(threading.Thread):
    """
        Class representing a sensor node. Each node has a unique identifier and a list of 
        sensors (Sensor objects) of different types. The nodes are clustered and they have a reference
        to the cluster head node (ClusterHead object). The node is a Thread that waits for aggregation
        requests from the Manager or other nodes or cluster head nodes. For testing purposes, each
        node must communicate with the Manager notifying it about its actions.
    """

    def __init__(self, nodeID, sensors, manager):
        threading.Thread.__init__(self)
        self.nodeID = nodeID
        self.sensors = {};
        for sensor in sensors:
            self.sensors[sensor.sensorType] = sensor
        self.clusterHead = None
        self.manager = manager

    def getNodeID(self):
        return self.nodeID

    def getSensors(self):
        return self.sensors.values()

    def setClusterHead(self, clusterHead):
        self.clusterHead = clusterHead

    def getClusterHead(self):
        return self.clusterHead

    def requestAggData():
        pass

    def run(self):
        #TODO
        """
        self.name = "Name " + str(self.nodeID)
        self.reqReceived = False;
        """
        while (1):
                """
                if (self.reqReceived == True):
                        print self.name + "a primit cerere\n"
                        self.reqReceived = False;
                """
                continue
        print "Exit thread " + str(self.nodeID) + "\n"

    def getAggregatedData(self, clusters, sensor_type):
        #TODO
        #Prin functia asta managerul trimite cereri de agregare nodului
        if (clusters != None):
                print "Cluster primesc lista cu clusters\n"
                self.reqReceived = True
                self.reqClusters = clusters
                self.sensor_type = sensor_type

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

        self.parentIsManager = False
        self.parentIsCluster = False
        self.parentIsNode = False
        self.reqReceived = False

        self.responses = 0
        self.destNodes = {};
        self.destClusters = {};
        self.results = {};
        self.tuples = {};
        self.responseLock = threading.Lock()

        for sensor in sensors:
            self.sensors[sensor.sensorType] = sensor
        self.clusterNodes = None

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

        if self.destClusters:
                for cluster in self.destClusters:
                        #apeleaza functia de request pt respectivul cluster
                        cluster.requestClusterToCluster(self, self.sensor_type, False)
                        self.manager.notify_req_cluster2cluster(self, cluster, self.sensor_type)
        

    def forwardRequestToNodes(self, managerNodeId):
            if managerNodeId != -1:
                self.destNodes.remove(managerNodeId)
            for node in self.destNodes:
                #apeleaza functia de request pt node
                node.requestAggData(self, self.sensor_type)
                self.manager.notify_req_cluster2node(self, node, self.sensor_type)

    # Calculate the final results per Cluster Head
    def aggregateResults(self):
        self.aggResult = []
        properSensor = self.sensors[self.sensor_type]
        minim = properSensor.getValue;
        maxim = minim;
        for result in self.results:
                if result > maxim:
                        maxim = result
                if result < minim
                        minim = result
        for tuplu in self.tuples:
                if tuplu[0] < minim:
                        minim = tuplu[0]
                if tuplu[1] > maxim:
                        maxim = tuplu[1]
        self.value = [minim, maxim]


    def forwardResponse(self):
        if self.parentIsCluster:
                parent.receiveResponseFromCluster(self.value)
                self.manager.notify_req_cluster2cluster(self, self.parent, self.sensor_type)
        if self.parentIsManager:
                self.manager.submitResponse(self, self.value)
        if self.parentIsNode:
                self.parent.receiveResponseFromCLuser(self.value)
                self.manager.notify_req_cluster2node(self, self.parent, self.sensor_type)



    def run(self):
        self.manager.registerClusterHead(self)
        while (1):
                if self.reqReceived == True:
                        # Decide how to forward to own nodes
                        if self in self.reqClusters:
                                if self.parentIsNode == True:
                                        forwardRequestToNodes(self.parent.getNodeID)
                                if self.parentIsManager == True:
                                        forwardRequestToNodes(-1)
                        if self.parentIsCluster == True:
                                forwardRequestToNodes(-1)

                        if (self.parentIsCluster == False):
                                forwardRequestToClusters()

                        #wait for all the nodes and clusters to respond
                        leng =  len(self.destNodes) + len(self.destClusters))
                        print "Trebuie sa astept dupa " + str(leng)
                        while (self.responses < len(self.destNodes) + len(self.destClusters)):
                                continue

                        self.aggregateResults()
                        self.forwardResponse()

                        self.reqReceived = False;
                continue

        print "Exit thread " + str(self.nodeID) + "\n"

    def getAggregatedData(self, clusters, sensor_type):
            print "Cluster primesc cerere de la manager\n"
            self.reqClusters = clusters
            self.sensor_type = sensor_type
            self.parentIsManager = True
            self.reqReceived = True
