""" mesageMe.shared.lib.encryption

    This module provides a simple wrapper around PyCrypto, making the
    encryption/decryption logic available to the rest of the MessageMe system.
"""
from Crypto           import Random
from Crypto.Cipher    import XOR

#############################################################################

def generate_random_key():
    """ Generate a random 64-character key to use for encryption.
    """
    generator = Random.new()
    bytes = generator.read(32)
    return hex_encode(bytes)


def encrypt(key, plaintext):
    """ Encrypt the given plaintext using the XOR cipher and the given key.

        We return a string containing the encrypted version of the plaintext.
    """
    cipher = XOR.new(hex_decode(key))
    return hex_encode(cipher.encrypt(plaintext))


def decrypt(key, ciphertext):
    """ Decrypt the given ciphertext using the XOR cipher and the given key.

        We return a string containing the decrypted version of the ciphertext.
    """
    cipher = XOR.new(hex_decode(key))
    return cipher.decrypt(hex_decode(ciphertext))


def hex_encode(s):
    """ Encode the given string into a sequence of hex digits.

        's' can be either a plaintext string, or a sequence of bytes containing
        binary data.  We convert this to a sequence of hex digits.
    """
    result = []
    for ch in s:
        result.append("%02x" % ord(ch))
    return "".join(result)


def hex_decode(s):
    """ Decode the given sequence of hex digits back into a string.

        We decode the given sequence of hex digits back into a plaintext string
        or a sequence of bytes containing binary data.  If the given string
        isn't a valid sequence of hex digits, we return None.
    """
    result = []
    for i in range(0, len(s), 2):
        hex_digits = s[i:i+2]
        try:
            ch = chr(int(hex_digits, 16))
        except ValueError:
            return None
        result.append(ch)
    return "".join(result)

