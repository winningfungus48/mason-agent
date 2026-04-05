"""
agents/lists_agent.py
---------------------
Smart list manager for Mason's Personal Agent.
Handles all named lists including grocery with category support.
"""

import os
import anthropic
from core.config import DOCUMENTS_DIR, LISTS, GROCERY_CATEGORIES
from core.display import wrap_display

client = anthropic.Anthropic()

GROCERY_CATEGORY_HINTS = {
    "Frozen":            ["frozen", "ice cream", "pizza", "edamame", "tater tots", "waffles", "nuggets", "fish sticks"],
    "Meat":              ["chicken", "beef", "ground beef", "steak", "pork", "bacon", "sausage", "shrimp", "salmon", "turkey", "lamb", "tilapia", "tuna", "fish", "deli meat", "hot dogs", "lunchmeat"],
    "Produce":           ["apple", "banana", "orange", "lettuce", "spinach", "kale", "tomato", "onion", "garlic", "pepper", "broccoli", "carrot", "celery", "avocado", "lime", "lemon", "mushroom", "zucchini", "cucumber", "potato", "sweet potato", "corn", "mango", "strawberry", "blueberry", "grape", "herbs", "cilantro", "parsley", "basil", "ginger", "jalapeño"],
    "Spices/Condiments": ["salt", "pepper", "cumin", "paprika", "oregano", "thyme", "cinnamon", "chili powder", "cayenne", "garlic powder", "onion powder", "turmeric", "ketchup", "mustard", "mayo", "mayonnaise", "soy sauce", "hot sauce", "sriracha", "worcestershire", "vinegar", "salsa", "ranch", "bbq sauce", "olive oil", "vegetable oil", "sesame oil", "honey", "sugar", "brown sugar"],
    "Pantry":            ["pasta", "rice", "quinoa", "oats", "bread", "tortilla", "flour", "baking powder", "baking soda", "beans", "lentils", "canned", "tomato sauce", "broth", "stock", "soup", "crackers", "chips", "cereal", "granola", "peanut butter", "jam", "jelly", "syrup", "coffee", "tea", "protein powder", "nuts", "almonds", "walnuts", "raisins"],
    "Dairy/Deli":        ["milk", "cheese", "butter", "cream", "yogurt", "eggs", "sour cream", "cream cheese", "cottage cheese", "whipping cream", "half and half", "parmesan", "mozzarella", "cheddar"],
    "Pet":               ["dog food", "cat food", "dog treats", "cat treats", "pet", "pedigree", "purina", "blue buffalo", "kibble", "litter", "flea", "tick", "heartworm"],
    "NonFood":           ["vitamin", "supplement", "shampoo", "conditioner", "soap", "lotion", "sunscreen", "deodorant", "toothpaste", "toothbrush", "medicine", "ibuprofen", "tylenol", "advil", "allergy", "band aid", "bandage", "toilet paper", "paper towel", "dish soap", "laundry", "detergent", "bleach", "trash bag", "ziplock", "foil", "plastic wrap", "razor", "shaving", "makeup", "skincare", "face wash"],
}

LIST_EMOJIS = {
    "grocery": "🛒", "chores": "🏠", "workout": "💪",
    "ai_research": "🤖", "errands": "🏃", "goals_90day": "🎯",
    "entertainment": "🎬", "gift_ideas": "🎁", "wishlist": "🛍️",
    "restaurants": "🍽️", "shower_thoughts": "💡",
}


def resolve_list(list_name):
    """Fuzzy match list name to filename."""
    name = list_name.lower().strip()
    if name in LISTS:
        return LISTS[name], name
    for key in LISTS:
        if name in key or key in name:
            return LISTS[key], key
    return None, None


def guess_grocery_category(item):
    item_lower = item.lower()
    for category, keywords in GROCERY_CATEGORY_HINTS.items():
        for keyword in keywords:
            if keyword in item_lower:
                return category
    return None


def categorize_with_claude(item):
    response = client.messages.create(
        model="claude-sonnet-4-20250514",
        max_tokens=50,
        messages=[{"role": "user", "content":
            f"Which single grocery category does '{item}' belong to? "
            f"Choose ONLY one: Frozen, Meat, Produce, Spices/Condiments, Pantry, Dairy/Deli, Pet, NonFood. "
            f"Reply with just the category name, nothing else."}]
    )
    return response.content[0].text.strip()


