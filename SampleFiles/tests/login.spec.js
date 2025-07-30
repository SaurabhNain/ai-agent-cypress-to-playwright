import LoginPage from '../pageObjects/LoginPage';

describe('Login Functionality', () => {
  const loginPage = new LoginPage();

  it('should login with valid credentials', () => {
    loginPage.visit();
    loginPage.enterUsername('standard_user');
    loginPage.enterPassword('secret_sauce');
    loginPage.clickLogin();

    cy.url().should('include', '/inventory');
  });
});
