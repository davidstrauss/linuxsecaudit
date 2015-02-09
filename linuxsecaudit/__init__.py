import subprocess
import errno

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

def lock_delay_check():
    try:
        config = subprocess.check_output(['dconf', 'read', '/org/gnome/desktop/session/idle-delay'], universal_newlines=True)
    except subprocess.CalledProcessError as e:
        raise CheckException('Checking screen lock delay failed. Return code: {}.'.format(e.returncode))

    print(config.strip())

    (numfmt, numraw) = config.strip().split(' ')
    lock_minutes = round(int(numraw) / 60)

    if numfmt != 'uint32':
        return (False, 'Unrecognized number format: {}.'.format(numfmt))

    if lock_minutes > 15:
        return (False, 'Screen lock is set to more than 15 minutes.')

    return (True, 'Screen lock is set to {} minutes.'.format(lock_minutes))

def main():
    firewall_result = firewall_check()
    show_result('Firewall', firewall_result[0], firewall_result[1])

    encryption_result = encryption_check()
    show_result('Encryption', encryption_result[0], encryption_result[1])

    #lock_result = lock_delay_check()
    #show_result('Screen Lock', lock_result[0], lock_result[1])
