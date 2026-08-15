from app.shared.events import DomainEvent

async def handle(event: DomainEvent) -> None:
    # Runtime business wiring is performed by the composition root.
    return None
