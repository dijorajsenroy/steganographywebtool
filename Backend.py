from PIL import Image, UnidentifiedImageError
import os
import sys
import hashlib
import secrets
from math import ceil
from Encryptions import PseudoNumberGenerator

ENCODING_SIZE = 32 # maximum of 32 bits can be encoded in each pixel

# Creating a Base Exception class for all image related exceptions
class SteganoImageException(Exception):
    def __init__(self, message):
        super().__init__(message)

# Exception in case image is too small for the data to be hidden
class SteganoImageOverflowError(SteganoImageException):
    def __init__(self):
        super().__init__("Image capacity is lower than data length to hide")


class SteganographyComputation:
    """
    1. Class to hide and recover text from an image.
    2. Pixels to use: Determined from NumberGenerator object (iterator).
    3. Seed is derivated from the password using 1M iterations of PBKDF2-HMAC-SHA256.
    """

    # parameterised constructor to initialise the Stego Object
    def __init__(self, image: str, key: str):
        """
        :param image: Stego Image to use as cover image
        :param file: The file to hide inside the cover image
        :param key: The key to use as password
        """
        # compatible with only png file to prevent compression loss.
        if not image.lower().endswith(".png"):
            print("Image is not an .png extension file. Process might fail.")

        try:
            self.image = Image.open(image)
        except UnidentifiedImageError as err:
            raise SteganoImageException(f"{image} is not an image. {err}")
        
        # Obtain dimensions of the image to give to PRNG class to generate coordinates
        image_x = self.image.size[0] 
        image_y = self.image.size[1]
        # creating a secure key using an SHA-256 algorithm
        secure_key = self.generateKey(key)
        # PRNG Class returns random coordinates to manipulate and hide data
        self.numberGenerator = iter(PseudoNumberGenerator(image_x, image_y, secure_key))

        # RGB pixels
        self.image_capacity = image_x * image_y * 3
        self.img = self.image.load()

    def generateKey(self, password=None) -> bytes:
        """
        1. Generate a random 256 bits number if `password` is None.
        2. Derive 'password' with 1M iterations of PBKDF2-HMAC-256 otherwise.
        :param password: Password to generate the final key from.
        :return: secure key in bytes format
        """
        if password:
            # if string password is provided, secure key is created accordingly
            key = hashlib.pbkdf2_hmac("sha256", bytes(password, "utf-8"), bytes(), 1000000)
        else:
            # random numbers are used if password is not provided
            key = secrets.randbits(256).to_bytes(32, sys.byteorder)

        return key

    # Gets the data to hide in bytes format 
    def get_data_from_file(self, data_file: str) -> None:
        """
        :param data_file: File to extract the data from
        :return: Data from "data_file"
        Return bytes data from "data_file"
        """
        if (os.path.isfile(data_file)):
            try:
                with open(data_file, "rb") as f:
                    # return bytes 
                    return f.read()
            except OSError as err:
                # raise error if the file was not found
                raise SteganoImageException(err)
    
    # Function to hide data inside the given cover image
    def LSB_hide(self, data_file: str, output_file: str) -> None:
        """
        :param data_file: File to hide
        :param output_file: File to write to (Stego object)
        This function is used to hide the text inside the image. Here we will be implementing
        LSB Algorithm but with only the coordinates selected by the PRNG class.
        """
        file_len = os.path.getsize(data_file)
        bits_to_hide_len = file_len * 8
        # Error: check if data is larger than image capacity
        if (bits_to_hide_len > self.image_capacity):
            raise SteganoImageOverflowError()
        # Obtain text data as bytes
        data = self.get_data_from_file(data_file)
        x, y, rgb = 0, 0, 0
        # convert the bytes data into binary format for LSB Algorithm
        tmp_bits = [bin(t)[2:] for t in data]
        # converting the binary data (msg) into 8-bit format 
        bits_to_hide = ["0" * (8 - len(t)) + t if len(t) < 8 else t for t in tmp_bits]
        # Total length is written on the ENCODING_SIZE first bits
        binary_encoded_size = "0" * (ENCODING_SIZE - len(bin(bits_to_hide_len)[2:])) + bin(bits_to_hide_len)[2:]
        # Total length is saved in the bits to be hidden array
        bits_to_hide.insert(0, binary_encoded_size)
        
        for byte in bits_to_hide:
            for bit in byte:
                if (rgb == 0):
                    try:
                        # obtain random coordinates to hide the byte of data
                        x, y = next(self.numberGenerator)
                    except StopIteration:
                        raise SteganoImageException("No more coordinates to use")
                # Obtain the value of the pixel at random coordinate (x,y)
                pixels_values = list(self.img[x, y])
                colour_value = pixels_values[rgb]
                # LSB is modified following 'bit' using bit manipulation
                colour_value = colour_value & 0xFE | int(bit)
                pixels_values[rgb] = colour_value
                # Saving the new pixel values in the output image
                self.img[x, y] = tuple(pixels_values)
                # incrementing variable to switch between r g b values
                rgb = (rgb + 1) % 3
        if not output_file:
            output_file = "outfile.png"
        try:
            self.image.save(output_file, quality=100)
        except ValueError as err:
            raise SteganoImageException(str(err))
        
    
    def LSB_recover(self, output_file: str) -> None:
        # :param output_file: File to write to
        # Recover hidden data from the image and write them to `output_file`
        ctr = 0
        size_to_recover = 0
        x = y = rgb = 0
        buffer = 0

        bytes_array = bytes()

        while (ctr < ENCODING_SIZE):
            if rgb == 0:
                try:
                    x, y = next(self.numberGenerator)
                except StopIteration:
                    raise SteganoImageException("No more coordinates to use")

            # Left bit shifft and add the bit from LSB of colour pixel
            size_to_recover = (size_to_recover << 1) + (self.img[x, y][rgb] & 1)
            rgb = (rgb + 1) % 3
            ctr += 1
        
        if size_to_recover > self.image_capacity:
            raise SteganoImageException("Bits length to recover is higher than image capacity. " 
                                      "Bad password, data is corrupted or nothing to recover.")
        ctr = 0
        while(ctr < size_to_recover):
            if rgb == 0:
                try:
                    x, y = next(self.numberGenerator)
                except StopIteration:
                    raise SteganoImageException("No more coordinates to use")

            buffer = (buffer << 1) + (self.img[x, y][rgb] & 1)
            ctr += 1
            rgb = (rgb + 1) % 3
            if ctr % 8 == 0:
                bytes_array += bytes([buffer])
                buffer = 0

        if not output_file:
            output_file = "a.out"
        try:
            with open(output_file, "wb") as f:
                f.write(bytes_array)
        except OSError as err:
            raise SteganoImageException(err)
