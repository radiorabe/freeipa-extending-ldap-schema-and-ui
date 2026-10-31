#!/usr/bin/python3
################################################################################
# populate_group_shares.py - Automatically create owncloud shares from groups 
#                            in LDAP
################################################################################
#
# Copyright (C) $( 2019 ) Radio Bern RaBe
#                    Switzerland
#                    http://www.rabe.ch
#
# This program is free software: you can redistribute it and/or
# modify it under the terms of the GNU Affero General Public
# License as published  by the Free Software Foundation, version
# 3 of the License.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU Affero General Public License for more details.
#
# You should have received a copy of the GNU Affero General Public
# License  along with this program.
# If not, see <http://www.gnu.org/licenses/>.
#
# Please submit enhancements, bugfixes or comments via:
# https://github.com/radiorabe/roaming-homes
#
# Authors:
#  Simon Nussbaum <smirta@gmx.net>
#
# Description:
# <LONGER-DESCRIPTION>
#
# Usage:
# python populate_group_shares.py
#

import os
import ldap, ldap.sasl
import random
import requests
import string
import xmltodict
import sys
sys.path.append('/etc/populate_group_shares')
try:
    from creds import username, password
    from ldapcreds import ldapuser, ldappw
except ImportError:
    if os.path.exists('/etc/populate_group_shares'):
        print('ERROR: Make sure creds.py and ldapcreds.py exist in "/etc/populate_group_shares", are readable and contain valid credentials.')
    else:
        print('ERROR: The path "/etc/populate_group_shares" where ldap and owncloud credentials are kept, does not exist.')
    exit(1)


def decode_ldap_value(value):
    if isinstance(value, bytes):
        return value.decode('utf-8')
    return value


def main ():
    # set default values
    hostname = os.uname()[1]
    ipa_server = os.environ.get('IPA_SERVER', 'ipa-01.service.int.rabe.ch')
    nc_server = hostname
    nc_federated = False
    nc_federated_server = os.environ.get('NC_FEDERATED_SERVER', 'vm-0026.service.int.rabe.ch')
    prefix = '0_RaBe_'
    default_quota = 'default'
    sharedwith_attribute = 'uidNumber'
    sharedwith_displayname = 'uid'

# sasl.gssapi auth for the future
#    auth_tokens = ldap.sasl.gssapi()
#    conn = ldap.initialize('ldaps://'+ipa_server)
#    conn.sasl_interactive_bind_s('', auth_tokens)

    conn = ldap.initialize('ldaps://'+ipa_server)
    conn.simple_bind_s('uid='+ldapuser+',cn=users,cn=accounts,dc=int,dc=rabe,dc=ch', ldappw)

    ldap_base = 'cn=groups,cn=accounts,dc=int,dc=rabe,dc=ch'
    query = '(nextcloudEnabled=TRUE)'
    result = conn.search_s(ldap_base, ldap.SCOPE_SUBTREE, query)

    for dn,entry in result:
        groupname = decode_ldap_value(entry['cn'][0])
        groupuser = groupname
        groupuserpwlength = 20
        groupuserpw = ''.join(random.choice(string.ascii_uppercase + string.ascii_lowercase + string.digits) for _ in range(groupuserpwlength))
        sharename = groupname
        quota = default_quota

        try:
            quota = decode_ldap_value(entry['nextcloudQuota'][0])
        except Exception:
            quota = default_quota

        # create user in nextcloud
        print('\ncreating user "'+groupuser+'" for group '+groupname)
        headers = {
            'OCS-APIRequest': 'true',
        }
        params = [
            ('userid', groupuser),
            ('password', groupuserpw),
            ('quota', quota),
        ]
        auth = (
            username, password,
        )
        resp0 = requests.post('https://'+nc_server+'/ocs/v1.php/cloud/users', headers=headers, data=params, auth=auth, allow_redirects=False)

#        resp0xmlobj = xmltodict.parse(resp0.text)
#        print(str(resp0xmlobj['ocs']['meta']['message'])+' (Statuscode '+str(resp0xmlobj['ocs']['meta']['statuscode'])+')')

