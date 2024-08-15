# based on https://python.langchain.com/docs/modules/agents/tools/custom_tools

from typing import Any, Dict, Optional, Sequence, Type, Union, List

from langchain_core.pydantic_v1 import BaseModel, Field
from langchain_core.tools import BaseTool
from langchain_core.callbacks import CallbackManagerForToolRun
from langchain_community.agent_toolkits.base import BaseToolkit

from rdf_graph import RdfGraph
import urllib



class BaseKGCreateTool(BaseModel):
    """Base tool for interacting with a rdf model."""

    model: RdfGraph = Field(exclude=True)
    
    base_uri: str = Field(exclude=True)

    return_full_uri: bool = Field(default=True, exclude=True)
    
    use_speaking_names: bool = Field(default=False, exclude=True)

    allow_schema_changes: bool = Field(default=True, exclude=True)

    def _create_uri(self, label: str, resource_type : str) -> str:
        if self.use_speaking_names:
            url = self.base_uri + urllib.parse.quote_plus(label)
            return self.model.create_unique_URI(url)
        else:
            return self.model.append_random_number(self.base_uri + resource_type)

    def _get_full_uri(self, uri: str) -> str:
        if not uri:
            return ""
        if self.return_full_uri:
            return uri
        else:
            return self.base_uri + uri
    
    def _shorten_uri(self, uri: str) -> str:
        if not uri:
            return ""
        if self.return_full_uri:
            return uri
        else:
            return uri[len(self.base_uri):]

    class Config(BaseTool.Config):
        pass




class _KGCreatePropertyToolInput(BaseModel):
    label: str = Field(..., description="An english and human-readable label for the property.") # the ... means that the field is required
    comment: str = Field(..., description="An english and human-readable comment for the property which describes in detail when the property should be used.")
    #domain: Optional[str] = Field(default="", description="The domain of the property (which is the type of the subject). It needs to be a URI of a class in the knowledge graph.")
    #range: Optional[str] = Field(default="",description="The range of the property (which is the type of the object). It needs to be a URI of a class in the knowledge graph.")
    domain: str = Field(..., description="The domain of the property (which is the type of the subject). It needs to be a class URI in the knowledge graph.")
    range: str = Field(..., description="The range of the property (which is the type of the object). It needs to be a class URIin the knowledge graph.")
    super_property_id: Optional[str] = Field(default="", description="A URI which is the identifier for the super property if existent.")

class KGCreatePropertyTool(BaseKGCreateTool, BaseTool):
    """Tool for creating a property in a knowledge graph."""

    name: str = "create_property"
    description: str = (
            "Creates a property in a knowledge graph and returns the property identifier."
        )
    args_schema: Type[BaseModel] = _KGCreatePropertyToolInput

    def _run(
        self,
        label: str,
        comment: str,
        domain: str = "",
        range: str = "",
        super_property_id: str = "",
        run_manager: Optional[CallbackManagerForToolRun] = None,
    ) -> str:
        """Execute the query, return the results or an error message."""

        from rdflib import URIRef, Literal
        from rdflib.namespace import RDF, RDFS

        domain_uri = super()._get_full_uri(domain)
        range_uri = super()._get_full_uri(range)
        super_property_uri = super()._get_full_uri(super_property_id)

        error_message_class = " Search for it with function search_class. If it cannot be found, create it with create_class function and use the URI."
        
        # validation step:
        if domain_uri:
            if self.model.URI_exists(domain_uri) == False:
                return "The domain of the property (which should be a class) does not exist in the graph." + error_message_class
            if self.model.URI_is_class(domain_uri) == False:
                return "The domain of the property (which should be a class) is not a class." + error_message_class
        if range_uri:
            if self.model.URI_exists(range_uri) == False:
                return "The range of the property (which should be a class) does not exist in the graph." + error_message_class
            if self.model.URI_is_class(range_uri) == False:
                return "The range of the property (which should be a class) is not a class." + error_message_class

        if super_property_uri:
            error_message_property = " Search for it with function search_property. If it cannot be found, create it with create_property function and use the URI."
            if self.model.URI_exists(super_property_uri) == False:
                return "The super property does not exist in the graph." + error_message_property
            if self.model.URI_is_property(super_property_uri) == False:
                return "The super property is not a property. Search for it with function search_property." + error_message_property


        # now create it:
        my_property_uri = super()._create_uri(label, "P")
        my_property = URIRef(my_property_uri)
        
        self.model.add((my_property, RDF.type, RDF.Property))
        self.model.add((my_property, RDFS.label, Literal(label)))
        self.model.add((my_property, RDFS.comment, Literal(comment)))

        if domain_uri:
            self.model.add((my_property, RDFS.domain, URIRef(domain_uri)))
        if range_uri:
            self.model.add((my_property, RDFS.range, URIRef(range_uri)))

        if super_property_uri:
            self.model.add((my_property, RDFS.subPropertyOf, URIRef(super_property_uri)))

        return super()._shorten_uri(my_property_uri)
    

