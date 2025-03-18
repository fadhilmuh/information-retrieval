import array

class StandardPostings:
    """ 
    Class dengan static methods, untuk mengubah representasi postings list
    yang awalnya adalah List of integer, berubah menjadi sequence of bytes.
    Kita menggunakan Library array di Python.

    ASUMSI: postings_list untuk sebuah term MUAT di memori!

    Silakan pelajari:
        https://docs.python.org/3/library/array.html
    """

    @staticmethod
    def encode(postings_list):
        """
        Encode postings_list menjadi stream of bytes

        Parameters
        ----------
        postings_list: List[int]
            List of docIDs (postings)

        Returns
        -------
        bytes
            bytearray yang merepresentasikan urutan integer di postings_list
        """
        # Untuk yang standard, gunakan L untuk unsigned long, karena docID
        # tidak akan negatif. Dan kita asumsikan docID yang paling besar
        # cukup ditampung di representasi 4 byte unsigned.
        return array.array('L', postings_list).tobytes()

    @staticmethod
    def decode(encoded_postings_list):
        """
        Decodes postings_list dari sebuah stream of bytes

        Parameters
        ----------
        encoded_postings_list: bytes
            bytearray merepresentasikan encoded postings list sebagai keluaran
            dari static method encode di atas.

        Returns
        -------
        List[int]
            list of docIDs yang merupakan hasil decoding dari encoded_postings_list
        """
        decoded_postings_list = array.array('L')
        decoded_postings_list.frombytes(encoded_postings_list)
        return decoded_postings_list.tolist()


class VBEPostings:
    """ 
    Berbeda dengan StandardPostings, dimana untuk suatu postings list,
    yang disimpan di disk adalah sequence of integers asli dari postings
    list tersebut apa adanya.

    Pada VBEPostings, kali ini, yang disimpan adalah gap-nya, kecuali
    posting yang pertama. Barulah setelah itu di-encode dengan Variable-Byte
    Enconding algorithm ke bytestream.

    Contoh:
    postings list [34, 67, 89, 454] akan diubah dulu menjadi gap-based,
    yaitu [34, 33, 22, 365]. Barulah setelah itu di-encode dengan algoritma
    compression Variable-Byte Encoding, dan kemudian diubah ke bytesream.

    ASUMSI: postings_list untuk sebuah term MUAT di memori!

    """

    @staticmethod
    def to_gap_based(postings_list):
        """
        Mengubah postings_list menjadi gap-based list. 
        postings_list[0] adalah posting yang pertama, postings_list[1]
        adalah posting yang kedua, dst.
        """
        gap_list = []
        prev = 0
        for posting in postings_list:
            gap_list.append(posting - prev)
            prev = posting
        return gap_list

    @staticmethod
    def encode(postings_list):
        """
        Encode postings_list menjadi stream of bytes (dengan Variable-Byte
        Encoding). JANGAN LUPA diubah dulu ke gap-based list, sebelum
        di-encode dan diubah ke bytearray.

        Parameters
        ----------
        postings_list: List[int]
            List of docIDs (postings)

        Returns
        -------
        bytes
            bytearray yang merepresentasikan urutan integer di postings_list
        """
        # Mengubah postings_list menjadi gap-based list
        gap_list = VBEPostings.to_gap_based(postings_list)

        # Meng-encode gap_list dengan Variable-Byte Encoding
        encoded_postings_list = VBEPostings.vb_encode(gap_list)

        # Mengubah encoded_postings_list menjadi bytearray
        encoded_postings_list = bytes(encoded_postings_list)

        assert VBEPostings.decode(encoded_postings_list) == postings_list, "Encoding and decoding mismatch"

        return encoded_postings_list
    
    @staticmethod
    def vb_encode(list_of_numbers):
        """ 
        Melakukan encoding (tentunya dengan compression) terhadap
        list of numbers, dengan Variable-Byte Encoding
        """
        bytestream = bytearray()
        for number in list_of_numbers:
            encoded_number = VBEPostings.vb_encode_number(number)
            bytestream.extend(encoded_number)
        return bytestream

    @staticmethod
    def vb_encode_number(number):
        """
        Encodes a number using Variable-Byte Encoding
        Lihat buku teks kita!
        """
        bytes_array = []
        while True:
            bytes_array.insert(0, number % 128) # prepend(bytes, number mod 128)
            if number < 128:
                break
            number = number // 128
        
        bytes_array[len(bytes_array) - 1] += 128
        return bytes(bytes_array)

    @staticmethod
    def decode(encoded_postings_list):
        """
        Decodes postings_list dari sebuah stream of bytes. JANGAN LUPA
        bytestream yang di-decode dari encoded_postings_list masih berupa
        gap-based list.

        Parameters
        ----------
        encoded_postings_list: bytes
            bytearray merepresentasikan encoded postings list sebagai keluaran
            dari static method encode di atas.

        Returns
        -------
        List[int]
            list of docIDs yang merupakan hasil decoding dari encoded_postings_list
        """
        # Decode encoded_postings_list
        # ke dalam list of numbers
        decoded_numbers = VBEPostings.vb_decode(encoded_postings_list)
        # Kemudian, ubah decoded_numbers menjadi postings_list
        postings_list = []
        prev = 0
        for number in decoded_numbers:
            postings_list.append(prev + number)
            prev += number
        return postings_list

    @staticmethod
    def vb_decode(encoded_bytestream):
        """
        Decoding sebuah bytestream yang sebelumnya di-encode dengan
        variable-byte encoding.
        """
        numbers = []
        n = 0
        for byte in encoded_bytestream:
            if (byte < 128):
                n = 128 * n + byte
            else:
                n = 128 * n + byte - 128
                numbers.append(n)
                n = 0
        return numbers

