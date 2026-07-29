import os
import sys
import anthropic
from knowledge_base import build_knowledge_base, search_modules, format_context

SYSTEM_PROMPT = """You are an expert Oracle Fusion Data Conversion AI assistant with deep knowledge of:
- FBDI (File Based Data Import), FBL (File Based Loader), ADFdi Spreadsheet Loader
- SOAP Web Services and REST APIs for Oracle Fusion
- PL/SQL development: APEX_WEB_SERVICE, DBMS_SCHEDULER, packages
- Oracle ATP Database, BI Publisher Report Service & Scheduler Service
- End-to-end data migration automation frameworks

You have access to a 21-module Fusion Data Conversion knowledge base with real PL/SQL packages, SQL scripts, and SOAP/REST examples.
Answer clearly and accurately. For code, follow the patterns from the knowledge base. Reference module numbers when relevant."""


def chat(kb, client, history, user_input):
    modules = search_modules(kb, user_input, top_k=3)
    context = format_context(kb, modules)

    system = SYSTEM_PROMPT
    if context:
        system += f"\n\n--- KNOWLEDGE BASE CONTEXT ---\n{context}"

    history.append({"role": "user", "content": user_input})

    response = client.messages.create(
        model="claude-sonnet-5",
        max_tokens=2048,
        system=system,
        messages=history,
    )
    answer = response.content[0].text
    history.append({"role": "assistant", "content": answer})

    if modules:
        ref = ", ".join([f"Module {m}" for m in modules])
        print(f"\n[Referencing: {ref}]")

    return answer


def main():
    api_key = os.environ.get("ANTHROPIC_API_KEY", "").strip()
    if not api_key:
        api_key = input("Enter your Anthropic API key: ").strip()
    if not api_key:
        print("API key required.")
        sys.exit(1)

    print("\nLoading Fusion knowledge base...")
    kb = build_knowledge_base()
    print(f"Loaded {len(kb)} modules.\n")

    client = anthropic.Anthropic(api_key=api_key)
    history = []

    print("=" * 60)
    print("  Oracle Fusion Data Conversion Agent")
    print("  Type your question | 'quit' to exit | 'clear' to reset")
    print("=" * 60)

    while True:
        try:
            user_input = input("\nYou: ").strip()
        except (EOFError, KeyboardInterrupt):
            print("\nGoodbye!")
            break

        if not user_input:
            continue
        if user_input.lower() == "quit":
            print("Goodbye!")
            break
        if user_input.lower() == "clear":
            history = []
            print("Chat cleared.")
            continue

        try:
            answer = chat(kb, client, history, user_input)
            print(f"\nAgent: {answer}\n")
        except anthropic.AuthenticationError:
            print("Invalid API key.")
            break
        except Exception as e:
            print(f"Error: {e}")


if __name__ == "__main__":
    main()
