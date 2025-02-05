import uuid
from pathlib import Path

# Create uploads directory if it doesn't exist
UPLOAD_DIRECTORY = Path("/tmp/uploads")
UPLOAD_DIRECTORY.mkdir(parents=True, exist_ok=True)


def save_uploaded_file(uploaded_file):
    """
    Save the uploaded file to a unique filename in the uploads directory.

    :param uploaded_file: Uploaded file object
    :return: Path to the saved file
    """
    random_filename = f"{uuid.uuid4()}.tar.gz"
    file_path = UPLOAD_DIRECTORY / random_filename

    with open(file_path, "wb") as f:
        f.write(uploaded_file.getbuffer())
    return file_path
