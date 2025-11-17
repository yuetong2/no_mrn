import re
import cv2
import numpy as np
import pytesseract
import streamlit as st
from PIL import Image
from streamlit_drawable_canvas import st_canvas

from no_mrn import _detect_and_mask, fix_ocr_text, NRIC_REGEX

# ---------------- UI CONFIG ----------------
st.set_page_config(page_title="NRIC Masking Tool", page_icon="🕵️", layout="wide")

st.title("🕵️ Singapore NRIC Masking Tool")
st.write(
    "Upload your screenshot. The tool will auto-detect and mask **Singapore NRIC/FIN**. "
    "You can also add extra manual masks for any missed information."
)

# --------- Helper to parse uploaded file ---------
def read_image(file):
    file_bytes = np.asarray(bytearray(file.read()), dtype=np.uint8)
    return cv2.imdecode(file_bytes, cv2.IMREAD_COLOR)

# --------- UI: File upload ---------
uploaded = st.file_uploader("Upload image", type=["png", "jpg", "jpeg"])

if not uploaded:
    st.info("👆 Upload an image above to start.")
    st.stop()

# --------- Load image ---------
image = read_image(uploaded)

if image is None:
    st.error("Error reading image.")
    st.stop()

col1, col2 = st.columns(2)

# =============== ORIGINAL IMAGE ===============
with col1:
    st.subheader("📸 Original")
    st.image(cv2.cvtColor(image, cv2.COLOR_BGR2RGB), use_column_width=True)

# ===== OCR (needed for preview + auto masking) =====
rgb = cv2.cvtColor(image, cv2.COLOR_BGR2RGB)
ocr_data = pytesseract.image_to_data(
    rgb,
    output_type=pytesseract.Output.DICT,
    config="--oem 1 --psm 6",
)

# ======================= PREVIEW DETECTED NRIC =======================
preview = image.copy()

for i, raw_text in enumerate(ocr_data.get("text", [])):
    if not raw_text:
        continue

    norm = fix_ocr_text(raw_text.strip())

    if re.fullmatch(NRIC_REGEX, norm):
        x = int(ocr_data["left"][i])
        y = int(ocr_data["top"][i])
        w = int(ocr_data["width"][i])
        h = int(ocr_data["height"][i])
        cv2.rectangle(preview, (x, y), (x + w, y + h), (0, 255, 0), 2)

with col2:
    st.subheader("🔍 Detection preview")
    st.image(cv2.cvtColor(preview, cv2.COLOR_BGR2RGB),
             caption="Green = suspected NRIC/FIN",
             use_column_width=True)

st.markdown("---")

# ======================= AUTO MASKING =======================
st.subheader("🛡 Auto-masked (NRIC/FIN)")
masked_count, auto_masked = _detect_and_mask(image.copy(), ocr_data)

st.image(cv2.cvtColor(auto_masked, cv2.COLOR_BGR2RGB),
         caption=f"Auto-masked {masked_count} region(s)",
         use_column_width=True)

success, buffer = cv2.imencode(".jpg", auto_masked)
if success:
    st.download_button(
        "Download auto-masked image",
        buffer.tobytes(),
        "masked_auto.jpg",
        mime="image/jpeg",
    )

st.markdown("---")

# ======================= MANUAL MASKING =======================
st.subheader("✏️ Optional: add extra manual masks")
st.write("Draw rectangles over MRN, phone numbers, addresses, or anything missed.")

canvas_h, canvas_w = auto_masked.shape[:2]

# Convert OpenCV image (BGR) -> RGB -> PIL
pil_bg = Image.fromarray(cv2.cvtColor(auto_masked, cv2.COLOR_BGR2RGB))

canvas_result = st_canvas(
    stroke_color="#000000",
    stroke_width=3,
    background_image=pil_bg,
    update_streamlit=True,
    height=canvas_h,
    width=canvas_w,
    drawing_mode="rect",
    key="manual_mask_canvas",
)

# ================= APPLY MANUAL MASKS ==================
if st.button("Apply manual masks & download final image"):
    final_img = auto_masked.copy()

    if canvas_result.json_data is not None:
        for obj in canvas_result.json_data.get("objects", []):
            if obj.get("type") != "rect":
                continue

            x = int(obj["left"])
            y = int(obj["top"])
            w = int(obj["width"])
            h = int(obj["height"])

            cv2.rectangle(final_img, (x, y), (x + w, y + h), (0, 0, 0), -1)

    st.subheader("✅ Final masked image (Auto + Manual)")
    st.image(cv2.cvtColor(final_img, cv2.COLOR_BGR2RGB), use_column_width=True)

    ok, final_buf = cv2.imencode(".jpg", final_img)
    if ok:
        st.download_button(
            "Download FINAL masked image",
            final_buf.tobytes(),
            "masked_final.jpg",
            mime="image/jpeg",
        )
