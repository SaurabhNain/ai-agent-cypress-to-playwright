// js/parseAst.js
// Node script to parse JS/TS files into Babel AST and extract Cypress metadata

const fs = require('fs');
const parser = require('@babel/parser');
const traverse = require('@babel/traverse').default;

const filePath = process.argv[2];
const sourceCode = fs.readFileSync(filePath, 'utf8');

const ast = parser.parse(sourceCode, {
  sourceType: 'module',
  plugins: ['jsx', 'typescript']
});

const customCommands = [];

traverse(ast, {
  CallExpression(path) {
    const callee = path.node.callee;
    if (
      callee.type === 'MemberExpression' &&
      callee.object.name === 'Cypress' &&
      callee.property.name === 'Commands'
    ) {
      customCommands.push(path.toString());
    }
  }
});

const output = {
  ast: ast.program.body,
  customCommands
};

console.log(JSON.stringify(output));
