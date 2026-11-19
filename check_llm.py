from src.agent.llm import get_llm

llm = get_llm()
reply = llm.invoke("hii......")
print(reply.content)