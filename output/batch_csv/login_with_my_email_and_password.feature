@user @authentication @notifications
Feature: Login With My Email And Password
  I can access my account

  Background:
    Given the user is on the application
    And my email and password so that i can access my account

  @happy_path @smoke
  Scenario: Successfully login with my email and password
    Given my email and password so that i can access my account
    When the user logins with my email and password
    Then the system should I can access my account

  @negative @error_handling
  Scenario: Unsuccessful login with invalid data
    Given the user is on the relevant page
    When the user tries to login with invalid with my email and password
    Then the system should display an appropriate error message
    And the user should remain on the current page

  @validation @boundary
  Scenario: Validate empty with my email and password
    Given the user is on the relevant page
    When the user leaves the with my email and password field empty
    And the user submits the form
    Then the system should display a validation error for the required field

  @validation @boundary
  Scenario: Validate maximum length for with my email and password
    Given the user is on the relevant page
    When the user enters extremely long text in the with my email and password field
    And the user submits the form
    Then the system should handle the input gracefully

  @security @edge_case
  Scenario: Login with SQL injection attempt
    Given the user is on the login page
    When the user enters "' OR 1=1 --" as the username
    And the user enters any value as the password
    And the user clicks the login button
    Then the system should reject the input
    And the system should not expose any database errors

  @security @edge_case
  Scenario: Login with XSS attempt
    Given the user is on the login page
    When the user enters "<script>alert('xss')</script>" as the username
    And the user clicks the login button
    Then the system should sanitize the input
    And no script should be executed

  @security @edge_case
  Scenario: Login with account lockout after multiple failures
    Given the user is on the login page
    When the user enters invalid credentials 5 times consecutively
    Then the account should be temporarily locked
    And the system should display an account lockout message

  @security @edge_case
  Scenario: Session timeout handling
    Given the user has been inactive for an extended period
    When the user tries to perform an action
    Then the system should redirect to the login page
    And the system should display a session expired message

  @edge_case @concurrency
  Scenario: Concurrent access handling
    Given multiple users are accessing the same resource simultaneously
    When they perform conflicting operations
    Then the system should handle concurrent access gracefully
    And data integrity should be maintained
