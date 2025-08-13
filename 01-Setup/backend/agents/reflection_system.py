# agents/reflection_system.py
# Step 4: Self-Reflection & Improvement

from typing import Dict, List, Any, Optional, Tuple
from dataclasses import dataclass
from datetime import datetime, timedelta
from enum import Enum
from .learning_system import LearningAgenticConverter, ConversionResult

class ReflectionTrigger(Enum):
    FAILURE_THRESHOLD = "failure_threshold"
    PERIODIC = "periodic"
    CONFIDENCE_DROP = "confidence_drop"
    USER_FEEDBACK = "user_feedback"
    PATTERN_MISMATCH = "pattern_mismatch"

@dataclass
class ReflectionInsight:
    """Represents an insight gained from self-reflection"""
    insight_type: str
    description: str
    evidence: List[str]
    suggested_action: str
    confidence: float
    priority: int  # 1-5, where 5 is highest priority

@dataclass
class PerformanceMetrics:
    """Current performance metrics for reflection"""
    success_rate: float
    avg_confidence: float
    avg_execution_time: float
    pattern_usage_rate: float
    user_satisfaction: float
    strategy_effectiveness: Dict[str, float]
    recent_failures: List[str]
    improvement_trend: str

class SelfReflectionEngine:
    """Engine for agent self-reflection and improvement"""
    
    def __init__(self, converter):
        self.converter = converter
        self.reflection_history = []
        self.last_reflection = None
        self.improvement_actions = []
        
    def should_reflect(self) -> Tuple[bool, Optional[ReflectionTrigger]]:
        """Determine if agent should perform self-reflection"""
        
        # Check failure threshold
        recent_failures = self._count_recent_failures()
        if recent_failures >= 3:
            return True, ReflectionTrigger.FAILURE_THRESHOLD
        
        # Check confidence drop
        confidence_trend = self._analyze_confidence_trend()
        if confidence_trend < -0.2:  # 20% drop
            return True, ReflectionTrigger.CONFIDENCE_DROP
        
        # Periodic reflection (every 50 conversions)
        if len(self.converter.conversion_history) % 50 == 0 and len(self.converter.conversion_history) > 0:
            return True, ReflectionTrigger.PERIODIC
        
        # Check user feedback
        negative_feedback = self._check_negative_feedback()
        if negative_feedback:
            return True, ReflectionTrigger.USER_FEEDBACK
        
        return False, None
    
    def perform_reflection(self, trigger: ReflectionTrigger) -> List[ReflectionInsight]:
        """Perform comprehensive self-reflection"""
        print(f"🤔 Starting self-reflection triggered by: {trigger.value}")
        
        # Gather current performance metrics
        metrics = self._gather_performance_metrics()
        
        # Analyze different aspects
        insights = []
        insights.extend(self._reflect_on_strategy_effectiveness(metrics))
        insights.extend(self._reflect_on_pattern_usage(metrics))
        insights.extend(self._reflect_on_failure_patterns(metrics))
        insights.extend(self._reflect_on_user_feedback(metrics))
        insights.extend(self._reflect_on_learning_progress(metrics))
        
        # Prioritize insights
        insights.sort(key=lambda x: x.priority, reverse=True)
        
        # Store reflection
        reflection_record = {
            "timestamp": datetime.now(),
            "trigger": trigger.value,
            "metrics": metrics,
            "insights": insights,
            "actions_planned": len([i for i in insights if i.priority >= 4])
        }
        self.reflection_history.append(reflection_record)
        self.last_reflection = reflection_record
        
        # Generate improvement actions
        self._generate_improvement_actions(insights)
        
        print(f"🎯 Generated {len(insights)} insights, {len([i for i in insights if i.priority >= 4])} high-priority")
        return insights
    
    def _gather_performance_metrics(self) -> PerformanceMetrics:
        """Gather comprehensive performance metrics"""
        history = self.converter.conversion_history
        recent_history = history[-20:] if len(history) > 20 else history
        
        if not recent_history:
            return PerformanceMetrics(0, 0, 0, 0, 0, {}, [], "insufficient_data")
        
        # Basic metrics
        success_rate = sum(1 for case in recent_history if case.success) / len(recent_history)
        avg_confidence = sum(case.confidence for case in recent_history) / len(recent_history)
        avg_execution_time = sum(case.execution_time for case in recent_history) / len(recent_history)
        
        # Pattern usage rate
        pattern_conversions = sum(1 for case in recent_history 
                                if hasattr(case, 'metadata') and case.metadata and 
                                case.metadata.get('used_pattern'))
        pattern_usage_rate = pattern_conversions / len(recent_history)
        
        # User satisfaction (from feedback scores)
        feedback_scores = [case.feedback_score for case in recent_history 
                          if case.feedback_score is not None]
        user_satisfaction = sum(feedback_scores) / len(feedback_scores) if feedback_scores else 0
        
        # Strategy effectiveness
        strategy_effectiveness = {}
        strategy_stats = {}
        for case in recent_history:
            strategy = case.strategy_used
            if strategy not in strategy_stats:
                strategy_stats[strategy] = {"attempts": 0, "successes": 0}
            strategy_stats[strategy]["attempts"] += 1
            if case.success:
                strategy_stats[strategy]["successes"] += 1
        
        for strategy, stats in strategy_stats.items():
            if stats["attempts"] > 0:
                strategy_effectiveness[strategy] = stats["successes"] / stats["attempts"]
        
        # Recent failures
        recent_failures = [case.input_hash for case in recent_history if not case.success]
        
        # Improvement trend
        improvement_trend = "stable"  # Simplified for now
        
        return PerformanceMetrics(
            success_rate=success_rate,
            avg_confidence=avg_confidence,
            avg_execution_time=avg_execution_time,
            pattern_usage_rate=pattern_usage_rate,
            user_satisfaction=user_satisfaction,
            strategy_effectiveness=strategy_effectiveness,
            recent_failures=recent_failures,
            improvement_trend=improvement_trend
        )
    
    def _reflect_on_strategy_effectiveness(self, metrics: PerformanceMetrics) -> List[ReflectionInsight]:
        """Reflect on which strategies are working well"""
        insights = []
        
        if not metrics.strategy_effectiveness:
            return insights
        
        # Find best and worst performing strategies
        best_strategy = max(metrics.strategy_effectiveness.items(), key=lambda x: x[1])
        worst_strategy = min(metrics.strategy_effectiveness.items(), key=lambda x: x[1])
        
        # Insight about best strategy
        if best_strategy[1] > 0.8:
            insights.append(ReflectionInsight(
                insight_type="strategy_success",
                description=f"Strategy '{best_strategy[0]}' is highly effective ({best_strategy[1]:.1%} success rate)",
                evidence=[f"Success rate: {best_strategy[1]:.1%}", "Consistently good results"],
                suggested_action=f"Increase usage of {best_strategy[0]} strategy for similar contexts",
                confidence=0.9,
                priority=4
            ))
        
        # Insight about worst strategy
        if worst_strategy[1] < 0.5:
            insights.append(ReflectionInsight(
                insight_type="strategy_failure",
                description=f"Strategy '{worst_strategy[0]}' is underperforming ({worst_strategy[1]:.1%} success rate)",
                evidence=[f"Success rate: {worst_strategy[1]:.1%}", "Multiple recent failures"],
                suggested_action=f"Revise decision criteria for {worst_strategy[0]} strategy or improve its implementation",
                confidence=0.8,
                priority=5
            ))
        
        return insights
    
    def _reflect_on_pattern_usage(self, metrics: PerformanceMetrics) -> List[ReflectionInsight]:
        """Reflect on pattern learning and usage"""
        insights = []
        
        # Low pattern usage might indicate learning issues
        if metrics.pattern_usage_rate < 0.2:
            insights.append(ReflectionInsight(
                insight_type="low_pattern_usage",
                description=f"Low pattern usage rate ({metrics.pattern_usage_rate:.1%})",
                evidence=["Few conversions using learned patterns", "Possible pattern matching issues"],
                suggested_action="Improve pattern extraction and matching algorithms",
                confidence=0.7,
                priority=3
            ))
        
        # High pattern usage with good results
        elif metrics.pattern_usage_rate > 0.6 and metrics.success_rate > 0.8:
            insights.append(ReflectionInsight(
                insight_type="effective_pattern_learning",
                description=f"High effective pattern usage ({metrics.pattern_usage_rate:.1%})",
                evidence=["Frequent pattern usage", "Good success rate"],
                suggested_action="Continue current pattern learning approach and expand pattern database",
                confidence=0.9,
                priority=2
            ))
        
        return insights
    
    def _reflect_on_failure_patterns(self, metrics: PerformanceMetrics) -> List[ReflectionInsight]:
        """Analyze failure patterns to identify improvement areas"""
        insights = []
        
        if len(metrics.recent_failures) >= 3:
            insights.append(ReflectionInsight(
                insight_type="failure_pattern",
                description=f"High failure rate detected: {len(metrics.recent_failures)} recent failures",
                evidence=[f"{len(metrics.recent_failures)} recent failures", "Pattern analysis needed"],
                suggested_action="Analyze failure contexts and develop specialized handling",
                confidence=0.8,
                priority=5
            ))
        
        return insights
    
    def _reflect_on_user_feedback(self, metrics: PerformanceMetrics) -> List[ReflectionInsight]:
        """Reflect on user satisfaction and feedback"""
        insights = []
        
        if metrics.user_satisfaction < 3.0:  # On 1-5 scale
            insights.append(ReflectionInsight(
                insight_type="low_user_satisfaction",
                description=f"User satisfaction is low ({metrics.user_satisfaction:.1f}/5.0)",
                evidence=["Low feedback scores", "User dissatisfaction"],
                suggested_action="Analyze user feedback patterns and improve output quality",
                confidence=0.9,
                priority=5
            ))
        elif metrics.user_satisfaction > 4.0:
            insights.append(ReflectionInsight(
                insight_type="high_user_satisfaction",
                description=f"High user satisfaction ({metrics.user_satisfaction:.1f}/5.0)",
                evidence=["Consistently good feedback", "User approval"],
                suggested_action="Maintain current quality standards and identify what users appreciate most",
                confidence=0.9,
                priority=2
            ))
        
        return insights
    
    def _reflect_on_learning_progress(self, metrics: PerformanceMetrics) -> List[ReflectionInsight]:
        """Reflect on overall learning and improvement trends"""
        insights = []
        
        if metrics.improvement_trend == "declining":
            insights.append(ReflectionInsight(
                insight_type="declining_performance",
                description="Performance is declining over time",
                evidence=["Decreasing success rate", "Negative trend"],
                suggested_action="Review recent changes and consider reverting problematic updates",
                confidence=0.8,
                priority=5
            ))
        elif metrics.improvement_trend == "improving":
            insights.append(ReflectionInsight(
                insight_type="positive_learning",
                description="Performance is improving over time",
                evidence=["Increasing success rate", "Positive trend"],
                suggested_action="Continue current learning approach and accelerate improvement",
                confidence=0.9,
                priority=3
            ))
        
        return insights
    
    def _generate_improvement_actions(self, insights: List[ReflectionInsight]):
        """Generate concrete improvement actions from insights"""
        high_priority_insights = [i for i in insights if i.priority >= 4]
        
        for insight in high_priority_insights:
            action = {
                "timestamp": datetime.now(),
                "insight_type": insight.insight_type,
                "action": insight.suggested_action,
                "status": "planned",
                "priority": insight.priority
            }
            self.improvement_actions.append(action)
            print(f"📋 Planned improvement action: {insight.suggested_action}")
    
    def _count_recent_failures(self) -> int:
        """Count failures in recent conversions"""
        recent = self.converter.conversion_history[-10:]
        return sum(1 for case in recent if not case.success)
    
    def _analyze_confidence_trend(self) -> float:
        """Analyze confidence trend over recent conversions"""
        if len(self.converter.conversion_history) < 20:
            return 0
        
        recent = self.converter.conversion_history[-10:]
        older = self.converter.conversion_history[-20:-10]
        
        recent_avg = sum(case.confidence for case in recent) / len(recent)
        older_avg = sum(case.confidence for case in older) / len(older)
        
        return recent_avg - older_avg
    
    def _check_negative_feedback(self) -> bool:
        """Check for recent negative user feedback"""
        recent = self.converter.conversion_history[-10:]
        negative_feedback = [case for case in recent 
                           if case.feedback_score is not None and case.feedback_score < 3]
        return len(negative_feedback) >= 2
    
    def get_reflection_summary(self) -> Dict:
        """Get summary of reflection activities"""
        return {
            "total_reflections": len(self.reflection_history),
            "last_reflection": self.last_reflection["timestamp"].isoformat() if self.last_reflection else None,
            "pending_actions": len([a for a in self.improvement_actions if a["status"] == "planned"]),
            "completed_actions": len([a for a in self.improvement_actions if a["status"] == "completed"]),
            "recent_insights": len(self.last_reflection["insights"]) if self.last_reflection else 0
        }

