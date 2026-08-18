import hashlib
import mimetypes
import unicodedata
import codecs
from src.woolf_agents.domains.artifacts.schemas.contracts import(
                                         FileHashResult, 
                                         MetadataFileResult,
                                         ExtractedStringsResult,
                                         TextEncoding
                                         )  
from pathlib import Path
from datetime import datetime, timezone
from collections.abc import Iterable
from typing import Protocol
from src.woolf_agents.domains.artifacts.schemas.contracts import HashAlgorithm
from langchain_core.documents import Document
from src.woolf_agents.infrastructure.vectorstore.contracts import VectorStoreProvider
from langchain_text_splitters import (
    RecursiveCharacterTextSplitter,
)
from langchain_community.document_loaders import (
    PyPDFLoader,
    TextLoader,
)
from tqdm import tqdm





#--------------------------------Сервіс хешування--------------------------------------------
class HashingService:
    
    def __init__(self, filepath: Path, algo: HashAlgorithm):
        self._filepath = filepath
        self._algo = algo
    
    def hash_calculating(self) -> FileHashResult:
        """_summary_
        Обчислює криптографічне значення хеша (digest) для локального файла 
        Returns:
            FileHashResult: _description_
        """
        hasher = hashlib.new(self._algo.value)
        processed_bytes = 0
        
        with open(self._filepath, "rb") as stream:
            for chunk in iter(lambda: stream.read(64*1024), b""):
                hasher.update(chunk)
                processed_bytes += len(chunk)
        return FileHashResult(
             algorithm=self._algo,
             filepath=self._filepath,
             value=hasher.hexdigest(),
             processed_bytes=processed_bytes
        )
#-------------------------------------------Сервіс отримання метаданих---------------------------------
class MetadataService:
    
    def __init__(self, filepath: Path):
        self._filepath = filepath
    
    def extract_metadata(self) ->MetadataFileResult:
        """Отримання метаданих з локального файла"""
        stat = self._filepath.stat()
        mime_type, _ = mimetypes.guess_type(self._filepath.name)
        
        return MetadataFileResult(
             filepath=self._filepath,
             filename=self._filepath.name,
             filesize_bytes=stat.st_size,
             extension=self._filepath.suffix.lower() or None,
             mimetype=mime_type,
             created_at=datetime.fromtimestamp(
                 timestamp=stat.st_ctime,
                 tz=timezone.utc
             ),
             modified_at=datetime.fromtimestamp(
                 timestamp=stat.st_mtime,
                 tz=timezone.utc
             )
        )



#---------------------------------------------Сервіс вилучення рядків з файла----------------------------------
class StringExtractionStrategy(Protocol):
    """Contract for extracting printable strings from binary data."""

    def extract(
        self,
        data: bytearray,
    ) -> str:
        """Extract printable strings from binary data."""
        ...



class AsciiStringExtractionStrategy:
    """Extract contiguous printable ASCII strings from binary data.""" 
    
    def __init__(self):
        self._MIN_PRINTABLE_BYTE = 0x20
        self._MAX_PRINTABLE_BYTE = 0x7E       

    def _is_printable(self, value: int)->bool:
        return  value >= self._MAX_PRINTABLE_BYTE and value <= self._MAX_PRINTABLE_BYTE
    
    def extract(self, data: bytearray) ->str:
        result_bytes: bytearray = []
        for ibyte in data:
            if self._is_printable(ibyte):
                result_bytes.append(ibyte)
        return result_bytes.decode("ascii").splitlines()

class UnicodeStringExtractorStrategy:
    
    def __init__(self, encoding: str):
        self._encoding = encoding  
    
    @staticmethod
    def _is_accepted_character(character: str) -> bool:
        if character in {"\t", "\n", "\r"}:
            return False

        return not unicodedata.category(
            character
        ).startswith("C")    
    
    def extract(self, data: bytearray)->str:
        results: list[str] = []
        decoder_type = codecs.getincrementaldecoder(
            self._encoding
        )
        decoder = decoder_type(errors="ignore")
        texts = decoder.decode(
            data,
            final=False
        ).splitlines()
        for text in texts:
            result: str = ""
            for character in text:
                if self._is_accepted_character(character=character):
                    result += character
            results.append(result)
                
        return results
        
class StringExtractionStrategyRegistry:
    
    def __init__(self, strategies: dict[TextEncoding, StringExtractionStrategy]):
        self._strategies = strategies
    
    def get(self, encoding: TextEncoding) -> StringExtractionStrategy:
        try:
            return self._strategies.get(encoding)
        except KeyError as ex:
            raise ValueError(f"Невірний ключ {str(ex)}")
           
    
