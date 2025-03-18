# A simple graph database using JSON files.
# For testing and low-scale applications.
# TODO: Add more features like constraints, indexes, etc.
# TODO: use Neo4j or similar for larger scale applications.
#

import json


class BasicGraphDB:
    def __init__(self):
        self.nodes = {}  # node_id -> node dict
        self.relationships = {}  # relationship_id -> relationship dict
        self.adjacency = {}  # node_id -> list of relationship ids
        self.next_node_id = 1
        self.next_rel_id = 1

    def to_dict(self):
        return {
            'nodes': self.nodes,
            'relationships': self.relationships,
            'adjacency': self.adjacency,
            'next_node_id': self.next_node_id,
            'next_rel_id': self.next_rel_id
        }
    
    @staticmethod
    def from_dict(data):
        graph = BasicGraphDB()
        graph.nodes = data['nodes']
        graph.relationships = data['relationships']
        graph.adjacency = data['adjacency']
        graph.next_node_id = data['next_node_id']
        graph.next_rel_id = data['next_rel_id']
        return graph

    def create_node(self, label, properties=None):
        node = {
            'id': self.next_node_id,
            'label': label,
            'properties': properties or {}
        }
        self.nodes[self.next_node_id] = node
        self.adjacency[self.next_node_id] = []
        self.next_node_id += 1
        return node

    def create_relationship(self, start_id, rel_type, end_id, properties=None, bidirectional=False):
        if start_id not in self.nodes or end_id not in self.nodes:
            raise ValueError("Both start and end nodes must exist.")
        relationship = {
            'id': self.next_rel_id,
            'start': start_id,
            'type': rel_type,
            'end': end_id,
            'properties': properties or {},
            'bidirectional': bidirectional
        }
        self.relationships[self.next_rel_id] = relationship
        self.adjacency[start_id].append(self.next_rel_id)
        if bidirectional:
            self.adjacency[end_id].append(self.next_rel_id)
        else:
            # Even if not bidirectional, store on end node to make querying both ways easier
            self.adjacency[end_id].append(self.next_rel_id)
        self.next_rel_id += 1
        return relationship

    def match_nodes(self, label=None, **property_filter):
        result = []
        for node in self.nodes.values():
            if label and node['label'] != label:
                continue
            if all(node['properties'].get(k) == v for k, v in property_filter.items()):
                result.append(node)
        return result

    def match_relationships(self, rel_type=None, property_filter=None):
        result = []
        for rel in self.relationships.values():
            if rel_type and rel['type'] != rel_type:
                continue
            if property_filter and not all(rel['properties'].get(k) == v for k, v in property_filter.items()):
                continue
            result.append(rel)
        return result

    def get_relationships_for_node(self, node_id, rel_type=None, direction='both'):
        rels = []
        for rel_id in self.adjacency.get(node_id, []):
            rel = self.relationships[rel_id]
            if rel_type and rel['type'] != rel_type:
                continue

            # Check direction
            if direction == 'out' and rel['start'] != node_id:
                continue
            if direction == 'in' and rel['end'] != node_id:
                continue

            rels.append(rel)
        return rels

    def update_node(self, node_id, properties):
        if node_id in self.nodes:
            self.nodes[node_id]['properties'].update(properties)
        else:
            raise ValueError("Node not found.")

    def update_relationship(self, rel_id, properties):
        if rel_id in self.relationships:
            self.relationships[rel_id]['properties'].update(properties)
        else:
            raise ValueError("Relationship not found.")

    def delete_node(self, node_id):
        if node_id in self.nodes:
            # Remove related relationships
            rel_ids = list(self.adjacency[node_id])
            for rel_id in rel_ids:
                self.delete_relationship(rel_id)
            del self.adjacency[node_id]
            del self.nodes[node_id]
        else:
            raise ValueError("Node not found.")

    def delete_relationship(self, rel_id):
        if rel_id in self.relationships:
            rel = self.relationships[rel_id]
            self.adjacency[rel['start']].remove(rel_id)
            if rel['end'] != rel['start'] or rel['bidirectional']:
                self.adjacency[rel['end']].remove(rel_id)
            del self.relationships[rel_id]
        else:
            raise ValueError("Relationship not found.")

    def print_graph(self):
        print("Nodes:")
        for node in self.nodes.values():
            print(node)
        print("\nRelationships:")
        for rel in self.relationships.values():
            print(rel)
