import heapq
import os
import hashlib


class HuffmanNode:
    def __init__(self, char, freq):
        self.char = char
        self.freq = freq
        self.left = None
        self.right = None

    def __lt__(self, other):
        return self.freq < other.freq


class HuffmanCoding:
    def __init__(self):
        self.heap = []
        self.codes = {}
        self.reverse_mapping = {}

    # ------------------------------------------------------------------ #
    #  Internal helpers                                                    #
    # ------------------------------------------------------------------ #

    def _reset_state(self):
        """Clear all instance state so the object can be reused safely."""
        self.heap = []
        self.codes = {}
        self.reverse_mapping = {}

    def make_frequency_dict(self, text_bytes):
        frequency = {}
        for character in text_bytes:
            frequency[character] = frequency.get(character, 0) + 1
        return frequency

    def make_heap(self, frequency):
        for key in frequency:
            node = HuffmanNode(key, frequency[key])
            heapq.heappush(self.heap, node)

    def merge_nodes(self):
        while len(self.heap) > 1:
            node1 = heapq.heappop(self.heap)
            node2 = heapq.heappop(self.heap)
            merged = HuffmanNode(None, node1.freq + node2.freq)
            merged.left = node1
            merged.right = node2
            heapq.heappush(self.heap, merged)

    def make_codes_helper(self, root, current_code):
        if root is None:
            return
        if root.char is not None:
            # FIX 1: single-symbol edge case — assign "0" instead of empty string
            code = current_code if current_code else "0"
            self.codes[root.char] = code
            self.reverse_mapping[code] = root.char
            return
        self.make_codes_helper(root.left,  current_code + "0")
        self.make_codes_helper(root.right, current_code + "1")

    def make_codes(self):
        root = heapq.heappop(self.heap)
        self.make_codes_helper(root, "")

    def get_encoded_text(self, text_bytes):
        return "".join(self.codes[char] for char in text_bytes)

    def pad_encoded_text(self, encoded_text):
        extra_padding = 8 - len(encoded_text) % 8
        if extra_padding == 8:
            extra_padding = 0
        encoded_text += "0" * extra_padding
        padded_info = "{0:08b}".format(extra_padding)
        return padded_info + encoded_text

    def get_byte_array(self, padded_encoded_text):
        if len(padded_encoded_text) % 8 != 0:
            raise ValueError("Padding error: bit string length is not a multiple of 8")
        b = bytearray()
        for i in range(0, len(padded_encoded_text), 8):
            b.append(int(padded_encoded_text[i:i + 8], 2))
        return b

    # ------------------------------------------------------------------ #
    #  FIX 3: Safe frequency table encoding (replaces pickle)             #
    # ------------------------------------------------------------------ #

    def _encode_freq_dict(self, frequency):
        """
        Encode {byte_int: count} as a flat byte sequence.
        Each entry = 1 byte (key) + 4 bytes (count, big-endian) = 5 bytes.
        No pickle → no arbitrary code execution on decompression.
        """
        parts = []
        for byte_val, count in frequency.items():
            parts.append(byte_val.to_bytes(1, "big"))
            parts.append(count.to_bytes(4, "big"))
        return b"".join(parts)

    def _decode_freq_dict(self, data):
        """Reverse of _encode_freq_dict."""
        if len(data) % 5 != 0:
            raise ValueError("Corrupt frequency table: length is not a multiple of 5")
        frequency = {}
        for i in range(0, len(data), 5):
            byte_val = data[i]
            count    = int.from_bytes(data[i + 1:i + 5], "big")
            frequency[byte_val] = count
        return frequency

    # ------------------------------------------------------------------ #
    #  FIX 4: Secure password hashing (pbkdf2 + random salt)             #
    # ------------------------------------------------------------------ #

    def _hash_password(self, password):
        """Return (salt, hash) using PBKDF2-HMAC-SHA256 with 100 000 iterations."""
        salt = os.urandom(16)
        digest = hashlib.pbkdf2_hmac("sha256", password.encode(), salt, 100_000)
        return salt, digest

    def _verify_password(self, password_attempt, salt, stored_hash):
        """Return True if the attempt matches the stored hash."""
        attempt_hash = hashlib.pbkdf2_hmac(
            "sha256", password_attempt.encode(), salt, 100_000
        )
        return attempt_hash == stored_hash

    # ------------------------------------------------------------------ #
    #  Encryption (XOR with cycling key — unchanged logic)               #
    # ------------------------------------------------------------------ #

    def simple_encrypt_decrypt(self, data_bytes, password):
        """XOR encryption/decryption with a cycling password key."""
        if not password:
            return data_bytes
        key     = password.encode()
        key_len = len(key)
        return bytes(byte ^ key[i % key_len] for i, byte in enumerate(data_bytes))

    # ------------------------------------------------------------------ #
    #  Public API                                                         #
    # ------------------------------------------------------------------ #

    def compress_bytes(self, file_bytes, password=None):
        """
        Compress raw bytes using Huffman coding, with optional XOR encryption.

        File format (bytes):
          [HasPwd  : 1 B ]
          [Salt    : 16 B]   (zeros when no password)
          [PassHash: 32 B]   (zeros when no password)
          [FreqLen : 4 B ]   big-endian uint32
          [FreqDict: N B ]   5 bytes per symbol (key=1B, count=4B)
          [Body    : M B ]   padded Huffman bitstream, XOR-encrypted if password set

        Returns: bytes
        """
        # FIX 2: reset state so the instance can be reused safely
        self._reset_state()

        if not file_bytes:
            raise ValueError("Input is empty — nothing to compress")

        # Step 1-3: build tree and codes
        frequency = self.make_frequency_dict(file_bytes)
        self.make_heap(frequency)
        self.merge_nodes()
        self.make_codes()

        # Step 4: encode
        encoded_text        = self.get_encoded_text(file_bytes)
        padded_encoded_text = self.pad_encoded_text(encoded_text)
        body                = bytes(self.get_byte_array(padded_encoded_text))

        # Step 5: encrypt body
        if password:
            body = self.simple_encrypt_decrypt(body, password)

        # Step 6: build header
        has_password = b"\x01" if password else b"\x00"

        if password:
            salt, pass_hash = self._hash_password(password)
        else:
            salt      = b"\x00" * 16
            pass_hash = b"\x00" * 32

        freq_dump = self._encode_freq_dict(frequency)
        freq_len  = len(freq_dump).to_bytes(4, "big")

        header = has_password + salt + pass_hash + freq_len + freq_dump
        return header + body

    def decompress_bytes(self, file_bytes, password_attempt=None):
        """
        Decompress bytes produced by compress_bytes.

        Raises ValueError for wrong/missing password or corrupt data.
        Returns: bytes
        """
        # FIX 2: reset state
        self._reset_state()

        ptr = 0

        # Step 1: password flag
        has_password = file_bytes[ptr] == 1
        ptr += 1

        # Step 2: salt + hash
        salt        = file_bytes[ptr:ptr + 16]; ptr += 16
        stored_hash = file_bytes[ptr:ptr + 32]; ptr += 32

        if has_password:
            if not password_attempt:
                raise ValueError("This file is password-protected. Please provide a password.")
            if not self._verify_password(password_attempt, salt, stored_hash):
                raise ValueError("Incorrect password.")

        # Step 3: frequency table
        freq_len  = int.from_bytes(file_bytes[ptr:ptr + 4], "big"); ptr += 4
        freq_dump = file_bytes[ptr:ptr + freq_len];                  ptr += freq_len
        frequency = self._decode_freq_dict(freq_dump)

        # Step 4: rebuild tree
        self.make_heap(frequency)
        self.merge_nodes()
        self.make_codes()

        # Step 5: read + decrypt body
        body = file_bytes[ptr:]
        if has_password:
            body = self.simple_encrypt_decrypt(body, password_attempt)

        if not body:
            return b""

        # Step 6: unpack bits
        bit_string = "".join(f"{byte:08b}" for byte in body)

        # Step 7: remove padding
        extra_padding = int(bit_string[:8], 2)
        bit_string    = bit_string[8:]

        # FIX (original): avoid bit_string[:-0] returning empty string
        if extra_padding != 0:
            encoded_text = bit_string[:-extra_padding]
        else:
            encoded_text = bit_string

        # Step 8: decode via reverse mapping
        decoded_bytes = bytearray()
        current_code  = ""
        for bit in encoded_text:
            current_code += bit
            if current_code in self.reverse_mapping:
                decoded_bytes.append(self.reverse_mapping[current_code])
                current_code = ""

        return bytes(decoded_bytes)


