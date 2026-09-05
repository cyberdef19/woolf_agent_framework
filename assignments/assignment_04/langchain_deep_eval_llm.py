from deepeval.models.base_model import DeepEvalBaseLLM
from pydantic import BaseModel

class LangChainDeepEvalLLM(DeepEvalBaseLLM):
    
    def __init__(self, model = None, *args, **kwargs):
        self.model = model
    
    def load_model(self, *args, **kwargs):
        return self.model
    
    def get_model_name(self, *args, **kwargs):
        return "LangChain_LLM"
    
    def generate(self, prompt: str, schema: type[BaseModel]|None=None):
        model = self.load_model()
        if schema is not None:
            structured_output = model.with_structured_output(schema)
            return structured_output.invoke(prompt)
        return model.invoke(prompt).content 
    
    async def a_generate(self, prompt: str, schema: type[BaseModel]|None=None):
        model = self.load_model
        
        if schema is not None:
            structured_output = model.with_structured_output(schema)
            return await structured_output.ainvoke(prompt)
        response = await model.ainvoke(prompt)
        return response.content