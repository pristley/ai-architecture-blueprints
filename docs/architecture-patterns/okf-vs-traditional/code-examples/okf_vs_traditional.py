"""
OKF vs Traditional Methods - Python Implementation Examples

This module demonstrates:
1. Traditional approach: REST API + relational database queries
2. OKF approach: File system-based semantic navigation

Examples show error handling, validation, and performance characteristics.
"""

import json
import yaml
import os
from typing import Dict, List, Optional, Any
from datetime import datetime
from pathlib import Path
import time


# =============================================================================
# TRADITIONAL APPROACH: REST API + Database Abstraction
# =============================================================================

class TraditionalCustomerRepository:
    """
    Simulates a traditional approach using REST API calls + database queries.
    
    In a real system, this would make HTTP calls to an API endpoint and handle:
    - Network latency
    - Authentication/authorization
    - Response parsing
    - Error handling
    - Retry logic
    - Rate limiting
    """

    def __init__(self, api_base_url: str, api_key: str):
        """
        Initialize with API endpoint and credentials.
        
        Args:
            api_base_url: Base URL for REST API (e.g., "https://api.company.com/v1")
            api_key: API key for authentication
        """
        self.api_base = api_base_url
        self.api_key = api_key
        self.call_count = 0  # Track API calls for performance measurement
        self.total_latency = 0.0

    def _simulate_api_call(self, endpoint: str, delay_ms: int = 50) -> Dict[str, Any]:
        """
        Simulate an API call with network latency.
        
        Args:
            endpoint: API endpoint path
            delay_ms: Simulated network latency in milliseconds
            
        Returns:
            Simulated API response
            
        Raises:
            ConnectionError: If API call fails
            ValueError: If response format is invalid
        """
        # Simulate network latency
        time.sleep(delay_ms / 1000.0)
        self.call_count += 1
        self.total_latency += delay_ms

        # Mock responses
        responses = {
            "/customers/cust_123": {
                "id": "cust_123",
                "name": "Acme Corp",
                "industry": "Technology",
                "annual_revenue": 5000000,
                "segment": "enterprise",
                "created_at": "2024-01-15T10:30:00Z",
            },
            "/customers/cust_123/contracts": {
                "data": [
                    {
                        "id": "contract_001",
                        "name": "Platform License 2024",
                        "value": 1500000,
                        "signed_date": "2024-01-20",
                        "status": "active",
                    },
                    {
                        "id": "contract_002",
                        "name": "Support & Maintenance",
                        "value": 300000,
                        "signed_date": "2024-01-20",
                        "status": "active",
                    },
                ],
                "count": 2,
            },
            "/customers/cust_123/contacts": {
                "data": [
                    {
                        "id": "contact_001",
                        "name": "John Smith",
                        "email": "john@acme.com",
                        "role": "Procurement Manager",
                        "phone": "+1-555-0100",
                    },
                    {
                        "id": "contact_002",
                        "name": "Sarah Johnson",
                        "email": "sarah@acme.com",
                        "role": "Technical Lead",
                        "phone": "+1-555-0101",
                    },
                ],
                "count": 2,
            },
        }

        if endpoint not in responses:
            raise ValueError(f"Endpoint not found: {endpoint}")

        return responses[endpoint]

    def get_customer(self, customer_id: str) -> Dict[str, Any]:
        """
        Get customer data via API call.
        
        Args:
            customer_id: Customer identifier
            
        Returns:
            Customer data dictionary
            
        Raises:
            ValueError: If API response is invalid
        """
        try:
            response = self._simulate_api_call(f"/customers/{customer_id}", delay_ms=50)
            return response
        except Exception as e:
            raise ValueError(f"Failed to fetch customer {customer_id}: {str(e)}")

    def get_customer_contracts(self, customer_id: str) -> List[Dict[str, Any]]:
        """
        Get customer contracts via separate API call.
        
        Args:
            customer_id: Customer identifier
            
        Returns:
            List of contract dictionaries
            
        Raises:
            ValueError: If API response is invalid
        """
        try:
            response = self._simulate_api_call(
                f"/customers/{customer_id}/contracts", delay_ms=50
            )
            return response["data"]
        except Exception as e:
            raise ValueError(f"Failed to fetch contracts for {customer_id}: {str(e)}")

    def get_customer_contacts(self, customer_id: str) -> List[Dict[str, Any]]:
        """
        Get customer contacts via separate API call.
        
        Args:
            customer_id: Customer identifier
            
        Returns:
            List of contact dictionaries
            
        Raises:
            ValueError: If API response is invalid
        """
        try:
            response = self._simulate_api_call(
                f"/customers/{customer_id}/contacts", delay_ms=50
            )
            return response["data"]
        except Exception as e:
            raise ValueError(f"Failed to fetch contacts for {customer_id}: {str(e)}")

    def get_customer_full_context(self, customer_id: str) -> Dict[str, Any]:
        """
        Assemble full customer context from multiple API calls.
        
        This demonstrates the traditional approach:
        - Multiple API calls required
        - Network latency multiplied by number of calls
        - Each API call has independent error handling
        - Response format varies per endpoint
        
        Args:
            customer_id: Customer identifier
            
        Returns:
            Complete customer context dictionary
            
        Raises:
            ValueError: If any API call fails
        """
        print(f"\n[TRADITIONAL] Fetching customer {customer_id}...")
        start_time = time.time()
        self.call_count = 0
        self.total_latency = 0

        try:
            # Call 1: Get customer info
            customer = self.get_customer(customer_id)

            # Call 2: Get contracts
            contracts = self.get_customer_contracts(customer_id)

            # Call 3: Get contacts
            contacts = self.get_customer_contacts(customer_id)

            # Manually assemble context (prone to errors)
            context = {
                "customer": customer,
                "contracts": contracts,
                "contacts": contacts,
                "metadata": {
                    "api_calls_made": self.call_count,
                    "total_latency_ms": int(self.total_latency),
                    "fetch_time_ms": int((time.time() - start_time) * 1000),
                },
            }

            print(f"  ✓ Made {self.call_count} API calls, {self.total_latency:.0f}ms latency")
            return context

        except Exception as e:
            raise ValueError(f"Failed to fetch full customer context: {str(e)}")


