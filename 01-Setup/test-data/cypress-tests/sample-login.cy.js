// sample-login.cy.js
describe('Login Tests', () => {
  beforeEach(() => {
    cy.visit('https://example.com/login');
  });

  it('should login with valid credentials', () => {
    // Enter username
    cy.get('[data-cy="username"]').type('testuser@example.com');
    
    // Enter password
    cy.get('[data-cy="password"]').type('password123');
    
    // Click login button
    cy.get('[data-cy="login-btn"]').click();
    
    // Verify successful login
    cy.url().should('include', '/dashboard');
    cy.get('.welcome-message').should('contain', 'Welcome back');
    cy.get('.user-profile').should('be.visible');
  });

  it('should show error for invalid credentials', () => {
    cy.get('[data-cy="username"]').type('invalid@example.com');
    cy.get('[data-cy="password"]').type('wrongpassword');
    cy.get('[data-cy="login-btn"]').click();
    
    cy.get('.error-message').should('be.visible');
    cy.get('.error-message').should('contain', 'Invalid credentials');
  });

  it('should validate required fields', () => {
    cy.get('[data-cy="login-btn"]').click();
    
    cy.get('[data-cy="username"]').should('have.class', 'error');
    cy.get('[data-cy="password"]').should('have.class', 'error');
  });
});