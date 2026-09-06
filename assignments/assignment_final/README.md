
Щоб запустити програму потрібно у режимі фінального домашнього завдання слід прослідкувати у VisualStudio Code наявність launch.json з наступним вмістом:
{
    "version": "0.2.0",
    "configurations": [
        {
            "name": "Debug Assignment Final",
            "type": "debugpy",
            "request": "launch",
            "program": "${workspaceFolder}/assignments/assignment_final/main.py",
            "cwd": "${workspaceFolder}",
            "env": {
                "PYTHONPATH": "${workspaceFolder}"
            },
            "console": "integratedTerminal",
            "justMyCode": true
        }
    ]
} 

Запуск програми відбувається через файл assignments\assinment_final\main.py.

Базовий рівень:
Створено мультиагентну систему, ядро якої складає агент планувальник MultiAgentPlannerExecuteGraph - агент планувальник з виконавцем та перепланувальником. Графовий агент, вузлами якого є планувальник, виконавець, перпланувальник та частина технічних вузлів для інкремента кроків виконання плану, підготовки структурованої відповіді тощо. Планувальник створює план для виконання завдання користувача. План звичайно невеликий. Після створення плану, план покроково передається для виконання у вузол виконавець, який делегує виконання кроків воркерам, що намагаються виконати поставлене кроком плана завдання. Один з воркерів (ToolCallingWarker) викликає ще одного агента (ToolCallingGraph), що є ReAct-агентом і своєму циклі пропонує JSON-схеми доступних інструментів до виклику runtime системою. Як і агент планувальник, так ReAct-агент є графовими агентами. ToolCallingGraph складається здебільшого з технічних вузлів. Основну роботу з мовною моделлю виконують вузли agent_node та structured_output_node. Увесь цикл агента "крутиться" по вузлам ToolCallingGraph. 

Основу виклику мовних моделей для будь-якого агента у системі, окрім агента SourceVerificatioAgent сладає клас LLMExecutor, який надає уніфікований засіб для виклику моделей з різним типом запитів, включаючи необхідність формування structured_output відповіді. Для реалізації роботи планувальника використвуються декілька воркерів, котрі також отримують доступ до можливостей llm через LLMExecutor - це воркери для виконання оцінки виконання кроку плану, оцінка виконання плану загалом та reasonning-воркер, основобю завдання якого є "розмірковування" над кроком плана, а також воркер для формування завершальної відповіді (StructuredOutputWorker).

Для виконання завдання у ToolCallingWorker є у наявності декілька інструментів: три для роботи з локальною векторною базою на основі Хрома, хоча в майбутньому можна буде підключити різні провайдери сховищ, створено фабрику таких сховищ. Інший інструмент для пошуку документів у мережі інтернет - поки що тільки через Tavily. У локальній базі зберігаються (поки лише 11 документів історичних джерел) документи, на основі яких система має перевіряти існуючі гіпотези і обирати найбільш імовірну, базуючися на реальних історичних фактах з існуючих історичних літературних джерел. У майбітньому таких джерел буде значно більше.

Також, створено фабрику різних типів різновидів мовних моделей, які можна підключити до системи, маючи API_KEY через OpenRouter.

Дане ядро працює у складі більшої агентної системи MASResearchGraph - який також є графом, який компілюється разом з ярдом інших агентів, включаючи MultiAgentPlannerExecuteGraph, а також агент CriticalDesicion і SourceVerificationAgent та HistoricalSuperviser. Саме MASResearchGraph запускає у роботу усі ці компоненти,Ю а маршрутизає виконання компонентів HistoricalSuperviser - як супервайзер системи. Якщо MultiAgentPlannerExecuteGraph разом з залежним від нього ToolCallingGpaph створює план для виконання завдання користувача, оцінює кроки виконання, формує завершальну відповідь на завдання, то CriticalDesicion - є критиком і намагається знайти критику для отриманої відповіді. У той же час SourceVerificationAgent - створений за принципом готового агента langchain з власним внутрішнім циклом - намагається верифікувати достовірність джерельної бази для отриманої відповіді. Цей агент, як і ToolCallingGraph отримав власні інструменти. Однак якщо у ToolCallingGraph їх 4, то у SourceVerificationAgent - всього 2. 

В системі використовується Sqlite Saver checkpointer, використовується на рівні MASResearchGraph. На рівні ядра системи MultiAgentPlannerExecuteGraph також використовує Sqlite Saver checkpointer. На скрінах продемонстровано persistance для MASResearchGraph. При незмінному thread_id відбувається крах системи (переривання режиму отладки) і запуск системи з місця збереження по скріншоту.
В системі також працює TrajectoryLogger, котрий дозволяє логувати виконання завдання кожним вузлом. В систему інтегровано MCP-сервер на основі FastMCP. Він наслідується від базового абстрактного класу, який надає до реалізації методи реєстрації інструментів, промптів, ресурсів, а також захисних механізмів сервера. Поки що ланцюжок захисту на сервері виглядає наступним чином:

  ErrorHandlingMiddleware(
                include_traceback=eha.include_traceback,
                transform_errors=eha.transform_errors
            )
        )
  #формує структуровані json логи
  self._mcp.add_middleware(
        StructuredLoggingMiddleware()
   )
   #реєструє помилки
    self._mcp.add_middleware(
         AuditMiddleware()
 )
    rla = RateLimittingArgs()
    #контролює частоту запитів
    self._mcp.add_middleware(
    RateLimitingMiddleware(
                max_requests_per_second=rla.max_requests_per_sec,
                burst_capacity=rla.burst_capacity
            )
        )

