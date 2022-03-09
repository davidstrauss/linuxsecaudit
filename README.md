# Linux Security Audit tool

## Installation (Fedora Silverblue 35+)

1. Install Python PIP and Wheel:

       rpm-ostree install python3-pip python3-wheel

1. Reboot:

       systemctl reboot

1. Install and enable the `linuxsecaudit` agent:

       sudo pip install --upgrade git+https://github.com/pantheon-systems/linuxsecaudit.git
       sudo systemctl start linuxsecaudit.timer
       sudo systemctl enable linuxsecaudit.timer
