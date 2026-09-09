@buyer @checkout @shopping_cart
Feature: Add Items To My Shopping Cart And Proceed To Checkout
  I can purchase products

  @happy_path @smoke
  Scenario: Successfully add items to my shopping cart and proceed to checkout
    Given the buyer is on the relevant page
    When the buyer adds items to my shopping cart and proceed to checkout
    And the buyer checkouts
    Then the system should I can purchase products

  @negative @error_handling
  Scenario: Unsuccessful add with invalid data
    Given the buyer is on the relevant page
    When the buyer tries to add with invalid items to my shopping cart and proceed to checkout
    Then the system should display an appropriate error message
    And the buyer should remain on the current page

  @validation @boundary
  Scenario: Validate empty items to my shopping cart and proceed to checkout
    Given the buyer is on the relevant page
    When the buyer leaves the items to my shopping cart and proceed to checkout field empty
    And the buyer submits the form
    Then the system should display a validation error for the required field

  @validation @boundary
  Scenario: Validate maximum length for items to my shopping cart and proceed to checkout
    Given the buyer is on the relevant page
    When the buyer enters extremely long text in the items to my shopping cart and proceed to checkout field
    And the buyer submits the form
    Then the system should handle the input gracefully

  @edge_case @payments
  Scenario: Payment with expired card
    Given the buyer is on the payment page
    When the buyer enters an expired credit card
    And the buyer submits the payment
    Then the system should display a card expired error
    And the payment should not be processed

  @edge_case @payments
  Scenario: Payment with insufficient funds
    Given the buyer is on the payment page
    When the buyer submits payment with insufficient funds
    Then the system should display an insufficient funds error
    And the order should remain in pending state

  @edge_case @payments @timeout
  Scenario: Payment network timeout
    Given the buyer is on the payment page
    When the buyer submits the payment
    And the payment gateway times out
    Then the system should display a timeout message
    And the system should not charge the buyer without confirmation

  @edge_case @concurrency
  Scenario: Concurrent access handling
    Given multiple buyers are accessing the same resource simultaneously
    When they perform conflicting operations
    Then the system should handle concurrent access gracefully
    And data integrity should be maintained