class ExtractStringsService:
    
    def __init__(self, 
                 filepath: Path,
                 encoding: TextEncoding,
                 min_length: int,
                 max_length: int,
                 max_strings: int,
                
                 ):
        self._filepath = filepath
        self._encoding = encoding
        self._min_length = min_length
        self._max_length = max_length
        self._max_strings = max_strings
        #self._mode = mode
        self._DEFAULT_BATCH_SIZE = 64 * 1024
        self._strategy_registry: StringExtractionStrategyRegistry = StringExtractionStrategyRegistry(
            {
                TextEncoding.ASCII:AsciiStringExtractionStrategy(),
                TextEncoding.UTF8: UnicodeStringExtractorStrategy("utf-8"),
                TextEncoding.UTF16_BE: UnicodeStringExtractorStrategy("utf-16-be"),
                TextEncoding.UTF16_LE: UnicodeStringExtractorStrategy("utf-16-le")
            }
        ) 
    
    def _read_chunks(self)->Iterable[bytes]:
           with open(self._filepath, "rb") as stream:
               while chunk := stream.read(self._DEFAULT_BATCH_SIZE):
                   yield chunk        
     
                   
    def extract_strings(self) -> ExtractedStringsResult:
        """Вибір стратегії та витягування рядків"""
        result: list[str] = []
        
        strategy = self._strategy_registry.get(encoding=self._encoding)   
        for chunk in self._read_chunks():
            extracted_strings = strategy.extract(bytearray(chunk))
            normalized_extracted_string = self._normalize_extracted_strings(extracted_strings)
            result.extend(normalized_extracted_string)
        print(result)  
        return ExtractedStringsResult(
            filepath=self._filepath,
            strings=result
        )
        
                    
        
    
    def _normalize_extracted_strings(self, values: list[str]) -> list[str]:
        """Нормалізація, дедублікація та лімітація витягнутого рядка"""

        unique_values: dict[str, None] = {}

        for raw_value in values:
            value = raw_value.strip()

            if len(value) < self._min_length:
                continue

            if self._max_length is not None:
                value = value[:self._max_length]

            if not value:
                continue

            unique_values.setdefault(value, None)

            if len(unique_values) >= self._max_strings:
                break

        return list(unique_values)

#------------------------------------Сервіс отримання підозрілих індикторів---------------------------------------
        
class HistoricalRetrieverService:
    
    def __init__(self, vector_store: VectorStoreProvider):
        self._vector_store = vector_store
    
    async def search(self, query: str, top_k: int) -> list[Document]:
        return await self._vector_store.similarity_search(query=query, top_k=top_k)
    
    async def add_documents(self, documents: list[Document], ids:list)->list[str]:
        return await self._vector_store.add_documents(documents=documents, ids=ids)
    


class HistoricalIngestionService:
    def __init__(self, vector_store, chunk_size: int = 1000, chunk_overlap: int = 150) -> None:
        self._vector_store = vector_store

        self._splitter = RecursiveCharacterTextSplitter(
            chunk_size=chunk_size,
            chunk_overlap=chunk_overlap,
        )

    def _load_file( self, file_path: Path) -> list[Document]:

        suffix = file_path.suffix.lower()

        if suffix == ".pdf":
            loader = PyPDFLoader(str(file_path))

        elif suffix in {".txt", ".md"}:
            loader = TextLoader(
                str(file_path),
                encoding="utf-8",
            )

        else:
            raise ValueError(
                f"Unsupported file type: {suffix}"
            )

        return loader.load()

    async def ingest_source(self, file_path: Path, source_metadata: dict) -> list[str]:

        documents = self._load_file(file_path)

        chunks = self._splitter.split_documents(
            documents
        )

        source_id = source_metadata["source_id"]

        for index, chunk in enumerate(chunks):
            chunk.metadata.update(
                source_metadata
            )

            chunk.metadata["chunk_index"] = index

        ids = [
            f"{source_id}_chunk_{index:04d}"
            for index in range(len(chunks))
        ]

        return await self._vector_store.add_documents(
            documents=chunks,
            ids=ids,
        )


async def ingest_all_sources(
    service: HistoricalIngestionService,
    sources: dict,
    base_dir: Path,
) -> None:

    for source_id, metadata in tqdm(sources.items()):

        file_path = (
            base_dir
            / metadata["file_name"]
        )

        await service.ingest_source(
            file_path=file_path,
            source_metadata={
                "source_id": source_id,
                **metadata,
            },
        )
        
    


        