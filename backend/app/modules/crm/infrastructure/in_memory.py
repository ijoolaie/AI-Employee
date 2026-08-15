from __future__ import annotations

class InMemoryCustomerRepository:
    def __init__(self):
        self.items = {}

    async def save(self, customer):
        self.items[str(customer.id)] = customer
        return customer

    async def get(self, customer_id):
        return self.items.get(customer_id)

class InMemoryConversationRepository:
    def __init__(self):
        self.items = {}

    async def save(self, conversation):
        self.items[str(conversation.id)] = conversation
        return conversation

    async def get(self, conversation_id):
        return self.items.get(conversation_id)

class InMemoryIdentityResolver:
    def __init__(self):
        self.by_email = {}

    async def resolve(self, email, external_id):
        if email and email in self.by_email:
            return {"customer_id": self.by_email[email]}
        return None
