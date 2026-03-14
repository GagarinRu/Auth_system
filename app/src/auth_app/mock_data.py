MOCK_DOCUMENTS = [
    {"id": 1, "title": "Договор поставки", "owner_id": 1, "content": "Содержимое договора..."},
    {"id": 2, "title": "Акт выполненных работ", "owner_id": 2, "content": "Содержимое акта..."},
    {"id": 3, "title": "Счет на оплату", "owner_id": 1, "content": "Содержимое счета..."},
]

MOCK_ORDERS = [
    {"id": 1, "description": "Заказ №1", "owner_id": 1, "status": "completed", "total": 15000},
    {"id": 2, "description": "Заказ №2", "owner_id": 2, "status": "pending", "total": 25000},
    {"id": 3, "description": "Заказ №3", "owner_id": 1, "status": "cancelled", "total": 8000},
]

MOCK_PRODUCTS = [
    {"id": 1, "name": "Ноутбук", "price": 50000, "stock": 10},
    {"id": 2, "name": "Смартфон", "price": 30000, "stock": 25},
    {"id": 3, "name": "Планшет", "price": 20000, "stock": 15},
]
