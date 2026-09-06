url_modelrouter = {
    "openrouter_url": "https://openrouter.ai/api/v1"
}

models_free = {
    
    "GOOGLEGEMMA426BA4B" : "google/gemma-4-26b-a4b-it:free",
    "GOOGLEGEMMA431B": "google/gemma-4-31B:free",
    "LING30FLASHFREE": "inclusionai/ling-3.0-flash:free",
    "GPTOSS20bFREE": "openai/gpt-oss-20b:free",
    "LAGUNAS21FREE": "poolside/laguna-s-2.1:free",  #для завдань tool calling coding
    "LAGUNAXS21FREE": "poolside/laguna-xs-2.1:free",  #для завдань tool calling coding
    "S21PROFREE": "poolside/s2.1-pro:free",
    "NEMOTRON3SUPERFREE": "nvidia/nemotron-3-super-120b-a12b:free",
    "NEMOTRONNANO9BV2FREE": "nvidia/nemotron-nano-9b-v2:free",
    "NEMOTRONNANO12B2VLFREE": "nvidia/nemotron-nano-12b-2vl:free",
    "NEMOTRON3NANO30BA3bFREE": "nvidia/nemotron-3-nano-30b-a3b:free",
    "NEMOTRON3ULTRAFREE": "nvidia/nemotron-3-ultra-550b-a55b:free",    #потужна модель, максимум розумових можливостей, на вершину fallback
    "NEMOTRON3NANOOMNIFREE": "nvidia/nemotron-3-nano-omni:free",
    "NEMOTRON3EMBED1BFREE": "nvidia/nemotron-3-embed-1b:free",         #векторні представлення
    "NEMOTRON35CONTENTSAFETYFREE": "nvidia/nemotron-3.5-content-safety:free",   #безпека, фільтрація запитів
        
}

models = {
    "IBMGRANITE418B":"ibm/granite-4.1-8b-instruct",     #0.05$M input tokens 0.10$M output tokens tool calling code generation RAG
    "DEEPSEEKV4FLASH0731": "deepseek/deepseek-v4-flash-0731",  #0.083/0.167 by 1M tokens reasoning
    "GEMINI25FLASH" : "gemini-2.0-flash",
}

