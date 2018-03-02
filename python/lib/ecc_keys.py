#!/usr/bin/env python

from OpenSSL import SSL

from cryptography.hazmat.primitives.asymmetric import ec
from cryptography.hazmat.backends.openssl.backend import backend
from cryptography.hazmat.primitives import serialization
from cryptography import x509
from cryptography.x509.oid import NameOID
from cryptography.hazmat.primitives import hashes
import os
import hashlib


# Generate Private Key
def generateKey(keyName, path=None):
	private_key = ec.generate_private_key(ec.SECP384R1(), backend)

	# Save as PEM files
	if path is not None:
		with open(path+'/'+keyName, "wb") as f:
		    f.write(privateKeyPEM(private_key))
		
		with open(path+'/'+keyName+".pub", "wb") as f:
		    f.write(publicKeyPEM(private_key.public_key()))
	
	return private_key

def deleteKey(keyName, path):
	try:
		os.remove(path+'/'+keyName)
		os.remove(path+'/'+keyName+".pub")
	except Exception as e:
		pass

def keyExists(keyName, path):
	return os.path.isfile(path+'/'+keyName) 

def privateKeyPEM(private_key):
	return private_key.private_bytes(
		encoding=serialization.Encoding.PEM,
		format=serialization.PrivateFormat.TraditionalOpenSSL,
		encryption_algorithm=serialization.NoEncryption())

def publicKeyPEM(public_key):
	return public_key.public_bytes(
		encoding=serialization.Encoding.PEM,
		format=serialization.PublicFormat.SubjectPublicKeyInfo)

def generateCSR(key, csrName, path=None):
	csr = x509.CertificateSigningRequestBuilder().subject_name(x509.Name([
	    x509.NameAttribute(NameOID.COUNTRY_NAME, u"US"),
	    x509.NameAttribute(NameOID.STATE_OR_PROVINCE_NAME, u"CO"),
	    x509.NameAttribute(NameOID.LOCALITY_NAME, u"Louisville"),
	    x509.NameAttribute(NameOID.ORGANIZATION_NAME, u"CableLabs"),
	    x509.NameAttribute(NameOID.COMMON_NAME, u"medicalDevice"),
	])
	# Sign the CSR with our private key.
	).sign(key, hashes.SHA256(), backend)

	if path is not None:
		# Write our CSR out to disk.
		with open(path+'/'+csrName+".pem", "wb") as f:
		    f.write(csr.public_bytes(serialization.Encoding.PEM))
	return csr

# Generate a hash of the public key for use as deviceID
def publicKeyHash(public_key):
	return hashlib.sha256(publicKeyPEM(public_key)).hexdigest()

def loadPrivateKey(name, path):
	with open(path+'/'+name, "rb") as key_file:
	    key = serialization.load_pem_private_key(
	        key_file.read(),
	        password=None,
	        backend=backend
	    )
	    return key

def loadPublicKey(name, path):
	with open(path+'/'+name+'.pub', "rb") as key_file:
	    key = serialization.load_pem_public_key(
	        key_file.read(),
	        backend=backend
	    )
	    return key

if __name__ == '__main__':

	keyPath = '../../ssh'
	if not os.path.exists(keyPath):
	    os.makedirs(keyPath)

	# Generate key pair
	private_key = generateKey("wifiKey", keyPath)
	public_key = private_key.public_key()

	# Generate a CSR
	csr = generateCSR(private_key, "wifiCSR", keyPath)

	# Read keys back in from PEM files
	testKey = loadPrivateKey("wifiKey", keyPath)
	testKeyPub = loadPublicKey("wifiKey", keyPath)

	deviceID = hashlib.sha256(publicKeyPEM(public_key)).hexdigest()

	print deviceID