class Simple8bPostings:
    """
    reference: https://github.com/jwilder/encoding/blob/master/simple8b/encoding.go#L32
    """
    MAX_VALUE = (1 << 60) - 1

    # ---- Helper Functions for Packing ----
    @staticmethod
    def _can_pack(src, n, bits):
        if len(src) < n:
            return False
        if bits == 0:
            return all(v == 1 for v in src[:n])
        max_val = (1 << bits) - 1
        return all(v <= max_val for v in src[:n])

    @staticmethod
    def _pack240(src):
        # Encodes 240 ones; selector 0
        return 0

    @staticmethod
    def _pack120(src):
        # Encodes 120 ones; selector 1
        return 1 << 60

    @staticmethod
    def _pack60(src):
        # Encodes 60 values using 1 bit each; selector 2
        value = 2 << 60
        for i in range(60):
            value |= (src[i] & 1) << i
        return value

    @staticmethod
    def _pack30(src):
        # Encodes 30 values using 2 bits each; selector 3
        value = 3 << 60
        for i in range(30):
            value |= (src[i] & 0x3) << (2 * i)
        return value

    @staticmethod
    def _pack20(src):
        # Encodes 20 values using 3 bits each; selector 4
        value = 4 << 60
        for i in range(20):
            value |= (src[i] & 0x7) << (3 * i)
        return value

    @staticmethod
    def _pack15(src):
        # Encodes 15 values using 4 bits each; selector 5
        value = 5 << 60
        for i in range(15):
            value |= (src[i] & 0xF) << (4 * i)
        return value

    @staticmethod
    def _pack12(src):
        # Encodes 12 values using 5 bits each; selector 6
        value = 6 << 60
        for i in range(12):
            value |= (src[i] & 0x1F) << (5 * i)
        return value

    @staticmethod
    def _pack10(src):
        # Encodes 10 values using 6 bits each; selector 7
        value = 7 << 60
        for i in range(10):
            value |= (src[i] & 0x3F) << (6 * i)
        return value

    @staticmethod
    def _pack8(src):
        # Encodes 8 values using 7 bits each; selector 8
        value = 8 << 60
        for i in range(8):
            value |= (src[i] & 0x7F) << (7 * i)
        return value

    @staticmethod
    def _pack7(src):
        # Encodes 7 values using 8 bits each; selector 9
        value = 9 << 60
        for i in range(7):
            value |= (src[i] & 0xFF) << (8 * i)
        return value

    @staticmethod
    def _pack6(src):
        # Encodes 6 values using 10 bits each; selector 10
        value = 10 << 60
        for i in range(6):
            value |= (src[i] & 0x3FF) << (10 * i)
        return value

    @staticmethod
    def _pack5(src):
        # Encodes 5 values using 12 bits each; selector 11
        value = 11 << 60
        for i in range(5):
            value |= (src[i] & 0xFFF) << (12 * i)
        return value

    @staticmethod
    def _pack4(src):
        # Encodes 4 values using 15 bits each; selector 12
        value = 12 << 60
        for i in range(4):
            value |= (src[i] & 0x7FFF) << (15 * i)
        return value

    @staticmethod
    def _pack3(src):
        # Encodes 3 values using 20 bits each; selector 13
        value = 13 << 60
        for i in range(3):
            value |= (src[i] & 0xFFFFF) << (20 * i)
        return value

    @staticmethod
    def _pack2(src):
        # Encodes 2 values using 30 bits each; selector 14
        value = 14 << 60
        for i in range(2):
            value |= (src[i] & 0x3FFFFFFF) << (30 * i)
        return value

    @staticmethod
    def _pack1(src):
        # Encodes 1 value using 60 bits; selector 15
        value = 15 << 60
        value |= src[0] & ((1 << 60) - 1)
        return value

    # ---- Helper Functions for Unpacking ----
    @staticmethod
    def _unpack240(v):
        return [1] * 240

    @staticmethod
    def _unpack120(v):
        return [1] * 120

    @staticmethod
    def _unpack60(v):
        return [(v >> i) & 1 for i in range(60)]

    @staticmethod
    def _unpack30(v):
        return [ (v >> (2 * i)) & 0x3 for i in range(30) ]

    @staticmethod
    def _unpack20(v):
        return [ (v >> (3 * i)) & 0x7 for i in range(20) ]

    @staticmethod
    def _unpack15(v):
        return [ (v >> (4 * i)) & 0xF for i in range(15) ]

    @staticmethod
    def _unpack12(v):
        return [ (v >> (5 * i)) & 0x1F for i in range(12) ]

    @staticmethod
    def _unpack10(v):
        return [ (v >> (6 * i)) & 0x3F for i in range(10) ]

    @staticmethod
    def _unpack8(v):
        return [ (v >> (7 * i)) & 0x7F for i in range(8) ]

    @staticmethod
    def _unpack7(v):
        return [ (v >> (8 * i)) & 0xFF for i in range(7) ]

    @staticmethod
    def _unpack6(v):
        return [ (v >> (10 * i)) & 0x3FF for i in range(6) ]

    @staticmethod
    def _unpack5(v):
        return [ (v >> (12 * i)) & 0xFFF for i in range(5) ]

    @staticmethod
    def _unpack4(v):
        return [ (v >> (15 * i)) & 0x7FFF for i in range(4) ]

    @staticmethod
    def _unpack3(v):
        return [ (v >> (20 * i)) & 0xFFFFF for i in range(3) ]

    @staticmethod
    def _unpack2(v):
        return [ (v >> (30 * i)) & 0x3FFFFFFF for i in range(2) ]

    @staticmethod
    def _unpack1(v):
        return [ v & ((1 << 60) - 1) ]

    # ---- Selector Table ----
    # This table associates selector values (the 4 MSB of a 64-bit word) with:
    #  n     : the number of values encoded
    #  pack  : the corresponding pack function
    #  unpack: the corresponding unpack function
    _selector = [
        {'n': 240, 'bit': 0,  'pack': _pack240.__func__, 'unpack': _unpack240.__func__},
        {'n': 120, 'bit': 0,  'pack': _pack120.__func__, 'unpack': _unpack120.__func__},
        {'n': 60,  'bit': 1,  'pack': _pack60.__func__,  'unpack': _unpack60.__func__},
        {'n': 30,  'bit': 2,  'pack': _pack30.__func__,  'unpack': _unpack30.__func__},
        {'n': 20,  'bit': 3,  'pack': _pack20.__func__,  'unpack': _unpack20.__func__},
        {'n': 15,  'bit': 4,  'pack': _pack15.__func__,  'unpack': _unpack15.__func__},
        {'n': 12,  'bit': 5,  'pack': _pack12.__func__,  'unpack': _unpack12.__func__},
        {'n': 10,  'bit': 6,  'pack': _pack10.__func__,  'unpack': _unpack10.__func__},
        {'n': 8,   'bit': 7,  'pack': _pack8.__func__,   'unpack': _unpack8.__func__},
        {'n': 7,   'bit': 8,  'pack': _pack7.__func__,   'unpack': _unpack7.__func__},
        {'n': 6,   'bit': 10, 'pack': _pack6.__func__,   'unpack': _unpack6.__func__},
        {'n': 5,   'bit': 12, 'pack': _pack5.__func__,   'unpack': _unpack5.__func__},
        {'n': 4,   'bit': 15, 'pack': _pack4.__func__,   'unpack': _unpack4.__func__},
        {'n': 3,   'bit': 20, 'pack': _pack3.__func__,   'unpack': _unpack3.__func__},
        {'n': 2,   'bit': 30, 'pack': _pack2.__func__,   'unpack': _unpack2.__func__},
        {'n': 1,   'bit': 60, 'pack': _pack1.__func__,   'unpack': _unpack1.__func__},
    ]

    # ---- Encoding Methods ----
    @classmethod
    def _encode_one(cls, src):
        # Returns (packed_value, count) for the first block of src.
        if cls._can_pack(src, 240, 0):
            return 0, 240
        elif cls._can_pack(src, 120, 0):
            return 1 << 60, 120
        elif cls._can_pack(src, 60, 1):
            return cls._pack60(src[:60]), 60
        elif cls._can_pack(src, 30, 2):
            return cls._pack30(src[:30]), 30
        elif cls._can_pack(src, 20, 3):
            return cls._pack20(src[:20]), 20
        elif cls._can_pack(src, 15, 4):
            return cls._pack15(src[:15]), 15
        elif cls._can_pack(src, 12, 5):
            return cls._pack12(src[:12]), 12
        elif cls._can_pack(src, 10, 6):
            return cls._pack10(src[:10]), 10
        elif cls._can_pack(src, 8, 7):
            return cls._pack8(src[:8]), 8
        elif cls._can_pack(src, 7, 8):
            return cls._pack7(src[:7]), 7
        elif cls._can_pack(src, 6, 10):
            return cls._pack6(src[:6]), 6
        elif cls._can_pack(src, 5, 12):
            return cls._pack5(src[:5]), 5
        elif cls._can_pack(src, 4, 15):
            return cls._pack4(src[:4]), 4
        elif cls._can_pack(src, 3, 20):
            return cls._pack3(src[:3]), 3
        elif cls._can_pack(src, 2, 30):
            return cls._pack2(src[:2]), 2
        elif cls._can_pack(src, 1, 60):
            return cls._pack1(src[:1]), 1
        else:
            if len(src) > 0:
                raise ValueError("value out of bounds: {}".format(src))
            return 0, 0

    @classmethod
    def encode_all(cls, src):
        """Encode the entire list of integers and return a list of 64-bit packed integers."""
        i = 0
        dst = []
        while i < len(src):
            remaining = src[i:]
            if cls._can_pack(remaining, 240, 0):
                dst.append(0)
                i += 240
            elif cls._can_pack(remaining, 120, 0):
                dst.append(1 << 60)
                i += 120
            elif cls._can_pack(remaining, 60, 1):
                dst.append(cls._pack60(src[i:i+60]))
                i += 60
            elif cls._can_pack(remaining, 30, 2):
                dst.append(cls._pack30(src[i:i+30]))
                i += 30
            elif cls._can_pack(remaining, 20, 3):
                dst.append(cls._pack20(src[i:i+20]))
                i += 20
            elif cls._can_pack(remaining, 15, 4):
                dst.append(cls._pack15(src[i:i+15]))
                i += 15
            elif cls._can_pack(remaining, 12, 5):
                dst.append(cls._pack12(src[i:i+12]))
                i += 12
            elif cls._can_pack(remaining, 10, 6):
                dst.append(cls._pack10(src[i:i+10]))
                i += 10
            elif cls._can_pack(remaining, 8, 7):
                dst.append(cls._pack8(src[i:i+8]))
                i += 8
            elif cls._can_pack(remaining, 7, 8):
                dst.append(cls._pack7(src[i:i+7]))
                i += 7
            elif cls._can_pack(remaining, 6, 10):
                dst.append(cls._pack6(src[i:i+6]))
                i += 6
            elif cls._can_pack(remaining, 5, 12):
                dst.append(cls._pack5(src[i:i+5]))
                i += 5
            elif cls._can_pack(remaining, 4, 15):
                dst.append(cls._pack4(src[i:i+4]))
                i += 4
            elif cls._can_pack(remaining, 3, 20):
                dst.append(cls._pack3(src[i:i+3]))
                i += 3
            elif cls._can_pack(remaining, 2, 30):
                dst.append(cls._pack2(src[i:i+2]))
                i += 2
            elif cls._can_pack(remaining, 1, 60):
                dst.append(cls._pack1(src[i:i+1]))
                i += 1
            else:
                raise ValueError("value out of bounds")
        return dst

    # ---- Decoding Methods ----
    @classmethod
    def _decode_one(cls, packed):
        sel = packed >> 60
        if sel >= 16:
            raise ValueError("invalid selector value: {}".format(sel))
        return cls._selector[sel]['unpack'](packed)

    @classmethod
    def decode_all(cls, packed_list):
        """Decode a list of 64-bit packed integers into the original list of integers."""
        result = []
        for p in packed_list:
            sel = p >> 60
            if sel >= 16:
                raise ValueError("invalid selector value: {}".format(sel))
            result.extend(cls._selector[sel]['unpack'](p))
        return result

    @staticmethod
    def _packed_to_bytes(packed_list):
        b = bytearray()
        for p in packed_list:
            b.extend(p.to_bytes(8, 'big'))
        return bytes(b)

    @staticmethod
    def _bytes_to_packed(b):
        if len(b) % 8 != 0:
            raise ValueError("Invalid byte length")
        packed_list = []
        for i in range(0, len(b), 8):
            p = int.from_bytes(b[i:i+8], 'big')
            packed_list.append(p)
        return packed_list

    # ---- Method Utama ----
    @classmethod
    def to_gap_list(cls, list_of_postings):
        """
        Convert a list of postings to a gap-based list.
        """
        gap_list = []
        prev = 0
        for posting in list_of_postings:
            gap_list.append(posting - prev)
            prev = posting
        return gap_list
    
    @classmethod
    def to_postings_list(cls, gap_list):
        """
        Convert a gap-based list back to the original postings list.
        """
        postings_list = []
        prev = 0
        for gap in gap_list:
            prev += gap
            postings_list.append(prev)
        return postings_list

    @classmethod
    def encode(cls, values):
        """
        Encode a list of unsigned integers (each < 1<<60) into a bytes object.
        """
        gap_list = cls.to_gap_list(values)
        packed_list = cls.encode_all(gap_list)
        encoded = cls._packed_to_bytes(packed_list)

        assert cls.decode(encoded) == values, "Encoding and decoding mismatch"

        return encoded

    @classmethod
    def decode(cls, data):
        """
        Decode a bytes object (produced by encode()) back into the original list of integers.
        """
        packed_list = cls._bytes_to_packed(data)
        gap_list = cls.decode_all(packed_list)
        return cls.to_postings_list(gap_list)

