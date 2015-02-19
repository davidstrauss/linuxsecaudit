# linux-security

## Installation

    sudo pip3 install git+https://github.com/pantheon-systems/linuxsecaudit.git

## Convert PKCS#12 to PEM

    openssl pkcs12 -in individual.p12 -clcerts -nodes -out individual-with-bags.pem
    openssl x509 -in individual-with-bags.pem > linuxsecaudit.pem
    openssl rsa -in individual-with-bags.pem >> linuxsecaudit.pem
    rm individual-with-bags.pem
    sudo chmod 600 linuxsecaudit.pem
    sudo chown root: linuxsecaudit.pem
    sudo mv linuxsecaudit.pem /etc/linuxsecaudit.pem