class FullyAgenticConverter(LearningAgenticConverter):
    """Fully agentic converter with self-reflection and continuous improvement"""
    
    def __init__(self, llm, memory_db_path: str = "agent_memory.db"):
        super().__init__(llm, memory_db_path)
        self.reflection_engine = SelfReflectionEngine(self)
        self.autonomy_level = 0.8  # How autonomous the agent is (0-1)
        print("✅ Fully agentic converter with self-reflection initialized")
    
    def convert(self, input_code: str) -> ConversionResult:
        """Fully agentic conversion with self-reflection"""
        
        # Check if self-reflection is needed
        should_reflect, trigger = self.reflection_engine.should_reflect()
        if should_reflect and self.autonomy_level > 0.7:
            print("🤔 Agent is performing self-reflection...")
            insights = self.reflection_engine.perform_reflection(trigger)
            
            # Log insights for user visibility
            for insight in insights[:3]:  # Show top 3 insights
                print(f"💡 Insight: {insight.description}")
        
        # Perform conversion
        result = super().convert(input_code)
        
        # Add self-reflection metadata
        result.metadata["reflection"] = {
            "reflection_triggered": should_reflect,
            "trigger": trigger.value if trigger else None,
            "autonomy_level": self.autonomy_level,
            "reflection_summary": self.reflection_engine.get_reflection_summary()
        }
        
        return result
    
    def set_autonomy_level(self, level: float):
        """Set how autonomous the agent should be (0-1)"""
        self.autonomy_level = max(0, min(1, level))
        print(f"🤖 Agent autonomy level set to {self.autonomy_level:.1%}")
    
    def get_agent_status(self) -> Dict:
        """Get comprehensive agent status"""
        base_stats = super().get_agent_status()
        reflection_summary = self.reflection_engine.get_reflection_summary()
        
        return {
            **base_stats,
            "agent_type": "fully_agentic",
            "autonomy_level": self.autonomy_level,
            "capabilities": base_stats["capabilities"] + ["self_reflection", "autonomous_improvement"],
            "reflection": reflection_summary,
            "total_conversions": len(self.conversion_history)
        }
    
    def trigger_manual_reflection(self) -> List[ReflectionInsight]:
        """Allow manual triggering of reflection"""
        print("🤔 Manual reflection triggered by user")
        return self.reflection_engine.perform_reflection(ReflectionTrigger.PERIODIC)

def setup_fully_agentic_pipeline(memory_db_path: str = "agent_memory.db", autonomy_level: float = 0.8):
    """Setup the fully agentic pipeline with all capabilities (Step 4)"""
    try:
        from dotenv import load_dotenv
        load_dotenv()
        
        from .dspy_implementation import GroqLLM
        llm = GroqLLM()
        
        converter = FullyAgenticConverter(llm, memory_db_path)
        converter.set_autonomy_level(autonomy_level)
        
        print("🤖 Fully agentic converter initialized (Step 4: Self-reflection & autonomy)")
        print("🧠 Capabilities: decision-making, planning, tool selection, adaptation, continuous learning, self-reflection")
        print(f"⚡ Autonomy level: {autonomy_level:.1%}")
        print("📚 Memory system: active")
        print("🔧 Available tools:", len(converter.tool_selector.tools))
        print("🤔 Self-reflection: enabled")
        
        return converter
        
    except Exception as e:
        print(f"❌ Error setting up fully agentic pipeline: {e}")
        raise e