class BaseFastMCP(ABC):
    
    def __init__(self, name: str, instructions: str):
        
        self._mcp = FastMCP(
            name=name,
            instructions=instructions
        )
        
        self._register_core_middlewares()
        self._register_providers()
        self._register_prompts()
        self._register_resources()
    
    @property
    def mcp(self)->FastMCP:
        return self._mcp
           
    @abstractmethod 
    def _register_resources(self)->None:
        ...
    
    @abstractmethod
    def _register_prompts(self) -> None:
        ...
    
    def _register_core_middlewares(self)->None:
        """Реєструє middlware рівні"""
        #перехоплює виключення будь-якого внутрішнього шару
        eha = ErrorHandlingArgs()
        self._mcp.add_middleware(
            ErrorHandlingMiddleware(
                include_traceback=eha.include_traceback,
                transform_errors=eha.transform_errors
            )
        )
        #формує структуровані json логи
        self._mcp.add_middleware(
            StructuredLoggingMiddleware()
        )
        #реєструє помилки
        self._mcp.add_middleware(
            AuditMiddleware()
        )
        rla = RateLimittingArgs()
        #контролює частоту запитів
        self._mcp.add_middleware(
            RateLimitingMiddleware(
                max_requests_per_second=rla.max_requests_per_sec,
                burst_capacity=rla.burst_capacity
            )
        )
    
    
    @abstractmethod
    def _register_providers(self) -> None:
        ...

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
                {research_result}

                Використовуй доступні інструменти лише для перевірки
                контексту джерел та пов'язаних джерел. 
                Інструмент search_related_sources використовуй для пошуку у локальній базі.
                Не використовуй його для пошуку в мережі інтернет. 
                Не веди пошук усіх джерел. Достатньо отримати 3 документи для підтвердження.
                
                Правила: 
                -Висновок формуй на основі знайдених історичних документів.
                -Заборонено викликати доступні тобі інструменти більше 3 разів.
                
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

Також, створено 6 тестів і створено демонстрацію на 3 запити, які перебираються у циклі. Реалізовано також HITL у системі як на рівні ядра так і на рівні MASResearchGraph.

Список mcp-інструментів

retrieve_sources

            Виконує семантичний пошук історичних літературних праць

            Args:
                query (str): Пошуковий запит 
                top_k (int, optional): Defaults to 5. Максимальна кількість знайдених джерел

            Returns:
                _type_: Повертає результат retrieve_historical_sources
                        
        
adjucent_chunks
            Отримує чанки знайдених документів

            Args:
                source_id (str):    ідентифікатор історичного джерела
                chunk_index (int):  індекс чанка 
                before (int, optional): Defaults to 1. Кількість чанків перед цільовим
                after (int, optional): Defaults to 1. Кількість чанків після цільового

            Returns:
                _type_: Повертає результат інструменту get_adjucent_chunks

search_source_related
             Здійснює пошук пов'язаних з документом source_id документів

            Args:
                source_id (str):   ідентифікатор документа джерела
                chunk_index (int):  ідентифікатор чанка
                top_k (int, optional): Defaults to 5. Максимальна кількість джерел

            Returns:
                _type_: Повертає результат інструмента search_related_sources
                    
search_web_historical
            
            Здійснює пошук історичних джерел в мережі Інтернет

            Args:
                query (str): Пошуковий запит до Tavily
                max_results (int, optional): Defaults to 5. Максимальна кількість результатів

            Returns:
                _type_: Повертає результат інструмента search_web_historical_sources

 Список mcp-prompts:
 verification_sources
            Формує інструкцію для верифікації джерельної бази отриманої відповіді       
 critical_review
            Формує інструкцію для критичної оцінки результату
            історичного дослідження.   

 Ресурс поки один 
    "heritage://research/methodology"
    research_methodology
            Методологія проведення історичних досліджень у системі Heritage.
            
Просунутий рівень:

Створено input та output guardrails - поки що лише англомовні. Input - валідує вхідні запити з метою не допустити появи prompt-ін'єкцій. Output_gurdrail дозволяє на виході проконтролювати чи модель у відповідь не передала чиїсь приватні дані користувачу. Усі ці "плюшки" в окремій директорії src\woolf_agents\core\guardrails. Окремо валідується доступність інструментів для окремих агентів за допомогою ToolGuard. 


Експертний рівень:

Підключено систему до LangSmith. Скрін демонструє наявність підключення та постійну роботу системи з цим сервісом.


        
