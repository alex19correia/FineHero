"""
User Contributions Collector for FineHero Knowledge Base
=========================================================

Collects and structures user-contributed content:
- Fine examples from real users
- Contest defense letters and case studies
- Successful contest examples
- Community feedback and improvements

Features:
- User submission validation
- Privacy protection
- Content moderation
- Automatic categorization
- Integration with existing legal knowledge base
"""

import json
import re
from datetime import datetime
from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass, asdict
from pathlib import Path
import hashlib
from datetime import date

@dataclass
class FineExample:
    """Structure for user-contributed fine examples"""
    fine_id: str
    fine_type: str  # "estacionamento", "velocidade", etc.
    location: str
    amount: float
    infraction_code: str
    date_issued: date
    authority: str  # "PSP", "GNR", "Camera Municipal"
    description: str
    user_city: str
    contest_outcome: Optional[str]  # "successful", "failed", "pending"
    user_notes: Optional[str]
    privacy_hash: str  # Anonymous user identifier
    submission_date: datetime
    
    def __post_init__(self):
        """Generate privacy-safe hash for user tracking"""
        if not self.privacy_hash:
            content = f"{self.user_city}_{self.date_issued}_{self.location}"
            self.privacy_hash = hashlib.md5(content.encode()).hexdigest()[:8]

@dataclass
class ContestExample:
    """Structure for contest defense examples"""
    contest_id: str
    fine_reference: str  # Links to fine_id
    contest_type: str  # "administrative", "judicial", "appeal"
    outcome: str  # "approved", "rejected", "partial"
    defense_strategy: str
    outcome_factors: List[str]
    supporting_law: str
    submission_date: datetime
    user_feedback_score: float  # 1-5 rating
    community_approved: bool

