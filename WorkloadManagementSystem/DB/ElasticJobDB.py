""" DIRAC JobDB class is a front-end to the main WMS database containing
  job definitions and status information. It is used in most of the WMS
  components

  The following methods are provided for public usage:

  getJobParameters()
  getJobParametersAndAttributes()

  setJobParameter()
"""

__RCSID__ = "$Id$"

from DIRAC import S_OK, S_ERROR, gLogger
from DIRAC.Core.Base.ElasticDB import ElasticDB as DB

#############################################################################


class ElasticJobDB(DB):

  def __init__(self):
    """ Standard Constructor
    """

    DB.__init__(self, 'jobelasticdb', 'WorkloadManagement/ElasticJobDB')

    self.log.info("==================================================")

#############################################################################
  def getJobParameters(self, jobID, paramList=None):
    """ Get Job Parameters defined for jobID.
      Returns a dictionary with the Job Parameters.
      If paramList is empty - all the parameters are returned.

    :param self: self reference
    :param int jobID: Job ID
    :param list paramList: list of parameters to be returned
    """

    self.log.debug('JobDB.getParameters: Getting Parameters for job %s' % jobID)

    resultDict = {}

    if paramList:
      paramNameList = []

      for x in paramList:
        paramNameList.append(x)

      query = {
          "query": {
              "bool": {
                  "must": [
                      {"match": {"JobID": jobID}}, {"match": {"Name": ','.join(paramNameList)}}]}},
          "_source": ["Name", "Value"]}

    else:
      query = {"query": {"match": {"JobID": jobID}}, "_source": ["Name", "Value"]}

    gLogger.debug("Getting results for ", jobID)
    result = self.query('jobelasticdb*', query)

    if not result['OK']:
      return S_ERROR(result)

    sources = result['Value']['hits']['hits']

    for source in sources:

      name = source['_source']['Name']
      value = source['_source']['Value']

      try:
        resultDict[name] = value.tostring()
      except BaseException:
        resultDict[name] = value

    return S_OK(resultDict)

############################################################################
  def getJobParametersAndAttributes(self, jobID, paramList=None):
    """ Get Job Parameters with Attributes defined for jobID.
      Returns a dictionary with the Job Parameters.
      If paramList is empty - all the parameters are returned.

    :param self: self reference
    :param int jobID: Job ID
    :param list paramList: list of parameters to be returned
    """

    self.log.debug('JobDB.getParameters: Getting Parameters for job %s' % jobID)

    jobParameters = ["JobID", "Name", "Value", "JobGroup", "Owner", "Proxy", "SubmissionTime", "RunningTime"]
    resultDict = {}

    if paramList:

      query = {
          "query": {
              "bool": {
                  "must": [
                      {"match": {"JobID": jobID}}, {"match": {"Name": ','.join(paramList)}}]}},
          "_source": jobParameters}

    else:
      query = {"query": {"match": {"JobID": jobID}}, "_source": jobParameters}

    gLogger.debug("Getting results for ", jobID)
    result = self.query('jobelasticdb*', query)

    if not result['OK']:
      return result

    sources = result['Value']['hits']['hits']
    jobParameters.remove("JobID")

    for source in sources:

      jobID = source['_source']['JobID']
      parametersDict = {}

      for parameter in jobParameters:
        parametersDict[parameter] = source['_source'][parameter]

      resultDict[jobID] = parametersDict

    return S_OK(resultDict)

#############################################################################
  def setJobParameter(
          self,
          jobID,
          key,
          value,
          jobGroup="00000000",
          owner='Unknown',
          proxy=None,
          subTime=None,
          runTime=None):
    """ Set parameters for the job JobID

    :param self: self reference
    :param int jobID: Job ID
    :param basestring key: Name
    :param keyword value: value
    :param text jobGroup: JobGroup
    :param text owner: Owner
    :param text proxy: Proxy
    :param date subTime: Submission Time
    :param date runTime: Running Time
    """

    query = {
        "query": {
            "term": {
                "JobID": jobID}},
        "script": {
            "inline": "ctx._source.Value = params.value; ctx._source.Name = params.name; ctx._source.JobGroup = params.jobGroup; ctx._source.Owner = params.owner; ctx._source.Proxy = params.proxy; ctx._source.SubmissionTime = params.subTime; ctx._source.RunningTime = params.runTime",
            "params": {
                "value": value,
                "name": key,
                "jobGroup": jobGroup,
                "owner": owner,
                "proxy": proxy,
                "subTime": subTime,
                "runTime": runTime}}}
    indexName = self.generateFullIndexName('jobelasticdb')
    result = self.exists(indexName)

    if not result:
      mapping = {
          "JobParameters": {
              "properties": {
                  "JobID": {
                      "type": "long"}, "Name": {
                      "type": "text"}, "Value": {
                      "type": "keyword"}, "JobGroup": {
                      "type": "text"}, "Owner": {
                      "type": "text"}, "Proxy": {
                      "type": "text"}, "SubmissionTime": {
                      "type": "date"}, "RunningTime": {
                      "type": "date"}}}}

      gLogger.debug("Creating index ", indexName)
      result = self.createIndex('jobelasticdb', mapping)

      if not result['OK']:
        return result

    result = self.update('jobelasticdb*', 'JobParameters', query)

    if not result['OK']:
      gLogger.error("JobDB.setJobParameter: operation failed.")
      return result

    if result['Value']['updated'] == 0:

      gLogger.debug("Updated values: ", 0)
      query = {
          "JobID": jobID,
          "Name": key,
          "Value": value,
          "JobGroup": jobGroup,
          "Owner": owner,
          "Proxy": proxy,
          "SubmissionTime": subTime,
          "RunningTime": runTime}

      gLogger.debug("Inserting values in index ", indexName)
      result = self.update(indexName, 'JobParameters', query, updateByQuery=False, id=jobID)

    if not result['OK']:
      gLogger.error("JobDB.setJobParameter: operation failed.")
      return result

    return result
