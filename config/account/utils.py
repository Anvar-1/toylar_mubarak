import base64
import numpy as np
from PIL import Image
import io
from django.utils import translation
import face_recognition


def set_language_for_user(user):
    """
    Foydalanuvchi tili bo‘yicha tarjima muhitini o‘rnatadi.

    :param user: Django foydalanuvchi obyekti
    :return: Foydalanuvchining tilini qaytaradi (masalan, 'uz')
    """
    # Foydalanuvchining tilini olish, default 'uz'
    language = getattr(user, 'language', 'uz')
    translation.activate(language)  # Tilni faollashtirish
    return language


def get_face_encoding(image_file):
    """
    Rasmni o‘qib, yuz encoding (kodlash) qaytaradi.
    Agar bir nechta yuz bo'lsa, birinchi yuzning encodingini qaytaradi.

    :param image_file: Rasm fayli yoki rasmning numpy array shakli
    :return: Yuz encoding (numpy array) yoki None
    """
    image = face_recognition.load_image_file(image_file)  # Rasmni yuklash
    encodings = face_recognition.face_encodings(image)  # Yuz encodinglarini olish

    # Agar rasmda yuz bo'lsa, birinchi yuzning encodingini qaytarish
    if encodings:
        return encodings[0]

    return None  # Agar yuz topilmasa, None qaytariladi


def base64_to_image(base64_string):
    """
    Base64 formatidagi rasmni numpy array'ga aylantiradi.

    :param base64_string: Base64 formatidagi rasm
    :return: Numpy array formatidagi rasm
    """
    # Base64 stringdagi "data:image/png;base64," kabi prefixni olib tashlash
    if base64_string.startswith('data:image'):
        base64_string = base64_string.split(",")[1]  # Prefixni olib tashlash

    img_bytes = base64.b64decode(base64_string)  # Base64 stringni byte formatiga aylantirish
    img = Image.open(io.BytesIO(img_bytes))  # PIL Image formatiga aylantirish
    return np.array(img)  # numpy arrayga aylantirish


def compare_faces(known_encoding, unknown_encoding, tolerance=0.5):
    """
    Ikki yuz encodingini taqqoslaydi va mosligini tekshiradi.

    :param known_encoding: Saqlangan yuz encodingi (ma'lumotlar bazasidan olingan)
    :param unknown_encoding: Yangi yuz encodingi (yuzni aniqlashdan olingan)
    :param tolerance: Moslik uchun ruxsat etilgan xatolik darajasi
    :return: True (yuzlar mos), False (yuzlar mos emas)
    """
    if known_encoding is None or unknown_encoding is None:
        return False  # Agar biri None bo'lsa, yuzlar mos emas

    # Face recognition kutubxonasi yordamida yuzlarni taqqoslash
    return face_recognition.compare_faces([known_encoding], unknown_encoding, tolerance=tolerance)[0]
