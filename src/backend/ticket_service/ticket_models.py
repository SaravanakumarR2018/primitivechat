from pydantic import BaseModel

class TicketByConversationBase(BaseModel):
    chat_id: str
    message_count: int

class TicketByConversationResponse(BaseModel):
    ticket_id: int
