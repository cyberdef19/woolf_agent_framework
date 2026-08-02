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



#--------------------------------Сервіс хешування--------------------------------------------
class HashingService:
    
    def __init__(self, filepath: Path, algo: str):
        self._filepath = filepath
        self._algo = algo
    
    def hash_calculating(self) -> FileHashResult:
        """_summary_
        Обчислює криптографічне значення хеша (digest) для локального файла 
        Returns:
            FileHashResult: _description_
        """
        hasher = hashlib.new(self._algo)
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
                 timestamp=stat.st_ctime_ns,
                 tz=timezone.utc
             ),
             modified_at=datetime.fromtimestamp(
                 timestamp=stat.st_mtime,
                 tz=timezone.utc
             )
        )

from typing import Protocol

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
        return result_bytes.decode("ascii")

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
        result: str = ""
        decoder_type = codecs.getincrementaldecoder(
            self._encoding
        )
        decoder = decoder_type(errors="ignore")
        text = decoder.decode(
            data,
            final=False
        )
        for character in text:
            if self._is_accepted_character(character=character):
                result += character
                
        return result
        
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
                 mode: str
                 ):
        self._filepath = filepath
        self._encoding = encoding
        self._min_length = min_length
        self._max_length = max_length
        self._max_strings = max_strings
        self._mode = mode
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
            result.append(normalized_extracted_string)
            
        return ExtractedStringsResult(
            filepath=self._filepath,
            strings=result
        )
        
                    
        
    
    def _normalize_extracted_strings(self, values: list[str]) -> list[str]:
        """Нормалізація, дедублікація та лімітація виятгнутого рядка"""

        unique_values: dict[str, None] = {}

        for raw_value in values:
            value = raw_value.strip()

            if len(value) < self._min_length:
                continue

            if self.max_length is not None:
                value = value[:self._max_length]

            if not value:
                continue

            unique_values.setdefault(value, None)

            if len(unique_values) >= self._max_strings:
                break

        return list(unique_values)

#------------------------------------Сервіс отримання підозрілих індикторів---------------------------------------
        

    


        