# ------------------------------------------------------------------ #
#  Quick self-test                                                    #
# ------------------------------------------------------------------ #

if __name__ == "__main__":
    test_cases = [
        (b"hello huffman world!", None,         "Normal text, no password"),
        (b"hello huffman world!", "secret123",  "Normal text, with password"),
        (b"aaaaaaaaaa",           None,         "Single repeated byte (edge case)"),
        (b"\x00\xff\x00\xff",    None,         "Binary data"),
        (b"x",                   None,         "Single byte"),
    ]

    print("Running self-tests...\n")
    all_passed = True

    for original, password, label in test_cases:
        hc = HuffmanCoding()
        try:
            compressed   = hc.compress_bytes(original, password)
            decompressed = hc.decompress_bytes(compressed, password)
            passed       = decompressed == original
            ratio        = len(compressed) / len(original)
            status       = "PASS" if passed else "FAIL"
            print(f"[{status}] {label}")
            print(f"       {len(original)} B → {len(compressed)} B  (ratio {ratio:.2f})")
            if not passed:
                all_passed = False
                print(f"       Expected: {original!r}")
                print(f"       Got:      {decompressed!r}")
        except Exception as e:
            all_passed = False
            print(f"[FAIL] {label}")
            print(f"       Exception: {e}")
        print()

    # Test wrong-password rejection
    hc = HuffmanCoding()
    compressed = hc.compress_bytes(b"secret data", "correct")
    try:
        hc.decompress_bytes(compressed, "wrong")
        print("[FAIL] Wrong password should have raised ValueError")
        all_passed = False
    except ValueError:
        print("[PASS] Wrong password correctly rejected\n")

    # Test reuse of same instance
    hc = HuffmanCoding()
    c1 = hc.compress_bytes(b"first call data")
    c2 = hc.compress_bytes(b"second call data")
    d1 = hc.decompress_bytes(c1)
    d2 = hc.decompress_bytes(c2)
    if d1 == b"first call data" and d2 == b"second call data":
        print("[PASS] Instance reuse works correctly\n")
    else:
        print("[FAIL] Instance reuse corrupted data\n")
        all_passed = False

    print("All tests passed!" if all_passed else "Some tests FAILED.")
