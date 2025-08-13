# agents/tool_system.py  
# Step 2: Implement Multi-Tool Selection

from abc import ABC, abstractmethod
from typing import Dict, List, Any, Optional
from enum import Enum
import re
from .agentic_core import AgenticConverter, ConversionResult, ConversionStrategy

class ToolType(Enum):
    AST_PARSER = "ast_parser"
    REGEX_MATCHER = "regex_matcher" 
    PATTERN_ANALYZER = "pattern_analyzer"
    SYNTAX_VALIDATOR = "syntax_validator"
    SEMANTIC_ANALYZER = "semantic_analyzer"

class Tool(ABC):
    """Base class for all agentic tools"""
    
    @abstractmethod
    def can_handle(self, code: str, context: Dict) -> float:
        """Returns confidence score (0-1) that this tool can handle the task"""
        pass
    
    @abstractmethod
    def execute(self, code: str, context: Dict) -> Dict:
        """Execute the tool and return results"""
        pass
    
    @property
    @abstractmethod
    def tool_type(self) -> ToolType:
        pass

class ASTParserTool(Tool):
    """Advanced AST parsing for complex code structures"""
    
    @property
    def tool_type(self) -> ToolType:
        return ToolType.AST_PARSER
    
    def can_handle(self, code: str, context: Dict) -> float:
        # Higher confidence for complex nested structures
        describe_count = code.count('describe(')
        nested_its = code.count('  it(')  # Indented its
        
        if describe_count > 2 or nested_its > 0:
            return 0.9
        elif describe_count > 0:
            return 0.7
        else:
            return 0.3
    
    def execute(self, code: str, context: Dict) -> Dict:
        # Simulate AST parsing (in real implementation, call your parseAst.js)
        structure = {
            "describes": re.findall(r"describe\(['\"]([^'\"]+)['\"]", code),
            "its": re.findall(r"it\(['\"]([^'\"]+)['\"]", code),
            "commands": re.findall(r"cy\.(\w+)\(", code),
            "custom_commands": [cmd for cmd in re.findall(r"cy\.(\w+)\(", code) 
                               if cmd not in ['get', 'type', 'click', 'should', 'visit']]
        }
        
        return {
            "success": True,
            "structure": structure,
            "complexity_score": len(structure["describes"]) * 2 + len(structure["its"]),
            "tool_used": "AST_PARSER"
        }

class RegexMatcherTool(Tool):
    """Fast regex-based pattern matching for simple conversions"""
    
    @property
    def tool_type(self) -> ToolType:
        return ToolType.REGEX_MATCHER
    
    def can_handle(self, code: str, context: Dict) -> float:
        # Good for simple, linear code
        lines = code.split('\n')
        cypress_commands = sum(1 for line in lines if 'cy.' in line)
        
        if cypress_commands < 5 and 'describe(' not in code:
            return 0.8
        elif cypress_commands < 10:
            return 0.6
        else:
            return 0.2
    
    def execute(self, code: str, context: Dict) -> Dict:
        # Simple regex replacements
        converted = code
        
        patterns = [
            (r"cy\.get\(['\"]([^'\"]+)['\"]\)", r"page.locator('\1')"),
            (r"\.type\(['\"]([^'\"]+)['\"]\)", r".fill('\1')"),
            (r"\.click\(\)", r".click()"),
            (r"cy\.visit\(['\"]([^'\"]+)['\"]\)", r"await page.goto('\1')"),
            (r"\.should\(['\"]contain['\"]\s*,\s*['\"]([^'\"]+)['\"]\)", 
             r".toContainText('\1')")
        ]
        
        for pattern, replacement in patterns:
            converted = re.sub(pattern, replacement, converted)
        
        return {
            "success": True,
            "converted_code": converted,
            "patterns_applied": len(patterns),
            "tool_used": "REGEX_MATCHER"
        }

