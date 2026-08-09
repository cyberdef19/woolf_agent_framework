from langchain_core.tools import tool
from pathlib import Path
from src.woolf_agents.domains.artifacts.schemas.contracts import (
    MetadataFileInput,
    MetadataLevel,
    MetadataFileResult,
    FileHashResult,
    CalculateHashInput,
    HashAlgorithm,
    ExtractedStringsResult,
    ExtractStringsInput,
    TextEncoding
)
from src.woolf_agents.domains.artifacts.services.services import(
    MetadataService,
    HashingService,
    ExtractStringsService
)
from pydantic import ValidationError

@tool(args_schema=MetadataFileInput)
def get_metadata_local_file(artifact_path: Path, metadata_level:MetadataLevel = MetadataLevel.BASIC)->dict[str, object]:
    """_summary_
       Виконує екстракцію метаданих з локального файла
    Args:
        pathfile (Path): _description_ - шлях до локального файла в операційній системі
        metadata_level (MetadataLevel, optional): _description_. Defaults to MetadataLevel.BASIC. - рівень отримання
        метаданих, за замовчуванням MetadataLevel.Basic
    
    Returns:
        dict[str, object]: _description_ - повертає дамп моделі у режимі json
    """

    try:
        service: MetadataService = MetadataService(filepath=artifact_path)
        result:MetadataFileResult = service.extract_metadata()
       
    except ValidationError as ex:
        raise 
    except Exception as ex:
        raise
    print("End Metadata")
    return result.model_dump(mode="json")

    
@tool(args_schema=CalculateHashInput)
def hashing_local_file(artifact_path:Path, algorithm: HashAlgorithm)->dict[str, object]:
    """_summary_
        Виконує обчислення хеша локального файла
    Args:
        path_file (Path): _description_ - шлях до локального файла в операційній системі
        algorithm (HashAlgorithm): _description_ - алгоритм хешування

    Returns:
        dict[str, object]: _description_ - повертає дамп моделі в режимі json
    """
    print("Start Hashing")
    try:
            service: HashingService = HashingService(filepath=artifact_path, algo=algorithm)
            result:FileHashResult = service.hash_calculating()
            
    except ValidationError as ex:
            raise 
    except Exception as ex:
            raise
    print("End Hashing")
    return result.model_dump(mode="json")


@tool(args_schema=ExtractStringsInput)
def extract_strings_local_file(artifact_path:Path, encoding:TextEncoding, max_length:int, min_length:int, max_strings:int)->dict[str, object]:
    """_summary_
        Отримує наявні рядки у файлі. Може використовувати різні алгоритми
    Args:
        path_file (Path): _description_  - шлях до локального файла в операційній системі 
        encoding (TextEncoding): _description_ - режим кодування рядків
        max_length (int): _description_  - максимальна довжина рядка
        min_length (int): _description_ - мінімальна довжина рядка
        max_strings (int): _description_ - максимальна кількість рядків до отримання

    Returns:
        dict[str, object]: _description_ - повертає дамп моделі в режимі json
    """
    print("Extract Data")
    try:
            service: ExtractStringsService = ExtractStringsService(
                filepath=artifact_path,
                encoding=encoding,
                max_length=max_length,
                min_length=min_length,
                max_strings=max_strings
                )
            result:ExtractedStringsResult = service.extract_strings()
                
    except ValidationError as ex:
            raise 
    except Exception as ex:
            raise
    return result.model_dump(mode="json")
        