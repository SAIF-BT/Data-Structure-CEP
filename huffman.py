import heapq
import os
import pickle
import hashlib

class HuffmanNode:
    def __init__(self, char, freq):
        self.char = char
        self.freq = freq
        self.left = None
        self.right = None

    # Define comparison for heap (min-heap based on frequency)
    def __lt__(self, other):
        return self.freq < other.freq

class HuffmanCoding:
    def __init__(self):
        self.heap = []
        self.codes = {}
        self.reverse_mapping = {}

    def make_frequency_dict(self, text_bytes):
        frequency = {}
        for character in text_bytes:
            if character not in frequency:
                frequency[character] = 0
            frequency[character] += 1
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
            self.codes[root.char] = current_code
            self.reverse_mapping[current_code] = root.char
            return

        self.make_codes_helper(root.left, current_code + "0")
        self.make_codes_helper(root.right, current_code + "1")

    def make_codes(self):
        root = heapq.heappop(self.heap)
        self.make_codes_helper(root, "")

    def get_encoded_text(self, text_bytes):
        # Optimization: Use join instead of string concatenation loop
        # This prevents O(N^2) slowdown on large files like images
        return "".join([self.codes[char] for char in text_bytes])

    def pad_encoded_text(self, encoded_text):
        extra_padding = 8 - len(encoded_text) % 8
        for i in range(extra_padding):
            encoded_text += "0"

        padded_info = "{0:08b}".format(extra_padding)
        encoded_text = padded_info + encoded_text
        return encoded_text

    def get_byte_array(self, padded_encoded_text):
        if len(padded_encoded_text) % 8 != 0:
            print("Padding error")
            exit(0)

        b = bytearray()
        # Process in chunks of 8
        for i in range(0, len(padded_encoded_text), 8):
            byte = padded_encoded_text[i:i+8]
            b.append(int(byte, 2))
        return b

    def simple_encrypt_decrypt(self, data_bytes, password):
        """
        Simple XOR encryption for the project requirement.
        """
        if not password:
            return data_bytes
        
        # Create a cycling key from the password
        key = password.encode()
        encrypted = bytearray()
        key_len = len(key)
        
        for i, byte in enumerate(data_bytes):
            encrypted.append(byte ^ key[i % key_len])
            
        return bytes(encrypted)

    def compress_bytes(self, file_bytes, password=None):
        """
        Main compression flow taking raw bytes and returning compressed bytes.
        """
        # 1. Frequency Map
        frequency = self.make_frequency_dict(file_bytes)
        
        # 2. Build Heap and Tree
        self.make_heap(frequency)
        self.merge_nodes()
        self.make_codes()

        # 3. Encode
        encoded_text = self.get_encoded_text(file_bytes)
        padded_encoded_text = self.pad_encoded_text(encoded_text)
        b = self.get_byte_array(padded_encoded_text)
        
        # 4. Encrypt Body (if password provided)
        final_body = self.simple_encrypt_decrypt(b, password)

        # 5. Prepare Header
        # Structure: [HasPassword(1)] + [PassHash(32)] + [FreqDictLen(4)] + [FreqDict] + [Body]
        
        has_password = b'\x01' if password else b'\x00'
        pass_hash = hashlib.sha256(password.encode()).digest() if password else b'\x00'*32
        
        freq_dump = pickle.dumps(frequency)
        freq_len = len(freq_dump).to_bytes(4, byteorder='big')
        
        header = has_password + pass_hash + freq_len + freq_dump
        
        return header + final_body

    def decompress_bytes(self, file_bytes, password_attempt=None):
        """
        Main decompression flow.
        """
        ptr = 0
        
        # 1. Read Password Flag
        has_password = file_bytes[ptr] == 1
        ptr += 1
        
        # 2. Verify Password
        stored_hash = file_bytes[ptr:ptr+32]
        ptr += 32
        
        if has_password:
            if not password_attempt:
                raise ValueError("Password required")
            
            attempt_hash = hashlib.sha256(password_attempt.encode()).digest()
            if attempt_hash != stored_hash:
                raise ValueError("Invalid Password")
        
        # 3. Read Frequency Table
        freq_len = int.from_bytes(file_bytes[ptr:ptr+4], byteorder='big')
        ptr += 4
        
        freq_dump = file_bytes[ptr:ptr+freq_len]
        ptr += freq_len
        
        frequency = pickle.loads(freq_dump)
        
        # 4. Rebuild Tree
        self.heap = []
        self.make_heap(frequency)
        self.merge_nodes()
        self.make_codes() 
        
        # 5. Read Body
        body_bytes = file_bytes[ptr:]
        
        # 6. Decrypt Body
        if has_password:
            body_bytes = self.simple_encrypt_decrypt(body_bytes, password_attempt)
            
        # 7. Decode Bitstream
        # Optimization: Use f-string formatting inside join for O(N) speed
        bit_string = "".join([f"{byte:08b}" for byte in body_bytes])
            
        # 8. Remove Padding
        if not bit_string:
            return b""
            
        padding_info = bit_string[:8]
        extra_padding = int(padding_info, 2)
        
        bit_string = bit_string[8:] 
        
        # FIX: Handle 0 padding correctly. 
        # In Python, string[:-0] returns an empty string, effectively deleting the data.
        if extra_padding != 0:
            encoded_text = bit_string[:-1*extra_padding]
        else:
            encoded_text = bit_string
        
        # 9. Traverse Tree to Decode
        decoded_bytes = bytearray()
        current_code = ""
        
        for bit in encoded_text:
            current_code += bit
            if current_code in self.reverse_mapping:
                character = self.reverse_mapping[current_code]
                decoded_bytes.append(character)
                current_code = ""
                
        return bytes(decoded_bytes)