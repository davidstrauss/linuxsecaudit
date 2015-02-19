import subprocess
import os
import http
import urllib
import urllib.request
import json
import ssl

class CheckException(Exception):
    pass

def show_result(name, success, details):
    success_text = '\033[92mPass\033[0m'
    if not success:
        success_text = '\033[91mFail\033[0m'
    print('[{}] {}: {}'.format(success_text, name, details))

def firewall_check():
    try:
        rules = subprocess.check_output(['iptables', '--list-rules'], universal_newlines=True)
    except subprocess.CalledProcessError as e:
        if e.returncode == 3:
            return (False, 'Insufficient access to run check.')
        raise CheckException('Listing rules failed. Return code: {}.'.format(e.returncode))

    rule_count = 0
    for line in rules.split('\n'):
        line = line.strip()
        if line == '':
            continue;
        if line == '-P INPUT ACCEPT':
            continue;
        if line == '-P FORWARD ACCEPT':
            continue;
        if line == '-P OUTPUT ACCEPT':
            continue;
        rule_count += 1;

    if rule_count == 0:
        return (False, 'No non-ACCEPT rules configured.')
    return (True, 'Found {} non-ACCEPT rule(s).'.format(rule_count))

def device_has_opal_ssc(device_path):
    try:
        status = subprocess.check_output(['hdparm', '-I', device_path], universal_newlines=True)
    except subprocess.CalledProcessError as e:
        raise CheckException('Checking for OPAL failed. Return code: {}.'.format(e.returncode))
    security_section = False
    for line in status.strip().split('\n'):
        if line.startswith('Security:'):
            security_section = True
            continue
        elif not line.startswith('\t'):  # Non-security section header.
            security_section = False
            continue
        if line.strip() == 'Security level maximum':
            return True
    return False

def encryption_check():
    try:
        with open('/proc/mounts', 'r') as mounts_file:
            mounts_data = mounts_file.read()
    except Exception as e:
        raise CheckException('Listing mounts failed. Error: {}.'.format(e))

    mounts = mounts_data.strip().split('\n')
    for mount in mounts:
        (device, path, fs, options, ignored0, ignored1) = mount.split(' ')

        if not device.startswith('/'):
            continue  # Not a normal block device.
        if device.startswith('/dev/mapper/luks-'):
            continue  # Encrypted with LUKS.
        if path.startswith('/boot'):
            continue  # Boot partitions don't need encyption.
        if path.startswith('/run/media'):
            continue  # Removable media doesn't need encryption.
        if device_has_opal_ssc(device):
            continue  # Encrypted with OPAL.
        return (False, 'Mount for path {} appears unencrypted.'.format(path))
    return (True, 'Primary mounts appear to use LUKS and/or OPAL.')

def get_human_users():
    try:
        with open('/etc/passwd', 'r') as passwd:
            users_raw = passwd.read()
    except Exception as e:
        raise CheckException('Listing users failed. Error: {}.'.format(e))
    users = {}
    for user_line in users_raw.strip().split('\n'):
        (username, password, uid, gid, uid_info, home_directory, shell) = user_line.split(':')
        if shell in ['/sbin/nologin', '/sbin/halt', '/sbin/shutdown ', '/bin/sync']:
            continue  # Non-human user.
        users[username] = home_directory
    return users

def get_gnome_lock_seconds_for_user(username, home_directory):
    if not os.path.isdir(os.path.join(home_directory, '.config')) and not os.path.isdir(os.path.join('/etc/dconf/profile/', username)):
        return 0  # No dconf for user.

    try:
        config = subprocess.check_output(['sudo', '-u{}'.format(username), 'dconf', 'read', '/org/gnome/desktop/session/idle-delay'], universal_newlines=True)
    except subprocess.CalledProcessError as e:
        raise CheckException('Checking GNOME screen lock delay failed. Return code: {}.'.format(e.returncode))

    try:
        (numfmt, numraw) = config.strip().split(' ')
    except ValueError:
        return 0
    if numfmt != 'uint32':
        raise CheckException('Unrecognized number format: {}.'.format(numfmt))
    return int(numraw)

def is_xscreensaver_custom_for_user(home_directory):
    return os.path.isfile(os.path.join(home_directory, '.xscreensaver'))

def lock_delay_check():
    users = get_human_users()
    for (username, home_directory) in users.items():
        seconds = get_gnome_lock_seconds_for_user(username, home_directory)
        if seconds > 900 or is_xscreensaver_custom_for_user(home_directory):
            return (False, 'Screen lock for user {} is unknown or too long.'.format(username))
    return (True, 'Screen lock delays appear compliant.')

def get_machine_id():
    try:
        with open('/etc/machine-id', 'r') as machine_id_file:
            machine_id = machine_id_file.read().strip()
    except Exception as e:
        raise CheckException('Retrieving machine ID failed. Error: {}.'.format(e))
    return machine_id

class HTTPSClientAuthHandler(urllib.request.HTTPSHandler):
    def https_open(self, req):
        return self.do_open(self.getConnection, req)

    def getConnection(self, host, timeout=300):
        client_context = ssl.create_default_context(ssl.Purpose.CLIENT_AUTH)
        client_context.load_cert_chain('/etc/linuxsecaudit.pem')
        return http.client.HTTPSConnection(host, context=client_context, timeout=timeout)

def submit_check(machine_id, results):
    uri = 'https://linuxsecaudit.pantheon.io/{}.json'.format(machine_id)
    body_data = json.dumps(results, sort_keys=True, indent=4).encode()
    opener = urllib.request.build_opener(HTTPSClientAuthHandler())
    request = urllib.request.Request(uri, data=body_data)
    request.add_header('Content-Type', 'application/json')
    request.get_method = lambda: 'PUT'
    response = opener.open(request)
    response.read()

def main():
    machine_id = get_machine_id()
    show_result('Machine ID', True, machine_id)

    results = {}

    firewall_result = firewall_check()
    show_result('Firewall', firewall_result[0], firewall_result[1])
    results['firewall'] = firewall_result

    encryption_result = encryption_check()
    show_result('Encryption', encryption_result[0], encryption_result[1])
    results['encryption'] = encryption_result

    lock_result = lock_delay_check()
    show_result('Screen Lock', lock_result[0], lock_result[1])
    results['screen_lock'] = lock_result

    upload_result = (True, 'Check results uploaded.')
    try:
        submit_check(machine_id, results)
    except FileNotFoundError:
        upload_result = (False, 'Certificate file not found at /etc/linuxsecaudit.pem')
    except PermissionError:
        upload_result = (False, 'Could not read certificate file at /etc/linuxsecaudit.pem')

    show_result('Upload', upload_result[0], upload_result[1])