def format_grocery_list(lines):
    categorized = {cat: [] for cat in GROCERY_CATEGORIES}
    uncategorized = []
    for line in lines:
        matched = False
        for cat in GROCERY_CATEGORIES:
            if line.startswith(f"[{cat}]"):
                categorized[cat].append(line[len(f"[{cat}]"):].strip())
                matched = True
                break
        if not matched:
            uncategorized.append(line)

    output = "🛒 GROCERY LIST:\n"
    for cat in GROCERY_CATEGORIES:
        if categorized[cat]:
            output += f"\n{cat}:\n" + "\n".join(f"  • {item}" for item in categorized[cat]) + "\n"
    if uncategorized:
        output += "\nOther:\n" + "\n".join(f"  • {item}" for item in uncategorized)
    return output.strip()


def list_add(list_name, item):
    try:
        filepath, resolved = resolve_list(list_name)
        if not filepath:
            return f"Unknown list '{list_name}'. Available lists: {', '.join(LISTS.keys())}"
        print(f"  [TOOL] Adding to {resolved}: {item}")
        full_path = os.path.join(DOCUMENTS_DIR, filepath)

        if resolved == "grocery":
            category = guess_grocery_category(item) or categorize_with_claude(item)
            if category not in GROCERY_CATEGORIES:
                category = "Pantry"
            tagged_item = f"[{category}] {item.strip()}"
            with open(full_path, "a", encoding="utf-8") as f:
                f.write(tagged_item + "\n")
            return f"✅ Added to grocery [{category}]: {item}"
        else:
            with open(full_path, "a", encoding="utf-8") as f:
                f.write(item.strip() + "\n")
            return f"✅ Added to {resolved}: {item}"
    except Exception as e:
        return f"Error adding to list: {str(e)}"


def list_view(list_name, filter_by=None):
    try:
        filepath, resolved = resolve_list(list_name)
        if not filepath:
            return f"Unknown list '{list_name}'. Available lists: {', '.join(LISTS.keys())}"
        print(f"  [TOOL] Viewing {resolved}")
        full_path = os.path.join(DOCUMENTS_DIR, filepath)
        if not os.path.exists(full_path):
            return f"Your {resolved} list is empty."
        with open(full_path, "r", encoding="utf-8") as f:
            lines = [l.strip() for l in f.readlines() if l.strip()]
        if not lines:
            return f"Your {resolved} list is empty."

        if resolved == "grocery":
            if filter_by:
                lines = [l for l in lines if filter_by.upper() in l.upper()]
                if not lines:
                    return f"No items matching '{filter_by}' in your grocery list."
            return wrap_display(format_grocery_list(lines))

        if filter_by:
            lines = [l for l in lines if filter_by.upper() in l.upper()]
            if not lines:
                return f"No items matching '{filter_by}' in your {resolved} list."
        return wrap_display(f"📋 {resolved.upper()} LIST:\n" + "\n".join(f"• {l}" for l in lines))
    except Exception as e:
        return f"Error viewing list: {str(e)}"


def list_remove(list_name, item):
    try:
        filepath, resolved = resolve_list(list_name)
        if not filepath:
            return f"Unknown list '{list_name}'. Available lists: {', '.join(LISTS.keys())}"
        print(f"  [TOOL] Removing from {resolved}: {item}")
        full_path = os.path.join(DOCUMENTS_DIR, filepath)
        if not os.path.exists(full_path):
            return f"Your {resolved} list is empty."
        with open(full_path, "r", encoding="utf-8") as f:
            lines = f.readlines()
        new_lines = [l for l in lines if item.lower() not in l.lower()]
        if len(new_lines) == len(lines):
            return f"Could not find '{item}' in your {resolved} list."
        with open(full_path, "w", encoding="utf-8") as f:
            f.writelines(new_lines)
        return f"✅ Removed from {resolved}: {item}"
    except Exception as e:
        return f"Error removing from list: {str(e)}"


def list_clear(list_name):
    try:
        filepath, resolved = resolve_list(list_name)
        if not filepath:
            return f"Unknown list '{list_name}'. Available lists: {', '.join(LISTS.keys())}"
        print(f"  [TOOL] Clearing {resolved}")
        full_path = os.path.join(DOCUMENTS_DIR, filepath)
        with open(full_path, "w", encoding="utf-8") as f:
            f.write("")
        return f"✅ {resolved} list cleared."
    except Exception as e:
        return f"Error clearing list: {str(e)}"


def list_show_all():
    try:
        print("  [TOOL] Showing all lists")
        summary = "📋 ALL LISTS:\n"
        for name, filename in LISTS.items():
            full_path = os.path.join(DOCUMENTS_DIR, filename)
            count = 0
            if os.path.exists(full_path):
                with open(full_path, "r", encoding="utf-8") as f:
                    count = len([l for l in f.readlines() if l.strip()])
            emoji = LIST_EMOJIS.get(name, "📝")
            summary += f"{emoji} {name}: {count} item{'s' if count != 1 else ''}\n"
        return wrap_display(summary.strip())
    except Exception as e:
        return f"Error showing lists: {str(e)}"