class UserContributionsCollector:
    """Collects and validates user contributions to fine database"""
    
    def __init__(self, data_dir: str = "knowledge_base/user_contributions"):
        self.data_dir = Path(data_dir)
        self.data_dir.mkdir(parents=True, exist_ok=True)
        
        # Load existing contributions
        self.fine_examples = self._load_fine_examples()
        self.contest_examples = self._load_contest_examples()
        
        # Contamination categories for automated detection
        self.fine_categories = {
            'estacionamento': {
                'codes': ['48', '49', '50', '51'],
                'keywords': ['estacionamento', 'paragem', 'zona azul', 'parque'],
                'amounts': {'min': 30, 'max': 300}
            },
            'velocidade': {
                'codes': ['101', '102', '103', '104'],
                'keywords': ['velocidade', 'excesso', 'radar', 'limite'],
                'amounts': {'min': 60, 'max': 1200}
            },
            'documentos': {
                'codes': ['121', '122', '123', '124'],
                'keywords': ['documento', 'matrícula', 'seguro', 'inspeção'],
                'amounts': {'min': 30, 'max': 600}
            },
            'sinais_luminosos': {
                'codes': ['51', '52', '53', '105'],
                'keywords': ['luz', 'semáforo', 'sinal', 'vermelho'],
                'amounts': {'min': 120, 'max': 600}
            }
        }

    def _load_fine_examples(self) -> Dict[str, FineExample]:
        """Load existing fine examples from JSON"""
        file_path = self.data_dir / "fine_examples.json"
        if file_path.exists():
            with open(file_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
                return {fine_id: FineExample(**fine_data) for fine_id, fine_data in data.items()}
        return {}

    def _load_contest_examples(self) -> Dict[str, ContestExample]:
        """Load existing contest examples from JSON"""
        file_path = self.data_dir / "contest_examples.json"
        if file_path.exists():
            with open(file_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
                return {contest_id: ContestExample(**contest_data) for contest_id, contest_data in data.items()}
        return {}

    def validate_fine_submission(self, submission: Dict) -> Tuple[bool, List[str]]:
        """
        Validate user-submitted fine information
        
        Args:
            submission: Dictionary with fine information
            
        Returns:
            Tuple of (is_valid, error_messages)
        """
        errors = []
        required_fields = ['fine_type', 'location', 'amount', 'date_issued', 'authority']
        
        # Check required fields
        for field in required_fields:
            if field not in submission or not submission[field]:
                errors.append(f"Missing required field: {field}")
        
        # Validate fine type
        if submission.get('fine_type') not in self.fine_categories:
            errors.append(f"Invalid fine type. Must be one of: {list(self.fine_categories.keys())}")
        
        # Validate amount ranges
        fine_type = submission.get('fine_type')
        if fine_type and fine_type in self.fine_categories:
            amount = submission.get('amount', 0)
            range_info = self.fine_categories[fine_type]['amounts']
            if not (range_info['min'] <= amount <= range_info['max']):
                errors.append(f"Amount {amount} outside expected range for {fine_type}: {range_info['min']}-{range_info['max']}")
        
        # Validate date format (should be recent - within last 2 years)
        try:
            submitted_date = datetime.strptime(submission['date_issued'], '%Y-%m-%d').date()
            if submitted_date > date.today():
                errors.append("Date cannot be in the future")
            elif submitted_date < date.today().replace(year=date.today().year - 2):
                errors.append("Date too old (must be within last 2 years)")
        except (ValueError, TypeError):
            errors.append("Invalid date format (use YYYY-MM-DD)")
        
        return len(errors) == 0, errors

    def submit_fine_example(self, submission: Dict) -> Optional[str]:
        """
        Submit a new fine example from user
        
        Args:
            submission: Dictionary with fine information
            
        Returns:
            fine_id if successful, None if failed
        """
        # Validate submission
        is_valid, errors = self.validate_fine_submission(submission)
        if not is_valid:
            print(f"Submission validation failed: {errors}")
            return None
        
        # Generate unique ID
        content = f"{submission['location']}_{submission['date_issued']}_{submission['amount']}"
        fine_id = hashlib.md5(content.encode()).hexdigest()[:8]
        
        # Create FineExample
        fine_example = FineExample(
            fine_id=fine_id,
            fine_type=submission['fine_type'],
            location=submission['location'],
            amount=submission['amount'],
            infraction_code=submission.get('infraction_code', ''),
            date_issued=datetime.strptime(submission['date_issued'], '%Y-%m-%d').date(),
            authority=submission['authority'],
            description=submission.get('description', ''),
            user_city=submission.get('user_city', ''),
            contest_outcome=submission.get('contest_outcome'),
            user_notes=submission.get('user_notes'),
            privacy_hash='',  # Will be generated in __post_init__
            submission_date=datetime.now()
        )
        
        # Store
        self.fine_examples[fine_id] = fine_example
        self._save_fine_examples()
        
        print(f"Fine example added: {fine_id} - {fine_example.fine_type} in {fine_example.location}")
        return fine_id

    def submit_contest_example(self, submission: Dict) -> Optional[str]:
        """
        Submit a new contest example from user
        
        Args:
            submission: Dictionary with contest information
            
        Returns:
            contest_id if successful, None if failed
        """
        # Validate submission
        required_fields = ['fine_reference', 'contest_type', 'outcome', 'defense_strategy']
        for field in required_fields:
            if field not in submission or not submission[field]:
                print(f"Missing required field: {field}")
                return None
        
        # Generate unique ID
        content = f"{submission['fine_reference']}_{submission['outcome']}_{datetime.now().isoformat()}"
        contest_id = hashlib.md5(content.encode()).hexdigest()[:8]
        
        # Create ContestExample
        contest_example = ContestExample(
            contest_id=contest_id,
            fine_reference=submission['fine_reference'],
            contest_type=submission['contest_type'],
            outcome=submission['outcome'],
            defense_strategy=submission['defense_strategy'],
            outcome_factors=submission.get('outcome_factors', []),
            supporting_law=submission.get('supporting_law', ''),
            submission_date=datetime.now(),
            user_feedback_score=submission.get('user_feedback_score', 3.0),
            community_approved=False
        )
        
        # Store
        self.contest_examples[contest_id] = contest_example
        self._save_contest_examples()
        
        print(f"Contest example added: {contest_id} - {contest_example.outcome}")
        return contest_id

    def _save_fine_examples(self):
        """Save fine examples to JSON file"""
        file_path = self.data_dir / "fine_examples.json"
        data = {fine_id: asdict(fine) for fine_id, fine in self.fine_examples.items()}
        with open(file_path, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=2, default=str)

    def _save_contest_examples(self):
        """Save contest examples to JSON file"""
        file_path = self.data_dir / "contest_examples.json"
        data = {contest_id: asdict(contest) for contest_id, contest in self.contest_examples.items()}
        with open(file_path, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=2, default=str)

    def get_fine_examples_by_type(self, fine_type: str, limit: int = 10) -> List[FineExample]:
        """Get fine examples by type"""
        examples = [fine for fine in self.fine_examples.values() if fine.fine_type == fine_type]
        return examples[:limit]

    def get_successful_contests(self, limit: int = 20) -> List[ContestExample]:
        """Get successful contest examples"""
        successful = [contest for contest in self.contest_examples.values() if contest.outcome == 'approved']
        return successful[:limit]

    def get_community_statistics(self) -> Dict:
        """Generate community contribution statistics"""
        total_fines = len(self.fine_examples)
        total_contests = len(self.contest_examples)
        
        # Fine type distribution
        fine_type_dist = {}
        for fine in self.fine_examples.values():
            fine_type_dist[fine.fine_type] = fine_type_dist.get(fine.fine_type, 0) + 1
        
        # Contest success rate
        contest_outcomes = {}
        for contest in self.contest_examples.values():
            contest_outcomes[contest.outcome] = contest_outcomes.get(contest.outcome, 0) + 1
        
        success_rate = 0
        if total_contests > 0:
            success_rate = (contest_outcomes.get('approved', 0) / total_contests) * 100
        
        return {
            'total_fine_examples': total_fines,
            'total_contest_examples': total_contests,
            'fine_type_distribution': fine_type_dist,
            'contest_outcome_distribution': contest_outcomes,
            'contest_success_rate': success_rate,
            'last_updated': datetime.now().isoformat()
        }

if __name__ == "__main__":
    # Example usage
    collector = UserContributionsCollector()
    
    # Sample fine submission
    sample_fine = {
        'fine_type': 'estacionamento',
        'location': 'Rua Augusta, Lisboa',
        'amount': 60.0,
        'date_issued': '2024-03-15',
        'authority': 'Câmara Municipal de Lisboa',
        'infraction_code': '48.1.a',
        'description': 'Estacionamento em zona proibida',
        'user_city': 'Lisboa',
        'contest_outcome': 'pending',
        'user_notes': 'Primeira multa nesta localização'
    }
    
    fine_id = collector.submit_fine_example(sample_fine)
    if fine_id:
        print(f"Added fine example: {fine_id}")
        
        # Sample contest submission
        sample_contest = {
            'fine_reference': fine_id,
            'contest_type': 'administrative',
            'outcome': 'approved',
            'defense_strategy': 'Ilegibilidade da sinalização',
            'outcome_factors': ['Sinalização confusa', 'Falta de visibilidade'],
            'supporting_law': 'Artigo 48º do Código da Estrada',
            'user_feedback_score': 4.5
        }
        
        contest_id = collector.submit_contest_example(sample_contest)
        if contest_id:
            print(f"Added contest example: {contest_id}")
    
    # Show statistics
    stats = collector.get_community_statistics()
    print(f"\nCommunity Statistics: {json.dumps(stats, indent=2)}")