# Create class tool

class _KGCreateClassToolInput(BaseModel):
    label: str = Field(..., description="An english and human-readable label for the class.") # the ... means that the field is required
    comment: str = Field(..., description="An english and human-readable comment for the class which describes in detail when the class should be used.")

    super_class_id: Optional[str] = Field(default="", description="A URI which is the identifier for the super property if existent.")


class KGCreateClassTool(BaseKGCreateTool, BaseTool):
    """Tool for creating a class in a knowledge graph."""

    name: str = "create_class"
    description: str = (
            "Creates a class in a knowledge graph and returns the class identifier."
        )
    args_schema: Type[BaseModel] = _KGCreateClassToolInput

    def _run(
        self,
        label: str,
        comment: str,
        super_class_id: str = "",
        run_manager: Optional[CallbackManagerForToolRun] = None,
    ) -> str:
        """Execute the query, return the results or an error message."""

        from rdflib import URIRef, Literal
        from rdflib.namespace import RDF, RDFS

        super_class_uri = super()._get_full_uri(super_class_id)

        # validation step:
        if super_class_uri:
            error_message_class = " Search for it with function search_class. If it cannot be found, create it with create_class function and use the URI."
            if self.model.URI_exists(super_class_uri) == False:
                return "The super class does not exist in the graph." + error_message_class
            if self.model.URI_is_class(super_class_uri) == False:
                return "The super class is not a class." + error_message_class
            
        my_class_uri = super()._create_uri(label, "C")
        my_class = URIRef(my_class_uri)
        
        self.model.add((my_class, RDF.type, RDFS.Class))
        self.model.add((my_class, RDFS.label, Literal(label)))
        self.model.add((my_class, RDFS.comment, Literal(comment)))
        if super_class_uri:
            self.model.add((my_class, RDFS.subClassOf, URIRef(super_class_id)))

        return super()._shorten_uri(my_class_uri)

# Create instance tool

class _KGCreateInstanceToolInput(BaseModel):
    label: str = Field(..., description="An english and human-readable label for the instance.") # the ... means that the field is required
    comment: str = Field(..., description="An english and human-readable comment for the instance which describes the instance in detail.")
    instance_type: str = Field(..., description="The type of the instance. It needs to be a class in the knowledge graph (URI). If not existent, create it first with create_class and use the created URI")

class KGCreateInstanceTool(BaseKGCreateTool, BaseTool):
    """Tool for creating an instance in a knowledge graph."""

    name: str = "create_instance"
    description: str = (
            "Creates an instance in a knowledge graph and returns the instance identifier."
        )
    args_schema: Type[BaseModel] = _KGCreateInstanceToolInput

    def _run(
        self,
        label: str,
        comment: str,
        instance_type: str,
        run_manager: Optional[CallbackManagerForToolRun] = None,
    ) -> str:
        """Execute the query, return the results or an error message."""

        from rdflib import URIRef, Literal
        from rdflib.namespace import RDF, RDFS

        instance_type_uri = super()._get_full_uri(instance_type)

        error_message_class = " Search for it with function search_class."
        if self.allow_schema_changes:
            error_message_class += " If it cannot be found, create it with create_class function and use the URI."

        # validation step:
        if self.model.URI_exists(instance_type_uri) == False:
            return "The instance type of the instance does not exist in the graph." + error_message_class
        if self.model.URI_is_class(instance_type_uri) == False:
            return "The instance type of the instance is not a class." + error_message_class

        my_instance_uri = super()._create_uri(label, "I")
        my_instance = URIRef(my_instance_uri)
        
        self.model.add((my_instance, RDF.type, URIRef(instance_type_uri)))
        self.model.add((my_instance, RDFS.label, Literal(label)))
        self.model.add((my_instance, RDFS.comment, Literal(comment)))

        return super()._shorten_uri(my_instance_uri)

