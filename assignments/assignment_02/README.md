Запуск проекту відбувається з assinment_02 - файл main.py. Даний планер призначений для історичної майбутньої платформи. Агент вибирає з доданих у векторну базу історичних дослідницьких джерел необхідну інформацію для дослідження різних гіпотез. На основі цих гіпотез llm має прийти до свого висновку грунтуючись на гіпотезах, що доступні у документах. 

1. **Planner** отримує `user_task` і створює структурований `BaseTaskPlan` зі списком кроків. Для історичного сценарію кожен крок має `objective`, `expected_result`, `operation`, `research_query`, `requires_evidence` тощо.

2. **PrepareStep** бере `plan.steps[current_step_idx]` і створює компактний `StepExecutionContext`: поточне завдання, поточний крок та необхідні результати попередніх кроків. Одночасно запам'ятовується `step_messages_start_idx`, щоб не передавати LLM всю накопичену історію.

3. **Executor** виконує лише поточний крок. Він отримує:
   `SystemMessage + StepExecutionContext + messages поточного кроку`.
   Якщо потрібні зовнішні дані, LLM генерує `tool_call`.

4. **ToolsNode** виконує інструмент, наприклад retrieval із ChromaDB, і додає `ToolMessage`. Після цього граф повертається в **Executor**, але `current_step_idx` не змінюється. Executor бачить локальну історію:
   `AIMessage(tool_call) → ToolMessage(result)` і продовжує той самий крок.

5. Коли Executor більше не викликає tools, його відповідь перетворюється на структурований **`BaseStepResult` / `HistoricalResearchStepResult`**.

6. **StepEvaluator** оцінює результат через `StepEvaluation`: чи досягнуто `objective`, чи достатньо інформації для наступного кроку, чи є суперечності та чи потрібен `continue / replan / interrupt / fail`.

7. При `continue` **PushStep** зберігає:
   `current_step_result → results`,
   `evaluated_current_step → evaluated_steps`
   і через reducer робить `current_step_idx + 1`. Потім новий `PrepareStep` створює контекст уже наступного кроку.

8. Після останнього кроку **PlanEvaluator** оцінює план цілком. Якщо результат достатній — формується фінальна структурована відповідь; якщо ні — можливий `Replanner`, HITL або завершення з помилкою.

У скороченому вигляді наш workflow зараз такий:

```text
User Task
   ↓
 Planner
   ↓
PrepareStep ←──────────────┐
   ↓                       │
Executor ←──── ToolsNode   │
   │           ↑           │
   ├─ tool_call┘           │
   ↓                       │
StepResult                 │
   ↓                       │
StepEvaluator              │
   ↓                       │
 PushStep ─────────────────┘
   │
   │ останній step
   ↓
PlanEvaluator
   ├── Replanner → ...
   ├── HITL
   └── Finalizer
          ↓
         END
```

Ключова ідея архітектури: **`plan` визначає, що робити; `Executor` вирішує, як виконати конкретний крок; tools дають зовнішні дані; evaluators контролюють якість; `results` є компактною пам'яттю виконаних кроків, а не вся LLM-історія.**
