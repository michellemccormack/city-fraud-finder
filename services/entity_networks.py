from __future__ import annotations
import re
from typing import List, Dict, Set, Tuple
from sqlalchemy import select
from db.models import Entity, Identifier, Alias
from core.utils import normalize_name, similarity

def extract_person_names(entity_name: str) -> List[str]:
    """Extract potential person names from entity name"""
    name = entity_name.strip()
    # Common patterns: "Last, First", "First Last", "LAST, FIRST M"
    parts = re.split(r'[,\s]+', name)
    
    # If comma-separated, likely "Last, First"
    if ',' in name:
        parts = [p.strip() for p in name.split(',')]
        if len(parts) >= 2:
            # Could be "Last, First" or "Last, First Middle"
            return [p.strip() for p in parts if len(p.strip()) > 2]
    
    # If all caps or title case, might be a person name
    if name.isupper() or (name[0].isupper() and not any(c in name for c in ['@', '/', '&'])):
        # Look for 2-4 word names (likely person names)
        words = [w.strip() for w in name.split() if w.strip()]
        if 2 <= len(words) <= 4:
            return words
    
    return []

def find_name_based_clusters(session, city_key: str, entity_type: str = None) -> List[Dict]:
    """Find clusters of entities that share person names or similar names"""
    query = select(Entity).where(Entity.city_key == city_key)
    if entity_type:
        query = query.where(Entity.entity_type == entity_type)
    entities = session.execute(query).scalars().all()
    
    # Extract person names from each entity
    entity_person_names: Dict[int, Set[str]] = {}
    for ent in entities:
        person_names = set()
        # Extract from main name
        for name_part in extract_person_names(ent.name or ""):
            person_names.add(normalize_name(name_part))
        # Extract from aliases
        for alias in ent.aliases:
            for name_part in extract_person_names(alias.alias):
                person_names.add(normalize_name(name_part))
        if person_names:
            entity_person_names[ent.id] = person_names
    
    # Find clusters: entities that share person names
    clusters: List[Set[int]] = []
    entity_to_cluster: Dict[int, int] = {}
    
    for ent1_id, names1 in entity_person_names.items():
        found_cluster = None
        for ent2_id, names2 in entity_person_names.items():
            if ent1_id == ent2_id:
                continue
            # Check for overlap in person names
            if names1 & names2:  # Set intersection
                cluster_idx = entity_to_cluster.get(ent2_id)
                if cluster_idx is not None:
                    found_cluster = cluster_idx
                    break
        
        if found_cluster is not None:
            clusters[found_cluster].add(ent1_id)
            entity_to_cluster[ent1_id] = found_cluster
        else:
            # Start new cluster
            cluster_idx = len(clusters)
            clusters.append({ent1_id})
            entity_to_cluster[ent1_id] = cluster_idx
    
    # Also find similar name clusters (for business name similarity)
    similar_clusters: List[Set[int]] = []
    processed = set()
    
    for ent1 in entities:
        if ent1.id in processed:
            continue
        cluster = {ent1.id}
        nname1 = normalize_name(ent1.name or "")
        
        for ent2 in entities:
            if ent2.id in processed or ent2.id == ent1.id:
                continue
            nname2 = normalize_name(ent2.name or "")
            sim = similarity(nname1, nname2)
            # High similarity might indicate same entity with slight name variations
            if sim > 0.85 and nname1 and nname2:
                cluster.add(ent2.id)
                processed.add(ent2.id)
        
        if len(cluster) > 1:
            similar_clusters.append(cluster)
            processed.update(cluster)
    
    # Combine and format results
    all_clusters = [c for c in clusters if len(c) > 1] + similar_clusters
    
    # Merge overlapping clusters
    merged_clusters = []
    for cluster in all_clusters:
        merged = False
        for merged_cluster in merged_clusters:
            if cluster & merged_cluster:
                merged_cluster.update(cluster)
                merged = True
                break
        if not merged:
            merged_clusters.append(cluster)
    
    # Format as list of cluster info
    result = []
    for cluster_ids in merged_clusters:
        if len(cluster_ids) < 2:
            continue
        cluster_entities = [e for e in entities if e.id in cluster_ids]
        # Find shared names/patterns
        shared_patterns = []
        if len(cluster_entities) > 0:
            all_names = [normalize_name(e.name or "") for e in cluster_entities]
            # Find common words
            words_list = [set(n.split()) for n in all_names if n]
            if words_list:
                common_words = set.intersection(*words_list) if len(words_list) > 1 else set()
                shared_patterns = [w for w in common_words if len(w) > 2][:3]
        
        result.append({
            "entity_ids": list(cluster_ids),
            "entity_count": len(cluster_ids),
            "shared_patterns": shared_patterns,
            "entities": [
                {
                    "id": e.id,
                    "name": e.name,
                    "type": e.entity_type,
                    "address": e.address,
                    "license_id": e.license_id
                }
                for e in cluster_entities
            ]
        })
    
    return sorted(result, key=lambda x: x["entity_count"], reverse=True)

