Feature: Environment Sanity Check
  Scenario: The environment is correctly configured
    Given the automation and infrastructure setup is complete
    When we run the test suite
    Then it should pass without errors
