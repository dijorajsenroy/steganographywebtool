from PIL import Image
import numpy as np
import sys
import os
import hashlib
from math import ceil
from Crypto.Cipher import ChaCha20

xorkey = 255
vignere_key = 'TEST'

# Function to apply a simple XOR transform to the image
def XOR_transform_img(path, key):
    msg_img = Image.fromarray(np.asarray(Image.open(path)) ^ key)
    msg_img.save('encrypted_img.png', 'PNG')

# Function to apply Vignére Cipher to the hidden message
def Vig_Transform_txt(msg, key):
    pass

# Custom Exception in case number generation fails
class NumberGeneratorError(Exception):
    def __init__(self, message):
        self.message = message

# PseudoNumberGenerator returns pairs of values generated from ChaCha20 stream cipher.
# The class is implemented so that its object is an iterable quantity
class PseudoNumberGenerator:

    def __init__(self, x: int, y: int, key: bytes):
        """
        :param x: Max range of values for x coordinate
        :param y: Max range of values for y coordinate
        :param key: Key to use for Pseudo Random Function
        """

        if not (x and y and key):
            # checks if x, y and key are nonzero and legal
            raise NumberGeneratorError("Bad coordinates or key")

        self.ctr = bytes(1)
        # function to generate coordinates
        self.coord = self.generateCoordinates(x, y)
        # using ChaCha20 stream cipher with 8 bit nonce
        self.prng = ChaCha20.new(key=key, nonce=bytes(8))

    # Function to generate a list of all possible x & y coordinates
    def generateCoordinates(self, x: int, y: int) -> list:
        coord = list()
        # saving all (i,j) pairs in the given x and y range
        for sublist in [[(i, j) for i in range(x)] for j in range(y)]:
            for elem in sublist:
                coord.append(elem)
        return coord

    # creating an iterable quantity
    def __iter__(self):
        return self

    # to obtain the next item in the iterable
    def __next__(self) -> list:

        # Increment self.ctr (convert bytes to int, increment and revert)
        next_ctr = int.from_bytes(self.ctr, sys.byteorder) + 1
        self.ctr = next_ctr.to_bytes(ceil(next_ctr.bit_length() / 8), sys.byteorder)

        # Stop Iterattion when there are no more coordinates in the iterator
        if not self.coord:
            raise StopIteration()

        # PRNG result is used to determined index in the list of coordinates that will be used
        index = int.from_bytes(self.prng.encrypt(self.ctr), sys.byteorder) % len(self.coord)
        # returning the pixel coordinates that will be used to hide image
        return self.coord.pop(index)
