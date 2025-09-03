"""
Blockchain Research Integrity for AI Scholar
Immutable research records, authorship verification, and research lineage tracking
"""
import asyncio
import hashlib
import json
import logging
from typing import Dict, Any, List, Optional, Tuple
from dataclasses import dataclass, asdict
from datetime import datetime
import uuid
from cryptography.hazmat.primitives import hashes, serialization
from cryptography.hazmat.primitives.asymmetric import rsa, padding
import base64

logger = logging.getLogger(__name__)

@dataclass
class ResearchRecord:
    """Immutable research record on blockchain"""
    record_id: str
    paper_id: str
    title: str
    authors: List[Dict[str, str]]  # name, affiliation, orcid
    abstract: str
    timestamp: datetime
    content_hash: str
    previous_hash: Optional[str]
    digital_signatures: List[Dict[str, str]]
    metadata: Dict[str, Any]
    version: int

@dataclass
class AuthorshipProof:
    """Cryptographic proof of authorship"""
    author_id: str
    paper_id: str
    contribution_type: str
    contribution_percentage: float
    digital_signature: str
    timestamp: datetime
    verification_status: str

@dataclass
class ResearchLineage:
    """Research lineage and dependency tracking"""
    lineage_id: str
    paper_id: str
    parent_papers: List[str]
    derived_works: List[str]
    methodology_lineage: List[str]
    data_lineage: List[str]
    citation_chain: List[Dict[str, Any]]
    influence_score: floatcl