# =============================================================================
# OKF APPROACH: File System-Based Semantic Navigation
# =============================================================================

class OKFCustomerRepository:
    """
    File system-based approach using Open Knowledge Format.
    
    Advantages:
    - Single file read for basic info
    - Relationships are pre-discovered (no additional queries)
    - Error handling is simpler (file I/O vs. network)
    - Schema changes don't break the code
    - Version history is embedded
    """

    def __init__(self, repo_path: str):
        """
        Initialize with OKF repository path.
        
        Args:
            repo_path: Path to OKF repository (e.g., "/data/okf-repo")
            
        Raises:
            ValueError: If repository path is invalid
        """
        if not os.path.isdir(repo_path):
            raise ValueError(f"Repository path not found: {repo_path}")

        self.repo_path = repo_path
        self.file_reads = 0
        self.total_io_time = 0.0

    def _load_yaml_file(self, file_path: str) -> Dict[str, Any]:
        """
        Load YAML file with error handling.
        
        Args:
            file_path: Path to YAML file
            
        Returns:
            Parsed YAML content as dictionary
            
        Raises:
            FileNotFoundError: If file doesn't exist
            yaml.YAMLError: If YAML is invalid
        """
        if not os.path.exists(file_path):
            raise FileNotFoundError(f"File not found: {file_path}")

        try:
            start_time = time.time()
            with open(file_path, "r") as f:
                data = yaml.safe_load(f)
            self.file_reads += 1
            self.total_io_time += time.time() - start_time
            return data
        except yaml.YAMLError as e:
            raise ValueError(f"Invalid YAML in {file_path}: {str(e)}")

    def get_customer_metadata(self, customer_id: str, year: str = "2024") -> Dict[str, Any]:
        """
        Load customer metadata from OKF file.
        
        Single file read with all necessary metadata.
        
        Args:
            customer_id: Customer identifier (e.g., "acme-corp")
            year: Year for versioning (e.g., "2024")
            
        Returns:
            Customer metadata with embedded relationships
            
        Raises:
            FileNotFoundError: If customer file doesn't exist
        """
        # In a real system, this path might be constructed from a semantic index
        file_path = (
            f"{self.repo_path}/customers/{year}/{customer_id}/metadata.okf.yaml"
        )

        return self._load_yaml_file(file_path)

    def get_customer_full_context(self, customer_id: str) -> Dict[str, Any]:
        """
        Assemble customer context from OKF files.
        
        Advantages:
        - Single file read for primary data
        - Relationships are pre-defined (no additional queries)
        - No network latency
        - Version history is embedded
        
        Args:
            customer_id: Customer identifier
            
        Returns:
            Complete customer context with relationships
            
        Raises:
            FileNotFoundError: If customer file doesn't exist
        """
        print(f"\n[OKF] Fetching customer {customer_id}...")
        start_time = time.time()
        self.file_reads = 0
        self.total_io_time = 0

        try:
            # Single file read
            customer = self.get_customer_metadata(customer_id)

            # Relationships are already defined in the file
            context = {
                "customer": {
                    "id": customer["_id"],
                    "name": customer["name"],
                    "industry": customer.get("industry"),
                    "revenue": customer.get("annual_revenue"),
                    "segment": customer.get("segment"),
                    "version": customer.get("_version"),
                },
                "relationships": customer.get("_references", []),
                "metadata": {
                    "file_reads": self.file_reads,
                    "io_time_ms": int(self.total_io_time * 1000),
                    "fetch_time_ms": int((time.time() - start_time) * 1000),
                },
            }

            print(f"  ✓ Made {self.file_reads} file reads, {self.total_io_time*1000:.1f}ms I/O")
            return context

        except FileNotFoundError:
            raise
        except Exception as e:
            raise ValueError(f"Failed to load customer context: {str(e)}")

    def follow_relationship(
        self, references: List[Dict[str, Any]], relation_type: str
    ) -> Optional[Dict[str, Any]]:
        """
        Follow a relationship to load related data.
        
        Demonstrates lazy loading pattern - relationships are discovered first,
        then loaded on demand.
        
        Args:
            references: List of _references from customer metadata
            relation_type: Type of relationship to follow (e.g., "contracts_active")
            
        Returns:
            Related entity data or None if relationship not found
        """
        for ref in references:
            if ref.get("relation") == relation_type:
                target_path = f"{self.repo_path}{ref['target']}"
                
                # Handle glob patterns (e.g., "/path/to/*")
                if "*" in target_path:
                    # In real system, use glob.glob to expand path
                    print(f"  Would load collection from: {target_path}")
                    return None
                else:
                    try:
                        return self._load_yaml_file(target_path)
                    except FileNotFoundError:
                        return None

        return None


