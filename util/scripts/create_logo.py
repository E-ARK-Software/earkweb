import base64


def get_base64_encoded_image(image_path):
    with open(image_path, "rb") as img_file:
        return base64.b64encode(img_file.read()).decode('utf-8')


print(get_base64_encoded_image("./path/to/logo.png"))
