# linux-security

## Installation

    sudo pip3 install git+https://github.com/pantheon-systems/linuxsecaudit.git

## Convert PKCS#12 to PEM

    openssl pkcs12 -in individual.p12 -clcerts -nodes -out individual-with-bags.pem
    openssl x509 -in individual-with-bags.pem > /etc/linuxsecaudit.pem
    chmod 600 /etc/linuxsecaudit.pem
    chown root: /etc/linuxsecaudit.pem
    openssl rsa -in individual-with-bags.pem >> /etc/linuxsecaudit.pem
    rm individual-with-bags.pem
