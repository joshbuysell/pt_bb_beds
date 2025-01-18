import streamlit as st
from PIL import Image, ImageDraw, ImageFont
import pandas as pd
import os
import io
import zipfile

FONT_PATH = "./Monaco.ttf"
FONT_SIZE = 65
IMAGE_FOLDER = "./images"
DEFAULT_PRICE_FILE = "./price.xlsx"


def read_prices(file):
    df = pd.read_excel(file)
    df['Назва'] = df['Назва'].str.lower()
    return {row['Назва']: {"Ліжечко": row["Ліжечко"], "Мятник": row["Мятник"], "Шухляда": row["Шухляда"]}
            for _, row in df.iterrows()}


def add_price_with_centered_text(image, prices, file_name):
    draw = ImageDraw.Draw(image)
    file_name = os.path.splitext(file_name)[0].lower()

    if file_name in prices:
        price_data = prices[file_name]

        width, height = image.size
        overlay_height = 350

        draw.rectangle(
            [(0, height - overlay_height), (width, height)],
            fill=(255, 255, 255, 255)
        )

        font = ImageFont.truetype(FONT_PATH, FONT_SIZE)

        y_offset = height - overlay_height + 30
        line_spacing = 30

        def draw_centered_text(text, y_position):
            text_bbox = draw.textbbox((0, 0), text, font=font)
            text_width = text_bbox[2] - text_bbox[0]
            x_position = (width - text_width) // 2
            draw.text((x_position, y_position), text, font=font, fill=(0, 0, 0))

        draw_centered_text(f"Ліжечко: {price_data['Ліжечко']} грн", y_offset)
        draw_centered_text(f"З маятником: {price_data['Мятник']} грн", y_offset + 65 + line_spacing)
        draw_centered_text(f"З шухлядою: {price_data['Шухляда']} грн", y_offset + 130 + line_spacing * 2)

    return image


def process_image(file_name, prices):
    """Обробляє одне зображення і повертає оброблене зображення."""
    image_path = os.path.join(IMAGE_FOLDER, file_name)
    image = Image.open(image_path).convert("RGBA")
    processed_image = add_price_with_centered_text(image, prices, file_name)
    return processed_image


st.title("Динамічний генератор цін для зображень")

is_mobile = st.sidebar.checkbox("Мобільний режим", value=False)
columns_count = 1 if is_mobile else 3

use_default = st.sidebar.checkbox("Використовувати стандартний Excel-файл", value=True)
if "prices" not in st.session_state:
    st.session_state["prices"] = {}

price_file_path = None
if use_default:
    st.sidebar.info("Використовується стандартний Excel-файл.")
    price_file_path = DEFAULT_PRICE_FILE
else:
    uploaded_price_file = st.sidebar.file_uploader("Завантажте Excel-файл із цінами", type=["xlsx"])
    if uploaded_price_file:
        price_file_path = uploaded_price_file

if 'price_file_path' in locals() and os.path.exists(price_file_path):
    if not st.session_state["prices"]:
        st.session_state["prices"] = read_prices(price_file_path)

    tab1, tab2 = st.tabs(["Редагування цін", "Завантаження результатів"])

    with tab1:
        st.subheader("Огляд та редагування цін")
        cols = st.columns(columns_count)

        processed_files = {}

        for idx, file_name in enumerate(os.listdir(IMAGE_FOLDER)):
            if file_name.endswith(".png") or file_name.endswith(".jpg"):
                col = cols[idx % columns_count]

                file_key = os.path.splitext(file_name)[0].lower()
                prices = st.session_state["prices"]

                prices[file_key]["Ліжечко"] = col.text_input(f"Ліжечко ({file_name})", value=prices[file_key]["Ліжечко"])
                prices[file_key]["Мятник"] = col.text_input(f"Маятник ({file_name})", value=prices[file_key]["Мятник"])
                prices[file_key]["Шухляда"] = col.text_input(f"Шухляда ({file_name})", value=prices[file_key]["Шухляда"])

                processed_image = process_image(file_name, prices)

                buf = io.BytesIO()
                processed_image.save(buf, format="PNG")
                buf.seek(0)
                processed_files[file_name] = buf.getvalue()

                col.image(processed_image, caption=f"Оновлене: {file_name}", use_container_width=True)

                col.download_button(
                    label="Завантажити зображення",
                    data=processed_files[file_name],
                    file_name=f"processed_{file_name}",
                    mime="image/png"
                )

    with tab2:
        if processed_files:
            st.subheader("Завантаження результатів")
            zip_buffer = io.BytesIO()
            with zipfile.ZipFile(zip_buffer, "w") as zipf:
                for file_name, file_data in processed_files.items():
                    zipf.writestr(file_name, file_data)
            zip_buffer.seek(0)

            st.download_button(
                label="Завантажити всі оброблені зображення (ZIP)",
                data=zip_buffer,
                file_name="processed_images.zip",
                mime="application/zip"
            )