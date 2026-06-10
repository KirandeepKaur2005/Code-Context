from llm import generate_response
from retriever import retrieve

def ask(repo_name, question):
    try:
        chunks = retrieve(
            repo_name,
            question,
            top_k=5
        )
        print("Chunks generated in rag.py")
    except Exception as e:
        print("Error while retrieving chunks in rag.py: ")
        print(e) 
        return "Failed to retrieve repository context."
    
    print("chunks: ", chunks)

    context = []
    print("Generating the real context")
    for chunk in chunks:
        context.append(
            f"""
                File: {chunk[1]}
                Language: {chunk[2]}
                Lines: {chunk[3]}-{chunk[4]}

                {chunk[5]}
            """
        )

    final_context = "\n".join(context)

    print("Context length:", len(final_context))
    print("Context length:", len(chunks))

    print("Generating response... ")
    try:
        response = generate_response(
            question,
            final_context
        )
    except Exception as e:
        print(" --- Error generated in rag.py during response generation")
        print(e)
        return "Failed to generate response."

    return response