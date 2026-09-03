export const demoScenarios = [
  {
    id: 'recoverable-payment',
    label: 'Recoverable Payment Failure',
    eventType: 'payment_failure',
    amount: '150.00',
    paymentMethod: 'Card',
    failureReason: 'network_error',
    description: 'Temporary bank or network interruption with good recovery potential',
  },
  {
    id: 'checkout-abandonment',
    label: 'Checkout Abandonment',
    eventType: 'checkout_abandonment',
    amount: '180.00',
    paymentMethod: 'Card',
    failureReason: 'cart_hesitation',
    description: 'Customer left an active cart and is highly likely to re-engage',
  },
  {
    id: 'fraud-safety',
    label: 'Fraud Safety Case',
    eventType: 'payment_failure',
    amount: '500.00',
    paymentMethod: 'Card',
    failureReason: 'fraud_hold',
    description: 'High-risk condition that requires manual review, not automation',
  },
] as const
