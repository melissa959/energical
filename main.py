from src.chat import ChatManager

chat = ChatManager()

print("\n=== PHASE 4A PART 1 + PHASE 3 TEST ===\n")

while True:
    user = input("You: ").strip()
    if user.lower() == "exit":
        break

    result = chat.send_message(user)

    print(f"\nTURN:   {result['turn_count']}")
    print(f"MEMORY: {result['memory']}")
    print(f"QUERY:  {result['retrieval_query']}")

    print("\nRETRIEVED PRODUCTS:")
    products = result["retrieved_products"]
    if not products:
        print("  No products found.")
    else:
        for i, p in enumerate(products, 1):
            print(f"  {i}. {p['metadata']['nom']} "
                  f"| {p['metadata']['prix']} DA "
                  f"| Stock: {p['metadata']['statut_stock']}")
    print()