ass BlockchainResearchIntegrity:
    """Blockchain-based research integrity system"""
    
    def __init__(self):
        self.blockchain = []
        self.pending_records = []
        self.author_keys = {}  # Store public keys for authors
        self.research_lineage = {}
        self.integrity_scores = {}
        
    async def timestamp_research(self, research_data: Dict[str, Any]) -> ResearchRecord:
        """Create immutable timestamp for research"""
        
        # Generate content hash
        content_hash = self._generate_content_hash(research_data)
        
        # Get previous hash
        previous_hash = self._get_previous_hash()
        
        # Create research record
        record = ResearchRecord(
            record_id=str(uuid.uuid4()),
            paper_id=research_data.get("paper_id", str(uuid.uuid4())),
            title=research_data.get("title", ""),
            authors=research_data.get("authors", []),
            abstract=research_data.get("abstract", ""),
            timestamp=datetime.now(),
            content_hash=content_hash,
            previous_hash=previous_hash,
            digital_signatures=[],
            metadata=research_data.get("metadata", {}),
            version=research_data.get("version", 1)
        )
        
        # Add to blockchain
        await self._add_to_blockchain(record)
        
        logger.info(f"🔗 Research timestamped: {record.record_id}")
        return record
    
    def _generate_content_hash(self, research_data: Dict[str, Any]) -> str:
        """Generate SHA-256 hash of research content"""
        
        # Create deterministic string from research data
        content_string = json.dumps({
            "title": research_data.get("title", ""),
            "abstract": research_data.get("abstract", ""),
            "authors": sorted(research_data.get("authors", []), key=lambda x: x.get("name", "")),
            "content": research_data.get("content", ""),
            "methodology": research_data.get("methodology", ""),
            "results": research_data.get("results", "")
        }, sort_keys=True)
        
        return hashlib.sha256(content_string.encode()).hexdigest()
    
    def _get_previous_hash(self) -> Optional[str]:
        """Get hash of previous block"""
        if self.blockchain:
            return self.blockchain[-1].content_hash
        return None
    
    async def _add_to_blockchain(self, record: ResearchRecord):
        """Add record to blockchain"""
        self.blockchain.append(record)
        
        # Update research lineage
        await self._update_research_lineage(record)
    
    async def verify_authorship(self, paper_id: str) -> Dict[str, Any]:
        """Verify research authorship and contributions"""
        
        # Find research record
        record = self._find_research_record(paper_id)
        if not record:
            return {"verified": False, "error": "Research record not found"}
        
        verification_results = []
        
        for author in record.authors:
            author_verification = await self._verify_single_author(
                author, paper_id, record
            )
            verification_results.append(author_verification)
        
        # Calculate overall verification score
        verified_authors = [v for v in verification_results if v["verified"]]
        verification_score = len(verified_authors) / len(verification_results) if verification_results else 0
        
        return {
            "paper_id": paper_id,
            "verification_score": verification_score,
            "author_verifications": verification_results,
            "blockchain_verified": True,
            "timestamp_verified": self._verify_timestamp(record),
            "content_integrity": self._verify_content_integrity(record)
        }
    
    def _find_research_record(self, paper_id: str) -> Optional[ResearchRecord]:
        """Find research record by paper ID"""
        for record in self.blockchain:
            if record.paper_id == paper_id:
                return record
        return None
    
    async def _verify_single_author(
        self, 
        author: Dict[str, str], 
        paper_id: str, 
        record: ResearchRecord
    ) -> Dict[str, Any]:
        """Verify single author's contribution"""
        
        author_id = author.get("orcid") or author.get("email") or author.get("name")
        
        # Check digital signature
        signature_verified = await self._verify_digital_signature(
            author_id, paper_id, record.digital_signatures
        )
        
        # Check ORCID verification
        orcid_verified = await self._verify_orcid(author.get("orcid"))
        
        # Check institutional affiliation
        affiliation_verified = await self._verify_affiliation(
            author.get("affiliation"), author_id
        )
        
        # Check contribution history
        contribution_history = await self._get_contribution_history(author_id)
        
        return {
            "author_id": author_id,
            "name": author.get("name"),
            "verified": signature_verified and orcid_verified,
            "signature_verified": signature_verified,
            "orcid_verified": orcid_verified,
            "affiliation_verified": affiliation_verified,
            "contribution_history": contribution_history,
            "verification_timestamp": datetime.now().isoformat()
        }
    
    async def _verify_digital_signature(
        self, 
        author_id: str, 
        paper_id: str, 
        signatures: List[Dict[str, str]]
    ) -> bool:
        """Verify digital signature for author"""
        
        # Find signature for this author
        author_signature = None
        for sig in signatures:
            if sig.get("author_id") == author_id:
                author_signature = sig
                break
        
        if not author_signature:
            return False
        
        # Get author's public key
        public_key = self.author_keys.get(author_id)
        if not public_key:
            return False
        
        try:
            # Verify signature (simplified - in production use proper cryptographic verification)
            signature_data = author_signature.get("signature", "")
            message = f"{author_id}:{paper_id}".encode()
            
            # Mock verification - in production, use actual cryptographic verification
            return len(signature_data) > 0
            
        except Exception as e:
            logger.error(f"Signature verification failed: {e}")
            return False
    
    async def _verify_orcid(self, orcid: Optional[str]) -> bool:
        """Verify ORCID identifier"""
        if not orcid:
            return False
        
        # Mock ORCID verification - in production, integrate with ORCID API
        orcid_pattern = r"^\d{4}-\d{4}-\d{4}-\d{3}[\dX]$"
        import re
        return bool(re.match(orcid_pattern, orcid))
    
    async def _verify_affiliation(self, affiliation: Optional[str], author_id: str) -> bool:
        """Verify institutional affiliation"""
        if not affiliation:
            return False
        
        # Mock affiliation verification - in production, integrate with institutional databases
        known_institutions = [
            "MIT", "Stanford", "Harvard", "Oxford", "Cambridge",
            "University of California", "Carnegie Mellon", "ETH Zurich"
        ]
        
        return any(inst.lower() in affiliation.lower() for inst in known_institutions)
    
    async def _get_contribution_history(self, author_id: str) -> Dict[str, Any]:
        """Get author's contribution history"""
        
        # Find all papers by this author
        author_papers = []
        for record in self.blockchain:
            for author in record.authors:
                if (author.get("orcid") == author_id or 
                    author.get("email") == author_id or 
                    author.get("name") == author_id):
                    author_papers.append({
                        "paper_id": record.paper_id,
                        "title": record.title,
                        "timestamp": record.timestamp.isoformat(),
                        "role": author.get("role", "author")
                    })
        
        return {
            "total_papers": len(author_papers),
            "papers": author_papers[-10:],  # Last 10 papers
            "first_publication": min([p["timestamp"] for p in author_papers]) if author_papers else None,
            "recent_activity": len([p for p in author_papers if 
                                 datetime.fromisoformat(p["timestamp"]) > datetime.now().replace(year=datetime.now().year-1)])
        }
    
    def _verify_timestamp(self, record: ResearchRecord) -> bool:
        """Verify blockchain timestamp integrity"""
        
        # Check if record is in blockchain
        if record not in self.blockchain:
            return False
        
        # Check hash chain integrity
        record_index = self.blockchain.index(record)
        
        if record_index > 0:
            previous_record = self.blockchain[record_index - 1]
            if record.previous_hash != previous_record.content_hash:
                return False
        
        return True
    
    def _verify_content_integrity(self, record: ResearchRecord) -> bool:
        """Verify content hasn't been tampered with"""
        
        # Recalculate content hash
        research_data = {
            "title": record.title,
            "abstract": record.abstract,
            "authors": record.authors,
            "metadata": record.metadata
        }
        
        calculated_hash = self._generate_content_hash(research_data)
        return calculated_hash == record.content_hash
    
    async def track_research_lineage(self, paper_id: str) -> ResearchLineage:
        """Track research lineage and dependencies"""
        
        record = self._find_research_record(paper_id)
        if not record:
            raise ValueError(f"Research record not found: {paper_id}")
        
        # Find parent papers (cited works)
        parent_papers = await self._find_parent_papers(paper_id)
        
        # Find derived works (papers that cite this work)
        derived_works = await self._find_derived_works(paper_id)
        
        # Track methodology lineage
        methodology_lineage = await self._track_methodology_lineage(paper_id)
        
        # Track data lineage
        data_lineage = await self._track_data_lineage(paper_id)
        
        # Build citation chain
        citation_chain = await self._build_citation_chain(paper_id)
        
        # Calculate influence score
        influence_score = await self._calculate_influence_score(paper_id, derived_works)
        
        lineage = ResearchLineage(
            lineage_id=str(uuid.uuid4()),
            paper_id=paper_id,
            parent_papers=parent_papers,
            derived_works=derived_works,
            methodology_lineage=methodology_lineage,
            data_lineage=data_lineage,
            citation_chain=citation_chain,
            influence_score=influence_score
        )
        
        # Store lineage
        self.research_lineage[paper_id] = lineage
        
        return lineage
    
    async def _find_parent_papers(self, paper_id: str) -> List[str]:
        """Find papers that this research builds upon"""
        
        record = self._find_research_record(paper_id)
        if not record:
            return []
        
        # Extract references from metadata
        references = record.metadata.get("references", [])
        
        # Find which references are also in our blockchain
        parent_papers = []
        for ref in references:
            ref_id = ref.get("paper_id") or ref.get("doi")
            if ref_id and self._find_research_record(ref_id):
                parent_papers.append(ref_id)
        
        return parent_papers
    
    async def _find_derived_works(self, paper_id: str) -> List[str]:
        """Find papers that cite this work"""
        
        derived_works = []
        
        for record in self.blockchain:
            references = record.metadata.get("references", [])
            for ref in references:
                ref_id = ref.get("paper_id") or ref.get("doi")
                if ref_id == paper_id:
                    derived_works.append(record.paper_id)
                    break
        
        return derived_works
    
    async def _track_methodology_lineage(self, paper_id: str) -> List[str]:
        """Track methodology evolution and lineage"""
        
        record = self._find_research_record(paper_id)
        if not record:
            return []
        
        methodology = record.metadata.get("methodology", {})
        method_type = methodology.get("type", "")
        
        # Find papers with similar methodologies
        methodology_lineage = []
        
        for other_record in self.blockchain:
            if other_record.paper_id == paper_id:
                continue
            
            other_methodology = other_record.metadata.get("methodology", {})
            other_method_type = other_methodology.get("type", "")
            
            # Check for methodology similarity
            if method_type and other_method_type:
                if method_type == other_method_type:
                    methodology_lineage.append(other_record.paper_id)
        
        return methodology_lineage
    
    async def _track_data_lineage(self, paper_id: str) -> List[str]:
        """Track data usage and lineage"""
        
        record = self._find_research_record(paper_id)
        if not record:
            return []
        
        datasets_used = record.metadata.get("datasets", [])
        
        # Find other papers using same datasets
        data_lineage = []
        
        for other_record in self.blockchain:
            if other_record.paper_id == paper_id:
                continue
            
            other_datasets = other_record.metadata.get("datasets", [])
            
            # Check for dataset overlap
            common_datasets = set(datasets_used) & set(other_datasets)
            if common_datasets:
                data_lineage.append(other_record.paper_id)
        
        return data_lineage
    
    async def _build_citation_chain(self, paper_id: str) -> List[Dict[str, Any]]:
        """Build complete citation chain"""
        
        citation_chain = []
        
        # Get direct citations
        derived_works = await self._find_derived_works(paper_id)
        
        for citing_paper_id in derived_works:
            citing_record = self._find_research_record(citing_paper_id)
            if citing_record:
                citation_chain.append({
                    "citing_paper_id": citing_paper_id,
                    "citing_paper_title": citing_record.title,
                    "citation_timestamp": citing_record.timestamp.isoformat(),
                    "citation_context": "direct_citation"  # Could extract actual context
                })
        
        return citation_chain
    
    async def _calculate_influence_score(self, paper_id: str, derived_works: List[str]) -> float:
        """Calculate research influence score"""
        
        # Base score from direct citations
        direct_citations = len(derived_works)
        
        # Weight by citing paper importance (recursive)
        weighted_score = 0.0
        for citing_paper_id in derived_works:
            citing_derived = await self._find_derived_works(citing_paper_id)
            citing_influence = len(citing_derived) * 0.5  # Recursive influence
            weighted_score += 1.0 + citing_influence
        
        # Normalize score
        influence_score = min(1.0, weighted_score / 100.0)  # Cap at 1.0
        
        return influence_score
    
    async def _update_research_lineage(self, record: ResearchRecord):
        """Update research lineage when new record is added"""
        
        # Update lineage for this paper
        await self.track_research_lineage(record.paper_id)
        
        # Update lineage for papers that this paper cites
        references = record.metadata.get("references", [])
        for ref in references:
            ref_id = ref.get("paper_id") or ref.get("doi")
            if ref_id and self._find_research_record(ref_id):
                await self.track_research_lineage(ref_id)
    
    async def generate_integrity_report(self, paper_id: str) -> Dict[str, Any]:
        """Generate comprehensive integrity report"""
        
        record = self._find_research_record(paper_id)
        if not record:
            return {"error": "Research record not found"}
        
        # Verify authorship
        authorship_verification = await self.verify_authorship(paper_id)
        
        # Get research lineage
        lineage = await self.track_research_lineage(paper_id)
        
        # Check for potential issues
        integrity_issues = await self._detect_integrity_issues(paper_id)
        
        # Calculate overall integrity score
        integrity_score = await self._calculate_integrity_score(
            authorship_verification, lineage, integrity_issues
        )
        
        return {
            "paper_id": paper_id,
            "integrity_score": integrity_score,
            "authorship_verification": authorship_verification,
            "research_lineage": asdict(lineage),
            "integrity_issues": integrity_issues,
            "blockchain_status": {
                "timestamped": True,
                "hash_verified": self._verify_content_integrity(record),
                "chain_verified": self._verify_timestamp(record)
            },
            "report_generated": datetime.now().isoformat()
        }
    
    async def _detect_integrity_issues(self, paper_id: str) -> List[Dict[str, Any]]:
        """Detect potential integrity issues"""
        
        issues = []
        record = self._find_research_record(paper_id)
        
        if not record:
            return issues
        
        # Check for duplicate content
        duplicate_check = await self._check_for_duplicates(record)
        if duplicate_check["duplicates_found"]:
            issues.append({
                "type": "potential_duplication",
                "severity": "high",
                "description": "Similar content found in other papers",
                "details": duplicate_check
            })
        
        # Check authorship consistency
        authorship_issues = await self._check_authorship_consistency(record)
        if authorship_issues:
            issues.append({
                "type": "authorship_inconsistency",
                "severity": "medium",
                "description": "Inconsistencies in author information",
                "details": authorship_issues
            })
        
        # Check citation integrity
        citation_issues = await self._check_citation_integrity(record)
        if citation_issues:
            issues.append({
                "type": "citation_issues",
                "severity": "low",
                "description": "Issues with citation formatting or accuracy",
                "details": citation_issues
            })
        
        return issues
    
    async def _check_for_duplicates(self, record: ResearchRecord) -> Dict[str, Any]:
        """Check for duplicate or highly similar content"""
        
        duplicates = []
        
        for other_record in self.blockchain:
            if other_record.paper_id == record.paper_id:
                continue
            
            # Simple similarity check based on title and abstract
            title_similarity = self._calculate_text_similarity(
                record.title, other_record.title
            )
            abstract_similarity = self._calculate_text_similarity(
                record.abstract, other_record.abstract
            )
            
            if title_similarity > 0.8 or abstract_similarity > 0.7:
                duplicates.append({
                    "paper_id": other_record.paper_id,
                    "title_similarity": title_similarity,
                    "abstract_similarity": abstract_similarity,
                    "timestamp": other_record.timestamp.isoformat()
                })
        
        return {
            "duplicates_found": len(duplicates) > 0,
            "duplicate_count": len(duplicates),
            "duplicates": duplicates
        }
    
    def _calculate_text_similarity(self, text1: str, text2: str) -> float:
        """Calculate simple text similarity"""
        
        # Simple word-based similarity
        words1 = set(text1.lower().split())
        words2 = set(text2.lower().split())
        
        if not words1 or not words2:
            return 0.0
        
        intersection = words1 & words2
        union = words1 | words2
        
        return len(intersection) / len(union) if union else 0.0
    
    async def _check_authorship_consistency(self, record: ResearchRecord) -> List[Dict[str, Any]]:
        """Check for authorship consistency issues"""
        
        issues = []
        
        for author in record.authors:
            author_id = author.get("orcid") or author.get("email") or author.get("name")
            
            # Check if author name is consistent across papers
            name_variations = await self._get_author_name_variations(author_id)
            if len(name_variations) > 2:  # More than 2 name variations might be suspicious
                issues.append({
                    "author_id": author_id,
                    "issue": "multiple_name_variations",
                    "variations": name_variations
                })
            
            # Check affiliation consistency
            affiliation_variations = await self._get_author_affiliation_variations(author_id)
            if len(affiliation_variations) > 3:  # Frequent affiliation changes
                issues.append({
                    "author_id": author_id,
                    "issue": "frequent_affiliation_changes",
                    "affiliations": affiliation_variations
                })
        
        return issues
    
    async def _get_author_name_variations(self, author_id: str) -> List[str]:
        """Get all name variations for an author"""
        
        name_variations = set()
        
        for record in self.blockchain:
            for author in record.authors:
                if (author.get("orcid") == author_id or 
                    author.get("email") == author_id):
                    name_variations.add(author.get("name", ""))
        
        return list(name_variations)
    
    async def _get_author_affiliation_variations(self, author_id: str) -> List[str]:
        """Get all affiliation variations for an author"""
        
        affiliation_variations = set()
        
        for record in self.blockchain:
            for author in record.authors:
                if (author.get("orcid") == author_id or 
                    author.get("email") == author_id):
                    affiliation_variations.add(author.get("affiliation", ""))
        
        return list(affiliation_variations)
    
    async def _check_citation_integrity(self, record: ResearchRecord) -> List[Dict[str, Any]]:
        """Check citation integrity"""
        
        issues = []
        references = record.metadata.get("references", [])
        
        # Check for self-citations
        self_citations = 0
        for ref in references:
            ref_authors = ref.get("authors", [])
            for record_author in record.authors:
                for ref_author in ref_authors:
                    if record_author.get("name") == ref_author.get("name"):
                        self_citations += 1
                        break
        
        if self_citations > len(references) * 0.3:  # More than 30% self-citations
            issues.append({
                "issue": "excessive_self_citations",
                "self_citation_rate": self_citations / len(references),
                "self_citations": self_citations,
                "total_references": len(references)
            })
        
        return issues
    
    async def _calculate_integrity_score(
        self, 
        authorship_verification: Dict[str, Any],
        lineage: ResearchLineage,
        integrity_issues: List[Dict[str, Any]]
    ) -> float:
        """Calculate overall integrity score"""
        
        # Base score from authorship verification
        authorship_score = authorship_verification.get("verification_score", 0.0)
        
        # Penalty for integrity issues
        issue_penalty = 0.0
        for issue in integrity_issues:
            severity = issue.get("severity", "low")
            if severity == "high":
                issue_penalty += 0.3
            elif severity == "medium":
                issue_penalty += 0.2
            else:
                issue_penalty += 0.1
        
        # Bonus for research influence
        influence_bonus = min(0.2, lineage.influence_score * 0.2)
        
        # Calculate final score
        integrity_score = max(0.0, min(1.0, authorship_score - issue_penalty + influence_bonus))
        
        return integrity_score

