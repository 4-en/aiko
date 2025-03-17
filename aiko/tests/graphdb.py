class GraphDB:
    def __init__(self):
        self.nodes = {}  # node_id -> node dict
        self.relationships = {}  # relationship_id -> relationship dict
        self.adjacency = {}  # node_id -> list of relationship ids
        self.next_node_id = 1
        self.next_rel_id = 1

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

# ---------------------------
# Example usage:
from aiko.core import Memory
from aiko.utils import date_parser
import datetime
import time
db = GraphDB()

# Create test memories
memories = [
    Memory(memory="Aiko's favorite food is fried tofu.", memory_time_point=date_parser.parse_timestamp(365)),
    Memory(memory="Aiko's favorite color is sky blue.", memory_time_point=date_parser.parse_timestamp(1365)),
    Memory(memory="Aiko's favorite movie is Spirited Away.", memory_time_point=date_parser.parse_timestamp(2365)),
    Memory(memory="Senko likes to watch the movie Spirited Away.", memory_time_point=date_parser.parse_timestamp(965)),
    Memory(memory="Aiko likes to play video games. Her favorite game is Oldschool Runescape.", memory_time_point=date_parser.parse_timestamp(1365)),
    Memory(memory="Senko's favorite game is Oldschool Runescape.", memory_time_point=date_parser.parse_timestamp(2365)),
    Memory(memory="B0aty is a famous Oldschool Runescape streamer on Twitch who is known for his hardcore ironman series.", memory_time_point=date_parser.parse_timestamp(2365)),
    Memory(memory="Aiko's favorite streamer is B0aty.", memory_time_point=date_parser.parse_timestamp(2365)),
    Memory(memory="Forsen is a popular Twitch streamer known for his variety streams.", memory_time_point=date_parser.parse_timestamp(2365)),
    Memory(memory="Aiko likes to watch Forsen's streams.", memory_time_point=date_parser.parse_timestamp(2365))
]

# Add memories to graph
for memory in memories:
    memory_dict = memory.to_dict()
    entities = memory.entities

    # Add the memory
    memory_node = db.create_node('Memory', memory_dict)

    # Add entities
    for entity in entities:
        entity_node = db.match_nodes(label='Entity', name=entity)
        if not entity_node:
            entity_node = db.create_node('Entity', {'name': entity})
        else:
            entity_node = entity_node[0]
        db.create_relationship(memory_node['id'], 'HAS_ENTITY', entity_node['id'])

# Query the graph
import random
# test by getting a random memory
memory_node = random.choice(db.match_nodes(label='Memory'))
start_memory = Memory.from_dict(memory_node['properties'])
print(f"Start Memory: {start_memory.memory}")
print(f"Entities: {",".join(start_memory.entities)}")

# now, for each entity, get the memories that also contain that entity
found = {}
for entity_rel in db.get_relationships_for_node(memory_node['id'], 'HAS_ENTITY'):
    entity_node = db.nodes[entity_rel['end']]
    entity = entity_node['properties']['name']
    for memory_rel in db.get_relationships_for_node(entity_node['id'], 'HAS_ENTITY'):
        memory_node = db.nodes[memory_rel['start']]
        memory = Memory.from_dict(memory_node['properties'])
        found[memory_node['id']] = memory

ranking = []
for memory_id, memory in found.items():
    # rank by number of entities in common
    common_entities = set(memory.entities).intersection(start_memory.entities)
    ranking.append((memory_id, len(common_entities)))

ranking.sort(key=lambda x: x[1], reverse=True)

for memory_id, score in ranking:
    memory_node = db.nodes[memory_id]
    memory = Memory.from_dict(memory_node['properties'])
    print(f"Memory: {memory.memory}")
    print(f"Entities: {','.join(memory.entities)}")
    print(f"Score: {score}")
    print()


