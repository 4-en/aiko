import os
import abc
from pathlib import Path
from typing import Union, Type, Dict
from io import BytesIO

import pdfplumber
import docx
import textract
from odf.opendocument import load as odt_load
from odf.text import P


class DocumentLoader(abc.ABC):
    """Abstract base class for document loaders."""

    @abc.abstractmethod
    def load(self, file_path: Union[str, Path]) -> str:
        """Load the contents of the document as a string."""
        pass


class TextLoader(DocumentLoader):
    """Loader for plain text (.txt, .md) files."""

    def load(self, file_path: Union[str, Path]) -> str:
        with open(file_path, "r", encoding="utf-8") as f:
            return f.read()


class RTFLoader(DocumentLoader):
    """Loader for RTF files."""

    def load(self, file_path: Union[str, Path]) -> str:
        try:
            import striprtf  # Requires `striprtf` package
            with open(file_path, "r", encoding="utf-8") as f:
                return striprtf.striprtf(f.read())
        except ImportError:
            raise ImportError("striprtf is required to parse RTF files. Install it with 'pip install striprtf'")


class PDFLoader(DocumentLoader):
    """Loader for PDF files."""

    def load(self, file_path: Union[str, Path]) -> str:
        text = ""
        with pdfplumber.open(file_path) as pdf:
            for page in pdf.pages:
                text += page.extract_text() + "\n"
        return text.strip()


class DocxLoader(DocumentLoader):
    """Loader for DOCX files."""

    def load(self, file_path: Union[str, Path]) -> str:
        doc = docx.Document(file_path)
        return "\n".join([para.text for para in doc.paragraphs])


class DocLoader(DocumentLoader):
    """Loader for DOC files using textract."""

    def load(self, file_path: Union[str, Path]) -> str:
        return textract.process(str(file_path)).decode("utf-8")


class ODTLoader(DocumentLoader):
    """Loader for ODT files."""

    def load(self, file_path: Union[str, Path]) -> str:
        odt_doc = odt_load(file_path)
        text = "\n".join([elem.firstChild.data for elem in odt_doc.getElementsByType(P) if elem.firstChild])
        return text


class DefaultLoader(DocumentLoader):
    """Default loader that attempts to read unknown file types as text."""

    def load(self, file_path: Union[str, Path]) -> str:
        try:
            with open(file_path, "r", encoding="utf-8") as f:
                return f.read()
        except UnicodeDecodeError:
            raise ValueError(f"Cannot read {file_path} as text. Possibly binary data.")


class DocumentLoaderRegistry:
    """Registry for document loaders to enable easy extensibility."""
    _loaders: Dict[str, Type[DocumentLoader]] = {}

    @classmethod
    def register_loader(cls, extension: str, loader_cls: Type[DocumentLoader]):
        cls._loaders[extension.lower()] = loader_cls

    @classmethod
    def get_loader(cls, file_path: Union[str, Path]) -> DocumentLoader:
        ext = os.path.splitext(file_path)[-1].lower()
        return cls._loaders.get(ext, DefaultLoader)()


# Register default loaders
DocumentLoaderRegistry.register_loader(".txt", TextLoader)
DocumentLoaderRegistry.register_loader(".md", TextLoader)
DocumentLoaderRegistry.register_loader(".rtf", RTFLoader)
DocumentLoaderRegistry.register_loader(".pdf", PDFLoader)
DocumentLoaderRegistry.register_loader(".docx", DocxLoader)
DocumentLoaderRegistry.register_loader(".doc", DocLoader)
DocumentLoaderRegistry.register_loader(".odt", ODTLoader)


def load_document(file_path: Union[str, Path]) -> str:
    """Load document content using the appropriate loader."""
    loader = DocumentLoaderRegistry.get_loader(file_path)
    return loader.load(file_path)


if __name__ == "__main__":
    test_file = "example.pdf"  # Replace with a real file
    try:
        content = load_document(test_file)
        print(content)
    except Exception as e:
        print(f"Error loading document: {e}")
