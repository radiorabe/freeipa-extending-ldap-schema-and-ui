"""userncquota.py - FreeIPA plugin to set a quota for nextcloud users.

Copyright (C) $( 2020 ) Radio Bern RaBe
                        Switzerland
                        http://www.rabe.ch

This program is free software: you can redistribute it and/or
modify it under the terms of the GNU Affero General Public
License as published  by the Free Software Foundation, version
3 of the License.

This program is distributed in the hope that it will be useful,
but WITHOUT ANY WARRANTY; without even the implied warranty of
MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
GNU Affero General Public License for more details.

You should have received a copy of the GNU Affero General Public
License  along with this program.
If not, see <http://www.gnu.org/licenses/>.

Please submit enhancements, bugfixes or comments via:
https://github.com/radiorabe/kanboard-tasks-from-email

Authors:
 Simon Nussbaum <smirta@gmx.net>

Description:
With this plugin a switch will be added to the ipa cli to set a quota for
users connecting to nextcloud. It will set the Attribute nextcloudQuota.
Allowed values are 'default' or an integer with 'MB', 'GB' etc.

For this to work, extending the LDAP schema is required.

Installation:
Copy file to <path to python lib>/ipaserver/plugins/

Usage:
ipa user-mod --nextcloudquota="100 MB" <username>
"""

from ipaserver.plugins import user
from ipalib.parameters import Str
from ipalib.text import _

user.user.takes_params = user.user.takes_params + (
    Str(
        "nextcloudquota?",
        cli_name="nextcloudquota",
        label=_("Nextcloud Share Quota"),
        doc=_(
            "Defines Nextcloud share quota in Bytes. "
            'Allowed values are "none",'
            '"default", e.g. "1024 MB" (default is "default").'
        ),
        default="default",
        autofill=True,
        pattern="^(default|none|[0-9]+ [MGT]B)$",
        pattern_errmsg="".join(
            'may only be "none", '
            '"default" or a number of mega-, giga- or terabytes (e.g. 1024 MB)'
        ),
    ),
)

user.user.default_attributes.append("nextcloudquota")


# pylint: disable-msg=unused-argument,invalid-name,line-too-long
def useradd_precallback(self, ldap, dn, entry, attrs_list, *keys, **options):
    """Callback for `register_pre_callback`.

    See <https://github.com/freeipa/freeipa/blob/master/doc/guide/guide.org#extending-existing-object> for details.
    """
    entry["objectclass"].append("nextclouduser")
    return dn


user.user_add.register_pre_callback(useradd_precallback)


# pylint: disable-msg=unused-argument,invalid-name,line-too-long
def usermod_precallback(self, ldap, dn, entry, attrs_list, *keys, **options):
    """Callback for `register_pre_callback`.

    See <https://github.com/freeipa/freeipa/blob/master/doc/guide/guide.org#extending-existing-object> for details.
    """
    if "objectclass" not in entry.keys():
        old_entry = ldap.get_entry(dn, ["objectclass"])
        entry["objectclass"] = old_entry["objectclass"]
    entry["objectclass"].append("nextclouduser")
    return dn


user.user_mod.register_pre_callback(usermod_precallback)
