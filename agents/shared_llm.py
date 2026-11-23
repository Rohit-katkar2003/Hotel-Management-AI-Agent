from langchain_openai import ChatOpenAI
from config import settings

def make_llm():
    return ChatOpenAI(
        model=settings.sensnova_model,
        temperature=settings.llm_temperature,
        api_key=settings.sensnova_api_key,
        base_url=settings.sensnova_base_url,
    )