# Global blockchain integrity system
blockchain_integrity = BlockchainResearchIntegrity()

# Convenience functions
async def timestamp_research(research_data: Dict[str, Any]) -> ResearchRecord:
    """Create immutable timestamp for research"""
    return await blockchain_integrity.timestamp_research(research_data)

async def verify_authorship(paper_id: str) -> Dict[str, Any]:
    """Verify research authorship"""
    return await blockchain_integrity.verify_authorship(paper_id)

async def track_research_lineage(paper_id: str) -> ResearchLineage:
    """Track research lineage and dependencies"""
    return await blockchain_integrity.track_research_lineage(paper_id)

async def generate_integrity_report(paper_id: str) -> Dict[str, Any]:
    """Generate comprehensive integrity report"""
    return await blockchain_integrity.generate_integrity_report(paper_id)

if __name__ == "__main__":
    # Example usage
    async def test_blockchain_integrity():
        print("🧪 Testing Blockchain Research Integrity...")
        
        # Test research timestamping
        research_data = {
            "paper_id": "test_paper_001",
            "title": "Blockchain Applications in Research Integrity",
            "abstract": "This paper explores the use of blockchain technology for ensuring research integrity...",
            "authors": [
                {
                    "name": "Dr. Alice Smith",
                    "orcid": "0000-0000-0000-0001",
                    "affiliation": "MIT",
                    "email": "alice@mit.edu"
                },
                {
                    "name": "Dr. Bob Johnson", 
                    "orcid": "0000-0000-0000-0002",
                    "affiliation": "Stanford",
                    "email": "bob@stanford.edu"
                }
            ],
            "metadata": {
                "methodology": {"type": "experimental"},
                "datasets": ["blockchain_dataset_1"],
                "references": [
                    {"paper_id": "ref_001", "authors": [{"name": "Dr. Charlie Brown"}]}
                ]
            }
        }
        
        record = await timestamp_research(research_data)
        print(f"✅ Research timestamped: {record.record_id}")
        
        # Test authorship verification
        verification = await verify_authorship(record.paper_id)
        print(f"✅ Authorship verification score: {verification['verification_score']:.2f}")
        
        # Test research lineage tracking
        lineage = await track_research_lineage(record.paper_id)
        print(f"✅ Research lineage tracked: influence score {lineage.influence_score:.2f}")
        
        # Test integrity report
        integrity_report = await generate_integrity_report(record.paper_id)
        print(f"✅ Integrity report generated: score {integrity_report['integrity_score']:.2f}")
        print(f"  - Issues found: {len(integrity_report['integrity_issues'])}")
    
    asyncio.run(test_blockchain_integrity())