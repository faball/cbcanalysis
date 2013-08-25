import xml.etree.ElementTree as ElementTree
import httplib
import xdglib

class ETElementExtension( ElementTree._ElementInterface ) :
	"""
	Extension to the ElementTree element interface that adds methods to get children with
	a particular name, regardless of the xml namespace.
	
	Author Mark Grimes (mark.grimes@bristol.ac.uk)
	Date 28/Aug/2013
	"""
	def __init__( self, baseclass ) :
		self=baseclass
	def getchildrennamed( self, name ) :
		returnValue=[]
		for child in self.getchildren():
			splitByNamespace=child.tag.split("}")
			if len(splitByNamespace)==1 : tagname=splitByNamespace[0]
			elif len(splitByNamespace)==2 : tagname=splitByNamespace[1]
			if name==tagname :
				child.__class__=ETElementExtension
				returnValue.append( child )
		return returnValue
	def getchildnamed( self, name ) :
		""" Returns the first child with the supplied name (or None), ignoring xml namespaces. """
		result=self.getchildrennamed( name )
		if len(result)==0 : return None
		else : return result[0]

		
class Context(object) :
	"""
	Class representing XDAQ Contexts, including all of the Applications in the Context.
	
	Author Mark Grimes (mark.grimes@bristol.ac.uk)
	Date 28/Aug/2013
	"""
	def __init__( self, elementTreeNode, configFilename ) :
		self.applications = []
		self.configFilename = configFilename
		self.jobid = -1
		# Split off anything that is part of the xml namespace (in ElementTree this
		# is encapsulated in curly braces).
		splitByNamespace=elementTreeNode.tag.split("}")
		if len(splitByNamespace)==1 : tagname=splitByNamespace[0]
		elif len(splitByNamespace)==2 : tagname=splitByNamespace[1]
		else : raise Exception( "Couldn't split off the namespace in '"+elementTreeNode.tag+"'" )
		if tagname!="Context" : raise Exception( "Not a Context node" )
		# Loop over the items and record the url and port
		for item in elementTreeNode.items() :
			if item[0]=="url" : currentURL=item[1]
		if currentURL==None : raise Exception( "Couldn't get the URL for this context" )
		self.host=currentURL.split(":")[-2].split("/")[-1] # Get everything after "http://" and before the port (i.e. last ":" separator)
		self.port=currentURL.split(":")[-1]
		# Now loop over all of the children and look for Application nodes
		for child in elementTreeNode.getchildren() :
			# Split off the namespace as before
			splitByNamespace=child.tag.split("}")
			if len(splitByNamespace)==1 : tagname=splitByNamespace[0]
			elif len(splitByNamespace)==2 : tagname=splitByNamespace[1]
			else : raise Exception( "Couldn't split off the namespace in '"+child.tag+"'" )
			if tagname=="Application" :
				# Loop over the items and record the url and port
				for item in child.items() :
					if item[0]=="class" : className=item[1]
					elif item[0]=="instance" : instance=item[1]
				# Now try and create the Application object and add it to the return value
				newApplication=Application( self.host, int(self.port), className, int(instance) )
				self.applications.append( newApplication )
	def __repr__(self) :
		return "<XDAQ Context "+self.host+", "+str(self.port)+", "+self.jobid+">"
	def startProcess(self) :
		self.jobid=-1
		response=ElementTree.fromstring( xdglib.sendConfigurationStartCommand( "http://"+self.host+":"+self.port, self.configFilename ) )
		response.__class__=ETElementExtension
		self.jobid = response.getchildnamed("Body").getchildnamed("jidResponse").getchildnamed("jid").text

	def killProcess(self) :
		response=ElementTree.fromstring( xdglib.sendConfigurationKillCommand( "http://"+self.host+":"+self.port, self.jobid ) )
		response.__class__=ETElementExtension
		reply=response.getchildnamed("Body").getchildnamed("getStateResponse").getchildnamed("reply").text
		if reply=='no job killed.' : return False
		elif reply=='killed by JID' :
			self.jobid=-1
			return True

