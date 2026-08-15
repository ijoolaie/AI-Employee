export const DOMAIN_EVENTS = {
  ORDER_COMPLETED: "commerce.order.completed",
  ORDER_CANCELLED: "commerce.order.cancelled",
  INVOICE_ISSUED: "billing.invoice.issued",
  PAYMENT_SUCCEEDED: "billing.payment.succeeded",
  CUSTOMER_CREATED: "crm.customer.created",
  DOCUMENT_INGESTED: "knowledge.document.ingested",
  WORKFLOW_RUN_COMPLETED: "workflow.run.completed",
  EMPLOYEE_RUN_COMPLETED: "employee.run.completed",
} as const;

export type DomainEventName = typeof DOMAIN_EVENTS[keyof typeof DOMAIN_EVENTS];
