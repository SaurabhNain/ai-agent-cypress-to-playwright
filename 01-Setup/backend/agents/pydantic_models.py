from pydantic import BaseModel, Field, validator
from typing import Dict, List, Optional, Union, Literal, Any
from enum import Enum

# ────────────────────────────────────────────────────────────────
# Generic Component Definitions
# ────────────────────────────────────────────────────────────────

class ComponentType(str, Enum):
    """Supported UI component types (generic)"""
    TEXT_BOX = "TextBox"
    COMBO_BOX = "ComboBox"
    SLIDER = "Slider"
    LABEL = "Label"
    BUTTON = "Button"
    CHECK_BOX = "CheckBox"
    RADIO_BUTTON = "RadioButton"
    GROUP_BOX = "GroupBox"
    OTHER = "Other"

class Position(BaseModel):
    """Position info for layout-aware components"""
    parent: str = Field(..., description="Parent container ID")
    order: int = Field(..., description="Order within the parent container")

class Styling(BaseModel):
    """Styling properties"""
    color: Optional[str] = None
    alignment: Optional[str] = None
    font_family: Optional[str] = None
    font_size: Optional[str] = None
    font_weight: Optional[str] = None

class Behavior(BaseModel):
    """Behavioral handlers"""
    onChange: Optional[str] = None
    onClick: Optional[str] = None
    onFocus: Optional[str] = None
    onBlur: Optional[str] = None

class Component(BaseModel):
    """Normalized component representation"""
    id: str
    type: ComponentType
    properties: Dict[str, Union[str, int, float, bool]]
    position: Optional[Position] = None
    styling: Optional[Styling] = Field(default_factory=Styling)
    behavior: Optional[Behavior] = Field(default_factory=Behavior)

# ────────────────────────────────────────────────────────────────
# Layout and Style Guide
# ────────────────────────────────────────────────────────────────

class Layout(BaseModel):
    structure: Literal["vertical", "horizontal", "grid"]
    relationships: List[Dict[str, str]] = Field(default_factory=list)

class StyleGuide(BaseModel):
    colors: Dict[str, str]
    fonts: Dict[str, str]
    spacing: Optional[Dict[str, str]] = None

    @validator("colors")
    def ensure_hex(cls, colors):
        for name, code in colors.items():
            if not code.startswith("#") and not code.startswith("rgba"):
                colors[name] = f"#{code}"
        return colors

# ────────────────────────────────────────────────────────────────
# Conversion / Validation Results
# ────────────────────────────────────────────────────────────────

class ValidationIssue(BaseModel):
    type: str
    description: str
    severity: Literal["info", "warning", "error"]

class ValidationFix(BaseModel):
    issue_index: int
    fix: str

class ValidationResult(BaseModel):
    valid: bool
    issues: List[ValidationIssue] = Field(default_factory=list)
    fixes: List[ValidationFix] = Field(default_factory=list)
    improved_code: Optional[str] = None

class ComponentResult(BaseModel):
    type: str
    code: str
    validation: Optional[ValidationResult] = None

# ────────────────────────────────────────────────────────────────
# API Models (used by FastAPI)
# ────────────────────────────────────────────────────────────────

class ConversionRequest(BaseModel):
    """Generic conversion request"""
    input_code: str
    style_options: Optional[Dict[str, str]] = None

class ConversionResponse(BaseModel):
    """Generic conversion response"""
    success: bool = True
    converted_code: str
    components: Optional[List[Any]] = None
    warnings: List[str] = Field(default_factory=list)
    metadata: Optional[Dict[str, Any]] = Field(default_factory=dict)

# ────────────────────────────────────────────────────────────────
# Agent Result Wrapper
# ────────────────────────────────────────────────────────────────

class AgentResult(BaseModel):
    success: bool
    data: Dict
    error: Optional[str] = None

# ────────────────────────────────────────────────────────────────
# DSPy-Compatible Agent I/O Models
# ────────────────────────────────────────────────────────────────

class PlannerInput(BaseModel):
    input_code: str

class PlannerOutput(BaseModel):
    components: List[Dict[str, Any]]
    layout: Dict[str, Any]
    style_guide: Dict[str, Any]

class ExecutorInput(BaseModel):
    component_data: Dict[str, Any]
    component_type: str
    style_guide: Dict[str, Any]

class ExecutorOutput(BaseModel):
    type: str
    code: str

class ValidatorInput(BaseModel):
    component_code: str
    component_data: Dict[str, Any]

class ValidatorOutput(BaseModel):
    validation: Dict[str, Any]
    code: str

class RegrouperInput(BaseModel):
    validated_components: List[Dict[str, Any]]
    layout_info: Dict[str, Any]
    style_guide: Dict[str, Any]

class RegrouperOutput(BaseModel):
    combined_code: str

class PipelineInput(BaseModel):
    input_code: str

class PipelineOutput(BaseModel):
    converted_code: str
    components: List[Dict[str, Any]]
    metadata: Optional[Dict[str, Any]] = Field(default_factory=dict)
