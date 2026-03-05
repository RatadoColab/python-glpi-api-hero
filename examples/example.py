import glpi_api_hero.api_comunication


user = 'sp-andre.proto'
passwd = 'sdsadasdasdad'
url = 'https://betacentral.ibge.gov.br/apírest.php'
apptoken = 'DSFdsfADSFADSgADFGFDSGDASFG'

ApiCommunication.setConnectionParameters(url = url, apptolen=apptoken, user=user, passwd=passwd );
ApiCommunication.initSession();

ApiCommunication.setProfileEntity(profiles_id=4, entities_id=111, is_recursive=True);

