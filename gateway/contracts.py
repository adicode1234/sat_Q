"""Validate specialist output at the service/controller boundary."""
from typing import Any, Literal
from pydantic import BaseModel, ConfigDict, Field


class SpecialistResult(BaseModel):
    model_config=ConfigDict(extra='allow',allow_inf_nan=False)
    status: Literal['complete','failed','unavailable']='complete'
    task: str
    model: str
    answer: str
    mode: str
    neural_confidence: float=Field(ge=0,le=1)
    confidence: dict
    claims: list[dict]=Field(default_factory=list)
    limitations: list[str]=Field(default_factory=list)
    evidence: list[dict]=Field(default_factory=list)
    spatial_outputs: dict=Field(default_factory=dict)
    metadata: dict=Field(default_factory=dict)
    timing: dict=Field(default_factory=dict)
    errors: list[dict]=Field(default_factory=list)
    overlay: dict | None=None


def checked_output(raw,tool,call,duration):
    from verification.confidence import normalize_score
    if not isinstance(raw,dict):raise ValueError('Specialist response must be an object')
    data={**raw,'task':call['task'],'model':tool['name'],
          'confidence':normalize_score(raw.get('neural_confidence'),tool.get('confidence_semantics','uncalibrated_model_score')),
          'timing':{'inference_s':duration},'metadata':{**raw.get('metadata',{}),'version':str(tool.get('version','1'))},
          'evidence':raw.get('claims',[]),'spatial_outputs':{'overlay':raw.get('overlay'),'heatmap':raw.get('heatmap')}}
    return SpecialistResult.model_validate(data).model_dump()


class EvidenceItem(BaseModel):
    model_config = ConfigDict(extra='forbid')
    text: str = Field(min_length=1)
    image_ids: list[str] = Field(min_length=1)
    kind: Literal['observed', 'inferred', 'uncertain', 'unsupported'] = 'uncertain'


class TaskEvidence(BaseModel):
    model_config = ConfigDict(extra='forbid')
    general: list[EvidenceItem] = Field(default_factory=list)
    before: list[EvidenceItem] = Field(default_factory=list)
    after: list[EvidenceItem] = Field(default_factory=list)
    optical: list[EvidenceItem] = Field(default_factory=list)
    sar: list[EvidenceItem] = Field(default_factory=list)
    agreement: list[EvidenceItem] = Field(default_factory=list)
    disagreement: list[EvidenceItem] = Field(default_factory=list)
    added: list[EvidenceItem] = Field(default_factory=list)
    removed: list[EvidenceItem] = Field(default_factory=list)
    reduced: list[EvidenceItem] = Field(default_factory=list)
    expanded: list[EvidenceItem] = Field(default_factory=list)
    unchanged: list[EvidenceItem] = Field(default_factory=list)


class RuntimeResponse(BaseModel):
    model_config = ConfigDict(extra='forbid')
    specialist: Literal['GeoChat', 'TEOChat', 'EarthMind']
    model: str = Field(min_length=1)
    answer: str = Field(min_length=1)
    observations: list[EvidenceItem] = Field(default_factory=list)
    evidence: TaskEvidence = Field(default_factory=TaskEvidence)
    uncertainty: list[str] = Field(default_factory=list)


class ReportConfidence(BaseModel):
    level: Literal['high', 'moderate', 'low'] | None = None
    reason: str = 'Calibrated confidence is unavailable; model text has not been independently verified.'


class AnalysisReport(BaseModel):
    model_config = ConfigDict(extra='forbid')
    query: str
    task: str
    specialist: str
    answer: str
    observations: list[EvidenceItem] = Field(default_factory=list)
    spatial_evidence: list[dict] = Field(default_factory=list)
    evidence: TaskEvidence = Field(default_factory=TaskEvidence)
    uncertainty: list[str] = Field(default_factory=list)
    confidence: ReportConfidence = Field(default_factory=ReportConfidence)
    execution_summary: dict
