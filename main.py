from langchain import hub
from langchain_openai import ChatOpenAI
from langchain.agents import AgentExecutor, create_openai_functions_agent


from KG_Create_Toolkit import KGCreateToolkit
from KG_Search_Toolkit import KGSearchToolkit


from rdf_graph import RdfGraph
model = RdfGraph()
#model = RdfGraph(source_file="myKB.ttl") 
#model = RdfGraph(query_endpoint="http://dbpedia.org/sparql")

base_uri = "http://myKB.org/"
return_full_uri = True
use_speaking_names = False
query_result_format = "csv"

tools = []
tools.extend(KGCreateToolkit(model=model, base_uri=base_uri, return_full_uri=return_full_uri, use_speaking_names=use_speaking_names).get_tools())
tools.extend(KGSearchToolkit(model=model, result_format=query_result_format).get_tools())

prompt = hub.pull("hwchase17/openai-functions-agent")
llm = ChatOpenAI(model="gpt-3.5-turbo", temperature=0)

agent = create_openai_functions_agent(llm, tools, prompt)

agent_executor = AgentExecutor(agent=agent, tools=tools, verbose=True)

#import json
#from langchain_core.utils.function_calling import convert_to_openai_tool
#for tool in tools:
#    print(json.dumps(convert_to_openai_tool(tool), indent=2))
#    print("------------------------------------")

sentence = "The capital of France is Paris."

agent_executor.invoke({"input": (
    "Extract all possible information from sentences by searching for instances, properties, and classes."
    "In case no corresponding entity is found, create it with the corresponding functions. "
    "Finally, add a statement to the knowledge graph."
    "Before creating a property, search for it with function search_property. "
    "Extract all possible information from the following sentence: "
    f"'{sentence}'")})

model.serialize(local_file="myKB.ttl")