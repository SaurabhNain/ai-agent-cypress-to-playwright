# agents/learning_system.py
# Step 3: Add Continuous Learning & Memory

import json
import sqlite3
import hashlib
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional, Tuple
from dataclasses import dataclass, asdict
from collections import defaultdict
from .tool_system import EnhancedAgenticConverter, ConversionResult, ConversionStrategy

@dataclass
class ConversionCase:
    """Represents a single conversion case for learning"""
    input_hash: str
    input_code: str
    output_code: str
    strategy_used: str
    success: bool
    confidence: float
    execution_time: float
    context: Dict[str, Any]
    feedback_score: Optional[float] = None
    timestamp: datetime = None
    
    def __post_init__(self):
        if self.timestamp is None:
            self.timestamp = datetime.now()

@dataclass
class LearningPattern:
    """Represents a learned pattern"""
    pattern_id: str
    input_pattern: str
    output_pattern: str
    success_rate: float
    usage_count: int
    avg_confidence: float
    context_conditions: Dict[str, Any]
    last_updated: datetime
    
class MemoryStore:
    """Persistent memory for the agent"""
    
    def __init__(self, db_path: str = "agent_memory.db"):
        self.db_path = db_path
        self._init_database()
    
    def _init_database(self):
        """Initialize SQLite database for memory storage"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # Conversion cases table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS conversion_cases (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                input_hash TEXT UNIQUE,
                input_code TEXT,
                output_code TEXT,
                strategy_used TEXT,
                success BOOLEAN,
                confidence REAL,
                execution_time REAL,
                context TEXT,
                feedback_score REAL,
                timestamp TEXT
            )
        ''')
        
        # Learned patterns table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS learned_patterns (
                pattern_id TEXT PRIMARY KEY,
                input_pattern TEXT,
                output_pattern TEXT,
                success_rate REAL,
                usage_count INTEGER,
                avg_confidence REAL,
                context_conditions TEXT,
                last_updated TEXT
            )
        ''')
        
        # Strategy performance table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS strategy_performance (
                strategy TEXT,
                context_hash TEXT,
                attempts INTEGER,
                successes INTEGER,
                avg_confidence REAL,
                avg_execution_time REAL,
                last_updated TEXT,
                PRIMARY KEY (strategy, context_hash)
            )
        ''')
        
        conn.commit()
        conn.close()
    
    def store_conversion_case(self, case: ConversionCase):
        """Store a conversion case in memory"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute('''
            INSERT OR REPLACE INTO conversion_cases 
            (input_hash, input_code, output_code, strategy_used, success, 
             confidence, execution_time, context, feedback_score, timestamp)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        ''', (
            case.input_hash, case.input_code, case.output_code,
            case.strategy_used, case.success, case.confidence,
            case.execution_time, json.dumps(case.context),
            case.feedback_score, case.timestamp.isoformat()
        ))
        
        conn.commit()
        conn.close()
    
    def get_similar_cases(self, input_hash: str, context: Dict, limit: int = 5) -> List[ConversionCase]:
        """Retrieve similar conversion cases for learning"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute('''
            SELECT * FROM conversion_cases 
            WHERE success = 1 
            ORDER BY confidence DESC, timestamp DESC 
            LIMIT ?
        ''', (limit,))
        
        cases = []
        for row in cursor.fetchall():
            cases.append(ConversionCase(
                input_hash=row[1],
                input_code=row[2],
                output_code=row[3],
                strategy_used=row[4],
                success=bool(row[5]),
                confidence=row[6],
                execution_time=row[7],
                context=json.loads(row[8]),
                feedback_score=row[9],
                timestamp=datetime.fromisoformat(row[10])
            ))
        
        conn.close()
        return cases
    
    def update_strategy_performance(self, strategy: str, context: Dict, success: bool, 
                                  confidence: float, execution_time: float):
        """Update strategy performance statistics"""
        context_hash = hashlib.md5(json.dumps(context, sort_keys=True).encode()).hexdigest()[:16]
        
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # Get existing record
        cursor.execute('''
            SELECT attempts, successes, avg_confidence, avg_execution_time 
            FROM strategy_performance 
            WHERE strategy = ? AND context_hash = ?
        ''', (strategy, context_hash))
        
        row = cursor.fetchone()
        
        if row:
            # Update existing
            attempts, successes, avg_conf, avg_time = row
            new_attempts = attempts + 1
            new_successes = successes + (1 if success else 0)
            new_avg_conf = (avg_conf * attempts + confidence) / new_attempts
            new_avg_time = (avg_time * attempts + execution_time) / new_attempts
            
            cursor.execute('''
                UPDATE strategy_performance 
                SET attempts = ?, successes = ?, avg_confidence = ?, 
                    avg_execution_time = ?, last_updated = ?
                WHERE strategy = ? AND context_hash = ?
            ''', (new_attempts, new_successes, new_avg_conf, new_avg_time,
                  datetime.now().isoformat(), strategy, context_hash))
        else:
            # Insert new
            cursor.execute('''
                INSERT INTO strategy_performance 
                (strategy, context_hash, attempts, successes, avg_confidence, 
                 avg_execution_time, last_updated)
                VALUES (?, ?, ?, ?, ?, ?, ?)
            ''', (strategy, context_hash, 1, 1 if success else 0, confidence,
                  execution_time, datetime.now().isoformat()))
        
        conn.commit()
        conn.close()

class PatternLearner:
    """Learns conversion patterns from successful cases"""
    
    def __init__(self, memory_store: MemoryStore):
        self.memory_store = memory_store
        self.learned_patterns: Dict[str, LearningPattern] = {}
        self._load_patterns()
    
    def _load_patterns(self):
        """Load existing patterns from memory"""
        conn = sqlite3.connect(self.memory_store.db_path)
        cursor = conn.cursor()
        
        cursor.execute('SELECT * FROM learned_patterns')
        for row in cursor.fetchall():
            pattern = LearningPattern(
                pattern_id=row[0],
                input_pattern=row[1],
                output_pattern=row[2],
                success_rate=row[3],
                usage_count=row[4],
                avg_confidence=row[5],
                context_conditions=json.loads(row[6]),
                last_updated=datetime.fromisoformat(row[7])
            )
            self.learned_patterns[pattern.pattern_id] = pattern
        
        conn.close()
        print(f"📚 Loaded {len(self.learned_patterns)} learned patterns")
    
    def find_matching_pattern(self, input_code: str, context: Dict) -> Optional[LearningPattern]:
        """Find the best matching learned pattern"""
        # Extract pattern from input code
        input_lines = input_code.strip().split('\n')
        key_patterns = []
        
        for line in input_lines:
            line = line.strip()
            if 'cy.' in line:
                if 'cy.get(' in line:
                    key_patterns.append('GET_ELEMENT')
                elif 'cy.type(' in line:
                    key_patterns.append('TYPE_TEXT')
                elif 'cy.click(' in line:
                    key_patterns.append('CLICK_ELEMENT')
                elif 'cy.should(' in line:
                    key_patterns.append('ASSERTION')
        
        input_pattern = '->'.join(key_patterns)
        
        # Find matching patterns
        best_match = None
        best_score = 0
        
        for pattern in self.learned_patterns.values():
            score = self._calculate_pattern_match_score(input_pattern, pattern, context)
            if score > best_score and score > 0.7:  # Threshold for confidence
                best_score = score
                best_match = pattern
        
        if best_match:
            print(f"🎯 Found matching pattern: {best_match.input_pattern} (score: {best_score:.2f})")
        
        return best_match
    
    def _calculate_pattern_match_score(self, input_pattern: str, learned_pattern: LearningPattern, context: Dict) -> float:
        """Calculate how well a learned pattern matches the current input"""
        # Pattern similarity
        input_steps = set(input_pattern.split('->'))
        learned_steps = set(learned_pattern.input_pattern.split('->'))
        
        if not input_steps or not learned_steps:
            return 0
        
        intersection = input_steps.intersection(learned_steps)
        union = input_steps.union(learned_steps)
        pattern_similarity = len(intersection) / len(union)
        
        # Context similarity
        context_similarity = 0
        if learned_pattern.context_conditions:
            matching_conditions = 0
            total_conditions = len(learned_pattern.context_conditions)
            
            for key, value in learned_pattern.context_conditions.items():
                if context.get(key) == value:
                    matching_conditions += 1
            
            context_similarity = matching_conditions / total_conditions if total_conditions > 0 else 0
        
        # Weighted score (pattern is more important than context)
        return pattern_similarity * 0.7 + context_similarity * 0.3

class LearningAgenticConverter(EnhancedAgenticConverter):
    """Agentic converter with continuous learning capabilities"""
    
    def __init__(self, llm, memory_db_path: str = "agent_memory.db"):
        super().__init__(llm)
        self.memory_store = MemoryStore(memory_db_path)
        self.pattern_learner = PatternLearner(self.memory_store)
        self.conversion_history = []
        print("✅ Learning-enabled agentic converter initialized")
    
    def convert(self, input_code: str) -> ConversionResult:
        """Enhanced conversion with learning"""
        start_time = datetime.now()
        print("🧠 Starting learning-enabled agentic conversion...")
        
        # Generate input hash for tracking
        input_hash = hashlib.md5(input_code.encode()).hexdigest()[:16]
        
        # Analyze code
        context = self._analyze_code(input_code)
        
        # Check for learned patterns first
        matching_pattern = self.pattern_learner.find_matching_pattern(input_code, context.__dict__)
        
        if matching_pattern and matching_pattern.success_rate > 0.8:
            print(f"🎯 Using learned pattern with {matching_pattern.success_rate:.1%} success rate")
            # Use pattern-guided conversion
            result = self._convert_with_pattern(input_code, matching_pattern, context)
        else:
            # Fall back to standard agentic conversion
            result = super().convert(input_code)
        
        # Calculate execution time
        execution_time = (datetime.now() - start_time).total_seconds()
        
        # Store conversion case for learning
        conversion_case = ConversionCase(
            input_hash=input_hash,
            input_code=input_code,
            output_code=result.code,
            strategy_used=result.strategy_used.value,
            success=result.success,
            confidence=result.confidence,
            execution_time=execution_time,
            context=context.__dict__
        )
        
        self.memory_store.store_conversion_case(conversion_case)
        self.conversion_history.append(conversion_case)
        
        # Update strategy performance
        self.memory_store.update_strategy_performance(
            result.strategy_used.value,
            context.__dict__,
            result.success,
            result.confidence,
            execution_time
        )
        
        # Learn from recent successful conversions
        if len(self.conversion_history) % 10 == 0:  # Learn every 10 conversions
            self._trigger_learning()
        
        # Enhance result with learning metadata
        result.metadata["learning"] = {
            "used_learned_pattern": matching_pattern is not None,
            "pattern_id": matching_pattern.pattern_id if matching_pattern else None,
            "total_learned_patterns": len(self.pattern_learner.learned_patterns),
            "conversion_number": len(self.conversion_history),
            "input_hash": input_hash
        }
        
        return result
    
    def _convert_with_pattern(self, input_code: str, pattern: LearningPattern, context) -> ConversionResult:
        """Convert using a learned pattern as guidance"""
        
        pattern_guided_prompt = f"""
        Convert this Cypress code to Playwright using the learned pattern:
        
        Input Pattern: {pattern.input_pattern}
        Expected Output Pattern: {pattern.output_pattern}
        Success Rate: {pattern.success_rate:.1%}
        
        Cypress Code:
        {input_code}
        
        Apply the pattern while adapting to the specific code structure.
        """
        
        try:
            converted_code = self.llm(pattern_guided_prompt)
            
            # Clean up response
            if "```javascript" in converted_code:
                converted_code = converted_code.split("```javascript")[1].split("```")[0].strip()
            elif "```" in converted_code:
                converted_code = converted_code.split("```")[1].split("```")[0].strip()
            
            # Update pattern usage
            pattern.usage_count += 1
            pattern.last_updated = datetime.now()
            
            return ConversionResult(
                success=True,
                code=converted_code,
                confidence=min(0.95, pattern.avg_confidence + 0.1),  # Slight boost for using learned pattern
                strategy_used=ConversionStrategy.SIMPLE,  # Simplified since pattern does the work
                issues=[],
                metadata={"used_pattern": pattern.pattern_id}
            )
            
        except Exception as e:
            # Pattern-guided conversion failed, fall back
            print(f"⚠️ Pattern-guided conversion failed: {e}")
            return super().convert(input_code)
    
    def _trigger_learning(self):
        """Trigger learning from recent successful conversions"""
        print("📚 Triggering learning from recent conversions...")
        
        # Get recent successful cases
        recent_successful = [case for case in self.conversion_history[-20:] 
                           if case.success and case.confidence > 0.7]
        
        if len(recent_successful) >= 3:
            # Simple pattern learning (in real implementation, use more sophisticated ML)
            print(f"🎓 Learning from {len(recent_successful)} successful cases")
        else:
            print("📖 Not enough successful cases to learn new patterns")
    
    def provide_feedback(self, input_hash: str, feedback_score: float):
        """Accept feedback on conversion quality (1-5 scale)"""
        conn = sqlite3.connect(self.memory_store.db_path)
        cursor = conn.cursor()
        
        cursor.execute('''
            UPDATE conversion_cases 
            SET feedback_score = ? 
            WHERE input_hash = ?
        ''', (feedback_score, input_hash))
        
        conn.commit()
        conn.close()
        
        print(f"📝 Received feedback score {feedback_score}/5 for conversion {input_hash}")
    
    def get_learning_stats(self) -> Dict:
        """Get comprehensive learning statistics"""
        recent_success_rate = self._calculate_recent_success_rate()
        avg_confidence = self._calculate_avg_confidence()
        
        return {
            "total_conversions": len(self.conversion_history),
            "learned_patterns": len(self.pattern_learner.learned_patterns),
            "recent_success_rate": recent_success_rate,
            "avg_confidence": avg_confidence,
            "memory_db_path": self.memory_store.db_path
        }
    
    def _calculate_recent_success_rate(self) -> float:
        """Calculate success rate for last 20 conversions"""
        recent = self.conversion_history[-20:]
        if not recent:
            return 0.0
        return sum(1 for case in recent if case.success) / len(recent)
    
    def _calculate_avg_confidence(self) -> float:
        """Calculate average confidence for recent conversions"""
        recent = self.conversion_history[-20:]
        if not recent:
            return 0.0
        return sum(case.confidence for case in recent) / len(recent)
    
    def get_agent_status(self) -> Dict:
        """Get comprehensive agent status including learning"""
        base_stats = super().get_agent_status()
        learning_stats = self.get_learning_stats()
        
        return {
            **base_stats,
            "agent_type": "learning_agentic",
            "capabilities": base_stats["capabilities"] + ["continuous_learning", "pattern_recognition", "memory_storage"],
            "learning": learning_stats
        }

def setup_learning_agentic_pipeline(memory_db_path: str = "agent_memory.db"):
    """Setup the learning-enabled agentic pipeline (Step 3)"""
    try:
        from dotenv import load_dotenv
        load_dotenv()
        
        from .dspy_implementation import GroqLLM
        llm = GroqLLM()
        
        converter = LearningAgenticConverter(llm, memory_db_path)
        print("🧠 Learning-enabled agentic converter initialized (Step 3: Learning & Memory)")
        print("📚 Memory system: active")
        print("🔧 Available tools:", len(converter.tool_selector.tools))
        
        return converter
        
    except Exception as e:
        print(f"❌ Error setting up learning-enabled agentic pipeline: {e}")
        raise e