import array
import bitarray as ba
from bitarray.util import int2ba

class EliasGammaPostings:
    @staticmethod
    def compress_to_gamma(numbers):
        # Convert numbers to gamma encoding
        bits = ba.bitarray()
        for n in numbers:
            assert(n > 0)
            msb_pos = n.bit_length() - 1
            
            # Add unary prefix
            for _ in range(msb_pos):
                bits.append(0)
            
            # Add binary part
            bits.extend(int2ba(n))
        return bits.tobytes()

    @staticmethod
    def gamma_to_numbers(byte_data):
        # Decode gamma encoded bytes to numbers
        bits = ba.bitarray(endian="big")
        bits.frombytes(byte_data)
        
        results = []
        position = 0
        
        while position < len(bits):
            # Count leading zeros (unary part)
            zero_count = 0
            while position < len(bits) and bits[position] == 0:
                zero_count += 1
                position += 1
                
            if position == len(bits):
                break
                
            # Decode binary part
            value = 1
            for _ in range(zero_count):
                position += 1
                value = (value << 1) | bits[position]
            
            position += 1
            results.append(value)
            
        return results

    @staticmethod
    def encode(doc_ids):
        if not doc_ids:
            return []
            
        # Create gap-based representation
        gaps = [doc_ids[0]]
        for i in range(1, len(doc_ids)):
            gaps.append(doc_ids[i] - doc_ids[i-1])
            
        encoded = EliasGammaPostings.compress_to_gamma(gaps)

        decoded =  EliasGammaPostings.decode(encoded)
        assert decoded == doc_ids, "Encoding and decoding mismatch"

        return encoded

    @staticmethod
    def decode(compressed_bytes):
        # Restore original postings from compressed bytes
        gaps = EliasGammaPostings.gamma_to_numbers(compressed_bytes)
        
        # Convert gaps back to absolute positions
        for i in range(1, len(gaps)):
            gaps[i] = gaps[i] + gaps[i-1]
            
        return gaps


if __name__ == '__main__':
    
    postings_list = [34, 67, 89, 454, 2345738]

    for Postings in [StandardPostings, VBEPostings, Simple8bPostings, EliasGammaPostings]:
        # Silakan sesuaikan jika ada perbedaan parameter pada metode encode dan decode Simple8bPostings
        print(Postings.__name__)
        encoded_postings_list = Postings.encode(postings_list)
        print("byte hasil encode: ", encoded_postings_list)
        print("ukuran encoded postings: ", len(encoded_postings_list), "bytes")
        decoded_posting_list = Postings.decode(encoded_postings_list)
        print("hasil decoding: ", decoded_posting_list)
        assert decoded_posting_list == postings_list, "hasil decoding tidak sama dengan postings original"
        print()
