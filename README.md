📂 Huffman File Compression and Security Tool

Project Description

This project implements a lossless data compression tool using the Huffman Coding Algorithm. Developed as a Design Project for a Data Structures & Algorithms (DSA) course (CS-218), the tool provides an intuitive Graphical User Interface (GUI) built with Streamlit and includes a necessary feature for setting a password for file security (XOR-based encryption).

The tool processes files (including text, source code, and binary images) byte-by-byte, making it universally applicable.

⚙️ Core Data Structures & Algorithm

Algorithm: Huffman Coding

Huffman Coding is a prefix-free variable-length coding scheme. It achieves compression by:

Counting Frequencies: Analyzing the input data to determine the frequency of each unique byte/character.

Building the Huffman Tree: Using a Min-Heap (Priority Queue) to efficiently build an optimal binary tree where frequent characters are near the root (short codes) and rare characters are deep in the tree (long codes).

Encoding: Traversing the final tree to generate the unique binary code for each byte.

DSA Components Used

Min-Heap (Priority Queue): Used to prioritize the two lowest frequency nodes for merging, ensuring the tree is optimally constructed.

Binary Tree: The fundamental data structure used to store the Huffman codes, where traversing left is '0' and traversing right is '1'.

Hash Map / Dictionary: Used to store the frequency counts of all 256 possible bytes (0-255).

🚀 Getting Started

Prerequisites

You need Python 3.8+ installed.

Installation

Clone the repository (if applicable) or ensure files are in one folder:

huffman.py
app.py
requirements.txt


Install Dependencies:
Use the provided requirements.txt file to install necessary libraries (Streamlit):

pip install -r requirements.txt


How to Run the Application

Execute the Streamlit command in your terminal:

streamlit run app.py


The application will open automatically in your web browser.

🔑 Security Feature: Password Protection

The tool includes an optional password feature on compression.

Compression: If a password is set, the tool uses hashlib.sha256 to store a hash of the password in the file header, and the encoded data body is encrypted using a simple XOR cipher with the password as the key.

Decompression: The user must provide the password. The tool verifies the password hash against the stored hash and then reverses the XOR cipher before decoding the Huffman bitstream.

📝 Report Generation

The application automatically calculates and stores key metrics (Original Size, Compressed Size, Ratio, Time Taken) in the session state after a successful compression. A Report Generator link in the sidebar allows you to download a Markdown file containing the full complexity analysis and the results of the latest run, fulfilling the project submission requirements.
