# agents/agentic_core.py
# Step 1: Add Decision-Making Logic

import json
import time
from typing import Dict, List, Any, Optional
from enum import Enum
from dataclasses import dataclass

class ConversionStrategy(Enum):
    SIMPLE = "simple"
    COMPLEX = "complex"
    CUSTOM_COMMANDS = "custom_commands"
    FORM_HEAVY = "form_heavy"
    API_TESTING = "api_testing"

class AgentDecision(Enum):
    CONTINUE = "continue"
    RETRY = "retry"
    ESCALATE = "escalate"
    SWITCH_STRATEGY = "switch_strategy"

@dataclass
class ConversionContext:
    code_complexity: int
    has_custom_commands: bool
    has_api_calls: bool
    has_form_interactions: bool
    test_count: int
    previous_attempts: List[str]
    success_rate: float = 0.0

@dataclass
class ConversionResult:
    success: bool
    code: str
    confidence: float
    strategy_used: ConversionStrategy
    issues: List[str]
    metadata: Dict[str, Any]

class AgenticConverter:
    """Step 1: Agentic converter with decision-making capabilities"""
    
    def __init__(self, llm):
        self.llm = llm
        self.memory = {}  # Store learning from past conversions
        print("✅ AgenticConverter initialized with decision-making")
    
    def __call__(self, input_code: str):
        """Make the converter callable like SimpleConverter"""
        result = self.convert(input_code)
        
        # Return in the same format as SimpleConverter for compatibility
        return {
            "converted_code": result.code,
            "success": result.success,
            "confidence": result.confidence,
            "strategy_used": result.strategy_used.value,
            "components": [
                {
                    "type": comp.get("type", "converted_test"),
                    "code": result.code,
                    "validation": {
                        "valid": True,
                        "issues": result.issues,
                        "fixes": [],
                        "improved_code": None
                    }
                } for comp in [{"type": "agentic_conversion"}]
            ],
            "metadata": {**result.metadata, "converter_type": "agentic"}
        }
        
    def convert(self, input_code: str) -> ConversionResult:
        """Main agentic conversion process"""
        print("🤖 Starting agentic conversion with decision-making...")
        
        # STEP 1: ANALYZE AND DECIDE
        context = self._analyze_code(input_code)
        strategy = self._decide_strategy(context)
        
        print(f"🧠 Decided on strategy: {strategy.value}")
        print(f"📊 Code complexity: {context.code_complexity}/10")
        
        # STEP 2: PLAN CONVERSION
        plan = self._create_conversion_plan(context, strategy)
        print(f"📋 Created plan with {len(plan)} steps")
        
        # STEP 3: EXECUTE WITH ADAPTATION
        result = self._execute_plan(input_code, plan, context)
        
        # STEP 4: LEARN FROM RESULT
        self._update_memory(context, strategy, result)
        
        return result
    
    def _analyze_code(self, code: str) -> ConversionContext:
        """Agent decides what type of code it's dealing with"""
        
        analysis_prompt = f"""
        Analyze this Cypress code and determine its characteristics:
        
        ```javascript
        {code}
        ```
        
        Return JSON with:
        {{
            "complexity_score": 1-10,
            "has_custom_commands": true/false,
            "has_api_calls": true/false, 
            "has_form_interactions": true/false,
            "test_count": number,
            "dominant_patterns": ["pattern1", "pattern2"],
            "risk_factors": ["risk1", "risk2"]
        }}
        """
        
        response = self.llm(analysis_prompt)
        
        try:
            analysis = json.loads(response)
            return ConversionContext(
                code_complexity=analysis.get("complexity_score", 5),
                has_custom_commands=analysis.get("has_custom_commands", False),
                has_api_calls=analysis.get("has_api_calls", False),
                has_form_interactions=analysis.get("has_form_interactions", False),
                test_count=analysis.get("test_count", 1),
                previous_attempts=[]
            )
        except json.JSONDecodeError:
            # Fallback to simple heuristics if LLM response is malformed
            return ConversionContext(
                code_complexity=len(code.split('\n')) // 10,
                has_custom_commands='cy.' in code and 'custom' in code.lower(),
                has_api_calls='intercept' in code or 'request' in code,
                has_form_interactions='.type(' in code or '.select(' in code,
                test_count=code.count('it('),
                previous_attempts=[]
            )
    
    def _decide_strategy(self, context: ConversionContext) -> ConversionStrategy:
        """Agent chooses the best strategy based on analysis"""
        
        # Decision tree based on code characteristics
        if context.has_custom_commands:
            return ConversionStrategy.CUSTOM_COMMANDS
        elif context.has_api_calls and context.code_complexity > 7:
            return ConversionStrategy.API_TESTING
        elif context.has_form_interactions and context.test_count > 3:
            return ConversionStrategy.FORM_HEAVY
        elif context.code_complexity > 6:
            return ConversionStrategy.COMPLEX
        else:
            return ConversionStrategy.SIMPLE
    
    def _create_conversion_plan(self, context: ConversionContext, strategy: ConversionStrategy) -> List[Dict]:
        """Agent creates a multi-step plan"""
        
        base_plan = [
            {"step": "parse_structure", "priority": "high"},
            {"step": "convert_commands", "priority": "high"},
            {"step": "handle_assertions", "priority": "medium"},
            {"step": "optimize_async", "priority": "medium"}
        ]
        
        # Agent adapts plan based on strategy
        if strategy == ConversionStrategy.CUSTOM_COMMANDS:
            base_plan.insert(1, {"step": "identify_custom_commands", "priority": "critical"})
            base_plan.append({"step": "create_helper_functions", "priority": "high"})
            
        elif strategy == ConversionStrategy.API_TESTING:
            base_plan.insert(2, {"step": "convert_intercepts", "priority": "critical"})
            base_plan.append({"step": "add_api_error_handling", "priority": "high"})
            
        elif strategy == ConversionStrategy.FORM_HEAVY:
            base_plan.append({"step": "optimize_form_selectors", "priority": "high"})
            base_plan.append({"step": "add_form_validation", "priority": "medium"})
        
        return base_plan
    
    def _execute_plan(self, code: str, plan: List[Dict], context: ConversionContext) -> ConversionResult:
        """Agent executes plan with adaptation"""
        
        # For now, use enhanced prompt based on strategy
        strategy_prompts = {
            ConversionStrategy.SIMPLE: self._get_simple_prompt(code),
            ConversionStrategy.COMPLEX: self._get_complex_prompt(code),
            ConversionStrategy.CUSTOM_COMMANDS: self._get_custom_commands_prompt(code),
            ConversionStrategy.FORM_HEAVY: self._get_form_heavy_prompt(code),
            ConversionStrategy.API_TESTING: self._get_api_testing_prompt(code)
        }
        
        strategy = self._decide_strategy(context)
        prompt = strategy_prompts.get(strategy, strategy_prompts[ConversionStrategy.SIMPLE])
        
        try:
            converted_code = self.llm(prompt)
            print("✅ Code converted successfully with strategy-specific approach")
            
            # Clean up response
            if "```javascript" in converted_code:
                converted_code = converted_code.split("```javascript")[1].split("```")[0].strip()
            elif "```" in converted_code:
                converted_code = converted_code.split("```")[1].split("```")[0].strip()
            
            return ConversionResult(
                success=True,
                code=converted_code,
                confidence=0.85,  # Higher confidence with agentic approach
                strategy_used=strategy,
                issues=[],
                metadata={"plan_steps": len(plan), "agentic": True}
            )
            
        except Exception as e:
            return ConversionResult(
                success=False,
                code=f"// Error during conversion: {str(e)}",
                confidence=0.0,
                strategy_used=strategy,
                issues=[str(e)],
                metadata={"error": str(e)}
            )
    
    def _get_simple_prompt(self, code: str) -> str:
        return f"""
        Convert this simple Cypress code to Playwright:
        
        {code}
        
        Use basic conversions:
        - cy.get() → page.locator()
        - cy.type() → page.fill()
        - cy.click() → page.click()
        - Add async/await and proper imports
        """
    
    def _get_complex_prompt(self, code: str) -> str:
        return f"""
        Convert this complex Cypress code to Playwright with careful attention to:
        
        {code}
        
        Focus on:
        - Nested test structures
        - Complex selectors
        - Multiple assertions
        - Proper async/await patterns
        - Error handling
        """
    
    def _get_custom_commands_prompt(self, code: str) -> str:
        return f"""
        Convert this Cypress code with custom commands to Playwright:
        
        {code}
        
        Special handling for:
        - Custom cy.* commands → create helper functions
        - Maintain command reusability
        - Document helper functions
        - Preserve custom logic
        """
    
    def _get_form_heavy_prompt(self, code: str) -> str:
        return f"""
        Convert this form-heavy Cypress code to Playwright:
        
        {code}
        
        Optimize for:
        - Form field interactions
        - Input validation
        - Form submission
        - Error state handling
        - Accessibility selectors
        """
    
    def _get_api_testing_prompt(self, code: str) -> str:
        return f"""
        Convert this API-testing Cypress code to Playwright:
        
        {code}
        
        Handle:
        - cy.intercept() → page.route()
        - API mocking and responses
        - Network conditions
        - Response validation
        - Async API calls
        """
    
    def _update_memory(self, context: ConversionContext, strategy: ConversionStrategy, result: ConversionResult):
        """Agent learns from each conversion"""
        
        memory_key = f"{strategy.value}_{context.code_complexity}_{context.test_count}"
        
        if memory_key not in self.memory:
            self.memory[memory_key] = {
                "attempts": 0,
                "successes": 0,
                "avg_confidence": 0.0,
                "common_issues": []
            }
        
        memory = self.memory[memory_key]
        memory["attempts"] += 1
        
        if result.success:
            memory["successes"] += 1
        
        # Update average confidence
        memory["avg_confidence"] = (
            (memory["avg_confidence"] * (memory["attempts"] - 1) + result.confidence) 
            / memory["attempts"]
        )
        
        # Track common issues
        for issue in result.issues:
            if issue not in memory["common_issues"]:
                memory["common_issues"].append(issue)
        
        print(f"📚 Updated memory: {memory['successes']}/{memory['attempts']} success rate")
    
    def get_performance_stats(self) -> Dict:
        """Agent reports its learning and performance"""
        
        total_attempts = sum(mem["attempts"] for mem in self.memory.values())
        total_successes = sum(mem["successes"] for mem in self.memory.values())
        
        return {
            "total_conversions": total_attempts,
            "success_rate": total_successes / total_attempts if total_attempts > 0 else 0,
            "strategies_learned": len(self.memory),
            "memory_entries": list(self.memory.keys())
        }

def setup_agentic_pipeline():
    """Initialize the agentic pipeline (Step 1)"""
    try:
        from dotenv import load_dotenv
        load_dotenv()
        
        from .dspy_implementation import GroqLLM
        llm = GroqLLM()
        
        converter = AgenticConverter(llm)
        print("🤖 Agentic converter initialized (Step 1: Decision-making)")
        
        return converter
        
    except Exception as e:
        print(f"❌ Error setting up agentic pipeline: {e}")
        raise e