/*
 *###############################################################################
 * userncquota.js - FreeIPA plugin to set a quota for nextcloud users via web ui 
 *###############################################################################
 *
 * Copyright (C) $( 2020 ) Radio Bern RaBe
 *                    Switzerland
 *                    http://www.rabe.ch
 *
 * This program is free software: you can redistribute it and/or
 * modify it under the terms of the GNU Affero General Public
 * License as published  by the Free Software Foundation, version
 * 3 of the License.
 *
 * This program is distributed in the hope that it will be useful,
 * but WITHOUT ANY WARRANTY; without even the implied warranty of
 * MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
 * GNU Affero General Public License for more details.
 *
 * You should have received a copy of the GNU Affero General Public
 * License  along with this program.
 * If not, see <http://www.gnu.org/licenses/>.
 *
 * Please submit enhancements, bugfixes or comments via:
 * https://github.com/radiorabe/kanboard-tasks-from-email
 *
 * Authors:
 *  Simon Nussbaum <smirta@gmx.net>
 *
 * Description:
 * With this plugin an input box will be added to the user settings in the web 
 * ui to set a quota for users connecting to nextcloud. It will set the 
 * Attribute nextcloudQuota. Allowed values are 'default' or an integer with 
 * 'MB', 'GB' etc.
 *
 * For this to work, extending the LDAP schema is required.
 *
 * Installation:
 * Copy file to /usr/share/ipa/ui/js/plugins/userncquota/userncquota.js
 *
 */
define([
		'freeipa/phases',
		'freeipa/user'],
		function(phases, user_mod) {
			
// helper function
function get_item(array, attr, value) {
	for (var i=0,l=array.length; i<l; i++) {
		if (array[i][attr] === value) 
			return array[i];
		}
		return null;
}

var nc_quota_plugin = {};

// adds nextcloud quota field into user account facet
nc_quota_plugin.add_nc_quota_pre_op = function() {
        var facet = get_item(user_mod.entity_spec.facets, '$type', 'details');
        var section = get_item(facet.sections, 'name', 'account');
        section.fields.push({
                                name: 'nextcloudquota',
                                label: 'Nextcloud Share Quota',
                                flags: ['w_if_no_aci']
        });
        return true;
};

phases.on('customization', nc_quota_plugin.add_nc_quota_pre_op);

return nc_quota_plugin;
});
