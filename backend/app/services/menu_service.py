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

    def create_menu_item(self, category_id, name, description, price, is_available=True, image_url=None):
        """
        Validates and creates a new menu item.
        """
        if not name or not name.strip():
            raise ValueError("Item name cannot be empty")

        try:
            category_id = int(category_id)
        except (ValueError, TypeError):
            raise ValueError("Invalid category_id: must be an integer")

        category = self.menu_dao.get_category_by_id(category_id)
        if not category:
            raise ValueError(f"Category {category_id} does not exist")

        try:
            dec_price = Decimal(str(price))
            if dec_price < 0:
                raise ValueError("Price cannot be negative")
        except Exception as e:
            if isinstance(e, ValueError):
                raise
            raise ValueError("Invalid price: must be a valid number")

        item_id = self.menu_dao.create_item(
            category_id=category_id,
            name=name.strip(),
            description=description,
            price=float(dec_price),
            is_available=1 if is_available else 0,
            image_url=image_url
        )
        return self.get_item_by_id(item_id)

    def update_menu_item(self, item_id, fields: dict):
        """
        Validates and updates an existing menu item.
        """
        item = self.get_item_by_id(item_id)
        if not item:
            raise LookupError(f"Menu item {item_id} not found")

        cleaned = {}
        if "name" in fields:
            name = fields["name"]
            if not name or not str(name).strip():
                raise ValueError("Item name cannot be empty")
            cleaned["name"] = str(name).strip()

        if "category_id" in fields:
            try:
                cid = int(fields["category_id"])
            except (ValueError, TypeError):
                raise ValueError("Invalid category_id")
            if not self.menu_dao.get_category_by_id(cid):
                raise ValueError(f"Category {cid} does not exist")
            cleaned["category_id"] = cid

        if "price" in fields:
            try:
                dec_price = Decimal(str(fields["price"]))
                if dec_price < 0:
                    raise ValueError("Price cannot be negative")
                cleaned["price"] = float(dec_price)
            except Exception as e:
                if isinstance(e, ValueError):
                    raise
                raise ValueError("Invalid price: must be a valid number")

        if "description" in fields:
            cleaned["description"] = fields["description"]

        if "image_url" in fields:
            cleaned["image_url"] = fields["image_url"]

        if "is_available" in fields:
            cleaned["is_available"] = 1 if fields["is_available"] else 0

        if cleaned:
            self.menu_dao.update_item(item_id, cleaned)

        return self.get_item_by_id(item_id)

    def update_item_availability(self, item_id, is_available: bool):
        """
        Toggles or sets the availability of an item.
        """
        item = self.get_item_by_id(item_id)
        if not item:
            raise LookupError(f"Menu item {item_id} not found")

        self.menu_dao.update_availability(item_id, is_available)
        return self.get_item_by_id(item_id)
