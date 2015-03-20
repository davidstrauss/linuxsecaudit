# Linux Security Audit tool

## Installation (Fedora 21+)

1. Place your individual certificate at `/etc/linuxsecaudit.pem` (see below if it's PKCS#12 format).
1. Install and enable the `linuxsecaudit` agent:

        sudo pip3 install --upgrade git+https://github.com/pantheon-systems/linuxsecaudit.git
        sudo systemctl start linuxsecaudit.timer
        sudo systemctl enable linuxsecaudit.timer

## Installation (Fedora 20)

1. Place your individual certificate at `/etc/linuxsecaudit.pem` (see below if it's PKCS#12 format).
1. Install and enable the `linuxsecaudit` agent:

        sudo yum install -y python3-pip hdparm
        sudo pip-python3 install --upgrade git+https://github.com/pantheon-systems/linuxsecaudit.git
        sudo systemctl start linuxsecaudit.timer
        sudo systemctl enable linuxsecaudit.timer

## Converting PKCS#12 to PEM

1. Export your browser certificate to `individual.p12`.
2. Convert the certificate to PEM format and put it where the audit tool can find it:
    openssl pkcs12 -in individual.p12 -clcerts -nodes -out individual-with-bags.pem
    openssl x509 -in individual-with-bags.pem > linuxsecaudit.pem
    openssl rsa -in individual-with-bags.pem >> linuxsecaudit.pem
    rm individual-with-bags.pem
    chmod 600 linuxsecaudit.pem
    sudo chown root: linuxsecaudit.pem
    sudo mv linuxsecaudit.pem /etc/linuxsecaudit.pem
