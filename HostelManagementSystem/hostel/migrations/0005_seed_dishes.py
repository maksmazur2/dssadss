from django.db import migrations


def seed_dishes(apps, schema_editor):
    Dish = apps.get_model('hostel', 'Dish')
    data = [
        # Breakfast
        ("Spinach & Feta Egg Wrap", "Scrambled eggs, spinach, feta in a whole‑wheat wrap.", "egg, dairy, wheat", "vegetarian, high-protein"),
        ("Greek Yogurt Parfait", "Yogurt, berries, granola, honey.", "dairy, wheat (granola), tree nuts (possible)", "vegetarian"),
        ("Oatmeal with Apples & Almonds", "Steel-cut oats, spiced apples, toasted almonds.", "tree nuts", "vegan option, high-fiber"),
        ("Banana Peanut Butter Overnight Oats", "Rolled oats, banana, peanut butter.", "peanuts", "vegetarian"),
        ("Veggie Breakfast Burrito", "Eggs, black beans, peppers, cheese, salsa in tortilla.", "egg, dairy, wheat", "vegetarian"),
        ("Smoked Salmon Bagel", "Whole-grain bagel, salmon, cream cheese, capers.", "fish, dairy, wheat", "pescatarian"),
        ("Tofu Scramble & Hash", "Crumbled tofu, peppers, potatoes, turmeric.", "soy", "vegan, gluten-free"),
        ("Chia Pudding with Mango", "Chia seeds, coconut milk, mango.", "", "vegan, gluten-free"),
        ("Blueberry Protein Pancakes", "Whole-wheat protein pancakes, blueberries.", "egg, dairy, wheat", "high-protein"),
        ("Cottage Cheese Bowl", "Cottage cheese, cucumber, tomato, olive oil.", "dairy", "vegetarian, high-protein, low-carb"),
        # Lunch
        ("Grilled Chicken Grain Bowl", "Chicken, quinoa, roasted veggies, tahini.", "sesame", "high-protein, gluten-free"),
        ("Lentil & Sweet Potato Curry", "Lentils, sweet potato, tomatoes, spices.", "", "vegan, gluten-free"),
        ("Turkey Avocado Sandwich", "Turkey, avocado, tomato, whole-wheat bread.", "wheat", "high-protein, dairy-free"),
        ("Falafel Pita with Tzatziki", "Baked falafel, greens, tzatziki in pita.", "wheat, dairy, sesame", "vegetarian"),
        ("BBQ Tofu Wrap", "Marinated tofu, slaw, BBQ sauce in tortilla.", "soy, wheat", "vegan"),
        ("Caprese Pasta Salad", "Pasta, mozzarella, tomato, basil.", "dairy, wheat", "vegetarian"),
        ("Shrimp Stir-Fry with Brown Rice", "Shrimp, broccoli, peppers, tamari.", "shellfish, soy", "gluten-free, high-protein"),
        ("Chickpea Shawarma Bowl", "Spiced chickpeas, rice, cucumbers, tahini.", "sesame", "vegan, gluten-free"),
        ("Beef & Veggie Stir-Fry", "Lean beef, snap peas, carrots, rice.", "soy (sauce)", "high-protein, dairy-free"),
        ("Roasted Veggie & Hummus Plate", "Roasted veggies, hummus, pita.", "sesame, wheat", "vegan"),
        # Dinner
        ("Baked Salmon with Herbed Rice", "Salmon, lemon, dill rice.", "fish", "high-protein, gluten-free"),
        ("Chicken Tikka with Basmati", "Grilled yogurt-marinated chicken, rice.", "dairy", "high-protein, gluten-free"),
        ("Mushroom Risotto", "Arborio rice, mushrooms, parmesan.", "dairy", "vegetarian"),
        ("Veggie Chili", "Beans, peppers, tomatoes, corn.", "", "vegan, gluten-free, high-protein"),
        ("Pasta Primavera", "Pasta with seasonal vegetables, light cream.", "dairy, wheat", "vegetarian"),
        ("Stir-Fried Udon with Tofu", "Udon noodles, tofu, veggies, soy-ginger sauce.", "soy, wheat, sesame", "vegan option, high-carb"),
        ("Lemon Herb Roast Chicken & Potatoes", "Roast chicken, potatoes, green beans.", "", "high-protein, gluten-free"),
        ("Paneer Butter Masala with Rice", "Paneer in tomato cream sauce, rice.", "dairy", "vegetarian, gluten-free"),
        ("Blackened Catfish with Slaw", "Catfish, cabbage slaw.", "fish, egg (slaw mayo)", "dairy-free"),
        ("Butternut Squash & Kale Farro Bowl", "Roasted squash, kale, farro, pumpkin seeds.", "wheat (farro)", "vegan"),
    ]
    for name, desc, allergens, tags in data:
        Dish.objects.get_or_create(
            name=name,
            defaults={
                "description": desc,
                "allergens": allergens,
                "tags": tags,
            },
        )


def unseed_dishes(apps, schema_editor):
    Dish = apps.get_model('hostel', 'Dish')
    names = [
        "Spinach & Feta Egg Wrap",
        "Greek Yogurt Parfait",
        "Oatmeal with Apples & Almonds",
        "Banana Peanut Butter Overnight Oats",
        "Veggie Breakfast Burrito",
        "Smoked Salmon Bagel",
        "Tofu Scramble & Hash",
        "Chia Pudding with Mango",
        "Blueberry Protein Pancakes",
        "Cottage Cheese Bowl",
        "Grilled Chicken Grain Bowl",
        "Lentil & Sweet Potato Curry",
        "Turkey Avocado Sandwich",
        "Falafel Pita with Tzatziki",
        "BBQ Tofu Wrap",
        "Caprese Pasta Salad",
        "Shrimp Stir-Fry with Brown Rice",
        "Chickpea Shawarma Bowl",
        "Beef & Veggie Stir-Fry",
        "Roasted Veggie & Hummus Plate",
        "Baked Salmon with Herbed Rice",
        "Chicken Tikka with Basmati",
        "Mushroom Risotto",
        "Veggie Chili",
        "Pasta Primavera",
        "Stir-Fried Udon with Tofu",
        "Lemon Herb Roast Chicken & Potatoes",
        "Paneer Butter Masala with Rice",
        "Blackened Catfish with Slaw",
        "Butternut Squash & Kale Farro Bowl",
    ]
    Dish.objects.filter(name__in=names).delete()


class Migration(migrations.Migration):

    dependencies = [
        ('hostel', '0004_dish_dailymenu_order_orderitem'),
    ]

    operations = [
        migrations.RunPython(seed_dishes, unseed_dishes),
    ]
