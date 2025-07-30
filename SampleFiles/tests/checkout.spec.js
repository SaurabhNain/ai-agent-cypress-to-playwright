import LoginPage from '../pageObjects/LoginPage';
import InventoryPage from '../pageObjects/InventoryPage';
import CartPage from '../pageObjects/CartPage';
import CheckoutPage from '../pageObjects/CheckoutPage';

describe('Checkout Flow', () => {
  const loginPage = new LoginPage();
  const inventoryPage = new InventoryPage();
  const cartPage = new CartPage();
  const checkoutPage = new CheckoutPage();

  before(() => {
    loginPage.visit();
    loginPage.enterUsername('standard_user');
    loginPage.enterPassword('secret_sauce');
    loginPage.clickLogin();
    inventoryPage.addBackpackToCart();
    inventoryPage.goToCart();
  });

  it('should complete checkout for one product', () => {
    cartPage.clickCheckout();
    checkoutPage.fillUserInfo('John', 'Doe', '12345');
    checkoutPage.clickContinue();
    checkoutPage.clickFinish();

    checkoutPage.getConfirmation().should('contain', 'THANK YOU FOR YOUR ORDER');
  });
});
