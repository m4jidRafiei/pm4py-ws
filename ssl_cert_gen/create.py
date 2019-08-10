from OpenSSL import crypto, SSL
from socket import gethostname
from pprint import pprint
from time import gmtime, mktime
from os.path import exists, join
import socket
import os


CN = str(socket.gethostname())
CERT_FILE = "this.crt"
KEY_FILE = "this.key"

C_F = CERT_FILE
K_F = KEY_FILE

 # create a key pair
k = crypto.PKey()
k.generate_key(crypto.TYPE_RSA, 1024)

 # create a self-signed cert
cert = crypto.X509()

cert.get_subject().C = "GE"
cert.get_subject().ST = "Germany"
cert.get_subject().L = "Aachen"
cert.get_subject().O = "PADS RWTH"
cert.get_subject().OU = "PADS_RWTH"
cert.get_subject().CN = CN

cert.set_serial_number(1000)

cert.gmtime_adj_notBefore(0)

cert.gmtime_adj_notAfter(315360000)

cert.set_issuer(cert.get_subject())

cert.set_pubkey(k)

cert.sign(k, 'sha1')

open(C_F, "wb").write(
crypto.dump_certificate(crypto.FILETYPE_PEM, cert))

open(K_F, "wb").write(
crypto.dump_privatekey(crypto.FILETYPE_PEM, k))


os.system("openssl rsa -in this.key -pubout -out pubkey.key")
