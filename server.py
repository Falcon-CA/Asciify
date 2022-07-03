import io
import os
from PIL import Image, ImageEnhance, ImageOps, UnidentifiedImageError
import random
import sys

from flask import Flask, Response, request, send_file

BRIGHTNESS = "$@B%8&WM#*oahkbdpqwmZO0QLCJUYXzcvunxrjft/|()1{}[]?+-~i!Il;:,^.' "

server = Flask(__name__)
sessions = set()


@server.route("/")
def server_root():
    return send_file("index.html")


@server.route("/convert", methods=["POST"])
def conversion():
    try:
        xsr = request.form.get("X-Ratio")
        xsr = float(xsr) if xsr else 1
        ysr = request.form.get("Y-Ratio")
        ysr = float(ysr) if ysr else 2
        reverse = request.form.get("Rev-Bright")
        reverse = reverse if reverse else False
        sharpness = request.form.get("Sharp-Factor")
        sharpness = float(sharpness) if sharpness else 1.7
    except ValueError:
        return Response("XSR and YSR must be floating points or integers >=1", status=400)
    if xsr < 1 or ysr < 1:
        return Response("XSR and YSR cannot be less than 0", status=400)
    if sharpness < 0 or sharpness > 2:
        return Response("Sharpness Factor must be a floating point between 0 and 2", status=400)

    file = request.files.get("Image-File")
    if file is None:
        return Response("No image file given", status=400)

    session_id = generate_id()
    while session_id in sessions:
        session_id = generate_id()
    sessions.add(session_id)
    file.save(f"cache/{session_id}")

    try:
        img = Image.open(f"cache/{session_id}")
    except UnidentifiedImageError:
        os.remove(f"cache/{session_id}")
        sessions.remove(session_id)
        return Response("That's not a valid image file", status=400)

    x = img.size[0] // xsr
    y = img.size[1] // ysr
    img = img.resize((x, y), resample=Image.NEAREST)
    img = ImageOps.grayscale(img)
    img = ImageEnhance.Sharpness(img).enhance(sharpness)

    buffer = io.BytesIO()
    local_brightness = BRIGHTNESS[::-1] if reverse else BRIGHTNESS
    for y_ in range(y):
        line = ""
        for x_ in range(x):
            pixel = local_brightness[img.getpixel((x_, y_)) >> 2]
            line += pixel
        line += "\n"
        buffer.write(line.encode("ascii"))
    buffer.seek(0)

    os.remove(f"cache/{session_id}")
    sessions.remove(session_id)
    return send_file(buffer, as_attachment=True, attachment_filename="conversion_result.txt")


def generate_id():
    return "".join([
        chr(random.randint(97, 122))
        for _ in range(20)
    ])


if __name__ == "__main__":
    server.config["MAX_CONTENT_LENGTH"] = 8 * 1024 * 1024
    if "cache" not in os.listdir():
        os.mkdir("cache")
    if "--debug" in sys.argv:
        server.run()
