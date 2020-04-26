################################################################################
# userncenabled.py - FreeIPA plugin to allow to enable users for nextcloud 
#                    via cli
################################################################################
#
# Copyright (C) $( 2020 ) Radio Bern RaBe
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
# https://github.com/radiorabe/kanboard-tasks-from-email
#
# Authors:
#  Simon Nussbaum <smirta@gmx.net>
#
# Description:
# With this plugin a switch will be added to the ipa cli to allow users to 
# connect to nextcloud. It will set the Attribute nextcloudEnabled either to 
# TRUE or FALSE.
#
# For this to work, extending the LDAP schema is required.
#
# Installation:
# Copy file to <path to python lib>/ipaserver/plugins/
#
# Usage:
# ipa user-mod --nextcloudenabled=TRUE <username>
#

from ipaserver.plugins import user
from ipalib.parameters import Bool
from ipalib import _

user.user.takes_params = user.user.takes_params + (
    Bool('nextcloudenabled?',
        cli_name='nextcloudenabled',
        label=_('Nextcloud Share enabled?'),
        doc=_('Whether or not a nextcloud share is created for this user (default is false).'),
        default=False,
        autofill=True,
        ),
    )

user.user.default_attributes.append('nextcloudenabled')

def useradd_precallback(self, ldap, dn, entry, attrs_list,
                        *keys, **options):
    entry['objectclass'].append('nextclouduser')
    return dn

user.user_add.register_pre_callback(useradd_precallback)

def usermod_precallback(self, ldap, dn, entry, attrs_list,
                        *keys, **options):
    if 'objectclass' not in entry.keys():
        old_entry = ldap.get_entry(dn, ['objectclass'])
        entry['objectclass'] = old_entry['objectclass']
    entry['objectclass'].append('nextclouduser')        
    return dn

user.user_mod.register_pre_callback(usermod_precallback)
