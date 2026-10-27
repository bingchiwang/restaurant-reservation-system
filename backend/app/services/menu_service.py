from decimal import Decimal

class MenuService:
    def __init__(self, menu_dao):
        self.menu_dao = menu_dao

    def get_categories(self, status="ACTIVE"):
        """
        Returns active menu categories.
        """
        return self.menu_dao.get_categories(status=status)

    def get_menu_items(self, category_id=None, only_available=True):
        """
        Returns menu items matching filter criteria.
        Ensures prices are properly formatted as numbers.
        """
        if category_id is not None:
            try:
                category_id = int(category_id)
            except (ValueError, TypeError):
                raise ValueError("Invalid category_id: must be an integer")

        items = self.menu_dao.get_items(category_id=category_id, only_available=only_available)

        # Ensure price is formatted as float for JSON serialization
        for item in items:
            if isinstance(item["price"], Decimal):
                item["price"] = float(item["price"])
            elif isinstance(item["price"], (int, float, str)):
                item["price"] = float(item["price"])

            item["is_available"] = bool(item["is_available"])

        return items

    def get_item_by_id(self, item_id):
        """
        Retrieves a single item with formatted price.
        """
        try:
            item_id = int(item_id)
        except (ValueError, TypeError):
            raise ValueError("Invalid item_id: must be an integer")

        item = self.menu_dao.get_item_by_id(item_id)
        if not item:
            return None

        if isinstance(item["price"], Decimal):
            item["price"] = float(item["price"])
        else:
            item["price"] = float(item["price"])
        item["is_available"] = bool(item["is_available"])

        return item
