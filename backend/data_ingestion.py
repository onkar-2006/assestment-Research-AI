import os
from typing import List
from langchain_core.documents import Document
from langchain_docling import DoclingLoader
from langchain_docling.loader import ExportType
from docling.chunking import HybridChunker
from docling.document_converter import DocumentConverter, PdfFormatOption
from docling.datamodel.pipeline_options import PdfPipelineOptions
from docling.datamodel.base_models import InputFormat
from dotenv import load_dotenv

load_dotenv()

class DocumentIngestor:
    def __init__(self, embed_model_id: str = "sentence-transformers/all-MiniLM-L6-v2"):
        pipeline_options = PdfPipelineOptions()
        pipeline_options.do_ocr = False 
        pipeline_options.do_table_structure = False  
        
        self.converter = DocumentConverter(
            format_options={
                InputFormat.PDF: PdfFormatOption(pipeline_options=pipeline_options)
            }
        )

        self.chunker = HybridChunker(tokenizer=embed_model_id)
        self.export_type = ExportType.DOC_CHUNKS

    def ingest(self, file_source: str) -> List[Document]:
        print(f" Start Ingesting: {file_source}")

        loader = DoclingLoader(
            file_path=file_source,
            export_type=self.export_type,
            chunker=self.chunker,
            converter=self.converter 
        )
        
        docs = loader.load()
        
        print(f" Successfully created {len(docs)} smart chunks.")

        filename = os.path.basename(file_source)
        for doc in docs:
            doc.metadata["source_file"] = filename
        return docs

