@admin @file_management
Feature: Upload A Csv File Of Products
  I can bulk-import inventory

  @happy_path @smoke
  Scenario: Successfully upload a csv file of products
    Given the admin is on the relevant page
    When the admin uploads a CSV file of products
    Then the system should I can bulk-import inventory

  @negative @error_handling
  Scenario: Unsuccessful upload with invalid data
    Given the admin is on the relevant page
    When the admin tries to upload with invalid a CSV file of products
    Then the system should display an appropriate error message
    And the admin should remain on the current page

  @edge_case @file_management
  Scenario: Upload file exceeding maximum size
    Given the admin is on the upload page
    When the admin selects a file larger than the maximum allowed size
    And the admin clicks the upload button
    Then the system should display a file size exceeded error
    And the file should not be uploaded

  @edge_case @file_management
  Scenario: Upload unsupported file format
    Given the admin is on the upload page
    When the admin selects a file with an unsupported format
    And the admin clicks the upload button
    Then the system should display an unsupported format error

  @edge_case @file_management
  Scenario: Upload file with zero bytes
    Given the admin is on the upload page
    When the admin selects an empty file with zero bytes
    And the admin clicks the upload button
    Then the system should reject the empty file

  @edge_case @concurrency
  Scenario: Concurrent access handling
    Given multiple admins are accessing the same resource simultaneously
    When they perform conflicting operations
    Then the system should handle concurrent access gracefully
    And data integrity should be maintained
