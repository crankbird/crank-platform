"""
Philosophical tagging schema for unified knowledge base integration.
Canonical source of truth for theme detection and clustering.
"""

PHILOSOPHICAL_SCHEMA = {
    "core_principle": "Intelligence Is Situated in Space and Time",
    
    "primary_markers": {
        "SHM": {
            "name": "Space-Has-Meaning",
            "description": "Context-dependent behavior shaped by location",
            "keywords": [
                "context-dependent", "local-first", "geographic", "jurisdictional",
                "embodied cognition", "situated intelligence", "environmental context",
                "edge computing", "distributed processing", "location-aware"
            ],
            "patterns": [
                r"different contexts? produce different",
                r"local\w* processing",
                r"regulatory environment",
                r"where you are changes",
                r"context[-\s]sensitive",
                r"location[-\s]dependent",
                r"location[-\s]aware",
                r"place[-\s]based", 
                r"geographical context"
            ],
            "weight": 1.2
        },
        
        "TUD": {
            "name": "Time-Unevenly-Distributed",
            "description": "Temporal relativity in capability and adoption",
            "keywords": [
                "temporal relativity", "future emerging", "asynchronous",
                "historical context", "innovation diffusion", "temporal arbitrage",
                "early adopters", "uneven distribution", "capability gradients",
                "adoption curves", "temporal complexity", "time scales"
            ],
            "patterns": [
                r"living in the future",
                r"capabilities don't distribute evenly",
                r"early adopters? vs",
                r"when you are changes",
                r"temporal[-\s]arbitrage",
                r"future arrives unevenly",
                r"different time scales?",
                r"adoption lag",
                r"capability gaps?",
                r"temporal[-\s]complexity"
            ],
            "weight": 1.3
        },
        
        "IIP": {
            "name": "Identity-Is-Plural",
            "description": "Multiple contextual identity expression",
            "keywords": [
                "multiple identity", "personas", "context-dependent identity",
                "role-based", "multiplicity-aware", "mascot systems",
                "situational identity", "persona-driven", "identity adaptation",
                "contextual personas", "identity flexibility", "role switching"
            ],
            "patterns": [
                r"different person in different contexts?",
                r"persona[-\s]driven",
                r"role[-\s]based",
                r"multiple identit",
                r"contain multitudes",
                r"contextual personas?",
                r"identity[-\s]flexibility",
                r"role[-\s]switching",
                r"situational[-\s]identity"
            ],
            "weight": 1.1
        },
        
        "AID": {
            "name": "Agency-Is-Distributed",
            "description": "Decentralized autonomous decision-making",
            "keywords": [
                "autonomous agents", "decentralized", "m2m economy",
                "edge intelligence", "distributed coordination", "anti-centralization",
                "agent commerce", "emergent intelligence", "distributed teams",
                "autonomous coordination", "distributed decision-making", "agent ecosystems"
            ],
            "patterns": [
                r"agents? making autonomous",
                r"edge nodes? coordinat",
                r"distributed teams? self[-\s]organiz",
                r"intelligence emerges across",
                r"m2m economy",
                r"agent[-\s]to[-\s]agent",
                r"autonomous[-\s]coordination",
                r"distributed[-\s]decision[-\s]making",
                r"agent[-\s]ecosystem"
            ],
            "weight": 1.4
        },

        "DHG": {
            "name": "Data-Has-Gravity",
            "description": "Computation follows meaning and context",
            "keywords": [
                "computational locality", "data sovereignty", "meaning-driven",
                "context-aware computation", "local data preference", "gravity-based",
                "data residency", "computation follows meaning", "semantic locality",
                "data magnetism", "computational attraction"
            ],
            "patterns": [
                r"process data where it lives",
                r"local context determines",
                r"data residency",
                r"computation follows meaning",
                r"data[-\s]gravity",
                r"semantic[-\s]locality",
                r"computational[-\s]attraction",
                r"data[-\s]magnetism",
                r"gravity[-\s]based"
            ],
            "weight": 1.15
        },

        "NET": {
            "name": "Network-Effects-Thinking",
            "description": "Connections and relationships precede and define entities",
            "keywords": [
                "network effects", "connections", "relationships", "protocols",
                "metadata over data", "linkages", "network topology", "graph thinking",
                "semantic connections", "relational architecture", "network-first",
                "the network is the computer", "protocol governance", "edge relationships"
            ],
            "patterns": [
                r"network is the computer",
                r"relationships? (?:are )?more important than",
                r"metadata (?:over|before|defines|more than) data",
                r"control(?:ling)? (?:the )?linkages?",
                r"connections? (?:determine|define|shape|precede)",
                r"protocol(?:s)? (?:enable|define|govern)",
                r"network effects?",
                r"semantic connections?",
                r"relational (?:architecture|thinking)",
                r"graph[-\s](?:thinking|first|topology)"
            ],
            "weight": 1.3
        }
    },
    
    "secondary_themes": {
        "BIZ": {
            "name": "Business-Systems",
            "description": "Revenue operations and brand science applications",
            "keywords": [
                "revops", "cognitive infrastructure", "brand science",
                "persona intelligence", "market segmentation", "customer experience",
                "revenue intelligence", "brand systems", "marketing operations"
            ],
            "weight": 0.7
        },
        
        "TECH": {
            "name": "Technical-Systems", 
            "description": "Distributed architecture and infrastructure",
            "keywords": [
                "distributed architecture", "container", "deployment",
                "api design", "service mesh", "security framework",
                "infrastructure automation", "microservices", "cloud native"
            ],
            "weight": 0.7
        },
        
        "COG": {
            "name": "Cognitive-Science",
            "description": "Memory, learning, and attention systems",
            "keywords": [
                "memory systems", "recall patterns", "learning adaptation",
                "attention management", "decision making", "embodied cognition",
                "cognitive science", "neural networks", "brain systems"
            ],
            "weight": 0.7
        },
        
        "STRAT": {
            "name": "Strategic-Applications",
            "description": "Competitive positioning and platform strategy",
            "keywords": [
                "competitive positioning", "platform strategy", "market timing",
                "network effects", "innovation diffusion", "strategic framework",
                "competitive advantage", "platform development"
            ],
            "weight": 0.7
        }
    },
    
    "coherence_levels": {
        5: "Very strong philosophical alignment across multiple principles",
        4: "Strong expression of core principles with clear applications",
        3: "Moderate philosophical content with some principle manifestation",
        2: "Weak philosophical content but supports themes",
        1: "Minimal philosophical content, preserved for completeness"
    },

    "readiness_thresholds": {
        "publication_ready": 3.5,
        "cross_reference_eligible": 2.8,
        "cluster_priority": 2.5,
        "integration_minimum": 2.0
    },
    
    "persona_mappings": {
        "SHM": ["systems_architect", "field_decision_maker"],
        "TUD": ["future_sensing_executive", "distributed_researcher"],
        "IIP": ["identity_fracturer", "context_aware_consumer"],
        "AID": ["systems_architect", "distributed_researcher"],
        "DHG": ["systems_architect", "field_decision_maker"],
        "NET": ["network_architect", "protocol_designer", "graph_theorist"]
    }
}