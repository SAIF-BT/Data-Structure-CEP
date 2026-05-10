import streamlit as st
import time
from huffman import HuffmanCoding

st.set_page_config(page_title="Huffman Compression Tool", layout="centered")

# --- STYLE & HEADER ---
st.title("🗜️ File Compression Tool (DSA CEP)")
st.markdown("### Computer Systems Engineering | CS-218")
st.markdown("---")

# --- SIDEBAR: REPORT GENERATION ---
with st.sidebar:
    st.header("📄 Report Generator")

    if "report_data" not in st.session_state:
        st.info("Compress a file first to generate stats for the report.")
    else:
        st.success("Stats ready! Click below to download.")
        rd = st.session_state["report_data"]

        report_text = f"""# DESIGN PROJECT REPORT: FILE COMPRESSION TOOL

**Course:** Data Structures & Algorithms (CS-218)
**Date:** {time.strftime("%Y-%m-%d")}

---

## 1. Compression Algorithm: Huffman Coding

Huffman coding is a lossless data-compression algorithm that assigns
variable-length prefix codes to symbols — shorter codes to more frequent
symbols, longer codes to rarer ones.

**Why Selected?**
- Provably optimal prefix code for a given symbol frequency distribution.
- Demonstrates core DSA concepts: Min-Heap (Priority Queue) and Binary Tree.
- Runs in O(N) time relative to file size (see analysis below).

---

## 2. Complexity Analysis

### Time Complexity
| Step | Complexity | Notes |
|------|-----------|-------|
| Build frequency map | O(N) | N = file size in bytes |
| Build min-heap | O(C) | C = unique byte values (≤ 256) |
| Build Huffman tree | O(C log C) | C merges, each O(log C) |
| Encode data | O(N) | One dict lookup per byte |
| **Total** | **O(N log C) ≈ O(N)** | C is bounded (≤ 256) |

### Space Complexity
**O(C)** auxiliary space for the frequency map and Huffman tree.
Since C ≤ 256 for byte data, auxiliary space is effectively constant
regardless of file size.

---

## 3. Results (Current Run)

| Metric | Value |
|--------|-------|
| File name | `{rd["filename"]}` |
| Original size | {rd["orig_size"]:,} bytes ({rd["orig_size"]/1024:.2f} KB) |
| Compressed size | {rd["comp_size"]:,} bytes ({rd["comp_size"]/1024:.2f} KB) |
| Space {'saved' if rd['ratio'] >= 0 else 'overhead'} | {abs(rd["ratio"]):.2f}% |
| Time taken | {rd["time"]:.4f} seconds |
| Password protected | {'Yes' if rd['password_used'] else 'No'} |

{"⚠️ Negative ratio: file is already compressed or too small for Huffman to help." if rd["ratio"] < 0 else "✅ Compression successful."}

---

## 4. Security Notes

- Encryption uses XOR with a cycling password key.
- Password verification uses **PBKDF2-HMAC-SHA256** with a random 16-byte
  salt and 100 000 iterations — resistant to offline brute-force attacks.
- The frequency table is stored as raw bytes (no pickle), eliminating any
  arbitrary code-execution risk on decompression.

---

## 5. Code Structure

| Component | Role |
|-----------|------|
| `HuffmanNode` | Tree node storing symbol and frequency |
| `make_frequency_dict` | Counts byte occurrences — O(N) |
| `make_heap / merge_nodes` | Builds min-heap and Huffman tree — O(C log C) |
| `make_codes_helper` | DFS to assign prefix codes |
| `get_encoded_text` | Maps each byte to its prefix code |
| `pad_encoded_text` | Aligns bit-string to byte boundary |
| `simple_encrypt_decrypt` | XOR encryption / decryption |
| `compress_bytes` | Full compression pipeline |
| `decompress_bytes` | Full decompression pipeline |
| `app.py` | Streamlit GUI |

---

*Design Project | Built with ❤️ by CS-24084 Saifullah Ghanghro*
"""

        st.download_button(
            label="📥 Download Project Report (.md)",
            data=report_text,
            file_name="DSA_Project_Report.md",
            mime="text/markdown",
        )

# --- MAIN TABS ---
tab1, tab2 = st.tabs(["🗜️ Compress", "🔓 Decompress"])

