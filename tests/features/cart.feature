Feature:Shopping cart
  We want to test that shopping cart functionality works correctly

  Scenario: Successful add product to cart
    Given The product has availability of 123
    And An empty shopping cart
    When I add product to the cart in amount 123
    Then Product is added to the cart successfully

  Scenario: Failed add product to cart
    Given The product has availability of 123
    And An empty shopping cart
    When I add product to the cart in amount 124
    Then Product is not added to cart successfully

  Scenario: Cart contains added product
    Given The product has availability of 10
    And An empty shopping cart
    When I add product to the cart in amount 5
    Then Cart contains the product

  Scenario: Cart total price is calculated correctly
    Given The product has availability of 10
    And An empty shopping cart
    When I add product to the cart in amount 2
    Then Cart total should be 246

  Scenario: Removing product from cart
    Given The product has availability of 10
    And An empty shopping cart
    When I add product to the cart in amount 3
    And I remove the product from the cart
    Then Cart should not contain the product
