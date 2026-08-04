from tests.unit.test_case import AgentTestCase, TestExpectation

TEST_CASES = [
    AgentTestCase(
        case_id="metadata_only",
        input_query=(
            "Отримай лише метадані файла "
            "samples/sample.bin."
        ),
        expected_result=(
            "Агент повинен викликати лише інструмент "
            "отримання метаданих і повернути відомості "
            "про файл."
        ),
        expectation=TestExpectation(
            required_tools=(
                "get_file_metadata",
            ),
            forbidden_tools=(
                "calculate_hash",
                "extract_strings",
                "extract_indicators",
            ),
            expected_status="completed",
        ),
    ),
    AgentTestCase(
        case_id="sha256_hash",
        input_query=(
            "Обчисли SHA-256 файла "
            "samples/sample.bin."
        ),
        expected_result=(
            "Агент повинен викликати calculate_hash "
            "з алгоритмом SHA-256."
        ),
        expectation=TestExpectation(
            required_tools=(
                "calculate_hash",
            ),
            expected_status="completed",
            expected_content=(
                "sha256",
            ),
        ),
    ),
    AgentTestCase(
        case_id="extract_strings",
        input_query=(
            "Витягни читабельні текстові рядки з файла "
            "samples/sample.bin."
        ),
        expected_result=(
            "Агент повинен використати інструмент "
            "витягування рядків."
        ),
        expectation=TestExpectation(
            required_tools=(
                "extract_strings",
            ),
            expected_status="completed",
        ),
    ),
    AgentTestCase(
        case_id="detect_indicators",
        input_query=(
            "Знайди потенційні IP, URL, домени та email "
            "у файлі samples/sample.bin."
        ),
        expected_result=(
            "Агент повинен виконати пошук індикаторів "
            "і не називати їх підтверджено шкідливими."
        ),
        expectation=TestExpectation(
            required_tools=(
                "extract_indicators",
            ),
            expected_status="completed",
        ),
    ),
    AgentTestCase(
        case_id="full_analysis",
        input_query=(
            "Проведи первинний аналіз файла "
            "samples/sample.bin: отримай метадані, "
            "SHA-256, рядки та потенційні індикатори."
        ),
        expected_result=(
            "Агент повинен використати всі чотири "
            "інструменти й сформувати структурований звіт."
        ),
        expectation=TestExpectation(
            required_tools=(
                "get_file_metadata",
                "calculate_hash",
                "extract_strings",
                "extract_indicators",
            ),
            expected_status="completed",
        ),
    ),
]