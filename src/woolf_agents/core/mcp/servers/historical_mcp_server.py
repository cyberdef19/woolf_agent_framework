from src.woolf_agents.core.mcp.providers.langchain_tool_provider import LangchainToolProvider
from src.woolf_agents.core.mcp.servers.base_server import BaseFastMCP
from src.woolf_agents.tools.retriever_tools import retrieve_historical_sources, get_adjacent_chunks, search_related_sources
from src.woolf_agents.tools.web_retriever_tools import search_web_historical_sources
from typing import Annotated
from pydantic import Field


class HistoricalMCPServer(BaseFastMCP):
    
    def __init__(self, 
                 name, 
                 instructions
                 ):
        super().__init__(
            name, 
            instructions
            )
    
    def _register_prompts(self):
        @self._mcp.prompt()
        def verification_sources(user_task: str, research_result: str, methodology: str) ->str:
            """Формує інструкцію для верифікації джерельної бази отриманої відповіді"""
            return f"""
                Перевір доказову базу результату дослідження.
                
                Перевір за методологією:
                {methodology}

                Завдання користувача:
                {user_task}

                Результат дослідження:
                {research_result.model_dump_json()}

                Використовуй доступні інструменти лише для перевірки
                контексту джерел та пов'язаних джерел.
                """
        
        
        @self._mcp.prompt()
        def critical_review(user_task: str, research_result: str) -> str:
            """
            Формує інструкцію для критичної оцінки результату
            історичного дослідження.
            """
            return f"""
            Надай критичну оцінку отриманому результату відповіді
            на завдання користувача.

            ЗАВДАННЯ КОРИСТУВАЧА:
            {user_task}

            РЕЗУЛЬТАТ ДОСЛІДЖЕННЯ:
            {research_result}

            Оціни результат за такими критеріями:

            1. Наскільки відповідь відповідає завданню користувача.
            2. Чи ґрунтуються ключові висновки на представлених доказах.
            3. Чи немає тверджень, сила яких перевищує силу наявних доказів.
            4. Чи присутні суперечності або логічні прогалини.
            5. Чи чітко відокремлені факти, інтерпретації та гіпотези.
            6. Чи зазначена невизначеність там, де доказів недостатньо.

            Не проводь нове дослідження.
            Не шукай нові джерела.
            Ти виконуєш роль критика вже отриманого результату.
            """
    
    def _register_resources(self):
        @self._mcp.resource("heritage://research/methodology")
        def research_methodology() -> str:
            """
            Методологія проведення історичних досліджень у системі Heritage.
            """
            return """
            МЕТОДОЛОГІЯ ІСТОРИЧНОГО ДОСЛІДЖЕННЯ HERITAGE

            1. Робота з історичними джерелами

            Перевага надається первинним історичним джерелам, якщо вони доступні.
            Вторинні джерела використовуються для доповнення, інтерпретації та
            зіставлення інформації.

            2. Розмежування фактів та інтерпретацій

            Необхідно чітко розрізняти:
            - факти, безпосередньо підтверджені джерелами;
            - твердження авторів джерел;
            - історичні інтерпретації;
            - дослідницькі гіпотези;
            - припущення, для яких недостатньо доказів.

            3. Перевірка доказів

            Важливі твердження повинні перевірятися за кількома незалежними
            джерелами, якщо такі джерела доступні. Збіг інформації у незалежних
            джерелах підвищує рівень її достовірності.

            4. Оцінювання джерел

            Під час використання історичного джерела необхідно враховувати:
            - його походження;
            - авторство;
            - час створення;
            - історичний контекст;
            - можливу упередженість автора;
            - мету створення джерела;
            - надійність та повноту представленої інформації.

            5. Суперечності між джерелами

            Суперечлива інформація не повинна автоматично відкидатися.
            Необхідно зафіксувати суперечність, порівняти відповідні джерела
            та визначити можливі причини розбіжностей.

            6. Робота з гіпотезами

            Історична гіпотеза повинна оцінюватися на основі доступних доказів.
            Необхідно враховувати як докази, що підтримують гіпотезу, так і
            докази, що їй суперечать.

            7. Формування висновків

            Висновки повинні ґрунтуватися на проаналізованих джерелах і доказах.
            Заборонено представляти непідтверджені припущення або гіпотези як
            встановлені історичні факти.

            8. Невизначеність

            Якщо наявних доказів недостатньо для надійного висновку, це повинно
            бути явно зазначено у результатах дослідження. Система не повинна
            заповнювати прогалини у доказах вигаданими фактами.

            9. Простежуваність

            Ключові твердження та висновки повинні, наскільки це можливо,
            бути пов'язані з джерелами та доказами, на яких вони ґрунтуються.

            10. Принцип обережності

            Сила сформульованого висновку не повинна перевищувати силу наявних
            історичних доказів.
            """
        
    def _register_providers(self):
        """Реєструє локального провайдера з інструментами"""
        @self._mcp.tool
        async def retrieve_sources( 
                                   query: Annotated[str, Field(min_length=1, max_length=500)],
                                   top_k: Annotated[int, Field(ge=1, le=20)] = 5
                                   ):
            """ Виконує семантичний пошук історичних літературних праць

            Args:
                query (str): Пошуковий запит 
                top_k (int, optional): Defaults to 5. Максимальна кількість знайдених джерел

            Returns:
                _type_: Повертає результат retrieve_historical_sources
            """            
            return await retrieve_historical_sources.ainvoke(
                        {
                            "query": query,
                            "top_k": top_k
                        }
            )
        
        @self._mcp.tool
        async def adjucent_chunks(
                             source_id: Annotated[str, Field(min_length=1, max_length=200)], 
                             chunk_index: Annotated[int, Field(ge=0)], 
                             before: Annotated[int, Field(ge=0, le=10)] = 1, 
                             after: Annotated[int, Field(ge=0, le=10)] = 1,
                             ):
            """ Отримує чанки знайдених документів

            Args:
                source_id (str):    ідентифікатор історичного джерела
                chunk_index (int):  індекс чанка 
                before (int, optional): Defaults to 1. Кількість чанків перед цільовим
                after (int, optional): Defaults to 1. Кількість чанків після цільового

            Returns:
                _type_: Повертає результат інструменту get_adjucent_chunks
            """            
            return await get_adjacent_chunks.ainvoke(
                {
                    "source_id":source_id,
                    "chunk_index": chunk_index,
                    "before": before,
                    "after": after
                }
            )
        @self._mcp.tool
        async def search_source_related( 
                                        source_id: Annotated[str, Field(min_length=1, max_length=200)], 
                                        chunk_index: Annotated[int, Field(ge=0)], 
                                        top_k: Annotated[int, Field(ge=1, le=20)] = 5
                                        ):
            """ Здійснює пошук пов'язаних з документом source_id документів

            Args:
                source_id (str):   ідентифікатор документа джерела
                chunk_index (int):  ідентифікатор чанка
                top_k (int, optional): Defaults to 5. Максимальна кількість джерел

            Returns:
                _type_: Повертає результат інструмента search_related_sources
            """            
            return await search_related_sources.ainvoke(
                {
                    "source_id":source_id,
                    "chunk_index": chunk_index,
                    "top_k": top_k
                }
            )
        
        @self._mcp.tool
        async def search_web_historical( 
                                        query: Annotated[str, Field(min_length=1, max_length=500)], 
                                        max_results: Annotated[int, Field(ge=1, le=20)] = 5
                                        ):
            """Здійснює пошук історичних джерел в мережі Інтернет

            Args:
                query (str): Пошуковий запит до Tavily
                max_results (int, optional): Defaults to 5. Максимальна кількість результатів

            Returns:
                _type_: Повертає результат інструмента search_web_historical_sources
            """            
            return await search_web_historical_sources.ainvoke(
                {
                    "query":query,
                    "max_results":max_results
                }
            )
        
        
        
