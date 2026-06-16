from pathlib import Path
from graph.state import MainState


SUPPORTED_FILE_TYPES = {
    ".pdf": "pdf",
    ".ppt": "ppt",
    ".pptx": "ppt",
    ".txt": "txt",
    ".md": "txt",
    ".png": "image",
    ".jpg": "image",
    ".jpeg": "image",
    ".webp": "image",
}


def detect_file_type_node(state: MainState) -> dict:
    try:
        if not state.get("is_file"):
            return {
                "status": "failed",
                "error": "No file found",
            }

        file_name = state.get("file_name")
        file_path = state.get("file_path")

        if not file_name and not file_path:
            return {
                "status": "failed",
                "error": "file_name or file_path is required",
            }

        name_or_path = file_name or file_path
        ext = Path(name_or_path).suffix.lower()

        file_type = SUPPORTED_FILE_TYPES.get(ext)

        if file_type is None:
            return {
                "status": "failed",
                "error": f"Unsupported file type: {ext}",
            }

        return {
            "file_type": file_type,
            "status": "file_type_detected",
            "error": None,
        }

    except Exception as e:
        return {
            "status": "failed",
            "error": str(e),
        }


def route_extractor(state: MainState) -> str:
    if state.get("status") == "failed":
        return "error"

    file_type = state.get("file_type")

    if file_type == "pdf":
        return "pdf"

    if file_type == "ppt":
        return "ppt"

    if file_type == "txt":
        return "txt"

    if file_type == "image":
        return "image"

    return "error"