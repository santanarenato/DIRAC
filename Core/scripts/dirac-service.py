#!/usr/bin/env python
########################################################################
# File :   dirac-service
# Author : Adria Casajus
########################################################################
__RCSID__ = "$Id$"

import sys
from DIRAC.ConfigurationSystem.Client.LocalConfiguration import LocalConfiguration
from DIRAC.FrameworkSystem.Client.Logger import gLogger
from DIRAC.Core.DISET.ServiceReactor import ServiceReactor
from DIRAC.Core.Utilities.DErrno import includeExtensionErrors

localCfg = LocalConfiguration()

positionalArgs = localCfg.getPositionalArguments()
if len( positionalArgs ) == 0:
  gLogger.fatal( "You must specify which server to run!" )
  sys.exit( 1 )

serverName = positionalArgs[0]
localCfg.setConfigurationForServer( serverName )
localCfg.addMandatoryEntry( "Port" )
#localCfg.addMandatoryEntry( "HandlerPath" )
localCfg.addMandatoryEntry( "/DIRAC/Setup" )
localCfg.addDefaultEntry( "/DIRAC/Security/UseServerCertificate", "yes" )
localCfg.addDefaultEntry( "LogLevel", "INFO" )
localCfg.addDefaultEntry( "LogColor", True )
resultDict = localCfg.loadUserData()
if not resultDict[ 'OK' ]:
  gLogger.initialize( serverName, "/" )
  gLogger.error( "There were errors when loading configuration", resultDict[ 'Message' ] )
  sys.exit( 1 )

includeExtensionErrors()


serverToLaunch = ServiceReactor()
result = serverToLaunch.initialize( positionalArgs )
if not result[ 'OK' ]:
  gLogger.error( result[ 'Message' ] )
  sys.exit( 1 )
result = serverToLaunch.serve()
if not result[ 'OK' ]:
  gLogger.error( result[ 'Message' ] )
  sys.exit( 1 )
