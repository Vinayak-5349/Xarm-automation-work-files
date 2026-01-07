"""
barcode_utils.py
-----------------
This file contains all utility classes for barcode generation,
image conversion, and serial communication.

Imported into app.py for clean separation of logic.
"""

import treepoem
from PIL import Image
import serial
import logging


# === Barcode Generator ===
class BarcodeGenerator:
    """
    Class to generate different types of barcodes
    such as Code128, GS1, UPC-A, and EAN-8.
    """

    def __init__(self, barcode_type: str, data: str):
        # barcode_type: type of barcode (e.g., "code128", "upc-a")
        # data: the text/number that will be encoded into the barcode
        self.barcode_type = barcode_type.lower()
        self.data = data

    def generate(self) -> Image.Image:
        """
        Main function to generate a barcode image
        depending on the barcode type chosen.
        """
        if self.barcode_type == "code128":
            return self.generate_code128_barcode(self.data)
        elif self.barcode_type == "gs1-databar-stacked-omni":
            return self.generate_GS1_DataBar_StackedOmni(self.data)
        elif self.barcode_type == "upc-a":
            bits = self.generate_upca(self.data)
            return ImageConverter.bits_to_image(bits)
        elif self.barcode_type == "ean-8":
            bits = self.generate_ean8(self.data)
            return ImageConverter.bits_to_image(bits)
        else:
            raise ValueError(f"Unsupported barcode type: {self.barcode_type}")

    def generate_GS1_DataBar_StackedOmni(self, data: str) -> Image.Image:
        """
        Generate GS1 DataBar Stacked Omni barcode.
        """
        try:
            image = treepoem.generate_barcode(
                barcode_type="databarstackedomni",
                data=f"01{data}"  # GS1 format requires '01' prefix
            )
            return image.convert("1")
        except Exception as e:
            raise ValueError(f"Barcode generation failed: {e}")

    def generate_ean8(self, ean: str) -> str:
        """
        Generate EAN-8 barcode (bit string).
        EAN-8 must be an 8-digit number.
        """
        if len(ean) != 8 or not ean.isdigit():
            raise ValueError("EAN-8 must be an 8-digit number")

        L_CODES = {str(i): format(i, '07b') for i in range(10)}
        R_CODES = {str(i): format(9 - i, '07b') for i in range(10)}

        bits = "101"
        for digit in ean[:4]:
            bits += L_CODES[digit]
        bits += "01010"
        for digit in ean[4:]:
            bits += R_CODES[digit]
        bits += "101"
        return bits

    def generate_upca(self, upca: str) -> str:
        """
        Generate UPC-A barcode (bit string).
        UPC-A must be a 12-digit number.
        """
        if len(upca) != 12 or not upca.isdigit():
            raise ValueError("UPC-A must be a 12-digit number")

        L_CODES = {str(i): format(i, '07b') for i in range(10)}
        R_CODES = {str(i): format(9 - i, '07b') for i in range(10)}

        bits = "101"
        for digit in upca[:6]:
            bits += L_CODES[digit]
        bits += "01010"
        for digit in upca[6:]:
            bits += R_CODES[digit]
        bits += "101"
        return bits

    def generate_code128_barcode(self, data: str, target_width=128, target_height=128) -> Image.Image:
        """
        Generate Code128 barcode using Treepoem.
        Resizes to fit 128x128 display.
        """
        try:
            image = treepoem.generate_barcode(
                barcode_type="code128",
                data=data
            ).convert("1")
            image = image.resize((target_width, target_height), Image.LANCZOS)
            return image
        except Exception as e:
            raise ValueError(f"Code 128 barcode generation failed: {e}")


# === Image Converter ===
class ImageConverter:
    """
    Utility functions to convert barcode bit strings into images
    and to convert images into byte arrays for serial communication.
    """

    @staticmethod
    def bits_to_image(bits: str, scale: int = 1, bar_height: int = 80) -> Image.Image:
        """
        Convert a binary string (bits) into a barcode image.
        """
        img = Image.new('1', (len(bits) * scale, bar_height), 1)
        for i, bit in enumerate(bits):
            if bit == '1':
                for x in range(scale):
                    for y in range(bar_height):
                        img.putpixel((i * scale + x, y), 0)

        # Resize and center to 128x128 display
        display_width, display_height = 128, 128
        final_img = Image.new('1', (display_width, display_height), 1)
        offset_x = (display_width - img.width) // 2
        offset_y = (display_height - bar_height) // 2
        final_img.paste(img, (offset_x, offset_y))
        return final_img

    @staticmethod
    def image_to_bytearray(image: Image.Image) -> bytearray:
        """
        Convert image pixels into a bytearray for serial transfer.
        """
        pixel_bytes = bytearray()
        for y in range(128):
            for byte in range(0, 128, 8):
                bits = 0
                for bit in range(8):
                    pixel = image.getpixel((byte + bit, y))
                    if pixel != 0:
                        bits |= (1 << (7 - bit))
                pixel_bytes.append(bits)
        return pixel_bytes


# === Serial Communication ===
class SerialCommunication:
    """
    Utility class for sending data to hardware devices
    via serial communication.
    """

    @staticmethod
    def send_to_serial(byte_data: bytearray, port, baud=115200, timeout=2):
        """
        Send the generated barcode as a bytearray to the serial port.
        """
        hex_code = ','.join(f'0x{b:02X}' for b in byte_data)
        data = f"barcode_image = bytearray([{hex_code}])\n__DONE__\n"
        try:
            with serial.Serial(port, baud, timeout=timeout) as ser:
                ser.write(data.encode('ascii'))
                logging.info(f"Barcode data sent successfully to {port}")
        except Exception as e:
            raise RuntimeError(f"Serial error on {port}: {e}")