# =============================================================================
# DEMONSTRATION & COMPARISON
# =============================================================================

def create_sample_okf_repo(repo_path: str) -> None:
    """
    Create a sample OKF repository structure for demonstration.
    
    Args:
        repo_path: Path where to create the repository
    """
    # Create directory structure
    os.makedirs(f"{repo_path}/customers/2024/acme-corp", exist_ok=True)

    # Create customer metadata file
    customer_metadata = {
        "_type": "Customer",
        "_id": "cust_123",
        "_version": "2.0",
        "_created": "2024-01-15T10:30:00Z",
        "_modified": "2024-06-28T14:22:00Z",
        "_references": [
            {
                "relation": "contracts_active",
                "target": "/customers/2024/acme-corp/contracts/active.okf.yaml",
                "cardinality": "many",
            },
            {
                "relation": "contacts",
                "target": "/customers/2024/acme-corp/contacts/john-smith.okf.yaml",
                "cardinality": "many",
            },
        ],
        "name": "Acme Corp",
        "industry": "Technology",
        "annual_revenue": 5000000,
        "segment": "enterprise",
    }

    # Write metadata file
    with open(f"{repo_path}/customers/2024/acme-corp/metadata.okf.yaml", "w") as f:
        yaml.dump(customer_metadata, f, default_flow_style=False)

    # Create contracts file
    contracts_data = {
        "_type": "ContractCollection",
        "items": [
            {
                "id": "contract_001",
                "name": "Platform License 2024",
                "value": 1500000,
                "signed_date": "2024-01-20",
                "status": "active",
            },
            {
                "id": "contract_002",
                "name": "Support & Maintenance",
                "value": 300000,
                "signed_date": "2024-01-20",
                "status": "active",
            },
        ],
    }

    os.makedirs(f"{repo_path}/customers/2024/acme-corp/contracts", exist_ok=True)
    with open(f"{repo_path}/customers/2024/acme-corp/contracts/active.okf.yaml", "w") as f:
        yaml.dump(contracts_data, f, default_flow_style=False)