class Application(object) :
	"""
	Class representing XDAQ Applications.
	
	Author Mark Grimes (mark.grimes@bristol.ac.uk)
	Date 28/Aug/2013
	"""
	def __init__(self, host, port, className, instance ) :
		self.host=host
		self.port=port
		self.className=className
		self.instance=instance
		self.jid=-1
		self.connection=httplib.HTTPConnection( self.host+":"+str(self.port) )
		# Make sure the connection is closed, because all the other methods assume
		# it's in that state. Presumably the connection will have failed at that
		# stage anyway.
		self.connection.close()

	def __repr__(self) :
		return "<XDAQ Application "+self.host+", "+str(self.port)+", "+self.className+", "+str(self.instance)+">"

	def sendCommand( self, command ) :
		return xdglib.sendSOAPCommand( self.host, self.port, self.className, self.instance, command )

	def getState(self) :
		try :
			result=ElementTree.fromstring( self.sendCommand('ParameterQuery') )
			result.__class__=ETElementExtension
			try :
				return result.getchildnamed("Body").getchildnamed("ParameterQueryResponse").getchildnamed("properties").getchildnamed("stateName").text
			except :
				return "<unknown>"
		except : return "<uncontactable>"

	def httpRequest( self, requestType, resource, parameters={} ) :
		"""
		Send an http request to the application to the resource specified, with
		optional parameters specified as a dictionary. "requestType" is the http
		type, e.g. "GET" or "POST".
		"""
		self.connection.connect()
		# I copied this from an example on stack overflow
		headers = {"Content-type": "application/x-www-form-urlencoded","Accept": "text/plain"}
		self.connection.request( requestType, urllib.quote(resource), urllib.urlencode(parameters), headers )
		response = self.connection.getresponse()
		self.connection.close()
		return response


class Program(object) :
	"""
	Class to control all XDAQ Contexts and Applications.
	
	Author Mark Grimes (mark.grimes@bristol.ac.uk)
	Date 29/Aug/2013
	"""
	def __init__( self, xdaqConfigFilename ) :
		self.contexts = []
		tree=ElementTree.parse( xdaqConfigFilename )
		for node in tree.getroot().getchildren() :
			try :
				newContext=Context( node, xdaqConfigFilename )
				self.contexts.append( newContext )
			except Exception as error :
				# Some of these nodes might not be Contexts, so don't print any errors for those
				if( str(error)!="Not a Context node" ) :
					print "Unable to create context for node",str(node),"because",str(error)
					
	def startAllProcesses( self ) :
		for context in self.contexts:
			context.startProcess()

	def killAllProcesses( self ) :
		for context in self.contexts:
			context.killProcess()

	def sendAllCommand( self, command ) :
		for context in self.contexts :
			for application in context.applications :
				application.sendCommand( command )

	def printAllStates( self ) :
		for context in self.contexts :
			firstApplication=True
			for application in context.applications :
				if firstApplication :
					contextString=context.host+":"+str(context.port)+" (job ID="+str(context.jobid)+")"
					firstApplication=False
				else : contextString=""
				print contextString.ljust(40)+application.className.ljust(30)+str(application.instance).rjust(4)+"   "+application.getState()

	def findAllMatchingApplications( self, className, instance=None ) :
		"""
		Returns an array of all the Applications that match the given className, and optional instance
		"""
		returnValue=[]
		for context in self.contexts :
			for application in context.applications :
				shouldAdd=False
				if application.className==className : shouldAdd=True
				if instance!=None :
					if instance!=application.instance : shouldAdd=False
				if shouldAdd : returnValue.append( application )
		return returnValue

	def sendAllMatchingApplicationsCommand( self, command, className, instance=None ) :
		matchingApps=self.findAllMatchingApplications( className, instance )
		for application in matchingApps :
			application.sendCommand( command )
