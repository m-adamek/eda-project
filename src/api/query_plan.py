
QUERY_GROUPS = {
    "identity_overlay_core": [
        '"digital identity" "information systems"',
        '"user identity" "information systems"',
        '"identity representation" system',
        '"display identity"',
        '"legal identity" "digital identity"',
        '"preferred name" system',
        'pronouns "information system"',
    ],

    "transgender_organizational_systems": [
        'transgender workplace system',
        'transgender "human resource"',
        'transgender "information system"',
        'misgendering workplace',
        'deadnaming system',
        'outing transgender workplace',
    ],

    "iam_architecture": [
        '"identity and access management" organization',
        '"identity management" "human resource"',
        '"identity lifecycle management"',
        '"federated identity" organization',
        'provisioning "identity management"',
        '"attribute based access control" identity',
    ],

    "inclusive_design_values": [
        '"value sensitive design" identity',
        '"inclusive design" identity',
        '"human centered design" identity system',
        '"participatory design" transgender',
        '"trans technology" design',
    ],

    "relational_legal_status": [
        '"same-sex marriage" "information system"',
        '"marital status" "information system"',
        '"civil status" "information system"',
        '"legal status" "information system"',
    ],
}


# Shared output schema.
# APIs return different JSON/XML structures, but every collector converts its
# source-specific response into these columns. This is what makes later merging
# with pandas straightforward.
OUTPUT_COLUMNS = [
    "source_database",
    "external_id",
    "doi",
    "title",
    "year",
    "citations",
    "query_group",
    "query",
    "source",
    "authors",
    "topics",
    "abstract",
]


def iter_queries():
    # This is a generator: it yields one (group, query) pair at a time.
    # Example yielded value:
    #   ("iam_architecture", '"identity lifecycle management"')

    for group, queries in QUERY_GROUPS.items():
        for query in queries:
            yield group, query