#        if resp0xmlobj['ocs']['meta']['statuscode'] == '102':
        if True:
            params = [
                ('key', 'password'),
                ('value', groupuserpw),
            ]
            resp01 = requests.put('https://'+nc_server+'/ocs/v1.php/cloud/users/'+groupuser, headers=headers, data=params, auth=auth, allow_redirects=False)
            print('  adjusting quota to '+quota)
            params = [
                ('key', 'quota'),
                ('value', quota),
            ]
            resp01 = requests.put('https://'+nc_server+'/ocs/v1.php/cloud/users/'+groupuser, headers=headers, data=params, auth=auth, allow_redirects=False)
#            resp01xmlobj = xmltodict.parse(resp01.text)
#            print('  '+str(resp01xmlobj['ocs']['meta']['status']))

        auth = (
            groupuser, groupuserpw,
        )

        # create group folder
        print('\n  creating folder '+prefix+sharename+' for group '+groupname+' in user '+groupuser)
        resp02 = requests.request('MKCOL', 'https://'+nc_server+'/remote.php/webdav/'+prefix+sharename, auth=auth)
        if resp02.status_code == 201:
            print('  folder created successfully')
        else:
            resp02xmlobj = xmltodict.parse(resp02.text)
            print('  '+str(resp02xmlobj['d:error']['s:message'])+' ('+str(resp02xmlobj['d:error']['s:exception'])+')')

        # group share for group folder
        print('\n  setting up sharing of folder '+prefix+sharename+' with all users of group '+groupname)
        ldap_base2 = 'cn=users,cn=accounts,dc=int,dc=rabe,dc=ch'
        query2 = '(&(nextcloudEnabled=TRUE)(objectClass=person)(memberOf=cn='+groupname+',cn=groups,cn=accounts,dc=int,dc=rabe,dc=ch))'
        result2 = conn.search_s(ldap_base2, ldap.SCOPE_SUBTREE, query2)

        auth = (
            groupuser, groupuserpw,
        )
        json_resp = requests.get('https://'+nc_server+'/ocs/v2.php/apps/files_sharing/api/v1/shares?format=json', auth=auth).json()
        respdata = json_resp['ocs']['data']
        shareslist = {}
        for d in respdata:
           shareslist[str(d['share_with']).split('@')[0]] = str(d['id'])
    
        ldapgroupmemberslist = []
        for dn,entry in result2:
            shareuserid = decode_ldap_value(entry[sharedwith_attribute][0])
            shareusername = decode_ldap_value(entry[sharedwith_displayname][0])
            ldapgroupmemberslist.append(shareuserid)

            print('  Adding share for '+shareusername)

            params = [
                    ('path', '/'+prefix+sharename),
            ]

            if nc_federated == True:
                params.extend([
                    ('shareType', '6'),
                    ('shareWith', shareuserid+'@'+nc_federated_server),
                ])
            else:
                params.extend([
                    ('shareType', '0'),
                    ('shareWith', shareuserid),
                ])

            if sharename == "sendungsmachende":
                print('    no perms due to sendungsmachende')
                params.extend([("permissions", 1)])
                
            resp03 = requests.post('https://'+nc_server+'/ocs/v2.php/apps/files_sharing/api/v1/shares', headers=headers, data=params, auth=auth)
            resp03xmlobj = xmltodict.parse(resp03.text)
            print('  '+str(resp03xmlobj['ocs']['meta']['message'])+' (Statuscode '+str(resp03xmlobj['ocs']['meta']['statuscode'])+')')
        
        todeleteshares = list(set(shareslist) - set(ldapgroupmemberslist))
        for tds in todeleteshares:
            print('  Deleting share for user '+tds)
            resp04 = requests.delete('https://'+nc_server+'/ocs/v1.php/apps/files_sharing/api/v1/shares/'+shareslist[tds], auth=auth)
            resp04xmlobj = xmltodict.parse(resp04.text)
            print('  '+str(resp04xmlobj['ocs']['meta']['status'])+' (Statuscode '+str(resp04xmlobj['ocs']['meta']['statuscode'])+')')

main ()
