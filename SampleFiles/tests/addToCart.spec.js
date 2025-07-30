import InventoryPage from '../pageObjects/InventoryPage';
import LoginPage from '../pageObjects/LoginPage';

describe('Add to Cart', () => {
  const loginPage = new LoginPage();
  const inventoryPage = new InventoryPage();

  beforeEach(() => {
    loginPage.visit();
    loginPage.enterUsername('standard_user');
    loginPage.enterPassword('secret_sauce');
    loginPage.clickLogin();
  });

  it('should add a product to cart and verify cart badge', () => {
    inventoryPage.addBackpackToCart();
    inventoryPage.getCartBadge().should('have.text', '1');
  });
});
