# based on https://python.langchain.com/docs/modules/agents/tools/custom_tools

from typing import Any, Dict, Optional, Sequence, Type, Union, List

from langchain_core.pydantic_v1 import BaseModel, Field
from langchain_core.tools import BaseTool
from langchain_core.callbacks import CallbackManagerForToolRun
from langchain_community.agent_toolkits.base import BaseToolkit

from rdf_graph import RdfGraph

class BaseKGSearchTool(BaseModel):
    """Base tool for interacting with a rdf model."""

    model: RdfGraph = Field(exclude=True)
    
    result_format: str = Field(default="txt", exclude=True)

    def format_result(self, result: Any) -> str:
        """Format the result of the query."""
        import io
        if self.result_format == "txt":
            from rdflib.plugins.sparql.results.txtresults import TXTResultSerializer
            with io.StringIO() as s:
                TXTResultSerializer(result).serialize(s, encoding="utf-8")
                serialized_result = s.getvalue()
            return serialized_result
        elif self.result_format == "csv":
            from rdflib.plugins.sparql.results.csvresults import CSVResultSerializer
            with io.BytesIO() as s:
                CSVResultSerializer(result).serialize(s, encoding="utf-8")
                serialized_result = s.getvalue().decode("utf-8")
            return serialized_result
        elif self.result_format == "json":
            from rdflib.plugins.sparql.results.jsonresults import JSONResultSerializer
            with io.BytesIO() as s:
                JSONResultSerializer(result).serialize(s, encoding="utf-8")
                serialized_result = s.getvalue().decode("utf-8")
            return serialized_result
        elif self.result_format == "xml":
            from rdflib.plugins.sparql.results.xmlresults import XMLResultSerializer
            with io.BytesIO() as s:
                XMLResultSerializer(result).serialize(s, encoding="utf-8")
                serialized_result = s.getvalue().decode("utf-8")
            return serialized_result
        else:
            raise ValueError(f"Unknown result format: {self.result_format}")

    class Config(BaseTool.Config):
        pass


class _SearchInstanceToolInput(BaseModel):
    search_text: str = Field(..., description="The text to search for instances in the knowledge graph. Can be a label or a description.")

class SearchInstanceTool(BaseKGSearchTool, BaseTool):
    """Tool for searching an instance in a knowledge graph."""

    name: str = "search_instance"
    description: str = (
            "Exact search for an instance in a knowledge graph. It returns possible instances with their labels, comments, types and identifiers."
        )
    args_schema: Type[BaseModel] = _SearchInstanceToolInput

    def _run(
        self,
        search_text: str,
        run_manager: Optional[CallbackManagerForToolRun] = None,
    ) -> str:
        """Execute the query, return the results or an error message."""

        result = self.model.query_return_full_result(f"""
        SELECT ?instance_id ?label ?comment ?type_label
        WHERE {{
            ?instance_id rdfs:label "{search_text}".
            ?instance_id rdfs:label ?label.
            ?instance_id rdfs:comment ?comment.
            ?instance_id a ?type.
            ?type rdfs:label ?type_label.
            ?type a rdfs:Class.
        }}
        """)

        return super().format_result(result)



 # search property

class _SearchPropertyToolInput(BaseModel):
    search_text: str = Field(..., description="The text to search for properties in the knowledge graph. Can be a label or a description.")

class SearchPropertyTool(BaseKGSearchTool, BaseTool):
    """Tool for searching an instance in a knowledge graph."""

    name: str = "search_property"
    description: str = (
            "Exact search for a property in a knowledge graph. It returns possible properties with their labels, comments, types and identifiers."
        )
    args_schema: Type[BaseModel] = _SearchPropertyToolInput

    def _run(
        self,
        search_text: str,
        run_manager: Optional[CallbackManagerForToolRun] = None,
    ) -> str:
        """Execute the query, return the results or an error message."""

        result = self.model.query_return_full_result(f"""
        SELECT ?property_id ?label ?comment ?domain_label ?range_label
        WHERE {{
            ?property_id a rdf:Property.
            ?property_id rdfs:label "{search_text}".
            ?property_id rdfs:label ?label.
            ?property_id rdfs:comment ?comment.
            ?property_id rdfs:domain ?domain.
            ?domain rdfs:label ?domain_label.
            ?property_id rdfs:range ?range.
            ?range rdfs:label ?range_label.
        }}        
        """)

        return super().format_result(result)


 # search class

class _SearchClassToolInput(BaseModel):
    search_text: str = Field(..., description="The text to search for properties in the knowledge graph. Can be a label or a description.")

class SearchClassTool(BaseKGSearchTool, BaseTool):
    """Tool for searching an classes in a knowledge graph."""

    name: str = "search_class"
    description: str = (
            "Exact search for a class in a knowledge graph. It returns possible classes with their labels, comments, types and identifiers."
        )
    args_schema: Type[BaseModel] = _SearchClassToolInput

    def _run(
        self,
        search_text: str,
        run_manager: Optional[CallbackManagerForToolRun] = None,
    ) -> str:
        """Execute the query, return the results or an error message."""

        result = self.model.query_return_full_result(f"""
        SELECT ?class_id ?label ?comment
        WHERE {{
            ?class_id a rdfs:Class.
            ?class_id rdfs:label "{search_text}".
            ?class_id rdfs:label ?label.
            ?class_id rdfs:comment ?comment.
        }}        
        """)

        return super().format_result(result)

# Toolkit

class KGSearchToolkit(BaseToolkit):
    """Toolkit for interacting with SQL databases."""

    model: RdfGraph = Field(exclude=True)
    result_format: str = Field(default="csv", exclude=True)

    class Config:
        """Configuration for this pydantic object."""

        arbitrary_types_allowed = True

    def get_tools(self) -> List[BaseTool]:
        """Get the tools in the toolkit."""

        search_instance_tool = SearchInstanceTool(model=self.model, result_format=self.result_format)
        search_property_tool = SearchPropertyTool(model=self.model, result_format=self.result_format)
        search_class_tool = SearchClassTool(model=self.model, result_format=self.result_format)

        return [
            search_instance_tool,
            search_property_tool,
            search_class_tool
        ]