def compare_approaches() -> None:
    """
    Demonstrate and compare traditional vs. OKF approaches.
    """
    print("=" * 70)
    print("OKF vs Traditional Methods - Python Implementation Comparison")
    print("=" * 70)

    # Setup OKF repository
    repo_path = "/tmp/okf-demo"
    create_sample_okf_repo(repo_path)

    # =================================================================
    # APPROACH 1: TRADITIONAL (REST API + Multiple Queries)
    # =================================================================
    print("\n[APPROACH 1: TRADITIONAL REST API]")
    print("-" * 70)

    traditional_repo = TraditionalCustomerRepository(
        api_base_url="https://api.company.com/v1", api_key="sk-xxxx"
    )

    try:
        traditional_context = traditional_repo.get_customer_full_context("cust_123")
        print(f"\nCustomer: {traditional_context['customer']['name']}")
        print(f"Contracts: {len(traditional_context['contracts'])} active")
        print(f"Contacts: {len(traditional_context['contacts'])} people")
        print(f"\nPerformance:")
        print(f"  - API calls: {traditional_context['metadata']['api_calls_made']}")
        print(f"  - Network latency: {traditional_context['metadata']['total_latency_ms']}ms")
        print(f"  - Total fetch time: {traditional_context['metadata']['fetch_time_ms']}ms")
    except Exception as e:
        print(f"Error: {e}")

    # =================================================================
    # APPROACH 2: OKF (File System + Semantic Navigation)
    # =================================================================
    print("\n[APPROACH 2: OKF FILE SYSTEM]")
    print("-" * 70)

    okf_repo = OKFCustomerRepository(repo_path)

    try:
        okf_context = okf_repo.get_customer_full_context("acme-corp")
        print(f"\nCustomer: {okf_context['customer']['name']}")
        print(f"Relationships defined: {len(okf_context['relationships'])}")
        print(f"  - contracts_active")
        print(f"  - contacts")
        print(f"\nPerformance:")
        print(f"  - File reads: {okf_context['metadata']['file_reads']}")
        print(f"  - I/O time: {okf_context['metadata']['io_time_ms']}ms")
        print(f"  - Total fetch time: {okf_context['metadata']['fetch_time_ms']}ms")
    except Exception as e:
        print(f"Error: {e}")

    # =================================================================
    # PERFORMANCE COMPARISON
    # =================================================================
    print("\n[PERFORMANCE COMPARISON]")
    print("-" * 70)

    traditional_latency = traditional_context["metadata"]["total_latency_ms"]
    okf_latency = okf_context["metadata"]["io_time_ms"]

    print(f"\nTraditional Approach:")
    print(f"  - Network latency: {traditional_latency}ms")
    print(f"  - API calls required: {traditional_context['metadata']['api_calls_made']}")

    print(f"\nOKF Approach:")
    print(f"  - I/O latency: {okf_latency}ms")
    print(f"  - File reads required: {okf_context['metadata']['file_reads']}")

    speedup = traditional_latency / max(okf_latency, 1)
    print(f"\nSpeedup: {speedup:.1f}x faster with OKF")

    # =================================================================
    # RELATIONSHIP TRAVERSAL
    # =================================================================
    print("\n[RELATIONSHIP TRAVERSAL]")
    print("-" * 70)

    print("\nOKF: Follow relationship to contracts")
    contracts = okf_repo.follow_relationship(
        okf_context["relationships"], "contracts_active"
    )
    if contracts:
        print(f"  Found {len(contracts['items'])} contracts")
        for contract in contracts["items"]:
            print(f"    - {contract['name']}: ${contract['value']:,}")

    # Cleanup
    import shutil
    shutil.rmtree(repo_path)


if __name__ == "__main__":
    compare_approaches()
