from typing import Dict, List, Optional
import random
import sys
import rdflib

class RdfGraph:

    def __init__(
        self,
        source_file: Optional[str] = None,
        serialization: Optional[str] = "ttl",
        query_endpoint: Optional[str] = None,
        update_endpoint: Optional[str] = None,
        graph_kwargs: Optional[Dict] = None,
    ) -> None:
        self.source_file = source_file
        self.serialization = serialization
        self.query_endpoint = query_endpoint
        self.update_endpoint = update_endpoint

        try:
            import rdflib
            from rdflib.plugins.stores import sparqlstore
        except ImportError:
            raise ValueError(
                "Could not import rdflib python package. "
                "Please install it with `pip install rdflib`."
            )
        
        if source_file and (query_endpoint or update_endpoint):
            raise ValueError(
                "Could not unambiguously initialize the graph wrapper. "
                "Specify either a file (local or online) via the source_file "
                "or a triple store via the endpoints."
            )
        
        self.graph = rdflib.Graph()
        if source_file:            
            self.graph.parse(source_file, format=self.serialization)

        if query_endpoint:
            if not update_endpoint:
                self._store = sparqlstore.SPARQLStore()
                self._store.open(query_endpoint)
            else:
                self._store = sparqlstore.SPARQLUpdateStore()
                self._store.open((query_endpoint, update_endpoint))
            graph_kwargs = graph_kwargs or {}
            self.graph = rdflib.Graph(self._store, **graph_kwargs)


    def query_return_full_result(
        self,
        query: str,
    ) -> List[rdflib.query.ResultRow]:
        """
        Query the graph.
        """
        from rdflib.exceptions import ParserError
        from rdflib.query import ResultRow

        try:
            return self.graph.query(query)
        except ParserError as e:
            raise ValueError("Generated SPARQL statement is invalid\n" f"{e}")



    def query(
        self,
        query: str,
    ) -> List[rdflib.query.ResultRow]:
        """
        Query the graph.
        """
        from rdflib.exceptions import ParserError
        from rdflib.query import ResultRow

        try:
            res = self.graph.query(query)
        except ParserError as e:
            raise ValueError("Generated SPARQL statement is invalid\n" f"{e}")
        return [r for r in res if isinstance(r, ResultRow)]

    def serialize(self, local_file: str) -> None:
        """
        Serialize the graph to a file.
        """
        self.graph.serialize(destination=local_file, format=local_file.split(".")[-1])

    def serialize_to_string(self) -> None:
        """
        Serialize the graph to a file.
        """
        return self.graph.serialize(format="ttl")

    def update(
        self,
        query: str,
    ) -> None:
        """
        Update the graph.
        """
        from rdflib.exceptions import ParserError

        try:
            self.graph.update(query)
        except ParserError as e:
            raise ValueError("Generated SPARQL statement is invalid\n" f"{e}")

    def exact_search(
        self,
        search_text: str,
    ) -> List[rdflib.query.ResultRow]:
        """
        Search for an exact match in the graph.
        """
        query = f"""
        SELECT ?s ?p ?o
        WHERE {{
            ?s ?p ?o .
            FILTER (str(?s) = "{search_text}" || str(?p) = "{search_text}" || str(?o) = "{search_text}")
        }}
        """
        return self.query(query)

    
    def add(
        self,
        triple: tuple,
    ) -> None:
        """
        Add triple to the graph.
        """
        self.graph.add(triple)

    def add_triples(
        self,
        triples: List[tuple],
    ) -> None:
        """
        Add triples to the graph.
        """
        for triple in triples:
            self.graph.add(triple)


    def URI_exists(self, uri : str) -> bool:
        """
        Check if a URI exists in the graph.
        """
        return (rdflib.URIRef(uri), None, None) in self.graph
    

    def URI_is_class(self, uri : str) -> bool:
        """
        Check if a URI exists in the graph and is a class.
        """
        return (rdflib.URIRef(uri), rdflib.RDF.type, rdflib.RDFS.Class) in self.graph or (rdflib.URIRef(uri), rdflib.RDF.type, rdflib.OWL.Class) in self.graph
    
    def URI_is_property(self, uri : str) -> bool:
        """
        Check if a URI exists in the graph and is a class.
        """
        return (rdflib.URIRef(uri), rdflib.RDF.type, rdflib.RDF.Property) in self.graph or (rdflib.URIRef(uri), rdflib.RDF.type, rdflib.OWL.ObjectProperty) in self.graph or (rdflib.URIRef(uri), rdflib.RDF.type, rdflib.OWL.DatatypeProperty) in self.graph
    
    def append_random_number(self, base_uri : str) -> str:
        """
        Get a URI that does not exist in the graph by appending a random number such that it is unique.
        """
        i = random.randint(0, sys.maxsize)
        uri = base_uri + str(i)

        while self.URI_exists(uri):
            i = random.randint(0, sys.maxsize)
            uri = base_uri + str(i)
        
        return uri
    
    def create_unique_URI(self, full_uri : str) -> str:
        """
        Get a URI that does not exist in the graph.
        """
        if self.URI_exists(full_uri) == False:
            return full_uri
        else:
            i = 1
            uri = full_uri + "_" + str(i)
            while self.URI_exists(uri):
                i += 1
                uri = full_uri + "_" + str(i)
            return uri