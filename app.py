import streamlit as st
import cv2
import numpy as np
import pytesseract
from no_mrn import _detect_and_mask, fix_ocr_text

st.set_page_config(page_title="NRIC Masking Tool", page_icon="🕵️")

st.title("🕵️ Singapore NRIC Masking Tool")
st.write("Paste (Ctrl+V) or drag-drop an image below — any detected NRIC/FIN will be masked automatically.")

uploaded = st.file_uploader("Upload or paste image", type=["png", "jpg", "jpeg"])

if uploaded:
    # Read uploaded image
    file_bytes = np.asarray(bytearray(uploaded.read()), dtype=np.uint8)
    image = cv2.imdecode(file_bytes, cv2.IMREAD_COLOR)

    # Convert to RGB for OCR
    rgb = cv2.cvtColor(image, cv2.COLOR_BGR2RGB)

    # Run OCR to get bounding boxes
    ocr_data = pytesseract.image_to_data(
        rgb,
        output_type=pytesseract.Output.DICT,
        config="--oem 1 --psm 6"
    )

    # Mask detected NRICs
    masked_count, masked_image = _detect_and_mask(image, ocr_data)

    # Display results
    st.image(
        cv2.cvtColor(masked_image, cv2.COLOR_BGR2RGB),
        caption=f"Masked {masked_count} region(s)",
        use_column_width=True,
    )

    # Offer download
    success, buffer = cv2.imencode(".jpg", masked_image)
    if success:
        st.download_button(
            "Download masked image",
            buffer.tobytes(),
            "masked_output.jpg",
            mime="image/jpeg"
        )

else:
    st.info("👆 Paste or upload an image to begin.")
