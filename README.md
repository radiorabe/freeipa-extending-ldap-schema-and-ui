# Extending FreeIPA LDAP schema and UI (By xample for Owncloud/Nextcloud)
An example to extend freeipa with custom attributes which can be configured through cli or web ui by an example for Owncloud/Nextcloud.

## Introduction
We needed this to integrate Owncloud/Nextcloud into FreeIPA. We wanted to be able to manage which user have Owncloud/Nextcloud shares and to set a quota individually. The latest documentation we found was for FreeiPA 3.3, [Extending FreeIPA](https://www.freeipa.org/images/5/5b/FreeIPA33-extending-freeipa.pdf). A lot has changed since then. This example here should work on FreeIPA 4 and later.

## How it works
First you'll have to extend the LDAP schema and then add some plugins for cli and web ui. We'll demonstrate by using the example for Owncloud/Nextcloud.

### Extending the schema
We used the object classes and attributes already defined for Nextcloud ([nextcloud.schema](https://github.com/nextcloud/univention-app/blob/master/nextcloud.schema)). We slightly adjusted them to fit our needs.
```
# Adjustments by $( 2020 ) Radio Bern RaBe, Simon Nussbaum <smirta@gmx.net>
# - Removed MUST ( cn ), because with this it did not work. But is not
#   a necessary condition for our case.
# - stripped objectClass 'nextcloudGroup', because it's not needed here.

# Attribute Types
#-----------------
dn: cn=schema
changetype: modify
add: attributeTypes
attributeTypes: ( 1.3.6.1.4.1.49213.1.1.1 NAME 'nextcloudEnabled'
        DESC 'whether user or group should be available in Nextcloud'
        EQUALITY caseIgnoreMatch
        SUBSTR caseIgnoreSubstringsMatch
        SYNTAX 1.3.6.1.4.1.1466.115.121.1.15 SINGLE-VALUE)
attributeTypes: ( 1.3.6.1.4.1.49213.1.1.2 NAME 'nextcloudQuota'
        DESC 'defines how much disk space is available for the user'
        EQUALITY caseIgnoreMatch
        SUBSTR caseIgnoreSubstringsMatch
        SYNTAX 1.3.6.1.4.1.1466.115.121.1.15 SINGLE-VALUE)
-
add: objectclasses
objectClasses: ( 1.3.6.1.4.1.49213.1.2.1 NAME 'nextcloudUser'
        DESC 'A Nextcloud user'
        SUP top AUXILIARY
        MAY ( nextcloudEnabled $ nextcloudQuota )
        )

```
[nextcloud.ldif](src/nextcloud.ldif)


___important note: the ldif file has to end with a blank line___



### cli plugin
There are slight differences to the guide [Extending the FreeIPA Server](https://www.freeipa.org/images/5/5b/FreeIPA33-extending-freeipa.pdf), but it still works close enough this way. The main differences are the path to the plugins that has changed. The import path for 'user' has to be adjusted and all plugins have to be copied to ```<path to python lib>/ipaserver/plugins``` (e.g. ```/usr/lib/python2.7/site-packages/ipaserver/plugins```) instead of ```<path to python lib>/ipalib/plugins``` (e.g. ```/usr/lib/python2.7/site-packages/ipalib/plugins```).

Plugin to enable user for having a nextcloud share: [userncenabled.py](src/userncenabled.py)

Plugin for setting a quota for a user: [userncquota.py](src/userncquota.py)

### web ui plugin
To have input fields, radio buttons, check boxes in the web ui we have to add plugins for this as well. The plugins are written in java script.


Plugin to enable user for having a nextcloud share: [userncenabled.js](src/userncenabled.js)                       

Plugin for setting a quota for a user: [userncquota.js](src/userncquota.js)

## Installation
Assuming having cloned this repo
```
git clone git@github.com:radiorabe/extending-freeipa.git
cd extending-freeipa/src
``` 
### LDAP schema extension
Extend the schema with the following command on the or a FreeIPA server:
```
ldapadd -H ldap://$HOSTNAME -D 'cn=Directory Manager' -W -f nextcloud.ldif
```


Check if schema was extended:
```
ldapsearch -H ldap://$HOSTNAME -D 'cn=Directory Manager' -W -x -s base -b 'cn=schema' objectclasses | grep -i nextcloud
ldapsearch -H ldap://$HOSTNAME -D 'cn=Directory Manager' -W -x -s base -b 'cn=schema' attributetypes | grep -i nextcloud
```


Add the new object class to the ipa user object class:
```
ipa config-mod --addattr=ipaUserObjectClasses=nextcloudUser
```

### cli plugins
Copy the plugin files to ```<path to python libs>/ipaserver/plugins``` and restart apache.
```
cp usernc* /usr/lib/python2.7/site-packages/ipaserver/plugins/
cd /usr/lib/python2.7/site-packages/ipaserver/plugins/
python -m compileall usernc* && python -O -m compileall usernc*
apachectl graceful 
```

### web ui plugins
Copy the plugin files to a subfolder with the same name as the file in ```<freeipa ui root>/js/plugins/``` and restart apache.
```
mkdir /usr/share/ipa/ui/js/plugins/{userncenabled,userncquota}
cp userncenabled.js /usr/share/ipa/ui/js/plugins/userncenabled/
cp userncquota.js /usr/share/ipa/ui/js/plugins/userncquota/
apachectl graceful 
```
