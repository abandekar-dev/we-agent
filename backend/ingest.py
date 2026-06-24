"""Ingest knowledge base content from Work Engineering repos."""

from knowledge import build_index

CONTENT_SOURCES = [
    # Work Engineering Resource Hub (landing page + docs)
    "/Users/aniketbandekar/Desktop/Work_Eng/Landing Page",
    # Work Engineering root docs
    "/Users/aniketbandekar/Desktop/Work_Eng/Discernment Framework",
    "/Users/aniketbandekar/Desktop/Work_Eng/Implementation playbooks",
    "/Users/aniketbandekar/Desktop/Work_Eng/Pattern Libraries",
    # Work Design Pod (agents, skills, engagements)
    "/Users/aniketbandekar/work-design-pod/.claude/agents",
    "/Users/aniketbandekar/work-design-pod/.claude/skills",
    "/Users/aniketbandekar/work-design-pod/docs",
    "/Users/aniketbandekar/work-design-pod/engagements",
]

if __name__ == "__main__":
    print("Building Work Engineering knowledge base index...\n")
    print("Content sources:")
    for src in CONTENT_SOURCES:
        print(f"  - {src}")
    print()
    build_index(CONTENT_SOURCES)
    print("\nDone! Knowledge base is ready.")
