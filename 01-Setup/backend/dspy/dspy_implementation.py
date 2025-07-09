import dspy
import os
from typing import Dict, List, Any

from pydantic_models import (
    PlannerOutput, ExecutorOutput, ValidatorOutput, RegrouperOutput, PipelineOutput
)
from groq import Groq

# ────────────────────────────────────────────────────────────────
# LLM Wrapper
# ────────────────────────────────────────────────────────────────
class GroqLLM(dspy.LLM):
    def __init__(self, model_name="llama3-70b-8192", api_key=None):
        self.model_name = model_name
        self.api_key = api_key or os.environ.get("GROQ_API_KEY")
        self.client = Groq(api_key=self.api_key)

    def basic_request(self, prompt, temperature=0.1, max_tokens=2000):
        messages = [{"role": "user", "content": prompt}]
        response = self.client.chat.completions.create(
            model=self.model_name,
            messages=messages,
            temperature=temperature,
            max_tokens=max_tokens
        )
        return response.choices[0].message.content

# ────────────────────────────────────────────────────────────────
# DSPy Signatures
# ────────────────────────────────────────────────────────────────
class PlannerSignature(dspy.Signature):
    input_code: str = dspy.InputField(desc="Source code to analyze")
    components: List[Dict[str, Any]] = dspy.OutputField(desc="Parsed components")
    layout: Dict[str, Any] = dspy.OutputField(desc="Layout structure")
    style_guide: Dict[str, Any] = dspy.OutputField(desc="Style guide")

class ExecutorSignature(dspy.Signature):
    component_data: Dict[str, Any] = dspy.InputField()
    component_type: str = dspy.InputField()
    style_guide: Dict[str, Any] = dspy.InputField()
    code: str = dspy.OutputField()
    type: str = dspy.OutputField()

class ValidationSignature(dspy.Signature):
    component_code: str = dspy.InputField()
    component_data: Dict[str, Any] = dspy.InputField()
    valid: bool = dspy.OutputField()
    issues: List[Dict[str, Any]] = dspy.OutputField()
    fixes: List[Dict[str, Any]] = dspy.OutputField()
    improved_code: str = dspy.OutputField()

class RegrouperSignature(dspy.Signature):
    validated_components: List[Dict[str, Any]] = dspy.InputField()
    layout_info: Dict[str, Any] = dspy.InputField()
    style_guide: Dict[str, Any] = dspy.InputField()
    converted_code: str = dspy.OutputField()

# ────────────────────────────────────────────────────────────────
# Agent Modules
# ────────────────────────────────────────────────────────────────
class PlannerModule(dspy.Module):
    def __init__(self):
        super().__init__()
        self.generate = dspy.ChainOfThought(PlannerSignature)

    def forward(self, input_code: str) -> PlannerOutput:
        result = self.generate(input_code=input_code)
        return PlannerOutput(**result.dict())

class ExecutorModule(dspy.Module):
    def __init__(self):
        super().__init__()
        self.convert = dspy.ChainOfThought(ExecutorSignature)

    def forward(self, component_data: Dict[str, Any], component_type: str, style_guide: Dict[str, Any]) -> ExecutorOutput:
        result = self.convert(
            component_data=component_data,
            component_type=component_type,
            style_guide=style_guide
        )
        return ExecutorOutput(**result.dict())

class ValidatorModule(dspy.Module):
    def __init__(self):
        super().__init__()
        self.validate = dspy.ChainOfThought(ValidationSignature)

    def forward(self, component_code: str, component_data: Dict[str, Any]) -> ValidatorOutput:
        result = self.validate(
            component_code=component_code,
            component_data=component_data
        )
        improved = result.improved_code if not result.valid and result.improved_code else component_code
        return ValidatorOutput(validation=result.dict(), code=improved)

class RegrouperModule(dspy.Module):
    def __init__(self):
        super().__init__()
        self.regroup = dspy.ChainOfThought(RegrouperSignature)

    def forward(self, validated_components: List[Dict[str, Any]], layout_info: Dict[str, Any], style_guide: Dict[str, Any]) -> RegrouperOutput:
        result = self.regroup(
            validated_components=validated_components,
            layout_info=layout_info,
            style_guide=style_guide
        )
        return RegrouperOutput(converted_code=result.converted_code)

# ────────────────────────────────────────────────────────────────
# Full Pipeline
# ────────────────────────────────────────────────────────────────
class CodeTransformationPipeline(dspy.Module):
    def __init__(self):
        super().__init__()
        self.planner = PlannerModule()
        self.executor = ExecutorModule()
        self.validator = ValidatorModule()
        self.regrouper = RegrouperModule()

    def forward(self, input_code: str) -> PipelineOutput:
        plan = self.planner(input_code)
        validated_components = []

        for component in plan.components:
            exec_result = self.executor(
                component_data=component,
                component_type=component.get("type"),
                style_guide=plan.style_guide
            )
            val_result = self.validator(exec_result.code, component)
            validated_components.append({
                "type": exec_result.type,
                "code": val_result.code,
                "validation": val_result.validation
            })

        regrouped = self.regrouper(
            validated_components=validated_components,
            layout_info=plan.layout,
            style_guide=plan.style_guide
        )

        return PipelineOutput(
            converted_code=regrouped.converted_code,
            components=validated_components
        )

# ────────────────────────────────────────────────────────────────
# Pipeline Setup
# ────────────────────────────────────────────────────────────────
def setup_dspy_pipeline():
    llm = GroqLLM()
    dspy.settings.configure(lm=llm)

    pipeline = CodeTransformationPipeline()
    compiler = dspy.TraceCompiler(pipeline)
    return compiler.compile(save_traces=True)
