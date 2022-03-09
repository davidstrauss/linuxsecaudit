# Linux Security Audit tool

## Installation (Fedora 35+)

1. Install and enable the `linuxsecaudit` agent:

        sudo pip install --upgrade git+https://github.com/pantheon-systems/linuxsecaudit.git
        sudo systemctl start linuxsecaudit.timer
        sudo systemctl enable linuxsecaudit.timer
