# Certificate Generation With XCA

> **COPIA DI LAVORO** — testo di **Betfair**, non del progetto.
> Fonte: *Betfair Exchange API Documentation* — <https://betfair-developer-docs.atlassian.net/wiki/spaces/1smk3cen4v3lu3yomq5qye0ni/pages/2687673>
> (spazio Confluence `1smk3cen4v3lu3yomq5qye0ni`, pagina id `2687673`; estratto il 2026-07-28
> con `scripts/fetch_betfair_docs.py`).
> **In caso di dubbio vince la pagina online**, che può essere più
> recente di questa copia: ri-esegui lo script per aggiornarla.

---

If setting up OpenSSL on your Windows machine seems challenging or unappealing, you have the option to utilize GUI wrappers that simplify the process. One such tool is XCA, an open-source wrapper for the OpenSSL toolset. XCA enables you to effortlessly generate keys, CSRs, and certificates through a user-friendly interface, storing all created items in a secure database file.

To begin, download XCA, the open-source wrapper for the OpenSSL toolset, by visiting:   
<http://sourceforge.net/projects/xca/>

## Step by Step Guide

1. Install XCA and run it.
2. Create a new Database,
3. Name it something sensible
4. Save it somewhere appropriate.

This proprietary database is useful for the XCA tool only and helps you store your keys, csrs, and certificates, the database file is not used in any part of the process with Betfair.

**Equivalent Open SSL Command - Create a public/private RSA key pair using OpenSSL**

openssl genrsa -out client-2048.key 2048

Create a public/private RSA key pair using XCA:

 

**Equivalent Open SSL Command - Create a certificate signing request (CSR).**

openssl req -new -config openssl.cnf -key client-2048.key -out client-2048.csr

* Select the Certificate signing requests tab and click **New Request**
* Select the CA template and click the **Apply Extensions** button.
* Please ensure that the Signature algorithm **SHA 512** is selected.

* Click on the **Subject** tab and enter the name etc.
* The key that you generated in the first step must be selected (if the key doesn't appear, check the "Used keys tool" box)

* Click on the **Extensions** tab
* Ensure that **Certification Authority** is selected as the type.
* Click OK.

**Equivalent Open SSL Command - Self-sign the certificate request to create a certificate**

openssl x509 -req -days 365 -in client-2048.csr -signkey client-2048.key -out client-2048.crt -extfile openssl.cnf -extensions ssl\_client 

**We will now create and sign a certificate from the first two steps:**

* Click the Certificates Tab and click New Certificate

* Click on the **Subject** tab and enter the name etc.

* The key that you generated in the first step must be selected (if the key doesn't appear, check the "Used keys tool" box)

* Click on the **Source** tab and select the parameters shown below:

* You should make sure that your CSR is selected but that “Copy extensions from the request” is unticked and that you have selected the [default] CA and pressed the “Apply extensions” button.

You can then press OK to create the self-signed certificate (see the result below)

**Next, we need to export the certificate for use in our application.**

* Export the Certificate

You should upload the .crt file exported to the [**My Security page**](https://docs.developer.betfair.com/display/1smk3cen4v3lu3yomq5qye0ni/Non-Interactive+%28bot%29+login#NonInteractive(bot)login-LinkingtheCertificatetoYourBetfairAccount) on [Betfair.com](http://Betfair.com) to allow this certificate access to your account.
