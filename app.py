import streamlit as st
import io
import time
from huffman import HuffmanCoding

st.set_page_config(page_title="Huffman Compression Tool", layout="centered")

# --- STYLE & HEADER ---
st.title("File Compression Tool (DSA CEP)")
st.markdown("### Computer Systems Engineering | CS-218")
st.markdown("---")

# --- SIDEBAR: REPORT GENERATION ---
with st.sidebar:
    st.header("📄 Report Generator")
    st.info("Compress a file first to generate the stats for the report.")
    if 'report_data' in st.session_state:
        st.success("Stats ready!")
        
        report_text = f"""
# DESIGN PROJECT REPORT: FILE COMPRESSION TOOL

**Course:** Data Structures & Algorithms (CS-218)
**Date:** {time.strftime("%Y-%m-%d")}

---

## 1. Compression Algorithm Selected: Huffman Coding
Huffman coding is a popular algorithm for lossless data compression. It assigns variable-length codes to input characters, with shorter codes assigned to more frequent characters.

**Why Selected?**
It allows for efficient, lossless compression suitable for the project requirements. It utilizes a Priority Queue (Min-Heap) and a Binary Tree, demonstrating key DSA concepts.

---

## 2. Complexity Analysis

### Time Complexity
1. **Building Frequency Map:** O(N) - where N is the file size (bytes).
2. **Building Heap:** O(C) - where C is the number of unique characters (max 256 for binary files).
3. **Building Huffman Tree:** O(C log C) - Extracting min items from heap.
4. **Encoding Data:** O(N) - Traversing the file and assigning codes.

**Overall Time Complexity:** O(N log C) ≈ O(N)
(Since C is constant/bounded for byte data, the algorithm is linear with respect to file size).

### Space Complexity
**O(C)** to store the frequency map and the Huffman Tree.
Since C <= 256 for binary files, the auxiliary space requirement is very low and constant relative to N.

---

## 3. Implementation & Results (Current Run)

**File Name:** `{st.session_state['report_data']['filename']}`
**Original Size:** {st.session_state['report_data']['orig_size']} bytes
**Compressed Size:** {st.session_state['report_data']['comp_size']} bytes
**Compression Ratio:** {st.session_state['report_data']['ratio']:.2f}% reduction
**Time Taken:** {st.session_state['report_data']['time']:.4f} seconds

---

## 4. Code Structure
The project is implemented in Python using:
- **Min-Heap:** For efficient selection of minimum frequency nodes.
- **Binary Tree:** For generating prefix codes.
- **Dictionary:** For O(1) access to character frequencies.
- **Streamlit:** For the Graphical User Interface.
"""
        st.download_button(
            label="Download Project Report (txt)",
            data=report_text,
            file_name="DSA_Project_Report.md",
            mime="text/markdown"
        )

# --- MAIN TABS ---
tab1, tab2 = st.tabs(["🗜️ Compress", "🔓 Decompress"])

# === TAB 1: COMPRESS ===
with tab1:
    st.subheader("Upload a File to Compress")
    
    # Added Helper Expander
    with st.expander("ℹ️ Which files compress best?"):
        st.markdown("""
        **Best Results (40-60% reduction):**
        - Text files (`.txt`, `.md`, `.csv`)
        - Source code (`.py`, `.c`, `.java`)
        - Uncompressed images (`.bmp`)
        
        **Poor Results (0-5% reduction):**
        - Already compressed files (`.jpg`, `.png`, `.mp4`, `.zip`)
        - *Reason:* These files typically have high entropy and no redundancy left to compress.
        """)

    uploaded_file = st.file_uploader("Choose a file", key="comp_uploader")
    
    password = st.text_input("Set Password (Optional)", type="password", key="comp_pass")
    
    if uploaded_file is not None:
        # Display File Info
        file_bytes = uploaded_file.getvalue()
        orig_size = len(file_bytes)
        st.write(f"**Original Size:** {orig_size / 1024:.2f} KB")
        
        if st.button("Compress File", type="primary"):
            start_time = time.time()
            
            # Run Huffman
            huffman = HuffmanCoding()
            try:
                compressed_data = huffman.compress_bytes(file_bytes, password)
                end_time = time.time()
                
                comp_size = len(compressed_data)
                ratio = ((orig_size - comp_size) / orig_size) * 100
                
                st.success("Compression Successful!")
                
                # Metrics
                col1, col2, col3 = st.columns(3)
                col1.metric("Original", f"{orig_size} B")
                col2.metric("Compressed", f"{comp_size} B")
                
                # Handle negative savings (common for small/compressed files)
                if ratio > 0:
                    col3.metric("Saved", f"{ratio:.1f}%")
                else:
                    col3.metric("Saved", f"{ratio:.1f}%", delta_color="inverse")
                    st.caption("Note: Negative savings occur when the file is already compressed or too small (header overhead).")
                
                # Save data for Report
                st.session_state['report_data'] = {
                    'filename': uploaded_file.name,
                    'orig_size': orig_size,
                    'comp_size': comp_size,
                    'ratio': ratio,
                    'time': end_time - start_time
                }
                
                # Download Button
                st.download_button(
                    label="Download Compressed File (.bin)",
                    data=compressed_data,
                    file_name=f"{uploaded_file.name}.bin",
                    mime="application/octet-stream"
                )
                
            except Exception as e:
                st.error(f"An error occurred: {e}")

# === TAB 2: DECOMPRESS ===
with tab2:
    st.subheader("Upload a Compressed File (.bin)")
    uploaded_comp = st.file_uploader("Choose file", type=['bin'], key="decomp_uploader")
    
    decrypt_pass = st.text_input("Enter Password (if set)", type="password", key="decomp_pass")
    
    if uploaded_comp is not None:
        if st.button("Decompress File"):
            file_bytes = uploaded_comp.getvalue()
            
            huffman = HuffmanCoding()
            try:
                decompressed_data = huffman.decompress_bytes(file_bytes, decrypt_pass)
                st.success("Decompression Successful!")
                
                st.write(f"**Recovered Size:** {len(decompressed_data) / 1024:.2f} KB")
                
                # Download Button (Generic name, user renames extension)
                st.download_button(
                    label="Download Recovered File",
                    data=decompressed_data,
                    file_name="decompressed_file",
                    mime="application/octet-stream",
                    help="Rename this file to its original extension (e.g., .txt or .jpg) after downloading."
                )
            except ValueError as ve:
                st.error(f"Security Error: {ve}")
            except Exception as e:
                st.error(f"Error: {e}")

# --- FOOTER ---
st.markdown("---")
st.caption("Design Project | Built with Love❤️❤️❤️ By CS-24097 Muhammad Sarim Khan")