class PatternAnalyzerTool(Tool):
    """Analyzes complex patterns and suggests best conversion approach"""
    
    @property
    def tool_type(self) -> ToolType:
        return ToolType.PATTERN_ANALYZER
    
    def can_handle(self, code: str, context: Dict) -> float:
        # Good for code with mixed patterns
        has_intercepts = 'cy.intercept' in code
        has_custom_commands = any(cmd in code for cmd in ['cy.login', 'cy.custom'])
        has_complex_chains = '.should(' in code and '.and(' in code
        
        if has_intercepts or has_custom_commands or has_complex_chains:
            return 0.9
        else:
            return 0.4
    
    def execute(self, code: str, context: Dict) -> Dict:
        patterns = {
            "api_intercepts": len(re.findall(r'cy\.intercept', code)),
            "command_chains": len(re.findall(r'cy\.\w+\([^)]*\)\.\w+', code)),
            "custom_commands": len([cmd for cmd in re.findall(r'cy\.(\w+)', code)
                                 if cmd not in ['get', 'type', 'click', 'should', 'visit']]),
            "assertions": len(re.findall(r'\.should\(', code))
        }
        
        # Suggest conversion strategy based on patterns
        if patterns["api_intercepts"] > 0:
            strategy = "api_testing_focused"
        elif patterns["custom_commands"] > 2:
            strategy = "custom_command_heavy"
        elif patterns["command_chains"] > patterns["assertions"]:
            strategy = "interaction_heavy"
        else:
            strategy = "assertion_heavy"
        
        return {
            "success": True,
            "patterns": patterns,
            "suggested_strategy": strategy,
            "tool_used": "PATTERN_ANALYZER"
        }

class SyntaxValidatorTool(Tool):
    """Validates converted code syntax"""
    
    @property
    def tool_type(self) -> ToolType:
        return ToolType.SYNTAX_VALIDATOR
    
    def can_handle(self, code: str, context: Dict) -> float:
        # Always good for validation
        return 0.8
    
    def execute(self, code: str, context: Dict) -> Dict:
        issues = []
        
        # Check for common syntax issues
        if 'await' in code and 'async' not in code:
            issues.append("Missing 'async' keyword in function definition")
        
        if 'page.locator' in code and 'await' not in code:
            issues.append("Missing 'await' before page.locator calls")
        
        if 'cy.' in code:
            issues.append("Unconverted Cypress commands found")
        
        # Check imports
        if 'expect(' in code and 'import' not in code:
            issues.append("Missing Playwright test imports")
        
        return {
            "success": len(issues) == 0,
            "issues": issues,
            "tool_used": "SYNTAX_VALIDATOR"
        }

class AgenticToolSelector:
    """Agent that intelligently selects and orchestrates tools"""
    
    def __init__(self):
        self.tools = [
            ASTParserTool(),
            RegexMatcherTool(), 
            PatternAnalyzerTool(),
            SyntaxValidatorTool()
        ]
        self.tool_performance = {}  # Track which tools work best for what
    
    def select_tools(self, code: str, context: Dict) -> List[Tool]:
        """Agent decides which tools to use and in what order"""
        
        tool_scores = []
        for tool in self.tools:
            confidence = tool.can_handle(code, context)
            
            # Factor in historical performance
            tool_key = f"{tool.tool_type.value}_{context.get('complexity', 'unknown')}"
            historical_success = self.tool_performance.get(tool_key, {}).get('success_rate', 0.5)
            
            # Weighted score
            final_score = confidence * 0.7 + historical_success * 0.3
            
            tool_scores.append((tool, final_score))
        
        # Sort by score and select top tools
        tool_scores.sort(key=lambda x: x[1], reverse=True)
        
        # Agent's decision logic for tool selection
        selected_tools = []
        
        # Always include the top scorer
        if tool_scores[0][1] > 0.5:
            selected_tools.append(tool_scores[0][0])
        
        # Add complementary tools
        for tool, score in tool_scores[1:]:
            if score > 0.6 and tool.tool_type != selected_tools[0].tool_type:
                selected_tools.append(tool)
                if len(selected_tools) >= 3:  # Max 3 tools
                    break
        
        # Always validate at the end
        validator = next((t for t in self.tools if t.tool_type == ToolType.SYNTAX_VALIDATOR), None)
        if validator and validator not in selected_tools:
            selected_tools.append(validator)
        
        print(f"🔧 Agent selected {len(selected_tools)} tools: {[t.tool_type.value for t in selected_tools]}")
        return selected_tools
    
    def execute_tools(self, code: str, context: Dict) -> Dict:
        """Execute selected tools in intelligent order"""
        
        selected_tools = self.select_tools(code, context)
        results = []
        current_code = code
        
        for i, tool in enumerate(selected_tools):
            print(f"🔄 Executing tool {i+1}/{len(selected_tools)}: {tool.tool_type.value}")
            
            try:
                result = tool.execute(current_code, context)
                result['tool_type'] = tool.tool_type.value
                results.append(result)
                
                # Update code for next tool if this tool generated new code
                if 'converted_code' in result:
                    current_code = result['converted_code']
                
                # Update tool performance tracking
                self._update_tool_performance(tool, context, result['success'])
                
            except Exception as e:
                print(f"❌ Tool {tool.tool_type.value} failed: {e}")
                results.append({
                    "success": False,
                    "error": str(e),
                    "tool_type": tool.tool_type.value
                })
        
        return {
            "final_code": current_code,
            "tool_results": results,
            "tools_used": len(selected_tools),
            "overall_success": all(r.get('success', False) for r in results)
        }
    
    def _update_tool_performance(self, tool: Tool, context: Dict, success: bool):
        """Track tool performance for future decision making"""
        
        tool_key = f"{tool.tool_type.value}_{context.get('complexity', 'unknown')}"
        
        if tool_key not in self.tool_performance:
            self.tool_performance[tool_key] = {
                "attempts": 0,
                "successes": 0,
                "success_rate": 0.5
            }
        
        perf = self.tool_performance[tool_key]
        perf["attempts"] += 1
        if success:
            perf["successes"] += 1
        
        perf["success_rate"] = perf["successes"] / perf["attempts"]
    
    def get_tool_stats(self) -> Dict:
        """Return performance statistics"""
        return {
            "available_tools": len(self.tools),
            "tool_performance": self.tool_performance,
            "total_executions": sum(p["attempts"] for p in self.tool_performance.values())
        }