# Create statement tool

class _KGCreateStatementToolInput(BaseModel):
    subject: str = Field(..., description="The subject id.")
    property: str = Field(..., description="The property id.")
    object: str = Field(..., description="The object id.")

class KGCreateStatementTool(BaseKGCreateTool, BaseTool):
    """Tool for creating an instance in a knowledge graph."""

    name: str = "create_statement"
    description: str = (
            "Creates a statement in a knowledge graph consisting of subject, property, and object."
        )
    args_schema: Type[BaseModel] = _KGCreateStatementToolInput

    def _run(
        self,
        subject: str,
        property: str,
        object: str,
        run_manager: Optional[CallbackManagerForToolRun] = None,
    ) -> str:
        """Execute the query, return the results or an error message."""

        from rdflib import URIRef, Literal
        from rdflib.namespace import RDF, RDFS

        subject_uri = super()._get_full_uri(subject)
        property_uri = super()._get_full_uri(property)
        object_uri = super()._get_full_uri(object)
        
        # validation step:
        if self.model.URI_exists(subject_uri) == False:
            return "Subject does not exist in the graph. Create it first."
        if self.model.URI_exists(property_uri) == False:
            return "Property does not exist in the graph. Create it first."
        if self.model.URI_is_property(property_uri) == False:
            return "Property is not a defined property in the KG. Create it first."
        if self.model.URI_exists(object_uri) == False:
            return "Object does not exist in the graph. Create it first."
        
        self.model.add((URIRef(subject_uri), URIRef(property_uri), URIRef(object_uri)))
        return "Statement created."
        

# Toolkit

class KGCreateToolkit(BaseToolkit):
    """Toolkit for creating instance, classes, and properties without providing an identifier."""

    model: RdfGraph = Field(exclude=True)
    
    base_uri: str = Field(exclude=True)

    return_full_uri: bool = Field(default=True, exclude=True)
    
    use_speaking_names: bool = Field(default=False, exclude=True)

    allow_schema_changes: bool = Field(default=True, exclude=True)

    class Config:
        """Configuration for this pydantic object."""

        arbitrary_types_allowed = True

    def get_tools(self) -> List[BaseTool]:
        """Get the tools in the toolkit."""
        create_instance_tool = KGCreateInstanceTool(model=self.model, base_uri=self.base_uri, return_full_uri=self.return_full_uri, use_speaking_names=self.use_speaking_names, allow_schema_changes=self.allow_schema_changes)
        create_statement_tool = KGCreateStatementTool(model=self.model, base_uri=self.base_uri, return_full_uri=self.return_full_uri, use_speaking_names=self.use_speaking_names, allow_schema_changes=self.allow_schema_changes)
        if self.allow_schema_changes == False:
            return [create_instance_tool, create_statement_tool]
        
        create_property_tool = KGCreatePropertyTool(model=self.model, base_uri=self.base_uri, return_full_uri=self.return_full_uri, use_speaking_names=self.use_speaking_names, allow_schema_changes=self.allow_schema_changes)
        create_class_tool = KGCreateClassTool(model=self.model, base_uri=self.base_uri, return_full_uri=self.return_full_uri, use_speaking_names=self.use_speaking_names, allow_schema_changes=self.allow_schema_changes)

        return [create_property_tool, create_class_tool, create_instance_tool, create_statement_tool]
