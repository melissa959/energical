from decision_tree import DecisionTree

tree = DecisionTree()

user_info = {
    "usage": "Maison",
    "energie": "Gaz"
}

result = tree.ready(
    "chaudiere",
    user_info
)

print(result)