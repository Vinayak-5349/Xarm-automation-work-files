from google.cloud import vision
import io

def extract_text(image_path):
    # Initialize client
    client = vision.ImageAnnotatorClient()

    # Read image
    with io.open(image_path, "rb") as image_file:
        content = image_file.read()

    image = vision.Image(content=content)

    # Perform text detection
    response = client.text_detection(image=image)
    texts = response.text_annotations

    if not texts:
        return "No text found."

    # The first item contains the full detected text
    full_text = texts[0].description
    return full_text


if __name__ == "__main__":
    result = extract_text("shared image.jpeg")  # Change path to your image
    print("OCR Result:\n", result)
