from abc import ABC, abstractmethod
from typing import Optional
from langchain_core.embeddings import Embeddings
from langchain_community.chat_models.tongyi import BaseChatModel
from langchain_community.embeddings import DashScopeEmbeddings
from langchain_community.chat_models.tongyi import ChatTongyi
from langchain_community.embeddings import DashScopeEmbeddings
from langchain_ollama.embeddings import OllamaEmbeddings
from langchain_community.embeddings import OpenAIEmbeddings
from langchain_ollama.chat_models import ChatOllama
from langchain_openai.chat_models import ChatOpenAI
from utils.config_handler import rag_conf


class BaseModelFactory(ABC):
    @abstractmethod
    def generator(self) -> Optional[Embeddings | BaseChatModel]:
        pass


class ChatModelFactory(BaseModelFactory):
    def generator(self) -> Optional[Embeddings | BaseChatModel]:
        if rag_conf['chat_model_source']=="ollma":
            return ChatOllama(model=rag_conf["chat_model_name"],reasoning=False)
        elif rag_conf['chat_model_source']=="tongyi":
            return ChatTongyi(model=rag_conf["chat_model_name"])
        else:
            return ChatOpenAI(model=rag_conf["chat_model_name"],base_url=rag_conf["chat_model_url"])


class EmbeddingsFactory(BaseModelFactory):
    def generator(self) -> Optional[Embeddings | BaseChatModel]:
        if rag_conf['embedding_model_source']=="ollma":
            return OllamaEmbeddings(model=rag_conf["embedding_model_name"])
        elif rag_conf['embedding_model_source']=="tongyi":
            return DashScopeEmbeddings(model=rag_conf["embedding_model_name"])
        else:
            return OpenAIEmbeddings(model=rag_conf["embedding_model_name"],base_url=rag_conf["embedding_model_url"])


chat_model = ChatModelFactory().generator()
embed_model = EmbeddingsFactory().generator()
