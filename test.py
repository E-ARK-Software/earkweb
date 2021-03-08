import rdflib
from networkx.drawing.nx_agraph import graphviz_layout
from rdflib.extras.external_graph_libs import rdflib_to_networkx_multidigraph
import networkx as nx
import matplotlib.pyplot as plt

url = 'https://www.w3.org/TeamSubmission/turtle/tests/test-30.ttl'

g = rdflib.Graph()
result = g.parse(url, format='turtle')

G = rdflib_to_networkx_multidigraph(result)

# Plot Networkx instance of RDF Graph
#pos = nx.spring_layout(G, scale=2)
edge_labels = nx.get_edge_attributes(G, 'r')
#nx.draw_networkx_edge_labels(G, graphviz_layout(G), edge_labels=edge_labels)
nx.draw(G, pos=nx.nx_agraph.graphviz_layout(G))
#nx.draw(G, with_labels=True)
plt.savefig("filename.png")
