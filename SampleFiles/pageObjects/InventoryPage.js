class InventoryPage {
  addBackpackToCart() {
    cy.get('[data-test="add-to-cart-sauce-labs-backpack"]').click();
  }

  getCartBadge() {
    return cy.get('.shopping_cart_badge');
  }
}

export default InventoryPage;
