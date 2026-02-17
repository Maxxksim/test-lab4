Feature: Product

  Scenario: Availability check exact amount
    Given Product named "Phone" with price 100 and availability 5
    When I check product availability for amount 5
    Then Availability result should be True

  Scenario: Availability check bigger amount
    Given Product named "Phone" with price 100 and availability 5
    When I check product availability for amount 6
    Then Availability result should be False

  Scenario: Buying product decreases availability
    Given Product named "Phone" with price 100 and availability 10
    When I buy product amount 4
    Then Product availability should be 6

  Scenario: Availability check with None
    Given Product named "Phone" with price 100 and availability 5
    When I check product availability for None
    Then Availability check should fail
