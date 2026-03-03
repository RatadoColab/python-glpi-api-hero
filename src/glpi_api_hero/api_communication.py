# SPDX-License-Identifier: GPL-3.0-or-later
# Copyright (C) 2026 Andre Proto
#
# This file is part of the GlpiApiHero project.
# It is licensed under the GNU General Public License v3.0 or (at your option)
# any later version. You should have received a copy of the GNU General Public
# License along with this file. If not, see <https://www.gnu.org/licenses/>.
#
# Description: Class to extend methods for API communication.
# Contact: andre.proto@ibge.gov.br

import glpi_api
from .exceptions import ApiConnectionError


class ApiCommunication:
    """Class for API communication.
    """
    ERROR = ''
    glpi = None
    logged_user = None
    
    glpi_connection = { url: '', apptoken: '', usertoken: '', user: None, passwd: None }
    glpi_environment = { profiles_id: None, entities_id: None, is_recursive: True }
    last_glpi_environment = { profiles_id: -1, entities_id: -1, is_recursive: None }
    
    @staticmethod
    def _resetGlpiEnv() -> None:
        ApiCommunication.last_glpi_environment['entities_id'] = -1;
        ApiCommunication.last_glpi_environment['profiles_id'] = -1;
        ApiCommunication.last_glpi_environment['is_recursive'] = None;
        ApiCommunication.glpi_environment['profiles_id'] = None;
        ApiCommunication.glpi_environment['entities_id'] = None;
        ApiCommunication.glpi_environment['is_recursive'] = True;

    @staticmethod
    def _setGlpiEnv() -> None:
        if (ApiCommunication.glpi_environment['profiles_id'] is not None) and (ApiCommunication.glpi_environment['profiles_id'] != ApiCommunication.last_glpi_environment['profiles_id']): 
            ApiCommunication.glpi.set_active_profile(ApiCommunication.glpi_environment['profiles_id'])
            ApiCommunication.last_glpi_environment['profiles_id'] = ApiCommunication.glpi_environment['profiles_id']
        if (ApiCommunication.glpi_environment['entities_id'] is not None) and (
        (ApiCommunication.glpi_environment['entities_id'] != ApiCommunication.last_glpi_environment['entities_id'] or ApiCommunication.glpi_environment['is_recursive'] != ApiCommunication.last_glpi_environment['is_recursive'])): 
            ApiCommunication.glpi.set_active_entities(ApiCommunication.glpi_environment['entities_id'], ApiCommunication.glpi_environment['is_recursive'])
            ApiCommunication.last_glpi_environment['entities_id'] = ApiCommunication.glpi_environment['entities_id']
            ApiCommunication.last_glpi_environment['is_recursive'] = ApiCommunication.glpi_environment['is_recursive']
    
    @staticmethod
    def getLoggedUser() -> dict:
        """Get information about current logged user

        Raises:
            ApiConnectionError: When the connection with GLPI server has failed

        Returns:
            dict: User data
        """
        ApiCommunication.initSession()
        if ApiCommunication.logged_user is None:
            try:
                session = ApiCommunication.glpi.get_full_session()
                ApiCommunication.logged_user = ApiCommunication.get_item('User', session['glpiID'])
            except glpi_api.GLPIError as err:
                raise ApiConnectionError(str(err))
        return ApiCommunication.logged_user
    
    @staticmethod
    def getConn() -> Any:
        """Return the original GLPI object that connects and operates GLPI methods.

        Returns:
            Any: The GLPI object or None
        """
        return ApiCommunication.glpi
    
    @staticmethod
    def initSession(verify_certs: bool = False) -> bool:
        """Initialize connection with GLPI API. Use setConnectionParameters before call this method.

        Args:
            verify_certs (bool, optional): Verify certificate on connection. Defaults to False.

        Raises:
            ApiConnectionError: When the connection with GLPI server has failed

        Returns:
            bool: True if connection was completed
        """
        
        if ApiCommunication.glpi is None:
            ApiCommunication.logged_user = None
            try:
                if ApiCommunication.glpi_connection['user'] is None:
                    ApiCommunication.glpi = glpi_api.GLPI(ApiCommunication.glpi_connection['url'], ApiCommunication.glpi_connection['apptoken'], ApiCommunication.glpi_connection['usertoken'], verify_certs = verify_certs)
                else:
                    ApiCommunication.glpi = glpi_api.GLPI(ApiCommunication.glpi_connection['url'], ApiCommunication.glpi_connection['apptoken'], auth=(ApiCommunication.glpi_connection['user'], ApiCommunication.glpi_connection['passwd']), verify_certs = verify_certs)
            except glpi_api.GLPIError as err:
                raise ApiConnectionError(str(err))
        return True
        
    @staticmethod
    def killSession():
        """Kill the current session with GLPI API Server.

        Raises:
            ApiConnectionError: When the connection with GLPI server has failed
        """
        ApiCommunication._resetGlpiEnv()
        ApiCommunication.logged_user = None
        if ApiCommunication.glpi is not None:
            try:
                ApiCommunication.glpi.kill_session()
                ApiCommunication.glpi = None
            except glpi_api.GLPIError as err:
                ApiCommunication.glpi = None
                raise ApiConnectionError(str(err))
            
    @staticmethod
    def setConnectionParameters(url: str, apptoken: str, usertooken: str = None, user: str = None, passwd: str = None) -> None:
        """Set the connection parameters before establish GLPI API server connection.
        
           Warninig: This method does not connect automatically with GLPI API Server. Call `initSession` after this method to do this. 

        Args:
            url (str): URL of GLPI API server (e.g. https://your.server/apirest.php) 
            apptoken (str): APP Token
            usertooken (str, optional): User Token. Defaults to None.
            user (str, optional): Username. When defined, it will be used instead usertoken. Defaults to None.
            passwd (str, optional): Password of the username filled in the last parameter. Defaults to None.
        """
        ApiComunication.glpi_connection['url'] = url;
        ApiComunication.glpi_connection['apptoken'] = apptoken;
        ApiComunication.glpi_connection['usertooken'] = usertooken;
        ApiComunication.glpi_connection['user'] = user;
        ApiComunication.glpi_connection['passwd'] = passwd;   
        
    @staticmethod
    def setProfileEntity(profiles_id: int, entities_id: int, is_recursive: bool = True) -> bool:
        """Set profile and entity of current session

        Args:
            profiles_id (int): The profile ID
            entities_id (int): The entity ID
            is_recursive (bool, optional): Active/Deactive recursive entity. Defaults to True.

        Raises:
            ApiConnectionError: When the connection with GLPI server has failed
            
        Returns:
            bool: True if the operation is done successfully, False otherwise.
        """
        ApiCommunication.glpi_environment['profiles_id'] = profiles_id;
        ApiCommunication.glpi_environment['entities_id'] = entities_id;
        ApiCommunication.glpi_environment['is_recursive'] = is_recursive;
        ApiCommunication.initSession()
        if ApiCommunication.glpi:
            ApiCommunication._setGlpiEnv()
            return True
        raise ApiConnectionError(f'Unable to connect on GLPI API server')
        