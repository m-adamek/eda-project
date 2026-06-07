# Shared search strategy for all bibliographic sources.
# The collectors for OpenAlex, Crossref and PubMed import this file so that every
# source uses the same conceptual query groups. This keeps the dataset comparable:
# if "iam_architecture" means one thing in OpenAlex, it means the same thing in
# Crossref and PubMed.
QUERY_GROUPS = {
    # Core identity-representation terms from the article draft.
    # These queries look for papers about digital/user identity and the distinction
    # between legal or formal identity and displayed/social identity.
    "identity_overlay_core": [
        '"digital identity" "information systems"',
        '"user identity" "information systems"',
        '"identity representation" system',
        '"display identity"',
        '"legal identity" "digital identity"',
        '"preferred name" system',
        'pronouns "information system"',
    ],

    # Terms linked to the lived organisational problem: transgender employees,
    # misgendering, deadnaming and outing. This group helps connect technical
    # system design with concrete risks for users.
    "transgender_organizational_systems": [
        'transgender workplace system',
        'transgender "human resource"',
        'transgender "information system"',
        'misgendering workplace',
        'deadnaming system',
        'outing transgender workplace',
    ],

    # Technical identity-management terms. IAM means Identity and Access Management:
    # systems/processes that create accounts, assign permissions, synchronise user
    # attributes and manage the identity lifecycle inside an organisation.
    "iam_architecture": [
        '"identity and access management" organization',
        '"identity management" "human resource"',
        '"identity lifecycle management"',
        '"federated identity" organization',
        'provisioning "identity management"',
        '"attribute based access control" identity',
    ],

    # Design and values vocabulary used in the theoretical part of the article.
    # This group searches for work that frames identity systems through inclusive,
    # human-centred, participatory or Value Sensitive Design.
    "inclusive_design_values": [
        '"value sensitive design" identity',
        '"inclusive design" identity',
        '"human centered design" identity system',
        '"participatory design" transgender',
        '"trans technology" design',
    ],

    # Terms for the article's second example: legal/relational status. These
    # queries look for rigid administrative data models around marriage, civil
    # status and legal status.
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
    # Generators are memory-friendly and convenient for loops over search terms.
    for group, queries in QUERY_GROUPS.items():
        for query in queries:
            yield group, query
