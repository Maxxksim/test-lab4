Feature: Order

  Scenario: Placing order decreases product availability
    Given Product "Phone" price 100 availability 10
    And Shopping cart with this product amount 3
    When I place order
    Then Product availability becomes 7

  Scenario: Placing order with empty cart
    Given Empty shopping cart
    When I place order
    Then Order completes without error

  Scenario: Order with None cart
    Given None cart
    When I try to place order
    Then Order fails
