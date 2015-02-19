# linux-security

## Convert PKCS#12 to PEM

    openssl pkcs12 -in individual.p12 -clcerts -nodes -out individual-with-bags.pem
    openssl rsa -in individual-with-bags.pem > individual.pem
    openssl x509 -in individual-with-bags.pem >> individual.pem
