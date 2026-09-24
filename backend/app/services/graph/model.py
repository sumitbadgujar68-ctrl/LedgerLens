from datetime import datetime
from decimal import Decimal
from enum import Enum
from typing import List, Optional

from pydantic import BaseModel, Field


class NodeType(str, Enum):
    WALLET = "wallet"
    TRANSACTION = "transaction"
    ASSET = "asset"
    CONTRACT = "contract"
    SERVICE = "service"


class EdgeType(str, Enum):
    TRANSFERRED_TO = "transferred_to"
    INTERACTED_WITH = "interacted_with"


class GraphNode(BaseModel):
    id: str
    type: NodeType = NodeType.WALLET
    label: Optional[str] = None
    hop: int = 0
    metadata: dict = Field(default_factory=dict)


class GraphEdge(BaseModel):
    id: str
    source: str
    target: str
    type: EdgeType = EdgeType.TRANSFERRED_TO
    transaction_hash: str
    amount: Decimal = Decimal("0")
    asset: Optional[str] = None
    timestamp: Optional[datetime] = None
    hop: int = 0
    metadata: dict = Field(default_factory=dict)

    def __hash__(self):
        return hash(self.id)

    def __eq__(self, other):
        if isinstance(other, GraphEdge):
            return self.id == other.id
        return False


class CanonicalGraph(BaseModel):
    root_wallet_address: str
    blockchain: str = "ethereum"
    nodes: List[GraphNode] = Field(default_factory=list)
    edges: List[GraphEdge] = Field(default_factory=list)
    node_count: int = 0
    edge_count: int = 0
    max_hop_depth: int = 0

    def finalize(self) -> "CanonicalGraph":
        self.node_count = len(self.nodes)
        self.edge_count = len(self.edges)
        if self.nodes:
            self.max_hop_depth = max((n.hop for n in self.nodes), default=0)
        return self


class TraceConfig(BaseModel):
    max_hops: int = Field(default=3, ge=1, le=10)
    max_branches: int = Field(default=25, ge=1, le=500)
    min_amount: Optional[Decimal] = None
    asset_filters: Optional[List[str]] = None
    time_range_start: Optional[datetime] = None
    time_range_end: Optional[datetime] = None
    page_size: int = Field(default=100, ge=1, le=1000)
    max_pages_per_wallet: int = Field(default=5, ge=1, le=50)