class EnhancedAgenticConverter(AgenticConverter):
    """Enhanced converter with intelligent tool selection"""
    
    def __init__(self, llm):
        super().__init__(llm)
        self.tool_selector = AgenticToolSelector()
        print("✅ Enhanced agentic converter with tool selection initialized")
    
    def convert(self, input_code: str) -> ConversionResult:
        """Enhanced conversion with tool selection"""
        print("🤖 Starting enhanced agentic conversion with tool selection...")
        
        # Analyze code
        context = self._analyze_code(input_code)
        
        # Agent selects and executes tools
        tool_results = self.tool_selector.execute_tools(input_code, context.__dict__)
        
        # Use tool insights to inform LLM conversion
        enhanced_context = {
            **context.__dict__,
            "tool_insights": tool_results
        }
        
        # Proceed with enhanced conversion using tool insights
        strategy = self._decide_strategy_with_tools(enhanced_context)
        plan = self._create_conversion_plan(context, strategy)
        result = self._execute_plan(input_code, plan, context)
        
        # Enhance result with tool information
        result.metadata["tool_analysis"] = tool_results
        result.metadata["tools_used"] = tool_results["tools_used"]
        result.metadata["enhanced_agentic"] = True
        
        return result
    
    def _decide_strategy_with_tools(self, enhanced_context: Dict) -> ConversionStrategy:
        """Make strategy decisions informed by tool analysis"""
        
        tool_insights = enhanced_context.get("tool_insights", {})
        
        # Use tool results to make better decisions
        for result in tool_insights.get("tool_results", []):
            if result.get("tool_type") == "PATTERN_ANALYZER":
                suggested = result.get("suggested_strategy")
                if suggested == "api_testing_focused":
                    return ConversionStrategy.API_TESTING
                elif suggested == "custom_command_heavy":
                    return ConversionStrategy.CUSTOM_COMMANDS
        
        # Fall back to original logic
        return super()._decide_strategy(enhanced_context)
    
    def get_agent_status(self) -> Dict:
        """Get comprehensive agent status"""
        base_stats = self.get_performance_stats()
        tool_stats = self.tool_selector.get_tool_stats()
        
        return {
            "agent_type": "enhanced_agentic",
            "capabilities": ["decision_making", "planning", "tool_selection", "adaptation"],
            "performance": base_stats,
            "tools": tool_stats,
            "total_conversions": base_stats["total_conversions"]
        }

def setup_enhanced_agentic_pipeline():
    """Setup the enhanced agentic pipeline with tool selection (Step 2)"""
    try:
        from dotenv import load_dotenv
        load_dotenv()
        
        from .dspy_implementation import GroqLLM
        llm = GroqLLM()
        
        converter = EnhancedAgenticConverter(llm)
        print("🤖 Enhanced agentic converter initialized (Step 2: Tool selection)")
        print("🔧 Available tools:", len(converter.tool_selector.tools))
        
        return converter
        
    except Exception as e:
        print(f"❌ Error setting up enhanced agentic pipeline: {e}")
        raise e