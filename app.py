# app.py

import re
import io

import cv2
import numpy as np
import pytesseract
import streamlit as st
from streamlit_drawable_canvas import st_canvas

from no_mrn import _detect_and_mask, fix_ocr_text, NRIC_REGEX

# ---------------- UI CONFIG ----------------
st.set_page_config(page_title="NRIC Masking Tool", page_icon="🕵️", layout="wide")

st.title("🕵️ Singapore NRIC Masking Tool")
st.write(
    "Upload a billing system screenshot. The tool will detect and mask **Singapore NRIC/FIN** "
    "automatically, and you can optionally add extra manual masks."
)

mode = st.sidebar.radio("Mode", ["Single image", "Batch (multiple images)"])
enable_manual = st.sidebar.checkbox("Enable manual masking (add extra masks)", value=True)

# Common helper: decode uploaded file to OpenCV image
def read_image(file) -> np.ndarray:
    file_bytes = np.asarray(bytearray(file.read()), dtype=np.uint8)
    image = cv2.imdecode(file_bytes, cv2.IMREAD_COLOR)
    return image


# =============== SINGLE IMAGE MODE ===============
if mode == "Single image":
    uploaded = st.file_uploader("Upload image", type=["png", "jpg", "jpeg"])

    if uploaded:
        image = read_image(uploaded)

        if image is None:
            st.error("Couldn't read the image. Please try a different file.")
        else:
            # Original display
            col1, col2 = st.columns(2)
            with col1:
                st.subheader("📸 Original")
                st.image(
                    cv2.cvtColor(image, cv2.COLOR_BGR2RGB),
                    caption="Original uploaded image",
                    use_column_width=True,
                )

            # OCR
            rgb = cv2.cvtColor(image, cv2.COLOR_BGR2RGB)
            ocr_data = pytesseract.image_to_data(
                rgb,
                output_type=pytesseract.Output.DICT,
                config="--oem 1 --psm 6",
            )

            # ---------- Detection preview ----------
            preview = image.copy()
            for i, raw_text in enumerate(ocr_data.get("text", [])):
                if not raw_text:
                    continue
                norm = fix_ocr_text(raw_text.strip())
                # Use your existing NRIC regex:
                if re.fullmatch(NRIC_REGEX, norm):
                    x = int(ocr_data["left"][i])
                    y = int(ocr_data["top"][i])
                    w = int(ocr_data["width"][i])
                    h = int(ocr_data["height"][i])
                    cv2.rectangle(preview, (x, y), (x + w, y + h), (0, 255, 0), 2)

            with col2:
                st.subheader("🔍 Detection preview")
                st.image(
                    cv2.cvtColor(preview, cv2.COLOR_BGR2RGB),
                    caption="Green boxes = suspected NRIC/FIN",
                    use_column_width=True,
                )

            st.markdown("---")

            # ---------- Auto-masking using your backend function ----------
            st.subheader("🛡 Auto-masked result (NRIC/FIN)")
            masked_count, auto_masked = _detect_and_mask(image.copy(), ocr_data)
            st.image(
                cv2.cvtColor(auto_masked, cv2.COLOR_BGR2RGB),
                caption=f"Auto-masked {masked_count} region(s)",
                use_column_width=True,
            )

            success, buffer = cv2.imencode(".jpg", auto_masked)
            if success:
                st.download_button(
                    "Download auto-masked image",
                    buffer.tobytes(),
                    "masked_auto.jpg",
                    mime="image/jpeg",
                )

            # ---------- Manual mask on top (optional) ----------
            if enable_manual:
                st.markdown("---")
                st.subheader("✏️ Optional: add extra manual masks")

                st.write(
                    "Draw rectangles over any extra sensitive info "
                    "(e.g., MRN, phone, address)."
                )

                # Use the auto-masked image as base for manual masking
                canvas_height, canvas_width = auto_masked.shape[:2]

                canvas_result = st_canvas(
                    stroke_color="#000000",
                    stroke_width=3,
                    background_image=cv2.cvtColor(auto_masked, cv2.COLOR_BGR2RGB),
                    update_streamlit=True,
                    height=canvas_height,
                    width=canvas_width,
                    drawing_mode="rect",
                    key="canvas_single",
                )

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

                    st.image(
                        cv2.cvtColor(final_img, cv2.COLOR_BGR2RGB),
                        caption="Final image with auto + manual masks",
                        use_column_width=True,
                    )

                    ok, final_buf = cv2.imencode(".jpg", final_img)
                    if ok:
                        st.download_button(
                            "Download FINAL masked image",
                            final_buf.tobytes(),
                            "masked_final.jpg",
                            mime="image/jpeg",
                        )

    else:
        st.info("👆 Upload an image above to start.")


# =============== BATCH MODE (MULTIPLE IMAGES) ===============
else:
    uploaded_files = st.file_uploader(
        "Upload multiple images", type=["png", "jpg", "jpeg"], accept_multiple_files=True
    )

    if uploaded_files:
        st.warning(
            "Batch mode does auto-masking only (no manual drawing) to keep it simple & fast."
        )

        results = []
        zip_buffer = io.BytesIO()
        import zipfile

        with zipfile.ZipFile(zip_buffer, "w") as zip_file:
            for file in uploaded_files:
                image = read_image(file)
                if image is None:
                    st.error(f"Could not read image: {file.name}")
                    continue

                rgb = cv2.cvtColor(image, cv2.COLOR_BGR2RGB)
                ocr_data = pytesseract.image_to_data(
                    rgb,
                    output_type=pytesseract.Output.DICT,
                    config="--oem 1 --psm 6",
                )

                masked_count, masked_img = _detect_and_mask(image.copy(), ocr_data)

                # Save each masked image into ZIP
                ok, buf = cv2.imencode(".jpg", masked_img)
                if ok:
                    zip_file.writestr(f"masked_{file.name}.jpg", buf.tobytes())

                results.append((file.name, masked_count, masked_img))

        # Show small previews and counts
        st.subheader("Batch results")
        for filename, count, masked_img in results:
            st.write(f"**{filename}** — masked `{count}` region(s)")
            st.image(
                cv2.cvtColor(masked_img, cv2.COLOR_BGR2RGB),
                use_column_width=True,
            )

        # Download ZIP with all masked images
        zip_buffer.seek(0)
        st.download_button(
            "Download all masked images (ZIP)",
            zip_buffer,
            "masked_images.zip",
            mime="application/zip",
        )
    else:
        st.info("👆 Upload multiple images to process them in batch.")