# ================================================================
# TAB 1 — COMPRESS
# ================================================================
with tab1:
    st.subheader("Upload a File to Compress")

    with st.expander("ℹ️ Which files compress best?"):
        st.markdown("""
**Best results (40–60% reduction)**
- Plain text (`.txt`, `.md`, `.csv`, `.log`)
- Source code (`.py`, `.c`, `.java`, `.html`)
- Uncompressed images (`.bmp`, `.tiff`)

**Poor results (0–5% or negative)**
- Already-compressed files (`.jpg`, `.png`, `.mp4`, `.zip`, `.pdf`)
- Very small files (header overhead dominates)

**Why?** Huffman coding exploits byte-frequency redundancy. Files that
have already been compressed have near-uniform byte distributions — nothing
left for Huffman to exploit.
        """)

    uploaded_file = st.file_uploader("Choose a file", key="comp_uploader")
    password = st.text_input(
        "Set Password (optional)",
        type="password",
        key="comp_pass",
        help="Leave blank for no encryption.",
    )

    if uploaded_file is not None:
        file_bytes = uploaded_file.getvalue()
        orig_size = len(file_bytes)

        # FIX: guard against empty files before showing the button
        if orig_size == 0:
            st.error("The uploaded file is empty. Please upload a non-empty file.")
        else:
            st.write(f"**Original size:** {orig_size:,} bytes ({orig_size / 1024:.2f} KB)")

            if st.button("Compress File", type="primary"):
                with st.spinner("Compressing…"):
                    huffman = HuffmanCoding()
                    try:
                        start_time = time.time()
                        compressed_data = huffman.compress_bytes(
                            file_bytes, password or None
                        )
                        elapsed = time.time() - start_time

                        comp_size = len(compressed_data)
                        ratio = ((orig_size - comp_size) / orig_size) * 100

                        st.success("✅ Compression successful!")

                        col1, col2, col3 = st.columns(3)
                        col1.metric("Original", f"{orig_size:,} B")
                        col2.metric("Compressed", f"{comp_size:,} B")
                        col3.metric(
                            "Saved",
                            f"{ratio:.1f}%",
                            delta_color="normal" if ratio >= 0 else "inverse",
                        )

                        if ratio < 0:
                            st.caption(
                                "ℹ️ Negative savings are normal for already-compressed "
                                "or very small files — the header overhead exceeds any gain."
                            )

                        # Save stats for sidebar report
                        st.session_state["report_data"] = {
                            "filename": uploaded_file.name,
                            "orig_size": orig_size,
                            "comp_size": comp_size,
                            "ratio": ratio,
                            "time": elapsed,
                            "password_used": bool(password),
                        }

                        # FIX: strip only the last extension so chained
                        # extensions like ".tar.gz" are handled correctly
                        original_name = uploaded_file.name
                        download_name = original_name + ".bin"

                        st.download_button(
                            label="📥 Download Compressed File (.bin)",
                            data=compressed_data,
                            file_name=download_name,
                            mime="application/octet-stream",
                        )

                    except Exception as e:
                        st.error(f"Compression failed: {e}")

# ================================================================
# TAB 2 — DECOMPRESS
# ================================================================
with tab2:
    st.subheader("Upload a Compressed File (.bin)")

    uploaded_comp = st.file_uploader(
        "Choose a .bin file", type=["bin"], key="decomp_uploader"
    )
    decrypt_pass = st.text_input(
        "Password (leave blank if none was set)",
        type="password",
        key="decomp_pass",
    )

    if uploaded_comp is not None:
        if st.button("Decompress File", type="primary"):
            with st.spinner("Decompressing…"):
                file_bytes = uploaded_comp.getvalue()
                huffman = HuffmanCoding()
                try:
                    decompressed_data = huffman.decompress_bytes(
                        file_bytes, decrypt_pass or None
                    )
                    recovered_size = len(decompressed_data)
                    st.success("✅ Decompression successful!")
                    st.write(
                        f"**Recovered size:** {recovered_size:,} bytes "
                        f"({recovered_size / 1024:.2f} KB)"
                    )

                    # FIX: strip .bin and suggest the original filename
                    original_name = uploaded_comp.name
                    suggested_name = (
                        original_name[:-4]      # remove ".bin"
                        if original_name.endswith(".bin")
                        else "decompressed_file"
                    )

                    st.download_button(
                        label="📥 Download Recovered File",
                        data=decompressed_data,
                        file_name=suggested_name,
                        mime="application/octet-stream",
                        help=f"File will be saved as '{suggested_name}'. "
                             "Rename it if the extension looks wrong.",
                    )

                # FIX: separate error messages for wrong password vs corrupt file
                except ValueError as ve:
                    st.error(f"🔐 Security error: {ve}")
                except Exception as e:
                    st.error(
                        f"Decompression failed: {e}\n\n"
                        "Make sure you uploaded a valid .bin file produced by this tool."
                    )

# --- FOOTER ---
st.markdown("---")
st.caption("Design Project | Built with ❤️ by CS-24084 Saifullah Ghanghro")
