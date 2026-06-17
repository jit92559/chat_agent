from graph.state import MainState
from llms.vision_model import get_vision_model
import base64
import pymupdf  # PyMuPDF

from pptx import Presentation
from docx import Document
from dotenv import load_dotenv

from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_core.messages import HumanMessage

load_dotenv()

vision_model = get_vision_model()

def describe_image_bytes(image_bytes: bytes, mime_type: str = "image/png") -> str:
    try:
        image_base64 = base64.b64encode(image_bytes).decode("utf-8")

        message = HumanMessage(
            content=[
                {
                    "type": "text",
                    "text": """
Extract all visible text from this image.
Also describe diagrams, charts, tables, screenshots, UI, and important visual details.
Return clean text suitable for RAG.
""",
                },
                {
                    "type": "image_url",
                    "image_url": {
                        "url": f"data:{mime_type};base64,{image_base64}"
                    },
                },
            ]
        )

        response = vision_model.invoke([message])
        return str(response.content)

    except Exception as e:
        return f"[VISION_ERROR] {str(e)}"


def pdf_extractor_node(state: MainState) -> dict:
    try:
        file_path = state["file_path"]
        doc = pymupdf.open(file_path)

        all_text = []

        for page_no, page in enumerate(doc, start=1):
            page_text = page.get_text("text")

            if page_text.strip():
                all_text.append(
                    f"\n--- Page {page_no} Text ---\n{page_text}"
                )

            # Full page OCR for scanned PDF pages
            try:
                pix = page.get_pixmap(matrix=pymupdf.Matrix(2, 2))
                page_image_bytes = pix.tobytes("png")

                page_description = describe_image_bytes(
                    page_image_bytes,
                    mime_type="image/png",
                )

                if page_description.strip():
                    all_text.append(
                        f"\n--- Page {page_no} Full Page Vision OCR ---\n"
                        f"{page_description}"
                    )

            except Exception as e:
                all_text.append(
                    f"\n--- Page {page_no} Full Page OCR Error ---\n{str(e)}"
                )

            # Extract embedded images
            images = page.get_images(full=True)

            for image_no, image in enumerate(images, start=1):
                try:
                    xref = image[0]
                    image_info = doc.extract_image(xref)

                    image_bytes = image_info["image"]

                    # skip tiny icons/logos
                    if len(image_bytes) < 3000:
                        continue

                    ext = image_info.get("ext", "png").lower()
                    if ext == "jpg":
                        ext = "jpeg"

                    mime_type = f"image/{ext}"

                    image_description = describe_image_bytes(
                        image_bytes,
                        mime_type=mime_type,
                    )

                    if image_description.strip():
                        all_text.append(
                            f"\n--- Page {page_no} Image {image_no} Description ---\n"
                            f"{image_description}"
                        )

                except Exception as e:
                    all_text.append(
                        f"\n--- Page {page_no} Image {image_no} Error ---\n{str(e)}"
                    )

        doc.close()

        extracted_text = "\n".join(all_text)

        if not extracted_text.strip():
            return {
                "extracted_text": "",
                "status": "failed",
                "error": "No text extracted from PDF",
            }

        return {
            "extracted_text": extracted_text,
            "status": "pdf_extracted",
            "error": None,
        }

    except Exception as e:
        return {
            "extracted_text": "",
            "status": "failed",
            "error": str(e),
        }


def ppt_extractor_node(state: MainState) -> dict:
    try:
        file_path = state["file_path"]
        prs = Presentation(file_path)

        all_text = []

        for slide_no, slide in enumerate(prs.slides, start=1):
            slide_text = []

            for shape in slide.shapes:
                if hasattr(shape, "text") and shape.text.strip():
                    slide_text.append(shape.text)

            if slide_text:
                all_text.append(
                    f"\n--- Slide {slide_no} Text ---\n"
                    + "\n".join(slide_text)
                )

            for shape_no, shape in enumerate(slide.shapes, start=1):
                try:
                    if hasattr(shape, "image"):
                        image_bytes = shape.image.blob

                        if len(image_bytes) < 3000:
                            continue

                        ext = shape.image.ext or "png"
                        ext = ext.lower()

                        if ext == "jpg":
                            ext = "jpeg"

                        mime_type = f"image/{ext}"

                        image_description = describe_image_bytes(
                            image_bytes,
                            mime_type=mime_type,
                        )

                        if image_description.strip():
                            all_text.append(
                                f"\n--- Slide {slide_no} Image {shape_no} Description ---\n"
                                f"{image_description}"
                            )

                except Exception as e:
                    all_text.append(
                        f"\n--- Slide {slide_no} Image {shape_no} Error ---\n{str(e)}"
                    )

        extracted_text = "\n".join(all_text)

        if not extracted_text.strip():
            return {
                "extracted_text": "",
                "status": "failed",
                "error": "No text extracted from PPTX",
            }

        return {
            "extracted_text": extracted_text,
            "status": "ppt_extracted",
            "error": None,
        }

    except Exception as e:
        return {
            "extracted_text": "",
            "status": "failed",
            "error": str(e),
        }


def image_extractor_node(state: MainState) -> dict:
    try:
        file_path = state["file_path"]

        with open(file_path, "rb") as f:
            image_bytes = f.read()

        description = describe_image_bytes(image_bytes)

        if not description.strip():
            return {
                "extracted_text": "",
                "status": "failed",
                "error": "No text extracted from image",
            }

        return {
            "extracted_text": description,
            "status": "image_extracted",
            "error": None,
        }

    except Exception as e:
        return {
            "extracted_text": "",
            "status": "failed",
            "error": str(e),
        }


def doc_extractor_node(state: MainState) -> dict:
    try:
        file_path = state["file_path"]
        doc = Document(file_path)

        text = "\n".join(
            para.text for para in doc.paragraphs if para.text.strip()
        )

        if not text.strip():
            return {
                "extracted_text": "",
                "status": "failed",
                "error": "No text extracted from DOCX",
            }

        return {
            "extracted_text": text,
            "status": "doc_extracted",
            "error": None,
        }

    except Exception as e:
        return {
            "extracted_text": "",
            "status": "failed",
            "error": str(e),
        }


def txt_extractor_node(state: MainState) -> dict:
    try:
        file_path = state["file_path"]

        with open(file_path, "r", encoding="utf-8", errors="ignore") as f:
            text = f.read()

        if not text.strip():
            return {
                "extracted_text": "",
                "status": "failed",
                "error": "No text extracted from TXT",
            }

        return {
            "extracted_text": text,
            "status": "txt_extracted",
            "error": None,
        }

    except Exception as e:
        return {
            "extracted_text": "",
            "status": "failed",
            "error": str(e),
        }


def error_node(state: MainState) -> dict:
    return {
        "error": f"Error: {state.get('error', 'Unknown error occurred')}",
        "status": "failed",
    }